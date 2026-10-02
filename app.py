"""
Face Recognition-Based Secure Login
------------------------------------
A self-contained Flask application demonstrating a two-factor login flow:
  1. Username + password (something you know)
  2. Live face verification with a lightweight blink-based liveness
     check (something you are)

Face detection:   OpenCV Haar Cascades (frontal face + eyes)
Face recognition:  OpenCV LBPH (Local Binary Patterns Histograms) recognizer
Storage:           SQLite for accounts, JPEG crops + a trained .yml model
                    on disk for face data (raw photos are cropped-to-face,
                    grayscale, 200x200 -- not full images).

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import base64
import io
import os
import sqlite3
import time
from datetime import datetime

import cv2
import numpy as np
from flask import (Flask, g, jsonify, redirect, render_template, request,
                    session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
FACE_DATA_DIR = os.path.join(BASE_DIR, "face_data")
MODEL_PATH = os.path.join(BASE_DIR, "model.yml")

SAMPLES_PER_USER = 20          # frames captured during enrollment
FACE_SIZE = (200, 200)         # normalized crop size fed to LBPH
LBPH_CONFIDENCE_THRESHOLD = 75 # lower = stricter match (LBPH: lower is better)
MOTION_DIFF_THRESHOLD = 2.2     # min avg pixel change (0-255) between frames to count as "alive"
VERIFY_FRAMES_NEEDED = 24      # frames captured during login verification

os.makedirs(FACE_DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

def _load_cascade(filename):
    """
    Load a Haar cascade, preferring the copy bundled in ./cascades (works
    regardless of the OpenCV build/platform) and falling back to the copy
    inside the installed cv2 package if present.
    """
    bundled_path = os.path.join(BASE_DIR, "cascades", filename)
    packaged_path = os.path.join(cv2.data.haarcascades, filename)

    for path in (bundled_path, packaged_path):
        if os.path.isfile(path):
            classifier = cv2.CascadeClassifier(path)
            if not classifier.empty():
                return classifier

    raise FileNotFoundError(
        f"Could not load Haar cascade '{filename}'. Checked:\n"
        f"  - {bundled_path}\n"
        f"  - {packaged_path}\n"
        "Make sure the 'cascades' folder was copied alongside app.py."
    )


face_cascade = _load_cascade("haarcascade_frontalface_default.xml")
eye_cascade = _load_cascade("haarcascade_eye.xml")


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            face_registered INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# Image / face helpers
# --------------------------------------------------------------------------
def decode_base64_image(data_url):
    """Convert a 'data:image/jpeg;base64,....' string into an OpenCV BGR image."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


def detect_largest_face(gray_img):
    faces = face_cascade.detectMultiScale(
        gray_img, scaleFactor=1.2, minNeighbors=6, minSize=(80, 80)
    )
    if len(faces) == 0:
        return None
    # pick the largest detected face (closest to camera)
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return faces[0]  # (x, y, w, h)


def detect_eyes(gray_face_roi):
    """
    Search only the upper ~60% of the face box (where eyes actually are).
    Restricting the region cuts out nose/mouth/jaw texture that otherwise
    causes the eye cascade to miss real, open eyes -- Haar eye detection is
    noisy enough already without giving it irrelevant area to search.
    """
    h = gray_face_roi.shape[0]
    upper = gray_face_roi[: int(h * 0.62), :]
    eyes = eye_cascade.detectMultiScale(
        upper, scaleFactor=1.05, minNeighbors=3, minSize=(18, 18)
    )
    return eyes


def crop_and_normalize(gray_img, box):
    x, y, w, h = box
    face_roi = gray_img[y : y + h, x : x + w]
    face_roi = cv2.resize(face_roi, FACE_SIZE)
    face_roi = cv2.equalizeHist(face_roi)  # normalize lighting
    return face_roi


def user_face_dir(username):
    path = os.path.join(FACE_DATA_DIR, username)
    os.makedirs(path, exist_ok=True)
    return path


def train_model():
    """(Re)trains the global LBPH recognizer over every enrolled user's saved crops."""
    faces = []
    labels = []

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    users = db.execute(
        "SELECT id, username FROM users WHERE face_registered = 1"
    ).fetchall()
    db.close()

    if not users:
        return False

    for user in users:
        folder = user_face_dir(user["username"])
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".jpg"):
                continue
            img = cv2.imread(os.path.join(folder, fname), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            faces.append(img)
            labels.append(user["id"])

    if not faces:
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(MODEL_PATH)
    return True


def load_recognizer():
    if not os.path.exists(MODEL_PATH):
        return None
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    return recognizer


# --------------------------------------------------------------------------
# Routes - pages
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", user=session.get("username"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if not username or not password:
            error = "Username and password are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."

        if not error:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                error = "That username is already taken."

        if error:
            return render_template("register.html", error=error)

        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, face_registered, created_at) "
            "VALUES (?, ?, 0, ?)",
            (username, generate_password_hash(password), datetime.utcnow().isoformat()),
        )
        db.commit()

        session["pending_enrollment_user"] = username
        return redirect(url_for("enroll_face"))

    return render_template("register.html", error=None)


@app.route("/enroll")
def enroll_face():
    username = session.get("pending_enrollment_user")
    if not username:
        return redirect(url_for("register"))
    return render_template(
        "capture.html",
        mode="enroll",
        username=username,
        samples_needed=SAMPLES_PER_USER,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid username or password.")

        if not user["face_registered"]:
            return render_template(
                "login.html",
                error="This account has no enrolled face data yet. Please contact support.",
            )

        session["pending_verify_user"] = username
        return redirect(url_for("verify_face"))

    return render_template("login.html", error=None)


@app.route("/verify")
def verify_face():
    username = session.get("pending_verify_user")
    if not username:
        return redirect(url_for("login"))
    return render_template(
        "capture.html",
        mode="verify",
        username=username,
        samples_needed=VERIFY_FRAMES_NEEDED,
    )


@app.route("/dashboard")
def dashboard():
    if not session.get("username"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session.get("username"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# --------------------------------------------------------------------------
# Routes - JSON API used by the webcam capture page
# --------------------------------------------------------------------------
@app.route("/api/enroll_frame", methods=["POST"])
def api_enroll_frame():
    username = session.get("pending_enrollment_user")
    if not username:
        return jsonify({"ok": False, "message": "No active enrollment session."}), 400

    payload = request.get_json(force=True)
    img = decode_base64_image(payload.get("image", ""))
    if img is None:
        return jsonify({"ok": False, "message": "Could not decode image."}), 400

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    box = detect_largest_face(gray)
    if box is None:
        return jsonify({"ok": False, "message": "No face detected. Center your face in frame."})

    face_crop = crop_and_normalize(gray, box)
    folder = user_face_dir(username)
    existing = [f for f in os.listdir(folder) if f.endswith(".jpg")]
    idx = len(existing) + 1
    cv2.imwrite(os.path.join(folder, f"sample_{idx:03d}.jpg"), face_crop)

    done = idx >= SAMPLES_PER_USER
    return jsonify({"ok": True, "message": "Face captured.", "count": idx, "done": done})


@app.route("/api/finish_enrollment", methods=["POST"])
def api_finish_enrollment():
    username = session.get("pending_enrollment_user")
    if not username:
        return jsonify({"ok": False, "message": "No active enrollment session."}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    folder = user_face_dir(username)
    count = len([f for f in os.listdir(folder) if f.endswith(".jpg")])

    if count < max(5, SAMPLES_PER_USER // 2):
        return jsonify({
            "ok": False,
            "message": f"Only {count} usable samples captured. Please retake, with better lighting and a centered face.",
        })

    db.execute("UPDATE users SET face_registered = 1 WHERE username = ?", (username,))
    db.commit()

    trained = train_model()
    if not trained:
        return jsonify({"ok": False, "message": "Model training failed. Try enrolling again."})

    session.pop("pending_enrollment_user", None)
    return jsonify({"ok": True, "redirect": url_for("login")})


def motion_thumbnail(gray_img, box):
    """
    Downsample the face region to a small grayscale thumbnail. Comparing
    thumbnails between consecutive frames gives a cheap, robust motion
    signal -- small enough to store in the session cookie between requests,
    unlike full frames or crops.
    """
    x, y, w, h = box
    roi = gray_img[y : y + h, x : x + w]
    thumb = cv2.resize(roi, (16, 16))
    return thumb.flatten().tolist()


def thumbnail_diff(a, b):
    if a is None or b is None:
        return 0.0
    arr_a = np.array(a, dtype=np.int16)
    arr_b = np.array(b, dtype=np.int16)
    return float(np.mean(np.abs(arr_a - arr_b)))


@app.route("/api/verify_frame", methods=["POST"])
def api_verify_frame():
    """
    Accepts one frame at a time during the login verification sequence.

    Liveness is judged by frame-to-frame motion: a live face in front of a
    webcam always shows small natural movement (blinks, micro head motion,
    breathing) between frames, while a printed photo or frozen screen does
    not. This is far more robust across real-world lighting/webcam quality
    than trying to catch a discrete "eyes closed" frame with a Haar eye
    cascade, which frequently misses open eyes entirely on consumer webcams.

    Face recognition (LBPH) runs on every frame where a face is detected,
    and a majority of frames must match the enrolled user within the
    confidence threshold.
    """
    username = session.get("pending_verify_user")
    if not username:
        return jsonify({"ok": False, "message": "No active login session."}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        return jsonify({"ok": False, "message": "User not found."}), 400

    recognizer = load_recognizer()
    if recognizer is None:
        return jsonify({"ok": False, "message": "No trained model available."}), 400

    payload = request.get_json(force=True)
    img = decode_base64_image(payload.get("image", ""))
    if img is None:
        return jsonify({"ok": False, "message": "Could not decode image."})

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    box = detect_largest_face(gray)

    state = session.get("verify_state", {
        "frames": 0, "prev_thumb": None, "max_motion": 0.0,
        "match_votes": 0, "total_predictions": 0,
    })

    if box is None:
        state["frames"] += 1
        session["verify_state"] = state
        return jsonify({
            "ok": True, "face_detected": False,
            "frames": state["frames"], "needed": VERIFY_FRAMES_NEEDED,
        })

    thumb = motion_thumbnail(gray, box)
    diff = thumbnail_diff(state["prev_thumb"], thumb)
    state["max_motion"] = max(state["max_motion"], diff)
    state["prev_thumb"] = thumb

    norm = crop_and_normalize(gray, box)
    label, confidence = recognizer.predict(norm)
    state["total_predictions"] += 1
    if label == user["id"] and confidence <= LBPH_CONFIDENCE_THRESHOLD:
        state["match_votes"] += 1

    state["frames"] += 1
    session["verify_state"] = state

    done = state["frames"] >= VERIFY_FRAMES_NEEDED
    result = {
        "ok": True,
        "face_detected": True,
        "frames": state["frames"],
        "needed": VERIFY_FRAMES_NEEDED,
        "done": done,
    }

    if done:
        liveness_ok = state["max_motion"] >= MOTION_DIFF_THRESHOLD
        match_ratio = (
            state["match_votes"] / state["total_predictions"]
            if state["total_predictions"] else 0
        )
        face_ok = state["total_predictions"] >= 3 and match_ratio >= 0.6

        session.pop("verify_state", None)

        if not liveness_ok:
            result["success"] = False
            result["reason"] = "liveness"
            result["message"] = "Liveness check failed \u2014 no natural movement detected. Please try again and move/blink naturally, not a static photo."
        elif not face_ok:
            result["success"] = False
            result["reason"] = "mismatch"
            result["message"] = "Face did not match the enrolled profile. Access denied."
        else:
            session["username"] = username
            session.pop("pending_verify_user", None)
            result["success"] = True
            result["message"] = "Identity verified."
            result["redirect"] = url_for("dashboard")

    return jsonify(result)


@app.route("/api/cancel", methods=["POST"])
def api_cancel():
    session.pop("pending_enrollment_user", None)
    session.pop("pending_verify_user", None)
    session.pop("verify_state", None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

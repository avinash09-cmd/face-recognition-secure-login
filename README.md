# Facescan — Face Recognition-Based Secure Login

A complete, working two-factor login system: **password + live face verification**,
built with Flask and OpenCV. Runs entirely locally — no cloud APIs, no external
face-recognition service.

## What it does

1. **Register** — create a username + password (stored as a salted hash).
2. **Enroll face** — your webcam captures 20 samples of your face, which are
   cropped, grayscale-normalized, and used to train a personal LBPH
   (Local Binary Patterns Histogram) recognition model.
3. **Log in** — enter your password (factor 1), then verify live on camera
   (factor 2). The system:
   - Detects your face each frame (Haar cascade)
   - Requires **live frame-to-frame motion** during the capture sequence
     (basic liveness check, so a printed photo or static image on a phone
     screen won't pass — only a real, moving human being will)
   - Runs face recognition on every frame and requires a majority match
     against your enrolled model, within a confidence threshold
4. **Dashboard** — only reachable after both factors succeed.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in a browser that has webcam access (Chrome/
Firefox/Edge all work; the browser will prompt for camera permission).

> Camera access via `getUserMedia` requires either `localhost` or HTTPS —
> it will not work over plain `http://<ip>` from another machine.

## Project structure

```
face_login/
├── app.py                  Flask app: routes, DB, face detection/training/verification
├── requirements.txt
├── database.db              SQLite (created on first run) — users table
├── model.yml                 Trained LBPH model (created after first enrollment)
├── face_data/<username>/     Cropped grayscale 200x200 face samples per user
├── templates/
│   ├── base.html            Shared layout/nav
│   ├── index.html           Landing page
│   ├── register.html        Step 1: create credentials
│   ├── login.html            Step 1: sign in with password
│   ├── capture.html          Step 2: webcam capture (shared by enroll + verify)
│   └── dashboard.html        Protected page after full login
└── static/
    ├── css/style.css        Design system
    └── js/capture.js        getUserMedia capture loop + API calls
```

## How the recognition works

- **Detection**: OpenCV Haar cascades (`haarcascade_frontalface_default.xml`,
  `haarcascade_eye.xml`), bundled with OpenCV — no extra downloads.
- **Recognition**: `cv2.face.LBPHFaceRecognizer` (from `opencv-contrib-python`).
  It's trained on all enrolled users' cropped face images, with each user's
  database ID as the label. On verification, `recognizer.predict()` returns a
  `(label, confidence)` pair — lower confidence means a closer match.
- **Liveness**: during the ~24-frame verification sequence, the app downsamples
  the detected face region to a small 16x16 thumbnail each frame and compares
  it to the previous frame's thumbnail. A live face in front of a webcam
  always shows some natural frame-to-frame movement (blinks, micro head
  motion, breathing); a printed photo or frozen screen doesn't. If no frame
  pair differs by more than `MOTION_DIFF_THRESHOLD`, verification fails even
  if the face otherwise matches — this blocks simple static-photo/replay
  attacks, and is considerably more robust across real webcams/lighting than
  trying to catch a discrete "eyes closed" frame with a Haar eye cascade
  (which frequently misses open eyes entirely on consumer hardware).
- **Storage**: only grayscale, cropped, equalized 200×200 face images are
  saved to disk — never the raw camera frame — and only numeric LBPH
  histograms are used for matching, not images sent anywhere external.

## Tuning knobs (top of `app.py`)

| Constant | Meaning |
|---|---|
| `SAMPLES_PER_USER` | How many frames to capture during enrollment (default 20) |
| `VERIFY_FRAMES_NEEDED` | Frames captured per login attempt (default 15) |
| `LBPH_CONFIDENCE_THRESHOLD` | Lower = stricter match required (default 75) |
| `MOTION_DIFF_THRESHOLD` | Min average pixel change (0-255) between frames to count as "alive" (default 2.2). Lower if real logins fail liveness in bright, still conditions; raise if a held-still photo passes. |

## Known limitations (be aware before using this beyond a demo)

- **LBPH is a classical, lightweight recognizer** — good for a personal/small-scale
  demo, but far less accurate than deep-learning embeddings (FaceNet/ArcFace) at
  scale or under varied lighting/pose. For production use, swap in a proper
  face-embedding model.
- **Motion-based liveness is a basic heuristic**, not a robust anti-spoofing
  system — it stops naive static-photo replay but not a video of the
  enrolled user played back on a phone/screen. Production systems combine
  multiple liveness signals (texture/depth analysis, challenge-response, IR
  sensors).
- **Single-process dev server** (`app.run(debug=True)`). For real deployment,
  run behind a production WSGI server (gunicorn/uwsgi) with `debug=False`,
  set a strong `FLASK_SECRET_KEY` environment variable, and serve over HTTPS.
- Treat face data as sensitive biometric data: encrypt at rest, and follow
  applicable regulations (GDPR, India's DPDP Act, etc.) for consent, storage,
  and deletion if you extend this beyond local/personal use.

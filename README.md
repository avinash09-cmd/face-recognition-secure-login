<div align="center">

# 👤 FACESCAN

### Face Recognition-Based Secure Two-Factor Authentication

A complete, lightweight **two-factor authentication (2FA)** system that combines password authentication with **real-time face verification and motion-based liveness detection**.

Runs entirely locally — **no cloud APIs, third-party biometric services, or external face-recognition calls required.**

**Theme:** Cybersecurity / Computer Vision & Artificial Intelligence
**Category:** Software

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge\&logo=flask\&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-LBPH_%26_Haar-5C3EE8?style=for-the-badge\&logo=opencv\&logoColor=white)](https://opencv.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)](https://www.sqlite.org/)

</div>

---

## 📌 Overview

**Facescan** is a locally hosted two-factor authentication system designed to secure login workflows using:

1. **Username + password authentication**
2. **Real-time facial verification**
3. **Motion-based liveness detection**

The project combines classical computer vision techniques with web-based authentication to provide an offline biometric authentication workflow.

Faces are detected using **Haar Cascade classifiers**, recognized using **LBPH (Local Binary Patterns Histograms)**, and checked for basic liveness using **frame-to-frame motion analysis**.

The entire pipeline runs locally, allowing biometric processing without sending face data to external services.

---

## ✨ Features

### 🔐 Two-Factor Authentication

Facescan implements two authentication factors:

* **Factor 1 — Knowledge**

  * Username
  * Password
  * Salted password hashing
  * SQLite-based credential storage

* **Factor 2 — Biometrics**

  * Live webcam capture
  * Face detection
  * LBPH face recognition
  * Motion-based liveness verification

Users are granted access to the protected dashboard only after both authentication stages succeed.

---

### 🧬 Face Enrollment & Modeling

During registration, the application captures multiple face samples from the user's webcam.

* Captures **20 face samples** by default
* Converts samples to grayscale
* Detects and crops the face region
* Normalizes each face crop to **200 × 200 pixels**
* Stores samples locally
* Trains an LBPH face-recognition model

Example storage structure:

```text
face_data/
└── username/
    ├── 1.jpg
    ├── 2.jpg
    ├── 3.jpg
    └── ...
```

No external face-recognition API is required.

---

### 👁️ Motion-Based Liveness Verification

Facescan includes a basic motion-based liveness layer to reduce the effectiveness of simple static-photo attacks.

During verification:

1. The webcam captures a sequence of frames.
2. The detected face region is downsampled.
3. Consecutive frames are compared.
4. Pixel-level differences are calculated.
5. Motion is accumulated across the verification sequence.
6. Authentication succeeds only when sufficient face matching **and** motion criteria are satisfied.

This is designed primarily to detect simple static-photo or printed-photo replay attempts.

> **Important:** This is a lightweight liveness mechanism, not a production-grade anti-spoofing system. It is not designed to defend against advanced replay, deepfake, or 3D-mask attacks.

---

### 💻 Web Interface

The application provides a browser-based interface built with Flask, HTML, CSS, and JavaScript.

Features include:

* Landing page
* Registration page
* Password login
* Webcam face enrollment
* Live face verification
* Liveness feedback
* Protected dashboard
* Session-based authentication
* Dark-themed user interface

---

## 🛠️ Tech Stack

| Domain                   | Technologies                              |
| ------------------------ | ----------------------------------------- |
| **Programming Language** | Python 3.10+                              |
| **Backend**              | Flask                                     |
| **Database**             | SQLite                                    |
| **Computer Vision**      | OpenCV                                    |
| **Face Detection**       | Haar Cascade Classifier                   |
| **Face Recognition**     | LBPH Face Recognizer                      |
| **Frontend**             | HTML5, CSS3, JavaScript                   |
| **Camera API**           | Browser `getUserMedia()`                  |
| **Authentication**       | Password hashing + session authentication |

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │       User           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Flask Web App      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Step 1: Login        │
                    │ Username + Password  │
                    └──────────┬───────────┘
                               │
                        Password Valid?
                          /          \
                        No            Yes
                        │              │
                        ▼              ▼
                  Reject Login   Step 2: Camera
                                      │
                                      ▼
                           ┌────────────────────┐
                           │ getUserMedia()     │
                           │ Webcam Stream      │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ OpenCV Pipeline    │
                           └─────────┬──────────┘
                                     │
                         ┌───────────┴───────────┐
                         │                       │
                         ▼                       ▼
                ┌─────────────────┐     ┌─────────────────┐
                │ Haar Cascade    │     │ Motion Liveness │
                │ Face Detection  │     │ Frame Analysis  │
                └────────┬────────┘     └────────┬────────┘
                         │                       │
                         ▼                       ▼
                ┌─────────────────┐     ┌─────────────────┐
                │ LBPH Recognition│     │ Motion Score    │
                │ Match Check     │     │ Threshold       │
                └────────┬────────┘     └────────┬────────┘
                         │                       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ 2FA Criteria Met?  │
                           └─────────┬──────────┘
                                /          \
                              Yes           No
                               │             │
                               ▼             ▼
                     ┌───────────────┐  ┌──────────────┐
                     │ Grant Access  │  │ Reject /     │
                     │ Dashboard     │  │ Try Again    │
                     └───────────────┘  └──────────────┘
```

---

## 🔄 How It Works

### 1. User Registration

The user creates an account with:

```text
Username
Password
```

The password is hashed before being stored in the SQLite database.

---

### 2. Face Enrollment

After registration, the user enters the face enrollment process.

```text
Webcam
   ↓
Capture Frames
   ↓
Detect Face using Haar Cascade
   ↓
Crop Face
   ↓
Convert to Grayscale
   ↓
Resize to 200 × 200
   ↓
Store Samples
   ↓
Train LBPH Model
```

The default configuration captures:

```text
20 face samples per user
```

---

### 3. Password Authentication

During login, the user submits:

```text
Username + Password
```

The application verifies the password against the stored password hash.

If the password is incorrect:

```text
Login → Rejected
```

If the password is correct:

```text
Login → Continue to Face Verification
```

---

### 4. Face Verification

The browser requests access to the webcam using:

```javascript
navigator.mediaDevices.getUserMedia()
```

The camera stream is processed during the verification stage.

OpenCV performs:

```text
Webcam Frame
     ↓
Face Detection
     ↓
Grayscale Conversion
     ↓
Face Normalization
     ↓
LBPH Prediction
     ↓
Confidence Check
```

---

### 5. Liveness Verification

At the same time, Facescan compares consecutive frames.

```text
Frame 1
   ↓
Frame 2
   ↓
Calculate Difference
   ↓
Frame 3
   ↓
Calculate Difference
   ↓
...
   ↓
Motion Score
```

If the detected face remains completely static, the liveness requirement may fail.

Natural movements such as:

* Slight head movement
* Blinking
* Small posture changes
* Facial movement

can generate frame-to-frame differences.

---

### 6. Final Authentication

Both conditions must pass:

```text
Password ✓
     +
Face Match ✓
     +
Liveness ✓
     ↓
Access Granted
```

Otherwise:

```text
Authentication Failed
        ↓
Try Again
```

---

## 🔎 Key Biometric Components

### 1. Haar Cascade Face Detection

Facescan uses OpenCV's pre-trained Haar Cascade classifier:

```text
haarcascade_frontalface_default.xml
```

The classifier detects faces inside webcam frames.

The project also includes:

```text
haarcascade_eye.xml
```

for eye detection where required by the implementation.

---

### 2. LBPH Face Recognition

Face recognition is performed using:

```python
cv2.face.LBPHFaceRecognizer_create()
```

LBPH stands for:

**Local Binary Patterns Histograms**

The algorithm converts local facial texture information into histograms and uses these features to compare a captured face against the trained model.

The recognizer produces:

```text
Predicted User ID
+
Confidence / Distance Score
```

For LBPH, the score behaves like a distance measure:

```text
Lower score → More similar
Higher score → Less similar
```

---

### 3. Motion-Based Liveness

For liveness analysis, the detected face region is reduced to a small representation.

Default approach:

```text
Face Region
     ↓
Downsample
     ↓
16 × 16 representation
     ↓
Compare consecutive frames
     ↓
Calculate pixel difference
     ↓
Calculate motion score
```

This allows the application to detect whether meaningful movement occurred during the verification sequence.

---

## ⚙️ Configuration

Important biometric parameters can be configured near the top of `app.py`.

| Variable                    | Default | Description                                                 |
| --------------------------- | ------: | ----------------------------------------------------------- |
| `SAMPLES_PER_USER`          |    `20` | Number of face samples captured during enrollment           |
| `VERIFY_FRAMES_NEEDED`      |    `15` | Minimum number of successful matching verification frames   |
| `LBPH_CONFIDENCE_THRESHOLD` |    `75` | Maximum LBPH distance allowed for a match                   |
| `MOTION_DIFF_THRESHOLD`     |   `2.2` | Minimum average frame-to-frame motion required for liveness |

### Example

```python
SAMPLES_PER_USER = 20

VERIFY_FRAMES_NEEDED = 15

LBPH_CONFIDENCE_THRESHOLD = 75

MOTION_DIFF_THRESHOLD = 2.2
```

### Adjusting Strictness

Generally:

```text
Lower LBPH threshold
        ↓
Stricter face matching
```

and:

```text
Higher motion threshold
        ↓
Stricter liveness requirement
```

However, overly strict values can increase false rejections, especially under poor lighting or webcam conditions.

---

# 📂 Project Structure

```text
face_login/
│
├── app.py
│   └── Flask application, authentication,
│       database logic and computer vision pipeline
│
├── requirements.txt
│   └── Python dependencies
│
├── database.db
│   └── SQLite database
│
├── model.yml
│   └── Trained LBPH model
│
├── face_data/
│   └── User-specific face samples
│       └── <username>/
│
├── cascades/
│   ├── haarcascade_frontalface_default.xml
│   └── haarcascade_eye.xml
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── capture.html
│   └── dashboard.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── capture.js
```

---

# 🚀 Getting Started

## Prerequisites

Make sure the following are installed:

* Python 3.10 or newer
* Git
* A working webcam
* Modern web browser
* Windows, Linux, or macOS

Check Python:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/avinash09-cmd/facescan.git
```

Navigate into the project:

```bash
cd facescan
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

After activation, you should see something similar to:

```text
(venv)
```

at the beginning of your terminal prompt.

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `pip` does not work, try:

```bash
python -m pip install -r requirements.txt
```

---

## 4. Run the Application

```bash
python app.py
```

You should see Flask start the local development server.

Open your browser and visit:

```text
http://localhost:5000
```

---

# 🌐 Browser Camera Permissions

Facescan uses the browser's:

```javascript
navigator.mediaDevices.getUserMedia()
```

API to access the webcam.

Modern browsers generally require camera access to occur within a **secure context**.

For local development, this normally works through:

```text
http://localhost:5000
```

You must also allow camera permissions when the browser asks.

If camera access is blocked:

1. Check browser permissions.
2. Make sure another application is not exclusively using the webcam.
3. Try `localhost` instead of an external IP address.
4. Check that the browser has permission to access the camera.

---

# 🧪 Authentication Workflow

### New User

```text
Open Facescan
      ↓
Register
      ↓
Create Username + Password
      ↓
Enroll Face
      ↓
Capture 20 Face Samples
      ↓
Train LBPH Model
      ↓
Registration Complete
```

### Existing User

```text
Login
  ↓
Username + Password
  ↓
Password Verification
  ↓
Webcam Verification
  ↓
Face Detection
  ↓
LBPH Recognition
  ↓
Motion Liveness
  ↓
2FA Successful
  ↓
Protected Dashboard
```

---

# 📸 Screenshots

Add your application screenshots to a folder such as:

```text
screenshots/
├── landing.png
├── registration.png
├── face-enrollment.png
├── verification.png
└── dashboard.png
```

Then add them to this README:

### Landing Page

The main Facescan landing page introducing the local two-factor authentication system.

```markdown
![Landing Page](screenshots/landing.png)
```

### Registration

Username and password registration before face enrollment.

```markdown
![Registration](screenshots/registration.png)
```

### Face Enrollment

Webcam-based face sample collection.

```markdown
![Face Enrollment](screenshots/face-enrollment.png)
```

### Live Verification

Real-time face recognition and liveness verification.

```markdown
![Live Verification](screenshots/verification.png)
```

### Protected Dashboard

Dashboard accessible after successful two-factor authentication.

```markdown
![Dashboard](screenshots/dashboard.png)
```

---

# 🔐 Security Design

Facescan demonstrates several security concepts:

### Password Security

Passwords should never be stored as plaintext.

The application stores password hashes rather than raw passwords.

```text
Plain Password
      ↓
Hashing
      ↓
Stored Hash
```

---

### Session Protection

Flask sessions are used to control access to protected routes.

The dashboard should only become accessible after successful authentication.

```text
Unauthenticated User
        ↓
      Login
        ↓
   Verification
        ↓
Authenticated Session
        ↓
    Dashboard
```

---

### Local Biometric Processing

Face processing is performed locally.

```text
Webcam
  ↓
Local Machine
  ↓
OpenCV
  ↓
Face Recognition
```

No external face-recognition service is required.

---

# 🛡️ Threat Model

Facescan is designed as an educational security project demonstrating defenses against basic authentication and biometric replay scenarios.

| Threat                            | Mitigation             |
| --------------------------------- | ---------------------- |
| Incorrect password                | Password verification  |
| Unauthorized dashboard access     | Session authentication |
| Unknown face                      | LBPH face matching     |
| Static photograph                 | Motion-based liveness  |
| Printed face                      | Motion-based liveness  |
| External biometric API dependency | Local processing       |
| Plaintext passwords               | Password hashing       |

---

# ⚠️ Limitations

## Classical LBPH Recognition

LBPH is lightweight and suitable for local experimentation, but it can be affected by:

* Lighting changes
* Camera quality
* Facial angle
* Facial expressions
* Occlusion
* Distance from camera

Modern deep-learning approaches such as FaceNet or ArcFace can provide more robust face representations in many environments.

---

## Basic Liveness Detection

The current motion-based liveness mechanism is intentionally lightweight.

It can help detect:

```text
Static Photograph
Printed Photograph
Completely Static Face
```

However, it is **not a complete presentation-attack detection system**.

It should not be considered sufficient against:

```text
Video Replay
Deepfake Replay
3D Face Masks
Sophisticated Presentation Attacks
Advanced Spoofing
```

---

## Biometric Data Storage

Face samples are stored locally under:

```text
face_data/
```

These files contain biometric information and should be protected appropriately.

For a real-world deployment, consider:

* Encryption at rest
* Strict filesystem permissions
* Secure deletion
* Access control
* Data retention policies
* Consent mechanisms
* Privacy requirements
* Applicable biometric/data-protection regulations

The current project is primarily intended for **educational, research, and demonstration purposes**.

---

# 🔮 Future Improvements

Potential improvements include:

* [ ] Deep-learning face embeddings
* [ ] ArcFace / FaceNet integration
* [ ] Stronger anti-spoofing models
* [ ] Blink-based challenge-response
* [ ] Randomized head-movement challenges
* [ ] Encrypted biometric storage
* [ ] Database-backed user management
* [ ] Role-based access control
* [ ] Account lockout after repeated failures
* [ ] Rate limiting
* [ ] Audit logging
* [ ] Email/SMS/Authenticator-based third factor
* [ ] Docker deployment
* [ ] HTTPS configuration
* [ ] Automated security testing
* [ ] Unit and integration tests

---

# 📊 Project Highlights

| Component              | Implementation          |
| ---------------------- | ----------------------- |
| Authentication         | Username + Password     |
| Second Factor          | Face Verification       |
| Face Detection         | Haar Cascade            |
| Face Recognition       | LBPH                    |
| Liveness               | Frame Difference        |
| Database               | SQLite                  |
| Backend                | Flask                   |
| Frontend               | HTML + CSS + JavaScript |
| Camera                 | Browser Webcam API      |
| Deployment             | Local / Offline         |
| External Biometric API | Not Required            |

---

# 🎯 Learning Outcomes

This project demonstrates practical concepts in:

### Cybersecurity

* Authentication
* Two-factor authentication
* Password security
* Session management
* Biometric security
* Spoofing considerations
* Threat modeling

### Computer Vision

* Face detection
* Image preprocessing
* Grayscale conversion
* Image normalization
* Histogram-based face recognition
* Frame comparison
* Motion analysis

### Web Development

* Flask routing
* HTML templates
* JavaScript
* Browser camera APIs
* Client-server communication
* Session-based access control

### Database

* SQLite
* User records
* Authentication data
* Local persistence

---

# 📚 Technologies Explained

### Flask

Python web framework used to build the application's backend and HTTP routes.

### OpenCV

Computer vision library used for:

* Face detection
* Image processing
* Face recognition
* Motion analysis

### Haar Cascade

A classical computer-vision method used to detect objects such as faces in images.

### LBPH

A lightweight face-recognition algorithm based on local texture patterns and histograms.

### SQLite

A lightweight file-based relational database used to store application data locally.

### `getUserMedia()`

A browser Web API that allows web applications to request access to devices such as webcams.

---

# 🔧 Troubleshooting

## Camera Not Opening

Check:

```text
Browser camera permission
        ↓
Webcam connection
        ↓
Other applications using webcam
        ↓
Browser support
```

Try restarting the browser and running:

```bash
python app.py
```

again.

---

## OpenCV `cv2.face` Not Found

If this error appears:

```text
AttributeError: module 'cv2' has no attribute 'face'
```

install the contrib package:

```bash
pip install opencv-contrib-python
```

You may also need to remove conflicting OpenCV installations before reinstalling:

```bash
pip uninstall opencv-python opencv-contrib-python
```

Then:

```bash
pip install opencv-contrib-python
```

---

## Port Already in Use

If port `5000` is already occupied, change the Flask port in `app.py`.

For example:

```python
app.run(debug=True, port=5001)
```

Then open:

```text
http://localhost:5001
```

---

# ⚖️ Disclaimer

Facescan is an **educational cybersecurity and computer-vision project**.

It demonstrates the implementation of password authentication, face recognition, and basic liveness verification in a local environment.

It should **not be considered a production-ready biometric authentication system** without additional security engineering, privacy controls, robust anti-spoofing mechanisms, testing, and compliance review.

---

# 👨‍💻 Author

**Avinash Kumar Singh**

B.Tech — Computer Science Engineering
Cyber Security & Digital Forensics

### GitHub

[@avinash09-cmd](https://github.com/avinash09-cmd)

### Project Repository

[github.com/avinash09-cmd/facescan](https://github.com/avinash09-cmd/facescan)

---

<div align="center">

### ⭐ If you found Facescan useful, consider giving the repository a star!

**Built with Python, Flask & OpenCV**

</div>

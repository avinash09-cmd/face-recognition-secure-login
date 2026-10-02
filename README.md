<div align="center">

# 👤 FACESCAN

### Face Recognition-Based Secure Two-Factor Authentication

A complete, lightweight two-factor login system combining password authentication with live face verification. Runs entirely locally—no cloud APIs, third-party services, or external face-recognition network calls required.

**Theme:** Cybersecurity / Computer Vision & Artificial Intelligence · **Category:** Software

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-LBPH_&_Haar-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

</div>

---

## 📌 Overview

**Facescan** is a local two-factor authentication (2FA) system designed to protect login workflows using password credentials alongside real-time biometric face verification. 

By combining classical face detection (**Haar Cascades**), histogram-based face recognition (**LBPH**), and **motion-based frame-to-frame liveness verification**, Facescan prevents naive static-photo replay attacks while eliminating third-party biometrics or cloud latency.

---

## ✨ Features

### 🔐 Two-Factor Authentication (2FA)
- **Factor 1 (Knowledge):** Standard username + salted password verification.
- **Factor 2 (Biometric):** Real-time webcam face capture, liveness check, and LBPH histogram matching.

### 🧬 Face Enrollment & Modeling
- **Local Sampling:** Captures 20 normalized (200×200) grayscale face samples per user upon enrollment.
- **On-Device Training:** Trains a personal Local Binary Patterns Histogram (LBPH) model locally without sending biometric data externally.

### 👁 Motion-Based Liveness Verification
- **Anti-Spoofing Protection:** Computes downsampled frame-to-frame motion differences (micro-movements, blinks, natural posture drift) across a ~24-frame verification window.
- **Photo Attack Defense:** Automatically rejects static photos or printed paper attacks if natural motion thresholds are not met.

### 💻 Clean UI & Protected Dashboard
- **Webcam Interface:** Built-in `getUserMedia` stream handling with visual frame indicators.
- **Secure Sessions:** Access to protected routes (dashboard) is restricted until both factors pass verification.

---

## 🛠 Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend & Web Framework** | Python 3.10+, Flask, SQLite |
| **Computer Vision & Biometrics** | OpenCV (`opencv-python`, `opencv-contrib-python`), Haar Cascades, LBPH |
| **Frontend UI** | HTML5 (`getUserMedia` Web API), CSS3 (Custom Design System), JavaScript |

---

## 📂 Project Structure

```text
face_login/
├── app.py                  # Flask web application, database, and vision pipeline
├── requirements.txt        # Python dependencies
├── database.db             # Local SQLite database (auto-generated on first run)
├── model.yml               # Trained LBPH model weights (generated after enrollment)
├── face_data/              # User-specific cropped 200x200 grayscale sample storage
│   └── <username>/
├── templates/
│   ├── base.html           # Shared navigation layout and styling scaffolding
│   ├── index.html          # Landing / overview page
│   ├── register.html       # Step 1: Account registration form
│   ├── login.html          # Step 1: Password sign-in form
│   ├── capture.html        # Step 2: Shared webcam capture interface (Enroll/Verify)
│   └── dashboard.html      # Protected area after successful 2FA
└── static/
    ├── css/style.css       # Custom UI layout and dark-mode styling
    └── js/capture.js       # Camera streaming, frame loops, and API communication

🔎 How It Works
+------------------+
  |  Step 1: Login   | ---> Verify Username & Password (Factor 1)
  +--------+---------+
           |
           v
  +------------------+
  |  Step 2: Camera  | ---> Request getUserMedia Web Stream
  +--------+---------+
           |
           v
  +------------------+
  |  OpenCV Pipeline | ---> Haar Cascade Face Detection
  +--------+---------+
           |
           +-----------------------+
           |                       |
           v                       v
  +------------------+   +-------------------+
  | LBPH Predictor   |   | Motion Liveness   |
  | (Match Check)    |   | (Frame Diff Check)|
  +--------+---------+   +---------+---------+
           |                       |
           +-----------+-----------+
                       |
                       v
            [ Pass 2FA Criteria? ]
             /                  \
          (Yes)                 (No)
           /                      \
          v                        v
  +---------------+        +---------------+
  | Grant Access  |        | Reject Access |
  | (Dashboard)   |        |  (Try Again)  |
  +---------------+        +---------------+

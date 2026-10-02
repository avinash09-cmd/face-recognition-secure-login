(function () {
  const cfg = window.CAPTURE_CONFIG;
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const statusChip = document.getElementById("statusChip");
  const progressFill = document.getElementById("progressFill");
  const progressLabel = document.getElementById("progressLabel");
  const resultBox = document.getElementById("resultBox");
  const cancelBtn = document.getElementById("cancelBtn");
  const sweep = document.getElementById("sweep");

  let stream = null;
  let capturing = false;
  let framesSent = 0;
  const CAPTURE_INTERVAL_MS = 350;

  function setStatus(text) {
    statusChip.textContent = text;
  }

  function showResult(kind, message) {
    resultBox.hidden = false;
    resultBox.className = "alert alert--" + kind;
    resultBox.textContent = message;
  }

  function updateProgress(count, total) {
    const pct = Math.min(100, Math.round((count / total) * 100));
    progressFill.style.width = pct + "%";
    progressLabel.textContent = count + " / " + total + " frames";
  }

  async function initCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 480, height: 480, facingMode: "user" },
        audio: false,
      });
      video.srcObject = stream;
      setStatus(cfg.mode === "enroll" ? "Hold steady\u2026" : "Look at camera, stay natural\u2026");
      video.addEventListener("loadedmetadata", () => {
        setTimeout(startCaptureLoop, 800); // brief warm-up so autofocus settles
      });
    } catch (err) {
      setStatus("Camera unavailable");
      showResult("error", "Could not access your camera: " + err.message +
        ". Check browser permissions and that you're on http://localhost or https.");
    }
  }

  function grabFrameAsDataUrl() {
    const size = 320;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    // undo the mirrored preview so the saved frame is "true" orientation
    ctx.translate(size, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, size, size);
    return canvas.toDataURL("image/jpeg", 0.85);
  }

  async function startCaptureLoop() {
    capturing = true;
    loop();
  }

  async function loop() {
    if (!capturing) return;
    const dataUrl = grabFrameAsDataUrl();

    try {
      if (cfg.mode === "enroll") {
        await sendEnrollFrame(dataUrl);
      } else {
        await sendVerifyFrame(dataUrl);
      }
    } catch (e) {
      setStatus("Network error \u2014 retrying\u2026");
    }

    if (capturing) {
      setTimeout(loop, CAPTURE_INTERVAL_MS);
    }
  }

  async function sendEnrollFrame(dataUrl) {
    const res = await fetch(cfg.enrollFrameUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    const data = await res.json();

    if (!data.ok) {
      setStatus(data.message || "No face detected");
      return;
    }

    if (data.count !== undefined) {
      updateProgress(data.count, cfg.samplesNeeded);
      setStatus("Captured sample " + data.count + " / " + cfg.samplesNeeded);
    }

    if (data.done) {
      capturing = false;
      setStatus("Training model\u2026");
      stopStream();
      const finishRes = await fetch(cfg.finishEnrollUrl, { method: "POST" });
      const finishData = await finishRes.json();
      if (finishData.ok) {
        showResult("success", "Enrollment complete. Redirecting to sign in\u2026");
        setTimeout(() => (window.location.href = finishData.redirect || cfg.loginUrl), 1200);
      } else {
        showResult("error", finishData.message || "Enrollment failed. Please try again.");
      }
    }
  }

  async function sendVerifyFrame(dataUrl) {
    const res = await fetch(cfg.verifyFrameUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    const data = await res.json();

    if (!data.ok) {
      showResult("error", data.message || "Verification error.");
      capturing = false;
      stopStream();
      return;
    }

    updateProgress(data.frames || 0, cfg.samplesNeeded);
    setStatus(data.face_detected ? "Face locked \u2014 keep looking at camera" : "Center your face in frame");

    if (data.done) {
      capturing = false;
      stopStream();
      if (data.success) {
        showResult("success", data.message || "Access granted.");
        setTimeout(() => (window.location.href = data.redirect || "/dashboard"), 900);
      } else {
        const kind = data.reason === "liveness" ? "warn" : "error";
        showResult(kind, data.message || "Verification failed.");
      }
    }
  }

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
    }
  }

  cancelBtn.addEventListener("click", async () => {
    capturing = false;
    stopStream();
    try {
      await fetch(cfg.cancelUrl, { method: "POST" });
    } catch (e) {
      /* ignore */
    }
    window.location.href = cfg.indexUrl;
  });

  window.addEventListener("beforeunload", stopStream);

  initCamera();
})();

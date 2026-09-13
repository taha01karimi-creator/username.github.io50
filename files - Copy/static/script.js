const urlInput = document.getElementById("url-input");
const videoBtn = document.getElementById("video-btn");
const audioBtn = document.getElementById("audio-btn");
const resultBox = document.getElementById("result-box");
const errorBox = document.getElementById("error-box");

function setLoading(btn, isLoading) {
  const spinner = btn.querySelector(".spinner");
  const text = btn.querySelector(".btn-text");
  btn.disabled = isLoading;
  spinner.classList.toggle("hidden", !isLoading);
  text.style.opacity = isLoading ? "0.6" : "1";
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideBoxes() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
  resultBox.classList.add("hidden");
  resultBox.innerHTML = "";
}

function formatDuration(seconds) {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

async function handleDownload(kind, btn) {
  const url = urlInput.value.trim();
  hideBoxes();

  if (!url) {
    showError("لطفاً یک لینک اینستاگرام وارد کن.");
    return;
  }

  setLoading(btn, true);
  try {
    const endpoint = kind === "audio" ? "/api/download-audio" : "/api/download-video";
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || "خطای ناشناخته");
    }

    let html = "";
    if (data.thumbnail) {
      html += `<img src="${data.thumbnail}" alt="thumbnail" />`;
    }
    html += `<p class="result-title">${data.title || (kind === "audio" ? "آهنگ آماده شد" : "ویدیو آماده شد")}</p>`;
    if (data.duration) {
      html += `<p class="result-sub">مدت زمان: ${formatDuration(data.duration)}</p>`;
    }
    const label = kind === "audio" ? "⬇️ دانلود آهنگ (MP3)" : "⬇️ دانلود ویدیو (MP4)";
    html += `<a class="download-link" href="${data.download_url}" download>${label}</a>`;

    resultBox.innerHTML = html;
    resultBox.classList.remove("hidden");
  } catch (err) {
    showError(err.message || "دانلود ناموفق بود.");
  } finally {
    setLoading(btn, false);
  }
}

videoBtn.addEventListener("click", () => handleDownload("video", videoBtn));
audioBtn.addEventListener("click", () => handleDownload("audio", audioBtn));

urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleDownload("video", videoBtn);
});

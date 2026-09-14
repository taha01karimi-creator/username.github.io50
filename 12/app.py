import os
import re
import uuid
from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# فایل کوکی اینستاگرام. اگر وجود نداشته باشد، دانلود با پیام روشن رد می‌شود
# (به‌جای تلاش ناموفق برای خواندن مستقیم از مرورگر که باعث قفل‌شدن می‌شد).
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

INSTAGRAM_URL_RE = re.compile(r"(instagram\.com|instagr\.am)", re.IGNORECASE)


def build_ydl_opts(outtmpl, audio_only):
    opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    if os.path.isfile(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE

    if audio_only:
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })

    return opts


def cleanup_old_files(max_files=50):
    """جلوگیری از پر شدن دیسک با پاک کردن قدیمی‌ترین فایل‌ها"""
    try:
        files = sorted(
            (os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)),
            key=os.path.getmtime,
        )
        while len(files) > max_files:
            os.remove(files.pop(0))
    except Exception:
        pass


def run_download(url, audio_only):
    """دانلود واقعی را انجام می‌دهد. خروجی: (نتیجه، پیام خطا)"""
    if not url:
        return None, "لینک ارسال نشده است."

    if not INSTAGRAM_URL_RE.search(url):
        return None, "فقط لینک‌های اینستاگرام (instagram.com) پشتیبانی می‌شوند."

    if not os.path.isfile(COOKIES_FILE):
        return None, (
            "فایل cookies.txt پیدا نشد. طبق راهنمای README یک بار کوکی حساب "
            "اینستاگرامتان را اکسپورت کرده و کنار app.py با نام cookies.txt "
            "قرار دهید، وگرنه اینستاگرام درخواست را رد می‌کند."
        )

    file_id = str(uuid.uuid4())
    kind = "audio" if audio_only else "video"
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}_{kind}.%(ext)s")
    ydl_opts = build_ydl_opts(outtmpl, audio_only)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = os.path.splitext(filename)[0] + ".mp3"
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        low = msg.lower()
        if "login" in low or "rate-limit" in low or "not available" in low:
            return None, (
                "اینستاگرام دسترسی را رد کرد. احتمالاً کوکی‌های شما منقضی "
                "شده‌اند؛ یک بار دیگر cookies.txt را از مرورگری که لاگین "
                "اینستاگرام هستید بگیرید و جایگزین کنید."
            )
        if "cookie" in low:
            return None, "خواندن فایل کوکی با مشکل مواجه شد. cookies.txt را دوباره اکسپورت کنید."
        return None, f"خطا در دانلود: {msg}"
    except Exception as e:
        return None, f"خطای غیرمنتظره: {str(e)}"

    if not filename or not os.path.isfile(filename):
        return None, "فایل خروجی ساخته نشد. دوباره امتحان کنید."

    cleanup_old_files()

    return {
        "download_url": f"/api/file/{os.path.basename(filename)}",
        "title": info.get("title") or "",
        "thumbnail": info.get("thumbnail") or "",
        "duration": info.get("duration"),
    }, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/download-video", methods=["POST"])
def download_video():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    result, error = run_download(url, audio_only=False)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"success": True, **result})


@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    result, error = run_download(url, audio_only=True)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"success": True, **result})


@app.route("/api/file/<path:filename>")
def get_file(filename):
    # جلوگیری از path traversal
    safe_name = os.path.basename(filename)
    path = os.path.join(DOWNLOAD_DIR, safe_name)
    if not os.path.isfile(path):
        return jsonify({"error": "فایل یافت نشد"}), 404

    # نوع درست فایل کمک می‌کند گوشی‌ها آن را دسته‌بندی کنند
    # (ویدیو در گالری، صدا در موزیک) — این رفتار خودِ سیستم‌عامل/مرورگر است.
    mimetype = "audio/mpeg" if safe_name.lower().endswith(".mp3") else "video/mp4"
    return send_file(path, as_attachment=True, mimetype=mimetype)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=port)

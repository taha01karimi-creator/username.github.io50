
import os
import sys

try:
    import yt_dlp
except ImportError:
    print("کتابخانه yt-dlp نصب نیست.")
    print("لطفاً ابتدا با دستور زیر آن را نصب کنید:")
    print("    pip install yt-dlp")
    sys.exit(1)


# مسیر پوشه‌ی مقصد برای ذخیره ویدیوها
DOWNLOAD_FOLDER = r"D:\TiTi"


def ensure_folder_exists(folder_path: str) -> None:
    """اگر پوشه‌ی مقصد وجود نداشت، آن را می‌سازد."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"پوشه‌ی '{folder_path}' ساخته شد.")
    else:
        print(f"پوشه‌ی '{folder_path}' از قبل وجود دارد.")


def download_instagram_video(url: str, folder_path: str) -> None:
    """ویدیوی اینستاگرام را با استفاده از yt-dlp دانلود می‌کند."""

    # الگوی نام‌گذاری فایل خروجی: عنوان ویدیو + پسوند فایل
    output_template = os.path.join(folder_path, "%(title).100s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/best",
        "quiet": False,
        "noplaylist": True,
    }

    print("در حال دانلود ویدیو... لطفاً صبر کنید.")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("دانلود با موفقیت انجام شد.")
        print(f"فایل در مسیر '{folder_path}' ذخیره شد.")
    except Exception as e:
        print("خطا در دانلود ویدیو:")
        print(str(e))
        print(
            "\nنکته: اگر پست/ریلز خصوصی باشد یا نیاز به لاگین داشته باشد، "
            "دانلود ممکن است ناموفق باشد."
        )


def main():
    print("=== دانلود ویدیوی اینستاگرام ===")
    url = input("لینک ویدیوی اینستاگرام را وارد کنید: ").strip()

    if not url:
        print("لینکی وارد نشده است. برنامه پایان یافت.")
        return

    ensure_folder_exists(DOWNLOAD_FOLDER)
    download_instagram_video(url, DOWNLOAD_FOLDER)


if __name__ == "__main__":
    main()

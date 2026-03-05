import os
import shutil
import hashlib
import argparse
from datetime import datetime

# ---------- CONFIG ----------
EXTENSION_MAP = {
    "code": ["py", "sh", "js", "cpp", "c"],
    "documents": ["pdf", "txt"],
    "word_docs": ["doc", "docx"],
    "images": ["jpg", "jpeg", "png", "gif"],
    "audio": ["mp3", "wav"],
    "video": ["mp4", "avi", "mkv"],
    "disk_images": ["iso"]
}
# ----------------------------


def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def get_file_hash(filepath):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, OSError):
        return None


def get_category(extension):
    for category, extensions in EXTENSION_MAP.items():
        if extension in extensions:
            return category
    return "other"


def is_hidden(filepath):
    return os.path.basename(filepath).startswith(".")


def organize_files(dry_run=False, sort_by_date=True, large_file_mb=None):
    base_dir = get_downloads_folder()
    seen_hashes = {}

    print(f"\nOrganizing: {base_dir}\n")

    organized_folders = set(list(EXTENSION_MAP.keys()) + ["other", "large_files"])

    for root, dirs, files in os.walk(base_dir):

        # 🔥 Prevent walking into organized folders
        dirs[:] = [d for d in dirs if d not in organized_folders]

        for file in files:
            full_path = os.path.join(root, file)

            if is_hidden(full_path):
                continue

            extension = file.split(".")[-1].lower()
            category = get_category(extension)

            # Large file detection
            if large_file_mb:
                try:
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    if size_mb >= large_file_mb:
                        category = "large_files"
                except OSError:
                    continue

            # Date sorting
            if sort_by_date:
                try:
                    mod_time = os.path.getmtime(full_path)
                    date = datetime.fromtimestamp(mod_time)
                    destination = os.path.join(
                        base_dir,
                        category,
                        str(date.year),
                        f"{date.month:02d}"
                    )
                except OSError:
                    continue
            else:
                destination = os.path.join(base_dir, category)

            os.makedirs(destination, exist_ok=True)

            file_hash = get_file_hash(full_path)
            if file_hash is None:
                continue

            if file_hash in seen_hashes:
                print(f"[DUPLICATE] Skipping {file}")
                continue

            seen_hashes[file_hash] = full_path

            target_path = os.path.join(destination, file)

            if os.path.abspath(full_path) == os.path.abspath(target_path):
                continue

            if dry_run:
                print(f"[DRY RUN] {full_path} → {target_path}")
            else:
                try:
                    shutil.move(full_path, target_path)
                    print(f"[MOVED] {file}")
                except Exception as e:
                    print(f"[ERROR] {file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Downloads Organizer")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-date", action="store_true")
    parser.add_argument("--large", type=int)

    args = parser.parse_args()

    organize_files(
        dry_run=args.dry_run,
        sort_by_date=not args.no_date,
        large_file_mb=args.large
    )
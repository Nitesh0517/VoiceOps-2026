"""Package the VoiceOps 2026 capstone submission ZIP according to the official brief."""
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "env", "node_modules"}
EXCLUDE_FILES = {".env", "zentromart.db", "zentromart.db-wal", "zentromart.db-shm", ".DS_Store", "Thumbs.db"}


def package_submission(output_filename: str = "voiceops_submission.zip"):
    out_path = ROOT / output_filename
    print(f"Building submission ZIP: {out_path} ...")
    
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Essential root files
        for fname in ["README.md", ".env.example", "requirements.txt", "run.py", "report.pdf", "SETUP_GUIDE.md", "streamlit_app.py"]:
            fpath = ROOT / fname
            if fpath.exists():
                print(f"  Adding file: {fname}")
                zf.write(fpath, arcname=fname)
            else:
                print(f"  [Warning] Missing: {fname}")

        # 2. Source code (app/, frontend/, sample_outputs/)
        for folder in ["app", "frontend", "sample_outputs"]:
            folder_path = ROOT / folder
            if folder_path.exists():
                for root, dirs, files in os.walk(folder_path):
                    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                    for file in files:
                        if file in EXCLUDE_FILES or file.endswith(".pyc"):
                            continue
                        if file.startswith(".env") and file != ".env.example":
                            continue
                        full_p = Path(root) / file
                        arcname = full_p.relative_to(ROOT)
                        zf.write(full_p, arcname=str(arcname))
                print(f"  Added directory: {folder}/")

        # 3. Optional demo video if present
        demo_mp4 = ROOT / "demo.mp4"
        if demo_mp4.exists():
            print("  Adding demo video: demo.mp4")
            zf.write(demo_mp4, arcname="demo.mp4")
        else:
            print("  [Info] demo.mp4 not found. Remember to record and place demo.mp4 before final portal upload.")

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\nSubmission ZIP created successfully: {output_filename} ({size_mb:.2f} MB)")
    return out_path


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "voiceops_submission.zip"
    package_submission(name)

"""
run.py — one-click launcher for the website.

Double-click this file, or type:   python run.py

It does three things:
  1. checks that your Python is new enough (3.10 or later),
  2. installs the libraries listed in requirements.txt (only when they are missing),
  3. starts the website, which opens in your browser at http://localhost:8501

Press Ctrl+C in this window to stop the website.
"""

import subprocess
import sys
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEEDED = {"streamlit": (1, 64), "pandas": (2, 0), "numpy": (1, 26), "matplotlib": (3, 8)}


def version_tuple(text):
    """'1.64.0' -> (1, 64). Only the first two numbers matter here."""
    parts = []
    for piece in text.split(".")[:2]:
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


def missing_libraries():
    """Names of libraries that are not installed, or are too old."""
    missing = []
    for name, minimum in NEEDED.items():
        try:
            if version_tuple(metadata.version(name)) < minimum:
                missing.append(name)
        except metadata.PackageNotFoundError:
            missing.append(name)
    return missing


def pause(message):
    print(message)
    try:
        input("Press Enter to close this window... ")
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    if sys.version_info < (3, 10):
        pause(f"This project needs Python 3.10 or newer. You have {sys.version.split()[0]}.\n"
              "Download the latest Python from https://www.python.org/downloads/")
        return

    missing = missing_libraries()
    if missing:
        print(f"Installing: {', '.join(missing)} (first time only, this can take a few minutes)...")
        command = [sys.executable, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")]
        if subprocess.call(command) != 0:
            print("Trying again for this user only...")
            if subprocess.call(command + ["--user"]) != 0:
                pause("Installing failed. Check your internet connection and try again.")
                return

    print("\nStarting Biomolecule Toxicity Detective...")
    print("Your browser will open at http://localhost:8501  (press Ctrl+C here to stop)\n")
    try:
        subprocess.call([sys.executable, "-m", "streamlit", "run", str(HERE / "app.py")], cwd=HERE)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

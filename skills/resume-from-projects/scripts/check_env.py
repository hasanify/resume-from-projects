#!/usr/bin/env python3
"""Check that everything the resume skill needs is installed.

Usage: python3 check_env.py [--install]

Prints one line per requirement and exits 1 if a required item is missing.
With --install it pip-installs missing Python packages and runs install_libreoffice.py
if LibreOffice is missing.
It never touches the project directory.
"""
import importlib
import os
import shutil
import subprocess
import subprocess as sp
import sys

PY_PACKAGES = {"docx": "python-docx", "pypdf": "pypdf", "pdfplumber": "pdfplumber"}


def have_font(*names):
    if not shutil.which("fc-list"):
        return None
    out = sp.run(["fc-list"], capture_output=True, text=True).stdout.lower()
    return any(n.lower() in out for n in names)


def main():
    install = "--install" in sys.argv
    ok = True

    print(f"python      {sys.version.split()[0]}")
    if sys.version_info < (3, 8):
        print("  ERROR: Python 3.8 or newer is required")
        ok = False

    for mod, pkg in PY_PACKAGES.items():
        try:
            importlib.import_module(mod)
            print(f"{pkg:<11} ok")
        except ImportError:
            if install:
                print(f"{pkg:<11} missing, installing...")
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                    capture_output=True, text=True)
                if r.returncode != 0:
                    r = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--quiet",
                         "--break-system-packages", pkg],
                        capture_output=True, text=True)
                if r.returncode == 0:
                    print(f"{pkg:<11} installed")
                    continue
            print(f"{pkg:<11} MISSING  -> pip install {pkg}")
            if mod != "pdfplumber":  # pdfplumber only powers optional checks
                ok = False

    git = shutil.which("git")
    print(f"git         {'ok' if git else 'missing (git history checks will be skipped)'}")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import install_libreoffice as il
    office = il.find_soffice()
    if not office and install:
        print("libreoffice missing, installing (this can take a few minutes)...")
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "install_libreoffice.py")])
        office = il.find_soffice()
    if office:
        print(f"libreoffice ok ({office})")
    else:
        print("libreoffice MISSING -> needed for docx to pdf. Run "
              "`python3 scripts/install_libreoffice.py` (or check_env.py --install), "
              "or open the .docx in Word and export a PDF yourself.")
        ok = False

    try:
        importlib.import_module("pypdfium2")
        print("pypdfium2   ok (PNG preview)")
    except ImportError:
        if shutil.which("pdftoppm"):
            print("pdftoppm    ok (PNG preview)")
        elif install:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pypdfium2"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                                    "--break-system-packages", "pypdfium2"], capture_output=True, text=True)
            print("pypdfium2   installed (PNG preview)" if r.returncode == 0 else
                  "pypdfium2   could not install; PNG preview unavailable")
            ok = ok and r.returncode == 0
        else:
            print("preview     MISSING -> pip install pypdfium2 (or install poppler) "
                  "to render the PDF to an image for visual checks")
            ok = False

    calibri = have_font("calibri")
    carlito = have_font("carlito")
    if calibri is None:
        print("fonts       cannot check (fc-list not found)")
    elif calibri or carlito:
        print(f"fonts       ok ({'Calibri' if calibri else 'Carlito, metric-compatible with Calibri'})")
    else:
        print("fonts       WARNING: neither Calibri nor Carlito installed. "
              "The PDF will use a different font and line breaks may shift. "
              "Install fonts-crosextra-carlito, or build with --font Arial.")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

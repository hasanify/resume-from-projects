#!/usr/bin/env python3
"""Install LibreOffice (and the Carlito font) when they are missing.

LibreOffice converts the .docx to PDF, so the PDF matches the Word file exactly.

Usage:
  install_libreoffice.py              install if missing, then verify
  install_libreoffice.py --check      only report whether it is installed (exit 0 or 1)
  install_libreoffice.py --dry-run    print the commands that would run, change nothing
  install_libreoffice.py --force      run the install even if LibreOffice is already present

Uses only the system package manager with fixed package names. It never downloads and
runs scripts, and it never touches the user's project directory.
  Linux    apt-get, dnf, yum, pacman, zypper or apk (root, or `sudo -n` without a password prompt)
  macOS    Homebrew cask (Homebrew itself is not installed for you)
  Windows  winget, then Chocolatey

Exit codes: 0 installed or already present, 1 not installed (--check only),
            5 needs a manual step (the exact command is printed),
            6 install ran but failed, 7 no supported package manager.
The last line printed is a JSON summary.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

WIN_PATHS = [r"C:\Program Files\LibreOffice\program\soffice.exe",
             r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]
MAC_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
DOWNLOAD = "https://www.libreoffice.org/download/download-libreoffice/"


def find_soffice():
    for n in ("soffice", "libreoffice"):
        p = shutil.which(n)
        if p:
            return p
    for p in [MAC_PATH, *WIN_PATHS]:
        if os.path.exists(p):
            return p
    return None


def works(so):
    try:
        r = subprocess.run([so, "--version"], capture_output=True, text=True, timeout=120)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)


def have_carlito_or_calibri():
    if not shutil.which("fc-list"):
        return None
    out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout.lower()
    return "carlito" in out or "calibri" in out


def priv_prefix():
    """Command prefix for admin rights: [] if root, ['sudo','-n'] if sudo exists, None if neither."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return []
    if shutil.which("sudo"):
        return ["sudo", "-n"]
    return None


def plan():
    """Return (name, steps). A step is (command list, required, needs_admin)."""
    sysname = platform.system()
    if sysname == "Linux":
        if shutil.which("apt-get"):
            return "apt", [
                (["apt-get", "update"], False, True),
                (["apt-get", "install", "-y", "--no-install-recommends", "libreoffice-writer"], True, True),
                (["apt-get", "install", "-y", "--no-install-recommends", "fonts-crosextra-carlito"], False, True),
            ]
        if shutil.which("dnf") or shutil.which("yum"):
            pm = "dnf" if shutil.which("dnf") else "yum"
            return pm, [
                ([pm, "install", "-y", "libreoffice-writer"], True, True),
                ([pm, "install", "-y", "google-crosextra-carlito-fonts"], False, True),
            ]
        if shutil.which("pacman"):
            return "pacman", [
                (["pacman", "-S", "--noconfirm", "--needed", "libreoffice-fresh"], True, True),
                (["pacman", "-S", "--noconfirm", "--needed", "ttf-carlito"], False, True),
            ]
        if shutil.which("zypper"):
            return "zypper", [
                (["zypper", "--non-interactive", "install", "libreoffice-writer"], True, True),
                (["zypper", "--non-interactive", "install", "google-carlito-fonts"], False, True),
            ]
        if shutil.which("apk"):
            return "apk", [
                (["apk", "add", "--no-cache", "libreoffice-writer"], True, True),
                (["apk", "add", "--no-cache", "font-carlito"], False, True),
            ]
        return None, []
    if sysname == "Darwin":
        if shutil.which("brew"):
            return "brew", [
                (["brew", "install", "--cask", "libreoffice"], True, False),
                (["brew", "install", "--cask", "font-carlito"], False, False),
            ]
        return None, []
    if sysname == "Windows":
        if shutil.which("winget"):
            return "winget", [
                (["winget", "install", "--id", "TheDocumentFoundation.LibreOffice", "-e", "--silent",
                  "--accept-package-agreements", "--accept-source-agreements"], True, False),
            ]
        if shutil.which("choco"):
            return "choco", [(["choco", "install", "libreoffice-fresh", "-y"], True, False)]
        return None, []
    return None, []


def result(code, **kw):
    kw["exit"] = code
    print(json.dumps(kw))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    so = find_soffice()
    if a.check:
        if so:
            ok, ver = works(so)
            print(f"LibreOffice found: {so} ({ver})")
            result(0 if ok else 1, installed=True, path=so, working=ok)
        print("LibreOffice not found")
        result(1, installed=False)
    if so and not a.force:
        ok, ver = works(so)
        print(f"LibreOffice already installed: {so} ({ver})")
        result(0, installed=True, path=so, already=True, working=ok)

    name, steps = plan()
    if not steps:
        print("No supported package manager found (apt, dnf, yum, pacman, zypper, apk, brew, winget, choco).")
        print(f"Install LibreOffice yourself from {DOWNLOAD} and run this again.")
        print("Without it you can still build the .docx (build_resume.py --no-pdf) and export a PDF from Word.")
        result(7, installed=False, reason="no package manager")

    prefix = priv_prefix()
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", HOMEBREW_NO_AUTO_UPDATE="1", HOMEBREW_NO_ENV_HINTS="1")
    print(f"Installing LibreOffice with {name}. This downloads a few hundred MB and can take several minutes.")

    manual = []
    for cmd, required, admin in steps:
        full = list(cmd)
        if admin:
            if prefix is None:
                manual.append(" ".join(cmd))
                continue
            full = prefix + cmd
        print("$ " + " ".join(full))
        if a.dry_run:
            continue
        try:
            r = subprocess.run(full, capture_output=True, text=True, timeout=1800, env=env)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"  failed to run: {e}")
            if required:
                result(6, installed=False, error=str(e))
            continue
        tail = "\n".join(((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-6:])
        if r.returncode != 0:
            low = tail.lower()
            if admin and prefix == ["sudo", "-n"] and ("password" in low or "sudo:" in low or "a terminal is required" in low):
                manual.append("sudo " + " ".join(cmd))
                print("  needs administrator rights and sudo asked for a password")
                if required:
                    break
                continue
            print(tail)
            if required:
                print(f"Install step failed (exit {r.returncode}). Install LibreOffice from {DOWNLOAD}")
                result(6, installed=False, command=" ".join(full), output=tail)
            else:
                print("  optional step failed, continuing")

    if manual:
        print("\nAdministrator rights are needed. Run these in a terminal, then run this script again:")
        for m in manual:
            print("  " + m)
        result(5, installed=False, manual_commands=manual)
    if a.dry_run:
        result(0, installed=False, dry_run=True)

    so = find_soffice()
    if not so:
        print(f"The install finished but soffice was not found. Open a new terminal, or install from {DOWNLOAD}")
        result(6, installed=False, error="soffice not found after install")
    ok, ver = works(so)
    print(f"LibreOffice ready: {so} ({ver})" if ok else f"LibreOffice installed at {so} but did not start: {ver}")
    font = have_carlito_or_calibri()
    if font is False:
        print("Note: neither Calibri nor Carlito is installed. Build with --font Arial, or install Carlito, "
              "so line breaks in the PDF match Word.")
    result(0 if ok else 6, installed=ok, path=so, version=ver, fonts_ok=font)


if __name__ == "__main__":
    main()

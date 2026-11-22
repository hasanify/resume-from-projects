#!/usr/bin/env python3
"""Verify the resume PDF and render it to PNG for visual inspection.

Usage: verify_pdf.py resume.pdf [--resume resume.json] [--png-dir DIR] [--dpi 110]
                     [--min-pt 9.5] [--min-bottom-in 0.35]

Checks: exactly one page, smallest font size, text inside the page margins,
link annotations present and matching resume.json, section headings in order,
no em dashes or double hyphens in extracted text.
Writes PNG(s) with pypdfium2 or pdftoppm (poppler) into a temp dir (or --png-dir) and prints their paths. The agent must then
look at the PNG: clipping, orphan words, uneven gaps, header separators.

Exit code 0 when every automated check passes, 1 otherwise.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf is required: pip install pypdf")
    sys.exit(2)

ORDER = ["SUMMARY", "PROJECTS", "EXPERIENCE", "SKILLS", "EDUCATION"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--resume", default=None)
    ap.add_argument("--png-dir", default=None)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--min-pt", type=float, default=9.5)
    ap.add_argument("--min-bottom-in", type=float, default=0.35)
    a = ap.parse_args()

    problems, notes = [], []
    reader = PdfReader(a.pdf)
    pages = len(reader.pages)
    print(f"pages: {pages}")
    if pages != 1:
        problems.append(f"PDF has {pages} pages, expected exactly 1")

    page = reader.pages[0]
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)

    # Link annotations
    uris = []
    for pg in reader.pages:
        for an in pg.get("/Annots") or []:
            an = an.get_object()
            act = an.get("/A")
            if act is not None:
                u = act.get_object().get("/URI")
                if u:
                    uris.append(str(u))
    print(f"links: {len(uris)} -> {uris}")
    if a.resume:
        data = json.load(open(a.resume, encoding="utf-8"))
        want = []
        c = data.get("contact") or {}
        if (c.get("email") or "").strip():
            want.append("mailto:" + re.sub(r"^mailto:", "", c["email"].strip()))
        for k in ("github", "linkedin", "website"):
            v = (c.get(k) or "").strip()
            if v:
                want.append(v if re.match(r"^https?://", v) else "https://" + v)
        for pr in data.get("projects") or []:
            v = (pr.get("url") or "").strip()
            if v:
                want.append(v if re.match(r"^https?://", v) else "https://" + v)
        norm = lambda s: s.rstrip("/").lower()
        got = {norm(u) for u in uris}
        for w in want:
            if norm(w) not in got:
                problems.append(f"missing clickable link for {w}")

    # Font sizes and bounds, text order
    try:
        import pdfplumber
        with pdfplumber.open(a.pdf) as pdf:
            pg = pdf.pages[0]
            chars = [c for c in pg.chars if c["text"].strip()]
            if chars:
                sizes = sorted({round(c["size"], 1) for c in chars})
                small = min(sizes)
                body_sizes = [s for s in sizes]
                print(f"font sizes (pt): {body_sizes}")
                if small < a.min_pt - 0.05:
                    problems.append(f"smallest font is {small} pt, below the {a.min_pt} pt floor")
                fonts = sorted({c["fontname"].split("+")[-1] for c in chars})
                print(f"fonts: {fonts}")
                left = min(c["x0"] for c in chars) / 72
                right = (pw - max(c["x1"] for c in chars)) / 72
                top = min(c["top"] for c in chars) / 72
                bottom = (ph - max(c["bottom"] for c in chars)) / 72
                print(f"whitespace (in): left {left:.2f}, right {right:.2f}, top {top:.2f}, bottom {bottom:.2f}")
                if min(left, right) < 0.5:
                    problems.append("text comes within 0.5 in of the left or right edge (clipping risk)")
                if bottom < a.min_bottom_in:
                    problems.append(f"only {bottom:.2f} in of space below the last line; the page is too full")
            text = pg.extract_text() or ""
            # Orphans: a wrapped line that holds a single word.
            words = pg.extract_words(use_text_flow=False, keep_blank_chars=False)
            lines = {}
            for w in words:
                lines.setdefault(round(w["top"] / 2), []).append(w)
            left_x = min((w["x0"] for w in words), default=0)
            for key in sorted(lines):
                ws = sorted(lines[key], key=lambda w: w["x0"])
                if len(ws) == 1 and ws[0]["x0"] - left_x >= 0.25 * 72 and ws[0]["text"] not in ("\u2022", "\u25cf", "\u25aa", "\uf0b7"):
                    problems.append(f"orphan word alone on a wrapped line: '{ws[0]['text']}'. Reword the bullet above it.")
    except ImportError:
        notes.append("pdfplumber not installed: font size and bounds checks skipped (pip install pdfplumber)")
        text = page.extract_text() or ""

    heads = [h for h in ORDER if re.search(rf"^{h}\s*$", text, re.M)]
    pos = [text.find(h) for h in heads]
    if pos != sorted(pos):
        problems.append("section headings are out of the expected order")
    print(f"headings found: {heads}")
    if "—" in text or "–" in text or " -- " in text:
        problems.append("extracted text contains an em dash, en dash or double hyphen")
    if re.search(r"\|\s*\||^\s*\||\|\s*$", text, re.M):
        problems.append("contact line has a leading, trailing or doubled separator")

    # Render
    png_dir = a.png_dir or tempfile.mkdtemp(prefix="resume_preview_")
    os.makedirs(png_dir, exist_ok=True)
    stem = os.path.join(png_dir, os.path.splitext(os.path.basename(a.pdf))[0] + "_preview")
    rendered = False
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(a.pdf)
        for i in range(len(doc)):
            img = doc[i].render(scale=a.dpi / 72).to_pil()
            out = f"{stem}-{i + 1}.png"
            img.save(out)
            print("png:", out)
        rendered = True
    except Exception:
        rendered = False
    if not rendered and shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(a.dpi), a.pdf, stem], check=False)
        pngs = sorted(f for f in os.listdir(png_dir) if f.startswith(os.path.basename(stem)) and f.endswith(".png"))
        for f in pngs:
            print("png:", os.path.join(png_dir, f))
        rendered = bool(pngs)
    if not rendered:
        notes.append("no PNG renderer: pip install pypdfium2 (or install poppler) to get a preview image")

    for n in notes:
        print("note:", n)
    if problems:
        print("\nFAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("\nOK: automated checks passed. Now look at the PNG for clipping, orphan words and uneven gaps.")


if __name__ == "__main__":
    main()

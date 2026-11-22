#!/usr/bin/env python3
"""Build a one-page resume .docx from resume.json and convert it to PDF.

Implements references/layout-spec.md. Needs python-docx, LibreOffice (soffice) and pypdf.

Usage:
  build_resume.py resume.json --outdir DIR [--level 0..3 | --auto-level]
                  [--basename NAME] [--font Calibri] [--no-pdf] [--no-install]

Exit codes: 0 one page, 3 overflow (more than one page), 4 conversion failed, 2 bad input.
Prints one JSON line with the result on stdout.

resume.json shape (every field optional except projects):
{
  "paper": "a4" | "letter",
  "lang": "en-GB",
  "name": "Jane Doe",
  "contact": {"email": "", "phone": "", "location": "", "github": "", "linkedin": "", "website": ""},
  "summary": "",
  "projects": [{"name": "", "url": "", "description": "", "stack": ["", ""],
                "bullets": ["", ""], "merge_desc_stack": false}],
  "experience": [{"title": "", "company": "", "dates": "", "bullets": [""]}],
  "skills": [{"label": "Languages", "items": ["Python"]}],
  "education": [{"degree": "", "institution": "", "year": "", "detail": ""}]
}
Empty strings, empty lists and missing keys are omitted from the document, along with
their labels and separators.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor

BODY_RGB = RGBColor(0x22, 0x22, 0x22)
ACCENT_HEX = "1F2A44"
ACCENT_RGB = RGBColor(0x1F, 0x2A, 0x44)

# level: body pt, margin in, section space before pt, entry gap pt, heading pt
LEVELS = {
    0: dict(body=10.5, margin=0.70, sec_before=8, entry_gap=4, heading=11),
    1: dict(body=10.5, margin=0.65, sec_before=6, entry_gap=3, heading=11),
    2: dict(body=10.0, margin=0.65, sec_before=6, entry_gap=3, heading=10.5),
    3: dict(body=10.0, margin=0.60, sec_before=5, entry_gap=2, heading=10.5),
}
NAME_PT = 21
CONTACT_PT = 10
BODY_FLOOR = 9.5


def clean(s):
    return (s or "").strip() if isinstance(s, str) else ""


def display_url(u):
    return re.sub(r"^https?://(www\.)?", "", u).rstrip("/")


def full_url(u, kind=None):
    u = u.strip()
    if kind == "email":
        return "mailto:" + re.sub(r"^mailto:", "", u)
    if re.match(r"^https?://", u):
        return u
    return "https://" + u


# ---------- style helpers ----------

def set_font(style, font, size=None, bold=None, italic=None, color=None):
    rpr = style.element.get_or_add_rPr()
    for tag in ("w:kern", "w:spacing", "w:caps", "w:smallCaps", "w:u"):
        for el in rpr.findall(qn(tag)):
            rpr.remove(el)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font)
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    if color is not None:
        style.font.color.rgb = color


def set_para(style, before=0, after=0, keep_next=None, line=1.0):
    pf = style.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.alignment = 0  # left
    if keep_next is not None:
        pf.keep_with_next = keep_next
    ppr = style.element.get_or_add_pPr()
    for tag in ("w:contextualSpacing", "w:pBdr"):
        for el in ppr.findall(qn(tag)):
            ppr.remove(el)


def add_bottom_border(style, color_hex, size_eighths=4, space=1):
    ppr = style.element.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(size_eighths))
    b.set(qn("w:space"), str(space))
    b.set(qn("w:color"), color_hex)
    pbdr.append(b)
    ppr.append(pbdr)


def get_or_add_style(styles, name, kind=WD_STYLE_TYPE.PARAGRAPH, base="Normal"):
    try:
        return styles[name]
    except KeyError:
        st = styles.add_style(name, kind)
        if base and kind == WD_STYLE_TYPE.PARAGRAPH:
            st.base_style = styles[base]
        return st


def setup_styles(doc, font, lv, lang):
    styles = doc.styles
    body = lv["body"]
    normal = styles["Normal"]
    set_font(normal, font, body, bold=False, italic=False, color=BODY_RGB)
    set_para(normal, 0, 0, line=1.0)
    rpr = normal.element.get_or_add_rPr()
    for el in rpr.findall(qn("w:lang")):
        rpr.remove(el)
    lg = OxmlElement("w:lang")
    lg.set(qn("w:val"), lang)
    lg.set(qn("w:eastAsia"), lang)
    rpr.append(lg)

    title = styles["Title"]
    set_font(title, font, NAME_PT, bold=True, italic=False, color=ACCENT_RGB)
    set_para(title, 0, 2, keep_next=True)

    contact = get_or_add_style(styles, "Contact")
    set_font(contact, font, CONTACT_PT, bold=False, color=BODY_RGB)
    set_para(contact, 0, 0, keep_next=False)

    h1 = styles["Heading 1"]
    set_font(h1, font, lv["heading"], bold=True, italic=False, color=ACCENT_RGB)
    set_para(h1, lv["sec_before"], 3, keep_next=True)
    add_bottom_border(h1, ACCENT_HEX)

    et = get_or_add_style(styles, "Entry Title")
    set_font(et, font, body, bold=True, italic=False, color=BODY_RGB)
    set_para(et, lv["entry_gap"], 0, keep_next=True)

    ed = get_or_add_style(styles, "Entry Detail")
    set_font(ed, font, body, bold=False, color=BODY_RGB)
    set_para(ed, 0, 0, keep_next=True)

    lb = styles["List Bullet"]
    set_font(lb, font, body, bold=False, italic=False, color=BODY_RGB)
    set_para(lb, 0, 0, keep_next=False)

    try:
        hl = styles["Hyperlink"]
    except KeyError:
        hl = styles.add_style("Hyperlink", WD_STYLE_TYPE.CHARACTER)
    hl.font.color.rgb = ACCENT_RGB
    hl.font.underline = True
    hl.hidden = False
    hl.quick_style = True


# ---------- run and paragraph helpers ----------

def add_hyperlink(par, url, text, bold=None):
    r_id = par.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    h.set(qn("w:history"), "1")
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rs = OxmlElement("w:rStyle")
    rs.set(qn("w:val"), "Hyperlink")
    rpr.append(rs)
    if bold is False:  # entry titles are bold; links on them should not be
        b = OxmlElement("w:b")
        b.set(qn("w:val"), "0")
        rpr.append(b)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    h.append(r)
    par._p.append(h)


def para(doc, text="", style="Normal"):
    p = doc.add_paragraph(style=style)
    if text:
        p.add_run(text)
    return p


def bullet(doc, text, lv):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.30)
    p.paragraph_format.first_line_indent = Inches(-0.15)
    # The list style carries its own tab stop. An explicit one at the text indent
    # keeps the first line aligned with wrapped lines in Word and LibreOffice.
    p.paragraph_format.tab_stops.add_tab_stop(Inches(0.30))
    p.add_run(text)
    return p


def right_tab(p, width_in):
    p.paragraph_format.tab_stops.add_tab_stop(Inches(width_in), WD_TAB_ALIGNMENT.RIGHT)


def heading(doc, text):
    return doc.add_paragraph(text.upper(), style="Heading 1")


# ---------- document ----------

def build_docx(data, path, level, font):
    lv = LEVELS[level]
    paper = (data.get("paper") or "a4").lower()
    lang = data.get("lang") or ("en-US" if paper == "letter" else "en-GB")
    doc = Document()
    for p in list(doc.paragraphs):  # template is empty, but be safe
        p._element.getparent().remove(p._element)
    sec = doc.sections[0]
    if paper == "letter":
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        page_w = 8.5
    else:
        sec.page_width, sec.page_height = Mm(210), Mm(297)
        page_w = 8.27
    m = Inches(lv["margin"])
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = m
    sec.header_distance = sec.footer_distance = Inches(0.3)
    content_w = page_w - 2 * lv["margin"]
    setup_styles(doc, font, lv, lang)

    name = clean(data.get("name"))
    c = data.get("contact") or {}
    if name:
        para(doc, name, "Title")
    items = []
    if clean(c.get("email")):
        items.append(("link", full_url(c["email"], "email"), clean(c["email"])))
    if clean(c.get("phone")):
        items.append(("text", clean(c["phone"])))
    if clean(c.get("location")):
        items.append(("text", clean(c["location"])))
    for key in ("github", "linkedin", "website"):
        if clean(c.get(key)):
            items.append(("link", full_url(c[key]), display_url(clean(c[key]))))
    if items:
        p = doc.add_paragraph(style="Contact")
        p.paragraph_format.space_after = Pt(max(lv["sec_before"] - 2, 2))
        for i, it in enumerate(items):
            if i:
                p.add_run(" | ")
            if it[0] == "text":
                p.add_run(it[1])
            else:
                add_hyperlink(p, it[1], it[2])
    elif name:
        doc.paragraphs[-1].paragraph_format.space_after = Pt(max(lv["sec_before"] - 2, 2))

    first_section = not (name or items)

    def section(title):
        nonlocal first_section
        h = heading(doc, title)
        if first_section:
            h.paragraph_format.space_before = Pt(0)
            first_section = False
        return h

    summary = clean(data.get("summary"))
    if summary:
        section("Summary")
        para(doc, summary)

    projects = [p for p in (data.get("projects") or []) if clean(p.get("name"))]
    if projects:
        section("Projects")
        for i, pr in enumerate(projects):
            t = para(doc, "", "Entry Title")
            t.add_run(clean(pr["name"]))
            if i == 0:
                t.paragraph_format.space_before = Pt(0)
            url = clean(pr.get("url"))
            if url:
                right_tab(t, content_w)
                t.add_run("\t")
                add_hyperlink(t, full_url(url), display_url(url), bold=False)
            desc = clean(pr.get("description"))
            stack = [clean(s) for s in (pr.get("stack") or []) if clean(s)]
            stack_txt = "Stack: " + ", ".join(stack) if stack else ""
            bullets = [clean(b) for b in (pr.get("bullets") or []) if clean(b)]
            if pr.get("merge_desc_stack") and desc and stack_txt:
                d = para(doc, "", "Entry Detail")
                r = d.add_run(desc.rstrip(".") + ". ")
                r.italic = True
                d.add_run(stack_txt)
            else:
                if desc:
                    d = para(doc, "", "Entry Detail")
                    d.add_run(desc).italic = True
                if stack_txt:
                    para(doc, stack_txt, "Entry Detail")
            for j, b in enumerate(bullets):
                bp = bullet(doc, b, lv)
                if j == len(bullets) - 1:
                    bp.paragraph_format.space_after = Pt(1)

    exp = [e for e in (data.get("experience") or []) if clean(e.get("title")) or clean(e.get("company"))]
    if exp:
        section("Experience")
        for i, e in enumerate(exp):
            t = para(doc, "", "Entry Title")
            if i == 0:
                t.paragraph_format.space_before = Pt(0)
            head = ", ".join(x for x in (clean(e.get("title")), clean(e.get("company"))) if x)
            t.add_run(head)
            if clean(e.get("dates")):
                right_tab(t, content_w)
                t.add_run("\t" + clean(e["dates"])).bold = False
            bl = [clean(b) for b in (e.get("bullets") or []) if clean(b)]
            for j, b in enumerate(bl):
                bp = bullet(doc, b, lv)
                if j == len(bl) - 1:
                    bp.paragraph_format.space_after = Pt(1)

    skills = [s for s in (data.get("skills") or []) if [x for x in (s.get("items") or []) if clean(x)]]
    if skills:
        section("Skills")
        for s in skills:
            items_txt = ", ".join(clean(x) for x in s["items"] if clean(x))
            label = clean(s.get("label"))
            para(doc, f"{label}: {items_txt}" if label else items_txt)

    edu = [e for e in (data.get("education") or []) if clean(e.get("degree")) or clean(e.get("institution"))]
    if edu:
        section("Education")
        for i, e in enumerate(edu):
            t = para(doc, "", "Entry Title")
            if i == 0:
                t.paragraph_format.space_before = Pt(0)
            t.add_run(", ".join(x for x in (clean(e.get("degree")), clean(e.get("institution"))) if x))
            if clean(e.get("year")):
                right_tab(t, content_w)
                t.add_run("\t" + clean(e["year"])).bold = False
            if clean(e.get("detail")):
                t.paragraph_format.keep_with_next = True
                para(doc, clean(e["detail"]), "Normal")

    cp = doc.core_properties
    cp.title = f"{name} Resume".strip() if name else "Resume"
    cp.author = name or ""
    cp.last_modified_by = name or ""
    cp.comments = ""
    cp.subject = ""
    cp.keywords = ""
    doc.save(path)


# ---------- conversion ----------

def find_soffice():
    for n in ("soffice", "libreoffice"):
        p = shutil.which(n)
        if p:
            return p
    for p in ("/Applications/LibreOffice.app/Contents/MacOS/soffice",
              r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if os.path.exists(p):
            return p
    return None


def ensure_soffice(auto_install=True):
    so = find_soffice()
    if so or not auto_install:
        return so
    inst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_libreoffice.py")
    print("LibreOffice not found. Installing it (install_libreoffice.py)...", file=sys.stderr)
    try:
        subprocess.run([sys.executable, inst], stdout=sys.stderr, stderr=sys.stderr, timeout=2400)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"installer did not run: {e}", file=sys.stderr)
    return find_soffice()


def to_pdf(docx_path, out_dir, auto_install=True):
    so = ensure_soffice(auto_install)
    if not so:
        raise RuntimeError("LibreOffice (soffice) not found and could not be installed automatically. "
                           "Run scripts/install_libreoffice.py and follow its output, or open the .docx in Word "
                           "and export a PDF.")
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    try:
        r = subprocess.run(
            [so, "--headless", "--norestore", "--nolockcheck",
             f"-env:UserInstallation=file://{profile}" if os.name != "nt" else f"-env:UserInstallation=file:///{profile.replace(os.sep, '/')}",
             "--convert-to", "pdf", "--outdir", out_dir, docx_path],
            capture_output=True, text=True, timeout=240)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if r.returncode != 0 or not os.path.exists(pdf):
        raise RuntimeError(f"conversion failed: {r.stderr.strip() or r.stdout.strip()}")
    return pdf


def page_count(pdf):
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf).pages)
    except ImportError:
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        return int(m.group(1)) if m else -1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("resume")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--level", type=int, default=0, choices=sorted(LEVELS))
    ap.add_argument("--auto-level", action="store_true",
                    help="try levels from --level upward until the PDF is one page")
    ap.add_argument("--basename", default=None, help="file name without extension")
    ap.add_argument("--font", default="Calibri")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--no-install", action="store_true",
                    help="do not try to install LibreOffice when it is missing")
    a = ap.parse_args()

    try:
        data = json.load(open(a.resume, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": f"cannot read resume json: {e}"}))
        sys.exit(2)
    if not (data.get("projects") or []):
        print(json.dumps({"ok": False, "error": "resume.json has no projects"}))
        sys.exit(2)

    name = clean(data.get("name"))
    base = a.basename or (re.sub(r"[^\w\-]+", "_", name).strip("_") + "_Resume" if name else "Resume")
    os.makedirs(a.outdir, exist_ok=True)

    levels = list(range(a.level, max(LEVELS) + 1)) if a.auto_level else [a.level]
    last = None
    for lvl in levels:
        tmp = tempfile.mkdtemp(prefix="resume_build_")
        try:
            docx_path = os.path.join(tmp, base + ".docx")
            build_docx(data, docx_path, lvl, a.font)
            if a.no_pdf:
                shutil.copy(docx_path, os.path.join(a.outdir, base + ".docx"))
                print(json.dumps({"ok": True, "docx": os.path.join(a.outdir, base + ".docx"), "pdf": None, "level": lvl}))
                return
            try:
                pdf = to_pdf(docx_path, tmp, auto_install=not a.no_install)
            except RuntimeError as e:
                print(json.dumps({"ok": False, "error": str(e)}))
                sys.exit(4)
            pages = page_count(pdf)
            last = {"level": lvl, "pages": pages}
            if pages == 1 or lvl == levels[-1]:
                d_out = os.path.join(a.outdir, base + ".docx")
                p_out = os.path.join(a.outdir, base + ".pdf")
                shutil.copy(docx_path, d_out)
                shutil.copy(pdf, p_out)
                lv = LEVELS[lvl]
                res = {"ok": pages == 1, "docx": d_out, "pdf": p_out, "pages": pages, "level": lvl,
                       "body_pt": lv["body"], "margin_in": lv["margin"], "paper": (data.get("paper") or "a4")}
                if pages != 1:
                    res["error"] = (f"overflow: {pages} pages at level {lvl}. Tighten the wording, "
                                    "drop the weakest bullet or project, then rebuild.")
                print(json.dumps(res))
                sys.exit(0 if pages == 1 else 3)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

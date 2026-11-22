#!/usr/bin/env python3
"""Lint resume.json text against references/writing-rules.md.

Usage: check_writing.py resume.json [--strict]

Finds banned words and phrases, em dashes, connective en dashes, double hyphens,
exclamation marks, emoji, weak opening verbs, repeated opening verbs, title-cased
bullets, numbers that have no `evidence` note, and bullets that are too long.
It cannot judge meaning. The agent still runs the draft/audit/final loop by hand.

Exit code 1 if any ERROR is found (WARN only fails with --strict).
"""
import argparse
import json
import re
import sys
from collections import Counter

BANNED = """
delve into|underscore|pivotal|realm|harness|illuminate|shed light on|bolster|streamline|streamlined|
streamlining|facilitate|facilitated|foster|leverage|leveraged|leveraging|cutting-edge|cutting edge|
state-of-the-art|innovative|revolutionary|revolutionized|game-changing|game changer|transformative|
groundbreaking|seamless|seamlessly|robust|scalable|holistic|synergy|synergies|paradigm shift|nuanced|
comprehensive|best practices|unlock|elevate|empower|empowered|empowering|showcase|testament|journey|
next-level|next level|next generation|ai powered|intelligent|ultimate|powerful|effortless|effortlessly|
utilize|utilized|utilizing|commence|endeavor|ascertain|elucidate|aforementioned|herein|
passionate|results-driven|results driven|dynamic|detail-oriented|self-starter|team player|hard-working|
hardworking|go-getter|visionary|rockstar|ninja|guru|spearheaded|spearhead|orchestrated|championed|
pioneered|ideated|operationalized|synergized|world-class|best-in-class|enterprise-grade|state of the art|
high-performance|end-to-end|full-fledged|sleek|truly|literally|essentially|ultimately|obviously|
undoubtedly|undeniably|fascinating|incredible|wonderful|amazing|significantly|drastically|greatly|
generally speaking|broadly speaking|at its core|in today's|fast-paced|ever-evolving|a wide range of|
various|a number of|honestly|let's dive|at the end of the day|it's worth noting|it is important to note
""".replace("\n", "")
BANNED_RE = re.compile(r"(?<![\w-])(" + "|".join(sorted({b.strip() for b in BANNED.split("|") if b.strip()}, key=len, reverse=True)) + r")(?![\w-])", re.I)

WEAK_OPENERS = re.compile(r"^(responsible for|worked on|helped( with| to)?|assisted( in| with)?|involved in|"
                          r"tasked with|participated in|was |were |duties included|in charge of)\b", re.I)
VAGUE = re.compile(r"\b(improved|increased|enhanced|boosted|optimi[sz]ed) (the )?(performance|efficiency|user experience|"
                   r"productivity|scalability|reliability|quality)\b", re.I)
NOT_JUST = re.compile(r"\b(not just|not only|isn't just|more than just)\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")
THIRD = re.compile(r"\b(he|she|they|his|her|their|i|my|me|we|our)\b", re.I)
NUM = re.compile(r"\d")


def walk(data):
    """Yield (path, text, kind). kind in bullet, line, other."""
    def s(path, v, kind="line"):
        if isinstance(v, str) and v.strip():
            yield path, v, kind
    yield from s("name", data.get("name"), "other")
    yield from s("summary", data.get("summary"))
    for i, p in enumerate(data.get("projects") or []):
        yield from s(f"projects[{i}].name", p.get("name"), "other")
        yield from s(f"projects[{i}].description", p.get("description"))
        for j, b in enumerate(p.get("bullets") or []):
            yield from s(f"projects[{i}].bullets[{j}]", b, "bullet")
    for i, e in enumerate(data.get("experience") or []):
        for j, b in enumerate(e.get("bullets") or []):
            yield from s(f"experience[{i}].bullets[{j}]", b, "bullet")
    for i, sk in enumerate(data.get("skills") or []):
        yield from s(f"skills[{i}].label", sk.get("label"), "other")
    for i, e in enumerate(data.get("education") or []):
        yield from s(f"education[{i}].detail", e.get("detail"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("resume")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.resume, encoding="utf-8"))
    errors, warns = [], []

    verbs_by_project = {}
    all_verbs = Counter()
    # Every string, including names and stack items, for the character checks.
    texts = list(walk(data))
    for i, p in enumerate(data.get("projects") or []):
        for j, st in enumerate(p.get("stack") or []):
            texts.append((f"projects[{i}].stack[{j}]", st, "other"))
    for i, sk in enumerate(data.get("skills") or []):
        for j, it in enumerate(sk.get("items") or []):
            texts.append((f"skills[{i}].items[{j}]", it, "other"))

    for path, t, kind in texts:
        if "—" in t:
            errors.append(f"{path}: em dash. Use a period, comma, colon or parentheses.")
        if "–" in t and not re.search(r"\d\s*–\s*\d", t):
            errors.append(f"{path}: en dash used as a connective. Rewrite the sentence.")
        if " -- " in t or "--" in t:
            errors.append(f"{path}: double hyphen used as a dash.")
        if "!" in t:
            errors.append(f"{path}: exclamation mark.")
        if EMOJI.search(t):
            errors.append(f"{path}: emoji.")
        if kind in ("bullet", "line"):
            for m in BANNED_RE.finditer(t):
                errors.append(f"{path}: banned word or phrase '{m.group(0)}'.")
            if NOT_JUST.search(t):
                errors.append(f"{path}: 'not just X but Y' construction.")
            if VAGUE.search(t):
                warns.append(f"{path}: vague outcome claim ({VAGUE.search(t).group(0)}). Say what changed, with a figure from the repo.")
            if t.count('"') >= 2 or t.count("“") >= 1:
                warns.append(f"{path}: quotation marks. Keep them only for real quotations.")
            if t.count(";") >= 1:
                warns.append(f"{path}: semicolon. Prefer two short sentences or a comma.")
            if re.search(r"\b[A-Z]{5,}\b", t) and not re.search(r"\b(HTTP|HTTPS|REST|JSON|OAuth|SQLite|GraphQL|OpenAPI|WebSocket|WEBHOOK)\b", t):
                warns.append(f"{path}: long all-caps word. Check for shouting emphasis.")
        if kind == "bullet":
            if WEAK_OPENERS.match(t.strip()):
                errors.append(f"{path}: weak opener '{t.split()[0]}'. Start with a specific past-tense verb.")
            if THIRD.search(t):
                warns.append(f"{path}: pronoun ('{THIRD.search(t).group(0)}'). Write bullets without pronouns.")
            words = re.findall(r"[A-Za-z][A-Za-z'\-]*", t)
            if len(words) >= 4 and sum(1 for w in words[1:] if w[0].isupper()) / max(len(words) - 1, 1) > 0.6:
                warns.append(f"{path}: looks title-cased. Use sentence case.")
            if t.strip().endswith("."):
                warns.append(f"{path}: trailing period. This skill ends bullets without one.")
            if len(t) > 210:
                warns.append(f"{path}: {len(t)} characters. Aim for one line, two at most.")
            if len(t) < 35:
                warns.append(f"{path}: very short ({len(t)} characters). Add the concrete detail.")
            first = re.sub(r"[^A-Za-z]", "", t.split()[0]).lower() if t.split() else ""
            m = re.match(r"(projects|experience)\[(\d+)\]", path)
            if m and first:
                verbs_by_project.setdefault((m.group(1), m.group(2)), []).append(first)
                all_verbs[first] += 1

    for (sec, idx), vs in verbs_by_project.items():
        for v, n in Counter(vs).items():
            if n > 1:
                errors.append(f"{sec}[{idx}]: opening verb '{v}' repeats {n} times in one entry.")
    for v, n in all_verbs.items():
        if n > 2:
            warns.append(f"opening verb '{v}' appears {n} times on the page. Vary it.")

    # Numbers need evidence
    for i, p in enumerate(data.get("projects") or []):
        ev = [e for e in (p.get("evidence") or []) if isinstance(e, str) and e.strip()]
        has_num_bullet = any(NUM.search(b or "") for b in (p.get("bullets") or []))
        if has_num_bullet and not ev:
            errors.append(f"projects[{i}] ({p.get('name')}): bullets contain numbers but `evidence` is empty. "
                          "Record where each number comes from (file, README line, git log).")

    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    if errors or (a.strict and warns):
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rank verified projects and pick the top N.

Inputs : scan.json (scan_projects.py) and verdicts.json (check_origin.py)
Usage  : rank_projects.py scan.json verdicts.json [--top 5] [--role "backend engineer"]
                          [--keywords python,fastapi] [--include-confirm name1,name2]
                          [--exclude name3] [--only-pinned] [--force-pin name4]
                          [--out ranking.json]

Projects the user named (scan.json `pinned`) are guaranteed a place if they pass verification;
the rest of the places go to the best-scoring others. --only-pinned skips the auto-fill.

Only projects with verdict `accept` are ranked, plus any `confirm` project whose
name you pass in --include-confirm (after the user said it is theirs).
Scores are 0 to 100. Weights:
  real-world signal 30, technical depth 20, user contribution 20,
  quality evidence 15, recency 10, role relevance 5 (redistributed when no role given).
The output lists the evidence behind every sub-score so the choice can be explained.
"""
import argparse
import json
import math
import re
import sys
from datetime import date

WEIGHTS = {"real_world": 30, "depth": 20, "contribution": 20, "quality": 15, "recency": 10, "relevance": 5}


def clamp(x):
    return max(0.0, min(1.0, x))


def parse_day(s):
    try:
        y, m, d = (int(x) for x in s[:10].split("-"))
        return date(y, m, d)
    except Exception:
        return None


def real_world(p):
    ev, s = [], 0.0
    if p["deploy"]:
        s += 0.3
        ev.append("deployment config: " + ", ".join(p["deploy"][:3]))
    if p["integrations"]:
        s += min(len(p["integrations"]), 3) / 3 * 0.3
        ev.append("integrations: " + ", ".join(p["integrations"]))
    if p["real_world_phrases"]:
        s += 0.2
        ev.append("README mentions: " + ", ".join(p["real_world_phrases"][:4]))
    if p["urls_in_readme"]:
        s += 0.2
        ev.append("live or doc URL in README: " + p["urls_in_readme"][0])
    return clamp(s), ev


def depth(p):
    ev = []
    loc = p["lines_of_code"]
    s_loc = clamp(math.log10(max(loc, 1)) / math.log10(20000))  # 20k LOC = full marks
    langs = [l for l in p["languages"] if l not in ("HTML", "CSS", "SQL", "Shell", "Jupyter")]
    s_lang = clamp(len(langs) / 3)
    s_dep = clamp(p["dependency_count"] / 30)
    s_dirs = clamp(len(p["top_dirs"]) / 8)
    ev.append(f"{loc} lines of code across {len(p['languages'])} language(s)")
    ev.append(f"{p['dependency_count']} dependencies, {len(p['top_dirs'])} top-level dirs")
    if p["monorepo_children"]:
        ev.append(f"{len(p['monorepo_children'])} packages/apps")
    return clamp(0.5 * s_loc + 0.2 * s_lang + 0.15 * s_dep + 0.15 * s_dirs), ev


def contribution(p):
    g = p["git"]
    if not g.get("is_git") or not g.get("commit_count"):
        return 0.5, ["no git history: neutral score, authorship unverified"]
    share = g["user_share"]
    fshare = g.get("user_file_share", 0.0)
    volume = clamp(g["user_commit_count"] / 60)
    ev = [f"{g['user_commit_count']} of {g['commit_count']} commits ({share:.0%})",
          f"touched {g['files_touched_by_user']} of {g['files_in_history']} files in history"]
    return clamp(0.5 * share + 0.25 * fshare + 0.25 * volume), ev


def quality(p):
    ev, s = [], 0.0
    if p["tests"]["count"]:
        s += 0.4
        ev.append(f"{p['tests']['count']} test file(s)")
    if p["ci"]:
        s += 0.3
        ev.append("CI config: " + ", ".join(p["ci"][:2]))
    rd = p["readme_chars"]
    if rd > 1500 or p["docs_files"] >= 3:
        s += 0.3
        ev.append(f"README {rd} chars, {p['docs_files']} docs file(s)")
    elif rd > 500:
        s += 0.15
        ev.append(f"README {rd} chars")
    return clamp(s), ev


def recency(p):
    g = p["git"]
    d = parse_day(g.get("user_last_commit") or g.get("last_commit") or "")
    if not d:
        return 0.4, ["no commit dates"]
    years = (date.today() - d).days / 365.25
    s = 1.0 if years <= 1 else 0.7 if years <= 2 else 0.4 if years <= 4 else 0.2
    return s, [f"last commit {d.isoformat()} ({years:.1f} years ago)"]


def relevance(p, words):
    if not words:
        return None, []
    hay = " ".join([p["name"], p["readme_excerpt"].lower(), " ".join(p["languages"]),
                    " ".join(p["frameworks"]), " ".join(p["integrations"]),
                    " ".join(p["dependencies_sample"])]).lower()
    hits = [w for w in words if w in hay]
    return clamp(len(hits) / max(len(words), 1)), [f"matches: {', '.join(hits)}" if hits else "no keyword matches"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan")
    ap.add_argument("verdicts")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--role", default="")
    ap.add_argument("--keywords", default="", help="comma-separated skills to favour")
    ap.add_argument("--include-confirm", default="", help="comma-separated names the user confirmed as theirs")
    ap.add_argument("--exclude", default="", help="comma-separated names to drop")
    ap.add_argument("--only-pinned", action="store_true",
                    help="feature only the projects the user named (scan.json `pinned` flag); no auto-fill")
    ap.add_argument("--force-pin", default="",
                    help="comma-separated pinned names that failed verification but the user insists are theirs "
                         "(only after the user saw the reasons)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    scan = json.load(open(a.scan, encoding="utf-8"))
    ver = {v["name"]: v for v in json.load(open(a.verdicts, encoding="utf-8"))["verdicts"]}
    inc = {x.strip() for x in a.include_confirm.split(",") if x.strip()}
    exc = {x.strip() for x in a.exclude.split(",") if x.strip()}
    words = [w.strip().lower() for w in a.keywords.split(",") if w.strip()]
    words += [w for w in re.split(r"[^a-z0-9+#.]+", a.role.lower()) if len(w) > 2 and w not in {"the", "and", "engineer", "developer"}]
    words = sorted(set(words))

    weights = dict(WEIGHTS)
    if not words:
        extra = weights.pop("relevance")
        total = sum(weights.values())
        weights = {k: v * (total + extra) / total for k, v in weights.items()}

    force = {x.strip() for x in a.force_pin.split(",") if x.strip()}
    pinned_names = [p["name"] for p in scan["projects"] if p.get("pinned")]
    pin_blocked = []
    ranked = []
    for p in scan["projects"]:
        v = ver.get(p["name"])
        if not v or p["name"] in exc:
            continue
        if a.only_pinned and not p.get("pinned"):
            continue
        if v["verdict"] == "reject" and p["name"] not in force:
            if p.get("pinned"):
                pin_blocked.append({"name": p["name"], "verdict": "reject", "reasons": v["reasons"]})
            continue
        if v["verdict"] == "confirm" and p["name"] not in inc and p["name"] not in force:
            if p.get("pinned"):
                pin_blocked.append({"name": p["name"], "verdict": "confirm", "reasons": v["reasons"]})
            continue
        subs = {}
        for key, fn in (("real_world", real_world), ("depth", depth), ("contribution", contribution),
                        ("quality", quality), ("recency", recency)):
            sc, ev = fn(p)
            subs[key] = {"score": round(sc, 3), "evidence": ev}
        rel, rel_ev = relevance(p, words)
        if rel is not None:
            subs["relevance"] = {"score": round(rel, 3), "evidence": rel_ev}
        total = sum(subs[k]["score"] * weights[k] for k in subs)
        ranked.append({"name": p["name"], "path": p["path"], "score": round(total, 1),
                       "pinned": bool(p.get("pinned")), "forced": p["name"] in force,
                       "flags": v["flags"], "subscores": subs,
                       "languages": p["languages"], "frameworks": p["frameworks"],
                       "integrations": p["integrations"]})
    ranked.sort(key=lambda r: -r["score"])
    # Pinned projects take their places first. Remaining places go to the best of the rest.
    pins_ok = [r for r in ranked if r["pinned"]]
    top_n = max(a.top, len(pins_ok))
    rest = [] if a.only_pinned else [r for r in ranked if not r["pinned"]]
    chosen = pins_ok + rest[: max(top_n - len(pins_ok), 0)]
    chosen.sort(key=lambda r: -r["score"])
    for i, r in enumerate(ranked):
        r["selected"] = any(c["name"] == r["name"] for c in chosen)
    res = {"top_n": top_n, "selected": [r["name"] for r in chosen],
           "ranked": ranked, "role_keywords": words,
           "pin_requests": scan.get("pin_requests", []), "pinned_selected": [r["name"] for r in pins_ok],
           "pin_blocked": pin_blocked, "pin_unmatched": scan.get("pin_unmatched", []),
           "pin_ambiguous": scan.get("pin_ambiguous", {})}
    notes = []
    if len(pins_ok) > a.top:
        notes.append(f"{len(pins_ok)} projects were named, more than the {a.top} requested. All named projects are kept. Tell the user, and offer to trim.")
    target = len(pins_ok) if a.only_pinned else top_n
    if len(chosen) < target or (not a.only_pinned and len(chosen) < a.top):
        notes.append(f"only {len(chosen)} project(s) available; fewer than the {a.top} requested. Do not pad.")
    if pin_blocked:
        notes.append("named project(s) failed verification and are NOT included: " + ", ".join(b["name"] for b in pin_blocked)
                     + ". Show the user the reasons. Include them only if the user confirms (--include-confirm) or insists (--force-pin).")
    if notes:
        res["note"] = " ".join(notes)
    txt = json.dumps(res, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
    else:
        print(txt)
    print("", file=sys.stderr)
    for i, r in enumerate(ranked, 1):
        mark = ">" if r["selected"] else " "
        pin = " (named by user)" if r["pinned"] else ""
        print(f" {mark}{i:>2}. {r['score']:>5.1f}  {r['name']}{pin}", file=sys.stderr)
    for b in pin_blocked:
        print(f"  BLOCKED named project {b['name']}: {b['verdict']}: {b['reasons'][0]}", file=sys.stderr)
    for n in res["pin_unmatched"]:
        print(f"  NOT FOUND named project: {n}", file=sys.stderr)
    if "note" in res:
        print("  " + res["note"], file=sys.stderr)


if __name__ == "__main__":
    main()

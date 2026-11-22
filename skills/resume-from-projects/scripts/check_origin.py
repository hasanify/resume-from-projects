#!/usr/bin/env python3
"""Decide which scanned projects are the user's own real-world work.

Input : scan JSON from scan_projects.py
Output: JSON verdicts. Each project gets verdict accept | reject | confirm, plus
        reasons and `search_queries` (project and package names only, never code)
        for the web check the agent runs when it has a search tool.

Usage:
  check_origin.py scan.json [--github-user U] [--user-name N]... [--out verdicts.json]

Verdicts:
  accept   looks like the user's own work
  reject   clone, fork, tutorial, popular open-source code, toy, or not the user's
  confirm  cannot be decided from files alone (no git history, thin history,
           popular name, foreign remote with high user share). Ask the user.

This script is read-only and offline. The web search step is done by the agent.
"""
import argparse
import json
import re
import sys

# Names of widely known public projects. A match does not reject by itself; it forces
# the web check and a confirm/reject decision.
POPULAR = set("""
react react-dom vue angular svelte next nextjs nuxt express koa fastify nest nestjs lodash underscore
jquery bootstrap tailwindcss tailwind webpack vite rollup babel eslint prettier typescript jest mocha
vitest axios moment dayjs rxjs redux zustand mobx d3 three threejs chartjs socket.io electron
django flask fastapi tornado celery requests numpy pandas scipy matplotlib scikit-learn sklearn
tensorflow pytorch torch keras transformers langchain pydantic sqlalchemy pytest black poetry pip
rails sinatra laravel symfony spring spring-boot hibernate gin echo fiber cobra viper hugo kubernetes
docker terraform ansible prometheus grafana redis postgres postgresql mysql mongodb sqlite
vscode atom neovim vim emacs tmux zsh oh-my-zsh homebrew deno bun node nodejs rust cargo ripgrep
bat fd exa tokio serde actix axum rocket flutter react-native expo ionic cordova
freecodecamp the-algorithms algorithms linux git curl openssl ffmpeg opencv
create-react-app todomvc realworld nodebestpractices awesome
""".split())

TUTORIAL_NAME_RE = re.compile(
    r"(tutorial|course|bootcamp|udemy|learn|learning|practice|exercise|homework|assignment|"
    r"todo-?app|to-?do-?list|hello-?world|calculator-?app|weather-?app|clone|playground|sandbox|test-?repo|untitled|new-project)", re.I)


def norm(s):
    return re.sub(r"[^a-z0-9.\-]", "", (s or "").lower().split("/")[-1])


def identity_tokens(names, github):
    toks = set()
    for n in names:
        for t in re.split(r"[\s._\-]+", n.lower()):
            if len(t) >= 3:
                toks.add(t)
        toks.add(re.sub(r"\s+", "", n.lower()))
    if github:
        toks.add(github.lower())
    return toks


def owner_is_user(owner, toks):
    if not owner:
        return None
    o = owner.lower()
    return any(t and (t == o or t in o or o in t and len(o) >= 4) for t in toks)


def holder_is_user(holder, toks):
    h = holder.lower()
    return any(t and t in h for t in toks)


def judge(p, toks, github):
    reasons, flags = [], []
    verdict = "accept"
    g = p["git"]
    sig = p["signals"]

    def reject(msg):
        nonlocal verdict
        verdict = "reject"
        reasons.append(msg)

    def confirm(msg):
        nonlocal verdict
        if verdict != "reject":
            verdict = "confirm"
        reasons.append(msg)

    # Toy and empty
    if sig["toy"]:
        reject("toy or empty: " + "; ".join(sig["toy"]))
    # Scaffold
    if sig["scaffold_readme"] and p["lines_of_code"] < 400:
        reject("README is the unmodified scaffold text and the code is small")
    # Tutorial
    if sig["tutorial_strong"]:
        reject("tutorial or course signals in README or name: " + ", ".join(sig["tutorial_strong"]))
    elif TUTORIAL_NAME_RE.search(p["name"]) and p["lines_of_code"] < 1500:
        confirm("name looks like a practice project (" + p["name"] + ")")
    elif sig["tutorial_weak"] and p["lines_of_code"] < 600 and not p["tests"]["count"]:
        confirm("weak tutorial signals (" + ", ".join(sig["tutorial_weak"]) + ") and little code")

    # Git authorship and origin
    if not g.get("is_git"):
        flags.append("no_git")
        confirm("no git history, authorship cannot be verified")
    elif g.get("commit_count", 0) == 0:
        reject("repository has no commits")
    else:
        total, mine, share = g["commit_count"], g["user_commit_count"], g["user_share"]
        if not toks and mine == 0:
            confirm("user identity unknown, so authorship is unchecked")
        elif mine == 0:
            reject(f"user authored none of the {total} commits")
        elif total >= 5 and share < 0.2:
            reject(f"user authored {mine} of {total} commits ({share:.0%})")
        elif total > 3 and mine < 3:
            reject(f"user authored only {mine} of {total} commits")
        elif total <= 3:
            flags.append("thin_history")
            confirm(f"only {total} commit(s) in history, so the real work may predate this repo")
        elif share < 0.5:
            flags.append("shared_project")
            reasons.append(f"shared project: user authored {mine} of {total} commits ({share:.0%}); describe only the user's part")

        owner = g.get("origin_owner")
        owned = owner_is_user(owner, toks)
        if g.get("origin_url"):
            if owned is False:
                flags.append("foreign_origin")
                share = g.get("user_share", 0)
                if share < 0.5:
                    reject(f"origin is {g['origin_url']} (owner {owner}) and the user authored {share:.0%} of commits")
                else:
                    confirm(f"origin is {g['origin_url']} (owner {owner}), not clearly the user's account; user authored {share:.0%}")
        if g.get("has_upstream_remote"):
            flags.append("fork_marker")
            if g.get("user_share", 0) < 0.5:
                reject("has an `upstream` remote (a fork) and the user authored a minority of commits")
            else:
                confirm("has an `upstream` remote (a fork of someone else's repo); confirm the user's changes are substantial")

    # License and README name another author
    root_holders = [h for h in p["license_holders"] if "/" not in h["file"] and "\\" not in h["file"]]
    foreign_root = [h for h in root_holders if toks and not holder_is_user(h["holder"], toks)]
    if foreign_root:
        flags.append("license_other_author")
        h = foreign_root[0]["holder"]
        if verdict == "reject" or "foreign_origin" in flags or "fork_marker" in flags:
            reasons.append(f"LICENSE names another holder ({h})")
        else:
            confirm(f"LICENSE names another holder ({h}); could be an employer, an org, or upstream code")
    nested = [h for h in p["license_holders"] if ("/" in h["file"] or "\\" in h["file"]) and toks and not holder_is_user(h["holder"], toks)]
    if nested and p["total_files"] > 0:
        flags.append("vendored_upstream")
        confirm(f"nested LICENSE from another holder at {nested[0]['file']} ({nested[0]['holder']}); may be a vendored upstream copy")
    meta = p.get("manifest_meta", {})
    author = meta.get("author")
    if author and toks and not holder_is_user(author, toks) and "foreign_origin" in flags:
        reasons.append(f"manifest author is {author}")

    # Name matches a well-known public project
    names = {norm(p["name"]), norm(meta.get("package_name"))}
    pop = sorted(n for n in names if n and n in POPULAR)
    if pop:
        flags.append("popular_name")
        confirm("name matches a widely known project (" + ", ".join(pop) + "); run the web check")

    queries = sorted({q for q in [p["name"], meta.get("package_name")] if q})
    return {
        "name": p["name"], "path": p["path"], "verdict": verdict,
        "reasons": reasons or ["own commits, no clone, fork or tutorial signals"],
        "flags": flags, "search_queries": queries,
        "origin_url": g.get("origin_url") if g.get("is_git") else None,
        "user_share": g.get("user_share") if g.get("is_git") else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan")
    ap.add_argument("--github-user", default=None)
    ap.add_argument("--user-name", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    with open(a.scan, encoding="utf-8") as f:
        scan = json.load(f)
    names = a.user_name or scan["user"].get("names", [])
    github = a.github_user or scan["user"].get("github")
    toks = identity_tokens(names, github)
    # email local-part is also a useful identity token
    for e in scan["user"].get("emails", []):
        local = e.split("@")[0].lower()
        if len(local) >= 3 and not re.fullmatch(r"\d+\+.*", local):
            toks.add(local)
        m = re.fullmatch(r"\d+\+(.+)", local)
        if m:
            toks.add(m.group(1))
    verdicts = [judge(p, toks, github) for p in scan["projects"] if "skipped_reason" not in p]
    res = {"verdicts": verdicts,
           "summary": {v: sum(1 for x in verdicts if x["verdict"] == v) for v in ("accept", "confirm", "reject")}}
    txt = json.dumps(res, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt)
    else:
        print(txt)
    print("", file=sys.stderr)
    for v in verdicts:
        print(f"  {v['verdict']:<8} {v['name']:<28} {v['reasons'][0]}", file=sys.stderr)


if __name__ == "__main__":
    main()

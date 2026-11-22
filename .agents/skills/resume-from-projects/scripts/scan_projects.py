#!/usr/bin/env python3
"""Scan a directory of projects and emit structured facts as JSON.

Read-only. Opens files for reading and runs only `git log`, `git remote -v`
and `git config --get`. It never writes inside the scanned directory, never runs
project code, and never sends anything over the network.

Usage:
  scan_projects.py DIR [--user-email E]... [--user-name N]... [--github-user U]
                       [--pin NAME[,NAME]]... [--max-deep 40] [--out scan.json]

Output JSON: {"root", "user", "projects": [ ... ], "notes": [ ... ]}
Each project holds metadata and short README excerpts, never source code.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", "dist", "build", ".git", "__pycache__",
    "target", ".next", ".nuxt", "out", "coverage", ".gradle", ".idea", ".vscode",
    ".tox", "site-packages", "bower_components", "Pods", ".dart_tool", ".cache",
    ".pytest_cache", ".mypy_cache", ".svn", ".hg", "vendor", "third_party",
    "DerivedData", ".terraform", ".serverless", ".turbo", ".parcel-cache",
}

LANG_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C",
    ".scala": "Scala", ".dart": "Dart", ".lua": "Lua", ".sh": "Shell", ".sql": "SQL",
    ".html": "HTML", ".css": "CSS", ".scss": "CSS", ".vue": "Vue", ".svelte": "Svelte",
    ".ex": "Elixir", ".exs": "Elixir", ".hs": "Haskell", ".r": "R", ".ipynb": "Jupyter",
    ".tf": "Terraform",
}
CODE_LANGS_EXCLUDED_FROM_DEPTH = {"HTML", "CSS", "SQL", "Shell", "Jupyter"}

MANIFESTS = [
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "pubspec.yaml", "mix.exs", "Package.swift",
    "CMakeLists.txt", "Makefile", "deno.json", "*.csproj", "*.sln",
]

CI_MARKERS = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci",
              ".travis.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml", ".drone.yml"]
DEPLOY_MARKERS = [
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yaml",
    "vercel.json", "netlify.toml", "fly.toml", "Procfile", "serverless.yml",
    "serverless.yaml", "render.yaml", "app.yaml", "railway.json", "heroku.yml",
    "k8s", "kubernetes", "helm", "terraform", "main.tf", "ansible", "nginx.conf",
    "firebase.json", "wrangler.toml", "cdk.json", "template.yaml", "Chart.yaml",
]
TEST_DIR_NAMES = {"tests", "test", "__tests__", "spec", "specs", "e2e", "cypress"}
TEST_FILE_RE = re.compile(r"(^test_.*\.py$|.*_test\.(py|go|rb|js|ts)$|.*\.(test|spec)\.(js|jsx|ts|tsx|mjs)$|.*Test\.java$|.*_spec\.rb$)")
ENTRY_NAMES = {
    "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py", "server.py", "cli.py",
    "index.js", "index.ts", "server.js", "server.ts", "app.js", "app.ts", "main.ts",
    "main.js", "main.go", "main.rs", "lib.rs", "Main.java", "Program.cs", "main.dart",
}
README_NAMES = ["README.md", "README.rst", "README.txt", "README", "readme.md", "Readme.md"]

FRAMEWORKS = {
    # name in dependency list (lowercase) -> display name
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt", "svelte": "Svelte",
    "@angular/core": "Angular", "express": "Express", "fastify": "Fastify", "koa": "Koa",
    "@nestjs/core": "NestJS", "flask": "Flask", "django": "Django", "fastapi": "FastAPI",
    "sqlalchemy": "SQLAlchemy", "prisma": "Prisma", "@prisma/client": "Prisma",
    "mongoose": "Mongoose", "sequelize": "Sequelize", "typeorm": "TypeORM",
    "tailwindcss": "Tailwind CSS", "pytest": "pytest", "jest": "Jest", "vitest": "Vitest",
    "playwright": "Playwright", "@playwright/test": "Playwright", "cypress": "Cypress",
    "socket.io": "Socket.IO", "graphql": "GraphQL", "apollo-server": "Apollo Server",
    "@apollo/client": "Apollo Client", "electron": "Electron", "react-native": "React Native",
    "expo": "Expo", "celery": "Celery", "redis": "Redis", "ioredis": "Redis",
    "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL", "psycopg": "PostgreSQL", "pg": "PostgreSQL", "asyncpg": "PostgreSQL",
    "pymongo": "MongoDB", "mongodb": "MongoDB", "mysql2": "MySQL", "pymysql": "MySQL",
    "sqlite3": "SQLite", "better-sqlite3": "SQLite", "kafka-python": "Kafka", "kafkajs": "Kafka",
    "pandas": "pandas", "numpy": "NumPy", "scikit-learn": "scikit-learn",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "keras": "Keras",
    "gin-gonic/gin": "Gin", "labstack/echo": "Echo", "gofiber/fiber": "Fiber",
    "actix-web": "Actix", "tokio": "Tokio", "axum": "Axum", "rocket": "Rocket",
    "spring-boot-starter-web": "Spring Boot", "pydantic": "Pydantic", "uvicorn": "Uvicorn",
    "gunicorn": "Gunicorn", "alembic": "Alembic", "trpc": "tRPC", "@trpc/server": "tRPC",
    "zod": "Zod", "webpack": "Webpack", "vite": "Vite", "rollup": "Rollup",
    "beautifulsoup4": "BeautifulSoup", "scrapy": "Scrapy", "selenium": "Selenium",
    "requests": "requests", "axios": "Axios", "docker": "Docker SDK",
}
# Dependencies that indicate a connection to a real external service.
INTEGRATIONS = {
    "stripe": "Stripe", "twilio": "Twilio", "@sendgrid/mail": "SendGrid", "sendgrid": "SendGrid",
    "boto3": "AWS", "aws-sdk": "AWS", "@aws-sdk": "AWS", "firebase": "Firebase",
    "firebase-admin": "Firebase", "@supabase/supabase-js": "Supabase", "supabase": "Supabase",
    "openai": "OpenAI API", "anthropic": "Anthropic API", "@anthropic-ai/sdk": "Anthropic API",
    "langchain": "LangChain", "slack_sdk": "Slack API", "@slack/bolt": "Slack API",
    "discord.py": "Discord API", "discord.js": "Discord API", "googleapis": "Google APIs",
    "google-api-python-client": "Google APIs", "razorpay": "Razorpay", "paypalrestsdk": "PayPal",
    "@sentry/node": "Sentry", "sentry-sdk": "Sentry", "mailgun": "Mailgun", "plaid": "Plaid",
    "shopify": "Shopify", "cloudinary": "Cloudinary", "mapbox-gl": "Mapbox", "algoliasearch": "Algolia",
    "telegraf": "Telegram Bot API", "python-telegram-bot": "Telegram Bot API", "tweepy": "X API",
    "octokit": "GitHub API", "@octokit/rest": "GitHub API", "pygithub": "GitHub API",
}

STRONG_TUTORIAL = re.compile(
    r"\b(tutorial|following along|follow along|udemy|coursera|codecademy|freecodecamp|"
    r"bootcamp|course project|class project|homework|assignment|lab exercise|"
    r"code ?along|from the (book|course|video)|youtube tutorial)\b", re.I)
WEAK_TUTORIAL = re.compile(
    r"\b(learning|learn|practice|exercise|boilerplate|starter|template|cloned? (of|from)|"
    r"my first|hello world|playground|sandbox|experiment)\b", re.I)
SCAFFOLD_README = re.compile(
    r"(bootstrapped with \[?create react app|this is a \[?next\.js\]?.*bootstrapped with|"
    r"getting started with create react app|this template provides a minimal setup to get react working in vite|"
    r"this is a \[vite\]|created with \[?angular cli|vue cli|npm create vite)", re.I)
REAL_WORLD_RE = re.compile(
    r"\b(production|deployed|live at|in use|used by|customers?|clients?|users?|paying|"
    r"internal tool|my (company|employer|business|startup)|freelance|contract(ed)?|"
    r"open[- ]sourced? and used)\b", re.I)
URL_RE = re.compile(r"https?://[^\s)>\]\"']+")


def run_git(path, *args, timeout=60):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    try:
        r = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", path, *args],
            capture_output=True, text=True, timeout=timeout, env=env,
            encoding="utf-8", errors="replace")
        if r.returncode != 0:
            return None
        return r.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def read_text(path, limit=200_000):
    try:
        if os.path.getsize(path) > 5_000_000:
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def find_readme(path):
    for n in README_NAMES:
        p = os.path.join(path, n)
        if os.path.isfile(p):
            return n, read_text(p)
    return None, ""


def has_marker(path):
    names = set(os.listdir(path)) if os.path.isdir(path) else set()
    if ".git" in names:
        return True
    if any(n in names for n in README_NAMES):
        return True
    for m in MANIFESTS:
        if "*" in m:
            suf = m.replace("*", "")
            if any(n.endswith(suf) for n in names):
                return True
        elif m in names:
            return True
    return False


def discover(root, notes):
    """Candidates: the root itself if it is a repo, else each immediate subdirectory.
    A container subdirectory (no markers, but children with markers) is expanded one level."""
    cands = []
    try:
        entries = sorted(os.listdir(root))
    except OSError as e:
        notes.append(f"cannot list {root}: {e}")
        return cands
    if os.path.isdir(os.path.join(root, ".git")):
        cands.append(root)
        return cands
    for name in entries:
        if name.startswith(".") or name in SKIP_DIRS:
            continue
        p = os.path.join(root, name)
        if not os.path.isdir(p) or os.path.islink(p):
            continue
        if has_marker(p):
            cands.append(p)
            continue
        # container folder: look one level down
        try:
            kids = [k for k in sorted(os.listdir(p)) if not k.startswith(".") and k not in SKIP_DIRS]
        except OSError:
            notes.append(f"unreadable directory skipped: {p}")
            continue
        found = False
        for k in kids:
            kp = os.path.join(p, k)
            if os.path.isdir(kp) and not os.path.islink(kp) and has_marker(kp):
                cands.append(kp)
                found = True
        if not found and kids:
            # a plain folder of loose code with no markers; keep it, it may still be a project
            cands.append(p)
    return cands


def walk_project(path, max_files=6000):
    """Walk without following symlinks. Returns counters and flags."""
    lang_files, lang_loc = Counter(), Counter()
    total_files = 0
    tests = set()
    ci = set()
    deploy = set()
    entry = []
    docs_files = 0
    licenses = []
    unreadable = 0
    has_vendor = False
    top_dirs = []
    source_files = []
    truncated = False
    root_len = len(path.rstrip(os.sep)) + 1
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False,
                                                onerror=lambda e: None):
        rel_dir = dirpath[root_len:] if len(dirpath) >= root_len else ""
        depth = rel_dir.count(os.sep) + (1 if rel_dir else 0)
        keep = []
        for d in dirnames:
            if d in SKIP_DIRS:
                if d in ("vendor", "third_party"):
                    has_vendor = True
                continue
            keep.append(d)
            low = d.lower()
            full_rel = os.path.join(rel_dir, d) if rel_dir else d
            if low in TEST_DIR_NAMES:
                tests.add(full_rel)
            if d in DEPLOY_MARKERS or low in DEPLOY_MARKERS:
                deploy.add(full_rel)
            for m in CI_MARKERS:
                if full_rel == m:
                    ci.add(full_rel)
        dirnames[:] = keep
        if depth == 0:
            top_dirs = sorted(keep)
        for fn in filenames:
            total_files += 1
            if total_files > max_files:
                truncated = True
                dirnames[:] = []
                break
            fp = os.path.join(dirpath, fn)
            rel = os.path.join(rel_dir, fn) if rel_dir else fn
            if fn in CI_MARKERS:
                ci.add(rel)
            if fn in DEPLOY_MARKERS:
                deploy.add(rel)
            if TEST_FILE_RE.match(fn):
                tests.add(rel)
            if fn in ENTRY_NAMES and depth <= 2:
                entry.append(rel)
            if fn.upper().startswith(("LICENSE", "LICENCE", "COPYING")) and depth <= 3:
                licenses.append(rel)
            ext = os.path.splitext(fn)[1].lower()
            if ext in (".md", ".rst", ".txt") and (rel_dir.startswith("docs") or rel_dir.startswith("doc")):
                docs_files += 1
            lang = LANG_BY_EXT.get(ext)
            if lang:
                lang_files[lang] += 1
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    unreadable += 1
                    continue
                if size <= 500_000 and len(source_files) < 3000 and lang not in ("Jupyter",):
                    try:
                        with open(fp, "rb") as f:
                            lang_loc[lang] += sum(1 for _ in f)
                        source_files.append(rel)
                    except OSError:
                        unreadable += 1
    return {
        "total_files": total_files, "truncated": truncated,
        "lang_files": dict(lang_files), "lang_loc": dict(lang_loc),
        "tests": sorted(tests)[:15], "test_file_count": len([t for t in tests if os.sep in t or "." in t]),
        "ci": sorted(ci), "deploy": sorted(deploy), "entry_points": entry[:10],
        "docs_files": docs_files, "licenses": licenses[:6], "unreadable": unreadable,
        "has_vendor_dir": has_vendor, "top_dirs": top_dirs[:25],
        "source_files": source_files,
    }


def parse_manifests(path):
    found, deps, meta = [], set(), {}
    try:
        names = os.listdir(path)
    except OSError:
        return found, [], meta
    for n in names:
        if n in MANIFESTS or any(m.startswith("*") and n.endswith(m[1:]) for m in MANIFESTS):
            found.append(n)
    # package.json
    pj = os.path.join(path, "package.json")
    if os.path.isfile(pj):
        try:
            d = json.loads(read_text(pj))
            meta["package_name"] = d.get("name")
            meta["version"] = d.get("version")
            meta["description"] = d.get("description")
            meta["license"] = d.get("license")
            repo = d.get("repository")
            meta["repository"] = repo.get("url") if isinstance(repo, dict) else repo
            meta["author"] = d.get("author") if isinstance(d.get("author"), str) else (d.get("author") or {}).get("name")
            meta["scripts"] = sorted((d.get("scripts") or {}).keys())[:15]
            meta["workspaces"] = d.get("workspaces")
            for k in ("dependencies", "devDependencies", "peerDependencies"):
                deps.update((d.get(k) or {}).keys())
        except (ValueError, AttributeError):
            pass
    # pyproject / Cargo via tomllib
    for fn in ("pyproject.toml", "Cargo.toml"):
        fp = os.path.join(path, fn)
        if os.path.isfile(fp):
            txt = read_text(fp)
            data = {}
            if tomllib:
                try:
                    data = tomllib.loads(txt)
                except Exception:
                    data = {}
            proj = data.get("project") or data.get("package") or (data.get("tool", {}).get("poetry") or {})
            if proj:
                meta.setdefault("package_name", proj.get("name"))
                meta.setdefault("version", proj.get("version") if isinstance(proj.get("version"), str) else None)
                meta.setdefault("description", proj.get("description"))
                lic = proj.get("license")
                meta.setdefault("license", lic if isinstance(lic, str) else (lic or {}).get("text") if isinstance(lic, dict) else None)
                authors = proj.get("authors")
                if authors and "author" not in meta:
                    a = authors[0]
                    meta["author"] = a if isinstance(a, str) else a.get("name")
                urls = proj.get("urls") or {}
                meta.setdefault("repository", proj.get("repository") or urls.get("Repository") or urls.get("Homepage"))
            for dep in (proj.get("dependencies") or []) if isinstance(proj.get("dependencies"), list) else []:
                deps.add(re.split(r"[<>=!~\[; ]", dep, maxsplit=1)[0].lower())
            for dep in (data.get("dependencies") or {}):
                deps.add(dep.lower())
            for dep in ((data.get("tool", {}).get("poetry") or {}).get("dependencies") or {}):
                deps.add(dep.lower())
            if not tomllib:
                m = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
                if m:
                    meta.setdefault("package_name", m.group(1))
    # requirements.txt
    rq = os.path.join(path, "requirements.txt")
    if os.path.isfile(rq):
        for line in read_text(rq).splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "-")):
                deps.add(re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].lower())
    # go.mod
    gm = os.path.join(path, "go.mod")
    if os.path.isfile(gm):
        txt = read_text(gm)
        m = re.search(r"^module\s+(\S+)", txt, re.M)
        if m:
            meta.setdefault("package_name", m.group(1))
        for mm in re.finditer(r"^\s*(?:require\s+)?([\w.\-]+\.[\w.\-]+/[\w./\-]+)\s+v", txt, re.M):
            deps.add(mm.group(1).lower())
    # pom.xml
    pom = os.path.join(path, "pom.xml")
    if os.path.isfile(pom):
        txt = read_text(pom)
        m = re.search(r"<artifactId>([^<]+)</artifactId>", txt)
        if m:
            meta.setdefault("package_name", m.group(1))
        for mm in re.finditer(r"<artifactId>([^<]+)</artifactId>", txt):
            deps.add(mm.group(1).lower())
    # Gemfile / composer.json (names only)
    gf = os.path.join(path, "Gemfile")
    if os.path.isfile(gf):
        for mm in re.finditer(r"^\s*gem\s+['\"]([^'\"]+)", read_text(gf), re.M):
            deps.add(mm.group(1).lower())
    return sorted(set(found)), sorted(deps), meta


def detect_stack(deps, walk):
    lower = {d.lower() for d in deps}
    frameworks, integrations = set(), set()
    for d in lower:
        for key, disp in FRAMEWORKS.items():
            if d == key or d.endswith("/" + key) or ("/" in key and key in d):
                frameworks.add(disp)
        for key, disp in INTEGRATIONS.items():
            if d == key or d.startswith(key):
                integrations.add(disp)
    if any(x.endswith("Dockerfile") or x.startswith("docker-compose") or x.startswith("compose.") for x in walk["deploy"]):
        frameworks.add("Docker")
    if any(".github/workflows" in x for x in walk["ci"]):
        frameworks.add("GitHub Actions")
    langs = sorted(walk["lang_loc"].items(), key=lambda kv: -kv[1])
    return [l for l, _ in langs], sorted(frameworks), sorted(integrations)


def parse_remote(url):
    """Return (host, owner, repo) from a git remote URL or (None, None, None)."""
    if not url:
        return None, None, None
    m = re.match(r"(?:git@|ssh://git@|https?://(?:[^@/]+@)?)([^:/]+)[:/]+([^/]+)/([^/\s]+?)(?:\.git)?/?$", url.strip())
    if m:
        return m.group(1).lower(), m.group(2), m.group(3)
    return None, None, None


def git_facts(path, user_emails, user_names, max_commits=5000):
    out = {"is_git": False}
    top = run_git(path, "rev-parse", "--show-toplevel")
    if not top:
        return out
    top = top.strip()
    out["is_git"] = True
    out["git_root_is_project"] = os.path.realpath(top) == os.path.realpath(path)
    remotes_raw = run_git(path, "remote", "-v") or ""
    remotes = {}
    for line in remotes_raw.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes[parts[0]] = parts[1]
    out["remotes"] = remotes
    origin = remotes.get("origin")
    host, owner, repo = parse_remote(origin)
    out["origin_url"] = origin
    out["origin_host"], out["origin_owner"], out["origin_repo"] = host, owner, repo
    out["has_upstream_remote"] = "upstream" in remotes

    scope = [] if out["git_root_is_project"] else ["--", "."]
    log = run_git(path, "log", f"-n{max_commits}", "--no-merges",
                  "--format=@@%H|%an|%ae|%aI", "--name-only", *scope, timeout=120)
    if log is None:
        out["commit_count"] = 0
        out["note"] = "git log failed or the repository has no commits"
        return out
    authors = Counter()
    author_emails = {}
    commits = []
    cur = None
    for line in log.splitlines():
        if line.startswith("@@"):
            h, name, email, date = (line[2:].split("|", 3) + ["", "", "", ""])[:4]
            cur = {"name": name, "email": email.lower(), "date": date, "files": []}
            commits.append(cur)
        elif line.strip() and cur is not None:
            cur["files"].append(line.strip())
    em = {e.lower() for e in user_emails}
    nm = {n.lower() for n in user_names}

    def is_user(c):
        return c["email"] in em or c["name"].lower() in nm

    user_commits = [c for c in commits if is_user(c)]
    for c in commits:
        authors[c["name"]] += 1
        author_emails.setdefault(c["name"], c["email"])
    all_files, user_files = set(), set()
    for c in commits:
        all_files.update(c["files"])
    for c in user_commits:
        user_files.update(c["files"])
    dates = sorted(c["date"] for c in commits if c["date"])
    udates = sorted(c["date"] for c in user_commits if c["date"])
    out.update({
        "commit_count": len(commits),
        "commit_count_capped": len(commits) >= max_commits,
        "user_commit_count": len(user_commits),
        "user_share": round(len(user_commits) / len(commits), 3) if commits else 0.0,
        "first_commit": dates[0][:10] if dates else None,
        "last_commit": dates[-1][:10] if dates else None,
        "user_first_commit": udates[0][:10] if udates else None,
        "user_last_commit": udates[-1][:10] if udates else None,
        "top_authors": [{"name": n, "commits": c} for n, c in authors.most_common(5)],
        "files_in_history": len(all_files),
        "files_touched_by_user": len(user_files),
        "user_file_share": round(len(user_files) / len(all_files), 3) if all_files else 0.0,
    })
    return out


def license_holders(path, licenses):
    holders = []
    for rel in licenses:
        txt = read_text(os.path.join(path, rel), 4000)
        for m in re.finditer(r"copyright\s*(?:\(c\)|©)?\s*(?:\d{4}(?:\s*[-,]\s*\d{4})*)?\s*,?\s*([^\n]+)", txt, re.I):
            h = m.group(1).strip().rstrip(".")
            if h and not h.lower().startswith(("notice", "holder", "and permission")):
                holders.append({"file": rel, "holder": h[:120]})
                break
    return holders


def monorepo_children(path, top_dirs, meta):
    kids = []
    for group in ("apps", "packages", "services", "libs", "modules", "cmd"):
        gp = os.path.join(path, group)
        if os.path.isdir(gp):
            try:
                for k in sorted(os.listdir(gp)):
                    kp = os.path.join(gp, k)
                    if os.path.isdir(kp) and not k.startswith(".") and k not in SKIP_DIRS:
                        mf, deps, m2 = parse_manifests(kp)
                        kids.append({"path": os.path.join(group, k), "manifests": mf,
                                     "package_name": m2.get("package_name"), "dependency_count": len(deps)})
            except OSError:
                pass
    return kids


def scan_project(path, user, deep=True):
    name = os.path.basename(path.rstrip(os.sep))
    p = {"name": name, "path": path}
    readme_name, readme = find_readme(path)
    walk = walk_project(path, max_files=6000 if deep else 1500)
    manifests, deps, meta = parse_manifests(path)
    langs, frameworks, integrations = detect_stack(deps, walk)
    g = git_facts(path, user["emails"], user["names"], 5000 if deep else 800)
    holders = license_holders(path, walk["licenses"])

    text_for_signals = " ".join([name, meta.get("package_name") or "", meta.get("description") or "", readme[:6000]])
    strong = sorted({m.group(0).lower() for m in STRONG_TUTORIAL.finditer(text_for_signals)})
    weak = sorted({m.group(0).lower() for m in WEAK_TUTORIAL.finditer(text_for_signals)})
    scaffold = bool(SCAFFOLD_README.search(readme[:3000]))
    loc_total = sum(walk["lang_loc"].values())
    src_files = sum(v for k, v in walk["lang_files"].items() if k not in CODE_LANGS_EXCLUDED_FROM_DEPTH)
    any_code_files = sum(walk["lang_files"].values())
    toy = []
    if loc_total < 60 and src_files <= 2:
        toy.append(f"only {any_code_files} code file(s) and {loc_total} lines")
    if not readme and not manifests and src_files <= 3:
        toy.append("no README, no manifest, almost no code")
    if g.get("is_git") and g.get("commit_count", 0) == 0:
        toy.append("empty repository")

    real_hits = sorted({m.group(0).lower() for m in REAL_WORLD_RE.finditer(readme[:8000])})
    urls = []
    for u in URL_RE.findall(readme[:8000]):
        u = u.rstrip(".,;")
        if not re.search(r"(shields\.io|badge|github\.com/.+/(actions|workflows)|travis-ci|codecov|img\.|localhost|127\.0\.0\.1|example\.com|npmjs\.com|pypi\.org)", u, re.I):
            urls.append(u)

    p.update({
        "readme_file": readme_name,
        "readme_chars": len(readme),
        "readme_excerpt": readme[:2500],
        "manifests": manifests,
        "manifest_meta": {k: v for k, v in meta.items() if v},
        "dependency_count": len(deps),
        "dependencies_sample": deps[:60],
        "languages": langs,
        "lines_of_code": loc_total,
        "lang_loc": walk["lang_loc"],
        "frameworks": frameworks,
        "integrations": integrations,
        "total_files": walk["total_files"],
        "walk_truncated": walk["truncated"],
        "top_dirs": walk["top_dirs"],
        "entry_points": walk["entry_points"],
        "tests": {"paths": walk["tests"], "count": walk["test_file_count"]},
        "ci": walk["ci"],
        "deploy": walk["deploy"],
        "docs_files": walk["docs_files"],
        "licenses": walk["licenses"],
        "license_holders": holders,
        "has_vendor_dir": walk["has_vendor_dir"],
        "unreadable_files": walk["unreadable"],
        "git": g,
        "real_world_phrases": real_hits[:10],
        "urls_in_readme": urls[:6],
        "signals": {
            "tutorial_strong": strong, "tutorial_weak": weak,
            "scaffold_readme": scaffold, "toy": toy,
        },
        "monorepo_children": monorepo_children(path, walk["top_dirs"], meta),
        "workspaces": meta.get("workspaces"),
        "scan_depth": "deep" if deep else "quick",
    })
    # Keep source_files out of the output; it can be large.
    return p


def _norm(x):
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def match_pins(pins, projects, root):
    """Resolve user-named projects to scanned candidates.
    A pin matches by exact folder name, by path (absolute or relative to root), or by
    normalised name (case, dashes and underscores ignored). A substring match is used
    only when it is unambiguous. Returns (pinned_paths, unmatched, ambiguous)."""
    pinned, unmatched, ambiguous = set(), [], {}
    for pin in pins:
        raw = pin.strip().strip('"\'')
        if not raw:
            continue
        cand_abs = os.path.abspath(raw if os.path.isabs(raw) else os.path.join(root, raw))
        hits = [p for p in projects if os.path.abspath(p["path"]) == cand_abs]
        if not hits:
            n = _norm(os.path.basename(raw.rstrip("/\\")))
            hits = [p for p in projects if _norm(p["name"]) == n]
        if not hits and len(_norm(raw)) >= 3:
            n = _norm(raw)
            hits = [p for p in projects if n in _norm(p["name"])]
        if not hits:
            unmatched.append(raw)
        elif len(hits) > 1:
            ambiguous[raw] = [h["name"] for h in hits]
        else:
            pinned.add(hits[0]["path"])
    return pinned, unmatched, ambiguous


def quick_score(p):
    s = 0
    s += min(p["lines_of_code"], 20000) / 2000
    s += 2 if p["tests"]["count"] else 0
    s += 1 if p["ci"] else 0
    s += 1 if p["deploy"] else 0
    g = p["git"]
    if g.get("is_git"):
        s += min(g.get("user_commit_count", 0), 100) / 20
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--user-email", action="append", default=[])
    ap.add_argument("--user-name", action="append", default=[])
    ap.add_argument("--github-user", default=None)
    ap.add_argument("--max-deep", type=int, default=40,
                    help="deep-read at most this many candidates after the quick pass")
    ap.add_argument("--pin", action="append", default=[],
                    help="project the user asked to feature (folder name or path). Repeatable, "
                         "or comma-separated. Pinned projects are always deep-read.")
    ap.add_argument("--out", default=None, help="write JSON here (default stdout)")
    a = ap.parse_args()
    a.pin = [x for item in a.pin for x in item.split(",") if x.strip()]

    root = os.path.abspath(os.path.expanduser(a.root))
    notes = []
    if not os.path.isdir(root):
        print(json.dumps({"error": f"not a directory: {root}"}))
        sys.exit(2)

    emails, names = list(a.user_email), list(a.user_name)
    if not emails and not names:
        ge = (run_git(root, "config", "--get", "user.email") or "").strip()
        gn = (run_git(root, "config", "--get", "user.name") or "").strip()
        if ge:
            emails.append(ge)
        if gn:
            names.append(gn)
        if ge or gn:
            notes.append("user identity taken from git config; pass --user-email/--user-name to override")
    if not emails and not names:
        notes.append("no user identity known: commit share cannot be computed. Ask the user for the name or email they commit with.")
    user = {"emails": emails, "names": names, "github": a.github_user}

    cands = discover(root, notes)
    if not cands:
        print(json.dumps({"root": root, "user": user, "projects": [],
                          "notes": notes + ["no candidate projects found (empty directory?)"]}, indent=2))
        return

    quick = []
    for c in cands:
        try:
            quick.append(scan_project(c, user, deep=False))
        except Exception as e:  # keep going on odd directories
            notes.append(f"could not scan {c}: {e}")
    quick.sort(key=quick_score, reverse=True)
    pinned_paths, pin_unmatched, pin_ambiguous = match_pins(a.pin, quick, root)
    for n in pin_unmatched:
        notes.append(f"requested project not found under the directory: {n}")
    for n, opts in pin_ambiguous.items():
        notes.append(f"requested project '{n}' matches several folders ({', '.join(opts)}); ask the user which one")
    for p in quick:
        p["pinned"] = p["path"] in pinned_paths
    # Pinned projects always get the deep read, even past the cap.
    deep_set = [p for p in quick if p["pinned"]]
    deep_set += [p for p in quick if not p["pinned"]][: max(a.max_deep - len(deep_set), 0)]
    if len(quick) > a.max_deep:
        notes.append(f"{len(quick)} candidates found; deep read capped at the top {a.max_deep} after a quick pass")
    projects = []
    for p in deep_set:
        try:
            projects.append(scan_project(p["path"], user, deep=True))
        except Exception as e:
            notes.append(f"deep scan failed for {p['path']}: {e}")
            projects.append(p)
    deep_paths = {d["path"] for d in deep_set}
    for p in projects:
        p["pinned"] = p["path"] in pinned_paths
    for p in quick:
        if p["path"] not in deep_paths:
            p["skipped_reason"] = "outside the deep-read cap"
            projects.append(p)
    result = {"root": root, "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "user": user, "pin_requests": a.pin, "pin_unmatched": pin_unmatched,
              "pin_ambiguous": pin_ambiguous, "projects": projects, "notes": notes}
    txt = json.dumps(result, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt)
    else:
        print(txt)
    # human summary on stderr
    print(f"\nScanned {len(projects)} candidate(s) under {root}", file=sys.stderr)
    for p in projects:
        g = p["git"]
        gs = (f"{g.get('user_commit_count', 0)}/{g.get('commit_count', 0)} commits"
              if g.get("is_git") else "no git")
        star = "*" if p.get("pinned") else " "
        print(f" {star}{p['name']:<28} {p['lines_of_code']:>7} LOC  {gs:<18} {', '.join(p['languages'][:3])}", file=sys.stderr)
    for n in notes:
        print(f"  note: {n}", file=sys.stderr)


if __name__ == "__main__":
    main()

<h1 align="center">resume-from-projects</h1>

<p align="center">
  <em>Your projects, minus the ones you didn't write.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
  <img src="https://img.shields.io/badge/python-3.8%2B-111111?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/output-docx%20%2B%20pdf-111111?style=flat-square" alt="Outputs docx and PDF">
  <img src="https://img.shields.io/badge/works%20with-any%20SKILL.md%20agent-111111?style=flat-square" alt="Works with any agent that reads SKILL.md">
</p>

An agent skill that reads a folder of software projects, throws out the clones, forks, tutorials and other people's code, ranks what is left, and builds a one-page resume as a Word file and a matching PDF.

It never invents a number, never touches your project directories, and never sends your source code anywhere.

## Why

Every developer folder has the same mix: three tutorial clones, a fork you fixed one bug in, two abandoned experiments, and the one project you actually built and shipped. A generic "write my resume" prompt puts all of them on the page, equally weighted, with invented metrics.

This skill does the boring part first. It checks authorship and origin, shows you the evidence, and only then writes the resume.

## What it does

1. **Scans** every project folder: README, manifests, structure, entry points, tests, CI, deploy config and git history.
2. **Verifies** each project is yours: origin owner, upstream fork markers, commit authorship, license and manifest authors, vendored code, tutorial wording, unmodified scaffolds, toy projects, well-known public names.
3. **Ranks** what passes on real-world signal, technical depth, your share of the work, quality evidence, recency and fit to the role you are targeting.
4. **Writes** plain, specific bullets, with an evidence entry for every number and strong claim.
5. **Builds** a one-page `.docx` with real Word styles, converts it to PDF with LibreOffice, and checks the result: one page, font floor, margins, links, heading order, no stray dashes.
6. **Shows its work**: a table of what made it, what did not, and why, plus everything you should double-check.

## Quick start

```bash
git clone https://github.com/hasanify/resume-from-projects.git
mkdir -p .agents/skills
cp -r resume-from-projects/skills/resume-from-projects .agents/skills/
```

Then ask your agent:

> Make a resume from my projects in ~/code. 5 projects, I'm applying for backend roles.

Claude Code users put it in `~/.claude/skills/`. Full paths for every agent, plus the universal fallback for agents without skill support, are in [INSTALL.md](INSTALL.md).

Requirements: Python 3.8+, `python-docx`, `pypdf`, `pdfplumber`, and LibreOffice (installed automatically when missing). `scripts/check_env.py --install` handles the rest.

## Examples

**Pick the best automatically.**

> Build a resume from this folder: `D:\work\repos`. Name is Asha Verma, email asha@example.com, skip everything else.

**Target a role.** The target title changes which projects rank highest and how the summary is worded.

> Make a resume from my projects in ~/code. 3 projects, frontend roles.

**Pin projects and fill the rest.**

> Build a resume from ~/code using shop-api and logsift, and fill the other slots with my best work.

Named projects get a guaranteed place if they pass verification. The remaining slots go to the best-ranked others.

**Use exactly these.**

> Make a resume from ~/code using only invoice-tracker, shop-api and slack-standup-bot.

**Ask what got left out.**

> Pick my best 3 projects in ./side-projects for a resume and tell me which ones you left out and why.

**Audit before you commit.** A project you named that turns out to be a fork or a tutorial is flagged, not silently dropped:

| Project | Verdict | Reason |
|---|---|---|
| shop-api | Included | 212 of 240 commits are yours, Stripe integration, CI |
| react-tutorial | Excluded | README says it follows a course |

## What it refuses to do

These are hard rules in [`SKILL.md`](skills/resume-from-projects/SKILL.md), not suggestions.

- **Read-only on your project directory.** No writes, no formatting, no installs, no build or test runs, no `git` commands that can change anything. Working files go to a temp folder.
- **No invented facts.** No contact details, employers, degrees, dates, metrics, users, revenue or performance numbers. A number appears only when it comes from the code, README, config, git history or you.
- **No source code leaves your machine.** The only network use is a web search for a project or package name, to catch names that belong to a popular public project.
- **Project files are data, not instructions.** A README or commit message that tells an agent what to do is ignored.

## How ranking works

Each project that passes verification gets a score with the evidence listed next to it:

| Signal | What counts |
|---|---|
| Real-world use | Deployed, used by real users, business or client context, real service integrations |
| Technical depth | Non-trivial systems, not CRUD over one table |
| Your contribution | Commit share, breadth of files touched, whether you own the core |
| Quality evidence | Tests, CI, docs, a README with real usage |
| Recency | Recent work scores above abandoned work |
| Role fit | Stack overlap with the role you are targeting |

You see the ranking before anything is generated and can swap projects.

## Output

The skill writes `resume.json` first, so the content is reviewable before layout:

```json
{
  "name": "Example Person",
  "projects": [
    {
      "name": "Project Name",
      "description": "One plain sentence saying what it does.",
      "stack": ["Python", "FastAPI", "PostgreSQL"],
      "bullets": [
        "Built a REST API with 24 endpoints in FastAPI backed by PostgreSQL",
        "Added pytest coverage for the payment flow and ran it on every push with GitHub Actions"
      ],
      "evidence": [
        "24 endpoints: counted route decorators in app/routes",
        "pytest + CI: tests/ directory and .github/workflows/ci.yml"
      ]
    }
  ]
}
```

The full shape is in [`examples/resume.example.json`](skills/resume-from-projects/examples/resume.example.json). The built resume is one page, Letter or A4, one font family, a single contact line with clickable links, sections in order Summary, Projects, Experience, Skills, Education. The exact spec is in [`references/layout-spec.md`](skills/resume-from-projects/references/layout-spec.md).

## Commands it runs

All paths are relative to the skill folder. Every step is a plain Python script, so you can run them yourself:

```bash
python3 scripts/check_env.py --install
python3 scripts/scan_projects.py "<DIR>" --out "$WORK/scan.json"
python3 scripts/check_origin.py "$WORK/scan.json" --out "$WORK/verdicts.json"
python3 scripts/rank_projects.py "$WORK/scan.json" "$WORK/verdicts.json" --top 5 --out "$WORK/ranking.json"
python3 scripts/check_writing.py "$WORK/resume.json"
python3 scripts/build_resume.py "$WORK/resume.json" --outdir "$WORK/out" --level 0
python3 scripts/verify_pdf.py "$WORK/out/<name>.pdf" --resume "$WORK/resume.json"
```

## FAQ

**Does it need my GitHub account?**
No. It reads local git history and config. Pass your commit email or handle when they differ from your git config. A web search is used only for name collisions, and it is skipped if your agent has no search tool.

**What if a project has no git history?**
It can still count, but authorship cannot be proven. The skill marks it "confirm" and asks you. Unanswered stays out.

**What if I insist on a project it flagged?**
It will include it, describe only what the evidence shows you did, and list it under "double-check" in the wrap-up. It will not write claims the code and history do not support.

**Can it produce more than one page?**
No. If content overflows it tightens wording, then spacing, then drops the lowest-ranked project. Body text never drops below 9.5 pt.

**Does it work outside Claude Code?**
Yes. It is a plain `SKILL.md` folder with Python scripts and no agent-specific tools: Codex, OpenCode, Antigravity, Gemini CLI, Cursor, Windsurf, Claude Code, or any agent that can read files and run shell commands.

## License

[MIT](LICENSE).

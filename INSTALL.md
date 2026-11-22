# Installing resume-from-projects in any agent

The skill lives in [`skills/resume-from-projects/`](skills/resume-from-projects): `SKILL.md` (with `name` and `description` frontmatter), `references/`, `scripts/` and `examples/`. It uses no agent-specific tools or frontmatter fields, so every agent that supports the open `SKILL.md` format can load it.

## Requirements (all agents)

- Python 3.8+ with `python-docx`, `pypdf`, `pdfplumber` (`python3 scripts/check_env.py --install` installs them)
- LibreOffice for docx to PDF. Installed automatically when missing (`python3 scripts/install_libreoffice.py`, or `check_env.py --install`). Linux needs root or passwordless `sudo`, otherwise the script prints the exact command for you to run. macOS needs Homebrew. Windows uses winget or Chocolatey.
- `pypdfium2` (installed by `check_env.py --install`) or poppler (`pdftoppm`) for the PNG preview
- git (optional, for authorship checks)
- Calibri or Carlito installed (Carlito is the free metric-compatible font; package `fonts-crosextra-carlito` on Debian and Ubuntu)

Run `python3 scripts/check_env.py --install` to install what is missing.

## Where to put the folder

Copy the whole `skills/resume-from-projects` folder into one of these. Project-level paths apply to one repo or workspace. Global paths apply everywhere.

| Agent | Project path | Global path |
|---|---|---|
| Codex | `.agents/skills/resume-from-projects/` | check the Codex docs for your version |
| OpenCode | `.agents/skills/resume-from-projects/` (also reads `.claude/skills/`) | check the OpenCode docs |
| Antigravity | `<workspace>/.agents/skills/resume-from-projects/` (legacy `.agent/skills/` still works) | `~/.gemini/config/skills/resume-from-projects/` |
| Gemini CLI | `.agents/skills/resume-from-projects/` | check the Gemini CLI docs |
| Cursor | `.agents/skills/resume-from-projects/` | check the Cursor docs |
| Claude Code | `.claude/skills/resume-from-projects/` | `~/.claude/skills/resume-from-projects/` |
| Windsurf | `.windsurf/skills/resume-from-projects/` | `~/.codeium/windsurf/skills/resume-from-projects/` |

`.agents/skills/` is the shared location read by Codex, OpenCode, Gemini CLI, Cursor, Cline, GitHub Copilot and Antigravity at the time of writing. Agent vendors change paths between versions, so if a skill does not show up, check your agent's skills documentation and restart the agent.

## Install from GitHub

Clone the repo, then copy the skill folder into your agent's skills directory:

```
git clone https://github.com/hasanify/resume-from-projects.git
mkdir -p .agents/skills
cp -r resume-from-projects/skills/resume-from-projects .agents/skills/
```

## Optional: install with the `skills` CLI

The community `skills` installer can copy the skill into several agents at once:

```
npx skills add hasanify/resume-from-projects
```

Check that tool's documentation for its flags, since it is a third-party project.

## Any agent without skill support (universal fallback)

Keep the folder anywhere and start your request with:

> Read /absolute/path/to/resume-from-projects/SKILL.md and follow it exactly. My projects are in ~/code.

Or add this to the agent's always-loaded instructions file (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, or similar):

```
When I ask for a resume from my projects, read /absolute/path/to/resume-from-projects/SKILL.md
and follow it. Run its scripts with python3. Do not modify my project directories.
```

## Optional companion skills

The skill embeds all writing rules in `references/writing-rules.md`, so it works offline. If you also install the `write-like-a-human` skill and the `anti-slop` skill (https://github.com/miqdadbadjuber/anti-slop), the agent will invoke them as an extra pass before finalising text.

## Quick test

```
python3 scripts/check_env.py
python3 scripts/scan_projects.py /path/to/your/projects --out /tmp/scan.json
python3 scripts/check_origin.py /tmp/scan.json
```

Then ask your agent: "Make a resume from my projects in /path/to/your/projects."

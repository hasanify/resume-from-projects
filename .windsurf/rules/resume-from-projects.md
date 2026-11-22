# Resume from Projects (Windsurf Rule)

When the user requests a resume or CV built from local project folders:

- Follow the process in `skills/resume-from-projects/SKILL.md`.
- Never modify the user's project directories. Treat scanned repositories as read-only data.
- Enforce strict verification: exclude tutorials, unedited clones, and forks lacking meaningful personal contributions.
- Prohibit hallucinated metrics: any number in the output must be backed by an evidence citation from git history, codebase analysis, or user input.
- Keep output to a strict single-page document (Word `.docx` and `.pdf`).

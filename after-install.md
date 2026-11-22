# resume-from-projects installed

You can now generate tailored, evidence-backed one-page resumes directly from your project folders.

## Triggering the skill

Ask your agent:

- *"Make a resume from my projects in ~/code."*
- *"Build a one-page resume from this folder for freelance backend pitches."*
- *"Pick my best 4 projects from D:\repos and draft a resume for a senior full-stack engineer role."*

## How it works

1. **Scans** project folders (README, manifests, git log, tests, CI).
2. **Verifies** your authorship (flags tutorials, course clones, forks, and toy scaffolds).
3. **Ranks** projects on real-world impact, technical depth, and role fit.
4. **Drafts** clean, grounded bullets with zero hallucinated metrics.
5. **Generates** a styled `.docx` and pixel-perfect `.pdf` via LibreOffice.

## Requirements

Ensure Python 3.8+ and LibreOffice are installed. Run:

```bash
python scripts/check_env.py --install
```

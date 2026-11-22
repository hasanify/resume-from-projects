# GitHub Copilot Instructions for resume-from-projects

This repository provides an AI agent skill that analyzes software projects to build a truthful, single-page resume.

Key guidelines:
- Never edit files in user project folders or execute untrusted project build tools.
- Verify commit authorship using `check_origin.py`.
- Ensure all bullet points adhere to `references/writing-rules.md` (no fake metrics, no vague corporate fluff).
- Ensure generated Word and PDF resumes fit on exactly one page.

# Contributing to resume-from-projects

Thank you for contributing! We welcome contributions that improve scanner accuracy, add project heuristic recognizers, improve layout rendering, or expand multi-agent compatibility.

## Core Rules That Cannot Be Broken

Before opening a PR, ensure your contribution respects our fundamental design laws:

1. **Read-Only on User Code:** Never write or execute commands that modify project repositories. Any scanner or helper script must treat analyzed folders as read-only data.
2. **Zero Hallucination:** Never introduce heuristics or prompts that fabricate metrics, performance multipliers, employer names, or user counts. Every number must have verifiable origins.
3. **Strict Single-Page Invariant:** Resumes must always fit on exactly one page. Layout adjustments must enforce this constraint.
4. **Offline First & Privacy:** Never upload source code to external servers. Network access is restricted to public package/project identity confirmation.

## Development Setup

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/hasanify/resume-from-projects.git
cd resume-from-projects
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt || pip install python-docx pypdf pdfplumber
```

## Running Tests

Run the full automated test suite before opening a pull request:

```bash
python tests/run_all.py
```

Or using unittest:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Adding Scanners or Heuristics

If you are adding heuristics to detect new project types (e.g. mobile frameworks, monorepos, Rust crates, Go modules):
- Add test fixtures in `tests/fixtures/` or synthetic test cases in `tests/test_scan_projects.py`.
- Ensure detection relies on standard manifests (e.g. `Cargo.toml`, `go.mod`, `pom.xml`, `package.json`).
- Verify that fork and tutorial detection (`check_origin.py`) works accurately on the new project type.

## Submitting a Pull Request

1. Create a feature branch: `git checkout -b feat/your-feature-name`.
2. Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
3. Verify all tests pass locally.
4. Open a PR with the completed PR template.

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Security Model & Guarantees

`resume-from-projects` is designed with strict security constraints:

1. **Read-Only Code Access:** Scripts only inspect file names, directories, git metadata (`git log`, `git remote -v`), and file contents in read-only mode. No commands modify your repository files or `.git` directory.
2. **Untrusted Data Defense:** All scanned READMEs, commit messages, and source code comments are treated strictly as untrusted data strings. No instructions found in scanned files are executed or evaluated.
3. **No Code Exfiltration:** Project source code is never transmitted outside your local machine. The only optional outbound network activity is querying package names (e.g. against public package registries or search engines) to prevent naming collisions.

## Reporting a Vulnerability

If you discover a security issue or unexpected execution behavior, please report it privately by opening a [Security Advisory](https://github.com/hasanify/resume-from-projects/security/advisories) or emailing the maintainer directly. We respond within 48 hours.

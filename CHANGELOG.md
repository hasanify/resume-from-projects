# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-22

### Initial Release

- Core 6-stage pipeline: scan, verify origin, rank, draft, build Word/PDF documents, and verify PDF page constraints.
- Project scanner supporting manifests across Node.js, Python, Rust, Go, Java, and Docker.
- Provenance verifier filtering tutorial clones, forks without contributions, and toy scaffolds.
- Zero-hallucination evidence rule mapping every claim to verifiable repository code or git history.
- LibreOffice headless PDF generation with typography and margin checks.

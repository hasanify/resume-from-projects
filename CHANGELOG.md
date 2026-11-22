# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2026-11-22

### Documentation

- add npx skills add command to Quick Start in README and localized docs

## [1.1.0] - 2026-11-22

### Features

- **ci:** add automated semantic release tagging, version bumping, and changelog workflow
- **ecosystem:** add multi-agent manifests and editor rules

### Bug Fixes

- **ci:** support --no-libreoffice flag in check_env and fix CI matrix runner dependencies

### Documentation

- enrich README and installation guides with ecosystem matrix and i18n links
- add pipeline architecture specification, zero-hallucination contract, and realistic role examples
- **i18n:** add Simplified Chinese, Spanish, and Japanese localized READMEs
- **community:** add contributing guide, issue templates, PR template, and security policy

### Tests

- add comprehensive automated test suite for scanner, origin check, ranker and writing rules

### Maintenance & CI

- add multi-platform test and manifest validation GitHub Actions workflows

### Other Changes

- update banner
- Remove sample output caption
- Reframe README for freelancers and developers
- Rewrite README copy, add banner and sample output screenshot
- Add release badge

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-22

### Initial Release

- Core 6-stage pipeline: scan, verify origin, rank, draft, build Word/PDF documents, and verify PDF page constraints.
- Project scanner supporting manifests across Node.js, Python, Rust, Go, Java, and Docker.
- Provenance verifier filtering tutorial clones, forks without contributions, and toy scaffolds.
- Zero-hallucination evidence rule mapping every claim to verifiable repository code or git history.
- LibreOffice headless PDF generation with typography and margin checks.

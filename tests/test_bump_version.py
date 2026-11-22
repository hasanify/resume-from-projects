"""Tests for scripts/bump_version.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import bump_version


class TestBumpVersion(unittest.TestCase):
    def test_parse_semver(self):
        self.assertEqual(bump_version.parse_semver("1.2.3"), (1, 2, 3))
        self.assertEqual(bump_version.parse_semver("v2.0.15"), (2, 0, 15))
        self.assertEqual(bump_version.parse_semver("invalid"), (1, 0, 0))

    def test_increment_semver(self):
        self.assertEqual(bump_version.increment_semver(1, 0, 0, "patch"), "1.0.1")
        self.assertEqual(bump_version.increment_semver(1, 0, 5, "minor"), "1.1.0")
        self.assertEqual(bump_version.increment_semver(1, 3, 2, "major"), "2.0.0")

    def test_analyze_commits_feature_detection(self):
        commits = [
            "feat(api): add new endpoint",
            "docs: update README",
            "chore: clean up dependencies"
        ]
        bump, categorized = bump_version.analyze_commits(commits)
        self.assertEqual(bump, "minor")
        self.assertEqual(len(categorized["Features"]), 1)
        self.assertEqual(len(categorized["Documentation"]), 1)
        self.assertEqual(len(categorized["Maintenance & CI"]), 1)

    def test_analyze_commits_breaking_change(self):
        commits = [
            "fix: small typo",
            "feat!: redesign entire scanner architecture",
            "docs: update changelog"
        ]
        bump, categorized = bump_version.analyze_commits(commits)
        self.assertEqual(bump, "major")

    def test_analyze_commits_patch_only(self):
        commits = [
            "fix(parser): handle empty strings",
            "docs: fix typo in installation guide"
        ]
        bump, categorized = bump_version.analyze_commits(commits)
        self.assertEqual(bump, "patch")

    def test_format_release_notes(self):
        categorized = {
            "Features": ["- **scanner:** add Rust Cargo support"],
            "Bug Fixes": ["- fix regex crash on windows"],
            "Performance": [],
            "Documentation": [],
            "Refactoring": [],
            "Tests": [],
            "Maintenance & CI": [],
            "Other Changes": []
        }
        notes = bump_version.format_release_notes("1.1.0", "2026-11-22", categorized)
        self.assertIn("## [1.1.0] - 2026-11-22", notes)
        self.assertIn("### Features", notes)
        self.assertIn("- **scanner:** add Rust Cargo support", notes)
        self.assertIn("### Bug Fixes", notes)


if __name__ == "__main__":
    unittest.main()

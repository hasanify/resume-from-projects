"""Tests for rank_projects.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "resume-from-projects", "scripts", "rank_projects.py")
)


class TestRankProjects(unittest.TestCase):
    def run_rank(self, scan_data, verdicts_data, *extra_args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f_s:
            json.dump(scan_data, f_s)
            scan_path = f_s.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f_v:
            json.dump(verdicts_data, f_v)
            verd_path = f_v.name

        try:
            cmd = [sys.executable, SCRIPT_PATH, scan_path, verd_path] + list(extra_args)
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        finally:
            for p in (scan_path, verd_path):
                if os.path.exists(p):
                    os.remove(p)

    def test_rank_prefers_depth_and_tests(self):
        p1 = {
            "name": "small-script",
            "path": "/code/small-script",
            "lines_of_code": 50,
            "total_files": 2,
            "languages": ["Python"],
            "dependency_count": 1,
            "dependencies_sample": ["requests"],
            "top_dirs": ["src"],
            "monorepo_children": [],
            "frameworks": [],
            "integrations": [],
            "real_world_phrases": [],
            "urls_in_readme": [],
            "tests": {"count": 0, "frameworks": []},
            "ci": [],
            "deploy": [],
            "docs_files": 0,
            "readme_chars": 100,
            "readme_excerpt": "A small utility script",
            "git": {
                "is_git": True,
                "commit_count": 2,
                "user_commit_count": 2,
                "user_share": 1.0,
                "files_in_history": 2,
                "files_touched_by_user": 2,
                "user_file_share": 1.0,
                "last_commit": "2024-01-01",
                "user_last_commit": "2024-01-01"
            },
            "pinned": False
        }
        p2 = {
            "name": "payment-platform",
            "path": "/code/payment-platform",
            "lines_of_code": 8500,
            "total_files": 48,
            "languages": ["Python"],
            "dependency_count": 15,
            "dependencies_sample": ["fastapi", "psycopg2", "stripe"],
            "top_dirs": ["app", "tests", "docs", "deploy"],
            "monorepo_children": [],
            "frameworks": ["fastapi"],
            "integrations": ["stripe", "postgresql"],
            "real_world_phrases": ["production client deployment"],
            "urls_in_readme": ["https://api.platform.example.com"],
            "tests": {"count": 45, "frameworks": ["pytest"]},
            "ci": [".github/workflows/ci.yml"],
            "deploy": ["Dockerfile"],
            "docs_files": 4,
            "readme_chars": 1500,
            "readme_excerpt": "High-throughput backend payment processing platform in Python",
            "git": {
                "is_git": True,
                "commit_count": 120,
                "user_commit_count": 105,
                "user_share": 0.87,
                "files_in_history": 48,
                "files_touched_by_user": 45,
                "user_file_share": 0.94,
                "last_commit": "2026-10-01",
                "user_last_commit": "2026-10-01"
            },
            "pinned": False
        }
        scan_data = {"projects": [p1, p2]}
        verdicts = {
            "verdicts": [
                {"name": "small-script", "verdict": "accept", "flags": [], "reasons": ["ok"]},
                {"name": "payment-platform", "verdict": "accept", "flags": [], "reasons": ["ok"]}
            ]
        }

        ranking = self.run_rank(scan_data, verdicts, "--top", "2", "--role", "backend engineer", "--keywords", "fastapi,python")
        ranked_names = [p["name"] for p in ranking["ranked"]]
        self.assertEqual(ranked_names[0], "payment-platform")
        self.assertGreater(ranking["ranked"][0]["score"], ranking["ranked"][1]["score"])

    def test_pinned_project_always_included(self):
        p1 = {
            "name": "p1",
            "path": "/code/p1",
            "lines_of_code": 5000,
            "total_files": 50,
            "languages": ["Rust"],
            "dependency_count": 10,
            "dependencies_sample": ["tokio"],
            "top_dirs": ["src"],
            "monorepo_children": [],
            "frameworks": [],
            "integrations": [],
            "real_world_phrases": [],
            "urls_in_readme": [],
            "tests": {"count": 10, "frameworks": []},
            "ci": [".github/workflows/ci.yml"],
            "deploy": [],
            "docs_files": 0,
            "readme_chars": 500,
            "readme_excerpt": "A rust utility",
            "git": {"is_git": True, "commit_count": 50, "user_commit_count": 50, "user_share": 1.0, "files_in_history": 50, "files_touched_by_user": 50, "user_file_share": 1.0, "last_commit": "2025-01-01", "user_last_commit": "2025-01-01"},
            "pinned": False
        }
        p2 = {
            "name": "p2",
            "path": "/code/p2",
            "lines_of_code": 100,
            "total_files": 3,
            "languages": ["Python"],
            "dependency_count": 1,
            "dependencies_sample": [],
            "top_dirs": ["src"],
            "monorepo_children": [],
            "frameworks": [],
            "integrations": [],
            "real_world_phrases": [],
            "urls_in_readme": [],
            "tests": {"count": 0, "frameworks": []},
            "ci": [],
            "deploy": [],
            "docs_files": 0,
            "readme_chars": 50,
            "readme_excerpt": "Script",
            "git": {"is_git": True, "commit_count": 2, "user_commit_count": 2, "user_share": 1.0, "files_in_history": 3, "files_touched_by_user": 3, "user_file_share": 1.0, "last_commit": "2024-01-01", "user_last_commit": "2024-01-01"},
            "pinned": True
        }
        scan_data = {"projects": [p1, p2]}
        verdicts = {
            "verdicts": [
                {"name": "p1", "verdict": "accept", "flags": [], "reasons": ["ok"]},
                {"name": "p2", "verdict": "accept", "flags": [], "reasons": ["ok"]}
            ]
        }

        ranking = self.run_rank(scan_data, verdicts, "--top", "1")
        ranked_names = [p["name"] for p in ranking["ranked"]]
        self.assertIn("p2", ranked_names)


if __name__ == "__main__":
    unittest.main()

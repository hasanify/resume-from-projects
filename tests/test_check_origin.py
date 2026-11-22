"""Tests for check_origin.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "resume-from-projects", "scripts", "check_origin.py")
)


class TestCheckOrigin(unittest.TestCase):
    def run_check(self, scan_data, *extra_args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(scan_data, f)
            temp_path = f.name
        try:
            cmd = [sys.executable, SCRIPT_PATH, temp_path] + list(extra_args)
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_accept_original_project(self):
        project = {
            "name": "billing-engine",
            "path": "/home/user/code/billing-engine",
            "lines_of_code": 2500,
            "git": {
                "is_git": True,
                "commit_count": 45,
                "user_commit_count": 42,
                "user_share": 0.93,
                "origin_owner": "myuser",
                "remotes": {"origin": "https://github.com/myuser/billing-engine.git"}
            },
            "signals": {
                "toy": [],
                "scaffold_readme": False,
                "tutorial_strong": [],
                "tutorial_weak": []
            },
            "tests": {"count": 12},
            "ci": {"has_ci": True},
            "licenses": ["MIT"],
            "license_holders": []
        }
        scan_data = {
            "root": "/home/user/code",
            "user": {"names": ["My User"], "emails": ["user@example.com"], "github": "myuser"},
            "projects": [project]
        }

        output = self.run_check(scan_data)
        verdicts = output["verdicts"]
        self.assertEqual(len(verdicts), 1)
        v = verdicts[0]
        self.assertEqual(v["verdict"], "accept")

    def test_reject_tutorial_course(self):
        project = {
            "name": "react-course-todo",
            "path": "/home/user/code/react-course-todo",
            "lines_of_code": 400,
            "git": {
                "is_git": True,
                "commit_count": 5,
                "user_commit_count": 5,
                "user_share": 1.0,
                "origin_owner": "myuser",
                "remotes": {}
            },
            "signals": {
                "toy": [],
                "scaffold_readme": False,
                "tutorial_strong": ["tutorial", "bootcamp"],
                "tutorial_weak": []
            },
            "tests": {"count": 0},
            "ci": {"has_ci": False},
            "licenses": [],
            "license_holders": []
        }
        scan_data = {
            "root": "/home/user/code",
            "user": {"names": ["My User"], "emails": ["user@example.com"], "github": "myuser"},
            "projects": [project]
        }

        output = self.run_check(scan_data)
        verdicts = output["verdicts"]
        self.assertEqual(len(verdicts), 1)
        v = verdicts[0]
        self.assertEqual(v["verdict"], "reject")
        self.assertTrue(any("tutorial" in r.lower() or "course" in r.lower() for r in v.get("reasons", [])))

    def test_confirm_without_git(self):
        project = {
            "name": "scripts-tool",
            "path": "/home/user/code/scripts-tool",
            "lines_of_code": 800,
            "git": {
                "is_git": False
            },
            "signals": {
                "toy": [],
                "scaffold_readme": False,
                "tutorial_strong": [],
                "tutorial_weak": []
            },
            "tests": {"count": 0},
            "ci": {"has_ci": False},
            "licenses": [],
            "license_holders": []
        }
        scan_data = {
            "root": "/home/user/code",
            "user": {"names": [], "emails": [], "github": None},
            "projects": [project]
        }

        output = self.run_check(scan_data)
        verdicts = output["verdicts"]
        self.assertEqual(len(verdicts), 1)
        v = verdicts[0]
        self.assertEqual(v["verdict"], "confirm")


if __name__ == "__main__":
    unittest.main()

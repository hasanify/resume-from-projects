"""Tests for scan_projects.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "resume-from-projects", "scripts", "scan_projects.py")
)


class TestScanProjects(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_scan_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_scan(self, *args):
        cmd = [sys.executable, SCRIPT_PATH, self.test_dir] + list(args)
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)

    def test_scan_empty_directory(self):
        data = self.run_scan()
        self.assertEqual(data["root"], os.path.abspath(self.test_dir))
        self.assertEqual(len(data["projects"]), 0)

    def test_scan_simple_project_with_readme_and_manifest(self):
        proj_dir = os.path.join(self.test_dir, "my-service")
        os.makedirs(proj_dir)

        # Create package.json
        with open(os.path.join(proj_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "name": "my-service",
                "version": "1.0.0",
                "dependencies": {"express": "^4.18.2"}
            }))

        # Create README.md
        with open(os.path.join(proj_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write("# my-service\nA REST API service for order processing.")

        data = self.run_scan()
        self.assertEqual(len(data["projects"]), 1)
        p = data["projects"][0]
        self.assertEqual(p["name"], "my-service")
        self.assertIn("express", p.get("dependencies_sample", []))

    def test_scan_project_with_git(self):
        proj_dir = os.path.join(self.test_dir, "git-app")
        os.makedirs(proj_dir)

        try:
            subprocess.run(["git", "init"], cwd=proj_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=proj_dir, check=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=proj_dir, check=True)

            test_file = os.path.join(proj_dir, "main.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("print('hello world')\n")

            subprocess.run(["git", "add", "main.py"], cwd=proj_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=proj_dir, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            self.skipTest("git not available in environment")

        data = self.run_scan("--user-email", "tester@example.com", "--user-name", "Tester")
        self.assertEqual(len(data["projects"]), 1)
        p = data["projects"][0]
        self.assertTrue(p["git"]["is_git"])
        self.assertEqual(p["git"]["commit_count"], 1)
        self.assertEqual(p["git"]["user_commit_count"], 1)


if __name__ == "__main__":
    unittest.main()

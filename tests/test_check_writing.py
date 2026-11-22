"""Tests for check_writing.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "resume-from-projects", "scripts", "check_writing.py")
)


class TestCheckWriting(unittest.TestCase):
    def run_lint(self, resume_data, *extra_args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(resume_data, f)
            temp_path = f.name
        try:
            cmd = [sys.executable, SCRIPT_PATH, temp_path] + list(extra_args)
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.returncode, res.stdout + res.stderr
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_banned_buzzwords_detected(self):
        resume = {
            "name": "Jane Doe",
            "summary": "Spearheaded groundbreaking AI synergies to seamlessly bolster productivity.",
            "projects": [
                {
                    "name": "Test Project",
                    "stack": ["Python"],
                    "bullets": [
                        "Leveraged cutting-edge algorithms to revolutionize data ingestion"
                    ],
                    "evidence": ["code in main.py"]
                }
            ]
        }
        code, output = self.run_lint(resume)
        self.assertIn("banned", output.lower())
        self.assertNotEqual(code, 0)

    def test_missing_evidence_for_numbers_flagged(self):
        resume = {
            "name": "Jane Doe",
            "projects": [
                {
                    "name": "Analytics Service",
                    "stack": ["Go"],
                    "bullets": [
                        "Reduced query latency by 45% across 12 endpoints"
                    ],
                    "evidence": []  # Missing evidence for 45% and 12
                }
            ]
        }
        code, output = self.run_lint(resume)
        self.assertIn("evidence", output.lower())
        self.assertNotEqual(code, 0)

    def test_clean_bullet_passes_linting(self):
        resume = {
            "name": "Jane Doe",
            "summary": "Backend engineer building data pipelines and API services in Python.",
            "projects": [
                {
                    "name": "Analytics Service",
                    "stack": ["Python", "PostgreSQL"],
                    "bullets": [
                        "Built a REST API with 12 endpoints in FastAPI backed by PostgreSQL"
                    ],
                    "evidence": [
                        "12 endpoints: counted router decorators in app/routes.py"
                    ]
                }
            ]
        }
        code, output = self.run_lint(resume)
        self.assertEqual(code, 0, f"Expected clean pass, got error output: {output}")


if __name__ == "__main__":
    unittest.main()

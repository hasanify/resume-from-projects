"""Validate resume JSON examples and schemas against layout specification."""
import json
import os
import unittest


class TestResumeSchema(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.example_path = os.path.join(
            self.repo_root, "skills", "resume-from-projects", "examples", "resume.example.json"
        )

    def test_example_json_valid_and_has_required_fields(self):
        self.assertTrue(os.path.exists(self.example_path), f"Example not found: {self.example_path}")
        with open(self.example_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("name", data)
        self.assertIsInstance(data["name"], str)
        self.assertIn("projects", data)
        self.assertIsInstance(data["projects"], list)
        self.assertGreater(len(data["projects"]), 0)

        for proj in data["projects"]:
            self.assertIn("name", proj)
            self.assertIn("description", proj)
            self.assertIn("stack", proj)
            self.assertIsInstance(proj["stack"], list)
            self.assertIn("bullets", proj)
            self.assertIsInstance(proj["bullets"], list)
            self.assertIn("evidence", proj)
            self.assertIsInstance(proj["evidence"], list)


if __name__ == "__main__":
    unittest.main()

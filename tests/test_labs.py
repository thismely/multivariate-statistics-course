"""Offline acceptance checks for the nine teaching laboratories."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABS_PATH = ROOT / "course" / "labs.json"
EXPECTED_IDS = {
    "pca",
    "fa",
    "cluster",
    "discriminant",
    "regression",
    "logistic",
    "cca",
    "ca",
    "evaluation",
}
REQUIRED_FIELDS = {
    "id",
    "title",
    "chapter",
    "knowledge_nodes",
    "code",
    "notebook",
    "data",
    "dictionary",
    "case",
    "description",
    "execution_status",
}


class LabManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.labs = json.loads(LABS_PATH.read_text(encoding="utf-8"))
        cls.by_id = {lab["id"]: lab for lab in cls.labs}

    def test_manifest_has_exactly_nine_labs_and_required_fields(self) -> None:
        self.assertEqual({lab["id"] for lab in self.labs}, EXPECTED_IDS)
        self.assertEqual(len(self.labs), 9)
        for lab in self.labs:
            self.assertTrue(REQUIRED_FIELDS.issubset(lab))
            self.assertTrue(lab["knowledge_nodes"])
            self.assertEqual(lab["execution_status"], "verified")
            self.assertEqual(lab["preview"], f"course/preview/{lab['id']}.html")

    def test_manifest_paths_are_course_relative_and_exist(self) -> None:
        for lab in self.labs:
            for key in ("code", "notebook", "data", "dictionary", "case"):
                value = lab[key]
                self.assertIsInstance(value, str)
                self.assertTrue(value.startswith("course/"), (lab["id"], key, value))
                self.assertFalse(Path(value).is_absolute())
                self.assertTrue((ROOT / value).is_file(), (lab["id"], key, value))

    def test_notebooks_are_valid_and_have_no_saved_outputs(self) -> None:
        sensitive = re.compile(
            "(?i)(password|api[_-]?key|secret|token|\\u5b66\\u53f7|\\u624b\\u673a\\u53f7|\\u8eab\\u4efd\\u8bc1|\\u59d3\\u540d)"
        )
        for lab in self.labs:
            notebook = json.loads((ROOT / lab["notebook"]).read_text(encoding="utf-8"))
            self.assertEqual(notebook["nbformat"], 4)
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    self.assertEqual(cell.get("outputs", []), [], lab["id"])
                    self.assertIsNone(cell.get("execution_count"))
            self.assertIsNone(sensitive.search(json.dumps(notebook, ensure_ascii=False)))

    def test_all_scripts_execute_offline_and_write_machine_results(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mvs-labs-") as tmp:
            output_root = Path(tmp)
            for lab in self.labs:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / lab["code"]),
                        "--output-dir",
                        str(output_root / lab["id"]),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result_path = output_root / lab["id"] / f"{lab['id']}_results.json"
                self.assertTrue(result_path.is_file(), lab["id"])
                result = json.loads(result_path.read_text(encoding="utf-8"))
                self.assertEqual(result["lab_id"], lab["id"])
                self.assertTrue(all(result["checks"].values()), result)

    def test_preview_build_is_static_and_escaped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mvs-preview-") as tmp:
            output_dir = Path(tmp) / "preview"
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build-labs.py"), "--output-dir", str(output_dir)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((output_dir / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertFalse(report["safety"]["script_tags_emitted"])
            for page in [output_dir / "index.html"] + [output_dir / f"{lab['id']}.html" for lab in self.labs]:
                self.assertTrue(page.is_file())
                self.assertNotIn("<script", page.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()

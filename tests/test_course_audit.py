from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "course-audit.py"
SPEC = importlib.util.spec_from_file_location("course_audit", SCRIPT)
assert SPEC and SPEC.loader
course_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(course_audit)


def _write(root: Path, relative: str, content: str | bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


_TEMP_DIRS: list[tempfile.TemporaryDirectory[str]] = []


def _base_project(*, resource_path: str = "course/lesson.md", resource_type: str = "notes") -> Path:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    # Keep the TemporaryDirectory alive through the test process.
    _TEMP_DIRS.append(temp)
    _write(root, "docs/privacy-review.json", json.dumps({"review_terms": [], "approvals": []}))
    _write(root, "src/data/chapters.json", json.dumps([{"id": "CH01", "title": "Chapter"}]))
    _write(root, "src/data/nodes.json", json.dumps([{"id": "node-1", "name": "Node"}]))
    _write(root, resource_path, "clean course content\n")
    manifest = [
        {
            "id": "resource-1",
            "title": "Lesson",
            "type": resource_type,
            "chapter": "CH01",
            "knowledge_nodes": ["node-1"],
            "path": resource_path,
            "public": True,
        }
    ]
    _write(root, "src/data/course-resources.json", json.dumps(manifest))
    return root


def _categories(report: dict, key: str = "failures") -> set[str]:
    return {item["category"] for item in report[key]}


class CourseAuditTests(unittest.TestCase):
    def test_clean_project_passes_and_excluded_tree_is_ignored(self) -> None:
        root = _base_project()
        _write(root, "node_modules/ignored.txt", "/" + "Users/hidden\n")
        _write(root, "dist/ignored.txt", "owner" + "@" + "private.test\n")
        report = course_audit.audit_project(root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["review_flags"], [])

    def test_direct_sensitive_values_fail_without_leaking_values(self) -> None:
        root = _base_project(resource_path="course/private-check.txt")
        email = "teacher" + "@" + "private.test"
        phone = "1" + "3800138000"
        national_id = "110105" + "1990" + "0101" + "123" + "X"
        absolute_path = "/" + "Users/alice/course"
        credential = "API_" + "KEY = " + repr("secretvalue")
        _write(
            root,
            "course/private-check.txt",
            "\n".join([email, phone, national_id, absolute_path, credential]),
        )
        report = course_audit.audit_project(root)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue({"email", "phone", "national_id", "absolute_user_path", "credential_assignment"} <= _categories(report))
        serialised = json.dumps(report, ensure_ascii=False)
        for value in (email, phone, national_id, absolute_path, "secretvalue"):
            self.assertNotIn(value, serialised)

    def test_notebook_execution_and_identity_metadata_fail(self) -> None:
        root = _base_project(resource_path="course/notebooks/example.ipynb", resource_type="notebook")
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "outputs": [{"output_type": "stream", "text": ["result"]}],
                    "metadata": {"author": "local contributor", "machine": "workstation"},
                    "source": [],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        _write(root, "course/notebooks/example.ipynb", json.dumps(notebook))
        report = course_audit.audit_project(root)
        self.assertTrue(
            {"notebook_outputs", "notebook_execution_count", "notebook_metadata_identity"} <= _categories(report)
        )

    def test_ooxml_text_is_scanned_but_generated_shape_ids_are_not(self) -> None:
        root = _base_project(resource_path="course/slides/example.pptx", resource_type="slides")
        path = root / "course/slides/example.pptx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "ppt/slides/slide1.xml",
                '<p:sld xmlns:p="urn:p"><p:t>owner' + "@" + 'private.test</p:t>'
                '<p:cNvPr id="3C18D451-ABCD-4E76-83C9-76983C7673D6"/></p:sld>',
            )
        report = course_audit.audit_project(root)
        self.assertIn("email", _categories(report))
        self.assertNotIn("phone", _categories(report))
        self.assertNotIn("national_id", _categories(report))

    def test_review_flag_requires_matching_path_category_and_hash(self) -> None:
        root = _base_project(resource_path="course/review.md")
        review_a = "\u6210" + "\u7ee9"
        review_b = "\u59d3" + "\u540d"
        content = "本练习包含" + review_a + "与" + review_b + "字段，仅供人工复核。\n"
        _write(root, "course/review.md", content)
        _write(
            root,
            "docs/privacy-review.json",
            json.dumps({"review_terms": [review_a, review_b], "approvals": []}),
        )
        report = course_audit.audit_project(root)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["summary"]["unapproved_review_flags"], 1)
        flag = report["review_flags"][0]
        self.assertNotIn(review_a, json.dumps(flag, ensure_ascii=False))
        approval = {"path": flag["path"], "category": flag["category"], "sha256": flag["sha256"]}
        _write(root, "docs/privacy-review.json", json.dumps({"review_terms": [review_a, review_b], "approvals": [approval]}))
        approved = course_audit.audit_project(root)
        self.assertEqual(approved["status"], "PASS")
        self.assertTrue(approved["review_flags"][0]["approved"])

    def test_manifest_references_and_registration_are_checked(self) -> None:
        root = _base_project(resource_path="course/known.md")
        _write(root, "course/unregistered.csv", "a,b\n1,2\n")
        manifest = [
            {
                "id": "resource-1",
                "title": "Known",
                "type": "notes",
                "chapter": "CH01",
                "knowledge_nodes": ["node-1"],
                "path": "course/known.md",
                "public": True,
                "data_ids": ["missing-data"],
                "code_id": "missing-code",
            },
            {
                "id": "resource-1",
                "title": "Unsafe",
                "type": "notes",
                "chapter": "CH99",
                "knowledge_nodes": ["missing-node"],
                "path": "../outside.md",
                "public": True,
            },
        ]
        _write(root, "src/data/course-resources.json", json.dumps(manifest))
        report = course_audit.audit_project(root)
        self.assertTrue(
            {
                "duplicate_id",
                "unsafe_resource_path",
                "resource_unknown_chapter",
                "resource_unknown_knowledge_node",
                "dangling_data_ids",
                "dangling_code_id",
                "unregistered_course_file",
            }
            <= _categories(report)
        )

    def test_explicit_internal_index_can_register_lab_files(self) -> None:
        root = _base_project(resource_path="course/lesson.md")
        _write(root, "course/internal.csv", "x\n1\n")
        _write(root, "course/labs.json", json.dumps([{"id": "lab", "data": "course/internal.csv"}]))
        report = course_audit.audit_project(root)
        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Audit the publishable course tree before a release.

The auditor is deliberately dependency free.  It checks the structured course
manifest, the source ``course/`` tree, generated public files, textual files,
Notebook state and XML members inside OOXML archives.  Findings contain only
relative file names, categories, line/member locations and hashes; matched
values are never copied to the report.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Mapping, Sequence


# Keep these as fragments so the scanner can inspect this file without
# matching its own rule literals.  The scripts directory is intentionally
# scanned; only these assembled expressions avoid self-referential findings.
_USER_ROOTS = ("U" + "sers", "h" + "ome")
_TOKEN_PREFIXES = (
    "g" + "hp_",
    "g" + "ho_",
    "g" + "hs_",
    "github" + "_pat_",
    "s" + "k-",
    "s" + "k_live_",
    "s" + "k_test_",
    "xox" + "b-",
    "xox" + "p-",
    "A" + "KIA",
    "A" + "Iza",
    "ya" + "29.",
    "npm_",
    "pypi-",
    "hf_",
)

_ABSOLUTE_USER_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    + r"/" + r"(?:" + "|".join(re.escape(x) for x in _USER_ROOTS) + r")/[^\s'\"<>]+"
    + r"|[A-Za-z]:[\\/]" + re.escape(_USER_ROOTS[0]) + r"[\\/][^\s'\"<>]+)"
)
_EMAIL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,63}(?![A-Za-z0-9._%+\-])"
)
_PHONE_RE = re.compile(
    r"(?<![A-Za-z0-9.])(?:\+?86[\s-]?)?1[3-9](?:[\s-]?\d){9}(?![A-Za-z0-9.])"
)
_ID18_RE = re.compile(
    r"(?<![A-Za-z0-9.])[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![A-Za-z0-9.])"
)
_ID15_RE = re.compile(
    r"(?<![A-Za-z0-9.])[1-9]\d{5}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}(?![A-Za-z0-9.])"
)
_TOKEN_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:"
    + "|".join(re.escape(x) for x in _TOKEN_PREFIXES)
    + r")[A-Za-z0-9._\-]{12,}"
)

# Credential assignment is intentionally broad enough to catch accidental
# publication of a short token, while common placeholders are ignored below.
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:api[_-]?key|access[_-]?token|auth(?:entication)?[_-]?token|"
    r"secret(?:[_-]?key)?|password|passwd|client[_-]?secret|authorization|bearer)"
    r"\s*[:=]\s*(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;\]}]+)"
)
_PLACEHOLDER_RE = re.compile(
    r"(?i)^(?:|none|null|false|true|redacted|redact|placeholder|changeme|change_me|"
    r"your[-_ ]?(?:api[-_ ]?)?(?:key|token|secret)|replace[-_ ]?me|todo|xxx+|\.\.\.)$"
)
_GUID_RE = re.compile(
    r"(?i)(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![0-9a-f])"
)
_HASH_FIELD_RE = re.compile(
    r"(?i)(?:sha(?:1|224|256|384|512)?|md5|hash|digest|checksum)\s*[\"']?\s*[:=]\s*[\"']?([0-9a-f]{32,})"
)

_DEFAULT_REVIEW_TERMS = ("\u6210\u7ee9", "\u59d3\u540d")

_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "dist",
        ".cache",
        "cache",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".vite",
        ".parcel-cache",
        ".ipynb_checkpoints",
        "coverage",
        "tmp",
        "temp",
    }
)
_TEXT_SUFFIXES = frozenset(
    {
        ".cjs",
        ".css",
        ".csv",
        ".html",
        ".htm",
        ".ini",
        ".ipynb",
        ".js",
        ".json",
        ".jsx",
        ".md",
        ".mjs",
        ".py",
        ".rst",
        ".scss",
        ".sh",
        ".sql",
        ".svg",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".vue",
        ".xml",
        ".yaml",
        ".yml",
    }
)
_OOXML_SUFFIXES = frozenset({".docx", ".pptx", ".xlsx"})
_ZIP_SUFFIXES = frozenset({".docx", ".pptx", ".xlsx", ".zip"})
_ARCHIVE_TEXT_SUFFIXES = _TEXT_SUFFIXES | frozenset({".rels", ".vml"})
_INDEX_BASENAMES = frozenset(
    {
        "index.json",
        "resource-index.json",
        "internal-index.json",
        "manifest.json",
        "labs.json",
        ".course-index.json",
    }
)
_INDEX_PATH_KEYS = frozenset(
    {
        "path",
        "paths",
        "file",
        "files",
        "code",
        "notebook",
        "data",
        "dictionary",
        "dataset",
        "case",
        "preview",
        "outputs",
        "internal_paths",
        "internal_files",
    }
)
_NOTEBOOK_IDENTITY_KEYS = frozenset(
    {
        "author",
        "authors",
        "creator",
        "created_by",
        "username",
        "user_name",
        "machine",
        "machine_name",
        "hostname",
        "host_name",
        "computer",
        "computer_name",
        "device_name",
        "working_directory",
        "cwd",
    }
)

_MAX_ARCHIVE_MEMBER_BYTES = 64 * 1024 * 1024
_MAX_ARCHIVE_TOTAL_BYTES = 256 * 1024 * 1024
_REVIEW_CONFIG_REL = "docs/privacy-review.json"
_COURSE_MANIFEST_REL = "src/data/course-resources.json"
_CHAPTERS_REL = "src/data/chapters.json"
_NODES_REL = "src/data/nodes.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_placeholder_email(match: str) -> bool:
    domain = match.rsplit("@", 1)[-1].lower()
    return domain in {"example.com", "example.org", "example.net", "invalid", "localhost"} or domain.endswith(
        ".invalid"
    )


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_meaningful(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_meaningful(v) for v in value)
    return True


def _normalise_review_terms(value: Any) -> list[str]:
    """Read configurable review terms without including them in reports."""

    if value is None:
        return list(_DEFAULT_REVIEW_TERMS)
    values: list[Any] = []
    if isinstance(value, Mapping):
        for child in value.values():
            values.extend(child if isinstance(child, list) else [child])
    elif isinstance(value, list):
        values = value
    else:
        values = [value]
    return sorted({item.strip() for item in values if isinstance(item, str) and item.strip()})


def _read_name_env() -> tuple[set[str], set[str]]:
    names: set[str] = set()
    hashes: set[str] = set()
    for env_name in ("COURSE_AUDIT_FORBIDDEN_NAMES", "COURSE_AUDIT_PRIVATE_NAMES"):
        raw = os.environ.get(env_name, "")
        if not raw:
            continue
        # Accept either a newline/comma separated list or a JSON list.  Values
        # remain process-local and are never echoed by this script.
        candidates: Any = raw
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                candidates = parsed
        except json.JSONDecodeError:
            pass
        if not isinstance(candidates, list):
            candidates = re.split(r"[,;\r\n]", str(candidates))
        names.update(str(item).strip() for item in candidates if str(item).strip())
    for env_name in (
        "COURSE_AUDIT_FORBIDDEN_NAME_HASHES",
        "COURSE_AUDIT_PRIVATE_NAME_HASHES",
        "COURSE_AUDIT_FORBIDDEN_NAME_SHA256",
    ):
        raw = os.environ.get(env_name, "")
        hashes.update(
            item.strip().lower()
            for item in re.split(r"[,;\r\n]", raw)
            if re.fullmatch(r"[0-9a-fA-F]{64}", item.strip())
        )
    return names, hashes


def _name_hash_candidates(text: str) -> Iterator[str]:
    # Chinese names and ordinary word tokens are considered only when hashes
    # were supplied by the local environment.  No candidate is reported.
    yield from re.findall(r"[\u4e00-\u9fff]{2,6}", text)
    yield from re.findall(r"(?<![A-Za-z])[A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20})?(?![A-Za-z])", text)


def _safe_course_path(value: Any) -> tuple[bool, str | None]:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        return False, None
    raw = value.strip().replace("\\", "/")
    # Drive prefixes and leading separators are absolute on at least one
    # supported platform.  Reject them before normalisation.
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        return False, None
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False, None
    normal = PurePosixPath(*parts).as_posix()
    if not normal.startswith("course/"):
        return False, None
    return True, normal


def _iter_release_files(root: Path) -> Iterator[Path]:
    """Yield files under root without descending into generated/cache trees."""

    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirpath = Path(directory)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in _EXCLUDED_DIRS and not (dirpath / name).is_symlink()
        )
        for name in sorted(filenames):
            path = dirpath / name
            if any(part in _EXCLUDED_DIRS for part in path.relative_to(root).parts):
                continue
            yield path


class Findings:
    """De-duplicate findings while retaining safe audit locations."""

    def __init__(self) -> None:
        self.failures: dict[tuple[str, str], dict[str, Any]] = {}
        self.reviews: dict[tuple[str, str], dict[str, Any]] = {}

    def add(
        self,
        status: str,
        path: str,
        category: str,
        *,
        file_sha256: str | None = None,
        location: str | None = None,
        count: int = 1,
    ) -> None:
        target = self.failures if status == "FAIL" else self.reviews
        key = (path, category)
        item = target.get(key)
        if item is None:
            item = {"path": path, "category": category, "count": 0}
            if file_sha256:
                item["sha256"] = file_sha256
            if status == "REVIEW":
                item["approved"] = False
            target[key] = item
        item["count"] += count
        if file_sha256 and "sha256" not in item:
            item["sha256"] = file_sha256
        if location:
            locations = item.setdefault("locations", [])
            if location not in locations and len(locations) < 12:
                locations.append(location)


def _line_matches(pattern: re.Pattern[str], line: str) -> int:
    return sum(1 for _ in pattern.finditer(line))


def _technical_numeric_identifier(line: str, match: re.Match[str]) -> bool:
    """Ignore generated GUIDs and hexadecimal digest fields.

    These values contain long digit runs that resemble a phone number or a
    national ID after XML tags/JSON punctuation are removed.  They are not
    user data and are handled separately from genuine numeric matches.
    """

    for candidate in _GUID_RE.finditer(line):
        if candidate.start() <= match.start() and match.end() <= candidate.end():
            return True
    for candidate in _HASH_FIELD_RE.finditer(line):
        if candidate.start(1) <= match.start() and match.end() <= candidate.end(1):
            return True
    return False


def _numeric_identifier_matches(pattern: re.Pattern[str], line: str) -> int:
    return sum(1 for match in pattern.finditer(line) if not _technical_numeric_identifier(line, match))


def _credential_assignment_count(line: str) -> int:
    count = 0
    for match in _CREDENTIAL_ASSIGNMENT_RE.finditer(line):
        value = match.group(0).split("=", 1)[-1].split(":", 1)[-1].strip()
        value = value.strip("\"'")
        if not _PLACEHOLDER_RE.fullmatch(value.strip()):
            count += 1
    return count


def _scan_text(
    text: str,
    report_path: str,
    file_sha256: str,
    findings: Findings,
    review_terms: Sequence[str],
    forbidden_names: set[str],
    forbidden_name_hashes: set[str],
    *,
    location_prefix: str | None = None,
) -> None:
    lines = text.splitlines() or [""]
    for line_number, line in enumerate(lines, 1):
        location_base = f"{location_prefix}:{line_number}" if location_prefix else str(line_number)

        def add_direct(category: str, count: int) -> None:
            if count:
                findings.add(
                    "FAIL",
                    report_path,
                    category,
                    file_sha256=file_sha256,
                    location=location_base,
                    count=count,
                )

        email_count = sum(1 for match in _EMAIL_RE.finditer(line) if not _is_placeholder_email(match.group(0)))
        add_direct("email", email_count)
        add_direct("absolute_user_path", _line_matches(_ABSOLUTE_USER_PATH_RE, line))
        add_direct("phone", _numeric_identifier_matches(_PHONE_RE, line))
        add_direct(
            "national_id",
            _numeric_identifier_matches(_ID18_RE, line) + _numeric_identifier_matches(_ID15_RE, line),
        )
        add_direct("credential_token", _line_matches(_TOKEN_RE, line))
        add_direct("credential_assignment", _credential_assignment_count(line))

        if forbidden_names:
            matches = sum(1 for name in forbidden_names if name in line)
            add_direct("forbidden_private_name", matches)
        if forbidden_name_hashes:
            matches = sum(
                1
                for candidate in _name_hash_candidates(line)
                if hashlib.sha256(candidate.encode("utf-8")).hexdigest().lower() in forbidden_name_hashes
            )
            add_direct("forbidden_private_name_hash", matches)

        review_count = sum(line.count(term) for term in review_terms if term)
        if review_count:
            findings.add(
                "REVIEW",
                report_path,
                "teaching_sensitive_keyword",
                file_sha256=file_sha256,
                location=location_base,
                count=review_count,
            )


def _walk_json(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_path = path + (str(key),)
            yield key_path, child
            yield from _walk_json(child, key_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            key_path = path + (str(index),)
            yield key_path, child
            yield from _walk_json(child, key_path)


def _audit_notebook(
    raw: bytes,
    report_path: str,
    file_sha256: str,
    findings: Findings,
    review_terms: Sequence[str],
    forbidden_names: set[str],
    forbidden_name_hashes: set[str],
) -> None:
    _scan_text(
        raw.decode("utf-8", errors="replace"),
        report_path,
        file_sha256,
        findings,
        review_terms,
        forbidden_names,
        forbidden_name_hashes,
    )
    try:
        notebook = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        findings.add("FAIL", report_path, "invalid_notebook_json", file_sha256=file_sha256)
        return
    if not isinstance(notebook, Mapping) or not isinstance(notebook.get("cells"), list):
        findings.add("FAIL", report_path, "invalid_notebook_schema", file_sha256=file_sha256)
        return
    for index, cell in enumerate(notebook["cells"]):
        if not isinstance(cell, Mapping):
            findings.add("FAIL", report_path, "invalid_notebook_cell", file_sha256=file_sha256, location=str(index))
            continue
        # nbformat's clean representation commonly retains outputs=[] and
        # execution_count=null.  Both are semantically unexecuted and pass;
        # non-empty/numbered values indicate a published execution trace.
        outputs = cell.get("outputs")
        if outputs not in (None, []):
            findings.add("FAIL", report_path, "notebook_outputs", file_sha256=file_sha256, location=str(index))
        if "execution_count" in cell and cell.get("execution_count") is not None:
            findings.add(
                "FAIL", report_path, "notebook_execution_count", file_sha256=file_sha256, location=str(index)
            )
        metadata = cell.get("metadata")
        if isinstance(metadata, Mapping):
            for key_path, value in _walk_json(metadata):
                key = key_path[-1].lower().replace("-", "_")
                if key in _NOTEBOOK_IDENTITY_KEYS and _meaningful(value):
                    findings.add(
                        "FAIL",
                        report_path,
                        "notebook_metadata_identity",
                        file_sha256=file_sha256,
                        location=str(index),
                    )
    root_metadata = notebook.get("metadata")
    if isinstance(root_metadata, Mapping):
        for key_path, value in _walk_json(root_metadata):
            key = key_path[-1].lower().replace("-", "_")
            if key in _NOTEBOOK_IDENTITY_KEYS and _meaningful(value):
                findings.add(
                    "FAIL", report_path, "notebook_metadata_identity", file_sha256=file_sha256, location="metadata"
                )


def _archive_member_safe(name: str) -> bool:
    posix = PurePosixPath(name)
    return not posix.is_absolute() and ".." not in posix.parts


def _xml_text_content(raw: bytes) -> str:
    """Extract XML text and meaningful attributes without drawing GUIDs in.

    OOXML stores generated shape and relationship identifiers in attributes.
    Scanning the serialized XML directly can turn an identifier split by tags
    into a false phone/ID match.  User-visible text and path-like attributes
    are retained; identifier attributes are deliberately ignored.
    """

    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(raw)
    except (ET.ParseError, UnicodeDecodeError):
        return raw.decode("utf-8", errors="replace")
    chunks: list[str] = []
    ignored_attributes = frozenset(
        {
            "id",
            "rid",
            "relid",
            "creationid",
            "shapeid",
            "spid",
            "idx",
            "index",
            "cx",
            "cy",
            "x",
            "y",
            "w",
            "h",
        }
    )
    for element in root.iter():
        if element.text:
            chunks.append(element.text)
        if element.tail:
            chunks.append(element.tail)
        for key, value in element.attrib.items():
            local_key = key.rsplit("}", 1)[-1].lower()
            if local_key not in ignored_attributes:
                chunks.append(value)
    return "\n".join(chunks)


def _scan_archive(
    raw: bytes,
    report_path: str,
    file_sha256: str,
    findings: Findings,
    review_terms: Sequence[str],
    forbidden_names: set[str],
    forbidden_name_hashes: set[str],
    *,
    depth: int = 0,
) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, OSError):
        findings.add("FAIL", report_path, "invalid_archive", file_sha256=file_sha256)
        return
    total = 0
    try:
        for info in archive.infolist():
            name = info.filename
            if info.is_dir():
                continue
            if not _archive_member_safe(name):
                findings.add("FAIL", report_path, "archive_member_path", file_sha256=file_sha256)
                continue
            if info.file_size > _MAX_ARCHIVE_MEMBER_BYTES:
                findings.add("FAIL", report_path, "archive_member_too_large", file_sha256=file_sha256)
                continue
            total += info.file_size
            if total > _MAX_ARCHIVE_TOTAL_BYTES:
                findings.add("FAIL", report_path, "archive_too_large", file_sha256=file_sha256)
                break
            suffix = Path(name).suffix.lower()
            # Images and other binary payloads cannot contain OOXML text that
            # the release policy is meant to inspect.
            if suffix not in _ARCHIVE_TEXT_SUFFIXES and suffix not in _ZIP_SUFFIXES:
                continue
            try:
                member = archive.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile):
                findings.add("FAIL", report_path, "archive_member_unreadable", file_sha256=file_sha256)
                continue
            location_prefix = name.replace("\n", " ")[:240]
            if suffix in _ZIP_SUFFIXES and depth < 2:
                _scan_archive(
                    member,
                    report_path,
                    file_sha256,
                    findings,
                    review_terms,
                    forbidden_names,
                    forbidden_name_hashes,
                    depth=depth + 1,
                )
            elif suffix in _ARCHIVE_TEXT_SUFFIXES:
                content = member.decode("utf-8", errors="replace")
                if suffix in {".xml", ".rels", ".vml"}:
                    content = _xml_text_content(member)
                _scan_text(
                    content,
                    report_path,
                    file_sha256,
                    findings,
                    review_terms,
                    forbidden_names,
                    forbidden_name_hashes,
                    location_prefix=location_prefix,
                )
    finally:
        archive.close()


def _load_json(root: Path, relative_path: str, findings: Findings) -> Any:
    path = root / relative_path
    if not path.is_file():
        findings.add("FAIL", relative_path, "missing_metadata_file")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        findings.add("FAIL", relative_path, "invalid_json")
        return None


def _unique_ids(value: Any, relative_path: str, category: str, findings: Findings) -> set[str]:
    if not isinstance(value, list):
        findings.add("FAIL", relative_path, f"{category}_not_list")
        return set()
    result: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            findings.add("FAIL", relative_path, f"{category}_item_schema", location=str(index))
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            findings.add("FAIL", relative_path, f"{category}_missing_id", location=str(index))
            continue
        if identifier in result:
            findings.add("FAIL", relative_path, "duplicate_id", location=str(index))
        result.add(identifier)
    return result


def _path_components_have_symlink(root: Path, relative_path: str) -> bool:
    current = root
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _validate_resource_path(
    root: Path,
    resource_manifest_path: str,
    field: str,
    value: Any,
    findings: Findings,
    *,
    item_index: int,
) -> str | None:
    safe, normal = _safe_course_path(value)
    if not safe or normal is None:
        findings.add("FAIL", resource_manifest_path, f"unsafe_resource_{field}", location=str(item_index))
        return None
    target = root / normal
    if _path_components_have_symlink(root, normal):
        findings.add("FAIL", resource_manifest_path, f"symlink_resource_{field}", location=str(item_index))
    if not target.is_file():
        findings.add("FAIL", resource_manifest_path, f"missing_resource_{field}", location=str(item_index))
    return normal


def _validate_resource_manifest(root: Path, findings: Findings) -> tuple[list[Mapping[str, Any]], set[str]]:
    raw = _load_json(root, _COURSE_MANIFEST_REL, findings)
    if not isinstance(raw, list):
        return [], set()
    resource_ids = _unique_ids(raw, _COURSE_MANIFEST_REL, "resource", findings)
    chapters_raw = _load_json(root, _CHAPTERS_REL, findings)
    nodes_raw = _load_json(root, _NODES_REL, findings)
    chapter_ids = _unique_ids(chapters_raw, _CHAPTERS_REL, "chapter", findings)
    node_ids = _unique_ids(nodes_raw, _NODES_REL, "node", findings)
    seen_paths: set[str] = set()
    valid_items: list[Mapping[str, Any]] = []
    required = ("id", "title", "type", "chapter", "knowledge_nodes", "path", "public")
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_item_schema", location=str(index))
            continue
        valid_items.append(item)
        for key in required:
            if key not in item:
                findings.add("FAIL", _COURSE_MANIFEST_REL, f"resource_missing_{key}", location=str(index))
        if not isinstance(item.get("id"), str) or not str(item.get("id", "")).strip():
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_invalid_id", location=str(index))
        for key in ("title", "type"):
            if not isinstance(item.get(key), str) or not item.get(key, "").strip():
                findings.add("FAIL", _COURSE_MANIFEST_REL, f"resource_invalid_{key}", location=str(index))
        if not isinstance(item.get("public"), bool):
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_invalid_public", location=str(index))
        chapter = item.get("chapter")
        if not isinstance(chapter, str) or chapter not in chapter_ids:
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_unknown_chapter", location=str(index))
        knowledge_nodes = item.get("knowledge_nodes")
        if not isinstance(knowledge_nodes, list) or not knowledge_nodes:
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_invalid_knowledge_nodes", location=str(index))
        elif any(not isinstance(node, str) or node not in node_ids for node in knowledge_nodes):
            findings.add("FAIL", _COURSE_MANIFEST_REL, "resource_unknown_knowledge_node", location=str(index))
        path = _validate_resource_path(
            root, _COURSE_MANIFEST_REL, "path", item.get("path"), findings, item_index=index
        )
        if path:
            if path in seen_paths:
                findings.add("FAIL", _COURSE_MANIFEST_REL, "duplicate_resource_path", location=str(index))
            seen_paths.add(path)
        preview = item.get("preview")
        if preview is not None:
            _validate_resource_path(root, _COURSE_MANIFEST_REL, "preview", preview, findings, item_index=index)
        for link_key in ("data_ids", "code_id", "notebook_id"):
            if link_key not in item:
                continue
            value = item.get(link_key)
            if link_key == "data_ids" and not isinstance(value, list):
                findings.add("FAIL", _COURSE_MANIFEST_REL, "invalid_data_ids", location=str(index))
            elif link_key != "data_ids" and not isinstance(value, str):
                findings.add("FAIL", _COURSE_MANIFEST_REL, f"invalid_{link_key}", location=str(index))
            values = value if isinstance(value, list) else [value]
            for reference in values:
                if not isinstance(reference, str) or reference not in resource_ids:
                    findings.add("FAIL", _COURSE_MANIFEST_REL, f"dangling_{link_key}", location=str(index))
    return valid_items, seen_paths


def _validate_link_fields(root: Path, resource_ids: set[str], findings: Findings) -> None:
    data_dir = root / "src" / "data"
    if not data_dir.is_dir():
        return
    for path in sorted(data_dir.glob("*.json")):
        relative_path = _relative(root, path)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        for key_path, child in _walk_json(value):
            key = key_path[-1] if key_path else ""
            if key not in {"data_ids", "code_id", "notebook_id"}:
                continue
            values = child if isinstance(child, list) else [child]
            if key == "data_ids" and not isinstance(child, list):
                findings.add("FAIL", relative_path, "invalid_data_ids")
            for reference in values:
                if not isinstance(reference, str) or reference not in resource_ids:
                    findings.add("FAIL", relative_path, f"dangling_{key}")


def _extract_index_paths(value: Any, key: str = "") -> Iterator[str]:
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_str = str(child_key)
            if child_key_str in _INDEX_PATH_KEYS:
                yield from _extract_index_paths(child, child_key_str)
            elif isinstance(child, (Mapping, list)):
                yield from _extract_index_paths(child, child_key_str)
    elif isinstance(value, list):
        for child in value:
            yield from _extract_index_paths(child, key)
    elif isinstance(value, str) and (value.startswith("course/") or value.startswith("./course/")):
        yield value


def _course_registration_audit(root: Path, registered_paths: set[str], findings: Findings) -> None:
    course_root = root / "course"
    if not course_root.is_dir():
        findings.add("FAIL", "course", "missing_course_directory")
        return
    for directory, dirnames, _ in os.walk(course_root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        for name in dirnames:
            candidate = directory_path / name
            if candidate.is_symlink():
                findings.add("FAIL", _relative(root, candidate), "course_directory_symlink")
        # Do not descend into a symlink while looking for registered files.
        dirnames[:] = [name for name in dirnames if not (directory_path / name).is_symlink()]
    internal_paths: set[str] = set()
    for path in sorted(_iter_release_files(course_root)):
        relative = _relative(root, path)
        if path.is_symlink():
            findings.add("FAIL", relative, "course_file_symlink")
        if path.name not in _INDEX_BASENAMES:
            continue
        internal_paths.add(relative)
        try:
            index_value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            findings.add("FAIL", relative, "invalid_internal_index")
            continue
        for indexed in _extract_index_paths(index_value):
            safe, normal = _safe_course_path(indexed)
            if not safe or normal is None:
                findings.add("FAIL", relative, "unsafe_internal_index_path")
                continue
            internal_paths.add(normal)
            target = root / normal
            if _path_components_have_symlink(root, normal):
                findings.add("FAIL", relative, "symlink_internal_index_path")
            if not target.is_file():
                findings.add("FAIL", relative, "missing_internal_index_path")
    allowed = registered_paths | internal_paths
    for path in sorted(_iter_release_files(course_root)):
        relative = _relative(root, path)
        # ``build-labs.py`` emits an index and a machine-readable build report
        # beside the per-lab previews.  The containing labs manifest is the
        # explicit internal index for this generated directory, so these two
        # files are covered even though they are not learner resources.
        if relative.startswith("course/preview/") and "course/labs.json" in internal_paths:
            allowed.add(relative)
        if relative not in allowed:
            findings.add("FAIL", relative, "unregistered_course_file")


def _load_review_config(root: Path, findings: Findings) -> tuple[list[str], list[Mapping[str, Any]]]:
    path = root / _REVIEW_CONFIG_REL
    if not path.exists():
        return list(_DEFAULT_REVIEW_TERMS), []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        findings.add("FAIL", _REVIEW_CONFIG_REL, "invalid_privacy_review_config")
        return list(_DEFAULT_REVIEW_TERMS), []
    if not isinstance(config, Mapping):
        findings.add("FAIL", _REVIEW_CONFIG_REL, "invalid_privacy_review_config")
        return list(_DEFAULT_REVIEW_TERMS), []
    terms = _normalise_review_terms(config.get("review_terms"))
    approvals = config.get("approvals", config.get("approved", []))
    if approvals is None:
        approvals = []
    if not isinstance(approvals, list) or any(not isinstance(item, Mapping) for item in approvals):
        findings.add("FAIL", _REVIEW_CONFIG_REL, "invalid_privacy_review_approvals")
        approvals = []
    return terms, [item for item in approvals if isinstance(item, Mapping)]


def _apply_review_approvals(reviews: dict[tuple[str, str], dict[str, Any]], approvals: Sequence[Mapping[str, Any]]) -> None:
    for item in reviews.values():
        item["approved"] = any(
            approval.get("path") == item.get("path")
            and approval.get("category") == item.get("category")
            and str(approval.get("sha256", approval.get("content_sha256", ""))).lower() == str(item.get("sha256", "")).lower()
            for approval in approvals
        )


def _scan_release_content(root: Path, findings: Findings, review_terms: Sequence[str]) -> int:
    forbidden_names, forbidden_hashes = _read_name_env()
    scanned = 0
    for path in _iter_release_files(root):
        relative = _relative(root, path)
        # This is policy input, rather than publishable course content.  Check
        # it for direct privacy leaks but do not apply keyword reviews to the
        # policy's own labels/reasons or let it recursively approve itself.
        if relative == _REVIEW_CONFIG_REL:
            try:
                raw = path.read_bytes()
            except OSError:
                findings.add("FAIL", relative, "unreadable_file")
                continue
            digest = _sha256(raw)
            _scan_text(
                raw.decode("utf-8", errors="replace"),
                relative,
                digest,
                findings,
                (),
                forbidden_names,
                forbidden_hashes,
            )
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            findings.add("FAIL", relative, "unreadable_file")
            continue
        scanned += 1
        digest = _sha256(raw)
        suffix = path.suffix.lower()
        if suffix == ".ipynb":
            _audit_notebook(raw, relative, digest, findings, review_terms, forbidden_names, forbidden_hashes)
        elif suffix in _ZIP_SUFFIXES:
            _scan_archive(raw, relative, digest, findings, review_terms, forbidden_names, forbidden_hashes)
        elif suffix in _TEXT_SUFFIXES:
            _scan_text(
                raw.decode("utf-8", errors="replace"),
                relative,
                digest,
                findings,
                review_terms,
                forbidden_names,
                forbidden_hashes,
            )
        else:
            # Do not attempt to infer text from arbitrary media or PDFs.  The
            # release requirements specifically cover text and OOXML XML.
            continue
    return scanned


def _clean_item(item: Mapping[str, Any]) -> dict[str, Any]:
    # Reports intentionally contain no source snippets or matched values.
    return {key: value for key, value in item.items() if key in {"path", "category", "count", "sha256", "approved", "locations"}}


def audit_project(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    findings = Findings()
    review_terms, approvals = _load_review_config(root, findings)
    resources, resource_paths = _validate_resource_manifest(root, findings)
    _validate_link_fields(root, {str(item.get("id")) for item in resources}, findings)

    registered = set(resource_paths)
    # Preview files are also course files and therefore count as registered.
    for item in resources:
        preview = item.get("preview") if isinstance(item, Mapping) else None
        if isinstance(preview, str):
            safe, normal = _safe_course_path(preview)
            if safe and normal:
                registered.add(normal)
    _course_registration_audit(root, registered, findings)
    scanned = _scan_release_content(root, findings, review_terms)
    _apply_review_approvals(findings.reviews, approvals)
    unapproved = sum(1 for item in findings.reviews.values() if not item.get("approved"))
    failure_items = [_clean_item(item) for item in findings.failures.values()]
    review_items = [_clean_item(item) for item in findings.reviews.values()]
    status = "PASS" if not failure_items and unapproved == 0 else "FAIL"
    return {
        "status": status,
        "scope": {
            "root": ".",
            "excluded_directories": sorted(_EXCLUDED_DIRS),
            "content_policy": "text and OOXML XML members; no external directories scanned",
        },
        "summary": {
            "resources": len(resources),
            "registered_course_paths": len(registered),
            "files_scanned": scanned,
            "failures": len(failure_items),
            "review_flags": len(review_items),
            "unapproved_review_flags": unapproved,
        },
        "failures": sorted(failure_items, key=lambda item: (item["path"], item["category"])),
        "review_flags": sorted(review_items, key=lambda item: (item["path"], item["category"])),
        "review_config": _REVIEW_CONFIG_REL,
        "notes": [
            "PASS requires zero direct failures and approval for every review flag.",
            "Review approvals match relative path, category and content sha256.",
            "Notebook outputs=[] and execution_count=null are treated as unexecuted.",
        ],
    }


def write_reports(root: Path | str, report: Mapping[str, Any]) -> None:
    root = Path(root).resolve()
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "course-resource-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Course resource audit",
        "",
        f"Status: **{report.get('status', 'FAIL')}**",
        "",
        "This report records file paths, categories, counts, locations and content hashes only. Matched values are omitted.",
        "",
        "## Scope",
        "",
        "- Root: `./`",
        "- Scanned: publish-tree text files and XML members in PPTX/XLSX/DOCX/ZIP archives.",
        "- Excluded: `node_modules`, `dist`, `.git` and cache/checkpoint directories.",
        "- A clean status requires every manual review flag to be approved by path, category and SHA-256 in `docs/privacy-review.json`.",
        "",
        "## Summary",
        "",
    ]
    for key, value in report.get("summary", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Direct failures", ""])
    failures = report.get("failures", [])
    if failures:
        for item in failures:
            lines.append(f"- `{item.get('path')}` — `{item.get('category')}` (count `{item.get('count', 1)}`)")
    else:
        lines.append("- None")
    lines.extend(["", "## Manual review flags", ""])
    reviews = report.get("review_flags", [])
    if reviews:
        for item in reviews:
            approval = "approved" if item.get("approved") else "unapproved"
            lines.append(
                f"- `{item.get('path')}` — `{item.get('category')}` — `{approval}` — SHA-256 `{item.get('sha256', '')}`"
            )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Review procedure",
            "",
            "Inspect each flagged file in context. Add an approval object containing its relative `path`, `category` and reported `sha256` to `docs/privacy-review.json` only after manual confirmation.",
            "",
        ]
    )
    (docs / "course-resource-audit.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = audit_project(args.root)
    write_reports(args.root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build a safe, dependency-free static preview for the nine course labs.

The renderer only emits escaped text and relative links. It does not emit a
script tag or execute notebook/code content, so it is suitable for a static
GitHub Pages artifact.
"""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

LAB_IDS = {
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
    "preview",
}
PATH_FIELDS = ("code", "notebook", "data", "dictionary", "case")


def esc(value: object) -> str:
    """Escape text for HTML text and attribute contexts."""

    return html.escape(str(value), quote=True)


def resolve_course_path(root: Path, value: str) -> Path:
    """Resolve a repository-relative course path and reject traversal."""

    candidate = Path(value)
    if candidate.is_absolute() or not value.startswith("course/"):
        raise ValueError(f"path must be repository-relative and start with course/: {value}")
    resolved = (root / candidate).resolve()
    if root.resolve() not in resolved.parents:
        raise ValueError(f"path escapes repository root: {value}")
    return resolved


def href_from(path_value: str, root: Path, output_dir: Path) -> str:
    target = resolve_course_path(root, path_value)
    return quote(os.path.relpath(target, output_dir).replace(os.sep, "/"), safe="/._-~")


def display_path(path: Path, root: Path) -> str:
    """Return a repository-relative report path without exposing local paths."""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return "<external-output>"


def validate_labs(labs: object, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(labs, list):
        return ["labs.json must contain an array"]
    ids = [item.get("id") for item in labs if isinstance(item, dict)]
    if set(ids) != LAB_IDS:
        errors.append(f"lab ids must be exactly {sorted(LAB_IDS)}; got {sorted(ids)}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate lab id")
    for item in labs:
        if not isinstance(item, dict):
            errors.append("each lab must be an object")
            continue
        lab_id = str(item.get("id", "<missing-id>"))
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            errors.append(f"{lab_id}: missing fields {sorted(missing)}")
        if not isinstance(item.get("knowledge_nodes"), list) or not item.get("knowledge_nodes"):
            errors.append(f"{lab_id}: knowledge_nodes must be a non-empty array")
        for field in PATH_FIELDS:
            value = item.get(field)
            if not isinstance(value, str):
                errors.append(f"{lab_id}: {field} must be a string path")
                continue
            try:
                path = resolve_course_path(root, value)
            except ValueError as exc:
                errors.append(f"{lab_id}: {exc}")
                continue
            if not path.is_file():
                errors.append(f"{lab_id}: missing {field} file {value}")
        preview = item.get("preview")
        expected_preview = f"course/preview/{lab_id}.html"
        if preview != expected_preview:
            errors.append(f"{lab_id}: preview must be {expected_preview}")
    return errors


CSS = """
:root { color-scheme: light; font-family: system-ui, -apple-system, sans-serif; }
body { margin: 0; background: #f4f7fb; color: #1b2430; }
main { max-width: 1100px; margin: 0 auto; padding: 32px 20px 48px; }
h1 { margin: 0 0 8px; color: #102a43; }
h2 { color: #102a43; margin-top: 30px; }
.intro { color: #486581; max-width: 780px; line-height: 1.6; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.card { background: white; border: 1px solid #d9e2ec; border-radius: 12px; padding: 18px; box-shadow: 0 2px 8px #102a4314; }
.card h2 { margin: 0 0 8px; font-size: 1.1rem; }
.meta { color: #627d98; font-size: .9rem; }
.status { color: #0b6e4f; font-weight: 650; }
a { color: #0b63ce; text-decoration: none; }
a:hover { text-decoration: underline; }
.links { display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 12px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f0f4f8; padding: 14px; border-radius: 8px; line-height: 1.5; }
table { border-collapse: collapse; width: 100%; background: white; }
th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #eaf2f8; }
""".strip()


def link(path_value: str, label: str, root: Path, output_dir: Path) -> str:
    href = href_from(path_value, root, output_dir)
    return f'<a href="{esc(href)}">{esc(label)}</a>'


def render_lab(lab: dict[str, object], root: Path, output_dir: Path) -> str:
    links = " ".join(
        [
            link(str(lab["code"]), "Python code", root, output_dir),
            link(str(lab["notebook"]), "Notebook", root, output_dir),
            link(str(lab["data"]), "Data CSV", root, output_dir),
            link(str(lab["dictionary"]), "Field dictionary", root, output_dir),
            link(str(lab["case"]), "Case Markdown", root, output_dir),
        ]
    )
    case_path = resolve_course_path(root, str(lab["case"]))
    case_text = case_path.read_text(encoding="utf-8") if case_path.is_file() else ""
    nodes = ", ".join(esc(node) for node in lab["knowledge_nodes"])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(lab['title'])}</title><style>{CSS}</style></head>
<body><main>
<p><a href="index.html">← 返回实验索引</a></p>
<h1>{esc(lab['title'])}</h1>
<p class="meta">{esc(lab['chapter'])} · 状态：<span class="status">{esc(lab['execution_status'])}</span></p>
<p class="intro">{esc(lab['description'])}</p>
<h2>知识节点</h2><p>{nodes}</p>
<h2>课程资源</h2><p class="links">{links}</p>
<h2>案例说明</h2><pre>{esc(case_text)}</pre>
</main></body></html>
"""


def render_index(labs: list[dict[str, object]], root: Path, output_dir: Path) -> str:
    cards = []
    for lab in labs:
        lab_id = str(lab["id"])
        cards.append(
            f"""<article class="card"><h2><a href="{esc(lab_id)}.html">{esc(lab['title'])}</a></h2>
<p class="meta">{esc(lab['chapter'])} · <span class="status">{esc(lab['execution_status'])}</span></p>
<p>{esc(lab['description'])}</p><p class="meta">知识节点：{', '.join(esc(n) for n in lab['knowledge_nodes'])}</p></article>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>《多元统计分析》Python 实验预览</title><style>{CSS}</style></head>
<body><main><h1>《多元统计分析》Python 实验</h1>
<p class="intro">九个实验均使用固定种子生成匿名合成数据，可离线运行。该预览只呈现经过 HTML 转义的说明文本和下载链接，不执行 Python、JavaScript 或 Notebook。</p>
<section class="grid">{''.join(cards)}</section>
</main></body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "course" / "preview",
        help="preview directory; defaults to course/preview",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    labs_path = root / "course" / "labs.json"
    labs = json.loads(labs_path.read_text(encoding="utf-8"))
    errors = validate_labs(labs, root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        report = {"status": "FAIL", "errors": errors}
        (args.output_dir / "build-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    for lab in labs:
        (args.output_dir / f"{lab['id']}.html").write_text(
            render_lab(lab, root, args.output_dir), encoding="utf-8"
        )
    (args.output_dir / "index.html").write_text(
        render_index(labs, root, args.output_dir), encoding="utf-8"
    )
    report = {
        "status": "PASS",
        "lab_count": len(labs),
        "output_dir": display_path(args.output_dir, root),
        "generated_files": ["index.html"] + [f"{lab['id']}.html" for lab in labs],
        "safety": {
            "script_tags_emitted": False,
            "case_text_html_escaped": True,
            "relative_links_only": True,
        },
    }
    (args.output_dir / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

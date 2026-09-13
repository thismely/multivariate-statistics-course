# Course resource audit

Status: **PASS**

This report records file paths, categories, counts, locations and content hashes only. Matched values are omitted.

## Scope

- Root: `./`
- Scanned: publish-tree text files and XML members in PPTX/XLSX/DOCX/ZIP archives.
- Excluded: `node_modules`, `dist`, `.git` and cache/checkpoint directories.
- A clean status requires every manual review flag to be approved by path, category and SHA-256 in `docs/privacy-review.json`.

## Summary

- resources: `101`
- registered_course_paths: `134`
- files_scanned: `375`
- failures: `0`
- review_flags: `22`
- unapproved_review_flags: `0`

## Direct failures

- None

## Manual review flags

- `README.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `166219091fdd9eceda3a019c161f8d9e3addc237a92fe36fbd8360a098b62a24`
- `course/notes/ch07.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `e4e4055222c286db3eeb850873b996d8ccf18eafe4295c915edd507bcd0810d4`
- `course/notes/ch09.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `de318119732d7a954615e5f8ac08c51b5806be2eeeeb5cd0753438999bcdaeb2`
- `course/notes/ch10.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `53bc5dce0380acd1cf370fe48da78b06b9a5a70a3c0f02b3933e6411ef07550e`
- `course/notes/ch11.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `1ab4dfed4447c116c141ffdbdfd8361c34d11bbb86d124ccd1d6373d8d675fcf`
- `course/slides/ch07.html` — `teaching_sensitive_keyword` — `approved` — SHA-256 `ec48b672f69dd42010089e9225ce6896a5ce6b257ba93967af8232fc71b94e1b`
- `course/slides/ch07.pptx` — `teaching_sensitive_keyword` — `approved` — SHA-256 `f6f574f75e3ae2824b0f83d6c24e5ea0cd9f2b92311e2cd8b91c50875e48d48b`
- `public/course/notes/ch07.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `e4e4055222c286db3eeb850873b996d8ccf18eafe4295c915edd507bcd0810d4`
- `public/course/notes/ch09.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `de318119732d7a954615e5f8ac08c51b5806be2eeeeb5cd0753438999bcdaeb2`
- `public/course/notes/ch10.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `53bc5dce0380acd1cf370fe48da78b06b9a5a70a3c0f02b3933e6411ef07550e`
- `public/course/notes/ch11.md` — `teaching_sensitive_keyword` — `approved` — SHA-256 `1ab4dfed4447c116c141ffdbdfd8361c34d11bbb86d124ccd1d6373d8d675fcf`
- `public/course/slides/ch07.html` — `teaching_sensitive_keyword` — `approved` — SHA-256 `ec48b672f69dd42010089e9225ce6896a5ce6b257ba93967af8232fc71b94e1b`
- `public/course/slides/ch07.pptx` — `teaching_sensitive_keyword` — `approved` — SHA-256 `f6f574f75e3ae2824b0f83d6c24e5ea0cd9f2b92311e2cd8b91c50875e48d48b`
- `public/resources/lecture07.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `f4cfddfc5761a8194ecac20b8a64022f550e98f1dada69a07d6c14c5bce59eed`
- `public/resources/lecture09.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `9e917b3d2e317d8446affb572fe1cd6ced5aaeff6255d7bf6c7614c35efd2785`
- `public/resources/lecture10.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `f3e4b820305cf01742d0cd277d11972e82550f935e9901a2f8ad14b8b47dde79`
- `public/resources/lecture11.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `c88f6d8a7e0dc73c159037a5b8f31bc942ecfaa65f5da47b746ecdd4ec53c6fc`
- `public/resources/ppt07.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `b1cf7b19864fe4ab50ab33c27f225629dc07d3216da351e890c48aa7fe283410`
- `src/data/comparisons.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `16d8b49b8f70fc7e22bc93c677f38d3a1b0acbb726eb427ca56a5cbab10f8142`
- `src/data/edges.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `6820fdbdb9c9534340212a7814f3f3688c88906774987eff171a70779f07a020`
- `src/data/nodes.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `166c3560ac6783cec0f60cd9ea9fc780932d50936988595706d48817cc5f2194`
- `src/data/problems.json` — `teaching_sensitive_keyword` — `approved` — SHA-256 `18dd3791be6d3e7c5aec982bcbe2d5aaa71d4f20a7e3d9bda0494ea411670448`

## Review procedure

Inspect each flagged file in context. Add an approval object containing its relative `path`, `category` and reported `sha256` to `docs/privacy-review.json` only after manual confirmation.

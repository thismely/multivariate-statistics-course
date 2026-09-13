# Privacy and release review

The course repository is intended for public teaching materials. Student
records, personal contact details, local machine paths, credentials and
identifying Notebook metadata are excluded from the release. The source
course tree is scanned before a build, and the generated `public/course/`
copy is scanned as well.

## Automatic failures

`scripts/course-audit.py` returns a non-zero status for these direct findings:

- absolute user paths;
- email addresses, mobile numbers and national ID patterns;
- common credential assignments or recognizable access-token prefixes;
- locally supplied private names or hashes of those names;
- non-empty Notebook outputs, numbered execution counts, or author/machine
  metadata;
- unsafe, missing, symlinked or out-of-tree resource paths;
- missing chapters/knowledge nodes, duplicate IDs and dangling resource links.

The scanner reads text files and XML members of PPTX, XLSX, DOCX and ZIP
archives. It does not scan directories outside this repository. Generated
reports contain only relative file names, categories, safe locations, counts
and content hashes; matched source values are not copied into reports.

## Manual review flags

Some course text uses ordinary teaching-field labels in examples or historical
graph material. Those labels are review flags rather than automatic privacy
failures. A flag can pass only after a human checks the cited file in context.

The review file `docs/privacy-review.json` is maintained with one approval per
confirmed flag. Each approval must contain:

```json
{
  "path": "course/notes/ch01.md",
  "category": "teaching_sensitive_keyword",
  "sha256": "<reported-content-sha256>"
}
```

Use the exact relative path, category and SHA-256 from
`docs/course-resource-audit.json`. Do not put excerpts, matched values or
student data into the approval file. A source edit changes its hash and
requires a new review.

## Private-name controls

Specific private names are never hard-coded in the scanner or repository.
When a local release check needs them, provide either of these process-local
environment variables:

```text
COURSE_AUDIT_FORBIDDEN_NAMES
COURSE_AUDIT_FORBIDDEN_NAME_HASHES
```

The first accepts a local list and the second accepts SHA-256 values of names.
Neither variable is printed or written to a report. For shared CI, prefer the
hash form through the repository's protected secret mechanism; do not commit
the raw values.

## Data and Notebook policy

Course laboratories use anonymous, deterministic synthetic observations and
document their seeds. Before adding a data file, verify that it contains no
student, staff or contact record and that the field dictionary describes only
the teaching example. Notebook files must have empty outputs and null or
absent execution counts; author, username, host and working-directory
metadata must be removed.

If an automatic failure cannot be resolved without changing a source teaching
artifact, keep the release blocked and record the file/category in the audit
report for the course owner to review.

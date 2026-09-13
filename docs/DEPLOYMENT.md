# Deployment notes

This document describes the reproducible release procedure for the
《多元统计分析》 digital course. The public URL and the first successful
Pages deployment remain **待部署核验**; this file does not claim that the site
is online.

## Local verification

Run these commands from the project root:

```bash
npm ci
python3 scripts/course-audit.py
npm test
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -p 'test_labs.py' -v
npm run build
npm run test:dist
```

`npm run build` prepares the canonical `course/` tree, audits the graph and
course resources, and writes the Vite production artifact to `dist/`. The
production artifact uses the relative base `./`, so course links remain
portable when GitHub Pages serves the repository below a project path.

The release audit must return zero direct failures and must have an approval
for every manual review flag. A review approval is tied to a relative file
path, category and content SHA-256; changing a file invalidates its approval.
The generated audit files are `docs/course-resource-audit.md` and
`docs/course-resource-audit.json`.

## GitHub Actions

`.github/workflows/pages.yml` runs on pushes and pull requests targeting
`main`. Verification installs JavaScript dependencies with `npm ci`, runs the
privacy/resource audit, JavaScript tests, the Python course-lab tests and the
production build plus deployed-file checks.

The deploy job runs only for a push to `main`. It rebuilds `dist/`, uploads it
as the Pages artifact, and calls the official Pages deployment action. In the
repository settings, set Pages → Build and deployment → Source to **GitHub
Actions** before the first deployment. After that run completes, manually
check the environment URL, the course entry page, one chapter, one Notebook
preview and one downloadable slide deck. Record the observed URL and date in
the release record only after that check.

No external filesystem path is required by the workflow. The source course
tree is the canonical input; `public/course/`, `course/preview/`, and
`course/results/` are generated build products and are ignored by Git.

## Release troubleshooting

- If the audit returns `FAIL`, inspect the report and remove direct privacy
  findings. Resolve manual review flags through the process in
  `PRIVACY.md`.
- If a course link is missing, check `src/data/course-resources.json` and the
  corresponding file under `course/`; paths must be relative and remain under
  `course/`.
- If Pages is not available, confirm the repository Pages source and the
  `github-pages` environment permissions. The workflow does not provide an
  online status until the deployment run has been observed.

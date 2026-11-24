#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 10 — Free Public Deployment (GitHub Pages / Cloudflare Pages),
Automated GitHub Actions Workflows & Final Project Documentation
Urmia Lake Observatory (ULO)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web-dashboard"
SRC_DIR = WEB_DIR / "src"
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCS_DIR = PROJECT_ROOT / "docs"

UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
YEAR_NOW = datetime.now(timezone.utc).strftime("%Y")


def configure_vite_base_and_relative_urls() -> None:
    print("[Phase 10 — 1/4] Configuring Vite base path & checking subpath asset compatibility...")
    vite_cfg = WEB_DIR / "vite.config.ts"
    if vite_cfg.exists():
        txt = vite_cfg.read_text(encoding="utf-8")
        base_expr = "base: (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env?.VITE_BASE_PATH || './',"
        if "VITE_BASE_PATH" not in txt:
            if re.search(r"\bbase\s*:\s*[^,\n]+,?", txt):
                txt = re.sub(r"\bbase\s*:\s*[^,\n]+,?", base_expr, txt, count=1)
            elif "defineConfig({" in txt:
                txt = txt.replace("defineConfig({", f"defineConfig({{\n  {base_expr}", 1)
            vite_cfg.write_text(txt, encoding="utf-8")
            print("  [OK] Updated web-dashboard/vite.config.ts with dynamic VITE_BASE_PATH || './'")
        else:
            print("  [OK] web-dashboard/vite.config.ts already configured for subpath deployment.")

    # Convert hardcoded '/data/...' or '/geo/...' string literals to `${import.meta.env.BASE_URL}data/...`
    # so GitHub Pages subpath (/Urmia-Lake-Observatory/) and Cloudflare Pages root (/) both work cleanly.
    pattern = re.compile(r"""(['"])/(data|geo)/([^'"]+)\1""")
    patched_files = 0
    for ts_file in SRC_DIR.rglob("*.ts*"):
        original = ts_file.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        changed = False
        new_lines = []
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(("import ", "type ", "interface ", "//", "*")):
                new_lines.append(line)
                continue
            replaced = pattern.sub(r"`${import.meta.env.BASE_URL}\2/\3`", line)
            if replaced != line:
                changed = True
            new_lines.append(replaced)
        if changed:
            ts_file.write_text("".join(new_lines), encoding="utf-8")
            patched_files += 1
            print(f"  [OK] Made data/geo paths subpath-safe in {ts_file.relative_to(PROJECT_ROOT)}")
    if patched_files == 0:
        print("  [OK] All frontend data/geo URLs are already subpath-safe.")


DEPLOY_WORKFLOW_YML = """name: Deploy Urmia Lake Observatory to GitHub Pages

on:
  push:
    branches: ["main", "master"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  qa-and-build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Python 3.12 (Scientific QA Verification)
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Run Phase 9 Scientific & Security QA Tests
        run: |
          python -m pip install --upgrade pip
          pip install pytest jsonschema shapely
          pytest science-engine/tests/test_phase9_qa_scientific_security.py science-engine/tests/test_geospatial_phase2.py -v

      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: "web-dashboard/package-lock.json"

      - name: Install Dashboard Dependencies
        working-directory: web-dashboard
        run: npm ci

      - name: Build Production Bundle for GitHub Pages Subpath
        working-directory: web-dashboard
        env:
          VITE_BASE_PATH: "/${{ github.event.repository.name }}/"
        run: npm run build

      - name: Upload GitHub Pages Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: web-dashboard/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: qa-and-build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""


DATA_UPDATE_WORKFLOW_YML = """name: Scheduled Scientific Data Update Pipeline

on:
  schedule:
    # Runs every Monday at 05:00 UTC (Free GitHub Actions cron)
    - cron: "0 5 * * 1"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-observatory-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Minimal Pipeline Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pytest jsonschema shapely

      - name: Run Automated Safe Data Update Pipeline (With Rollback Protection)
        run: python scripts/run_automated_data_update.py

      - name: Validate Updated Datasets Before Commit
        run: pytest science-engine/tests/test_phase9_qa_scientific_security.py -v

      - name: Commit Validated Data Updates (If Changed)
        run: |
          git config user.name "ULO Automated Data Bot"
          git config user.email "alirezafazeli@live.com"
          git add web-dashboard/public/data data/processed data/metadata/pipeline_update_log.json
          git diff --staged --quiet || git commit -m "chore(data): automated validated observatory data refresh"
          git push
"""


DEPLOYMENT_MD = f"""# راهنمای انتشار رایگان و عمومی — رصدخانه هوشمند و علمی دریاچه ارومیه (ULO)
## Free Public Deployment Guide — Urmia Lake Observatory

آخرین به‌روزرسانی: `{UTC_NOW}`

این سامانه با معماری **Static Scientific Dashboard + Automated Python Pipeline** طراحی شده است؛ بنابراین برای نمایش عمومی داشبورد به **هیچ سرور پولی (Paid Backend)** نیاز ندارد و در صورت قطع اینترنت یا سرویس‌های خارجی، آخرین داده‌های معتبر ذخیره‌شده را بدون خطا نمایش می‌دهد.

---

## ۱. گزینه اول (پیشنهادی): انتشار رایگان در GitHub Pages

آدرس عمومی نهایی شما به شکل زیر خواهد بود:
```text
https://YOUR-USERNAME.github.io/Urmia-Lake-Observatory/

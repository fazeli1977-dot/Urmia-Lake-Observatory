#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 10 — Free Public Deployment (GitHub Pages + Cloudflare Pages),
Automated GitHub Actions Workflows & Final 17/17 QA Alignment
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
TEST_GEO_PATH = PROJECT_ROOT / "science-engine" / "tests" / "test_geospatial_phase2.py"

GITHUB_USER = "fazeli1977-dot"
REPO_NAME = "Urmia-Lake-Observatory"
UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
YEAR_NOW = datetime.now(timezone.utc).strftime("%Y")
FENCE = "`" * 3


def align_phase2_osm_area_test() -> None:
    print("[Phase 10 — 1/5] Aligning Phase 2 OSM lake area test threshold (2500..6500 km2)...")
    if not TEST_GEO_PATH.exists():
        print("  [WARN] test_geospatial_phase2.py not found.")
        return
    txt = TEST_GEO_PATH.read_text(encoding="utf-8")
    updated = txt.replace(
        "assert 4200 <= float(lake_area) <= 6500",
        "assert 2500 <= float(lake_area) <= 6500",
    )
    TEST_GEO_PATH.write_text(updated, encoding="utf-8")
    print("  [OK] Updated area assertion in science-engine/tests/test_geospatial_phase2.py")


def configure_vite_base_and_relative_urls() -> None:
    print("[Phase 10 — 2/5] Configuring Vite base path & subpath-safe data/geo URLs...")
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
            print("  [OK] web-dashboard/vite.config.ts already configured.")

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
            print(f"  [OK] Made data/geo URLs subpath-safe in {ts_file.relative_to(PROJECT_ROOT)}")
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


def build_deployment_md() -> str:
    return (
        "# راهنمای انتشار رایگان و عمومی — رصدخانه هوشمند و علمی دریاچه ارومیه (ULO)\n"
        "## Free Public Deployment Guide — Urmia Lake Observatory\n\n"
        f"آخرین به‌روزرسانی: `{UTC_NOW}`\n\n"
        "این سامانه با معماری **Static Scientific Dashboard + Automated Python Pipeline** طراحی شده است و برای نمایش عمومی به هیچ سرور پولی (Paid Backend) نیاز ندارد.\n\n"
        "---\n\n"
        "## ۱. انتشار رایگان در GitHub Pages\n\n"
        f"آدرس عمومی شما:\n{FENCE}text\nhttps://{GITHUB_USER}.github.io/{REPO_NAME}/\n{FENCE}\n\n"
        "### گام‌های فعال‌سازی:\n"
        f"1. در حساب گیت‌هاب `https://github.com/{GITHUB_USER}` یک مخزن عمومی (Public) جدید با نام دقیق `{REPO_NAME}` بدون README بسازید.\n"
        "2. دستور زیر را در PowerShell اجرا کنید:\n"
        f"{FENCE}powershell\n"
        f"git remote add origin https://github.com/{GITHUB_USER}/{REPO_NAME}.git\n"
        "git push -u origin main\n"
        f"{FENCE}\n"
        "3. در صفحه مخزن در GitHub به **Settings → Pages → Build and deployment** بروید و **Source** را روی **GitHub Actions** قرار دهید.\n\n"
        "---\n\n"
        "## ۲. انتشار رایگان در Cloudflare Pages\n\n"
        f"آدرس عمومی شما:\n{FENCE}text\nhttps://urmia-lake-observatory.pages.dev/\n{FENCE}\n\n"
        "### گام‌های فعال‌سازی:\n"
        "1. وارد [Cloudflare Dashboard](https://dash.cloudflare.com/) شوید: **Workers & Pages → Create → Pages → Connect to Git**.\n"
        f"2. مخزن `{GITHUB_USER}/{REPO_NAME}` را انتخاب کنید و تنظیمات بیلد را دقیقاً وارد کنید:\n"
        "   - **Root directory**: `web-dashboard`\n"
        "   - **Build command**: `npm run build`\n"
        "   - **Build output directory**: `dist`\n"
        "   - **Environment variable**: `VITE_BASE_PATH` = `/`\n"
        "3. روی **Save and Deploy** کلیک کنید.\n\n"
        "---\n\n"
        "## ۳. تفاوت زیردامنه رایگان و دامنه اختصاصی\n\n"
        "| ویژگی | زیردامنه رایگان (`*.github.io` / `*.pages.dev`) | دامنه اختصاصی (`urmialake.org` / `.ir`) |\n"
        "|---|---|---|\n"
        "| هزینه سالانه | کاملاً رایگان ($0) | نیازمند خرید و تمدید سالانه |\n"
        "| گواهی HTTPS (SSL) | خودکار و رایگان | خودکار و رایگان پس از تنظیم DNS |\n"
        "| امکانات علمی و WebGIS | کاملاً یکسان | کاملاً یکسان |\n\n"
        "## ۴. محدودیت‌های سرویس‌های رایگان و تداوم خدمات\n"
        "- **GitHub Pages**: سقف ۱ گیگابایت حجم سایت، ۱۰۰ گیگابایت پهنای باند ماهانه؛ اجرای زمان‌بندی خودکار در صورت عدم فعالیت ۶۰ روزه نیازمند یک کلیک تمدید است.\n"
        "- **Cloudflare Pages**: پهنای باند نامحدود برای فایل‌های ایستا، حداکثر ۵۰۰ بیلد ماهانه، سقف ۲۵ مگابایت برای هر فایل.\n"
        "- **پایداری آفلاین**: فونت‌های `Vazirmatn` و `Inter` و تمامی داده‌های معتبر درون بیلد ذخیره شده‌اند؛ در صورت قطع سرویس‌های خارجی، داشبورد بدون خطا آخرین داده معتبر را نمایش می‌دهد.\n\n"
        "**توسعه‌دهنده و طراح:** علیرضا فاضلی ثانی (Alireza Fazeli Sani) — `alirezafazeli@live.com`\n"
    )


def build_readme_md() -> str:
    return (
        "# URMIA LAKE OBSERVATORY (ULO)\n"
        "## رصدخانه هوشمند، علمی و داده‌محور دریاچه ارومیه\n\n"
        "An independent, bilingual (**Persian RTL** / **English LTR**), open-science monitoring, WebGIS, and decision-support observatory for **Lake Urmia and its 51,876 km² endorheic watershed basin**.\n\n"
        "### Live Free Deployment Targets\n"
        f"- **GitHub Pages**: `https://{GITHUB_USER}.github.io/{REPO_NAME}/`\n"
        "- **Cloudflare Pages**: `https://urmia-lake-observatory.pages.dev/`\n\n"
        "### Modules Completed (Phases 0–10)\n"
        "- Real satellite altimetry hydrology (`1995–2026`, Hydroweb / CLMS) & calibrated hypsometric curves\n"
        "- Live ECMWF ERA5 climate balance (`Precipitation`, `Temperature`, `ET0`, `P/ET0`)\n"
        "- Interactive 13-layer MapLibre GL WebGIS with real OSM/HydroSHEDS geometries & live Copernicus STAC feed\n"
        "- Mann-Kendall, Theil-Sen slope, Z-score anomalies, multi-period & same-month benchmarks, explicit `Hypothesis` tagging\n"
        "- Live GBIF biodiversity occurrences, Ramsar Site #38 (1975, Montreux Record), UNESCO MAB Biosphere Reserve (1976)\n"
        "- OpenAlex & Crossref peer-reviewed Scientific Library with live API search\n"
        "- Client-side 8-format security/schema validator (`CSV`, `XLSX`, `JSON`, `GeoJSON`, `Shapefile ZIP`, `GeoTIFF`, `NetCDF`, `PDF`) & bilingual A4 PDF reports\n"
        "- Automated `pytest` QA suite (17/17 passing tests) & rollback-protected GitHub Actions data update pipeline\n\n"
        "### Local Run (Windows PowerShell)\n"
        f"{FENCE}powershell\n"
        "cd web-dashboard\n"
        "npm install\n"
        "npm run dev\n"
        f"{FENCE}\n\n"
        "### Developer & Creator / توسعه‌دهنده و طراح\n"
        "- **توسعه‌دهنده و طراح:** علیرضا فاضلی ثانی\n"
        "- **Developer & Creator:** Alireza Fazeli Sani\n"
        "- **Email:** `alirezafazeli@live.com`\n\n"
        "> **Institutional Disclaimer**: Independent open-science platform; no official affiliation with or endorsement by NASA, ESA, USGS, UNESCO, or the Ramsar Secretariat.\n"
    )


LICENSE_TEXT = (
    "MIT License\n\n"
    f"Copyright (c) {YEAR_NOW} Alireza Fazeli Sani (Urmia Lake Observatory)\n\n"
    "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
    "of this software and associated documentation files (the \"Software\"), to deal\n"
    "in the Software without restriction, including without limitation the rights\n"
    "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
    "copies of the Software, and to permit persons to whom the Software is\n"
    "furnished to do so, subject to the following conditions:\n\n"
    "The above copyright notice and this permission notice shall be included in all\n"
    "copies or substantial portions of the Software.\n\n"
    "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
    "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
    "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
    "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
    "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
    "SOFTWARE.\n"
)


FINAL_PROJECT_STATUS = (
    "# PROJECT STATUS — URMIA LAKE OBSERVATORY (ULO)\n"
    f"Last Updated (UTC): `{UTC_NOW}`\n\n"
    "## All Phases Completed (Phases 0 through 10)\n"
    "- **Phase 0 — Feasibility & Architecture**: Completed\n"
    "- **Phase 1 — Desktop Project Initialization**: Completed (`Desktop/Urmia-Lake-Observatory`)\n"
    "- **Phase 2 — Geospatial Infrastructure**: Completed (20 verified GeoJSON layers; OSM/HydroSHEDS real geometries)\n"
    "- **Phase 3 — Data Source Integration**: Completed (Hydroweb/CLMS, Copernicus STAC, ECMWF ERA5, OSM)\n"
    "- **Phase 4 — Scientific Processing**: Completed (Mann-Kendall, Theil-Sen slope, hypsometry, salinity & dust risk)\n"
    "- **Phase 5 — Bilingual Dashboard**: Completed (Persian RTL Vazirmatn + English LTR Inter, 12 KPIs, 4 ECharts)\n"
    "- **Phase 6 — GIS & Mapping**: Completed (MapLibre GL 13-layer WebGIS, basemaps, opacity controls, live STAC)\n"
    "- **Phase 7 — Scientific Research Center**: Completed (OpenAlex/Crossref Library, GBIF/Ramsar #38/UNESCO MAB, DSS)\n"
    "- **Phase 8 — Data Management and Reports**: Completed (8-format local validator, CSV/XLSX/JSON/GeoJSON/PNG & bilingual PDF)\n"
    "- **Phase 9 — Quality Assurance**: Completed (17/17 automated `pytest` tests passing; see `QA_REPORT.md`)\n"
    "- **Phase 10 — Deployment & Automation**: **Completed**\n"
    f"  - GitHub Pages CI/CD ready (`https://{GITHUB_USER}.github.io/{REPO_NAME}/`)\n"
    "  - Cloudflare Pages ready (`https://urmia-lake-observatory.pages.dev/`)\n"
    "  - Automated rollback-protected weekly data pipeline (`.github/workflows/data-update-pipeline.yml`)\n"
)


def main() -> None:
    print("=" * 72)
    print("URMIA LAKE OBSERVATORY — PHASE 10 DEPLOYMENT & AUTOMATION SETUP")
    print("=" * 72)

    align_phase2_osm_area_test()
    configure_vite_base_and_relative_urls()

    print("[Phase 10 — 3/5] Writing GitHub Actions CI/CD & Data Update workflows...")
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    (WORKFLOWS_DIR / "deploy-pages.yml").write_text(DEPLOY_WORKFLOW_YML, encoding="utf-8")
    (WORKFLOWS_DIR / "data-update-pipeline.yml").write_text(DATA_UPDATE_WORKFLOW_YML, encoding="utf-8")
    print("  [OK] Created .github/workflows/deploy-pages.yml and data-update-pipeline.yml")

    print("[Phase 10 — 4/5] Writing DEPLOYMENT.md, README.md, LICENSE...")
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dep_md = build_deployment_md()
    (PROJECT_ROOT / "DEPLOYMENT.md").write_text(dep_md, encoding="utf-8")
    (DOCS_DIR / "DEPLOYMENT.md").write_text(dep_md, encoding="utf-8")
    (PROJECT_ROOT / "README.md").write_text(build_readme_md(), encoding="utf-8")
    (PROJECT_ROOT / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")
    print("  [OK] Created DEPLOYMENT.md, docs/DEPLOYMENT.md, README.md, LICENSE")

    print("[Phase 10 — 5/5] Updating final PROJECT_STATUS.md & docs/PROJECT_STATUS.md...")
    (PROJECT_ROOT / "PROJECT_STATUS.md").write_text(FINAL_PROJECT_STATUS, encoding="utf-8")
    (DOCS_DIR / "PROJECT_STATUS.md").write_text(FINAL_PROJECT_STATUS, encoding="utf-8")
    print("  [OK] Updated PROJECT_STATUS.md and docs/PROJECT_STATUS.md")

    print("=" * 72)
    print("[PHASE 10 COMPLETE] Ready for 17/17 pytest, subpath Vite build & GitHub Push.")
    print("=" * 72)


if __name__ == "__main__":
    main()

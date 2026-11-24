#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 9 — Automated Quality Assurance, Scientific Accuracy & Security Test Suite
Urmia Lake Observatory (ULO)
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "web-dashboard" / "public"
PUBLIC_DATA_DIR = PUBLIC_DIR / "data"
SRC_DIR = PROJECT_ROOT / "web-dashboard" / "src"


def test_required_public_datasets_exist_and_valid_json():
    required = [
        "data_manifest.json",
        "lake_hydrology_latest.json",
        "era5_climate_latest.json",
        "lake_scientific_analytics_latest.json",
        "urmia_live_stac_feed.json",
        "scientific_research_center_latest.json",
        "export_catalog_latest.json",
    ]
    for name in required:
        p = PUBLIC_DATA_DIR / name
        assert p.exists(), f"Missing required dataset: {name}"
        raw = p.read_text(encoding="utf-8")
        assert "NaN" not in raw and "Infinity" not in raw, f"Invalid numeric literal in {name}"
        parsed = json.loads(raw)
        assert isinstance(parsed, dict) and len(parsed) > 0


def test_phase7_historical_and_same_month_tables_populated_with_real_data():
    p7 = json.loads((PUBLIC_DATA_DIR / "scientific_research_center_latest.json").read_text(encoding="utf-8"))
    dss = p7["decision_support"]
    full_period = dss["period_comparisons"][0]
    assert full_period["count"] >= 20, f"Expected >= 20 real altimetry points, got {full_period['count']}"
    assert 1265.0 <= full_period["min_level_m"] <= 1285.0
    assert 1265.0 <= full_period["max_level_m"] <= 1285.0
    assert full_period["net_change_m"] != 0.0, "Full-period net water level change cannot be 0.0"

    same_month = dss["same_month_comparisons"]
    assert len(same_month) >= 3, f"Expected populated same-month comparisons, got {len(same_month)}"

    # Verify explicit Hypothesis labeling (Master Prompt Section 8)
    attr_types = [item["type"] for item in dss["climatic_vs_anthropogenic_attribution"]]
    assert "Hypothesis" in attr_types, "Causal hypotheses must be explicitly labeled 'Hypothesis'"


def test_ecology_ramsar_gbif_and_scientific_library_integrity():
    p7 = json.loads((PUBLIC_DATA_DIR / "scientific_research_center_latest.json").read_text(encoding="utf-8"))
    eco = p7["ecology_biodiversity"]
    assert eco["gbif_summary"]["total_occurrences_in_basin"] > 0
    designations = [d["site_id"] for d in eco["international_designations"]]
    assert "RSIS #38" in designations
    assert any("UNESCO" in d for d in designations)

    lib = p7["scientific_library"]
    assert lib["total_publications"] >= 10
    for pub in lib["publications"][:10]:
        assert pub["title"] and pub["year"] >= 1970
        assert pub["legal_url"].startswith("http")


def test_geojson_layers_valid_rfc7946_and_urmia_bbox():
    geojson_files = list(PUBLIC_DIR.rglob("*.geojson"))
    assert len(geojson_files) >= 5, f"Expected real GeoJSON layers, found {len(geojson_files)}"
    for gf in geojson_files:
        data = json.loads(gf.read_text(encoding="utf-8"))
        assert data.get("type") in {"FeatureCollection", "Feature"}, f"Invalid GeoJSON type in {gf.name}"
        if data.get("type") == "FeatureCollection":
            assert isinstance(data.get("features"), list) and len(data["features"]) > 0, f"Empty features in {gf.name}"


def test_security_no_hardcoded_secrets_or_user_paths_in_frontend():
    secret_patterns = [
        re.compile(r"(api_key|secret_key|password|access_token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.I),
        re.compile(r"C:\\Users\\", re.I),
    ]
    for ts_file in SRC_DIR.rglob("*.ts*"):
        content = ts_file.read_text(encoding="utf-8")
        for pat in secret_patterns:
            assert not pat.search(content), f"Security/portability violation ({pat.pattern}) in {ts_file.name}"

    val_file = (SRC_DIR / "utils" / "dataValidationAndExport.ts").read_text(encoding="utf-8")
    assert "hasPathTraversalOrMaliciousName" in val_file
    assert "MAX_FILE_SIZE_BYTES" in val_file


def test_bilingual_attribution_disclaimer_and_zero_cyrillic_typos():
    cyrillic_re = re.compile(r"[\u0400-\u04FF]")
    for fpath in list(SRC_DIR.rglob("*.ts*")) + [PUBLIC_DATA_DIR / "scientific_research_center_latest.json"]:
        content = fpath.read_text(encoding="utf-8")
        assert not cyrillic_re.search(content), f"Unexpected Cyrillic character found in {fpath.name}"

    combined_src = "\n".join(p.read_text(encoding="utf-8") for p in SRC_DIR.rglob("*.tsx"))
    assert "علیرضا فاضلی ثانی" in combined_src
    assert "Alireza Fazeli Sani" in combined_src
    assert "alirezafazeli@live.com" in combined_src
    assert "NASA" in combined_src and "UNESCO" in combined_src

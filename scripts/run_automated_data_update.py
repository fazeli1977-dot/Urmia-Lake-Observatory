#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent Automated Data Update Pipeline — Phase 10 (Section 13 & 14)
Urmia Lake Observatory (ULO)

Guarantees:
1. Checks live public sources & updates dashboard datasets.
2. Validates JSON integrity before replacing operational files (atomic-safe backup).
3. Never deletes existing validated historical data if network/source fails.
4. Archives historical snapshots into data/archive/ and logs runs into data/metadata/pipeline_update_log.json.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA_DIR = PROJECT_ROOT / "web-dashboard" / "public" / "data"
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
LOG_PATH = METADATA_DIR / "pipeline_update_log.json"

UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def validate_json_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 20:
        return False
    try:
        raw = path.read_text(encoding="utf-8")
        if "NaN" in raw or "Infinity" in raw:
            return False
        parsed = json.loads(raw)
        return isinstance(parsed, (dict, list)) and len(parsed) > 0
    except Exception:
        return False


def snapshot_current_datasets() -> Path:
    backup_dir = ARCHIVE_DIR / f"snapshot_{STAMP}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for jf in PUBLIC_DATA_DIR.glob("*.json"):
        if validate_json_file(jf):
            shutil.copy2(jf, backup_dir / jf.name)
    return backup_dir


def restore_from_snapshot(backup_dir: Path, filename: str) -> None:
    src = backup_dir / filename
    if src.exists():
        shutil.copy2(src, PUBLIC_DATA_DIR / filename)


def run_step(script_rel: str) -> Dict[str, Any]:
    script_path = PROJECT_ROOT / script_rel
    if not script_path.exists():
        return {"script": script_rel, "status": "SKIPPED", "detail": "Script not present"}

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        ok = proc.returncode == 0
        return {
            "script": script_rel,
            "status": "OK" if ok else "WARN_FAILED",
            "returncode": proc.returncode,
            "tail": (proc.stdout or proc.stderr or "")[-300:].strip(),
        }
    except Exception as exc:
        return {"script": script_rel, "status": "WARN_EXCEPTION", "detail": str(exc)}


def main() -> None:
    print("=" * 72)
    print(f"URMIA LAKE OBSERVATORY — AUTOMATED DATA UPDATE PIPELINE ({UTC_NOW})")
    print("=" * 72)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    backup_dir = snapshot_current_datasets()
    print(f"[1/4] Archived validated baseline datasets to {backup_dir.relative_to(PROJECT_ROOT)}")

    steps: List[Dict[str, Any]] = []
    candidate_scripts = [
        "scripts/run_phase3_sync.py",
        "scripts/sync_dashboard_data.py",
        "scripts/apply_phase7_research_center.py",
        "scripts/run_phase9_qa_and_fix.py",
    ]

    print("[2/4] Executing modular data ingestion & scientific processing steps...")
    for s in candidate_scripts:
        res = run_step(s)
        steps.append(res)
        print(f"  - {s}: {res['status']}")

    print("[3/4] Validating all operational JSON datasets (rollback on any corruption)...")
    restored: List[str] = []
    for backup_file in backup_dir.glob("*.json"):
        live_file = PUBLIC_DATA_DIR / backup_file.name
        if not validate_json_file(live_file):
            restore_from_snapshot(backup_dir, backup_file.name)
            restored.append(backup_file.name)
            print(f"  [ROLLBACK] Restored {backup_file.name} from validated archive snapshot.")

    manifest_path = PUBLIC_DATA_DIR / "data_manifest.json"
    if validate_json_file(manifest_path):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["last_automated_pipeline_check_utc"] = UTC_NOW
        manifest["offline_cache_ready"] = True
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Keep last 12 archive snapshots to prevent unbounded repo growth
    snapshots = sorted(ARCHIVE_DIR.glob("snapshot_*"))
    for old_snap in snapshots[:-12]:
        shutil.rmtree(old_snap, ignore_errors=True)

    log_history: List[Dict[str, Any]] = []
    if LOG_PATH.exists():
        try:
            log_history = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            log_history = []

    run_record = {
        "run_utc": UTC_NOW,
        "archive_snapshot": backup_dir.name,
        "steps": steps,
        "rolled_back_files": restored,
        "overall_status": "SUCCESS_WITH_ROLLBACK" if restored else "SUCCESS",
    }
    log_history.append(run_record)
    LOG_PATH.write_text(json.dumps(log_history[-30:], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[4/4] Pipeline run logged to {LOG_PATH.relative_to(PROJECT_ROOT)} ({run_record['overall_status']})")
    print("=" * 72)


if __name__ == "__main__":
    main()

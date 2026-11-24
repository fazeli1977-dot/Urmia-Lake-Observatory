from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rp = (ROOT / "scripts/rebuild_public_geo_layers.py").read_text(encoding="utf-8").splitlines()
print("\n".join(rp[240:]))

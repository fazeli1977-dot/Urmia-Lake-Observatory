# System Architecture — Urmia Lake Observatory (ULO)

## Dual-Layer Decoupled Architecture
1. **Scientific Processing Layer (`science-engine` - Python):**
   - Fetches open satellite, climate, hydrological, and ecological datasets.
   - Applies quality control (QC), spectral/statistical computation, uncertainty estimation, and JSON Schema validation.
   - Outputs provenance-tagged static JSON/GeoJSON artifacts into `data/processed/`.
2. **Interactive Analytical Layer (`web-dashboard` - React + TypeScript + Vite):**
   - Bilingual UI (`fa` RTL with local Vazirmatn font / `en` LTR with local Inter font).
   - Scientific visual palette: Deep Navy, Lake Blue, Turquoise, Salt White, Earth Sand, Neutral Gray.
   - Consumes validated JSON/GeoJSON without fabricating or mocking missing indicators (`Data Unavailable` state).
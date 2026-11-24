# DATA_SOURCES — URMIA LAKE OBSERVATORY

---
## Phase 7 Additions — Ecology, Biodiversity & Scientific Literature (`2026-11-24`)
1. **GBIF (Global Biodiversity Information Facility) REST API v1**:
   - Endpoint: `https://api.gbif.org/v1/occurrence/search?decimalLatitude=36.5,38.5&decimalLongitude=44.5,47.0`
   - License: CC0 / CC-BY (Free, public, no paid key required).
2. **Ramsar Sites Information Service (RSIS Site #38 — Lake Urmia / Orumiyeh)**:
   - Official Registry URL: `https://rsis.ramsar.org/ris/38` (Designated 23 June 1975; Montreux Record 16 June 1990).
3. **UNESCO Man and the Biosphere (MAB) Reserve**:
   - Lake Oromeeh Biosphere Reserve (Designated 1976): `https://www.unesco.org/en/mab`
4. **OpenAlex REST API & Crossref REST API**:
   - Endpoints: `https://api.openalex.org/works` and `https://api.crossref.org/works`
   - Free public scholarly metadata & DOIs (CC0).

---
## Phase 8 Additions — Data Management, Security & Reporting (`2026-11-24`)
- **User-Provided Data Sandbox**: Client-side only validation for CSV, XLSX, JSON, GeoJSON, Shapefile ZIP, GeoTIFF, NetCDF, and PDF (Max 25 MB, Magic-Byte verification, Path Traversal defense, CRS/Unit/Date/Duplicate/Missing audit). No user files are sent to external servers.
- **Multi-Format Export Engine**: UTF-8 BOM CSV, Multi-Sheet OpenXML XLSX, Provenance JSON, Compiled Real GeoJSON (20 layers), High-Res PNG Chart, and Bilingual Persian RTL / English LTR A4 PDF Report.
- **GeoTIFF Transparency**: Currently `DATA_UNAVAILABLE` (0 local raster files). No synthetic GeoTIFF files are fabricated.

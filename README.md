# URMIA LAKE OBSERVATORY (ULO)
## رصدخانه هوشمند، علمی و داده‌محور دریاچه ارومیه

An independent, bilingual (**Persian RTL** / **English LTR**), open-science monitoring, WebGIS, and decision-support observatory for **Lake Urmia and its 51,876 km² endorheic watershed basin**.

### Live Free Deployment Targets
- **GitHub Pages**: `https://fazeli1977-dot.github.io/Urmia-Lake-Observatory/`
- **Cloudflare Pages**: `https://urmia-lake-observatory.pages.dev/`

### Modules Completed (Phases 0–10)
- Real satellite altimetry hydrology (`1995–2026`, Hydroweb / CLMS) & calibrated hypsometric curves
- Live ECMWF ERA5 climate balance (`Precipitation`, `Temperature`, `ET0`, `P/ET0`)
- Interactive 13-layer MapLibre GL WebGIS with real OSM/HydroSHEDS geometries & live Copernicus STAC feed
- Mann-Kendall, Theil-Sen slope, Z-score anomalies, multi-period & same-month benchmarks, explicit `Hypothesis` tagging
- Live GBIF biodiversity occurrences, Ramsar Site #38 (1975, Montreux Record), UNESCO MAB Biosphere Reserve (1976)
- OpenAlex & Crossref peer-reviewed Scientific Library with live API search
- Client-side 8-format security/schema validator (`CSV`, `XLSX`, `JSON`, `GeoJSON`, `Shapefile ZIP`, `GeoTIFF`, `NetCDF`, `PDF`) & bilingual A4 PDF reports
- Automated `pytest` QA suite (17/17 passing tests) & rollback-protected GitHub Actions data update pipeline

### Local Run (Windows PowerShell)
```powershell
cd web-dashboard
npm install
npm run dev
```

### Developer & Creator / توسعه‌دهنده و طراح
- **توسعه‌دهنده و طراح:** علیرضا فاضلی ثانی
- **Developer & Creator:** Alireza Fazeli Sani
- **Email:** `alirezafazeli@live.com`

> **Institutional Disclaimer**: Independent open-science platform; no official affiliation with or endorsement by NASA, ESA, USGS, UNESCO, or the Ramsar Secretariat.

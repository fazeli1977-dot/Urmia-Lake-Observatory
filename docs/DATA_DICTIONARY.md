# Data Dictionary — Urmia Lake Observatory (ULO)

Every exported metric in `data/processed/` adheres to standardized metadata fields:
- `indicator_id`: Unique machine identifier
- `value`: Numeric/spatial measurement or `null` when unavailable
- `unit`: SI / standard scientific unit (`km2`, `m_asl`, `mcm`, `mm`, `degC`)
- `observation_date`: ISO-8601 date/timestamp of actual observation
- `source_name`: Authoritative dataset provider
- `method`: Algorithm / index used
- `uncertainty`: Quantitative interval or qualitative confidence level
- `status`: `valid` | `uncertain` | `unavailable`
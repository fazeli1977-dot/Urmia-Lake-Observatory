import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats


def mann_kendall_test(values: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    آزمون ناپارامتریک Mann-Kendall با تصحیح گره‌ها (Tied Groups) و محاسبه Z و p-value
    """
    x = np.asarray(values, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 3:
        raise ValueError("Mann-Kendall requires at least 3 valid observations.")

    s = 0
    for k in range(n - 1):
        diff = x[k + 1:] - x[k]
        s += int(np.sum(np.sign(diff)))

    # محاسبه واریانس با تصحیح مقادیر تکراری (Ties)
    unique_x, counts = np.unique(x, return_counts=True)
    tie_counts = counts[counts > 1]
    tie_term = np.sum(tie_counts * (tie_counts - 1) * (2 * tie_counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

    if var_s == 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0

    p_value = float(2 * (1 - stats.norm.cdf(abs(z))))
    tau = float(s / (0.5 * n * (n - 1)))
    significant = bool(p_value < alpha)

    if significant:
        trend = "increasing" if z > 0 else "decreasing"
    else:
        trend = "no_significant_trend"

    return {
        "n": int(n),
        "s_statistic": int(s),
        "var_s": round(float(var_s), 4),
        "z_score": round(float(z), 4),
        "p_value": round(p_value, 6),
        "kendall_tau": round(tau, 4),
        "alpha": alpha,
        "significant": significant,
        "trend": trend,
    }


def sens_slope_per_year(dates: pd.Series, values: np.ndarray) -> Dict[str, float]:
    """
    محاسبه شیب ناپارامتریک Sen بر حسب واحد در سال (با در نظر گرفتن فاصله دقیق روزها)
    """
    t_days = (pd.to_datetime(dates) - pd.to_datetime(dates.iloc[0])).dt.total_seconds() / 86400.0
    t_years = t_days.to_numpy(dtype=float) / 365.25
    y = np.asarray(values, dtype=float)

    n = len(y)
    if n < 2:
        raise ValueError("Sen's slope requires at least 2 observations.")

    slopes: List[float] = []
    for i in range(n - 1):
        dt = t_years[i + 1:] - t_years[i]
        dy = y[i + 1:] - y[i]
        valid = dt > 0
        if np.any(valid):
            slopes.extend((dy[valid] / dt[valid]).tolist())

    if not slopes:
        raise ValueError("No valid positive time intervals found for Sen's slope.")

    slopes_arr = np.array(slopes, dtype=float)
    median_slope = float(np.median(slopes_arr))
    intercept = float(np.median(y - median_slope * t_years))

    return {
        "slope_per_year": round(median_slope, 4),
        "slope_per_decade": round(median_slope * 10.0, 4),
        "intercept": round(intercept, 4),
    }


def analyze_hydrology_trends(json_path: str = "data/processed/lake_hydrology_latest.json") -> Dict[str, Any]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Hydrology file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    ts = payload.get("water_level_timeseries", [])
    if not ts:
        raise ValueError("water_level_timeseries is empty or missing in JSON.")

    df = pd.DataFrame(ts)
    date_col = "date" if "date" in df.columns else df.columns[0]
    level_col = next(
        (c for c in ["level_m", "water_level_m", "elevation_m", "value"] if c in df.columns),
        None,
    )
    if level_col is None:
        raise KeyError(f"Could not detect water level column in timeseries columns: {list(df.columns)}")

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).dropna(subset=[level_col]).reset_index(drop=True)

    results: Dict[str, Any] = {
        "source_file": str(path),
        "detected_columns": {"date": date_col, "level": level_col},
        "total_records": int(len(df)),
        "date_range": {
            "start": df[date_col].iloc[0].strftime("%Y-%m-%d"),
            "end": df[date_col].iloc[-1].strftime("%Y-%m-%d"),
        },
        "periods": {},
    }

    end_date = df[date_col].iloc[-1]
    windows = {
        "full_record": df,
        "last_10_years": df[df[date_col] >= (end_date - pd.DateOffset(years=10))],
        "last_5_years": df[df[date_col] >= (end_date - pd.DateOffset(years=5))],
    }

    for name, sub_df in windows.items():
        if len(sub_df) >= 3:
            mk = mann_kendall_test(sub_df[level_col].to_numpy())
            sen = sens_slope_per_year(sub_df[date_col], sub_df[level_col].to_numpy())
            results["periods"][name] = {
                "start_date": sub_df[date_col].iloc[0].strftime("%Y-%m-%d"),
                "end_date": sub_df[date_col].iloc[-1].strftime("%Y-%m-%d"),
                "mann_kendall": mk,
                "sens_slope_m": sen,
            }

    return results


if __name__ == "__main__":
    summary = analyze_hydrology_trends()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

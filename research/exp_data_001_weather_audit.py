"""
EXP-DATA-001: DEMETER Weather Database Statistical Audit
=========================================================
Audits weather_history.db for:
  - Total observations and forecasts
  - Date range and temporal span
  - Per-field null/missing values (missingness percentage)
  - Duplicate records (by timestamp + lat + lon)
  - Sampling interval statistics (mean, std, median, min, max)
  - Temporal consistency gaps
  - Value range outlier check (temperature, humidity, pressure, etc.)
  - Unique robot IDs and geographic coordinates

Evidence classification: [FACT / MEASURED] upon completion.
Results saved to: research/data/EXP_DATA_001_weather_audit.json
"""

import sqlite3
import json
import time
import statistics
from pathlib import Path
from datetime import datetime

ROOT    = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "weather_history.db"
OUT_DIR = ROOT / "research" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIMESTAMP = time.strftime("%Y-%m-%dT%H%M%S")

print("=" * 70)
print("EXP-DATA-001: Weather History Database Audit")
print("=" * 70)
print(f"Database: {DB_PATH}")
print(f"Run time: {RUN_TIMESTAMP}\n")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

audit = {
    "experiment_id": "EXP-DATA-001",
    "date": time.strftime("%Y-%m-%d"),
    "run_timestamp": RUN_TIMESTAMP,
    "database_path": str(DB_PATH),
    "database_size_mb": round(DB_PATH.stat().st_size / (1024 * 1024), 2),
    "observations": {},
    "forecasts": {},
    "claim_classification": "FACT / MEASURED"
}

# ─── OBSERVATIONS TABLE ───────────────────────────────────────────────────────
print("─── OBSERVATIONS TABLE ───")

# Total count
total_obs = cur.execute("SELECT COUNT(*) FROM weather_observations").fetchone()[0]
print(f"  Total records: {total_obs}")
audit["observations"]["total_records"] = total_obs

# Date range
date_range = cur.execute(
    "SELECT MIN(timestamp), MAX(timestamp) FROM weather_observations"
).fetchone()
print(f"  Date range: {date_range[0]} → {date_range[1]}")
audit["observations"]["earliest_timestamp"] = date_range[0]
audit["observations"]["latest_timestamp"]   = date_range[1]

# Temporal span in days
try:
    t_start = datetime.fromisoformat(date_range[0])
    t_end   = datetime.fromisoformat(date_range[1])
    span_days = (t_end - t_start).total_seconds() / 86400
    audit["observations"]["span_days"] = round(span_days, 2)
    print(f"  Temporal span: {round(span_days, 2)} days")
except Exception as e:
    audit["observations"]["span_days"] = f"PARSE_ERROR: {e}"

# Unique robot IDs
robots = [r[0] for r in cur.execute("SELECT DISTINCT robot_id FROM weather_observations").fetchall()]
print(f"  Robot IDs: {robots}")
audit["observations"]["unique_robot_ids"] = robots

# Unique coordinates
coord_count = cur.execute(
    "SELECT COUNT(DISTINCT lat || ',' || lon) FROM "
    "(SELECT ROUND(latitude, 4) AS lat, ROUND(longitude, 4) AS lon FROM weather_observations)"
).fetchone()[0]
print(f"  Unique locations (lat/lon 4dp): {coord_count}")
audit["observations"]["unique_locations_4dp"] = coord_count

# Schema / columns
cols_info = cur.execute("PRAGMA table_info(weather_observations)").fetchall()
col_names = [c[1] for c in cols_info]
audit["observations"]["columns"] = col_names

# Per-field missingness (NULL count)
nullability = {}
numeric_fields = ["temperature", "humidity", "pressure", "rain_probability",
                  "precipitation", "wind_speed", "uv_index", "cloud_cover", "visibility"]
print("\n  Per-field NULL analysis:")
for field in numeric_fields:
    null_count = cur.execute(f"SELECT COUNT(*) FROM weather_observations WHERE {field} IS NULL").fetchone()[0]
    pct = round(100 * null_count / total_obs, 2) if total_obs > 0 else 0.0
    nullability[field] = {"null_count": null_count, "missing_pct": pct}
    print(f"    {field:<25}: {null_count} nulls ({pct}%)")
audit["observations"]["per_field_nullability"] = nullability

# Duplicate check
dup_count = cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT timestamp, latitude, longitude, COUNT(*) as cnt
        FROM weather_observations
        GROUP BY timestamp, latitude, longitude
        HAVING cnt > 1
    )
""").fetchone()[0]
print(f"\n  Duplicate records (same timestamp+lat+lon): {dup_count}")
audit["observations"]["duplicate_records"] = dup_count

# Sampling interval (sort timestamps, compute differences)
print("\n  Computing sampling intervals...")
timestamps = [r[0] for r in cur.execute(
    "SELECT timestamp FROM weather_observations ORDER BY timestamp ASC"
).fetchall()]

intervals_sec = []
for i in range(1, len(timestamps)):
    try:
        t0 = datetime.fromisoformat(timestamps[i-1])
        t1 = datetime.fromisoformat(timestamps[i])
        delta = (t1 - t0).total_seconds()
        if 0 < delta < 86400:  # only count intervals < 24h as valid
            intervals_sec.append(delta)
    except Exception:
        pass

if intervals_sec:
    interval_stats = {
        "count": len(intervals_sec),
        "mean_sec": round(statistics.mean(intervals_sec), 2),
        "median_sec": round(statistics.median(intervals_sec), 2),
        "stdev_sec": round(statistics.stdev(intervals_sec), 2) if len(intervals_sec) > 1 else 0.0,
        "min_sec": round(min(intervals_sec), 2),
        "max_sec": round(max(intervals_sec), 2),
    }
    print(f"    Mean interval: {interval_stats['mean_sec']}s | Median: {interval_stats['median_sec']}s | StdDev: {interval_stats['stdev_sec']}s")
    audit["observations"]["sampling_interval_stats"] = interval_stats
else:
    audit["observations"]["sampling_interval_stats"] = "INSUFFICIENT_DATA"

# Value range check — detect outliers against physically valid ranges
print("\n  Value range check (plausibility audit):")
range_checks = {
    "temperature":     (-20, 55),
    "humidity":        (0, 100),
    "pressure":        (900, 1100),
    "wind_speed":      (0, 100),
    "uv_index":        (0, 15),
    "cloud_cover":     (0, 100),
}
outlier_summary = {}
for field, (lo, hi) in range_checks.items():
    out_low  = cur.execute(f"SELECT COUNT(*) FROM weather_observations WHERE {field} < {lo}").fetchone()[0]
    out_high = cur.execute(f"SELECT COUNT(*) FROM weather_observations WHERE {field} > {hi}").fetchone()[0]
    total_out = out_low + out_high
    outlier_summary[field] = {"below_min": out_low, "above_max": out_high, "total_outliers": total_out, "valid_range": f"[{lo}, {hi}]"}
    print(f"    {field:<20}: out_of_range={total_out}  (below {lo}: {out_low}, above {hi}: {out_high})")
audit["observations"]["value_outliers"] = outlier_summary

# ─── FORECASTS TABLE ─────────────────────────────────────────────────────────
print("\n─── FORECASTS TABLE ───")
total_fcast = cur.execute("SELECT COUNT(*) FROM weather_forecasts").fetchone()[0]
print(f"  Total records: {total_fcast}")
audit["forecasts"]["total_records"] = total_fcast

fcast_range = cur.execute(
    "SELECT MIN(created_at), MAX(created_at), MIN(forecast_date), MAX(forecast_date) FROM weather_forecasts"
).fetchone()
print(f"  Created range: {fcast_range[0]} → {fcast_range[1]}")
print(f"  Forecast date range: {fcast_range[2]} → {fcast_range[3]}")
audit["forecasts"]["created_range"]       = {"min": fcast_range[0], "max": fcast_range[1]}
audit["forecasts"]["forecast_date_range"] = {"min": fcast_range[2], "max": fcast_range[3]}

# Per-field null check for forecasts
fcast_nulls = {}
fcast_numeric = ["temperature_max", "temperature_min", "rain_probability",
                 "precipitation", "humidity", "wind_speed", "uv_index"]
for field in fcast_numeric:
    null_count = cur.execute(f"SELECT COUNT(*) FROM weather_forecasts WHERE {field} IS NULL").fetchone()[0]
    pct = round(100 * null_count / total_fcast, 2) if total_fcast > 0 else 0.0
    fcast_nulls[field] = {"null_count": null_count, "missing_pct": pct}
print(f"  Per-field nullability: {json.dumps(fcast_nulls, indent=4)}")
audit["forecasts"]["per_field_nullability"] = fcast_nulls

conn.close()

# ─── Save audit report ────────────────────────────────────────────────────────
out_path = OUT_DIR / f"EXP_DATA_001_weather_audit_{RUN_TIMESTAMP}.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)
print(f"\n[SAVED] Audit report: {out_path}")

print("\n" + "=" * 70)
print("EXP-DATA-001 COMPLETE")
print("Claim classification: [FACT / MEASURED]")
print(f"Evidence file: {out_path}")

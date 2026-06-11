#!/usr/bin/env python3
"""
Compute comfort KPIs from converted ego vehicle-state CSV files.

This version is tailored to the reduced fields you actually export/use:

  time, x, y, vx, yaw_angle, yaw_rate, steering_angle, steering_rate, ax

Expected CSV from batch_convert_bags.py:
  test_id, scenario, changed_parameter, changed_value, bag_timestamp_ns,
  time, x, y, vx, yaw_angle, yaw_rate, steering_angle, steering_rate, ax

Computed KPI time series:
  time
  velocity
  longitudinal_acceleration
  lateral_acceleration
  longitudinal_jerk
  lateral_jerk
  yaw_rate
  yaw_acceleration
  steering_angle
  steering_angle_rate

Outputs:
  <csv-folder>/kpi_evaluation/kpi_timeseries.csv
  <csv-folder>/kpi_evaluation/kpi_summary.csv
  <csv-folder>/kpi_evaluation/signal_diagnostics.csv

Usage:
  python compute_vehicle_kpis.py --csv "$LATEST/all_vehicle_state.csv"

Optional:
  python compute_vehicle_kpis.py \
    --csv "$LATEST/all_vehicle_state.csv" \
    --smooth-window 5
"""

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "time",
    "x",
    "y",
    "vx",
    "yaw_angle",
    "yaw_rate",
    "steering_angle",
    "steering_rate",
    "ax",
]

META_COLUMNS = [
    "test_id",
    "scenario",
    "changed_parameter",
    "changed_value",
]

NUMERIC_COLUMNS = [
    "bag_timestamp_ns",
    "time",
    "x",
    "y",
    "vx",
    "yaw_angle",
    "yaw_rate",
    "steering_angle",
    "steering_rate",
    "ax",
    "changed_value",
]


def make_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def ensure_metadata_columns(df: pd.DataFrame, csv_path: Path) -> pd.DataFrame:
    """
    batch_convert_bags.py creates metadata columns.
    If a user evaluates a single raw CSV without them, create safe defaults.
    """
    df = df.copy()

    if "test_id" not in df.columns:
        df["test_id"] = csv_path.stem

    if "scenario" not in df.columns:
        df["scenario"] = "unknown"

    if "changed_parameter" not in df.columns:
        df["changed_parameter"] = "unknown"

    if "changed_value" not in df.columns:
        df["changed_value"] = np.nan

    return df


def signal_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for col in df.columns:
        s = df[col]
        row = {
            "column": col,
            "dtype": str(s.dtype),
            "rows": int(len(s)),
            "non_null": int(s.notna().sum()),
            "unique_values": int(s.nunique(dropna=True)),
            "is_constant": bool(s.nunique(dropna=True) <= 1),
        }

        if pd.api.types.is_numeric_dtype(s):
            row.update(
                {
                    "min": float(s.min()) if s.notna().any() else np.nan,
                    "max": float(s.max()) if s.notna().any() else np.nan,
                    "mean": float(s.mean()) if s.notna().any() else np.nan,
                    "std": float(s.std()) if s.notna().any() else np.nan,
                }
            )

        rows.append(row)

    return pd.DataFrame(rows)


def derivative(values: pd.Series, time: pd.Series) -> pd.Series:
    """
    Numerical derivative dy/dt with duplicate-timestamp handling.
    Uses np.gradient on unique timestamps and interpolates missing derivative samples.
    """
    y = values.to_numpy(dtype=float)
    t = time.to_numpy(dtype=float)

    out = np.full(len(y), np.nan, dtype=float)
    valid = np.isfinite(y) & np.isfinite(t)

    if valid.sum() < 2:
        return pd.Series(out, index=values.index)

    valid_idx = np.where(valid)[0]
    y_valid = y[valid]
    t_valid = t[valid]

    _, unique_pos = np.unique(t_valid, return_index=True)
    unique_pos = np.sort(unique_pos)

    if len(unique_pos) < 2:
        return pd.Series(out, index=values.index)

    grad = np.gradient(y_valid[unique_pos], t_valid[unique_pos])
    out[valid_idx[unique_pos]] = grad

    return pd.Series(out, index=values.index).interpolate(limit_direction="both")


def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series
    return series.rolling(window=window, center=True, min_periods=1).mean()


def prepare_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates relative time per test_id.
    Uses message time if available.
    """
    df = df.copy()
    df = df.sort_values(["test_id", "time"])
    df["time_absolute_raw"] = df["time"]
    df["time"] = df["time"] - df.groupby("test_id")["time"].transform("min")
    return df


def compute_kpi_timeseries_for_test(group: pd.DataFrame, smooth_window: int) -> pd.DataFrame:
    g = group.sort_values("time").copy()

    # Velocity:
    # vx is the longitudinal ego-frame speed in your data.
    g["velocity"] = g["vx"].abs()

    # Longitudinal acceleration:
    # ax is plausible and corresponds to d(vx)/dt in your logs.
    g["longitudinal_acceleration"] = g["ax"]

    # Lateral acceleration:
    # vy and ay are not used. In the ego-frame data, lateral comfort acceleration
    # is computed from speed and yaw-rate:
    #
    #   a_lat = v * yaw_rate
    #
    # velocity is non-negative, yaw_rate keeps the sign.
    g["lateral_acceleration"] = g["velocity"] * g["yaw_rate"]

    # Smooth signals before differentiation to reduce numerical jerk spikes.
    longitudinal_acceleration_smooth = rolling_mean(
        g["longitudinal_acceleration"],
        smooth_window,
    )
    lateral_acceleration_smooth = rolling_mean(
        g["lateral_acceleration"],
        smooth_window,
    )
    yaw_rate_smooth = rolling_mean(
        g["yaw_rate"],
        smooth_window,
    )

    # Jerk and yaw acceleration.
    g["longitudinal_jerk"] = derivative(
        longitudinal_acceleration_smooth,
        g["time"],
    )
    g["lateral_jerk"] = derivative(
        lateral_acceleration_smooth,
        g["time"],
    )
    g["yaw_acceleration"] = derivative(
        yaw_rate_smooth,
        g["time"],
    )

    # Steering angle rate:
    # You already record steering_rate, so use it directly.
    g["steering_angle_rate"] = g["steering_rate"]

    return g[
        [
            "test_id",
            "scenario",
            "changed_parameter",
            "changed_value",
            "time",
            "x",
            "y",
            "velocity",
            "longitudinal_acceleration",
            "lateral_acceleration",
            "longitudinal_jerk",
            "lateral_jerk",
            "yaw_rate",
            "yaw_acceleration",
            "yaw_angle",
            "steering_angle",
            "steering_angle_rate",
        ]
    ]


def rms(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) == 0:
        return np.nan
    return float(np.sqrt(np.mean(values**2)))


def abs_percentile(series: pd.Series, percentile: float) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna().abs().to_numpy(dtype=float)
    if len(values) == 0:
        return np.nan
    return float(np.percentile(values, percentile))


def summarize_test(group: pd.DataFrame) -> Dict[str, object]:
    kpis = [
        "velocity",
        "longitudinal_acceleration",
        "lateral_acceleration",
        "longitudinal_jerk",
        "lateral_jerk",
        "yaw_rate",
        "yaw_acceleration",
        "yaw_angle",
        "steering_angle",
        "steering_angle_rate",
    ]

    result: Dict[str, object] = {
        "test_id": group["test_id"].iloc[0],
        "scenario": group["scenario"].iloc[0],
        "changed_parameter": group["changed_parameter"].iloc[0],
        "changed_value": group["changed_value"].iloc[0],
        "duration_s": float(group["time"].max() - group["time"].min()),
        "samples": int(len(group)),
    }

    for kpi in kpis:
        s = pd.to_numeric(group[kpi], errors="coerce")

        result[f"{kpi}_mean"] = float(s.mean())
        result[f"{kpi}_min"] = float(s.min())
        result[f"{kpi}_max"] = float(s.max())
        result[f"{kpi}_abs_max"] = float(s.abs().max())
        result[f"{kpi}_abs_p95"] = abs_percentile(s, 95)
        result[f"{kpi}_rms"] = rms(s)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to all_vehicle_state.csv or a single vehicle_state.csv",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory. Default: <csv-folder>/kpi_evaluation",
    )
    parser.add_argument(
        "--smooth-window",
        type=int,
        default=5,
        help="Centered rolling mean window before numerical derivatives. Use 1 for no smoothing.",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    out_dir = (
        Path(args.out_dir).expanduser().resolve()
        if args.out_dir
        else csv_path.parent / "kpi_evaluation"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df = ensure_metadata_columns(df, csv_path)
    df = make_numeric(df)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise RuntimeError(
            "Missing required columns in CSV: "
            + ", ".join(missing)
            + "\nExpected at least: "
            + ", ".join(REQUIRED_COLUMNS)
        )

    # Save raw signal diagnostics.
    diag_path = out_dir / "signal_diagnostics.csv"
    signal_diagnostics(df).to_csv(diag_path, index=False)

    # Prepare relative time per test.
    df = prepare_time(df)

    # Compute KPI time series per test.
    kpi_frames: List[pd.DataFrame] = []
    for _, group in df.groupby("test_id", sort=False):
        kpi_frames.append(
            compute_kpi_timeseries_for_test(
                group=group,
                smooth_window=args.smooth_window,
            )
        )

    kpi_timeseries = pd.concat(kpi_frames, ignore_index=True)

    # Summary per test.
    summary_rows = [
        summarize_test(group)
        for _, group in kpi_timeseries.groupby("test_id", sort=False)
    ]
    summary = pd.DataFrame(summary_rows)

    summary = summary.sort_values(
        ["scenario", "changed_parameter", "changed_value"],
        na_position="first",
    )

    kpi_timeseries_path = out_dir / "kpi_timeseries.csv"
    kpi_summary_path = out_dir / "kpi_summary.csv"

    kpi_timeseries.to_csv(kpi_timeseries_path, index=False)
    summary.to_csv(kpi_summary_path, index=False)

    print(f"[OK] Signal diagnostics: {diag_path}")
    print(f"[OK] KPI time series:    {kpi_timeseries_path}")
    print(f"[OK] KPI summary:        {kpi_summary_path}")

    preview_columns = [
        "test_id",
        "scenario",
        "changed_parameter",
        "changed_value",
        "velocity_max",
        "longitudinal_acceleration_abs_max",
        "lateral_acceleration_abs_max",
        "longitudinal_jerk_abs_max",
        "lateral_jerk_abs_max",
        "yaw_rate_abs_max",
        "yaw_acceleration_abs_max",
        "steering_angle_abs_max",
        "steering_angle_rate_abs_max",
    ]

    existing_preview_columns = [
        col for col in preview_columns
        if col in summary.columns
    ]

    print()
    print(summary[existing_preview_columns].to_string(index=False))


if __name__ == "__main__":
    main()
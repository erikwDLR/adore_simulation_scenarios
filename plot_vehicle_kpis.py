#!/usr/bin/env python3
"""
Visualize KPI results created by compute_vehicle_kpis.py / compute_vehicle_kpis_reduced.py.

Expected input folder:
  <bags-root>/kpi_evaluation/
    kpi_timeseries.csv
    kpi_summary.csv

Creates:
  <bags-root>/kpi_evaluation/plots/
    01_trajectory_<scenario>.png
    02_timeseries_<scenario>_<changed_parameter>.png
    03_metric_<metric>_<scenario>_<changed_parameter>.png

Usage:
  python plot_vehicle_kpis.py --kpi-dir "$LATEST/kpi_evaluation"

Optional examples:
  python plot_vehicle_kpis.py --kpi-dir "$LATEST/kpi_evaluation" --scenario single_parked
  python plot_vehicle_kpis.py --kpi-dir "$LATEST/kpi_evaluation" --parameter side_clearance
  python plot_vehicle_kpis.py --kpi-dir "$LATEST/kpi_evaluation" --metric lateral_jerk_abs_p95
"""

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_SUMMARY_METRICS = [
    "velocity_max",
    "velocity_mean",
    "longitudinal_acceleration_abs_p95",
    "lateral_acceleration_abs_p95",
    "longitudinal_jerk_abs_p95",
    "lateral_jerk_abs_p95",
    "yaw_rate_abs_p95",
    "yaw_acceleration_abs_p95",
    "steering_angle_rate_abs_p95",
]

DEFAULT_TIMESERIES_METRICS = [
    "velocity",
    "longitudinal_acceleration",
    "lateral_acceleration",
    "longitudinal_jerk",
    "lateral_jerk",
    "yaw_rate",
    "yaw_acceleration",
    "steering_angle",
    "steering_angle_rate",
]


def safe_name(text: object) -> str:
    value = str(text)
    for old, new in [
        (" ", "_"),
        ("/", "_"),
        ("\\", "_"),
        (".", "p"),
        ("-", "m"),
        ("=", "_"),
        (":", "_"),
    ]:
        value = value.replace(old, new)
    return value


def filter_df(
    df: pd.DataFrame,
    scenario: Optional[str],
    parameter: Optional[str],
) -> pd.DataFrame:
    out = df.copy()

    if scenario:
        out = out[out["scenario"] == scenario]

    if parameter:
        out = out[out["changed_parameter"] == parameter]

    return out


def plot_trajectories(ts: pd.DataFrame, out_dir: Path) -> None:
    if "x" not in ts.columns or "y" not in ts.columns:
        return

    for scenario, scenario_df in ts.groupby("scenario", sort=False):
        fig, ax = plt.subplots(figsize=(9, 7))

        for test_id, g in scenario_df.groupby("test_id", sort=False):
            label = str(g["changed_parameter"].iloc[0])
            value = g["changed_value"].iloc[0]

            if pd.notna(value):
                label = f"{label}={value}"

            if label == "baseline":
                label = "baseline"

            ax.plot(g["x"], g["y"], linewidth=1.2, label=label)

        ax.set_title(f"XY-Trajektorien: {scenario}")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.axis("equal")
        ax.grid(True)
        ax.legend(fontsize=8, loc="best")

        fig.tight_layout()
        fig.savefig(out_dir / f"01_trajectory_{safe_name(scenario)}.png", dpi=160)
        plt.close(fig)


def plot_timeseries_by_parameter(
    ts: pd.DataFrame,
    out_dir: Path,
    metrics: Iterable[str],
) -> None:
    existing_metrics = [m for m in metrics if m in ts.columns]

    if not existing_metrics:
        return

    for (scenario, parameter), part in ts.groupby(["scenario", "changed_parameter"], sort=False):
        if part.empty:
            continue

        for metric in existing_metrics:
            fig, ax = plt.subplots(figsize=(10, 5))

            for test_id, g in part.groupby("test_id", sort=False):
                value = g["changed_value"].iloc[0]
                label = "baseline" if parameter == "baseline" else f"{parameter}={value}"
                ax.plot(g["time"], g[metric], linewidth=1.2, label=label)

            ax.set_title(f"{metric} über Zeit | {scenario} | {parameter}")
            ax.set_xlabel("Zeit [s]")
            ax.set_ylabel(metric)
            ax.grid(True)
            ax.legend(fontsize=8, loc="best")

            fig.tight_layout()
            fig.savefig(
                out_dir / f"02_timeseries_{safe_name(scenario)}_{safe_name(parameter)}_{safe_name(metric)}.png",
                dpi=160,
            )
            plt.close(fig)


def plot_summary_metric_vs_parameter(
    summary: pd.DataFrame,
    out_dir: Path,
    metrics: Iterable[str],
) -> None:
    existing_metrics = [m for m in metrics if m in summary.columns]

    if not existing_metrics:
        return

    # Only parameter sweeps with numeric changed_value are useful for metric-vs-value plots.
    summary = summary.copy()
    summary["changed_value_num"] = pd.to_numeric(summary["changed_value"], errors="coerce")

    for (scenario, parameter), part in summary.groupby(["scenario", "changed_parameter"], sort=False):
        if parameter == "baseline":
            continue

        part = part.dropna(subset=["changed_value_num"]).sort_values("changed_value_num")

        if len(part) < 2:
            continue

        for metric in existing_metrics:
            fig, ax = plt.subplots(figsize=(8, 5))

            ax.plot(
                part["changed_value_num"],
                part[metric],
                marker="o",
                linewidth=1.5,
            )

            ax.set_title(f"{metric} vs. {parameter} | {scenario}")
            ax.set_xlabel(parameter)
            ax.set_ylabel(metric)
            ax.grid(True)

            fig.tight_layout()
            fig.savefig(
                out_dir / f"03_metric_{safe_name(metric)}_{safe_name(scenario)}_{safe_name(parameter)}.png",
                dpi=160,
            )
            plt.close(fig)


def plot_parameter_ranking(
    summary: pd.DataFrame,
    out_dir: Path,
    metric: str,
) -> None:
    if metric not in summary.columns:
        return

    ranking = summary.sort_values(metric, ascending=True).copy()

    if len(ranking) > 30:
        ranking = ranking.head(30)

    labels: List[str] = []
    for _, row in ranking.iterrows():
        if row["changed_parameter"] == "baseline":
            labels.append(f"{row['scenario']} | baseline")
        else:
            labels.append(f"{row['scenario']} | {row['changed_parameter']}={row['changed_value']}")

    fig, ax = plt.subplots(figsize=(12, max(6, 0.28 * len(ranking))))

    ax.barh(labels, ranking[metric])
    ax.set_title(f"Ranking nach {metric}")
    ax.set_xlabel(metric)
    ax.grid(True, axis="x")

    fig.tight_layout()
    fig.savefig(out_dir / f"04_ranking_{safe_name(metric)}.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kpi-dir",
        required=True,
        help="Folder containing kpi_timeseries.csv and kpi_summary.csv",
    )
    parser.add_argument("--scenario", default=None, help="Optional scenario filter")
    parser.add_argument("--parameter", default=None, help="Optional changed_parameter filter")
    parser.add_argument(
        "--metric",
        default=None,
        help="Optional single summary metric for parameter plots and ranking, e.g. lateral_jerk_abs_p95",
    )
    parser.add_argument(
        "--no-timeseries",
        action="store_true",
        help="Skip time-series plots.",
    )
    parser.add_argument(
        "--no-trajectories",
        action="store_true",
        help="Skip trajectory plots.",
    )
    args = parser.parse_args()

    kpi_dir = Path(args.kpi_dir).expanduser().resolve()
    ts_path = kpi_dir / "kpi_timeseries.csv"
    summary_path = kpi_dir / "kpi_summary.csv"

    if not ts_path.exists():
        raise FileNotFoundError(ts_path)

    if not summary_path.exists():
        raise FileNotFoundError(summary_path)

    out_dir = kpi_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = pd.read_csv(ts_path)
    summary = pd.read_csv(summary_path)

    ts = filter_df(ts, args.scenario, args.parameter)
    summary = filter_df(summary, args.scenario, args.parameter)

    if ts.empty:
        raise RuntimeError("No time-series rows left after filtering.")

    if summary.empty:
        raise RuntimeError("No summary rows left after filtering.")

    metrics = [args.metric] if args.metric else DEFAULT_SUMMARY_METRICS

    if not args.no_trajectories:
        plot_trajectories(ts, out_dir)

    if not args.no_timeseries:
        plot_timeseries_by_parameter(
            ts,
            out_dir,
            DEFAULT_TIMESERIES_METRICS,
        )

    plot_summary_metric_vs_parameter(summary, out_dir, metrics)

    if args.metric:
        plot_parameter_ranking(summary, out_dir, args.metric)
    else:
        plot_parameter_ranking(summary, out_dir, "lateral_jerk_abs_p95")

    print(f"[OK] Plots written to: {out_dir}")
    print()
    print("Useful files:")
    for path in sorted(out_dir.glob("*.png"))[:20]:
        print(f"  {path}")
    if len(list(out_dir.glob("*.png"))) > 20:
        print("  ...")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Batch-convert ROS2 MCAP bags produced by automation_test.py into CSV files.

Expected automation structure:
bags/comfort_settings_YYYYMMDD_HHMMSS/
  summary.csv
  C001_single_parked_baseline/
    metadata.json
    rosbag/
      metadata.yaml
      *.mcap

Default export:
- Per test case: <test_dir>/vehicle_state.csv
- Combined file: <bags_root>/all_vehicle_state.csv

Usage:
  python batch_convert_bags.py --bags-root ./bags/comfort_settings_20260611_083701

Optional:
  python batch_convert_bags.py --bags-root ./bags/comfort_settings_20260611_083701 \
    --topic /ego_vehicle/vehicle_state_dynamic \
    --output-name vehicle_state.csv
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


DEFAULT_TOPIC = "/ego_vehicle/vehicle_state_dynamic"
DEFAULT_FIELDS = ["time","x","y","vx","yaw_angle","yaw_rate","steering_angle","steering_rate","ax"]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def get_nested_attr(obj: Any, dotted_name: str) -> Any:
    """
    Reads normal and nested message fields, e.g.:
      "x"
      "pose.position.x"
      "header.stamp.sec"
    """
    value = obj
    for part in dotted_name.split("."):
        value = getattr(value, part)
    return value


def scalarize(value: Any) -> Any:
    """
    Make ROS values CSV-compatible.
    """
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # Some ROS primitive arrays arrive as list/tuple/array-like.
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value))

    # Fall back to string representation for nested/custom objects.
    return str(value)


def find_bag_dirs_from_summary(bags_root: Path) -> List[Path]:
    summary = bags_root / "summary.csv"
    bag_dirs: List[Path] = []

    if not summary.exists():
        return bag_dirs

    with open(summary, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bag_output = row.get("bag_output")
            status = row.get("status")
            if status != "finished" or not bag_output:
                continue

            path = Path(bag_output)
            if path.exists():
                bag_dirs.append(path)

    return bag_dirs


def find_bag_dirs_recursively(bags_root: Path) -> List[Path]:
    """
    Finds ROS2 bag directories by looking for metadata.yaml.
    """
    return sorted({p.parent for p in bags_root.rglob("metadata.yaml")})


def discover_bag_dirs(bags_root: Path) -> List[Path]:
    bag_dirs = find_bag_dirs_from_summary(bags_root)

    if not bag_dirs:
        bag_dirs = find_bag_dirs_recursively(bags_root)

    # Keep only MCAP bags.
    bag_dirs = [
        p for p in bag_dirs
        if (p / "metadata.yaml").exists() and any(p.glob("*.mcap"))
    ]

    return sorted(set(bag_dirs))


def get_topic_type_map(reader: SequentialReader) -> Dict[str, str]:
    return {topic.name: topic.type for topic in reader.get_all_topics_and_types()}


def convert_one_bag(
    bag_dir: Path,
    topic: str,
    fields: List[str],
    output_name: str,
) -> Tuple[Optional[Path], int, Optional[str]]:
    """
    Returns:
      (csv_path, rows_written, error)
    """
    test_dir = bag_dir.parent
    metadata = read_json(test_dir / "metadata.json")

    reader = SequentialReader()
    reader.open(
        StorageOptions(uri=str(bag_dir), storage_id="mcap"),
        ConverterOptions("", ""),
    )

    type_map = get_topic_type_map(reader)

    if topic not in type_map:
        available = ", ".join(sorted(type_map.keys()))
        return None, 0, f"topic not found: {topic}. Available topics: {available}"

    msg_type = get_message(type_map[topic])
    csv_path = test_dir / output_name

    meta_columns = [
        "test_id",
        "scenario",
        "changed_parameter",
        "changed_value",
    ]

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                *meta_columns,
                "bag_timestamp_ns",
                *fields,
            ],
        )
        writer.writeheader()

        count = 0

        while reader.has_next():
            current_topic, data, bag_timestamp_ns = reader.read_next()

            if current_topic != topic:
                continue

            msg = deserialize_message(data, msg_type)

            row: Dict[str, Any] = {
                "test_id": metadata.get("test_id", test_dir.name),
                "scenario": metadata.get("scenario"),
                "changed_parameter": metadata.get("changed_parameter"),
                "changed_value": metadata.get("changed_value"),
                "bag_timestamp_ns": bag_timestamp_ns,
            }

            for field in fields:
                try:
                    row[field] = scalarize(get_nested_attr(msg, field))
                except AttributeError:
                    row[field] = ""

            writer.writerow(row)
            count += 1

    return csv_path, count, None


def combine_csvs(csv_files: Iterable[Path], combined_path: Path) -> int:
    csv_files = list(csv_files)
    if not csv_files:
        return 0

    rows_written = 0

    with open(csv_files[0], "r", newline="") as first:
        reader = csv.DictReader(first)
        fieldnames = reader.fieldnames or []

    with open(combined_path, "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    writer.writerow(row)
                    rows_written += 1

    return rows_written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bags-root",
        required=True,
        help="Root folder created by automation_test.py, e.g. ./bags/comfort_settings_20260611_083701",
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help=f"Topic to export. Default: {DEFAULT_TOPIC}",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        default=DEFAULT_FIELDS,
        help=f"Message fields to export. Default: {' '.join(DEFAULT_FIELDS)}",
    )
    parser.add_argument(
        "--output-name",
        default="vehicle_state.csv",
        help="Per-test CSV filename. Default: vehicle_state.csv",
    )
    parser.add_argument(
        "--combined-name",
        default="all_vehicle_state.csv",
        help="Combined CSV filename in bags root. Default: all_vehicle_state.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bags_root = Path(args.bags_root).expanduser().resolve()

    if not bags_root.exists():
        raise FileNotFoundError(f"bags root does not exist: {bags_root}")

    bag_dirs = discover_bag_dirs(bags_root)

    if not bag_dirs:
        raise RuntimeError(f"No MCAP bag directories found below: {bags_root}")

    print(f"[INFO] Found {len(bag_dirs)} bag(s)")
    print(f"[INFO] Topic: {args.topic}")
    print(f"[INFO] Fields: {args.fields}")

    converted_files: List[Path] = []

    for bag_dir in bag_dirs:
        print(f"[CONVERT] {bag_dir}")
        try:
            csv_path, row_count, error = convert_one_bag(
                bag_dir=bag_dir,
                topic=args.topic,
                fields=args.fields,
                output_name=args.output_name,
            )

            if error:
                print(f"[SKIP] {bag_dir}: {error}")
                continue

            if csv_path is not None:
                converted_files.append(csv_path)
                print(f"[OK] {csv_path} ({row_count} rows)")

        except Exception as exc:
            print(f"[ERROR] {bag_dir}: {exc}")

    combined_path = bags_root / args.combined_name
    total_rows = combine_csvs(converted_files, combined_path)

    print(f"[SUMMARY] Converted bags: {len(converted_files)} / {len(bag_dirs)}")
    print(f"[SUMMARY] Combined CSV: {combined_path} ({total_rows} rows)")


if __name__ == "__main__":
    main()

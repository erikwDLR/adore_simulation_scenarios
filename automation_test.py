import csv
import json
import os
import signal
import subprocess
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from ruamel.yaml import YAML


# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------

script_dir = Path(__file__).resolve().parent

yaml_file = (
    script_dir
    / "../../ros2_workspace/src/adore_ros2_nodes/decision_maker/config/obstacle_avoidance.yaml"
).resolve()


launch_files = {
    "single_parked": (script_dir / "schwarzerberg_OA_single_scenario.py").resolve(),
    "two_parked": (script_dir / "schwarzerberg_OA_two_scenario.py").resolve(),
}

run_duration_s = 60
startup_delay_s = 3

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
bags_root = script_dir / "bags" / f"comfort_settings_{timestamp}"
bags_root.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------
# YAML handling
# ------------------------------------------------------------------------------

yaml = YAML()
yaml.preserve_quotes = True


def load_config(path: Path):
    with open(path, "r") as f:
        return yaml.load(f)


def write_config(path: Path, config):
    with open(path, "w") as f:
        yaml.dump(config, f)


def set_obstacle_avoidance_params(config, params: dict):
    ros_params = config["/**"]["ros__parameters"]

    for short_name, value in params.items():
        full_name = f"obstacle_avoidance.{short_name}"

        if full_name not in ros_params:
            raise KeyError(f"Parameter not found in YAML: {full_name}")

        ros_params[full_name] = value


# ------------------------------------------------------------------------------
# Baseline comfort setting
# ------------------------------------------------------------------------------

baseline_params = {
    # Single obstacle / general comfort
    "side_clearance": 0.8,
    "front_clearance": 7.0,
    "rear_clearance": 7.0,
    "stop_before_obstacle": 8.0,
    "max_speed_during_avoidance": 2.7,
    "max_object_ahead": 40.0,
    "lateral_candidate_extra_steps": 1,
    "lateral_candidate_extra_step": 0.30,

    # Multi obstacle comfort
    "cluster_hold_gap_s": 10.0,
    "shift_hull_gap_s": 20.0,
    "min_alpha_between_hull_obstacles": 0.5,
}


single_parked_sweep = {
    "side_clearance": [0.5, 0.8, 1.0],
    "front_clearance": [5.0, 7.0, 10.0],
    "rear_clearance": [5.0, 7.0, 10.0],
    "stop_before_obstacle": [6.0, 8.0, 11.0],
    "max_speed_during_avoidance": [2.0, 2.7, 3.5, 4.2],
    "max_object_ahead": [30.0, 40.0, 50.0],
    "lateral_candidate_extra_steps": [0, 1, 2],
    "lateral_candidate_extra_step": [0.20, 0.30, 0.40],
}


two_parked_sweep = {
    "cluster_hold_gap_s": [5.0, 10.0, 15.0],
    "shift_hull_gap_s": [10.0, 20.0, 30.0],
    "min_alpha_between_hull_obstacles": [0.0, 0.5, 0.8, 1.0],
}


# ------------------------------------------------------------------------------
# Test case generation
# ------------------------------------------------------------------------------

def make_test_cases(scenario_name: str, sweep: dict):
    test_cases = []

    # Baseline
    test_cases.append({
        "scenario": scenario_name,
        "changed_parameter": "baseline",
        "changed_value": None,
        "params": deepcopy(baseline_params),
    })

    # One-factor-at-a-time variation
    for param_name, values in sweep.items():
        baseline_value = baseline_params[param_name]

        for value in values:
            if value == baseline_value:
                continue

            params = deepcopy(baseline_params)
            params[param_name] = value

            test_cases.append({
                "scenario": scenario_name,
                "changed_parameter": param_name,
                "changed_value": value,
                "params": params,
            })

    return test_cases


test_cases = []
test_cases += make_test_cases("single_parked", single_parked_sweep)
test_cases += make_test_cases("two_parked", two_parked_sweep)


# ------------------------------------------------------------------------------
# Process handling
# ------------------------------------------------------------------------------

def safe_name(value) -> str:
    text = str(value)
    text = text.replace(".", "p")
    text = text.replace("-", "m")
    text = text.replace("/", "_")
    text = text.replace(" ", "_")
    return text


def stop_process_group(proc: subprocess.Popen, name: str, timeout_s: float = 10.0):
    if proc is None:
        return

    if proc.poll() is not None:
        return

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f"[WARN] {name} did not stop after SIGINT. Sending SIGTERM.")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            print(f"[WARN] {name} did not stop after SIGTERM. Sending SIGKILL.")
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()


def run_test(test_index: int, test_case: dict, original_config):
    scenario = test_case["scenario"]
    changed_parameter = test_case["changed_parameter"]
    changed_value = test_case["changed_value"]
    params = test_case["params"]

    launch_file = launch_files[scenario]

    if not launch_file.exists():
        print(f"[SKIP] Launch file for scenario '{scenario}' does not exist: {launch_file}")
        return {
            "status": "skipped",
            "reason": "missing_launch_file",
            "launch_file": str(launch_file),
        }

    test_id = f"C{test_index:03d}_{scenario}_{changed_parameter}"
    if changed_value is not None:
        test_id += f"_{safe_name(changed_value)}"

    test_dir = bags_root / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    # Always start from original YAML + comfort baseline + one changed parameter
    config = deepcopy(original_config)
    set_obstacle_avoidance_params(config, params)
    write_config(yaml_file, config)

    # Save the exact YAML used for this run
    used_yaml_file = test_dir / "obstacle_avoidance_used.yaml"
    write_config(used_yaml_file, config)

    metadata = {
        "test_id": test_id,
        "scenario": scenario,
        "changed_parameter": changed_parameter,
        "changed_value": changed_value,
        "params": params,
        "launch_file": str(launch_file),
        "yaml_file": str(yaml_file),
        "used_yaml_file": str(used_yaml_file),
        "run_duration_s": run_duration_s,
    }

    with open(test_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    bag_output = test_dir / "rosbag"

    print()
    print("------------------------------------------------------------")
    print(f"[RUN] {test_id}")
    print(f"[SCENARIO] {scenario}")
    print(f"[PARAM] {changed_parameter} = {changed_value}")
    print(f"[BAG] {bag_output}")
    print("------------------------------------------------------------")

    bag_proc = None
    launch_proc = None

    try:
        # Start rosbag first, so startup is also captured.
        bag_proc = subprocess.Popen(
            [
                "ros2",
                "bag",
                "record",
                "-a",
                "-o",
                str(bag_output),
            ],
            preexec_fn=os.setsid,
        )

        time.sleep(startup_delay_s)

        launch_proc = subprocess.Popen(
            [
                "ros2",
                "launch",
                str(launch_file),
            ],
            preexec_fn=os.setsid,
        )

        time.sleep(run_duration_s)

        stop_process_group(launch_proc, "launch")
        time.sleep(2)
        stop_process_group(bag_proc, "rosbag")

        print(f"[DONE] {test_id}")

        return {
            "status": "finished",
            "test_id": test_id,
            "bag_output": str(bag_output),
        }

    except KeyboardInterrupt:
        print("[INTERRUPTED] Stopping running processes...")
        stop_process_group(launch_proc, "launch")
        stop_process_group(bag_proc, "rosbag")
        raise

    except Exception as e:
        print(f"[ERROR] {test_id}: {e}")
        stop_process_group(launch_proc, "launch")
        stop_process_group(bag_proc, "rosbag")

        return {
            "status": "error",
            "test_id": test_id,
            "error": str(e),
        }


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main():
    print(f"YAML file: {yaml_file}")
    print(f"Output root: {bags_root}")
    print(f"Planned test cases: {len(test_cases)}")

    original_text = yaml_file.read_text()
    original_config = load_config(yaml_file)

    results = []

    try:
        for i, test_case in enumerate(test_cases, start=1):
            result = run_test(i, test_case, original_config)
            results.append({
                "index": i,
                "scenario": test_case["scenario"],
                "changed_parameter": test_case["changed_parameter"],
                "changed_value": test_case["changed_value"],
                **result,
            })

    finally:
        # Restore original YAML exactly
        yaml_file.write_text(original_text)
        print("[RESTORE] Original obstacle_avoidance.yaml restored.")

    # Write summary CSV
    summary_file = bags_root / "summary.csv"

    with open(summary_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "scenario",
                "changed_parameter",
                "changed_value",
                "status",
                "test_id",
                "bag_output",
                "reason",
                "launch_file",
                "error",
            ],
        )
        writer.writeheader()

        for row in results:
            writer.writerow({
                "index": row.get("index"),
                "scenario": row.get("scenario"),
                "changed_parameter": row.get("changed_parameter"),
                "changed_value": row.get("changed_value"),
                "status": row.get("status"),
                "test_id": row.get("test_id"),
                "bag_output": row.get("bag_output"),
                "reason": row.get("reason"),
                "launch_file": row.get("launch_file"),
                "error": row.get("error"),
            })

    print(f"[SUMMARY] {summary_file}")


if __name__ == "__main__":
    main()
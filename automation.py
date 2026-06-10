import yaml
import subprocess
import signal
import time
from pathlib import Path
from ruamel.yaml import YAML

script_dir = Path(__file__).resolve().parent

yaml_file = Path(
    script_dir
    / "../../ros2_workspace/src/adore_ros2_nodes/decision_maker/config/obstacle_avoidance.yaml"
)

launch_file = (script_dir / "schwarzerberg_OA_scenario.py").resolve()

yaml = YAML()
yaml.preserve_quotes = True

weights = [10.0]

for weight in weights:

    with open(yaml_file, "r") as f:
        config = yaml.load(f)

    config["/**"]["ros__parameters"]["obstacle_avoidance.front_clearance"] = weight

    with open(yaml_file, "w") as f:
        yaml.dump(config, f)

    launch_proc = subprocess.Popen(
        [
            "ros2",
            "launch",
            str(launch_file),
        ]
    )

    # time.sleep(1)

    bag_proc = subprocess.Popen(
        [
            "ros2",
            "bag",
            "record",
            "-a",
            "-o",
            f"bags/weight_{weight}"
        ]
    )

    time.sleep(60)

    bag_proc.send_signal(signal.SIGINT)
    bag_proc.wait()

    launch_proc.send_signal(signal.SIGINT)
    launch_proc.wait()

    print(f"Finished {weight}")
from launch import LaunchDescription
import os
from scenario_helpers.simulated_vehicle import create_simulated_vehicle_nodes
from scenario_helpers.visualizer import create_visualization_nodes

def generate_launch_description():
    # Get the directory of this launch file
    launch_file_dir = os.path.dirname(os.path.realpath(__file__))
    map_image_folder = os.path.abspath(os.path.join(launch_file_dir, "../assets/maps/"))
    map_folder = os.path.abspath(os.path.join(launch_file_dir, "../assets/tracks/"))
    vehicle_param = os.path.abspath(os.path.join(launch_file_dir, "../assets/vehicle_params/"))
    map_file = map_folder + "/de_bs_borders_wfs.r2sr"
    vehicle_model_file = vehicle_param + "/NGC.json"

    return LaunchDescription([
        *create_visualization_nodes(
            whitelist=["ego_vehicle"],
            asset_folder=map_image_folder,
            use_center_ego=True
        ),

        *create_simulated_vehicle_nodes(
            namespace="ego_vehicle",
            start_pose=(606450.573, 5797277.124, 1.5),
            goal_position=(606471.04, 5797161.11),
            map_file=map_file,
            model_file=vehicle_model_file,
            controllable=True,
            v2x_id=0,
            vehicle_id=0,
            controller=1,
            debug=False
        )
    ])

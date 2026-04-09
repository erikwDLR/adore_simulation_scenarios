# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

from launch import LaunchDescription
from launch_ros.actions import Node #
# from ament_index_python.packages import get_package_share_directory

import os
import sys
sys.path.append(os.path.dirname(__file__)) # this line is very importatnt to find the helper functions

from position import Position
from simulated_vehicle import create_simulated_vehicle
from visualizer import create_visualizer

start_position = Position(lat_long=(52.315893, 10.561526), psi=0.0)
goal_position = Position(lat_long=(52.314396, 10.562628), psi=0.0)

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if base_dir not in sys.path:
#     sys.path.insert(0, base_dir)




def generate_launch_description():
    
    
    # from scenario_helpers.simulated_vehicle import create_simulated_vehicle_nodes
    # from scenario_helpers.visualizer import create_visualization_nodes
    # # Get the directory of this launch file
    # launch_file_dir = os.path.dirname(os.path.realpath(__file__))
    # map_image_folder = os.path.abspath(
    #     os.path.join(launch_file_dir, "../assets/maps/"))
    # map_folder = os.path.abspath(os.path.join(
    #     launch_file_dir, "../assets/tracks/"))
    # vehicle_param = os.path.abspath(os.path.join(
    #     launch_file_dir, "../assets/vehicle_params/"))
    # map_file = map_folder + "/de_bs_borders_wfs.r2sr"
    # vehicle_model_file = vehicle_param + "/NGC.json"
    # simulated_vehicle_model_file = vehicle_param + "/FC2.json"
    
    # path_shift_params_file = os.path.abspath(
    # os.path.join(launch_file_dir, "../scenario_helpers/path_shift_params.yaml")
        #)
    

    return LaunchDescription([
        
        *create_simulated_vehicle(
            namespace="ego_vehicle",
            start_pose_utm=start_position.get_utm_coordinates(),
            goal_position_utm=goal_position.get_utm_coordinates(),
            vehicle_id=111,
            v2x_id=0,
        ),
        *create_visualizer(
            whitelist=["ego_vehicle"],
            visualization_offset=start_position.get_utm_coordinates(),
        ),
        
        # *create_simulated_vehicle(
        #     namespace="slow_car",
        #     #start_pose_utm = Position(lat_long=(52.315838, 10.562684), psi=3.03).get_utm_coordinates(),
        #     start_pose_utm = Position(lat_long=(52.315829, 10.562819), psi=3.03).get_utm_coordinates(),
        #     goal_position_utm  = Position(lat_long=(52.314444, 10.561929), psi=0.0).get_utm_coordinates(),
        #     #goal_position_utm  = Position(lat_long=(52.315829, 10.562819), psi=0.0).get_utm_coordinates(),
        #     v2x_id=1,
        #     vehicle_id=99,
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="ego_vehicle",
        #     start_pose_utm=Position(lat_long=(52.315893, 10.561526), psi=0.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.314444, 10.561929), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=111,
        #     v2x_id=0,
        # ),

        # *create_simulated_vehicle(
        #     namespace="simL1",
        #     start_pose_utm=Position(lat_long=(52.315875, 10.562259), psi=-0.15).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.315875, 10.562259), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=2,
        #     v2x_id=2,
        # ),

        # *create_simulated_vehicle(
        #     namespace="simL2",
        #     start_pose_utm=Position(lat_long=(52.315846, 10.562361), psi=-0.15).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.315846, 10.562361), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=3,
        #     v2x_id=3,
        # ),

        # *create_simulated_vehicle(
        #     namespace="simR1",
        #     start_pose_utm=Position(lat_long=(52.315826, 10.562258), psi=-0.15).get_utm_coordinates(),
        #     #start_pose_utm=Position(lat_long=(52.315826, 10.562258), psi=0.25).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.315826, 10.562258), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=4,
        #     v2x_id=4,
        # ),

        # *create_simulated_vehicle(
        #     namespace="simR2",
        #     start_pose_utm=Position(lat_long=(52.315815, 10.562389), psi=-0.15).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.315815, 10.562389), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=5,
        #     v2x_id=5,
        # ),

        *create_simulated_vehicle(
            namespace="simR3",
            start_pose_utm=Position(lat_long=(52.315803, 10.562609), psi=1.5).get_utm_coordinates(),
            goal_position_utm=Position(lat_long=(52.315803, 10.562609), psi=0.0).get_utm_coordinates(),
            vehicle_id=6,
            v2x_id=6,
        ),

        # *create_simulated_vehicle(
        #     namespace="slow_car2",
        #     start_pose_utm=Position(lat_long=(52.315818, 10.562844), psi=3.03).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.314444, 10.561929), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=7,
        #     v2x_id=7,
        # )
    ])
    
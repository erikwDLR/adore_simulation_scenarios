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
from launch_ros.actions import Node

import sys
import os
sys.path.append(os.path.dirname(__file__)) # this line is very importatnt to find the helper functions

from position import Position
from simulated_vehicle import create_simulated_vehicle
from visualizer import create_visualizer

start_position = Position(lat_long=(52.402773, 10.231041), psi=-3.0)
goal_position = Position(lat_long=(52.401652, 10.224147), psi=0.0)

def generate_launch_description():
    return LaunchDescription([
        *create_simulated_vehicle(
            namespace="ego_vehicle",
            start_pose_utm=start_position.get_utm_coordinates(),
            goal_position_utm=goal_position.get_utm_coordinates(),
            vehicle_id=111,
            v2x_id=0,
            map_file="r2s_flightfield_edemissen_26022026_25832.r2sr",
        ),
        *create_visualizer(
            whitelist=["ego_vehicle"],
            visualization_offset=start_position.get_utm_coordinates(),
        ),
        
        *create_simulated_vehicle(
            namespace="oncoming_vehicle",
            start_pose_utm=Position(lat_long=(52.402311, 10.228955), psi=0.0).get_utm_coordinates(),
            goal_position_utm=Position(lat_long=(52.402901, 10.231940), psi=0.0).get_utm_coordinates(),
            vehicle_id=99,
            v2x_id=1,
        ),
        
        *create_simulated_vehicle(
            namespace="lane_blocking_vehicle",
            start_pose_utm=Position(lat_long=(52.402632, 10.230170), psi=2.7).get_utm_coordinates(),
            goal_position_utm=Position(lat_long=(52.402632, 10.230170), psi=2.7).get_utm_coordinates(),
            vehicle_id=2,
            v2x_id=2,
        ),
        
        # *create_simulated_vehicle(
        #     namespace="neighbor_lane_vehicle",  #can be turned so that it is partly in the lane of the ego vehicle
        #     start_pose_utm=Position(lat_long=(52.402521, 10.229703), psi=3.75).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402521, 10.229703), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=3,
        #     v2x_id=3,
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="parked_vehicle", # can be turned so that it is completly blocking or partyly blocking the ego lane
        #     start_pose_utm=Position(lat_long=(52.402427, 10.229150), psi=3.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402427, 10.229150), psi=3.0).get_utm_coordinates(),
        #     vehicle_id=4,
        #     v2x_id=4,
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="street_blocking_vehicle", # can be turned so that it is completly blocking or partyly blocking the street
        #     start_pose_utm=Position(lat_long=(52.402446, 10.229254), psi=3.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402446, 10.229254), psi=3.0).get_utm_coordinates(),
        #     vehicle_id=4,
        #     v2x_id=4,
        # ),
    ])











# from launch import LaunchDescription
# import os
# import sys
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if base_dir not in sys.path:
#     sys.path.insert(0, base_dir)


# def generate_launch_description():
#     from scenario_helpers.simulated_vehicle import create_simulated_vehicle_nodes
#     from scenario_helpers.visualizer import create_visualization_nodes
#     # Get the directory of this launch file
#     launch_file_dir = os.path.dirname(os.path.realpath(__file__))
#     map_image_folder = os.path.abspath(
#         os.path.join(launch_file_dir, "../assets/maps/"))
#     map_folder = os.path.abspath(os.path.join(
#         launch_file_dir, "../assets/tracks/"))
#     vehicle_param = os.path.abspath(os.path.join(
#         launch_file_dir, "../assets/vehicle_params/"))
#     map_file = map_folder + "/r2s_flightfield_edemissen_26022026_25832.r2sr"
#     vehicle_model_file = vehicle_param + "/NGC.json"

#     return LaunchDescription([
#         *create_visualization_nodes(
#             whitelist=["ego_vehicle", "slow_car", "simL1", "simL2", "simR1", "simR2"],
#             asset_folder=map_image_folder,
#             visualization_offset=(606440.120, 5797321.700),
#         ),

#         *create_simulated_vehicle_nodes(
#             namespace="ego_vehicle",
#             start_pose=(583266.7740, 5806405.922, 2.0),
#             goal_position=(583642.316, 5806463.028),
#             map_file=map_file,
#             model_file=vehicle_model_file,
#             controllable=True,
#             v2x_id=0,
#             vehicle_id=111,
#             controller=1,
#             debug=False
#         ),
#         # *create_simulated_vehicle_nodes(
#         #     namespace="slow_car",
#         #     start_pose=(606505.298, 5797317.409, 3.03),
#         #     goal_position=(606471.04, 5797161.11),
#         #     map_file=map_file,
#         #     model_file=vehicle_model_file,
#         #     controllable=True,
#         #     v2x_id=1,
#         #     vehicle_id=99,
#         #     controller=1,
#         #     debug=False
#         # ),
#         # *create_simulated_vehicle_nodes(
#         #     namespace="simL1",
#         #     start_pose=(606490.120, 5797320.700, -0.15),
#         #     goal_position=(606471.04, 5797161.11),
#         #     map_file=map_file,
#         #     model_file=vehicle_model_file,
#         #     controllable=False,
#         #     v2x_id=2,
#         #     vehicle_id=2,
#         #     controller=0,
#         #     debug=False
#         # ),
#         # *create_simulated_vehicle_nodes(
#         #     namespace="simL2",
#         #     start_pose=(606497.120, 5797319.700, -0.15),
#         #     goal_position=(606471.04, 5797161.11),
#         #     map_file=map_file,
#         #     model_file=vehicle_model_file,
#         #     controllable=False,
#         #     v2x_id=4,
#         #     vehicle_id=4,
#         #     controller=0,
#         #     debug=False
#         # ),
#         # *create_simulated_vehicle_nodes(
#         #     namespace="simR1",
#         #     start_pose=(606490.120, 5797315.300, -0.15),
#         #     goal_position=(606471.04, 5797161.11),
#         #     map_file=map_file,
#         #     model_file=vehicle_model_file,
#         #     controllable=False,
#         #     v2x_id=3,
#         #     vehicle_id=3,
#         #     controller=0,
#         #     debug=False
#         # ),
#         # *create_simulated_vehicle_nodes(
#         #     namespace="simR2",
#         #     start_pose=(606497.120, 5797314.300, -0.15),
#         #     goal_position=(606471.04, 5797161.11),
#         #     map_file=map_file,
#         #     model_file=vehicle_model_file,
#         #     controllable=False,
#         #     v2x_id=5,
#         #     vehicle_id=5,
#         #     controller=0,
#         #     debug=False
#         # )
#     ])

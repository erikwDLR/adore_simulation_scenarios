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
#start_position = Position(lat_long=(52.402311, 10.228955), psi=0.0)
#goal_position = Position(lat_long=(52.402901, 10.231940), psi=0.0)

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
        
        # *create_simulated_vehicle(
        #     namespace="oncoming_vehicle",
        #     start_pose_utm=Position(lat_long=(52.402311, 10.228955), psi=0.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402901, 10.231940), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=99,
        #     v2x_id=1,
        #     vehicle_parameters_file = "NGC.json",
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="lane_blocking_vehicle",
        #     start_pose_utm=Position(lat_long=(52.402632, 10.230170), psi=2.7).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402632, 10.230170), psi=2.7).get_utm_coordinates(),
        #     vehicle_id=2,
        #     v2x_id=2,
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="in_lane_right_obstacle",
        #     start_pose_utm=Position(lat_long=(52.402639, 10.230170), psi=0.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402639, 10.230170), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=6,
        #     v2x_id=6,
        #     vehicle_parameters_file = "obstacle.json",
        # ),
        
        *create_simulated_vehicle(
            namespace="neighbor_lane_obstacle",
            start_pose_utm=Position(lat_long=(52.402568, 10.230100), psi=0.0).get_utm_coordinates(),
            goal_position_utm=Position(lat_long=(52.402568, 10.230100), psi=0.0).get_utm_coordinates(),
            vehicle_id=8,
            v2x_id=8,
            vehicle_parameters_file = "obstacle.json",
        ),
        
        # *create_simulated_vehicle(
        #     namespace="neighbor_lane_obstacle",
        #     start_pose_utm=Position(lat_long=(52.402590, 10.230100), psi=0.0).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402590, 10.230100), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=8,
        #     v2x_id=8,
        #     vehicle_parameters_file = "obstacle.json",
        # ),
        
        
        *create_simulated_vehicle(
            namespace="in_lane_left_obstacle",
            start_pose_utm=Position(lat_long=(52.402617, 10.230170), psi=0.0).get_utm_coordinates(),
            goal_position_utm=Position(lat_long=(52.402617, 10.230170), psi=0.0).get_utm_coordinates(),
            vehicle_id=7,
            v2x_id=7,
            vehicle_parameters_file = "obstacle.json",
        ),
        
        # *create_simulated_vehicle(
        #     namespace="neighbor_lane_vehicle",  #can be turned so that it is partly in the lane of the ego vehicle
        #     start_pose_utm=Position(lat_long=(52.402521, 10.229703), psi=3.75).get_utm_coordinates(),
        #     goal_position_utm=Position(lat_long=(52.402521, 10.229703), psi=0.0).get_utm_coordinates(),
        #     vehicle_id=3,
        #     v2x_id=3,
        #     vehicle_parameters_file = "NGC.json",
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

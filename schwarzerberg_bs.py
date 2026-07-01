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

from position import Position, Waypoint
from simulated_vehicle import create_simulated_vehicle
from visualizer import create_visualizer

# start_position = Position(lat_long=(52.291434, 10.513898), psi=-3.0)
# goal_position = Position(lat_long=(52.291207, 10.511044), psi=-3.0)

# start_position = Position(lat_long=(52.291613, 10.516043), psi=-3.04)
# goal_position = Position(lat_long=(52.292296, 10.516745), psi=0.0)

start_position = Position(lat_long=(52.291498, 10.514635), psi=-3.04)
goal_position = Position(lat_long=(52.290905, 10.508069), psi=0.0)

def generate_launch_description():
    return LaunchDescription([
        *create_simulated_vehicle(
            namespace="ego_vehicle",
            start_position_utm=start_position.get_utm_coordinates(),
            goals=[Waypoint(goal_position)],
            vehicle_id=111,
            v2x_id=0,
            map_file="de_bs_borders_wfs.r2sr",
            #max_speed= 8.333,  # 30 km/h
            max_speed=13.889,  # 50 km/h
        ),
        
        *create_visualizer(
            whitelist=["ego_vehicle"],
            visualization_offset=start_position.get_utm_coordinates(),
        ),

        *create_simulated_vehicle(
            namespace="parked_vehicle_1",
            start_position_utm=Position(lat_long=(52.291343, 10.512557), psi=-3.0).get_utm_coordinates(),
            goals=[Waypoint(Position(lat_long=(52.291343, 10.512557), psi=-3.0))],
            vehicle_id=1,
            v2x_id=1,
            vehicle_parameters_file = "NGC.json",
        ),

        # *create_simulated_vehicle(
        #     namespace="parked_vehicle_2",
        #     start_position_utm=Position(lat_long=(52.291334, 10.512360), psi=-3.0).get_utm_coordinates(),
        #     goals=[Waypoint(Position(lat_long=(52.291334, 10.512360), psi=-3.0))],
        #     vehicle_id=2,
        #     v2x_id=2,
        #     vehicle_parameters_file = "NGC.json",
        # ),
        
        # *create_simulated_vehicle(
        #     namespace="obastacle",
        #     start_position_utm=Position(lat_long=(52.291334, 10.512468), psi=-3.0).get_utm_coordinates(),
        #     goals=[Waypoint(Position(lat_long=(52.291334, 10.512468), psi=-3.0))],
        #     vehicle_id=3,
        #     v2x_id=3,
        #     vehicle_parameters_file = "obstacle.json",
        # ),

        *create_simulated_vehicle(
            namespace="oncoming_vehicle",
            start_position_utm=Position(lat_long=(52.291177, 10.511060), psi=0.0).get_utm_coordinates(),
            goals=[Waypoint(Position(lat_long=(52.291399, 10.513708), psi=0.25))],
            vehicle_id=3,
            v2x_id=3,
            vehicle_parameters_file = "NGC.json",
            map_file="de_bs_borders_wfs.r2sr",
            #max_speed=13.889,  # 50 km/h
            max_speed= 5.0,  #
            #max_speed= 6.0,  
        ),
    ])

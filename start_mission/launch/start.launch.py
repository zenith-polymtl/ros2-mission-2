#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    publisher_node = Node(
        package="mission",
        executable="state",
        name="state"
    )

    vision_node = Node(
        package="mission",
        executable="vision",
        name="vision"
    )

    approach_node = Node(
        package="mission",
        executable="approach",
        name="approach"
    )

    ld.add_action(publisher_node)
    ld.add_action(vision_node)
    ld.add_action(approach_node)
    return ld
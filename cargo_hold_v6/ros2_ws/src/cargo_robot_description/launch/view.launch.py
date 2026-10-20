from pathlib import Path
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    share=Path(get_package_share_directory('cargo_robot_description'))
    return LaunchDescription([
        Node(package='robot_state_publisher',executable='robot_state_publisher',
            parameters=[{'robot_description':(share/'urdf'/'cargo_robot.urdf').read_text()}]),
        Node(package='cargo_robot_description',executable='urdf_scissor_demo.py'),
        Node(package='rviz2',executable='rviz2',arguments=['-d',str(share/'config'/'robot.rviz')])])

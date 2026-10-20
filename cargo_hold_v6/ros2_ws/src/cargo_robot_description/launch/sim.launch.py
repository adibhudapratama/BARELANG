from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory, get_package_prefix
import os

def generate_launch_description():
    share=Path(get_package_share_directory('cargo_robot_description'))
    gzshare=Path(get_package_share_directory('ros_gz_sim'))
    lib=Path(get_package_prefix('cargo_robot_description'))/'lib'
    return LaunchDescription([
        DeclareLaunchArgument('demo',default_value='false'),
        DeclareLaunchArgument('mode',default_value='stack'),
        DeclareLaunchArgument('layers',default_value='3'),
        DeclareLaunchArgument('unload',default_value='true'),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH',str(share/'models')+os.pathsep+os.environ.get('GZ_SIM_RESOURCE_PATH','')),
        SetEnvironmentVariable('GZ_SIM_SYSTEM_PLUGIN_PATH',str(lib)+os.pathsep+os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH','')),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gzshare/'launch'/'gz_sim.launch.py')),
            launch_arguments={'gz_args':'-r '+str(share/'worlds'/'cargo_demo.sdf'),'on_exit_shutdown':'true'}.items()),
        Node(package='robot_state_publisher',executable='robot_state_publisher',
            parameters=[{'robot_description':(share/'urdf'/'cargo_robot.urdf').read_text(),'use_sim_time':True}]),
        Node(package='ros_gz_bridge',executable='parameter_bridge',
            parameters=[{'config_file':str(share/'config'/'bridge.yaml'),'use_sim_time':True}],output='screen'),
        Node(package='cargo_robot_description',executable='battery_estimator.py',parameters=[{'use_sim_time':True}],output='screen'),
        Node(package='cargo_robot_description',executable='demo_cycle.py',
            parameters=[{'use_sim_time':True,'mode':LaunchConfiguration('mode'),
                         'layers':ParameterValue(LaunchConfiguration('layers'),value_type=int),
                         'unload':ParameterValue(LaunchConfiguration('unload'),value_type=bool)}],condition=IfCondition(LaunchConfiguration('demo')),output='screen')])

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, TimerAction, RegisterEventHandler, EmitEvent
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import PushRosNamespace, Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # 1. OpenManipulator-X Launch
    open_manipulator_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('open_manipulator_bringup'), 'launch', 'open_manipulator_x.launch.py')
        ])
    )

    # 2. RealSense Camera Launch (inside a namespace to isolate robot_description)
    realsense_launch = TimerAction(
        period=5.0,
        actions=[
            GroupAction(
                actions=[
                    PushRosNamespace('camera_namespace'),
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource([
                            os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')
                        ])
                    )
                ]
            )
        ]
    )

    # 3. Hand Tracker Node
    hand_tracker_node = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='hand_tracking_openx',
                executable='hand_tracker_node',
                name='hand_tracker_node',
                output='screen',
                parameters=[{
                    'image_topic': '/camera_namespace/camera/camera/color/image_raw'
                }],
                on_exit=[
                    EmitEvent(event=Shutdown())
                ]
            )
        ]
    )

    return LaunchDescription([
        open_manipulator_launch,
        realsense_launch,
        hand_tracker_node
    ])

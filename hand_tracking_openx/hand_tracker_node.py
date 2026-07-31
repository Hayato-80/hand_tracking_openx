import sys
import os
import math
import time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from cv_bridge import CvBridge
import cv2
from ament_index_python.packages import get_package_share_directory

# Automatically add the venv site-packages to sys.path if it exists
venv_path = os.path.expanduser('~/ros2_ws/.venv/lib/python3.12/site-packages')
if os.path.exists(venv_path) and venv_path not in sys.path:
    sys.path.insert(0, venv_path)

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

class HandTrackerNode(Node):
    def __init__(self):
        super().__init__('hand_tracker_node')
        
        if not HAS_MEDIAPIPE:
            self.get_logger().error("MediaPipe is not installed.")
            sys.exit(1)

        self.bridge = CvBridge()
        
        self.declare_parameter('image_topic', '/camera_namespace/camera/camera/color/image_raw')
        topic_name = self.get_parameter('image_topic').get_parameter_value().string_value
        
        self.subscription = self.create_subscription(
            Image,
            topic_name,
            self.image_callback,
            10)
            
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10)
        self.current_joints = [0.0, 0.0, 0.0, 0.0]
        self.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
        self.has_joint_states = False
            
        self.publisher_ = self.create_publisher(Image, '~/image_annotated', 10)
        
        self.arm_publisher = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10
        )

        model_path = os.path.join(
            get_package_share_directory('hand_tracking_openx'), 'hand_landmarker.task'
        )
        if not os.path.exists(model_path):
            self.get_logger().error(f"Model {model_path} not found! Please download it.")
            sys.exit(1)

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
        self.detector = vision.HandLandmarker.create_from_options(options)

        self.last_command_time = time.time()
        self.command_interval = 0.1 

        self.get_logger().info(f"Hand tracker initialized. Subscribed to {topic_name}")
        
        # Send to initial pose (last motor pitched UP ~30 degrees = -0.524 rad)
        self.initial_pose = [0.0, -1.0, 1.0, -0.524]
        self.initial_pose_time = 0.0
        
        # Timer for sending initial pose (wait a bit for subscribers to connect)
        self.create_timer(2.0, self.send_initial_pose)
        
        # Target EMA
        self.target_joints_ema = np.array(self.initial_pose)

    def send_initial_pose(self):
        if self.initial_pose_time > 0:
            return
            
        self.get_logger().info("Sending arm to initial pose [0.0, -1.0, 1.0, 0.0]...")
        traj = JointTrajectory()
        traj.header.stamp = self.get_clock().now().to_msg()
        traj.joint_names = self.joint_names
        
        point = JointTrajectoryPoint()
        point.positions = self.initial_pose
        point.time_from_start.sec = 2
        point.time_from_start.nanosec = 0

        traj.points.append(point)
        self.arm_publisher.publish(traj)
        self.initial_pose_time = time.time()

    def image_callback(self, msg):
        # Wait until initial pose trajectory finishes (2 seconds + 0.5s buffer)
        if self.initial_pose_time == 0 or time.time() - self.initial_pose_time < 2.5:
            return
            
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            return

        cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv_image_rgb)
        
        detection_result = self.detector.detect(mp_image)
        
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                h, w, _ = cv_image.shape
                for lm in hand_landmarks:
                    cv2.circle(cv_image, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
                
                # Draw crosshair for Visual Servoing target
                target_x_px = int(0.5 * w)
                target_y_px = int(0.5 * h)
                cv2.drawMarker(cv_image, (target_x_px, target_y_px), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
                
                self.process_teleop(hand_landmarks)
                break 

        cv2.imshow("Hand Tracking", cv_image)
        cv2.waitKey(1)

        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
            annotated_msg.header = msg.header
            self.publisher_.publish(annotated_msg)
        except Exception:
            pass

    def joint_state_callback(self, msg):
        if set(self.joint_names).issubset(set(msg.name)):
            for i, name in enumerate(self.joint_names):
                idx = msg.name.index(name)
                self.current_joints[i] = msg.position[idx]
            self.has_joint_states = True

    def process_teleop(self, hand_landmarks):
        now = time.time()
        if now - self.last_command_time < self.command_interval:
            return
        self.last_command_time = now

        if not self.has_joint_states:
            return

        WRIST = 0
        THUMB_TIP = 4
        INDEX_FINGER_TIP = 8

        wrist = hand_landmarks[WRIST]
        x = wrist.x
        y = wrist.y

        thumb_tip = hand_landmarks[THUMB_TIP]
        index_tip = hand_landmarks[INDEX_FINGER_TIP]
        
        dist = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        
        is_open = dist > 0.05
        
        # When hand is closed (rock), do nothing (stop)
        if is_open:
            # IMAGE-BASED VISUAL SERVOING (IBVS)
            # The goal is to move the robot so the hand aligns with the target (center of image)
            target_x = 0.5
            target_y = 0.5
            
            error_x = target_x - x
            error_y = target_y - y
            
            # Deadzone to stop micro-jitter when hand is near the center
            if abs(error_x) < 0.05: error_x = 0.0
            if abs(error_y) < 0.05: error_y = 0.0
            
            # Proportional velocity gains (slightly increased for faster tracking)
            k_yaw = 0.8
            k_pitch = -0.8
            
            q_dot = np.zeros(4)
            q_dot[0] = error_x * k_yaw
            q_dot[1] = error_y * k_pitch
            
            # Update EMA target by integrating the velocity
            # This ensures smooth, continuous movement towards the hand without jumping
            self.target_joints_ema = self.target_joints_ema + q_dot * self.command_interval
            
            # Joint limits (approximate OM-X limits in radians)
            limits_min = np.array([-3.14, -1.5, -1.5, -1.7])
            limits_max = np.array([3.14, 1.5, 1.4, 1.97])
            target_joints = np.clip(self.target_joints_ema, limits_min, limits_max)

            traj = JointTrajectory()
            traj.header.stamp = self.get_clock().now().to_msg()
            traj.joint_names = self.joint_names
            
            point = JointTrajectoryPoint()
            point.positions = target_joints.tolist()
            point.time_from_start.sec = 0
            point.time_from_start.nanosec = int(self.command_interval * 1e9 * 1.5)

            traj.points.append(point)
            self.arm_publisher.publish(traj)

    def destroy_node(self):
        if hasattr(self, 'detector') and self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HandTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # rclpy.shutdown() can sometimes hang, and cv2.destroyAllWindows() can hang.
        try:
            cv2.destroyAllWindows()
            rclpy.shutdown()
        except:
            pass
        os._exit(0)  # Force OS-level exit to ensure Launch Shutdown triggers immediately

if __name__ == '__main__':
    main()

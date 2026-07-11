#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Bool, Int16
from eufs_msgs.msg import CanState
from .missionLauncher import AMIToConfig
import time

'''
Mission indicator

uint16 ami_state

uint16 AMI_NOT_SELECTED=10
uint16 AMI_ACCELERATION=11
uint16 AMI_SKIDPAD=12
uint16 AMI_AUTOCROSS=13
uint16 AMI_TRACK_DRIVE=14
uint16 AMI_AUTONOMOUS_DEMO=15
uint16 AMI_ADS_INSPECTION=16
uint16 AMI_ADS_EBS=17
uint16 AMI_DDT_INSPECTION_A=18
uint16 AMI_DDT_INSPECTION_B=19
uint16 AMI_JOYSTICK=20
uint16 AMI_MANUAL=21

'''


class MissionFinisher(Node):

    def __init__(self):
        super().__init__('mission_finisher')

        self.get_logger().info('Mission Finisher Node has started.')

        # ==========================
        # Parameters / Topics
        # ==========================

        self.declare_parameter('slam_distance_topic', '/slam/distance')
        self.declare_parameter('loop_closure_topic', '/loop_closure_flag')
        self.declare_parameter('orange_cone_topic', '/perception/isOrangeCone')
        self.declare_parameter('skidpad_finisher_topic', '/skidpad_finisher')
        self.declare_parameter('mission_finisher_topic', '/finisher/is_finished')
        self.declare_parameter('loop_closure_count_topic', '/supervisor/loopClosureCount')

        self.declare_parameter('acceleration_distance', 40)

        # Use 2 for testing.
        # Later change this to 10 for real trackdrive.
        self.declare_parameter('trackdrive_loop_target', 2)

        self.slamDistanceTopic = self.get_parameter(
            'slam_distance_topic'
        ).get_parameter_value().string_value

        self.loopClosureTopic = self.get_parameter(
            'loop_closure_topic'
        ).get_parameter_value().string_value

        self.isOrangeConeTopic = self.get_parameter(
            'orange_cone_topic'
        ).get_parameter_value().string_value

        self.skidpadFinisherTopic = self.get_parameter(
            'skidpad_finisher_topic'
        ).get_parameter_value().string_value

        self.missionFinisherTopic = self.get_parameter(
            'mission_finisher_topic'
        ).get_parameter_value().string_value

        self.loopClosureCountTopic = self.get_parameter(
            'loop_closure_count_topic'
        ).get_parameter_value().string_value

        self.acceleration_distance = self.get_parameter(
            'acceleration_distance'
        ).get_parameter_value().double_value

        self.trackdrive_loop_target = self.get_parameter(
            'trackdrive_loop_target'
        ).get_parameter_value().integer_value

        # ==========================
        # State
        # ==========================

        self.mission_selected = CanState.AMI_NOT_SELECTED
        self.loopClosureCount = 0
        self.finished_sent = False

        # ==========================
        # Publishers
        # ==========================

        self.mission_finisher_pub = self.create_publisher(
            Bool,
            self.missionFinisherTopic,
            10
        )

        self.loop_closure_count_pub = self.create_publisher(
            Int16,
            self.loopClosureCountTopic,
            10
        )

        # ==========================
        # Subscribers
        # ==========================

        self.can_state_sub = self.create_subscription(
            CanState,
            '/ros_can/state',
            self.canStateCallback,
            10
        )

        self.distance_sub = self.create_subscription(
            Float32,
            self.slamDistanceTopic,
            self.acceleration_distance_callback,
            10
        )

        self.loop_closure_sub = self.create_subscription(
            Bool,
            self.loopClosureTopic,
            self.loopClosure_callback,
            10
        )

        self.orange_cone_sub = self.create_subscription(
            Bool,
            self.isOrangeConeTopic,
            self.orangeCone_callback,
            10
        )

        self.skidpad_sub = self.create_subscription(
            Bool,
            self.skidpadFinisherTopic,
            self.skidpad_callback,
            10
        )

        self.get_logger().info(f"Listening to distance topic: {self.slamDistanceTopic}")
        self.get_logger().info(f"Listening to loop closure topic: {self.loopClosureTopic}")
        self.get_logger().info(f"Publishing finish flag on: {self.missionFinisherTopic}")

    # ==========================
    # CAN State
    # ==========================

    def canStateCallback(self, msg: CanState):

        if self.mission_selected != msg.ami_state:
            self.get_logger().info(f"🎯 New mission selected: {msg.ami_state}")

            self.loopClosureCount = 0
            self.finished_sent = False

            count_msg = Int16()
            count_msg.data = self.loopClosureCount
            self.loop_closure_count_pub.publish(count_msg)

        self.mission_selected = msg.ami_state

    # ==========================
    # Helper
    # ==========================

    def publish_finished(self, reason: str):

        if self.finished_sent:
            return

        self.finished_sent = True

        self.get_logger().warn(f"🏁 Mission finished: {reason}")

        self.mission_finisher_pub.publish(
            Bool(data=True)
        )

    # ==========================
    # Mission Conditions
    # ==========================

    def acceleration_distance_callback(self, msg: Float32):

        if self.mission_selected != CanState.AMI_ACCELERATION:
            return

        if self.finished_sent:
            return

        self.get_logger().info(f"Acceleration distance = {msg.data}")

        if msg.data >= self.acceleration_distance:
            self.publish_finished("acceleration distance reached")

    def skidpad_callback(self, msg: Bool):

        if self.mission_selected != CanState.AMI_SKIDPAD:
            return

        if self.finished_sent:
            return

        if msg.data:
            self.publish_finished("skidpad finisher flag received")

    def loopClosure_callback(self, msg: Bool):

        if not msg.data:
            return

        if self.finished_sent:
            return

        # Autocross finishes on first loop closure
        if self.mission_selected == CanState.AMI_AUTOCROSS:
            self.publish_finished("autocross loop closure detected")

        # Trackdrive counts loop closures
        elif self.mission_selected == CanState.AMI_TRACK_DRIVE:
            self.loopClosureCount += 1

            count_msg = Int16()
            count_msg.data = self.loopClosureCount
            self.loop_closure_count_pub.publish(count_msg)

            self.get_logger().info(
                f"🏁 Trackdrive loop closure count = {self.loopClosureCount}"
            )

            if self.loopClosureCount >= self.trackdrive_loop_target:
                self.publish_finished("trackdrive loop target reached")

    def orangeCone_callback(self, msg: Bool):

        if not msg.data:
            return

        if self.finished_sent:
            return

        if self.mission_selected == CanState.AMI_AUTOCROSS:
            self.publish_finished("autocross orange cone detected")

        elif self.mission_selected == CanState.AMI_SKIDPAD:
            self.publish_finished("skidpad orange cone detected")

        elif self.mission_selected == CanState.AMI_ACCELERATION:
            self.publish_finished("acceleration orange cone detected")


def main(args=None):
    rclpy.init(args=args)

    node = MissionFinisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
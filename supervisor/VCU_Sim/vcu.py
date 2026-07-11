#!/usr/bin/env python3
"""
VCU (Vehicle Control Unit) Simulator for Formula Student AI
Simulates VCU2AI messages and responds to AI2VCU commands
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from enum import IntEnum
import math
import random

# ROS message imports
from eufs_msgs.msg import CanState, WheelSpeedsStamped, VehicleCommandsStamped
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import Imu, NavSatFix
from std_msgs.msg import String, Bool
from ackermann_msgs.msg import AckermannDriveStamped
from std_srvs.srv import Trigger

class ASState(IntEnum):
    AS_OFF = 0
    AS_READY = 1
    AS_DRIVING = 2
    AS_EMERGENCY_BRAKE = 3
    AS_FINISHED = 4

class AMIState(IntEnum):
    AMI_NOT_SELECTED = 10
    AMI_ACCELERATION = 11
    AMI_SKIDPAD = 12
    AMI_AUTOCROSS = 13
    AMI_TRACK_DRIVE = 14
    AMI_STATIC_INSPECTION_A = 15
    AMI_STATIC_INSPECTION_B = 16
    AMI_AUTONOMOUS_DEMO = 17

class VCUSimulator(Node):
    def __init__(self):
        super().__init__('vcu_simulator')
        
        # Initialize vehicle state
        self.as_state = ASState.AS_OFF
        self.ami_state = AMIState.AMI_NOT_SELECTED
        self.handshake_bit = False
        self.driving_flag_received = False
        self.mission_complete_received = False
        
        # Vehicle dynamics
        self.wheel_speeds = [0.0, 0.0, 0.0, 0.0]  # FL, FR, RL, RR (RPM)
        self.steering_angle = 0.0  # degrees
        self.vehicle_speed = 0.0   # m/s
        self.pulse_counts = [0, 0, 0, 0]  # FL, FR, RL, RR
        
        # Command inputs from AI
        self.ai_steering_cmd = 0.0
        self.ai_torque_cmd = 0.0
        self.ai_brake_cmd = 0.0
        self.ai_rpm_cmd = 0.0
        self.ai_ebs_request = False
        
        # Simulation parameters
        self.wheel_radius = 0.2  # meters
        self.max_rpm = 3000
        self.max_steering = 540  # degrees
        
        # GPS simulation
        self.gps_lat_deg = 55
        self.gps_lat_min = 51.5
        self.gps_lon_deg = -4
        self.gps_lon_min = 12.3
        self.gps_altitude = 100.0
        
        # IMU simulation
        self.imu_accel = [0.0, 0.0, 9.81]  # m/s^2
        self.imu_gyro = [0.0, 0.0, 0.0]    # rad/s
        
        # QoS profile
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Publishers (simulating the real car's CAN messages)
        self.state_pub = self.create_publisher(CanState, '/ros_can/state', qos_profile)
        self.state_str_pub = self.create_publisher(String, '/ros_can/state_str', qos_profile)
        self.wheel_speeds_pub = self.create_publisher(WheelSpeedsStamped, '/ros_can/wheel_speeds', qos_profile)
        self.twist_pub = self.create_publisher(TwistWithCovarianceStamped, '/ros_can/twist', qos_profile)
        self.imu_pub = self.create_publisher(Imu, '/ros_can/imu', qos_profile)
        self.gps_pub = self.create_publisher(NavSatFix, '/ros_can/fix', qos_profile)
        
        # Subscribers (listening to AI commands)
        self.cmd_sub = self.create_subscription(
            AckermannDriveStamped, '/cmd', self.cmd_callback, qos_profile)
        self.vehicle_cmd_sub = self.create_subscription(
            VehicleCommandsStamped, '/ros_can/vehicle_commands', self.vehicle_cmd_callback, qos_profile)
        self.driving_flag_sub = self.create_subscription(
            Bool, '/state_machine/driving_flag', self.driving_flag_callback, qos_profile)
        self.mission_complete_sub = self.create_subscription(
            Bool, '/ros_can/mission_completed', self.mission_complete_callback, qos_profile)
        
        # Services for manual control
        self.set_as_state_srv = self.create_service(
            Trigger, '/vcu_sim/next_as_state', self.next_as_state_callback)
        self.set_ami_state_srv = self.create_service(
            Trigger, '/vcu_sim/cycle_ami_state', self.cycle_ami_state_callback)
        self.emergency_stop_srv = self.create_service(
            Trigger, '/vcu_sim/emergency_stop', self.emergency_stop_callback)
        
        # Timer for publishing simulated data
        self.timer = self.create_wall_timer(0.02, self.publish_simulated_data)  # 50 Hz
        self.dynamics_timer = self.create_wall_timer(0.01, self.update_vehicle_dynamics)  # 100 Hz
        
        # State machine timer
        self.state_timer = self.create_wall_timer(1.0, self.update_state_machine)  # 1 Hz
        
        self.get_logger().info("VCU Simulator started")
        self.get_logger().info("Available services:")
        self.get_logger().info("  /vcu_sim/next_as_state - Advance AS state")
        self.get_logger().info("  /vcu_sim/cycle_ami_state - Cycle AMI state")
        self.get_logger().info("  /vcu_sim/emergency_stop - Trigger emergency stop")
        self.print_current_state()

    def cmd_callback(self, msg):
        """Handle Ackermann drive commands from AI"""
        if self.as_state == ASState.AS_DRIVING:
            # Convert steering angle from radians to degrees
            self.ai_steering_cmd = msg.drive.steering_angle * 180.0 / math.pi
            
            # Simulate vehicle response to commands
            acceleration = msg.drive.acceleration
            if acceleration > 0:
                self.ai_torque_cmd = abs(acceleration) * 100  # Simplified torque calculation
                self.ai_brake_cmd = 0.0
                self.ai_rpm_cmd = min(2000, abs(acceleration) * 500)
            elif acceleration < 0:
                self.ai_torque_cmd = 0.0
                self.ai_brake_cmd = abs(acceleration) * 50
                self.ai_rpm_cmd = 0.0
            else:
                self.ai_torque_cmd = 0.0
                self.ai_brake_cmd = 0.0
                self.ai_rpm_cmd = 0.0

    def vehicle_cmd_callback(self, msg):
        """Handle vehicle commands from ROS CAN node"""
        self.ai_steering_cmd = msg.commands.steering
        self.ai_torque_cmd = msg.commands.torque
        self.ai_brake_cmd = msg.commands.braking
        self.ai_rpm_cmd = msg.commands.rpm
        self.ai_ebs_request = (msg.commands.ebs == 1)
        
        # Toggle handshake bit
        self.handshake_bit = not self.handshake_bit

    def driving_flag_callback(self, msg):
        """Handle driving flag from state machine"""
        self.driving_flag_received = msg.data

    def mission_complete_callback(self, msg):
        """Handle mission completion flag"""
        self.mission_complete_received = msg.data

    def update_vehicle_dynamics(self):
        """Update simulated vehicle dynamics"""
        if self.as_state == ASState.AS_DRIVING:
            # Simple vehicle dynamics simulation
            dt = 0.01  # 100 Hz update rate
            
            # Update vehicle speed based on torque and braking
            if self.ai_torque_cmd > 0:
                acceleration = self.ai_torque_cmd / 1000.0  # Simplified
                self.vehicle_speed += acceleration * dt
            elif self.ai_brake_cmd > 0:
                deceleration = self.ai_brake_cmd / 100.0 * 10  # Simplified
                self.vehicle_speed -= deceleration * dt
            else:
                # Coast down
                self.vehicle_speed *= 0.995
            
            # Limit speed
            self.vehicle_speed = max(0, min(self.vehicle_speed, 30))  # Max 30 m/s
            
            # Update steering (with some lag)
            steering_diff = self.ai_steering_cmd - self.steering_angle
            self.steering_angle += steering_diff * 0.1  # 10% per step
            self.steering_angle = max(-self.max_steering, min(self.max_steering, self.steering_angle))
            
            # Convert speed to wheel RPM (simplified, assuming no slip)
            rpm_base = (self.vehicle_speed / (2 * math.pi * self.wheel_radius)) * 60
            
            # Add some noise and differences between wheels
            self.wheel_speeds[0] = rpm_base + random.uniform(-5, 5)  # FL
            self.wheel_speeds[1] = rpm_base + random.uniform(-5, 5)  # FR
            self.wheel_speeds[2] = rpm_base + random.uniform(-5, 5)  # RL
            self.wheel_speeds[3] = rpm_base + random.uniform(-5, 5)  # RR
            
            # Update pulse counts (incremental)
            for i in range(4):
                self.pulse_counts[i] += int(self.wheel_speeds[i] / 60 * dt * 100)  # Arbitrary scaling
            
            # Update IMU data based on motion
            self.imu_accel[0] = (self.ai_torque_cmd - self.ai_brake_cmd * 2) / 100.0  # Longitudinal
            self.imu_accel[1] = math.sin(math.radians(self.steering_angle)) * 0.1  # Lateral
            self.imu_gyro[2] = self.vehicle_speed * math.sin(math.radians(self.steering_angle)) / 2.0  # Yaw rate
        else:
            # Vehicle not driving, decay all values
            self.vehicle_speed *= 0.95
            self.steering_angle *= 0.9
            for i in range(4):
                self.wheel_speeds[i] *= 0.9

    def update_state_machine(self):
        """Update the AS state machine based on conditions"""
        if self.ai_ebs_request:
            self.as_state = ASState.AS_EMERGENCY_BRAKE
            self.get_logger().warn("EMERGENCY BRAKE ACTIVATED!")
            return
        
        if self.mission_complete_received and self.as_state == ASState.AS_DRIVING:
            self.as_state = ASState.AS_FINISHED
            self.get_logger().info("Mission completed - AS_FINISHED")

    def publish_simulated_data(self):
        """Publish all simulated sensor data"""
        timestamp = self.get_clock().now()
        
        # Publish CAN state
        state_msg = CanState()
        state_msg.as_state = int(self.as_state)
        state_msg.ami_state = int(self.ami_state)
        self.state_pub.publish(state_msg)
        
        # Publish state string
        state_str_msg = String()
        as_str = f"AS:{ASState(self.as_state).name}"
        ami_str = f"AMI:{AMIState(self.ami_state).name}"
        driving_str = f"DRIVING:{self.driving_flag_received}"
        state_str_msg.data = f"{as_str} {ami_str} {driving_str}"
        self.state_str_pub.publish(state_str_msg)
        
        # Publish wheel speeds
        wheel_msg = WheelSpeedsStamped()
        wheel_msg.header.stamp = timestamp
        wheel_msg.header.frame_id = "base_footprint"
        wheel_msg.speeds.lf_speed = self.wheel_speeds[0]
        wheel_msg.speeds.rf_speed = self.wheel_speeds[1]
        wheel_msg.speeds.lb_speed = self.wheel_speeds[2]
        wheel_msg.speeds.rb_speed = self.wheel_speeds[3]
        wheel_msg.speeds.steering = math.radians(-self.steering_angle)  # Convert to radians, inverted
        self.wheel_speeds_pub.publish(wheel_msg)
        
        # Publish twist
        twist_msg = TwistWithCovarianceStamped()
        twist_msg.header.stamp = timestamp
        twist_msg.header.frame_id = "base_footprint"
        twist_msg.twist.twist.linear.x = self.vehicle_speed
        twist_msg.twist.twist.angular.z = self.imu_gyro[2]
        # Set covariance (simplified)
        twist_msg.twist.covariance = [1e-3] + [0]*5 + [0]*5 + [1e-3] + [0]*24
        self.twist_pub.publish(twist_msg)
        
        # Publish IMU
        imu_msg = Imu()
        imu_msg.header.stamp = timestamp
        imu_msg.header.frame_id = "base_footprint"
        imu_msg.linear_acceleration.x = self.imu_accel[0]
        imu_msg.linear_acceleration.y = self.imu_accel[1]
        imu_msg.linear_acceleration.z = self.imu_accel[2]
        imu_msg.angular_velocity.x = self.imu_gyro[0]
        imu_msg.angular_velocity.y = self.imu_gyro[1]
        imu_msg.angular_velocity.z = self.imu_gyro[2]
        self.imu_pub.publish(imu_msg)
        
        # Publish GPS
        gps_msg = NavSatFix()
        gps_msg.header.stamp = timestamp
        gps_msg.header.frame_id = "base_footprint"
        gps_msg.latitude = self.gps_lat_deg + self.gps_lat_min / 60.0
        gps_msg.longitude = self.gps_lon_deg + self.gps_lon_min / 60.0
        gps_msg.altitude = self.gps_altitude
        self.gps_pub.publish(gps_msg)

    def next_as_state_callback(self, request, response):
        """Service to advance to next AS state"""
        old_state = self.as_state
        
        if self.as_state == ASState.AS_OFF:
            if self.ami_state != AMIState.AMI_NOT_SELECTED:
                self.as_state = ASState.AS_READY
            else:
                response.success = False
                response.message = "Cannot go to AS_READY: AMI state not selected"
                return response
        elif self.as_state == ASState.AS_READY:
            if self.driving_flag_received:
                self.as_state = ASState.AS_DRIVING
            else:
                response.success = False
                response.message = "Cannot go to AS_DRIVING: driving flag not set"
                return response
        elif self.as_state == ASState.AS_DRIVING:
            self.as_state = ASState.AS_FINISHED
        elif self.as_state == ASState.AS_FINISHED:
            self.as_state = ASState.AS_OFF
            self.mission_complete_received = False
        elif self.as_state == ASState.AS_EMERGENCY_BRAKE:
            self.as_state = ASState.AS_OFF
            self.ai_ebs_request = False
        
        response.success = True
        response.message = f"AS state changed from {ASState(old_state).name} to {ASState(self.as_state).name}"
        self.get_logger().info(response.message)
        self.print_current_state()
        return response

    def cycle_ami_state_callback(self, request, response):
        """Service to cycle through AMI states"""
        old_state = self.ami_state
        
        # Cycle through common AMI states
        ami_cycle = [
            AMIState.AMI_NOT_SELECTED,
            AMIState.AMI_ACCELERATION,
            AMIState.AMI_SKIDPAD,
            AMIState.AMI_AUTOCROSS,
            AMIState.AMI_TRACK_DRIVE,
        ]
        
        try:
            current_index = ami_cycle.index(self.ami_state)
            next_index = (current_index + 1) % len(ami_cycle)
            self.ami_state = ami_cycle[next_index]
        except ValueError:
            self.ami_state = AMIState.AMI_ACCELERATION
        
        response.success = True
        response.message = f"AMI state changed from {AMIState(old_state).name} to {AMIState(self.ami_state).name}"
        self.get_logger().info(response.message)
        self.print_current_state()
        return response

    def emergency_stop_callback(self, request, response):
        """Service to trigger emergency stop"""
        self.as_state = ASState.AS_EMERGENCY_BRAKE
        self.ai_ebs_request = True
        response.success = True
        response.message = "Emergency stop triggered"
        self.get_logger().warn(response.message)
        self.print_current_state()
        return response

    def print_current_state(self):
        """Print current vehicle state"""
        self.get_logger().info(f"Current State - AS: {ASState(self.as_state).name}, AMI: {AMIState(self.ami_state).name}")
        self.get_logger().info(f"Speed: {self.vehicle_speed:.2f} m/s, Steering: {self.steering_angle:.1f}°")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        vcu_sim = VCUSimulator()
        rclpy.spin(vcu_sim)
    except KeyboardInterrupt:
        pass
    finally:
        if 'vcu_sim' in locals():
            vcu_sim.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
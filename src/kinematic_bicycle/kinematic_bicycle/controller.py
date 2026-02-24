import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from nav_msgs.msg import Odometry, Path
import numpy as np
import math

# --- Pure Pursuit Constants ---
# Increased MIN to help steering at low speeds.
K_Ld = 0.18 # Lookahead distance gain
Ld_MIN = 1.5 # Increased slightly for initial stability
WHEELBASE = 2.5 

# --- PID Constants ---
KP_SPEED = 3.0
KI_SPEED = 0.08
KD_SPEED = 0.3  
KT = 0.2 #Constant for target speed adjustment based on steering angle  
# --- PID Constants for Stopping ---
STOP_DISTANCE = 12  # Distance to final waypoint to start stopping
KP_STOP = 50.0  
KI_STOP = 0.05
KD_STOP = 10.0


class Controller(Node):
    def __init__(self):
        super().__init__('controller')
        self.get_logger().info("Controller Node Initialized (Pure Pursuit + PID)")
        
        # --- State Variables ---
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.current_v = 0.0 
        self.waypoints = [] 
        self.target_index = 0
        
        # PID control history
        self.error_sum = 0.0
        self.last_error = 0.0
        self.dt = 0.1 

        # Timer for control loop
        self.timer = self.create_timer(self.dt, self.controlLoop)

        # Publishers and Subscribers
        self.throttlePub = self.create_publisher(Float32, '/throttle', 10)
        self.steerPub = self.create_publisher(Float32, '/steer', 10)
        
        self.stateSubscription = self.create_subscription(
            Odometry, '/state', self.stateCallback, 10)
        
        self.pathSubscription = self.create_subscription(
            Path, '/path', self.pathCallback, 10)

        self.target_speed = 7.5  # Set initial target speed as instance variable




    def stateCallback(self, state:Odometry):
        
        # Position
        self.current_x = state.pose.pose.position.x
        self.current_y = state.pose.pose.position.y
        
        # Velocity
        self.current_v = state.twist.twist.linear.x
        
        # Orientation (Yaw is the rotation about Z from a quaternion)
        q = state.pose.pose.orientation
        
        # 📢 Standard Yaw Extraction (using tf_transformations could be cleaner, but this works)
        # Yaw extraction formula used here is standard for Z-axis rotation.
        self.current_yaw = math.atan2(
            2 * (q.w * q.z + q.x * q.y),
            1 - 2 * (q.y * q.y + q.z * q.z)
        )



    def pathCallback(self, path:Path):
        
        # Store only the poses (waypoints)
        self.waypoints = path.poses
        self.get_logger().info(f"Received path with {len(self.waypoints)} waypoints.")





    def controlLoop(self):
        """Main control loop, called by the timer."""
        if not self.waypoints:
            self.get_logger().info("Waiting for a path...")
            return

        # Initialize steering_angle
        steering_angle = 0.0
        
        # 1. Update Target Index
        self.target_index = self.searchTargetPoint()

        # 2. Calculate Steering Angle (Pure Pursuit) - Always calculate steering
        steering_angle = self.purePursuit(self.target_index)

        # 2.5 compute distance to final waypoint
        last_wp = self.waypoints[-1].pose.position
        dist_to_last = math.hypot(last_wp.x - self.current_x, last_wp.y - self.current_y)

        # 3. Decide whether to stop or continue PID control
        if self.target_index >= len(self.waypoints) - 1 and dist_to_last <= STOP_DISTANCE:
            # close enough to final point -> use braking routine (PID-based)
            throttle_input = self.stopCar()
        else:
            throttle_input = self.pidController()

        # 4. Publish Control Inputs
        steer_msg = Float32(data=steering_angle * 180 / np.pi)  # Convert radians to degrees
        throttle_msg = Float32(data=throttle_input)

        self.steerPub.publish(steer_msg)
        self.throttlePub.publish(throttle_msg)

        self.get_logger().debug(f"V: {self.current_v:.2f}, Steer: {steering_angle * 180 / np.pi:.1f} deg, Throttle: {throttle_input:.2f}")




    def stopCar(self):
        """Gradually stop the car using PID control."""
        # Set a target speed of 0 for stopping
        target_speed = 0.0
        error = target_speed - self.current_v
        
        # PID calculations
        P = KP_STOP * error
        self.error_sum += error * self.dt
        I = KI_STOP * self.error_sum
        D = KD_STOP * (error - self.last_error) / self.dt
        self.last_error = error       
        throttle = P + I + D     
        return np.clip(throttle, -1.0, 1.0)  # Ensure throttle is within valid range
    
  
  
  
    def pidController(self):
        
        # Use self.target_speed instead of TARGET_SPEED
        error = self.target_speed - self.current_v
        
        P = KP_SPEED * error
        
        self.error_sum += error * self.dt
        I = KI_SPEED * self.error_sum
        
        D = KD_SPEED * (error - self.last_error) / self.dt
        self.last_error = error
        
        throttle = P + I + D
        
        # Clamp the output to valid ROS throttle range
        #return np.clip(throttle, -1.0, 1.0)
        
        #Apply zonne deadband
        if -0.01 < throttle < 0.01:
            throttle = 0.0
        
        return np.clip(throttle, -1.0, 1.0)
        
    
    
    def searchTargetPoint(self):
        # Calculate dynamic lookahead distance
        Ld = K_Ld * (self.current_v**2) + Ld_MIN
        
        # Update target speed based on steering angle
        current_steering = np.pi / 180 * abs(self.purePursuit(self.target_index))
        
        # Predict turn and adjust target speed
        if self.target_index < len(self.waypoints) - 1:
            next_wp_x = self.waypoints[self.target_index + 1].pose.position.x
            next_wp_y = self.waypoints[self.target_index + 1].pose.position.y
            
            # Calculate the angle to the next waypoint
            angle_to_next_wp = math.atan2(next_wp_y - self.current_y, next_wp_x - self.current_x)
            angle_diff = angle_to_next_wp - self.current_yaw
            
            # Normalize angle difference to be within -pi to pi
            angle_diff = (angle_diff + np.pi) % (2 * np.pi) - np.pi
            
            # Define a threshold for detecting a turn (e.g., 30 degrees)
            TURN_THRESHOLD = np.deg2rad(2.5)  # 30 degrees in radians
            
            # If the angle difference exceeds the threshold, it's a turn
            if abs(angle_diff) > TURN_THRESHOLD:
                # Gradually reduce target speed before the turn
                self.target_speed = max(2.5, self.target_speed - (abs(angle_diff) * 7))  # Adjust speed reduction factor as needed
            else:
                self.target_speed = 7.5  # Reset to normal speed if not turning
            if current_steering > np.deg2rad(5):
                Ld = 4.0  # Increase lookahead distance during sharp turns

        # Start search from the last known target index to reduce computation
        for i in range(self.target_index, len(self.waypoints)):
            wp_x = self.waypoints[i].pose.position.x
            wp_y = self.waypoints[i].pose.position.y
            
            distance = math.sqrt((wp_x - self.current_x)**2 + (wp_y - self.current_y)**2)
            
            # Select the first waypoint outside the lookahead distance as the target
            if distance > Ld:
                return i
    
        # If near the end, target the last point
        return len(self.waypoints) - 1
    



    def purePursuit(self, target_index):        
        if not self.waypoints or target_index >= len(self.waypoints):
            return 0.0 

        tx = self.waypoints[target_index].pose.position.x
        ty = self.waypoints[target_index].pose.position.y
        
        # 2. Transform Target Point to Vehicle Coordinates (Rear Axle Frame)
        dx = tx - self.current_x
        dy = ty - self.current_y
        
        # Rotate the delta (dx, dy) by -yaw to get car-relative coordinates
        tx_c = dx * math.cos(self.current_yaw) + dy * math.sin(self.current_yaw)
        ty_c = -dx * math.sin(self.current_yaw) + dy * math.cos(self.current_yaw)
        
        # 3. Recalculate Ld (should match dynamic Ld calculation for alpha)
        Ld = math.sqrt(tx_c**2 + ty_c**2)
        
        # 4. Calculate Angle to Target (alpha)
        alpha = math.atan2(ty_c, tx_c)
        
        # 5. Pure Pursuit Steering Formula
        delta = math.atan2(2 * WHEELBASE * math.sin(alpha), Ld)
        
        # Constrain the steering angle (35 degrees max)
        MAX_STEER_RAD = 35 * np.pi / 180 
        return np.clip(delta, -MAX_STEER_RAD, MAX_STEER_RAD)


def main(args=None):
    rclpy.init(args=args)
    controller = Controller()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()
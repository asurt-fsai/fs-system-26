#!/usr/bin/env python3
"""
VCU Simulator Controller - Interactive command-line interface
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from std_msgs.msg import Bool
import threading
import sys
import time

class VCUController(Node):
    def __init__(self):
        super().__init__('vcu_controller')
        
        # Service clients
        self.next_as_state_client = self.create_client(Trigger, '/vcu_sim/next_as_state')
        self.cycle_ami_state_client = self.create_client(Trigger, '/vcu_sim/cycle_ami_state')
        self.emergency_stop_client = self.create_client(Trigger, '/vcu_sim/emergency_stop')
        
        # Publishers for testing
        self.driving_flag_pub = self.create_publisher(Bool, '/state_machine/driving_flag', 10)
        self.mission_complete_pub = self.create_publisher(Bool, '/ros_can/mission_completed', 10)
        
        # Wait for services
        self.get_logger().info("Waiting for VCU simulator services...")
        self.next_as_state_client.wait_for_service(timeout_sec=5.0)
        self.cycle_ami_state_client.wait_for_service(timeout_sec=5.0)
        self.emergency_stop_client.wait_for_service(timeout_sec=5.0)
        self.get_logger().info("Connected to VCU simulator!")

    def call_service(self, client, service_name):
        """Call a service and return the response"""
        if not client.service_is_ready():
            self.get_logger().error(f"{service_name} service not available")
            return None
        
        request = Trigger.Request()
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            response = future.result()
            if response.success:
                self.get_logger().info(f"{service_name}: {response.message}")
            else:
                self.get_logger().warn(f"{service_name}: {response.message}")
            return response
        else:
            self.get_logger().error(f"Failed to call {service_name}")
            return None

    def next_as_state(self):
        """Advance to next AS state"""
        return self.call_service(self.next_as_state_client, "Next AS State")

    def cycle_ami_state(self):
        """Cycle AMI state"""
        return self.call_service(self.cycle_ami_state_client, "Cycle AMI State")

    def emergency_stop(self):
        """Trigger emergency stop"""
        return self.call_service(self.emergency_stop_client, "Emergency Stop")

    def set_driving_flag(self, flag):
        """Set driving flag"""
        msg = Bool()
        msg.data = flag
        self.driving_flag_pub.publish(msg)
        self.get_logger().info(f"Driving flag set to: {flag}")

    def set_mission_complete(self, flag):
        """Set mission complete flag"""
        msg = Bool()
        msg.data = flag
        self.mission_complete_pub.publish(msg)
        self.get_logger().info(f"Mission complete flag set to: {flag}")

def print_menu():
    """Print the control menu"""
    print("\n" + "="*50)
    print("VCU SIMULATOR CONTROLLER")
    print("="*50)
    print("1. Next AS State (OFF -> READY -> DRIVING -> FINISHED)")
    print("2. Cycle AMI State (mission selection)")
    print("3. Set Driving Flag TRUE")
    print("4. Set Driving Flag FALSE")
    print("5. Set Mission Complete TRUE")
    print("6. Set Mission Complete FALSE")
    print("7. Emergency Stop")
    print("8. Show this menu")
    print("9. Quit")
    print("="*50)

def main():
    rclpy.init()
    
    controller = VCUController()
    
    # Start ROS spinning in a separate thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(controller,), daemon=True)
    spin_thread.start()
    
    print("VCU Simulator Controller started!")
    print("This tool helps you control the simulated vehicle state")
    print_menu()
    
    # Typical workflow explanation
    print("\nTYPICAL WORKFLOW:")
    print("1. First, select an AMI state (option 2)")
    print("2. Then advance AS state to READY (option 1)")
    print("3. Set driving flag to TRUE (option 3)")
    print("4. Advance AS state to DRIVING (option 1)")
    print("5. Your autonomous system can now send commands!")
    print("6. Set mission complete when done (option 5)")
    print("7. Or use emergency stop if needed (option 7)")
    
    try:
        while True:
            try:
                choice = input("\nEnter your choice (1-9): ").strip()
                
                if choice == '1':
                    controller.next_as_state()
                elif choice == '2':
                    controller.cycle_ami_state()
                elif choice == '3':
                    controller.set_driving_flag(True)
                elif choice == '4':
                    controller.set_driving_flag(False)
                elif choice == '5':
                    controller.set_mission_complete(True)
                elif choice == '6':
                    controller.set_mission_complete(False)
                elif choice == '7':
                    controller.emergency_stop()
                elif choice == '8':
                    print_menu()
                elif choice == '9':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-9.")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
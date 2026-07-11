#!/usr/bin/python3
"""
Static B
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool, Int16
import time
from tf_helper.StatusPublisher import StatusPublisher
import numpy as np
from std_srvs.srv import Trigger
from ..helpers.intervalTimer import IntervalTimer
from ackermann_msgs.msg import AckermannDriveStamped



class StaticB(Node):
    """
    Static B
    -----------------------
    Attributes:
        started: bool
    -----------------------
    returns:
        None
    """

    def __init__(self) -> None:
        super().__init__('StaticB_Node')

        self.declare_parameters(
            namespace='',
            parameters=[
                ('/ackr', rclpy.Parameter.Type.STRING),
                ('/ros_can/ebs', rclpy.Parameter.Type.STRING),
                ('/finisher/is_finished', rclpy.Parameter.Type.STRING),
                ('/supervisor/driving_flag', rclpy.Parameter.Type.STRING),
                
                
                        
            ])
        self.drivingFlag = False
        self.status = StatusPublisher("/status/staticB", self)

    def drivingFlagCallback(self, msg: Bool) -> None:
        """
        Callback for the driving flag
        """
        self.get_logger().info("inside driving callback")
        self.drivingFlag = msg.data
        if self.drivingFlag:
            self.run()

    #@staticmethod
    def run(self) -> None:
        """
        Run Static B
        """
        self.get_logger().info("Starting Static B: Ramp to 50 RPM → EBS Stop")

        # Get topic names from parameters
        velTopic = self.get_parameter("/ackr").get_parameter_value().string_value
        isFinishedTopic = self.get_parameter("/finisher/is_finished").get_parameter_value().string_value
        ebsTopic = self.get_parameter("/ros_can/ebs").get_parameter_value().string_value

        # Setup publishers
        velPub = self.create_publisher(AckermannDriveStamped, velTopic, 10)
        finishPub = self.create_publisher(Bool, isFinishedTopic, 10)


        # Configuration
        target_velocity = 1.32  # 50 RPM in m/s (2*π*50*0.253/60)
        ramp_time = 10.0         # Time to reach 50 RPM (seconds)
        hold_time = 10.0         # Time to hold at 50 RPM before EBS (seconds)

        # --- PHASE 1: Ramp up to 50 RPM smoothly 
        start_time = time.time()
        msg = AckermannDriveStamped()
        msg.drive.speed = 0.0
        msg.drive.steering_angle = 0.0
        while time.time() - start_time < ramp_time:
            elapsed = time.time() - start_time
            msg.drive.speed = (elapsed / ramp_time) * target_velocity
            velPub.publish(msg)
            #self.get_logger().info(f"Ramping up: {velocity:.2f} m/s")
            time.sleep(0.1)

        # --- PHASE 2: Hold at 50 RPM 
        msg.drive.speed = target_velocity
        velPub.publish(msg)
        self.get_logger().info(f"Holding at 50 RPM ({target_velocity:.2f} m/s)")
        time.sleep(hold_time)

        # Publishing state as "finished" while velocity is still at 50 RPM triggering EBS
        finishPub.publish(Bool(data=True))
        self.get_logger().info("Publishing finish signal")


        ###########################
        #CALLING EBS SERVICE HERE
        ###########################
        
        client = self.create_client(Trigger, ebsTopic)
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error(f"EBS service {ebsTopic} not available!")
            return

        request = Trigger.Request()
        self.get_logger().warn("Triggering EBS...")

        future = client.call_async(request)
        future.add_done_callback(self.ebs_response_callback)  # <-- key fix here

        msg.drive.speed = 0.0
        velPub.publish(msg)  
        finishPub.publish(Bool(data=True))
        self.get_logger().info("Publishing finish signal")
        self.get_logger().info("finished")

    def ebs_response_callback(self, future):
        try:
            result = future.result()
            if result.success:
                self.get_logger().info(f"EBS activated successfully: {result.message}")
            else:
                self.get_logger().error(f"EBS activation failed: {result.message}")
        except Exception as e:
            self.get_logger().error(f"EBS service call failed: {e}")  

    

def main() -> None:
    """
    Static B, publish stuff
    """

    rclpy.init()

    staticB = StaticB()
    staticB.status.starting()
    staticB.status.ready()

    heartbeartRateThread = IntervalTimer(0.1, staticB.status.running)
    #drivingFlagTopic = staticB.get_parameter("/supervisor/driving_flag").get_parameter_value().string_value
    drivingFlagTopic = "/supervisor/driving_flag"
    
    staticB.create_subscription(Bool, drivingFlagTopic, staticB.drivingFlagCallback, 10)


    rate = staticB.create_rate(10)
    heartbeartRateThread.start()
    rclpy.spin(staticB)

    while rclpy.ok():
        if staticB.drivingFlag:
            staticB.run()
            break
        
    rate.sleep()
        
    rclpy.shutdown() 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
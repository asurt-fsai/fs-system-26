#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool, Int16
from std_srvs.srv import Trigger
from tf_helper.StatusPublisher import StatusPublisher
from ackermann_msgs.msg import AckermannDriveStamped
from ..helpers.intervalTimer import IntervalTimer

class AutonomousDemo(Node):
    """
    Autonomous Demo
    -----------------------
    Attributes:
        started: bool
    -----------------------
    returns:
        None
    """

    def __init__(self) -> None:
        super().__init__("Auto_demo_node")
        self.drivingFlag = False
        self.status = StatusPublisher("/status/autonomous_demo", self)


        self.declare_parameter('maxSteer',rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter('/ackr', rclpy.Parameter.Type.STRING)
        self.declare_parameter('/finisher/is_finished', rclpy.Parameter.Type.STRING)
        self.declare_parameter("/supervisor/driving_flag", rclpy.Parameter.Type.STRING)
        self.declare_parameter('/ros_can/ebs', '/ros_can/ebs') 
        self.create_timer(0.01, lambda:self.status.running())

        
    def drivingFlagCallback(self, msg: Bool) -> None:
        """
        Callback for the driving flag
        """
        self.drivingFlag = msg.data
        if self.drivingFlag:
            self.run()
         


    def run(self) -> None:
        """
        Run Autonomous Demo
        """
        self.get_logger().info("Starting Autonomous Demo")

        
        controlCmdTopic = self.get_parameter("/ackr").get_parameter_value().string_value
        isFinishedTopic = self.get_parameter("/finisher/is_finished").get_parameter_value().string_value
        maxSteerDouble = self.get_parameter("maxSteer").get_parameter_value().double_value
        ebsTopic = self.get_parameter('/ros_can/ebs').get_parameter_value().string_value
        maxSteer = Float32()
        maxSteer = maxSteerDouble

        controlCmdPub = self.create_publisher(AckermannDriveStamped, controlCmdTopic, 10)
        finishPub = self.create_publisher(Bool, isFinishedTopic, 10)
        distPub = self.create_publisher(Float32, '/distance', 10)


    
        time.sleep(4)

        msg = AckermannDriveStamped()
        msg.drive.speed = 0.0
        msg.drive.steering_angle = -maxSteer
        controlCmdPub.publish(msg)
        time.sleep(3)

        msg.drive.steering_angle = maxSteer 
        controlCmdPub.publish(msg)
        time.sleep(3)

        msg.drive.steering_angle = 0.0
        controlCmdPub.publish(msg)
        time.sleep(3)

        timeStart = time.time()
        distance = 0
        initial_velocity = 0  
        acceleration = 1  
        deceleration = -1

        while distance < 2: # 10m is the target distance
            currentTime = time.time()
            timeElapsed = currentTime - timeStart 

            velocity = initial_velocity + acceleration * timeElapsed
            msg.drive.speed = velocity
            msg.drive.steering_angle = 0.0
            controlCmdPub.publish(msg)

            
            distance = initial_velocity * timeElapsed + 0.5 * acceleration * (timeElapsed**2)
            dist = Float32(data=distance)
            distPub.publish(dist)
            time.sleep(0.01)

        self.get_logger().info("distance: " + str(distance))
        self.get_logger().info("vel: " + str(velocity * 3.6))

        distance = 2
        timeStart = time.time()
        initial_velocity = velocity 
        while  distance < 4 and velocity > 0:
            currentTime = time.time()
            timeElapsed = currentTime - timeStart 

            velocity = initial_velocity + deceleration * timeElapsed
            msg.drive.speed = velocity
            msg.drive.steering_angle = 0.0
            controlCmdPub.publish(msg)
            
            distance = 2 + velocity * timeElapsed + 0.5 * abs(deceleration) * (timeElapsed**2)
            dist = Float32(data=distance)
            distPub.publish(dist)

            time.sleep(0.01)



        msg.drive.speed = 0.0
        msg.drive.steering_angle = 0.0
        controlCmdPub.publish(msg)

        self.get_logger().info("distance: " + str(distance))
        self.get_logger().info("vel: " + str(velocity * 3.6))
        time.sleep(2)

        timeStart = time.time()
        initial_velocity = 0
        while distance < 8:
            currentTime = time.time()
            timeElapsed = currentTime - timeStart 

            velocity = initial_velocity + acceleration * timeElapsed
            msg.drive.speed = velocity
            msg.drive.steering_angle = 0.0
            controlCmdPub.publish(msg)

            
            distance = 4 + initial_velocity * timeElapsed + 0.5 * acceleration * (timeElapsed**2)
            dist = Float32(data=distance)
            distPub.publish(dist)
            time.sleep(0.01)
            if distance >= 8 : break

        self.get_logger().info(f"current velocity is: {velocity}")    


        ###########################
        #CALLING EBS SERVICE HERE
        ###########################
        
        # --- Trigger EBS ---

        client = self.create_client(Trigger, ebsTopic)
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error(f"EBS service {ebsTopic} not available!")
            return

        request = Trigger.Request()
        self.get_logger().warn("Triggering EBS...")

        future = client.call_async(request)
        future.add_done_callback(self.ebs_response_callback)  # <-- key fix here

        # Do NOT spin here!

        # --- EBS Stops the car ---
        msg.drive.speed = 0.0
        controlCmdPub.publish(msg)

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




    def callback(self,request:Trigger.Request,response:Trigger.Response):
        response.success=True
        response.message = "hey there"
        self.get_logger().info("sending back response from logger:"+ str(response.success))

        print("sending back response:",response.success)
        return response

def main() -> None:
    """
    Autonomous Demo, publish stuff
    """

    rclpy.init()
    autonomousDemo = AutonomousDemo()

    autonomousDemo.status.starting()
    autonomousDemo.status.ready()

    heartbeartRateThread = IntervalTimer(0.1, autonomousDemo.status.running)

   
    drivingFlagTopic = "/supervisor/driving_flag"
    #drivingFlagTopic = autonomousDemo.get_parameter("/supervisor/driving_flag").get_parameter_value().string_value
    autonomousDemo.create_subscription(Bool, drivingFlagTopic, autonomousDemo.drivingFlagCallback, 10)

    rate = autonomousDemo.create_rate(10)
    heartbeartRateThread.start()

    rclpy.spin(autonomousDemo)


    while rclpy.ok():

        
        if autonomousDemo.drivingFlag:
            autonomousDemo.run()
            break
    
    rate.sleep()

    rclpy.shutdown()    

        

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()
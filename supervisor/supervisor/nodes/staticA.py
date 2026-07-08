#!/usr/bin/python3
"""
Static A
"""
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool, Int16
from tf_helper.StatusPublisher import StatusPublisher
from ..helpers.intervalTimer import IntervalTimer
from ackermann_msgs.msg import AckermannDriveStamped
import threading

#from sleep import sleepForSecondsAndSendHeartBeat
import numpy as np


class StaticA(Node):
    """
    Static A
    -----------------------
    Attributes:
        started: bool
    -----------------------
    returns:
        None
    """

    """
    can states:
    uint16 AS_OFF=0
    uint16 AS_READY=1
    uint16 AS_DRIVING=2
    uint16 AS_EMERGENCY_BRAKE=3
    uint16 AS_FINISHED=4

    """

    def __init__(self) -> None:
        super().__init__("StaticA_Node")
        self.declare_parameter('maxSteer',rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter('/ackr', rclpy.Parameter.Type.STRING)
        self.declare_parameter("/finisher/is_finished", rclpy.Parameter.Type.STRING)
        self.declare_parameter('/state', rclpy.Parameter.Type.STRING)
        self.declare_parameter('/supervisor/driving_flag', rclpy.Parameter.Type.STRING)
        self.get_logger().info("Static A Node Started")
        # self.started = True
        self.drivingFlag = False
        self.status = StatusPublisher("/status/staticA", self)

    def drivingFlagCallback(self, msg: Bool):
        """
        Callback for the driving flag
        """
        self.drivingFlag = msg.data
        self.get_logger().info(str(msg.data))
        if self.drivingFlag == True:
            self.run()

    def run(self) -> None:
        """
        Run Static A
        """
        self.get_logger().info("Starting Static A")
        controlCmdTopic = self.get_parameter("/ackr").get_parameter_value().string_value
        isFinishedTopic =  self.get_parameter("/finisher/is_finished").get_parameter_value().string_value


        controlCmdPub = self.create_publisher(AckermannDriveStamped, controlCmdTopic, 10)
        finishPub = self.create_publisher(Bool, isFinishedTopic, 10)

        maxSteerDouble =self.get_parameter("maxSteer").get_parameter_value().double_value

        maxSteer = Float32()
        maxSteer = maxSteerDouble
 
        msg = AckermannDriveStamped()
        msg.drive.speed = 0.0
        msg.drive.steering_angle = -maxSteer
        controlCmdPub.publish(msg)
        time.sleep(5)

        msg.drive.steering_angle = maxSteer
        controlCmdPub.publish(msg)
        time.sleep(5)

        msg.drive.steering_angle = 0.0
        controlCmdPub.publish(msg)
        time.sleep(5)


        timeStart = time.time()

        while time.time() - timeStart < 10:
            
            msg.drive.speed =2 * np.pi * 200 * 0.253 / 60 * 0.1 * (time.time() - timeStart)
            controlCmdPub.publish(msg)
            time.sleep(0.1)


        timeStart = 5
        while timeStart > 0:
            
            msg.drive.speed = 2 * np.pi * 200 * 0.253 / 60 * 0.1 * (2*timeStart)
            msg.drive.steering_angle = 0.0
            controlCmdPub.publish(msg)
            timeStart = timeStart -0.1
            time.sleep(0.1)

        msg.drive.speed = 0.0
        msg.drive.steering_angle = 0.0
        controlCmdPub.publish(msg)
        time.sleep(1)

        msg = Bool()
        msg.data = True
        finishPub.publish(msg)
       
        
    



def main() -> None:
    """
    Static A, publish stuff
    """

    rclpy.init()
  
    staticA = StaticA()
    staticA.status.starting()
    staticA.status.ready()

#ros2 topic pub -1 /supervisor/driving_flag std_msgs/msg/Bool "{data: true}"

    heartbeartRateThread = IntervalTimer(0.1, staticA.status.running)
    #drivingFlagTopic = staticA.get_parameter("/supervisor/driving_flag").get_parameter_value().string_value #law system sha8al fel mosab2a
    #drivingFlagTopic = "/supervisor/driving_flag" #law manual publishing 3al topic
    drivingFlagTopic = "state_machine/driving_flag"
    staticA.create_subscription(Bool, drivingFlagTopic, staticA.drivingFlagCallback, 10)
    staticA.get_logger().info("Static A Node Started")
    rate = staticA.create_rate(10)
    heartbeartRateThread.start()
    rclpy.spin(staticA)

    while rclpy.ok():
        if staticA.drivingFlag:
            staticA.run()
            break

    rate.sleep()

    rclpy.shutdown()    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
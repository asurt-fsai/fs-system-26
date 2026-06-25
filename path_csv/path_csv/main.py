import numpy as np
import csv 
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import rclpy
import rclpy.time

class CSVtopath(Node):
    def __init__(self):
        super().__init__('path')
        qos_profile = QoSProfile(depth=10)
        qos_profile.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.publisher_=self.create_publisher(Path,'path',qos_profile)
        arr = np.genfromtxt('/home/fsai/Desktop/IPG_2025Modified/formula-carmaker-fs_2024Modified/formula-carmaker-fs_2024/FCM_Projects/FS_autonomous/ros/ros2_ws/src/path_csv/ipg_track_newww.csv', delimiter=',' )
        timer = self.create_timer(0.1, self.publishPath)
        self.pathMsg = Path()
        self.pathMsg.header.frame_id="map"
        self.rate = 10

        for idx,point in enumerate(arr):
            if (idx % self.rate==0):
                pose = PoseStamped()   
                pose.header.frame_id = "map"
                pose.pose.position.x = point[0]
                pose.pose.position.y = point[1]
                self.pathMsg.poses.append(pose)


    def publishPath(self):
        self.publisher_.publish(self.pathMsg)

def main(args=None):
    rclpy.init(args=args)
    csvtopath =CSVtopath()
    csv_file='/home/fsai/wapoints_ws/src/path_csv/track.csv'
    rclpy.spin(csvtopath)
    csvtopath.destroy_node()
    rclpy.shutdown()

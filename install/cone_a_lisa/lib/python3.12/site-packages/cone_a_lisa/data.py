import os
import csv
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray

class ObjectListSaver(Node):
    def __init__(self):
        super().__init__('objectlist_saver')

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.filename = os.path.join(desktop_path, "objectlist_data.csv")
        self.get_logger().info(f"Saving CSV file to: {self.filename}")

        self.csv_file = open(self.filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        # Write CSV header
        self.csv_writer.writerow(['timestamp', 'cone_id', 'x', 'y', 'z', 'r', 'g', 'b', 'a'])

        self.subscription = self.create_subscription(
            MarkerArray,
            '/carmaker/ObjectList',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        timestamp = self.get_clock().now().to_msg().sec  # seconds since epoch

        for idx, marker in enumerate(msg.markers):
            pos = marker.pose.position
            col = marker.color
            self.csv_writer.writerow([
                timestamp,
                idx,
                pos.x, pos.y, pos.z,
                col.r, col.g, col.b, col.a
            ])
        self.csv_file.flush()  # flush after each callback to save data immediately

def main(args=None):
    rclpy.init(args=args)
    node = ObjectListSaver()
    rclpy.spin(node)
    node.csv_file.close()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

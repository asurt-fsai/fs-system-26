import rclpy
from rclpy.node import Node
from std_msgs.msg import String  # or any other message type you need
from asurt_msgs.msg import NodeStatus

class subb(Node):
    def __init__(self,modules):
        super().__init__('subscriber_node')
        
        self.modules = modules
        
        
        self.create_subscriptions(self.modules)
        # prevent unused variable warning

    def create_subscriptions(self, modules):
        # for module in modules:
        # self.get_logger().info(f"Creating subscription sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssfor {modules}")
        
        self.get_logger().info(f"MODULESSSSSSSSSSS: {modules[0].hasHeartbeat}")
        self.create_subscription(
            NodeStatus,
            "/status/simple_pure_pursuit",
            self.heartbeatCallback,
            10
        )
# 
    def heartbeatCallback(self, msg: NodeStatus) -> None:
        """
        Callback for the heartbeat topic

        Parameters
        ----------
        msg : NodeStatus
            The message from the heartbeat topic
        """
        self.get_logger().info("Heartbeat received")
        self.get_logger().info("Heartbeat receivinggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggd")
        # self.get_logger().info(f"Heartbeat received: {msg.status}")
        # module.states = msg.status
        # module.heartcount += 1.0   
        # self.get_logger().info(f"module states: {module.states}")     




def main(args=None):
    rclpy.init(args=args)
    node = subb()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

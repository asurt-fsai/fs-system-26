import rclpy
from rclpy.node import Node
from std_msgs.msg import String  # or any other message type you need
from asurt_msgs.msg import NodeStatus

class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')

        # prevent unused variable warning

    def create_subscription(self, modules):
        for module in modules:
           
            subscription = self.create_subscription(
                NodeStatus,
                module.hasHeartbeat,
                lambda msg: self.heartbeatCallback(msg, module),
                10
            )

    def heartbeatCallback(self, msg: NodeStatus, module) -> None:
        """
        Callback for the heartbeat topic

        Parameters
        ----------
        msg : NodeStatus
            The message from the heartbeat topic
        """
        self.get_logger().info("Heartbeat received")
        self.get_logger().info(f"Heartbeat received: {msg.status}")
        module.states = msg.status
        module.heartcount += 1.0        




def main(args=None):
    rclpy.init(args=args)
    node = SubscriberNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

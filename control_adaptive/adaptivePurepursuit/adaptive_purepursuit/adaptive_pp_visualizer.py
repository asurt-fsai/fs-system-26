import rclpy
from rclpy.node import Node
import math
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import PointStamped, Point, TransformStamped
from std_msgs.msg import Float32
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import TransformBroadcaster

class AdaptivePPVisualizer(Node):
    def __init__(self):
        super().__init__('adaptive_pp_visualizer')
        
        self.declare_parameter("car_length", 2.8)
        self.declare_parameter("car_width", 1.4)
        self.declare_parameter("wheelbase", 1.575)
        
        self.car_length = self.get_parameter("car_length").value
        self.car_width = self.get_parameter("car_width").value
        self.wheelbase = self.get_parameter("wheelbase").value
        
        self.odom = None
        self.drive = None
        self.lookahead_pt = None
        self.lookahead_dist = None
        
        self.sub_odom = self.create_subscription(Odometry, '/carmaker/Odometry', self.odom_cb, 10)
        self.sub_drive = self.create_subscription(AckermannDriveStamped, '/drive', self.drive_cb, 10)
        self.sub_la_pt = self.create_subscription(PointStamped, '/purepursuit/lookahead_point', self.la_pt_cb, 10)
        self.sub_la_dist = self.create_subscription(Float32, '/purepursuit/lookahead_distance', self.la_dist_cb, 10)
        
        self.marker_pub = self.create_publisher(MarkerArray, '/purepursuit/visualization', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.timer = self.create_timer(0.05, self.timer_cb) # 20 Hz
        self.get_logger().info("Adaptive Pure Pursuit Visualizer started.")
        
    def odom_cb(self, msg):
        self.odom = msg
        
    def drive_cb(self, msg):
        self.drive = msg
        
    def la_pt_cb(self, msg):
        self.lookahead_pt = msg
        
    def la_dist_cb(self, msg):
        self.lookahead_dist = msg
        
    def timer_cb(self):
        if self.odom is None:
            return
            
        ma = MarkerArray()
        
        # TF Broadcast
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.odom.pose.pose.position.x
        t.transform.translation.y = self.odom.pose.pose.position.y
        t.transform.translation.z = 0.0
        t.transform.rotation = self.odom.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)
        
        # 1. Car Footprint (base_link frame)
        m_car = Marker()
        m_car.header.frame_id = 'base_link'
        m_car.header.stamp = t.header.stamp
        m_car.ns = 'car'
        m_car.id = 0
        m_car.type = Marker.LINE_LIST
        m_car.action = Marker.ADD
        m_car.scale.x = 0.04
        m_car.color.r = 0.0
        m_car.color.g = 0.85
        m_car.color.b = 1.0
        m_car.color.a = 1.0
        
        rear_overhang = (self.car_length - self.wheelbase) * 0.35
        front_overhang = self.car_length - self.wheelbase - rear_overhang
        x_rear = -rear_overhang
        x_front = self.wheelbase + front_overhang
        hw = self.car_width / 2.0
        
        corners = [
            (x_rear, -hw), (x_front, -hw),
            (x_front, -hw), (x_front, hw),
            (x_front, hw), (x_rear, hw),
            (x_rear, hw), (x_rear, -hw)
        ]
        for c1, c2 in zip(corners[0::2], corners[1::2]):
            p1 = Point(); p1.x = c1[0]; p1.y = c1[1]; p1.z = 0.15
            p2 = Point(); p2.x = c2[0]; p2.y = c2[1]; p2.z = 0.15
            m_car.points.extend([p1, p2])
            
        ma.markers.append(m_car)
        
        # 2. Lookahead Point & Line (map frame)
        if self.lookahead_pt is not None:
            # Sphere
            m_pt = Marker()
            m_pt.header.frame_id = 'base_link'
            m_pt.header.stamp = t.header.stamp
            m_pt.ns = 'lookahead_pt'
            m_pt.id = 1
            m_pt.type = Marker.SPHERE
            m_pt.action = Marker.ADD
            m_pt.scale.x = 0.4
            m_pt.scale.y = 0.4
            m_pt.scale.z = 0.4
            m_pt.color.r = 1.0
            m_pt.color.g = 0.0
            m_pt.color.b = 0.0
            m_pt.color.a = 1.0
            m_pt.pose.position.x = self.lookahead_pt.point.x
            m_pt.pose.position.y = self.lookahead_pt.point.y
            m_pt.pose.position.z = 0.2
            ma.markers.append(m_pt)
            
            # Line
            m_line = Marker()
            m_line.header.frame_id = 'base_link'
            m_line.header.stamp = t.header.stamp
            m_line.ns = 'lookahead_line'
            m_line.id = 2
            m_line.type = Marker.LINE_STRIP
            m_line.action = Marker.ADD
            m_line.scale.x = 0.05
            m_line.color.r = 1.0
            m_line.color.g = 1.0
            m_line.color.b = 0.0
            m_line.color.a = 1.0
            p_car = Point()
            #p_car.x = self.odom.pose.pose.position.x
            #p_car.y = self.odom.pose.pose.position.y
            p_car.x = 0.0
            p_car.y = 0.0
            p_car.z = 0.2
            p_la = Point()
            p_la.x = self.lookahead_pt.point.x
            p_la.y = self.lookahead_pt.point.y
            p_la.z = 0.2
            m_line.points = [p_car, p_la]
            ma.markers.append(m_line)

            # Forward red line
            m_fwd = Marker()
            m_fwd.header.frame_id = 'base_link'
            m_fwd.header.stamp = t.header.stamp
            m_fwd.ns = 'forward_line'
            m_fwd.id = 6
            m_fwd.type = Marker.LINE_STRIP
            m_fwd.action = Marker.ADD
            m_fwd.scale.x = 0.05
            m_fwd.color.r = 1.0
            m_fwd.color.g = 0.0
            m_fwd.color.b = 0.0
            m_fwd.color.a = 1.0
            p_fwd_start = Point()
            p_fwd_start.x = 0.0
            p_fwd_start.y = 0.0
            p_fwd_start.z = 0.2
            p_fwd_end = Point()
            p_fwd_end.x = 5.0  # 5 meters forward
            p_fwd_end.y = 0.0
            p_fwd_end.z = 0.2
            m_fwd.points = [p_fwd_start, p_fwd_end]
            ma.markers.append(m_fwd)
            
        # 3. Lookahead Distance Circle (base_link frame)
        if self.lookahead_dist is not None:
            m_dist = Marker()
            m_dist.header.frame_id = 'base_link'
            m_dist.header.stamp = t.header.stamp
            m_dist.ns = 'lookahead_dist'
            m_dist.id = 3
            m_dist.type = Marker.LINE_STRIP
            m_dist.action = Marker.ADD
            m_dist.scale.x = 0.03
            m_dist.color.r = 0.0
            m_dist.color.g = 1.0
            m_dist.color.b = 0.0
            m_dist.color.a = 0.7
            radius = float(self.lookahead_dist.data)
            for i in range(37):
                angle = i * 10.0 * math.pi / 180.0
                p = Point()
                p.x = radius * math.cos(angle)
                p.y = radius * math.sin(angle)
                p.z = 0.1
                m_dist.points.append(p)
            ma.markers.append(m_dist)
            
        # 4. Velocity and Steering (from Drive and Odom)
        if self.drive is not None:
            m_steer = Marker()
            m_steer.header.frame_id = 'base_link'
            m_steer.header.stamp = t.header.stamp
            m_steer.ns = 'steering'
            m_steer.id = 4
            m_steer.type = Marker.ARROW
            m_steer.action = Marker.ADD
            m_steer.scale.x = 0.1
            m_steer.scale.y = 0.2
            m_steer.scale.z = 0.2
            m_steer.color.r = 1.0
            m_steer.color.g = 0.5
            m_steer.color.b = 0.0
            m_steer.color.a = 1.0
            
            p_start = Point()
            p_start.x = self.wheelbase
            p_start.y = 0.0
            p_start.z = 0.3
            
            steer_angle = self.drive.drive.steering_angle
            p_end = Point()
            p_end.x = self.wheelbase + 1.0 * math.cos(steer_angle)
            p_end.y = 1.0 * math.sin(steer_angle)
            p_end.z = 0.3
            m_steer.points = [p_start, p_end]
            ma.markers.append(m_steer)
            
            # Velocity arrow (map frame)
            m_vel = Marker()
            m_vel.header.frame_id = 'map'
            m_vel.header.stamp = t.header.stamp
            m_vel.ns = 'velocity'
            m_vel.id = 5
            m_vel.type = Marker.ARROW
            m_vel.action = Marker.ADD
            m_vel.scale.x = 0.1
            m_vel.scale.y = 0.2
            m_vel.scale.z = 0.2
            m_vel.color.r = 0.0
            m_vel.color.g = 1.0
            m_vel.color.b = 1.0
            m_vel.color.a = 1.0
            
            v = self.odom.twist.twist.linear.x
            arrow_len = max(1.0, min(v * 0.5, 4.0)) # scale with speed
            
            q = self.odom.pose.pose.orientation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            
            p_vstart = Point()
            p_vstart.x = self.odom.pose.pose.position.x
            p_vstart.y = self.odom.pose.pose.position.y
            p_vstart.z = 0.2
            
            p_vend = Point()
            p_vend.x = p_vstart.x + arrow_len * math.cos(yaw)
            p_vend.y = p_vstart.y + arrow_len * math.sin(yaw)
            p_vend.z = 0.2
            
            m_vel.points = [p_vstart, p_vend]
            ma.markers.append(m_vel)
            
        self.marker_pub.publish(ma)

def main(args=None):
    rclpy.init(args=args)
    node = AdaptivePPVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

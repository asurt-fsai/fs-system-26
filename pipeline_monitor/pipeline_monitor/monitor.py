import rclpy
from rclpy.node import Node
import collections

from zed_msgs.msg import ObjectsStamped
from asurt_msgs.msg import LandmarkArray as PerceptionLandmarks
from cone_mapping.msg import LandmarkArray as GlobalCones
from nav_msgs.msg import Path
from ackermann_msgs.msg import AckermannDriveStamped

class StageTracker:
    def __init__(self, initial_time_ns):
        self.t0 = initial_time_ns
        self.perception_time = None
        self.mapping_time = None
        self.planning_time = None
        self.control_time = None
        self.is_printed = False  # Track whether this frame card has already processed down to control

class PipelineSequenceMonitor(Node):
    def __init__(self):
        super().__init__('pipeline_sequence_monitor')
        
        self.history = collections.OrderedDict()
        self.max_history_size = 300
        
        # Subscriptions
        self.create_subscription(ObjectsStamped, '/zed/zed_node/obj_det/objects', self.cam_cb, 10)
        self.create_subscription(PerceptionLandmarks, '/perception_landmarks', self.perception_cb, 10)
        self.create_subscription(GlobalCones, '/map/global_cones', self.mapping_cb, 10)
        self.create_subscription(Path, '/path', self.planning_cb, 10)
        self.create_subscription(AckermannDriveStamped, '/ackr', self.control_cb, 10)
        
        self.get_logger().info("Sequence Monitor updated with duplicate protection and crash safety filters.")

    def get_stamp_ns(self, header):
        return (header.stamp.sec * 10**9) + header.stamp.nanosec

    def get_or_create_tracker(self, stamp_ns, skip_completed=False):
        if stamp_ns in self.history:
            if not (skip_completed and self.history[stamp_ns].is_printed):
                return self.history[stamp_ns]
            
        # Match within a 500ms window to absorb the 400ms processing bottleneck
        MAX_ALLOWABLE_DRIFT_NS = 200_000_000 
        closest_stamp = None
        smallest_diff = MAX_ALLOWABLE_DRIFT_NS

        for existing_stamp, tracker in self.history.items():
            if skip_completed and tracker.is_printed:
                continue  # Skip cards that already completed the full stack loop
                
            diff = abs(existing_stamp - stamp_ns)
            if diff < smallest_diff:
                smallest_diff = diff
                closest_stamp = existing_stamp

        if closest_stamp is not None:
            return self.history[closest_stamp]

        if len(self.history) > self.max_history_size:
            self.history.popitem(last=False)
        
        self.history[stamp_ns] = StageTracker(stamp_ns)
        return self.history[stamp_ns]

    # ---- CALLBACKS ----
    def cam_cb(self, msg):
        stamp_ns = self.get_stamp_ns(msg.header)
        self.get_or_create_tracker(stamp_ns)

    def perception_cb(self, msg):
        now_ns = self.get_clock().now().nanoseconds
        stamp_ns = self.get_stamp_ns(msg.header)
        tracker = self.get_or_create_tracker(stamp_ns)
        tracker.perception_time = now_ns

    def mapping_cb(self, msg):
        now_ns = self.get_clock().now().nanoseconds
        stamp_ns = self.get_stamp_ns(msg.header)
        tracker = self.get_or_create_tracker(stamp_ns)
        tracker.mapping_time = now_ns

    def planning_cb(self, msg):
        now_ns = self.get_clock().now().nanoseconds
        stamp_ns = self.get_stamp_ns(msg.header)
        tracker = self.get_or_create_tracker(stamp_ns)
        tracker.planning_time = now_ns

    def control_cb(self, msg):
        now_ns = self.get_clock().now().nanoseconds
        stamp_ns = self.get_stamp_ns(msg.header)
        # Skip already completed cards to prevent identical duplicate frame metrics prints
        tracker = self.get_or_create_tracker(stamp_ns, skip_completed=True)
        
        tracker.control_time = now_ns
        self.print_sequence_breakdown(stamp_ns, tracker)

    # ---- PRINT ENGINE ----
    def print_sequence_breakdown(self, seq_id, tracker):
        # Enforce existence of core nodes before evaluating metrics
        if not tracker.perception_time or not tracker.planning_time:
            return

        # Mark it immediately to prevent cross-callback duplicate executions
        tracker.is_printed = True

        # Steps Duration
        p_dur = abs((tracker.perception_time - tracker.t0)) / 1e6 if tracker.perception_time else 0.0
        m_dur = abs((tracker.mapping_time - tracker.perception_time)) / 1e6 if tracker.mapping_time else 0.0
        pl_dur = abs((tracker.planning_time - tracker.perception_time)) / 1e6 if tracker.planning_time else 0.0
        c_dur = abs((tracker.control_time - tracker.planning_time)) / 1e6 if tracker.control_time else 0.0
        total_e2e = abs((tracker.control_time - tracker.t0)) / 1e6 if tracker.control_time else 0.0
        
        # Filter out extreme race condition out-of-order anomalies if timestamps cross drops
        if pl_dur < 0 or c_dur < 0:
            return 

        log_str = (
            f"\nSequence ID [{seq_id}]:\n"
            f" ├── 1. Perception Step: {p_dur:.2f} ms (AI Process Time)\n"
            f" ├── 2. Mapping Step:    {m_dur:.2f} ms\n"
            f" ├── 3. Planning Step:   {pl_dur:.2f} ms\n"
            f" └── 4. Control Step:    {c_dur:.2f} ms\n"
            f" ═════════════════════════════════\n"
            f" TOTAL EXECUTION TIME:   {total_e2e:.2f} ms\n"
        )
        self.get_logger().info(log_str)

def main(args=None):
    rclpy.init(args=args)
    node = PipelineSequenceMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import os

class PipelineProfiler(Node):
    def __init__(self):
        super().__init__('pipeline_profiler')
        
        self.times = {
            'Perception': 0.0,
            'Mapping': 0.0,
            'Path Planning': 0.0,
            'Control': 0.0
        }
        
        # Subscriptions to the profiling topics
        self.create_subscription(Float64, '/diagnostics/comp_time/perception', lambda msg: self.update_time('Perception', msg.data), 10)
        self.create_subscription(Float64, '/diagnostics/comp_time/slam', lambda msg: self.update_time('Mapping', msg.data), 10)
        self.create_subscription(Float64, '/diagnostics/comp_time/global_planning_dl', lambda msg: self.update_time('Path Planning', msg.data), 10)
        self.create_subscription(Float64, '/diagnostics/comp_time/control', lambda msg: self.update_time('Control', msg.data), 10)
        
        # Timer to refresh terminal UI at 10Hz
        self.create_timer(0.1, self.draw_dashboard)

    def update_time(self, module, val):
        self.times[module] = val

    def draw_dashboard(self):
        # Clear screen for a smooth, static update effect
        os.system('clear')
        
        total_comp = sum(self.times.values())
        
        print("\033[1;36m" + "="*50)
        print("    PIPELINE COMPUTATION PROFILE MONITOR (ms)    ")
        print("="*50 + "\033[0m")
        
        for module, comp_time in self.times.items():
            # Color code based on speed (Green < 15ms, Yellow < 40ms, Red >= 40ms)
            if comp_time < 15.0:
                color = "\033[32m" # Green
            elif comp_time < 40.0:
                color = "\033[33m" # Yellow
            else:
                color = "\033[31m" # Red
                
            bar = "█" * int(min(comp_time, 40) / 2)
            print(f" {module:<15} : {color}{comp_time:6.2f} ms {bar:<20}\033[0m")
            
        print("\033[1;36m" + "-"*50)
        print(f" Total CPU Budget  :  {total_comp:.2f} ms")
        print("="*50 + "\033[0m")

def main(args=None):
    rclpy.init(args=args)
    node = PipelineProfiler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

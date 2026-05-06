import rclpy
from rclpy.node import Node
from asurt_msgs.msg import Event
#from jtop import jtop
import json
import psutil


class SystemHealthNode(Node):
    def __init__(self):
        super().__init__('system_health_node')

        # Parameters for process lists
        self.declare_parameter('cpu_process_names')
        self.declare_parameter('gpu_process_names')
        
        # Overall thresholds
        self.declare_parameter('overall_cpu_threshold', 80.0)
        self.declare_parameter('overall_gpu_threshold', 300.0)
        self.declare_parameter('overall_power_max_threshold', 30.0)
        self.declare_parameter('overall_power_min_threshold', 10.0)
        self.declare_parameter('overall_temperature_threshold', 30.0)
        
        # Per-process threshold overrides (optional)
        self.declare_parameter('process_thresholds', '{}')

        self.cpu_process_names = self.get_parameter(
            'cpu_process_names'
        ).get_parameter_value().string_array_value
        
        self.gpu_process_names = self.get_parameter(
            'gpu_process_names'
        ).get_parameter_value().string_array_value

        self.overall_cpu_threshold = self.get_parameter('overall_cpu_threshold').value
        self.overall_gpu_threshold = self.get_parameter('overall_gpu_threshold').value
        self.overall_power_max_threshold = self.get_parameter('overall_power_max_threshold').value
        self.overall_power_min_threshold = self.get_parameter('overall_power_min_threshold').value
        self.overall_temperature_threshold = self.get_parameter('overall_temperature_threshold').value
        
        # Parse per-process thresholds
        process_thresholds_json = self.get_parameter('process_thresholds').value
        try:
            self.process_thresholds = json.loads(process_thresholds_json)
        except json.JSONDecodeError:
            self.get_logger().warn(
                f"Invalid JSON for process_thresholds: {process_thresholds_json}. Using defaults."
            )
            self.process_thresholds = {}

        self.pub = self.create_publisher(Event, '/logging/events', 10)
        self.timer = self.create_timer(1.0, self.check_processes)
        self.timer2 = self.create_timer(1.0, self.check_overall_health)
        self.CPU_COUNT = psutil.cpu_count()
        # self.jetson = jtop()
        # self.jetson.start()

        # Track active alerts per process: {(process_name, pid): {alert_type: is_active}}
        self.active_alerts = {}
        
        # Track overall system alerts
        self.overall_alerts = {}

        self.get_logger().info(f"Monitoring CPU processes: {self.cpu_process_names}")
        self.get_logger().info(f"Monitoring GPU processes: {self.gpu_process_names}")
        self.get_logger().info(f"Overall thresholds - CPU: {self.overall_cpu_threshold}%, GPU: {self.overall_gpu_threshold}MB, Max Power: {self.overall_power_max_threshold}W, Min Power: {self.overall_power_min_threshold}W")
        if self.process_thresholds:
            self.get_logger().info(f"Custom process thresholds: {self.process_thresholds}")

    def get_threshold(self, process_name, threshold_type):
        """
        Get threshold for a specific process and type.
        
        Args:
            process_name: Name of the process
            threshold_type: 'cpu', 'gpu', or 'mem'
        
        Returns:
            Threshold value (float) or None if not applicable
        """
        # Check if process has custom thresholds
        if process_name in self.process_thresholds:
            process_config = self.process_thresholds[process_name]
            if threshold_type in process_config:
                return process_config[threshold_type]
        
        # Return None if no custom threshold and no default should apply
        return None

    def publish_event(self, event_type, process_name, details, is_start=True):
        msg = Event()
        msg.stamp = self.get_clock().now().to_msg()
        msg.severity = "WARN" if is_start else "INFO"
        msg.category = "RESOURCES"
        msg.event_type = f"{event_type}_{'START' if is_start else 'STOP'}"
        msg.source = process_name
        msg.details_json = json.dumps(details)

        self.pub.publish(msg)

    def match_cpu_process(self, process):
        """Match a psutil process to a monitored process name."""
        try:
            name = process.name()
            cmdline = " ".join(process.cmdline())

            for target in self.cpu_process_names:
                if target in name or target in cmdline:
                    return target

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return None

    def match_gpu_process(self, proc_tuple):
        """Match a jtop process to a monitored GPU process name."""
        # proc_tuple[9] = process name from jtop
        name = proc_tuple[9]
        for target in self.gpu_process_names:
            if target in name:
                return target
        return None

    def check_alert(self, proc_key, alert_type, is_high, details):
        """
        Check if alert state changed and publish start/stop events accordingly.

        proc_key: (process_name, pid)
        alert_type: e.g., "HIGH_CPU"
        is_high: True if threshold exceeded
        details: dict with metric values
        """
        if proc_key not in self.active_alerts:
            self.active_alerts[proc_key] = {}

        was_active = self.active_alerts[proc_key].get(alert_type, False)

        if is_high and not was_active:
            # Threshold crossed: send START event
            self.publish_event(alert_type, proc_key[0], details, is_start=True)
            self.active_alerts[proc_key][alert_type] = True

        elif not is_high and was_active:
            # Back to normal: send STOP event
            self.publish_event(alert_type, proc_key[0], details, is_start=False)
            self.active_alerts[proc_key][alert_type] = False

    def check_processes(self):
        """Monitor both CPU-only processes (psutil) and GPU processes (jtop)"""
        current_procs = set()

        # Monitor CPU-only processes
        self._check_cpu_processes(current_procs)
        
        # Monitor GPU processes
        self._check_gpu_processes(current_procs)

        # Clean up alerts for processes that no longer exist
        dead_procs = set(self.active_alerts.keys()) - current_procs

        for proc_key in dead_procs:
            # Send STOP events for any active alerts
            for alert_type, is_active in self.active_alerts[proc_key].items():
                if is_active:
                    self.publish_event(
                        alert_type,
                        proc_key[0],
                        {"pid": proc_key[1], "reason": "process_terminated"},
                        is_start=False
                    )
            del self.active_alerts[proc_key]

    def _check_cpu_processes(self, current_procs):
        """Check CPU-only processes using psutil"""
        if not self.cpu_process_names:
            return

        for proc in psutil.process_iter(['pid', 'name', 'cpu_num', 'memory_info']):
            try:
                matched_name = self.match_cpu_process(proc)
                if not matched_name:
                    continue

                pid = proc.pid
                cpu_percent = proc.cpu_percent(interval=None) / self.CPU_COUNT
                mem_mb = proc.memory_info().rss / (1024 * 1024)  # Convert to MB

                proc_key = (matched_name, pid)
                current_procs.add(proc_key)

                cpu_threshold = self.get_threshold(matched_name, 'cpu')
                mem_threshold = self.get_threshold(matched_name, 'mem')

                self.get_logger().info(
                    f"CPU Process {matched_name} (PID {pid}) --> CPU: {cpu_percent:.2f}%, MEM: {mem_mb:.2f} MB"
                )

                # Check CPU threshold
                if cpu_threshold is not None:
                    self.check_alert(
                        proc_key,
                        "HIGH_CPU",
                        cpu_percent > cpu_threshold,
                        {"cpu": cpu_percent, "pid": pid, "threshold": cpu_threshold}
                    )

                # Check Memory threshold
                if mem_threshold is not None:
                    self.check_alert(
                        proc_key,
                        "HIGH_MEMORY",
                        mem_mb > mem_threshold,
                        {"memory_mb": mem_mb, "pid": pid, "threshold": mem_threshold}
                    )

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def _check_gpu_processes(self, current_procs):
        """Check GPU processes using jtop"""
        # if not self.gpu_process_names:
        #     return

        # processes = self.jetson.processes
        # CPU_CORES = 8

        # for proc in processes:
        #     matched_name = self.match_gpu_process(proc)
        #     if not matched_name:
        #         continue

        #     pid = proc[0]
        #     cpu = float(proc[6] or 0.0) / CPU_CORES
        #     mem_raw = proc[7] or 0
        #     mem = mem_raw / (1024)  # MB
        #     gpu_mem = (proc[8] or 0) / (1024)  # MB

        #     proc_key = (matched_name, pid)
        #     current_procs.add(proc_key)

        #     cpu_threshold = self.get_threshold(matched_name, 'cpu')
        #     gpu_threshold = self.get_threshold(matched_name, 'gpu')
        #     mem_threshold = self.get_threshold(matched_name, 'mem')

        #     self.get_logger().info(
        #         f"GPU Process {matched_name} (PID {pid}) --> GPU: {gpu_mem:.2f}MB, CPU: {cpu:.2f}%, MEM: {mem:.2f}MB"
        #     )

        #     # Check CPU threshold
        #     if cpu_threshold is not None:
        #         self.check_alert(
        #             proc_key,
        #             "HIGH_CPU",
        #             cpu > cpu_threshold,
        #             {"cpu": cpu, "pid": pid, "threshold": cpu_threshold}
        #         )

        #     # Check GPU threshold
        #     if gpu_threshold is not None:
        #         self.check_alert(
        #             proc_key,
        #             "HIGH_GPU",
        #             gpu_mem > gpu_threshold,
        #             {"gpu_memory": gpu_mem, "pid": pid, "threshold": gpu_threshold}
        #         )

        #     # Check Memory threshold
        #     if mem_threshold is not None:
        #         self.check_alert(
        #             proc_key,
        #             "HIGH_MEMORY",
        #             mem > mem_threshold,
        #             {"memory_mb": mem, "pid": pid, "threshold": mem_threshold}
        #         )

    def check_overall_health(self):
        """Check overall system health and publish alerts if thresholds exceeded"""
        # System percentage CPU utilization
        #cpu = psutil.cpu_percent()
        pass
        # cpu = 100 - self.jetson.cpu['total']['idle']
        # #print(self.jetson.cpu['total'].keys())
        # #print("########################################")
        # print(self.jetson.temperature['Tboard'].keys())
        # # Current GPU load
        # gpu = self.jetson.gpu['gv11b']['status']['load']

        # # temperature in Celsius
        # temperature = self.jetson.temperature['Tboard']['temp']

        # # Total estimate board power in milliwatt
        # power = self.jetson.power['tot']['power'] / 1000

        # self.get_logger().info(
        #     f"SYSTEM SNAPSHOT: CPU={cpu}%, GPU={gpu}%, Temp={temperature}°C, Power={power}W"
        # )

        # # Check overall CPU threshold
        # is_high_cpu = cpu > self.overall_cpu_threshold
        # self.check_overall_alert(
        #     "OVERALL_HIGH_CPU",
        #     is_high_cpu,
        #     {"cpu": cpu, "threshold": self.overall_cpu_threshold}
        # )

        # # Check overall GPU threshold
        # is_high_gpu = gpu > self.overall_gpu_threshold
        # self.check_overall_alert(
        #     "OVERALL_HIGH_GPU",
        #     is_high_gpu,
        #     {"gpu": gpu, "threshold": self.overall_gpu_threshold}
        # )

        # # Check XAVIER power threshold
        # is_high_power = power > self.overall_power_max_threshold
        # self.check_overall_alert(
        #     "XAVIER_HIGH_POWER",
        #     is_high_power,
        #     {"power": power, "threshold": self.overall_power_max_threshold}
        # )

        # is_low_power = power < self.overall_power_min_threshold
        # self.check_overall_alert(
        #     "XAVIER_LOW_POWER",
        #     is_low_power,
        #     {"power": power, "threshold": self.overall_power_min_threshold}
        # )

        # is_high_temp = temperature > self.overall_temperature_threshold
        # self.check_overall_alert(
        #     "XAVIER_HIGH_TEMP",
        #     is_high_temp,
        #     {"temperature": temperature, "threshold": self.overall_temperature_threshold}
        # )

    def check_overall_alert(self, alert_type, is_high, details):
        """
        Check if overall system alert state changed and publish start/stop events.

        alert_type: e.g., "OVERALL_HIGH_CPU"
        is_high: True if threshold exceeded
        details: dict with metric values
        """
        was_active = self.overall_alerts.get(alert_type, False)

        if is_high and not was_active:
            # Threshold crossed: send START event
            self.publish_event(alert_type, "SYSTEM", details, is_start=True)
            self.overall_alerts[alert_type] = True

        elif not is_high and was_active:
            # Back to normal: send STOP event
            self.publish_event(alert_type, "SYSTEM", details, is_start=False)
            self.overall_alerts[alert_type] = False
        
    def destroy_node(self):
        self.jetson.close()
        super().destroy_node()

def main():
    rclpy.init()
    node = SystemHealthNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


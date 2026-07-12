#!/usr/bin/env python3
"""
Planning Deep-Learning Node — TensorRT + Multiprocessing Architecture
=====================================================================
Inference runs in a **separate OS process** with its own Python GIL and
CUDA context.  The ROS node process handles only:
  • Heartbeat timer  (status.running() at 10 Hz)
  • Perception subscriber (cone filtering + queue put — pure Python, fast)
  • Result-polling timer  (queue get + Path publish — pure Python, fast)

Because no GPU work ever happens in the ROS process, the heartbeat can
NEVER be blocked by inference, regardless of model latency, thermal
throttling, or CUDA stalls.
"""

import os
import math
import queue
import numpy as np
import multiprocessing as mp

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Path
from geometry_msgs.msg import Pose, PoseStamped
from ament_index_python.packages import get_package_share_directory
from tf_helper.StatusPublisher import StatusPublisher


# ────────────────────────────────────────────────────────────────────
# INFERENCE WORKER  (runs in its own OS process — never touches rclpy)
# ────────────────────────────────────────────────────────────────────
def _inference_worker(engine_path, input_q, output_q):
    """
    Standalone function executed in a child process.
    Has its own Python interpreter, GIL, and CUDA context.
    Loops forever:  get cone array → run TensorRT → put result.
    """
    import pycuda.driver as cuda          # only imported in THIS process
    cuda.init()
    dev = cuda.Device(0)
    ctx = dev.make_context()

    try:
        import tensorrt as trt             # noqa: F401 — needed by TensorRTModel
        np.bool = np.bool_                 # numpy compat fix

        # Import the model class (pycuda.autoinit is no longer in it,
        # so importing it doesn't create a competing CUDA context).
        from planning_deep_learning.tensorrt_model import TensorRTModel

        model = TensorRTModel(engine_path)

        # Signal the parent that we're ready
        output_q.put("__READY__")

        while True:
            # Block up to 1 s so we can check for the shutdown sentinel
            try:
                input_data = input_q.get(timeout=1.0)
            except queue.Empty:
                continue

            if input_data is None:         # shutdown sentinel
                break

            try:
                result = model.predict(input_data)

                # Drain any stale result the parent hasn't consumed yet
                # so the output queue always holds only the *latest* prediction.
                while not output_q.empty():
                    try:
                        output_q.get_nowait()
                    except queue.Empty:
                        break

                output_q.put(result)       # already a .copy() from predict()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[InferenceWorker] Error during predict: {e}")
    finally:
        ctx.pop()
        ctx.detach()


# ────────────────────────────────────────────────────────────────────
# ROS 2 NODE  (main process — no CUDA, no pycuda, no tensorrt)
# ────────────────────────────────────────────────────────────────────
class PlanningDlNode(Node):

    def __init__(self, model_path: str):
        super().__init__("planning_dl")

        # --- Callback Groups ------------------------------------------------
        # Two separate groups so the heartbeat timer can NEVER be starved
        # by perception / result-polling work, even under GIL contention.
        self.heartbeat_group = MutuallyExclusiveCallbackGroup()
        self.work_group      = MutuallyExclusiveCallbackGroup()

        # --- Model metadata --------------------------------------------------
        self.is_colorless = "colorless" in model_path.lower()
        self.get_logger().info("--- Initializing TensorRT Planning Node (multiprocessing) ---")
        self.get_logger().info(f"Engine : {model_path}")
        self.get_logger().info(f"Colorless: {self.is_colorless}")

        # --- Launch the inference worker process -----------------------------
        # Use 'spawn' so the child gets a clean Python interpreter — the safest
        # option for CUDA (avoids inheriting half-initialised GPU state from a
        # fork).
        mp_ctx = mp.get_context("spawn")
        self.input_queue  = mp_ctx.Queue(maxsize=2)
        self.output_queue = mp_ctx.Queue(maxsize=4)

        self._worker = mp_ctx.Process(
            target=_inference_worker,
            args=(model_path, self.input_queue, self.output_queue),
            daemon=True,                   # auto-killed if main process exits
        )
        self._worker.start()
        self.get_logger().info(
            f"Inference worker launched  (PID={self._worker.pid}).  "
            f"Waiting for engine to load …"
        )

        # Wait for the worker to finish loading the TensorRT engine.
        # Engine deserialization can take several seconds on the Xavier.
        try:
            ready = self.output_queue.get(timeout=60)
            if ready == "__READY__":
                self.get_logger().info("✅ Inference worker READY.")
        except queue.Empty:
            self.get_logger().error(
                "⚠️  Inference worker did not become ready within 60 s!  "
                "Check stderr for errors from the worker process."
            )

        # --- Status / Heartbeat ----------------------------------------------
        self.status = StatusPublisher("/status/planning_node", self)
        self.status.starting()
        self.status_timer = self.create_timer(
            0.1,                            # 10 Hz heartbeat
            self._heartbeat_callback,
            callback_group=self.heartbeat_group,
        )
        self.status.ready()

        # --- Result-polling timer --------------------------------------------
        # Checks the output queue at 50 Hz and publishes the Path as soon as
        # a new prediction arrives.
        self.result_timer = self.create_timer(
            0.02,                           # 50 Hz poll
            self._poll_results,
            callback_group=self.work_group,
        )

        # --- Cached state ----------------------------------------------------
        self.path = None

        # --- ROS pub/sub -----------------------------------------------------
        self.subscriber1 = self.create_subscription(
            MarkerArray,
            "/perception_markers",
            self.receiveFromPerception,
            10,
            callback_group=self.work_group,
        )
        self.publisher = self.create_publisher(Path, "/path", 10)

    # ── Heartbeat (own callback group → own thread → never blocked) ──
    def _heartbeat_callback(self):
        self.status.running()

    # ── Result poller ────────────────────────────────────────────────
    def _poll_results(self):
        """Drain the output queue and publish the latest prediction."""
        latest = None
        while not self.output_queue.empty():
            try:
                latest = self.output_queue.get_nowait()
            except queue.Empty:
                break

        if latest is not None:
            # predict() returns shape (1, 15, 2);  [0] → (15, 2)
            self.path = latest[0]
            self._publish_path()

    # ── Perception callback ─────────────────────────────────────────
    def receiveFromPerception(self, msg: MarkerArray) -> None:
        if len(msg.markers) == 0:
            return

        visible_cones = []

        for marker in msg.markers:
            # Local frame:  X Forward, Y Left →  Model:  X Right, Y Forward
            x_model = -marker.pose.position.y
            y_model =  marker.pose.position.x

            dist = math.hypot(x_model, y_model)

            # 15-metre radius, ignore very close cones
            if dist > 15.0 or dist < 0.5:
                continue

            # 60-degree forward cone
            angle = math.atan2(x_model, y_model)
            if abs(angle) > (math.pi / 3):
                continue

            r, g, b = marker.color.r, marker.color.g, marker.color.b

            is_white  = r > 0.95 and g > 0.95 and b > 0.95
            is_blue   = b > 0.80 and g < 0.45 and r < 0.45
            is_yellow = r > 0.70 and g > 0.70 and b < 0.45

            if is_white:
                continue

            if self.is_colorless:
                if is_blue or is_yellow:
                    visible_cones.append((dist, [x_model, y_model]))
            else:
                if is_blue:
                    visible_cones.append((dist, [x_model, y_model, 1.0, 0.0]))
                elif is_yellow:
                    visible_cones.append((dist, [x_model, y_model, 0.0, 1.0]))

        # Nearest-first, max 10 cones
        visible_cones.sort(key=lambda item: item[0])
        MAX_CONES = 10
        cones_features = [c[1] for c in visible_cones[:MAX_CONES]]

        if len(cones_features) == 0:
            return                         # nothing to infer on

        cones_array = np.array(cones_features, dtype=np.float32)

        # Zero-pad to MAX_CONES rows
        feature_dim = 2 if self.is_colorless else 4
        if len(cones_array) < MAX_CONES:
            pad = np.zeros((MAX_CONES - len(cones_array), feature_dim),
                           dtype=np.float32)
            cones_array = np.concatenate([cones_array, pad], axis=0)

        # ── Send to inference worker (non-blocking) ─────────────────
        # If the queue is full the worker is still busy with the previous
        # frame — drop the oldest frame so the worker always gets the most
        # recent data.
        try:
            self.input_queue.put_nowait(cones_array)
        except queue.Full:
            try:
                self.input_queue.get_nowait()   # discard stale frame
            except queue.Empty:
                pass
            try:
                self.input_queue.put_nowait(cones_array)
            except queue.Full:
                pass                        # edge case: just skip this frame

    # ── Path publisher ──────────────────────────────────────────────
    def _publish_path(self):
        if self.path is None:
            return

        timestamp = self.get_clock().now().to_msg()
        path_msg = Path()
        path_msg.header.stamp    = timestamp
        path_msg.header.frame_id = "zed_left_camera_frame"

        for pt in self.path:
            pose = Pose()
            # Model (X right, Y forward) → ROS local frame (X forward, Y left)
            pose.position.y = -float(pt[0])
            pose.position.x =  float(pt[1])

            ps = PoseStamped()
            ps.pose = pose
            ps.header.frame_id = "zed_left_camera_frame"
            path_msg.poses.append(ps)

        self.publisher.publish(path_msg)

    # ── Clean shutdown ──────────────────────────────────────────────
    def destroy_node(self):
        self.get_logger().info("Shutting down inference worker …")
        try:
            self.input_queue.put_nowait(None)      # send shutdown sentinel
            self._worker.join(timeout=5.0)
            if self._worker.is_alive():
                self._worker.terminate()
                self.get_logger().warn("Worker did not exit cleanly — terminated.")
        except Exception:
            pass
        super().destroy_node()


# ────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)

    model_file = os.path.join(
        get_package_share_directory("planning_deep_learning"),
        "Completed_Models",
        "best_model.engine",
    )
    node = PlanningDlNode(model_file)

    # Two threads: one for the heartbeat group, one for the work group.
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user.")
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

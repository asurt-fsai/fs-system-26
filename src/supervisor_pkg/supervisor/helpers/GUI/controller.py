import logging
import os
import signal
import subprocess
import threading
import rclpy

from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.Missions.MissionManager import MissionManager
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.Supervisor import Supervisor

class GUIController:
    def __init__(self, use_docker=False):
        if not rclpy.ok():
            rclpy.init(args=None)

        self.logger = logging.getLogger(__name__)
        self.module_manager = ModuleManager()
        self.mission_manager = MissionManager.getInstance()
        self.mission_manager.setModuleManager(self.module_manager)
        self._status_process = None
        self._heartbeat_process = None
        self._static_process = None
        self._last_module_names = []
        self._last_mission_name = None
        self._last_mission_type = None
        self._comm_thread = None
        self._communication = CommunicationLayer.getInstance()
        self._ensure_supervisor_running()

        self._mission_map = {
            "StaticA": MissionType.STATIC_A,
            "StaticB": MissionType.STATIC_B,
            "Autocross": MissionType.AUTOCROSS,
            "Trackdrive": MissionType.TRACKDRIVE,
            "Skidpad": MissionType.SKIDPAD,
            "Acceleration": MissionType.ACCELERATION,
            "AutoDemo": MissionType.AUTODEMO,
        }

    def _ensure_supervisor_running(self):
        if getattr(self._communication, "_supervisor", None) is None:
            Supervisor(self._communication, self.mission_manager, self.module_manager)

        if self._comm_thread is None or not self._comm_thread.is_alive():
            self._comm_thread = threading.Thread(target=self._communication.spin, daemon=True)
            self._comm_thread.start()

    def _spawn_process(self, cmd):
        """Spawn a subprocess in its own process group for reliable shutdown."""
        return subprocess.Popen(cmd, preexec_fn=os.setsid)

    def _stop_process(self, process, name: str):
        if process is None:
            return None
        if process.poll() is not None:
            return None

        try:
            self.logger.info(f"[GUI] Stopping {name}")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=2)
        except Exception:
            try:
                self.logger.warning(f"[GUI] Force-killing {name}")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception as exc:
                self.logger.error(f"[GUI] Failed to stop {name}: {exc}")
        return None

    def _has_running_modules(self) -> bool:
        for module in self.module_manager.getModules().values():
            process = getattr(module, "process", None)
            if process and process.poll() is None:
                return True
        return False

    def start_mission(self, mission_name, launch_only: bool = False):
        mission_type = self._mission_map.get(mission_name)
        if mission_type is None:
            self.logger.error(f"[GUI] Unknown mission name: {mission_name}")
            return

        if self._has_running_modules():
            self.logger.warning(
                "[GUI] Mission launch blocked: previous modules are still running. Use Shutdown first."
            )
            return

        if launch_only:
            try:
                modules = self.mission_manager.resolveModules(mission_type)
            except Exception as exc:
                self.logger.error(f"[GUI] Module resolution failed: {exc}")
                return

            self._last_module_names = [m.pkg for m in modules]
            self._last_mission_name = mission_name
            self._last_mission_type = mission_type
            self.logger.info(
                f"[GUI] Mission '{mission_name}' modules resolved: count={len(modules)} names={self._last_module_names}"
            )

            self.module_manager.registerModules(modules)
            failed = self.module_manager.launchAll()
            if failed:
                failed_names = [m.pkg for m in failed]
                self.logger.error(
                    f"[GUI] Module launch failed: {len(failed)} module(s) failed: {failed_names}"
                )
                return

            self.logger.info(f"[GUI] Module launch completed for mission: {mission_name}")
        else:
            try:
                self.logger.info(f"[GUI] Creating mission: {mission_name} (type={mission_type.name})")
                mission_obj = self.mission_manager.createMission(mission_type)
                self.logger.info(f"[GUI] Mission created successfully: {type(mission_obj).__name__}")
            except RuntimeError as exc:
                self.logger.warning(f"[GUI] Mission creation blocked: {exc}")
                active = self.mission_manager.getActiveMission()
                active_type = getattr(active, "missionType", None)
                if active and active_type == mission_type:
                    is_static = mission_type in (
                        MissionType.STATIC_A,
                        MissionType.STATIC_B,
                        MissionType.AUTODEMO,
                    )
                    self.logger.info("[GUI] Mission already active; reopening mission window")
                    if is_static:
                        self.stop_sim_and_close_status()
                        self.open_static_mission_window(mission_name)
                    else:
                        self.open_status_window()
                        self.start_heartbeat_simulation()
                        self.stop_static_mission_window()
                return
            except Exception as exc:
                self.logger.error(f"[GUI] Unexpected error creating mission: {exc}")
                return

            modules = self.mission_manager.resolveModules(mission_type)
            self._last_module_names = [m.pkg for m in modules]
            self._last_mission_name = mission_name
            self._last_mission_type = mission_type
            self.logger.info(
                f"[GUI] Mission '{mission_name}' modules resolved: count={len(modules)} names={self._last_module_names}"
            )

            try:
                self.logger.info(f"[GUI] Starting mission: {mission_name}")
                self.mission_manager.startMission()
                self.logger.info(f"[GUI] Mission started successfully: {mission_name}")
            except Exception as exc:
                self.logger.error(f"[GUI] Mission start failed: {exc}")
                return

        is_static = mission_type in (MissionType.STATIC_A, MissionType.STATIC_B, MissionType.AUTODEMO)

        self.logger.info(f"[GUI] Is static mission: {is_static}")
        if is_static:
            self.stop_sim_and_close_status()
            self.open_static_mission_window(mission_name)
        else:
            # Auto-open node status monitor and start simulated heartbeats for quick validation.
            self.open_status_window()
            self.start_heartbeat_simulation()
            self.stop_static_mission_window()

    def _sim_nodes(self):
        if self._last_module_names:
            return self._last_module_names
        modules = self.module_manager.getModules()
        return list(modules.keys())

    def start_heartbeat_simulation(self):
        nodes = self._sim_nodes()
        if not nodes:
            self.logger.warning("[GUI] No mission modules found. Start a mission first.")
            return

        self.stop_heartbeat_simulation()

        cmd = [
            "ros2", "run", "supervisor_pkg", "heartbeat_simulator",
            "--nodes", *nodes,
            "--period", "0.8",
        ]
        self.logger.info(f"[GUI] Starting heartbeat simulator for nodes={nodes}")
        self._heartbeat_process = self._spawn_process(cmd)

    def simulate_heartbeat_drop(self):
        nodes = self._sim_nodes()
        if not nodes:
            self.logger.warning("[GUI] No mission modules found. Start a mission first.")
            return

        self.stop_heartbeat_simulation()
        drop_node = nodes[0]
        cmd = [
            "ros2", "run", "supervisor_pkg", "heartbeat_simulator",
            "--nodes", *nodes,
            "--period", "0.8",
            "--drop-node", drop_node,
            "--drop-after", "7",
            "--drop-duration", "10",
        ]
        self.logger.info(
            f"[GUI] Starting heartbeat drop test. node={drop_node}; expect supervisor restart logs on timeout"
        )
        self._heartbeat_process = self._spawn_process(cmd)

    def stop_heartbeat_simulation(self):
        self._heartbeat_process = self._stop_process(self._heartbeat_process, "heartbeat simulator")

    def open_status_window(self):
        if self._status_process and self._status_process.poll() is None:
            self.logger.info("[GUI] Status window already running")
            return
        self.logger.info("[GUI] Launching status window")
        self._status_process = self._spawn_process(["ros2", "run", "supervisor_pkg", "status"])

    def open_static_mission_window(self, mission_name: str):
        if self._static_process and self._static_process.poll() is None:
            self.logger.info("[GUI] Static mission window already running; restarting")
            self._static_process = self._stop_process(self._static_process, "static mission window")
        self.logger.info(f"[GUI] Launching static mission window for {mission_name}")
        self._static_process = self._spawn_process(
            [
                "ros2",
                "run",
                "supervisor_pkg",
                "static_mission_gui",
                "--mission",
                mission_name,
            ]
        )

    def shutdown(self):
        try:
            self.stop_sim_and_close_status()
            self.stop_static_mission_window()
            self.module_manager.shutdownAll()
            self.mission_manager.clearActiveMission()
            self._last_module_names = []
            self.logger.info("[GUI] Shutdown complete, mission lock released")
        except Exception as exc:
            self.logger.error(f"[GUI] Shutdown failed: {exc}", exc_info=True)

    def restart(self):
        if self._last_mission_type is None:
            self.logger.warning("[GUI] Restart requested with no selected mission")
            return

        self.logger.info(f"[GUI] Restarting whole mission: {self._last_mission_name}")
        self.stop_sim_and_close_status()
        self.stop_static_mission_window()
        self.module_manager.shutdownAll()
        self.mission_manager.clearActiveMission()

        try:
            mission_obj = self.mission_manager.createMission(self._last_mission_type)
            modules = self.mission_manager.resolveModules(self._last_mission_type)
            self._last_module_names = [m.pkg for m in modules]
            self.logger.info(
                f"[GUI] Mission restarted -> created={type(mission_obj).__name__} modules={len(modules)}"
            )
            self.mission_manager.startMission()
            if self._last_mission_type in (MissionType.STATIC_A, MissionType.STATIC_B, MissionType.AUTODEMO):
                self.stop_sim_and_close_status()
                self.open_static_mission_window(self._last_mission_name)
            else:
                self.open_status_window()
                self.start_heartbeat_simulation()
                self.stop_static_mission_window()
        except Exception as exc:
            self.logger.error(f"[GUI] Mission restart failed: {exc}", exc_info=True)

    def stop_sim_and_close_status(self):
        self.stop_heartbeat_simulation()
        self._status_process = self._stop_process(self._status_process, "status window")

    def stop_static_mission_window(self):
        self._static_process = self._stop_process(self._static_process, "static mission window")
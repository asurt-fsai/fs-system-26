import logging
import os
import signal
import subprocess
import threading
import rclpy

from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.clients.mission_manager_client import MissionManagerClient
from supervisor.helpers.clients.module_manager_client import ModuleManagerClient
from supervisor.helpers.Commands.ShutdownModulesCommand import ShutdownModulesCommand
from supervisor.helpers.Commands.RestartModuleCommand import RestartModuleCommand
from supervisor.helpers.Commands.EmergencyStopCommand import EmergencyStopCommand

class GUIController:
    def __init__(self, use_docker=False):
        if not rclpy.ok():
            rclpy.init(args=None)

        self.logger = logging.getLogger(__name__)
        self.module_manager = ModuleManager()
        self._status_process = None
        self._static_process = None
        self._last_module_names = []
        self._last_mission_name = None
        self._last_mission_type = None
        self._comm_thread = None
        self._communication = CommunicationLayer.getInstance()
        self._mission_manager_client = MissionManagerClient(self._communication)
        self._module_manager_client = ModuleManagerClient(self._communication)
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

        self._last_mission_name = mission_name
        self._last_mission_type = mission_type
        self._last_module_names = []
        self._mission_manager_client.start_mission(mission_type)
        self.logger.info(f"[GUI] Mission start published: {mission_name}")

        is_static = mission_type in (MissionType.STATIC_A, MissionType.STATIC_B, MissionType.AUTODEMO)

        self.logger.info(f"[GUI] Is static mission: {is_static}")
        if is_static:
            self.stop_sim_and_close_status()
            self.open_static_mission_window(mission_name)
        else:
            self.open_status_window()
            self.stop_static_mission_window()

    def _sim_nodes(self):
        if self._last_module_names:
            return self._last_module_names
        modules = self.module_manager.getModules()
        return list(modules.keys())
##
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
            supervisor = getattr(self._communication, "_supervisor", None)
            if supervisor is not None:
                supervisor.issueCommand(ShutdownModulesCommand(self._module_manager_client, self.logger))
            else:
                self.module_manager.shutdownAll()
            self._mission_manager_client.stop_mission()
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
        supervisor = getattr(self._communication, "_supervisor", None)
        if supervisor is not None:
            supervisor.issueCommand(ShutdownModulesCommand(self._module_manager_client, self.logger))
        else:
            self.module_manager.shutdownAll()
        self._mission_manager_client.stop_mission()
        self._mission_manager_client.start_mission(self._last_mission_type)
        if self._last_mission_type in (MissionType.STATIC_A, MissionType.STATIC_B, MissionType.AUTODEMO):
            self.stop_sim_and_close_status()
            self.open_static_mission_window(self._last_mission_name)
        else:
            self.open_status_window()
            self.stop_static_mission_window()

    def restart_modules(self):
        supervisor = getattr(self._communication, "_supervisor", None)
        modules = list(self.module_manager.getModules().values())
        if not modules:
            self.logger.warning("[GUI] Restart requested but no modules found")
            return
        if supervisor is None:
            self.logger.warning("[GUI] Supervisor not available; restarting directly")
            for module in modules:
                module.restart()
            return
        for module in modules:
            supervisor.issueCommand(
                RestartModuleCommand(self._module_manager_client, module.pkg, self.logger)
            )

    def emergency_stop(self):
        supervisor = getattr(self._communication, "_supervisor", None)
        if supervisor is None:
            self.logger.error("[GUI] Supervisor not available; cannot issue EmergencyStopCommand")
            return
        supervisor.issueCommand(
            EmergencyStopCommand(self._mission_manager_client, self._module_manager_client, self.logger)
        )

    def stop_sim_and_close_status(self):
        self._status_process = self._stop_process(self._status_process, "status window")

    def stop_static_mission_window(self):
        self._static_process = self._stop_process(self._static_process, "static mission window")

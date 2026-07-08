
"""
Local OS-based launcher using subprocess.
Used for launching ROS2 modules locally.
"""    

import os
import subprocess
import time
import psutil
from supervisor.helpers.Module.ProcessLauncher import ProcessLauncher
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Module.Module import Module
import logging

LOG_DIR = os.path.expanduser("~/.ros/logs/supervisor_modules")



class LocalLauncher(ProcessLauncher):    

    def __init__(self):
        self.logger= logging.getLogger(__name__)

    def launch(self, module) -> bool:
        """
        Input  : module (Module) — module to launch
        Output : bool — True if launch successful, False otherwise
        Logic  : Check if module is not already running.
                 Launch module using ros2 launch with subprocess.
                 Initialize lastHeartbeatTime and restartAttempts.
                 Set module state to Starting.
                 Return True on success, False on failure.
        """
        if module.process and module.state == ModuleState.Running:
            self.logger.info(f"[MODULE] Cannot launch from state {module.state}")
            return False

        try:
            self.logger.info(f"[MODULE] Launching {module.pkg}/{module.launchFile} ...")
            self.logger.info(
                f"[MODULE] Command: ros2 launch {module.pkg} {module.launchFile}"
            )
            module.state = ModuleState.Starting

            os.makedirs(LOG_DIR, exist_ok=True)
            log_path = os.path.join(LOG_DIR, f"{module.pkg}.log")
            module.log_file_path = log_path
            log_file = open(log_path, "a")

            module.process = subprocess.Popen(
                ["ros2", "launch", module.pkg, module.launchFile],
                stdout=log_file,
                stderr=log_file,
            )

            module.lastHeartbeatTime = time.time()
            return True

        except Exception as e:
            self.logger.error(f"[MODULE] Launch failed: {e}")
            module.state = ModuleState.Error
            module.process = None
            return False
        
    def shutdown(self, module) -> bool:
        """
        Input  : module (Module) — module to shutdown
        Output : bool — True if shutdown successful, False otherwise
        Logic  : Check if module process exists, return if not.
                 Get parent and all child processes recursively.
                 Terminate all child processes first.
                 Terminate parent process.
                 Wait up to 5 seconds for all processes to exit.
                 Set module state to Shutdown and clear process reference.
                 Return True on success, False on critical errors.
                 Handle NoSuchProcess and other exceptions gracefully.
        """

        self.logger.info(f"[LocalLauncher] Shutting down {module.pkg}")

        if not module.process:
            module.state = ModuleState.Shutdown
            return True

        try:
            # Get parent process
            parent = psutil.Process(module.process.pid)

            # Get all children recursively
            children = parent.children(recursive=True)

            self.logger.info(f"[LocalLauncher] Killing {len(children)} child processes")

            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass

            # Terminate parent
            parent.terminate()

            # Wait for all to exit
            psutil.wait_procs([parent] + children, timeout=5)

            module.state = ModuleState.Shutdown
            module.process = None
            return True

        except psutil.NoSuchProcess:
            pid = getattr(module.process, 'pid', None)
            self.logger.info(f"[LocalLauncher] Shutdown warning: process PID not found (pid={pid})")
            module.process = None
            module.state = ModuleState.Shutdown
            return True

        except Exception as e:
            self.logger.error(f"[LocalLauncher] Shutdown error: {e}")
            module.process = None
            module.state = ModuleState.Error
            return False
        

    def restart(self, module) -> bool:
        """
        Input  : module (Module) — module to restart
        Output : bool — True if restart successful, False otherwise
        Logic  : Call shutdown(module) to gracefully stop the process.
                 Wait 2 seconds for system to settle.
                 Call launch(module) to start the process again.
                 Return True only if launch succeeds.
        """
        self.shutdown(module)
        time.sleep(2)  # Small cooldown between shutdown and launch
        return self.launch(module)
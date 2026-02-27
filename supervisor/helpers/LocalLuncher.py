
"""
Local OS-based launcher using subprocess.
Used for launching ROS2 modules locally.
"""    

import subprocess
import time
import psutil
from .process_launcher import ProcessLauncher
from ModuleState import ModuleState



class LocalLauncher(ProcessLauncher):    
    
    
    # --------------------------------------------------
    # Launch Process
    # --------------------------------------------------
    def launch(self, module) -> bool:
        """
        Launch the ROS module using ros2 launch.
        """

        # Prevent invalid state launch
        if self._state not in [
            ModuleState.Shutdown,
            ModuleState.Error,
            ModuleState.Unresponsive,
        ]:
            print(f"[MODULE] Cannot launch from state {self._state}")
            return False

        try:
            print(f"[MODULE] Launching {self.pkg}/{self.launch_file} ...")

            self._state = ModuleState.Starting

            # Optional: Validate launch path exists
            # (Debug protection — optional but useful)
            import os
            pkg_path = os.path.join(
                os.getenv("ROS_PACKAGE_PATH", ""),
                self.pkg,
                "launch",
                self.launch_file,
            )

            if not os.path.exists(pkg_path):
                print(f"[MODULE] Warning: Launch file not found at {pkg_path}")

            # Start process
            self._process = subprocess.Popen(
                ["ros2", "launch", self.pkg, self.launch_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print(f"[MODULE] Process started with PID: {self._process.pid}")

            # Reset runtime tracking
            self._last_heartbeat = None
            self._restart_attempts = 0

            return True

        except Exception as e:
            print(f"[MODULE] Launch failed: {e}")
            self._state = ModuleState.Error
            self._process = None
            return False


    def shutdown(self, module):
        """
        Robust shutdown:
        - Kill child processes
        - Kill parent process
        - Wait safely
        """

        print(f"[LocalLauncher] Shutting down {module.pkg}")

        if not module.process:
            return

        try:
            # Get parent process
            parent = psutil.Process(module.process.pid)

            # Get all children recursively
            children = parent.children(recursive=True)

            print(f"[LocalLauncher] Killing {len(children)} child processes")

            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass

            # Terminate parent
            parent.terminate()

            # Wait for all to exit
            psutil.wait_procs([parent] + children, timeout=5)

        except Exception as e:
            print(f"[LocalLauncher] Shutdown error: {e}")

        finally:
            module.process = None
        


    def restart(self, module) -> bool:
        """
        Restart the ROS module safely.
        Handles restart attempts, cooldown, and state transitions.
        """

        # Prevent restart in invalid states
        if self._state == ModuleState.Starting:
            print(f"[MODULE] {self.name} is already starting. Restart aborted.")
            return False

        if self._restart_attempts >= self._max_restart_attempts:
            print(f"[MODULE] Max restart attempts reached for {self.name}.")
            self._state = ModuleState.Error
            return False

        # Count this attempt
        self._restart_attempts += 1

        print(
            f"[MODULE] Restarting {self.name} "
            f"(Attempt {self._restart_attempts}/{self._max_restart_attempts})..."
        )

        # Force shutdown of the module
        self.shutdown_module()

        # Cooldown before relaunch
        time.sleep(2)

        # Try to launch again
        success = self.launch_module()

        if success:
            print(f"[MODULE] {self.name} restart initiated (Starting state).")
            self._state = ModuleState.Starting
        else:
            print(f"[MODULE] Restart failed for {self.name}.")
            self._state = ModuleState.Error

        return success

"""
Local OS-based launcher using subprocess.
Used for launching ROS2 modules locally.
"""    

import subprocess
import time
import psutil
from ProcessLauncher import ProcessLauncher
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
        if module.state not in [
            ModuleState.Shutdown,
            ModuleState.Error,
            ModuleState.Unresponsive,
        ]:
            print(f"[MODULE] Cannot launch from state {module.state}")
            return False

        try:
            print(f"[MODULE] Launching {module.pkg}/{module.launchFile} ...")

            module.state = ModuleState.Starting

            # Optional: Validate launch path exists
            # (Debug protection — optional but useful)
            import os
            pkg_path = os.path.join(
                os.getenv("ROS_PACKAGE_PATH", ""),
                module.pkg,
                "launch",
                module.launchFile,
            )

            if not os.path.exists(pkg_path):
                print(f"[MODULE] Warning: Launch file not found at {pkg_path}")

            # Start process
            module.process = subprocess.Popen(
                ["ros2", "launch", module.pkg, module.launchFile],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print(f"[MODULE] Process started with PID: {module.process.pid}")

            # Reset runtime tracking
            module.lastHeartbeatTime = 0.0
            module.restartAttempts = 0

            return True

        except Exception as e:
            print(f"[MODULE] Launch failed: {e}")
            module.state = ModuleState.Error
            module.process = None
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

            module.state = ModuleState.Shutdown

        except Exception as e:
            print(f"[LocalLauncher] Shutdown error: {e}")
            module.state = ModuleState.Error

        finally:
            module.process = None
        


    def restart(self, module) -> bool:
        """
        Restart the ROS module safely.
        Handles restart attempts, cooldown, and state transitions.
        """

        # Prevent restart in invalid states
        if module.state == ModuleState.Starting:
            print(f"[MODULE] {module.pkg} is already starting. Restart aborted.")
            return False

        if module.restartAttempts >= module.maxRestartAttempts:
            print(f"[MODULE] Max restart attempts reached for {module.pkg}.")
            module.state = ModuleState.Error
            return False

        # Count this attempt
        module.restartAttempts += 1

        print(
            f"[MODULE] Restarting {module.pkg} "
            f"(Attempt {module.restartAttempts}/{module.maxRestartAttempts})..."
        )

        # Force shutdown of the module
        self.shutdown(module)

        # Cooldown before relaunch
        time.sleep(2)

        # Try to launch again
        success = self.launch(module)

        if success:
            print(f"[MODULE] {module.pkg} restart initiated (Starting state).")
            module.state = ModuleState.Starting
        else:
            print(f"[MODULE] Restart failed for {module.pkg}.")
            module.state = ModuleState.Error

        return success
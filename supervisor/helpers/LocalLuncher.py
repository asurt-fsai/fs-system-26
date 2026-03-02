
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
        #NO LOGIC - just execute shutdown + launch
        self.shutdown(module)
        time.sleep(2)  # Small cooldown between shutdown and launch
        return self.launch(module)
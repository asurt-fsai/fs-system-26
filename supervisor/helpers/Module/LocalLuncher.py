
"""
Local OS-based launcher using subprocess.
Used for launching ROS2 modules locally.
"""    

import subprocess
import time
import psutil
import os
from supervisor.helpers.Module.ProcessLauncher import ProcessLauncher
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Module.Module import Module



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
            
            # Just try to launch - let ros2 handle the path resolution
            module.process = subprocess.Popen(
                ["ros2", "launch", module.pkg, module.launchFile],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            print(f"[MODULE] Process started with PID: {module.process.pid}")
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
            #module.state = ModuleState.Error
            return False

        #finally:
        #    module.process = None
        return True
        

    def restart(self, module) -> bool:
        #just execute shutdown + launch
        self.shutdown(module)
        time.sleep(2)  # Small cooldown between shutdown and launch
        return self.launch(module)
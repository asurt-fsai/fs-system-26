
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
import threading



class LocalLauncher(ProcessLauncher):    
    
    
    # --------------------------------------------------
    # Launch Process
    # --------------------------------------------------
    def launch(self, module) -> bool:
        if module.process and module.state == ModuleState.Running:
            print(f"[MODULE] Cannot launch from state {module.state}")
            return False

        try:
            print(f"[MODULE] Launching {module.pkg}/{module.launchFile} ...")
            module.state = ModuleState.Starting

            launcher_process = subprocess.Popen(
                ["ros2", "launch", module.pkg, module.launchFile],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            def drain(pipe):
                try:
                    for _ in pipe:
                        pass
                except Exception:
                    pass

            threading.Thread(target=drain, args=(launcher_process.stdout,), daemon=True).start()
            threading.Thread(target=drain, args=(launcher_process.stderr,), daemon=True).start()

            # Wait for child node process to spawn
            deadline = time.time() + 5.0
            child = None
            while time.time() < deadline:
                time.sleep(0.3)
                try:
                    children = psutil.Process(launcher_process.pid).children(recursive=True)
                    if children:
                        child = children[-1]
                        break
                except Exception:
                    break

            if child:
                module.process = child
                print(f"[MODULE] Actual node PID: {module.process.pid}")
            else:
                module.process = launcher_process
                print(f"[MODULE] Warning: no child found, tracking launcher PID")

            module.lastHeartbeatTime = time.time()
            module.restartAttempts = 0
            return True

        except Exception as e:
            print(f"[MODULE] Launch failed: {e}")
            module.state = ModuleState.Error
            module.process = None
            return False
        
    def shutdown(self, module) -> bool:
        """
        Robust shutdown:
        - Kill child processes
        - Kill parent process
        - Wait safely
        """

        print(f"[LocalLauncher] Shutting down {module.pkg}")

        if not module.process:
            module.state = ModuleState.Shutdown
            return True

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
            module.process = None
            return True

        except psutil.NoSuchProcess:
            pid = getattr(module.process, 'pid', None)
            print(f"[LocalLauncher] Shutdown warning: process PID not found (pid={pid})")
            module.process = None
            module.state = ModuleState.Shutdown
            return True

        except Exception as e:
            print(f"[LocalLauncher] Shutdown error: {e}")
            module.process = None
            module.state = ModuleState.Error
            return False
        

    def restart(self, module) -> bool:
        #just execute shutdown + launch
        self.shutdown(module)
        time.sleep(2)  # Small cooldown between shutdown and launch
        return self.launch(module)
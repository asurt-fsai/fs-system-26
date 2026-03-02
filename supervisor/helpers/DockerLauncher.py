import subprocess
import time
from ModuleState import ModuleState
from ProcessLauncher import ProcessLauncher


class DockerLauncher(ProcessLauncher):  

    def __init__(self, image_name: str):
        self.image_name = image_name

    # ==================================================
    # Launch
    # ==================================================

    def launch(self, module) -> bool:  # Fixed: return bool
        """
        Launch the module inside a Docker container.
        """

        # Prevent invalid state launch (same as LocalLauncher)
        if module.state not in [
            ModuleState.Shutdown,
            ModuleState.Error,
            ModuleState.Unresponsive,
        ]:
            print(f"[DockerLauncher] Cannot launch {module.pkg} from state {module.state}")
            return False

        container_name = f"{module.pkg}_container"

        print(f"[DockerLauncher] Launching {container_name}")

        try:
            module.state = ModuleState.Starting

            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "--name",
                    container_name,
                    self.image_name,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"[DockerLauncher] Launch failed: {result.stderr}")
                module.state = ModuleState.Error
                module.process = None
                return False  

            container_id = result.stdout.strip()

            print(f"[DockerLauncher] Container started ID={container_id}")

            # We store container name instead of ID for easier control
            module.process = container_name
            module.lastHeartbeatTime = 0.0  # Reset heartbeat tracking
            module.restartAttempts = 0  # Reset restart attempts

            return True  

        except Exception as e:
            print(f"[DockerLauncher] Launch exception: {e}")
            module.state = ModuleState.Error
            module.process = None
            return False  

    # ==================================================
    # Shutdown
    # ==================================================

    def shutdown(self, module):
        """
        Stop and remove Docker container.
        """

        if not module.process:
            module.state = ModuleState.Shutdown 
            return

        container_name = module.process

        print(f"[DockerLauncher] Stopping {container_name}")

        try:
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                module.state = ModuleState.Shutdown
            else:
                print(f"[DockerLauncher] Shutdown warning: {result.stderr}")
                module.state = ModuleState.Error

        except Exception as e:
            print(f"[DockerLauncher] Shutdown error: {e}")
            module.state = ModuleState.Error

        finally:
            module.process = None

    # ==================================================
    # Restart
    # ==================================================

    def restart(self, module) -> bool:
        """NO LOGIC - just execute shutdown + launch"""
        self.shutdown(module)
        time.sleep(2)
        return self.launch(module)

    # ==================================================
    # Health Check
    # ==================================================

    def is_running(self, module) -> bool:
        """
        Check if container is running.
        """

        if not module.process:
            return False

        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", module.process],
                capture_output=True,
                text=True,
                check=True  
            )
            return result.stdout.strip() == "true"
        except Exception as e:
            print(f"[DockerLauncher] Health check failed: {e}")
            return False
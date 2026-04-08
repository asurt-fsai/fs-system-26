import subprocess
import time
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Module.ProcessLauncher import ProcessLauncher


class DockerLauncher(ProcessLauncher):  

    def __init__(self, image_name: str):
        self.image_name = image_name

    # ==================================================
    # Launch
    # ==================================================

    def launch(self, module) -> bool:
        """
        Input  : module (Module) — module to launch inside Docker container
        Output : bool — True if launch successful, False otherwise
        Logic  : Check if module is in valid state for launch (Shutdown/Error/Unresponsive).
                 Launch Docker container using 'docker run -d --rm' command.
                 Extract container ID from Docker output.
                 Store container name in module.process for tracking.
                 Initialize lastHeartbeatTime to current time and restartAttempts to 0.
                 Set module state to Starting.
                 Return True on success, False on failure.
        """

        # Prevent invalid state launch (same as LocalLauncher)
        if module.state not in [
            ModuleState.Shutdown,
            ModuleState.Error,
            ModuleState.Unresponsive,
        ]:
            self.logger.info(f"[DockerLauncher] Cannot launch {module.pkg} from state {module.state}")
            return False

        container_name = f"{module.pkg}_container"

        self.logger.info(f"[DockerLauncher] Launching {container_name}")

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
                self.logger.info(f"[DockerLauncher] Launch failed: {result.stderr}")
                module.state = ModuleState.Error
                module.process = None
                return False  

            container_id = result.stdout.strip()

            self.logger.info(f"[DockerLauncher] Container started ID={container_id}")

            # We store container name instead of ID for easier control
            module.process = container_name
            module.lastHeartbeatTime = time.time()  # Initialize heartbeat timing
            module.restartAttempts = 0  # Reset restart attempts

            return True  

        except Exception as e:
            self.logger.info(f"[DockerLauncher] Launch exception: {e}")
            module.state = ModuleState.Error
            module.process = None
            return False  

    # ==================================================
    # Shutdown
    # ==================================================

    def shutdown(self, module) -> bool:
        """
        Input  : module (Module) — module to shutdown inside Docker container
        Output : bool — True if shutdown successful, False on critical error
        Logic  : Check if module process exists, return True immediately if not.
                 Execute 'docker stop' command on the container.
                 Set module state to Shutdown on success, Error on failure.
                 Clear module.process reference.
                 Return True on success, False on Docker command error.
        """

        if not module.process:
            module.state = ModuleState.Shutdown
            return True

        container_name = module.process

        self.logger.info(f"[DockerLauncher] Stopping {container_name}")

        try:
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                module.state = ModuleState.Shutdown
                module.process = None
                return True
            else:
                self.logger.info(f"[DockerLauncher] Shutdown warning: {result.stderr}")
                module.state = ModuleState.Error
                module.process = None
                return False

        except Exception as e:
            self.logger.info(f"[DockerLauncher] Shutdown error: {e}")
            module.state = ModuleState.Error
            module.process = None
            return False

    # ==================================================
    # Restart
    # ==================================================

    def restart(self, module) -> bool:
        """
        Input  : module (Module) — module to restart inside Docker container
        Output : bool — True if restart successful, False otherwise
        Logic  : Call shutdown(module) to gracefully stop the container.
                 Wait 2 seconds for system to settle.
                 Call launch(module) to start the container again.
                 Return True only if launch succeeds.
        """
        self.shutdown(module)
        time.sleep(2)
        return self.launch(module)

    # ==================================================
    # Health Check
    # ==================================================

    def is_running(self, module) -> bool:
        """
        Input  : module (Module) — module with Docker container to check
        Output : bool — True if container is running, False otherwise
        Logic  : Check if module process exists, return False if not.
                 Execute 'docker inspect' command to check container running state.
                 Parse output for running status string 'true'.
                 Return True if running, False if stopped or error.
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
            self.logger.info(f"[DockerLauncher] Health check failed: {e}")
            return False
import subprocess
import logging
from supervisor.helpers.Commands.Command import Command


class DockerStopCommand(Command):

    def __init__(self, mission_name: str):
        self.mission_name = mission_name
        self.logger = logging.getLogger(__name__)

    def execute(self):

        if not self.mission_name:
            self.logger.error("[DockerStop] No mission provided")
            return False

       
        cmd = [
            "docker", "compose",
            "-f", f"missions/{self.mission_name}.yaml",
            "down"
        ]

        self.logger.info(f"[DockerStop] Stopping {self.mission_name}")
        self.logger.info(f"[DockerStop] Command: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True)
            self.logger.info("[DockerStop] Success")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"[DockerStop] Failed: {e}")
            return False

        except FileNotFoundError:
            self.logger.error("[DockerStop] Docker not found")
            return False
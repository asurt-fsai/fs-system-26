import os
import subprocess
import logging
from eufs_msgs.msg import CanState
from supervisor.helpers.Commands.Command import Command

class DockerLaunchCommand(Command):
    """
    Command to launch a mission using docker compose based on AMI state.
    """

    # ==========================
    # Mission → Compose file
    # ==========================
    MISSION_FILES = {
        "autonomous_demo": "missions/autonomous_demo.yaml",
        "autocross": "missions/autocross.yaml",
        "track_drive": "missions/track_drive.yaml",
        "acceleration" : "missions/acceleration.yaml", 
        "skidpad" : "missions/skidpad.yaml",

    }

    # Optional: for better logging
    AMI_NAMES = {
        CanState.AMI_NOT_SELECTED: "NOT_SELECTED",
        CanState.AMI_ACCELERATION: "ACCELERATION",
        CanState.AMI_SKIDPAD: "SKIDPAD",
        CanState.AMI_AUTOCROSS: "AUTOCROSS",
        CanState.AMI_TRACK_DRIVE: "TRACK_DRIVE",
        CanState.AMI_AUTONOMOUS_DEMO: "AUTONOMOUS_DEMO",
    }

    def __init__(self, ami_state: int):
        self.ami_state = ami_state
        self.logger = logging.getLogger(__name__)
        self.mission_name = self.map_ami_to_mission()  # Initialize here to store the active mission name

    # ==========================
    # Map AMI → mission name
    # ==========================
    def map_ami_to_mission(self):
        mapping = {
            CanState.AMI_AUTONOMOUS_DEMO: "autonomous_demo",
            CanState.AMI_AUTOCROSS: "autocross",
            CanState.AMI_ACCELERATION: "acceleration",
            CanState.AMI_SKIDPAD: "skidpad",
            CanState.AMI_TRACK_DRIVE: "track_drive",
        }
        return mapping.get(self.ami_state, None)
    
    def getMissionName(self):
        return self.mission_name

    # ==========================
    # Execute (main logic)
    # ==========================
    def execute(self):

        # 1. Ignore NOT_SELECTED
        if self.ami_state == CanState.AMI_NOT_SELECTED:
            self.logger.info("[DockerLaunchCommand] AMI_NOT_SELECTED → no action")
            return False

        # 2. Convert AMI → mission name
        mission_name = self.mission_name  # Store for Supervisor to track active mission

        if mission_name is None:
            self.logger.error(f"[DockerLaunchCommand] Unknown AMI state: {self.ami_state}")
            return False
        
        #3.Check Docker availability when we actually need it
        try:
            # Quick check if docker compose is available
            subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                check=True,
                timeout=2
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.logger.error(f"[DockerLaunchCommand] Docker Compose not available: {e}")
            return False



        # 4. Get compose file
        compose_file = self.MISSION_FILES.get(mission_name)

        if compose_file is None:
            self.logger.error(f"[DockerLaunchCommand] No compose file for mission: {mission_name}")
            return False

        # 5. Check file exists
        if not os.path.isfile(compose_file):
            self.logger.error(f"[DockerLaunchCommand] File not found: {compose_file}")
            return False

        # 6. Build docker compose command
        cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]

        # 7. Logging
        ami_name = self.AMI_NAMES.get(self.ami_state, "UNKNOWN")
        self.logger.info(f"[DockerLaunchCommand] AMI: {ami_name} ({self.ami_state})")
        self.logger.info(f"[DockerLaunchCommand] Mission: {mission_name}")
        self.logger.info(f"[DockerLaunchCommand] Command: {' '.join(cmd)}")

        # 8. Execute command
        try:
            subprocess.run(cmd, check=True)
            self.logger.info("[DockerLaunchCommand] Mission launched successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"[DockerLaunchCommand] Launch failed: {e}")
            return False

        except FileNotFoundError:
            self.logger.error("[DockerLaunchCommand] Docker not found in PATH")
            return False
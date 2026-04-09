import time

from .ModuleState import ModuleState

class Module:

    def __init__(
        self,
        pkg: str,
        launch_file: str,
        communication,
        launcher,
        heartbeat_timeout: float = 5.0,
        max_restart_attempts: int = 3,
    ):
        self.pkg = pkg
        self.launchFile = launch_file

        self.communication = communication
        self.launcher = launcher

        self.state = ModuleState.Shutdown
        self.process = None

        self.lastHeartbeatTime = 0.0
        self.heartbeatTimeout = heartbeat_timeout

        self.restartAttempts = 0
        self.maxRestartAttempts = max_restart_attempts

        self.lastRestartTime = 0.0
        self.restartCooldown = 3.0

        # Register to communication layer
        self.communication.register_module(self)

    # ==================================================
    # Lifecycle
    # ==================================================

    def launch(self):
        if self.state == ModuleState.Running:
            return

        print(f"[MODULE] Launching {self.pkg}")

        self.state = ModuleState.Starting
        self.launcher.launch(self)

    def shutdown(self):
        print(f"[MODULE] Shutting down {self.pkg}")

        self.launcher.shutdown(self)
        self.state = ModuleState.Shutdown

    def restart(self):
        now = time.time()

        # Prevent restart spam
        if self.restartAttempts >= self.max_restart_attempts:
            print(f"[MODULE] {self.pkg} reached max restart attempts.")
            self.state = ModuleState.Error
            return

        if now - self.lastRestartTime < self.restartCooldown:
            return

        self.restartAttempts += 1
        self.lastRestartTime = now

        print(f"[MODULE] Restarting {self.pkg} (Attempt {self.restartAttempts})")

        self.launcher.restart(self)
        self.state = ModuleState.Starting

    # ==================================================
    # Heartbeat Handling
    # ==================================================

    def on_heartbeat(self):
        """
        Called by CommunicationLayer when heartbeat message arrives.
        """
        self.lastHeartbeatTime = time.time()
        self.state = ModuleState.Running
        self.restartAttempts = 0  # Reset after healthy signal

    # ==================================================
    # Health Monitoring
    # ==================================================

    def check_health(self):

        # 1 If process crashed
        if self.process and self.process.poll() is not None:
            print(f"[MODULE] {self.pkg} process died.")
            self.state = ModuleState.Unresponsive
            self.restart()
            return

        # 2️ If heartbeat timeout
        if self.state == ModuleState.Running:
            if time.time() - self.lastHeartbeatTime > self.heartbeatTimeout:
                print(f"[MODULE] {self.pkg} heartbeat timeout.")
                self.state = ModuleState.Unresponsive
                self.restart()
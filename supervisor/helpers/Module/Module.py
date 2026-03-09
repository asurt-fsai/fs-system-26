
from supervisor.helpers.Module.ModuleState import ModuleState
from threading import Lock
import time
 
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

        self._lock = Lock()

    # ==================================================
    # Lifecycle
    # ==================================================

    def launch(self):
        if self.state == ModuleState.Running:
            return False

        print(f"[MODULE] Launching {self.pkg}")

        # Reset tracking only on intentional manual launch
        self.restartAttempts = 0
        self.lastHeartbeatTime = time.time()  
        return self.launcher.launch(self)

    def shutdown(self):
        print(f"[MODULE] Shutting down {self.pkg}")

        success=self.launcher.shutdown(self)
        #self.state = ModuleState.Shutdown
        self.process = None
        self.state = ModuleState.Shutdown if success else ModuleState.Error

    def restart(self):
            """ALL restart logic is here"""
            now = time.time()

            # Check max attempts
            if self.restartAttempts >= self.maxRestartAttempts:
                print(f"[MODULE] {self.pkg} reached max restart attempts ({self.maxRestartAttempts}).")
                self.state = ModuleState.Error
                return False

            # Check cooldown
            if now - self.lastRestartTime < self.restartCooldown:
                print(f"[MODULE] {self.pkg} in cooldown. Restart delayed.")
                return False

            # Update tracking BEFORE restart attempt
            self.restartAttempts += 1
            self.lastRestartTime = now

            print(f"[MODULE] Restarting {self.pkg} (Attempt {self.restartAttempts}/{self.maxRestartAttempts})...")

            time.sleep(0.5)
            # Delegate execution to launcher ,just execution
            
            success = self.launcher.restart(self)

            if success:
                print(f"[MODULE] {self.pkg} restart initiated successfully.")
                self.state = ModuleState.Starting  # wait for heartbeat to confirm Running
            else:
                print(f"[MODULE] {self.pkg} restart failed.")
                self.state = ModuleState.Error

            return success
    # ==================================================
    # Heartbeat Handling
    # ==================================================

    def on_heartbeat(self):
        """
        Called by CommunicationLayer when heartbeat message arrives.
        """
        self.lastHeartbeatTime = time.time()
        self.state = ModuleState.Running

    # ==================================================
    # Health Monitoring
    # ==================================================

    def check_health(self):
    
        # 1  If Docker launcher
        if hasattr(self.launcher, "is_running"):
            if self.process and not self.launcher.is_running(self):
                print(f"[MODULE] {self.pkg} container stopped.")
                self.state = ModuleState.Unresponsive
                self.restart()
                return
        # If Local launcher    
        # 2 If process crashed
        else:
            if self.process and self.process.poll() is not None:
                print(f"[MODULE] {self.pkg} process died.")
                self.state = ModuleState.Unresponsive
                self.restart()
                return

        # Heartbeat timeout
        if self.state == ModuleState.Running:
            if time.time() - self.lastHeartbeatTime > self.heartbeatTimeout:
                print(f"[MODULE] {self.pkg} heartbeat timeout.")
                self.state = ModuleState.Unresponsive
                self.restart()
        # heartbeats trigger a restart even if the process hasn't exited.
        if self.lastHeartbeatTime and (time.time() - self.lastHeartbeatTime > self.heartbeatTimeout):
            print(f"[MODULE] {self.pkg} heartbeat timeout.")
            self.state = ModuleState.Unresponsive
            self.restart()
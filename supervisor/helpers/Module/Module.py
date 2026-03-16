
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
        self.launcherProcess = None  # ← add this

        self.lastHeartbeatTime = 0.0
        self.heartbeatTimeout = heartbeat_timeout

        self.restartAttempts = 0
        self.maxRestartAttempts = max_restart_attempts

        self.lastRestartTime = 0.0
        self.restartCooldown = 3.0

        # Register to communication layer
        self.communication.registerModule(self)

        self._lock = Lock()

    # ==================================================
    # Lifecycle
    # ==================================================

    def launch(self):
        """
        Input  : None
        Output : bool — True if launch succeeded
        Logic  : Guard against launching from invalid state.
                 Reset restartAttempts and lastHeartbeatTime.
                 Delegate to launcher.launch(self).
        """

        if self.state == ModuleState.Running:
            return False

        print(f"[MODULE] Launching {self.pkg}")

        # Reset tracking only on intentional manual launch
        self.restartAttempts = 0
        self.lastHeartbeatTime = time.time()  
        return self.launcher.launch(self)

    def shutdown(self):
        """
        Input  : None
        Output : None
        Logic  : Delegate to launcher.shutdown(self).
                 Set process = None.
                 Update state based on shutdown success/failure.
        """
        print(f"[MODULE] Shutting down {self.pkg}")

        success=self.launcher.shutdown(self)
        #self.state = ModuleState.Shutdown
        self.process = None
        self.state = ModuleState.Shutdown if success else ModuleState.Error

    def restart(self):  
            """
            Input  : None
            Output : bool — True if restart was initiated successfully
            Logic  : Check max restart attempts — if exceeded set state=Error and return False.
                        Check cooldown — if too soon return False.
                        Increment restartAttempts, update lastRestartTime.
                        Delegate execution to launcher.restart(self).
                        Set state=Starting on success, Error on failure.
            """

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
    
    def getState(self) -> ModuleState:
        """
        input: None
        output: ModuleState
        logic: Returns current state of the module.
        """
        return self.state
    


    
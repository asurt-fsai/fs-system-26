from supervisor.helpers.Module.ModuleState import ModuleState
import time
import logging
 
class Module:

    def __init__(
        self,
        pkg: str,
        launch_file: str,
        communication,
        launcher,
        heartbeat_timeout: float = 5.0,
    ):
        self.pkg = pkg
        self.launchFile = launch_file

        self.communication = communication
        self.launcher = launcher

        self.state = ModuleState.Shutdown
        self.process = None

        self.lastHeartbeatTime = 0.0
        self.heartbeatTimeout = heartbeat_timeout

        self.lastRestartTime = 0.0
        self.restartCooldown = 3.0
        self.logger = logging.getLogger(__name__)


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

        self.logger.info(f"[MODULE] Launching {self.pkg}")

        # Reset tracking only on intentional manual launch
        success = self.launcher.launch(self)
        if success:
            self.lastHeartbeatTime = time.time()
        return success

    def shutdown(self):
        """
        Input  : None
        Output : None
        Logic  : Delegate to launcher.shutdown(self).
                 Set process = None.
                 Update state based on shutdown success/failure.
        """
        self.logger.info(f"[MODULE] Shutting down {self.pkg}")

        success=self.launcher.shutdown(self)
        #self.state = ModuleState.Shutdown

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

            # Check cooldown
            if now - self.lastRestartTime < self.restartCooldown:
                self.logger.info(f"[MODULE] {self.pkg} in cooldown. Restart delayed.")
                return False

            # Update tracking BEFORE restart attempt
            self.lastRestartTime = now

            self.logger.info(f"[MODULE] Restarting {self.pkg} ")

            time.sleep(0.5)
            # Delegate execution to launcher ,just execution
            
            success = self.launcher.restart(self)

            if success:
                self.logger.info(f"[MODULE] {self.pkg} restart initiated successfully.")
                self.state = ModuleState.Starting  # wait for heartbeat to confirm Running
            else:
                self.logger.error(f"[MODULE] {self.pkg} restart failed.")
                self.state = ModuleState.Error

            return success
    
    def getState(self) -> ModuleState:
        """
        input: None
        output: ModuleState
        logic: Returns current state of the module.
        """
        return self.state
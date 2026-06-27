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
        startup_timeout: float = None,
        heartbeat_topic: str = None,
    ):
        self.pkg = pkg
        self.launchFile = launch_file

        self.communication = communication
        self.launcher = launcher

        self.state = ModuleState.Shutdown
        self.process = None

        self.lastHeartbeatTime = 0.0
        self.heartbeatTimeout = heartbeat_timeout
        self.heartbeatTopic = heartbeat_topic

        # Optional startup timeout used when a module is Starting but hasn't reported a heartbeat yet
        # If not provided, default to 2x heartbeat timeout
        if startup_timeout is None:
            self.startupTimeout = max(2.0 * heartbeat_timeout, 1.0)
        else:
            self.startupTimeout = startup_timeout


        self.lastRestartTime = 0.0
        self.restartCooldown = 3.0
        self.logger = logging.getLogger(__name__)

            # Modules do not interact with CommunicationLayer (no ROS logic here)


    def launch(self):
        """
        Input  : None
        Output : bool — True if launch succeeded
        Logic  : Guard against launching from invalid state.
                 Reset restartAttempts and lastHeartbeatTime.
                 Delegate to launcher.launch(self).
        """

        # Prevent launching if already starting or running
        if self.state in (ModuleState.Starting, ModuleState.Running):
            self.logger.info(f"[MODULE] Cannot launch from state {self.state}")
            return False

        self.logger.info(f"[MODULE] Launching {self.pkg}")
        # record the start time for startup timeout checks
        self.startTime = time.time()

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

        success = self.launcher.shutdown(self)
        # Ensure process reference is cleared on successful shutdown
        if success:
            self.process = None
            self.state = ModuleState.Shutdown
        else:
            self.state = ModuleState.Error

    def restart(self):
        """
        Input  : None
        Output : bool — True if restart was initiated successfully
        Logic  : Check cooldown, update lastRestartTime, delegate to launcher.restart(),
                 set state to Starting on success, Error on failure.
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

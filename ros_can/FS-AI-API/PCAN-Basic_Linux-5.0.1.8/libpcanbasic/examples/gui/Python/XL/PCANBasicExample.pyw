# -*- coding: cp1252 -*-
######################################################################
#  PCAN-Basic Example
#
#  ~~~~~~~~~~~~
#
#  ------------------------------------------------------------------
#  Author : Keneth Wagner
#  Language: Python 2.7
#  ------------------------------------------------------------------
#
#  Copyright (C) 1999-2025  PEAK-System Technik GmbH, Darmstadt
######################################################################

from PCANBasic import *  ## PCAN-Basic library import

## Imports for UI
##
from Tkinter import *  ## TK UI library
import Tix  ## TK extensions library

import tkMessageBox  ## Simple-Messages library
import traceback  ## Error-Tracing library

import string  ## String functions
import tkFont  ## Font-Management library

import time  ## Time-related library
import threading  ## Threading-based Timer library
import random  ## Random library

import platform  ## Underlying platform�s info library

TCL_DONT_WAIT = 1 << 1
TCL_WINDOW_EVENTS = 1 << 2
TCL_FILE_EVENTS = 1 << 3
TCL_TIMER_EVENTS = 1 << 4
TCL_IDLE_EVENTS = 1 << 5
TCL_ALL_EVENTS = 0


COL_TYPE = 0
COL_PID = 1
COL_LENGTH = 2
COL_SDT = 3
COL_VCID = 4
COL_AF = 5
COL_TIME = 6
COL_COUNT = 7
COL_DATA = 8

IS_WINDOWS = platform.system() == "Windows"
DISPLAY_UPDATE_MS = 100

if IS_WINDOWS:
    FRAME_WIDTH = 760
    FRAME_HEIGHT = 650
    GROUPBOX_WIDTH = 745
    GROUPBOX_HEIGHT = 70
    ###*#################################################################################
    ### Checks if the Windows-Event functionality can be used, by loading               #
    ### the respective module                                                           #
    ###                                                                                 #
    ### Win32 library for Window32 Events handling                                      #
    ### Module is part of "Python for Win32 Extensions"                                 #
    ### Web: http://starship.python.net/~skippy/                                        #
    #####################################################################################
    try:
        import win32event

        WINDOWS_EVENT_SUPPORT = True
    except ImportError:
        WINDOWS_EVENT_SUPPORT = False
else:
    FRAME_WIDTH = 970
    FRAME_HEIGHT = 730
    GROUPBOX_WIDTH = 958
    GROUPBOX_HEIGHT = 80
    WINDOWS_EVENT_SUPPORT = False


## Convert a CAN DLC value into the actual data length of the CAN XL frame.
##
def GetLengthFromDLC(dlc, messageTypeXL):
    if ((messageTypeXL & PCAN_MESSAGE_STATUS.value) == PCAN_MESSAGE_STATUS.value or 
        (messageTypeXL & PCAN_MESSAGE_XL.value) != PCAN_MESSAGE_XL.value):
        if dlc <= 8:
            return dlc

        if dlc == 9:
            return 12
        elif dlc == 10:
            return 16
        elif dlc == 11:
            return 20
        elif dlc == 12:
            return 24
        elif dlc == 13:
            return 32
        elif dlc == 14:
            return 48
        elif dlc == 15:
            return 64

        return dlc

    if dlc < 0:
        return 1

    if dlc > 2047:
        return 2048

    return dlc + 1


###*****************************************************************
### Timer class
###*****************************************************************
class TimerRepeater(object):
    """
    A simple timer implementation that repeats itself
    """

    # Constructor
    #
    def __init__(self, name, interval, target, isUi, args=[], kwargs={}):
        """
        Creates a timer.

        Parameters:
            name        name of the thread
            interval    interval in second between execution of target
            target      function that is called every 'interval' seconds
            args        non keyword-argument list for target function
            kwargs      keyword-argument list for target function
        """
        # define thread and stopping thread event
        self._name = name
        self._thread = None
        self._event = None
        self._isUi = isUi
        # initialize target and its arguments
        self._target = target
        self._args = args
        self._kwargs = kwargs
        # initialize timer
        self._interval = interval
        self._bStarted = False

    # Runs the thread that emulates the timer
    #
    def _run(self):
        """
        Runs the thread that emulates the timer.

        Returns:
            None
        """
        while not self._event.wait(self._interval):
            if self._isUi:
                # launch target in the context of the main loop
                root.after(1, self._target, *self._args, **self._kwargs)
            else:
                self._target(*self._args, **self._kwargs)

    # Starts the timer
    #
    def start(self):
        """
        Starts the timer

        Returns:
            None
        """
        # avoid multiple start calls
        if self._thread == None:
            self._event = threading.Event()
            self._thread = threading.Thread(None, self._run, self._name)
            self._thread.start()

    # Stops the timer
    #
    def stop(self):
        """
        Stops the timer

        Returns:
            None
        """
        if self._thread != None:
            self._event.set()
            self._thread = None


class CANProtocol(object):
    CAN = 0x1
    CAN_FD = 0x2
    CAN_XL = 0x4


###*****************************************************************
### Message Status structure used to show CAN Messages
### in a ListView
###*****************************************************************
class MessageStatus(object):
    def __init__(
        self, canMsg=TPCANMsgXL(), canTimestamp=TPCANTimestampXL(), listIndex=-1
    ):
        self.__m_Msg = canMsg
        self.__m_TimeStamp = canTimestamp
        self.__m_OldTimeStamp = canTimestamp
        self.__m_iIndex = listIndex
        self.__m_iCount = 1
        self.__m_bShowPeriod = True
        self.__m_bWasChanged = False
        self.__m_bWasInserted = True

    def Update(self, canMsg, canTimestamp):
        self.__m_Msg = canMsg
        self.__m_OldTimeStamp = self.__m_TimeStamp
        self.__m_TimeStamp = canTimestamp
        self.__m_bWasChanged = True
        self.__m_iCount = self.__m_iCount + 1

    @property
    def ShowingPeriod(self):
        return self.__m_bShowPeriod

    @ShowingPeriod.setter
    def ShowingPeriod(self, value):
        if self.__m_bShowPeriod ^ value:
            self.__m_bShowPeriod = value
            self.__m_bWasChanged = True

    @property
    def MarkedAsInserted(self):
        return self.__m_bWasInserted

    @MarkedAsInserted.setter
    def MarkedAsInserted(self, value):
        self.__m_bWasInserted = value

    @property
    def MarkedAsUpdated(self):
        return self.__m_bWasChanged

    @MarkedAsUpdated.setter
    def MarkedAsUpdated(self, value):
        self.__m_bWasChanged = value

    @property
    def TypeString(self):
        is_echo = (
            self.__m_Msg.MSGTYPE & PCAN_MESSAGE_ECHO.value
        ) == PCAN_MESSAGE_ECHO.value

        if (
            self.__m_Msg.MSGTYPE & PCAN_MESSAGE_STATUS.value
        ) == PCAN_MESSAGE_STATUS.value:
            return "STATUS"

        if (
            self.__m_Msg.MSGTYPE & PCAN_MESSAGE_ERRFRAME.value
        ) == PCAN_MESSAGE_ERRFRAME.value:
            return "ERROR"

        if (self.__m_Msg.MSGTYPE & PCAN_MESSAGE_XL.value) == PCAN_MESSAGE_XL.value:
            str_temp = "XL"
        elif (
            self.__m_Msg.MSGTYPE & PCAN_MESSAGE_EXTENDED.value
        ) == PCAN_MESSAGE_EXTENDED.value:
            str_temp = "EXT"
        else:
            str_temp = "STD"

        if (self.__m_Msg.MSGTYPE & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value:
            str_temp += " [ ECHO ]" if is_echo else " /RTR"
        else:
            if is_echo:
                str_temp += " [ ECHO"
            else:
                str_temp += " ["

            if self.__m_Msg.MSGTYPE >= PCAN_MESSAGE_XL.value:
                if self.__m_Msg.RRS:
                    str_temp += " RRS"
                if self.__m_Msg.SEC:
                    str_temp += " SEC"
                str_temp += " ]"
            elif self.__m_Msg.MSGTYPE > PCAN_MESSAGE_EXTENDED.value:
                if (
                    self.__m_Msg.MSGTYPE & PCAN_MESSAGE_FD.value
                ) == PCAN_MESSAGE_FD.value:
                    str_temp += " FD"
                if (
                    self.__m_Msg.MSGTYPE & PCAN_MESSAGE_BRS.value
                ) == PCAN_MESSAGE_BRS.value:
                    str_temp += " BRS"
                if (
                    self.__m_Msg.MSGTYPE & PCAN_MESSAGE_ESI.value
                ) == PCAN_MESSAGE_ESI.value:
                    str_temp += " ESI"
                str_temp += " ]"

        return str_temp

    @property
    def TimeString(self):
        fTime = self.__m_TimeStamp.value / 1000.0
        if self.__m_bShowPeriod:
            fTime -= self.__m_OldTimeStamp.value / 1000.0
        return "%.1f" % fTime

    @property
    def PidString(self):
        if (
            self.__m_Msg.MSGTYPE & PCAN_MESSAGE_EXTENDED.value
        ) == PCAN_MESSAGE_EXTENDED.value:
            return "%.8X" % self.__m_Msg.PID
        else:
            return "%.3X" % self.__m_Msg.PID

    @property
    def SdtString(self):
        return "{:02X}h".format(self.__m_Msg.SDT)

    @property
    def VcidString(self):
        return "{:02X}h".format(self.__m_Msg.VCID)

    @property
    def AfString(self):
        return "{:08X}h".format(self.__m_Msg.AF)

    @property
    def DataString(self):
        strTemp = ""
        for i in range(GetLengthFromDLC(self.__m_Msg.DLC, self.__m_Msg.MSGTYPE)):
            strTemp += "%.2X " % self.__m_Msg.DATA[i]
        return strTemp

    @property
    def CANMsg(self):
        return self.__m_Msg

    @property
    def Timestamp(self):
        return self.__m_TimeStamp

    @property
    def Position(self):
        return self.__m_iIndex

    @property
    def Count(self):
        return self.__m_iCount


###*****************************************************************


###*****************************************************************
### PCAN-basic Example app
###*****************************************************************
class PCANBasicExample(object):
    ## Constructor
    ##
    def __init__(self, parent):
        # Parent's configuration
        self.m_Parent = parent
        self.m_Parent.wm_title("PCAN-Basic XL Example")
        self.m_Parent.resizable(False, False)
        self.m_Parent.protocol("WM_DELETE_WINDOW", self.Form_OnClosing)

        # Frame's configuration
        self.m_Frame = Frame(self.m_Parent)
        self.m_Frame.grid(row=0, column=0, padx=5, pady=2, sticky="nwes")

        # Example's configuration
        self.InitializeBasicComponents()
        self.CenterTheWindow()
        self.InitializeWidgets()
        self.ConfigureLogFile()

        self.SetConnectionStatus(False)
        self.FillRandomData()

    ## Destructor
    ##
    def destroy(self):
        self.m_Parent.destroy()

    ## Message loop
    ##
    def loop(self):
        # This is an explict replacement for _tkinter mainloop()
        # It lets catch keyboard interrupts easier, and avoids
        # the 20 msec. dead sleep() which burns a constant CPU.
        while self.exit < 0:
            # There are 2 whiles here. The outer one lets you continue
            # after a ^C interrupt.
            try:
                # This is the replacement for _tkinter mainloop()
                # It blocks waiting for the next Tcl event using select.
                while self.exit < 0:
                    # prevent UI concurrency errors with timers (read and
                    # display)
                    # with self._lock:
                    self.m_Parent.tk.dooneevent(TCL_ALL_EVENTS)
            except SystemExit:
                # Tkinter uses SystemExit to exit
                self.exit = 1
                return
            except KeyboardInterrupt:
                if tkMessageBox.askquestion("Interrupt", "Really Quit?") == "yes":
                    # self.tk.eval('exit')
                    self.exit = 1
                    return
                continue
            except:
                # Otherwise it's some other error
                t, v, tb = sys.exc_info()
                text = ""
                for line in traceback.format_exception(t, v, tb):
                    text += line + "\n"
                try:
                    tkMessageBox.showerror("Error", text)
                except:
                    pass
                self.exit = 1
                raise SystemExit(1)

    ################################################################################################################################################
    ### Help functions
    ################################################################################################################################################

    ## Initializes app members
    ##
    def InitializeBasicComponents(self):
        self.m_Width = FRAME_WIDTH
        self.m_Height = FRAME_HEIGHT
        self.exit = -1
        self.m_objPCANBasic = PCANBasic()
        self.m_PcanHandle = PCAN_NONEBUS
        self.m_LastMsgsList = []

        self.m_CanRead = False

        if WINDOWS_EVENT_SUPPORT:
            self.m_ReadThread = None
            self.m_Terminated = False
            self.m_ReceiveEvent = win32event.CreateEvent(None, 0, 0, None)

        self._lock = threading.RLock()

        if IS_WINDOWS or (not IS_WINDOWS):
            self.m_PARAMETERS = {
                "Device ID": PCAN_DEVICE_ID,
                "5V Power": PCAN_5VOLTS_POWER,
                "Auto-reset on BUS-OFF": PCAN_BUSOFF_AUTORESET,
                "CAN Listen-Only": PCAN_LISTEN_ONLY,
                "Debugs Log": PCAN_LOG_STATUS,
                "Receive Status": PCAN_RECEIVE_STATUS,
                "CAN Controller Number": PCAN_CONTROLLER_NUMBER,
                "Trace File": PCAN_TRACE_STATUS,
                "Channel Identification (USB)": PCAN_CHANNEL_IDENTIFYING,
                "Channel Capabilities": PCAN_CHANNEL_FEATURES,
                "Bit rate Adaptation": PCAN_BITRATE_ADAPTING,
                "Get Bit rate Nominal Information": PCAN_BITRATE_INFO_CC,
                "Get Bit rate FD Information": PCAN_BITRATE_INFO_FD,
                "Get Bit rate XL Information": PCAN_BITRATE_INFO_XL,
                "Get CAN Nominal Speed Bit/s": PCAN_BUSSPEED_NOMINAL,
                "Get CAN FD Speed Bit/s": PCAN_BUSSPEED_FD,
                "Get CAN XL Speed Bit/s": PCAN_BUSSPEED_XL,
                "Get IP Address": PCAN_IP_ADDRESS,
                "Get LAN Service Status": PCAN_LAN_SERVICE_STATUS,
                "Reception of Status Frames": PCAN_ALLOW_STATUS_FRAMES,
                "Reception of RTR Frames": PCAN_ALLOW_RTR_FRAMES,
                "Reception of Error Frames": PCAN_ALLOW_ERROR_FRAMES,
                "Interframe Transmit Delay": PCAN_INTERFRAME_DELAY,
                "Reception of Echo Frames": PCAN_ALLOW_ECHO_FRAMES,
                "Hard Reset Status": PCAN_HARD_RESET_STATUS,
                "Communication Direction": PCAN_LAN_CHANNEL_DIRECTION,
                "Global Unique Identifier (GUID)": PCAN_DEVICE_GUID,
            }
        else:
            self.m_PARAMETERS = {
                "Device ID": PCAN_DEVICE_ID,
                "5V Power": PCAN_5VOLTS_POWER,
                "Auto-reset on BUS-OFF": PCAN_BUSOFF_AUTORESET,
                "CAN Listen-Only": PCAN_LISTEN_ONLY,
                "Debugs Log": PCAN_LOG_STATUS,
            }

    ## Initializes the complete UI
    ##
    def InitializeWidgets(self):
        # Connection groupbox
        self.gbConnection = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT,
            width=GROUPBOX_WIDTH,
            text=" Connection ",
        )
        self.gbConnection.grid_propagate(0)
        self.gbConnection.grid(row=0, column=0, padx=2, pady=2)
        self.InitializeConnectionWidgets()

        ## Message Filtering groupbox
        self.gbMsgFilter = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT,
            width=GROUPBOX_WIDTH,
            text=" Message Filtering ",
        )
        self.gbMsgFilter.grid_propagate(0)
        self.gbMsgFilter.grid(row=1, column=0, padx=2, pady=2)
        self.InitializeFilteringWidgets()

        ## Configuration Parameters groupbox
        self.gbParameters = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT,
            width=GROUPBOX_WIDTH,
            text=" Configuration Parameters ",
        )
        self.gbParameters.grid_propagate(0)
        self.gbParameters.grid(row=2, column=0, padx=2, pady=2)
        self.InitializeConfigurationWidgets()

        ## Messages Reading groupbox
        self.gbReading = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT * 2 + 20,
            width=GROUPBOX_WIDTH,
            text=" Messages Reading ",
        )
        self.gbReading.grid_propagate(0)
        self.gbReading.grid(row=3, column=0, padx=2, pady=2)
        self.InitializeReadingWidgets()

        ## Messages Writing groupbox
        self.gbWriting = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT + 45,
            width=GROUPBOX_WIDTH,
            text=" Write Messages ",
        )
        self.gbWriting.grid_propagate(0)
        self.gbWriting.grid(row=4, column=0, padx=2, pady=2)
        self.InitializeWritingWidgets()

        ## Information groupbox
        self.gbInfo = LabelFrame(
            self.m_Frame,
            height=GROUPBOX_HEIGHT + 65,
            width=GROUPBOX_WIDTH,
            text=" Information ",
        )
        self.gbInfo.grid_propagate(0)
        self.gbInfo.grid(row=5, column=0, padx=2, pady=2)
        self.InitializeInformationWidgets()

        self.DoRefresh()

    ## Initializes controls and variables in the groupbox "Connection"
    ##
    def InitializeConnectionWidgets(self):
        # Control variables
        #
        self.m_BitrateLA = StringVar(value="Bit rate:")
        self.m_BitrateTXT = StringVar(
            value="f_clock_mhz=160,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,fd_tseg1=63,fd_tseg2=16,fd_sjw=16,fd_ssp_offset=0,xl_tseg1=10,xl_tseg2=9,xl_sjw=9,xl_ssp_offset=10,xl_error_signaling=1,xl_transceiver_mode_switch=0"
        )

        Label(self.gbConnection, anchor=W, text="Hardware:").grid(row=0, sticky=W)
        self.cbbChannel = Tix.ComboBox(
            self.gbConnection, command=self.cbbChannel_SelectedIndexChanged
        )
        self.cbbChannel.subwidget("entry")["width"] = 18
        self.cbbChannel.subwidget("listbox")["width"] = 18
        self.cbbChannel.grid(row=1, column=0, sticky=W)

        Label(
            self.gbConnection,
            width=10,
            anchor=W,
            padx=10,
            textvariable=self.m_BitrateLA,
        ).grid(row=0, column=1, sticky=W)
        self.txtBitrate = Entry(
            self.gbConnection, width=84, textvariable=self.m_BitrateTXT
        )
        self.txtBitrate.grid(row=1, column=1, columnspan=6, padx=9, pady=0)

        self.btnInit = Button(
            self.gbConnection, width=8, text="Initialize", command=self.btnInit_Click
        )

        self.btnInit.grid(row=0, column=8, sticky=W)

        self.btnRelease = Button(
            self.gbConnection,
            width=8,
            state=DISABLED,
            text="Release",
            command=self.btnRelease_Click,
        )
        self.btnRelease.grid(row=1, column=8, sticky=W)

    ## Initializes controls and variables in the groupbox "Message Filtering"
    ##
    def InitializeFilteringWidgets(self):
        # Control variables
        #
        self.m_FilteringRDB = IntVar(value=1)

        self.rdbFilterOpen = Radiobutton(
            self.gbMsgFilter, text="Open", value=1, variable=self.m_FilteringRDB
        )
        self.rdbFilterOpen.grid(row=1, column=1, padx=0, pady=10)

        self.rdbFilterClose = Radiobutton(
            self.gbMsgFilter, text="Close", value=0, variable=self.m_FilteringRDB
        )
        self.rdbFilterClose.grid(row=1, column=2, padx=0, pady=10)

        Label(self.gbMsgFilter, width=67, text=" ").grid(row=1, column=5)

        self.btnFilterApply = Button(
            self.gbMsgFilter,
            width=8,
            state=DISABLED,
            text="Apply",
            command=self.btnFilterApply_Click,
        )
        self.btnFilterApply.grid(row=1, padx=5, column=6, sticky=W)

        self.btnFilterQuery = Button(
            self.gbMsgFilter,
            width=8,
            state=DISABLED,
            text="Query",
            command=self.btnFilterQuery_Click,
        )
        self.btnFilterQuery.grid(row=1, column=7, sticky=W)

        self.rdbFilterOpen.select()

    ## Initializes controls and variables in the groupbox "Configuration Parameters"
    ##
    def InitializeConfigurationWidgets(self):
        # Control variables
        #
        self.m_ConfigurationRDB = IntVar(value=1)
        self.m_DeviceIdOrDelayNUD = StringVar(value="0")
        self.m_DeviceIdOrDelay = StringVar(value="Device ID:")

        # Controls
        #
        Label(self.gbParameters, anchor=W, text="Parameter:").grid(
            row=0, column=0, sticky=W
        )
        self.cbbParameter = Tix.ComboBox(
            self.gbParameters, command=self.cbbParameter_SelectedIndexChanged
        )
        self.cbbParameter.subwidget("entry")["width"] = 30
        self.cbbParameter.subwidget("listbox")["width"] = 30
        self.cbbParameter.subwidget("listbox")["height"] = 6
        self.cbbParameter.grid(row=1, column=0, sticky=W)
        for name, value in self.m_PARAMETERS.iteritems():
            self.cbbParameter.insert(Tix.END, name)
        self.cbbParameter.bind(
            "<<ComboboxSelected>>", self.cbbParameter_SelectedIndexChanged
        )
        self.cbbParameter["selection"] = "Debugs Log"

        Label(self.gbParameters, anchor=W, text="Activation:").grid(
            row=0, column=1, sticky=W
        )
        self.rdbParamActive = Radiobutton(
            self.gbParameters, text="Active", value=1, variable=self.m_ConfigurationRDB
        )
        self.rdbParamActive.grid(row=1, column=1, padx=0, pady=2, sticky=W)

        self.rdbParamInactive = Radiobutton(
            self.gbParameters,
            anchor=W,
            width=20,
            text="Inactive",
            value=0,
            variable=self.m_ConfigurationRDB,
        )
        self.rdbParamInactive.grid(row=1, column=2, padx=0, pady=2, sticky=W)

        Label(
            self.gbParameters, anchor=W, width=20, textvariable=self.m_DeviceIdOrDelay
        ).grid(row=0, column=3, sticky=W)
        self.nudDeviceIdOrDelay = Spinbox(
            self.gbParameters,
            width=15,
            state=DISABLED,
            from_=0,
            to=0x7FF,
            textvariable=self.m_DeviceIdOrDelayNUD,
        )
        self.nudDeviceIdOrDelay.grid(row=1, column=3, padx=0, pady=2, sticky=W)

        self.btnParameterSet = Button(
            self.gbParameters,
            width=8,
            state=ACTIVE,
            text="Set",
            command=self.btnParameterSet_Click,
        )
        self.btnParameterSet.grid(row=1, padx=5, column=4, sticky=W)

        self.btnParameterGet = Button(
            self.gbParameters,
            width=8,
            state=ACTIVE,
            text="Get",
            command=self.btnParameterGet_Click,
        )
        self.btnParameterGet.grid(row=1, column=5, sticky=W)

    ## Initializes controls and variables in the groupbox "Messages Reading"
    ##
    def InitializeReadingWidgets(self):
        # Control variables
        #
        self.m_ListColCaption = [
            "Type",
            "|PID",
            "|Length",
            "|SDT",
            "|VCID",
            "|AF",
            "|Rcv Time",
            "|Count",
            "|Data",
        ]
        if IS_WINDOWS:
            self.m_ListColSpace = [13, 10, 7, 5, 5, 10, 8, 6, 13]
        else:
            self.m_ListColSpace = [13, 10, 7, 5, 5, 7, 13, 8, 23]

        self.m_ListCaptionPadxSpaces = []
        for colText, colWidth in zip(self.m_ListColCaption, self.m_ListColSpace):
            self.m_ListCaptionPadxSpaces.append(colWidth - len(colText))
        self.m_ListCaptionPadxSpaces[0] = self.m_ListCaptionPadxSpaces[0] - 1

        if IS_WINDOWS:
            self.m_ListFont = tkFont.Font(family="Lucida Console", size="10")
        else:
            self.m_ListFont = tkFont.Font(family="Monospace", size="10")

        self.m_ReadingRDB = IntVar(value=0)
        self.m_ShowPeriod = True
        self.m_ShowPeriodCHB = IntVar(value=1)

        self.tmrRead = TimerRepeater("tmrRead", 0.050, self.tmrRead_Tick, False)

        # Controls
        #
        self.rdbTimer = Radiobutton(
            self.gbReading,
            text="Read using a Timer",
            value=1,
            variable=self.m_ReadingRDB,
            command=self.rdbTimer_CheckedChanged,
        )
        self.rdbTimer.grid(row=0, column=0, padx=5, pady=2, sticky=W)

        if IS_WINDOWS:
            self.rdbEvent = Radiobutton(
                self.gbReading,
                text="Reading using an Event",
                value=2,
                variable=self.m_ReadingRDB,
                command=self.rdbTimer_CheckedChanged,
            )
            self.rdbEvent.grid(row=0, column=1, padx=5, pady=2, sticky=W)
            if IS_WINDOWS:
                self.rdbEvent["state"] = ACTIVE
            else:
                self.rdbEvent["state"] = DISABLED

        self.rdbManual = Radiobutton(
            self.gbReading,
            text="Manual Read",
            value=0,
            variable=self.m_ReadingRDB,
            command=self.rdbTimer_CheckedChanged,
        )
        self.rdbManual.grid(row=0, column=2, padx=5, pady=2, sticky=W)

        self.chbShowPeriod = Checkbutton(
            self.gbReading,
            width=16,
            text="Timestamp as period",
            variable=self.m_ShowPeriodCHB,
            command=self.chbShowPeriod_CheckedChanged,
        )
        self.chbShowPeriod.grid(row=0, column=3, padx=5, pady=2)

        self.yReadScroll = Scrollbar(self.gbReading, orient=VERTICAL)
        self.yReadScroll.grid(row=1, column=4, rowspan=3, sticky=N + S)

        self.xReadScroll = Scrollbar(self.gbReading, orient=HORIZONTAL)
        self.xReadScroll.grid(row=3, padx=5, column=0, columnspan=4, sticky=W + E)

        tempString = ""
        for caption, spaces in zip(self.m_ListColCaption, self.m_ListCaptionPadxSpaces):
            tempString = tempString + "{0}{1}".format(caption, " " * spaces)
        Label(
            self.gbReading,
            anchor=W,
            text=tempString,
            bg="#E2E2E3",
            fg="#000000",
            font=self.m_ListFont,
            relief=GROOVE,
        ).grid(row=1, column=0, columnspan=4, padx=5, sticky="nwes")

        self.lstMessages = Tix.TList(
            self.gbReading,
            relief=GROOVE,
            height=5,
            orient="horizontal",
            itemtype="text",
            font=self.m_ListFont,
            command=self.btnMsgClear_Click,
        )
        self.lstMessages.grid(row=2, column=0, padx=5, columnspan=4, sticky="nwes")

        # self.yReadScroll['command'] = self.lstMessages.yview
        # self.xReadScroll['command'] = self.lstMessages.xview
        self.lstMessages.config(yscrollcommand=self.yReadScroll.set)
        self.yReadScroll.config(command=self.lstMessages.yview)
        self.lstMessages.config(xscrollcommand=self.xReadScroll.set)
        self.xReadScroll.config(command=self.lstMessages.xview)

        Label(self.gbReading, width=1, text=" ").grid(row=0, column=5)

        self.btnRead = Button(
            self.gbReading,
            width=8,
            state=DISABLED,
            text="Read",
            command=self.btnRead_Click,
        )
        self.btnRead.grid(row=1, column=6, padx=4, sticky=NW)

        self.btnMsgClear = Button(
            self.gbReading,
            width=8,
            state=ACTIVE,
            text="Clear",
            command=self.btnMsgClear_Click,
        )
        self.btnMsgClear.grid(row=2, column=6, padx=4, pady=4, sticky=NW)

    ## Initializes controls and variables in the groupbox "Write Messages"
    ##
    def InitializeWritingWidgets(self):
        # Control variables
        #
        self.m_PIDTXT = StringVar(value="000")
        self.m_SDTTXT = StringVar(value="00")
        self.m_VCIDTXT = StringVar(value="00")
        self.m_AFTXT = StringVar(value="00000000")
        self.m_RRSCHB = IntVar(value=0)
        self.m_SECCHB = IntVar(value=0)
        self.m_LengthNUD = StringVar(value="8")

        Label(self.gbWriting, anchor=W, text="PID (Hex):").grid(
            row=0, padx=3, sticky=NW
        )
        self.txtPID = Entry(self.gbWriting, width=11, textvariable=self.m_PIDTXT)
        self.txtPID.bind("<FocusOut>", self.txtPID_Leave)
        self.txtPID.grid(row=1, column=0, padx=5, pady=0, sticky=NW)

        Label(self.gbWriting, anchor=W, width=5, padx=5, text="DLC:").grid(
            row=0, column=1, sticky=NW
        )
        self.nudLength = Spinbox(
            self.gbWriting,
            width=10,
            from_=0,
            to=2047,
            textvariable=self.m_LengthNUD,
            command=self.nudLength_ValueChanged,
        )
        self.nudLength.grid(row=1, column=1, padx=5, pady=0, sticky=NW)
        self.nudLength.bind("<FocusOut>", self.nudLength_Leave)

        self.laLength = Label(self.gbWriting, anchor=W, text="Length: 9 B.")
        self.laLength.grid(row=0, column=2, columnspan=2, padx=3, sticky=NW)

        self.chbRRS = Checkbutton(self.gbWriting, text="RRS", variable=self.m_RRSCHB)
        self.chbRRS.grid(row=1, column=2, padx=0, pady=0, sticky=NW)

        self.chbSEC = Checkbutton(self.gbWriting, text="SEC", variable=self.m_SECCHB)
        self.chbSEC.grid(row=1, column=3, padx=0, pady=0, sticky=NW)

        Label(self.gbWriting, anchor=NW, text="SDT (Hex):").grid(
            row=2, padx=3, sticky=SW
        )
        self.txtSDT = Entry(self.gbWriting, width=11, textvariable=self.m_SDTTXT)
        self.txtSDT.bind("<FocusOut>", self.txtSDT_Leave)
        self.txtSDT.grid(row=3, column=0, padx=5, pady=0, sticky=NW)

        Label(self.gbWriting, anchor=NW, text="VCID (Hex):").grid(
            row=2, column=1, padx=3, sticky=SW
        )
        self.txtVCID = Entry(self.gbWriting, width=11, textvariable=self.m_VCIDTXT)
        self.txtVCID.bind("<FocusOut>", self.txtVCID_Leave)
        self.txtVCID.grid(row=3, column=1, padx=5, pady=0, sticky=NW)

        Label(self.gbWriting, anchor=NW, text="AF (Hex):").grid(
            row=2, column=2, columnspan=2, padx=3, sticky=SW
        )
        self.txtAF = Entry(self.gbWriting, width=15, textvariable=self.m_AFTXT)
        self.txtAF.bind("<FocusOut>", self.txtAF_Leave)
        self.txtAF.grid(row=3, column=2, columnspan=2, padx=5, pady=0, sticky=NW)

        self.txtData = Text(self.gbWriting, wrap="word", height=4, width=45)
        self.txtData.grid(row=1, column=4, rowspan=3, sticky=NW)

        scrollbar = Scrollbar(
            self.gbWriting, orient=VERTICAL, command=self.txtData.yview
        )
        scrollbar.grid(row=1, column=5, rowspan=3, sticky=NS)

        self.txtData.config(yscrollcommand=scrollbar.set)
        self.txtData.config(state="disabled")

        self.btnWrite = Button(
            self.gbWriting,
            width=8,
            state=DISABLED,
            text="Write",
            command=self.btnWrite_Click,
        )
        self.btnWrite.grid(row=3, column=6, padx=20, sticky=E)

    ## Initializes controls and variables in the groupbox "Information"
    ##
    def InitializeInformationWidgets(self):
        # Controls
        #
        self.yInfoScroll = Scrollbar(self.gbInfo, orient=VERTICAL)
        self.yInfoScroll.grid(row=0, column=1, sticky=N + S)

        self.lbxInfo = Listbox(
            self.gbInfo,
            width=90,
            height=6,
            activestyle="none",
            yscrollcommand=self.yInfoScroll.set,
        )
        self.lbxInfo.grid(row=0, column=0, padx=5, sticky="nwes")
        self.lbxInfo.bind("<Double-1>", self.btnInfoClear_Click)

        self.yInfoScroll["command"] = self.lbxInfo.yview
        self.lbxInfo.insert(
            END,
            "Select a Hardware and a configuration for it. Then click "
            "Initialize"
            " button",
        )
        self.lbxInfo.insert(
            END,
            "When activated, the Debug-Log file will be found in the same directory as this application",
        )
        self.lbxInfo.insert(
            END,
            "When activated, the PCAN-Trace file will be found in the same directory as this application",
        )

        Label(self.gbInfo, width=2, text=" ").grid(row=0, column=2)

        if IS_WINDOWS:
            btnPadx = 4
            btnPady = 25
        else:
            btnPadx = 0
            btnPady = 30

        self.btnGetVersions = Button(
            self.gbInfo,
            width=8,
            state=DISABLED,
            text="Versions",
            command=self.btnGetVersions_Click,
        )
        self.btnGetVersions.grid(row=0, column=3, padx=btnPadx, sticky=NW)

        self.btnInfoClear = Button(
            self.gbInfo,
            width=8,
            state=ACTIVE,
            text="Clear",
            command=self.btnInfoClear_Click,
        )
        self.btnInfoClear.grid(row=0, column=4, sticky=NW)

        self.btnStatus = Button(
            self.gbInfo,
            width=8,
            state=DISABLED,
            text="Status",
            command=self.btnStatus_Click,
        )
        self.btnStatus.grid(row=0, column=3, padx=btnPadx, pady=btnPady, sticky=W)

        self.btnReset = Button(
            self.gbInfo,
            width=8,
            state=DISABLED,
            text="Reset",
            command=self.btnReset_Click,
        )
        self.btnReset.grid(row=0, column=4, pady=btnPady, sticky=W)

    ## Creates random data bytes for a CAN XL message to be sent
    ##
    def RandomizeData(self):
        data = bytearray(
            random.getrandbits(8) for _ in range(int(self.m_LengthNUD.get()) + 1)
        )
        self.m_DataEdits = data

    ## Updates the control showing the CAN XL data in the UI
    ##
    def UpdateData(self):
        self.txtData.config(state="normal")
        self.txtData.delete("1.0", END)
        self.txtData.insert(END, " ".join("{:02X}".format(b) for b in self.m_DataEdits))
        self.txtData.config(state="disabled")

    ## Randomizes and show the CAN data for send
    ##
    def FillRandomData(self):
        self.RandomizeData()
        self.UpdateData()

    ## Centers the app from in the middle of the screen
    ##
    def CenterTheWindow(self):
        Desktop = self.m_Parent.winfo_toplevel()
        desktopWidth = Desktop.winfo_screenwidth()
        desktopHeight = Desktop.winfo_screenheight()

        self.m_Parent.geometry(
            "{0}x{1}+{2}+{3}".format(
                self.m_Width,
                self.m_Height,
                (desktopWidth - self.m_Width) / 2,
                (desktopHeight - self.m_Height) / 2,
            )
        )

    ## Configures the Debug-Log file of PCAN-Basic
    ##
    def ConfigureLogFile(self):
        # Sets the mask to catch all events
        #
        iBuffer = LOG_FUNCTION_ALL

        # Configures the log file.
        # NOTE: The Log capability is to be used with the NONEBUS Handle. Other handle than this will
        # cause the function fail.
        #
        self.m_objPCANBasic.SetValue(PCAN_NONEBUS, PCAN_LOG_CONFIGURE, iBuffer)

    ## Configures the PCAN-Trace file for a PCAN-Basic Channel
    ##
    def ConfigureTraceFile(self):
        # Configure the maximum size of a trace file to 5 megabytes
        #
        iBuffer = 5
        stsResult = self.m_objPCANBasic.SetValue(
            self.m_PcanHandle, PCAN_TRACE_SIZE, iBuffer
        )
        if stsResult != PCAN_ERROR_OK:
            self.IncludeTextMessage(self.GetFormatedError(stsResult))

        # Configure the way how trace files are created:
        # * Standard name is used
        # * Existing file is ovewritten,
        # * Only one file is created.
        # * Recording stopts when the file size reaches 5 megabytes.
        #
        iBuffer = TRACE_FILE_SINGLE | TRACE_FILE_OVERWRITE
        stsResult = self.m_objPCANBasic.SetValue(
            self.m_PcanHandle, PCAN_TRACE_CONFIGURE, iBuffer
        )
        if stsResult != PCAN_ERROR_OK:
            self.IncludeTextMessage(self.GetFormatedError(stsResult))

    ## Help Function used to get an error as text
    ##
    def GetFormatedError(self, error):
        # Gets the text using the GetErrorText API function
        # If the function success, the translated error is returned. If it fails,
        # a text describing the current error is returned.
        #
        stsReturn = self.m_objPCANBasic.GetErrorText(error, 0)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(
                error
            )
        else:
            return stsReturn[1]

    ## Includes a new line of text into the information Listview
    ##
    def IncludeTextMessage(self, strMsg):
        self.lbxInfo.insert(END, strMsg)
        self.lbxInfo.see(END)

    ## Gets the current status of the PCAN-Basic message filter
    ##
    def GetFilterStatus(self):
        # Tries to get the sttaus of the filter for the current connected hardware
        #
        stsResult = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_MESSAGE_FILTER)

        # If it fails, a error message is shown
        #
        if stsResult[0] != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(stsResult[0]))
            return (False,)
        else:
            return True, stsResult[1]

    ## Activates/deaactivates the different controls of the form according
    ## with the current connection status
    ##
    def SetConnectionStatus(self, bConnected=True):
        # Gets the status values for each case
        #
        self.m_Connected = bConnected
        if bConnected:
            stsConnected = ACTIVE
            stsNotConnected = DISABLED
        else:
            stsConnected = DISABLED
            stsNotConnected = ACTIVE

        # Buttons
        #
        self.btnInit["state"] = stsNotConnected
        if (self.m_ReadingRDB.get() == 0) and bConnected:
            self.btnRead["state"] = ACTIVE
        else:
            self.btnRead["state"] = DISABLED
        self.btnWrite["state"] = stsConnected
        self.btnRelease["state"] = stsConnected
        self.btnFilterApply["state"] = stsConnected
        self.btnFilterQuery["state"] = stsConnected
        self.btnGetVersions["state"] = stsConnected
        self.btnStatus["state"] = stsConnected
        self.btnReset["state"] = stsConnected

        # ComboBoxs
        #
        self.cbbChannel["state"] = stsNotConnected

        # Hardware configuration and read mode
        #
        if not bConnected:
            self.cbbChannel_SelectedIndexChanged(self.cbbChannel["value"])
            self.tmrDisplayManage(False)
        else:
            self.rdbTimer_CheckedChanged()
            self.tmrDisplayManage(True)

    ## Gets the formated text for a PCAN-Basic channel handle
    ##
    def FormatChannelName(self, handle, protocol):
        if handle < 0x100:
            devDevice = TPCANDevice(handle >> 4)
            byChannel = handle & 0xF
        else:
            devDevice = TPCANDevice(handle >> 8)
            byChannel = handle & 0xFF

        toRet = StringVar()

        strFormat = "{0}:{1} {2} ({3:X2}h)"
        bIsFD = (protocol & CANProtocol.CAN_FD) == CANProtocol.CAN_FD
        bIsXL = (protocol & CANProtocol.CAN_XL) == CANProtocol.CAN_XL

        if bIsXL & bIsFD:
            toRet.set(
                "%s: FD/XL %s (%.2Xh)"
                % (self.GetDeviceName(devDevice.value), byChannel, handle)
            )
        elif bIsFD:
            toRet.set(
                "%s: FD %s (%.2Xh)"
                % (self.GetDeviceName(devDevice.value), byChannel, handle)
            )
        elif bIsXL:
            toRet.set(
                "%s: XL %s (%.2Xh)"
                % (self.GetDeviceName(devDevice.value), byChannel, handle)
            )
        else:
            toRet.set(
                "%s %s (%.2Xh)"
                % (self.GetDeviceName(devDevice.value), byChannel, handle)
            )

        return toRet.get()

    ## Gets the name of a PCAN device
    ##
    def GetDeviceName(self, handle):
        switcher = {
            PCAN_NONEBUS.value: "PCAN_NONEBUS",
            PCAN_PCI.value: "PCAN_PCI",
            PCAN_USB.value: "PCAN_USB",
            PCAN_LAN.value: "PCAN_LAN",
        }

        return switcher.get(handle, "UNKNOWN")

    ## Button btnHwRefresh handler
    ##
    def DoRefresh(self):

        # Clears the Channel comboBox and fill it again with
        # the detected hardware
        #
        items = []
        self.cbbChannel.subwidget("listbox").delete(0, Tix.END)

        result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_ATTACHED_CHANNELS)
        if result[0] == PCAN_ERROR_OK:
            # Include only connectable channels
            #
            for channel in result[1]:

                protocol = CANProtocol.CAN
                if (channel.device_features & FEATURE_XL_CAPABLE) == FEATURE_XL_CAPABLE:
                    protocol |= CANProtocol.CAN_XL
                if (channel.device_features & FEATURE_FD_CAPABLE) == FEATURE_FD_CAPABLE:
                    protocol |= CANProtocol.CAN_FD

                if (
                    channel.channel_condition & PCAN_CHANNEL_AVAILABLE
                    == PCAN_CHANNEL_AVAILABLE
                    and protocol & CANProtocol.CAN_XL == CANProtocol.CAN_XL
                ):
                    items.append(
                        self.FormatChannelName(
                            channel.channel_handle,
                            protocol,
                        )
                    )

        items.sort()
        self.cbbChannel
        for name in items:
            self.cbbChannel.insert(Tix.END, name)
        self.cbbChannel["selection"] = self.cbbChannel.pick(Tix.END)
        self.cbbChannel.insert(Tix.END, "... refresh ...")

    ################################################################################################################################################
    ### Message-proccessing functions
    ################################################################################################################################################
    def GetMsgString(self, msgStatus):
        # The Type of the message
        strTemp = msgStatus.TypeString
        toRet = strTemp + " " * (self.m_ListColSpace[COL_TYPE] - len(strTemp))
        # The msg PID
        strTemp = msgStatus.PidString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_PID] - len(strTemp)))
        # The length of the msg
        strTemp = str(GetLengthFromDLC(msgStatus.CANMsg.DLC, msgStatus.CANMsg.MSGTYPE))
        toRet = toRet + (
            strTemp + " " * (self.m_ListColSpace[COL_LENGTH] - len(strTemp))
        )
        # The msg SDT
        strTemp = msgStatus.SdtString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_SDT] - len(strTemp)))
        # The msg VCID
        strTemp = msgStatus.VcidString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_VCID] - len(strTemp)))
        # The msg AF
        strTemp = msgStatus.AfString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_AF] - len(strTemp)))
        # The timestamp
        strTemp = msgStatus.TimeString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_TIME] - len(strTemp)))
        # The count of msgs
        strTemp = str(msgStatus.Count)
        toRet = toRet + (
            strTemp + " " * (self.m_ListColSpace[COL_COUNT] - len(strTemp))
        )
        # The Data
        strTemp = msgStatus.DataString
        toRet = toRet + (strTemp + " " * (self.m_ListColSpace[COL_DATA] - len(strTemp)))

        return toRet

    ## Display CAN messages in the Message-ListView
    ##
    def DisplayMessages(self):
        with self._lock:
            for msgStatus in self.m_LastMsgsList:
                if not msgStatus.MarkedAsInserted:
                    self.lstMessages.insert(
                        msgStatus.Position, text=self.GetMsgString(msgStatus)
                    )
                    msgStatus.MarkedAsInserted = True
                elif msgStatus.MarkedAsUpdated:
                    self.lstMessages.delete(msgStatus.Position)
                    self.lstMessages.insert(
                        msgStatus.Position, text=self.GetMsgString(msgStatus)
                    )
                    msgStatus.MarkedAsUpdated = False

    ## Inserts a new entry for a new message in the Message-ListView
    ##
    def InsertMsgEntry(self, newMsg, timeStamp):
        # Format the new time information
        #
        with self._lock:
            # The status values associated with the new message are created
            #
            msgStsCurrentMsg = MessageStatus(
                newMsg, timeStamp, len(self.m_LastMsgsList)
            )
            msgStsCurrentMsg.MarkedAsInserted = False
            msgStsCurrentMsg.ShowingPeriod = self.m_ShowPeriod
            self.m_LastMsgsList.append(msgStsCurrentMsg)

    def ProcessMessageXL(self, *args):
        with self._lock:
            # Split the arguments. [0] TPCANMsgXL, [1] TPCANTimestampXL
            #
            theMsg = args[0][0]
            itsTimeStamp = args[0][1]

            for msg in self.m_LastMsgsList:
                if (
                    (msg.CANMsg.PID == theMsg.PID)
                    and (msg.CANMsg.MSGTYPE == theMsg.MSGTYPE)
                    and (msg.CANMsg.SDT == theMsg.SDT)
                    and (msg.CANMsg.VCID == theMsg.VCID)
                    and (msg.CANMsg.AF == theMsg.AF)
                    and (msg.CANMsg.RRS == theMsg.RRS)
                    and (msg.CANMsg.SEC == theMsg.SEC)
                ):
                    msg.Update(theMsg, itsTimeStamp)
                    return
            self.InsertMsgEntry(theMsg, itsTimeStamp)

    ## Thread-Function used for reading PCAN-Basic messages
    ##
    def CANReadThreadFunc(self):
        try:
            self.m_Terminated = False

            # Configures the Receive-Event.
            #
            stsResult = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_RECEIVE_EVENT, self.m_ReceiveEvent.handle
            )

            if stsResult != PCAN_ERROR_OK:
                print("Error: " + self.GetFormatedError(stsResult))
            else:
                while not self.m_Terminated:
                    if (
                        win32event.WaitForSingleObject(self.m_ReceiveEvent, 50)
                        == win32event.WAIT_OBJECT_0
                    ):
                        self.ReadMessages()

                # Resets the Event-handle configuration
                #
                self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_RECEIVE_EVENT, 0)
        except:
            print("Error occurred while processing CAN data")

    ################################################################################################################################################
    ### Event Handlers
    ################################################################################################################################################

    ## Form-Closing Function / Finish function
    ##
    def Form_OnClosing(self, event=None):
        # close current connection
        # if the event-thread is running the process would not terminate
        if self.btnRelease["state"] != DISABLED:
            self.btnRelease_Click()
        # Releases the used PCAN-Basic channel
        #
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)
        """Quit our mainloop."""
        self.exit = 0

    ## Button btnInit handler
    ##
    def btnInit_Click(self):

        # Connects a selected PCAN-Basic channel
        #
        result = self.m_objPCANBasic.InitializeXL(
            self.m_PcanHandle, self.m_BitrateTXT.get()
        )

        if result != PCAN_ERROR_OK:
            if result != PCAN_ERROR_CAUTION:
                tkMessageBox.showinfo("Error!", self.GetFormatedError(result))
            else:
                self.IncludeTextMessage(
                    "******************************************************"
                )
                self.IncludeTextMessage(
                    "The bitrate being used is different than the given one"
                )
                self.IncludeTextMessage(
                    "******************************************************"
                )
                result = PCAN_ERROR_OK
        else:
            # Prepares the PCAN-Basic's PCAN-Trace file
            #
            self.ConfigureTraceFile()

        # Sets the connection status of the form
        #
        self.SetConnectionStatus(result == PCAN_ERROR_OK)

    ## Button btnRelease handler
    ##
    def btnRelease_Click(self):
        if WINDOWS_EVENT_SUPPORT:
            if self.m_ReadThread != None:
                self.m_Terminated = True
                self.m_ReadThread.join()
                self.m_ReadThread = None

        # We stop to read from the CAN queue
        #
        self.tmrRead.stop()

        # Releases a current connected PCAN-Basic channel
        #
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)

        # Sets the connection status of the main-form
        #
        self.SetConnectionStatus(False)

    ## Button btnFilterApply handler
    ##
    def btnFilterApply_Click(self):
        # Gets the current status of the message filter
        #
        filterRet = self.GetFilterStatus()

        if not filterRet[0]:
            return

        # The filter will be full opened or complete closed
        #
        if self.m_FilteringRDB.get() == 0:
            filterMode = PCAN_FILTER_CLOSE
            textEnd = "closed"
        else:
            filterMode = PCAN_FILTER_OPEN
            textEnd = "opened"

        # The filter is configured
        #
        result = self.m_objPCANBasic.SetValue(
            self.m_PcanHandle, PCAN_MESSAGE_FILTER, filterMode
        )

        # If success, an information message is written, if it is not, an error message is shown
        #
        if result == PCAN_ERROR_OK:
            self.IncludeTextMessage("The filter was successfully " + textEnd)
        else:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result))

    ## Button btnFilterQuery handler
    ##
    def btnFilterQuery_Click(self):
        # Queries the current status of the message filter
        #
        filterRet = self.GetFilterStatus()

        if filterRet[0]:
            if filterRet[1] == PCAN_FILTER_CLOSE:
                self.IncludeTextMessage("The Status of the filter is: closed.")
            elif filterRet[1] == PCAN_FILTER_OPEN:
                self.IncludeTextMessage("The Status of the filter is: full opened.")
            else:
                self.IncludeTextMessage(
                    "The Status ofself.tmrRead the filter is: Invalid."
                )

    ## Button btnParameterSet handler
    ##
    def btnParameterSet_Click(self):
        currentVal = self.cbbParameter["selection"]
        iVal = self.m_PARAMETERS[currentVal]

        if self.m_ConfigurationRDB.get() == 1:
            iBuffer = PCAN_PARAMETER_ON
            lastStr = "activated"
            lastStr2 = "ON"
            lastStr3 = "enabled"
        else:
            iBuffer = PCAN_PARAMETER_OFF
            lastStr = "deactivated"
            lastStr2 = "OFF"
            lastStr3 = "disabled"

        # The device identifier of a channel will be set
        #
        if iVal == PCAN_DEVICE_ID:
            iBuffer = int(self.m_DeviceIdOrDelayNUD.get())
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_DEVICE_ID, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The desired Device-ID was successfully configured"
                )

        # The 5 Volt Power feature of a channel will be set
        #
        elif iVal == PCAN_5VOLTS_POWER:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_5VOLTS_POWER, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The USB/PC-Card 5 power was successfully " + lastStr
                )

        # The feature for automatic reset on BUS-OFF will be set
        #
        elif iVal == PCAN_BUSOFF_AUTORESET:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_BUSOFF_AUTORESET, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The automatic-reset on BUS-OFF was successfully " + lastStr
                )

        # The CAN option "Listen Only" will be set
        #
        elif iVal == PCAN_LISTEN_ONLY:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_LISTEN_ONLY, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The CAN option " "Listen Only" " was successfully " + lastStr
                )

        # The feature for logging debug-information will be set
        #
        elif iVal == PCAN_LOG_STATUS:
            result = self.m_objPCANBasic.SetValue(
                PCAN_NONEBUS, PCAN_LOG_STATUS, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The feature for logging debug information was successfully "
                    + lastStr
                )

        # The channel option "Receive Status" will be set
        #
        elif iVal == PCAN_RECEIVE_STATUS:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_RECEIVE_STATUS, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The channel option " "Receive Status" " was set to  " + lastStr2
                )

        # The feature for tracing will be set
        #
        elif iVal == PCAN_TRACE_STATUS:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_TRACE_STATUS, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The feature for tracing data was successfully " + lastStr
                )

        # The feature for tracing will be set
        #
        elif iVal == PCAN_CHANNEL_IDENTIFYING:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The procedure for channel identification was successfully "
                    + lastStr
                )

        # The feature for using an already configured bit rate will be set
        #
        elif iVal == PCAN_BITRATE_ADAPTING:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_BITRATE_ADAPTING, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The feature for bit rate adaptation was successfully " + lastStr
                )

        # The option "Allow Status Frames" will be set
        #
        elif iVal == PCAN_ALLOW_STATUS_FRAMES:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_ALLOW_STATUS_FRAMES, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The reception of Status frames was successfully " + lastStr3
                )

        # The option "Allow RTR Frames" will be set
        #
        elif iVal == PCAN_ALLOW_RTR_FRAMES:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_ALLOW_RTR_FRAMES, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The reception of RTR frames was successfully " + lastStr3
                )

        # The option "Allow Error Frames" will be set
        #
        elif iVal == PCAN_ALLOW_ERROR_FRAMES:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_ALLOW_ERROR_FRAMES, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The reception of Error frames was successfully " + lastStr3
                )

        # The option "Interframes Delay" will be set
        #
        elif iVal == PCAN_INTERFRAME_DELAY:
            iBuffer = int(self.m_DeviceIdOrDelayNUD.get())
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_INTERFRAME_DELAY, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The delay between transmitting frames was successfully set"
                )

        # The option "Allow Echo Frames" will be set
        #
        elif iVal == PCAN_ALLOW_ECHO_FRAMES:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_ALLOW_ECHO_FRAMES, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The reception of Echo frames was successfully " + lastStr3
                )

        # The option "Hard Reset Status" will be set
        #
        elif iVal == PCAN_HARD_RESET_STATUS:
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_HARD_RESET_STATUS, iBuffer
            )
            if result == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The activation of a hard reset within the method PCANBasic.Reset was successfully "
                    + lastStr3
                )

        # The current parameter is invalid
        #
        else:
            result = (PCAN_ERROR_UNKNOWN, 0)
            tkMessageBox.showinfo("Error!", "Wrong parameter code.")

        # If the function fail, an error message is shown
        #
        if result != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result))

    ## Button btnParameterGet handler
    ##
    def btnParameterGet_Click(self):
        currentVal = self.cbbParameter["selection"]
        iVal = self.m_PARAMETERS[currentVal]

        # The device identifier of a channel will be retrieved
        #
        if iVal == PCAN_DEVICE_ID:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_DEVICE_ID)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The configured Device-ID is {0:X}h".format(result[1])
                )

        # The activation status of the 5 Volt Power feature of a channel will be retrieved
        #
        elif iVal == PCAN_5VOLTS_POWER:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_5VOLTS_POWER)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The 5-Volt Power of the USB/PC-Card is " + lastStr
                )

        # The activation status of the feature for automatic reset on BUS-OFF will be retrieved
        #
        elif iVal == PCAN_BUSOFF_AUTORESET:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BUSOFF_AUTORESET
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The automatic-reset on BUS-OFF is " + lastStr)

        # The activation status of the CAN option "Listen Only" will be retrieved
        #
        elif iVal == PCAN_LISTEN_ONLY:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_LISTEN_ONLY)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The CAN option " "Listen Only" " is " + lastStr
                )

        # The activation status for the feature for logging debug-information will be retrieved
        #
        elif iVal == PCAN_LOG_STATUS:
            result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_LOG_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The feature for logging debug information is " + lastStr
                )

        # The activation status of the channel option "Receive Status"  will be retrieved
        #
        elif iVal == PCAN_RECEIVE_STATUS:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_RECEIVE_STATUS
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The channel option " "Receive Status" " is " + lastStr
                )

        # The Number of the CAN-Controller used by a PCAN-Channel
        #
        elif iVal == PCAN_CONTROLLER_NUMBER:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_CONTROLLER_NUMBER
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The CAN Controller number is {0}".format(result[1])
                )

        # The activation status for the feature for tracing data will be retrieved
        #
        elif iVal == PCAN_TRACE_STATUS:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_TRACE_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage("The feature for tracing data is " + lastStr)

        # The activation status of the Channel Identifying procedure will be retrieved
        #
        elif iVal == PCAN_CHANNEL_IDENTIFYING:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The identification procedure of the selected channel is " + lastStr
                )

        # The extra capabilities of a hardware will asked
        #
        elif iVal == PCAN_CHANNEL_FEATURES:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_CHANNEL_FEATURES
            )
            if result[0] == PCAN_ERROR_OK:
                if (result[1] & FEATURE_FD_CAPABLE) == FEATURE_FD_CAPABLE:
                    lastStr = "does support"
                else:
                    lastStr = "DOESN'T SUPPORT"
                self.IncludeTextMessage(
                    "The channel %s Flexible Data-Rate (CAN-FD) " % lastStr
                )
                if (result[1] & FEATURE_XL_CAPABLE) == FEATURE_XL_CAPABLE:
                    lastStr = "does support"
                else:
                    lastStr = "DOESN'T SUPPORT"
                self.IncludeTextMessage("The channel %s Extra Long (CAN-XL) " % lastStr)
                if (result[1] & FEATURE_DELAY_CAPABLE) == FEATURE_DELAY_CAPABLE:
                    lastStr = "does support"
                else:
                    lastStr = "DOESN'T SUPPORT"
                self.IncludeTextMessage(
                    "The channel %s an inter-frame delay for sending messages "
                    % lastStr
                )
                if (result[1] & FEATURE_IO_CAPABLE) == FEATURE_IO_CAPABLE:
                    lastStr = "does allow"
                else:
                    lastStr = "DOESN'T ALLOW"
                self.IncludeTextMessage("The channel %s using I/O pins " % lastStr)

        # The status of the bit rate adapting feature will be retrieved
        #
        elif iVal == PCAN_BITRATE_ADAPTING:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BITRATE_ADAPTING
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "ON"
                else:
                    lastStr = "OFF"
                self.IncludeTextMessage(
                    "The feature for bit rate adaptation is %s" % lastStr
                )

        # The bit rate of the connected nominal channel will be retrieved (String value)
        #
        elif iVal == PCAN_BITRATE_INFO_CC:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BITRATE_INFO_CC
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The bit rate Nominal of the channel is represented by the following values:"
                )
                for strPart in result[1].decode("utf-8").split(","):
                    self.IncludeTextMessage("   * " + strPart)

        # The bit rate of the connected FD channel will be retrieved (String value)
        #
        elif iVal == PCAN_BITRATE_INFO_FD:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BITRATE_INFO_FD
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The bit rate FD of the channel is represented by the following values:"
                )
                for strPart in result[1].decode("utf-8").split(","):
                    self.IncludeTextMessage("   * " + strPart)

        # The bit rate of the connected XL channel will be retrieved (String value)
        #
        elif iVal == PCAN_BITRATE_INFO_XL:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BITRATE_INFO_XL
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The bit rate XL of the channel is represented by the following values:"
                )
                for strPart in result[1].decode("utf-8").split(","):
                    self.IncludeTextMessage("   * " + strPart)

        # The nominal speed configured on the CAN bus will be retrived (bits/second)
        #
        elif iVal == PCAN_BUSSPEED_NOMINAL:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_BUSSPEED_NOMINAL
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The nominal speed of the channel is %d bit/s" % result[1]
                )

        # The FD speed configured on the CAN bus will be retrived (bits/second)
        #
        elif iVal == PCAN_BUSSPEED_FD:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BUSSPEED_FD)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The FD speed of the channel is %d bit/s" % result[1]
                )

        # The XL speed configured on the CAN bus will be retrived (bits/second)
        #
        elif iVal == PCAN_BUSSPEED_XL:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_BUSSPEED_XL)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The XL speed of the channel is %d bit/s" % result[1]
                )

        # The IP address of a LAN channel as string, in IPv4 format
        #
        elif iVal == PCAN_IP_ADDRESS:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_IP_ADDRESS)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The IP address of the channel is %s" % result[1]
                )

        # The running status of the LAN Service
        #
        elif iVal == PCAN_LAN_SERVICE_STATUS:
            result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_LAN_SERVICE_STATUS)
            if result[0] == PCAN_ERROR_OK:
                if result[1] == SERVICE_STATUS_RUNNING:
                    lastStr = "running"
                else:
                    lastStr = "NOT running"
                self.IncludeTextMessage("The LAN service is %s" % lastStr)

        # The reception of Status frames
        #
        elif iVal == PCAN_ALLOW_STATUS_FRAMES:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_ALLOW_STATUS_FRAMES
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage(
                    "The reception of Status frames is %s" % lastStr
                )

        # The reception of RTR frames
        #
        elif iVal == PCAN_ALLOW_RTR_FRAMES:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_ALLOW_RTR_FRAMES
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of RTR frames is %s" % lastStr)

        # The reception of Error frames
        #
        elif iVal == PCAN_ALLOW_ERROR_FRAMES:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_ALLOW_ERROR_FRAMES
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of Error frames is %s" % lastStr)

        # The Interframe delay of an USB channel will be retrieved
        #
        elif iVal == PCAN_INTERFRAME_DELAY:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_INTERFRAME_DELAY
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage(
                    "The configured interframe delay is {0} µs".format(result[1])
                )

        # The reception of Echo frames
        #
        elif iVal == PCAN_ALLOW_ECHO_FRAMES:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_ALLOW_ECHO_FRAMES
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "enabled"
                else:
                    lastStr = "disabled"
                self.IncludeTextMessage("The reception of Echo frames is %s" % lastStr)

        # The activation of Hard Reset
        #
        elif iVal == PCAN_HARD_RESET_STATUS:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_HARD_RESET_STATUS
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == PCAN_PARAMETER_ON:
                    lastStr = "performing"
                else:
                    lastStr = "NOT performing"
                self.IncludeTextMessage(
                    "The method PCANBasic.Reset is %s a hardware reset" % lastStr
                )

        # The direction of the communication with a LAN channel
        #
        elif iVal == PCAN_LAN_CHANNEL_DIRECTION:
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_LAN_CHANNEL_DIRECTION
            )
            if result[0] == PCAN_ERROR_OK:
                if result[1] == LAN_DIRECTION_READ:
                    lastStr = "incoming only"
                elif result[1] == LAN_DIRECTION_WRITE:
                    lastStr = "outgoing only"
                elif result[1] == LAN_DIRECTION_READ_WRITE:
                    lastStr = "bidirectional"
                else:
                    lastStr = "undefined (0x%.4X)" % result[1]
                self.IncludeTextMessage("The communication flow is: %s" % lastStr)

        # The GUID of the device
        #
        elif iVal == PCAN_DEVICE_GUID:
            result = self.m_objPCANBasic.GetValue(self.m_PcanHandle, PCAN_DEVICE_GUID)
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("The GUID of the device is %s" % result[1])

        # The current parameter is invalid
        #
        else:
            result = (PCAN_ERROR_UNKNOWN, 0)
            tkMessageBox.showinfo("Error!", "Wrong parameter code.")

        # If the function fail, an error message is shown
        #
        if result[0] != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result[0]))

    def ReadMessageXL(self):
        # We execute the "ReadXL" function of the PCANBasic
        #
        result = self.m_objPCANBasic.ReadXL(self.m_PcanHandle)

        if result[0] == PCAN_ERROR_OK:
            # We show the received message
            #
            self.ProcessMessageXL(result[1:])

        return result[0]

    def WriteFrameXL(self):
        # We create a TPCANMsgXL message structure
        #
        CANMsg = TPCANMsgXL()

        # We configurate the Message.
        #
        CANMsg.PID = int(self.m_PIDTXT.get(), 16)
        CANMsg.DLC = int(self.m_LengthNUD.get())
        CANMsg.MSGTYPE = PCAN_MESSAGE_XL
        CANMsg.SDT = int(self.m_SDTTXT.get(), 16)
        CANMsg.VCID = int(self.m_VCIDTXT.get(), 16)
        CANMsg.AF = int(self.m_AFTXT.get(), 16)
        CANMsg.RRS = int(self.m_RRSCHB.get())
        CANMsg.SEC = int(self.m_SECCHB.get())

        iLength = GetLengthFromDLC(CANMsg.DLC, CANMsg.MSGTYPE)
        # We get so much data as the Len of the message
        #
        for i in range(iLength):
            CANMsg.DATA[i] = self.m_DataEdits[i]

        # The message is sent to the configured hardware
        #
        return self.m_objPCANBasic.WriteXL(self.m_PcanHandle, CANMsg)

    def ReadMessages(self):
        stsResult = PCAN_ERROR_OK

        # We read at least one time the queue looking for messages.
        # If a message is found, we look again trying to find more.
        # If the queue is empty or an error occurr, we get out from
        # the dowhile statement.
        #
        while self.m_CanRead and not (stsResult & PCAN_ERROR_QRCVEMPTY):
            stsResult = self.ReadMessageXL()
            if stsResult == PCAN_ERROR_ILLOPERATION:
                break

    ## Button btnRead handler
    ##
    def btnRead_Click(self):
        # We execute the "Read" function of the PCANBasic
        #
        result = self.ReadMessageXL()
        if result != PCAN_ERROR_OK:
            # If an error occurred, an information message is included
            #
            self.IncludeTextMessage(self.GetFormatedError(result))

    ## Button btnGetVersions handler
    ##
    def btnGetVersions_Click(self):
        # We get the vesion of the PCAN-Basic API
        #
        result = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_API_VERSION)
        if result[0] == PCAN_ERROR_OK:
            self.IncludeTextMessage("API Version: " + result[1])

            # We get the version of the firmware on the device
            #
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_FIRMWARE_VERSION
            )
            if result[0] == PCAN_ERROR_OK:
                self.IncludeTextMessage("Firmware Version: " + result[1])

            # We get the driver version of the channel being used
            #
            result = self.m_objPCANBasic.GetValue(
                self.m_PcanHandle, PCAN_CHANNEL_VERSION
            )
            if result[0] == PCAN_ERROR_OK:
                # Because this information contains line control characters (several lines)
                # we split this also in several entries in the Information List-Box
                #
                lines = string.split(result[1], "\n")
                self.IncludeTextMessage("Channel/Driver Version: ")
                for line in lines:
                    self.IncludeTextMessage("     * " + line)

        # If an error ccurred, a message is shown
        #
        if result[0] != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedError(result[0]))

    ## Button btnMsgClear handler
    ##
    def btnMsgClear_Click(self, *args):
        # The information contained in the messages List-View
        # is cleared
        #
        with self._lock:
            self.lstMessages.delete(0, END)
            self.m_LastMsgsList = []

    ## Button btnInfoClear handler
    ##
    def btnInfoClear_Click(self, event=None):
        # The information contained in the Information List-Box
        # is cleared
        #
        self.lbxInfo.delete(0, END)

    ## Button btnWrite handler
    ##
    def btnWrite_Click(self):
        # Send the message
        #
        stsResult = self.WriteFrameXL()

        # The message was successfully sent
        #
        if stsResult == PCAN_ERROR_OK:
            self.IncludeTextMessage("Message was successfully SENT")
        else:
            # An error occurred.  We show the error.
            #
            tkMessageBox.showinfo(self.GetFormatedError(stsResult))

    ## Button btnReset handler
    ##
    def btnReset_Click(self):
        # Resets the receive and transmit queues of a PCAN Channel.
        #
        result = self.m_objPCANBasic.Reset(self.m_PcanHandle)

        # If it fails, a error message is shown
        #
        if result != PCAN_ERROR_OK:
            tkMessageBox.showinfo("Error!", self.GetFormatedTex(result))
        else:
            self.IncludeTextMessage("Receive and transmit queues successfully reset")

    ## Button btnStatus handler
    ##
    def btnStatus_Click(self):
        # Gets the current BUS status of a PCAN Channel.
        #
        result = self.m_objPCANBasic.GetStatus(self.m_PcanHandle)

        # Switch On Error Name
        #
        if result == PCAN_ERROR_INITIALIZE:
            errorName = "PCAN_ERROR_INITIALIZE"
        elif result == PCAN_ERROR_BUSLIGHT:
            errorName = "PCAN_ERROR_BUSLIGHT"
        elif result == PCAN_ERROR_BUSWARNING:
            errorName = "PCAN_ERROR_BUSWARNING"
        elif result == PCAN_ERROR_BUSPASSIVE:
            errorName = "PCAN_ERROR_BUSPASSIVE"
        elif result == PCAN_ERROR_BUSOFF:
            errorName = "PCAN_ERROR_BUSOFF"
        elif result == PCAN_ERROR_OK:
            errorName = "PCAN_ERROR_OK"
        else:
            errorName = "See Documentation"

        # Display Message
        #
        self.IncludeTextMessage("Status: {0} ({1:X}h)".format(errorName, result))

    ## Combobox cbbChannel handler
    ##
    def cbbChannel_SelectedIndexChanged(self, currentValue):
        # Get the handle from the text being shown
        #
        strChannel = self.cbbChannel["value"]

        if strChannel == "":
            return

        if "refresh" in strChannel:
            self.DoRefresh()
            return

        startIndex = strChannel.index("(") + 1
        strChannel = strChannel[startIndex : startIndex + 3]
        strChannel = strChannel.replace("h", "")
        self.m_PcanHandle = int(strChannel, 16)

    ## Combobox cbbParameter handler
    ##
    def cbbParameter_SelectedIndexChanged(self, currentValue=None):
        # Activates/deactivates controls according with the selected
        # PCAN-Basic parameter
        #
        bIsRB = (
            currentValue != "Device ID" and currentValue != "Interframe Transmit Delay"
        )
        if currentValue == "Interframe Transmit Delay":
            self.m_DeviceIdOrDelay.set("Delay (µs):")
        else:
            self.m_DeviceIdOrDelay.set("Device ID:")
        root.update_idletasks()

        if bIsRB:
            self.rdbParamActive["state"] = ACTIVE
            self.rdbParamInactive["state"] = ACTIVE
            self.nudDeviceIdOrDelay["state"] = DISABLED
        else:
            self.rdbParamActive["state"] = DISABLED
            self.rdbParamInactive["state"] = DISABLED
            self.nudDeviceIdOrDelay["state"] = NORMAL

    ## checkbutton chbShowPeriod handler
    ##
    def chbShowPeriod_CheckedChanged(self):
        with self._lock:
            self.m_ShowPeriod = self.m_ShowPeriodCHB.get()
            for msgStatus in self.m_LastMsgsList:
                msgStatus.ShowingPeriod = self.m_ShowPeriod

    ## Radiobutton rdbTimer handler
    ##
    def rdbTimer_CheckedChanged(self):
        self.m_CanRead = False

        if self.btnRelease["state"] == DISABLED:
            return
        # Stop the timer, if running
        #
        self.tmrRead.stop()

        # Stop the thread if running
        #
        if WINDOWS_EVENT_SUPPORT:
            if self.m_ReadThread != None:
                self.m_Terminated = True
                self.m_ReadThread.join()
                self.m_ReadThread = None

        self.m_CanRead = True

        # According with the kind of reading, a timer, a thread or a button will be enabled
        #
        if self.m_ReadingRDB.get() == 1:
            self.tmrRead.start()

        if self.m_ReadingRDB.get() == 2:
            if WINDOWS_EVENT_SUPPORT:
                self.m_Terminate = False
                self.m_ReadThread = threading.Thread(None, self.CANReadThreadFunc)
                self.m_ReadThread.start()
            else:
                tkMessageBox.showerror(
                    "Module ''win32Event'' not found",
                    message="The Win32 Library ('Python Win32 Extensions') is not installed.",
                )

        if (self.btnRelease["state"] != DISABLED) and (self.m_ReadingRDB.get() == 0):
            self.btnRead["state"] = ACTIVE
        else:
            self.btnRead["state"] = DISABLED

    ## Entry txtPID OnLeave handler
    ##
    def txtPID_Leave(self, *args):
        # Sets the text length and maximum PID value
        #
        iTextLength = 3
        uiMaxValue = 0x7FF

        try:
            iValue = int(self.m_PIDTXT.get(), 16)
        except ValueError:
            iValue = 0
        finally:
            # The Textbox for the PID is represented with 3 characters
            # We check that the PID is not bigger than current maximum value
            #
            if iValue > uiMaxValue:
                iValue = uiMaxValue
            self.m_PIDTXT.set("{0:0{1}X}".format(iValue, iTextLength))
            return True

    ## Entry txtSDT OnLeave handler
    ##
    def txtSDT_Leave(self, *args):
        # Sets the text length and maximum SDT value
        #
        iTextLength = 2
        uiMaxValue = 0xFF

        try:
            iValue = int(self.m_SDTTXT.get(), 16)
        except ValueError:
            iValue = 0
        finally:
            # The Textbox for the SDT is represented with 2 characters
            # We check that the SDT is not bigger than current maximum value
            #
            if iValue > uiMaxValue:
                iValue = uiMaxValue
            self.m_SDTTXT.set("{0:0{1}X}".format(iValue, iTextLength))
            return True

    ## Entry txtVCID OnLeave handler
    ##
    def txtVCID_Leave(self, *args):
        # Sets the text length and maximum VCID value
        #
        iTextLength = 2
        uiMaxValue = 0xFF

        try:
            iValue = int(self.m_VCIDTXT.get(), 16)
        except ValueError:
            iValue = 0
        finally:
            # The Textbox for the vCID is represented with 2 characters
            # We check that the VCID is not bigger than current maximum value
            #
            if iValue > uiMaxValue:
                iValue = uiMaxValue
            self.m_VCIDTXT.set("{0:0{1}X}".format(iValue, iTextLength))
            return True

    ## Entry txtAF OnLeave handler
    ##
    def txtAF_Leave(self, *args):
        # Sets the text length and maximum AF value
        #
        iTextLength = 8
        uiMaxValue = 0xFFFFFFFF

        try:
            iValue = int(self.m_AFTXT.get(), 16)
        except ValueError:
            iValue = 0
        finally:
            # The Textbox for the AF is represented with 8 characters
            # We check that the AF is not bigger than current maximum value
            #
            if iValue > uiMaxValue:
                iValue = uiMaxValue
            self.m_AFTXT.set("{0:0{1}X}".format(iValue, iTextLength))
            return True

    # Spinbutton nudLength handler
    def nudLength_ValueChanged(self):
        self.FillRandomData()

        self.laLength.config(
            text="Length: {} B.".format(int(self.m_LengthNUD.get()) + 1)
        )

    # Spinbutton nudLength leave handler
    def nudLength_Leave(self, event):
        try:
            iCount = int(self.m_LengthNUD.get())

            iCount = iCount
            if iCount < 0:
                iCount = 0
            elif iCount > 2047:
                iCount = 2047

        except ValueError:
            iCount = 0

        self.m_LengthNUD.set(str(iCount))

        self.FillRandomData()

        self.laLength.config(
            text="Length: {} B.".format(int(self.m_LengthNUD.get()) + 1)
        )

    def tmrRead_Tick(self):
        # Checks if in the receive-queue are currently messages for read
        #
        self.ReadMessages()

    def tmrDisplayManage(self, active):
        if active:
            self.m_Parent.after(0, self.tmrThreadSafeDisplay_Tick)

    def tmrThreadSafeDisplay_Tick(self):
        self.DisplayMessages()
        if self.m_Connected:
            self.m_Parent.after(DISPLAY_UPDATE_MS, self.tmrThreadSafeDisplay_Tick)


###*****************************************************************


###*****************************************************************
### ROOT
###*****************************************************************


### Loop-Functionallity
def RunMain(root):
    global basicExl

    # Creates a PCAN-Basic application
    #
    basicExl = PCANBasicExample(root)

    # Runs the Application / loop-start
    #
    basicExl.loop()

    # Application's destrution / loop-end
    #
    basicExl.destroy()


if __name__ == "__main__":
    # Creates the Tkinter-extension Root
    #
    root = Tix.Tk()
    # Uses the root to launch the PCAN-Basic Example application
    #
    RunMain(root)
###*****************************************************************

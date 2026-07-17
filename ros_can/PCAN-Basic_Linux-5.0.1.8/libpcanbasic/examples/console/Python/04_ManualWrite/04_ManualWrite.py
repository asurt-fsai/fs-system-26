## Needed Imports
from enum import Enum
from PCANBasic import *
import os
import sys

class CANProtocol(Enum):
    CAN = 1
    CAN_FD = 2
    CAN_XL = 3

class ManualWrite():

    # Defines
    #region

    # Sets the PCANHandle (Hardware Channel)
    PcanHandle = PCAN_USBBUS1

    # Sets the desired connection mode
    Protocol = CANProtocol.CAN

    # Sets the bitrate for normal CAN devices
    Bitrate = PCAN_BAUD_500K

    # Sets the bitrate for CAN FD devices. 
    # Example - Bitrate Nom: 1Mbit/s FD: 2Mbit/s:
    #   "f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1"
    BitrateFD = b'f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1'
    
    # Sets the bitrate for CAN XL devices.
    # Example - Bitrate Nom: 500kbit/s FD: 2Mbit/s XL: 8Mbit/s: 
    #   "f_clock=160000000, brp=1, nom_tseg1=255, nom_tseg2=64, nom_sjw=64, fd_tseg1=63, fd_tseg2=16, fd_sjw=16, fd_ssp_offset=0, xl_tseg1=10, xl_tseg2=9, xl_sjw=9, xl_ssp_offset=10, xl_error_signaling=1, xl_transceiver_mode_switch=0"
    BitrateXL = b'f_clock=160000000, brp=1, nom_tseg1=255, nom_tseg2=64, nom_sjw=64, fd_tseg1=63, fd_tseg2=16, fd_sjw=16, fd_ssp_offset=0, xl_tseg1=10, xl_tseg2=9, xl_sjw=9, xl_ssp_offset=10, xl_error_signaling=1, xl_transceiver_mode_switch=0'
    #endregion

    # Members
    #region

    # Shows if DLL was found
    m_DLLFound = False

    #endregion

    def __init__(self):
        """
        Create an object starts the program
        """
        self.ShowConfigurationHelp() ## Shows information about this sample
        self.ShowCurrentConfiguration() ## Shows the current parameters configuration

        ## Checks if PCANBasic.dll is available, if not, the program terminates
        try:
            self.m_objPCANBasic = PCANBasic()
            self.m_DLLFound = True
        except :
            print("Unable to find the library: PCANBasic.dll !")
            self.getInput("Press <Enter> to quit...")
            self.m_DLLFound = False
            return

        
        ## Initialization of the selected channel
        if self.Protocol == CANProtocol.CAN_XL:
            stsResult = self.m_objPCANBasic.InitializeXL(self.PcanHandle,self.BitrateXL)
        elif self.Protocol == CANProtocol.CAN_FD:
            stsResult = self.m_objPCANBasic.InitializeFD(self.PcanHandle,self.BitrateFD)
        else:
            stsResult = self.m_objPCANBasic.Initialize(self.PcanHandle,self.Bitrate)

        if stsResult != PCAN_ERROR_OK:
            print("Can not initialize. Please check the defines in the code.")
            self.ShowStatus(stsResult)
            print("")
            self.getInput("Press <Enter> to quit...")
            return

        ## Writing messages...
        print("Successfully initialized.")
        self.getInput("Press <Enter> to write...")
        strinput = "y"
        while strinput == "y":
            self.clear()
            self.WriteMessages()
            strinput = self.getInput("Do you want to write again? yes[y] or any other key to exit...", "y")

    def __del__(self):
        if self.m_DLLFound:
            self.m_objPCANBasic.Uninitialize(PCAN_NONEBUS)

    def getInput(self, msg="Press <Enter> to continue...", default=""):
        res = default
        if sys.version_info[0] >= 3:
            res = input(msg + " ")
        else:
            res = raw_input(msg + " ")
        if len(res) == 0:
            res = default
        return res

    # Main-Functions
    #region
    def WriteMessages(self):
        '''
        Function for writing PCAN-Basic messages
        '''
        if self.Protocol == CANProtocol.CAN_XL:
            stsResult = self.WriteMessageXL()
        elif self.Protocol == CANProtocol.CAN_FD:
            stsResult = self.WriteMessageFD()
        else:
            stsResult = self.WriteMessage()

        ## Checks if the message was sent
        if (stsResult != PCAN_ERROR_OK):
            self.ShowStatus(stsResult)
        else:
            print("Message was successfully SENT")

    def WriteMessage(self):
        """
        Function for writing messages on CAN devices

        Returns:
            A TPCANStatus error code
        """
        ## Sends a CAN message with extended ID, and 8 data bytes
        msgCanMessage = TPCANMsg()
        msgCanMessage.ID = 0x100
        msgCanMessage.LEN = 8
        msgCanMessage.MSGTYPE = PCAN_MESSAGE_EXTENDED.value
        for i in range(8):
            msgCanMessage.DATA[i] = i
            pass
        return self.m_objPCANBasic.Write(self.PcanHandle, msgCanMessage)

    def WriteMessageFD(self):
        """
        Function for writing messages on CAN-FD devices

        Returns:
            A TPCANStatus error code
        """
        ## Sends a CAN-FD message with standard ID, 64 data bytes, and bitrate switch
        msgCanMessageFD = TPCANMsgFD()
        msgCanMessageFD.ID = 0x100
        msgCanMessageFD.DLC = 15
        msgCanMessageFD.MSGTYPE = PCAN_MESSAGE_FD.value | PCAN_MESSAGE_BRS.value
        for i in range(64):
            msgCanMessageFD.DATA[i] = i
            pass
        return self.m_objPCANBasic.WriteFD(self.PcanHandle, msgCanMessageFD)
    
    def WriteMessageXL(self):
        """
        Function for writing messages on CAN-XL devices

        Returns:
            A TPCANStatus error code
        """
        ## Sends a CAN-XL message with standard ID, 2047 data bytes
        msgCanMessageXL = TPCANMsgXL()
        msgCanMessageXL.PID = 0x100
        msgCanMessageXL.DLC = 2046
        msgCanMessageXL.SDT = 0
        msgCanMessageXL.VCID = 0
        msgCanMessageXL.AF = 0
        msgCanMessageXL.RRS = False
        msgCanMessageXL.SEC = False
        msgCanMessageXL.MSGTYPE = PCAN_MESSAGE_XL.value
        for i in range(2047):
            input = i % 256
            msgCanMessageXL.DATA[i] = input
            pass
        return self.m_objPCANBasic.WriteXL(self.PcanHandle, msgCanMessageXL)
    #endregion

    # Help-Functions
    #region
    def clear(self):
        """
        Clears the console
        """
        if os.name=='nt':
            os.system('cls')
        else:
            os.system('clear')
        
    def ShowConfigurationHelp(self):
        """
        Shows/prints the configurable parameters for this sample and information about them
        """
        print("=========================================================================================")
        print("|                        PCAN-Basic ManualWrite Example                                  |")
        print("=========================================================================================")
        print("Following parameters are to be adjusted before launching, according to the hardware used |")
        print("                                                                                         |")
        print("* PcanHandle: Numeric value that represents the handle of the PCAN-Basic channel to use. |")
        print("              See 'PCAN-Handle Definitions' within the documentation                     |")
        print("* Protocol: Enum value that indicates the communication protocol, CAN, CAN-FD or CAN-XL. |")
        print("* Bitrate: Numeric value that represents the BTR0/BR1 bitrate value to be used for CAN   |")
        print("           communication                                                                 |")
        print("* BitrateFD: String value that represents the nominal/FD bitrate value to be used for    |")
        print("             CAN-FD communication                                                        |")
        print("* BitrateXL: String value that represents the nominal/FD/XL bitrate value to be used for |")
        print("             CAN-XL communication                                                        |")
        print("=========================================================================================")
        print("")

    def ShowCurrentConfiguration(self):
        """
        Shows/prints the configured parameters
        """
        print("Parameter values used")
        print("----------------------")
        print("* PCANHandle: " + self.FormatChannelName(self.PcanHandle, self.Protocol))
        print("* Protocol: " + self.Protocol.name.replace('_', ' '))
        print("* Bitrate: " + self.ConvertBitrateToString(self.Bitrate))
        print("* BitrateFD: " + self.ConvertBytesToString(self.BitrateFD))
        print("* BitrateXL: " + self.ConvertBytesToString(self.BitrateXL))
        print("")

    def ShowStatus(self,status):
        """
        Shows formatted status

        Parameters:
            status = Will be formatted
        """
        print("=========================================================================================")
        print(self.GetFormattedError(status))
        print("=========================================================================================")
    
    def FormatChannelName(self, handle, protocol):
        """
        Gets the formatted text for a PCAN-Basic channel handle

        Parameters:
            handle = PCAN-Basic Handle to format
            protocol = Used CAN protocol

        Returns:
            The formatted text for a channel
        """
        handleValue = handle.value
        if handleValue < 0x100:
            devDevice = TPCANDevice(handleValue >> 4)
            byChannel = handleValue & 0xF
        else:
            devDevice = TPCANDevice(handleValue >> 8)
            byChannel = handleValue & 0xFF

        if protocol == CANProtocol.CAN_XL:
            return ('%s:XL %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))
        elif protocol == CANProtocol.CAN_FD:
            return ('%s:FD %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))
        else:
            return ('%s %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))

    def GetFormattedError(self, error):
        """
        Help Function used to get an error as text

        Parameters:
            error = Error code to be translated

        Returns:
            A text with the translated error
        """
        ## Gets the text using the GetErrorText API function. If the function success, the translated error is returned.
        ## If it fails, a text describing the current error is returned.
        stsReturn = self.m_objPCANBasic.GetErrorText(error,0x09)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            message = str(stsReturn[1])
            return message.replace("'","",2).replace("b","",1)

    def GetDeviceName(self, handle):
        """
        Gets the name of a PCAN device

        Parameters:
            handle = PCAN-Basic Handle for getting the name

        Returns:
            The name of the handle
        """
        switcher = {
            PCAN_NONEBUS.value: "PCAN_NONEBUS",
            PCAN_PCI.value: "PCAN_PCI",
            PCAN_USB.value: "PCAN_USB",
            PCAN_LAN.value: "PCAN_LAN"
        }

        return switcher.get(handle,"UNKNOWN")   

    def ConvertBitrateToString(self, bitrate):
        """
        Convert bitrate c_short value to readable string

        Parameters:
            bitrate = Bitrate to be converted

        Returns:
            A text with the converted bitrate
        """
        m_BAUDRATES = {PCAN_BAUD_1M.value:'1 MBit/sec', PCAN_BAUD_800K.value:'800 kBit/sec', PCAN_BAUD_500K.value:'500 kBit/sec', PCAN_BAUD_250K.value:'250 kBit/sec',
                       PCAN_BAUD_125K.value:'125 kBit/sec', PCAN_BAUD_100K.value:'100 kBit/sec', PCAN_BAUD_95K.value:'95,238 kBit/sec', PCAN_BAUD_83K.value:'83,333 kBit/sec',
                       PCAN_BAUD_50K.value:'50 kBit/sec', PCAN_BAUD_47K.value:'47,619 kBit/sec', PCAN_BAUD_33K.value:'33,333 kBit/sec', PCAN_BAUD_20K.value:'20 kBit/sec',
                       PCAN_BAUD_10K.value:'10 kBit/sec', PCAN_BAUD_5K.value:'5 kBit/sec'}
        return m_BAUDRATES[bitrate.value]

    def ConvertBytesToString(self, bytes):
        """
        Convert bytes value to string

        Parameters:
            bytes = Bytes to be converted

        Returns:
            Converted bytes value as string
        """
        return str(bytes).replace("'","",2).replace("b","",1)
    #endregion

## Starts the program
ManualWrite()
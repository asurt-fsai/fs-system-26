/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * 03_ManualRead.h - PCANBasic Example: ManualRead
 *
 * Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 *
 * Contact:     <linux.peak@hms-networks.com>
 * Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
 *              Romain Tissier <romain.tissier@hms-networks.com>
 */
#include "linux_interop.h"
#include "PCANBasic.h"

// Enum for connection modes
enum CANProtocol { CAN, CAN_FD, CAN_XL };

class ManualRead
{
private:
    /// <summary>
    /// Sets the PCANHandle (Hardware Channel)
    /// </summary>
    const TPCANHandle PcanHandle = PCAN_USBBUS1;
    /// <summary>
    /// Sets the desired connection mode
    /// </summary>
    const CANProtocol Protocol = CANProtocol::CAN;
    /// <summary>
    /// Sets the bitrate for normal CAN devices
    /// </summary>
    const TPCANBaudrate Bitrate = PCAN_BAUD_500K;
    /// <summary>
    /// Sets the bitrate for CAN FD devices.
    /// Example - Bitrate Nom: 1Mbit/s FD: 2Mbit/s:
    ///   "f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1"
    /// </summary>
    TPCANBitrateFD BitrateFD = const_cast<LPSTR>("f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1");
    /// <summary>
    /// Sets the bitrate for CAN XL devices. 
    /// Example - Bitrate Nom: 500kbit/s FD: 2Mbit/s XL: 8Mbit/s: 
    ///   "f_clock=160000000, brp=1, nom_tseg1=255, nom_tseg2=64, nom_sjw=64, fd_tseg1=63, fd_tseg2=16, fd_sjw=16, fd_ssp_offset=0, xl_tseg1=10, xl_tseg2=9, xl_sjw=9, xl_ssp_offset=10, xl_error_signaling=1, xl_transceiver_mode_switch=0"
    /// </summary>
    TPCANBitrateXL BitrateXL = const_cast<LPSTR>("f_clock=160000000, brp=1, nom_tseg1=255, nom_tseg2=64, nom_sjw=64, fd_tseg1=63, fd_tseg2=16, fd_sjw=16, fd_ssp_offset=0, xl_tseg1=10, xl_tseg2=9, xl_sjw=9, xl_ssp_offset=10, xl_error_signaling=1, xl_transceiver_mode_switch=0");

public:
    // ManualRead constructor
    //
    ManualRead();

    // ManualRead destructor
    //
    ~ManualRead();

private:
    /// <summary>
    /// Function for reading PCAN-Basic messages
    /// </summary>
    void ReadMessages();

    /// <summary>
    /// Function for reading messages on CAN-XL devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus ReadMessageXL();

    /// <summary>
    /// Function for reading messages on CAN-FD devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus ReadMessageFD();

    /// <summary>
    /// Function for reading CAN messages on normal CAN devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus ReadMessage();

    /// <summary>
    /// Processes a received CAN message
    /// </summary>
    /// <param name="msg">The received PCAN-Basic CAN message</param>
    /// <param name="itsTimeStamp">Timestamp of the message as TPCANTimestamp structure</param>
    void ProcessMessageCan(TPCANMsg msg, TPCANTimestamp itsTimeStamp);

    /// <summary>
    /// Processes a received CAN-FD message
    /// </summary>
    /// <param name="msg">The received PCAN-Basic CAN-FD message</param>
    /// <param name="itsTimeStamp">Timestamp of the message as microseconds (ulong)</param>
    void ProcessMessageCanFD(TPCANMsgFD msg, TPCANTimestampFD itsTimeStamp);

    /// <summary>
    /// Processes a received CAN-XL message
    /// </summary>
    /// <param name="msg">The received PCAN-Basic CAN-XL message</param>
    /// <param name="itsTimeStamp">Timestamp of the message as microseconds (ulong)</param>
    void ProcessMessageCanXL(TPCANMsgXL msg, TPCANTimestampXL itsTimeStamp);

    /// <summary>
    /// Shows/prints the configurable parameters for this sample and information about them
    /// </summary>
    void ShowConfigurationHelp();

    /// <summary>
    /// Shows/prints the configured parameters
    /// </summary>
    void ShowCurrentConfiguration();

    /// <summary>
    /// Shows formatted status
    /// </summary>
    /// <param name="status">Will be formatted</param>
    void ShowStatus(TPCANStatus status);

    /// <summary>
    /// Gets the formatted text for a PCAN-Basic channel handle
    /// </summary>
    /// <param name="handle">PCAN-Basic Handle to format</param>
    /// <param name="protocol">Used CAN protocol</param>
    /// <returns>The formatted text for a channel</returns>
    void FormatChannelName(TPCANHandle handle, LPSTR buffer, CANProtocol protocol);

    /// <summary>
    /// Gets name of a TPCANHandle
    /// </summary>
    /// <param name="handle">TPCANHandle to get name</param>
    /// <param name="buffer">A string buffer for the name of the TPCANHandle (size MAX_PATH)</param>
    void GetTPCANHandleName(TPCANHandle handle, LPSTR buffer);

    /// <summary>
    /// Help Function used to get an error as text
    /// </summary>
    /// <param name="error">Error code to be translated</param>
    /// <param name="buffer">A string buffer for the translated error (size MAX_PATH)</param>
    void GetFormattedError(TPCANStatus error, LPSTR buffer);

    /// <summary>
    /// Convert bitrate c_short value to readable string
    /// </summary>
    /// <param name="bitrate">Bitrate to be converted</param>
    /// <param name="buffer">A string buffer for the converted bitrate (size MAX_PATH)</param>
    void ConvertBitrateToString(TPCANBaudrate bitrate, LPSTR buffer);

    /// <summary>
    /// Gets the string representation of the type of a CAN message
    /// </summary>
    /// <param name="msgType">Type of a CAN message</param>
    /// <returns>The type of the CAN message as string</returns>
    std::string GetMsgTypeString(TPCANMessageType msgType);

    /// <summary>
    ///  Gets the string representation of the type of a CAN XL message
    /// </summary>
    /// <param name="msgType">Type of a CAN XL message</param>
    /// <param name="rrsFlag">The RRS flag of the XL message</param>
    /// <param name="secFlag">The SEC flag of the XL message</param>
    /// <returns>The type of the CAN XL message as string</returns>
    std::string GetMsgTypeStringXL(TPCANMessageTypeXL msgType, bool rrsFlag, bool secFlag);

    /// <summary>
    /// Gets the string representation of the ID of a CAN message
    /// </summary>
    /// <param name="id">Id to be parsed</param>
    /// <param name="msgType">Type flags of the message the Id belong</param>
    /// <returns>Hexadecimal representation of the ID of a CAN message</returns>
    std::string GetIdString(UINT32 id, TPCANMessageType msgType);

    /// <summary>
    /// Gets the string representation of the ID of a CAN XL message
    /// </summary>
    /// <param name="id">Id to be parsed</param>
    /// <param name="msgType">Type flags of the message the Id belong</param>
    /// <returns>Hexadecimal representation of the ID of a CAN XL message</returns>
    std::string GetIdString(UINT32 id, TPCANMessageTypeXL msgType);

    /// <summary>
    /// Gets the data length of a CAN message
    /// </summary>
    /// <param name="dlc">Data length code of a CAN message</param>
    /// <returns>Data length as integer represented by the given DLC code</returns>
    int GetLengthFromDLC(BYTE dlc);

    /// <summary>
    /// Converts a CAN DLC value into the actual data length of the CAN-XL frame.
    /// </summary>
    /// <param name="dlc">A value between 0 and 2047 (CAN XL DLC range)</param>
    /// <returns>The length represented by the DLC</returns>
    int GetLengthFromDLC(WORD dlc);

    /// <summary>
    /// Gets the string representation of the timestamp of a CAN message, in milliseconds
    /// </summary>
    /// <param name="time">Timestamp in microseconds</param>
    /// <returns>String representing the timestamp in milliseconds</returns>
    std::string GetTimeString(TPCANTimestampFD time);

    /// <summary>
    /// Gets the data of a CAN message as a string
    /// </summary>
    /// <param name="data">Array of bytes containing the data to parse</param>
    /// <param name="msgType">Type flags of the message the data belong</param>
    /// <param name="dataLength">The amount of bytes to take into account within the given data</param>
    /// <returns>A string with hexadecimal formatted data bytes of a CAN message</returns>
    std::string GetDataString(BYTE data[], TPCANMessageType msgType, int dataLength);

    /// <summary>
    /// Gets the data of a CAN XL message as a string
    /// </summary>
    /// <param name="data">Array of bytes containing the data to parse</param>
    /// <param name="msgType">Type flags of the message the data belong</param>
    /// <param name="dataLength">The amount of bytes to take into account within the given data</param>
    /// <returns>A string with hexadecimal formatted data bytes of a CAN message</returns>
    std::string GetDataString(BYTE data[], TPCANMessageTypeXL msgType, int dataLength);

    /// <summary>
    /// Gets the data of a CAN message as a string
    /// </summary>
    /// <param name="data">Array of bytes containing the data to parse</param>
    /// <param name="dataLength">The amount of bytes to take into account within the given data</param>
    /// <returns>A string with hexadecimal formatted data bytes of a CAN message</returns>
    std::string GetDataString(BYTE  data[], int dataLength);
};

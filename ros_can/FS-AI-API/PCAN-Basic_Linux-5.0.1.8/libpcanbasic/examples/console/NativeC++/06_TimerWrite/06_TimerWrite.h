/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * 06_TimerWrite.h - PCANBasic Example: TimerWrite
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

class TimerWrite
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
    /// <summary>
    /// Timerinterval (ms) for reading
    /// </summary>
    const int TimerInterval = 250;
    /// <summary>
    /// Shows if DLL was found
    /// </summary>
    bool m_DLLFound;
    /// <summary>
    /// Used for writing
    /// </summary>
    std::thread* m_hTimer;
    /// <summary>
    /// Shows if thread run
    /// </summary>
    bool m_TimerOn;

public:
    // TimerWrite constructor
    //
    TimerWrite();

    // TimerWrite destructor
    //
    ~TimerWrite();

private:
    /// <summary>
    /// Thread function for reading messages
    /// </summary>
    void TimerThread();

    /// <summary>
    /// Function for writing PCAN-Basic messages
    /// </summary>
    void WriteMessages();

    /// <summary>
    /// Function for writing messages on CAN devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus WriteMessage();

    /// <summary>
    /// Function for writing messages on CAN-FD devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus WriteMessageFD();

    /// <summary>
    /// Function for writing messages on CAN-XL devices
    /// </summary>
    /// <returns>A TPCANStatus error code</returns>
    TPCANStatus WriteMessageXL();

    /// <summary>
    /// Checks for availability of the PCANBasic labrary
    /// </summary>
    /// <returns>If the library was found or not</returns>
    bool CheckForLibrary();

    /// <summary>
    /// Shows/prints the configurable parameters for this sample and information about them
    /// </summary>
    void ShowConfigurationHelp();

    /// <summary>
    /// Shows/prints the configured paramters
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
};

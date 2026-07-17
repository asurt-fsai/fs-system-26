/* SPDX-License-Identifier: LGPL-2.1-only */
 /*
 * PCANBasic JAVA Interface.
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
 * PCAN is a registered Trademark of PEAK-System Germany GmbH
 *
 * Author:       Fabrice Vergnaud
 * Contact:      <linux.peak@hms-networks.com>
 * Maintainer:   Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
 */
package peak.can.basic;

/**
 * Bitrate parameters composing a TPCANBitrateXL. Take a look at
 * www.peak-system.com for our free software "Bit Rate Calculation Tool" to
 * calculate the bitrate string for every baudrate and sample point.
 */
public enum TPCANBitrateXLValue {

    /**
     * Clock frequency in Herz (80000000, 60000000, 40000000, 30000000,
     * 24000000, 20000000)
     */
    PCAN_BR_CLOCK("f_clock"),
    /**
     * Clock frequency in Megaherz (80, 60, 40, 30, 24, 20)
     */
    PCAN_BR_CLOCK_MHZ("f_clock_mhz"),
    /**
     * Clock prescaler for nominal time quantum
     */
    PCAN_BR_NOM_BRP("nom_brp"),
    /**
     * TSEG1 segment for nominal bit rate in time quanta
     */
    PCAN_BR_NOM_TSEG1("nom_tseg1"),
    /**
     * TSEG2 segment for nominal bit rate in time quanta
     */
    PCAN_BR_NOM_TSEG2("nom_tseg2"),
    /**
     * Synchronization Jump Width for nominal bit rate in time quanta
     */
    PCAN_BR_NOM_SJW("nom_sjw"),
    /**
     * Sample point for nominal bit rate
     */
    PCAN_BR_NOM_SAMPLE("nom_sam"),
    /**
     * Clock prescaler for highspeed data time quantum
     */
    PCAN_BR_DATA_BRP("data_brp"),
    /**
     * TSEG1 segment for fast data bit rate in time quanta
     */
    PCAN_BR_DATA_TSEG1("data_tseg1"),
    /**
     * TSEG2 segment for fast data bit rate in time quanta
     */
    PCAN_BR_DATA_TSEG2("data_tseg2"),
    /**
     * Synchronization Jump Width for highspeed data bit rate in time quanta
     */
    PCAN_BR_DATA_SJW("data_sjw"),
    /**
     * Secondary sample point delay for highspeed data bitrate in cyles
     */
    PCAN_BR_DATA_SAMPLE("data_ssp_offset"),
    /**
     * Clock prescaler for nominal, CAN FD and CAN XL bit rates
     */
    PCAN_BR_BRP("brp"),
    /**
     * Clock prescaler for fast data time quantum
     */
    PCAN_BR_FD_TSEG1("fd_tseg1"),
    /**
     * Clock prescaler for fast data time quantum
     */
    PCAN_BR_FD_TSEG2("fd_tseg2"),
    /**
     * Synchronization Jump Width for fast data bit rate in time quanta
     */
    PCAN_BR_FD_SJW("fd_sjw"),
    /**
     * Secondary sample point delay for fast data bit rate in cycles
     */
    PCAN_BR_FD_SSP_OFFSET("fd_ssp_offset"),
    /**
     * Clock prescaler for XL time quantum
     */
    PCAN_BR_XL_TSEG1("xl_tseg1"),
    /**
     * Clock prescaler for XL time quantum
     */
    PCAN_BR_XL_TSEG2("xl_tseg2"),
    /**
     * Synchronization Jump Width for XL bit rate in time quanta
     */
    PCAN_BR_XL_SJW("xl_sjw"),
    /**
     * Secondary sample point delay for XL bit rate in cycles
     */
    PCAN_BR_XL_SSP_OFFSET("xl_ssp_offset"),
    /**
     * CAN XL PWM Offset in mtq ticks == f_cancore cycles
     */
    PCAN_BR_XL_PWM_OFFSET("xl_pwm_offset"),
    /**
     * CAN XL PWM Short phase in mtq ticks == f_cancore cycles
     */
    PCAN_BR_XL_PWM_SHORT("xl_pwm_short"),
    /**
     * CAN XL PWM Long phase in mtq ticks == f_cancore cycles
     */
    PCAN_BR_XL_PWM_LONG("xl_pwm_long"),
    /**
     * XL transceiver mode switch 1 = CAN XL Data Phase uses 'fast TX' or 'fast
     * RX' with PWM encoding 0 = CAN XL Data Phase uses no PWM encoding
     * (recessive/dominant only, like CAN FD)
     */
    PCAN_BR_XL_TRANSCEIVER_MODE_SWITCH("xl_transceiver_mode_switch"),
    /**
     * XL error signaling 1 = Error Signaling with Error Frame in case of bus
     * errors 0 = No Error Signaling
     */
    PCAN_BR_XL_ERROR_SIGNALING("xl_error_signaling");

    private final String value;

    private TPCANBitrateXLValue(String value) {
        this.value = value;
    }

    /**
     * The string value of Bitrate XL string parameter
     *
     * @return String corresponding to the bitrate XL string parameter
     */
    public String getValue() {
        return this.value;
    }
};

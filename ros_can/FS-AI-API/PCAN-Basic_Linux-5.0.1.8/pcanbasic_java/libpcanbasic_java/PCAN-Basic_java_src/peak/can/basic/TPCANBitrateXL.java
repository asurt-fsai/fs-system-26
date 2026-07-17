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
 * XL bit rates for the CAN XL controller. You can define your own bit rate with
 * the XL string, as shown in this exemple:
 * "f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,
 * fd_tseg1=63,fd_tseg2=16,fd_sjw=16,fd_ssp_offset=0,xl_tseg1=10,
 * xl_tseg2=9,xl_sjw=9,xl_ssp_offset=10,
 * xl_error_signaling=1,xl_transceiver_mode_switch=0"
 */
public class TPCANBitrateXL {

    private String value;

    /**
     * Creates a CAN XL bitrate
     *
     * @param value A CAN XL bitrate string (for instance:
     * "f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,
     * fd_tseg1=63,fd_tseg2=16,fd_sjw=16,fd_ssp_offset=0,xl_tseg1=10,
     * xl_tseg2=9,xl_sjw=9,xl_ssp_offset=10,
     * xl_error_signaling=1,xl_transceiver_mode_switch=0")
     */
    public TPCANBitrateXL(String value) {
        this.value = value;
    }

    /**
     * Returns the string configuration of the bitrate code.
     *
     * @return The bitrate string configuration
     */
    public String getValue() {
        return this.value;
    }

    /**
     * Sets string configuration of the bitrate code.
     *
     * @param value The new bitrate string configuration
     */
    public void setValue(String value) {
        this.value = value;
    }
};

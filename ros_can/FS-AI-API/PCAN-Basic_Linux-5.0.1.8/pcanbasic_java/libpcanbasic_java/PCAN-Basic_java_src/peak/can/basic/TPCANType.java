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
 * Author:       Jonathan Urban/Uwe Wilhelm/Fabrice Vergnaud
 * Contact:      <linux.peak@hms-networks.com>
 * Maintainer:   Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
 */
package peak.can.basic;

/**
 * Represents a PCAN device
 *
 * Since 5.0, only Plug'n play hardware are supported.
 */
public enum TPCANType {
    /**
     * Undefined, unknown or not selected PCAN type value
     */
    PCAN_TYPE_NONE((byte) 0x00);

    private TPCANType(byte value) {
        this.value = value;
    }

    /**
     * The identifier of the CAN hardware type
     *
     * @return Identifier of the CAN hardware type
     */
    public byte getValue() {
        return this.value;
    }
    private final byte value;
};

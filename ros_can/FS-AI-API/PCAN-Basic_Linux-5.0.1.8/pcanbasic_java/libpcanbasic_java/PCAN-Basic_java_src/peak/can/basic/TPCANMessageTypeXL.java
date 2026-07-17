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

import java.util.EnumSet;

/**
 * Represents the type of a PCAN XL message
 */
public enum TPCANMessageTypeXL {

    /**
     * The PCAN message is a CAN Standard Frame (11-bit identifier)
     */
    PCAN_MESSAGE_STANDARD((short) 0x00),
    /**
     * The PCAN message is a CAN Remote-Transfer-Request Frame
     */
    PCAN_MESSAGE_RTR((short) 0x01),
    /**
     * The PCAN message is a CAN Extended Frame (29-bit identifier)
     */
    PCAN_MESSAGE_EXTENDED((short) 0x02),
    /**
     * The PCAN message represents a FD frame in terms of CiA Specs
     */
    PCAN_MESSAGE_FD((short) 0x04),
    /**
     * The PCAN message represents a FD bit rate switch (CAN data at a higher
     * bitrate)
     */
    PCAN_MESSAGE_BRS((short) 0x08),
    /**
     * The PCAN message represents a FD error state indicator(CAN FD transmitter
     * was error active)
     */
    PCAN_MESSAGE_ESI((short) 0x10),
    /**
     * The PCAN message represents an error frame
     */
    PCAN_MESSAGE_ERRFRAME((short) 0x40),
    /**
     * The PCAN message represents a PCAN status message
     */
    PCAN_MESSAGE_STATUS((short) 0x80),
    /**
     * The PCAN message represents a XL frame in terms of CiA Specs
     */
    PCAN_MESSAGE_XL((short) 0x100),
    /**
     * The PCAN message represents a protocol exception from CAN core
     */
    PCAN_MESSAGE_PROTOCOL_EXCEPTION((short) 0x200),
    /**
     * The PCAN message represents an error notification from CAN core
     */
    PCAN_MESSAGE_ERROR_NOTIFICATION((short) 0x400);

    private TPCANMessageTypeXL(short value) {
        this.value = value;
    }

    /**
     * The value of the message type
     *
     * @return Value of the message type
     */
    public short getValue() {
        return this.value;
    }

    private final short value;

    /**
     * Gets the value of an EnumSet
     *
     * @param type collection of TPCANMessageType
     * @return value of the EnumSet
     */
    public static short getValue(EnumSet<TPCANMessageTypeXL> type) {
        byte result = 0;
        for (TPCANMessageTypeXL t : type) {
            result |= t.value;
        }
        return result;
    }
}

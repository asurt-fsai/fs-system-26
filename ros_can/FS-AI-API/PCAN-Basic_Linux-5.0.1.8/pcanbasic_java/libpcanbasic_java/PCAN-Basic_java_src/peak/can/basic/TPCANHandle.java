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

import java.util.ArrayDeque;
import java.util.Deque;

/**
 * Represents a PCAN-hardware channel handle.
 */
public enum TPCANHandle {

    /**
     * Undefined/default value for a PCAN bus
     */
    PCAN_NONEBUS((short) 0x00),
    /**
     * PCAN-PCI interface, channel 1
     */
    PCAN_PCIBUS1((short) 0x41),
    /**
     * PCAN-PCI interface, channel 2
     */
    PCAN_PCIBUS2((short) 0x42),
    /**
     * PCAN-PCI interface, channel 3
     */
    PCAN_PCIBUS3((short) 0x43),
    /**
     * PCAN-PCI interface, channel 4
     */
    PCAN_PCIBUS4((short) 0x44),
    /**
     * PCAN-PCI interface, channel 5
     */
    PCAN_PCIBUS5((short) 0x45),
    /**
     * PCAN-PCI interface, channel 6
     */
    PCAN_PCIBUS6((short) 0x46),
    /**
     * PCAN-PCI interface, channel 7
     */
    PCAN_PCIBUS7((short) 0x47),
    /**
     * PCAN-PCI interface, channel 8
     */
    PCAN_PCIBUS8((short) 0x48),
    /**
     * PCAN-PCI interface, channel 9
     */
    PCAN_PCIBUS9((short) 0x409),
    /**
     * PCAN-PCI interface, channel 10
     */
    PCAN_PCIBUS10((short) 0x40A),
    /**
     * PCAN-PCI interface, channel 11
     */
    PCAN_PCIBUS11((short) 0x40B),
    /**
     * PCAN-PCI interface, channel 12
     */
    PCAN_PCIBUS12((short) 0x40C),
    /**
     * PCAN-PCI interface, channel 13
     */
    PCAN_PCIBUS13((short) 0x40D),
    /**
     * PCAN-PCI interface, channel 14
     */
    PCAN_PCIBUS14((short) 0x40E),
    /**
     * PCAN-PCI interface, channel 15
     */
    PCAN_PCIBUS15((short) 0x40F),
    /**
     * PCAN-PCI interface, channel 16
     */
    PCAN_PCIBUS16((short) 0x410),
    /**
     * PCAN-USB interface, channel 1
     */
    PCAN_USBBUS1((short) 0x51),
    /**
     * PCAN-USB interface, channel 2
     */
    PCAN_USBBUS2((short) 0x52),
    /**
     * PCAN-USB interface, channel 3
     */
    PCAN_USBBUS3((short) 0x53),
    /**
     * PCAN-USB interface, channel 4
     */
    PCAN_USBBUS4((short) 0x54),
    /**
     * PCAN-USB interface, channel 5
     */
    PCAN_USBBUS5((short) 0x55),
    /**
     * PCAN-USB interface, channel 6
     */
    PCAN_USBBUS6((short) 0x56),
    /**
     * PCAN-USB interface, channel 7
     */
    PCAN_USBBUS7((short) 0x57),
    /**
     * PCAN-USB interface, channel 8
     */
    PCAN_USBBUS8((short) 0x58),
    /**
     * PCAN-USB interface, channel 9
     */
    PCAN_USBBUS9((short) 0x509),
    /**
     * PCAN-USB interface, channel 10
     */
    PCAN_USBBUS10((short) 0x50A),
    /**
     * PCAN-USB interface, channel 11
     */
    PCAN_USBBUS11((short) 0x50B),
    /**
     * PCAN-USB interface, channel 12
     */
    PCAN_USBBUS12((short) 0x50C),
    /**
     * PCAN-USB interface, channel 13
     */
    PCAN_USBBUS13((short) 0x50D),
    /**
     * PCAN-USB interface, channel 14
     */
    PCAN_USBBUS14((short) 0x50E),
    /**
     * PCAN-USB interface, channel 15
     */
    PCAN_USBBUS15((short) 0x50F),
    /**
     * PCAN-USB interface, channel 16
     */
    PCAN_USBBUS16((short) 0x510),
    /**
     * PCAN-LAN1 interface, channel 1
     */
    PCAN_LANBUS1((short) 0x801),
    /**
     * PCAN-LAN2 interface, channel 2
     */
    PCAN_LANBUS2((short) 0x802),
    /**
     * PCAN-LAN3 interface, channel 3
     */
    PCAN_LANBUS3((short) 0x803),
    /**
     * PCAN-LAN4 interface, channel 4
     */
    PCAN_LANBUS4((short) 0x804),
    /**
     * PCAN-LAN5 interface, channel 5
     */
    PCAN_LANBUS5((short) 0x805),
    /**
     * PCAN-LAN6 interface, channel 6
     */
    PCAN_LANBUS6((short) 0x806),
    /**
     * PCAN-LAN7 interface, channel 7
     */
    PCAN_LANBUS7((short) 0x807),
    /**
     * PCAN-LAN8 interface, channel 8
     */
    PCAN_LANBUS8((short) 0x808),
    /**
     * PCAN-LAN interface, channel 9
     */
    PCAN_LANBUS9((short) 0x809),
    /**
     * PCAN-LAN interface, channel 10
     */
    PCAN_LANBUS10((short) 0x80A),
    /**
     * PCAN-LAN interface, channel 11
     */
    PCAN_LANBUS11((short) 0x80B),
    /**
     * PCAN-LAN interface, channel 12
     */
    PCAN_LANBUS12((short) 0x80C),
    /**
     * PCAN-LAN interface, channel 13
     */
    PCAN_LANBUS13((short) 0x80D),
    /**
     * PCAN-LAN interface, channel 14
     */
    PCAN_LANBUS14((short) 0x80E),
    /**
     * PCAN-LAN interface, channel 15
     */
    PCAN_LANBUS15((short) 0x80F),
    /**
     * PCAN-LAN interface, channel 16
     */
    PCAN_LANBUS16((short) 0x810);

    /**
     * Creates a CAN Handle
     *
     * @param value value of the CAN Handle
     */
    private TPCANHandle(short value) {
        this.value = value;
    }

    /**
     * The value of the CAN handle
     *
     * @return Value of the CAN handle
     */
    public short getValue() {
        return this.value;
    }

    /**
     * Returns All PCAN Channels which are initializable (All except
     * PCAN_NONEBUS)
     *
     * @return PCAN Channels array
     */
    public static Object[] initializableChannels() {
        TPCANHandle[] values = TPCANHandle.values();
        int size = values.length;
        Deque<TPCANHandle> result = new ArrayDeque<TPCANHandle>(size);
        for (int i = 1; i < size; i++) {
            result.add(values[i]);
        }
        return result.toArray();
    }

    public static Object[] pnpChannels() {
        TPCANHandle[] values = TPCANHandle.values();
        int size = values.length;
        Deque<TPCANHandle> result = new ArrayDeque<TPCANHandle>(size);
        result.add(TPCANHandle.PCAN_USBBUS1);
        result.add(TPCANHandle.PCAN_USBBUS2);
        result.add(TPCANHandle.PCAN_USBBUS3);
        result.add(TPCANHandle.PCAN_USBBUS4);
        result.add(TPCANHandle.PCAN_USBBUS5);
        result.add(TPCANHandle.PCAN_USBBUS6);
        result.add(TPCANHandle.PCAN_USBBUS7);
        result.add(TPCANHandle.PCAN_USBBUS8);
        result.add(TPCANHandle.PCAN_USBBUS9);
        result.add(TPCANHandle.PCAN_USBBUS10);
        result.add(TPCANHandle.PCAN_USBBUS11);
        result.add(TPCANHandle.PCAN_USBBUS12);
        result.add(TPCANHandle.PCAN_USBBUS13);
        result.add(TPCANHandle.PCAN_USBBUS14);
        result.add(TPCANHandle.PCAN_USBBUS15);
        result.add(TPCANHandle.PCAN_USBBUS16);

        result.add(TPCANHandle.PCAN_PCIBUS1);
        result.add(TPCANHandle.PCAN_PCIBUS2);
        result.add(TPCANHandle.PCAN_PCIBUS3);
        result.add(TPCANHandle.PCAN_PCIBUS4);
        result.add(TPCANHandle.PCAN_PCIBUS5);
        result.add(TPCANHandle.PCAN_PCIBUS6);
        result.add(TPCANHandle.PCAN_PCIBUS7);
        result.add(TPCANHandle.PCAN_PCIBUS8);
        result.add(TPCANHandle.PCAN_PCIBUS9);
        result.add(TPCANHandle.PCAN_PCIBUS10);
        result.add(TPCANHandle.PCAN_PCIBUS11);
        result.add(TPCANHandle.PCAN_PCIBUS12);
        result.add(TPCANHandle.PCAN_PCIBUS13);
        result.add(TPCANHandle.PCAN_PCIBUS14);
        result.add(TPCANHandle.PCAN_PCIBUS15);
        result.add(TPCANHandle.PCAN_PCIBUS16);

        result.add(TPCANHandle.PCAN_LANBUS1);
        result.add(TPCANHandle.PCAN_LANBUS2);
        result.add(TPCANHandle.PCAN_LANBUS3);
        result.add(TPCANHandle.PCAN_LANBUS4);
        result.add(TPCANHandle.PCAN_LANBUS5);
        result.add(TPCANHandle.PCAN_LANBUS6);
        result.add(TPCANHandle.PCAN_LANBUS7);
        result.add(TPCANHandle.PCAN_LANBUS8);
        result.add(TPCANHandle.PCAN_LANBUS9);
        result.add(TPCANHandle.PCAN_LANBUS10);
        result.add(TPCANHandle.PCAN_LANBUS11);
        result.add(TPCANHandle.PCAN_LANBUS12);
        result.add(TPCANHandle.PCAN_LANBUS13);
        result.add(TPCANHandle.PCAN_LANBUS14);
        result.add(TPCANHandle.PCAN_LANBUS15);
        result.add(TPCANHandle.PCAN_LANBUS16);
        return result.toArray();
    }

    /**
     * Verify the provided TPCANHandle is an USB Device
     *
     * @param handle to verify
     * @return true if the TPCANHandle is an USB Device, false if not
     */
    public static boolean isPCANUSBHardware(TPCANHandle handle) {
        switch (handle) {
            case PCAN_USBBUS1:
            case PCAN_USBBUS2:
            case PCAN_USBBUS3:
            case PCAN_USBBUS4:
            case PCAN_USBBUS5:
            case PCAN_USBBUS6:
            case PCAN_USBBUS7:
            case PCAN_USBBUS8:
            case PCAN_USBBUS9:
            case PCAN_USBBUS10:
            case PCAN_USBBUS11:
            case PCAN_USBBUS12:
            case PCAN_USBBUS13:
            case PCAN_USBBUS14:
            case PCAN_USBBUS15:
            case PCAN_USBBUS16:
                return true;
            default:
                return false;
        }
    }

    private final short value;
};

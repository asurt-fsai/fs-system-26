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
 * Defines a CAN XL message.
 */
public class TPCANMsgXL implements Cloneable {

    /**
     * CAN-XL: Priority ID (physical layer) (0..0x7FF) CAN-CC/CAN-FD: 11/29-bit
     * message identifier
     */
    private int _PID;
    /**
     * Virtual CAN network ID
     */
    private byte _VCID;
    /**
     * Type of the message
     */
    private EnumSet<TPCANMessageTypeXL> _type = EnumSet.noneOf(TPCANMessageTypeXL.class);

    /**
     * Data Length Code of the message (0..2047)
     */
    private short _dlc = 0;

    /**
     * Service Data unit(SDU) protocol Type
     */
    private byte _SDT;
    /**
     * Acceptance Field, SDU - specific high - layer ID
     */
    private int _AF;
    /**
     * Remote Request Substitution flag (0..1)
     */
    private byte _RRS;
    /**
     * Simple Extended Content flag (0..1)
     */
    private byte _SEC;
    /**
     * Data of the message (DATA[0]..DATA[2047])
     */
    private byte _data[] = new byte[2048];

    /**
     * Default constructor
     */
    public TPCANMsgXL() {
    }

    /**
     * Constructs a new message object.
     *
     * @param pid
     * @param vcid
     * @param msgtype
     * @param dlc
     * @param sdt
     * @param af
     * @param rrs
     * @param sec
     * @param data
     */
    public TPCANMsgXL(int pid, byte vcid, EnumSet<TPCANMessageTypeXL> msgtype, short dlc, byte sdt, int af, byte rrs, byte sec, byte[] data) {
        _PID = pid;
        _VCID = vcid;
        _type = msgtype;
        _dlc = dlc;
        _SDT = sdt;
        _AF = af;
        _RRS = rrs;
        _SEC = sec;
        _data = data;
        System.arraycopy(data, 0, _data, 0, getLengthFromDLC(_type, _dlc));
    }

    public void setPID(int _PID) {
        this._PID = _PID;
    }

    public void setVCID(byte _VCID) {
        this._VCID = _VCID;
    }

    public void setSDT(byte _SDT) {
        this._SDT = _SDT;
    }

    public void setAF(int _AF) {
        this._AF = _AF;
    }

    public void setRRS(byte _RRS) {
        this._RRS = _RRS;
    }

    public void setSEC(byte _SEC) {
        this._SEC = _SEC;
    }

    /**
     * Sets the data of this message.
     *
     * @param data the message data
     * @param length the message length
     */
    public void setData(byte[] data, short length) {
        System.arraycopy(data, 0, _data, 0, length);
    }

    /**
     * Sets the data length code of this message.
     *
     * @param dlc the data length code of the message
     */
    public void setDlc(short dlc) {
        _dlc = dlc;
    }

    /**
     * Sets the type of this message.
     *
     * @param type the message type
     */
    public void setType(EnumSet<TPCANMessageTypeXL> type) {
        _type = type;
    }

    /**
     * Sets the type of this message.
     *
     * @param type the message type
     */
    public void setType(short type) {
        EnumSet<TPCANMessageTypeXL> eset;

        eset = EnumSet.noneOf(TPCANMessageTypeXL.class);
        for (TPCANMessageTypeXL t : TPCANMessageTypeXL.values()) {
            if ((type & t.getValue()) == t.getValue()) {
                eset.add(t);
            }
        }
        // fix type PCAN_MESSAGE_STANDARD (value is 0)
        if (eset.contains(TPCANMessageTypeXL.PCAN_MESSAGE_EXTENDED)
                || eset.contains(TPCANMessageTypeXL.PCAN_MESSAGE_STATUS)
                || eset.contains(TPCANMessageTypeXL.PCAN_MESSAGE_ERRFRAME)) {
            eset.remove(TPCANMessageTypeXL.PCAN_MESSAGE_STANDARD);
        }
        _type = eset;
    }

    public int getPID() {
        return _PID;
    }

    public byte getVCID() {
        return _VCID;
    }

    public byte getSDT() {
        return _SDT;
    }

    public int getAF() {
        return _AF;
    }

    public byte getRRS() {
        return _RRS;
    }

    public byte getSEC() {
        return _SEC;
    }

    /**
     * Gets the data of this message.
     *
     * @return the message data
     */
    public byte[] getData() {
        return _data;
    }

    /**
     * Gets the data length code of this message.
     *
     * @return the message Data Length Code
     */
    public short getDlc() {
        return _dlc;
    }

    /**
     * Gets the length of this message based on its DLC.
     *
     * @return the message length
     */
    public short getLengthFromDLC() {
        return getLengthFromDLC(_type, _dlc);
    }

    /**
     * Gets the length of a message based on a DLC.
     *
     * @param type CAN frame type
     * @param dlc data length code
     * @return the message length
     */
    public static short getLengthFromDLC(EnumSet<TPCANMessageTypeXL> type, short dlc) {
        if (type.contains(TPCANMessageTypeXL.PCAN_MESSAGE_XL)) {
            return (short) (dlc + 1);
        } else if (type.contains(TPCANMessageTypeXL.PCAN_MESSAGE_FD)) {
            return TPCANMsgFD.getLengthFromDLC((byte) dlc);
        } else {
            return dlc;
        }
    }

    /**
     * Gets the type of this message.
     *
     * @return the message type
     */
    public EnumSet<TPCANMessageTypeXL> getTypeEnum() {
        return _type;
    }

    /**
     * Gets the type of this message.
     *
     * @return the message type
     */
    public short getType() {
        short res;

        res = 0;
        for (TPCANMessageTypeXL t : _type) {
            res |= t.getValue();
        }
        return res;
    }

    /**
     * Clones this message object.
     *
     * @return The cloned message object.
     */
    @Override
    public Object clone() {
        TPCANMsgXL msg = null;
        try {
            msg = (TPCANMsgXL) super.clone();
            msg._data = _data.clone();
        } catch (CloneNotSupportedException e) {
            System.out.println(e.getMessage());
        }
        return msg;
    }
}

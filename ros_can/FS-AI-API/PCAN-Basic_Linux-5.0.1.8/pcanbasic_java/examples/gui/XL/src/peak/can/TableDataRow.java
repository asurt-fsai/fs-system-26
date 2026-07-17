/* SPDX-License-Identifier: LGPL-2.1-only */
 /*
 * Demo Application for PCANBasic JAVA JNI Interface.
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
package peak.can;

import peak.can.basic.TPCANMessageTypeXL;
import peak.can.basic.TPCANMsgXL;
import peak.can.basic.TPCANTimestampXL;

/**
 * The TableDataRow class is a structure to store all provided info by a CAN XL
 * Message
 */
public class TableDataRow {

    // Private fields
    private int counter;
    private TPCANMsgXL messageXl;
    private TPCANTimestampXL rcvTimeXl;


    /**
     * Sets number of times the CAN Message was readed
     *
     * @param counter number of times the CAN Message was readed
     */
    public void setCounter(int counter) {
        this.counter = counter;
    }
    /**
     * Sets wrapped TPCANMsg
     *
     * @param message wrapped TPCANMsg
     */
    public void setMessage(TPCANMsgXL message) {
        this.messageXl = message;
    }

    /**
     * Sets wrapped TPCANTimestamp
     *
     * @param rcvTime wrapped TPCANTimestampXL
     */
    public void setRcvTime(TPCANTimestampXL rcvTime) {
        this.rcvTimeXl = rcvTime;
    }

    public String getMsgType() {
        String result;
        int typeFlagsHandled = 0;
        short msgType;

        result = "";
        if (messageXl != null) {
            msgType = messageXl.getType();
            if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_EXTENDED.getValue()) != 0) {
                result = "EXT";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_EXTENDED.getValue();
            } else if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_STATUS.getValue()) != 0) {
                result = "STATUS";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_STATUS.getValue();
            } else if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_ERRFRAME.getValue()) != 0) {
                result = "ERROR";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_ERRFRAME.getValue();
            } else {
                result = "STD";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_STANDARD.getValue();
            }

            if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_RTR.getValue()) != 0) {
                result += "/RTR";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_RTR.getValue();
            }

            if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_XL.getValue()) != 0) {
                result += " XL";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_XL.getValue();
            }

            if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_FD.getValue()) != 0) {
                result += " [ FD";
                typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_FD.getValue();
                if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_BRS.getValue()) != 0) {
                    result += " BRS";
                    typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_BRS.getValue();
                }
                if ((msgType & TPCANMessageTypeXL.PCAN_MESSAGE_ESI.getValue()) != 0) {
                    result += " ESI";
                    typeFlagsHandled += TPCANMessageTypeXL.PCAN_MESSAGE_ESI.getValue();
                }
                result += " ]";
            }
            if (typeFlagsHandled != msgType) {
                result += String.format(" (%02Xh)", msgType);
            }
        }
        return result;
    }

    public int getMsgPID() {
        if (messageXl != null) {
            return messageXl.getPID();
        }
        return 0;
    }

    public int getMsgLength() {
        if (messageXl != null) {
            return messageXl.getLengthFromDLC();
        }
        return 0;
    }
    public int getMsgSDT() {
        if (messageXl != null) {
            return messageXl.getSDT();
        }
        return 0;
    }
    public int getMsgVCID() {
        if (messageXl != null) {
            return messageXl.getVCID();
        }
        return 0;
    }
    public int getMsgAF() {
        if (messageXl != null) {
            return messageXl.getAF();
        }
        return 0;
    }
    public String getRcvTimeAsString() {
        if (rcvTimeXl != null) {
            return String.valueOf(rcvTimeXl.getValue());
        }
        return null;
    }
    /**
     * Gets number of times the CAN Message was readed
     *
     * @return number of times
     */
    public int getCounter() {
        return counter;
    }

    public byte[] getMsgData() {
        if (messageXl != null) {
            return messageXl.getData();
        }
        return null;
    }
}

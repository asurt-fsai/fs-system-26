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
 * Author:       Jonathan Urban/Uwe Wilhelm/Fabrice Vergnaud
 * Contact:      <linux.peak@hms-networks.com>
 * Maintainer:   Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
 */
package peak.can;

import java.util.EnumSet;
import java.util.Vector;
import java.util.Random;
import peak.can.basic.PCANBasic;
import peak.can.basic.TPCANHandle;
import peak.can.basic.TPCANMessageTypeXL;
import peak.can.basic.TPCANMsgXL;
import peak.can.basic.TPCANStatus;

/**
 * The CANSendThread class extends Thread class and is used to send CAN Messages.
 */
public class CANSendThread extends Thread
{
    // PCANBasic instance used to call read functions
    private PCANBasic pcanBasic;
    // Collection which stores all connected channels
    private Vector<ChannelItem> connectedChannelCollection = null;
    // Used to send CAN Messages with  Interval
    private int SendInterval;

    // Local CAN variables
    private TPCANMsgXL canMessageXl = null;
    private TPCANStatus ret;
    // Random Generator
    Random randomGenerator;

    public int getSendInterval()
    {
        return SendInterval;
    }

    public void setSendInterval(int interval)
    {
        SendInterval = interval;
    }

    /**
     *
     * @param pcanbasic PCANBasic instance used to call read functions
     * @param connectedChannelCollection Reference to the collection which stores all connected channels
     */
    public CANSendThread(PCANBasic pcanbasic, Vector<ChannelItem> connectedChannelCollection)
    {
        this.pcanBasic = pcanbasic;
        this.connectedChannelCollection = connectedChannelCollection;

         // Create new CAN Message
        this.canMessageXl = new TPCANMsgXL();
        this.canMessageXl.setPID((int)1024); // HEX 400
        this.canMessageXl.setDlc((short)1999); // 2000 Bytes
        this.canMessageXl.setType(EnumSet.of(TPCANMessageTypeXL.PCAN_MESSAGE_STANDARD, TPCANMessageTypeXL.PCAN_MESSAGE_XL));
        this.randomGenerator = new Random();
    }

    /**
     * Starts thread process
     */
    public void run()
    {
        while (true)
        {
            synchronized (connectedChannelCollection) {
                // Process each connected channel
                for (ChannelItem item : connectedChannelCollection)
                {
                    if ((item != MarkAllChannelItem.getInstance()) && (item.getWorking()))
                        // Call the PCANBasic Send Function
                        callAPIFunctionSend(item.getHandle());
                }
            }

            // Sleep Time
            try
            {
                Thread.sleep(SendInterval);
            }
            catch (InterruptedException e)
            {
                return;
            }
        }
    }

    /**
     * Calls the PCANBasic Send Function
     *
     * @param handle The handle of a PCAN Channel
     * @param isCanFd Channel is initialized in CAN FD mode
     */
    public void callAPIFunctionSend(TPCANHandle handle)
    {
        byte Data;
        try
        {
            int length;
            Data = (byte)randomGenerator.nextInt(249);
            length = canMessageXl.getLengthFromDLC();
            for (int i = 0; i < length; i++)
                this.canMessageXl.getData()[i]= (byte)(Data + i);

            // We execute the "Write" function of the PCANBasic
            ret = pcanBasic.WriteXL(handle, canMessageXl);
            // Process result
            if (ret == TPCANStatus.PCAN_ERROR_OK)
            {
              // Critical Area
              synchronized (Application.token)
              {
                // Put Message In the dataRowCollection
              }
            }

        }
        catch (Exception e)
        {
            System.out.println("CANSendThread Exception:" + e.getMessage());
            e.printStackTrace();
            System.exit(0);
        }
    }
}

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

import peak.can.basic.TPCANHandle;

/**
 * The ChannelItem class wraps a PCANBasic Channel within his TPCANHandle
 * and a boolean property which indicates if it is in working state.
 */
public class ChannelItem
{

    protected TPCANHandle handle;
    private boolean working = false;

    /**
     * Default Constructor
     */
    public ChannelItem()
    {
    }

    /**
     * Constructor
     * @param handle The wrapped PCANHandle
     */
    public ChannelItem(TPCANHandle handle)
    {
        this.handle = handle;
    }

    @Override
    public String toString()
    {
        String str = handle.toString();
        if (working)
            str += " Working";
        else
            str += " In Pause";
        return str;
    }

    /**
     * Gets the PCAN Handle
     * @return The handle
     */
    public TPCANHandle getHandle()
    {
        return handle;
    }
    /**
     * Sets the PCAN Handle
     * @param handle PCAN Handle
     */
    public void setHandle(TPCANHandle handle)
    {
        this.handle = handle;
    }

    /**
     * Indicates if Handle is Working
     * @return true if handle is working, false if not
     */
    public boolean getWorking()
    {
        return working;
    }

    /**
     * Sets PCAN Handle state
     * @param working true if handle is working, false if not
     */
    public void setWorking(boolean working)
    {
        this.working = working;
    }
}

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

/**
 * The MarkAllChannelItem class use an Singleton Design Pattern to represent all connected ChannelItem.
 * It has the undefined/default value for a PCAN bus (PCAN_NONEBUS) and it is labeled "All" in a JComponent.
 */

import peak.can.basic.TPCANHandle;

public class MarkAllChannelItem extends ChannelItem
{

    // Static instance
    private static MarkAllChannelItem instance;

    /**
     * Default Constructor
     */
    public MarkAllChannelItem()
    {
        // Sets the PCANHandle PCAN_NONEBUS
        this.handle = TPCANHandle.PCAN_NONEBUS;
    }

    /**
     * Gets Singleton
     * @return single instance
     */
    public static MarkAllChannelItem getInstance()
    {
        if (null == instance)
            instance = new MarkAllChannelItem();
        return instance;
    }

    /**
     * Gets a label to represent the singleton
     * @return label
     */
    @Override
    public String toString()
    {
        return "ALL";
    }
}

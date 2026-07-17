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
package peak.can;

/**
 * The MutableInteger class wraps a value of the primitive type int in an object. An object of type Integer contains a single field whose type is int.
 * This class is used because Java.Lang.Integer objects are defined as Imutable. Yet, we need to maintain object reference when it's passed to the JNI library using.
 * So, we defined a simple Class which extends Java.Lang.Object to resolve the problematic.
 *
 * @version 1.9
 */
public class MutableLong
{

    /**
     * Constructor
     * @param value int value
     */
    public MutableLong(long value)
    {
        this.value = value;
    }

    /**
     * Constructor parsing the string argument as a integer
     * @param value long as string
     * @param radix
     */
    public MutableLong(String value, int radix)
    {
        this.value = Long.parseUnsignedLong(value, radix);
    }

    /**
     * Gets long value
     * @return long value
     */
    public long getValue()
    {
        return value;
    }

    /**
     * Sets integer value
     * @param value Integer value
     */
    public void setValue(long value)
    {
        this.value = value;
    }
    public long value;

    /**
     * Overrides toString() to display int value
     * @return MutableInteger's value as a string
     */
    @Override
    public String toString()
    {
        return Long.toUnsignedString(value, 16);
    }
}

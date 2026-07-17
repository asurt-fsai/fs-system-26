/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Copyright (C) 2001-2025 PEAK System-Technik GmbH <www.peak-system.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 * Contact:      <linux.peak@hms-networks.com>
 * Author:       Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#ifndef __PCAN_USBXL_H__
#define __PCAN_USBXL_H__

/*
 * INCLUDES
 */
#include <linux/types.h>
#include <linux/usb.h>
#include <linux/can/dev.h>	/* include early because of get_can_dlc() def */

#include "src/pcan_main.h"
#include "src/pcanfd_usb.h"
#include "src/pcanxl_core_user.h"

/*
 * DEFINES
 */
#define PCAN_USBXL_PRODUCT_ID		0x0030

/*
 * External API
 */
int pcan_usbxl_init(struct pcan_usb_interface *);
int pcan_usbxl_init_ep(struct pcan_usb_interface *usb_if);

#endif

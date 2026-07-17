/* SPDX-License-Identifier: GPL-2.0 */
/*
 * PCAN-USB Pro / PCAN-USB Pro FD firmware objects
 *
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
#ifndef CANXL_USB_H
#define CANXL_USB_H

#include "src/pcanfd_usb_fw.h"

#define CANXL_USB_CLK_160MHZ		0x6

/* PCAN-USBXL specific messages */
#define CANXL_USB_TP_HEADER		0x34

struct __packed canxl_usb_tp_hdr {
	struct canxl_tx_hdr     hdr;	/* CANXL_USB_TP_HEADER */
	u32			reserved_1;
	u32			reserved_2;
	__le16			total_size;
	u16			reserved_3;
};

#define CANXL_USB_MSG_CALIBRATION	0x20

struct __packed canxl_usb_ts_msg {
	struct canxl_rx_hdr     hdr;	/* CANXL_USB_MSG_CALIBRATION */
	__le16			usb_frame_index;
	u16			unused_2;
};

#define CANXL_USB_MSG_DEBUG		0xfc

struct __packed canxl_usb_dbg_msg {
	struct canxl_rx_hdr     hdr;	/* CANXL_USB_MSG_DEBUG */
	u8			d[64];
};

#endif

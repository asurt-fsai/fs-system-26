/* SPDX-License-Identifier: GPL-2.0 */
/*
 * CAN-FD extension to PEAK-System CAN products.
 *
 * Copyright (C) 2015-2025 PEAK System-Technik GmbH <www.peak-system.com>
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
#ifndef __pcanxl_core_h__
#define __pcanxl_core_h__

#include "src/pcan_common.h"
#include "src/pcan_main.h"
#include "src/pcan_fops.h"

/* hidden flag used to check init settings
 * (see lib/libpcanfd.h:#define OFD_PCANFD_MASK              (~0xff000000)
 */
#define PCANFD_INIT_USER		0x80000000
#define PCANFD_INIT_BTR_NOK		0x40000000

int pcan_bittiming_normalize_ex(struct pcan_bittiming *pbt, u32 clock_Hz,
				const struct pcanfd_bittiming_range *caps,
				int pwm_encoding, int desired_brp);
static inline int
pcan_bittiming_normalize(struct pcan_bittiming *pbt, u32 clock_Hz,
			 const struct pcanfd_bittiming_range *caps)
{
	return pcan_bittiming_normalize_ex(pbt, clock_Hz, caps, 0, 0);
}

struct pcan_bittiming *pcan_btr0btr1_to_bittiming(struct pcan_bittiming *pbt,
						  u16 btr0btr1);

int pcanxl_debug_msg(struct pcandev *dev, char sens,
		     struct pcanxl_msg *msg, u8 *data, int err);

struct pcanfd_init *pcan_init_to_fd(struct pcandev *dev,
				    struct pcanfd_init *pfdi,
				    const TPCANInit *pi);
struct pcanxl_init *pcan_init_to_xl(struct pcandev *dev,
				    struct pcanxl_init *pxli,
				    const TPCANInit *pi);
struct pcanxl_init *pcanfd_init_to_xl(struct pcandev *dev,
				      struct pcanxl_init *pxli,
				      const struct pcanfd_init *pfdi);

static inline struct pcanxl_init *pcanxl_copy_init(struct pcanxl_init *pd,
						   const struct pcanxl_init *ps)
{
	*pd = *ps;
	return pd;
}

u32 pcan_xfer_time_ms(struct pcandev *dev, u32 tx_frm, long tx_data);

static inline u32 pcan_xfer_max_time_ms(struct pcandev *dev, u32 tx_frm)
{
	return pcan_xfer_time_ms(dev, tx_frm, -1);
}

int pcanxl_tx_delay_ex(struct pcandev *dev, int extra_ms);

static inline int pcanxl_tx_delay(struct pcandev *dev)
{
	return pcanxl_tx_delay_ex(dev, 0);
}

void __pcanxl_dev_reset(struct pcandev *dev);

#define pcanxl_dev_reset(d)	__pcanxl_dev_reset(d)

void pcanxl_dev_open_init(struct pcandev *dev);
int pcanxl_dev_open(struct pcandev *dev, struct pcanxl_init *pfdi);

int pcanxl_ioctl_set_init(struct pcandev *dev, struct pcanxl_init *pfdi);
int pcanxl_ioctl_get_init(struct pcandev *dev, struct pcanxl_init *pfdi);
int pcanxl_ioctl_reset(struct pcandev *dev, unsigned long flags);
int pcanxl_ioctl_get_state(struct pcandev *dev, struct pcanfd_state *pfds);
int pcanxl_ioctl_add_filter(struct pcandev *dev, struct pcanfd_msg_filter *pf);
int pcanxl_ioctl_add_filters(struct pcandev *dev,
			     struct pcanfd_msg_filters *pfl);
int pcanxl_ioctl_get_filters(struct pcandev *dev,
			     struct pcanfd_msg_filters *pfl);
int pcanxl_ioctl_recv_msg(struct pcandev *dev, struct pcanxl_rxmsg *pxl,
			  void __user *udatat_ptr, struct pcanusr *usr);
int pcanxl_ioctl_recv_msgs(struct pcandev *dev, struct pcanxl_rxmsgs_fd *pl,
			   struct pcanusr *usr);

int pcanxl_ioctl_send_msg(struct pcandev *dev, struct pcanxl_txmsg *pxl,
			  void __user *udata_ptr, struct pcanusr *usr);
int pcanxl_ioctl_send_msgs(struct pcandev *dev, struct pcanxl_txmsgs_fd *pl,
			   struct pcanusr *usr);
#endif

/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * CAN-FD extension to PEAK-System CAN products.
 *
 * Copyright (C) 2014-2025 PEAK System-Technik GmbH <www.peak-system.com>
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
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#ifndef __PCANXL_H__
#define __PCANXL_H__

#include <linux/version.h>
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 1, 0)
#include <linux/time_types.h>		/* __kernel_timexxx */
#else
/* linux/time_types.h introduced in kernel 5.1; define needed types inline */
#include <linux/types.h>
#ifndef PCAN_COMPAT_KERNEL_TIME_TYPES
#define PCAN_COMPAT_KERNEL_TIME_TYPES
struct __kernel_sock_timeval { __s64 tv_sec; __s64 tv_usec; };
struct __kernel_timespec      { __s64 tv_sec; __s64 tv_nsec; };
#endif
#endif

#include "pcanfd.h"			/* include the CANFD API */

/* Type values */
#define PCANXL_TYPE_NOP			PCANFD_TYPE_NOP
#define PCANXL_TYPE_CANCC		PCANFD_TYPE_CAN20_MSG
#define PCANXL_TYPE_CANFD		PCANFD_TYPE_CANFD_MSG
#define PCANXL_TYPE_STATUS		PCANFD_TYPE_STATUS
#define PCANXL_TYPE_CANXL		5
#define PCANXL_TYPE_ERROR		6

/* SET_INIT/GET_INIT flags
 *
 * PCANXL_INIT_XL means that 3 bitrates need to be specified:
 * - the nominal one
 * - the FD fata bitrate (+PCANFD_INIT_FD => mixed CANFD/CANXL network)
 * - the XL data bitrate (mixed CANFD/CANXL network xor pure CANXL network)
 *
 * Note: PCANXL_INIT_XL|PCANFD_INIT_FD implies CANFD ISO
 */
#define PCANXL_INIT_FD			PCANFD_INIT_FD
#define PCANXL_INIT_XL			0x00010000
#define PCANXL_INIT_TRX_MODE_SWITCH_ON	0x00020000
#define PCANXL_INIT_ERR_SIGNALING_OFF	0x00040000	/* CANXL mode only */

/* Pure-CANXL Pulse With Modulation settings
 * Values are given in mtq ticks based on core clock frequency with:
 * - pwms < pwml
 * - pwms+pwl <= pwm_max ~ clock (MHz) / 5M
 *   pwm_max	clock (MHz)
 *   4		20/24
 *   6		30
 *   8		40
 *   12		60
 *   16		80
 *   32		160
 */
struct pcanxl_pwm_range {
	__u16	pwml_min;
	__u16	pwml_max;
	__u16	pwms_min;
	__u16	pwms_max;
	__u16	pwmo_min;	/* 0 = no offset */
	__u16	pwmo_max;
};

struct pcanxl_pwm {
	__u16	pwm_long;
	__u16	pwm_short;
	__u16	pwm_offset;	/* 0 = no offset */
	__u16	unused;
};

enum {
	PCANXL_CAN_CC,		/* n/a */
	PCANXL_CAN_FD,		/* n/a */
	PCANXL_CAN_XL,
	PCANXL_CAN_FILLER,
	PCANXL_CAN_MAX
};

#define PCANXL_RXMT_LIMIT_NO	0	/* no limit (endless) */
#define PCANXL_RXMT_LIMIT_MAX	15	/* 1 attempt + 14 retries */

/* SSP offset (in clock sycles) */
#define PCANXL_SSP_OFFSET_SP	0		/* SSP same as SP */
#define PCANXL_SSP_OFFSET_OFF	0xffffffff	/* SSP bit test switched off */
#define PCANXL_SSP_OFFSET_MIN	1
#define PCANXL_SSP_OFFSET_MAX	0xfe

struct pcanxl_init {
	__u32			flags;
	__u32			clock_Hz;
	struct pcan_bittiming	nominal;
	struct pcan_bittiming	fd_data;
	struct pcan_bittiming	xl_data;
	struct pcanxl_pwm	xl_pwm;
	__u8			rxmt_limit[PCANXL_CAN_MAX];
};

/* [PCANXL_TYPE_STATUS]
 *
 * id field values are extended to these values:
 */
enum pcanxl_status {
	PCANXL_OVERLOAD = PCANFD_STATUS_COUNT,

	PCANXL_STATUS_COUNT
};

/* new flags value telling that err_code/_type are saved into ctrlr_data */
#define PCANXL_ERROR_BUS_CODETYPE	0x00000800

/* ctrlr_data new index names (msg.id <= PCANFD_ERROR_BUSOFF) */
#define PCANXL_ERRCODE		PCANFD_BUSLOAD_UNIT
#define PCANXL_ERRTYPE		PCANFD_BUSLOAD_DEC

/* [PCANXL_TYPE_ERROR]
 *
 * PCANXL_TYPE_ERROR supersedes PCANFD_TYPE_ERROR_MSG.
 * PCANXL_TYPE_ERROR saves err_code into ctrlr_data[PCANXL_ERRCODE], while
 * PCANFD_TYPE_ERROR saved err_code into data[0].
 * PCANFD_TYPE_ERROR is not posted anymore.
 */

/* This PCANXL_TYPE_ERROR has not been written on the bus because of
 * error_signaling mode = off
 */
#define PCANXL_ERROR_SIGN_OFF	0x00008000	/* Error notification only */

/* [PCANXL_TYPE_CANXL]
 *
 * flags bits definition (lowest byte is backward compatible with old MSGTYPE)
 */
#define PCANXL_MSG_TRUNC_DATA	0x00001000	/* truncated data[] */
#define PCANXL_MSG_SEC		0x00002000	/* Simple Extended Content */
#define PCANXL_MSG_RRS		0x00004000	/* Remote Request Substitute */

#define PCANXL_CANCC_MAXDATALEN	PCANFD_CAN20_MAXDATALEN
#define PCANXL_CANFD_MAXDATALEN	PCANFD_CANFD_MAXDATALEN
#define PCANXL_CANXL_MAXDATALEN	2048

#define PCANXL_MAXDATALEN	PCANXL_CANXL_MAXDATALEN

/* CAN_CC/CAN_FD PID = upper 11 bits of the 29-bit ID field */
#define PCANXL_PID_MASK		0x000007ffUL
#define PCANXL_VCID_MASK	0x00ff0000UL

#define PCANXL_PID(id)		((__u16)((id) & PCANXL_PID_MASK))
#define PCANXL_VCID(id)		((__u8)(((__u32)(id) & PCANXL_VCID_MASK) >> 16))
#define PCANXL_ID(v, p)		((((__u32)(v) << 16) & PCANXL_VCID_MASK) | \
				((p) & PCANXL_PID_MASK))

/* CiA611-1 SDU Type */
#define PCANXL_SDT_CONTENT		0x01	/* af = message id */
#define PCANXL_SDT_NODE			0x02	/* af = dest + src addr */
#define PCANXL_SDT_TUNNEL_CAN		0x03	/* af = CAN frame 11/29 b ID */
#define PCANXL_SDT_TUNNEL_ETH		0x04	/* af = user defined */
#define PCANXL_SDT_TUNNEL_ETH_MAP	0x05	/* af = truncated dest MAC addr
						   vci = vlan id */

/* new ctrlr_data indexes */
enum pcanxl_ctrlr_data {
	PCANXL_POS_CODE,			/* PCANXL_OVERLOAD */
	PCANXL_CTRLRDATA_UNUSED_1,
	PCANXL_CTRLRDATA_UNUSED_2,
	PCANXL_CTRLRDATA_UNUSED_3,
	PCANXL_CTRLRDATA_UNUSED_4,
	PCANXL_CTRLRDATA_UNUSED_5,
	PCANXL_CTRLRDATA_UNUSED_6,

	PCANXL_MAXCTRLRDATALEN
};

#define pcanxl_hdr					\
	__u16	type;					\
	__u16	data_len;				\
	__u32	id;					\
	__u32	flags;					\
	__u8	ctrlr_data[PCANXL_MAXCTRLRDATALEN];	\
	__u8	sdt;					\
	__u32	af;					\
	struct __kernel_timespec timestamp

/* Note:
 * @id:    8 bit vcid / 11 bit priority
 * @flags: PCANFD_MSG_RTR(MSGTYPE_RTR) ignored
 *         PCANFD_MSG_EXT(MSGTYPE_EXTENDED) ignored
 */
struct pcanxl_msg_hdr {
	pcanxl_hdr;
};

#define __flex_pcanxl_msg {						    \
	pcanxl_hdr;							    \
	__u8    data[] __attribute__((aligned(8))) __counted_by(data_len);  \
}

#define __pcanxl_msg(x) {						    \
	pcanxl_hdr;							    \
	__u8    data[x] __attribute__((aligned(8)));			    \
}

struct pcanxl_msg	__flex_pcanxl_msg;
struct pcanxl_msg_cc	__pcanxl_msg(PCANFD_CAN20_MAXDATALEN);
struct pcanxl_msg_fd	__pcanxl_msg(PCANFD_CANFD_MAXDATALEN);
struct pcanxl_msg_xl	__pcanxl_msg(PCANXL_CANXL_MAXDATALEN);

/* messages list base type (flex array of items) */
struct __flex_array_of_struct(pcanxl_msg);

#define pcanxl_msgs			pcanxl_msgs_0

/* PCANFD_OPT_CHANNEL_FEATURES option:
 * features of a channel
 */
#define PCANXL_FEATURE_XL		0x00010000

/* CANXL core options */
#define PCANXL_OPT_START		PCANFD_OPT_MAX

enum {
	PCANXL_OPT_XL_BITTIMING_RANGES = PCANXL_OPT_START,
	PCANXL_OPT_XL_PWM_RANGES,

	PCANXL_OPT_MAX
};

/* ioctls codes */
#define PCANXL_SEQ_START		0xa0

enum {
	PCANXL_SEQ_SEND_MSG = PCANXL_SEQ_START,
	PCANXL_SEQ_RECV_MSG,
};

#define PCANXL_SET_INIT		_IOC(_IOC_WRITE, PCAN_MAGIC_NUMBER, \
				     PCANFD_SEQ_SET_INIT, \
				     sizeof(struct pcanxl_init))

#define PCANXL_GET_INIT		_IOC(_IOC_READ, PCAN_MAGIC_NUMBER, \
				     PCANFD_SEQ_GET_INIT, \
				     sizeof(struct pcanxl_init))

/*  _IOC_SIZEBITS=14 => 16KB available */
#define PCANXL_SEND_MSG(d)	_IOC(_IOC_WRITE, PCAN_MAGIC_NUMBER, \
				     PCANXL_SEQ_SEND_MSG, d)
#define PCANXL_RECV_MSG(d)	_IOC(_IOC_READ, PCAN_MAGIC_NUMBER, \
				     PCANXL_SEQ_RECV_MSG, d)

/* DLC handling */
static inline __u8 pcanxl_msg_read_dlc(struct pcanxl_msg *msg)
{
	return ((msg->flags & PCANFD_DLC_MASK) >> PCANFD_DLC_SHIFT);
}

static inline void pcanxl_msg_store_dlc(struct pcanxl_msg *msg, __u8 dlc)
{
	msg->flags &= ~PCANFD_DLC_MASK;
	msg->flags |= ((__u32 )dlc << PCANFD_DLC_SHIFT) & PCANFD_DLC_MASK;
}

#endif

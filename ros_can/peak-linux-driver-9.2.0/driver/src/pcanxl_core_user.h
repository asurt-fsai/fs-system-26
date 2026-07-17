/* SPDX-License-Identifier: GPL-2.0 */
/*
 * CAN driver for PEAK System micro-CAN based adapters
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
#ifndef PCANXL_CORE_USER_H
#define PCANXL_CORE_USER_H

#include "pcanfd_core_user.h"

/* Bittimings length */
#define CANXL_NOMINAL_BRP_BITS		CANFD_TSLOW_BRP_BITS	/* 10 */
#define CANXL_NOMINAL_TSEG1_BITS	9
#define CANXL_NOMINAL_TSEG2_BITS	CANFD_TSLOW_TSEG2_BITS	/* 7 */
#define CANXL_NOMINAL_SJW_BITS		CANFD_TSLOW_SJW_BITS	/* 7 */

#define CANXL_FDDATA_BRP_BITS		CANXL_NOMINAL_BRP_BITS
#define CANXL_FDDATA_TSEG1_BITS		8
#define CANXL_FDDATA_TSEG2_BITS		7
#define CANXL_FDDATA_SJW_BITS		7

#define CANXL_XLDATA_BRP_BITS		CANXL_NOMINAL_BRP_BITS
#define CANXL_XLDATA_TSEG1_BITS		8
#define CANXL_XLDATA_TSEG2_BITS		7
#define CANXL_XLDATA_SJW_BITS		7

/*
 * DEPRECATED:
 *
 * CANFD_CMD_TIMING_SLOW
 * CANFD_CMD_TIMING_FAST
 */
#define CANXL_CMD_TIMING_NOMINAL	0x44
#define CANXL_CMD_TIMING_FD		0x45
#define CANXL_CMD_TIMING_XL		0x46

#define CANXL_CMD_PWM_CFG_XL		0x47

#define CANXL_CMD_FD_OPTS		0x55
#define CANXL_CMD_XL_OPTS		0x56

#define CANXL_CMD_RE_XMT_LIMIT_CC	0x60	/* not used yet */
#define CANXL_CMD_RE_XMT_LIMIT_FD	0x61	/* not used yet */
#define CANXL_CMD_RE_XMT_LIMIT_XL	0x62

#define CANXL_TX_MSG_CCFD		0x30
#define CANXL_TX_PAUSE			0x32
#define CANXL_TX_MSG_XL			0x33

#define CANXL_RX_MSG_CCFD		CANFD_MSG_CAN_RX
#define CANXL_RX_ERROR			CANFD_MSG_ERROR
#define CANXL_RX_STATUS			CANFD_MSG_STATUS
#define CANXL_RX_MSG_XL			0x05
#define CANXL_RX_ERR_CNT_DEC		0x06
#define CANXL_RX_ERR_NOTIF		0x07
#define CANXL_RX_PROT_EXCEPT		0x08
#define CANXL_RX_OVERLOAD		0x09
#define CANXL_RX_BUSLOAD2		0x0b
#define CANXL_RX_OVERRUN		0x21	/* Rx Buffer Overrun */

/*
 * NOT YET IMPLEMENTED
 *
 * CANFD_CMD_SET_STD_FILTER
 * CANFD_CMD_SET_ERR_GEN1
 * CANFD_CMD_SET_ERR_GEN2
 * CANFD_CMD_DIS_ERR_GEN
 * CANFD_CMD_SET_ERR_GEN_S
 */
#define CANXL_CMD_BUSLOAD2_PERIOD	0x12

#define CANXL_CMD_BUSLOAD2_PERIOD_MIN	1000

struct __packed canxl_busload2_period {
	__le16	opcode_channel;	/* CANXL_CMD_BUSLOAD2_PERIOD */
	u16	unused_1;
	__le32	period_us;	/* At least, 2x longest CAN frame */
};

#define canxl_command	canfd_command

#define CANXL_INIT_ERR_SIGNALING_ON	0x00000100
#define CANXL_INIT_TRX_MODE_SWITCH_ON	0x00000200
#define CANXL_INIT_XL_FFE		0x00001000

/* Initialize CANXL controler */
struct __packed canxl_init_mode {
	__le16	opcode_channel;	/* CANFD_CMD_NORMAL_MODE
				 * CANFD_CMD_LISTEN_ONLY_MODE */
	u8	unused_1;
	u8	ewl;		/* Error Warning limit */

	__le32	mc_flags;	/* Mode Control flags */
};

#define CANXL_TSEG1_MASK	GENMASK(CANXL_NOMINAL_TSEG1_BITS-1, 0)

#define CANXL_SJW_MASK		GENMASK(CANXL_NOMINAL_SJW_BITS-1, 0)
#define CANXL_TSEG2_MASK	GENMASK(CANXL_NOMINAL_TSEG2_BITS+9, 10)
#define CANXL_BRP_MASK		GENMASK(CANXL_NOMINAL_BRP_BITS+19, 20)

/* Set nominal, FD or XL bitrate (XL timing is based on nominal BRP) */
struct __packed canxl_timing {
	__le16	opcode_channel;	/* CANXL_CMD_TIMING_NOMINAL
       				 * CANXL_CMD_TIMING_FD
				 * CANXL_CMD_TIMING_XL */
	__le16	tseg1;
	__le32	sjw_tseg2_brp;
};

/* Set CAN-XL PWM coding (instead of NRZ) in mtq ticks based on Core clock
 * PWM coding enables throughput from 10 Mbps to 20 Mbps (CAN SIC XL transceiver
 * needed)
 */
#define CANXL_PWML_BITS		6
#define CANXL_PWMS_BITS		6
#define CANXL_PWMO_BITS		6

#define CANXL_PWML_MASK		GENMASK(CANXL_PWML_BITS-1, 0)
#define CANXL_PWMS_MASK		GENMASK(CANXL_PWMS_BITS-1, 0)
#define CANXL_PWMO_MASK		GENMASK(CANXL_PWMO_BITS-1, 0)

#define CANXL_PWM_LONG(s)	((s) & CANXL_PWML_MASK)
#define CANXL_PWM_SHORT(s)	((s) & CANXL_PWMS_MASK)
#define CANXL_PWM_OFFSET(s)	((s) & CANXL_PWMO_MASK)

struct __packed canxl_pwm_config {
	__le16	opcode_channel;	/* CANXL_CMD_PWM_CFG_XL */

	__le16	pwml;
	__le16	pwms;
	__le16	pwmo;
};

#define CANXL_SSP_OFFSET_SAME_SP		0x00	/* CANFD compatible */
#define CANXL_SSP_OFFSET_USER_MIN		0x01
#define CANXL_SSP_OFFSET_USER_MAX		0xfe
#define CANXL_SSP_OFFSET_BIT_TEST_OFF		0xff

/* Set the SSP (Secondary Sample Point) offset for CANFD/CANXL bitrate
 * The propagation delay in the data phase can be longer than the bit time. In
 * this case, the data bits are sampled at a Secondary Sample Point (SSP)
 * (see also Transmitter Delay Compensation (TDC)).
 */
struct __packed canxl_opts {
	__le16	opcode_channel;	/* CANXL_CMD_FD_OPTS
       				 * CANXL_CMD_XL_OPTS */
	u16	unused_1;

	u8	ssp_offset;	/* offset in clock cycles */
	u8	unused_2[3];
};

/* Configures the re-transmit-limit for CAN/CANFD/CANXL (CANXL only atm) */
#define CANXL_XMT_LIMIT(v)	((v) & 0xf)

struct __packed canxl_xmt_limit {
	__le16	opcode_channel;	/* CANXL_CMD_RE_XMT_LIMIT_CC
       				 * CANXL_CMD_RE_XMT_LIMIT_FD
				 * CANXL_CMD_RE_XMT_LIMIT_XL */
	u16	unused;

	u8	xmt_limit;
	u8	unused_2[3];
};

/* CANCC/CANFD/CANXL messages flags */
#define CANXL_FLG_RTR		CANFD_MSG_RTR
#define CANXL_FLG_EXT_ID	CANFD_MSG_EXT_ID	/* CANXL: 0 */
#define CANXL_FLG_HW_SRR	CANFD_MSG_HW_SRR	/* self-receive req. */
#define CANXL_FLG_SINGLE_SHOT	CANFD_MSG_SINGLE_SHOT
#define CANXL_FLG_FD_FRAME_FMT	CANFD_MSG_EXT_DATA_LEN
#define CANXL_FLG_FD_BRS	CANFD_MSG_BITRATE_SWITCH	/* CANXL: 0 */
#define CANXL_FLG_FD_ESI	CANFD_MSG_ERROR_STATE_IND	/* CANXL: 0 */
#define CANXL_FLG_API_SRR	CANFD_MSG_API_SRR

#define CANXL_CHANNEL_MASK	GENMASK(7, 4)

/* Tx message header */
struct __packed canxl_tx_hdr {
	__le16  size;		/* Multiple of 4 */
	u8	type;
	u8	channel_rsrvd;	/* unused */
};

#define CANXL_FD_DLC_MASK	GENMASK(7, 4)

/* Tx message for CANCC/CANFD:
 * - data are present only if DLC>0
 * - 32-bits aligned (if DLC=1 then sizeof(d)=4) 
 */
struct __packed canxl_tx_msg_fd {
	struct canxl_tx_hdr hdr;	/* CANXL_TX_MSG_CCFD */

	__le64	tag;		/* Self-receive message */

	u8	dlc;		/* CANFD DLC (4 upper bits) */
	u8	client;		/* Self-receive message */
	__le16	flags;

	__le32	id;
	u8	d[] __counted_by(dlc);	/* data only present if DLC > 0 */
};

/* CANXL flags for CANXL messages */
#define CANXL_MSG_XLF		0x0100	/* Must be set for CANXL frames only */

#define CANXL_XL_PID_MASK	GENMASK(10, 0)	/* Priority ID */
#define CANXL_XL_RRS		BIT(11)		/* RRS bit of frame */
#define CANXL_XL_DLC_MASK	GENMASK(22, 12)	/* Bytes count - 1 */
#define CANXL_XL_SEC		BIT(23)		/* Simple Extended Content */
#define CANXL_XL_SDT_MASK	GENMASK(31, 24)	/* SDU Type */

/* 32-bits aligned Tx message for CANXL */
struct __packed canxl_tx_msg_xl {
	struct canxl_tx_hdr hdr;	/* CANXL_TX_MSG_XL */

	__le64	tag;		/* Self-receive message */

	u8	vcid;		/* Virtual CAN ID */
	u8	client;		/* Self-receive message */
	__le16	flags;

	__le32	pid_rrs_dlc_sec_sdt;

	__le32	af;		/* Acceptance Field */
	u8	d[];		/* sizeof(d[]) = ((dlc/4)+1) * 4 */
};

#define CANXL_TX_PAUSE_DELAY_MASK	GENMASK(9, 0)

/* Tx pause is used to delay (block) reading Tx cache during delay µs.
 * This is used to limit busload and prevent overloading on rx side.
 */
struct __packed canxl_tx_pause {
	struct canxl_tx_hdr hdr;	/* CANXL_TX_PAUSE */

	u32	rsrvd_delay;	/* Tx pause in microseconds */
};

/* Rx message header */
struct __packed canxl_rx_hdr {
	__le16  size;
	u8	type;
	u8	channel_rsrvd;
	__le64	timestamp;	/* nanoseconds */
};

/* Rx message for CANCC/CANFD:
 * - data are present only if DLC>0
 * - 32-bits aligned (if DLC=1 then sizeof(d)=4) 
 */
struct __packed canxl_rx_msg_fd {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_MSG_CCFD */

	__le64	tag;		/* Self-receive message */

	u8	dlc;		/* CANFD DLC (4 upper bits) */

	u8	client;		/* Self-receive message */
	__le16	flags;

	__le32	id;
	u8	d[] __counted_by(dlc);	/* data only present if DLC > 0 */
};

/* Rx message for CANXL
 * - 32-bits aligned
 */
struct __packed canxl_rx_msg_xl {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_MSG_XL */

	__le64	tag;		/* Self-receive message */

	u8	vcid;		/* Virtual CAN ID */
	u8	client;		/* Self-receive message */
	__le16	flags;

	__le32	pid_rrs_dlc_sec_sdt;

	__le32	af;		/* Acceptance field */
	u8	d[];		/* sizeof(d[]) = ((dlc/4)+1) * 4 */
};

/* unused when type=CANXL_RX_ERR_CNT_DEC */
#define CANXL_ERR_TYPE_MASK		GENMASK(6, 4)

#define CANXL_ERR_FDF_BIT		1
#define CANXL_ERR_ID_28_21		2
#define CANXL_ERR_SOF			3
#define CANXL_ERR_IDE_BIT		5
#define CANXL_ERR_ID_20_18		6
#define CANXL_ERR_ID_17_13		7
#define CANXL_ERR_CRC_SEQ		8
#define CANXL_ERR_R0_BIT		9
#define CANXL_ERR_DATA_FLD		10
#define CANXL_ERR_DLC			11
#define CANXL_ERR_RTR_BIT		12
#define CANXL_ERR_R1_BIR		13
#define CANXL_ERR_ID_4_0		14
#define CANXL_ERR_ID_12_5		15
#define CANXL_ERR_ACTIVE_ERR_FLG	17
#define CANXL_ERR_INTERMISSION		18
#define CANXL_ERR_EFF_FDF_RSVD		20
#define CANXL_ERR_BRS_BIT		21
#define CANXL_ERR_PASSIVE_ERR_FLG	22
#define CANXL_ERR_ERROR_DELIM		23
#define CANXL_ERR_CRC_DELIM		24
#define CANXL_ERR_ACK_SLOT		25
#define CANXL_ERR_EOF			26
#define CANXL_ERR_ACK_DELIM		27
#define CANXL_ERR_OVRLD_FLAG		28
#define CANXL_ERR_ESI_BIT		29
#define CANXL_ERR_XLF_BIT		38
#define CANXL_ERR_RESXL_BIT		39
#define CANXL_ERR_ADH_BIT		40
#define CANXL_ERR_DHX_DL1_FLD		41
#define CANXL_ERR_SDT_FLD		42
#define CANXL_ERR_SEC_BIT		43
#define CANXL_ERR_DLC_XL_FLD		44
#define CANXL_ERR_SBC			45
#define CANXL_ERR_PCRC			46
#define CANXL_ERR_VCID			47
#define CANXL_ERR_AF			48
#define CANXL_ERR_DATA_XL_FLD		49
#define CANXL_ERR_CRC_XL_FLD		50
#define CANXL_ERR_FCP			51
#define CANXL_ERR_DAS			52

/* CANXL_ERR_xxx, unused when type=CANXL_RX_ERR_CNT_DEC */
#define CANXL_ERR_CODE_MASK		GENMASK(6, 0)

/* "direction" bit values */
#define CANXL_DIR_TX			0
#define CANXL_DIR_RX			1
#define CANXL_ERR_D			BIT(7)

/* CANXL_RX_ERROR	generated every time when a bus error was detected and
 *			error signaling is enabled.
 * CANXL_RX_PROT_EXCEPT	the protocol controller enters exception state e.g. on
 * 			resXL bit (recessive) or whenever an error is detected
 * 			and error signaling is disabled
 * CANXL_RX_ERR_CNT_DEC	generated every time when one of the error counters
 * 			counts down e.g. successfull frame transfer (TX / RX).
 * CANXL_RX_ERR_NOTIF	generated every time when a bus error was detected and
 * 			error signaling is disabled.
 */
struct __packed canxl_rx_error {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_ERROR,
					   CANXL_RX_PROT_EXCEPT,
					   CANXL_RX_ERR_CNT_DEC,
					   CANXL_RX_ERR_NOTIF
					 */
	u8	err_type_d;
	u8	err_code;
	u8	tx_err;		/* unused when type=CANXL_RX_ERR_NOTIF */
	u8	rx_err;		/* unused when type=CANXL_RX_ERR_NOTIF */
};

#define CANXL_STATUS_RX_BARRIER		BIT(4)	/* Receive Barrier */
#define CANXL_STATUS_ERROR_PASSIVE	BIT(5)	/* rx_err or tx_err >= 128 */
#define CANXL_STATUS_ERROR_STATUS	BIT(6)	/* rx_err or tx_err >= EWL */
#define CANXL_STATUS_BUS_STATUS		BIT(7)	/* Bus-Off */

/* A status frame is generated every time when internal status has changed to
 * forward info to the application.
 */
struct __packed canxl_rx_status {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_STATUS */

	u8	rb_ep_es_bs;
	u8	unused_2[3];
};

#define CANXL_OVL_D				BIT(7)

#define CANXL_POS_EOF_BIT_7			0
#define CANXL_POS_DELIM_BIT_8_ACTIVE_FLG	1
#define CANXL_POS_DELIM_BIT_8_PASSIVE_FLG	2
#define CANXL_POS_DELIM_BIT_8_OVERLOAD_FLG	3
#define CANXL_POS_INTERMISSION_BIT_1		4
#define CANXL_POS_INTERMISSION_BIT_2		5

#define CANXL_POS_CODE_MASK			GENMASK(3, 0)

/* An overload frame is send e.g. during INTERMISSION field, see detailed
 * position codes.
 */
struct __packed canxl_rx_overload {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_OVERLOAD */

	u8	d;
	u8	pos_code;		/* see CANXL_POS_xxx */

	u8	unused_3[2];
};

#define CANXL_BUSLOAD2_IV	BIT(2)	/* Interval Violation */
#define CANXL_BUSLOAD2_RM	BIT(3)	/* CAN controller in Reset Mode */
#define CANXL_BUSLOAD2_BS	BIT(7)	/* Bus Status flag of core (bus-off) */

/* Busload record showing information about bus usage ratios. */
struct __packed canxl_rx_busload2 {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_BUSLOAD2 */

	__le32	poi_time_low;
	__le32	poi_time_high;
	__le32	idle_counter;
	__le32	busy_counter;
	u8	bs_rm_iv;
	u8	zero[3];
};

/* An overrun frame is generated every time when a record is discarded
 * internally.
 */
struct __packed canxl_rx_overrun {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_OVERRUN */

	u8	unused[4];
};

#define CANXL_BUSLOAD_MASK	GENMASK(11, 0)

/* A busload frame will be generated every 4096 bittimes */
struct __packed canxl_rx_busload {
	struct canxl_rx_hdr	hdr;	/* CANXL_RX_BUSLOAD */

	u8	unused_1[2];

	u16	busload;
};

void canxl_dump_rx_msg(const char *prompt, void *rx_msg);

/* CANXL ctrl plane functions */
int canxl_set_bus_on(struct pcandev *dev);
int canxl_set_bus_off(struct pcandev *dev);

/* CANXL high level functions */
int canxl_soft_init(struct pcandev *dev, struct pcan_version *hw_ver);
int canxl_device_open_xl(struct pcandev *dev, struct pcanxl_init *pfdi,
			 u16 ext_to_set, u16 ext_to_clr);
int canxl_device_open_fd(struct pcandev *dev, struct pcanfd_init *pfdi,
			 u16 ext_to_set, u16 ext_to_clr);
int canxl_device_close(struct pcandev *dev);

/* Specific CANXL rx message handlers */
int canxl_post_rxmsg_fd(struct pcandev *dev, struct canxl_rx_msg_fd *rm,
			struct pcan_timespec *ptv);
int canxl_post_rxmsg_xl(struct pcandev *dev, struct canxl_rx_msg_xl *rm,
			struct pcan_timespec *ptv);
int canxl_post_error_notification(struct pcandev *dev,
				  struct canxl_rx_error *pe,
				  struct pcan_timespec *ptv);
int canxl_post_protocol_exception(struct pcandev *dev,
				  struct canxl_rx_error *pe,
				  struct pcan_timespec *ptv);
int canxl_post_overload(struct pcandev *dev,
			struct canxl_rx_overload *pe,
			struct pcan_timespec *ptv);

int canxl_post_error(struct pcandev *dev, struct canxl_rx_error *er,
		     struct pcan_timespec *ptv);
int canxl_post_status(struct pcandev *dev, struct canxl_rx_status *st,
		      struct pcan_timespec *ptv);
int canxl_post_busload2(struct pcandev *dev, struct canxl_rx_busload2 *bl,
		        struct pcan_timespec *ptv);

/* Generic CANXL messages handlers */
int canxl_handle_msg(struct ucan_engine *ucan, void *msg_addr);
int canxl_encode_txmsg(struct pcandev *dev, u8 *buffer_addr, int buffer_size);

#endif	/* PCANXL_CORE_USER_H */

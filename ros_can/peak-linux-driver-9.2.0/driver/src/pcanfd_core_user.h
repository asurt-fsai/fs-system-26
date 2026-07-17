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
#ifndef CANFD_CORE_USER_H
#define CANFD_CORE_USER_H

/* CANFD commands opcodes list (low-order 10 bits) */
#define CANFD_CMD_NOP			0x000
#define CANFD_CMD_RESET_MODE		0x001
#define CANFD_CMD_NORMAL_MODE		0x002
#define CANFD_CMD_LISTEN_ONLY_MODE	0x003
#define CANFD_CMD_TIMING_SLOW		0x004
#define CANFD_CMD_TIMING_FAST		0x005
#define CANFD_CMD_SET_STD_FILTER	0x006
#define CANFD_CMD_RESERVED2		0x007
#define CANFD_CMD_FILTER_STD		0x008
#define CANFD_CMD_TX_ABORT		0x009
#define CANFD_CMD_WR_ERR_CNT		0x00a
#define CANFD_CMD_SET_EN_OPTION		0x00b
#define CANFD_CMD_CLR_DIS_OPTION	0x00c
#define CANFD_CMD_RX_BARRIER		0x010

#define CANFD_CMD_END_OF_COLLECTION	0x3ff

/* CANFD received messages list */
#define CANFD_MSG_CAN_RX		0x0001
#define CANFD_MSG_ERROR			0x0002
#define CANFD_MSG_STATUS		0x0003
#define CANFD_MSG_BUSLOAD		0x0004

#define CANFD_MSG_CACHE_CRITICAL	0x0102

/* CANFD transmitted messages */
#define CANFD_MSG_CAN_TX		0x1000

/* CANFD Tx Pause record */
#define CANFD_MSG_CAN_TX_PAUSE		0x1002

/* CANFD command common header */
#define CANFD_CMD_OPCODE(c)		((c)->opcode_channel & 0x3ff)
#define CANFD_CMD_CHANNEL(c)		((c)->opcode_channel >> 12)
#define CANFD_CMD_OPCODE_CHANNEL(c, o)	cpu_to_le16(((c) << 12) | ((o) & 0x3ff))

struct __packed canfd_command {
	__le16	opcode_channel;
	__le16	args[3];
};

#define CANFD_TSLOW_BRP_BITS		10
#define CANFD_TFAST_BRP_BITS		10

/* current version of CANFD IP core */
#define CANFD_TSLOW_TSEG1_BITS		8
#define CANFD_TSLOW_TSEG2_BITS		7
#define CANFD_TSLOW_SJW_BITS		7

#define CANFD_TFAST_TSEG1_BITS		5
#define CANFD_TFAST_TSEG2_BITS		4
#define CANFD_TFAST_SJW_BITS		4

#define CANFD_TSLOW_BRP_MASK		((1 << CANFD_TSLOW_BRP_BITS) - 1)
#define CANFD_TSLOW_TSEG1_MASK		((1 << CANFD_TSLOW_TSEG1_BITS) - 1)
#define CANFD_TSLOW_TSEG2_MASK		((1 << CANFD_TSLOW_TSEG2_BITS) - 1)
#define CANFD_TSLOW_SJW_MASK		((1 << CANFD_TSLOW_SJW_BITS) - 1)

#define CANFD_TFAST_BRP_MASK		((1 << CANFD_TFAST_BRP_BITS) - 1)
#define CANFD_TFAST_TSEG1_MASK		((1 << CANFD_TFAST_TSEG1_BITS) - 1)
#define CANFD_TFAST_TSEG2_MASK		((1 << CANFD_TFAST_TSEG2_BITS) - 1)
#define CANFD_TFAST_SJW_MASK		((1 << CANFD_TFAST_SJW_BITS) - 1)

/* CANFD TIMING_SLOW command fields */
#define CANFD_TSLOW_SJW_T(s, t)		(((s) & CANFD_TSLOW_SJW_MASK) | \
								((!!(t)) << 7))
#define CANFD_TSLOW_TSEG2(t)		((t) & CANFD_TSLOW_TSEG2_MASK)
#define CANFD_TSLOW_TSEG1(t)		((t) & CANFD_TSLOW_TSEG1_MASK)
#define CANFD_TSLOW_BRP(b)		cpu_to_le16((b) & CANFD_TSLOW_BRP_MASK) 

struct __packed canfd_timing_slow {
	__le16	opcode_channel;

	u8	ewl;		/* Error Warning limit */
	u8	sjw_t;		/* Sync Jump Width + Triple sampling */
	u8	tseg2;		/* Timing SEGment 2 */
	u8	tseg1;		/* Timing SEGment 1 */

	__le16	brp;		/* BaudRate Prescaler */
};

/* CANFD TIMING_FAST command fields */
#define CANFD_TFAST_SJW(s)		((s) & CANFD_TFAST_SJW_MASK)
#define CANFD_TFAST_TSEG2(t)		((t) & CANFD_TFAST_TSEG2_MASK)
#define CANFD_TFAST_TSEG1(t)		((t) & CANFD_TFAST_TSEG1_MASK)
#define CANFD_TFAST_BRP(b)		cpu_to_le16((b) & CANFD_TFAST_BRP_MASK)

struct __packed canfd_timing_fast {
	__le16	opcode_channel;

	u8	unused;
	u8	sjw;		/* Sync Jump Width */
	u8	tseg2;		/* Timing SEGment 2 */
	u8	tseg1;		/* Timing SEGment 1 */

	__le16	brp;		/* BaudRate Prescaler */
};

/* (old) CANFD FILTER_STD command fields */
#define CANFD_FLTSTD_ROW_IDX_BITS	6

struct __packed canfd_filter_std {
	__le16	opcode_channel;

	__le16	idx;
	__le32	mask;		/* CAN-ID bitmask in idx range */
};

/* CANFD SET_STD_FILTER command fields */
struct __packed canfd_std_filter {
	__le16	opcode_channel;

	u8	unused;
	u8	idx;
	__le32	mask;		/* CAN-ID bitmask in idx range */
};

/* CANFD TX_ABORT commands fields */
#define CANFD_TX_ABORT_FLUSH		0x0001

struct __packed canfd_tx_abort {
	__le16	opcode_channel;

	__le16	flags;
	u32	unused;
};

/* CANFD WR_ERR_CNT command fields */
#define CANFD_WRERRCNT_TE		0x4000	/* Tx error cntr write Enable */
#define CANFD_WRERRCNT_RE		0x8000	/* Rx error cntr write Enable */

struct __packed canfd_wr_err_cnt {
	__le16	opcode_channel;

	__le16	sel_mask;
	u8	tx_counter;	/* Tx error counter new value */
	u8	rx_counter;	/* Rx error counter new value */

	u16	unused;
};

/* CANFD SET_EN_OPTION/CLR_DIS_OPTION commands fields */
#define CANFD_OPTION_ERROR		0x0001
#define CANFD_OPTION_BUSLOAD		0x0002
#define CANFD_OPTION_ISO_MODE		0x0004
#define CANFD_OPTION_LO_MODE		0x0008	/* Diag FD only */
#define CANFD_OPTION_20AB_MODE		0x0010	/* force CAN 2.0 A/B format */
#define CANFD_OPTION_TS_SOF		0x0020	/* TS at SOF instead of EOF */
#define CANFD_OPTION_SELF_ACK		0x0040	/* Send ACK when writing */
#define CANFD_OPTION_BRS_IGN		0x0080	/* Ign rx BRS frames */

struct __packed canfd_option {
	__le16	opcode_channel;

	__le16	mask;
	u16	unused;
	__le16	ext_mask;
};

#ifdef PCANFD_FEATURE_ERR_GEN

/* Error Generator part */
#define CANFD_CMD_SET_ERR_GEN_S		0x011

#define CANFD_ERR_GEN_ERR_POS_BIT	10

#define CANFD_ERR_GEN_ERR_POS_MASK	GENMASK(CANFD_ERR_GEN_ERR_POS_BIT-1, 0)
#define CANFD_ERR_GEN_ERR_POS(p)	((p) & CANFD_ERR_GEN_ERR_POS_MASK)

struct __packed canfd_set_err_gen_s {
	__le16	opcode_channel;	/* CANFD_CMD_SET_ERR_GEN_S */

	__le16	err_pos;
	__le32	unused;
};

#define CANFD_CMD_SET_ERR_GEN_1		0x00d
#define CANFD_CMD_SET_ERR_GEN		CANFD_CMD_SET_ERR_GEN_1

#define CANFD_ERR_GEN_ID_BIT		29

#define CANFD_ERR_GEN_ID_MASK		GENMASK(CANFD_ERR_GEN_ID_BIT-1, 0)
#define CANFD_ERR_GEN_ID(id)		((id) & CANFD_ERR_GEN_ID_MASK)

struct __packed canfd_set_err_gen_1 {
	__le16	opcode_channel;	/* CANFD_CMD_SET_ERR_GEN_1 */

	__le16	err_pos;
	__le32	id;
};

#define CANFD_CMD_SET_ERR_GEN_2		0x00e

struct __packed canfd_set_err_gen_2 {
	__le16	opcode_channel;	/* CANFD_CMD_SET_ERR_GEN_2 */

	__le16	unsed;
	__le16	to_kill;
	__le16	to_spare;
};

#define CANFD_CMD_DIS_ERR_GEN		0x00f

#endif

/* CANFD received messages global format */
struct __packed canfd_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
};

/* CANFD flags for CAN/CANFD messages */
#define CANFD_MSG_API_SRR		0x80	/* tx frame echo + tag */
#define CANFD_MSG_ERROR_STATE_IND	0x40	/* error state indicator */
#define CANFD_MSG_BITRATE_SWITCH	0x20	/* bitrate switch */
#define CANFD_MSG_EXT_DATA_LEN		0x10	/* extended data length */
#define CANFD_MSG_SINGLE_SHOT		0x08
#define CANFD_MSG_HW_SRR		0x04	/* loopback */
#define CANFD_MSG_EXT_ID		0x02
#define CANFD_MSG_RTR			0x01

#define CANFD_MSG_CHANNEL(m)		((m)->channel_dlc & 0xf)
#define CANFD_MSG_DLC(m)		((m)->channel_dlc >> 4)

struct __packed canfd_rx_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
	__le32	tag_low;
	__le32	tag_high;
	u8	channel_dlc;
	u8	client;
	__le16	flags;
	__le32	can_id;
	u8	d[];
};

/* CANFD error types */
#define CANFD_ERMSG_BIT_ERROR		0
#define CANFD_ERMSG_FORM_ERROR		1
#define CANFD_ERMSG_STUFF_ERROR		2
#define CANFD_ERMSG_OTHER_ERROR		3
#define CANFD_ERMSG_ERR_CNT_DEC		4

#define CANFD_ERMSG_CHANNEL(e)		((e)->channel_type_d & 0x0f)
#define CANFD_ERMSG_ERRTYPE(e)		(((e)->channel_type_d >> 4) & 0x07)
#define CANFD_ERMSG_D(e)		((e)->channel_type_d & 0x80)

#define CANFD_ERMSG_ERRCODE(e)		((e)->code_g & 0x7f)
#define CANFD_ERMSG_G(e)		((e)->code_g & 0x80)

struct __packed canfd_error_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
	u8	channel_type_d;
	u8	code_g;
	u8	tx_err_cnt;
	u8	rx_err_cnt;
};

#define CANFD_STMSG_CHANNEL(e)		((e)->channel_p_w_b & 0x0f)
#define CANFD_STMSG_RB(e)		((e)->channel_p_w_b & 0x10)
#define CANFD_STMSG_PASSIVE(e)		((e)->channel_p_w_b & 0x20)
#define CANFD_STMSG_WARNING(e)		((e)->channel_p_w_b & 0x40)
#define CANFD_STMSG_BUSOFF(e)		((e)->channel_p_w_b & 0x80)

struct __packed canfd_status_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
	u8	channel_p_w_b;
	u8	unused[3];
};

#define CANFD_BLMSG_CHANNEL(e)		((e)->channel & 0x0f)

struct __packed canfd_bus_load_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
	u8	channel;
	u8	unused;
	__le16	bus_load;
};

#define CANFD_CCMSG_CHANNEL(e)		((e)->channel & 0x0f)

struct __packed canfd_cache_critical_msg {
	__le16	size;
	__le16	type;
	__le32	ts_low;
	__le32	ts_high;
	u8	channel;
	u8	unused[3];
};

/* CANFD transmitted message format */
#define CANFD_MSG_CHANNEL_DLC(c, d)	(((c) & 0xf) | ((d) << 4))

struct __packed canfd_tx_msg {
	__le16	size;
	__le16	type;
	__le32	tag_low;
	__le32	tag_high;
	u8	channel_dlc;
	u8	client;
	__le16	flags;
	__le32	can_id;
	u8	d[];
};

/* CANFD Tx Pause record */
#define CANFD_TXPAUSE_DELAY_MAX		0x3ff
#define CANFD_TXPAUSE_DELAY(d)		((d) & CANFD_TXPAUSE_DELAY_MAX)

struct __packed canfd_tx_pause {
	__le16	size;
	__le16	type;
	__le16	delay;			/* pause in µs (10-low order bits) */
	__le16	reserved;
};

#ifndef get_can_dlc

/* some (very) old Kernels don't #define get_can_dlc() */
#define get_can_dlc(i)			(min_t(__u8, (i), 8))

#endif

/* CANFD utilities */
u8 pcan_dlc2len(u8 can_dlc);
u8 pcan_len2dlc(u8 len);

/* uCAN message programming interface */
struct pcandev *canfd_init_cmd(struct pcandev *dev);
int canfd_flush_cmd(struct pcandev *dev);
void *canfd_add_cmd(struct pcandev *dev, int cmd_op);

/* uCAN interface functions */
void *canfd_add_cmd_nop(struct pcandev *dev);
void *canfd_add_cmd_reset_mode(struct pcandev *dev);
void *canfd_add_cmd_rx_barrier(struct pcandev *dev);
void *canfd_add_cmd_wr_err_cnt(struct pcandev *dev, u16 sel_mask,
			       u8 tx_counter, u8 rx_counter);
void *canfd_add_cmd_set_en_option(struct pcandev *dev, u16 mask, u16 ext_mask);
void *canfd_add_cmd_clr_dis_option(struct pcandev *dev, u16 mask, u16 ext_mask);

/* CANFD ctrl plane functions */
int canfd_set_bus_on(struct pcandev *dev);
int canfd_set_bus_off(struct pcandev *dev);
int canfd_set_options(struct pcandev *dev, u16 mask, u16 ext_mask);
int canfd_clr_options(struct pcandev *dev, u16 mask, u16 ext_mask);

int canfd_clr_err_counters(struct pcandev *dev);
int canfd_set_all_acceptance_filter(struct pcandev *dev);

int canfd_set_msg_filters(struct pcandev *dev, u16 mask);
int canfd_clr_msg_filters(struct pcandev *dev, u16 mask);

int canfd_tx_abort(struct pcandev *dev, u16 flags);
int canfd_rx_barrier(struct pcandev *dev);

int canfd_set_clock_domain(struct pcandev *dev, struct pcanxl_init *pfdi);

/* CANFD high level functions */
int canfd_soft_init(struct pcandev *dev, struct pcan_version *hw_ver);
int canfd_device_open_fd(struct pcandev *dev, struct pcanfd_init *pfdi,
			 u16 ext_to_set, u16 ext_to_clr);
int canfd_device_close(struct pcandev *dev);
int canfd_reset_path(struct pcandev *dev);

#ifdef PCANFD_FEATURE_ERR_GEN
int canfd_handle_error_generator_option(struct pcandev *dev,
				     struct pcanfd_error_generator *eg);
#endif

/* Specific CANFD rx message handlers */
int canfd_post_rxmsg(struct pcandev *dev, struct canfd_rx_msg *msg,
		     struct pcan_timespec *ptv);
int canfd_post_error(struct pcandev *dev, struct canfd_error_msg *em,
		     struct pcan_timespec *ptv);
int canfd_post_status(struct pcandev *dev, struct canfd_status_msg *sm,
		      struct pcan_timespec *ptv);
int canfd_post_busload(struct pcandev *dev, struct canfd_bus_load_msg *bl,
		       struct pcan_timespec *ptv);
int canfd_post_overflow(struct pcandev *dev, struct pcan_timespec *ptv);

/* Utils */
int canfd_handle_rxmsg_flags(struct pcanxl_rxmsg *rx, u16 msg_flags,
			     u8 client);
int canfd_encode_txmsg_flags(struct pcanxl_txmsg *tx, u16 *msg_flags,
			     u8 *client);

/* Generic CANFD message handlers */
int canfd_handle_rxmsg(struct ucan_engine *ucan, void *msg_addr);
int canfd_encode_txmsg(struct pcandev *dev, u8 *buffer_addr, int buffer_size);

/* uCAN Core messages list/buffer handlers */
int ucan_handle_msgs_buffer(struct ucan_engine *canfd, void *msg_addr,
			    int msg_len);
int ucan_handle_msgs_list(struct ucan_engine *canfd, void *msg_addr,
			  int *msg_count);
int ucan_encode_msgs_buffer(struct pcandev *dev, u8 *buffer_addr,
			    int *buffer_size);
#endif

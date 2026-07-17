/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcanfd_ucan.c - the uCAN firmware global interface
 *
 * Copyright (C) 2014-2025 PEAK System-Technik GmbH <www.peak-system.com>
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
 * Credit:       Austin Anderson <austin.anderson@advanced-space.com>
 *               (endianess issue with __le16 flags in struct canfd_tx_msg)
 */
/*#define DEBUG*/
/*#undef DEBUG*/

#include "src/pcan_common.h"
#include "src/pcan_main.h"

#ifdef NETDEV_SUPPORT
#include "src/pcan_netdev.h"            /* for hotplug pcan_netdev_register() */
#else
#include <linux/can/dev.h>
#endif

#include "src/pcanxl_core.h"
#include "src/pcanfd_core_user.h"	/* uCAN base common messages */

#ifdef USB_SUPPORT
#include "src/pcanfd_usb_fw.h"		/* uCAN USB devices specific messages */
#endif

#ifdef DEBUG_USB_LITE
#define DEBUG_BUS_MODE
#define DEBUG_SLOW_BITTIMINGS
#define DEBUG_FAST_BITTIMINGS
#define DEBUG_ERR_GEN

#ifdef DEBUG
//#define DEBUG_BUS_LOAD	/* very (VERY) verbose (one msg every 500 µs) */
#define DEBUG_RX_PATH
#define DEBUG_TX_PATH
#define DEBUG_TRACE
#endif
#endif

/* if defined, set the number of times an outgoing CAN message is repeated
 * in the outgoing stream. This enables to do some internal tests only!
 * This MUST not be defined in a production version!
 */
//#define CANFD_TEST_TX_BURST		5

/* If defined, do single-frame uCAN ouput records.
 * If not defined, the buffer is filled with pending frames.
 */
//#define CANFD_WRITE_ONE_FRAME_PER_PACKET

/* Hardware timing capabilities */
static const struct pcanfd_bittiming_range canfd_slow_capabilities = {

	.brp_min = 1,
	.brp_max = (1 << CANFD_TSLOW_BRP_BITS),
	.brp_inc = 1,

	.tseg1_min = 1,
	.tseg1_max = (1 << CANFD_TSLOW_TSEG1_BITS),	// 64 or 256
	.tseg2_min = 1,
	.tseg2_max = (1 << CANFD_TSLOW_TSEG2_BITS),	// 16 or 128
	.sjw_min = 1,
	.sjw_max = (1 << CANFD_TSLOW_SJW_BITS)		// 16 or 128
};

static const struct pcanfd_bittiming_range canfd_fast_capabilities = {

	.brp_min = 1,
	.brp_max = (1 << CANFD_TFAST_BRP_BITS),
	.brp_inc = 1,
	.tseg1_min = 1,
	.tseg1_max = (1 << CANFD_TFAST_TSEG1_BITS),	// 16 or 32
	.tseg2_min = 1,
	.tseg2_max = (1 << CANFD_TFAST_TSEG2_BITS),	// 8 or 16
	.sjw_min = 1,
	.sjw_max = (1 << CANFD_TFAST_SJW_BITS)		// 4 or 16
};

typedef struct __array_of_struct(pcanfd_available_clock, 6)
	pcanfd_6_clocks_device;

static const pcanfd_6_clocks_device canfd_clocks = {
	.count = 6,
	.list = {
		[0] = { .clock_Hz = 80*MHz, .clock_src = 80*MHz, },
		[1] = { .clock_Hz = 20*MHz, .clock_src = 240*MHz, },
		[2] = { .clock_Hz = 24*MHz, .clock_src = 240*MHz, },
		[3] = { .clock_Hz = 30*MHz, .clock_src = 240*MHz, },
		[4] = { .clock_Hz = 40*MHz, .clock_src = 240*MHz, },
		[5] = { .clock_Hz = 60*MHz, .clock_src = 240*MHz, },
	}
};

static const u8 pcan_fd_dlc2len[] = {
	0, 1, 2, 3, 4, 5, 6, 7,
	8, 12, 16, 20, 24, 32, 48, 64
};

/* get data length from can_dlc with sanitized can_dlc */
u8 pcan_dlc2len(u8 can_dlc)
{
	return pcan_fd_dlc2len[can_dlc & 0x0F];
}

static const u8 pcan_fd_len2dlc[] = {
	0, 1, 2, 3, 4, 5, 6, 7, 8,	/* 0 - 8 */
	9, 9, 9, 9,			/* 9 - 12 */
	10, 10, 10, 10,			/* 13 - 16 */
	11, 11, 11, 11,			/* 17 - 20 */
	12, 12, 12, 12,			/* 21 - 24 */
	13, 13, 13, 13, 13, 13, 13, 13,	/* 25 - 32 */
	14, 14, 14, 14, 14, 14, 14, 14,	/* 33 - 40 */
	14, 14, 14, 14, 14, 14, 14, 14,	/* 41 - 48 */
	15, 15, 15, 15, 15, 15, 15, 15,	/* 49 - 56 */
	15, 15, 15, 15, 15, 15, 15, 15	/* 57 - 64 */
};

/* map the sanitized data length to an appropriate data length code */
u8 pcan_len2dlc(u8 len)
{
	if (len > 64)
		return 0xF;

	return pcan_fd_len2dlc[len];
}

struct pcandev *canfd_init_cmd(struct pcandev *dev)
{
	dev->ucan.cmd_len = 0;
	return dev;
}

int canfd_flush_cmd(struct pcandev *dev)
{
	if (dev->ucan.cmd_len && !dev->ucan.ops.send_cmd(dev))
		canfd_init_cmd(dev);

	return dev->ucan.cmd_len;
}

void *canfd_add_cmd(struct pcandev *dev, int cmd_op)
{
	const int cmd_size = sizeof(u64);
	struct canfd_command *cmd;

	if (dev->ucan.cmd_len + cmd_size > dev->ucan.cmd_size) {
#ifdef DEBUG_ALL
		pr_info(DEVICE_NAME ": %s(): device cmd buffer full "
			" (%u+%u > %u): it is flushed!\n",
		       DEVICE_NAME, __func__,
		       dev->ucan.cmd_len, cmd_size, dev->ucan.cmd_size);
#endif
		if (canfd_flush_cmd(dev))
			return NULL;

		canfd_init_cmd(dev);
	}

	cmd = dev->ucan.cmd_head + dev->ucan.cmd_len;

	/* unused bits should be 0 */
	*(u64 *)cmd = 0;

	cmd->opcode_channel = CANFD_CMD_OPCODE_CHANNEL(dev->can_idx, cmd_op);
	dev->ucan.cmd_len += cmd_size;

	return cmd;
}

/* uCAN commands interface functions */

void *canfd_add_cmd_nop(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_NOP);
}

void *canfd_add_cmd_reset_mode(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_RESET_MODE);
}

static void *canfd_add_cmd_normal_mode(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_NORMAL_MODE);
}

static void *canfd_add_cmd_listen_only_mode(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_LISTEN_ONLY_MODE);
}

#ifdef PCANFD_FEATURE_ERR_GEN

static void *canfd_add_cmd_err_gen_s(struct pcandev *dev,
				     struct pcanfd_error_generator *eg)
{
	struct canfd_set_err_gen_s *cmd = canfd_add_cmd(dev, CANFD_CMD_SET_ERR_GEN_S);
	if (cmd) {
#ifdef DEBUG_ERR_GEN
		pr_info(DEVICE_NAME
			"%u: single shot error generator on bit #%u\n",
			dev->nMinor, eg->bit_pos);
#endif
		cmd->err_pos = cpu_to_le16(CANFD_ERR_GEN_ERR_POS(eg->bit_pos));
	}

	return cmd;
}

static void *canfd_add_cmd_err_gen_1(struct pcandev *dev,
				     struct pcanfd_error_generator *eg)
{
	struct canfd_set_err_gen_1 *cmd = canfd_add_cmd(dev, CANFD_CMD_SET_ERR_GEN_1);
	if (cmd) {
#ifdef DEBUG_ERR_GEN
		pr_info(DEVICE_NAME
			"%u: error generator_1: bit #%u on next ID %08xh\n",
			dev->nMinor, eg->bit_pos, eg->can_id);
#endif
		cmd->err_pos = cpu_to_le16(CANFD_ERR_GEN_ERR_POS(eg->bit_pos));
		cmd->id = cpu_to_le32(CANFD_ERR_GEN_ID(eg->can_id));
	}

	return cmd;
}

static void *canfd_add_cmd_err_gen_2(struct pcandev *dev,
				     struct pcanfd_error_generator *eg)
{
	struct canfd_set_err_gen_2 *cmd = canfd_add_cmd(dev, CANFD_CMD_SET_ERR_GEN_2);
	if (cmd) {
#ifdef DEBUG_ERR_GEN
		pr_info(DEVICE_NAME
			"%u: error generator_2: to_kill=%u to_spare=%uh\n",
			dev->nMinor, eg->to_kill_nb, eg->to_spare_nb);
#endif
		cmd->to_kill = cpu_to_le16(eg->to_kill_nb);
		cmd->to_spare = cpu_to_le16(eg->to_spare_nb);
	}

	return cmd;
}

static void *canfd_add_cmd_err_gen_dis(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_DIS_ERR_GEN);
}

int canfd_handle_error_generator_option(struct pcandev *dev,
				     struct pcanfd_error_generator *eg)
{
	void *cmd = canfd_init_cmd(dev);

	switch (eg->mode) {
	case PCANFD_ERR_GEN_STOP:
		cmd = canfd_add_cmd_err_gen_dis(dev);
		break;
	case PCANFD_ERR_GEN_START_SINGLE:
		cmd = canfd_add_cmd_err_gen_s(dev, eg);
		break;
	case PCANFD_ERR_GEN_START_PERIODIC:
		cmd = canfd_add_cmd_err_gen_1(dev, eg);
		cmd = canfd_add_cmd_err_gen_2(dev, eg);
		break;
	default:
		return -EINVAL;
	}

	/* send the command */
	return (cmd) ? canfd_flush_cmd(dev) : -ENOSPC;
}
#endif

static void *canfd_add_cmd_timing_slow(struct pcandev *dev,
				       struct pcan_bittiming *pbr)
{
	struct canfd_timing_slow *cmd = canfd_add_cmd(dev, CANFD_CMD_TIMING_SLOW);
	if (cmd) {
#ifdef DEBUG_SLOW_BITTIMINGS
		pr_info(DEVICE_NAME ": pcan%u = SLOW"
			"[brp=%u tseg1=%u tseg2=%u sjw=%u ts=%u]\n",
			dev->nMinor,
			pbr->brp, pbr->tseg1, pbr->tseg2, pbr->sjw, pbr->tsam);
#endif
		cmd->sjw_t = CANFD_TSLOW_SJW_T(pbr->sjw - 1, pbr->tsam);
		cmd->tseg1 = CANFD_TSLOW_TSEG1(pbr->tseg1 - 1);
		cmd->tseg2 = CANFD_TSLOW_TSEG2(pbr->tseg2 - 1);
		cmd->brp = CANFD_TSLOW_BRP(pbr->brp - 1);

		cmd->ewl = 96;	/* default */
	}

	return cmd;
}

static void *canfd_add_cmd_timing_fast(struct pcandev *dev,
					struct pcan_bittiming *pbr)
{
	struct canfd_timing_fast *cmd = canfd_add_cmd(dev, CANFD_CMD_TIMING_FAST);
	if (cmd) {
#ifdef DEBUG_FAST_BITTIMINGS
		pr_info(DEVICE_NAME ": pcan%u = FAST"
			"[brp=%u tseg1=%u tseg2=%u sjw=%u]\n",
			dev->nMinor,
			pbr->brp, pbr->tseg1, pbr->tseg2, pbr->sjw);
#endif
		cmd->sjw = CANFD_TFAST_SJW(pbr->sjw - 1);
		cmd->tseg1 = CANFD_TFAST_TSEG1(pbr->tseg1 - 1);
		cmd->tseg2 = CANFD_TFAST_TSEG2(pbr->tseg2 - 1);
		cmd->brp = CANFD_TFAST_BRP(pbr->brp - 1);
	}

	return cmd;
}

static void *canfd_add_cmd_tx_abort(struct pcandev *dev, u16 flags)
{
	struct canfd_tx_abort *cmd = canfd_add_cmd(dev, CANFD_CMD_TX_ABORT);
	if (cmd)
		cmd->flags = cpu_to_le16(flags);

	return cmd;
}

void *canfd_add_cmd_rx_barrier(struct pcandev *dev)
{
	return canfd_add_cmd(dev, CANFD_CMD_RX_BARRIER);
}

void *canfd_add_cmd_wr_err_cnt(struct pcandev *dev, u16 sel_mask,
			       u8 tx_counter, u8 rx_counter)
{
	struct canfd_wr_err_cnt *cmd = canfd_add_cmd(dev, CANFD_CMD_WR_ERR_CNT);
	if (cmd) {
		cmd->sel_mask = cpu_to_le16(sel_mask);
		cmd->tx_counter = tx_counter;
		cmd->rx_counter = rx_counter;
	}

	return cmd;
}

void *canfd_add_cmd_set_en_option(struct pcandev *dev, u16 mask, u16 ext_mask)
{
	struct canfd_option *cmd = canfd_add_cmd(dev, CANFD_CMD_SET_EN_OPTION);
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(mask=%04xh, ext_mask=%04xh)\n",
		__func__, mask, ext_mask);
#endif
	if (cmd) {
		cmd->mask = cpu_to_le16(mask);
		cmd->ext_mask = cpu_to_le16(ext_mask);
	}

	return cmd;
}

void *canfd_add_cmd_clr_dis_option(struct pcandev *dev, u16 mask, u16 ext_mask)
{
	struct canfd_option *cmd = canfd_add_cmd(dev, CANFD_CMD_CLR_DIS_OPTION);
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(mask=%04xh, ext_mask=%04xh)\n",
		__func__, mask, ext_mask);
#endif
	if (cmd) {
		cmd->mask = cpu_to_le16(mask);
		cmd->ext_mask = cpu_to_le16(ext_mask);
	}

	return cmd;
}

/* pcan interface functions */

int canfd_clr_err_counters(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif
	if (!canfd_add_cmd_wr_err_cnt(canfd_init_cmd(dev),
				     CANFD_WRERRCNT_TE|CANFD_WRERRCNT_RE, 0, 0))
		return -EINVAL;

	dev->tx_error_counter = 0;
	dev->rx_error_counter = 0;

	/* send the command */
	return canfd_flush_cmd(dev);
}

/* int canfd_set_all_acceptance_filter(struct pcandev *dev)
 */
int canfd_set_all_acceptance_filter(struct pcandev *dev)
{
	struct canfd_std_filter *cmd = NULL;
	const int n = 1 << CANFD_FLTSTD_ROW_IDX_BITS;
	int i, err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif

	/* build (and send) a command for each row */
	canfd_init_cmd(dev);
	for (i = 0; i < n; i++) {

		while (1) {
			cmd = canfd_add_cmd(dev, CANFD_CMD_SET_STD_FILTER);
			if (cmd)
				break;

			/* not enough room? flush the cmds and retry */
			err = canfd_flush_cmd(dev);
			if (err)
				return err;
		}

		cmd->idx = i;
		cmd->mask = cpu_to_le32(0xffffffff);
	}

	/* send the pending commands */
	return canfd_flush_cmd(dev);
}

/* int canfd_tx_abort(struct pcandev *dev, u16 flags)
 */
int canfd_tx_abort(struct pcandev *dev, u16 flags)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u, flags=%04xh)\n",
		__func__, dev->nMinor, flags);
#endif
	if (!canfd_add_cmd_tx_abort(canfd_init_cmd(dev), flags))
		return -EINVAL;

	/* send the command */
	return canfd_flush_cmd(dev);
}

/* int canfd_rx_barrier(struct pcandev *dev)
 */
int canfd_rx_barrier(struct pcandev *dev)
{
#if defined(DEBUG_TRACE) || defined(DEBUG_BUS_MODE)
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	if (!canfd_add_cmd_rx_barrier(canfd_init_cmd(dev)))
		return -EINVAL;

	/* send the command */
	return canfd_flush_cmd(dev);
}

/* int canfd_set_bus_on(struct pcandev *dev)
 *
 * Set uCAN device bus controller to ON.
 */
int canfd_set_bus_on(struct pcandev *dev)
{
	int err;
	void *cmd = (dev->init_settings.flags & PCANFD_INIT_LISTEN_ONLY) ?
			canfd_add_cmd_listen_only_mode(canfd_init_cmd(dev)) :
			canfd_add_cmd_normal_mode(canfd_init_cmd(dev));

#if defined(DEBUG_TRACE) || defined(DEBUG_BUS_MODE)
	pr_info(DEVICE_NAME ": %s(pcan%u): %s\n", __func__, dev->nMinor,
		(dev->init_settings.flags & PCANFD_INIT_LISTEN_ONLY) ?
			"LISTEN_ONLY" : "NORMAL");
#endif

	if (!cmd)
		return -EINVAL;

	/* send the command */
	err = canfd_flush_cmd(dev);
	if (!err)
		dev->flags |= PCAN_DEV_BUS_ON;

	return err;
}

/* int canfd_set_bus_off(struct pcandev *dev)
 *
 * Set uCAN device bus controller to OFF.
 */
int canfd_set_bus_off(struct pcandev *dev)
{
	int err, extra_ms = 50;

#if defined(DEBUG_TRACE) || defined(DEBUG_BUS_MODE)
	pr_info(DEVICE_NAME ": %s(pcan%u): bus=%d\n",
		__func__, dev->nMinor, dev->bus_state);
#endif

	/* Prepare the command to go off the bus */
	if (!canfd_add_cmd_reset_mode(canfd_init_cmd(dev)))
		return -EINVAL;

	/* wait a bit for last data to be written on CAN bus.
	 *
	 * Imported from v8:
	 *
	 * This delay is mandatory when going to BUS_OFF with uCAN devices:
	 * - 5 ms is not enough if any data buffer was almost filled
	 * - 10 ms is enough for uCAN USB devices but not for uCAN PCIe devices
	 *
	 * Note: this wait MUST not be interruptible for USB devices.
	 */
	pcanxl_tx_delay_ex(dev, extra_ms);

	/* send the command */
	err = canfd_flush_cmd(dev);
	if (!err)
		dev->flags &= ~(PCAN_DEV_BUS_ON|PCAN_DEV_CTRLR_FATAL);

	return err;
}

int canfd_set_options(struct pcandev *dev, u16 mask, u16 ext_mask)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u, mask=%04xh, ext_mask=%04xh)\n",
		__func__, dev->nMinor, mask, ext_mask);
#endif
	if (!canfd_add_cmd_set_en_option(canfd_init_cmd(dev), mask, ext_mask))
		return -EINVAL;

	/* send the command */
	return canfd_flush_cmd(dev);
}

int canfd_clr_options(struct pcandev *dev, u16 mask, u16 ext_mask)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u, mask=%04xh, ext_mask=%04xh)\n",
		__func__, dev->nMinor, mask, ext_mask);
#endif
	if (!canfd_add_cmd_clr_dis_option(canfd_init_cmd(dev), mask, ext_mask))
		return -EINVAL;

	/* send the command */
	return canfd_flush_cmd(dev);
}

static inline int canfd_set_iso_mode(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	return canfd_set_options(dev, CANFD_OPTION_ISO_MODE, 0);
}

static inline int canfd_clr_iso_mode(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	return canfd_clr_options(dev, CANFD_OPTION_ISO_MODE, 0);
}

#ifdef CANFD_OPTION_20AB_MODE
static inline int canfd_set_can20ab_mode(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	return canfd_set_options(dev, CANFD_OPTION_20AB_MODE, 0);
}

static inline int canfd_clr_can20ab_mode(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	return canfd_clr_options(dev, CANFD_OPTION_20AB_MODE, 0);
}
#endif

static int canfd_dev_reset(struct pcandev *dev)
{
	int err;

#ifdef DEBUG_BUS_MODE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif

	err = canfd_set_bus_off(dev);
	if (err)
		return err;

	err = canfd_clr_err_counters(dev);
	if (err)
		return err;

	return canfd_set_bus_on(dev);
}

int canfd_soft_init(struct pcandev *dev, struct pcan_version *hw_ver)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif
	pcan_soft_init_ex(dev,
			  (const struct pcanfd_available_clocks *)&canfd_clocks,
			  &canfd_slow_capabilities,
			  PCAN_DEV_FD_RDY |
#ifdef PCANFD_FEATURE_ERR_GEN
			  PCAN_DEV_ERR_GEN_RDY |
#endif
			  PCAN_DEV_BUSLOAD_RDY |
			  PCAN_DEV_ECHO_RDY |
			  PCAN_DEV_SJA1000_RDY);
	
	/* Tx Pause option is available for all HW running FW >= 2.4.0 */
	if (VER_NUM(hw_ver->major,
		    hw_ver->minor,
		    hw_ver->subminor) >= VER_NUM(2, 4, 0))
		dev->features |= PCAN_DEV_TXPAUSE_RDY;

	dev->fd_bittiming_caps = &canfd_fast_capabilities;

	/* if global dbitrate is not 0, then consider to open in CAN-FD */
	if (dev->def_init_settings.fd_data.bitrate) {
		dev->def_init_settings.flags |= PCANXL_INIT_FD;

		pcan_bittiming_normalize(&dev->def_init_settings.fd_data,
					 dev->sysclock_Hz,
					 dev->fd_bittiming_caps);

		/* reset default init settings with new data bitrate specs */
		pcanxl_copy_init(&dev->init_settings, &dev->def_init_settings);
	}

	/* this kind of controller can be reset */
	dev->device_reset = canfd_dev_reset;

	return 0;
}

int canfd_set_clock_domain(struct pcandev *dev, struct pcanxl_init *pxli)
{
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	/* set the uCAN clock domain */
	if (dev->ucan.ops.set_clk_domain) {

		err = dev->ucan.ops.set_clk_domain(dev, pxli);

		/* looks like pxli->clock_Hz was wrong: it must be
		 * reset to its default value and the bittimings must be
		 * computed accordingly and the clock domain reset as well.
		 */
		if (err == -EINVAL) {

			pr_err(DEVICE_NAME "%u: "
				"unsupported user clock %u Hz: "
				"using default %u Hz\n",
				dev->nMinor, pxli->clock_Hz,
				dev->clocks_list->list[0].clock_Hz);

			/* uCAN device default clock value */
			pxli->clock_Hz = dev->clocks_list->list[0].clock_Hz;

			/* use bitrate bps value as reference to rebuild BRP,
			 * TSEGx and SJW accroding to the default clock
			 */
			pcan_bitrate_to_bittiming(&pxli->nominal,
							dev->bittiming_caps,
							pxli->clock_Hz);
			if (pxli->flags & PCANXL_INIT_FD)
				pcan_bitrate_to_bittiming(&pxli->fd_data,
							dev->fd_bittiming_caps,
							pxli->clock_Hz);

			/* finaly, reset to default clock domain */
			err = dev->ucan.ops.set_clk_domain(dev, pxli);
		}

#if defined(DEBUG_SLOW_BITTIMINGS) || defined(DEBUG_FAST_BITTIMINGS)
		pr_info(DEVICE_NAME ": pcan%u = [clk=%u]\n",
			dev->nMinor, pxli->clock_Hz);
#endif
	}

	return err;
}

int canfd_device_open_fd(struct pcandev *dev, struct pcanfd_init *pfdi,
			 u16 ext_to_set, u16 ext_to_clr)
{
	u16 opt_to_clr = 0, opt_to_set = CANFD_OPTION_ERROR;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	err = canfd_set_clock_domain(dev, (struct pcanxl_init *)pfdi);
	if (err)
		return err;

	/* Start populating the output buffer with reset error counters */
	if (!canfd_add_cmd_wr_err_cnt(canfd_init_cmd(dev),
				      CANFD_WRERRCNT_TE|CANFD_WRERRCNT_RE,
				      0, 0))
		goto fail;

	dev->tx_error_counter = 0;
	dev->rx_error_counter = 0;

	/* clear/set options */
	if (pfdi->flags & PCANFD_INIT_BUS_LOAD_INFO)
		opt_to_set |= CANFD_OPTION_BUSLOAD;
	else
		opt_to_clr |= CANFD_OPTION_BUSLOAD;

	if (pfdi->flags & PCANXL_INIT_FD) {

		opt_to_clr |= CANFD_OPTION_20AB_MODE;

		if (pfdi->flags & PCANFD_INIT_FD_NON_ISO) {
			opt_to_clr |= CANFD_OPTION_ISO_MODE;
		} else {
			opt_to_set |= CANFD_OPTION_ISO_MODE;
		}
	} else {
		/* force CAN 2.0 A/B mode */
		opt_to_set |= CANFD_OPTION_20AB_MODE;
	}

	if (opt_to_clr || ext_to_clr) {
		if (!canfd_add_cmd_clr_dis_option(dev, opt_to_clr, ext_to_clr))
			goto fail;
	}

	if (opt_to_set || ext_to_set) {
		if (!canfd_add_cmd_set_en_option(dev, opt_to_set, ext_to_set))
			goto fail;
	}

	if (pfdi->flags & PCANXL_INIT_FD) {
		if (!canfd_add_cmd_timing_fast(dev, &pfdi->data))
			goto fail;
	}

	if (!canfd_add_cmd_timing_slow(dev, &pfdi->nominal))
		goto fail;

	/* Send this buffer first */
	err = canfd_flush_cmd(dev);
	if (err)
		return err;

	/* Then, set filter mode command: accept all */
	return canfd_set_all_acceptance_filter(dev);

fail:
	return -ENOSPC;
}

/*
 * int canfd_device_close(struct pcandev *dev)
 */
int canfd_device_close(struct pcandev *dev)
{
	u16 opt_to_clr = CANFD_OPTION_ERROR|CANFD_OPTION_BUSLOAD;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif

	if (dev->flags & PCAN_DEV_SELF_ACK)
		opt_to_clr |= CANFD_OPTION_SELF_ACK;
	if (dev->flags & PCAN_DEV_TS_SOF)
		opt_to_clr |= CANFD_OPTION_TS_SOF;
	if (dev->flags & PCAN_DEV_BRS_IGN)
		opt_to_clr |= CANFD_OPTION_BRS_IGN;

	/* clear all options set */
	err = canfd_clr_options(dev, opt_to_clr, 0);
	if (!err)
		dev->flags &= ~(PCAN_DEV_SELF_ACK |
				PCAN_DEV_TS_SOF |
				PCAN_DEV_BRS_IGN);

	return err;
}

/* int canfd_reset_path(struct pcandev *dev)
 *
 * After reset, the CAN core stays active.
 */
int canfd_reset_path(struct pcandev *dev)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif
	/* reset the Tx path first */
	err = canfd_tx_abort(dev, CANFD_TX_ABORT_FLUSH);
	if (err)
		goto fail;

	/* reset the Rx path next */
	err = canfd_rx_barrier(dev);
fail:
	return err;
}

/*
 * int canfd_handle_rxmsg_flags(struct pcanxl_rxmsg *rx, u16 msg_flags,xi
 * 				u8 client)
 * RETURN:
 *
 * 0 if RTR flag is set
 * 1 if not.
 */
int canfd_handle_rxmsg_flags(struct pcanxl_rxmsg *rx, u16 msg_flags, u8 client)
{
	if (msg_flags & CANFD_MSG_EXT_DATA_LEN) {

		if (msg_flags & CANFD_MSG_BITRATE_SWITCH)
			rx->msg.flags |= PCANFD_MSG_BRS;

		if (msg_flags & CANFD_MSG_ERROR_STATE_IND)
			rx->msg.flags |= PCANFD_MSG_ESI;
	}

	if (msg_flags & CANFD_MSG_EXT_ID)
		rx->msg.flags |= PCANFD_MSG_EXT;

	if (msg_flags & CANFD_MSG_API_SRR) {
		rx->msg.flags |= PCANFD_MSG_ECHO;
		rx->msg.ctrlr_data[PCANFD_ECHOID] = client;
	}

	if (msg_flags & CANFD_MSG_HW_SRR)
		rx->msg.flags |= PCANFD_MSG_SLF;

	if (msg_flags & CANFD_MSG_SINGLE_SHOT)
		rx->msg.flags |= PCANFD_MSG_SNG;

	if (msg_flags & CANFD_MSG_RTR) {
		rx->msg.flags |= PCANFD_MSG_RTR;
		return 0;
	}

	return 1;
}

/* int canfd_post_rxmsg(struct pcandev *dev,
 *			struct canfd_rx_msg *rm, struct pcan_timespec *ptv)
 *
 *	Default handler of incoming CAN messages
 */
int canfd_post_rxmsg(struct pcandev *dev,
		     struct canfd_rx_msg *rm, struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg_fd rx;
	const u16 msg_flags = le16_to_cpu(rm->flags);
	u8 dlc = CANFD_MSG_DLC(rm);

#if defined(DEBUG_TRACE) || defined(DEBUG_RX)
	pr_info(DEVICE_NAME ": %s(pcan%u): wCANStatus=%xh "
		"rx=[flags=%04xh dlc=%02xh ts32=%u id=%08xh]\n",
		__func__, dev->nMinor, dev->wCANStatus, msg_flags, dlc,
		le32_to_cpu(rm->ts_low), le32_to_cpu(rm->can_id));
#endif

	rx.msg.flags = pcanxl_msg_flags_dlc_set(PCANFD_MSG_STD, dlc);

	if (msg_flags & CANFD_MSG_EXT_DATA_LEN) {
		/* CAN FD frame */
		rx.msg.type = PCANFD_TYPE_CANFD_MSG;
		rx.msg.data_len = pcan_dlc2len(dlc);
	} else {
		/* CAN 2.0 frame */
		rx.msg.type = PCANFD_TYPE_CAN20_MSG;
		rx.msg.data_len = get_can_dlc(dlc);
	}

	rx.msg.id = le32_to_cpu(rm->can_id);
	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

#ifdef PCANFD_RAWTIMESTAMP
	rx.msg.flags |= PCANFD_RAWTIMESTAMP;
	rx.msg.raw_timestamp = ((u64 )le32_to_cpu(rm->ts_high) << 32) |
							le32_to_cpu(rm->ts_low);
#endif

	/* check whether posting a CAN frame to user is relevant */
	if (!pcan_post_rxmsg_is_ok(dev)) {
#ifdef DEBUG_RX_PATH
		pcanxl_debug_msg(dev, 'D', (struct pcanxl_msg *)&rx.msg,
				 rm->d, 0);
#endif
		return 0;
	}

	/* map uCAN-FD message flags to pcanfd API */
	if (canfd_handle_rxmsg_flags((struct pcanxl_rxmsg *)&rx,
				     msg_flags,
				     rm->client))
		memcpy(rx.msg.data, rm->d, rx.msg.data_len);

#ifdef DEBUG_RX_PATH
	return pcanxl_debug_msg(dev, '>', (struct pcanxl_msg *)&rx.msg, rm->d,
				pcan_xxxdev_rx(dev, &rx));
#else
	return pcan_xxxdev_rx(dev, &rx);
#endif
}

int canfd_post_error(struct pcandev *dev, struct canfd_error_msg *er,
		     struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = { .msg = { .data_len = 0, } };
	struct pcan_bus_error err = {
		.type = CANFD_ERMSG_ERRTYPE(er),
		.code = CANFD_ERMSG_ERRCODE(er),
		.rx = CANFD_ERMSG_D(er),
		.gen = CANFD_ERMSG_G(er)
	};

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u): "
		"rx=[type=0x%02x ts32=0x%08x d=%u g=%u code=0x%02x "
		"err_cnt[rx=%u tx=%u]]\n",
		__func__, dev->nMinor,
		CANFD_ERMSG_ERRTYPE(er), le32_to_cpu(er->ts_low),
		!!CANFD_ERMSG_D(er),
		!!CANFD_ERMSG_G(er),
		CANFD_ERMSG_ERRCODE(er),
		er->rx_err_cnt, er->tx_err_cnt);
#endif

	/* keep a trace of tx and rx error counters for later use */
	dev->rx_error_counter = er->rx_err_cnt;
	dev->tx_error_counter = er->tx_err_cnt;

#ifdef DEBUG
	if (dev->rx_error_counter || dev->tx_error_counter)
		pr_err(DEVICE_NAME "%u: errors: rx=%u tx=%u\n", dev->nMinor,
		       dev->rx_error_counter, dev->tx_error_counter);
#endif

	/* not an "error" but a status... */
	if (CANFD_ERMSG_ERRTYPE(er) > PCANFD_ERRMSG_OTHER) {
		rx.msg.type = PCANFD_TYPE_STATUS;
		rx.msg.id = dev->bus_state;
		rx.msg.ctrlr_data[PCANXL_ERRCODE] = err.code;
		rx.msg.ctrlr_data[PCANXL_ERRTYPE] = err.type;
		rx.msg.flags = PCANFD_ERROR_BUS | PCANXL_ERROR_BUS_CODETYPE;
		if (err.rx)
			rx.msg.flags |= PCANFD_ERRMSG_RX;
	} else {
		pcan_handle_error_msg(dev, &rx, &err);
	}

	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

	return pcan_xxxdev_rx(dev, &rx);
}

int canfd_post_status(struct pcandev *dev,
		      struct canfd_status_msg *st, struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u): bus_state=%u "
		"ts32=0x%08x RB=%u EP=%u EW=%u BO=%u]\n",
		__func__, dev->nMinor, dev->bus_state,
		le32_to_cpu(st->ts_low), !!CANFD_STMSG_RB(st),
		!!CANFD_STMSG_PASSIVE(st), !!CANFD_STMSG_WARNING(st),
		!!CANFD_STMSG_BUSOFF(st));
#endif

	if (CANFD_STMSG_BUSOFF(st)) {
		pcan_handle_busoff(dev, &rx);
	} else if (!pcan_handle_error_status(dev, &rx,
					     CANFD_STMSG_WARNING(st),
					     CANFD_STMSG_PASSIVE(st))) {
		/* no error bit (so, no error, back to active state) */
		pcan_handle_error_active(dev, &rx);
	}

	if (rx.msg.type == PCANFD_TYPE_NOP) {
#ifdef DEBUG
		pr_info(DEVICE_NAME
			": %s(pcan%u): status msg discarded (NOP)\n",
			__func__, dev->nMinor);
#endif
		return 0;
	}

	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

	return pcan_xxxdev_rx(dev, &rx);
}

int canfd_post_busload(struct pcandev *dev, struct canfd_bus_load_msg *bl,
		       struct pcan_timespec *ptv)
{
#ifdef DEBUG_BUS_LOAD
	pr_info(DEVICE_NAME "%u: bus_state=%u ts32=0x%08x bus_load=%u\n",
		dev->nMinor, dev->bus_state,
		le32_to_cpu(bl->ts_low), le16_to_cpu(bl->bus_load));
#endif

	return pcan_handle_bus_load(dev,
			(10000UL * le16_to_cpu(bl->bus_load)) >> 12);
}

int canfd_post_overflow(struct pcandev *dev, struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = {
		.msg = {
			.type = PCANFD_TYPE_STATUS,
			.flags = PCANFD_ERROR_CTRLR,
			.id = PCANFD_RX_OVERFLOW,
		}
	};

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif

	/* do some filter to avoid overflowing rx queue with the same STATUS
	 * messages
	 */
	if (!pcan_handle_error_ctrl(dev, &rx, PCANFD_RX_OVERFLOW))
		return 0;

	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

	return pcan_xxxdev_rx(dev, &rx);
}

/*
 * int canfd_handle_rxmsg(struct ucan_engine *ucan, void *msg_addr)
 *
 * Handler of a uCAN-CANFD structured message.
 */
int canfd_handle_rxmsg(struct ucan_engine *ucan, void *msg_addr)
{
	struct canfd_msg *msg = (struct canfd_msg *)msg_addr;
	void *arg = NULL;
	int msg_size;
	u16 msg_type;
	int ci = -1, err;
	int (*msg_cb)(struct ucan_engine *, void *, void *);
	struct pcandev *dev = container_of(ucan, struct pcandev, ucan);

	msg_size = le16_to_cpu(msg->size);
	if (!msg->size || !msg->type) {
		/* null packet found: end of list */
		msg_size = 0;
		goto lbl_return;
	}

	msg_type = le16_to_cpu(msg->type);

#ifdef DEBUG_RX
	switch (msg_type) {
#ifdef USB_SUPPORT
	case CANFD_USB_MSG_CALIBRATION:
#endif
#ifndef DEBUG_BUS_LOAD
	case CANFD_MSG_BUSLOAD:
#endif
	case CANFD_MSG_ERROR:
		break;
	default:
		dump_mem("received rec", msg, msg_size);
	}
#endif

	/* theses msgs carry a channel index */
	switch (msg_type) {

	case CANFD_MSG_CAN_RX:
		ci = CANFD_MSG_CHANNEL((struct canfd_rx_msg *)msg);
		break;

	case CANFD_MSG_ERROR:
		ci = CANFD_ERMSG_CHANNEL((struct canfd_error_msg *)msg);
		break;

	case CANFD_MSG_STATUS:
		ci = CANFD_STMSG_CHANNEL((struct canfd_status_msg *)msg);
		break;

	case CANFD_MSG_BUSLOAD:
		ci = CANFD_BLMSG_CHANNEL((struct canfd_bus_load_msg *)msg);
		break;

	case CANFD_MSG_CACHE_CRITICAL:
		ci = CANFD_CCMSG_CHANNEL((struct canfd_cache_critical_msg *)msg);
		if (ci < ucan->devs_count) {
			struct pcanxl_rxmsg s;

			dev = ucan_dev(ucan, ci);

			if (!(dev->flags & PCAN_DEV_CTRLR_FATAL)) {
				dev->flags |= PCAN_DEV_CTRLR_FATAL;

				pr_warn(DEVICE_NAME "%u: rx cache has reached"
					"a critical size\n", dev->nMinor);
			}

			pcan_handle_error_ctrl(dev, &s, PCANFD_RX_OVERFLOW);

#ifdef NETDEV_SUPPORT
			pcan_netdev_rx(dev, &s);
#else
			if (pcan_chardev_rx(dev, &s) > 0)
				pcan_event_signal(&dev->in_event);
#endif
			return 0;
		}
		break;

#ifdef USB_SUPPORT
	case CANFD_CMD_END_OF_COLLECTION:
	case 0xffff:
		/* such msg_type should not occur, but we never know... */
		return 0;

	case CANFD_USB_MSG_CALIBRATION:
		arg = pcan_usb_get_if(ucan_dev(ucan, 0));
		if (!arg) {

			/* protect from interrupt that might occur before
			 * initialization completion: in that rare case, this
			 * message can be silently ignored.
			 */
			goto lbl_return;
		}
		break;

	case CANFD_USB_MSG_OVERRUN:
		ci = CANFD_USB_OVMSG_CHANNEL((struct ucan_usb_ovr_msg *)msg);
		break;
#endif
	}

	if (msg_type < ucan->ops.handle_msg_size) {
		if (!ucan->ops.handle_msg_table[msg_type]) {
#ifdef DEBUG_UNKNOWN_REC
			pr_warn(DEVICE_NAME
				": %s: unhandled rx CANFD rec %03xh: "
				"it is ignored\n",
				dev->adapter->name, msg_type);
			dump_mem("unhandled rec", msg, msg_size);
#endif
			/* stop everything */
			msg_size = -EBADMSG;

			goto lbl_return;
		}

		msg_cb = ucan->ops.handle_msg_table[msg_type];

#ifdef PCAN_USB_DEPRECATED
	} else if (ucan->ops.handle_private_msg) {
		msg_cb = ucan->ops.handle_private_msg;
#endif
	} else {
		pr_err(DEVICE_NAME
		       ": %s: out of range rx uCAN rec %03xh >= %u: "
		       "it is ignored\n", dev->adapter->name, msg_type,
		       ucan->ops.handle_msg_size);

		dump_mem("out of range rec", msg, msg_size);

		/* stop everything */
		msg_size = -EBADMSG;

		goto lbl_return;
	}

	if (ci != -1) {

		/* be sure of the index read... */
		if ((ci < 0) || (ci >= ucan->devs_count)) {
			pr_warn(DEVICE_NAME
				": %s: invalid channel %d in uCAN "
				"rec %03xh: it is ignored\n",
				dev->adapter->name, ci, msg_type);

			/* stop everything */
			msg_size = -EBADMSG;

			goto lbl_return;
		}

		arg = ucan_dev(ucan, ci);
	}

	err = msg_cb(ucan, msg, arg);
	if (err < 0)
		return err;

lbl_return:
	return msg_size;
}

/*
 * int canfd_encode_txmsg_flags(struct pcanxl_txmsg *tx, u16 *msg_flags,
 * 				u8 *client)
 */
int canfd_encode_txmsg_flags(struct pcanxl_txmsg *tx, u16 *msg_flags,
			     u8 *client)
{
	u16 tx_flags = (tx->msg.flags & PCANFD_MSG_EXT) ? CANFD_MSG_EXT_ID : 0;

	/* echo: application self-received frame: it's like
	 * PCANFD_MSG_SLF but with an application specific flag and
	 * an 8 bit application specific value.
	 */
	if (tx->msg.flags & PCANFD_MSG_ECHO) {
		tx_flags |= CANFD_MSG_HW_SRR|CANFD_MSG_API_SRR;
		if (client)
			*client = tx->msg.ctrlr_data[PCANFD_ECHOID];

	/* self:
	 * frame written on the bus and copied in rx path too.
	 */
	} else if (tx->msg.flags & PCANFD_MSG_SLF) {
		tx_flags |= CANFD_MSG_HW_SRR;
	}

	/* Single-Shot */
	if (tx->msg.flags & PCANFD_MSG_SNG)
		tx_flags |= CANFD_MSG_SINGLE_SHOT;

	switch (tx->msg.type) {

	case PCANFD_TYPE_CANFD_MSG:
		/* CAN-FD frames */
		tx_flags |= CANFD_MSG_EXT_DATA_LEN;

		if (tx->msg.flags & PCANFD_MSG_BRS)
			tx_flags |= CANFD_MSG_BITRATE_SWITCH;

		if (tx->msg.flags & PCANFD_MSG_ESI)
			tx_flags |= CANFD_MSG_ERROR_STATE_IND;

		break;

	case PCANFD_TYPE_CAN20_MSG:
		/* CAN 2.0 frames */
		if (tx->msg.flags & PCANFD_MSG_RTR)
			tx_flags |= CANFD_MSG_RTR;
		break;
	}

	if (msg_flags)
		*msg_flags = tx_flags;

	return 0;
}

/*
 * int canfd_encode_txmsg(struct pcandev *dev, u8 *buffer_addr,
 * 			   int buffer_size)
 *
 * @return:
 *
 * 	> 0		size in bytes of the copied msg
 *	-ENODATA	if Tx fifo is empty
 *	-ENOSPC		if output buffer is not large enough
 */
int canfd_encode_txmsg(struct pcandev *dev, u8 *buffer_addr, int buffer_size)
{
	struct canfd_tx_msg *tx_msg = (struct canfd_tx_msg *)buffer_addr;

	/* Note: no need to allocate space for data in stack here: data are
	 * directly copied into the outgoing buffer (see pcan_txfifo_out())
	 */
	struct pcanxl_txmsg tx;
	int tx_msg_size, err, dlc;
	u16 tx_flags;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u)\n", __func__, dev->nMinor);
#endif

	/* Check how many bytes are to be read from Tx FIFO.
	 * WARNING: DON'T pull anything from the fifo in case there is not
	 * enough room in the output buffer sent to the device, but just peek
	 * the header to get the entire size of the frame.
	 */
	err = pcan_txfifo_hdr_peek(dev, &tx);
	if (!err) {
#ifdef DEBUG_TX_PATH
		pr_info(DEVICE_NAME ": %s(pcan%u): "
			"No more header to read from Tx fifo\n",
			__func__, dev->nMinor);
#endif
		return -ENODATA;
	}

	dlc = pcan_len2dlc(tx.msg.data_len);
	tx_msg_size = ALIGN(sizeof(*tx_msg) + pcan_dlc2len(dlc), 4);

	/* if not enough room to entirely copy it, stop here */
	if (tx_msg_size > buffer_size) {
#ifdef DEBUG_TX_PATH
		pcanxl_debug_msg(dev, 'D', (struct pcanxl_msg *)&tx.msg,
				 NULL, -ENOSPC);
		pr_info(DEVICE_NAME ": %s(pcan%u): "
			"%u bytes left too small for storing %u bytes\n",
			__func__, dev->nMinor, buffer_size, tx_msg_size);
#endif
		return -ENOSPC;
	}

	/* get the enqueued entire message header and copy its data into the
	 * buffer of the encoded message
	 */
	err = pcan_txfifo_out(dev, &tx, tx_msg->d);
	if (err < 0)
		return err;

	dev->total_stats.tx.bytes += tx.msg.data_len;
	dev->session_stats.tx.bytes += tx.msg.data_len;

#ifdef CANFD_MSG_CAN_TX_PAUSE
	if (dev->tx_iframe_delay_us)
		err += ALIGN(sizeof(struct canfd_tx_pause), 4);
#endif

	tx_msg->type = cpu_to_le16(CANFD_MSG_CAN_TX);
	tx_msg->size = cpu_to_le16(tx_msg_size);

	canfd_encode_txmsg_flags(&tx, &tx_flags, &tx_msg->client);

	tx_msg->can_id = (tx_flags & CANFD_MSG_EXT_ID) ?
				cpu_to_le32(tx.msg.id & CAN_EFF_MASK) :
				cpu_to_le32(tx.msg.id & CAN_SFF_MASK);

	switch (tx.msg.type) {

	case PCANFD_TYPE_CAN20_MSG:

		if (dlc == PCANFD_CAN20_MAXDATALEN) {
			u8 tmp_dlc = pcanxl_msg_flags_dlc_get(tx.msg.flags);
			if (tmp_dlc > dlc)
				dlc = tmp_dlc;
		}
		break;
	}

	tx_msg->channel_dlc = CANFD_MSG_CHANNEL_DLC(dev->can_idx, dlc);
	tx_msg->flags = cpu_to_le16(tx_flags);

#ifdef CANFD_MSG_CAN_TX_PAUSE
	if (dev->tx_iframe_delay_us) {
		struct canfd_tx_pause *p;

		if (dev->tx_iframe_delay_us > CANFD_TXPAUSE_DELAY_MAX)
			dev->tx_iframe_delay_us = CANFD_TXPAUSE_DELAY_MAX;

		p = (struct canfd_tx_pause *)(buffer_addr + tx_msg_size);
		p->type = cpu_to_le16(CANFD_MSG_CAN_TX_PAUSE);
		p->size = cpu_to_le16(sizeof(*p));
		p->delay = cpu_to_le16(dev->tx_iframe_delay_us);
		p->reserved = 0;
	}
#endif /* CANFD_MSG_CAN_TX_PAUSE */

#ifdef DEBUG_TX_PATH
	pcanxl_debug_msg(dev, '<', (struct pcanxl_msg *)&tx.msg,
			 tx_msg->d, tx_msg_size);
#endif
	return tx_msg_size;
}

/* uCAN IP core general messages handlers */

/* int ucan_handle_msgs_buffer(struct ucan_engine *ucan, void *buffer_addr,
 *			       int buffer_len)
 */
int ucan_handle_msgs_buffer(struct ucan_engine *ucan, void *buffer_addr,
			    int buffer_len)
{
	//const int msg_size_max = ALIGN(sizeof(struct canfd_rx_msg) + 64, 4);
	struct canfd_msg *rx_msg;
	int msg_len = 0;
	u8 *msg_ptr = buffer_addr;
	int msg_nb = 0, msg_size;

	/* process any pending fragmented msg first */
	if (ucan->frag_size > 0) {
		int tail_size;

		rx_msg = (struct canfd_msg *)ucan->frag_rec;
		msg_size = le16_to_cpu(rx_msg->size);

		tail_size = msg_size - ucan->frag_size;
		memcpy(ucan->frag_rec + ucan->frag_size,
		       msg_ptr, tail_size);

		//msg_size = canfd_handle_rxmsg(ucan, ucan->frag_rec);
		/* TODO: think about processing fragmented DATA (if any...) */
		msg_size = ucan->ops.rx_msg_handler(ucan, ucan->frag_rec);
		if (msg_size <= 0)
			return msg_size;

		msg_ptr += tail_size;
		msg_nb++;

		msg_len += tail_size;
		ucan->frag_size = 0;
	}

	/* loop reading all the records from the incoming message */
	for (; msg_len < buffer_len; msg_len += msg_size) {
		rx_msg = (struct canfd_msg *)msg_ptr;
		msg_size = le16_to_cpu(rx_msg->size);

		/* a null packet can be found at the end of a list */
		if (!msg_size)
			break;

		/* handle fragmentation */
		if ((msg_len + msg_size) > buffer_len) {

			/* fragmented msg */
			ucan->frag_size = buffer_len - msg_len;
			memcpy(ucan->frag_rec, msg_ptr, ucan->frag_size);

#ifdef DEBUG
			pr_warn(DEVICE_NAME
				": msg #%u fragmented: %u/%u bytes pending "
				"(buffer_len=%d msg_len=%d)\n",
				msg_nb+1, ucan->frag_size, msg_size,
				buffer_len, msg_len);
#endif
			break;
		}

		//msg_size = canfd_handle_rxmsg(ucan, msg_ptr);
		msg_size = ucan->ops.rx_msg_handler(ucan, msg_ptr);
		if (msg_size <= 0)
			break;

		msg_ptr += msg_size;
		msg_nb++;
	}

#ifdef DEBUG
	pr_info(DEVICE_NAME ": %s(): found %u msg(s) in %u bytes buffer\n",
		__func__, msg_nb, buffer_len);
#endif

	/* in case of error, dump the whole messages (list) */
	if (msg_size < 0) {

#ifdef DEBUG_UNKNOWN_REC
		if (msg_size != -ENOSPC) {
			pr_err(DEVICE_NAME
				": msg[addr=%p ptr=%p len=%d]\n",
				buffer_addr, msg_ptr, msg_len);
			dump_mem("received err msg", buffer_addr, msg_len);
		}
#endif
		return msg_size;
	}

	return 0;
}

/*
 * int ucan_handle_msgs_list(struct ucan_engine *ucan, void *msg_addr,
 *				int *msg_count)
 */
int ucan_handle_msgs_list(struct ucan_engine *ucan, void *msg_addr,
			  int *msg_count)
{
	u8 *msg_ptr = msg_addr;
	int msg_len = 0;
	int msg_size = 0;
	int i;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(msg_count=%d)\n", __func__, *msg_count);
#endif

	/* loop reading all the records from the incoming message */
	for (i = 0; i < *msg_count; i++) {
		//msg_size = canfd_handle_rxmsg(ucan, msg_ptr);
		msg_size = ucan->ops.rx_msg_handler(ucan, msg_ptr);

		/* a null packet can be found at the end of a list */
		if (msg_size <= 0)
			break;

		/* next record is 32-Bit aligned */
		msg_size = ALIGN(msg_size, 4);

		msg_len += msg_size;
		msg_ptr += msg_size;
	}

	*msg_count = i;

	/* in case of error, dump the failed message,
	 * except in case of not enough space in Rx FIFO...
	 */
	if (msg_size < 0) {
#ifdef DEBUG_UNKNOWN_REC
		if (msg_size != -ENOSPC)
			dump_mem("received err msg",
				 msg_ptr, sizeof(struct canfd_rx_msg));
#endif
		return msg_size;
	}

	return 0;
}

/*
 * int ucan_encode_msgs_buffer(struct pcandev *dev,
 *				u8 *buffer_addr, int *buffer_size)
 *
 * Read msgs from CAN Tx fifo and encode them into the given buffer.
 *
 *	-ENODATA	if no more data in CAN fifo,
 *	-ENOSPC		if *buffer_size is not large enough to store a TX_x
 *			record
 *			any other -ERR.
 *	>= 0		if output buffer is full of TX_x records,
 */
int ucan_encode_msgs_buffer(struct pcandev *dev, u8 *buffer_addr,
			    int *buffer_size)
{
	int msg_len, rec_count;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(buffer_size=%d)\n", __func__, *buffer_size);
#endif

	for (msg_len = rec_count = 0; msg_len < *buffer_size; ) {
		err = dev->ucan.ops.tx_msg_encoder(dev, buffer_addr + msg_len,
						   *buffer_size - msg_len);
		if (err < 0) {
#ifdef DEBUG_TX_PATH
			pr_info(DEVICE_NAME ": %s(): err %d while encoding msg "
				"*buffer_size=%d msg_len=%d rec_count=%d\n",
				__func__, err,
				*buffer_size, msg_len, rec_count);
#endif
			break;
		}

		/* to be sure to not count other msgs than CAN frames */
		if (!err)
			continue;

		msg_len += ALIGN(err, 4);
		rec_count++;

#ifdef CANFD_WRITE_ONE_FRAME_PER_PACKET
		err = -ENODATA;
		break;
#endif
	}

	if (rec_count) {

		dev->total_stats.tx.frames += rec_count;
		dev->session_stats.tx.frames += rec_count;

		/* if the entire packet is not filled, set the size of last
		 * msg to 0 to mark end-of-rec (only if one record has been
		 * stored into the buffer)
		 */
		if (msg_len < *buffer_size) {
			*(u32 *)(buffer_addr + msg_len) = 0;
			msg_len += sizeof(u32);
		}
	}

	/* set the whole size of the message to send */
	*buffer_size = msg_len;

#ifdef DEBUG_TX_PATH
	dump_mem("encoded buffer", buffer_addr, *buffer_size);
#endif

	return !err ? rec_count : err;
	//return -ENODATA;
}

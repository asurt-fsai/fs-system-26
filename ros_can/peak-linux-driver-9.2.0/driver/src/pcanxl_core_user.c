/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcanxl_ucan.c - the uCAN firmware global interface
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
 *               (endianess issue with __le16 flags in struct canxl_tx_msg)
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

#include "src/pcanxl_core.h"		/* pcan with CANXL support core API */
#include "src/pcanxl_core_user.h"	/* CANXL base common messages */

#ifdef USB_SUPPORT
#include "src/pcanxl_usb_fw.h"		/* uCAN USB devices specific messages */
#endif

#ifdef DEBUG
#define DEBUG_BUS_MODE
//#define DEBUG_BUS_LOAD	/* May be *VERY* verbose (see 'bl_period')  */
#define DEBUG_RX_PATH
#define DEBUG_TX_PATH
#define DEBUG_TRACE
#define DEBUG_INIT
#else
//#define DEBUG_BUS_MODE
//#define DEBUG_BUS_LOAD
//#define DEBUG_RX_PATH
//#define DEBUG_TX_PATH
//#define DEBUG_TRACE
//#define DEBUG_INIT
#endif

/* if defined, set the number of times an outgoing CAN message is repeated
 * in the outgoing stream. This enables to do some internal tests only!
 * This MUST not be defined in a production version!
 */
//#define CANXL_TEST_TX_BURST		5

/* If defined, do single-frame uCAN ouput records.
 * If not defined, the buffer is filled with pending frames.
 */
//#define CANFD_WRITE_ONE_FRAME_PER_PACKET

typedef struct __array_of_struct(pcanfd_available_clock, 7)
	pcanxl_7_clocks_device;

static const pcanxl_7_clocks_device canxl_clocks = {
	.count = 7,
	.list = {
		[0] = { .clock_Hz = 160*MHz, .clock_src = 80*MHz, },
		[1] = { .clock_Hz = 80*MHz, .clock_src = 80*MHz, },
		[2] = { .clock_Hz = 20*MHz, .clock_src = 240*MHz, },
		[3] = { .clock_Hz = 24*MHz, .clock_src = 240*MHz, },
		[4] = { .clock_Hz = 30*MHz, .clock_src = 240*MHz, },
		[5] = { .clock_Hz = 40*MHz, .clock_src = 240*MHz, },
		[6] = { .clock_Hz = 60*MHz, .clock_src = 240*MHz, },
	}
};

/* Hardware timing capabilities */
static const struct pcanfd_bittiming_range canxl_nominal_capabilities = {

	.brp_min = 1,
	.brp_max = (1 << CANXL_NOMINAL_BRP_BITS),
	.brp_inc = 1,

	.tseg1_min = 1,
	.tseg1_max = (1 << CANXL_NOMINAL_TSEG1_BITS),
	.tseg2_min = 1,
	.tseg2_max = (1 << CANXL_NOMINAL_TSEG2_BITS),
	.sjw_min = 1,
	.sjw_max = (1 << CANXL_NOMINAL_SJW_BITS)
};

static const struct pcanfd_bittiming_range canxl_fd_data_capabilities = {

	.brp_min = 1,
	.brp_max = (1 << CANXL_FDDATA_BRP_BITS),
	.brp_inc = 1,
	.tseg1_min = 1,
	.tseg1_max = (1 << CANXL_FDDATA_TSEG1_BITS),
	.tseg2_min = 1,
	.tseg2_max = (1 << CANXL_FDDATA_TSEG2_BITS),
	.sjw_min = 1,
	.sjw_max = (1 << CANXL_FDDATA_SJW_BITS)
};

static const struct pcanfd_bittiming_range canxl_xl_data_capabilities = {

	.brp_min = 1,
	.brp_max = (1 << CANXL_XLDATA_BRP_BITS),
	.brp_inc = 1,
	.tseg1_min = 1,
	.tseg1_max = (1 << CANXL_XLDATA_TSEG1_BITS),
	.tseg2_min = 1,
	.tseg2_max = (1 << CANXL_XLDATA_TSEG2_BITS),
	.sjw_min = 1,
	.sjw_max = (1 << CANXL_XLDATA_SJW_BITS)
};

static const struct pcanxl_pwm_range canxl_xl_pwm_capabilities = {
	.pwml_min = 2,
	.pwml_max = (1 << CANXL_PWML_BITS) - 1,
	.pwms_min = 1,
	.pwms_max = (1 << CANXL_PWMS_BITS) - 1,
	.pwmo_min = 0,
	.pwmo_max = (1 << CANXL_PWMO_BITS) - 1,
};

/* CANXL commands interface functions */

static inline void *canxl_init_cmd(struct pcandev *dev)
{
	return canfd_init_cmd(dev);
}

static inline void *canxl_add_cmd(struct pcandev *dev, int cmd_op)
{
	return canfd_add_cmd(dev, cmd_op);
}

#define CANXL_EWL_DEF			96
#define CANXL_XL_FRAME_FMT_DEF		1
#define CANXL_PHY_MODE_SWITCH_DEF	0
#define CANXL_ERR_SIGNALING_DEF		1	/* no XL mode */

static void *canxl_add_cmd_init(struct pcandev *dev, struct pcanxl_init *pxli)
{
	int op_mode = (pxli->flags & PCANFD_INIT_LISTEN_ONLY) ?
			CANFD_CMD_LISTEN_ONLY_MODE : CANFD_CMD_NORMAL_MODE;

	struct canxl_init_mode *cmd = canxl_add_cmd(dev, op_mode);
	if (cmd) {
		u32 mc_flags = 0;

		cmd->ewl = CANXL_EWL_DEF;

		if (pxli->flags & PCANXL_INIT_XL)
			mc_flags |= CANXL_INIT_XL_FFE;

		if (pxli->flags & PCANXL_INIT_TMS_ON)
			mc_flags |= CANXL_INIT_TRX_MODE_SWITCH_ON;

		else if (!(pxli->flags & PCANXL_INIT_ES_OFF))
			mc_flags |= CANXL_INIT_ERR_SIGNALING_ON;

		/* if XL frame not selected, then error signaling is ON (like
		 * CAN_CC CAN_FD)
		 *
		 * error signaling = OFF => pure CAN-XL
		 * - Rx node: re-integrates after an Error
		 * - Tx node: does not check for Tx errors! Always
		 *   transmit the full frame
		 *
		 * error signaling = ON & xceiver mode switch = OFF =>
		 * Mixed network
		 */
		if (!(mc_flags & CANXL_INIT_XL_FFE) ||
		    (pxli->flags & PCANXL_INIT_FD))
			mc_flags |= CANXL_INIT_ERR_SIGNALING_ON;

#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: op_mode=[FFE=%u TMS=%u ES=%u]\n",
			dev->nMinor,
			!!(mc_flags & CANXL_INIT_XL_FFE),
			!!(mc_flags & CANXL_INIT_TRX_MODE_SWITCH_ON),
			!!(mc_flags & CANXL_INIT_ERR_SIGNALING_ON));
#endif
		/* else (pure CANXL) => error signaling = OFF */
		cmd->mc_flags = __cpu_to_le32(mc_flags);
	}

	return cmd;
}

/*
 * @timing = CANXL_CMD_TIMING_NOMINAL |
 *           CANXL_CMD_TIMING_FD |
 *           CANXL_CMD_TIMING_XL
 */
static void *canxl_add_cmd_timing(struct pcandev *dev, int timing,
				  struct pcan_bittiming *pbr)
{
	struct canxl_timing *cmd = canfd_add_cmd(dev, timing);
	if (cmd) {
#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: %s_bittiming: "
			"[brp=%u tseg1=%u tseg2=%u sjw=%u sp=%u ts=%u]\n",
			dev->nMinor,
			(timing == CANXL_CMD_TIMING_NOMINAL) ? "nom" :
			(timing == CANXL_CMD_TIMING_FD) ? "fd" : "xl",
			pbr->brp, pbr->tseg1, pbr->tseg2, pbr->sjw,
			pbr->sample_point, pbr->tsam);
#endif
		cmd->tseg1 = __cpu_to_le16(
			FIELD_PREP(CANXL_TSEG1_MASK, pbr->tseg1 - 1));
		cmd->sjw_tseg2_brp = __cpu_to_le32(
			FIELD_PREP(CANXL_SJW_MASK, pbr->sjw - 1) |
			FIELD_PREP(CANXL_TSEG2_MASK, pbr->tseg2 - 1));

		if (timing != CANXL_CMD_TIMING_XL)
			cmd->sjw_tseg2_brp |= __cpu_to_le32(
				FIELD_PREP(CANXL_BRP_MASK, pbr->brp - 1));
	}

	return cmd;
}

/*
 * static void *canxl_add_cmd_pwm_xl(struct pcandev *dev,
 * 				     struct pcanxl_pwm *pwm)
 *
 * TMS:
 * - Arbitration (aka slow) phase: NRZ
 * - Data (aka fast) phase: PWM
 *   - switch on ADH sequence detection,
 *   - go back to NRZ on DAS sequence
 *
 * PWM symbol is expressed in tq (=mtq for CANXL).
 * tq = 1 / clock_Hz (= 6.25 ns for a 160 MHz clock)
 * pwm_short + pwm_long <= 200 ns =>
 * pwm_short + pwm_long <= 32 mtq (for a 160 MHz clock)
 * Optimum values for
 * pwm_long = 75%
 * pwm_short = 25%
 * pwm_offset is necessary only in certain cases in the ADH sequence
 * detection, when fast rate is not a multiple of the slow rate, we need such
 * an offset (expressed in mtq too).
 *
 * PWM period time = [205 ns.. 245 ns] ; PWM < 200ns => switch to fast Mode
 *
 * Note: PWM period time should be >= 200 ns, it looks impossible to run the
 * "push pull" behavior with data rates < 5 Mbps:
 *
 * 		bit time
 * 5 Mbps	200 ns
 * 10 Mbps	100 ns
 * 2 Mbps	500 ns	-> PWM period time not ok, no transceiver switching!
 *
 * However, this issue can be solved through configuration of "multiple PWM
 * periods / bit"
 */
static void *canxl_add_cmd_pwm_xl(struct pcandev *dev, struct pcanxl_pwm *pwm)
{
	struct canxl_pwm_config *cmd = canfd_add_cmd(dev, CANXL_CMD_PWM_CFG_XL);
	if (cmd) {
#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: pwm: [offset=%u long=%u short=%u]\n",
			dev->nMinor,
			pwm->pwm_offset, pwm->pwm_long, pwm->pwm_short);
#endif
		/* TODO long+short <= period = f(clock) */
		cmd->pwml = cpu_to_le16(CANXL_PWM_LONG(pwm->pwm_long));
		cmd->pwms = cpu_to_le16(CANXL_PWM_SHORT(pwm->pwm_short));
		cmd->pwmo = cpu_to_le16(CANXL_PWM_OFFSET(pwm->pwm_offset));
	}

	return cmd;
}

/*
 * static void *canxl_add_cmd_busload2_period(struct pcandev *dev,
 *					      u32 period_us)
 */
static void *canxl_add_cmd_busload2_period(struct pcandev *dev, u32 period_us)
{
	struct canxl_busload2_period *cmd =
		canfd_add_cmd(dev, CANXL_CMD_BUSLOAD2_PERIOD);

	if (cmd) {
#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: bus_load period=%u us\n", dev->nMinor,
			period_us);
#endif
		cmd->period_us = cpu_to_le32(period_us);
	}

	return cmd;
}

/*
 * static void *canxl_add_cmd_opts(struct pcandev *dev, u16 cmd, u32 ssp_offset)
 */
static void *canxl_add_cmd_opts(struct pcandev *dev, u16 cmd_id, u32 ssp_offset)
{
	struct canxl_opts *cmd = canfd_add_cmd(dev, cmd_id);
	if (cmd) {
#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: %s_ssp_offset=%u\n", dev->nMinor,
			(cmd_id == CANXL_CMD_FD_OPTS) ? "fd" :
			(cmd_id == CANXL_CMD_XL_OPTS) ? "xl" : "??",
			ssp_offset);
#endif
		cmd->ssp_offset = cpu_to_le32(ssp_offset & 0xff);
	}

	return cmd;
}

static inline void *canxl_add_cmd_xl_opts(struct pcandev *dev, u32 ssp_offset)
{
	return canxl_add_cmd_opts(dev, CANXL_CMD_XL_OPTS, ssp_offset);
}

static inline void *canxl_add_cmd_fd_opts(struct pcandev *dev, u32 ssp_offset)
{
	return canxl_add_cmd_opts(dev, CANXL_CMD_FD_OPTS, ssp_offset);
}

/*
 * static void *canxl_add_cmd_re_xmt_limit(struct pcandev *dev, u16 cmd_id,
 * 					   u8 xmt_limit)
 */
static void *canxl_add_cmd_re_xmt_limit(struct pcandev *dev, u16 cmd_id,
					u8 xmt_limit)
{
	struct canxl_xmt_limit *cmd = canfd_add_cmd(dev, cmd_id);
	if (cmd) {
#ifdef DEBUG_INIT
		pr_info(DEVICE_NAME "%u: %s_xmt_limit=%u\n", dev->nMinor,
			(cmd_id == CANXL_CMD_RE_XMT_LIMIT_CC) ? "cc" :
			(cmd_id == CANXL_CMD_RE_XMT_LIMIT_FD) ? "fd" : "xl",
			xmt_limit);
#endif
		cmd->xmt_limit = CANXL_XMT_LIMIT(xmt_limit);
	}

	return cmd;
}

static inline void *canxl_add_cmd_re_xmt_limit_xl(struct pcandev *dev,
						  u8 xmt_limit)
{
	return canxl_add_cmd_re_xmt_limit(dev, CANXL_CMD_RE_XMT_LIMIT_XL,
					  xmt_limit);
}

/*
 * void canxl_dump_rx_msg(const char *prompt, void *rx_msg)
 */
void canxl_dump_rx_msg(const char *prompt, void *rx_msg)
{
	struct canxl_rx_hdr *rx_hdr = (struct canxl_rx_hdr *)rx_msg;
	dump_mem(prompt, rx_hdr, le16_to_cpu(rx_hdr->size));
}

/* int canxl_set_bus_on(struct pcandev *dev)
 *
 * Set CANXL device bus controller to ON.
 */
int canxl_set_bus_on(struct pcandev *dev)
{
	int err;
	void *cmd = canxl_add_cmd_init(canxl_init_cmd(dev),
				       &dev->init_settings);

#if defined(DEBUG_TRACE) || defined(DEBUG_BUS_MODE) || defined(DEBUG_INIT)
	pr_info(DEVICE_NAME ": %s(pcan%d): %s\n", __func__, dev->nMinor,
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

/* int canxl_set_bus_off(struct pcandev *dev)
 *
 * Set CANXL device bus controller to OFF.
 */
int canxl_set_bus_off(struct pcandev *dev)
{
	int err;

#if defined(DEBUG_TRACE) || defined(DEBUG_BUS_MODE)
	pr_info(DEVICE_NAME ": %s(pcan%d): bus=%d\n",
		__func__, dev->nMinor, dev->bus_state);
#endif

	/* Prepare the command to go off the bus */
	if (!canfd_add_cmd_reset_mode(canfd_init_cmd(dev)))
		return -EINVAL;

	/* wait a bit for last data to be written on CAN bus (only if bus is
	 * in a correct state).
	 *
	 * CANXL core cache size is 4KB;
	 * USB write buffer is 5*512 Bytes long =>
	 * ~2x buffers might be waiting to be written on wire.
	 * if frames have been written during that session, then consider
	 * time to flush these buffers.
	 */
	pcanxl_tx_delay(dev);

	/* send the command */
	err = canfd_flush_cmd(dev);
	if (!err)
		dev->flags &= ~(PCAN_DEV_BUS_ON|PCAN_DEV_CTRLR_FATAL);

	return err;
}

static int canxl_dev_reset(struct pcandev *dev)
{
	int err;

#ifdef DEBUG_BUS_MODE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	err = canxl_set_bus_off(dev);
	if (err)
		return err;

	err = canfd_clr_err_counters(dev);
	if (err)
		return err;

	return canxl_set_bus_on(dev);
}

/*
 * int canxl_soft_init(struct pcandev *dev, struct pcan_version *hw_ver)
 */
int canxl_soft_init(struct pcandev *dev, struct pcan_version *hw_ver)
{
	u32 dev_features = PCAN_DEV_XL_RDY | PCAN_DEV_FD_RDY |
			   PCAN_DEV_ECHO_RDY | PCAN_DEV_TS_SOF_RDY |
			   PCAN_DEV_SELF_ACK_RDY | PCAN_DEV_BRS_IGN_RDY |
			   PCAN_DEV_SJA1000_RDY;
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif
	/* Bus load  option is available for FW >= 1.2.0 */
	if (VER_NUM(hw_ver->major,
		    hw_ver->minor,
		    hw_ver->subminor) >= VER_NUM(1, 2, 0))
		dev_features |= PCAN_DEV_BUSLOAD_RDY;

	/* TODO: Is Tx Pause option available too? */
	//dev_features |= PCAN_DEV_TXPAUSE_RDY;

	pcan_soft_init_ex(dev,
			  (const struct pcanfd_available_clocks *)&canxl_clocks,
			  &canxl_nominal_capabilities,
			  dev_features);

	dev->fd_bittiming_caps = &canxl_fd_data_capabilities;
	dev->xl_bittiming_caps = &canxl_xl_data_capabilities;
	dev->xl_pwm_caps = &canxl_xl_pwm_capabilities;

	/* if global dbitrate is not 0, then consider to open in CAN-FD */
	if (dev->def_init_settings.fd_data.bitrate) {
		dev->def_init_settings.flags |= PCANXL_INIT_FD;

		pcan_bittiming_normalize(&dev->def_init_settings.fd_data,
					 dev->sysclock_Hz,
					 dev->fd_bittiming_caps);

		/* reset default init settings with new fd data bitrate specs */
		pcanxl_copy_init(&dev->init_settings, &dev->def_init_settings);
	}

	/* if global xbitrate is not 0, then consider to open in CAN-XL */
	if (dev->def_init_settings.xl_data.bitrate) {
		dev->def_init_settings.flags |= PCANXL_INIT_XL;

		pcan_bittiming_normalize(&dev->def_init_settings.xl_data,
					 dev->sysclock_Hz,
					 dev->xl_bittiming_caps);

		/* reset default init settings with new xl data bitrate specs */
		pcanxl_copy_init(&dev->init_settings, &dev->def_init_settings);
	}

	/* put XL device reset callback because canxl_bus_on() SHOULD be used */
	dev->device_reset = canxl_dev_reset;

	return 0;
}

/*
 * int canxl_device_open_xl(struct pcandev *dev, struct pcanxl_init *pxli,
 *			    u16 ext_to_set, u16 ext_to_clr)
 *
 * Interoperability with CAN FD for mixed FD/XL networks.
 *
 * CAN XL will be operable with all 4 transceivers (HS, FD, SIC, SIC-XL):
 *
 * o Classical CAN up to 1Mbit/s
 *
 * o CAN FD up to 2Mbit/s and CAN XL-SIC up to 5-8Mbps (err_sign=1 mode_sw=0)
 *   CAN FD frame defines the "res" bit for future protocol extensions:
 *   - res=0	CAN FD node expects CAN FD frame
 *   - res=1	CAN FD node enters bus integration state
 *  		CAN FD finishes bus integration when the CAN XL frame ends
 *
 *   - 2048 bytes payload possible; HS, FD & SIC transceivers ok.
 *   - two data bitrates on the same bus
 *   - mixed network: SIC (5-8Mbps) + FD transceivers (2Mbps)
 *   - mixed network: SIC XL transceivers only: 20 Mbps between XL nodes +
 *                    5-8Mbps with CAN FD nodes
*
 * o CAN XL up to 20 Mbit/s (err_sgn=0 mode_sw=1) : pure CAN XL network; only
 *   SIC-XL transceivers. CAN XL ISNOT compatible with CANFD!
 */

/* Note: CAN FD FW sends BUSLOAD indication every 500 µs! */
#define CANXL_CMD_BUSLOAD2_PERIOD_DEF	1000

int canxl_device_open_xl(struct pcandev *dev, struct pcanxl_init *pxli,
			 u16 ext_to_set, u16 ext_to_clr)
{
	/* ISO mode is mandatory with XL FW */
	u16 opt_to_clr = 0, opt_to_set = CANFD_OPTION_ERROR |
					 CANFD_OPTION_ISO_MODE;
	/* set bus load interval
	 * Note: bus load interval shoumd be > 2 x longest frame delay
	 * _CC: 159 / nom_btr
	 * _FD: 90 / nom_btr + 520 / fd_btr
	 * _XL: 16528 / xl_btr
	 */
	u32 bl_period = CANXL_CMD_BUSLOAD2_PERIOD_DEF, bl_period_min;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif
	/* same clocks as CANFD core */
	err = canfd_set_clock_domain(dev, pxli);
	if (err)
		return err;

	/* Start populating the output buffer with reset error counters */
	if (!canfd_add_cmd_wr_err_cnt(canfd_init_cmd(dev),
				      CANFD_WRERRCNT_TE|CANFD_WRERRCNT_RE,
				      0, 0))
		goto fail;

	dev->tx_error_counter = 0;
	dev->rx_error_counter = 0;

	if (pxli->flags & PCANFD_INIT_BUS_LOAD_INFO) {
		opt_to_set |= CANFD_OPTION_BUSLOAD;
	} else {
		opt_to_clr |= CANFD_OPTION_BUSLOAD;
	}

	/* clear/set options */
	if (pxli->flags & (PCANXL_INIT_FD|PCANXL_INIT_XL)) {

		opt_to_clr |= CANFD_OPTION_20AB_MODE;

		if (!(pxli->flags & PCANXL_INIT_XL)) {
			bl_period_min =
				(90 * USEC_PER_SEC) / pxli->nominal.bitrate +
				(520 * USEC_PER_SEC) / pxli->fd_data.bitrate;
		} else {
			/* the arbitration phase is neglected */
			u64 largest_frm_time = 16528ULL * USEC_PER_SEC;

			do_div(largest_frm_time, pxli->xl_data.bitrate);
			bl_period_min = largest_frm_time;
		}

		/* CAN FD only option */
		if (!(pxli->flags & PCANXL_INIT_XL)) {
			if (pxli->flags & PCANFD_INIT_FD_NON_ISO)
				opt_to_clr |= CANFD_OPTION_ISO_MODE;
			else
				opt_to_set |= CANFD_OPTION_ISO_MODE;
		}

	} else {
		bl_period_min = (159 * USEC_PER_SEC) / pxli->nominal.bitrate;

		/* force CAN 2.0 A/B mode */
		opt_to_set |= CANFD_OPTION_20AB_MODE;
	}

	if (opt_to_clr || ext_to_clr) {
		if (!canfd_add_cmd_clr_dis_option(dev, opt_to_clr, ext_to_clr))
			goto fail;
	}

	if (opt_to_set || ext_to_set) {

		/* bus load interval should be > 2 x longest frame delay */
		bl_period_min <<= 1;
		if (bl_period_min < CANXL_CMD_BUSLOAD2_PERIOD_MIN)
			bl_period_min = CANXL_CMD_BUSLOAD2_PERIOD_MIN;

		if (bl_period < bl_period_min)
			bl_period = bl_period_min;

		if (opt_to_set & CANFD_OPTION_BUSLOAD) {
			if (!canxl_add_cmd_busload2_period(dev, bl_period))
				goto fail;
		}

		if (!canfd_add_cmd_set_en_option(dev, opt_to_set, ext_to_set))
			goto fail;
	}

	/* Set timings */
	if (!canxl_add_cmd_timing(dev, CANXL_CMD_TIMING_NOMINAL,
				  &pxli->nominal))
		goto fail;

	if (pxli->flags & PCANXL_INIT_FD) {

		/* PCANXL_INIT_FD => error_signaling ON */
		if (!canxl_add_cmd_timing(dev, CANXL_CMD_TIMING_FD,
					  &pxli->fd_data))
			goto fail;

		if (!canxl_add_cmd_fd_opts(dev, pxli->fd_data.ssp_offset))
			goto fail;
	}

	if (pxli->flags & PCANXL_INIT_XL) {

		/* based on nominal BRP, command is used for CAN-XL data
		 * bitrate
		 */
		if (!canxl_add_cmd_timing(dev, CANXL_CMD_TIMING_XL,
					  &pxli->xl_data))
			goto fail;

		if (!canxl_add_cmd_xl_opts(dev, pxli->xl_data.ssp_offset))
			goto fail;

		if (!canxl_add_cmd_re_xmt_limit_xl(dev,
					pxli->rxmt_limit[PCANXL_CAN_XL]))
			goto fail;

		if (pxli->flags & PCANXL_INIT_TMS_ON)
			if (!canxl_add_cmd_pwm_xl(dev, &pxli->xl_pwm))
				goto fail;
	}

	/* Send the whole buffer */
	return canfd_flush_cmd(dev);

fail:
	return -ENOSPC;
}

/*
 * int canxl_device_open_fd(struct pcandev *dev, struct pcanfd_init *pfdi,
 *			    u16 ext_to_set, u16 ext_to_clr)
 */
int canxl_device_open_fd(struct pcandev *dev, struct pcanfd_init *pfdi,
			 u16 ext_to_set, u16 ext_to_clr)
{
	/* be sure to allow access to struct pcanfd_init member only */
	pfdi->flags &= ~PCANXL_INIT_XL;
	pfdi->data.ssp_offset = CANXL_SSP_OFFSET_SAME_SP;

	return canxl_device_open_xl(dev, (struct pcanxl_init *)pfdi,
				    ext_to_set, ext_to_clr);
}

/*
 * int canxl_device_close(struct pcandev *dev)
 */
int canxl_device_close(struct pcandev *dev)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	return canfd_device_close(dev);
}

/*
 * static int canxl_handle_rxmsg_flags(struct pcanxl_rxmsg *rx, u16 msg_flags,
 *				       u8 client)
 */
static int canxl_handle_rxmsg_flags(struct pcanxl_rxmsg *rx, u16 msg_flags,
				    u8 client)
{
	/* sanitize non sense flags for CANXL */
	msg_flags &= ~(CANFD_MSG_EXT_DATA_LEN |
		       CANFD_MSG_EXT_ID |
		       CANFD_MSG_RTR);

	/* CANXL_MSG_XLF flag is redundant with the API msg type */

	return canfd_handle_rxmsg_flags(rx, msg_flags, client);
}

/* int canxl_post_rxmsg_fd(struct pcandev *dev, struct canxl_rx_msg_fd *rm,
 *			   struct pcan_timespec *ptv)
 *
 *	Handler of incoming CANCC/CANFD messages
 */
int canxl_post_rxmsg_fd(struct pcandev *dev, struct canxl_rx_msg_fd *rm,
			struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg_fd rx;
	const u16 msg_flags = le16_to_cpu(rm->flags);
	u8 dlc = FIELD_GET(CANXL_FD_DLC_MASK, rm->dlc);

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d): wCANStatus=%xh "
		"rx=[id=%xh flags=%04xh dlc=%02xh ts=%llu]\n",
		__func__, dev->nMinor, dev->wCANStatus,
		le32_to_cpu(rm->id), msg_flags, dlc,
		le64_to_cpu(rm->hdr.timestamp));
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

	rx.msg.id = le32_to_cpu(rm->id);
	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

#ifdef PCANFD_RAWTIMESTAMP
	rx.msg.flags |= PCANFD_RAWTIMESTAMP;
	rx.msg.raw_timestamp = le64_to_cpu(rm->timestamp);
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
	canfd_handle_rxmsg_flags((struct pcanxl_rxmsg *)&rx,
				 msg_flags, rm->client);

#ifdef DEBUG_RX_PATH
	return pcanxl_debug_msg(dev, '>', (struct pcanxl_msg *)&rx.msg, rm->d,
				pcan_xxxdev_rx_ex(dev, &rx, rm->d));
#else
	return pcan_xxxdev_rx_ex(dev, &rx, rm->d);
#endif
}

/*
 * int canxl_post_error_notification(struct pcandev *dev,
 * 				     struct canxl_rx_error *en,
 * 				     struct pcan_timespec *ptv)
 *
 * "whenever an error is detected and error signaling is disabled"
 *
 * Same as canxl_post_error() except that no errror frame is written on the
 * wire. Should occur "only" when the controller doesn't see any ACK to the
 * frame it wrote, when in error signaling mode = off. All other "errors" are
 * notified through protocol_exception().
 */
int canxl_post_error_notification(struct pcandev *dev,
				  struct canxl_rx_error *en,
				  struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = { .msg = { .data_len = 0, } };
	struct pcan_bus_error err = {
		.type = FIELD_GET(CANXL_ERR_TYPE_MASK, en->err_type_d),
		.code = FIELD_GET(CANXL_ERR_CODE_MASK, en->err_code),
		.rx = en->err_type_d & CANXL_ERR_D,
	};

#ifdef DEBUG_TRACE
	if (printk_ratelimit())
		pr_info(DEVICE_NAME
			"%u : %s(): rx=[type=0x%02x ts=%llu dir=%s code=%u\n",
			dev->nMinor, __func__, err.type,
			le64_to_cpu(en->hdr.timestamp),
			(err.rx) ? "Rx" : "Tx", err.code);
#endif

	rx.msg.flags = PCANXL_ERROR_SIGN_OFF;

	/* not an "error" but a status... */
	if (err.type > PCANFD_ERRMSG_OTHER) {
		rx.msg.type = PCANFD_TYPE_STATUS;
		rx.msg.id = dev->bus_state;
		rx.msg.ctrlr_data[PCANXL_ERRCODE] = err.code;
		rx.msg.ctrlr_data[PCANXL_ERRTYPE] = err.type;
		rx.msg.flags |= PCANFD_ERROR_BUS | PCANXL_ERROR_BUS_CODETYPE;
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

/*
 * int canxl_post_protocol_exception(struct pcandev *dev,
 * 				     struct canxl_rx_error *pe,
 * 				     struct pcan_timespec *ptv)
 *
 * "the protocol controller enters exception state e.g. on resXL bit (recessive)
 * or whenever an error is detected and error signaling is disabled"
 */
int canxl_post_protocol_exception(struct pcandev *dev,
				  struct canxl_rx_error *pe,
				  struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = { .msg = { .data_len = 0, } };
	struct pcan_bus_error err = {
		.type = FIELD_GET(CANXL_ERR_TYPE_MASK, pe->err_type_d),
		.code = FIELD_GET(CANXL_ERR_CODE_MASK, pe->err_code),
		.rx = pe->err_type_d & CANXL_ERR_D,
	};

#ifdef DEBUG_TRACE
	if (printk_ratelimit())
		pr_info(DEVICE_NAME
			"%u : %s(): rx=[type=0x%02x ts=%llu dir=%s code=%u "
			"err_cnt[rx=%u tx=%u]]\n",
			dev->nMinor, __func__, err.type,
			le64_to_cpu(pe->hdr.timestamp),
			(err.rx) ? "Rx" : "Tx", err.code,
			pe->rx_err, pe->tx_err);
#endif

#ifdef DEBUG
	if (dev->rx_error_counter || dev->tx_error_counter)
		pr_err(DEVICE_NAME "%u: errors: rx=%u tx=%u\n", dev->nMinor,
		       dev->rx_error_counter, dev->tx_error_counter);
#endif

	rx.msg.flags = PCANXL_ERROR_SIGN_OFF;

	/* not an "error" but a status... */
	if (err.type > PCANFD_ERRMSG_OTHER) {
		rx.msg.type = PCANFD_TYPE_STATUS;
		rx.msg.id = dev->bus_state;
		rx.msg.ctrlr_data[PCANXL_ERRCODE] = err.code;
		rx.msg.ctrlr_data[PCANXL_ERRTYPE] = err.type;
		rx.msg.flags |= PCANFD_ERROR_BUS | PCANXL_ERROR_BUS_CODETYPE;
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

/*
 * int canxl_post_overload(struct pcandev *dev,
 * 			   struct canxl_rx_overload *ov,
 * 			   struct pcan_timespec *ptv)
 *
 * "an overload frame is send e.g. during INTERMISSION field, see detailed
 *  position codes" (CANXL_POS_xxx)
 */
int canxl_post_overload(struct pcandev *dev,
			struct canxl_rx_overload *ov,
			struct pcan_timespec *ptv)
{
	u8 pos_code = FIELD_GET(CANXL_POS_CODE_MASK, ov->pos_code);
	struct pcanxl_rxmsg rx = {
		.msg = {
			.type = PCANXL_TYPE_STATUS,
			.id = PCANXL_OVERLOAD,
			.ctrlr_data = {
				[PCANXL_POS_CODE] = pos_code,
			},
		},
	};
	u8 d = FIELD_GET(CANXL_OVL_D, ov->d);

#ifdef DEBUG_TRACE
	if (printk_ratelimit())
		pr_info(DEVICE_NAME
			": %s(): rx=[pos=%u d=%02xh ts=%llu]\n",
			__func__, pos_code, d, le64_to_cpu(ov->hdr.timestamp));
#endif

	if (d)
		rx.msg.flags |= PCANFD_ERRMSG_RX;

	if (ptv) {
		rx.msg.flags |= PCANFD_TIMESTAMP;
		rx.hwtv = *ptv;
	}

	return pcan_xxxdev_rx(dev, &rx);
}

/* int canxl_post_rxmsg_xl(struct pcandev *dev, struct canxl_rx_msg_xl *rm,
 *			   struct pcan_timespec *ptv)
 *
 *	Handler of incoming CANCC/CANFD messages
 */
int canxl_post_rxmsg_xl(struct pcandev *dev, struct canxl_rx_msg_xl *rm,
			struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = {
		.msg = { .type = PCANXL_TYPE_CANXL, },
	};
	const u16 rm_flags = le16_to_cpu(rm->flags);
	const u32 rm_pid_rrs_dlc_sec_sdt = le32_to_cpu(rm->pid_rrs_dlc_sec_sdt);

	rx.msg.data_len = 1 +
		FIELD_GET(CANXL_XL_DLC_MASK, rm_pid_rrs_dlc_sec_sdt);

#if defined(DEBUG_TRACE)
	pr_info(DEVICE_NAME ": %s(pcan%d): "
		"rx=[flags=%04xh vcid=%d dlc=%d ts=%llu pid=%04xh sdt=%02xh]\n",
		__func__, dev->nMinor, rm_flags, rm->vcid, rx.msg.data_len - 1,
		le64_to_cpu(rm->hdr.timestamp),
		(u8 )FIELD_GET(CANXL_XL_PID_MASK, rm_pid_rrs_dlc_sec_sdt),
		(u8 )FIELD_GET(CANXL_XL_SDT_MASK, rm_pid_rrs_dlc_sec_sdt));
#endif

	/* check whether posting a CAN frame to user is relevant */
	if (!pcan_post_rxmsg_is_ok(dev))
		return 0;

	/* map uCAN-XL message flags to pcanxl API */
	canxl_handle_rxmsg_flags(&rx, rm_flags, rm->client);

	rx.msg.id = PCANXL_ID(rm->vcid,
			      FIELD_GET(CANXL_XL_PID_MASK,
				        rm_pid_rrs_dlc_sec_sdt));
	rx.msg.af = le32_to_cpu(rm->af);
	rx.msg.sdt = FIELD_GET(CANXL_XL_SDT_MASK, rm_pid_rrs_dlc_sec_sdt);

	if (rm_pid_rrs_dlc_sec_sdt & CANXL_XL_SEC)
		rx.msg.flags |= PCANXL_MSG_SEC;

	/* RRS flag: Remote Request Substitute flag, which is a static dominant
	 * bit as remote frames aren't supported in CANFD nor CANXL
	 */
	if (rm_pid_rrs_dlc_sec_sdt & CANXL_XL_RRS)
		rx.msg.flags |= PCANXL_MSG_RRS;

#ifdef DEBUG_RX_PATH
	return pcanxl_debug_msg(dev, '>', (struct pcanxl_msg *)&rx.msg, rm->d,
				pcan_xxxdev_rx_ex(dev, &rx, rm->d));
#else
	return pcan_xxxdev_rx_ex(dev, &rx, rm->d);
#endif
}

/*
 * int canxl_post_error(struct pcandev *dev, struct canxl_rx_error *er,
 * 		        struct pcan_timespec *ptv)
 */
int canxl_post_error(struct pcandev *dev, struct canxl_rx_error *er,
		     struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx = { .msg = { .data_len = 0, } };
	struct pcan_bus_error err = {
		.type = FIELD_GET(CANXL_ERR_TYPE_MASK, er->err_type_d),
		.code = FIELD_GET(CANXL_ERR_CODE_MASK, er->err_code),
		.rx = er->err_type_d & CANXL_ERR_D,
	};

	/* avoid posting the same msg several times */
	if ((er->rx_err == dev->rx_error_counter) &&
	    (er->tx_err == dev->tx_error_counter))
		return 0;

#ifdef DEBUG_TRACE
	if (printk_ratelimit())
		pr_info(DEVICE_NAME
			"%u : %s(): rx=[type=0x%02x ts=%llu dir=%s code=%u "
			"err_cnt[rx=%u tx=%u]]\n",
			dev->nMinor, __func__, err.type,
			le64_to_cpu(er->hdr.timestamp),
			(err.rx) ? "Rx" : "Tx", err.code,
			er->rx_err, er->tx_err);
#endif

	/* keep a trace of the error info for later use, and, also, to
	 * avoid posting the same message several times
	 */
	dev->rx_error_counter = er->rx_err;
	dev->tx_error_counter = er->tx_err;

#ifdef DEBUG
	if (dev->rx_error_counter || dev->tx_error_counter)
		pr_err(DEVICE_NAME "%u: errors: rx=%u tx=%u\n", dev->nMinor,
			dev->rx_error_counter, dev->tx_error_counter);
#endif

	/* not an "error" but a status... */
	if (err.type > PCANFD_ERRMSG_OTHER) {
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

int canxl_post_status(struct pcandev *dev,
		      struct canxl_rx_status *st, struct pcan_timespec *ptv)
{
	struct pcanxl_rxmsg rx;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d): bus_state=%u "
		"ts=%llu RB=%u EP=%u EW=%u BO=%u]\n",
		__func__, dev->nMinor, dev->bus_state,
		le64_to_cpu(st->hdr.timestamp),
		(u8 )(st->rb_ep_es_bs & CANXL_STATUS_RX_BARRIER),
		(u8 )(st->rb_ep_es_bs & CANXL_STATUS_ERROR_PASSIVE),
		(u8 )(st->rb_ep_es_bs & CANXL_STATUS_ERROR_STATUS),
		(u8 )(st->rb_ep_es_bs & CANXL_STATUS_BUS_STATUS));
#endif

	if (st->rb_ep_es_bs & CANXL_STATUS_BUS_STATUS) {
		pcan_handle_busoff(dev, &rx);

	} else if (!pcan_handle_error_status(dev, &rx,
				st->rb_ep_es_bs & CANXL_STATUS_ERROR_STATUS,
				st->rb_ep_es_bs & CANXL_STATUS_ERROR_PASSIVE)) {
		/* no error bit (so, no error, back to active state) */
		pcan_handle_error_active(dev, &rx);
	}

	if (rx.msg.type == PCANFD_TYPE_NOP) {
#ifdef DEBUG
		pr_info(DEVICE_NAME "%s(pcan%d): status msg discarded (NOP)\n",
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

int canxl_post_busload2(struct pcandev *dev, struct canxl_rx_busload2 *bl,
		        struct pcan_timespec *ptv)
{
	u32 busy_counter = le32_to_cpu(bl->busy_counter);
	u32 idle_counter = le32_to_cpu(bl->idle_counter);
	u64 bus_load;

	/* ignore when  busy_counter and idle_counter are both NULL */
	if (!idle_counter) {
		if (!busy_counter)
			return 0;
		bus_load = 10000;
	} else if (!busy_counter) {
		bus_load = 0;
	} else {
		bus_load = 10000ULL * busy_counter;
		do_div(bus_load, busy_counter + idle_counter);
	}

#ifdef DEBUG_BUS_LOAD
	pr_info(DEVICE_NAME "%u: bus_state=%u ts=%llu busy=%u idle=%u "
		"bl=%llu\n",
		dev->nMinor, dev->bus_state, le64_to_cpu(bl->hdr.timestamp),
		busy_counter, idle_counter, bus_load);
#endif

	return pcan_handle_bus_load(dev, bus_load);
}

int canxl_handle_msg(struct ucan_engine *ucan, void *msg_addr)
{
	struct canxl_rx_hdr *msg = (struct canxl_rx_hdr *)msg_addr;
	void *arg = NULL;
	int msg_size;
	u16 msg_type;
	int ci = -1, err;
	int (*msg_cb)(struct ucan_engine *, void *, void *);
	struct pcandev *dev = container_of(ucan, struct pcandev, ucan);

	msg_size = le16_to_cpu(msg->size);
	if (!msg->size || !msg->type) {
		/* null packet found (CANFD_CMD_NOP): end of list */
		msg_size = 0;
		goto lbl_return;
	}

	msg_type = le16_to_cpu(msg->type);

	switch (msg_type) {

#ifdef USB_SUPPORT
	case CANXL_USB_MSG_CALIBRATION:
		arg = pcan_usb_get_if(ucan_dev(ucan, 0));
		if (!arg) {

			/* protect from interrupt that might occur before
			 * initialization completion: in that rare case, this
			 * message can be silently ignored.
			 */
			goto lbl_return;
		}
		break;
#endif
	default:

		/* these msgs carry a channel index */
		ci = FIELD_GET(CANXL_CHANNEL_MASK, msg->channel_rsrvd);
		break;
	}

	if (msg_type < ucan->ops.handle_msg_size) {
		if (!ucan->ops.handle_msg_table[msg_type]) {

#ifdef DEBUG_UNKNOWN_REC
			pr_warn(DEVICE_NAME
				": %s: unhandled rx CANXL rec %03xh: "
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
		       "it is ignored\n",
		       dev->adapter->name, msg_type,
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

static void canxl_encode_txmsg_fd(struct pcandev *dev, struct pcanxl_txmsg *tx,
				  int tx_msg_size,
				  u8 *buffer_addr, int buffer_size)
{
	struct canxl_tx_msg_fd *tx_msg = (struct canxl_tx_msg_fd *)buffer_addr;
	int dlc = pcan_len2dlc(tx->msg.data_len);
	u16 tx_flags;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d,"
		"msg [type=%u id=%xh dlen=%u flg=%xh])\n",
		__func__, dev->nMinor, tx->msg.type, tx->msg.id,
		tx->msg.data_len, tx->msg.flags);
#endif

	tx_msg->hdr.type = cpu_to_le16(CANXL_TX_MSG_CCFD);
	tx_msg->hdr.size = cpu_to_le16(tx_msg_size);

	canfd_encode_txmsg_flags(tx, &tx_flags, &tx_msg->client);

	tx_msg->id = (tx_flags & CANFD_MSG_EXT_ID) ?
				cpu_to_le32(tx->msg.id & CAN_EFF_MASK) :
				cpu_to_le32(tx->msg.id & CAN_SFF_MASK);

	switch (tx->msg.type) {

	case PCANFD_TYPE_CAN20_MSG:

		if (dlc == PCANFD_CAN20_MAXDATALEN) {
			u8 tmp_dlc = pcanxl_msg_flags_dlc_get(tx->msg.flags);
			if (tmp_dlc > dlc)
				dlc = tmp_dlc;
		}
		break;
	}

	tx_msg->dlc = FIELD_PREP(CANXL_FD_DLC_MASK, dlc);
	tx_msg->flags = cpu_to_le16(tx_flags);
}

static int canxl_encode_txmsg_flags(struct pcanxl_txmsg *tx, u16 *msg_flags,
				    u8 *client)
{
	u16 tx_flags;
	int res = canfd_encode_txmsg_flags(tx, msg_flags, client);

	switch (tx->msg.type) {

	case PCANXL_TYPE_CANXL:
		/* CANXL_FLG_FD_FRAME_FMT(0x10) => DLC is a value not a code
		 * ESI, BRS, RTR,EXT = 0
		 */
		tx_flags = CANXL_FLG_FD_FRAME_FMT|CANXL_MSG_XLF;
		break;
	}

	if (msg_flags)
		*msg_flags |= tx_flags;

	return res;
}

static void canxl_encode_txmsg_xl(struct pcandev *dev, struct pcanxl_txmsg *tx,
				  int tx_msg_size,
				  u8 *buffer_addr, int buffer_size)
{
	struct canxl_tx_msg_xl *tx_msg = (struct canxl_tx_msg_xl *)buffer_addr;
	u16 tx_flags;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d, "
		"msg [type=%u id=%xh len=%u flg=%xh])\n",
		__func__, dev->nMinor, tx->msg.type, tx->msg.id,
		tx->msg.data_len, tx->msg.flags);
#endif

	tx_msg->hdr.type = cpu_to_le16(CANXL_TX_MSG_XL);
	tx_msg->hdr.size = cpu_to_le16(tx_msg_size);

	canxl_encode_txmsg_flags(tx, &tx_flags, &tx_msg->client);

	tx_msg->flags = cpu_to_le16(tx_flags);

	tx_msg->pid_rrs_dlc_sec_sdt = __cpu_to_le32(
		FIELD_PREP(CANXL_XL_PID_MASK, PCANXL_PID(tx->msg.id)) |
		FIELD_PREP(CANXL_XL_DLC_MASK, tx->msg.data_len - 1) |
		FIELD_PREP(CANXL_XL_SDT_MASK, tx->msg.sdt));

	if (tx->msg.flags & PCANXL_MSG_SEC)
		tx_msg->pid_rrs_dlc_sec_sdt |= __cpu_to_le32(CANXL_XL_SEC);

	/* RRS flag: Remote Request Substitute flag, which is a static dominant
	 * bit as remote frames aren't supported in CANFD nor CANXL
	 */
	if (tx->msg.flags & PCANXL_MSG_RRS)
		tx_msg->pid_rrs_dlc_sec_sdt |= __cpu_to_le32(CANXL_XL_RRS);

	tx_msg->vcid = PCANXL_VCID(tx->msg.id);
	tx_msg->af = cpu_to_le32(tx->msg.af);
}

/*
 * int canxl_encode_txmsg(struct pcandev *dev, u8 *buffer_addr,
 * 			   int buffer_size)
 *
 * @return:
 *
 * 	> 0		size in bytes of the copied msg
 *	-ENODATA	if Tx fifo is empty
 *	-ENOSPC		if output buffer is not large enough
 */
int canxl_encode_txmsg(struct pcandev *dev, u8 *buffer_addr, int buffer_size)
{
	struct pcanxl_txmsg tx;
	void (*tx_msg_encoder)(struct pcandev *dev, struct pcanxl_txmsg *tx,
			       int tx_msg_size,
			       u8 *buffer_addr, int buffer_size);
	char *tx_msg_data;
	int tx_msg_size;

	/* Check how many bytes are to be read from Tx FIFO.
	 * WARNING: DON'T pull anything from the fifo in case there is not
	 * enough room in the output buffer sent to the device, but just peek
	 * the header to get the entire size of the frame.
	 */
	int err = pcan_txfifo_hdr_peek(dev, &tx);
	if (!err) {
#ifdef DEBUG_TX_PATH
		pr_info(DEVICE_NAME ": %s(): "
			"No more header to read from Tx fifo\n",
			__func__);
#endif
		return -ENODATA;
	}

	/* According to the message type, compute:
	 * - the encoder callback (records formats are different)
	 * - the data address (in the record) where to copy the data byte
	 *   from the Tx Fifo
	 * - the exact size needed to store the whole record in the output
	 *   buffer.
	 */
	switch (tx.msg.type) {
	case PCANFD_TYPE_CAN20_MSG:
	case PCANFD_TYPE_CANFD_MSG:
		tx_msg_encoder = canxl_encode_txmsg_fd;
		tx_msg_data = buffer_addr + offsetof(struct canxl_tx_msg_fd, d);
		tx_msg_size = ALIGN(sizeof(struct canxl_tx_msg_fd) +
				    tx.msg.data_len, 4);
		break;

	case PCANXL_TYPE_CANXL:
		tx_msg_encoder = canxl_encode_txmsg_xl;
		tx_msg_data = buffer_addr + offsetof(struct canxl_tx_msg_xl, d);
		tx_msg_size = ALIGN(sizeof(struct canxl_tx_msg_xl) +
				    tx.msg.data_len, 4);
		break;
	default:
		pr_err(DEVICE_NAME "%d: "
		       "Invalid msg type %0xh(%u) read from Tx fifo err %d\n",
		       dev->nMinor, tx.msg.type, tx.msg.type, err);

		return -EINVAL;
	}

	/* if not enough room to entirely copy it, stop here */
	if (tx_msg_size > buffer_size) {
#ifdef DEBUG_TX_PATH
		pcanxl_debug_msg(dev, 'D', (struct pcanxl_msg *)&tx.msg,
				 NULL, -ENOSPC);
		pr_info(DEVICE_NAME ": %s(pcan%d): "
			"%u bytes left too small for storing %u bytes\n",
			__func__, dev->nMinor, buffer_size, tx_msg_size);
#endif
		return -ENOSPC;
	}

	/* Since there is enough room to store the pending frame,
	 * can read the entire enqueued CAN message.
	 */
	err = pcan_txfifo_out(dev, &tx, tx_msg_data);
	if (err < 0) {
		pr_err(DEVICE_NAME "%u: "
		       "unable to read item from Tx fifo err %d\n",
		       dev->nMinor, err);

		return err;
	}

	tx_msg_encoder(dev, &tx, tx_msg_size, buffer_addr, buffer_size);

	dev->total_stats.tx.bytes += tx.msg.data_len;
	dev->session_stats.tx.bytes += tx.msg.data_len;

#ifdef DEBUG_TX_PATH
	pcanxl_debug_msg(dev, '<', (struct pcanxl_msg *)&tx.msg,
			 tx_msg_data, tx_msg_size);
#endif
	return tx_msg_size;
}

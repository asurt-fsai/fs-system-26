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
/*#define DEBUG*/
/*#undef DEBUG*/

#include "src/pcanxl_core.h"
#include "src/pcan_filter.h"

#ifdef DEBUG
#define DEBUG_WAIT_RD
#define DEBUG_WAIT_WR
#define DEBUG_OPEN
#define DEBUG_BITRATE
#else
//#define DEBUG_WAIT_RD
//#define DEBUG_WAIT_WR
//#define DEBUG_OPEN
//#define DEBUG_TRACE
//#define DEBUG_BITRATE
#endif

/* Timeout set to task waiting for room in the tx queue.
 * 0 means infinite.
 * != 0 implies that the wait might end with -ETIMEDOUT.
 */
//#define PCANFD_TIMEOUT_WAIT_FOR_WR	100
#define PCANFD_TIMEOUT_WAIT_FOR_WR	0

/* if defined, the controller is NOT reset if it is currently configured
 * with the same bittiming specs than the new one. This is especially useful
 * when calling ioctl(SET_INIT) next to open("/dev/pcanX").
 */
#define PCANFD_IGNORE_SAME_BITTIMING

/*
 * void __pcan_bittiming_to_bitrate(struct pcan_bittiming *pbt, u32 clk_Hz)
 *
 * Compute bitrate according to bittiming spec and Clock frequency.
 *
 * WARNING: pbt->brp MUST BE != 0
 */
static void __pcan_bittiming_to_bitrate(struct pcan_bittiming *pbt, u32 clk_Hz)
{
	u64 v64;

	if (!pbt->sjw)
		pbt->sjw = 1; /* ??? */

	pbt->sample_point = (PCAN_SAMPT_SCALE *
		(1 + pbt->tseg1)) / (1 + pbt->tseg1 + pbt->tseg2);

	pbt->bitrate = pcan_get_bps(clk_Hz, pbt);

	v64 = (u64 )pbt->brp * GHz;
	do_div(v64, clk_Hz);
	pbt->tq = (u32 )v64;
}

/*
 * static int pcan_bittiming_to_bitrate(struct pcandev *dev,
 *					struct pcan_bittiming *pbt,
 *					u32 clk_Hz)
 */
static int pcan_convert_bittiming(struct pcandev *dev,
				  struct pcan_bittiming *pbt,
				  u32 clk_Hz)
{
	if (pbt->brp) {
		u32 user_bitrate = pbt->bitrate;

		__pcan_bittiming_to_bitrate(pbt, clk_Hz);

		if (user_bitrate && user_bitrate != pbt->bitrate) {
			pr_err(DEVICE_NAME
			       "%u: [BRP=%u TSEGx=%u/%u CLK=%u Hz]=%u bps "
			       "which is different from user value %u bps\n",
			       dev->nMinor, pbt->brp,
			       pbt->tseg1, pbt->tseg2, clk_Hz,
			       pbt->bitrate, user_bitrate);

			return -EINVAL;
		}

	} else if (!pbt->bitrate) {
		pr_err(DEVICE_NAME "%u: can't fix wrong %u Hz clock with "
		       "null BRP and null bitrate\n",
		       dev->nMinor, clk_Hz);

		return -EINVAL;
	}

	/* bitrate is now valid. Can reset BRP to force to compute the correct
	 * value next
	 */
	pbt->brp = 0;

	return 0;
}

int pcan_bittiming_normalize_ex(struct pcan_bittiming *pbt, u32 clock_Hz,
				const struct pcanfd_bittiming_range *caps,
				int pwm_encoding, int desired_brp)
{
	int err = 0;

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME ": %s(L%u)\n", __func__, __LINE__);
	pcanfd_dump_bittiming(pbt, clock_Hz);
#endif

	/* NEW 8.2: always trust BRP/TEGx first:
	 * if brp valid, use these for computing the bitrate field
	 *
	 * NEW 9.0: use BRP and TSEGx values only if they all are not 0!
	 */
	if (pbt->brp && pbt->tseg1 && pbt->tseg2) {
		if (pbt->brp < caps->brp_min)
			pbt->brp = caps->brp_min;
		else if (pbt->brp > caps->brp_max)
			pbt->brp = caps->brp_max;

		if (pbt->tseg1 < caps->tseg1_min)
			pbt->tseg1 = caps->tseg1_min;
		else if (pbt->tseg1 > caps->tseg1_max)
			pbt->tseg1 = caps->tseg1_max;

		if (pbt->tseg2 < caps->tseg2_min)
			pbt->tseg2 = caps->tseg2_min;
		else if (pbt->tseg2 > caps->tseg2_max)
			pbt->tseg2 = caps->tseg2_max;

		__pcan_bittiming_to_bitrate(pbt, clock_Hz);

	} else if (pbt->bitrate) {
		err = pcan_bitrate_to_bittiming_ex(pbt, caps, clock_Hz,
						   pwm_encoding, desired_brp);

	/* else, if any of them is valid, it's an error!
	 * THIS SHOULD NOT OCCUR!
	 */
	} else {
		pr_err(DEVICE_NAME
		       ": invalid bittiming specs: unable to normalize\n");

		return -EINVAL;
	}

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME ": %s(L%u)\n", __func__, __LINE__);
	pcanfd_dump_bittiming(pbt, clock_Hz);
#endif
	return err;
}

/*
 * Convert SJA1000 BTR0BTR1 16-bits value into a generic bittiming
 * representation
 */
struct pcan_bittiming *pcan_btr0btr1_to_bittiming(struct pcan_bittiming *pbt,
						  u16 btr0btr1)
{
	pbt->sjw = 1 + ((btr0btr1 & 0xc000) >> 14);
	pbt->brp = 1 + ((btr0btr1 & 0x3f00) >> 8);
	pbt->tsam = (btr0btr1 & 0x0080) >> 7;
	pbt->tseg2 = 1 + ((btr0btr1 & 0x0070) >> 4);
	pbt->tseg1 = 1 + (btr0btr1 & 0x000f);
	pbt->bitrate = 0;

	__pcan_bittiming_to_bitrate(pbt, 8*MHz);

	return pbt;
}

#define PCANXL_DATALEN_DBG_SIZE		8

int pcanxl_debug_msg(struct pcandev *dev, char sens,
		     struct pcanxl_msg *msg, u8 *data, int err)
{
	char tmp[3*PCANXL_DATALEN_DBG_SIZE+1];

	if (data) {
		int i, l;

		for (i = l = 0; i < PCANXL_DATALEN_DBG_SIZE; i++)
			if (i < msg->data_len)
				l += scnprintf(tmp+l, sizeof(tmp) - l, "%02x ",
					       data[i]);
			else
				break;
	} else {
		*tmp = '\0';
	}

	pr_info(DEVICE_NAME "%d: %c id=%xh len=%u data=[%s] (err %d)\n",
			dev->nMinor, sens, msg->id, msg->data_len, tmp, err);
	return err;
}

/* Convert old CAN 2.0 init object into new-style CAN-FD init object. */
struct pcanfd_init *pcan_init_to_fd(struct pcandev *dev,
				    struct pcanfd_init *pfdi,
				    const TPCANInit *pi)
{
	/* DON'T memset('\0') the struct pcanxl_init since it may already
	 * contain data (or other CANXL specific values). Caller HAS TO
	 * initialize the struct pcanxl_init by himself!
	 */
	memset(&pfdi->data, '\0', sizeof(struct pcan_bittiming));

	if (!pfdi->clock_Hz)
		pfdi->clock_Hz = dev->sysclock_Hz;

	if (!(pi->ucCANMsgType & MSGTYPE_EXTENDED))
		pfdi->flags |= PCANFD_INIT_STD_MSG_ONLY;

	if (pi->ucListenOnly)
		pfdi->flags |= PCANFD_INIT_LISTEN_ONLY;

	if (pi->wBTR0BTR1) {
		pcan_btr0btr1_to_bittiming(&pfdi->nominal, pi->wBTR0BTR1);

		if (pfdi->clock_Hz != 8*MHz) {

			/* compute new bittiming according to the real clock */
			pcan_bitrate_to_bittiming(&pfdi->nominal,
						  dev->bittiming_caps,
						  pfdi->clock_Hz);
		}
	}

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME ": %s(): 8xMHz btr0btr1=%04xh =>\n",
		__func__, pi->wBTR0BTR1);
	pcanfd_dump_bittiming(&pfdi->nominal, pfdi->clock_Hz);
#endif
	return pfdi;
}

struct pcanxl_init *pcanfd_init_to_xl(struct pcandev *dev,
				      struct pcanxl_init *pxli,
				      const struct pcanfd_init *pfdi)
{
	/* DON'T memset('\0') the struct pcanxl_init since it may already
	 * contain data (or other CANXL specific values). Caller HAS TO
	 * initialize the struct pcanxl_init by himself!
	 */
	pxli->flags |= pfdi->flags;

	if (!pxli->clock_Hz) {
		pxli->clock_Hz = pfdi->clock_Hz;
		if (!pxli->clock_Hz)
			pxli->clock_Hz = dev->sysclock_Hz;
	}

	memcpy(&pxli->nominal, &pfdi->nominal, sizeof(pxli->nominal));
	memcpy(&pxli->fd_data, &pfdi->data, sizeof(pxli->fd_data));

	memset(&pxli->xl_data, '\0', sizeof(struct pcan_bittiming));

	return pxli;
}

struct pcanxl_init *pcan_init_to_xl(struct pcandev *dev,
				    struct pcanxl_init *pxli,
				    const TPCANInit *pi)
{
	struct pcanfd_init fdi = {};
	return pcanfd_init_to_xl(dev, pxli, pcan_init_to_fd(dev, &fdi, pi));

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME ": %s(): 8xMHz btr0btr1=%04xh =>\n",
		__func__, pi->wBTR0BTR1);
	pcanfd_dump_bittiming(&pxli->nominal, pxli->clock_Hz);
#endif
	return pxli;
}

/*
 * u32 pcan_xfer_time_ms(struct pcandev *dev, u32 tx_frm, long tx_data)
 *
 * Compute time in ms. to transfer tx_frm frames with tx_data data bytes at
 * the device nominal bitrate.
 *
 * @tx_frm: number of CAN frames
 * @tx_data: number of data bytes
 *
 * if tx_data < 0 then CAN_CC/CAN_FD max data length and nominal bitrate
 * are used.
 */
u32 pcan_xfer_time_ms(struct pcandev *dev, u32 tx_frm, long tx_data)
{
	/* CANCC frame = SOF+HDR(18)+DATA+CRC(15)+DEL+ACK+DEL+EOF(7)
	 *                           ----
	 * 	       = HDR = 44b + IFS(3b) = 47b
	 *
	 * Worst case of stuffing for a 8 bytes data frame adds 19 bits.
	 *
	 * Extended Id format needs +20 bits => HDR = 67b
	 *
	 * Extended 8 bytes frame with worst case of bit stuffing <= 157 bits
	 * (+ IFS(3b)) = 160 = 96 + 8 * 8 = 67 + 8 * 8 + 29 (stuff)
	 *
	 * see: https://en.wikipedia.org/wiki/CAN_bus#Bit_stuffing
	 *
	 * CANFD frame = SOF+HDR(22)+DATA+STF(4)+CRC(22)+FSB(7)+
	 * 		 ACK(2)+EOF(7)
	 *             = 65b + 64 * 8b = 577b + IFS(3b) = 580b
	 *             = 68 + 64 * 8b
	 * Using EFF in CANFD frame adds 11-bit.
	 * Worst case of bit stuffing with 64 data bytes = 673b
	 * (see: https://electronics.stackexchange.com/questions/284797/can-fd-bit-stuffing)
	 * => CANFD HDR with max stuffing = 673 - 64 x 8 = 161
	 */
	//u32 nom_bits = 76; /* 11-bit ID + stuff_max */
	u32 nom_bits = 96; /* 29-bit ID + stuff_max */
	u32 data_bits = PCANFD_CAN20_MAXDATALEN * BITS_PER_BYTE;
	u32 data_bitrate = dev->init_settings.nominal.bitrate;

	if (dev->init_settings.flags & PCANXL_INIT_XL) {
		data_bits = PCANXL_CANXL_MAXDATALEN * BITS_PER_BYTE;
		data_bitrate = dev->init_settings.xl_data.bitrate;

	} else if (dev->init_settings.flags & PCANXL_INIT_FD) {
		//nom_bits = 161; /* 11-bit ID + stuff_max */
		nom_bits = 172; /* 29-bit ID + stuff_max */
		data_bits = PCANFD_CANFD_MAXDATALEN * BITS_PER_BYTE;

		/* Using data bitrate here can lead to very short delay when
		 * CAN-FD frames are written wihout BRS. Therefore, use
		 * nominal bitrate instead.
		 */
		//data_bitrate = dev->init_settings.fd_data.bitrate;
	}

	nom_bits *= tx_frm;

	if (tx_data >= 0)
		data_bits = tx_data * BITS_PER_BYTE;
	else
		data_bits *= tx_frm;

	return DIV_ROUND_UP(MSEC_PER_SEC * nom_bits,
			    dev->init_settings.nominal.bitrate) +
	       DIV_ROUND_UP(MSEC_PER_SEC * data_bits, data_bitrate);
}

/*
 * void pcanxl_tx_delay_ex(struct pcandev *dev, u32 extra_ms)
 *
 * Wait for enough time to be sure that all sent frames have been written on
 * wire.
 *
 * WARNING: this function DOESN'T take into account Tx fifo content, it assumes
 * that pcan_release_path() has been called before (waiting for Tx FIFO to be
 * empty puts the calling task in SLEEP state).
 */
int pcanxl_tx_delay_ex(struct pcandev *dev, int extra_ms)
{
	struct pcan_frm_counter in_flight = { 0, 0 };
	u32 ms_to_wait;

	/* no need to wait? */
	if (dev->linger_opt_value == PCANFD_OPT_LINGER_NOWAIT)
		return 0;

#ifdef USB_SUPPORT
	if (pcan_is_usb_kind(dev)) {
		struct pcan_usb_interface *usb_if = pcan_usb_get_if(dev);
		extra_ms += usb_if->rtt_ms;
	}
#endif

	if (dev->icache) {
#ifdef DEBUG_OPEN
		char tmp[81];
		int l = 0;
#endif
		int i;

		for (i = 0; i < dev->icache->size; i++) {
			in_flight.frames += dev->icache->rec[i].frames;
			in_flight.bytes += dev->icache->rec[i].bytes;
#ifdef DEBUG_OPEN
			l += scnprintf(tmp+l, sizeof(tmp)-l, "%u/%u ",
				       dev->icache->rec[i].frames,
				       dev->icache->rec[i].bytes);
		}

		tmp[--l] = ']';
		pr_info(DEVICE_NAME ": %s(pcan%u): cache=[%s\n",
			__func__, dev->nMinor, tmp);
	}

	pr_info(DEVICE_NAME
		": %s(pcan%u): in_flight=%u/%u +%u\n", __func__, dev->nMinor,
		in_flight.frames, in_flight.bytes, extra_ms);
#else
		}
	}
#endif

	/* if bus is not in valid state, or if there are no frame in flight
	 * then no need to wait
	 */
	if ((dev->bus_state != PCANFD_ERROR_ACTIVE) || !in_flight.frames)
		return 0;

	/* time to wait for data in-flight to be written on the wire */
	ms_to_wait = extra_ms + pcan_xfer_time_ms(dev,
						  in_flight.frames,
						  in_flight.bytes);
	/* barrier */
	if (ms_to_wait > 500) {
		pr_warn(DEVICE_NAME "%u: %s CAN%u: "
			"too long time to flush %u ms!\n",
			dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
			ms_to_wait);
		ms_to_wait = 500;
	}

#ifdef DEBUG_OPEN
	pr_info(DEVICE_NAME ": %s(pcan%u): waiting for %ums...\n",
		__func__, dev->nMinor, ms_to_wait);
#endif

	/* Note: this wait MUST not be interruptible for USB devices (=>
	 * mdelay() mandatory)
	 */
	mdelay(ms_to_wait);

	return ms_to_wait;
}

/*
 * void __pcanxl_dev_reset(struct pcandev *dev)
 *
 * Release a device: after that call, the device is no more opened.
 * WARNING: caller should normally wait for the output fifo to be empty
 *          before calling pcanxl_dev_reset()
 */
void __pcanxl_dev_reset(struct pcandev *dev)
{
	/* close Tx engine BEFORE device_release() so that device Tx resources
	 * will be able to be safety released from writing task.
	 */
	pcan_lock_irqsave_ctxt flags;

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(pcan%d bus=%u)\n", __func__, dev->nMinor,
		dev->bus_state);
#endif

	dev->lock_irq(dev, &flags);
	pcan_set_tx_engine(dev, TX_ENGINE_CLOSED);
	dev->unlock_irq(dev, &flags);

	/* release the device (= USB_device::bus_off() callback)*/
	if (dev->device_release)
		dev->device_release(dev);

	dev->flags &= ~PCAN_DEV_OPENED;
	pcan_set_bus_state(dev, PCANFD_UNKNOWN);

	if (dev->adapter->opened_count > 0)
		dev->adapter->opened_count--;

#if defined(DEBUG) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(pcan%d): rx=%u/%u tx=%u/%u\n",
		__func__, dev->nMinor,
		dev->session_stats.rx.frames,
		dev->total_stats.rx.frames,
		dev->session_stats.tx.frames,
		dev->total_stats.tx.frames);
#endif
}

/*
 * void pcanxl_dev_open_init(struct pcandev *dev)
 *
 * open() path
 */
void pcanxl_dev_open_init(struct pcandev *dev)
{
	/* nofilter */
	dev->acc_11b.code = 0;
	dev->acc_11b.mask = CAN_MAX_STANDARD_ID;
	dev->acc_29b.code = 0;
	dev->acc_29b.mask = CAN_MAX_EXTENDED_ID;

	dev->tx_iframe_delay_us = 0;
	//dev->ts_xmit_start_ms = 0;

	/* Nope! Consider that PCANFD_OPT_ALLOWED_MSGS option can be set
	 * once the device is opened, so don't reset this mask when
	 * SET_INIT is called
	 */
	//dev->allowed_msgs = PCANFD_ALLOWED_MSG_DEFAULT;

	/* Nope! Since pcan v8.6, time sync is handled as soon as the device
	 * hw is probed (mainly USB devices): starting/stopping CM when
	 * opening/closing the PCAN-Chip does not work, since ts in CM are not
	 * based like ts in CAN msgs...
	 * (see also: CANFD_USB_START_CM_AT_OPEN)
	 */
	//pcan_sync_init(dev);

	/* New: reset these counters too */
	dev->total_stats.error_counter = 0;
	dev->total_stats.rx_irq_counter = 0;
	dev->total_stats.tx_irq_counter = 0;

	/* reset session counters */
	pcan_stats_reset(&dev->session_stats);

	pcan_set_bus_state(dev, PCANFD_UNKNOWN);

	/* WARNING: all the below stuff was done in soft_init() in v8, which
	 * means that, once changed, these values was kept even after a close().
	 * Now, in v9, these values MUST be set each time the device is opened,
	 * in case the default values aren't ok.
	 */
	dev->linger_opt_value = MAX_WAIT_UNTIL_CLOSE;

#ifndef NETDEV_SUPPORT
	__pcan_set_ts_mode(dev, -1, true);
#endif
}

/*
 * int pcanxl_fix_init_clock(struct pcandev *dev, struct pcanxl_init *pxli)
 *
 * Check if given clock is a valid one. If not, bittimings are changed to
 * keep any bitrate value defined by user.
 */
static int pcanxl_fix_init_clock(struct pcandev *dev, struct pcanxl_init *pxli)
{
	const struct pcanfd_available_clocks *pc = dev->clocks_list;
	int i, err;

	for (i = 0; i < pc->count; i++)
		if (pxli->clock_Hz == pc->list[i].clock_Hz)
			break;

	/* user clock found in device clocks list: nothing to do */
	if (i < pc->count)
		return 0;

	/* fix user clock with device default one to convert the bitrate value
	 * in valid bittiming registers values.
	 *
	 * User has given an unknown clock:
	 * - either compute desired bitrate according to BRP,TSEGx,
	 * - or use given bitrate value to compute new BRPS,TSEGx,SJW values
	 *   according to device default clock,
	 */
	err = pcan_convert_bittiming(dev, &pxli->nominal, pxli->clock_Hz);
	if (err)
		return err;

	/* Do the same with CAN FD bittimings: consider BRP/TSEGx expressed with
	 * wong clock, so use them to compute the desired FD data bitrate first.
	 */
	if (pxli->flags & PCANXL_INIT_FD) {
		err = pcan_convert_bittiming(dev, &pxli->fd_data,
					     pxli->clock_Hz);
		if (err)
			return err;
	}

	/* Do the same with CAN XL bittimings: consider BRP/TSEGx expressed with
	 * wong clock, so use them to compute the desired XL data bitrate first.
	 *
	 * XL data bittiming:
	 *
	 * TODO: CiA CANXL guidelines and application notes 612_1
	 * Table 1 - CAN XL clock recommendations
	 *
	 * For data phase bit-rates <=	Clock
	 * <= 20 Mbit/s			160 MHz (or multiple)
	 * <= 5 Mbit/s			80 MHz (or multiple)
	 */
	if (pxli->flags & PCANXL_INIT_XL) {
		err = pcan_convert_bittiming(dev, &pxli->xl_data,
					     pxli->clock_Hz);
		if (err)
			return err;
	}

	/* fix user clock with device default one to convert the bitrate value
	 * in valid bittiming registers values
	 */
	pxli->clock_Hz = dev->sysclock_Hz;

	return 0;
}

/*
 * int __pcanxl_dev_open(struct pcandev *dev, struct pcanxl_init *pxli)
 *
 * open() path
 * consider pxli ok
 */
static int __pcanxl_dev_open(struct pcandev *dev, struct pcanxl_init *pxli)
{
	struct pcanxl_init tmp_init;
	int err;

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(pcan%d): btr=%u,%u,%u\n",
		__func__, dev->nMinor, pxli->nominal.bitrate,
		pxli->fd_data.bitrate, pxli->xl_data.bitrate);
	pcanfd_dump_bittiming(&pxli->nominal, pxli->clock_Hz);
	if (pxli->flags & PCANXL_INIT_FD)
		pcanfd_dump_bittiming(&pxli->fd_data, pxli->clock_Hz);
	if (pxli->flags & PCANXL_INIT_XL)
		pcanfd_dump_bittiming(&pxli->xl_data, pxli->clock_Hz);
#endif

	/* do this BEFORE calling open callbacks, to be ready to handle
	 * timestamps conversion if any msg is posted by them. These two init
	 * steps are made again at the end, as usual.
	 */
	pcan_gettimeofday_ns(&dev->init_timestamp);

	pcanxl_copy_init(&tmp_init,
			 pcanxl_copy_init(&dev->init_settings, pxli));

	pcanxl_dev_open_init(dev);

	/* use old APi entry (with wBTR0BTR1) if CAN controller clock
	 * is 8 MHz.
	 */
	if (pxli->clock_Hz == 8*MHz) {
		TPCANInit init;

		pxli->flags &= ~(PCANXL_INIT_FD|PCANXL_INIT_XL);
		memset(&pxli->fd_data, '\0', sizeof(struct pcan_bittiming));
		memset(&pxli->xl_data, '\0', sizeof(struct pcan_bittiming));

		init.ucCANMsgType = (pxli->flags & PCANFD_INIT_STD_MSG_ONLY) ?
						0 : MSGTYPE_EXTENDED;
		init.ucListenOnly = !!(pxli->flags & PCANFD_INIT_LISTEN_ONLY);

		/* we're sure that the bittiming are ok: no need to check nor
		 * convert them again.
		 */
		init.wBTR0BTR1 = pcan_bittiming_to_btr0btr1(&pxli->nominal);
		if (!init.wBTR0BTR1) {
			init.wBTR0BTR1 = sja1000_bitrate(
				dev->def_init_settings.nominal.bitrate,
				dev->def_init_settings.nominal.sample_point,
				dev->def_init_settings.nominal.sjw);
#ifdef DEBUG
			pr_err(DEVICE_NAME "%d: using default BTR0BTR1\n",
			       dev->nMinor);
#endif
		}

#ifdef DEBUG_BITRATE
		pr_info(DEVICE_NAME "%d: time=%llu.%09llus: opening with "
			"BTR0BTR1=%04xh (bitrate=%u sp=%u) flags=%08xh\n",
			dev->nMinor, dev->init_timestamp.tv_sec,
			dev->init_timestamp.tv_nsec, init.wBTR0BTR1,
			pxli->nominal.bitrate, pxli->nominal.sample_point,
			pxli->flags);
		pr_info(DEVICE_NAME "%d: nominal "
			"[brp=%d tseg1=%d tseg2=%d sjw=%d]\n",
			dev->nMinor, pxli->nominal.brp, pxli->nominal.tseg1,
			pxli->nominal.tseg2, pxli->nominal.sjw);
#endif

		/* device is not CAN-FD capable: forward to (old) CAN 2.0 API */
		err = dev->device_open(dev, init.wBTR0BTR1,
				       init.ucCANMsgType, init.ucListenOnly);

	/* use the new API entry point (erroneously called "open_fd") that 
	 * enable to setup the true bitimings according to a given clock, as
	 * well as defining a data bitrate (CAN-FD)
	 */
	} else {

#ifdef DEBUG_BITRATE
		pr_info(DEVICE_NAME "%d: time=%llu.%09llus: opening with "
			"clk=%u bitrate=%u fd_dbitrate=%u xl_dbitrate=%u "
			"(flags=%08xh)\n",
			dev->nMinor, dev->init_timestamp.tv_sec,
			dev->init_timestamp.tv_nsec, pxli->clock_Hz,
			pxli->nominal.bitrate, pxli->fd_data.bitrate,
			pxli->xl_data.bitrate, pxli->flags);
		pr_info(DEVICE_NAME "%d: nominal "
			"[brp=%d tseg1=%d tseg2=%d sjw=%d sp=%u]\n",
			dev->nMinor, pxli->nominal.brp, pxli->nominal.tseg1,
			pxli->nominal.tseg2, pxli->nominal.sjw,
			pxli->nominal.sample_point);
		if (pxli->flags & PCANXL_INIT_FD)
			pr_info(DEVICE_NAME "%d: fd_data "
			"[brp=%d tseg1=%d tseg2=%d sjw=%d sp=%u]\n",
			dev->nMinor, pxli->fd_data.brp,
			pxli->fd_data.tseg1, pxli->fd_data.tseg2,
			pxli->fd_data.sjw, pxli->fd_data.sample_point);
		if (pxli->flags & PCANXL_INIT_XL)
			pr_info(DEVICE_NAME "%d: xl_data "
			"[brp=%d tseg1=%d tseg2=%d sjw=%d sp=%u]\n",
			dev->nMinor, pxli->xl_data.brp,
			pxli->xl_data.tseg1, pxli->xl_data.tseg2,
			pxli->xl_data.sjw, pxli->xl_data.sample_point);
#endif
		if (dev->device_open_xl)
			err = dev->device_open_xl(dev, pxli);
		else
			err = dev->device_open_fd(dev,
						  (struct pcanfd_init *)pxli);
	}

	if (!err) {
		pcan_lock_irqsave_ctxt flags;

		dev->flags |= PCAN_DEV_OPENED;
		dev->opened_index = dev->adapter->opened_count++;

		pcan_gettimeofday_ns(&dev->init_timestamp);

		/* remember the init settings for further usage */
		pcanxl_copy_init(&dev->init_settings, pxli);

		/* default tx engine state: ready to start! */
		dev->lock_irq(dev, &flags);

		if (dev->locked_tx_engine_state == TX_ENGINE_CLOSED)
			pcan_set_tx_engine(dev, TX_ENGINE_STOPPED);

		dev->unlock_irq(dev, &flags);

		/* now bus load timer is started when bus state goes to
		 * ERROR_ACTIVE (see pcan_set_bus_state()) when not in
		 * NETDEV mode.
		 */
		return 0;
	}

	/* since these settings are bad, should undo the above 
	 * pcanxl_copy_init()
	 */
	pcanxl_copy_init(&dev->init_settings, &tmp_init);

	return err;
}

/*
 * bool pcanxl_check_sspo(struct pcandev *dev, struct pcan_bittiming *bt)
 *
 * TSE3: SP position difference error
 * If the SP positions of the nominal bit time are different in transmitter and
 * receiver, then there is a static offset between the time-stamp positions.
 *
 * TSE3_O = (SP transmitter – SP receiver) * Tbit
 *
 * This systematic error should be avoided by configuring in transmitter and
 * receiver the same SP position in the nominal bit time.
 *
 * TSE3_O occurs only on receiver side. This is because the transmitter is
 * considered as reference.
 *
 * Example:
 *
 *	Nominal bit time: Tbit = 2000 ns (500 kbit/s)
 *	Nominal SP transmitter: 80 %
 *	Nominal SP receiver: 70 %
 *
 * TSE3_O = 10 %*2000 ns = 200 ns
 */
static bool pcanxl_check_sspo(struct pcandev *dev, struct pcan_bittiming *bt)
{
	switch (bt->ssp_offset) {
	case PCANXL_SSP_OFFSET_SP:
	case PCANXL_SSP_OFFSET_OFF:
		break;

	default:
		if (bt->ssp_offset > PCANXL_SSP_OFFSET_MAX) {
			pr_err(DEVICE_NAME "%d: %s CAN%u %u: SSP offset "
			       "value %02xh out of range [%02xh..%02xh]\n",
			       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
			       dev->adapter->index, bt->ssp_offset,
			       PCANXL_SSP_OFFSET_MIN, PCANXL_SSP_OFFSET_MAX);

			return false;
		}
	}

	return true;
}

/* length of a PWM symbol (in nanoseconds) */
#define PWM_BIT_TIME_MIN_NS	45
#define PWM_BIT_TIME_MAX_NS	200
#define PWM_BIT_TIME_NS		PWM_BIT_TIME_MAX_NS

/*
 * static int pcanxl_set_default_pwm(struct pcandev *dev,
 * 				     struct pcanxl_init *pxli)
 *
 * Set the optimum value 25%/75% of the NRZ bit time to PWM short/long
 *
 * WARNING: Nominal AND XL data bitrates values SHOULD NOT BE 0!
 */
static int pcanxl_set_default_pwm(struct pcandev *dev, struct pcanxl_init *pxli)
{
	u32 nom_mtq, xl_mtq, base_mtq;

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME "%u: %s(nom_btr=%u xl_data=%u)\n",
		dev->nMinor, __func__, pxli->nominal.bitrate,
		pxli->xl_data.bitrate);
#endif

	if (!pxli->nominal.bitrate || !pxli->xl_data.bitrate) {
		pr_err(DEVICE_NAME "%u: %s(): Abnormal NULL bitrates "
		       "nominal=%u xl_data=%u\n",
		       dev->nMinor, __func__, pxli->nominal.bitrate,
		       pxli->xl_data.bitrate);
		return -EINVAL;
	}

	/* 1 - calculate nom_mtq and xl_mtq
	 * nom_btr = 1000 kbps => nom_mtq = 160
	 * nom_btr = 500 kbps => nom_mtq = 320
	 */
	nom_mtq = pxli->clock_Hz / pxli->nominal.bitrate;

	/* xl_data = 4 Mbps => xl_mtq = 40
	 * xl_data = 2 Mbps => xl_mtq = 80
	 */
	xl_mtq = pxli->clock_Hz / pxli->xl_data.bitrate;

	/* 2 - PWM symbol needs 200 ns => 5M x PWM per second are needed:
	 *
	 * if xl_data >= 5 MBps: straight and easy
	 */
	if (pxli->xl_data.bitrate >= 5000000) {

		/* 1 PWM symbol per data bit required */
		base_mtq = xl_mtq;
	} else {

		/* more than 1 PWM symbol per data bit required. This is
		 * achieved by configuring a shorter PWM symbol time:
		 *
		 * Ex:
		 * - xl_data = 4 Mbps => 1 bit time = 250 ns
		 * - xl_data = 2 Mbps => 1 bit time = 500 ns
		 *
		 * See CiA 612-2 5.8.4
		 */
		u32 xl_bit_time = NSEC_PER_SEC / pxli->xl_data.bitrate;

		/* PWM symbol per bit (min) = roundup(xl_bit_time / 200)
		 *
		 * xl_data = 4 Mbps => pwm_per_bit_min = (250+199)/200 = 2
		 * xl_data = 2 Mbps => pwm_per_bit_min = (500+199)/200 = 3
		 */
		u32 pwm_per_bit_min = (xl_bit_time + PWM_BIT_TIME_NS-1) /
						PWM_BIT_TIME_NS;

		/* Note: knowing that this loop can't be endless,
		 *       pwm_per_bit = xl_bit_time *ISNOT* an acceptable value.
		 *       But, since optimal base_mtq minimum value is 4, then
		 *       let set the upper limit of pwm_per_bit to
		 *       xl_mtq / 4.
		 */
		const u32 pwm_per_bit_max = xl_mtq / 4;

		u32 pwm_per_bit;

		/* then, loop to find the first multiple of PWM symbols that
		 * fits into xl_bit_time:
		 *
		 * xl_data = 4 Mbps => mod(250, 2) == 0
		 *
		 *      PWM |    1    |    2    |
		 *
		 * => pwm_per_bit = 2 (PWM length = 125 ns)
		 *
		 * But also:
		 *
		 * xl_data = 4 Mbps => mod(250, 5) == 0
		 *
		 *      PWM | 1 | 2 | 3 | 4 | 5 |
		 *
		 * data bit |                   |
		 *          <------ 250 ns ----->
		 *
		 * => pwm_per_bit = 5 (PWM length = 50 ns)
		 *
		 * An extra loop is need to check which pwm_per_bit also fits
		 * arbitration rate.
		 *
		 * xl_data = 2 Mbps => mod(500, 4) == 0
		 *
		 *      PWM |  1 |  2 |  3 |  4 |
		 *
		 * => pwm_per_bit = 4 (PWM length = 125 ns)
		 *
		 * But also:
		 *
		 * xl_data = 2 Mbps => mod(500, 5) == 0
		 *
		 *      PWM | 1 | 2 | 3 | 4 | 5 |
		 *
		 * data bit |                   |
		 *          <------ 250 ns ----->
		 *
		 * => pwm_per_bit = 5 (PWM length = 100 ns)
		 *
		 * An extra loop is need to check which pwm_per_bit also fits
		 * arbitration rate.
		 */
		int got_it = 0;

		for (pwm_per_bit = pwm_per_bit_min;
				pwm_per_bit < pwm_per_bit_max;
							pwm_per_bit++) {
			u32 pwm_len = xl_bit_time / pwm_per_bit;
			if (pwm_len < PWM_BIT_TIME_MIN_NS)
				break;

			got_it = !(xl_bit_time % pwm_per_bit);
			if (got_it)
				break;
		}

		/* "In case there is no integer multiples found, change the data
		 *  bit rate slightly until an integer number of PWM symbols per
		 *  data bit is found."
		 */
		if (!got_it) {
			pr_err(DEVICE_NAME
			       "%u: %s(): can't find integer multiples "
			       "to get a number of PWM per data bit. You "
			       "should slightly change the data bit rate value "
			       "of %u bps\n", dev->nMinor, __func__,
			       pxli->xl_data.bitrate);

			return -EAGAIN;
		}

		base_mtq = xl_mtq / pwm_per_bit;
	}

	/* round_up(base_mtq / 4) */
	pxli->xl_pwm.pwm_short = (base_mtq + 3) / 4;
	pxli->xl_pwm.pwm_long = base_mtq - pxli->xl_pwm.pwm_short;
	pxli->xl_pwm.pwm_offset = nom_mtq % base_mtq;

	return 0;
}

/*
 * static int pcanxl_check_pwm(struct pcandev *dev, struct pcanxl_pwm *pwm,
 * 			       u32 clk_Hz)
 */
static int pcanxl_check_pwm(struct pcandev *dev, struct pcanxl_pwm *pwm,
			    u32 clk_Hz)
{
	unsigned int pwm_max_sum, pwm_sum;

	/* if one or the other is 0, then compute its value according to the
	 * other one.
	 */
	if (!pwm->pwm_short)
		pwm->pwm_short = pwm->pwm_long / 3;

	else if (!pwm->pwm_long)
		pwm->pwm_long = 3 * pwm->pwm_short;

	else if (pwm->pwm_short >= pwm->pwm_long) {
		pr_err(DEVICE_NAME "%d: %s CAN%u %u: PWM short >= long!\n",
		       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
		       dev->adapter->index);

		return -EINVAL;
	}

	/* once pwms/pwm are ok, check if pwmo is */
	pwm_sum = pwm->pwm_short + pwm->pwm_long;
	if (pwm->pwm_offset >= pwm_sum) {
		pr_err(DEVICE_NAME "%d: %s CAN%u %u: PWM offset >= PWM(%u)!\n",
		       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
		       dev->adapter->index, pwm_sum);

		return -EINVAL;
	}

	/* period (tq) = 1 / clock_Hz
	 * pwm_short + pwm_long <= 200ns
	 */
	/* PWM symbol needs 200 ns which means 5M x PWM * per second */
	pwm_max_sum = clk_Hz / (NSEC_PER_SEC / PWM_BIT_TIME_NS);

	if (pwm_sum > pwm_max_sum) {
		pr_err(DEVICE_NAME "%d: %s CAN%u %u: PWM length %u > %u ns!\n",
		       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
		       dev->adapter->index, pwm_sum, PWM_BIT_TIME_NS);

		return -EINVAL;
	}

	return 0;
}

/*
 * int __pcanxl_check_init(struct pcandev *dev, struct pcanxl_init *pxli)
 *
 * Verify settings in struct pcanxl_init and fill defaults with their values
 */
static int __pcanxl_check_init(struct pcandev *dev, struct pcanxl_init *pxli)
{
	int use_def_nominal = !pxli->nominal.brp && !pxli->nominal.bitrate;
	int err;

#ifdef DEBUG_BITRATE
	pr_info(DEVICE_NAME "%s(L%u)\n", __func__, __LINE__);
	pcanfd_dump_bittiming(&pxli->nominal, pxli->clock_Hz);
	if (pxli->flags & PCANXL_INIT_FD)
		pcanfd_dump_bittiming(&pxli->fd_data, pxli->clock_Hz);
	if (pxli->flags & PCANXL_INIT_XL)
		pcanfd_dump_bittiming(&pxli->xl_data, pxli->clock_Hz);
#endif

	/* check init settings: */

	/* if user has not given any bitrate nor BRP, setup default
	 * settings for the nominal bitrate *and* clock.
	 */
	if (use_def_nominal) {
		pxli->clock_Hz = dev->def_init_settings.clock_Hz;
		pxli->nominal = dev->def_init_settings.nominal;

	} else {

		/* Either BRP or bitrate is correct:
		 * if user has given no clock, use device current clock
		 */
		if (!pxli->clock_Hz) {

			/* TODO:
			 * CiA CANXL guidelines and application notes 612_1
			 * Table 1 - CAN XL clock recommendations
			 *
			 * For data phase bit-rates <=	Clock
			 * <= 20 Mbit/s			160 MHz (or multiple)
			 * <= 5 Mbit/s			80 MHz (or multiple)
			 */
			pxli->clock_Hz = dev->sysclock_Hz;

		/* otherwise, check if user clock is valid. If not AND
		 * if bittiming are used, then convert them into values that
		 * match the device default clock, to be compatible with
		 * SJA1000 8 MHz clock values.
		 */
		} else {
			err = pcanxl_fix_init_clock(dev, pxli);
			if (err)
				return err;
		}

		/* be sure now that bitrate and brp,tsegx,sjw are set */
		err = pcan_bittiming_normalize(&pxli->nominal,
					       pxli->clock_Hz,
					       dev->bittiming_caps);
		if (err) {
			pr_err(DEVICE_NAME
			       "%d: error %d in user nominal bittiming:\n",
			       dev->nMinor, err);

			pcanfd_dump_bittiming(&pxli->nominal, pxli->clock_Hz);

			return err;
		}
	}

	/* At that point, pxli->clock_Hz is ok, and nominal bittiming is
	 * entirely valid, that is, nominal.brp as well as nominal.bitrate != 0
	 */
#ifdef DEBUG_OPEN
	pr_info(DEVICE_NAME "%d: opening %s CAN%u %u with nominal bittiming:\n",
		dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
		dev->adapter->index);

	pcanfd_dump_bittiming(&pxli->nominal, pxli->clock_Hz);
#endif

	/* check if fd_data bittiming capabilities are defined for that kind
	 * of device (in other words, check if that device can be opened in
	 * CAN FD mode)
	 */
	if (pxli->flags & PCANXL_INIT_FD) {

		if (!dev->fd_bittiming_caps ||
		    !(dev->features & PCAN_DEV_FD_RDY)) {

			pr_err(DEVICE_NAME "%d: %s CAN%u %u: "
			       "can't be opened in CAN-FD mode\n",
			       dev->nMinor, dev->adapter->name,
			       pcan_idx(dev)+1, dev->adapter->index);

			return -EOPNOTSUPP;
		}

		/* In that case, can't simply rely on BRP and bitrate values,
		 * because BRP == 0 here also means "use nominal BRP".
		 */
		if (!pxli->fd_data.brp)
			pxli->fd_data.brp = pxli->nominal.brp;

		if (!pcan_is_bittiming_valid(&pxli->fd_data))
			pxli->fd_data = dev->def_init_settings.fd_data;

		else {
			/* be sure that bitrate and brp,tsegx,sjw are set
			 * Note: NRZ encoding is used for FD data bitrate
			 */
			err = pcan_bittiming_normalize_ex(&pxli->fd_data,
							  pxli->clock_Hz,
							 dev->fd_bittiming_caps,
							  0,
							  pxli->nominal.brp);
			if (err) {
				pr_err(DEVICE_NAME
				       "%d: error %d in user FD data "
				       "bittiming\n", dev->nMinor, err);

				pcanfd_dump_bittiming(&pxli->fd_data,
						      pxli->clock_Hz);
				return err;
			}

			/* For CAN FD the data bitrate has to be >= the nominal
			 * bitrate
			 */
			if (pxli->fd_data.bitrate < pxli->nominal.bitrate) {
				pr_err(DEVICE_NAME
				       "%d: %s CAN%u %u FD data bitrate "
				       "(%u bps) should be greater than "
				       "nominal bitrate (%u bps)\n",
				       dev->nMinor, dev->adapter->name,
				       pcan_idx(dev)+1, dev->adapter->index,
				       pxli->fd_data.bitrate,
				       pxli->nominal.bitrate);

				return -EINVAL;
			}

			/* In theory, both BRP should be equal */
			if (pxli->fd_data.brp != pxli->nominal.brp)
				pr_warn(DEVICE_NAME "%d: %s CAN%u %u: "
					"CAN-FD mode: it's recommended to use "
					"the same BRP values for nominal and "
					"data phases\n",
					dev->nMinor, dev->adapter->name,
					pcan_idx(dev)+1, dev->adapter->index);
		}

#ifdef DEBUG_OPEN
		pr_info(DEVICE_NAME
			"%d: opening %s CAN%u %u with FD data bittiming:\n",
			dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
			dev->adapter->index);

		pcanfd_dump_bittiming(&pxli->fd_data, pxli->clock_Hz);
#endif
	}

	/* Same for CAN-XL */
	if (pxli->flags & PCANXL_INIT_XL) {

		if (!dev->xl_bittiming_caps ||
		    !(dev->features & PCAN_DEV_XL_RDY)) {

			pr_err(DEVICE_NAME "%d: %s CAN%u %u: "
			       "can't be opened in CAN-XL mode\n",
			       dev->nMinor, dev->adapter->name,
			       pcan_idx(dev)+1, dev->adapter->index);

			return -EOPNOTSUPP;
		}

		if (!pxli->xl_data.brp)
			pxli->xl_data.brp = pxli->nominal.brp;

		if (!pcan_is_bittiming_valid(&pxli->xl_data))
			pxli->xl_data = dev->def_init_settings.xl_data;

		else {
			int pwm_encoding = 0;

			/* mixed network mode */
			if (pxli->flags & PCANXL_INIT_FD) {

				/* XL CANFD implies ISO CANFD */
				pxli->flags &= ~PCANFD_INIT_FD_NON_ISO;

				/* mixed network => error signaling ON =>
				 * PHY mode switch OFF (1 & 1 not allowed)
				 */
				pxli->flags &= ~PCANXL_INIT_TMS_ON;

				if (!pcanxl_check_sspo(dev, &pxli->fd_data))
					return -EINVAL;

				if (!pcanxl_check_sspo(dev, &pxli->xl_data))
					return -EINVAL;

			/* Pure CANXL: error_signaling OFF implies no SSP bit
			 * test
			 */
			/* If TMS is on, then check PWM parameter too */
			} else if (pxli->flags & PCANXL_INIT_TMS_ON) {
				struct pcanxl_pwm *pwm = &pxli->xl_pwm;

				/* no choice: error signaling MUST be off! */
				pxli->flags |= PCANXL_INIT_ES_OFF;

				/* if neither pwms nor pml are given, then
				 * compute their default (and optimum) values
				 */
				if (!pwm->pwm_short && !pwm->pwm_long) {
					err = pcanxl_set_default_pwm(dev, pxli);
					if (err)
						return err;
				} else {
					err = pcanxl_check_pwm(dev, pwm,
							       pxli->clock_Hz);
					if (err)
						return err;
				}

				pwm_encoding = 1;
			}

			/* Pure CANXL: error_signaling OFF implies no SSP bit
			 * test
			 */
			if (pxli->flags & PCANXL_INIT_ES_OFF) {
				pxli->xl_data.ssp_offset =
					pxli->fd_data.ssp_offset =
						PCANXL_SSP_OFFSET_OFF;
			}

			/* Remove non sense flags when in XL mode */
			pxli->flags &= ~PCANFD_INIT_STD_MSG_ONLY;

			/* be sure that bitrate and brp,tsegx,sjw are set */
			err = pcan_bittiming_normalize_ex(&pxli->xl_data,
							  pxli->clock_Hz,
							 dev->xl_bittiming_caps,
							  pwm_encoding,
							  pxli->nominal.brp);
			if (err) {
				pr_err(DEVICE_NAME
				       "%d: error %d in user XL data "
				       "bittiming\n", dev->nMinor, err);

				pcanfd_dump_bittiming(&pxli->xl_data,
						      pxli->clock_Hz);
				return err;
			}

			/* be sure to use the nominal BRP value */
			if (pxli->xl_data.brp != pxli->nominal.brp) {
				pr_err(DEVICE_NAME "%d: %s CAN%u %u: "
				       "nominal BRP %u different from XL "
				       "data BRP %u\n",
					dev->nMinor, dev->adapter->name,
					pcan_idx(dev)+1, dev->adapter->index,
					pxli->nominal.brp, pxli->xl_data.brp);

				return -EINVAL;
			}

			/* For CAN XL the data bitrate has to be >= 2 x the
			 * nominal bitrate
			 */
			if (pxli->xl_data.bitrate < 2 * pxli->nominal.bitrate) {
				pr_err(DEVICE_NAME
				       "%d: %s CAN%u %u XL data bitrate "
				       "(%u bps) should be greater than "
				       "2 x nominal bitrate (%u bps)\n",
				       dev->nMinor, dev->adapter->name,
				       pcan_idx(dev)+1, dev->adapter->index,
				       pxli->xl_data.bitrate,
				       pxli->nominal.bitrate);

				return -EINVAL;
			}

		}

#ifdef DEBUG_OPEN
		pr_info(DEVICE_NAME
			"%d: opening %s CAN%u %u with XL data bittiming:\n",
			dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
			dev->adapter->index);

		pcanfd_dump_bittiming(&pxli->xl_data, pxli->clock_Hz);
#endif
	}

	return 0;
}

#ifdef DEBUG_OPEN
static inline int _pcanxl_check_init(unsigned int l, struct pcandev *dev,
				     struct pcanxl_init *pxli)
{
	const char *fn = strrchr(__FILE__, '/');
	pr_info(DEVICE_NAME "%u: %s L%u: pcanxl_check_init()\n",
		dev->nMinor, fn ? fn+1 : __FILE__, l);
	return __pcanxl_check_init(dev, pxli);
}

#define pcanxl_check_init(d, i)	_pcanxl_check_init(__LINE__, d, i)
#else
#define pcanxl_check_init(d, i)	__pcanxl_check_init(d, i)
#endif

/*
 * int pcanxl_dev_open(struct pcandev *dev, struct pcanxl_init *pxli)
 *
 * open() path
 */
int pcanxl_dev_open(struct pcandev *dev, struct pcanxl_init *pxli)
{
	int err;

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(pcan%d): btr=%u,%u,%u\n",
		__func__, dev->nMinor, pxli->nominal.bitrate,
		pxli->fd_data.bitrate, pxli->xl_data.bitrate);
#endif

	if (pxli->flags & PCANFD_INIT_BTR_NOK) {
		err = pcanxl_check_init(dev, pxli);
		if (err)
			return err;

		/* no need to check them next */
		pxli->flags &= ~PCANFD_INIT_BTR_NOK;
	}

	return __pcanxl_dev_open(dev, pxli);
}

#ifdef PCANFD_IGNORE_SAME_BITTIMING
/*
 * Compare bitrate settings according to the following criteria:
 *
 * - clock MUST be the same. If clock_Hz is 0, then default device clock is
 *   used for comparison.
 *
 * Return:
 *
 * < 0 if error
 * == 0 if bittiming settings are equal
 * > 0 if bittiming settings are different
 */
static int pcanxl_are_bittiming_equal(struct pcandev *dev,
				      struct pcanxl_init *pfi1,
				      struct pcanxl_init *pfi2)
{
	int err;

	/* first, be sure that all settings are filled and correct */
	if (pfi1->flags & PCANFD_INIT_BTR_NOK) {
		err = pcanxl_check_init(dev, pfi1);
		if (err)
			return err;

		/* no need to check them next */
		pfi1->flags &= ~PCANFD_INIT_BTR_NOK;
	}

	if (pfi2->flags & PCANFD_INIT_BTR_NOK) {
		err = pcanxl_check_init(dev, pfi2);
		if (err)
			return err;

		/* no need to check them next */
		pfi2->flags &= ~PCANFD_INIT_BTR_NOK;
	}

#ifdef DEBUG_OPEN
	pr_info(DEVICE_NAME ": %s() comparing nominal:\n", __func__);
	pcanfd_dump_bittiming(&pfi1->nominal, pfi1->clock_Hz);
	pcanfd_dump_bittiming(&pfi2->nominal, pfi1->clock_Hz);
#endif

	/* now compare settings */
	if (pfi1->clock_Hz != pfi2->clock_Hz)
		return 1;

	if (memcmp(&pfi1->nominal, &pfi2->nominal,
		   sizeof(struct pcan_bittiming)))
		return 2;

	if (pfi1->flags & PCANXL_INIT_FD) {

		if (!(pfi2->flags & PCANXL_INIT_FD))
			return 4;

		if (pfi1->flags & PCANFD_INIT_FD_NON_ISO) {
			if (!(pfi2->flags & PCANFD_INIT_FD_NON_ISO))
				return 11;
		} else if (pfi2->flags & PCANFD_INIT_FD_NON_ISO)
			return 12;

#ifdef DEBUG_OPEN
		pr_info(DEVICE_NAME ": %s() comparing FD data:\n", __func__);
		pcanfd_dump_bittiming(&pfi1->fd_data, pfi1->clock_Hz);
		pcanfd_dump_bittiming(&pfi2->fd_data, pfi2->clock_Hz);
#endif
		if (memcmp(&pfi1->fd_data, &pfi2->fd_data,
			   sizeof(struct pcan_bittiming)))
			return 13;

	} else if (pfi2->flags & PCANXL_INIT_FD)
		return 4;

	if (pfi1->flags & PCANXL_INIT_XL) {

		if (!(pfi2->flags & PCANXL_INIT_XL))
			return 8;

		if (pfi1->flags & PCANXL_INIT_TMS_ON) {
			if (!(pfi2->flags & PCANXL_INIT_TMS_ON))
				return 9;
		} else if (pfi2->flags & PCANXL_INIT_TMS_ON)
			return 9;

		if (pfi1->flags & PCANXL_INIT_ES_OFF) {
			if (!(pfi2->flags & PCANXL_INIT_ES_OFF))
				return 10;
		} else if (pfi2->flags & PCANXL_INIT_ES_OFF)
			return 10;

#ifdef DEBUG_OPEN
		pr_info(DEVICE_NAME ": %s() comparing XL data:\n", __func__);
		pcanfd_dump_bittiming(&pfi1->xl_data, pfi1->clock_Hz);
		pcanfd_dump_bittiming(&pfi2->xl_data, pfi2->clock_Hz);
#endif
		if (memcmp(&pfi1->xl_data, &pfi2->xl_data,
			   sizeof(struct pcan_bittiming)))
			return 17;

		if (memcmp(&pfi1->xl_pwm, &pfi2->xl_pwm,
			   sizeof(struct pcanxl_pwm)))
			return 18;

	} else if (pfi2->flags & PCANXL_INIT_XL)
		return 8;

	if (pfi1->flags & PCANFD_INIT_LISTEN_ONLY) {
		if (!(pfi2->flags & PCANFD_INIT_LISTEN_ONLY))
			return 5;
	} else if (pfi2->flags & PCANFD_INIT_LISTEN_ONLY)
		return 5;

	return 0;
}
#endif

/*
 * int pcanxl_ioctl_set_init(struct pcandev *dev, struct pcanxl_init *pxli)
 *
 * User-only.
 *
 * Called only from:
 *
 * - ioctl(PCAN_INIT)
 * - ioctl(PCANFD_SET_INIT)
 * - ioctl(PCANXL_SET_INIT)
 * - write("i xxx")
 */
int pcanxl_ioctl_set_init(struct pcandev *dev, struct pcanxl_init *pxli)
{
	int err = 0;

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(pcan%d bus=%u): nOpenPaths=%d\n", __func__,
		dev->nMinor, dev->bus_state, dev->nOpenPaths);
#endif

	if ((dev->flags & PCAN_DEV_OPENED) && (dev->nOpenPaths > 1)) {
		pr_err(DEVICE_NAME "%d: %s CAN%u %u "
		       "can't be initialized when opened %d time\n",
		       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
		       dev->adapter->index, dev->nOpenPaths);

		err = -EBUSY;
		goto lbl_exit;
	}

	/* sanitize */
	if (!(dev->features & PCAN_DEV_BUSLOAD_RDY))
		pxli->flags &= ~PCANFD_INIT_BUS_LOAD_INFO;

	/* force bittiming checking and remember init comes from userland */
	pxli->flags |= PCANFD_INIT_BTR_NOK|PCANFD_INIT_USER;

#ifdef PCANFD_IGNORE_SAME_BITTIMING
	/* if the device is not yet configured then do it */
	if (!(dev->flags & PCAN_DEV_OPENED))
		goto lbl_do_reset;

	/* ignoring same bittimings needs of course that the state of the bus
	 * is correct. Unfortunately, it might be UNKNOWN if ioctl(SET_INIT)
	 * is called next to open().
	 */
	if (dev->bus_state > PCANFD_ERROR_ACTIVE)
		goto lbl_do_reset;

	/* if bittiming are different, donot flush fifos but reset controller
	 * only; Otherwise, return the error.
	 */
	err = pcanxl_are_bittiming_equal(dev, &dev->init_settings, pxli);
	if (err) {
		if (err > 0) {
#ifdef DEBUG_OPEN
			pr_info(DEVICE_NAME
				"%u: bittiming specs different (err %d)\n",
				dev->nMinor, err);
#endif
			goto lbl_do_reset;
		}

		return err;
	}

	/* bittiming are equal. If controller has been opened WITHOUT
	 * bus load option, and if new init wants them, then controller
	 * must be closed then open.
	 */
	if (!(dev->features & PCAN_DEV_BUSLOAD_RDY) ||
	    (dev->init_settings.flags & PCANFD_INIT_BUS_LOAD_INFO) ||
	    !(pxli->flags & PCANFD_INIT_BUS_LOAD_INFO)) {

		/* Don't need to change the controller state. Just
		 * update the device init_settings fields with
		 * other initialization settings that don't deal with
		 * the controller itself.
		 */
		pcanxl_copy_init(&dev->init_settings, pxli);

#ifndef NETDEV_SUPPORT
		/* in case controler is not changed, then donot reset rx fifo
		 * either so that any event that might have come in between
		 * won't be lost...
		 */

		/* send back a STATUS[bus_state] */
		pcan_post_bus_state(dev);
#endif
		return 0;
	}

lbl_do_reset:
#endif

	/* flush Tx fifo (only): Rx fifo may contain unread msgs) */
	pcan_kfifo_reset(&dev->tx_fifo);

	dev->wCANStatus &= ~CAN_ERR_XMTFULL;

	/* do reset the device */
	pcanxl_dev_reset(dev);

#ifndef NETDEV_SUPPORT
#ifdef PCAN_USES_O_ACCMODE_HACK
	/* User sets a bitrate that is not the current/default one.
	 * Unfortunately, between open() and this initialization, one or several
	 * msgs may already have been pushed into rx fifo. The problem is
	 * if we don't reset it now, the same STATUS[ACTIVE] may be present
	 * twice (because all "dev->posted" fields have been reset by
	 * pcanxl_dev_reset() ->...-> pcan_init_session_counters()).
	 */
	pcan_kfifo_reset(&dev->rx_fifo);

	dev->wCANStatus &= ~CAN_ERR_OVERRUN;
#else
	/* When O_ACCMODE is not handled by pcan, then donot reset Rx fifo:
	 * user may read twice the same STATUS but frames read between
	 * open() and the following new init won't be lost.
	 */
#endif
#endif

	/* then reopen it with the user settings */
	err = pcanxl_dev_open(dev, pxli);

lbl_exit:
	return err;
}

int pcanxl_ioctl_get_init(struct pcandev *dev, struct pcanxl_init *pxli)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif

	pcanxl_copy_init(pxli, &dev->init_settings);

	return 0;
}

int pcanxl_ioctl_reset(struct pcandev *dev, unsigned long flags)
{
	pcan_lock_irqsave_ctxt irq_flags;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d, flgs=%08lxh)\n",
		__func__, dev->nMinor, flags);
#endif

	dev->lock_irq(dev, &irq_flags);

	if (flags & PCANFD_RESET_RXFIFO) {
#ifndef NETDEV_SUPPORT
		pcan_kfifo_reset(&dev->rx_fifo);
#endif
		dev->wCANStatus &= ~CAN_ERR_OVERRUN;
	}

	if (flags & PCANFD_RESET_TXFIFO) {

		/* lock the access to the fifo because interrupts are enabled */
		pcan_kfifo_reset(&dev->tx_fifo);

		dev->wCANStatus &= ~CAN_ERR_XMTFULL;
	}

	if (flags & PCANFD_RESET_CTRLR) {

		if (dev->device_reset) {

			/* consider that this soft reset also resets total
			 * stats
			 */
			pcan_stats_reset(&dev->total_stats);

			dev->rx_error_counter = 0;
			dev->tx_error_counter = 0;

			dev->time_sync.ts_fixed = 0;

			pcan_set_tx_engine(dev, TX_ENGINE_STOPPED);

			pcan_set_bus_state(dev, PCANFD_UNKNOWN);

			dev->unlock_irq(dev, &irq_flags);

			return dev->device_reset(dev);
		} else {
			err = -ENOTSUPP;
		}
	}

	dev->unlock_irq(dev, &irq_flags);

	return err;
}

/* add a message filter_element into the filter chain or delete all
 * filter_elements
 */
int pcanxl_ioctl_add_filter(struct pcandev *dev, struct pcanfd_msg_filter *pf)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* filter == NULL -> delete the filter_elements in the chain */
	if (!pf) {
		pcan_delete_filter_all(dev->filter);
		return 0;
	}

	return pcan_add_filter(dev->filter,
		               pf->id_from, pf->id_to, pf->msg_flags);
}

/* add several message filter_element into the filter chain.
 */
int pcanxl_ioctl_add_filters(struct pcandev *dev,
			     struct pcanfd_msg_filters *pfl)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* filter == NULL -> delete the filter_elements in the chain */
	if (!pfl) {
		pcan_delete_filter_all(dev->filter);
		return 0;
	}

	return pcan_add_filters(dev->filter, pfl->list, pfl->count);
}

/* get several message filter_element from the filter chain.
 */
int pcanxl_ioctl_get_filters(struct pcandev *dev,
			     struct pcanfd_msg_filters *pfl)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* filter == NULL -> return the current nb of filters in the chain */
	if (!pfl)
		return pcan_get_filters_count(dev->filter);

	err = pcan_get_filters(dev->filter, pfl->list, pfl->count);
	if (err < 0) {
		pfl->count = 0;
		return err;
	}

	pfl->count = err;
	return 0;
}

int pcanxl_ioctl_get_state(struct pcandev *dev, struct pcanfd_state *pfds)
{
	int len;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	pfds->ver_major = PCAN_VERSION_MAJOR;
	pfds->ver_minor = PCAN_VERSION_MINOR;
	pfds->ver_subminor = PCAN_VERSION_SUBMINOR;

	pcanxl_to_timeval(&pfds->tv_init, &dev->init_timestamp);

	pfds->bus_state = dev->bus_state;
	pfds->device_id = dev->device_alt_num;

	pfds->open_counter = dev->nOpenPaths;
	pfds->filters_counter = pcan_get_filters_count(dev->filter);

	pfds->hw_type = dev->wType;
	pfds->channel_number = pcan_idx(dev);

#ifdef USB_SUPPORT
	if (dev->wType == HW_USB_X6) {
		struct pcan_usb_interface *usb_if;

		usb_if = pcan_usb_get_if(dev);

		pfds->channel_number += usb_if->index * usb_if->can_count;
	}
#endif
 
	pfds->can_status = dev->wCANStatus;
	pfds->bus_load = dev->bus_load;

	pfds->tx_pending_msgs = pcan_kfifo_count(&dev->tx_fifo);
	len = kfifo_len(&dev->tx_fifo.kfifo);

	/* With CAN-XL, can only give an estimation of the maximum number
	 * of msgs
	 */
	pfds->tx_max_msgs = len ?
		(kfifo_size(&dev->tx_fifo.kfifo) * pfds->tx_pending_msgs) / len:
		0;

#ifndef NETDEV_SUPPORT
	pfds->rx_pending_msgs = pcan_kfifo_count(&dev->rx_fifo);
	len = kfifo_len(&dev->rx_fifo.kfifo);
	pfds->rx_max_msgs = len ?
		(kfifo_size(&dev->rx_fifo.kfifo) * pfds->rx_pending_msgs) / len:
		0;
#else
	pfds->rx_max_msgs = 0;
	pfds->rx_pending_msgs = 0;
#endif
	pfds->tx_error_counter = dev->tx_error_counter;
	pfds->rx_error_counter = dev->rx_error_counter;

	pfds->tx_frames_counter = dev->total_stats.tx.frames;
	pfds->rx_frames_counter = dev->total_stats.rx.frames;

	pfds->host_time_ns = dev->time_sync.tv_ns;
	pfds->hw_time_ns = dev->time_sync.ts_ns;

	return 0;
}

/*
 * static int pcanxl_recv_msg(struct pcandev *dev, struct pcanxl_rxmsg *rx,
 * 			      void __user *udata, struct pcanusr *ctx)
 *
 * Note: each rx->msg.data_len MUST be populated with the available space in
 * 	 the rx->msg.data[] array.
 *
 * @RETURN:
 *
 * >= 0	if a message has been read from device Rx fifo
 * < 0	in case of error
 */
static int pcanxl_recv_msg(struct pcandev *dev, struct pcanxl_rxmsg *rx,
			   void __user *udata, struct pcanusr *ctx)
{
#ifdef NETDEV_SUPPORT
	return -EAGAIN;		/* be compatible with old behaviour */
#else
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%u): is_plugged=%d nOpenPaths=%d\n",
		__func__, dev->nMinor, dev->is_plugged, dev->nOpenPaths);
#endif
	do {
		/* if the device has been plugged out while waiting,
		 * or if any task is closing it
		 */
		if (!dev->is_plugged || !dev->nOpenPaths) {
			err = -ENODEV;
			break;
		}

		/* get data from fifo
		 * support nonblocking read if requested
		 */
		err = (udata) ? pcan_rxfifo_out_user(dev, rx, udata)
			      : pcan_rxfifo_out(dev, rx, rx->msg.data);

		/* got a msg from rx fifo */
		if (err >= 0) {

			pcan_sync_timestamps(dev, rx);

			/* CAN_ERR_OVERRUN is now entirely handled in
			 * pcan_kfifo.c
			 */
#ifdef pcan_event_clear
			/* if rx fifo is now empty, then the corresponding event
			 * should be cleared now.
			 */
			if (!err)
				pcan_event_clear(&dev->in_event);
#endif

			break;
		}

		if (err != -ENODATA) {

			pr_err(DEVICE_NAME "%d: %s CAN%u %u: "
			       "Rx fifo out-of-sync! (err %d)\n",
			       dev->nMinor, dev->adapter->name, pcan_idx(dev)+1,
			       dev->adapter->index, err);
			break;
		}

		err = -EAGAIN;

		if (!ctx || (ctx->open_flags & O_NONBLOCK)) {
#ifdef PCAN_NO_EWOULDBLOCK
			/* ioctl(PCAN_READ_MSG) = 0 */
			err = pcan_init_rxmsg(dev, rx,
					      PCANFD_TYPE_STATUS,
					      PCANFD_RX_EMPTY,
					      PCANFD_ERROR_INTERNAL);
#else
			/* ioctl(PCAN_READ_MSG) = -EWOULDBLOCK */
			break;
#endif
		}

		/* check whether the task is able to wait:
		 * Linux: always!
		 * RT: depends on the RT context of the running task
		 */
		if (!pcan_task_can_wait()) {
			pr_info(DEVICE_NAME
				": %s(%u): ABNORMAL task unable to wait!\n",
				__func__, __LINE__);
			break;
		}

		/* sleep until some msg is available. */
#ifdef DEBUG_WAIT_RD
		pr_info(DEVICE_NAME
			": %s(%u): waiting for some msgs to read...\n",
			__func__, __LINE__);
#endif

		/* task might go to sleep: unlock current dev */
		pcan_unlock_dev(dev);

		/* wait for some msg in the Rx queue.
		 *
		 * Note: ^C may occur while waiting. In RT, preemption can 
		 * schedule another task that might call close() while we're
		 * always waiting here.
		 * - If the event is destroyed by some other task, the below
		 *   call fails with err=-EIDRM(43).
		 * - if some other task deletes this waiting task, this tasks
		 *   is first unblocked, thus err=-EINTR(4).
		 */
		err = pcan_event_wait(dev->in_event,
					!dev->is_plugged ||
					pcan_kfifo_count(&dev->rx_fifo));

		pcan_lock_dev(dev);

#ifdef DEBUG_WAIT_RD
		pr_info(DEVICE_NAME
			": end of waiting for rx fifo not empty: err=%d\n",
			err);
#endif

	} while (err >= 0);

	/* Note: ERESTARTSYS == 512 */
	return (err == -ERESTARTSYS) ? -EINTR : err;
#endif
}

/* this function SHOULD be used with dev->isr_lock locked */
int __pcan_dev_start_writing(struct pcandev *dev, struct pcanusr *ctx)
{
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME
		": %s(pcan%u) flags=%08xh tx_engine_state=%u bus=%d\n",
		__func__, dev->nMinor, dev->flags, dev->locked_tx_engine_state,
		dev->bus_state);
#endif

	/* no need to start anything in that context */
	if (!(dev->flags & PCAN_DEV_OPENED)) {
		return -ENETDOWN;
	}

	/* Hem... this should be tested here. But PCAN-USB takes up to ~900 ms
	 * to notify from ERROR_ACTIVE. See also handle_error_active() in
	 * src/pcan_main.c
	 */
	if (dev->bus_state == PCANFD_UNKNOWN) {
		return 0;
	}

	/* if we just put the 1st message (=the fifo was empty), we can start
	 * writing on hardware if it is ready for doing this.
	 */
	if (dev->locked_tx_engine_state == TX_ENGINE_STOPPED) {
		err = dev->device_write(dev, ctx);
	}

	/* since v8.8, device_write() should not return -ENODATA except if no
	 * data has been read from the Tx fifo. Since __pcan_dev_start_writing()
	 * is called after having put a frame into the Tx fifo, err
	 * cannot be -ENODATA.
	 */
	return (err == -ENODATA) ? 0 : err;
}

static int pcanxl_start_tx_engine(struct pcandev *dev, struct pcanusr *ctx)
{
	pcan_lock_irqsave_ctxt lck_ctx;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d bus_state=%u)\n",
		__func__, dev->nMinor, dev->bus_state);
#endif

	dev->lock_irq(dev, &lck_ctx);

	/* if can device ready to send, start writing */
	err = __pcan_dev_start_writing(dev, ctx);

	dev->unlock_irq(dev, &lck_ctx);

	return err;
}

/*
 * Return:
 * > 0		Tx fifo number of items
 * 0		if nothing done in Tx fifo.
 * < 0		An error code:
 *		-EBADMSG	if sending CAN FD msg on CAN 2.0 settings
 *				if sending extended id while std msg allowed
 *		-ENODEV		if device no more plugged
 *		-ENETDOWN	if bus off
 *		-EAGAIN		if Tx fifo full
 *		-EINTR		if wait() has been interrupted
 */
static int pcanxl_send_msg(struct pcandev *dev, struct pcanxl_txmsg *tx,
			   void __user *udata_ptr, struct pcanusr *ctx)
{
	int err;

	switch (tx->msg.type) {

	case PCANXL_TYPE_CANXL:
		/* accept such messages for devices that have been initialized
		 * for CAN-XL.
		 */
		if ((dev->init_settings.flags & PCANXL_INIT_XL) &&
				(tx->msg.data_len <= PCANXL_MAXDATALEN))
			break;

		/* Ok to be permissive *BUT* force the message to be
		 * CAN FD only, that is, CAN-XL specific flags won't be
		 * taken into account next.
		 */
		tx->msg.type = PCANFD_TYPE_CANFD_MSG;

		/* fall through */
		fallthrough;
	case PCANFD_TYPE_CANFD_MSG:

		/* accept such messages for devices that have been initialized
		 * for CAN-FD.
		 */
		if ((dev->init_settings.flags & PCANXL_INIT_FD) &&
				(tx->msg.data_len <= PCANFD_CANFD_MAXDATALEN))
			break;

		/* Ok to be permissive *BUT* force the message to be
		 * CAN 2.0 only, that is, CAN-FD specific flags won't be
		 * taken into account next.
		 */
		tx->msg.type = PCANFD_TYPE_CAN20_MSG;

		/* fall through */
		fallthrough;
	case PCANFD_TYPE_CAN20_MSG:
		if (tx->msg.data_len <= PCANFD_CAN20_MAXDATALEN)
			break;

		/* fall through */
		fallthrough;
	default:
		pr_err(DEVICE_NAME
			": trying to send invalid msg (type=%xh len=%d)\n",
			tx->msg.type, tx->msg.data_len);

		return -EBADMSG;
	}

	/* filter extended data if initialized to standard only
	 * SGr note: no need to wait for doing such a test...
	 */
	if ((dev->init_settings.flags & PCANFD_INIT_STD_MSG_ONLY)
	   && ((tx->msg.flags & PCANFD_MSG_EXT) || (tx->msg.id > 2047))) {

		pr_err(DEVICE_NAME
			": trying to send ext msg %xh while not setup for\n",
			tx->msg.id);
		return -EBADMSG;
	}

	if (!(dev->features & PCAN_DEV_SLF_RDY)
	  && (tx->msg.flags & PCANFD_MSG_SLF)) {
		pr_err(DEVICE_NAME
			": trying to send unsupported slf msg %xh\n",
			tx->msg.id);
		return -EBADMSG;
	}

	if (!(dev->features & PCAN_DEV_SNG_RDY)
	  && (tx->msg.flags & PCANFD_MSG_SNG)) {
		pr_err(DEVICE_NAME
			": trying to send unsupported single-shot msg %xh\n",
			tx->msg.id);
		return -EBADMSG;
	}

	do {
		unsigned int sizeof_tx;

		/* if the device has been plugged out while waiting,
		 * or if any task is closing it
		 */
		if (!dev->is_plugged || !dev->nOpenPaths) {
			err = -ENODEV;
			break;
		}

		/* no need to write in case of BUS_OFF state */
		if (dev->bus_state == PCANFD_ERROR_BUSOFF) {
			err = -ENETDOWN;
			break;
		}

		/* put data into fifo */
		err = (udata_ptr) ? pcan_txfifo_in_user(dev, tx, udata_ptr)
				  : pcan_txfifo_in(dev, tx, tx->msg.data);
		if (err > 0)
			break;

		/* Tx FIFO is full. If bus_state is in PASSIVE state, then no
		 * need to wait (again)
		 */
		if (dev->bus_state == PCANFD_ERROR_PASSIVE) {
			/* ESHUTDOWN	Cannot send after... */
			err = -ESHUTDOWN;
			break;
		}

		err = -EAGAIN;

#ifdef pcan_event_clear
		/* tx fifo is now full, then the corresponding writing event
		 * should be cleared now.
		 */
		pcan_event_clear(&dev->out_event);
#endif

		/* support nonblocking write if requested */
		if (!ctx || (ctx->open_flags & O_NONBLOCK)) {
			/* v9: DON'T post DRV_ERR=TX_OVRFL anymore because:
			 * 1 - kfifo doesn't enable to patch last pushed item,
			 *     therefore, this STATUS msg will quickly fill
			 *     Rx FIFO
			 * 2 - OVERFLOW message means that a msg has been lost
			 *     which is not the case here!
			 */
			break;
		}

		if (!pcan_task_can_wait()) {
			pr_info(DEVICE_NAME
				": %s(%u): ABNORMAL task unable to wait!\n",
				__func__, __LINE__);
			break;
		}

		/* check Tx engine whether it is running before going asleep
		 * (Note: useful only if one has sent more msgs than Tx fifo
		 * size, at once)
		 */
		pcanxl_start_tx_engine(dev, ctx);

		/* sleep until space is available. */
		sizeof_tx = sizeof(*tx) + tx->msg.data_len;
#ifdef DEBUG_WAIT_WR
		pr_info(DEVICE_NAME
			"%d: waiting %u ms for %u bytes free space to write\n",
			dev->nMinor, PCANFD_TIMEOUT_WAIT_FOR_WR, sizeof_tx);
#endif

		/* task might go to sleep: unlock current dev */
		pcan_unlock_dev(dev);

		/* wait up to 100 ms. for some room in the Tx queue.
		 *
		 * some logs:
		 *
[ 7977.396005] pcan: pcanxl_send_msg(359): waiting for some free space to write...
...
[ 7977.400974] pcan: CAN1 lnk=1 signaling writing task...
...
[ 7977.400977] pcan: end of waiting for tx fifo not full: err=0
		 *
		 * Note: ^C may occur while waiting. In RT, preemption can 
		 * schedule another task that might call close() while we're
		 * always waiting here.
		 * - If the event is destroyed by some other task, the below
		 *   call fails with err=-EIDRM(43).
		 * - if some other task deletes this waiting task, this tasks
		 *   is first unblocked, thus err=-EINTR(4).
		 */
		err = pcan_event_wait_timeout(dev->out_event,
					!dev->is_plugged ||
					pcan_txfifo_avail(dev) >= sizeof_tx ||
					dev->bus_state >= PCANFD_ERROR_PASSIVE,
					PCANFD_TIMEOUT_WAIT_FOR_WR);

		/* lock the device again */
		pcan_lock_dev(dev);

#ifdef DEBUG_WAIT_WR
		pr_info(DEVICE_NAME
			": end of waiting for tx fifo not full: err=%d\n",
			err);
#endif

	} while (err >= 0);

	return (err == -ERESTARTSYS) ? -EINTR : err;
}

/*
 * int pcanxl_ioctl_recv_msg(struct pcandev *dev, struct pcanxl_rxmsg *rx,
 *			     void __user *udata, struct pcanusr *ctx)
 * @RETURN:
 *
 * == 0	if a message has been read from device Rx fifo
 * < 0	in case of error

 */
int pcanxl_ioctl_recv_msg(struct pcandev *dev, struct pcanxl_rxmsg *rx,
			  void __user *udata, struct pcanusr *ctx)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s()\n", __func__);
#endif

	err = pcanxl_recv_msg(dev, rx, udata, ctx);

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(): returns %d\n", __func__, err);
#endif

	if (err >= 0) {
		switch (rx->msg.type) {
		case PCANFD_TYPE_STATUS:
			if ((rx->msg.flags & PCANFD_ERROR_INTERNAL) &&
			    (rx->msg.id == PCANFD_RX_OVERFLOW)) {
				rx->msg.flags |= PCANFD_OVRCNT;
				rx->msg.ctrlr_data[PCANFD_RXERRCNT] =
				       dev->session_stats.rx_lost;

				dev->session_stats.rx_lost = 0;
			}
			break;
		}

		err = 0;
	}

	return err;
}

/*
 * int pcanxl_ioctl_recv_msgs(struct pcandev *dev, struct pcanxl_rxmsgs_fd *pl,
 *			      struct pcanusr *ctx)
 *
 * Note: each .msg.data_len of pl->list[] array MUST be populated with the
 *       available space in .msg.data[] array.
 */
int pcanxl_ioctl_recv_msgs(struct pcandev *dev, struct pcanxl_rxmsgs_fd *pl,
			   struct pcanusr *ctx)
{
	struct pcanxl_rxmsg_fd *rx;
	int err = 0, n = pl->count, saved_flags = ctx->open_flags;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(count=%u)\n", __func__, n);
#endif

	rx = pl->list;

	for (pl->count = 0; pl->count < n; pl->count++) {
		err = pcanxl_recv_msg(dev, (struct pcanxl_rxmsg *)rx, NULL,
				      ctx);
		if (err < 0)
			break;

		/* the task won't block anymore since at least one msg has been
		 * read.
		 */
		ctx->open_flags |= O_NONBLOCK;
		rx++;
	}

	/* restore original flags asap */
	ctx->open_flags = saved_flags;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(count=%u): got %u msgs (err %d)\n",
			__func__, n, pl->count, err);
#endif
	return (pl->count > 0) ? 0 : err;
}

/*
 * int pcanxl_ioctl_send_msg(struct pcandev *dev, struct pcanxl_txmsg *tx,
 *			     void __user *udata_ptr, struct pcanusr *ctx)
 */
int pcanxl_ioctl_send_msg(struct pcandev *dev, struct pcanxl_txmsg *tx,
			  void __user *udata_ptr, struct pcanusr *ctx)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(type=%d data_len=%d)\n",
		__func__, tx->msg.type, tx->msg.data_len);
#endif

	err = pcanxl_send_msg(dev, tx, udata_ptr, ctx);

	/* start Tx engine only if Tx fifo is not empty */
	if (err > 0)
		err = pcanxl_start_tx_engine(dev, ctx);

	return err >= 0 ? 0 : err;
}

/*
 * int pcanxl_ioctl_send_msgs(struct pcandev *dev, struct pcanxl_txmsgs_fd *pl,
 *			      struct pcanusr *ctx)
 */
int pcanxl_ioctl_send_msgs(struct pcandev *dev, struct pcanxl_txmsgs_fd *pl,
			   struct pcanusr *ctx)
{
	struct pcanxl_txmsg_fd *tx;
	int err = 0, msgs_queued = 0, n = pl->count;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(count=%u)\n", __func__, n);
#endif

	tx = pl->list;
	for (pl->count = 0; pl->count < n; pl->count++) {
		err = pcanxl_send_msg(dev, (struct pcanxl_txmsg *)tx, NULL,
				      ctx);

		/* don't stop sending if error is related to the msg only */
		if (err < 0) {
			if (err != -EBADMSG)
				break;
		} else {
			msgs_queued += err;
		}

		tx++;
	}

#ifdef DEBUG
	pr_info(DEVICE_NAME ": %s(count=%u): queued %u msgs\n",
		__func__, n, msgs_queued);
#endif

	/* if at least ONE message has been enqueued */
	if (msgs_queued > 0) {

		/* if we just put the 1st message (=the fifo was empty),
		 * we can start writing on hardware if it is ready for doing
		 * this.
		 */
		err = pcanxl_start_tx_engine(dev, ctx);
	}

	return msgs_queued ? 0 : err;
}

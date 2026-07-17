/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcan_usbfd.c - the inner parts for PCAN-USB (Pro) FD support
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
 */
/* #define DEBUG */
/* #undef DEBUG */

#include "src/pcan_common.h"

#ifdef USB_SUPPORT

#ifdef DEBUG_USB_LITE
#define DEBUG_CMD
#define DEBUG_RX_PATH
#define DEBUG_TX_PATH
#ifdef DEBUG_USB
#define DEBUG_TRACE
#define DEBUG_RX_PATH_FULL
#define DEBUG_TX_PATH_FULL
#endif
#endif

#include "src/pcanxl_usb.h"
#include "src/pcanxl_usb_fw.h"

#ifdef NETDEV_SUPPORT
#include "src/pcan_netdev.h"		/* for hotplug pcan_netdev_register() */
#else
#include <linux/can/dev.h>
#endif

static int pcan_usbxl_devices = 0;

static inline int pcan_usbxl_send_ucan_cmd(struct pcandev *dev)
{
#ifdef DEBUG_CMD
	dump_mem("sent cmd", dev->ucan.cmd_head, dev->ucan.cmd_len);
#endif
	/* same inherited function to send a cmd to uCAN-XL core */
	return dev->ucan.ovr_ops.send_cmd(dev);
}

#ifdef DEBUG_RX_PATH
static int pcan_usbxl_handle_msg(struct ucan_engine *ucan, void *msg_addr)
{
	int err = canxl_handle_msg(ucan, msg_addr);

	if (err < 0)
		canxl_dump_rx_msg("unhandled CANXL-USB rx msg", msg_addr);

	return err;
}
#endif

/*
 * static int pcan_usbxl_encode_tx_msg(struct pcandev *dev, u8 *b_addr,
 *				       int b_size)
 *
 * PCAN-USBXL specific encoder: a transport header must be added to the
 * buffer.
 */
static int pcan_usbxl_encode_msgs_buffer(struct pcandev *dev, u8 *b_addr,
					 int *b_size)
{
	struct canxl_usb_tp_hdr *tp_hdr;
	int pl_size = *b_size;
	int err;

#ifdef DEBUG_TX_PATH
	pr_info(DEVICE_NAME ": %s(%s CAN%u, b_size=%d)\n",
		__func__, dev->adapter->name, pcan_idx(dev)+1, *b_size);
#endif

	if (pl_size < sizeof(*tp_hdr)) {
		pr_err(DEVICE_NAME ": %s(): "
			"%u bytes left too short for transport header\n",
			__func__, pl_size);

		return -ENOSPC;
	}

	pl_size -= sizeof(*tp_hdr);

	/* default is: nothing is encoded in the buffer */
	*b_size = 0;

	err = ucan_encode_msgs_buffer(dev, b_addr + sizeof(*tp_hdr), &pl_size);
	if (pl_size) {
		int total_size = sizeof(*tp_hdr) + pl_size;

		tp_hdr = (struct canxl_usb_tp_hdr *)b_addr;

		tp_hdr->hdr.size = cpu_to_le16(sizeof(*tp_hdr));
		tp_hdr->hdr.type = CANXL_USB_TP_HEADER;
		tp_hdr->reserved_1 = 0;
		tp_hdr->reserved_2 = 0;

		/* set the whole size of the packet to send */
		*b_size = ALIGN(total_size, 4);

		/* should be a multiple of 512 bytes */
		total_size = ((total_size >> 9) + 1) << 9;
		tp_hdr->total_size = cpu_to_le16(total_size);

		tp_hdr->reserved_3 = 0;

#ifdef DEBUG_TX_PATH
		dump_mem("Tx buffer", b_addr, *b_size);

	} else if (err != -ENODATA) {
		pr_warn(DEVICE_NAME ": failed (err %d)\n", err);
#endif
	}

	return err;
}

#define PCAN_USB_XL_SYNC_PERIOD		NSEC_PER_SEC

static struct pcan_timespec *pcan_usbxl_ts_decoder(struct pcandev *dev,
						   void *rx_msg,
						   struct pcan_timespec *tv)
{
	struct canxl_rx_hdr *rx_hdr = (struct canxl_rx_hdr *)rx_msg;
	u64 ts_ns = le64_to_cpu(rx_hdr->timestamp);

#ifndef NETDEV_SUPPORT
	/* simulate sync if calibration msgs aren't used for that */
	if (pcan_usb_get_if(dev)->cm_ignore_count < 0) {

		u64 delta_ns = ts_ns - dev->time_sync.ts_ns;

		/* simulate sync every PCAN_USB_XL_SYNC_PERIOD */
		if (delta_ns >= PCAN_USB_XL_SYNC_PERIOD) {

#ifdef PCAN_USBPRO_TS_RESYNC_PERIOD
			/* Note: pcan_sync_times() resets the entire
			 *       time_sync field when ts_us == 0 .
			 */
			if (delta_ns >= PCAN_USBPRO_TS_RESYNC_PERIOD)
				dev->time_sync.ts_ns = 0;
#endif
			pcan_sync_times_ns(dev, ts_ns, 0);
		}
	}
#endif /* NETDEV_SUPPORT */

	pcan_sync_decode_ns(dev, ts_ns, tv);

	return tv;
}

/* handle uCAN Rx CAN CC/FD message */
static int pcan_usbxl_decode_rxmsg_ccfd(struct ucan_engine *ucan,
					void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	canxl_dump_rx_msg("CAN_CCFD msg", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_rxmsg_fd(dev,
					(struct canxl_rx_msg_fd *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN Rx CAN XL message */
static int pcan_usbxl_decode_rxmsg_xl(struct ucan_engine *ucan,
				      void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	canxl_dump_rx_msg("CAN_XL msg", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_rxmsg_xl(dev,
					(struct canxl_rx_msg_xl *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN Rx CAN XL error notification message */
static int pcan_usbxl_decode_error_notification(struct ucan_engine *ucan,
						void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	if (printk_ratelimit())
		canxl_dump_rx_msg("CAN_XL error notification", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_error_notification(dev,
					(struct canxl_rx_error *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN Rx CAN XL protocol exception message */
static int pcan_usbxl_decode_protocol_exception(struct ucan_engine *ucan,
						void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	if (printk_ratelimit())
		canxl_dump_rx_msg("CAN_XL protocol exception", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_protocol_exception(dev,
					(struct canxl_rx_error *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN Rx CAN XL overload message */
static int pcan_usbxl_decode_overload(struct ucan_engine *ucan,
				      void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	if (printk_ratelimit())
		canxl_dump_rx_msg("CAN_XL overload", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_overload(dev,
					(struct canxl_rx_overload *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN Rx CAN XL overrun message
 *
 * "in general, it's the same than CANFD IP OVERRUN(0x101) message"
 */
static int pcan_usbxl_decode_overrun(struct ucan_engine *ucan,
				     void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	if (printk_ratelimit())
		canxl_dump_rx_msg("CAN_XL overrun", rx_msg);
#endif

	return pcan_usbpro_return(dev,
				  canfd_post_overflow(dev,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN-XL error message */
static int pcan_usbxl_decode_error(struct ucan_engine *ucan,
				   void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;

#ifdef DEBUG_RX_PATH
	if (printk_ratelimit())
		canxl_dump_rx_msg("CANXL-USB ERROR msg", rx_msg);
#endif
	return pcan_usbpro_return(dev,
				  canxl_post_error(dev,
					(struct canxl_rx_error *)rx_msg,
					ucan->ops.ts_decoder(dev,
							     rx_msg,
							     &tv)));
}

/* handle uCAN-XL status message */
static int pcan_usbxl_decode_status(struct ucan_engine *ucan,
				    void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;
	struct pcan_timespec tv;
	int err;

#ifdef DEBUG_RX_PATH
	canxl_dump_rx_msg("CANXL-USB STATUS msg", rx_msg);
#endif
	err = canxl_post_status(dev, (struct canxl_rx_status *)rx_msg,
				ucan->ops.ts_decoder(dev, rx_msg, &tv));

	/* bus is ok: if tx_engine idle, set it to STOPPED so that user will
	 * initiate writing on it
	 */
	if ((dev->bus_state != PCANFD_ERROR_BUSOFF) &&
			(dev->locked_tx_engine_state == TX_ENGINE_IDLE))
		pcan_set_tx_engine(dev, TX_ENGINE_STOPPED);

	return pcan_usbpro_return(dev, err);
}

/* handle uCAN-XL bus-load Gen2 message */
static int pcan_usbxl_decode_busload2(struct ucan_engine *ucan,
				      void *rx_msg, void *arg)
{
	struct pcandev *dev = (struct pcandev *)arg;

#ifdef DEBUG_RX_PATH
	canxl_dump_rx_msg("CANXL-USB BUS-LOAD_2 msg", rx_msg);
#endif

	return pcan_usbpro_return(dev,
			canxl_post_busload2(dev,
					    (struct canxl_rx_busload2 *)rx_msg,

	/* don't lose time to decode timestamp: bus load events frequency is
	 * very high so use time of day instead
	 */
					   NULL));
}


/* handle USB-XL calibration message: timestamp in nanoseconds!
 *
 * Note: SOF packet (11-bit frame number) is sent every:
 * - 1 ms +/- 500 ns on FS bus
 * - 125 µs +/- 0.0625 µs on HS bus
 *
 * Frame_number(n) = (Frame_number(n-1) + 1000) % 2048
 */
static int pcan_usbxl_decode_calibration(struct ucan_engine *ucan,
					 void *rx_msg, void *arg)
{
	struct canxl_usb_ts_msg *rx_ts = (struct canxl_usb_ts_msg *)rx_msg;
	struct pcan_usb_interface *usb_if = (void *)arg;
	u64 ts_us = le64_to_cpu(rx_ts->hdr.timestamp);

	do_div(ts_us, 1000);

#ifdef DEBUG_RX_PATH_FULL
	canxl_dump_rx_msg("CANXL-USB Calibration msg", rx_msg);
#endif

#ifdef DEBUG_TIMING_USB
	pr_info(DEVICE_NAME ": PCAN_CM %llu %u %d\n",
		le64_to_cpu(rx_ts->hdr.timestamp),
		le16_to_cpu(rx_ts->usb_frame_index),
		usb_get_current_frame_number(usb_if->usb_dev));
#endif

	return pcan_usbpro_handle_calibration(usb_if, ts_us,
				le16_to_cpu(rx_ts->usb_frame_index));
}

/* int pcan_usbxl_open_xl(struct pcandev *dev, struct pcanxl_init *pfdi)
 */
static int pcan_usbxl_open_xl(struct pcandev *dev, struct pcanxl_init *pfdi)
{
	unsigned short usb_opt_to_clr = 0, usb_opt_to_set = 0;

#if defined(DEBUG_TRACE) || defined(DEBUG_IRQ)
	pr_info(DEVICE_NAME ": %s(CAN%u, flags=%xh clk=%u Hz)\n",
		__func__, pcan_idx(dev)+1, pfdi->flags, pfdi->clock_Hz);
#endif

	/* setup fast-forward option */
	if (fast_fwd)
		usb_opt_to_set |= CANFD_USB_OPTION_FAST_FWD;
	else
		usb_opt_to_clr |= CANFD_USB_OPTION_FAST_FWD;

	return canxl_device_open_xl(dev, pfdi, usb_opt_to_set, usb_opt_to_clr);
}

/*
 * void pcan_usbxl_free(struct pcan_usb_interface *usb_if)
 */
static void pcan_usbxl_free(struct pcan_usb_interface *usb_if)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(usb_if->index=%d)\n", __func__, usb_if->index);
#endif
	switch (le16_to_cpu(usb_if->usb_dev->descriptor.idProduct)) {
	case PCAN_USBXL_PRODUCT_ID:
		pcan_usbxl_devices--;
		break;

	default:
		break;
	}

	/* release dynamic memory only once */
	usb_if->adapter = pcan_free_adapter(usb_if->adapter);
}

/*
 * static int pcan_usbxl_set_clk_domain(struct pcandev *dev,
 * 				        struct pcanxl_init *pxli)
 */
static int pcan_usbxl_set_clk_domain(struct pcandev *dev,
				     struct pcanxl_init *pxli)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(CAN%u, clk=%u Hz)\n",
		__func__, pcan_idx(dev)+1, pxli->clock_Hz);
#endif
	/* select the clock for the CAN */
	switch (pxli->clock_Hz) {
	case 160000000:
		ucan_usb_set_clck_domain(dev, CANXL_USB_CLK_160MHZ);
		break;

	default:
		return dev->ucan.ovr_ops.set_clk_domain(dev, pxli);
	}

	return 0;
}

/*
 * static void pcan_usbxl_init_callbacks(struct pcan_usb_interface *usb_if)
 */
static void pcan_usbxl_init_callbacks(struct pcan_usb_interface *usb_if)
{
	pcan_usbfd_init_callbacks(usb_if);

	usb_if->device_free = pcan_usbxl_free;

	usb_if->device_ctrl_open_xl = pcan_usbxl_open_xl;
	usb_if->device_ctrl_set_bus_on = canxl_set_bus_on;
	usb_if->device_ctrl_set_bus_off = canxl_set_bus_off;
	usb_if->device_ctrl_msg_encode = pcan_usbxl_encode_msgs_buffer;
}

/* interface functions used to send commands / handle msgs to USB/uCAN */
static int (*pcan_usbxl_msg_handlers[])(struct ucan_engine *,
					void *, void *) = {
	[CANXL_RX_MSG_CCFD] = pcan_usbxl_decode_rxmsg_ccfd,
	[CANXL_RX_MSG_XL] = pcan_usbxl_decode_rxmsg_xl,
	[CANXL_RX_ERR_NOTIF] = pcan_usbxl_decode_error_notification,
	[CANXL_RX_PROT_EXCEPT] = pcan_usbxl_decode_protocol_exception,
	[CANXL_RX_OVERLOAD] = pcan_usbxl_decode_overload,
	[CANXL_RX_OVERRUN] = pcan_usbxl_decode_overrun,

	[CANFD_MSG_ERROR] = pcan_usbxl_decode_error,
	[CANFD_MSG_STATUS] = pcan_usbxl_decode_status,

	[CANXL_RX_BUSLOAD2] = pcan_usbxl_decode_busload2,
	[CANXL_USB_MSG_CALIBRATION] = pcan_usbxl_decode_calibration,
};

static struct ucan_ops pcan_usbxl_ucan_ops = {
	.set_clk_domain = pcan_usbxl_set_clk_domain,
	.send_cmd = pcan_usbxl_send_ucan_cmd,
	.tx_msg_encoder = canxl_encode_txmsg,
#ifdef DEBUG_RX_PATH
	.rx_msg_handler = pcan_usbxl_handle_msg,
#else
	.rx_msg_handler = canxl_handle_msg,
#endif
	.ts_decoder = pcan_usbxl_ts_decoder,
	.handle_msg_table = pcan_usbxl_msg_handlers,
	.handle_msg_size = ARRAY_SIZE(pcan_usbxl_msg_handlers),
};

static struct ucan_ops *pcan_usbxl_init_callbacks_dev(struct pcandev *dev)
{
	/* First, init with default CANFD members */
	pcan_usbfd_init_callbacks_dev(dev);

	/* save uCAN CANFD members function in order to override them */
	dev->ucan.ovr_ops = dev->ucan.ops;

	dev->ucan.ops = pcan_usbxl_ucan_ops;

	return &pcan_usbxl_ucan_ops;
}

/*
 * int pcan_usbxl_init(struct pcan_usb_interface *usb_if)
 *
 * Do device specific initialization.
 */
int pcan_usbxl_init(struct pcan_usb_interface *usb_if)
{
	struct pcan_usb_interface *same_if = NULL;
	u32 bl_version;
	size_t c;
	int err;

	if (!usb_if) {
		pr_info(DEVICE_NAME ": NULL usb_if!\n");
		return -ENODEV;
	}
	if (!usb_if->usb_dev) {
		pr_info(DEVICE_NAME ": NULL usb_if->usb_dev!\n");
		return -ENODEV;
	}

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME
		": %s(bus=%d port=%d parent_port=%d can_count=%zu)\n",
		__func__,
		usb_if->usb_dev->bus->busnum,
		usb_if->usb_dev->portnum,
		usb_if->usb_dev->parent->portnum,
		usb_if->can_count);
#endif

	/* cm_ignore_count = -1: donot rely on calibration msgs timestamps any 
	 * more to sync clocks, since these timestamps may reset each time
	 * interface is put UP or USB X6 is unplugged.
	 *
	 * Clock sync is then based on event timestamps only:
	 * when the last synchronization is more than one second old, then a new
	 * one is made. If the last sync is more than one hour old, then the
	 * clocks drift calculations are reset (see src/pcan_usbpro.c).
	 *
	 * cm_ignore_count = 0 means that clock_drift will be computed by
	 * calibration messages (CM) only: CM ts is not kept as a base to event
	 * timestamps. Only the diff between two ts of CM is kept.
	 * Events timestamps must then be rebased.
	 */
	pcan_usbpro_init_calibration(usb_if, 0);

	switch (le16_to_cpu(usb_if->usb_dev->descriptor.idProduct)) {

	case PCAN_USBXL_PRODUCT_ID:
		usb_if->adapter = pcan_alloc_adapter("PCAN-USB XL",
						     "IPEH-005022",
						     pcan_usbxl_devices++,
						     usb_if->can_count);
		break;
	}

	if (!usb_if->adapter)
		return -ENOMEM;

	/* Set PCAN-USB (Pro) FD default hardware specific callbacks */
	pcan_usbxl_init_callbacks(usb_if);

	for (c = 0; c < usb_if->can_count; c++) {
		struct pcandev *dev = usb_if_dev(usb_if, c);
		if (!dev) {
			pr_err(DEVICE_NAME
				": %s: ABNORMAL NULL dev #%zu/%zu\n",
				usb_if->adapter->name, c, usb_if->can_count);
			return -ENODEV;
		}

		pcan_usbxl_init_callbacks_dev(dev);

		/* remember the list of channels in each channel */
		dev->ucan.devs = usb_if->devs;
		dev->ucan.devs_count = usb_if->can_count;

		/* use the allocated commands buffer for building uCAN cmds */
		dev->ucan.cmd_head = dev->port.usb.cout_baddr;
		dev->ucan.cmd_size = dev->port.usb.cout_bsize;
	}

	/* Tell module the CAN driver is loaded */
	err = pcan_usbpro_driver_loaded(usb_if, 0, 1);
	if (err) {
		pr_err(DEVICE_NAME
			": unable to tell %s that driver is loaded (err %d)\n",
			usb_if->adapter->name, err);
		return err;
	}

	/* read fw info */
	err = pcan_usbfd_get_fw_info(usb_if, !same_if, &bl_version);
	if (err) {
		pr_err(DEVICE_NAME
			": unable to read fw info from %s (err %d)\n",
			usb_if->adapter->name, err);
		return err;
	}

	/* init adapter fw version with (only) first interface fw version */
	if (!usb_if->index)
		usb_if->adapter->hw_ver = usb_if->hw_ver;

	return 0;
}
#endif /* USB_SUPPORT */

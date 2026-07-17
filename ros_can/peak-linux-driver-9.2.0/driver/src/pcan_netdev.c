/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcan_netdev.c - CAN network device support functions
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
 * Maintainer:   Stephane Grosjean <stephane.grosjean@hms-networks.com>
 * Contributors: Klaus Hitschler <klaus.hitschler@gmx.de>
 *               Oliver Hartkopp <oliver.hartkopp@volkswagen.de> socket-CAN
 */
/* #define DEBUG */
/*#undef DEBUG*/

#include "src/pcan_common.h"
#include <linux/sched.h>
#include <linux/skbuff.h>
#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 9, 0)
#include <linux/can/skb.h>
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)
#include <linux/units.h>
#endif
#endif
#include "src/pcan_main.h"
#include "src/pcan_netdev.h"
#include "src/pcanxl_core.h"

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 4, 0)

/* 6.19.0 defines CAN_CTRLMODE_XL and donot use can_change_mtu() anymore */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 19, 0)
#define INCLUDE_CANXL_SUPPORT
#define DONT_USE_CAN_CHANGE_MTU
#endif

/* pcan_netdev_register() use alloc_candev() instead of alloc_netdev() */
#define USES_ALLOC_CANDEV

/* using alloc_candev() also means:
 * - don't care about LINUX_CAN_RESTART_TIMER (restart is handled by
 *   can_restart_work)
 */
#endif

/* If defined, then donot use linux-can can_restart() mechanism to prevent
 * race condition around CARRIER_ON (see comments around
 * FIX_CAN_RESTART_CARRIER_ON) but our own one.
 */
#define FIX_CAN_RESTART_CARRIER_ON

#ifdef USES_ALLOC_CANDEV
#include <linux/can/dev.h>

#ifdef FIX_CAN_RESTART_CARRIER_ON
#define USES_PCAN_RESTART
#endif

#else
#define USES_PCAN_RESTART
#endif

#ifdef DEBUG
#define DEBUG_TX
#define DEBUG_RX
#define DEBUG_OPEN
#define DEBUG_DEFCLK
#else
//#define DEBUG_TX
//#define DEBUG_RX
//#define DEBUG_OPEN
//#define DEBUG_DEFCLK
#endif

#define CAN_NETDEV_NAME		"can%d"

#ifndef NEGA
#define MEGA			1000000UL
#endif

static char *assign  = NULL;
module_param(assign, charp, 0444);
MODULE_PARM_DESC(assign, "assignment for netdevice names to CAN devices");

static char *defclk = NULL;
module_param(defclk, charp, 0444);
MODULE_PARM_DESC(defclk, "default clock in Hz used by channels (0=default)");

#if LINUX_VERSION_CODE >= KERNEL_VERSION(4, 8, 0)
/* Mainline Kernel removed restart_timer from 4.8 *BUT* Canonical has decided
 * to backport the change in their 4.4.0-59.
 * -DLINUX_CAN_RESTART_TIMER should be decided by Makefile.
 */
#undef LINUX_CAN_RESTART_TIMER
#endif

#define pcan_priv	pcanusr

#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 6, 0)
/* Note: Kernel 3.6 is the first one in which CAN-FD has been added.
 * Code below has been imported from linux-3.6/include/linux/can.h */
#define CAN_MAX_DLEN		8

#elif LINUX_VERSION_CODE < KERNEL_VERSION(3, 18, 0)
static inline bool can_is_canfd_skb(const struct sk_buff *skb)
{
	return skb->len == CANFD_MTU;
}
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 6, 0)
/* convert a timeval to ktime_t format: */
static inline ktime_t timeval_to_ktime(struct timeval tv)
{
	return ktime_set(tv.tv_sec, tv.tv_usec * NSEC_PER_USEC);
}
#endif

/*
 * struct device *pcandev_to_dev(struct pcandev *pdev)
 *
 *	Get the kernel device object address attached to the pcandev object,
 *	NULL if the pcandev object isn't linked to any kernel device.
 */
static struct device *pcandev_to_dev(struct pcandev *pdev)
{
	switch (pdev->wType) {
	case HW_ISA:
	case HW_ISA_SJA:
		return NULL;	/* no system device to provide */

	case HW_DONGLE_SJA:
	case HW_DONGLE_SJA_EPP:
	case HW_DONGLE_PRO:
	case HW_DONGLE_PRO_EPP:
#ifdef PARPORT_SUBSYSTEM
		return &pdev->port.dng.pardev->dev;
#else
		return NULL;	/* no system device to provide */
#endif
#ifdef PCI_SUPPORT
	case HW_PCI:
	case HW_PCIE_FD:
		return &pdev->port.pci.pciDev->dev;
#endif
#ifdef PCCARD_SUPPORT
	case HW_PCCARD:
		return NULL;	/* no system device to provide */
#endif
#ifdef USB_SUPPORT
	case HW_USB:
	case HW_USB_FD:
	case HW_USB_PRO:
	case HW_USB_PRO_FD:
	case HW_USB_X6:
	case HW_USB_XL:
		return &pcan_usb_get_if(pdev)->usb_intf->dev;
#endif
	default:
		break;
	}

	return NULL;
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
static struct can_bittiming *pcan_netdev_get_nom_bittiming(struct pcandev *dev)
{
	struct net_device *ndev = dev->netdev;
	if (ndev) {
		struct pcan_priv *priv = netdev_priv(ndev);
		return &priv->can.bittiming;
	}

	return NULL;
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 15, 0)
static struct can_bittiming *pcan_netdev_get_fd_bittiming(struct pcandev *dev)
{
	struct net_device *ndev = dev->netdev;
	if (ndev) {
		struct pcan_priv *priv = netdev_priv(ndev);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)
		return &priv->can.fd.data_bittiming;
#else
		return &priv->can.data_bittiming;
#endif
	}

	return NULL;
}
#endif	/* 3.6.15 */
#endif	/* 3.6.0 */

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 194)
static struct can_tdc *pcan_netdev_get_fd_tdc(struct net_device *ndev)
{
	struct pcan_priv *priv = netdev_priv(ndev);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)
	return &priv->can.fd.tdc;
#else
	return &priv->can.tdc;
#endif
}
#endif

#ifdef INCLUDE_CANXL_SUPPORT
static struct can_bittiming *pcan_netdev_get_xl_bittiming(struct pcandev *dev)
{
	struct net_device *ndev = dev->netdev;
	if (ndev) {
		struct pcan_priv *priv = netdev_priv(ndev);
		return &priv->can.xl.data_bittiming;
	}
	return NULL;
}
#endif

/* Mainline drivers don't set any default nominal nor data bitrate.
 * Therefore, this function is useless.
 */

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
static void pcan_copy_bt_from_netdev(struct pcan_bittiming *pp,
				     const struct can_bittiming *pc)
{
	pp->bitrate = pc->bitrate;
	pp->sample_point = pc->sample_point * 10;
	pp->tq = pc->tq;
	pp->tseg1 = pc->prop_seg + pc->phase_seg1;
	pp->tseg2 = pc->phase_seg2;
	pp->sjw = pc->sjw;
	pp->brp = pc->brp;
}
#endif

/* AF_CAN netdevice: open device */
static int pcan_netdev_open(struct net_device *dev)
{
	struct pcan_priv *priv = netdev_priv(dev);
	struct pcandev *pdev = priv->dev;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(%s)\n", __func__, dev->name);
#endif
	err = open_candev(dev);
	if (err)
		return err;

	pdev->init_settings.flags &=  ~(PCANXL_INIT_FD | PCANXL_INIT_XL |
					PCANFD_INIT_FD_NON_ISO |
					PCANFD_INIT_LISTEN_ONLY |
					PCANFD_INIT_STD_MSG_ONLY |
					PCANFD_INIT_BUS_LOAD_INFO);

	pdev->init_settings.clock_Hz = priv->can.clock.freq;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
	memset(&pdev->init_settings.nominal, '\0',
					sizeof(struct pcan_bittiming));

	pcan_copy_bt_from_netdev(&pdev->init_settings.nominal,
				 pcan_netdev_get_nom_bittiming(pdev));

	memset(&pdev->init_settings.fd_data, '\0',
					sizeof(struct pcan_bittiming));

	memset(&pdev->init_settings.xl_data, '\0',
					sizeof(struct pcan_bittiming));
	memset(&pdev->init_settings.xl_pwm, '\0', sizeof(struct pcanxl_pwm));
	memset(&pdev->init_settings.rxmt_limit, '\0', PCANXL_CAN_MAX);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 15, 0)

	/* CAN_CTRLMODE_FD only exists from 3.15 */
	if (priv->can.ctrlmode & CAN_CTRLMODE_FD) {

		pdev->init_settings.flags |= PCANXL_INIT_FD;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 18, 5)
		if (priv->can.ctrlmode & CAN_CTRLMODE_FD_NON_ISO)
			pdev->init_settings.flags |= PCANFD_INIT_FD_NON_ISO;
#endif
		pcan_copy_bt_from_netdev(&pdev->init_settings.fd_data,
					 pcan_netdev_get_fd_bittiming(pdev));

		pdev->init_settings.fd_data.ssp_offset = PCANXL_SSP_OFFSET_SP;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 194)
		{
			struct can_tdc *tdc = pcan_netdev_get_fd_tdc(dev);

			if (priv->can.ctrlmode & CAN_CTRLMODE_TDC_AUTO)
				pdev->init_settings.fd_data.ssp_offset =
					tdc->tdco;
		}
#endif /* 5.15.194 */
	}

#ifdef INCLUDE_CANXL_SUPPORT
	if (priv->can.ctrlmode & CAN_CTRLMODE_XL) {

		/* Default is: pure CAN-XL (ES=0) */
		pdev->init_settings.flags |= PCANXL_INIT_XL |
					     PCANXL_INIT_ES_OFF;

		pdev->init_settings.flags &= ~PCANFD_INIT_FD_NON_ISO;

		pcan_copy_bt_from_netdev(&pdev->init_settings.xl_data,
					 pcan_netdev_get_xl_bittiming(pdev));

		pdev->init_settings.xl_data.ssp_offset = PCANXL_SSP_OFFSET_SP;

		/* Note: TDC only used when TMS=0 while PWM is used when
		 * TMS=1
		 */
		if (priv->can.ctrlmode & CAN_CTRLMODE_XL_TDC_AUTO)
			pdev->init_settings.xl_data.ssp_offset =
				priv->can.xl.tdc.tdco;
		if (priv->can.ctrlmode & CAN_CTRLMODE_XL_TMS) {
			pdev->init_settings.flags |= PCANXL_INIT_TMS_ON;

			pdev->init_settings.xl_pwm.pwm_offset =
				priv->can.xl.pwm.pwmo;
			pdev->init_settings.xl_pwm.pwm_short =
				priv->can.xl.pwm.pwms;
			pdev->init_settings.xl_pwm.pwm_long =
				priv->can.xl.pwm.pwml;

			/* Request to verify these PWM specs */
			pdev->init_settings.flags |= PCANFD_INIT_BTR_NOK;

		/* mixed-mode: ES=1 */
		} else if (priv->can.ctrlmode & CAN_CTRLMODE_FD)
			pdev->init_settings.flags &= ~PCANXL_INIT_ES_OFF;
	}
#endif /*  INCLUDE_CANXL_SUPPORT */

#endif	/* 3.15.0 */
#endif	/* 3.6.0 */

	if (priv->can.ctrlmode & CAN_CTRLMODE_LISTENONLY)
		pdev->init_settings.flags |= PCANFD_INIT_LISTEN_ONLY;

	/* yes we will do read and write */
	priv->open_flags = O_RDWR;

	err = pcan_open_path(pdev, priv);
	if (err)
		return -ENODEV;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 17, 0)
	/* If "presume-ack" is supported, then set the corresponding option
	 * accordingly.
	 * WARNING: once presume-ack set to on the nfurther ip link ste canX up
	 * will still use implicit presume-ack=on!
	 * "presume-ack off" MUST explicitely used to remove the option!
	 */
	if (priv->can.ctrlmode_supported & CAN_CTRLMODE_PRESUME_ACK) {
		u32 v = !!(priv->can.ctrlmode & CAN_CTRLMODE_PRESUME_ACK);
		err = __pcan_set_dev_opt(pdev, PCANFD_OPT_SELF_ACK, v);
		if (err)
			netdev_warn(dev, "can't set presume-ack=%u (err %d)\n",
				    v, err);
	}
#endif

	netif_start_queue(dev);

	return 0;
}

static struct pcandev *pcan_netdev_get_dev(struct pcan_priv *priv)
{
	struct pcandev *pdev = priv->dev;

	if (pdev) {
#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
		pr_info(DEVICE_NAME ": %s(%s): plugged=%u\n",
			__func__, (pdev->netdev) ? pdev->netdev->name : "NULL",
			pdev->is_plugged);
#endif

		/* if we are unregistering the dev, then it is in the list. */
		if (pdev->netdev)

			/* check whether this device is always linked. */
			if (!pcan_is_device_in_list(pdev))
				return NULL;

		/* if the device is plugged out */
		if (!pdev->is_plugged)
			return NULL;
	}

	return pdev;
}

/* AF_CAN netdevice: close device */
static int pcan_netdev_close(struct net_device *dev)
{
	struct pcan_priv *priv = netdev_priv(dev);
	struct pcandev *pdev = pcan_netdev_get_dev(priv);

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(%s): pdev=%p pdev->netdev=%p vs. ndev=%p\n",
		__func__, dev->name, pdev, (pdev) ? pdev->netdev : NULL, dev);
#endif

	if (pdev)
		pcan_release_path(pdev, priv);

	netif_stop_queue(dev);
	close_candev(dev);

	priv->can.state = CAN_STATE_STOPPED;

	return 0;
}

/* AF_CAN netdevice: get statistics for device */
struct net_device_stats *pcan_netdev_get_stats(struct net_device *dev)
{
#if LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 23)
	struct pcan_priv *priv = netdev_priv(dev);

	/* TODO: read statistics from chip */
	return &priv->stats;
#else
	return &dev->stats;
#endif
}

/* AF_CAN netdevice: transmit handler for device */
static int pcan_netdev_start_xmit(struct sk_buff *skb, struct net_device *dev)
{
	struct pcan_priv *priv = netdev_priv(dev);
	struct pcandev *pdev = pcan_netdev_get_dev(priv);
	struct net_device_stats *stats = pcan_netdev_get_stats(dev);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
	struct canfd_frame *cf = (struct canfd_frame *)skb->data;
#else
	struct can_frame *cf = (struct can_frame *)skb->data;
#endif
	pcan_lock_irqsave_ctxt lck_ctx;
	struct pcanxl_txmsg tx;
	u8 *tx_msg_data;
	int err;

#if defined(DEBUG_TRACE) || defined(DEBUG_TX)
	pr_info(DEVICE_NAME ": %s(id=%xh dlc=%u "
		"[%02x %02x %02x %02x %02x %02x %02x %02x] "
		") < %s tx queue\n",
		__func__, cf->can_id,
#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
		cf->len,
#else
		cf->can_dlc,
#endif
		cf->data[0], cf->data[1], cf->data[2], cf->data[3],
		cf->data[4], cf->data[5], cf->data[6], cf->data[7],
		dev->name);
#endif

	/* if the device is plugged out */
	if (!pdev) {
		stats->tx_dropped++;
		goto free_out;
	}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 0, 9)
	if (can_dev_dropped_skb(dev, skb))
		return NETDEV_TX_OK;
#endif

	/* convert SocketCAN CAN frame to PCAN FIFO compatible format */
	memset(&tx, '\0', sizeof(tx));

	tx.msg.flags = PCANFD_MSG_STD;

#ifdef INCLUDE_CANXL_SUPPORT
	if (can_is_canxl_skb(skb)) {
		struct canxl_frame *xl = (struct canxl_frame *)skb->data;

		tx.msg.type = PCANXL_TYPE_CANXL;

		if (xl->flags & CANXL_SEC)
			tx.msg.flags |= PCANXL_MSG_SEC;

		if (xl->flags & CANXL_RRS)
			tx.msg.flags |= PCANXL_MSG_RRS;

		tx.msg.id = xl->prio;
		tx.msg.data_len = xl->len;
		tx.msg.af = xl->af;
		tx.msg.sdt = xl->sdt;

		tx_msg_data = xl->data;
	} else {
#endif
		tx.msg.type = PCANXL_TYPE_CANCC;

		if (cf->can_id & CAN_RTR_FLAG)
			tx.msg.flags |= PCANFD_MSG_RTR;
		if (cf->can_id & CAN_EFF_FLAG)
			tx.msg.flags |= PCANFD_MSG_EXT;
		tx.msg.id = cf->can_id & CAN_ERR_MASK;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
		if (can_is_canfd_skb(skb)) {

			tx.msg.type = PCANXL_TYPE_CANFD;

			if (cf->flags & CANFD_ESI)
				tx.msg.flags |= PCANFD_MSG_ESI;
			if (cf->flags & CANFD_BRS)
				tx.msg.flags |= PCANFD_MSG_BRS;

#ifdef CAN_CTRLMODE_CC_LEN8_DLC
		} else if (cf->len == PCANFD_CAN20_MAXDATALEN) {
			tx.msg.flags = pcanxl_msg_flags_dlc_set(tx.msg.flags,
				can_get_cc_dlc((struct can_frame *)skb->data,
					       priv->can.ctrlmode));
#endif
		}

		tx.msg.data_len = cf->len;
#else
		tx.msg.data_len = cf->can_dlc;
#endif
		tx_msg_data = cf->data;

#ifdef INCLUDE_CANXL_SUPPORT
	}
#endif

	if (priv->can.ctrlmode & CAN_CTRLMODE_LOOPBACK) {

		/* Note: 
		 * - _SLF is supported by all devices (Self Receive Request)
		 * - _ECHO has been added for CANFD to add a user bit to the
		 *   _SLF frame.
		 * In socket-can, _SLF is used for echo management and 
		 * _SLF+_ECHO is used for loopbacked frames.
		 * In pcan, _ECHO = _SLF + userbit for CANFD equipments.
		 * In order to do like it is done in peak_xxx mainline drivers,
		 * _ECHO could be only used here *BUT* it is only handled by
		 * the uCAN module. Thus, should set both bits here.
		 */
		tx.msg.flags |= PCANFD_MSG_SLF|PCANFD_MSG_ECHO;
	}

	if (priv->can.ctrlmode & CAN_CTRLMODE_ONE_SHOT)
		tx.msg.flags |= PCANFD_MSG_SNG;

	/* put data into fifo */
	err = pcan_txfifo_in(pdev, &tx, tx_msg_data);
	if (err < 0) {
		pr_err(DEVICE_NAME ": Tx fifo full: frame %x dropped: "
			"%s net queue stopped\n", tx.msg.id, dev->name);

		/* stop netdev queue when PCAN FIFO is full */
		stats->tx_fifo_errors++; /* just for informational purposes */
		netif_stop_queue(dev);

		stats->tx_dropped++;
		goto free_out;
	}

#ifdef DEBUG_TX
	pr_info(DEVICE_NAME ": %xh dlc=%d "
		"[%02x %02x %02x %02x %02x %02x %02x %02x] "
		"> %s CAN%u\n",
		tx.msg.id, tx.msg.data_len,
		cf->data[0], cf->data[1], cf->data[2], cf->data[3],
		cf->data[4], cf->data[5], cf->data[6], cf->data[7],
		pdev->adapter->name, pcan_idx(pdev)+1);
#endif
	/* if we just put the 1st message (=the fifo was empty), we can start
	 * writing on hardware if it is ready for doing this.
	 */
	pcan_lock_get_irqsave(&pdev->isr_lock, lck_ctx);

		/* if can device ready to send, start writing */
		__pcan_dev_start_writing(pdev, NULL);

	pcan_lock_put_irqrestore(&pdev->isr_lock, lck_ctx);

	stats->tx_packets++;
	stats->tx_bytes += tx.msg.data_len;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(4, 7, 0)
	netdev_get_tx_queue(dev, 0)->trans_start = jiffies;
#endif

	/* stop Tx queue if we reach hi-water level */
	if (kfifo_ratio(&pdev->tx_fifo.kfifo) > txqhiwat) {
		netif_stop_queue(dev);
#ifdef DEBUG_TX
		pr_info(DEVICE_NAME ": Tx fifo hi-water reached: "
			"%s net queue stopped\n", dev->name);
#endif
	}

free_out:
	dev_kfree_skb(skb);

	return 0;
}

#if LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 33)
struct sk_buff *alloc_can_skb(struct net_device *dev, struct can_frame **cf)
{
	struct sk_buff *skb;

	skb = netdev_alloc_skb(dev, sizeof(struct can_frame));
	if (unlikely(!skb))
		return NULL;

	skb->protocol = htons(ETH_P_CAN);
	skb->pkt_type = PACKET_BROADCAST;
	skb->ip_summed = CHECKSUM_UNNECESSARY;

	*cf = (struct can_frame *)skb_put(skb, sizeof(struct can_frame));
	memset(*cf, 0, sizeof(struct can_frame));

	return skb;
}
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 11, 0)
#define CAN_CC_LEN(cc)		(cc)->len
#else
#define CAN_CC_LEN(cc)		(cc)->can_dlc
#endif

static int pcan_alloc_skb_cc(struct net_device *ndev,
			     struct pcanxl_msg *msg, u8 *data,
			     struct sk_buff **skb)
{
	struct pcan_priv *priv = netdev_priv(ndev);
	struct net_device_stats *stats = pcan_netdev_get_stats(ndev);
	struct pcandev *dev = pcan_netdev_get_dev(priv);
	u8 *prx_cnt, *ptx_cnt;
	struct can_frame *cc;

	*skb = alloc_can_skb(ndev, &cc);
	if (!*skb)
		return -ENOMEM;

	switch (msg->type) {

	case PCANXL_TYPE_CANCC:
		cc->can_id = msg->id & CAN_ERR_MASK;
		if (msg->flags & PCANFD_MSG_RTR)
			cc->can_id |= CAN_RTR_FLAG;
		if (msg->flags & PCANFD_MSG_EXT)
			cc->can_id |= CAN_EFF_FLAG;

#ifdef CAN_CTRLMODE_CC_LEN8_DLC
		/* Note: can_frame_set_cc_len() sets
		 * cf->len = can_cc_dlc2len(dlc);
		 */
		can_frame_set_cc_len(cc,
				     pcanxl_msg_flags_dlc_get(msg->flags),
				     priv->can.ctrlmode);
#endif
		memcpy(cc->data, data, msg->data_len);
		CAN_CC_LEN(cc) = msg->data_len;

		break;

	case PCANXL_TYPE_ERROR:

		/* v9: ignore simple errors counter decr notification */
		if (msg->id > PCANFD_ERRMSG_OTHER)
			return 0;

		stats->rx_errors++;
		priv->can.can_stats.bus_error++;

		/* v9: don't forward bus errors if berr-reporting is off */
		if (!(priv->can.ctrlmode & CAN_CTRLMODE_BERR_REPORTING))
			return 0;

		cc->can_id = CAN_ERR_FLAG | CAN_ERR_PROT | CAN_ERR_BUSERROR;
		CAN_CC_LEN(cc) = CAN_ERR_DLC;

		switch (msg->id) {
		case PCANFD_ERRMSG_BIT:
			cc->data[2] = CAN_ERR_PROT_BIT;
			break;
		case PCANFD_ERRMSG_FORM:
			cc->data[2] = CAN_ERR_PROT_FORM;
			break;
		case PCANFD_ERRMSG_STUFF:
			cc->data[2] = CAN_ERR_PROT_STUFF;
			break;
		case PCANFD_ERRMSG_OTHER:
			break;
		}

		/* set error location */
		cc->data[3] = msg->ctrlr_data[PCANXL_ERRCODE];

		/* Error occurred during transmission? */
		if (!(msg->flags & PCANFD_ERRMSG_RX))
			cc->data[2] |= CAN_ERR_PROT_TX;

		cc->data[6] = dev->tx_error_counter;
		cc->data[7] = dev->rx_error_counter;

		break;

	case PCANFD_TYPE_STATUS:

		/* use device counters instead of data bytes saved into
		 * msg->data because these counters are copied into msg->data[]
		 * just before being pushed into chardev rx fifo. Thus,
		 * msg->data[] don't contain any rx/tx err counters!
		 */
		prx_cnt = &dev->rx_error_counter;
		ptx_cnt = &dev->tx_error_counter;

		cc->can_id = CAN_ERR_FLAG;
		CAN_CC_LEN(cc) = CAN_ERR_DLC;

		switch (msg->id) {
		case PCANFD_ERROR_BUSOFF:
			if (priv->can.state == CAN_STATE_BUS_OFF) {
				kfree_skb(*skb);
				return 0;
			}

			can_bus_off(ndev);
			
			/* this is not done by native linux-can drivers.
			 * looks like it MUST be for PCAN-USB
			 */
			netif_stop_queue(ndev);

			priv->can.can_stats.bus_off++;
			priv->can.state = CAN_STATE_BUS_OFF;
			cc->can_id |= CAN_ERR_BUSOFF_NETDEV;

			break;

		case PCANFD_ERROR_PASSIVE:
			if (priv->can.state == CAN_STATE_ERROR_PASSIVE) {
				kfree_skb(*skb);
				return 0;
			}

			priv->can.state = CAN_STATE_ERROR_PASSIVE;
			priv->can.can_stats.error_passive++;
			cc->can_id |= CAN_ERR_CRTL;
			if (*prx_cnt > 127)
				cc->data[1] |= CAN_ERR_CRTL_RX_PASSIVE;
			if (*ptx_cnt > 127)
				cc->data[1] |= CAN_ERR_CRTL_TX_PASSIVE;
			break;

		case PCANFD_ERROR_WARNING:
			if (priv->can.state == CAN_STATE_ERROR_WARNING) {
				kfree_skb(*skb);
				return 0;
			}

			priv->can.state = CAN_STATE_ERROR_WARNING;
			priv->can.can_stats.error_warning++;

			cc->can_id |= CAN_ERR_CRTL;
			if (*prx_cnt > 96)
				cc->data[1] |= CAN_ERR_CRTL_RX_WARNING;
			if (*ptx_cnt > 96)
				cc->data[1] |= CAN_ERR_CRTL_TX_WARNING;
			break;

		case PCANFD_RX_OVERFLOW:
			if (msg->flags & PCANFD_ERROR_PROTOCOL) {
				cc->can_id |= CAN_ERR_PROT;
				cc->data[2] |= CAN_ERR_PROT_OVERLOAD;
			} else {
				cc->can_id |= CAN_ERR_CRTL;
				cc->data[1] |= CAN_ERR_CRTL_RX_OVERFLOW;

				stats->rx_over_errors++;
				stats->rx_errors++;
			}
			break;
		case PCANFD_TX_OVERFLOW:
			cc->can_id |= CAN_ERR_CRTL;
			cc->data[1] |= CAN_ERR_CRTL_TX_OVERFLOW;
			break;
		}
		break;
	}

	return sizeof(struct can_frame);
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)

#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 15, 0)
struct sk_buff *alloc_canfd_skb(struct net_device *dev,
				struct canfd_frame **cfd)
{
	struct sk_buff *skb;

	skb = netdev_alloc_skb(dev, sizeof(struct can_skb_priv) +
			       sizeof(struct canfd_frame));
	if (unlikely(!skb))
		return NULL;

	skb->protocol = htons(ETH_P_CANFD);
	skb->pkt_type = PACKET_BROADCAST;
	skb->ip_summed = CHECKSUM_UNNECESSARY;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 9, 0)
	can_skb_reserve(skb);
	can_skb_prv(skb)->ifindex = dev->ifindex;
#endif

	*cfd = (struct canfd_frame *)skb_put(skb, sizeof(struct canfd_frame));
	memset(*cfd, 0, sizeof(struct canfd_frame));

	return skb;
}
#endif

static int pcan_alloc_skb_fd(struct net_device *ndev,
			     struct pcanxl_msg *msg, u8 *data,
			     struct sk_buff **skb)
{
	struct pcan_priv *priv = netdev_priv(ndev);
	struct canfd_frame *fd;

	if (!(priv->can.ctrlmode & CAN_CTRLMODE_FD)) {
		pr_err(DEVICE_NAME
		       ": CANFD frame discarded (%s not CAN-FD)\n",
		       ndev->name);
		return 0;
	}

	/* handle CAN-FD when kernel is ok for this */
	*skb = alloc_canfd_skb(ndev, &fd);
	if (!*skb)
		return -ENOMEM;

	if (msg->flags & PCANFD_MSG_ESI)
		fd->flags |= CANFD_ESI;
	if (msg->flags & PCANFD_MSG_BRS)
		fd->flags |= CANFD_BRS;

	fd->can_id = msg->id & CAN_ERR_MASK;
	if (msg->flags & PCANFD_MSG_EXT)
		fd->can_id |= CAN_EFF_FLAG;

	if (msg->flags & PCANFD_MSG_RTR) {
		fd->can_id |= CAN_RTR_FLAG;

	} else {
		memcpy(fd->data, data, msg->data_len);
		fd->len = msg->data_len;
	}

	return sizeof(struct canfd_frame);
}

#ifdef INCLUDE_CANXL_SUPPORT
static int pcan_alloc_skb_xl(struct net_device *ndev,
			     struct pcanxl_msg *msg, u8 *data,
			     struct sk_buff **skb)
{
	struct canxl_frame *xl;

	/* Note: alloc_canxl_skb() sets ::len and ::flags */
	*skb = alloc_canxl_skb(ndev, &xl, msg->data_len);
	if (!*skb)
		return -ENOMEM;

	xl->prio = msg->id;

	if (msg->flags & PCANXL_MSG_SEC)
		xl->flags |= CANXL_SEC;
	if (msg->flags & PCANXL_MSG_RRS)
		xl->flags |= CANXL_RRS;

	xl->sdt = msg->sdt;
	xl->af = msg->af;

	memcpy(xl->data, data, msg->data_len);

	return CANXL_HDR_SIZE + msg->data_len;
}
#endif /* INCLUDE_CANXL_SUPPORT */
#endif /* 3.6.0 */

/* AF_CAN netdevice: receive function (put can_frame to netdev queue) */
int __pcan_netdev_rx(struct pcandev *dev, struct pcanxl_rxmsg *rx, u8 *data)
{
	struct pcanxl_msg *msg = (struct pcanxl_msg *)&rx->msg;
	struct net_device *ndev = dev->netdev;
	struct net_device_stats *stats;
	struct pcan_priv *priv;
	struct sk_buff *skb;
#ifdef FIX_CAN_RESTART_CARRIER_ON
	enum can_state prev_can_state;
#endif
	int lf;

#if defined(DEBUG_TRACE) || defined(DEBUG_RX)
	pr_info(DEVICE_NAME ": %s(type=%d id=%xh flgs=%xh dlc=%u "
		"[%02x %02x %02x %02x %02x %02x %02x %02x] "
		") < %s CAN%u\n",
		__func__, msg->type, msg->id, msg->flags, msg->data_len,
		data[0], data[1], data[2], data[3],
		data[4], data[5], data[6], data[7],
		dev->adapter->name, pcan_idx(dev)+1);
#endif

	/* under high busload condition, interrupts may occur before everything
	 * has been completed.
	 */
	if (!ndev)
		return 0;

	priv = netdev_priv(ndev);

	switch (msg->type) {

	default:
		return -EINVAL;

	case PCANFD_TYPE_NOP:
		/* ignored */
		return 0;

	case PCANFD_TYPE_STATUS:
		switch (msg->id) {
		case PCANFD_ERROR_ACTIVE:

#ifdef FIX_CAN_RESTART_CARRIER_ON
			prev_can_state = priv->can.state;
#endif

			/* event not converted. Moreover, sure that state was
			 * not ERROR_ACTIVE
			 */
			priv->can.state = CAN_STATE_ERROR_ACTIVE;

#ifdef FIX_CAN_RESTART_CARRIER_ON
			/* if we're back here because of restart-ms then
			 * do call netif_carrier_on() now
			 */
			if ((prev_can_state == CAN_STATE_BUS_OFF) &&
						    (priv->can.restart_ms))
				netif_carrier_on(ndev);
#endif

			/* netif_wake_queue() reschedules Tx queue */
			netif_wake_queue(ndev);

			/* fall through */
			fallthrough;
		case PCANFD_UNKNOWN:
		case PCANFD_BUS_ERROR:
		case PCANFD_BUS_LOAD:
			return 0;
		}

		/* fall through */
		fallthrough;
	case PCANXL_TYPE_ERROR:
	case PCANXL_TYPE_CANCC:
		lf = pcan_alloc_skb_cc(ndev, msg, data, &skb);
		break;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
	case PCANXL_TYPE_CANFD:
		/* handle CAN-XL when kernel is ok for this */
		lf = pcan_alloc_skb_fd(ndev, msg, data, &skb);
		break;

#ifdef INCLUDE_CANXL_SUPPORT
	case PCANXL_TYPE_CANXL:
		/* handle CAN-XL when kernel is ok for this */
		lf = pcan_alloc_skb_xl(ndev, msg, data, &skb);
		break;
#endif
#endif
	}

	if (lf <= 0)
		return lf;

	switch (msg->type) {

	case PCANXL_TYPE_CANCC:
	case PCANXL_TYPE_CANFD:
	case PCANXL_TYPE_CANXL:

		/* use hw timestamp if given, only relevant for CAN frames: */

		/* Consider netdev hw timestamps as RAW timestamps. Therefore,
		 * give socket application the raw value given by the device.
		 */
		if (dev->features & PCAN_DEV_HWTS_RDY) {
			s64 s = rx->hwtv.hw_ns;
			struct skb_shared_hwtstamps *hwts;
			struct timeval ts;

			ts.tv_usec = do_div(s, NSEC_PER_SEC) / NSEC_PER_USEC;
			ts.tv_sec = (__kernel_time_t )s;

			hwts = skb_hwtstamps(skb);
			hwts->hwtstamp = timeval_to_ktime(ts);
		}

		/* "do not increase rx stats when genereting CAN rx error msg
		 * frame" * (see linux-can)
	 	 */
		stats = pcan_netdev_get_stats(ndev);
		stats->rx_packets++;
		stats->rx_bytes += msg->data_len;

		break;
	}

#if LINUX_VERSION_CODE == KERNEL_VERSION(4, 1, 0) \
   || LINUX_VERSION_CODE == KERNEL_VERSION(4, 1, 1)
	/* mandatory for Kernels 4.1.[01] */
	__net_timestamp(skb);
#endif

	netif_rx(skb);

	return 1;
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 15, 0)
static int pcan_netdev_change_mtu(struct net_device *netdev, int new_mtu)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ":%s(new_mtu=%d) old_mtu=%d\n",
		__func__, new_mtu, netdev->mtu);
#endif
	/* Do not allow changing the MTU while running */
	if (netdev->flags & IFF_UP)
		return -EBUSY;

	/* allow change of MTU according to the CANFD ability of the device */
	if (new_mtu != CAN_MTU) {
		if (new_mtu != CANFD_MTU)
			return -EINVAL;
	}

	netdev->mtu = new_mtu;
	return 0;
}
#endif
#endif

#if LINUX_VERSION_CODE > KERNEL_VERSION(2, 6, 28)
static const struct net_device_ops pcan_netdev_ops = {
	.ndo_open	= pcan_netdev_open,
	.ndo_start_xmit	= pcan_netdev_start_xmit,
	.ndo_stop	= pcan_netdev_close,
	.ndo_get_stats	= pcan_netdev_get_stats,
#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 15, 0)
	.ndo_change_mtu = pcan_netdev_change_mtu,
#elif !defined(DONT_USE_CAN_CHANGE_MTU)
	.ndo_change_mtu = can_change_mtu,
#endif
#endif
};
#endif

#ifndef USES_ALLOC_CANDEV
/* AF_CAN netdevice: initialize data structure (should do what can_setup() in
 * drivers/net/can/dev.c does
 */
static void pcan_netdev_init(struct net_device *dev)
{
	dev->type = ARPHRD_CAN;
	dev->hard_header_len = 0;
#ifdef CAN_MTU
	dev->mtu = CAN_MTU;
#else
	dev->mtu = sizeof(struct can_frame);
#endif
	dev->addr_len = 0;
	dev->tx_queue_len = 10;

	dev->flags = IFF_NOARP;

	dev->features = NETIF_F_HW_CSUM;
}
#endif /* USES_ALLOC_CANDEV */

static void pcan_check_ifname(char *name)
{
	/* check wanted assigned 'name' against existing device names */
#if LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 24)
	if (__dev_get_by_name(name)) {
#else
	if (__dev_get_by_name(&init_net, name)) {
#endif
		pr_info(DEVICE_NAME ": assigned netdevice %s already exists\n",
			name);

		*name = 0; /* mark for auto assignment */
	}
}

/* AF_CAN netdevice: try to reassign netdev name according to user needs */
static void pcan_netdev_create_name(char *name, struct pcandev *pdev)
{
	int minor = pdev->nMinor;
	char *pa = assign;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME
		": %s(): minor=%d major=%d (usb major=%d) assign=\"%s\"\n",
		__func__, minor, pdev->nMajor, USB_MAJOR, assign);
#endif
	if (!assign) /* auto assignment */
		return;

	if (!strncmp(pa, "devid", 5)) {

		/* if device defines an alternate number, use it instead of
		 * its minor
		 */
		if (pdev->flags & PCAN_DEV_USES_ALT_NUM) {
			snprintf(name, IFNAMSIZ-1, CAN_NETDEV_NAME,
					(int )pdev->device_alt_num);
			pcan_check_ifname(name);
			if (*name)
				return;
		} else {
			pr_warn(DEVICE_NAME ": pcan%u: "
				"can't assign flashed device id to can name\n",
				minor);
		}

		pa += 5;
		if (*pa++ != ',')
			return;
	}

	if (!strncmp(pa, "peak", 4)) {

		/* assign=peak
		 * easy: /dev/pcanXX -> canXX
		 */
		snprintf(name, IFNAMSIZ-1, CAN_NETDEV_NAME, minor);

	} else {

		/* e.g. assign=pcan32:can1,pcan41:can2 */
		int peaknum, netnum;
		char *ptr = pa;

		while (ptr < (pa + strlen(pa))) {
			/* search first 'p' from pcanXX */
			ptr = strchr(ptr, 'p');
			if (!ptr)
				return; /* no match => quit */

			if (sscanf(ptr, DEVICE_NAME "%d:can%d", &peaknum,
								&netnum) != 2) {
				pr_info(DEVICE_NAME
					": bad parameter format in netdevice "
					"assignment.\n");
				return; /* bad parameter format => quit */
			}

			if (peaknum == minor) {
				snprintf(name, IFNAMSIZ-1, CAN_NETDEV_NAME,
									netnum);
				break; /* done */
			}
			ptr++; /* search for next 'p' */
		}
	}

	if (*name)
		pcan_check_ifname(name);
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
static struct can_bittiming_const *
	pcan_netdev_convert_bt_caps(struct can_bittiming_const *pconst,
				    const struct pcanfd_bittiming_range *pcaps)
{
	if (!pcaps)
		return NULL;

	memset(pconst, '\0', sizeof(*pconst));

	strncpy(pconst->name, DEVICE_NAME, sizeof(pconst->name));
	pconst->tseg1_min = pcaps->tseg1_min;
	pconst->tseg1_max = pcaps->tseg1_max;
	pconst->tseg2_min = pcaps->tseg2_min;
	pconst->tseg2_max = pcaps->tseg2_max;
	pconst->sjw_max = pcaps->sjw_max;
	pconst->brp_min = pcaps->brp_min;
	pconst->brp_max = pcaps->brp_max;
	pconst->brp_inc = pcaps->brp_inc;

	return pconst;
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 194)
static struct can_tdc_const *
	pcan_netdev_convert_tdc_caps(struct can_tdc_const *pconst)
{
	memset(pconst, '\0', sizeof(*pconst));

	/* ssp = tdcv + tdco */
	pconst->tdco_min = PCANXL_SSP_OFFSET_MIN;
	pconst->tdco_max = PCANXL_SSP_OFFSET_MAX;

	return pconst;
}
#endif
	
#ifdef INCLUDE_CANXL_SUPPORT
/* need struct can_pwm_const */
static struct can_pwm_const *
	pcan_netdev_convert_pwm_caps(struct can_pwm_const *pconst,
				     const struct pcanxl_pwm_range *pcaps)
{
	if (!pcaps)
		return NULL;

	memset(pconst, '\0', sizeof(*pconst));
	pconst->pwms_min = pcaps->pwms_min;
	pconst->pwms_max = pcaps->pwms_max;
	pconst->pwml_min = pcaps->pwml_min;
	pconst->pwml_max = pcaps->pwml_max;
	pconst->pwmo_min = pcaps->pwmo_min;
	pconst->pwmo_max = pcaps->pwmo_max;

	return pconst;
}
#endif
#endif

static void pcan_netdev_do_restart(struct pcandev *pdev)
{
	pcan_set_tx_engine(pdev, TX_ENGINE_STOPPED);

	/* re-open the device itself */
	pcanxl_dev_open(pdev, &pdev->init_settings);
}

#if defined(USES_PCAN_RESTART) || defined(LINUX_CAN_RESTART_TIMER)
/*
 * SHOULD do what it is done by linux-can can_restart() function
 */
static void pcan_netdev_restart_work(struct work_struct *work)
{
	struct delayed_work *dwork = to_delayed_work(work);

#ifdef LINUX_CAN_RESTART_TIMER
	struct pcandev *pdev = container_of(dwork, struct pcandev,
						restart_work);
	pcan_netdev_do_restart(pdev);
#else
	struct pcan_priv *priv = container_of(dwork, struct pcan_priv,
						can.restart_work);
	struct pcandev *pdev = priv->dev;
	struct sk_buff *skb;
	struct can_frame *cf;
	int err;

	/* copied from can_restart(): we have  no choice, can_restart()
	 * is not public.
	 */
	/* Since 6.5.12, BUG_ON() is replaced by a simple error */
	//BUG_ON(netif_carrier_ok(pdev->netdev));
	if (netif_carrier_ok(pdev->netdev))
		netdev_err(pdev->netdev, "Attempt to restart for bus-off recovery, but carrier is OK?\n");

	/* can_flush_echo_skb(dev.c) is static. Since our echo_skb_max is 0,
	 * this call is useless... */
	/* send restart message upstream */
	skb = alloc_can_err_skb(pdev->netdev, &cf);
	if (skb == NULL) {
		err = -ENOMEM;
		goto restart;
	}
	cf->can_id |= CAN_ERR_RESTARTED;

	netif_rx(skb);

	/* error packets are no more counted as rx packets in modern linux-can*/
restart:
	priv->can.can_stats.restarts++;

	/* Now restart the device */
	err = priv->can.do_set_mode(pdev->netdev, CAN_MODE_START);

#ifdef FIX_CAN_RESTART_CARRIER_ON
	/* Donot put carrier on here because do_set_mode() may not be atomic
	 * and BUS_OFF state can be reached (and so, can_bus_off() can be
	 * called) before going back here... The below netif_carrier_on() is
	 * the cause of restart mechanism malfunction when the delay is short
	 * (~ 10 ms)
	 */
#else
	netif_carrier_on(pdev->netdev);
#endif

	if (err)
		netdev_err(pdev->netdev, "Error %d during restart", err);
	else
		netdev_info(pdev->netdev, "restarted\n");
#endif
}
#endif

static int pcan_netdev_set_mode(struct net_device *ndev, enum can_mode mode)
{
	struct pcan_priv *priv = netdev_priv(ndev);
	struct pcandev *pdev = pcan_netdev_get_dev(priv);

	if (!pdev)
		return -ENODEV;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(%s CAN%u mode=%d)\n",
		__func__, pdev->adapter->name, pcan_idx(pdev)+1, mode);
#endif
	switch (mode) {

	case CAN_MODE_START:

#ifdef LINUX_CAN_RESTART_TIMER
		/* do restart in a safe context */
		schedule_delayed_work(&pdev->restart_work, 0);
#else
		/* we're running in a safe context */
		pcan_netdev_do_restart(pdev);
#endif

		break;

	default:
		return -EOPNOTSUPP;
	}

	return 0;
}

static int pcan_netdev_get_berr_counter(const struct net_device *ndev,
					struct can_berr_counter *bec)
{
	struct pcan_priv *priv = netdev_priv(ndev);
	struct pcandev *pdev;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(ndev=%p priv=%p)\n",
		__func__, ndev, priv);
#endif

	if (!priv)
		return -ENODEV;

	pdev = pcan_netdev_get_dev(priv);
	if (!pdev)
		return -ENODEV;

	bec->txerr = pdev->tx_error_counter;
	bec->rxerr = pdev->rx_error_counter;

	return 0;
}

/* AF_CAN netdevice: register network device
 *
 * Note that this function might be called from interrupt context.
 */
int pcan_netdev_register(struct pcandev *pdev)
{
	struct net_device *ndev;
	struct pcan_priv *priv;
	char name[IFNAMSIZ] = {0};
	char *can_type = "CAN";

	pcan_netdev_create_name(name, pdev);

	if (!name[0]) {
		/* use the default: autoassignment */
		strncpy(name, CAN_NETDEV_NAME, IFNAMSIZ-1);
	}

#ifdef LINUX_26

#ifdef USES_ALLOC_CANDEV
	ndev = alloc_candev(sizeof(*priv), 0);
	if (!ndev) {
		pr_err(DEVICE_NAME ": out of memory\n");
		return 1;
	}

	strncpy(ndev->name, name, sizeof(ndev->name));

	priv = netdev_priv(ndev);

#else

#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 17, 0)
	ndev = alloc_netdev(sizeof(*priv), name, pcan_netdev_init);
#else
	ndev = alloc_netdev(sizeof(*priv), name, NET_NAME_UNKNOWN,
			pcan_netdev_init);
#endif

	if (!ndev) {
		pr_err(DEVICE_NAME ": out of memory\n");
		return 1;
	}

	priv = netdev_priv(ndev);

	/* copied from alloc_candev() */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 33)
	priv->can.echo_skb_max = 0;
#endif
	priv->can.state = CAN_STATE_STOPPED;

#endif /* USES_ALLOC_CANDEV */

#ifdef LINUX_CAN_RESTART_TIMER
	init_timer(&priv->can.restart_timer);

#elif defined(USES_PCAN_RESTART)
	/* Since 4.8, can_bus_off(dev.c) schedules delayed work to run in a
	 * while. So the delayed work struct MUST be initialized here.
	 * Unfortunately, can_restart_work(dev.c) is not public, so we have to
	 * set our own delayed work callback.
	 *
	 * Unfortunately (again), can_restart_work(dev.c) calls
	 * can_restart(dev.c) which is not public too.
	 *
	 * So, our pcan_netdev_restart_work() will have to do the job as
	 * can_restart() does.
	 */
	INIT_DELAYED_WORK(&priv->can.restart_work, pcan_netdev_restart_work);
#endif

	priv->can.do_set_mode = pcan_netdev_set_mode;

#if LINUX_VERSION_CODE > KERNEL_VERSION(2, 6, 28)
	ndev->netdev_ops  = &pcan_netdev_ops;
#else
	ndev->open = pcan_netdev_open;
	ndev->stop = pcan_netdev_close;
	ndev->hard_start_xmit = pcan_netdev_start_xmit;
	ndev->get_stats = pcan_netdev_get_stats;
#endif

	/* while our implementation doesn't put back sent frames into rx path,
	 * then we can't say we do any ECHO!
	 */

	ndev->dev_id = (u16)pdev->can_idx;
#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 15, 0)
	ndev->dev_port = (u16)pdev->can_idx;
#endif

	if (defclk) {
		const struct pcanfd_available_clocks *pc = pdev->clocks_list;
		char *sep = NULL;

		/* if this pcan device is not part of the defclk
		 * string, use its default clock
		 */
		u32 clk = pdev->sysclock_Hz, tmp32;

		/* first, search if there is no global definition for the
		 * new default clock for all the CAN devices:
		 * "defclk=x"
		 */
		int l = strtounit(defclk, &tmp32, "kM" ), i;

#ifdef DEBUG_DEFCLK
		pr_info(DEVICE_NAME
			": does \"defclk=%s\" define a global value? "
			"l=%d tmp32=%u\n", defclk, l, tmp32);
#endif
		if (l < 0) {
			char pcan_name[16], *f;

			/* there is no global definition. 
			 * look now for a specific one:
			 * "defclk=pcanx:x,"
			 */
			int ln = scnprintf(pcan_name, sizeof(name),
					   DEVICE_NAME "%u:", pdev->nMinor);

			f = strstr(defclk, pcan_name);
#ifdef DEBUG_DEFCLK
			pr_info(DEVICE_NAME
				": does \"defclk=%s\" contain \"%s\"? "
				"f=%p\n", defclk, pcan_name, f);
#endif
			if (f) {

				/* found it! */
				f += ln;

				/* replace any ',' by tmp EOL */
				sep = strchr(f, ',');
				if (sep)
					*sep = '\0';

				l = strtounit(f, &tmp32, "kM" );
#ifdef DEBUG_DEFCLK
				pr_info(DEVICE_NAME
					": does \"defclk=%s\" define a new clk "
					"value for pcan%u? l=%d tmp32=%u\n",
					defclk, pdev->nMinor, l, tmp32);
#endif
			}
		}

		/* if a clk value is defined for this dev and this new value
		 * is different from 0, it could be used
		 */
		if ((l > 0) && (tmp32))

			/* defclk=MHz value: check if exists */
			clk = tmp32;

		/* restore cmdline as it was */
		if (sep)
			*sep = ',';

		/* check now if clk is known by the current device */
		for (i = 0; i < pc->count; i++)
			if (clk == pc->list[i].clock_Hz)
				break;

		/* if yes and if it is not the default one, then rebuild
		 * bittiming settings
		 */
		if ((i < pc->count) && (clk != pdev->sysclock_Hz)) {
#ifdef DEBUG_DEFCLK
			pr_info(DEVICE_NAME ": " DEVICE_NAME "%u: "
				"default clock set to %uHz\n",
				pdev->nMinor, tmp32);
#endif

			/* Yep! Use it */
			pdev->sysclock_Hz = clk;

			/* convert "bitrate" into new bittiming according to
			 * new clk
			 */
			pcan_bitrate_to_bittiming( &pdev->init_settings.nominal,
				pdev->bittiming_caps,
				pdev->sysclock_Hz);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 15, 0)
			/* convert "dbitrate" into new bittiming according to
			 * new clk
			 */
			if (pdev->features & PCAN_DEV_FD_RDY) {

				pcan_bitrate_to_bittiming(
					&pdev->init_settings.fd_data,
					pdev->fd_bittiming_caps,
					pdev->sysclock_Hz);
			}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 1, 0)
			/* convert "xlbitrate" into new bittiming according to
			 * new clk
			 */
			if (pdev->features & PCAN_DEV_XL_RDY) {

				pcan_bitrate_to_bittiming(
					&pdev->init_settings.xl_data,
					pdev->xl_bittiming_caps,
					pdev->sysclock_Hz);
			}
#endif
#endif
		}
	}

	priv->can.clock.freq = pdev->sysclock_Hz;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(4, 16, 0)
	priv->can.bitrate_max = 1 * MEGA /* bps */;
#endif

	/* mainline drivers don't set any default bitrate */
	/* default supported ctrlmode for all PCAN interfaces */
	priv->can.ctrlmode_supported = CAN_CTRLMODE_3_SAMPLES |
#ifdef CAN_CTRLMODE_CC_LEN8_DLC
				       /* All PEAK-System devices support it */
				       CAN_CTRLMODE_CC_LEN8_DLC |
#endif
				       CAN_CTRLMODE_LISTENONLY;

	/* if the device does support it, then export that LOOPBACK is also
	 * supported
	 */
	if (pdev->features & PCAN_DEV_SLF_RDY)
		priv->can.ctrlmode_supported |= CAN_CTRLMODE_LOOPBACK;

	/* if the device does support it, then export that ONE_SHOT is also
	 * supported
	 */
	if (pdev->features & PCAN_DEV_SNG_RDY)
		priv->can.ctrlmode_supported |= CAN_CTRLMODE_ONE_SHOT;

	/* if the device does support it, then export that BERR_REPORTING is
	 * also supported
	 */
	if (pdev->features & PCAN_DEV_ERRCNT_RDY) {
		priv->can.ctrlmode_supported |= CAN_CTRLMODE_BERR_REPORTING;
		priv->can.do_get_berr_counter = pcan_netdev_get_berr_counter;
	}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 6, 0)
	/* registering via register_candv() enables to play with bitrates too */
	priv->can.bittiming_const = pcan_netdev_convert_bt_caps(&priv->bt_const,
							pdev->bittiming_caps);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 15, 0)

	/* if an open_fd entry point is defined, then the device is CAN-FD */
	if (pdev->features & PCAN_DEV_FD_RDY) {

		priv->can.ctrlmode_supported |= CAN_CTRLMODE_FD;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 18, 5)
#if LINUX_VERSION_CODE >= KERNEL_VERSION(4, 16, 0)
		priv->can.bitrate_max = 8 * MEGA /* bps */;
#endif
		priv->can.ctrlmode_supported |= CAN_CTRLMODE_FD_NON_ISO;
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 15, 194)
		/* TDC is possible in CANFD for CANX XL device only */
		if (pdev->features & PCAN_DEV_XL_RDY)
			priv->can.ctrlmode_supported |= CAN_CTRLMODE_TDC_AUTO;

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)
		priv->can.fd.data_bittiming_const =
#else
		priv->can.data_bittiming_const =
#endif
			pcan_netdev_convert_bt_caps(&priv->fd_bt_const,
						    pdev->fd_bittiming_caps);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)
		priv->can.fd.tdc_const =
#else
		priv->can.tdc_const =
#endif
			pcan_netdev_convert_tdc_caps(&priv->tdc_const);
#endif /* 5.15.194 */

		can_type = "CAN-FD";
	}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(3, 17, 0)
	if (pdev->features & PCAN_DEV_SELF_ACK_RDY)
		priv->can.ctrlmode_supported |= CAN_CTRLMODE_PRESUME_ACK;
#endif

#ifdef INCLUDE_CANXL_SUPPORT

	/* if an open_xl entry point is defined, then the device is CAN-XL */
	if (pdev->features & PCAN_DEV_XL_RDY) {

		priv->can.bitrate_max = 20 * MEGA /* bps */;

		priv->can.ctrlmode_supported |= CAN_CTRLMODE_XL |
						CAN_CTRLMODE_XL_TDC_AUTO |
#ifdef CAN_CTRLMODE_XL_ERR_SIGNAL
						CAN_CTRLMODE_XL_ERR_SIGNAL |
#endif
						CAN_CTRLMODE_RESTRICTED |
						CAN_CTRLMODE_XL_TMS;

		priv->can.xl.data_bittiming_const =
			pcan_netdev_convert_bt_caps(&priv->xl_bt_const,
						    pdev->xl_bittiming_caps);
		priv->can.xl.pwm_const =
			pcan_netdev_convert_pwm_caps(&priv->xl_pwm_const,
						     pdev->xl_pwm_caps);
		priv->can.xl.tdc_const =
			pcan_netdev_convert_tdc_caps(&priv->tdc_const);

		priv->can.fd.tdc_const = priv->can.xl.tdc_const;

		can_type = "CAN-XL";
	}
#endif	/* INCLUDE_CANXL_SUPPORT */

#endif	/* 3.15.0 */

	SET_NETDEV_DEV(ndev, pcandev_to_dev(pdev));

	/* 3.6.0+: need to register as candev for CAN-FD support */
	if (register_candev(ndev)) {
#else
	SET_NETDEV_DEV(ndev, pcandev_to_dev(pdev));

	if (register_netdev(ndev)) {
#endif
		pr_info(DEVICE_NAME ": Failed registering netdevice\n");
		free_netdev(ndev);
		return 1;
	}

#else /* 3.6.0 LINUX_26 */

	ndev = (struct net_device*)pcan_malloc(sizeof(struct net_device),
					       GFP_KERNEL);
	if (!ndev) {
		pr_err(DEVICE_NAME ": out of memory\n");
		return 1;
	}

	memset(ndev, 0, sizeof(struct net_device));

	priv = pcan_malloc(sizeof(*priv), GFP_KERNEL);
	if (!priv) {
		pr_err(DEVICE_NAME ": out of memory\n");
		pcan_free(ndev);
		return 1;
	}

	memset(priv, 0, sizeof(struct pcan_priv));
	ndev->priv = priv;

	/* fill net_device structure */
	pcan_netdev_init(ndev);

	ndev->open = pcan_netdev_open;
	ndev->stop = pcan_netdev_close;
	ndev->hard_start_xmit = pcan_netdev_start_xmit;
	ndev->get_stats = pcan_netdev_get_stats;

	ndev->dev_id = (u16)pdev->can_idx;

	strncpy(ndev->name, name, IFNAMSIZ-1); /* name the device */

	SET_NETDEV_DEV(ndev, pcandev_to_dev(pdev));

	SET_MODULE_OWNER(ndev);

	if (register_netdev(ndev)) {
		pr_info(DEVICE_NAME ": Failed registering netdevice\n");
		pcan_free(priv);
		pcan_free(ndev);
		return 1;
	}

#endif /* LINUX_26 */

	/* Make references between pcan device and netdevice */
	priv->dev = pdev;
	pdev->netdev = ndev;

#ifdef LINUX_CAN_RESTART_TIMER
	/* init delayed work struct that handles restart out of any
	 * interrupt context
	 */
	INIT_DELAYED_WORK(&pdev->restart_work, pcan_netdev_restart_work);
#endif
	pr_info(DEVICE_NAME ": registered %s netdevice %s for %s hw (%d,%d)\n",
	       can_type, ndev->name, pdev->type, pdev->nMajor, pdev->nMinor);

	return 0;
}

/* AF_CAN netdevice: unregister network device */
int pcan_netdev_unregister(struct pcandev *pdev)
{
	struct net_device *ndev = pdev->netdev;

	if (!ndev)
		return 1;

	/* mark as unregistered to be sure not to loop here again */
	pdev->netdev = NULL;

#if defined(DEBUG_TRACE) || defined(DEBUG_OPEN)
	pr_info(DEVICE_NAME ": %s(%s)\n", __func__, ndev->name);
#endif
#ifdef LINUX_CAN_RESTART_TIMER
	cancel_delayed_work_sync(&pdev->restart_work);
#endif

#if LINUX_VERSION_CODE < KERNEL_VERSION(3, 6, 0)
	unregister_netdev(ndev);
#else
	unregister_candev(ndev);
#endif

#ifndef LINUX_26
	{
		struct pcan_priv *priv = netdev_priv(ndev);
		if (priv)
			pcan_free(priv);
	}
#endif

	return 0;
}

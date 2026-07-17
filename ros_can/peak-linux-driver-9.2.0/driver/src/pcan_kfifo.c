/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcan_fifo.h - all about fifo buffer management
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
 */
#include "src/pcan_common.h"
#include "src/pcan_main.h"

/* pcan_kfifo_compat.h is pulled in via pcan_common.h above;
 * it provides either the native <linux/kfifo.h> (>= 2.6.33) or the
 * self-contained compatibility implementation (< 2.6.33).
 */

//#define DEBUG_TRACE

#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 10, 0)
/**
 * kfifo_skip_count - skip output data
 * @fifo: address of the fifo to be used
 * @count: count of data to skip
 */
#define	kfifo_skip_count(fifo, count) do { \
	typeof((fifo) + 1) __tmp = (fifo); \
	const size_t __recsize = sizeof(*__tmp->rectype); \
	struct __kfifo *__kfifo = &__tmp->kfifo; \
	if (__recsize) \
		__kfifo_skip_r(__kfifo, __recsize); \
	else \
		__kfifo->out += (count); \
} while(0)
#endif

/*
 * int pcan_kfifo_init(struct pcan_kfifo *fifo, void *buf, unsigned int size)
 */
int pcan_kfifo_init(struct pcan_kfifo *fifo, void *buf, unsigned int size)
{
#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(size=%u)\n", __func__, size);
#endif

	pcan_lock_init(&fifo->lock);
	fifo->count = 0;
	fifo->data_len = 0;
	fifo->total_count = 0;
	fifo->total_data_len = 0;
	return kfifo_init(&fifo->kfifo, buf, size);
}

void pcan_kfifo_reset(struct pcan_kfifo *fifo)
{
	unsigned long flags;

	pcan_lock_get_irqsave(&fifo->lock, flags);
	kfifo_reset(&fifo->kfifo);
	fifo->count = 0;
	fifo->data_len = 0;
	fifo->total_count = 0;
	fifo->total_data_len = 0;
	pcan_lock_put_irqrestore(&fifo->lock, flags);
}

/*
 * Saves a message made of an header and data in the kfifo.
 *
 * Note that there's always room to add at least one more header (the
 * emergency header), which can be used to store an emergency message of the
 * OVERFLOW type.
 *
 * @RETURN:
 * < 0 if error,
 * the count of messages saved into otherwise.
 */
static int pcan_fifo_in(struct pcan_kfifo *fifo,
			void *hdr, int sizeof_hdr,
			void *data, int sizeof_data)
{
	int fifo_avail, fifo_needed = sizeof_hdr + sizeof_data;
	unsigned long flags;
	int err;

	pcan_lock_get_irqsave(&fifo->lock, flags);

	fifo_avail = kfifo_avail(&fifo->kfifo) - sizeof_hdr;
	if (fifo_needed > fifo_avail) {
#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME
			": %s(): can't put %d bytes into %d bytes kfifo\n",
			__func__, fifo_needed, fifo_avail);
#endif
		/* if there is a chance to put at least sizeof_hdr next */
		err = fifo_avail >= 0 ? -ENOSPC : -ESPIPE;
		goto lbl_unlock;
	}

	err = kfifo_in(&fifo->kfifo, hdr, sizeof_hdr);
	if (err != sizeof_hdr) {
		pr_err(DEVICE_NAME
		       ": %s(): can't put %d hdr bytes into kfifo!\n",
		       __func__, sizeof_hdr);
		err = -ESPIPE;
		goto lbl_unlock;
	}

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(): put %d hdr bytes into kfifo\n",
		__func__, sizeof_hdr);
#endif

	if ((sizeof_data > 0) && data) {
		err = kfifo_in(&fifo->kfifo, data, sizeof_data);
		if (err != sizeof_data) {
			err = -ESPIPE;
			goto lbl_unlock;
		}

		fifo->data_len += sizeof_data;
		fifo->total_data_len += sizeof_data;

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(): put %d data bytes into kfifo\n",
			__func__, sizeof_data);
	} else {
		pr_info(DEVICE_NAME
			": %s(): put no (%d) data bytes into kfifo\n",
			__func__, sizeof_data);
#endif
	}

	fifo->total_count++;
	err = ++fifo->count;

lbl_unlock:
	pcan_lock_put_irqrestore(&fifo->lock, flags);

	return err;
}

/*
 * @RETURN:
 * < 0 if error,
 * the count of message saved into otherwise.
 */
static int pcan_fifo_in_user(struct pcan_kfifo *fifo,
			     void *hdr, int sizeof_hdr,
			     void __user *udata, int sizeof_data)
{
	int fifo_avail, fifo_needed = sizeof_hdr + sizeof_data;
	unsigned long flags;
	int err;

	pcan_lock_get_irqsave(&fifo->lock, flags);

	fifo_avail = kfifo_avail(&fifo->kfifo) - sizeof_hdr;
	if (fifo_needed > fifo_avail) {
#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME
			": %s(): can't put %d bytes into %d bytes kfifo\n",
			__func__, fifo_needed, fifo_avail);
#endif
		/* if there is a chance to pout at least sizeof_hdr next */
		err = fifo_avail >= 0 ? -ENOSPC : -ESPIPE;
		goto lbl_unlock;
	}

	err = kfifo_in(&fifo->kfifo, hdr, sizeof_hdr);
	if (err != sizeof_hdr) {
		pr_err(DEVICE_NAME
		       ": %s(): can't put %d hdr bytes into kfifo!\n",
		       __func__, sizeof_hdr);
		err = -ESPIPE;
		goto lbl_unlock;
	}

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(): put %d hdr bytes into kfifo\n",
		__func__, sizeof_hdr);
#endif

	if ((sizeof_data > 0) && udata) {
		unsigned int copied;
		err = kfifo_from_user(&fifo->kfifo, udata, sizeof_data,
				      &copied);
		if (err) {
			pr_err(DEVICE_NAME
			       ": %s(): kfifo_from_user() err %d "
			       "(len=%d copied=%d)\n",
			       __func__, err, sizeof_data, copied);
			goto lbl_unlock;
		}

		fifo->data_len += sizeof_data;
		fifo->total_data_len += sizeof_data;

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME
			": %s(): put %d user data bytes into kfifo\n",
			__func__, copied);
	} else {
		pr_info(DEVICE_NAME
			": %s(): put no (%d) user data bytes into kfifo\n",
			__func__, sizeof_data);
#endif
	}

	fifo->total_count++;
	err = ++fifo->count;

lbl_unlock:
	pcan_lock_put_irqrestore(&fifo->lock, flags);

	return err;
}

/*
 * @RETURN:
 *
 * < 0 in case of error,
 * the count of msgs still in the queue otherwise.
 */
static int pcan_fifo_out(struct pcan_kfifo *fifo,
			 void *hdr, int sizeof_hdr,
			 u8 *data_buf, int hdr_msg_off)
{
	struct pcanxl_msg *msg = (struct pcanxl_msg *)(hdr + hdr_msg_off);
	const int msg_data_size = msg->data_len;
	int msg_data_len;
	unsigned long flags;
	int err;

	err = pcan_kfifo_hdr_out_irqsave(fifo, hdr, sizeof_hdr, flags);
	if (err)
		return err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(): read %d hdr bytes from kfifo\n",
		__func__, sizeof_hdr);
#endif
	msg_data_len = msg->data_len;
	if (msg_data_len <= 0)
		goto lbl_ok;

	if (data_buf) {

		if (msg_data_len > msg_data_size) {
			msg->flags |= PCANXL_MSG_TRUNC_DATA;
			msg_data_len = msg_data_size;
		}

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(): read %d data bytes from kfifo\n",
			__func__, msg_data_len);
#endif

		err = kfifo_out(&fifo->kfifo, data_buf, msg_data_len);
		if (err != msg_data_len) {
			err = -ESPIPE;
			goto lbl_unlock;
		}

		msg_data_len = msg->data_len - err;
		msg->data_len = err;

		fifo->data_len = (fifo->data_len > msg->data_len) ?
				fifo->data_len - msg->data_len : 0;
	}

	if (msg_data_len > 0) {
#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(): (%d data bytes to ignore)\n",
			__func__, msg_data_len);
#endif
		kfifo_skip_count(&fifo->kfifo, msg_data_len);
	}

lbl_ok:
	err = (fifo->count > 0) ? --fifo->count : 0;

lbl_unlock:
	pcan_lock_put_irqrestore(&fifo->lock, flags);

	return err;
}

#ifndef NETDEV_SUPPORT
/*
 * @RETURN:
 *
 * < 0 in case of error,
 * the count of msgs still in the queue otherwise.
 */
static int pcan_fifo_out_user(struct pcan_kfifo *fifo,
			 void *hdr, int sizeof_hdr,
			 void __user *udata_buf, int hdr_msg_off)
{
	struct pcanxl_msg *msg = (struct pcanxl_msg *)(hdr + hdr_msg_off);
	const int msg_data_size = msg->data_len;
	int msg_data_len;
	unsigned long flags;
	int err;

	err = pcan_kfifo_hdr_out_irqsave(fifo, hdr, sizeof_hdr, flags);
	if (err)
		return err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(): read %d hdr bytes from kfifo\n",
		__func__, sizeof_hdr);
#endif
	msg_data_len = msg->data_len;
	if (msg_data_len <= 0)
		goto lbl_ok;

	if (udata_buf) {
		unsigned int copied;

		if (msg_data_len > msg_data_size) {
			msg->flags |= PCANXL_MSG_TRUNC_DATA;
			msg_data_len = msg_data_size;
		}

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(): read %d data bytes from kfifo\n",
			__func__, msg_data_len);
#endif

		/* Note: copy_to_user() returns the number of bytes that cannot
		 * be copied. If xxx_to_user() fails to copy *ALL* the bytes,
		 * it's because of a memory alignment issue. Therefore, to be
		 * able to transfer 2KB chunks then the user memory SHOULD be
		 * allocated!
		 */
		err = kfifo_to_user(&fifo->kfifo, udata_buf, msg_data_len,
				    &copied);
		if (err) {
			pr_err(DEVICE_NAME
			       ": %s(): kfifo_to_user() err %d "
			       "(len=%d copied=%d)\n",
			       __func__, err, msg_data_len, copied);
			goto lbl_unlock;
		}

		msg_data_len = msg->data_len - copied;
		msg->data_len = copied;

		fifo->data_len = (fifo->data_len > msg->data_len) ?
				fifo->data_len - msg->data_len : 0;
	}

	if (msg_data_len > 0) {
#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(): (%d data bytes to ignore)\n",
			__func__, msg_data_len);
#endif
		kfifo_skip_count(&fifo->kfifo, msg_data_len);
	}

lbl_ok:
	err = (fifo->count > 0) ? --fifo->count : 0;

lbl_unlock:
	pcan_lock_put_irqrestore(&fifo->lock, flags);

	return err;
}
#endif

/*
 * int pcan_txfifo_in(struct pcandev *dev, struct pcanxl_txmsg *tx,
 *		      u8 *data_buf)
 * RETURN:
 *
 * > 0	Number of items currently in the fifo
 * < 0	Error
 */
int pcan_txfifo_in(struct pcandev *dev, struct pcanxl_txmsg *tx,
		   u8 *data_buf)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
		__func__, tx->msg.type, tx->msg.id, tx->msg.data_len);
#endif
	err =  pcan_fifo_in(&dev->tx_fifo, tx, sizeof(*tx), data_buf,
			    tx->msg.data_len);
	if (err == -ENOSPC)
		pcan_set_status_bit(dev, CAN_ERR_XMTFULL);

	return err;
}

int pcan_txfifo_in_user(struct pcandev *dev, struct pcanxl_txmsg *tx,
			void __user *udata_buf)
{
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
		__func__, tx->msg.type, tx->msg.id, tx->msg.data_len);
#endif
	err =  pcan_fifo_in_user(&dev->tx_fifo, tx, sizeof(*tx), udata_buf,
				 tx->msg.data_len);
	if (err == -ENOSPC)
		pcan_set_status_bit(dev, CAN_ERR_XMTFULL);

	return err;
}

/*
 * int pcan_txfifo_hdr_peek(struct pcandev *dev, struct pcanxl_txmsg *tx)
 */
int pcan_txfifo_hdr_peek(struct pcandev *dev, struct pcanxl_txmsg *tx)
{
	int err = kfifo_out_peek(&dev->tx_fifo.kfifo, tx, sizeof(*tx));

#ifdef DEBUG_TRACE
	if (err > 0)
		pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
			__func__, tx->msg.type, tx->msg.id, tx->msg.data_len);
#endif
	return err;
}

/*
 * int pcan_txfifo_out(struct pcandev *dev, struct pcanxl_txmsg *tx,
 *		       u8 *data_buf)
 */
int pcan_txfifo_out(struct pcandev *dev, struct pcanxl_txmsg *tx,
		    u8 *data_buf)
{
	int err = pcan_fifo_out(&dev->tx_fifo, tx, sizeof(*tx),
				data_buf, offsetof(struct pcanxl_txmsg, msg));
	if (err >= 0) {
		pcan_clear_status_bit(dev, CAN_ERR_XMTFULL);

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
			__func__, tx->msg.type, tx->msg.id, tx->msg.data_len);
#endif
	}
	return err;
}

#ifndef NETDEV_SUPPORT
/*
 * int pcan_rxfifo_in(struct pcandev *dev, struct pcanxl_rxmsg *rx,
 *		      u8 *data_buf)
 */
int pcan_rxfifo_in(struct pcandev *dev, struct pcanxl_rxmsg *rx,
		   u8 *data_buf)
{
	int err;

	/* silently discard messages if we are closing: tasks won't  be able
	 * to read from the Rx fifo anymore
	 */
	if (dev->flags & PCAN_DEV_CLOSING)
		return 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
		__func__, rx->msg.type, rx->msg.id, rx->msg.data_len);
#endif
	err = pcan_fifo_in(&dev->rx_fifo, rx, sizeof(*rx), data_buf,
			    rx->msg.data_len);
	if (err == -ENOSPC)
		pcan_set_status_bit(dev, CAN_ERR_OVERRUN);

	return err;
}

/*
 * int pcan_rxfifo_out(struct pcandev *dev, struct pcanxl_rxmsg *rx,
 *		       u8 *data_buf)
 */
int pcan_rxfifo_out(struct pcandev *dev, struct pcanxl_rxmsg *rx,
		    u8 *data_buf)
{
	int err = pcan_fifo_out(&dev->rx_fifo, rx, sizeof(*rx), data_buf,
				offsetof(struct pcanxl_rxmsg, msg));
	if (err >= 0) {
		pcan_clear_status_bit(dev, CAN_ERR_OVERRUN);

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
			__func__, rx->msg.type, rx->msg.id, rx->msg.data_len);
#endif
	}

	return err;
}

int pcan_rxfifo_out_user(struct pcandev *dev, struct pcanxl_rxmsg *rx,
			 void __user *udata_buf)
{
	int err = pcan_fifo_out_user(&dev->rx_fifo, rx, sizeof(*rx), udata_buf,
				     offsetof(struct pcanxl_rxmsg, msg));
	if (err >= 0) {
		pcan_clear_status_bit(dev, CAN_ERR_OVERRUN);

#ifdef DEBUG_TRACE
		pr_info(DEVICE_NAME ": %s(type=%d id=%d len=%d)\n",
			__func__, rx->msg.type, rx->msg.id, rx->msg.data_len);
#endif
	}

	return err;
}

#endif

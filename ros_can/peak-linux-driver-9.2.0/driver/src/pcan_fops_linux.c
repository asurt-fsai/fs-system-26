/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcan_fops_linux.c - all file operation functions, exports only struct fops
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
 *               Edouard Tisserant <edouard.tisserant@lolitech.fr> XENOMAI
 *               Laurent Bessard <laurent.bessard@lolitech.fr> XENOMAI
 *               Oliver Hartkopp <oliver.hartkopp@volkswagen.de> socket-CAN
 *               Marcel Offermans <marcel.offermans@luminis.nl>
 *               Arno <a.vdlaan@hccnet.nl>
 *               John Privitera <JohnPrivitera@dciautomation.com>
 */
/* #define DEBUG */
/* #undef DEBUG */
static struct pcandev *pcan_get_dev_lock(struct pcanusr *pud)
{
	struct pcandev *dev = pcan_get_dev(pud);
	if (dev)
		pcan_lock_dev(dev);

	return dev;
}

/* return a locked (mutex) device according to its (major, minor) */
static struct pcandev* pcan_search_dev_lock(int major, int minor)
{
	struct pcandev *dev = pcan_search_dev(major, minor);
	if (dev)
		pcan_lock_dev(dev);

	return dev;
}

/* put (unlock) a locked device */
static int pcan_put_dev_unlock(struct pcandev *dev, long err)
{
	if (dev)
		pcan_unlock_dev(dev);

	return pcan_put_dev(dev, err);
}

/* is called when the path is opened */
static int pcan_open(struct inode *inode, struct file *filep)
{
	struct pcandev *dev;
	struct pcanusr *usr;
	int _major = MAJOR(inode->i_rdev);
	int _minor = minor(inode->i_rdev);
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(minor=%d, f_flags=%08xh (%o) f_mode=%08xh)\n",
		__func__, _minor, filep->f_flags, filep->f_flags,
		filep->f_mode);
#endif
	dev = pcan_search_dev_lock(_major, _minor);
	if (!dev)
		return -ENODEV;

	/* create file object */
	usr = pcan_malloc(sizeof(struct pcanusr), GFP_KERNEL);
	if (!usr) {
		pr_err(DEVICE_NAME ": %s(): memory allocation failed!\n",
		       __func__);
		return pcan_put_dev_unlock(dev, -ENOMEM);
	}

	/* fill file object and init read and write method buffers */
	usr->dev = dev;

	/* O_RDONLY(0) =>
	 * - O_WRONLY(1) not set
	 * - O_RDWR(2) not set
	 */
	usr->open_flags = filep->f_flags;
	usr->filep = filep;

	if (filep->f_mode & FMODE_READ) {
		usr->nReadRest = 0;
		usr->nTotalReadCount = 0;
		usr->pcReadPointer = usr->pcReadBuffer;
	}

	/* F_MODE_WRITE not set when O_RDONLY used */
	if (filep->f_mode & FMODE_WRITE) {
		usr->nWriteCount = 0;
		usr->pcWritePointer = usr->pcWriteBuffer;
	}

	usr->recv_msgs_list = NULL;

	filep->private_data = (void *)usr;

	/* why? dev->init_settings are filled from:
	 * - dev->def_init_settings which are supposed to be ok
	 * - user settings (see PCANFD_SET_INIT) but ioctl_set_init() handler
	 *   does check them before copying them into dev->init_settings.
	 */
	err = pcan_open_path(dev, usr);
	if (!err)
		return pcan_put_dev_unlock(dev, 0);

	pcan_free(usr);

	return pcan_put_dev_unlock(dev, err);
}

static int pcan_release(struct inode *inode, struct file *filep)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	struct pcandev *dev = pcan_get_dev_lock(usr);

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(dev=%p)\n", __func__, dev);
#endif

	/* free the associated irq and allocated memory */
	if (dev)
		pcan_release_path(dev, usr);

	if (usr)
		pcan_free(usr->recv_msgs_list);

	filep->private_data = pcan_free(usr);

	return pcan_put_dev_unlock(dev, 0);
}

/*
 * is called at user ioctl() with cmd = PCAN_INIT
 */
static int pcan_ioctl_init(struct pcandev *dev, TPCANInit __user *pi)
{
	struct pcanxl_init xli = {};
	TPCANInit init;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	err = copy_from_user(&init, pi, sizeof(init));
	if (err) {
		pr_err(DEVICE_NAME ": %s(): copy_from_user() failure\n",
			__func__);
		return -EFAULT;
	}

	/* convert wBTR0BTR1 (8MHz) value into bitrate value. pxli->clock_Hz
	 * is let 0 so that pcanxl_dev_open() will fill it with device default
	 * clock.
	 */
	return pcanxl_ioctl_set_init(dev, pcan_init_to_xl(dev, &xli, &init));
}

/*
 * is called at user ioctl() with cmd = PCAN_WRITE_MSG
 */
static int pcan_ioctl_write(struct pcandev *dev, TPCANMsg __user *txu,
			    struct pcanusr *usr)
{
	struct pcanxl_txmsg_cc tx;
	TPCANMsg msg;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* get from user space */
	if (copy_from_user(&msg, txu, sizeof(msg))) {
		pr_err(DEVICE_NAME ": %s(): copy_from_user() failure\n",
			__func__);
		err = -EFAULT;
		goto fail;
	}

	/* do some minimal (but mandatory!) check */
	if (msg.LEN > PCANFD_CAN20_MAXDATALEN) {
		pr_err(DEVICE_NAME
			": trying to send msg %xh  with invalid data len %d\n",
			msg.ID, msg.LEN);
		err = -EINVAL;
		goto fail;
	}

	/* convert old-style TPCANMsg into new-style struct pcanxl_txmsg */
	copy_from_cc((struct pcanxl_msg *)&tx.msg, &msg);
	err = pcanxl_ioctl_send_msg(dev, (struct pcanxl_txmsg *)&tx, NULL, usr);
	if (err)
		goto fail;

	return 0;

fail:
#ifdef DEBUG
        pr_err(DEVICE_NAME ": failed to write CAN frame (err %d)\n", err);
#endif
	return err;
}

/*
 * is called at user ioctl() with cmd = PCAN_READ_MSG
 */
static int pcan_ioctl_read(struct pcandev *dev, TPCANRdMsg __user *rxu,
			   struct pcanusr *usr)
{
	struct pcanxl_rxmsg_cc rx;
	TPCANRdMsg msg;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	do {
		rx.msg.data_len = PCANFD_CAN20_MAXDATALEN;
		err = pcanxl_ioctl_recv_msg(dev,
					    (struct pcanxl_rxmsg *)&rx, NULL,
					    usr);
		if (err)
			return err;

		/* Give STATUS msg to application too */
		if (rx.msg.type == PCANFD_TYPE_STATUS)
			break;

		if (!pcan_is_cc((struct pcanxl_msg *)&rx.msg)) {
			pr_err(DEVICE_NAME ": CAN-FD/XL frame discarded "
				"(CAN 2.0 application)\n");
			err = -EINVAL;
		}
	} while (err);

	if (copy_to_user(rxu, copy_to_cc(&msg, (struct pcanxl_msg *)&rx.msg),
			 sizeof(*rxu))) {
		pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			__func__);
		err = -EFAULT;
	}

	return err;
}

/*
 * is called at user ioctl() with cmd = PCAN_GET_STATUS
 */
static int pcan_ioctl_status(struct pcandev *dev, TPSTATUS __user *status)
{
	TPSTATUS local;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	pcan_ioctl_status_common(dev, &local);

	if (copy_to_user(status, &local, sizeof(local))) {
		pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			__func__);
		err = -EFAULT;
		goto fail;
	}

	dev->wCANStatus = 0;
	dev->nLastError = 0;

fail:
	return err;
}

/*
 * is called at user ioctl() with cmd = PCAN_GET_EXT_STATUS
 */
static int pcan_ioctl_extended_status(struct pcandev *dev,
				      TPEXTENDEDSTATUS __user *status)
{
	TPEXTENDEDSTATUS local;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	pcan_ioctl_extended_status_common(dev, &local);

	if (copy_to_user(status, &local, sizeof(local))) {
		pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			__func__);
		err = -EFAULT;
		goto fail;
	}

	dev->wCANStatus = 0;
	dev->nLastError = 0;

fail:
	return err;
}

/*
 * is called at user ioctl() with cmd = PCAN_DIAG
 */
static int pcan_ioctl_diag(struct pcandev *dev, TPDIAG __user *diag)
{
	TPDIAG local;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	pcan_ioctl_diag_common(dev, &local);

	if (copy_to_user(diag, &local, sizeof(local))) {
		pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			__func__);
		err = -EFAULT;
	}

	return err;
}

/*
 * get BTR0BTR1 init values
 */
static int pcan_ioctl_BTR0BTR1(struct pcandev *dev, TPBTR0BTR1 __user *BTR0BTR1)
{
	TPBTR0BTR1 local;
	int err = 0;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	if (copy_from_user(&local, BTR0BTR1, sizeof(local))) {
		pr_err(DEVICE_NAME ": %s(): copy_from_user() failure\n",
			__func__);
		err = -EFAULT;
		goto fail;
	}

	/* this does not influence hardware settings, only BTR0BTR1 values
	 * are calculated
	 */
	local.wBTR0BTR1 = sja1000_bitrate(local.dwBitRate, 0, 0 /* TODO */);
	if (!local.wBTR0BTR1) {
		err = -EINVAL;
		goto fail;
	}

	if (copy_to_user(BTR0BTR1, &local, sizeof(*BTR0BTR1))) {
		pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			__func__);
		err = -EFAULT;
	}

fail:
	return err;
}

/*
 * add a message filter_element into the filter chain or delete all
 * filter_elements
 */
static int pcan_ioctl_msg_filter(struct pcandev *dev,
				 TPMSGFILTER __user *filter)
{
	TPMSGFILTER local_filter;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* filter == NULL -> delete the filter_elements in the chain */
	if (!filter) {
		pcan_delete_filter_all(dev->filter);
		return 0;
	}

	if (copy_from_user(&local_filter, filter, sizeof(local_filter))) {
		pr_err(DEVICE_NAME ": %s(): copy_from_user() failure\n",
			__func__);
		return -EFAULT;
	}

	return pcan_add_filter(dev->filter, local_filter.FromID,
				local_filter.ToID, local_filter.MSGTYPE);
}

/*
 * set or get extra parameters from the devices
 */
static int pcan_ioctl_extra_parameters(struct pcandev *dev,
				       TPEXTRAPARAMS __user *params,
				       int sizeof_extra_params)
{
	TPEXTRAPARAMS local;
	int err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d, s=%d)\n",
		__func__, dev->nMinor, sizeof_extra_params);
#endif

	if (copy_from_user(&local, params, sizeof_extra_params)) {
		pr_err(DEVICE_NAME ": %s(): copy_from_user() failure\n",
		       __func__);
		err = -EFAULT;
		goto fail;
	}

	err = _pcan_ioctl_extra_parameters(dev, &local, sizeof_extra_params);
	if (!err)
		if (copy_to_user(params, &local, sizeof_extra_params)) {
			pr_err(DEVICE_NAME ": %s(): copy_to_user() failure\n",
			       __func__);
			err = -EFAULT;
		}

fail:
	return err;
}

/* device is considered as locked when entering this function */
static long __pcan_ioctl(struct file *filep, unsigned int cmd, void __user *up,
			 struct pcandev *dev)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	struct pcanxl_init xli;
	struct pcanfd_state fds;
	struct pcanfd_msg fdm;
	int err, l;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d, cmd=%u (NR=%u))\n",
		__func__, dev->nMinor, cmd, _IOC_NR(cmd));
#endif

	switch (cmd) {
	case PCAN_INIT:
		err = pcan_ioctl_init(dev, (TPCANInit __user *)up);
		break;
	case PCAN_READ_MSG:
		/* support blocking and nonblocking IO */
		err = pcan_ioctl_read(dev, (TPCANRdMsg __user *)up, usr);
		break;
	case PCAN_WRITE_MSG:
		/* support blocking and nonblocking IO */
		err = pcan_ioctl_write(dev, (TPCANMsg __user *)up, usr);
		break;
	case PCAN_GET_STATUS:
		err = pcan_ioctl_status(dev, (TPSTATUS __user *)up);
		break;
	case PCAN_GET_EXT_STATUS:
		err = pcan_ioctl_extended_status(dev,
						(TPEXTENDEDSTATUS __user *)up);
		break;
	case PCAN_DIAG:
		err = pcan_ioctl_diag(dev, (TPDIAG __user *)up);
		break;
	case PCAN_BTR0BTR1:
		err = pcan_ioctl_BTR0BTR1(dev, (TPBTR0BTR1 __user *)up);
		break;
	case PCAN_MSG_FILTER:
		err = pcan_ioctl_msg_filter(dev, (TPMSGFILTER __user *)up);
		break;
	case PCAN_EXTRA_PARAMS_8_13:
	case PCAN_EXTRA_PARAMS:
		err = pcan_ioctl_extra_parameters(dev,
						(TPEXTRAPARAMS __user *)up,
						_IOC_SIZE(cmd));
		break;

	/* CAN-FD/CAN-XL new API */
	case PCANFD_SET_INIT:
	case PCANXL_SET_INIT:
#ifdef DEBUG_CHRDEV_SIZEOF
		/* sizeof		32-bit	64-bit
		 * struct pcanfd_init	80	80
		 * struct pcanxl_init	124	124
		 *
		 * IO_SIZE(cmd) = 124 => struct pcanxl_init
		 */
		pr_info(DEVICE_NAME ": _IOC_SIZE=%u vs. "
			"sizeof struct[pcanfd_init=%u pcanxl_init=%u]\n",
			_IOC_SIZE(cmd),
			(unsigned )sizeof(struct pcanfd_init),
			(unsigned )sizeof(struct pcanxl_init));
#endif
		err = copy_from_user(&xli, up, _IOC_SIZE(cmd));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_from_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
		}

		/* To be SURE */
		if (cmd == PCANFD_SET_INIT)
			xli.flags &= ~PCANXL_INIT_XL;

		err = pcanxl_ioctl_set_init(dev, &xli);
		break;

	case PCANFD_GET_INIT:
	case PCANXL_GET_INIT:
#ifdef DEBUG_CHRDEV_SIZEOF
		pr_info(DEVICE_NAME ": _IOC_SIZE=%u vs. "
			"sizeof struct[pcanfd_init=%u pcanxl_init=%u]\n",
			_IOC_SIZE(cmd),
			(unsigned )sizeof(struct pcanfd_init),
			(unsigned )sizeof(struct pcanxl_init));
#endif
		err = pcanxl_ioctl_get_init(dev, &xli);
		if (err)
			break;

		err = copy_to_user(up, &xli, _IOC_SIZE(cmd));
		if (err) {
			pr_err(DEVICE_NAME ": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
		}
		break;

	case PCANFD_RESET:
		err = pcanxl_ioctl_reset(dev, (unsigned long )up);
		break;

	case PCANFD_GET_STATE:
		err = pcanxl_ioctl_get_state(dev, &fds);
		if (err)
			break;

		err = copy_to_user(up, &fds, sizeof(fds));
		if (err) {
			pr_err(DEVICE_NAME ": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
		}	
		break;

#ifdef PCANFD_ADD_FILTER
	case PCANFD_ADD_FILTER:
		if (up) {
			struct pcanfd_msg_filter mf;

			err = copy_from_user(&mf, up, sizeof(mf));
			if (err) {
				pr_err(DEVICE_NAME
					": %s(%u): copy_from_user() failure\n",
					__func__, __LINE__);
				err = -EFAULT;
			}
			err = pcanxl_ioctl_add_filter(dev, &mf);
		} else {
			err = pcanxl_ioctl_add_filter(dev, NULL);
		}
		break;
#endif

	case PCANFD_ADD_FILTERS:
		if (up) {
			struct pcanfd_msg_filters mfl, *pfl;

			l = sizeof(struct pcanfd_msg_filters_0);
			err = copy_from_user(&mfl, up, l);
			if (err) {
				pr_err(DEVICE_NAME
					": %s(%u): copy_from_user() failure\n",
					__func__, __LINE__);
				err = -EFAULT;
				break;
			}

			if (!mfl.count) {
				err = 0;
				break;
			}

			l += mfl.count * sizeof(struct pcanfd_msg_filter);
			pfl = pcan_malloc(l, GFP_KERNEL);
			if (!pfl) {
				pr_err("%s: failed to alloc filter list\n",
						DEVICE_NAME);
				err = -ENOMEM;
				break;
			}

			if (copy_from_user(pfl, up, l)) {
				pcan_free(pfl);
				pr_err(DEVICE_NAME
					": %s(%u): copy_from_user() failure\n",
					__func__, __LINE__);
				err = -EFAULT;
			} else {
				/* re-sync with kernel space content */
				pfl->count = mfl.count;
				err = pcanxl_ioctl_add_filters(dev, pfl);
			}

			pcan_free(pfl);
		} else {
			err = pcanxl_ioctl_add_filters(dev, NULL);
		}
		break;

	case PCANFD_GET_FILTERS:
		if (up) {
			struct pcanfd_msg_filters mfl, *pfl;

			l = sizeof(struct pcanfd_msg_filters_0);
			err = copy_from_user(&mfl, up, l);
			if (err) {
				pr_err(DEVICE_NAME
					": %s(%u): copy_from_user() failure\n",
					__func__, __LINE__);
				err = -EFAULT;
				break;
			}

			if (!mfl.count) {
				err = 0;
				break;
			}

			l += mfl.count * sizeof(struct pcanfd_msg_filter);
			pfl = pcan_malloc(l, GFP_KERNEL);
			if (!pfl) {
				pr_err("%s: failed to alloc filter list\n",
						DEVICE_NAME);
				err = -ENOMEM;
				break;
			}

			pfl->count = mfl.count;
			err = pcanxl_ioctl_get_filters(dev, pfl);

			/* copy the count and the filter received */
			l = sizeof(struct pcanfd_msg_filters_0) +
				pfl->count * sizeof(struct pcanfd_msg_filter);

			if (copy_to_user(up, pfl, l)) {
				pr_err(DEVICE_NAME
					": %s(%u): copy_to_user() failure\n",
					__func__, __LINE__);
				err = -EFAULT;
			}

			pcan_free(pfl);
		} else {
			err = pcanxl_ioctl_get_filters(dev, NULL);
		}
		break;

	case PCANFD_SEND_MSG:
		err = copy_from_user(&fdm, up, sizeof(fdm));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_from_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
			break;
		}
		err = pcanfd_ioctl_send_msg(dev, &fdm, usr);
		break;

	case PCANFD_RECV_MSG:
		err = pcanfd_ioctl_recv_msg(dev, &fdm, usr);
		if (err)
			break;

		err = copy_to_user(up, &fdm, sizeof(fdm));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
			break;
		}
		break;

	case PCANFD_SEND_MSGS:
		err = handle_pcanfd_send_msgs(dev, up, usr, NULL);
		break;

	case PCANFD_RECV_MSGS:
		err = handle_pcanfd_recv_msgs(dev, up, usr, NULL);
		break;

	case PCANFD_GET_AVAILABLE_CLOCKS:
		err = handle_pcanfd_get_av_clocks(dev, up, usr, NULL);
		break;

	case PCANFD_GET_BITTIMING_RANGES:
		err = handle_pcanfd_get_bittiming_ranges(dev, up,
							 usr, NULL);
		break;

	case PCANFD_GET_OPTION:
		err = handle_pcanfd_get_option(dev, up, usr, NULL);
		break;

	case PCANFD_SET_OPTION:
		err = handle_pcanfd_set_option(dev, up, usr, NULL);
		break;

	default:
		err = handle_pcan_flex_cmd(cmd, dev, up, usr, NULL);
		break;
	}

#ifdef DEBUG
	pr_info(DEVICE_NAME ": %s(pcan%u, cmd=%u (NR=%u)): returns %d\n",
		__func__, dev->nMinor, cmd, _IOC_NR(cmd), err);
#endif

	return err;
}

/* ioctl() entry point: lock the device then handle the ioctl cmd */
static long _pcan_ioctl(struct file *filep, unsigned int cmd, void __user *up)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	long err;

	struct pcandev *dev = pcan_get_dev_lock(usr);
	if (!dev)
		return -ENODEV;

	err = __pcan_ioctl(filep, cmd, up, dev);
	return pcan_put_dev_unlock(dev, err);
}

/*
 * is called at user ioctl() call
 */
#if LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 36)
static int pcan_ioctl(struct inode *inode,
		      struct file *filep, unsigned int cmd, unsigned long arg)
#else
static long pcan_ioctl(struct file *filep, unsigned int cmd, unsigned long arg)
#endif
{
	return _pcan_ioctl(filep, cmd, (void __user *)arg);
}

#ifdef PCAN_CONFIG_COMPAT
/*
 * 32-bit application using 64-bit driver
 */
#define __array_of_struct32(_n, _x)					\
	_n##s_##_x {							\
		__u32		count;					\
		struct _n	list[_x];				\
	} __aligned(4)

struct pcanfd_msg32 {
	__u16	type;
	__u16	data_len;
	__u32	id;
	__u32	flags;
	struct compat_timeval	timestamp;
	__u8	ctrlr_data[PCANFD_MAXCTRLRDATALEN];
	__u8	data[PCANFD_MAXDATALEN] __attribute__((aligned(8)));
} __aligned(4);

struct __array_of_struct32(pcanfd_msg32, 0);

#define pcanfd_msgs32		pcanfd_msg32s_0

struct pcanfd_state32 {
	__u16	ver_major, ver_minor, ver_subminor;

	struct compat_timeval	tv_init;

	compat_int_t	bus_state;

	__u32	device_id;

	__u32	open_counter;
	__u32	filters_counter;

	__u16	hw_type;
	__u16	channel_number;

	__u16	can_status;
	__u16	bus_load;

	__u32	tx_max_msgs;
	__u32	tx_pending_msgs;
	__u32	rx_max_msgs;
	__u32	rx_pending_msgs;
	__u32	tx_frames_counter;
	__u32	rx_frames_counter;
	__u32	tx_error_counter;
	__u32	rx_error_counter;

	__u64	host_time_ns;
	__u64	hw_time_ns;
} __aligned(4);

/* Device options */
struct pcanfd_option32 {
	compat_int_t	size;
	compat_int_t	name;
	compat_uptr_t 	value;
} __aligned(4);

struct pcanxl_msg32 {
	__u16   type;
	__u16   data_len;
	__u32   id;
	__u32   flags;
	struct compat_timeval timestamp;
	__u8    ctrlr_data[PCANXL_MAXCTRLRDATALEN];
	__u32   af;
	__u8    sdt;
	__u8	data[];
} __aligned(4);

struct __array_of_struct32(pcanxl_msg32, 0);

#define pcanxl_msgs32		pcanxl_msg32s_0

#define PCANFD_GET_STATE32	_IOR(PCAN_MAGIC_NUMBER, PCANFD_SEQ_GET_STATE,\
					struct pcanfd_state32)

#define PCANFD_SEND_MSG32	_IOW(PCAN_MAGIC_NUMBER, PCANFD_SEQ_SEND_MSG,\
					struct pcanfd_msg32)

#define PCANFD_RECV_MSG32	_IOR(PCAN_MAGIC_NUMBER, PCANFD_SEQ_RECV_MSG,\
					struct pcanfd_msg32)

#define PCANFD_SEND_MSGS32	_IOWR(PCAN_MAGIC_NUMBER, PCANFD_SEQ_SEND_MSGS,\
					struct pcanfd_msgs32)

#define PCANFD_RECV_MSGS32	_IOWR(PCAN_MAGIC_NUMBER, PCANFD_SEQ_RECV_MSGS,\
					struct pcanfd_msgs32)

#define PCANFD_GET_OPTION32	_IOWR(PCAN_MAGIC_NUMBER, PCANFD_SEQ_GET_OPTION,\
					struct pcanfd_option32)

#define PCANFD_SET_OPTION32	_IOW(PCAN_MAGIC_NUMBER, PCANFD_SEQ_SET_OPTION,\
					struct pcanfd_option32)

/* because of the struct timeval different size, we must
 * do some manual copy...
 */
static struct pcanxl_txmsg *copy_from_fd32(struct pcanxl_txmsg_fd *d,
					   const struct pcanfd_msg32 *s)
{
	/* note: copying msgs from userspace means that this is a message
	 * to send: no need to copy every fields...
	 */
	d->msg.type = s->type;
	d->msg.data_len = (s->data_len > PCANFD_CANFD_MAXDATALEN) ?
				PCANFD_CANFD_MAXDATALEN : s->data_len;
	d->msg.id = s->id;
	d->msg.flags = s->flags;
	memcpy(d->msg.data, s->data, d->msg.data_len);

	return (struct pcanxl_txmsg *)d;
}

static struct pcanfd_msg32 *copy_to_fd32(struct pcanfd_msg32 *d,
					 const struct pcanxl_rxmsg_fd *s)
{
	s64 tv_nsec = s->msg.timestamp.tv_nsec;

	d->type = s->msg.type;
	d->data_len = (s->msg.data_len > PCANFD_CANFD_MAXDATALEN) ?
				PCANFD_CANFD_MAXDATALEN : s->msg.data_len;
	d->id = s->msg.id;
	d->flags = s->msg.flags;

	d->timestamp.tv_sec = s->msg.timestamp.tv_sec;

	/* a = do_div(b, c); <=> { a = b % c ; b = b / c; } */
	do_div(tv_nsec, NSEC_PER_USEC);
	d->timestamp.tv_usec = (__kernel_suseconds_t )tv_nsec;

	memcpy(d->ctrlr_data, s->msg.ctrlr_data, PCANFD_MAXCTRLRDATALEN);
	memcpy(d->data, s->msg.data, d->data_len);

	return d;
}

static int handle_pcanfd_send_msgs32(struct pcandev *dev, void __user *up,
				     struct pcanusr *dev_priv)
{
	struct pcanfd_msg32s_0 __user *pl32 = (struct pcanfd_msg32s_0 *)up;
	struct pcanxl_txmsgs_fd txs, *pl;
	int i, l, err;

	l = sizeof(*pl32);
	err = copy_from_user(&txs, up, l);
	if (err) {
		pr_err(DEVICE_NAME ": %s(%u): copy_from_user() failure\n",
			__func__, __LINE__);
		return -EFAULT;
	}

	/* ok. Nothing to send. So nothing done. Perfect. */
	if (!txs.count)
		return 0;

	l += txs.count * (sizeof(txs.list[0]) + PCANFD_MAXDATALEN);
	pl = pcan_malloc(l, GFP_KERNEL);
	if (!pl) {
		pr_err(DEVICE_NAME ": %s(): failed to alloc msgs list\n",
			__func__);
		return -ENOMEM;
	}

	for (i = 0; i < txs.count; i++) {
		struct pcanfd_msg32 m32;

		err = copy_from_user(&m32, &pl32->list[i], sizeof(m32));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_from_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
			goto lbl_free;
		}

		copy_from_fd32(&pl->list[i], &m32);
	}

	pl->count = i;
	err = pcanxl_ioctl_send_msgs(dev, pl, dev_priv);

	/* copy the count of msgs really sent (= pl->count) */
	if (copy_to_user(pl32, pl, sizeof(*pl32))) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_to_user() failure\n",
			__func__, __LINE__);
		err = -EFAULT;
	}

lbl_free:
	pcan_free(pl);

	return err;
}

static int handle_pcanfd_recv_msgs32(struct pcandev *dev, void __user *up,
				     struct pcanusr *dev_priv)
{
	struct pcanfd_msg32s_0 __user *pl32 = (struct pcanfd_msg32s_0 *)up;
	struct pcanxl_rxmsgs_fd rxs, *pl;
	int i, l, err;

	l = sizeof(*pl32);
	err = copy_from_user(&rxs, up, l);
	if (err) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_from_user() failure\n",
			__func__, __LINE__);
		return -EFAULT;
	}

	/* ok! no room for saving rcvd msgs!? Thus, nothing returned */
	if (!rxs.count)
		return 0;

	l += rxs.count * (sizeof(rxs.list[0]) * PCANFD_MAXDATALEN);
	pl = pcan_malloc(l, GFP_KERNEL);
	if (!pl) {
		pr_err(DEVICE_NAME ": failed to alloc msgs list\n");
		return -ENOMEM;
	}

	pl->count = rxs.count;

	/* tell that no more than 64 bytes can be saved into each slot buffer */
	for (i = 0; i < pl->count; i++)
		pl->list[i].msg.data_len = PCANFD_MAXDATALEN;

	err = pcanxl_ioctl_recv_msgs(dev, pl, dev_priv);

	/* copy the count of msgs received */
	if (copy_to_user(pl32, pl, sizeof(*pl32))) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_to_user() failure\n",
			__func__, __LINE__);
		err = -EFAULT;
		goto lbl_free;
	}

	/* copy the msgs received */
	for (i = 0; i < pl->count; i++) {
		struct pcanfd_msg32 m32;

		if (copy_to_user(&pl32->list[i],
				 copy_to_fd32(&m32, &pl->list[i]),
				 sizeof(m32))) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
			break;
		}
	}

lbl_free:
	pcan_free(pl);

	return err;
}

static int handle_pcanfd_get_option32(struct pcandev *dev, void __user *up,
				      struct pcanusr *usr, void *c)
{
	struct pcanfd_option32 opt32;
	const int l = sizeof(opt32);
	struct pcanfd_option opt;

	int err = pcan_copy_from_user(&opt32, up, l, c);
	if (err) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_from_user() failure\n",
			__func__, __LINE__);
		return -EFAULT;
	}

	if (opt32.name >= PCANXL_OPT_MAX) {
		pr_err(DEVICE_NAME ": invalid option name %d to get\n",
			opt32.name);
		return -EINVAL;
	}

	if (!dev->option[opt32.name].get) {
		return -EOPNOTSUPP;
	}

	if (dev->option[opt32.name].req_size > 0)

		/* if user option buffer size is too small, return the 
		 * requested size with -ENOSPC
		 */
		if (opt32.size < dev->option[opt32.name].req_size) {
			pr_warn(DEVICE_NAME
				": invalid option size %d < %d for option %d\n",
				opt32.size, dev->option[opt32.name].req_size,
				opt32.name);
			opt.size = dev->option[opt32.name].req_size;
			err = -ENOSPC;
			goto lbl_cpy_size;
		}

	opt.name = opt32.name;
	opt.size = opt32.size;
	opt.value = compat_ptr(opt32.value);

	err = dev->option[opt32.name].get(dev, &opt, c);
	if (err && err != -ENOSPC)
		return err;

lbl_cpy_size:
	/* update 'size' field */
	if (pcan_copy_to_user(up+offsetof(struct pcanfd_option32, size),
			 &opt.size, sizeof(opt.size), c)) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_to_user() failure\n",
			__func__, __LINE__);
		err = -EFAULT;
	}

	return err;
}

static int handle_pcanfd_set_option32(struct pcandev *dev, void __user *up,
				      struct pcanusr *usr, void *c)
{
	struct pcanfd_option32 opt32;
	struct pcanfd_option opt;
	int l = sizeof(opt32);

	int err = pcan_copy_from_user(&opt32, up, l, c);
	if (err) {
		pr_err(DEVICE_NAME
			": %s(%u): copy_from_user() failure\n",
			__func__, __LINE__);
		return -EFAULT;
	}

	if (opt32.name >= PCANXL_OPT_MAX) {
		pr_err(DEVICE_NAME ": invalid option name %d to get\n",
			opt32.name);
		return -EINVAL;
	}

	if (!dev->option[opt32.name].set) {
		return -EOPNOTSUPP;
	}

	opt.name = opt32.name;
	opt.size = opt32.size;
	opt.value = compat_ptr(opt32.value);

	return dev->option[opt.name].set(dev, &opt, c);
}

static long pcan_compat_ioctl(struct file *filep, unsigned int cmd,
			      unsigned long arg)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	void __user *argp = compat_ptr(arg);

	struct pcanxl_txmsg_fd txfdm = {
		.msg = { .data_len = PCANFD_CANFD_MAXDATALEN }
	};

	struct pcanxl_rxmsg_fd rxfdm = {
		.msg = { .data_len = PCANFD_CANFD_MAXDATALEN }
	};
	struct pcanfd_msg32 fdm32;

	struct pcanfd_state fds;
	struct pcanfd_state32 fds32;
	struct pcandev *dev;
	void *ps, *pd;
	long err;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(cmd=%u) NR=%u SIZE=%u\n",
		__func__, cmd, _IOC_NR(cmd), _IOC_SIZE(cmd));
#endif

	dev = pcan_get_dev_lock(usr);
	if (!dev)
		return -ENODEV;

	switch (cmd) {

	case PCANFD_GET_STATE32:
		err = pcanxl_ioctl_get_state(dev, &fds);
		if (err)
			break;

		/* because of the struct timeval different size, we must
		 * do some manual copy...
		 */
		ps = &fds;
		pd = &fds32;

		memcpy(pd, ps, offsetof(struct pcanfd_state, tv_init));

		fds32.tv_init.tv_sec = fds.tv_init.tv_sec;
		fds32.tv_init.tv_usec = fds.tv_init.tv_usec;

		memcpy(pd+offsetof(struct pcanfd_state32, bus_state),
			ps+offsetof(struct pcanfd_state, bus_state),
			sizeof(fds32) - 
				offsetof(struct pcanfd_state32, bus_state));

		err = copy_to_user(argp, &fds32, sizeof(fds32));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure: err %ld\n",
				__func__, __LINE__, err);
			err = -EFAULT;
		}
		break;

	case PCANFD_SEND_MSG32:
		err = copy_from_user(&fdm32, argp, sizeof(fdm32));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_from_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
			break;
		}

		err = pcanxl_ioctl_send_msg(dev, copy_from_fd32(&txfdm, &fdm32),
					    NULL, usr);
		break;

	case PCANFD_RECV_MSG32:
		err = pcanxl_ioctl_recv_msg(dev, (struct pcanxl_rxmsg *)&rxfdm,
					    NULL, usr);
		if (err)
			break;

		err = copy_to_user(argp,
				   copy_to_fd32(&fdm32, &rxfdm),
				   sizeof(fdm32));
		if (err) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			err = -EFAULT;
		}
		break;

	case PCANFD_SEND_MSGS32:
		err = handle_pcanfd_send_msgs32(dev, argp, usr);
		break;

	case PCANFD_RECV_MSGS32:
		err = handle_pcanfd_recv_msgs32(dev, argp, usr);
		break;

	case PCANFD_GET_OPTION32:
		err = handle_pcanfd_get_option32(dev, argp, usr, NULL);
		break;

	case PCANFD_SET_OPTION32:
		err = handle_pcanfd_set_option32(dev, argp, usr, NULL);
		break;

	default:
		/* call the unlocked device entry point */
		err = __pcan_ioctl(filep, cmd, argp, dev);
	}

	return pcan_put_dev_unlock(dev, err);
}
#endif

/*
 * is called when read from the path
 */
static ssize_t pcan_read(struct file *filep, char *buf, size_t count,
								loff_t *f_pos)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	struct pcanxl_rxmsg_fd rxfd = {
		.msg = { .data_len = PCANFD_CANFD_MAXDATALEN }
	};
	struct pcanxl_rxmsg *rx = (struct pcanxl_rxmsg *)&rxfd;
	int err, len = 0;

	struct pcandev *dev = pcan_get_dev_lock(usr);

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__,
		(dev) ? dev->nMinor : 0xff);
#endif
	if (!dev)
		return -ENODEV;

	if (usr->nReadRest <= 0) {
		err = pcanxl_ioctl_recv_msg(dev, rx, NULL, usr);
		if (err)
			return pcan_put_dev_unlock(dev, err);

		usr->nReadRest =
			pcan_make_output(usr->pcReadBuffer,
					 (struct pcanxl_msg *)&rx->msg);

		usr->pcReadPointer = usr->pcReadBuffer;
	}

	/* give the data to the user */
	if (count > usr->nReadRest) {
		/* put all data to user */
		len = usr->nReadRest;
		usr->nReadRest = 0;
		if (copy_to_user(buf, usr->pcReadPointer, len)) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			return pcan_put_dev_unlock(dev, -EFAULT);
		}
		usr->pcReadPointer = usr->pcReadBuffer;
	} else {
		/* put only partial data to user */
		len = count;
		usr->nReadRest -= count;
		if (copy_to_user(buf, usr->pcReadPointer, len)) {
			pr_err(DEVICE_NAME
				": %s(%u): copy_to_user() failure\n",
				__func__, __LINE__);
			return pcan_put_dev_unlock(dev, -EFAULT);
		}
		usr->pcReadPointer =
				(u8 *)((u8*)usr->pcReadPointer + len);
	}

	*f_pos += len;
	usr->nTotalReadCount += len;

	return pcan_put_dev_unlock(dev, len);
}

static int pcan_write_line(struct pcanusr *usr, u8 *ptr, size_t count)
{
	struct pcandev *dev = usr->dev;
	u32 amount, offset;
	int err = 0;

	amount = (u32)(usr->pcWritePointer - ptr - 1);
	offset = (u32)(ptr - usr->pcWriteBuffer + 1);

	if ((amount > WRITEBUFFER_SIZE) || (offset > WRITEBUFFER_SIZE)) {
		pr_err(DEVICE_NAME ": %s() fault: %zu %u, %u: \n",
			__func__, count, amount, offset);
		err = -EFAULT;
		goto lbl_err;
	}

	/* pcan v9: only CAN frames with less than 64 bytes can use that API */
	if (pcan_parse_input_idle(usr->pcWriteBuffer)) {
		struct pcanxl_txmsg_fd tx_fd = {
			.msg = { .data_len = PCANFD_MAXDATALEN, }
		};
		struct pcanxl_txmsg *tx = (struct pcanxl_txmsg *)&tx_fd;

		if (pcan_parse_input_message(usr->pcWriteBuffer,
					     (struct pcanxl_msg *)&tx->msg)) {
			struct pcanxl_init xli;

			err = pcan_parse_input_init(usr->pcWriteBuffer, &xli);
			if (err)
				goto lbl_err;

			/* init the associated chip and the fifos again
			 * with new parameters
			 */
			err = pcanxl_ioctl_set_init(dev, &xli);
			if (err)
				goto lbl_err;
		} else {
			err = pcanxl_ioctl_send_msg(dev, tx, NULL, usr);
			if (err)
				if (err != -ENODATA)
					goto lbl_err;
		}
	}

	/* move rest of amount data in buffer offset steps to left */
	memmove(usr->pcWriteBuffer, ptr + 1, amount);
	usr->pcWritePointer -= offset;

lbl_err:
	return err;
}

static ssize_t pcan_write(struct file *filep, const char *buf, size_t count,
								loff_t *f_pos)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	int err = 0;
	u32 dwRest;
	u8 *ptr;

	struct pcandev *dev = pcan_get_dev_lock(usr);
	if (!dev)
		return -ENODEV;

#ifdef DEBUG_TRACE
	pr_info(DEVICE_NAME ": %s(pcan%d)\n", __func__, dev->nMinor);
#endif

	/* calculate remaining buffer space */
	dwRest = WRITEBUFFER_SIZE -
		(usr->pcWritePointer - usr->pcWriteBuffer);
	count  = (count > dwRest) ? dwRest : count;

	if (copy_from_user(usr->pcWritePointer, buf, count)) {
		pr_err(DEVICE_NAME ": %s(%u): copy_from_user() failure\n",
			__func__, __LINE__);
		return pcan_put_dev_unlock(dev, -EFAULT);
	}

	/* adjust working pointer to end */
	usr->pcWritePointer += count;

	/* iterate search blocks ending with '\n' */
	while (1) {

		/* search first '\n' from begin of buffer */
		ptr = usr->pcWriteBuffer;
		while ((*ptr != '\n') && (ptr < usr->pcWritePointer))
			ptr++;

		/* parse input when a CR was found */
		if ((*ptr == '\n') && (ptr < usr->pcWritePointer)) {
			err = pcan_write_line(usr, ptr, count);
			if (err)
				return pcan_put_dev_unlock(dev, err);
		} else
			break; /* no CR found */
	}

	if (usr->pcWritePointer >=
				(usr->pcWriteBuffer + WRITEBUFFER_SIZE)) {
		/* reject all */
		usr->pcWritePointer = usr->pcWriteBuffer;
		return pcan_put_dev_unlock(dev, -EINVAL);
	}

	return pcan_put_dev_unlock(dev, count);
}

/*
 * is called at poll or select
 */
static unsigned int pcan_poll(struct file *filep, poll_table *wait)
{
	struct pcanusr *usr = (struct pcanusr *)filep->private_data;
	struct pcandev *dev = pcan_get_dev_lock(usr);
	unsigned int mask = 0;

	if (!dev)
		return POLLERR;

	/* return on ops that could be performed without blocking */

#ifndef NETDEV_SUPPORT
	poll_wait(filep, &dev->in_event, wait);

	if (!kfifo_is_empty(&dev->rx_fifo.kfifo))
		mask |= POLLIN | POLLRDNORM;
#endif
	poll_wait(filep, &dev->out_event, wait);

	if (kfifo_ratio(&dev->tx_fifo.kfifo) < txqhiwat)
		mask |= POLLOUT | POLLWRNORM;

	return pcan_put_dev_unlock(dev, mask);
}

/*
 * this structure is used in init_module(void)
 */
struct file_operations pcan_fops = {
	/*
	 * marrs:  added owner, which is used to implement a use count that
	 *         disallows rmmod calls when the driver is still in use (as
	 *         suggested by Duncan Sands on the linux-kernel mailinglist)
	 */
	owner:      THIS_MODULE,
	open:       pcan_open,
	release:    pcan_release,
	read:       pcan_read,
	write:      pcan_write,
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,36)
	ioctl:      pcan_ioctl,
#else
	unlocked_ioctl: pcan_ioctl,
#endif
#ifdef PCAN_CONFIG_COMPAT
	compat_ioctl: pcan_compat_ioctl,
#endif
	poll:       pcan_poll,
};

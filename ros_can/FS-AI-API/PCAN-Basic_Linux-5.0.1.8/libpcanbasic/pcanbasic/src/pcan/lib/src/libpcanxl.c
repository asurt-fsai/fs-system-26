/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * libpcanxl.c
 *
 * the shared library to unify the interface to the PEAK-System CAN[FD] devices
 *
 * Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
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
 * Contact:       <linux.peak@hms-networks.com>
 * Author:        Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */

/* #define DEBUG */

#include "libpcanfd.c"

#include "libpcanxl.h"

/*
 * int pcanxl_set_init(int fd, struct pcanxl_init *pxli)
 *
 *	Enable to initialize an opened device with bitrate (and data bitrate
 *	if the device is CAN-FD capable) specification.
 *
 * RETURN:
 *
 *	0 if the device has been correctly initialized,
 *	a negative (errno) code otherwise.
 */
int pcanxl_set_init(int fd, struct pcanxl_init *pxli)
{
#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pxli=%p)\n", __func__, fd, pxli);
#endif
	if (!pxli)
		return -EINVAL;

	pxli->flags &= OFD_PCANFD_MASK;
	return -__errno_ioctl(fd, PCANXL_SET_INIT, pxli);
}

/*
 * int pcanxl_get_init(int fd, struct pcanxl_init *pxli)
 *
 *	Read the initialization settings of an opened device.
 *
 * RETURN:
 *
 *	0 if the device has been correctly initialized,
 *	a negative (errno) code otherwise.
 *
 *	-EINVAL		the pxli argument is NULL.
 */
int pcanxl_get_init(int fd, struct pcanxl_init *pxli)
{
#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pxli=%p)\n", __func__, fd, pxli);
#endif
	if (!pxli)
		return -EINVAL;

	return -__errno_ioctl(fd, PCANXL_GET_INIT, pxli);
}

/*
 * int pcanxl_send_msg(int fd, const struct pcanxl_msg *pxlm)
 * int pcanxl_send_msg_local(int fd, const struct pcanxl_msg *pxlm)
 *
 *	Write a CAN message into the device output queue.
 *
 * 	pxlm->data_len MUST indicate the number of data bytes to copy from
 * 	pxlm->data[] array to the output CAN frame.
 *
 *	If no space is available in the device output queue, and if the
 *	device is opened in blocking mode, then the calling task goes to sleep,
 *	waiting for some space freed by the driver.
 *
 *	If the device is opened in non-blocking mode, the task doesn't wait and
 *	-EWOULDBLOCK is returned instead.
 *
 * WARNING:
 *
 * 	pcanxl_send_msg() doesn't allow @pxlm to be a local variable
 *      address. If so, then use pcanxl_send_msg_local() instead.  	
 *
 * RETURN:
 *
 *	0 if the message has been correctly sent,
 *	a negative (errno) code otherwise.
 */
int pcanxl_send_msg(int fd, const struct pcanxl_msg *pxlm)
{
#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pfdm[id=%d len=%d])\n", __func__, fd,
		  pxlm->id, pxlm->data_len);
#endif
	if (!pxlm)
		return -EINVAL;

	return -__errno_ioctl(fd, PCANXL_SEND_MSG(pxlm->data_len), pxlm);
}

int pcanxl_send_msg_local(int fd, const struct pcanxl_msg *pxlm)
{
	void *p;
	int l, err;

#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pfdm[id=%d len=%d])\n", __func__, fd,
		  pxlm->id, pxlm->data_len);
#endif
	if (!pxlm)
		return -EINVAL;

	l = sizeof(*pxlm) + pxlm->data_len;
	p = malloc(l);
	if (!p)
		return -ENOMEM;

	memcpy(p, pxlm, l);
	err = -__errno_ioctl(fd, PCANXL_SEND_MSG(pxlm->data_len), p);
	free(p);

	return err;
}

/*
 * int pcanxl_recv_msg(int fd, struct pcanxl_msg *pxlm)
 * int pcanxl_recv_msg_local(int fd, struct pcanxl_msg *pxlm)
 *
 *	Read one received message from the device input queue.
 *
 * 	pxlm->data_len MUST indicate the size of pxlm->data[] array.
 *
 *	If they are no messages to read from the device input queue, and if the
 *	device is opened in blocking mode, then the calling task goes to sleep,
 *	waiting for any incoming event from the driver.
 *
 *	If the device is opened in non-blocking mode, the task doesn't wait and
 *	-EWOULDBLOCK is returned instead.
 *
 * WARNING:
 *
 * 	pcanxl_recv_msg() doesn't allow @pxlm to be a local variable
 *      address. If so, then use pcanxl_recv_msg_local() instead.  	
 * 
 * RETURN:
 *
 *	0 if a message has been correctly received, and
 *	  pxlm->data_len indicates the number of data bytes read from the
 *	  received CAN frame,
 *	a negative (errno) code otherwise.
 */
int pcanxl_recv_msg(int fd, struct pcanxl_msg *pxlm)
{
#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pfdm=%p)\n", __func__, fd, pxlm);
#endif
	if (!pxlm)
		return -EINVAL;

	return -__errno_ioctl(fd, PCANXL_RECV_MSG(pxlm->data_len), pxlm);
}

int pcanxl_recv_msg_local(int fd, struct pcanxl_msg *pxlm)
{
	void *p;
	int l, err;

#ifdef DEBUG
	__fprintf(stddbg, "%s(fd=%d pfdm[id=%d len=%d])\n", __func__, fd,
		  pxlm->id, pxlm->data_len);
#endif
	if (!pxlm)
		return -EINVAL;

	l = sizeof(*pxlm) + pxlm->data_len;
	p = malloc(l);
	if (!p)
		return -ENOMEM;

	err = -__errno_ioctl(fd, PCANXL_RECV_MSG(pxlm->data_len), p);
	if (!err)
		memcpy(pxlm, p, l);

	free(p);

	return err;
}

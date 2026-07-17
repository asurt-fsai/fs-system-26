/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * libpcanxl.h - common header to access the functions within libpcanxl.so.x.x.
 *
 * Copyright (C) 2015-2025  PEAK System-Technik GmbH <www.peak-system.com>
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
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#ifndef __LIBPCANXL_H__
#define __LIBPCANXL_H__

#include <libpcanfd.h>
#include <pcanxl.h>

/*
 * new API entry points
 */
#ifdef __cplusplus
extern "C" {
#endif

/*
 * int pcanxl_set_init(int fd, struct pcanxl_init *pxli)
 *
 *	Enable to initialize an opened device with nominal bitrate (and data
 *	bitrate	if the device can operate in CAN FD or CAN XL mode).
 *
 * RETURN:
 *
 *	0 if the device has been correctly initialized,
 *	a negative (errno) code otherwise.
 */
int pcanxl_set_init(int fd, struct pcanxl_init *pxli);

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
int pcanxl_get_init(int fd, struct pcanxl_init *pxli);

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
int pcanxl_send_msg(int fd, const struct pcanxl_msg *pxlm);
int pcanxl_send_msg_local(int fd, const struct pcanxl_msg *pxlm);

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
int pcanxl_recv_msg(int fd, struct pcanxl_msg *pxlm);
int pcanxl_recv_msg_local(int fd, struct pcanxl_msg *pxlm);

/*
 * int pcanxl_is_canxl_capable(int fd)
 *
 *	Helper function useful to know whether a CAN device is or is not CAN-XL
 *	capable.
 */
int pcanxl_is_canxl_capable(int fd);

/*
 * These functions are simple aliases with their corresponding entries in the
 * v8 libpcanfd API.
 */

/*
 * int pcanxl_reset(int fd, unsigned long flags)
 *
 *	Enable to reset things in the driver (see PCAND_RESET_xxx in pcanfd.h)
 *
 * RETURN:
 *
 *	0 if all reset operations were successful,
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_reset(int fd, unsigned long flags)
{
	return pcanfd_reset(fd, flags);
}

/*
 * int pcanxl_get_state(int fd, struct pcanfd_state *pfds)
 *
 *	Read the state of a CAN device/channel.
 *
 * RETURN:
 *
 *	0 if the device has been correctly initialized,
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_get_state(int fd, struct pcanfd_state *pfds)
{
	return pcanfd_get_state(fd, pfds);
}

/*
 * int pcanxl_add_filters(int fd, struct pcanfd_msg_filters *pfl)
 * int pcanxl_add_filter(int fd, struct pcanfd_msg_filter *pf)
 * int pcanxl_add_filters_list(int fd, int count, struct pcanfd_msg_filter *pf)
 *
 *	Add a message filters list into the device's message filters list.
 *
 * RETURN:
 *
 *	0 if the filters list has been correctly added,
 *	a negative (errno) code otherwise.
 *
 *	-EINVAL		the pfl argument is NULL.
 */
static inline int pcanxl_add_filters(int fd,
				     const struct pcanfd_msg_filters *pfl)
{
	return pcanfd_add_filters(fd, pfl);
}

static inline int pcanxl_add_filter(int fd, const struct pcanfd_msg_filter *pf)
{
	return pcanfd_add_filter(fd, pf);
}

static inline int pcanxl_add_filters_list(int fd, int count,
					const struct pcanfd_msg_filter *pf)
{
	return pcanfd_add_filters_list(fd, count, pf);
}

/*
 * int pcanxl_get_filters(int fd, struct pcanfd_msg_filters *pfl)
 * int pcanxl_get_filters_list(int fd, int count, struct pcanfd_msg_filter *pf)
 *
 *	Copy the message filters list from the device's message filters list.
 *
 * RETURN:
 *
 *	0 if the filters list has been correctly coppied,
 *	a negative (errno) code otherwise.
 *
 *	-EINVAL		the pfl argument is NULL.
 */
static inline int pcanxl_get_filters(int fd, struct pcanfd_msg_filters *pfl)
{
	return pcanfd_get_filters(fd, pfl);
}

static inline int pcanxl_get_filters_list(int fd, int count,
					  struct pcanfd_msg_filter *pf)
{
	return pcanfd_get_filters_list(fd, count, pf);
}

/*
 * int pcanxl_del_filters(int fd);
 *
 *	Remove all the message filters from the device's messages filter list.
 *
 * RETURN:
 *
 *	0 if the filter has been correctly sent,
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_del_filters(int fd)
{
	return pcanfd_del_filters(fd);
}

/*
 * int pcanxl_set_device_id(int fd, __u32 devid)
 *
 *	Set a "device id." to a CAN channel (when the corresponding hardware
 *	enables it) so that this CAN channel will be able to be always 
 *	identified by this device id. This is mainly uiseful for USB CAN
 *	interfaces that can be plugged and re-plugged to different USB sockets.
 *	By convention, the value 0xffffffff means "no device id.".
 *
 * RETURN:
 *
 *	O if setting a new device id. to the CAN channel succeeded.
 *
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_set_device_id(int fd, __u32 devid)
{
	return pcanfd_set_device_id(fd, devid);
}

/*
 * int pcanxl_get_device_id(int fd, __u32 *pdevid)
 *
 *	Get the "device id." previously set to a CAN channel or 0xffffffff
 *	if there wasn't any. See "pcanxl_set_device_id()" for more information
 *	about the utility of "device id."
 *
 * RETURN:
 *
 *	O if setting a new device id. to the CAN channel succeeded.
 *
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_get_device_id(int fd, __u32 *pdevid)
{
	return pcanfd_get_device_id(fd, pdevid);
}

/*
 * int pcanxl_get_available_clocks(int fd, struct pcanfd_available_clocks *pac)
 *
 *	Read clock values available for the CAN-FD device.
 *	User MUST setup pac->count to the number of
 *	struct pcanfd_available_clock items allocated in pac->list[] array.
 *
 *	The driver fills list[] with all the clock values that can be selected
 *	in the device. list[0] always contains the default clock.
 *
 * RETURN:
 *
 *	0 if success (list[0] is the default clock value)
 *
 *	a negative (errno) code otherwise.
 */
static
inline int pcanxl_get_available_clocks(int fd,
				       struct pcanfd_available_clocks *pac)
{
	return pcanfd_get_available_clocks(fd, pac);
}

/*
 * int pcanxl_get_bittiming_ranges(int fd,
 *                                 struct pcanfd_bittiming_ranges *pbtr)
 *
 *	Read bittiming ranges available in the CAN-FD device.
 *	User MUST setup pbtr->count to the number of
 *	struct pcanfd_bittiming_range items allocated in pbtr->list[] array.
 *
 *	The driver fills list[0] with the [nominal] bitrate bittiming ranges.
 *	If the device is CAN-FD capable, then the driver also fills list[1] with
 *	the data bitrate bittiming ranges.
 *
 * RETURN:
 *
 *	0 if at least the [nominal] bitrate bittiming ranges has been copiedr.
 *	  For CAN 2.0 devices, pbtr->count is set to 1, while
 *	  pbtr->count is set to 2 for CAN-FD capable devices.
 *
 *	a negative (errno) code otherwise.
 */
static
inline int pcanxl_get_bittiming_ranges(int fd,
				       struct pcanfd_bittiming_ranges *pbtr)
{
	return pcanfd_get_bittiming_ranges(fd, pbtr);
}

/*
 * int pcanxl_get_option(int fd, int name, void *value, int size)
 *
 *	Get an option value from the opened channel.
 *
 * RETURN:
 *
 *	a negative (errno) code in case of error
 *
 *	a count of bytes <= size in case of success
 *
 *	a count of bytes > size in case of to small value buffer: in this case,
 *	this count is the size the buffer should be, to successfully get this
 *	option.
 */
static inline int pcanxl_get_option(int fd, int name, void *value, int size)
{
	return pcanfd_get_option(fd, name, value, size);
}

/*
 * int pcanxl_set_option(int fd, int name, const void *value, int size)
 *
 *	Set an option value to the opened channel.
 *
 * RETURN:
 *
 *	0 if the option has been set.
 *
 *	a negative (errno) code otherwise.
 */
static inline int pcanxl_set_option(int fd, int name, void *value, int size)
{
	return pcanfd_set_option(fd, name, value, size);
}

/*
 * int pcanxl_close(int fd)
 *
 *	Close any opened descriptor.
 *
 * RETURN:
 *
 *	-1
 */
static inline int pcanxl_close(int fd)
{
	return pcanfd_close(fd);
}

#endif /* __LIBPCANXL_H__ */

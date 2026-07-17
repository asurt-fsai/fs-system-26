/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanread.cpp - PCANBasic Example: Simple Read
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
 * Contact:      <linux.peak@hms-networks.com>
 * Maintainer:   Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
 *               Stephane Grosjean <stephane.grosjean@hms-networks.com>
 * Author:       Thomas Haber <thomas@toem.de>
 */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <asm/types.h>

#ifndef NO_RT
#include <sys/mman.h>

#ifdef RTAI
#include <rtai_lxrt.h>
#endif

// PCAN-Basic device used to read on
// (RT version doesn't handle USB devices)
#define PCAN_DEVICE PCAN_PCIBUS1
#else

// PCAN-Basic device used to read on
#define PCAN_DEVICE PCAN_USBBUS1
#endif

#include "PCANBasic.h"
#define _PCAN_BITRATE_500K_2M ((TPCANBitrateFD)u8"f_clock=80000000, nom_brp=1,  nom_tseg1=127, nom_tseg2=32, nom_sjw=32, data_brp=1, data_tseg1=31, data_tseg2=8, data_sjw=8")

static int g_app_stop = 0;
static void signal_handler(int s)
{
	g_app_stop = 1;
	printf("Interrupted by SIG%u!\n", s);
}

static int get_fd_len(__u8 dlc) {
	dlc = dlc & 0x0F;
	if (dlc <= 8)
		return dlc;
	switch(dlc) {
	case 9:
		return 12;
	case 10:
		return 16;
	case 11:
		return 20;
	case 12:
		return 24;
	case 13:
		return 32;
	case 14:
		return 48;
	case 15:
	default:
		return 64;
	}
}
////////////////////////////////////////////////////////////////////////////////////////////////////
/// <summary>	Main entry-point for this application. </summary>
///
/// <remarks>	 </remarks>
///
/// <param name="argc">	The argc. </param>
/// <param name="argv">	[in,out] If non-null, the argv. </param>
///
/// <returns>	. </returns>
////////////////////////////////////////////////////////////////////////////////////////////////////
int main(int argc, char *argv[])
{
	TPCANMsgFD Message;
	TPCANTimestampFD ts_app_start;
	TPCANTimestampFD ts;
	TPCANTimestampFD ts_prev;
	TPCANTimestampFD ts_diff;
	TPCANStatus Status;
	unsigned int pcan_device = PCAN_DEVICE;
	unsigned long long diff;
	TPCANBitrateFD bitratefd = _PCAN_BITRATE_500K_2M;

#ifndef NO_RT
	mlockall(MCL_CURRENT | MCL_FUTURE);

#ifdef RTAI
	// Initialize LXRT
	RT_TASK *mainr = rt_task_init_schmod(nam2num("MAINR"), 0, 0, 0,
										 SCHED_FIFO, 0xF);
	if (!mainr)
	{
		printf("pcanreadfd(%xh): unable to setup main RT task\n",
			   PCAN_DEVICE);
		return -1;
	}
	rt_make_hard_real_time();
#endif
#endif

	// get the device from the cmd line if provided
	if (argc > 1)
	{
		char *endptr;
		unsigned long tmp = strtoul(argv[1], &endptr, 0);
		if (*endptr == '\0')
			pcan_device = tmp;
	}

	// below usleep() will be INTRuptible by user
	signal(SIGINT, signal_handler);

	ts_app_start = 0;
	Status = CAN_InitializeFD(pcan_device, bitratefd);
	printf("CAN_InitializeFD(%xh): Status=0x%x\n", pcan_device, (int)Status);
	if (Status)
		goto lbl_exit;

	while (g_app_stop == 0)
	{
		while ((Status = CAN_ReadFD(pcan_device, &Message, &ts)) == PCAN_ERROR_QRCVEMPTY && g_app_stop == 0)
			if (usleep(100))
				break;

		if (Status != PCAN_ERROR_OK)
		{
			printf("CAN_ReadFD(%xh) failure 0x%x\n", pcan_device, (int)Status);
			break;
		}
		else
		{
			if (ts_app_start == 0) {
				ts_app_start = ts;
				ts_prev = ts;
			}
		}

		diff = ts - ts_prev;
		if ((Message.MSGTYPE & PCAN_MESSAGE_EXTENDED) == PCAN_MESSAGE_EXTENDED)
			printf("  - R ID:%08X ", (int)Message.ID);
		else
			printf("  - R ID:    %04X ", (int)Message.ID);
		
		printf("DLC:%1X TYPE:%02X ", (int)Message.DLC, (int)Message.MSGTYPE);
		
		printf("TS:%010lu.%03lu delta:%07llu.%03llu ",
			(long)((ts - ts_app_start) / 1000),
			(long)((ts - ts_app_start) % 1000),
			diff / 1000, diff % 1000);
		
		printf("DATA:");
		for (int i = 0; i < get_fd_len(Message.DLC); ++i)
			printf("%02X ", (int)Message.DATA[i]);
		
		printf("\n");
		ts_prev = ts;

#ifdef XENOMAI
		// force flush of printf buffers
		rt_print_flush_buffers();
#endif
	}

	CAN_Uninitialize(pcan_device);

lbl_exit:
#ifdef XENOMAI
#elif defined(RTAI)
	rt_make_soft_real_time();
	rt_task_delete(mainr);
#endif

	return 0;
}

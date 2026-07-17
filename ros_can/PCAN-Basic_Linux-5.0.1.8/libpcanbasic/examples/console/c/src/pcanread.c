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
#define PCAN_DEVICE	PCAN_PCIBUS1
#else

// PCAN-Basic device used to read on
#define PCAN_DEVICE	PCAN_USBBUS1
#endif

#include "PCANBasic.h"

static int g_app_stop = 0;
static void signal_handler(int s)
{
	g_app_stop = 1;
	printf("Interrupted by SIG%u!\n", s);
}

static int get_cc_len(__u8 dlc) {
	return (dlc <= 8) ? dlc : 8;
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
	TPCANMsg Message;
	TPCANTimestamp ts;
	TPCANTimestamp ts_prev;
	TPCANTimestamp ts_diff;
	TPCANTimestamp ts_app_start;
	TPCANStatus Status;
	unsigned int pcan_device = PCAN_DEVICE;
	unsigned long long diff;

#ifndef NO_RT
	mlockall(MCL_CURRENT | MCL_FUTURE);

#ifdef RTAI
	// Initialize LXRT
	RT_TASK *mainr = rt_task_init_schmod(nam2num("MAINR"), 0, 0, 0,
					     SCHED_FIFO, 0xF);
	if (!mainr)
	{
		printf("pcanread(%xh): unable to setup main RT task\n",
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

	Status = CAN_Initialize(pcan_device, PCAN_BAUD_500K, 0, 0, 0);
	printf("CAN_Initialize(%xh): Status=0x%x\n", pcan_device, (int)Status);
	if (Status)
		goto lbl_exit;

	ts_app_start.micros = 0;
	ts_app_start.millis = 0;
	ts_app_start.millis_overflow = 0;
	
	while (g_app_stop == 0)
	{
		while ((Status = CAN_Read(pcan_device, &Message, &ts)) == PCAN_ERROR_QRCVEMPTY && g_app_stop == 0)
			if (usleep(100))
				break;

		if (Status != PCAN_ERROR_OK)
		{
			printf("CAN_Read(%xh) failure 0x%x\n", pcan_device, (int)Status);
			break;
		}
		else
		{
			if (ts_app_start.micros == 0 && ts_app_start.millis == 0) {
				ts_app_start.micros = 1;
				ts_app_start.millis = ts.millis;
				ts_prev = ts;
			}
		}

		ts_diff.millis = ts.millis - ts_prev.millis;
		if (ts.micros >= ts_prev.micros)
		{
			ts_diff.micros = ts.micros - ts_prev.micros;
		}
		else
		{
			ts_diff.millis--;
			ts_diff.micros = 1000 - ts_prev.micros + ts.micros;
		}
		diff = (ts.millis - ts_prev.millis) * 1000 + (ts.micros - ts_prev.micros);

		if ((Message.MSGTYPE & PCAN_MESSAGE_EXTENDED) == PCAN_MESSAGE_EXTENDED)
			printf("  - R ID:%08X ", (int)Message.ID);
		else
			printf("  - R ID:    %04X ", (int)Message.ID);
		
		printf("DLC:%1X TYPE:%02X ", (int)Message.LEN, (int)Message.MSGTYPE);
		
		printf("TS:%010u.%03u delta:%07u.%03u ",
			ts.millis - ts_app_start.millis, ts.micros, 
			ts_diff.millis, ts_diff.micros);
		
		printf("DATA:");
		for (int i = 0; i < get_cc_len(Message.LEN); ++i)
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

/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanwrite.cpp - PCANBasic Example: Simple Write
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
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <asm/types.h>

#ifndef NO_RT
#include <sys/mman.h>

#ifdef RTAI
#include <rtai_lxrt.h>
#endif

// PCAN-Basic device used to read on
// (RT version doesn't handle USB devices)
#define PCAN_DEVICE PCAN_PCIBUS2
#else

// PCAN-Basic device used to read on
#define PCAN_DEVICE PCAN_USBBUS2
#endif

#include <PCANBasic.h>

// XL 500k/2M/8.8M
#define _PCAN_BITRATE_XL_500K_2M_8M ((TPCANBitrateXL)u8"f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,fd_tseg1=63,fd_tseg2=16,fd_sjw=16,fd_ssp_offset=0,xl_tseg1=9,xl_tseg2=8,xl_sjw=8,xl_ssp_offset=0,xl_error_signaling=1,xl_transceiver_mode_switch=0")
// XL 500k/20M tms=1
#define _PCAN_BITRATE_XL_500K_20M_TMS ((TPCANBitrateXL)u8"f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,xl_tseg1=4,xl_tseg2=3,xl_sjw=3,xl_pwm_offset=0,xl_pwm_short=2,xl_pwm_long=6,xl_error_signaling=0,xl_transceiver_mode_switch=1")
// XL 500k/4M ES=0
#define _PCAN_BITRATE_XL_500K_4M_ESOFF ((TPCANBitrateXL)u8"f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,xl_tseg1=31,xl_tseg2=8,xl_sjw=8,xl_error_signaling=0,xl_transceiver_mode_switch=0")
// XL 500k/2M/4M (PCANBasic GUI examples)
#define _PCAN_BITRATE_XL_500K_2M_4M ((TPCANBitrateXL)u8"f_clock=160000000,brp=1,nom_tseg1=255,nom_tseg2=64,nom_sjw=64,fd_tseg1=63,fd_tseg2=16,fd_sjw=16,fd_ssp_offset=0,xl_tseg1=10,xl_tseg2=9,xl_sjw=9,xl_ssp_offset=10,xl_error_signaling=1,xl_transceiver_mode_switch=0")

#define _PCAN_BITRATE_XL _PCAN_BITRATE_XL_500K_2M_8M

static int g_app_stop = 0;
static void signal_handler(int s)
{
	g_app_stop = 1;
	printf("Interrupted by SIG%u!\n", s);
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
	TPCANMsgXL Message;
	TPCANStatus Status;
	unsigned long ulIndex = 0;
	unsigned int pcan_device = PCAN_DEVICE;
	TPCANBitrateXL bitratexl = _PCAN_BITRATE_XL;

#ifndef NO_RT
	mlockall(MCL_CURRENT | MCL_FUTURE);

#ifdef RTAI
	// Initialize LXRT
	RT_TASK *mainr = rt_task_init_schmod(nam2num("MAINW"), 0, 0, 0,
										 SCHED_FIFO, 0xF);
	if (!mainr)
	{
		printf("pcanwritexl(%xh): unable to setup main RT task\n",
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

	// be INTRuptible by user
	signal(SIGINT, signal_handler);

	Status = CAN_InitializeXL(pcan_device, bitratexl);
	printf("CAN_InitializeXL(%xh): Status=0x%x\n", pcan_device, (int)Status);
	if (Status)
		goto lbl_exit;

	Message.PID = 0x123;
	Message.DLC = 2047;
	Message.MSGTYPE = PCAN_MESSAGE_XL;
	memset(Message.DATA, '\0', sizeof(Message.DATA));

	while (g_app_stop == 0)
	{
		while ((Status = CAN_WriteXL(pcan_device, &Message)) == PCAN_ERROR_OK && g_app_stop == 0)
		{
			// increment data bytes
			for (int i = 0; i < sizeof(Message.DATA); i++)
				if (++Message.DATA[i])
					break;
			Message.DATA[Message.DLC]++;

			ulIndex++;
			if ((ulIndex % 1000) == 0)
				printf("  - T Message %i\n", (int)ulIndex);
		}

		if (Status != PCAN_ERROR_QXMTFULL &&
			Status != PCAN_ERROR_XMTFULL)
		{
			printf("CAN_WriteXL(%xh): Error 0x%x\n", pcan_device,
				   (int)Status);
			break;
		}

		// Tx queue is full: must wait a bit instad of forever
		// looping. Handle ^C here too.
		if (usleep(100))
			break;
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

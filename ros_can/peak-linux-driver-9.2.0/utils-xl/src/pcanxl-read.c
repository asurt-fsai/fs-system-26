/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-read.c - a small program that writes to stdout the frames it reads
 * 		   from a CANXL channel.
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#include <time.h>		/* clock_gettime() */

#include "pcanxl-common.c"

/*
 * static int help_handler(struct cmdline_opt *opt_table, void *arg)
 */
static int help_handler(struct cmdline_opt *opt_table, void *arg)
{
	printf("\
Reads CAN frames and writes them to stdout.\n\
\n\
USAGE:\n\
%s [OPTIONS] /dev/pcanX\n\
\n\
OPTIONS:\n", (char *)opt_table->user_data);

	cmdline_display_options(opt_table);
	exit(0);
}

/*
 * int main(int argc, char *argv[])
 *
 * CAN-XL	flags				ES		TMS
 * Pure		PCANXL_INIT_XL|
 * 		PCANXL_INIT_ERR_SIGNALING_OFF	0		0
 * Pure	SIC-XL	PCANXL_INIT_XL|
 *              PCANXL_INIT_TRX_MODE_SWITCH_ON	0 (implicit)	1 PWM
 * Mixed	PCANXL_INIT_XL|PCANXL_INIT_FD	1		0
 * Forbidden	PCANXL_INIT_XL|PCANXL_INIT_FD|
 *              PCANXL_INIT_TRX_MODE_SWITCH_ON	1 		1
 */
int main(int argc, char *argv[])
{
	unsigned long long total_data_len = 0;
	struct timespec time_start, time_end, time_xfer;
	struct pcanxl_init xl_init = {
		.flags = PCANXL_DEF_INIT,
		.nominal = { .bitrate = PCANXL_DEF_NBITRATE,
			     .sample_point = PCANXL_DEF_NSP, },
		.fd_data = { .bitrate = PCANXL_DEF_DBITRATE,
			     .sample_point = PCANXL_DEF_DSP, },
		.xl_data = { .bitrate = PCANXL_DEF_XBITRATE,
			     .sample_point = PCANXL_DEF_XSP,
			     .ssp_offset = PCANXL_DEF_XSSPO, },
		.xl_pwm = {
			.pwm_offset = PCANXL_DEF_PWMO,
			.pwm_short = PCANXL_DEF_PWMS,
			.pwm_long = PCANXL_DEF_PWML,
		},
	};
	struct cmdline_opt opt_table[] = {
		{
			"help", 'h',	/* MUST be the 1st */
			help_inline_puts, help_handler,
			.user_data = argv[0],
		},
		{
			"nolog", 'd',
			nolog_inline_puts, nolog_handler,
		},
		{
			"listen-only", 'l',
			listen_only_inline_puts, listen_only_handler,
			.user_data = &xl_init,
		},
		{
			"clock", 'q',
			clock_inline_puts, clock_handler, OPT_ARG_NUM,
			.user_data = &xl_init,
		},
		{
			"nombtr", 'n',
			nominal_inline_puts, nominal_handler, OPT_ARG,
			.user_data = &xl_init,
		},
#ifndef PCANXL_CAN_CC_ONLY
		{
			"fdbtr", 'f',
			fd_data_inline_puts, fd_data_handler, OPT_ARG,
			.user_data = &xl_init,
		},
#ifndef PCANXL_CAN_FD_ONLY
		{
			"xlbtr", 'x',
			xl_data_inline_puts, xl_data_handler, OPT_ARG,
			.user_data = &xl_init,
		},
		{
			"tms", 't',
			tms_inline_puts, tms_handler, OPT_ARG,
			.user_data = &xl_init,
		},
		{
			"es", 'e',
			es_inline_puts, es_handler, OPT_ARG,
			.user_data = &xl_init,
		},
		{
			"pwm", 'p',
			pwm_inline_puts, pwm_handler, OPT_ARG,
			.user_data = &xl_init,
		},
#endif
#endif
		{ NULL, }
	};
	int i, fd, err;

	stdlog = stderr;

	/* 1st, process cmdline options */
	err = cmdline_process_options(argc, argv, opt_table);
	if (err)
		usage("Unknown command line option\n");

	/* Next, get cmdline parameters */
	for (i = 1; i < argc; i++)
		if (argv[i][0] != '-')
			dev_name = argv[i];

	if (!dev_name)
		usage("Missing device name on command line\n");

	fd = open(dev_name, O_RDWR);
	if (fd < 0)
		usage("Unable to open device %s (errno %d)\n", dev_name, errno);

	/* allocate (mandatory) the memory used to receive CANXL frames */
	xl_frame_rx = malloc(sizeof(struct pcanxl_msg_xl));
	if (!xl_frame_rx) {
		fprintf(stderr, "malloc(%zu) failed (errno %d)\n",
			sizeof(struct pcanxl_msg_xl), errno);
		goto lbl_exit;
	}

	/* Initialize the controller according to xl_init and read init settings
	 * back, to get parameter driver default values
	 */
	err = set_and_get_init(fd, &xl_init);
	if (err)
		goto lbl_exit;

	/* Wait for STATUS=ACTIVE */
	if (!wait_for_msg(fd, PCANFD_TYPE_STATUS) ||
			(xl_frame_rx->id != PCANFD_ERROR_ACTIVE)) {
		fprintf(stderr,
			"%s: unable to get BUS STATUS=ERROR_ACTIVE. Abort!\n",
			dev_name);
		goto lbl_exit;
	}

	/* starting from now, system calls may end with errno=EINTR */
	setup_sig_handler(SIGINT, signal_handler);

	for (i = 0; ; i++) {
		int l;

		/* Wait for any message */
		if (!wait_for_msg(fd, PCANXL_DEF_TYPE))
			break;

		if (!i)
			clock_gettime(CLOCK_REALTIME, &time_start);

		/* Data frame ID/AF=1 or 2 */
		l = write(STDOUT_FILENO, xl_frame_rx->data,
					 xl_frame_rx->data_len);
		if (l < xl_frame_rx->data_len) {
			fprintf(stderr,
				"unable to write to stdout (errno %d)\n",
				errno);
			break;
		}

		total_data_len += xl_frame_rx->data_len;
		fprintf(stderr, "%llu\r", total_data_len);
		if (!(i % 10))
			fflush(stderr);

#if defined(PCANXL_CAN_CC_ONLY) || defined(PCANXL_CAN_FD_ONLY)
		/* Last frame ID=2 */
		if (xl_frame_rx->id == 2) {
#else
		/* Last frame AF=2 (CAN XL only) */
		if (xl_frame_rx->af == 2) {
#endif
			clock_gettime(CLOCK_REALTIME, &time_end);
			timespecsub(&time_end, &time_start, &time_xfer);
			fflush(stdout);
			break;
		}
	}

	if (total_data_len > 0) {
		unsigned long long ms = time_xfer.tv_sec * 1000 +
					time_xfer.tv_nsec / 1000000;
		unsigned long long bits = total_data_len * 8;

		__log(stderr, "Got %llu bytes in %llu.%09llus (%llu bps)\n", 
		      total_data_len, time_xfer.tv_sec, time_xfer.tv_nsec,
		      (bits / ms) * 1000);
	}

	fputc('\n', stderr);

lbl_exit:
	__log(stdlog, "%s: closing device\n", dev_name);
	close(fd);

	free(xl_frame_rx);

	return err ? 1 : 0;
}

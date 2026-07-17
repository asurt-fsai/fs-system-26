/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-gen.c - a small program that periodically sends CANXL frames on the
 * 		  bus.
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
Writes CAN frames on a bus.\n\
\n\
USAGE:\n\
%s [OPTIONS] /dev/pcanX\n\
\n\
OPTIONS:\n", (char *)opt_table->user_data);

	cmdline_display_options(opt_table);
	exit(0);
}

static void every_inline_puts(struct cmdline_opt *opt)
{
	unsigned long *every_us = (unsigned long *)opt->user_data;

	printf("Writing period in us. or 'echo' "
	       "(default: %lu us.)\n", *every_us);
}

static int every_handler(struct cmdline_opt *opt, void *arg)
{
	long *every_us = (long *)opt->user_data;
	char *argv = (char *)arg;

	if (!strcmp(argv, "echo"))
		*every_us = -1;
	else {
		unsigned long v;
		int err = strtounit(argv, "kM",  &v);
		if (err)
			usage("Wrong delay specification\n");

		*every_us = (long )v;
	}

	__log(stddbg, "%s(): every_us = %ld\n", __func__, *every_us);

	return 0;
}

static struct pcanxl_msg_xl xl_frame_tx = {
	.type = PCANXL_DEF_TYPE,
	.flags = PCANXL_DEF_FLAGS,
	.sdt = PCANXL_SDT_MAN_RSRVD_LOW,
	.data_len = PCANXL_DEF_DATALEN,
	.ctrlr_data = {
		[PCANFD_ECHOID] = 0x11,		/* if PCANFD_MSG_ECHO */
	},
};

/*
 * int main(int argc, char *argv[])
 *
 * CAN-XL	flags				ES		TMS
 * Pure		PCANXL_INIT_XL|
 * 		PCANXL_INIT_ERR_SIGNALING_OFF	0		0
 * Pure	SIC-XL	PCANXL_INIT_XL|
 *              PCANXL_INIT_TRX_MODE_SWITCH_ON	0 (implicit)	1 PWM
 * Mixed	PCANXL_INIT_XL|PCANFD_INIT_FD	1		0
 * Forbidden	PCANXL_INIT_XL|PCANFD_INIT_FD|
 *              PCANXL_INIT_TRX_MODE_SWITCH_ON	1 		1
 */
int main(int argc, char *argv[])
{
	__u32 opt_slfack = 0;
	__u32 opt_hwtimestamp = PCANFD_OPT_HWTIMESTAMP_RAW;
	unsigned long opt_data_len = xl_frame_tx.data_len;
	long opt_every_us = 1000;
	unsigned long opt_frm_count = 1;
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
		.rxmt_limit = {
			[PCANXL_CAN_XL] = PCANXL_RXMT_LIMIT_MAX,
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
			"count", 'c',
			count_inline_puts, count_handler, OPT_ARG_NUM,
			.user_data = &opt_frm_count,
		},
		{
			"datalen", 'l',
			data_len_inline_puts, data_len_handler, OPT_ARG_NUM,
			.user_data = &opt_data_len,
		},
		{
			"slfack", 's',
			slfack_inline_puts, slfack_handler,
			.user_data = &opt_slfack,
		},
		{
			"every", 'r',
			every_inline_puts, every_handler, OPT_ARG,
			.user_data = &opt_every_us,
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
	__u32 opt_allowed_msgs = PCANFD_ALLOWED_MSG_ALL;
	int i, fd, err;

	stdlog = stderr;

	/* 1st, process cmdline options */
	err = cmdline_process_options(argc, argv, opt_table);
	if (err)
		usage("Unknown command line option\n");

	/* init real data bytes count with user value (if given) */
	xl_frame_tx.data_len = (__u16 )opt_data_len;

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

	err = pcanxl_set_option(fd, PCANFD_OPT_ALLOWED_MSGS,
				&opt_allowed_msgs, sizeof(opt_allowed_msgs));
	if (err) {
		fprintf(stderr,
			"%s: failed to set ALLOWED_MSGS option (errno %d)\n",
			dev_name, errno);
		goto lbl_exit;
	}

	__log(stddbg, "%s: ALLOWED_MSGS option set\n", dev_name);

	/* Initialize the controller according to xl_init and read init settings
	 * back, to get parameter driver default values
	 */
	err = set_and_get_init(fd, &xl_init);
	if (err)
		goto lbl_exit;

	/* Initialize frame data bytes */
	for (i = 0; i < xl_frame_tx.data_len; i++)
		xl_frame_tx.data[i] = i & 0xff;

	/* Wait for STATUS=ACTIVE */
	if (!wait_for_msg(fd, PCANFD_TYPE_STATUS) ||
			(xl_frame_rx->id != PCANFD_ERROR_ACTIVE)) {
		fprintf(stderr,
			"%s: unable to get BUS STATUS=ERROR_ACTIVE. Abort!\n",
			dev_name);
		goto lbl_exit;
	}

	/* Set SELF_ACK option if needed */
	if (opt_slfack) {
		err = pcanxl_set_option(fd, PCANFD_OPT_SELF_ACK, &opt_slfack,
					sizeof(opt_slfack));
		if (err) {
			fprintf(stderr,
				"%s: failed to set SLF_ACK option (errno %d)\n",
				dev_name, errno);
			goto lbl_exit;
		}

		__log(stddbg, "%s: SLF_ACK option set\n", dev_name);
	}

	if (opt_every_us < 0)
		xl_frame_tx.flags |= PCANFD_MSG_ECHO;

	/* starting from now, system calls may end with errno=EINTR */
	setup_sig_handler(SIGINT, signal_handler);

	for (i = 1; ; i++) {
		char type_str[PCANXL_MSG_TYPE_MAXLEN+1];
		char id_str[PCANXL_MSG_ID_MAXLEN+1];
		struct timespec time_now;

		 if (opt_frm_count && i > opt_frm_count)
			 break;

		/* SDT=manufacturer-specific => ID saved in AF */
		xl_frame_tx.af = i+1;

		xl_frame_tx.data[0] = i & 0xff;

		/* Send the frame */
		err = pcanxl_send_msg(fd, (struct pcanxl_msg *)&xl_frame_tx);
		if (err) {
			fprintf(stderr,
				"%s: failed to send frame #%u (errno %d)\n",
				dev_name, i, errno);
			break;
		}

		printf("%u\r", i+1);
		if (!(i % 10))
			fflush(stdout);

		clock_gettime(CLOCK_REALTIME, &time_now);
		to_kernel_timespec(&xl_frame_tx.timestamp, &time_now);
		__log_pcanxl_msg(stdlog, dev_name, '<',
				 (const struct pcanxl_msg *)&xl_frame_tx);

		/* Wait for the (potential) echo */
		if (xl_frame_tx.flags & PCANFD_MSG_ECHO) {
			struct __kernel_timespec time_echo;

			if (!wait_for_msg(fd, xl_frame_tx.type))
				goto lbl_exit;

			/* get the time the frame has been written on wire */
			time_echo = xl_frame_rx->timestamp;

		/* otherwise, wait for a given delay */
		} else if (opt_every_us > 0) {

			usleep(opt_every_us);
			if (errno == EINTR)
				break;
		}
	}

	fputc('\n', stdout);
	fflush(stdout);

lbl_exit:
	__log(stdlog, "%s: closing device\n", dev_name);
	close(fd);

	free(xl_frame_rx);

	return err ? 1 : (i < opt_frm_count) ? 2 : 0;
}

/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-common.c - common globals.
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <fcntl.h>		/* open() */
#include <unistd.h>		/* close() */
#include <sys/time.h>		/* struct timeval, timersub() */
#include <errno.h>

#include "libpcanxl.h"
#include "pcanxl-cmdline.h"
#include "pcanxl-utils.h"

/* PCAN XL interfaces default clock rate (Hz) */
#define PCANXL_DEF_CLOCK	160000000

#ifdef PCANXL_CAN_CC_ONLY
#define PCANXL_DEF_INIT		0
#define PCANXL_DEF_TYPE		PCANXL_TYPE_CANCC
#define PCANXL_DEF_FLAGS	PCANFD_TIMESTAMP|PCANFD_MSG_EXT
#define PCANXL_DEF_DATALEN	8

#elif defined(PCANXL_CAN_FD_ONLY)
#define PCANXL_DEF_INIT		PCANXL_INIT_FD
#define PCANXL_DEF_TYPE		PCANXL_TYPE_CANFD
#define PCANXL_DEF_FLAGS	PCANFD_TIMESTAMP|PCANFD_MSG_EXT|PCANFD_MSG_BRS
#define PCANXL_DEF_DATALEN	64

#else /* CAN_XL */
#define PCANXL_DEF_INIT		PCANXL_INIT_XL|\
				PCANXL_INIT_TRX_MODE_SWITCH_ON|\
				PCANXL_INIT_ERR_SIGNALING_OFF

#define PCANXL_DEF_TYPE		PCANXL_TYPE_CANXL
#define PCANXL_DEF_FLAGS	PCANFD_TIMESTAMP
#define PCANXL_DEF_DATALEN	2048

#endif

#define PCANXL_DEF_NBITRATE	1000000
#define PCANXL_DEF_NSP		0

#define PCANXL_DEF_DBITRATE	4000000
#define PCANXL_DEF_DSP		0
#define PCANXL_DEF_DSSPO	0

#define PCANXL_DEF_XBITRATE	10000000
#define PCANXL_DEF_XSP		0
#define PCANXL_DEF_XSSPO	60

/*
 * Optimum PWM symbol setting:
 * pwms = pwml / 3 (25%/75%)
 * pwmo = 0 except for some cases
 */
#define PCANXL_PWMO_10MB	0
#define PCANXL_PWMS_10MB	4
#define PCANXL_PWML_10MB	12

#define PCANXL_PWMO_4MB		0
#define PCANXL_PWMS_4MB		2
#define PCANXL_PWML_4MB		6

/* nom_bitrate = 500 k */
#define PCANXL_PWMO_2MB		0
#define PCANXL_PWMS_2MB		1
#define PCANXL_PWML_2MB		3

#define PCANXL_PWMO_DEF		0
#define PCANXL_PWMS_DEF		0
#define PCANXL_PWML_DEF		0

#define PCANXL_DEF_PWMO		PCANXL_PWMO_DEF
#define PCANXL_DEF_PWMS		PCANXL_PWMS_DEF
#define PCANXL_DEF_PWML		PCANXL_PWML_DEF

static FILE *stdlog = NULL;
static FILE *stddbg = NULL;
static char *dev_name = NULL;

static struct pcanxl_msg_xl *xl_frame_rx;

/*
 * static void usage(const char *fmt, ...)
 */
static void usage(const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);

	if (fmt) {
		vprintf(fmt, ap);
		putchar('\n');
	}

	printf("(see -h | --help option)\n");

	va_end(ap);
	exit(0);
}

static void help_inline_puts(struct cmdline_opt *opt)
{
	puts("display this help");
}

static void nolog_inline_puts(struct cmdline_opt *opt)
{
	puts("set discreet mode");
}

static int nolog_handler(struct cmdline_opt *opt, void *arg)
{
	stdlog = NULL;

	return 0;
}

static void count_inline_puts(struct cmdline_opt *opt)
{
	unsigned long *count = (unsigned long *)opt->user_data;

	printf("Number of CAN frames to process "
	       "(0: nolimit, default: %lu)\n", *count);
}

static int count_handler(struct cmdline_opt *opt, void *arg)
{
	unsigned long *count = (unsigned long *)opt->user_data;

	if (!arg)
		usage("Missing or invalid count of frames specification\n");

	*count = *(unsigned long *)arg;

	__log(stddbg, "%s(): count = %lu\n", __func__, *count);

	return 0;
}

static void slfack_inline_puts(struct cmdline_opt *opt)
{
	puts("set self-ack mode (default: off)");
}

static int slfack_handler(struct cmdline_opt *opt, void *arg)
{
	__u32 *opt_slfack = (__u32 *)opt->user_data;

	*opt_slfack = 1;

	__log(stddbg, "%s(): opt_slfack = %lu\n", __func__, *opt_slfack);

	return 0;
}

static void listen_only_inline_puts(struct cmdline_opt *opt)
{
	puts("Set listen-only initialisation mode (default: off)");
}

static int listen_only_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	pxli->flags |= PCANFD_INIT_LISTEN_ONLY;

	__log(stddbg, "%s(): flags = %08xh\n", __func__, pxli->flags);

	return 0;
}

static const char *on_off_str[2] = { "off", "on" };

static void tms_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("CANXL Transceiver Mode Switch on|off (default: %s)\n",
	       on_off_str[!!(pxli->flags & PCANXL_INIT_TRX_MODE_SWITCH_ON)]);
}

static int tms_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;
	char *str = (char *)arg;

	if (!str)
		usage("Missing transceiver mode switch specification\n");

	if (!strcasecmp(str, "on") || !strcasecmp(str, "1")) {
		pxli->flags |= PCANXL_INIT_TRX_MODE_SWITCH_ON;

	} else if (!strcasecmp(str, "off") || !strcasecmp(str, "0")) {
		pxli->flags &= ~PCANXL_INIT_TRX_MODE_SWITCH_ON;
	} else {
		usage("Wrong error signaling mode specification!");
	}

	__log(stddbg, "%s(): flags = %08xh\n", __func__, pxli->flags);

	return 0;
}

static void es_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("CANXL Error Signaling mode on|off (default: %s)\n",
	       on_off_str[!(pxli->flags & PCANXL_INIT_ERR_SIGNALING_OFF)]);
}

static int es_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;
	char *str = (char *)arg;

	if (!str)
		usage("Missing error signaling mode specification\n");

	/* if ES is on, then TMS can't be on too (on is the application default)
	 * but set INIT_FD.
	 */
	if (!strcasecmp(str, "on") || !strcasecmp(str, "1")) {
		pxli->flags &= ~(PCANXL_INIT_ERR_SIGNALING_OFF|
				 PCANXL_INIT_TRX_MODE_SWITCH_ON);
		pxli->flags |= PCANXL_INIT_FD;

	} else if (!strcasecmp(str, "off") || !strcasecmp(str, "0")) {
		pxli->flags |= PCANXL_INIT_ERR_SIGNALING_OFF;
	} else {
		usage("Wrong error signaling mode specification!");
	}

	__log(stddbg, "%s(): flags = %08xh\n", __func__, pxli->flags);

	return 0;
}

static void clock_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("Clock specification in MHz "
	       "(default: %u MHz)\n", pxli->clock_Hz / 1000000);
}

static int clock_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;
	unsigned long clock;

	if (!arg)
		usage("Missing or invalid clock specification\n");

	clock = *(unsigned long *)arg;
	if ((clock < 20) || (clock > 160))
		usage("Clock value must be in range [20..160]\n");

	pxli->clock_Hz = clock * 1000000;

	__log(stddbg, "%s(): clock_HZ = %lu\n",
	      __func__, pxli->clock_Hz);

	return 0;
}

static int btr_sp_handler(char *argv, struct pcan_bittiming *pbt)
{
	char *sp_sep = strchr(argv, ':');
	unsigned long v;
	int err;

	if (sp_sep) {
		err = strtounit(sp_sep+1, NULL,  &v);
		if (err)
			return -1;

		/* SHOULD be in range [0..9999] */
		pbt->sample_point = v;
		*sp_sep = '\0';
	}

	err = strtounit(argv, "kM",  &v);
	if (err)
		return -2;

	pbt->bitrate = v;

	return err;
}

static void nominal_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("nominal bitrate btr[:sp] "
	       "(default: %uK:%04u)\n", pxli->nominal.bitrate / 1000,
	       pxli->nominal.sample_point);
}

static int nominal_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	switch (btr_sp_handler(arg, &pxli->nominal)) {
	case -1:
		usage("Wrong nominal sample point specification\n");
	case -2:
		usage("Wrong nominal bitrate specification\n");
	}

	__log(stddbg, "%s(): nominal_arg = %lu (sp=%lu)\n",
	      __func__, pxli->nominal.bitrate, pxli->nominal.sample_point);

	return 0;
}

static void fd_data_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("CANFD data bitrate btr[:sp] "
	       "(default: %uM:%04u)\n", pxli->fd_data.bitrate / 1000000,
	       pxli->fd_data.sample_point);
}

static int fd_data_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	switch (btr_sp_handler(arg, &pxli->fd_data)) {
	case -1:
		usage("Wrong CANFD data sample point specification\n");
	case -2:
		usage("Wrong CANFD data bitrate specification\n");
	}

	/* fd_data implies PCANXL_INIT_FD */
	pxli->flags |= PCANXL_INIT_FD;

	__log(stddbg, "%s(): fd_data_arg = %lu (sp=%lu)\n",
	      __func__, pxli->fd_data.bitrate, pxli->fd_data.sample_point);

	return 0;
}

static void xl_data_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("CANXL data bitrate btr[:sp] "
	       "(default: %uM:%04u)\n", pxli->xl_data.bitrate / 1000000,
	       pxli->xl_data.sample_point);
}

static int xl_data_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	switch (btr_sp_handler(arg, &pxli->xl_data)) {
	case -1:
		usage("Wrong CANXL data sample point specification\n");
	case -2:
		usage("Wrong CANXL data bitrate specification\n");
	}

	/* xl_data implies PCANFD_INIT_XL */
	pxli->flags |= PCANXL_INIT_XL;

	__log(stddbg, "%s(): xl_data_arg = %lu (sp=%lu)\n",
	      __func__, pxli->xl_data.bitrate, pxli->xl_data.sample_point);

	return 0;
}

static void pwm_inline_puts(struct cmdline_opt *opt)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;

	printf("CANXL PWM specification pwms[:pwml[:pwmo]] (default %u:%u:%u)\n",
	       pxli->xl_pwm.pwm_short, pxli->xl_pwm.pwm_long,
	       pxli->xl_pwm.pwm_offset);
}

static int pwm_handler(struct cmdline_opt *opt, void *arg)
{
	struct pcanxl_init *pxli = (struct pcanxl_init *)opt->user_data;
	char *pc = (char *)arg, *endptr;
	unsigned long pwms, pwml, pwmo;

	pwms = strtoul(pc, &endptr, 0);
	switch (*endptr) {
	case ':' :
		pc = endptr + 1;
		pwml = strtoul(pc, &endptr, 0);
		switch (*endptr) {
		case ':' :
			pc = endptr + 1;
			pwmo = strtoul(pc, &endptr, 0);
			switch (*endptr) {
			case ':' :
			case '\0':
				pxli->xl_pwm.pwm_offset = (__u16 )pwmo;
				break;
			default:
				usage("Wrong PWM offset value");
			}
		case '\0':
			pxli->xl_pwm.pwm_long = (__u16 )pwml;
			break;
		default:
			usage("Wrong PWM long value");
		}
	case '\0':
		pxli->xl_pwm.pwm_short = (__u16 )pwms;
		break;
	default:
		usage("Wrong PWM short value");
	}

	__log(stddbg, "%s(): PWM = %u:%u:%u\n",
	      __func__, pxli->xl_pwm.pwm_short, pxli->xl_pwm.pwm_long,
	      pxli->xl_pwm.pwm_offset);

	return 0;
}

static void data_len_inline_puts(struct cmdline_opt *opt)
{
	unsigned long *data_len = (unsigned long *)opt->user_data;

	printf("CAN frame data length specification "
	       "(default: %lu Bytes)\n", *data_len);
}

static int data_len_handler(struct cmdline_opt *opt, void *arg)
{
	unsigned long *data_len = (unsigned long *)opt->user_data;

	if (!arg)
		usage("Missing or invalid data length specification\n");

	*data_len = *(unsigned long *)arg;
	if (*data_len > PCANXL_MAXDATALEN)
		usage("CAN frame can't be larger than %u bytes!\n",
		      PCANXL_MAXDATALEN);

	__log(stddbg, "%s(): data_len = %lu\n", __func__, *data_len);

	return 0;
}

/*
 * static int set_and_get_init(int fd, struct pcanxl_init *xl_init)
 */
static int set_and_get_init(int fd, struct pcanxl_init *xl_init)
{
	int err;

	__log(stdlog, "%s: init %luMHz core in CAN_%s with "
	      "flg=%08xh bitrates=[nominal=%lu:%04lu ",
	      dev_name, xl_init->clock_Hz / 1000000,
	      (xl_init->flags & PCANXL_INIT_XL) ? "XL" :
		      (xl_init->flags & PCANXL_INIT_FD) ? "FD" :
		      "CC",
	      xl_init->flags,
	      xl_init->nominal.bitrate, xl_init->nominal.sample_point);

	if (xl_init->flags & PCANXL_INIT_FD)
		__log(stdlog, "fd=%lu:%04lu sspo=%u ",
		      xl_init->fd_data.bitrate, xl_init->fd_data.sample_point,
		      xl_init->fd_data.ssp_offset);

	if (xl_init->flags & PCANXL_INIT_XL) {

		__log(stdlog, "xl=%lu:%04lu sspo=%u] ES=%u TMS=%u",
		      xl_init->xl_data.bitrate, xl_init->xl_data.sample_point,
		      xl_init->xl_data.ssp_offset,
		      !(xl_init->flags & PCANXL_INIT_ERR_SIGNALING_OFF),
		      !!(xl_init->flags & PCANXL_INIT_TRX_MODE_SWITCH_ON));

		if (xl_init->flags & PCANXL_INIT_TRX_MODE_SWITCH_ON) {
			/* If user changed default xl data bitrate, then set pwm
			 * settings to 0 so that driver will compute them
			 */
			if (xl_init->xl_data.bitrate != PCANXL_DEF_XBITRATE)
				memset(&xl_init->xl_pwm, '\0',
				       sizeof(struct pcanxl_pwm));

			__log(stdlog, " pwm[short=%u long=%u offset=%u]",
			      xl_init->xl_pwm.pwm_short,
			      xl_init->xl_pwm.pwm_long,
			      xl_init->xl_pwm.pwm_offset);
		}
	}
	__log(stdlog, "\n");

	/* Initialize the controller with user and default values */
	err = pcanxl_set_init(fd, xl_init);
	if (err) {
		fprintf(stderr, "%s: failed to initialize device (errno %d)\n",
			dev_name, errno);
		goto lbl_return;
	}

	__log(stdlog, "%s: device initialized\n", dev_name);

	/* Read controller effective initialization settings */
	err = pcanxl_get_init(fd, xl_init);
	if (err) {
		fprintf(stderr,
			"%s: failed to get device init settings (errno %d)\n",
			dev_name, errno);
		goto lbl_return;
	}

	__log(stdlog, "%s: init settings=[clock=%luMHz flags=%08xh "
	      "bitrate[nominal=%lu:%04lu brp=%u tseg1=%u tseg2=%u sjw=%u",
	      dev_name, xl_init->clock_Hz / 1000000, xl_init->flags,
	      xl_init->nominal.bitrate, xl_init->nominal.sample_point,
	      xl_init->nominal.brp, xl_init->nominal.tseg1,
	      xl_init->nominal.tseg2, xl_init->nominal.sjw);

	if (xl_init->flags & PCANXL_INIT_FD)
		__log(stdlog, " fd=%lu:%04lu brp=%u tseg1=%u tseg2=%u "
			      "sjw=%u sspo=%u",
		      xl_init->fd_data.bitrate, xl_init->fd_data.sample_point,
		      xl_init->fd_data.brp, xl_init->fd_data.tseg1,
		      xl_init->fd_data.tseg2, xl_init->fd_data.sjw,
		      xl_init->fd_data.ssp_offset);

	if (xl_init->flags & PCANXL_INIT_XL) {
		__log(stdlog, " xl=%lu:%04lu brp=%u tseg1=%u tseg2=%u sjw=%u "
			      "sspo=%u] ES=%u TMS=%u",
		      xl_init->xl_data.bitrate, xl_init->xl_data.sample_point,
		      xl_init->xl_data.brp, xl_init->xl_data.tseg1,
		      xl_init->xl_data.tseg2, xl_init->xl_data.sjw,
		      xl_init->xl_data.ssp_offset,
		      !(xl_init->flags & PCANXL_INIT_ERR_SIGNALING_OFF),
		      !!(xl_init->flags & PCANXL_INIT_TRX_MODE_SWITCH_ON));

		if (xl_init->flags & PCANXL_INIT_TRX_MODE_SWITCH_ON) {
			__log(stdlog, " pwm[short=%u long=%u offset=%u]",
			      xl_init->xl_pwm.pwm_short,
			      xl_init->xl_pwm.pwm_long,
			      xl_init->xl_pwm.pwm_offset);
		}
	}
	__log(stdlog, "]");

lbl_return:
	__log(stdlog, "\n");

	return err;
}

/*
 * static int wait_for_msg(int fd, int msg_type)
 */
static int wait_for_msg(int fd, int msg_type)
{
	char type_str[PCANXL_MSG_TYPE_MAXLEN+1];
	char id_str[PCANXL_MSG_ID_MAXLEN+1];
	int err, lprefix;

	/* ALWAYS set data buffer length before! */
	xl_frame_rx->data_len = sizeof(xl_frame_rx->data);

	err = pcanxl_recv_msg(fd, (struct pcanxl_msg *)xl_frame_rx);
	if (err) {
		if (errno != EINTR)
			fprintf(stderr,
				"%s: failed to read msg (errno %d)\n",
				dev_name, errno);
		return 0;
	}

	__log_pcanxl_msg(stdlog, dev_name, '>',
			 (const struct pcanxl_msg *)xl_frame_rx);

	return (xl_frame_rx->type == msg_type);
}

/*
 * static void signal_handler(int s)
 *
 * Linux signal handler.
 *
 * Note that all children do inherit from their parent's signal handler
 */
static void signal_handler(int s)
{
	__log(stddbg, "SIG(%d) caught!\n", s);

	switch (s) {

	case SIGINT:
		__log(stdlog, "User interrupt!\n");
		break;

	default:
		break;
	}
}


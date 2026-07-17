/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanerrgen.c - CAN CC/FD error generator
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <signal.h>
#include <fcntl.h>              /* open() */
#include <unistd.h>             /* close() */
#include <sys/time.h>           /* struct timeval, timersub() */
#include <errno.h>

#include <libpcanfd.h>

#define CMD_CHECK		"check"
#define CMD_PERIODIC		"every"
#define CMD_SINGLE		"single"

#define CMD_OPT_NOMBTR		"nombtr"	/* btr[:sp] */
#define CMD_OPT_NOMBTR_SHORT	'b'		/* same than pcanfdtst */
#define CMD_OPT_FDBTR		"fdbtr"
#define CMD_OPT_FDBTR_SHORT	'd'		/* same than pcanfdtst */

#define CMD_OPT_BITPOS		"bitpos"
#define CMD_OPT_BITPOS_SHORT	'p'
#define CMD_OPT_HELP		"help"
#define CMD_OPT_HELP_SHORT	'h'
#define CMD_OPT_CANID		"id"
#define CMD_OPT_CANID_SHORT	'i'
#define CMD_OPT_KILL		"kill"
#define CMD_OPT_KILL_SHORT	'k'
#define CMD_OPT_QUIET		"quiet"
#define CMD_OPT_QUIET_SHORT	'q'
#define CMD_OPT_SPARE		"spare"
#define CMD_OPT_SPARE_SHORT	's'
#define CMD_OPT_WAIT		"wait"
#define CMD_OPT_WAIT_SHORT	'w'

#define BITPOS_DEFAULT		50
#define KILL_DEFAULT		1
#define QUIET_DEFAULT		0
#define SPARE_DEFAULT		5
#define WAIT_DEFAULT		0

static int quiet = QUIET_DEFAULT;

/*
 * void usage(const char *fmt, ...)
 */
static void usage(const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);

	if (fmt) {
		vprintf(fmt, ap);
		putchar('\n');
	}

	printf(
"\n"
"USAGE:\n"
"\n"
"	$ pcangenerr CMD [OPTIONS] /dev/pcanX\n"
"\n"
"CMD:\n"
"	%s		check whether the device is capable of generating\n"
"			errors on the CAN bus\n"
"	%s		loop on destroying a certain number of CAN frames\n"
"			(default: %u) based on an ID, sparing others (default:%u)\n"
"	%s		destroy bits in the next CAN frame\n"
"\n"
"OPTIONS:\n"
"\n"
"	-%c | --%s b	nominal bitrate[:sample_point x 10000]\n"
"	-%c | --%s b	CAN FD data bitrate[:sample_point x 10000]\n"
"	-%c | --%s	display this help\n"
"	-%c | --%s n	frame CAN ID to destroy next\n"
"	-%c | --%s n	number of frames of the given ID to destroy in a row\n"
"	-%c | --%s n	bit position to destroy, either > 15 or > 39 depending\n"
"			on the standard or extended format of the CAN ID\n"
"			(default: %u)\n"
"	-%c | --%s	quiet mode (default: %s)\n"
"	-%c | --%s n	number of frames of the given ID to spare in a row\n"
"	-%c | --%s s	delay before automatically stopping the generator,\n"
"			0 means infinite wait, ^C to stop (default: %u s)\n"
"\n"
	, CMD_CHECK
	, CMD_PERIODIC, KILL_DEFAULT, SPARE_DEFAULT
	, CMD_SINGLE
	, CMD_OPT_NOMBTR_SHORT, CMD_OPT_NOMBTR
	, CMD_OPT_FDBTR_SHORT, CMD_OPT_FDBTR
	, CMD_OPT_HELP_SHORT, CMD_OPT_HELP
	, CMD_OPT_CANID_SHORT, CMD_OPT_CANID
	, CMD_OPT_KILL_SHORT, CMD_OPT_KILL
	, CMD_OPT_BITPOS_SHORT, CMD_OPT_BITPOS, BITPOS_DEFAULT
	, CMD_OPT_QUIET_SHORT, CMD_OPT_QUIET, QUIET_DEFAULT ? "yes" : "no"
	, CMD_OPT_SPARE_SHORT, CMD_OPT_SPARE
	, CMD_OPT_WAIT_SHORT, CMD_OPT_WAIT, WAIT_DEFAULT
	);

	va_end(ap);
	exit(1);
}

/*
 * void help(void)
 */
static void help(void)
{
	usage(
"CAN Error generator for Linux PCAN driver.\n"
"Generates error(s) on the CAN bus through a PCAN device capable of doing so.");
}

/*
 * void signal_handler(int s)
 *
 * Linux signal handler.
 *
 * Note that all children do inherit from their parent's signal handler
 */
static void signal_handler(int s)
{
	switch (s) {

	case SIGINT:
		if (!quiet)
			printf("User interrupt!");
		else
			putchar('\n');
		fflush(stdout);
		break;

	default:
		break;
	}
}

/*
 * int setup_sig_handler(int signum, void (*f)(int))
 */
static int setup_sig_handler(int signum, void (*f)(int))
{
	struct sigaction act;

	memset(&act, 0, sizeof act);
	sigemptyset(&act.sa_mask);
	act.sa_handler = f;

	/* siagaction() is thread -safe */
	return sigaction(signum, &act, NULL);
}

/*
 * strtounit(argv, "kM");
 * strtouint(argv, "ms");
 */
static char *strtounit(char *str, char *units, unsigned long *pv)
{
	char *endptr;
	unsigned long m = 1;
	unsigned long v = strtoul(str, &endptr, 0);

	if (*endptr) {
		if (units) {
			char *pu;

			/* might not be invalid if found char is a unit */
			for (pu = units; *pu; pu++) {
				m *= 1000;
				if (*endptr == *pu) {
					endptr++;
					break;
				}
			}

			/* *endptr is not a unit, then don't change v */
			if (!*pu)
				m = 1;
		}
	}

	if (pv)
	       *pv = v * m;

	return endptr;
}

/*
 * char *btrstr(unsigned long btr, char *buffer, int l)
 */
static char *btrstr(unsigned long btr, char *buffer, int l)
{
	if (btr >= 1000000)
		snprintf(buffer, l, "%luM", btr / 1000000);
	else if (btr >= 1000)
		snprintf(buffer, l, "%luk", btr / 1000);
	else
		snprintf(buffer, l, "%lu", btr);

	return buffer;
}

/*
 * int main(int argc, char *argv[])
 *
 */
int main(int argc, char *argv[])
{
	struct pcanfd_init fdi = { .flags = 0, };
	struct pcanfd_error_generator eg;
	char *dev_name = NULL;
	unsigned int auto_stop_delay = 0;
	__u32 dev_features;
	unsigned char ctx = 0;
	int i, fd, err;

	/* Init to invalid values */
	memset(&eg, 0xff, sizeof(eg));

	/* Next, get cmdline parameters */
	for (i = 1; i < argc; i++)
		if (ctx) {
			unsigned long btr, sp = 0;
			char *endptr;
			long l;

			switch (ctx) {
			case CMD_OPT_CANID_SHORT:
			case CMD_OPT_BITPOS_SHORT:
			case CMD_OPT_KILL_SHORT:
			case CMD_OPT_SPARE_SHORT:
			case CMD_OPT_WAIT_SHORT:
				l = (long )strtoul(argv[i], &endptr, 0);
				if (*endptr || l < 0)
					usage("'-%c': Value must be numeric and positive", ctx);
				break;
			case CMD_OPT_NOMBTR_SHORT:
			case CMD_OPT_FDBTR_SHORT:
#if 0
				btr = strtoul(argv[i], &endptr, 10);
#else
				endptr = strtounit(argv[i], "kM", &btr);
#endif
				switch (*endptr) {
				case ':':
					sp = strtoul(endptr+1, &endptr, 10);
					if (*endptr || sp > 10000)
						usage("'-%c %u:%u%c': Invalid sample point value (should be in range [0..10000])", ctx, btr, sp, *endptr);
				case 0:
					break;
				default:
					usage("'-%c %u%c': Invalid bitrate specification", ctx, btr, *endptr);
				}
				break;
			}

			switch (ctx) {
			case CMD_OPT_BITPOS_SHORT:
				eg.bit_pos = l;
				break;
			case CMD_OPT_CANID_SHORT:
				eg.can_id = l;
				break;
			case CMD_OPT_KILL_SHORT:
				eg.to_kill_nb = l;
				break;
			case CMD_OPT_SPARE_SHORT:
				eg.to_spare_nb = l;
				break;
			case CMD_OPT_WAIT_SHORT:
				auto_stop_delay = l;
				break;
			case CMD_OPT_NOMBTR_SHORT:
				fdi.nominal.bitrate = btr;
				fdi.nominal.sample_point = sp;
				break;
			case CMD_OPT_FDBTR_SHORT:
				fdi.flags |= PCANFD_INIT_FD;
				fdi.data.bitrate = btr;
				fdi.data.sample_point = sp;
				break;
			}

			ctx = 0;

		} else if (argv[i][0] == '-') {
			char opt = argv[i][1];

			if (opt == '-') {
				if (!strcmp(argv[i]+2, CMD_OPT_BITPOS))
					opt = CMD_OPT_BITPOS_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_HELP))
					opt = CMD_OPT_HELP_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_CANID))
					opt = CMD_OPT_CANID_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_QUIET))
					opt = CMD_OPT_QUIET_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_WAIT))
					opt = CMD_OPT_WAIT_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_NOMBTR))
					opt = CMD_OPT_NOMBTR_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_FDBTR))
					opt = CMD_OPT_FDBTR_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_SPARE))
					opt = CMD_OPT_SPARE_SHORT;
				else if (!strcmp(argv[i]+2, CMD_OPT_KILL))
					opt = CMD_OPT_KILL_SHORT;
				else
					usage("'--%s': Unknown long option",
					      argv[i]+2);
			}

			switch (opt) {
			case CMD_OPT_BITPOS_SHORT:
			case CMD_OPT_CANID_SHORT:
			case CMD_OPT_KILL_SHORT:
			case CMD_OPT_SPARE_SHORT:
			case CMD_OPT_WAIT_SHORT:
			case CMD_OPT_NOMBTR_SHORT:
			case CMD_OPT_FDBTR_SHORT:
				ctx = opt;
				break;
			case CMD_OPT_QUIET_SHORT:
				quiet = 1;
				break;
			case CMD_OPT_HELP_SHORT:
				help();
				break;
			default:
				usage("'-%c': Unknown option", opt);
			}

		} else if (i == 1) {
			if (!strcmp(argv[1], CMD_SINGLE))
				eg.mode = PCANFD_ERR_GEN_START_SINGLE;
			else if (!strcmp(argv[1], CMD_PERIODIC))
				eg.mode = PCANFD_ERR_GEN_START_PERIODIC;
			else if (!strcmp(argv[1], CMD_OPT_HELP))
				help();
			else if (strcmp(argv[1], CMD_CHECK))
				usage("'%s': Unknown command", argv[1]);
		} else {
			dev_name = argv[i];
		}

	if (!dev_name)
		usage("Missing device name on command line");

	/* Sanity checks */
	switch (eg.mode) {
	case PCANFD_ERR_GEN_START_SINGLE:
	case PCANFD_ERR_GEN_START_PERIODIC:
		if (eg.bit_pos == 0xffff)
			eg.bit_pos = BITPOS_DEFAULT;

		if (eg.mode == PCANFD_ERR_GEN_START_PERIODIC) {

			if (eg.can_id == 0xffffffff)
				usage("An explicit value must be given to the CAN ID of the frame(s) to destroy.");

			if (eg.to_kill_nb == 0xffff)
				eg.to_kill_nb = KILL_DEFAULT;

			if (eg.to_spare_nb == 0xffff)
				eg.to_spare_nb = SPARE_DEFAULT;
		}
		break;
	case 0xffff:	/* check */
		break;
	default:
		usage("CMD is mandatory on command line");
	}

	fd = open(dev_name, O_RDONLY);
	if (fd < 0)
		usage("Unable to open device %s (errno %d)", dev_name, errno);

	if (!quiet)
		printf("%s: opened\n", dev_name);

	/* Check if the device is able to generate errors */
	err = pcanfd_get_option(fd, PCANFD_OPT_CHANNEL_FEATURES,
				&dev_features, sizeof(dev_features));
	if (err < 0) {
		perror("Failed to get device channel features");
		goto lbl_close;
	}

	if (!(dev_features & PCANFD_FEATURE_ERR_GEN)) {
		printf("%s: cannot generate error on the CAN bus, sorry.\n",
		       dev_name);
		err = ENOTSUP;
		goto lbl_close;
	}

	if (!quiet || eg.mode == 0xffff) {
		printf("%s: capable of generating errors on the CAN bus\n",
		       dev_name);

		if (eg.mode == 0xffff) {
			err = 0;
			goto lbl_close;
		}
	}

	/* Must know the CAN bus configuration to start error generator.
	 * - If the device is already opened, our init doesn't care and will be
	 *   rejected with -EBUSY.
	 * - If the device is not opened, it must be configured with the right
	 *   settings.
	 */
	if (fdi.nominal.bitrate) {
		int busy = 0;

		err = pcanfd_set_init(fd, &fdi);
		switch (err) {
		case -EBUSY:
			busy++;
		case 0:
			break;
		default:
			perror("Initialization of the device failed");
			goto lbl_close;
		}

		/* read init settings */
		err = pcanfd_get_init(fd, &fdi);
		if (err)
			perror("Reading initialization settings failed");
		else if (!quiet) {
			char tmp[10];
			const int ltmp = sizeof(tmp);

			printf("%s: %sconfigured with -b %s:%u",
			       dev_name, (busy) ? "already " : "",
			       btrstr(fdi.nominal.bitrate, tmp, ltmp),
			       fdi.nominal.sample_point);
			if (fdi.flags & PCANFD_INIT_FD) 
				printf(" -d %s:%u",
				       btrstr(fdi.data.bitrate, tmp, ltmp),
				       fdi.data.sample_point);

			putchar('\n');
		}
	}

	/* Start error generator */
	err = pcanfd_set_option(fd, PCANFD_OPT_ERR_GEN, &eg, sizeof(eg));
	if (err) {
		perror("Failed to start/stop error generator");
		goto lbl_close;
	}

	if (!quiet) {
		printf("%s: error generator ", dev_name);
		switch (eg.mode) {
		case PCANFD_ERR_GEN_START_SINGLE:
			printf("started: next CAN frame bit #%u will be "
			       "destroyed\n", eg.bit_pos);
			break;
		case PCANFD_ERR_GEN_START_PERIODIC:
			printf("started: periodically destroying bit #%u of the"
			       " next %u CAN frames with ID=%08Xh, then sparing"
			       " the following %u frames\n",
			       eg.bit_pos, eg.to_kill_nb,
			       eg.can_id, eg.to_spare_nb);
			break;
		}
	}

	/* starting from now, system calls may end with errno=EINTR */
	setup_sig_handler(SIGINT, signal_handler);

	/* In any case, we MUST wait, because we must be certain that the
	 * command will be taken into account, before closing.
	 */
	if (auto_stop_delay <= 0) {

		printf("%s: press Ctrl-C to stop error generator...", dev_name);
		fflush(stdout);

		/* infinite wait stopped upon receiving a signal */
		pause();
	} else {
		if (!quiet) {
			printf("%s: waiting %u s. before stopping "
		       	       "error generator...",
			       dev_name, auto_stop_delay);
			fflush(stdout);
		}

		sleep(auto_stop_delay);
	}

	if (!quiet)
		printf("\n%s: stopping error generator now\n", dev_name);

	if (eg.mode == PCANFD_ERR_GEN_START_PERIODIC) {

		/* Stop error generator now */
		eg.mode = PCANFD_ERR_GEN_STOP;
		err = pcanfd_set_option(fd, PCANFD_OPT_ERR_GEN,
					&eg, sizeof(eg));
		if (err)
			perror("Failed to stop error generator");
	}

lbl_close:
	close(fd);

	if (!quiet)
		printf("%s: closed (return code=%d)\n", dev_name, err);

	return err;
}

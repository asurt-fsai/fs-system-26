/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-cmdline.c
*
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#include <string.h>
#include <stdlib.h>

#include "pcanxl-cmdline.h"
#include "pcanxl-utils.h"

/*
 * int cmdline_process_options(int argc, char *argv[],
 * 			       struct cmdline_opt *opt_table)
 *
 * @RETURN:
 *
 * 0	options processing has succeeded
 * < 0	error in processing command line options
 */
int cmdline_process_options(int argc, char *argv[],
			    struct cmdline_opt *opt_table)
{
	int i, j, err = 0;
	unsigned long v;

	for (i = 1; i < argc; i++) {
		if (argv[i][0] == '-') {
			struct cmdline_opt *o;
			char opt = argv[i][1];

			if (opt == '-') {
				for (o = opt_table; o->long_name; o++)
					if (!strcmp(argv[i]+2, o->long_name)) {
						opt = o->abbrev;
						break;
					}
			}

			for (o = opt_table; o->long_name; o++) {
				void *arg = NULL;

				if (opt != o->abbrev)
					continue;

				if ((o->flags & OPT_ARG) && (++i < argc)) {

					if (o->flags & OPT_NUM) {
						err = strtounit(argv[i],
								"kM",
								&v);
						if (!err)
							arg = &v;
					} else {
						arg = argv[i];
					}
				}

				err = o->opt_handler(o, arg);

				/* Note: option arg is marked as an option so
				 * that furth loop on cmdline will not interpret
				 * it as a cmdline arg.
				 *
				 */
				if (arg)
					argv[i][0] = '-';

				break;
			}

			if (!o->long_name)
				return -1;

			if (err)
				break;
		}
	}

	return err;
}

/*
 * void cmdline_display_options(struct cmdline_opt *opt_table)
 */
void cmdline_display_options(struct cmdline_opt *opt_table)
{
	const char *fmt = "-%c | --%s %c";
	struct cmdline_opt *opt;
	int l, lmax = 0;

	/* 1st pass to compute length of lines */
	for (opt = opt_table; opt->long_name; opt++) {
		l = snprintf(NULL, 0, fmt,
			     opt->abbrev, opt->long_name,
			(opt->flags & OPT_ARG) ? 'v' : ' ');
		if (l > lmax)
			lmax = l;
	}

	/* 2nd pass to display and fill with blanks */
	for (opt = opt_table; opt->long_name; opt++) {
		l = printf(fmt,
			   opt->abbrev, opt->long_name,
			   (opt->flags & OPT_ARG) ? 'v' : ' ');
		while (l++ <= lmax)
			putchar(' ');
		if (opt->opt_help_puts)
			opt->opt_help_puts(opt);
		else
			putchar('\n');
	}

	putchar('\n');
}

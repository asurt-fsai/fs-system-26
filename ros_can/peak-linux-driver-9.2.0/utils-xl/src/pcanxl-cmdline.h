/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-cmdline.h
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#ifndef __CMDLINE_H__
#define __CMDLINE_H__

#define OPT_ARG			0x00000001
#define OPT_NUM			0x00000002
#define OPT_ARG_NUM		(OPT_ARG|OPT_NUM)

struct cmdline_opt {
	const char *long_name;
	char abbrev;
	void (*opt_help_puts)(struct cmdline_opt *);
	int (*opt_handler)(struct cmdline_opt *, void *arg);
	unsigned long flags;
	void *user_data;
};

#ifdef __cplusplus
extern "C" {
#endif

int cmdline_process_options(int argc, char *argv[],
			    struct cmdline_opt *opt_table);

void cmdline_display_options(struct cmdline_opt *opt_table);

#ifdef __cplusplus
};
#endif

#endif /* __CMDLINE_H__ */

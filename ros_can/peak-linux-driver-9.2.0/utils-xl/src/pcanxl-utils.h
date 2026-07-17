/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-utils.h
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#ifndef __PCANXLUTILS_H__
#define __PCANXLUTILS_H__

#include <stdio.h>
#include <signal.h>

#include "pcanxl.h"

/* libbsd
 * https://gitlab.freedesktop.org/libbsd/libbsd.git
 *
 * Linux sys/time.h does not define struct timespec operation while BSD does:
 */
#ifndef timespecadd
#define	timespecadd(tsp, usp, vsp)					\
	do {								\
		(vsp)->tv_sec = (tsp)->tv_sec + (usp)->tv_sec;		\
		(vsp)->tv_nsec = (tsp)->tv_nsec + (usp)->tv_nsec;	\
		if ((vsp)->tv_nsec >= 1000000000L) {			\
			(vsp)->tv_sec++;				\
			(vsp)->tv_nsec -= 1000000000L;			\
		}							\
	} while (0)
#endif

#ifndef timespecsub
#define	timespecsub(tsp, usp, vsp)					\
	do {								\
		(vsp)->tv_sec = (tsp)->tv_sec - (usp)->tv_sec;		\
		(vsp)->tv_nsec = (tsp)->tv_nsec - (usp)->tv_nsec;	\
		if ((vsp)->tv_nsec < 0) {				\
			(vsp)->tv_sec--;				\
			(vsp)->tv_nsec += 1000000000L;			\
		}							\
	} while (0)
#endif

#define PCANXL_MSG_TYPE_MAXLEN		32
#define PCANXL_MSG_ID_MAXLEN		32
#define PCANXL_MSG_FLAGS_MAXLEN		32
#define PCANXL_MSG_CTRLR_DATA_MAXLEN	32

#ifdef __cplusplus
extern "C" {
#endif

void dump_mem(void *b, int l);

int strtounit(char *str, char *units, unsigned long *pv);

struct __kernel_timespec *to_kernel_timespec(struct __kernel_timespec *d,
					     const struct timespec *s);

int setup_sig_handler(int signum, void (*f)(int));

int pcanxl_msg_type_str(char *buf, int len, const struct pcanxl_msg *msg);
int pcanxl_msg_id_str(char *buf, int len, const struct pcanxl_msg *msg);

int __log(FILE *fp, char *fmt, ...);
void __log_pcanxl_msg(FILE *fp, const char *dev_name, unsigned char dir,
                      const struct pcanxl_msg *msg);

#ifdef __cplusplus
};
#endif

#endif /* __PCANXLUTILS_H__ */

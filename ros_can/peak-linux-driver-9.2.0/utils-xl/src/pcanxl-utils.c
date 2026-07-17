/* SPDX-License-Identifier: LGPL-2.1-only */
/*
 * pcanxl-utils.c
 *
 * Copyright (C) 2015-2026  PEAK System-Technik GmbH <www.peak-system.com>
 *
 * Contact: <linux.peak@hms-networks.com>
 * Author:  Stephane Grosjean <stephane.grosjean@hms-networks.com>
 */
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>

#include "pcanxl-utils.h"
#include "pcanxl-cmdline.h"

void dump_mem(void *b, int l)
{
	unsigned char *pc = (unsigned char *)b;
	int i;

	for (i = 0; i < l; ) {
		printf("%02x ", *pc++);

		if (!(++i % 16))
			putchar('\n');
		else if (!(i % 8))
			fputs("- ", stdout);
	}
	fflush(stdout);
}

/*
 * strtounit(argv, "kM");
 * strtouint(argv, "ms");
 */
int strtounit(char *str, char *units, unsigned long *pv)
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
				if (*endptr == *pu)
					break;
			}

			if (!*pu)
				return -1;
		} else {
			return -2;
		}
	}

	if (pv)
	       *pv = v * m;

	return 0;
}

/*
 * struct kernel_timespec *to_kernel_timespec(struct __kernel_timespec *d,
 * 					      const struct timespec *s)
 *
 * 32-bit arch: sizeof(struct timespec)=8
 */
struct __kernel_timespec *to_kernel_timespec(struct __kernel_timespec *d,
					     const struct timespec *s)
{
	d->tv_sec = s->tv_sec;
	d->tv_nsec = s->tv_nsec;

	return d;
}

/*
 * int setup_sig_handler(int signum, void (*f)(int))
 */
int setup_sig_handler(int signum, void (*f)(int))
{
	struct sigaction act;

	memset(&act, 0, sizeof act);
	sigemptyset(&act.sa_mask);
	act.sa_handler = f;

	/* siagaction() is thread -safe */
	return sigaction(signum, &act, NULL);
}

/*
 * int pcanxl_msg_type_str(char *buf, int len, const struct pcanxl_msg *msg)
 */
int pcanxl_msg_type_str(char *buf, int len, const struct pcanxl_msg *msg)
{
	char *msg_type_str;

	switch (msg->type) {
	case PCANXL_TYPE_NOP:
		msg_type_str = "PCANXL_TYPE_NOP";
		break;
	case PCANXL_TYPE_CANCC:
		msg_type_str = "PCANXL_TYPE_CANCC";
		break;
	case PCANXL_TYPE_CANFD:
		msg_type_str = "PCANXL_TYPE_CANFD";
		break;
	case PCANXL_TYPE_STATUS:
		msg_type_str = "PCANXL_TYPE_STATUS";
		break;
	/* CAN-XL API extension */
	case PCANXL_TYPE_CANXL:
		msg_type_str = "PCANXL_TYPE_CANXL";
		break;
	case PCANXL_TYPE_ERROR:
		msg_type_str = "PCANXL_TYPE_ERROR";
		break;
	default:
		msg_type_str = "PCANXL_UNKNWON";
	}

	return snprintf(buf, len, "%s(%u)", msg_type_str, msg->type);
}

/*
 * int pcanxl_msg_flags_str(char *buf, int len, const struct pcanxl_msg *msg)
 */
int pcanxl_msg_flags_str(char *buf, int len, const struct pcanxl_msg *msg)
{
	static const char *err_flg_str[32] = {
		[7] = "bus",			/* 0x00000080 */
		[8] = "pro",			/* 0x00000100 */
		[9] = "ctr",			/* 0x00000200 */
		[10] = "drv",			/* 0x00000400 */
		[11] = "ect",			/* 0x00000800 */
		[12] = "rx",			/* 0x00001000 */
		[13] = "gen",			/* 0x00002000 */
		[15] = "eso",			/* 0x00008000 */
	};

	/* DLC saved into 0x00000F00 for CAN[FD/XL] msg only */
	static const char *frm_flg_str[32] = {
		[0] = "rtr",			/* 0x00000001 */
		[1] = "ext",			/* 0x00000002 */
		[2] = "slf",			/* 0x00000004 */
		[3] = "sng",			/* 0x00000008 */

		[4] = "ech",			/* 0x00000010 */

		[12] = "trc",			/* 0x00001000 */
		[13] = "sec",			/* 0x00002000 */
		[14] = "rrs",			/* 0x00004000 */

		[20] = "brs",			/* 0x00100000 */
		[21] = "esi",			/* 0x00200000 */
	};

	static const char *all_flg_str[32] = {
		[24] = "ts",			/* 0x01000000 */
		[25] = "hw",			/* 0x02000000 */
		[28] = "ec",			/* 0x10000000 */
		[29] = "bl",			/* 0x20000000 */
		[30] = "oc",			/* 0x40000000 */
	};
	const char **flg_str;

	/* remove any DLC value from the bitmask */
	__u32 msg_flg = msg->flags & ~PCANFD_DLC_MASK;
	int i, l = 0;

	*buf = '\0';

	switch (msg->type) {
	case PCANXL_TYPE_CANFD:
	case PCANXL_TYPE_CANCC:
	case PCANXL_TYPE_CANXL:
		flg_str = frm_flg_str;
		break;
	default:
		flg_str = err_flg_str;
	}

	for (i = 0; i < 32; i++)
		if ((msg_flg & (1 << i)) && (flg_str[i])) {
			l += snprintf(buf+l, len-l, "%s,", flg_str[i]);
			msg_flg &= ~(1 << i);
		}

	for (i = 0; i < 32; i++)
		if (msg_flg & (1 << i))
			l += snprintf(buf+l, len-l, "%s,",
				      all_flg_str[i] ? all_flg_str[i] : "???");
	if (l)
		buf[--l] = '\0';

	return l;
}

/*
 * int pcanxl_msg_id_str(char *buf, int len, const struct pcanxl_msg *msg)
 */ 
int pcanxl_msg_id_str(char *buf, int len, const struct pcanxl_msg *msg)
{
	const char *msg_id_str = "PCANFD_STATUS_UNKNOWN";
	static const char *bus_state_str[PCANXL_STATUS_COUNT] = {
		"PCANFD_UNKNOWN",
		"PCANFD_ERROR_ACTIVE",
		"PCANFD_ERROR_WARNING",
		"PCANFD_ERROR_PASSIVE",
		"PCANFD_ERROR_BUSOFF",
		"PCANFD_RX_EMPTY",
		"PCANFD_RX_OVERFLOW",
		"PCANFD_RESERVED_1",
		"PCANFD_TX_OVERFLOW",
		"PCANFD_RESERVED_2",
		"PCANFD_BUS_LOAD",
		"PCANXL_OVERLOAD"
	};
	static const char *bus_err_str[PCANFD_ERRMSG_COUNT] = {
		"PCANFD_ERRMSG_BIT",
		"PCANFD_ERRMSG_FORM",
		"PCANFD_ERRMSG_STUFF",
		"PCANFD_ERRMSG_OTHER"
	};
	int l;

	switch (msg->type) {
	case PCANXL_TYPE_CANCC:
	case PCANXL_TYPE_CANFD:
		l = snprintf(buf, len, "%0*xh(%u)",
			    (msg->flags & PCANFD_MSG_EXT) ? 8 : 3,
			    msg->id, msg->id);
		break;

	case PCANXL_TYPE_CANXL:
		l =  snprintf(buf, len, "PID=%u VCID=%u",
			      PCANXL_PID(msg->id), PCANXL_VCID(msg->id));
		break;

	case PCANXL_TYPE_STATUS:
		if (msg->flags & (PCANFD_ERROR_BUS|
				  PCANFD_ERROR_PROTOCOL|
				  PCANFD_ERROR_CTRLR|
				  PCANFD_ERROR_INTERNAL)) {

			if (msg->id < PCANXL_STATUS_COUNT)
				msg_id_str = bus_state_str[msg->id];

			l = snprintf(buf, len, "%s", msg_id_str);
		} else {
			l = snprintf(buf, len, "%08xh", msg->id);
		}
		l += snprintf(buf+l, len-l, " (%u)", msg->id);
		break;

	case PCANXL_TYPE_ERROR:
		if (msg->id < PCANFD_ERRMSG_COUNT) {
			msg_id_str = bus_err_str[msg->id];

			l = snprintf(buf, len, "%s", msg_id_str);
		} else {
			l = snprintf(buf, len, "%08xh", msg->id);
		}
		l += snprintf(buf+l, len-l, " (%u)", msg->id);
		break;

	default:
		l = snprintf(buf, len, "%08xh(%u)", msg->id, msg->id);
	}

	return l;
}

/*
 * static int pcanxl_status_ctrlr_data_str(char *buf, int len,
 *					   const struct pcanxl_msg *msg)
 */
static int pcanxl_status_ctrlr_data_str(char *buf, int len,
					const struct pcanxl_msg *msg)
{
	int l = 0;

	switch (msg->id) {
	case PCANFD_ERROR_ACTIVE:
	case PCANFD_ERROR_WARNING:
	case PCANFD_ERROR_PASSIVE:
	case PCANFD_ERROR_BUSOFF:
		if (msg->flags & PCANXL_ERROR_BUS_CODETYPE)
			l += snprintf(buf+l, len-l, "err_code=%u err_type=%u",
				      msg->ctrlr_data[PCANXL_ERRCODE],
				      msg->ctrlr_data[PCANXL_ERRTYPE]);

		/* fallthrough */
	case PCANFD_BUS_LOAD:
		break;

	case PCANXL_OVERLOAD:
		l = snprintf(buf, len, "pos_code=%u ",
			     msg->ctrlr_data[PCANXL_POS_CODE]);
	}

	/* display rxerr/txerr only if they aren't 0 */
	if ((msg->flags & PCANFD_ERRCNT) &&
		(msg->ctrlr_data[PCANFD_RXERRCNT] ||
		 msg->ctrlr_data[PCANFD_TXERRCNT]))
		l += snprintf(buf+l, len-l, "rxerr=%u txerr=%u",
			      msg->ctrlr_data[PCANFD_RXERRCNT],
			      msg->ctrlr_data[PCANFD_TXERRCNT]);

	if (msg->flags & PCANFD_BUSLOAD)
		l += snprintf(buf+l, len-l, "bus=%u.%u%%",
				msg->ctrlr_data[PCANFD_BUSLOAD_UNIT],
				msg->ctrlr_data[PCANFD_BUSLOAD_DEC]);

	return l;
}

/*
 * int pcanxl_msg_ctrlr_data_str(char *buf, int len,
 * 				 const struct pcanxl_msg *msg)
 */
int pcanxl_msg_ctrlr_data_str(char *buf, int len, const struct pcanxl_msg *msg)
{
	int l = 0;

	*buf = '\0';

	switch (msg->type) {
	case PCANXL_TYPE_CANCC:
	case PCANXL_TYPE_CANFD:
	case PCANXL_TYPE_CANXL:
		if (msg->flags & PCANFD_MSG_ECHO)
			l = snprintf(buf, len, "echo=%u",
				      msg->ctrlr_data[PCANFD_ECHOID]);
		break;

	case PCANXL_TYPE_STATUS:
		l = pcanxl_status_ctrlr_data_str(buf, len, msg);
		break;

	case PCANXL_TYPE_ERROR:
		/* Note: msg->id = err_type */
		l = snprintf(buf, len, "err_code=%u",
			     msg->ctrlr_data[PCANXL_ERRCODE]);
		break;
	}

	return l;
}

int __log(FILE *fp, char *fmt, ...)
{
	int l = 0;
	va_list ap;
	va_start(ap, fmt);

	if (fp)
		l = vfprintf(fp, fmt, ap);

	va_end(ap);
	return l;
}

/*
 * void __log_pcanxl_msg(FILE *fp, const char *dev_name, unsigned char dir,
 *			 const struct pcanxl_msg *msg)
 */
void __log_pcanxl_msg(FILE *fp, const char *dev_name, unsigned char dir,
		      const struct pcanxl_msg *msg)
{
	char type_str[PCANXL_MSG_TYPE_MAXLEN+1];
	char id_str[PCANXL_MSG_ID_MAXLEN+1];
	char flags_str[PCANXL_MSG_FLAGS_MAXLEN+1];
	char ctrlr_data_str[PCANXL_MSG_CTRLR_DATA_MAXLEN+1];
	int lprefix = __log(fp, "%s: ", dev_name);
	int l;

	if (msg->flags & PCANFD_TIMESTAMP)
		lprefix += __log(fp, "%-10lld.%09lld ",
				 msg->timestamp.tv_sec, msg->timestamp.tv_nsec);

	lprefix += __log(fp, "%c ", dir);

	pcanxl_msg_type_str(type_str, sizeof(type_str), msg);

	pcanxl_msg_id_str(id_str, sizeof(id_str), msg);

	pcanxl_msg_flags_str(flags_str, sizeof(flags_str), msg);

	__log(fp, "%s: [%s flg=%08xh (%s)",
	      type_str, id_str, msg->flags, flags_str);

	if (pcanxl_msg_ctrlr_data_str(ctrlr_data_str, sizeof(ctrlr_data_str),
				      msg))
		__log(fp, " %s", ctrlr_data_str);

	if (msg->data_len)
		__log(fp, " len=%u", msg->data_len);

	__log(fp, "]");

	if (msg->data_len) {
		char line[81];
		const int cpl = (sizeof(line) - lprefix) / 3;
		int i, l;

		__log(fp, "\n");

		memset(line, ' ', l = lprefix);
		for (i = 0; i < msg->data_len; ) {

			l += snprintf(line+l, sizeof(line)-l, "%02X ",
				      msg->data[i]);

			if (!(++i % cpl)) {
				/*line[l-1] = '\0';*/
				__log(fp, "%s\n", line);
				memset(line, ' ', l = lprefix);
			}
		}
		if (i % cpl)
			__log(fp, "%s", line);
	}

	__log(fp, "\n");
}

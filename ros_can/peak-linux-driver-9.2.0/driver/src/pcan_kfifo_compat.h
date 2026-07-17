/* SPDX-License-Identifier: GPL-2.0 */
/*
 * pcan_kfifo_compat.h - kfifo API compatibility shim for kernels < 2.6.33
 *
 * Copyright (C) 2001-2025 PEAK System-Technik GmbH <www.peak-system.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Contact:      <linux.peak@hms-networks.com>
 * Maintainer:   Stephane Grosjean <stephane.grosjean@hms-networks.com>
 *
 * --------------------------------------------------------------------
 * The kfifo API was completely redesigned in Linux 2.6.33.
 * This file provides a self-contained implementation of the new
 * type-safe API (based on struct __kfifo) for older kernels.
 *
 * Only the subset used by the PCAN driver is implemented:
 *   struct __kfifo / struct kfifo
 *   kfifo_init, kfifo_reset
 *   kfifo_size, kfifo_len, kfifo_avail, kfifo_is_empty
 *   kfifo_in, kfifo_out, kfifo_out_peek
 *   kfifo_from_user, kfifo_to_user
 *   __kfifo_skip_r  (stub, never called for plain byte-fifos)
 *
 * Note: kfifo_skip_count() remains defined in pcan_kfifo.c (guard < 6.10.0)
 *       and works without modification with the struct layout below.
 * --------------------------------------------------------------------
 */
#ifndef __PCAN_KFIFO_COMPAT_H__
#define __PCAN_KFIFO_COMPAT_H__

#include <linux/version.h>

#if LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 33)

/*
 * Kernel >= 2.6.33: use the native kfifo API.
 */
#include <linux/kfifo.h>

#else /* LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 33) */

/*
 * Kernel < 2.6.33: self-contained implementation of the new-style kfifo API.
 *
 * Prerequisite: this file must be included AFTER <linux/kernel.h>,
 * <linux/string.h> and <linux/uaccess.h> (or <asm/uaccess.h>).
 * pcan_common.h takes care of that before including this file.
 */
#include <linux/kernel.h>	/* min(), pr_err(), ... */
#include <linux/string.h>	/* memcpy() */
#include <linux/errno.h>	/* EINVAL, EFAULT */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 18)
#include <linux/uaccess.h>
#else
#include <asm/uaccess.h>	/* copy_to_user(), copy_from_user() */
#endif

/* ================================================================== */
/* Structures                                                          */
/* ================================================================== */

/**
 * struct __kfifo - internal FIFO state (mirrors the 2.6.33+ kernel struct)
 * @in:    write index (never wraps; effective offset = in & mask)
 * @out:   read index
 * @mask:  size minus 1 (size must be a power of two)
 * @esize: element size (always 1 for a plain byte-FIFO)
 * @data:  pointer to the caller-allocated buffer
 */
struct __kfifo {
	unsigned int	in;
	unsigned int	out;
	unsigned int	mask;
	unsigned int	esize;
	void		*data;
};

/**
 * struct kfifo - byte-FIFO object compatible with the 2.6.33+ API
 *
 * The union satisfies the kfifo_skip_count() macro in pcan_kfifo.c
 * (guard < 6.10.0):
 *   - __tmp->kfifo   -> struct __kfifo ('out' field directly accessible)
 *   - __tmp->rectype -> char(*)[0]  -> sizeof(*rectype) == 0
 *     => the "else __kfifo->out += count" branch is always taken;
 *        __kfifo_skip_r() is never reached.
 */
struct kfifo {
	union {
		struct __kfifo	kfifo;
		char		(*rectype)[0];	/* sizeof(*rectype) == 0 */
	};
};

/* ================================================================== */
/* __kfifo_skip_r stub                                                 */
/* Never called for plain byte-fifos, but must be declared so that    */
/* the kfifo_skip_count() macro compiles without an implicit-function  */
/* error (the if(__recsize) branch references it statically).         */
/* ================================================================== */

static inline void __kfifo_skip_r(struct __kfifo *fifo, size_t recsize)
{
	/* plain byte-fifos have recsize == 0; this branch is never
	 * reached inside kfifo_skip_count(). */
	(void)fifo;
	(void)recsize;
}

/* ================================================================== */
/* Basic accessors (macros, also usable with &fifo->kfifo pointers)   */
/* ================================================================== */

/**
 * kfifo_size - return the total capacity of the fifo in bytes
 */
#define kfifo_size(fifo)	((fifo)->kfifo.mask + 1u)

/**
 * kfifo_len - return the number of bytes stored in the fifo
 */
#define kfifo_len(fifo)		((fifo)->kfifo.in - (fifo)->kfifo.out)

/**
 * kfifo_avail - return the number of free bytes in the fifo
 */
#define kfifo_avail(fifo)	(kfifo_size(fifo) - kfifo_len(fifo))

/**
 * kfifo_is_empty - return true if the fifo contains no data
 */
#define kfifo_is_empty(fifo)	((fifo)->kfifo.in == (fifo)->kfifo.out)

/**
 * kfifo_is_full - return true if the fifo has no free space
 */
#define kfifo_is_full(fifo)	(kfifo_avail(fifo) == 0u)

/**
 * kfifo_reset - discard all data in the fifo
 *
 * Do not call while a concurrent producer or consumer is accessing
 * the fifo without holding a lock.
 */
#define kfifo_reset(fifo) \
	do { (fifo)->kfifo.in = (fifo)->kfifo.out = 0; } while (0)

/* ================================================================== */
/* Initialisation                                                      */
/* ================================================================== */

/**
 * kfifo_init - initialise a kfifo with a pre-allocated buffer
 * @fifo: pointer to the struct kfifo to initialise
 * @buf:  data buffer (size MUST be a power of two)
 * @size: buffer size in bytes (must be a power of two)
 *
 * Returns 0 on success, -EINVAL if @buf is NULL or @size is not
 * a power of two.
 */
static inline int kfifo_init(struct kfifo *fifo, void *buf,
			     unsigned int size)
{
	if (!buf || !size || (size & (size - 1u)))
		return -EINVAL;
	fifo->kfifo.data  = buf;
	fifo->kfifo.mask  = size - 1u;
	fifo->kfifo.esize = 1u;
	fifo->kfifo.in    = 0u;
	fifo->kfifo.out   = 0u;
	return 0;
}

/* ================================================================== */
/* Writing into the fifo                                               */
/* ================================================================== */

/**
 * kfifo_in - copy bytes into the fifo
 * @fifo: address of the kfifo
 * @buf:  pointer to the data to insert
 * @len:  number of bytes to insert
 *
 * Returns the number of bytes actually copied (may be less than @len
 * if the fifo does not have enough free space).
 *
 * A write memory barrier is issued before updating @in so that the
 * consumer always sees the data before the updated pointer.
 */
static inline unsigned int kfifo_in(struct kfifo *fifo,
				    const void *buf, unsigned int len)
{
	unsigned int avail = kfifo_avail(fifo);
	unsigned int size  = kfifo_size(fifo);
	unsigned int in    = fifo->kfifo.in & fifo->kfifo.mask;
	unsigned int l;

	if (len > avail)
		len = avail;
	if (!len)
		return 0;

	/* Linear copy, then wrap-around tail if needed */
	l = min(len, size - in);
	memcpy((char *)fifo->kfifo.data + in, buf, l);
	memcpy((char *)fifo->kfifo.data, (const char *)buf + l, len - l);

	smp_wmb();	/* data must be visible before the pointer update */
	fifo->kfifo.in += len;
	return len;
}

/* ================================================================== */
/* Reading from the fifo                                               */
/* ================================================================== */

/**
 * kfifo_out - extract bytes from the fifo
 * @fifo: address of the kfifo
 * @buf:  destination buffer
 * @len:  maximum number of bytes to extract
 *
 * Returns the number of bytes actually copied.
 * @out is advanced: the bytes are consumed.
 */
static inline unsigned int kfifo_out(struct kfifo *fifo,
				     void *buf, unsigned int len)
{
	unsigned int used = kfifo_len(fifo);
	unsigned int size = kfifo_size(fifo);
	unsigned int out  = fifo->kfifo.out & fifo->kfifo.mask;
	unsigned int l;

	if (len > used)
		len = used;
	if (!len)
		return 0;

	smp_rmb();	/* read data after observing the updated @in pointer */

	l = min(len, size - out);
	memcpy(buf, (const char *)fifo->kfifo.data + out, l);
	memcpy((char *)buf + l, (const char *)fifo->kfifo.data, len - l);

	fifo->kfifo.out += len;
	return len;
}

/**
 * kfifo_out_peek - read bytes from the fifo WITHOUT consuming them
 * @fifo: address of the kfifo
 * @buf:  destination buffer
 * @len:  maximum number of bytes to read
 *
 * Returns the number of bytes copied. @out is NOT advanced:
 * the data remains available in the fifo.
 */
static inline unsigned int kfifo_out_peek(struct kfifo *fifo,
					  void *buf, unsigned int len)
{
	unsigned int used = kfifo_len(fifo);
	unsigned int size = kfifo_size(fifo);
	unsigned int out  = fifo->kfifo.out & fifo->kfifo.mask;
	unsigned int l;

	if (len > used)
		len = used;
	if (!len)
		return 0;

	smp_rmb();

	l = min(len, size - out);
	memcpy(buf, (const char *)fifo->kfifo.data + out, l);
	memcpy((char *)buf + l, (const char *)fifo->kfifo.data, len - l);

	/* Do NOT update fifo->kfifo.out: this is a peek */
	return len;
}

/* ================================================================== */
/* User-space variants                                                 */
/* ================================================================== */

/**
 * kfifo_from_user - copy data from user space into the fifo
 * @fifo:   address of the kfifo
 * @from:   user-space source pointer
 * @len:    number of bytes to copy
 * @copied: [out] number of bytes actually copied
 *
 * Returns 0 on success, -EFAULT on access fault.
 */
static inline int kfifo_from_user(struct kfifo *fifo,
				  const void __user *from, unsigned int len,
				  unsigned int *copied)
{
	unsigned int avail = kfifo_avail(fifo);
	unsigned int size  = kfifo_size(fifo);
	unsigned int in    = fifo->kfifo.in & fifo->kfifo.mask;
	unsigned int l;

	if (len > avail)
		len = avail;

	if (!len) {
		*copied = 0;
		return 0;
	}

	l = min(len, size - in);

	if (copy_from_user((char *)fifo->kfifo.data + in, from, l))
		goto fault;

	if (len > l &&
	    copy_from_user((char *)fifo->kfifo.data,
			   (const char __user *)from + l, len - l))
		goto fault;

	smp_wmb();
	fifo->kfifo.in += len;
	*copied = len;
	return 0;

fault:
	*copied = 0;
	return -EFAULT;
}

/**
 * kfifo_to_user - copy data from the fifo to user space
 * @fifo:   address of the kfifo
 * @to:     user-space destination pointer
 * @len:    maximum number of bytes to copy
 * @copied: [out] number of bytes actually copied
 *
 * Returns 0 on success, -EFAULT on access fault.
 * @out is advanced: the bytes are consumed.
 */
static inline int kfifo_to_user(struct kfifo *fifo,
				void __user *to, unsigned int len,
				unsigned int *copied)
{
	unsigned int used = kfifo_len(fifo);
	unsigned int size = kfifo_size(fifo);
	unsigned int out  = fifo->kfifo.out & fifo->kfifo.mask;
	unsigned int l;

	if (len > used)
		len = used;

	if (!len) {
		*copied = 0;
		return 0;
	}

	smp_rmb();

	l = min(len, size - out);

	if (copy_to_user(to, (const char *)fifo->kfifo.data + out, l))
		goto fault;

	if (len > l &&
	    copy_to_user((char __user *)to + l,
			 (const char *)fifo->kfifo.data, len - l))
		goto fault;

	fifo->kfifo.out += len;
	*copied = len;
	return 0;

fault:
	*copied = 0;
	return -EFAULT;
}

#endif /* LINUX_VERSION_CODE < KERNEL_VERSION(2, 6, 33) */

#endif /* __PCAN_KFIFO_COMPAT_H__ */

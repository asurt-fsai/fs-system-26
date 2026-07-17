# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - global Makefile for all Linux components of libpcanbasic
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
# Author:      Stephane Grosjean <stephane.grosjean@hms-networks.com>
#
define do-make
@echo
@ echo "***"
@ echo "*** Processing 'libpcanbasic_jni' directory..."
@ echo "***"
@make -C libpcanbasic_jni $1
@echo
@ echo "***"
@ echo "*** Processing 'libpcanbasic_java' directory..."
@ echo "***"
@make -C libpcanbasic_java $1
@echo
@ echo "***"
@ echo "*** Processing 'examples' directory..."
@ echo "***"
@make -C examples $1
endef

define make-all
$(call do-make, all)
endef

define make-clean
$(call do-make, clean)
endef

define make-install
$(call do-make, install)
endef

define make-uninstall
$(call do-make, uninstall)
endef

all:
	$(make-all)

clean:
	$(make-clean)

install:
	$(make-install)

uninstall:
	$(make-uninstall)

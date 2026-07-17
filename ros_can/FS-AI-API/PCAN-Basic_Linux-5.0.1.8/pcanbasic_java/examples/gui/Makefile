# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - Build examples of pcanbasic_java
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
#
define do-make
@echo
@ echo "***"
@ echo "*** Processing examples 'gui' directory..."
@ echo "***"
@make -C CAN $1
@make -C CAN_CC+FD $1
@make -C FD $1
@make -C XL $1
endef

define make-all
$(call do-make, all)
endef

define make-clean
$(call do-make, clean)
endef

all:
	$(make-all)

clean:
	$(make-clean)

install:
uninstall:
xeno:
rtai:

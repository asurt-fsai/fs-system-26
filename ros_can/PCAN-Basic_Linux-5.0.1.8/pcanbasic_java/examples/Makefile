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
@ echo "*** Processing Java examples 'console' directory..."
@ echo "***"
@make -C console $1
@ echo "***"
@ echo "*** Processing Java examples 'gui' directory..."
@ echo "***"
@make -C gui $1
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

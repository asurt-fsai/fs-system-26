# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - Build console examples of libpcanbasic
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
#
define do-make
@echo
@ echo "***"
@ echo "*** Processing 'C' directory (console examples)..."
@ echo "***"
@make -C c $1
@echo
@ echo "***"
@ echo "*** Processing 'NativeC++' directory (console examples)..."
@ echo "***"
@make -C NativeC++ $1
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

define make-xeno
$(call do-make, xeno)
endef

define make-rtai
$(call do-make, rtai)
endef

all:
	$(make-all)

clean:
	$(make-clean)

install:
	$(make-install)

uninstall:
	$(make-uninstall)

xeno:
	$(make-xeno)

rtai:
	$(make-rtai)

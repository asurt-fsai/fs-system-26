# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - Makefile for the PCAN driver test programs.
#
# Copyright (C) 2001-2025 PEAK System-Technik GmbH <www.peak-system.com>
#
# Contact:      <linux.peak@hms-networks.com>
# Maintainer:   Stephane Grosjean <stephane.grosjean@hms-networks.com>
# Contribution: Klaus Hitschler <klaus.hitschler@gmx.de>
#

SRC := src
#
# override default CC = cc
CC = $(CROSS_COMPILE)gcc

BINDIR = $(DESTDIR)/usr/local/bin

ifeq ($(APP),)

# Utils
ALL = pcanxl-loop pcanxl-ping pcanxl-pong pcanxl-dump pcanxl-gen pcanxl-write pcanxl-read

all: banner
	@for a in $(ALL); do \
		if ! $(MAKE) --no-print-directory APP=$$a; then break; fi; \
	 done

banner:
	@echo "***"
	@echo "*** Making PCAN v9 API CAN-CC/CAN-FD/CAN-XL utilities"
	@echo "***"
	@echo "*** $(CC) version: `$(CC) -dumpversion`"
	@echo "***"

can_cc_only:
	$(MAKE) CFLAGS=-DPCANXL_CAN_CC_ONLY all

can_fd_only:
	$(MAKE) CFLAGS=-DPCANXL_CAN_FD_ONLY all

clean:
	-rm -f $(SRC)/*~ $(SRC)/*.o *~ $(ALL)

install:
	-@for f in $(ALL); do \
		if [ -f $$f ]; then cp $$f $(BINDIR); \
		else echo "Warning: $$f not found, it can't be installed!"; \
		fi; \
	 done

uninstall:
	-cd $(BINDIR); rm -f $(ALL)

# Need:
# $ sudo apt-get install gcc-multilib  g++-multilib
all32:
	$(MAKE) BITS=32

xeno rtai:
	@echo "No real time versions of these tools available"

else

PCANDRV_DIR := ../driver
PCANLIB_DIR := ../lib

INC := -I$(SRC) -I$(PCANLIB_DIR) -I$(PCANDRV_DIR)

# C flags
CFLAGS += $(INC)
CFLAGS += -g

#CFLAGS += -DPCANXL_CAN_CC_ONLY
#CFLAGS += -DPCANXL_CAN_FD_ONLY

# LDLIBS before -lpcanfd means that local libpcanxl will be linked
# LDLIBS after -lpcanfd means that global libpcanxl will be linked. If not found
# then local libpcanxl will be linked.
LDFLAGS += -lpcanxl

# --- note --------------------------------------------------------------------
# Because these examples have to be built BEFORE libpcan[xl] (as well as
# the pcan driver) is installed, local paths HAVE TO be added to the command
# lines of gcc (see usage of -Wl,rpath in  LDFLAGS below).
# Once libpcan[xl] as well as the pcan driver are installed, these command
# line options are useless and SHOULD NOT be added to any application.
LDFLAGS += -L$(PCANLIB_DIR)/lib$(BITS) -Wl,-rpath $(PCANLIB_DIR)/lib$(BITS)
# --- end of note -------------------------------------------------------------

ifeq ($(BITS),32)
CFLAGS += -m32
LDFLAGS += -m32
endif

$(APP): $(SRC)/$(APP).o $(SRC)/pcanxl-cmdline.o $(SRC)/pcanxl-utils.o $(SRC)/pcanxl-common.o
	$(CC) $^ $(LDFLAGS) -o $@

$(SRC)/%.o: $(SRC)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

endif # $(APP)

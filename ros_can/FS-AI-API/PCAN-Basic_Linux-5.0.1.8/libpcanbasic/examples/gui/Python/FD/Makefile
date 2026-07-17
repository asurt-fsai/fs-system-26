# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - Python example Makefile (mainly useful to avoid unknown target
#            errors as well as being able to clean tmp files)
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
# Author:      Stephane Grosjean <stephane.grosjean@hms-networks.com>
#


PYTHON_ALIAS = python
PYTHON_V2 = python2
PYTHON_V3 = python3
PYTHON_ALIAS_STS = $(shell $(PYTHON_ALIAS) --version 2>&1 > /dev/null; echo $$?)
PYTHON_V2_STS = $(shell $(PYTHON_V2) --version 2>&1 > /dev/null; echo $$?)
PYTHON_V3_STS = $(shell $(PYTHON_V3) --version 2>&1 > /dev/null; echo $$?)

ifeq ($(PYTHON_ALIAS_STS),0)
  PYTHON_CMD = $(PYTHON_ALIAS)
  PYTHON_VERSION_FULL = $(wordlist 2,4,$(subst ., ,$(shell $(PYTHON_ALIAS) --version 2>&1)))
else 
  ifeq ($(PYTHON_V2_STS),0)
    PYTHON_CMD = $(PYTHON_V2)
    PYTHON_VERSION_FULL = $(wordlist 2,4,$(subst ., ,$(shell $(PYTHON_V2) --version 2>&1)))
  else
    ifeq ($(PYTHON_V3_STS),0)
      PYTHON_CMD = $(PYTHON_V3)
      PYTHON_VERSION_FULL = $(wordlist 2,4,$(subst ., ,$(shell $(PYTHON_V3) --version 2>&1)))
    else
      PYTHON_VERSION_FULL =
    endif
  endif
endif

ifneq ($(PYTHON_VERSION_FULL),)
PYTHON_VERSION_MAJOR = $(word 1,$(PYTHON_VERSION_FULL))
PYTHON_VERSION_MINOR = $(word 2,$(PYTHON_VERSION_FULL))
PYTHON_VERSION_PATCH = $(word 3,$(PYTHON_VERSION_FULL))
PYTHON_RUN_SCRIPT_V2 = $(PYTHON_CMD) PCANBasicExample.pyw
PYTHON_RUN_SCRIPT_V3 = $(PYTHON_CMD) PCANBasicExample_py3.pyw

PYTHON_RUN_SCRIPT = $(PYTHON_RUN_SCRIPT_V$(PYTHON_VERSION_MAJOR))
PYTHON_MSG = Running script with Python v$(PYTHON_VERSION_MAJOR).$(PYTHON_VERSION_MINOR): $(PYTHON_RUN_SCRIPT)...

ifeq ($(PYTHON_VERSION_MAJOR),3)
ifeq ($(shell test $(PYTHON_VERSION_MINOR) -ge 13; echo $$?),0)
PYTHON_MSG += "\n"
PYTHON_MSG += "-------"
PYTHON_MSG += "\n"
PYTHON_MSG += "WARNING: Python 3.13+ does NOT support module tkinter.tix, script will fail with ImportError."
PYTHON_MSG += "\n"
PYTHON_MSG += " >> Install Python 3.12 and run this sample with:"
PYTHON_MSG += "\n"
PYTHON_MSG += " $$ python3.12 PCANBasicExample_py3.pyw"
PYTHON_MSG += "\n"
PYTHON_MSG += "-------"
endif
endif

else
PYTHON_MSG = Error: python not found...
PYTHON_RUN_SCRIPT =
endif

all:
	@echo Use "make run" to execute sample.

install:
uninstall:
xeno:
rtai:

clean:
	-rm -f *.pyc __pycache__

.PHONY: run
run:
	@echo -e $(PYTHON_MSG)
	$(PYTHON_RUN_SCRIPT)

# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - PCANBasic_java library
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
#
JAVA = java
JAVAC = javac
JAR = jar

TITLE := PCANBasic_java CC+FD example

ALL = $(TARGET)

PROJECT_ROOT = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

CLASS_DIR = $(PROJECT_ROOT)/classes
SRC_DIR = $(PROJECT_ROOT)/src
FILES = $(shell find $(SRC_DIR) | grep .java$)

JAR_PATH ?= ../../../libpcanbasic_java/PCAN-Basic_java_lib
LIB_PCANBASIC_JAR = $(JAR_PATH)/PCAN-Basic_java.jar

TARGET = $(CLASS_DIR)/peak/can/Application.class


all: message $(ALL)

message:
	@echo
	@echo "***"
	@echo "*** Making $(TITLE)"
	@echo "***"
	@echo "*** target=$(ALL)"
	@echo "*** $(JAVAC) version=$(shell $(JAVAC) -version)"
	@echo "*** source: $(SRC_DIR)"
	@echo "***"

clean:
	-find $(CLASS_DIR) -name "*.class" -delete
	-find $(CLASS_DIR) -type d -delete

$(LIB_PCANBASIC_JAR):
	@echo "Failed to find $(LIB_PCANBASIC_JAR)..."
	@echo "Please build PCAN-Basic_java library first."
	@echo "You can also override the default path by defining JAR_PATH."
	@exit 1

$(TARGET): $(LIB_PCANBASIC_JAR)
	@echo Compiling java files...
	$(JAVAC) -cp "$(LIB_PCANBASIC_JAR):" -d "$(CLASS_DIR)" $(FILES)

run: $(TARGET)
	$(JAVA) -cp "$(LIB_PCANBASIC_JAR):$(CLASS_DIR)" peak.can.Application
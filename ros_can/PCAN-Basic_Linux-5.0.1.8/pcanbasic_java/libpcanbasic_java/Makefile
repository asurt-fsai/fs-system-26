# SPDX-License-Identifier: LGPL-2.1-only
#
# Makefile - PCANBasic_java library
#
# Copyright (C) 2001-2025  PEAK System-Technik GmbH <www.peak-system.com>
#
# Contact:     <linux.peak@hms-networks.com>
# Maintainer:  Fabrice Vergnaud <fabrice.vergnaud@hms-networks.com>
#
JAVAC = javac
JAR = jar

TITLE := PCANBasic_java library

TARGET = PCAN-Basic_java.jar
ALL = $(TARGET)

PROJECT_ROOT = $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

CLASS_DIR = $(PROJECT_ROOT)/classes
SRC_PCANBASIC_DIR = $(PROJECT_ROOT)/PCAN-Basic_java_src
OUT_DIR = $(PROJECT_ROOT)/PCAN-Basic_java_lib
#JAVA_FILES = $(shell find $(SRC_PCANBASIC_DIR) -name "*.java")
FILES = $(shell find $(SRC_PCANBASIC_DIR) | grep .java$)

all: message $(ALL)

message:
	@echo
	@echo "***"
	@echo "*** Making $(TITLE)"
	@echo "***"
	@echo "*** target=$(ALL)"
	@echo "*** $(JAVAC) version=$(shell $(JAVAC) -version)"
	@echo "*** source: $(SRC_PCANBASIC_DIR)"
	@echo "*** out: $(OUT_DIR)"
	@echo "***"

clean:
	-find $(CLASS_DIR) -name "*.class" -delete
	-find $(CLASS_DIR) -type d -delete
	-find $(OUT_DIR)/$(TARGET) -delete

$(TARGET):
	@echo Compiling java files...
	$(JAVAC) -d "$(CLASS_DIR)" $(FILES)
	@echo Creating jar file...
	cd $(CLASS_DIR) && $(JAR) cf "$(OUT_DIR)/$(TARGET)" .

install:
uninstall:

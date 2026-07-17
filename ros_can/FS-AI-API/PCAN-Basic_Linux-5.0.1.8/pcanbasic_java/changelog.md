# Changelog
All notable changes to "pcanbasic java" will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [5.0.0] - 2025-09-18
### Updated
- Synchronized version with PCAN-Basic 5.0.0
### Added
- Added support to CAN XL features
### Removed
- All types related to non Plug-n-Play devices are now deprecated.

## [4.10.0] - 2024-12-09
### Updated
- Synchronized version with PCAN-Basic 4.10.0

## [4.9.0] - 2024-10-01
### Updated
- Synchronized version with PCAN-Basic 4.9.0
### Added
- Added enum TPCANParameter.PCAN_LAN_CHANNEL_DIRECTION.
- Added values TPCANParameterValue.LAN_DIRECTION_xxx.
### Updated
- PCANBasicExample: added support for parameter PCAN_LAN_CHANNEL_DIRECTION.

## [4.8.0] - 2023-10-25
### Added
- Added enum TPCANParameter.PCAN_HARD_RESET_STATUS.
### Updated
- Changed value of MAX_LENGTH_VERSION_STRING to 256
- Fixed issue with TPCANFDMsg.getTypeEnum(): PCAN_MESSAGE_STANDARD was removed if following flags were set: PCAN_MESSAGE_RTR, PCAN_MESSAGE_BRS and PCAN_MESSAGE_ESI (for ex. STD/RTR exists...)
- PCANBasicExample: fixed UI issues when receiving CAN FD message

## [4.7.0] - 2022-01-24
### Added
- Added enum TPCANParameterValue.TRACE_FILE_DATA_LENGTH.
### Updated
- Updated javadoc

## [4.6.1] - 2022-05-10
### Added
- Added classes peak.can.MutableInteger and peak.can.MutableLong (required by PCANBasic_JNI library)
### Updated
- Updated javadoc

## [4.6.0] - 2022-01-05
### Updated
- Upgraded library to support new features from PCAN-Basic v4.6 (TPCANParameter.PCAN_ALLOW_ECHO_FRAMES, TPCANParameter.PCAN_DEVICE_PART_NUMBER)

## [4.5.0] - 2021-08-26
### Updated
- Upgraded library to support new features from PCAN-Basic v4.5 (LookUpChannel)

## [4.4.1] - 2021-07-23
### Updated
- Fixed issue with TPCANTimestamp on ARM architecture: cast in setMillis changed from jint to jlong
- Reminder: java TPCANTimestamp.millis is of type "long" to prevent overflow (instead of uint32_t as unsigned type doesn't exist)

## [4.4.0] - 2020-08-07
### Changed
- Updated libpcanbasic_jni to support features from PCAN-Basic 4.4
- Updated examples to support features from PCAN-Basic 4.4
- Added licence information to all java files

## [4.3.2] - 2019-10-08
### Changed
- PCANBasic.java: loadLibrary will try "pcanbasic_jni" first and fallback to "PCANBasic_JNI" on failure.
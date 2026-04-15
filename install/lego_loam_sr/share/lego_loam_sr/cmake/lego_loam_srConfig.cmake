# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_lego_loam_sr_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED lego_loam_sr_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(lego_loam_sr_FOUND FALSE)
  elseif(NOT lego_loam_sr_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(lego_loam_sr_FOUND FALSE)
  endif()
  return()
endif()
set(_lego_loam_sr_CONFIG_INCLUDED TRUE)

# output package information
if(NOT lego_loam_sr_FIND_QUIETLY)
  message(STATUS "Found lego_loam_sr: 1.0.0 (${lego_loam_sr_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'lego_loam_sr' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT lego_loam_sr_DEPRECATED_QUIET)
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(lego_loam_sr_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake")
foreach(_extra ${_extras})
  include("${lego_loam_sr_DIR}/${_extra}")
endforeach()

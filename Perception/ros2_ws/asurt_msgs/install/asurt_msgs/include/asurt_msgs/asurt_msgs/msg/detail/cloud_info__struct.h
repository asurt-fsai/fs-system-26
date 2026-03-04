// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from asurt_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__STRUCT_H_
#define ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'start_ring_index'
// Member 'end_ring_index'
// Member 'segmented_cloud_ground_flag'
// Member 'segmented_cloud_col_ind'
// Member 'segmented_cloud_range'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/CloudInfo in the package asurt_msgs.
typedef struct asurt_msgs__msg__CloudInfo
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__int32__Sequence start_ring_index;
  rosidl_runtime_c__int32__Sequence end_ring_index;
  float start_orientation;
  float end_orientation;
  float orientation_diff;
  /// true - ground point, false - other points
  rosidl_runtime_c__boolean__Sequence segmented_cloud_ground_flag;
  /// point column index in range image
  rosidl_runtime_c__uint32__Sequence segmented_cloud_col_ind;
  /// point range
  rosidl_runtime_c__float__Sequence segmented_cloud_range;
} asurt_msgs__msg__CloudInfo;

// Struct for a sequence of asurt_msgs__msg__CloudInfo.
typedef struct asurt_msgs__msg__CloudInfo__Sequence
{
  asurt_msgs__msg__CloudInfo * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} asurt_msgs__msg__CloudInfo__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__STRUCT_H_

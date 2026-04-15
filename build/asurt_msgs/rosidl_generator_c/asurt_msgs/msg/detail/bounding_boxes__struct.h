// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from asurt_msgs:msg/BoundingBoxes.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "asurt_msgs/msg/bounding_boxes.h"


#ifndef ASURT_MSGS__MSG__DETAIL__BOUNDING_BOXES__STRUCT_H_
#define ASURT_MSGS__MSG__DETAIL__BOUNDING_BOXES__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'view_id'
#include "rosidl_runtime_c/string.h"
// Member 'bounding_boxes'
#include "asurt_msgs/msg/detail/bounding_box__struct.h"

/// Struct defined in msg/BoundingBoxes in the package asurt_msgs.
typedef struct asurt_msgs__msg__BoundingBoxes
{
  rosidl_runtime_c__String view_id;
  uint16_t object_count;
  asurt_msgs__msg__BoundingBox__Sequence bounding_boxes;
} asurt_msgs__msg__BoundingBoxes;

// Struct for a sequence of asurt_msgs__msg__BoundingBoxes.
typedef struct asurt_msgs__msg__BoundingBoxes__Sequence
{
  asurt_msgs__msg__BoundingBoxes * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} asurt_msgs__msg__BoundingBoxes__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ASURT_MSGS__MSG__DETAIL__BOUNDING_BOXES__STRUCT_H_

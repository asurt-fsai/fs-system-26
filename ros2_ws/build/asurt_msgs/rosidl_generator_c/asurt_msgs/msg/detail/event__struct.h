// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from asurt_msgs:msg/Event.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__EVENT__STRUCT_H_
#define ASURT_MSGS__MSG__DETAIL__EVENT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"
// Member 'severity'
// Member 'category'
// Member 'event_type'
// Member 'source'
// Member 'details_json'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Event in the package asurt_msgs.
typedef struct asurt_msgs__msg__Event
{
  builtin_interfaces__msg__Time stamp;
  rosidl_runtime_c__String severity;
  rosidl_runtime_c__String category;
  rosidl_runtime_c__String event_type;
  rosidl_runtime_c__String source;
  rosidl_runtime_c__String details_json;
} asurt_msgs__msg__Event;

// Struct for a sequence of asurt_msgs__msg__Event.
typedef struct asurt_msgs__msg__Event__Sequence
{
  asurt_msgs__msg__Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} asurt_msgs__msg__Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ASURT_MSGS__MSG__DETAIL__EVENT__STRUCT_H_

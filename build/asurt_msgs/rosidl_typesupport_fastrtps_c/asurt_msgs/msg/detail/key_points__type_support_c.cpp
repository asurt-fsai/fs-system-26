// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from asurt_msgs:msg/KeyPoints.idl
// generated code does not contain a copyright notice
#include "asurt_msgs/msg/detail/key_points__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "asurt_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "asurt_msgs/msg/detail/key_points__struct.h"
#include "asurt_msgs/msg/detail/key_points__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif

#include "rosidl_runtime_c/primitives_sequence.h"  // classes, keypoints, track_ids
#include "rosidl_runtime_c/primitives_sequence_functions.h"  // classes, keypoints, track_ids

// forward declare type support functions


using _KeyPoints__ros_msg_type = asurt_msgs__msg__KeyPoints;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_asurt_msgs__msg__KeyPoints(
  const asurt_msgs__msg__KeyPoints * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: view_id
  {
    cdr << ros_message->view_id;
  }

  // Field name: object_count
  {
    cdr << ros_message->object_count;
  }

  // Field name: track_ids
  {
    size_t size = ros_message->track_ids.size;
    auto array_ptr = ros_message->track_ids.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: classes
  {
    size_t size = ros_message->classes.size;
    auto array_ptr = ros_message->classes.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: keypoints
  {
    size_t size = ros_message->keypoints.size;
    auto array_ptr = ros_message->keypoints.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_deserialize_asurt_msgs__msg__KeyPoints(
  eprosima::fastcdr::Cdr & cdr,
  asurt_msgs__msg__KeyPoints * ros_message)
{
  // Field name: view_id
  {
    cdr >> ros_message->view_id;
  }

  // Field name: object_count
  {
    cdr >> ros_message->object_count;
  }

  // Field name: track_ids
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.get_state();
    bool correct_size = cdr.jump(size);
    cdr.set_state(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->track_ids.data) {
      rosidl_runtime_c__uint8__Sequence__fini(&ros_message->track_ids);
    }
    if (!rosidl_runtime_c__uint8__Sequence__init(&ros_message->track_ids, size)) {
      fprintf(stderr, "failed to create array for field 'track_ids'");
      return false;
    }
    auto array_ptr = ros_message->track_ids.data;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: classes
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.get_state();
    bool correct_size = cdr.jump(size);
    cdr.set_state(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->classes.data) {
      rosidl_runtime_c__uint8__Sequence__fini(&ros_message->classes);
    }
    if (!rosidl_runtime_c__uint8__Sequence__init(&ros_message->classes, size)) {
      fprintf(stderr, "failed to create array for field 'classes'");
      return false;
    }
    auto array_ptr = ros_message->classes.data;
    cdr.deserialize_array(array_ptr, size);
  }

  // Field name: keypoints
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.get_state();
    bool correct_size = cdr.jump(size);
    cdr.set_state(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->keypoints.data) {
      rosidl_runtime_c__uint16__Sequence__fini(&ros_message->keypoints);
    }
    if (!rosidl_runtime_c__uint16__Sequence__init(&ros_message->keypoints, size)) {
      fprintf(stderr, "failed to create array for field 'keypoints'");
      return false;
    }
    auto array_ptr = ros_message->keypoints.data;
    cdr.deserialize_array(array_ptr, size);
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_asurt_msgs__msg__KeyPoints(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _KeyPoints__ros_msg_type * ros_message = static_cast<const _KeyPoints__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: view_id
  {
    size_t item_size = sizeof(ros_message->view_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: object_count
  {
    size_t item_size = sizeof(ros_message->object_count);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: track_ids
  {
    size_t array_size = ros_message->track_ids.size;
    auto array_ptr = ros_message->track_ids.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: classes
  {
    size_t array_size = ros_message->classes.size;
    auto array_ptr = ros_message->classes.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: keypoints
  {
    size_t array_size = ros_message->keypoints.size;
    auto array_ptr = ros_message->keypoints.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_asurt_msgs__msg__KeyPoints(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Field name: view_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: object_count
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: track_ids
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: classes
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: keypoints
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = asurt_msgs__msg__KeyPoints;
    is_plain =
      (
      offsetof(DataType, keypoints) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_key_asurt_msgs__msg__KeyPoints(
  const asurt_msgs__msg__KeyPoints * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: view_id
  {
    cdr << ros_message->view_id;
  }

  // Field name: object_count
  {
    cdr << ros_message->object_count;
  }

  // Field name: track_ids
  {
    size_t size = ros_message->track_ids.size;
    auto array_ptr = ros_message->track_ids.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: classes
  {
    size_t size = ros_message->classes.size;
    auto array_ptr = ros_message->classes.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  // Field name: keypoints
  {
    size_t size = ros_message->keypoints.size;
    auto array_ptr = ros_message->keypoints.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serialize_array(array_ptr, size);
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_key_asurt_msgs__msg__KeyPoints(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _KeyPoints__ros_msg_type * ros_message = static_cast<const _KeyPoints__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: view_id
  {
    size_t item_size = sizeof(ros_message->view_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: object_count
  {
    size_t item_size = sizeof(ros_message->object_count);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: track_ids
  {
    size_t array_size = ros_message->track_ids.size;
    auto array_ptr = ros_message->track_ids.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: classes
  {
    size_t array_size = ros_message->classes.size;
    auto array_ptr = ros_message->classes.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: keypoints
  {
    size_t array_size = ros_message->keypoints.size;
    auto array_ptr = ros_message->keypoints.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_key_asurt_msgs__msg__KeyPoints(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;
  // Field name: view_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: object_count
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: track_ids
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: classes
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: keypoints
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = asurt_msgs__msg__KeyPoints;
    is_plain =
      (
      offsetof(DataType, keypoints) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _KeyPoints__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const asurt_msgs__msg__KeyPoints * ros_message = static_cast<const asurt_msgs__msg__KeyPoints *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_asurt_msgs__msg__KeyPoints(ros_message, cdr);
}

static bool _KeyPoints__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  asurt_msgs__msg__KeyPoints * ros_message = static_cast<asurt_msgs__msg__KeyPoints *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_asurt_msgs__msg__KeyPoints(cdr, ros_message);
}

static uint32_t _KeyPoints__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_asurt_msgs__msg__KeyPoints(
      untyped_ros_message, 0));
}

static size_t _KeyPoints__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_asurt_msgs__msg__KeyPoints(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_KeyPoints = {
  "asurt_msgs::msg",
  "KeyPoints",
  _KeyPoints__cdr_serialize,
  _KeyPoints__cdr_deserialize,
  _KeyPoints__get_serialized_size,
  _KeyPoints__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _KeyPoints__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_KeyPoints,
  get_message_typesupport_handle_function,
  &asurt_msgs__msg__KeyPoints__get_type_hash,
  &asurt_msgs__msg__KeyPoints__get_type_description,
  &asurt_msgs__msg__KeyPoints__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, asurt_msgs, msg, KeyPoints)() {
  return &_KeyPoints__type_support;
}

#if defined(__cplusplus)
}
#endif

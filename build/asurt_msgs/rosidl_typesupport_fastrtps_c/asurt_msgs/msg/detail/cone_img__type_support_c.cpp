// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from asurt_msgs:msg/ConeImg.idl
// generated code does not contain a copyright notice
#include "asurt_msgs/msg/detail/cone_img__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "asurt_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "asurt_msgs/msg/detail/cone_img__struct.h"
#include "asurt_msgs/msg/detail/cone_img__functions.h"
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

#include "sensor_msgs/msg/detail/image__functions.h"  // img

// forward declare type support functions

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
bool cdr_serialize_sensor_msgs__msg__Image(
  const sensor_msgs__msg__Image * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
bool cdr_deserialize_sensor_msgs__msg__Image(
  eprosima::fastcdr::Cdr & cdr,
  sensor_msgs__msg__Image * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
size_t get_serialized_size_sensor_msgs__msg__Image(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
size_t max_serialized_size_sensor_msgs__msg__Image(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
bool cdr_serialize_key_sensor_msgs__msg__Image(
  const sensor_msgs__msg__Image * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
size_t get_serialized_size_key_sensor_msgs__msg__Image(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
size_t max_serialized_size_key_sensor_msgs__msg__Image(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_asurt_msgs
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, sensor_msgs, msg, Image)();


using _ConeImg__ros_msg_type = asurt_msgs__msg__ConeImg;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_asurt_msgs__msg__ConeImg(
  const asurt_msgs__msg__ConeImg * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: detection_id
  {
    cdr << ros_message->detection_id;
  }

  // Field name: rows
  {
    cdr << ros_message->rows;
  }

  // Field name: cols
  {
    cdr << ros_message->cols;
  }

  // Field name: img
  {
    cdr_serialize_sensor_msgs__msg__Image(
      &ros_message->img, cdr);
  }

  // Field name: track_id
  {
    cdr << ros_message->track_id;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_deserialize_asurt_msgs__msg__ConeImg(
  eprosima::fastcdr::Cdr & cdr,
  asurt_msgs__msg__ConeImg * ros_message)
{
  // Field name: detection_id
  {
    cdr >> ros_message->detection_id;
  }

  // Field name: rows
  {
    cdr >> ros_message->rows;
  }

  // Field name: cols
  {
    cdr >> ros_message->cols;
  }

  // Field name: img
  {
    cdr_deserialize_sensor_msgs__msg__Image(cdr, &ros_message->img);
  }

  // Field name: track_id
  {
    cdr >> ros_message->track_id;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_asurt_msgs__msg__ConeImg(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _ConeImg__ros_msg_type * ros_message = static_cast<const _ConeImg__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: detection_id
  {
    size_t item_size = sizeof(ros_message->detection_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: rows
  {
    size_t item_size = sizeof(ros_message->rows);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: cols
  {
    size_t item_size = sizeof(ros_message->cols);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: img
  current_alignment += get_serialized_size_sensor_msgs__msg__Image(
    &(ros_message->img), current_alignment);

  // Field name: track_id
  {
    size_t item_size = sizeof(ros_message->track_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_asurt_msgs__msg__ConeImg(
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

  // Field name: detection_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: rows
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: cols
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: img
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_sensor_msgs__msg__Image(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: track_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = asurt_msgs__msg__ConeImg;
    is_plain =
      (
      offsetof(DataType, track_id) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_key_asurt_msgs__msg__ConeImg(
  const asurt_msgs__msg__ConeImg * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: detection_id
  {
    cdr << ros_message->detection_id;
  }

  // Field name: rows
  {
    cdr << ros_message->rows;
  }

  // Field name: cols
  {
    cdr << ros_message->cols;
  }

  // Field name: img
  {
    cdr_serialize_key_sensor_msgs__msg__Image(
      &ros_message->img, cdr);
  }

  // Field name: track_id
  {
    cdr << ros_message->track_id;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_key_asurt_msgs__msg__ConeImg(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _ConeImg__ros_msg_type * ros_message = static_cast<const _ConeImg__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: detection_id
  {
    size_t item_size = sizeof(ros_message->detection_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: rows
  {
    size_t item_size = sizeof(ros_message->rows);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: cols
  {
    size_t item_size = sizeof(ros_message->cols);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: img
  current_alignment += get_serialized_size_key_sensor_msgs__msg__Image(
    &(ros_message->img), current_alignment);

  // Field name: track_id
  {
    size_t item_size = sizeof(ros_message->track_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_key_asurt_msgs__msg__ConeImg(
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
  // Field name: detection_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: rows
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: cols
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Field name: img
  {
    size_t array_size = 1;
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_sensor_msgs__msg__Image(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Field name: track_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = asurt_msgs__msg__ConeImg;
    is_plain =
      (
      offsetof(DataType, track_id) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _ConeImg__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const asurt_msgs__msg__ConeImg * ros_message = static_cast<const asurt_msgs__msg__ConeImg *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_asurt_msgs__msg__ConeImg(ros_message, cdr);
}

static bool _ConeImg__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  asurt_msgs__msg__ConeImg * ros_message = static_cast<asurt_msgs__msg__ConeImg *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_asurt_msgs__msg__ConeImg(cdr, ros_message);
}

static uint32_t _ConeImg__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_asurt_msgs__msg__ConeImg(
      untyped_ros_message, 0));
}

static size_t _ConeImg__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_asurt_msgs__msg__ConeImg(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_ConeImg = {
  "asurt_msgs::msg",
  "ConeImg",
  _ConeImg__cdr_serialize,
  _ConeImg__cdr_deserialize,
  _ConeImg__get_serialized_size,
  _ConeImg__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _ConeImg__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_ConeImg,
  get_message_typesupport_handle_function,
  &asurt_msgs__msg__ConeImg__get_type_hash,
  &asurt_msgs__msg__ConeImg__get_type_description,
  &asurt_msgs__msg__ConeImg__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, asurt_msgs, msg, ConeImg)() {
  return &_ConeImg__type_support;
}

#if defined(__cplusplus)
}
#endif

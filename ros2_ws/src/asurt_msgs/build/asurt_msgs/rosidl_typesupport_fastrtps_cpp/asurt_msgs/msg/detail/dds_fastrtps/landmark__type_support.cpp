// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from asurt_msgs:msg/Landmark.idl
// generated code does not contain a copyright notice
#include "asurt_msgs/msg/detail/landmark__rosidl_typesupport_fastrtps_cpp.hpp"
#include "asurt_msgs/msg/detail/landmark__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions
namespace geometry_msgs
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const geometry_msgs::msg::Point &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  geometry_msgs::msg::Point &);
size_t get_serialized_size(
  const geometry_msgs::msg::Point &,
  size_t current_alignment);
size_t
max_serialized_size_Point(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace geometry_msgs


namespace asurt_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_asurt_msgs
cdr_serialize(
  const asurt_msgs::msg::Landmark & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: position
  geometry_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
    ros_message.position,
    cdr);
  // Member: type
  cdr << ros_message.type;
  // Member: identifier
  cdr << ros_message.identifier;
  // Member: probability
  cdr << ros_message.probability;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_asurt_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  asurt_msgs::msg::Landmark & ros_message)
{
  // Member: position
  geometry_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
    cdr, ros_message.position);

  // Member: type
  cdr >> ros_message.type;

  // Member: identifier
  cdr >> ros_message.identifier;

  // Member: probability
  cdr >> ros_message.probability;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_asurt_msgs
get_serialized_size(
  const asurt_msgs::msg::Landmark & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: position

  current_alignment +=
    geometry_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
    ros_message.position, current_alignment);
  // Member: type
  {
    size_t item_size = sizeof(ros_message.type);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: identifier
  {
    size_t item_size = sizeof(ros_message.identifier);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: probability
  {
    size_t item_size = sizeof(ros_message.probability);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_asurt_msgs
max_serialized_size_Landmark(
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


  // Member: position
  {
    size_t array_size = 1;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size =
        geometry_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_Point(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Member: type
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: identifier
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: probability
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = asurt_msgs::msg::Landmark;
    is_plain =
      (
      offsetof(DataType, probability) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _Landmark__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const asurt_msgs::msg::Landmark *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _Landmark__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<asurt_msgs::msg::Landmark *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _Landmark__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const asurt_msgs::msg::Landmark *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _Landmark__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_Landmark(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _Landmark__callbacks = {
  "asurt_msgs::msg",
  "Landmark",
  _Landmark__cdr_serialize,
  _Landmark__cdr_deserialize,
  _Landmark__get_serialized_size,
  _Landmark__max_serialized_size
};

static rosidl_message_type_support_t _Landmark__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_Landmark__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace asurt_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_asurt_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<asurt_msgs::msg::Landmark>()
{
  return &asurt_msgs::msg::typesupport_fastrtps_cpp::_Landmark__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, asurt_msgs, msg, Landmark)() {
  return &asurt_msgs::msg::typesupport_fastrtps_cpp::_Landmark__handle;
}

#ifdef __cplusplus
}
#endif

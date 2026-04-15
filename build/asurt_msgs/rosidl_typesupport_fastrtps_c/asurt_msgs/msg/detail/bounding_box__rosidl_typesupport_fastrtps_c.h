// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from asurt_msgs:msg/BoundingBox.idl
// generated code does not contain a copyright notice
#ifndef ASURT_MSGS__MSG__DETAIL__BOUNDING_BOX__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define ASURT_MSGS__MSG__DETAIL__BOUNDING_BOX__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "asurt_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "asurt_msgs/msg/detail/bounding_box__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_asurt_msgs__msg__BoundingBox(
  const asurt_msgs__msg__BoundingBox * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_deserialize_asurt_msgs__msg__BoundingBox(
  eprosima::fastcdr::Cdr &,
  asurt_msgs__msg__BoundingBox * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_asurt_msgs__msg__BoundingBox(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_asurt_msgs__msg__BoundingBox(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
bool cdr_serialize_key_asurt_msgs__msg__BoundingBox(
  const asurt_msgs__msg__BoundingBox * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t get_serialized_size_key_asurt_msgs__msg__BoundingBox(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
size_t max_serialized_size_key_asurt_msgs__msg__BoundingBox(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_asurt_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, asurt_msgs, msg, BoundingBox)();

#ifdef __cplusplus
}
#endif

#endif  // ASURT_MSGS__MSG__DETAIL__BOUNDING_BOX__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_

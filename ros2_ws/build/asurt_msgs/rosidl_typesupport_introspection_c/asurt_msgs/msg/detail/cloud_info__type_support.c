// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from asurt_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "asurt_msgs/msg/detail/cloud_info__rosidl_typesupport_introspection_c.h"
#include "asurt_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "asurt_msgs/msg/detail/cloud_info__functions.h"
#include "asurt_msgs/msg/detail/cloud_info__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `start_ring_index`
// Member `end_ring_index`
// Member `segmented_cloud_ground_flag`
// Member `segmented_cloud_col_ind`
// Member `segmented_cloud_range`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  asurt_msgs__msg__CloudInfo__init(message_memory);
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_fini_function(void * message_memory)
{
  asurt_msgs__msg__CloudInfo__fini(message_memory);
}

size_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__start_ring_index(
  const void * untyped_member)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return member->size;
}

const void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__start_ring_index(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__start_ring_index(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__start_ring_index(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const int32_t * item =
    ((const int32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__start_ring_index(untyped_member, index));
  int32_t * value =
    (int32_t *)(untyped_value);
  *value = *item;
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__start_ring_index(
  void * untyped_member, size_t index, const void * untyped_value)
{
  int32_t * item =
    ((int32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__start_ring_index(untyped_member, index));
  const int32_t * value =
    (const int32_t *)(untyped_value);
  *item = *value;
}

bool asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__start_ring_index(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  rosidl_runtime_c__int32__Sequence__fini(member);
  return rosidl_runtime_c__int32__Sequence__init(member, size);
}

size_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__end_ring_index(
  const void * untyped_member)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return member->size;
}

const void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__end_ring_index(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__int32__Sequence * member =
    (const rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__end_ring_index(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  return &member->data[index];
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__end_ring_index(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const int32_t * item =
    ((const int32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__end_ring_index(untyped_member, index));
  int32_t * value =
    (int32_t *)(untyped_value);
  *value = *item;
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__end_ring_index(
  void * untyped_member, size_t index, const void * untyped_value)
{
  int32_t * item =
    ((int32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__end_ring_index(untyped_member, index));
  const int32_t * value =
    (const int32_t *)(untyped_value);
  *item = *value;
}

bool asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__end_ring_index(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__int32__Sequence * member =
    (rosidl_runtime_c__int32__Sequence *)(untyped_member);
  rosidl_runtime_c__int32__Sequence__fini(member);
  return rosidl_runtime_c__int32__Sequence__init(member, size);
}

size_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_ground_flag(
  const void * untyped_member)
{
  const rosidl_runtime_c__boolean__Sequence * member =
    (const rosidl_runtime_c__boolean__Sequence *)(untyped_member);
  return member->size;
}

const void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_ground_flag(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__boolean__Sequence * member =
    (const rosidl_runtime_c__boolean__Sequence *)(untyped_member);
  return &member->data[index];
}

void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_ground_flag(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__boolean__Sequence * member =
    (rosidl_runtime_c__boolean__Sequence *)(untyped_member);
  return &member->data[index];
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_ground_flag(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const bool * item =
    ((const bool *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_ground_flag(untyped_member, index));
  bool * value =
    (bool *)(untyped_value);
  *value = *item;
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_ground_flag(
  void * untyped_member, size_t index, const void * untyped_value)
{
  bool * item =
    ((bool *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_ground_flag(untyped_member, index));
  const bool * value =
    (const bool *)(untyped_value);
  *item = *value;
}

bool asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_ground_flag(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__boolean__Sequence * member =
    (rosidl_runtime_c__boolean__Sequence *)(untyped_member);
  rosidl_runtime_c__boolean__Sequence__fini(member);
  return rosidl_runtime_c__boolean__Sequence__init(member, size);
}

size_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_col_ind(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint32__Sequence * member =
    (const rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return member->size;
}

const void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_col_ind(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint32__Sequence * member =
    (const rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_col_ind(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint32__Sequence * member =
    (rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return &member->data[index];
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_col_ind(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint32_t * item =
    ((const uint32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_col_ind(untyped_member, index));
  uint32_t * value =
    (uint32_t *)(untyped_value);
  *value = *item;
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_col_ind(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint32_t * item =
    ((uint32_t *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_col_ind(untyped_member, index));
  const uint32_t * value =
    (const uint32_t *)(untyped_value);
  *item = *value;
}

bool asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_col_ind(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint32__Sequence * member =
    (rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  rosidl_runtime_c__uint32__Sequence__fini(member);
  return rosidl_runtime_c__uint32__Sequence__init(member, size);
}

size_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_range(
  const void * untyped_member)
{
  const rosidl_runtime_c__float__Sequence * member =
    (const rosidl_runtime_c__float__Sequence *)(untyped_member);
  return member->size;
}

const void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_range(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__float__Sequence * member =
    (const rosidl_runtime_c__float__Sequence *)(untyped_member);
  return &member->data[index];
}

void * asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_range(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__float__Sequence * member =
    (rosidl_runtime_c__float__Sequence *)(untyped_member);
  return &member->data[index];
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_range(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const float * item =
    ((const float *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_range(untyped_member, index));
  float * value =
    (float *)(untyped_value);
  *value = *item;
}

void asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_range(
  void * untyped_member, size_t index, const void * untyped_value)
{
  float * item =
    ((float *)
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_range(untyped_member, index));
  const float * value =
    (const float *)(untyped_value);
  *item = *value;
}

bool asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_range(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__float__Sequence * member =
    (rosidl_runtime_c__float__Sequence *)(untyped_member);
  rosidl_runtime_c__float__Sequence__fini(member);
  return rosidl_runtime_c__float__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_member_array[9] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "start_ring_index",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, start_ring_index),  // bytes offset in struct
    NULL,  // default value
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__start_ring_index,  // size() function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__start_ring_index,  // get_const(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__start_ring_index,  // get(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__start_ring_index,  // fetch(index, &value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__start_ring_index,  // assign(index, value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__start_ring_index  // resize(index) function pointer
  },
  {
    "end_ring_index",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, end_ring_index),  // bytes offset in struct
    NULL,  // default value
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__end_ring_index,  // size() function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__end_ring_index,  // get_const(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__end_ring_index,  // get(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__end_ring_index,  // fetch(index, &value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__end_ring_index,  // assign(index, value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__end_ring_index  // resize(index) function pointer
  },
  {
    "start_orientation",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, start_orientation),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "end_orientation",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, end_orientation),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "orientation_diff",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, orientation_diff),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "segmented_cloud_ground_flag",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, segmented_cloud_ground_flag),  // bytes offset in struct
    NULL,  // default value
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_ground_flag,  // size() function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_ground_flag,  // get_const(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_ground_flag,  // get(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_ground_flag,  // fetch(index, &value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_ground_flag,  // assign(index, value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_ground_flag  // resize(index) function pointer
  },
  {
    "segmented_cloud_col_ind",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, segmented_cloud_col_ind),  // bytes offset in struct
    NULL,  // default value
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_col_ind,  // size() function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_col_ind,  // get_const(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_col_ind,  // get(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_col_ind,  // fetch(index, &value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_col_ind,  // assign(index, value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_col_ind  // resize(index) function pointer
  },
  {
    "segmented_cloud_range",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(asurt_msgs__msg__CloudInfo, segmented_cloud_range),  // bytes offset in struct
    NULL,  // default value
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__size_function__CloudInfo__segmented_cloud_range,  // size() function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_const_function__CloudInfo__segmented_cloud_range,  // get_const(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__get_function__CloudInfo__segmented_cloud_range,  // get(index) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__fetch_function__CloudInfo__segmented_cloud_range,  // fetch(index, &value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__assign_function__CloudInfo__segmented_cloud_range,  // assign(index, value) function pointer
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__resize_function__CloudInfo__segmented_cloud_range  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_members = {
  "asurt_msgs__msg",  // message namespace
  "CloudInfo",  // message name
  9,  // number of fields
  sizeof(asurt_msgs__msg__CloudInfo),
  asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_member_array,  // message members
  asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_init_function,  // function to initialize message memory (memory has to be allocated)
  asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_type_support_handle = {
  0,
  &asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_asurt_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, asurt_msgs, msg, CloudInfo)() {
  asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_type_support_handle.typesupport_identifier) {
    asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &asurt_msgs__msg__CloudInfo__rosidl_typesupport_introspection_c__CloudInfo_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

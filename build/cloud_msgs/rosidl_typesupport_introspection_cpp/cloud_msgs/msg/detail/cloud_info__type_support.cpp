// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from cloud_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "cloud_msgs/msg/detail/cloud_info__functions.h"
#include "cloud_msgs/msg/detail/cloud_info__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace cloud_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void CloudInfo_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) cloud_msgs::msg::CloudInfo(_init);
}

void CloudInfo_fini_function(void * message_memory)
{
  auto typed_message = static_cast<cloud_msgs::msg::CloudInfo *>(message_memory);
  typed_message->~CloudInfo();
}

size_t size_function__CloudInfo__start_ring_index(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<int32_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__CloudInfo__start_ring_index(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<int32_t> *>(untyped_member);
  return &member[index];
}

void * get_function__CloudInfo__start_ring_index(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<int32_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__CloudInfo__start_ring_index(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const int32_t *>(
    get_const_function__CloudInfo__start_ring_index(untyped_member, index));
  auto & value = *reinterpret_cast<int32_t *>(untyped_value);
  value = item;
}

void assign_function__CloudInfo__start_ring_index(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<int32_t *>(
    get_function__CloudInfo__start_ring_index(untyped_member, index));
  const auto & value = *reinterpret_cast<const int32_t *>(untyped_value);
  item = value;
}

void resize_function__CloudInfo__start_ring_index(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<int32_t> *>(untyped_member);
  member->resize(size);
}

size_t size_function__CloudInfo__end_ring_index(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<int32_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__CloudInfo__end_ring_index(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<int32_t> *>(untyped_member);
  return &member[index];
}

void * get_function__CloudInfo__end_ring_index(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<int32_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__CloudInfo__end_ring_index(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const int32_t *>(
    get_const_function__CloudInfo__end_ring_index(untyped_member, index));
  auto & value = *reinterpret_cast<int32_t *>(untyped_value);
  value = item;
}

void assign_function__CloudInfo__end_ring_index(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<int32_t *>(
    get_function__CloudInfo__end_ring_index(untyped_member, index));
  const auto & value = *reinterpret_cast<const int32_t *>(untyped_value);
  item = value;
}

void resize_function__CloudInfo__end_ring_index(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<int32_t> *>(untyped_member);
  member->resize(size);
}

size_t size_function__CloudInfo__segmented_cloud_ground_flag(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<bool> *>(untyped_member);
  return member->size();
}

void fetch_function__CloudInfo__segmented_cloud_ground_flag(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & member = *reinterpret_cast<const std::vector<bool> *>(untyped_member);
  auto & value = *reinterpret_cast<bool *>(untyped_value);
  value = member[index];
}

void assign_function__CloudInfo__segmented_cloud_ground_flag(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & member = *reinterpret_cast<std::vector<bool> *>(untyped_member);
  const auto & value = *reinterpret_cast<const bool *>(untyped_value);
  member[index] = value;
}

void resize_function__CloudInfo__segmented_cloud_ground_flag(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<bool> *>(untyped_member);
  member->resize(size);
}

size_t size_function__CloudInfo__segmented_cloud_col_ind(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<uint32_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__CloudInfo__segmented_cloud_col_ind(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<uint32_t> *>(untyped_member);
  return &member[index];
}

void * get_function__CloudInfo__segmented_cloud_col_ind(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<uint32_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__CloudInfo__segmented_cloud_col_ind(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const uint32_t *>(
    get_const_function__CloudInfo__segmented_cloud_col_ind(untyped_member, index));
  auto & value = *reinterpret_cast<uint32_t *>(untyped_value);
  value = item;
}

void assign_function__CloudInfo__segmented_cloud_col_ind(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<uint32_t *>(
    get_function__CloudInfo__segmented_cloud_col_ind(untyped_member, index));
  const auto & value = *reinterpret_cast<const uint32_t *>(untyped_value);
  item = value;
}

void resize_function__CloudInfo__segmented_cloud_col_ind(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<uint32_t> *>(untyped_member);
  member->resize(size);
}

size_t size_function__CloudInfo__segmented_cloud_range(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<float> *>(untyped_member);
  return member->size();
}

const void * get_const_function__CloudInfo__segmented_cloud_range(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<float> *>(untyped_member);
  return &member[index];
}

void * get_function__CloudInfo__segmented_cloud_range(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<float> *>(untyped_member);
  return &member[index];
}

void fetch_function__CloudInfo__segmented_cloud_range(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const float *>(
    get_const_function__CloudInfo__segmented_cloud_range(untyped_member, index));
  auto & value = *reinterpret_cast<float *>(untyped_value);
  value = item;
}

void assign_function__CloudInfo__segmented_cloud_range(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<float *>(
    get_function__CloudInfo__segmented_cloud_range(untyped_member, index));
  const auto & value = *reinterpret_cast<const float *>(untyped_value);
  item = value;
}

void resize_function__CloudInfo__segmented_cloud_range(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<float> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember CloudInfo_message_member_array[9] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "start_ring_index",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, start_ring_index),  // bytes offset in struct
    nullptr,  // default value
    size_function__CloudInfo__start_ring_index,  // size() function pointer
    get_const_function__CloudInfo__start_ring_index,  // get_const(index) function pointer
    get_function__CloudInfo__start_ring_index,  // get(index) function pointer
    fetch_function__CloudInfo__start_ring_index,  // fetch(index, &value) function pointer
    assign_function__CloudInfo__start_ring_index,  // assign(index, value) function pointer
    resize_function__CloudInfo__start_ring_index  // resize(index) function pointer
  },
  {
    "end_ring_index",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, end_ring_index),  // bytes offset in struct
    nullptr,  // default value
    size_function__CloudInfo__end_ring_index,  // size() function pointer
    get_const_function__CloudInfo__end_ring_index,  // get_const(index) function pointer
    get_function__CloudInfo__end_ring_index,  // get(index) function pointer
    fetch_function__CloudInfo__end_ring_index,  // fetch(index, &value) function pointer
    assign_function__CloudInfo__end_ring_index,  // assign(index, value) function pointer
    resize_function__CloudInfo__end_ring_index  // resize(index) function pointer
  },
  {
    "start_orientation",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, start_orientation),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "end_orientation",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, end_orientation),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "orientation_diff",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, orientation_diff),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "segmented_cloud_ground_flag",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, segmented_cloud_ground_flag),  // bytes offset in struct
    nullptr,  // default value
    size_function__CloudInfo__segmented_cloud_ground_flag,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    fetch_function__CloudInfo__segmented_cloud_ground_flag,  // fetch(index, &value) function pointer
    assign_function__CloudInfo__segmented_cloud_ground_flag,  // assign(index, value) function pointer
    resize_function__CloudInfo__segmented_cloud_ground_flag  // resize(index) function pointer
  },
  {
    "segmented_cloud_col_ind",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, segmented_cloud_col_ind),  // bytes offset in struct
    nullptr,  // default value
    size_function__CloudInfo__segmented_cloud_col_ind,  // size() function pointer
    get_const_function__CloudInfo__segmented_cloud_col_ind,  // get_const(index) function pointer
    get_function__CloudInfo__segmented_cloud_col_ind,  // get(index) function pointer
    fetch_function__CloudInfo__segmented_cloud_col_ind,  // fetch(index, &value) function pointer
    assign_function__CloudInfo__segmented_cloud_col_ind,  // assign(index, value) function pointer
    resize_function__CloudInfo__segmented_cloud_col_ind  // resize(index) function pointer
  },
  {
    "segmented_cloud_range",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(cloud_msgs::msg::CloudInfo, segmented_cloud_range),  // bytes offset in struct
    nullptr,  // default value
    size_function__CloudInfo__segmented_cloud_range,  // size() function pointer
    get_const_function__CloudInfo__segmented_cloud_range,  // get_const(index) function pointer
    get_function__CloudInfo__segmented_cloud_range,  // get(index) function pointer
    fetch_function__CloudInfo__segmented_cloud_range,  // fetch(index, &value) function pointer
    assign_function__CloudInfo__segmented_cloud_range,  // assign(index, value) function pointer
    resize_function__CloudInfo__segmented_cloud_range  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers CloudInfo_message_members = {
  "cloud_msgs::msg",  // message namespace
  "CloudInfo",  // message name
  9,  // number of fields
  sizeof(cloud_msgs::msg::CloudInfo),
  false,  // has_any_key_member_
  CloudInfo_message_member_array,  // message members
  CloudInfo_init_function,  // function to initialize message memory (memory has to be allocated)
  CloudInfo_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t CloudInfo_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &CloudInfo_message_members,
  get_message_typesupport_handle_function,
  &cloud_msgs__msg__CloudInfo__get_type_hash,
  &cloud_msgs__msg__CloudInfo__get_type_description,
  &cloud_msgs__msg__CloudInfo__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace cloud_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<cloud_msgs::msg::CloudInfo>()
{
  return &::cloud_msgs::msg::rosidl_typesupport_introspection_cpp::CloudInfo_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, cloud_msgs, msg, CloudInfo)() {
  return &::cloud_msgs::msg::rosidl_typesupport_introspection_cpp::CloudInfo_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

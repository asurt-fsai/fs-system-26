// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from asurt_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_
#define ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "asurt_msgs/msg/detail/cloud_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace asurt_msgs
{

namespace msg
{

namespace builder
{

class Init_CloudInfo_segmented_cloud_range
{
public:
  explicit Init_CloudInfo_segmented_cloud_range(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  ::asurt_msgs::msg::CloudInfo segmented_cloud_range(::asurt_msgs::msg::CloudInfo::_segmented_cloud_range_type arg)
  {
    msg_.segmented_cloud_range = std::move(arg);
    return std::move(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_segmented_cloud_col_ind
{
public:
  explicit Init_CloudInfo_segmented_cloud_col_ind(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_range segmented_cloud_col_ind(::asurt_msgs::msg::CloudInfo::_segmented_cloud_col_ind_type arg)
  {
    msg_.segmented_cloud_col_ind = std::move(arg);
    return Init_CloudInfo_segmented_cloud_range(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_segmented_cloud_ground_flag
{
public:
  explicit Init_CloudInfo_segmented_cloud_ground_flag(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_col_ind segmented_cloud_ground_flag(::asurt_msgs::msg::CloudInfo::_segmented_cloud_ground_flag_type arg)
  {
    msg_.segmented_cloud_ground_flag = std::move(arg);
    return Init_CloudInfo_segmented_cloud_col_ind(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_orientation_diff
{
public:
  explicit Init_CloudInfo_orientation_diff(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_ground_flag orientation_diff(::asurt_msgs::msg::CloudInfo::_orientation_diff_type arg)
  {
    msg_.orientation_diff = std::move(arg);
    return Init_CloudInfo_segmented_cloud_ground_flag(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_end_orientation
{
public:
  explicit Init_CloudInfo_end_orientation(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_orientation_diff end_orientation(::asurt_msgs::msg::CloudInfo::_end_orientation_type arg)
  {
    msg_.end_orientation = std::move(arg);
    return Init_CloudInfo_orientation_diff(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_start_orientation
{
public:
  explicit Init_CloudInfo_start_orientation(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_end_orientation start_orientation(::asurt_msgs::msg::CloudInfo::_start_orientation_type arg)
  {
    msg_.start_orientation = std::move(arg);
    return Init_CloudInfo_end_orientation(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_end_ring_index
{
public:
  explicit Init_CloudInfo_end_ring_index(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_start_orientation end_ring_index(::asurt_msgs::msg::CloudInfo::_end_ring_index_type arg)
  {
    msg_.end_ring_index = std::move(arg);
    return Init_CloudInfo_start_orientation(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_start_ring_index
{
public:
  explicit Init_CloudInfo_start_ring_index(::asurt_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_end_ring_index start_ring_index(::asurt_msgs::msg::CloudInfo::_start_ring_index_type arg)
  {
    msg_.start_ring_index = std::move(arg);
    return Init_CloudInfo_end_ring_index(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_header
{
public:
  Init_CloudInfo_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CloudInfo_start_ring_index header(::asurt_msgs::msg::CloudInfo::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_CloudInfo_start_ring_index(msg_);
  }

private:
  ::asurt_msgs::msg::CloudInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::asurt_msgs::msg::CloudInfo>()
{
  return asurt_msgs::msg::builder::Init_CloudInfo_header();
}

}  // namespace asurt_msgs

#endif  // ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_

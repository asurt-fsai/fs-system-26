// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from cloud_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "cloud_msgs/msg/cloud_info.hpp"


#ifndef CLOUD_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_
#define CLOUD_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "cloud_msgs/msg/detail/cloud_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace cloud_msgs
{

namespace msg
{

namespace builder
{

class Init_CloudInfo_segmented_cloud_range
{
public:
  explicit Init_CloudInfo_segmented_cloud_range(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  ::cloud_msgs::msg::CloudInfo segmented_cloud_range(::cloud_msgs::msg::CloudInfo::_segmented_cloud_range_type arg)
  {
    msg_.segmented_cloud_range = std::move(arg);
    return std::move(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_segmented_cloud_col_ind
{
public:
  explicit Init_CloudInfo_segmented_cloud_col_ind(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_range segmented_cloud_col_ind(::cloud_msgs::msg::CloudInfo::_segmented_cloud_col_ind_type arg)
  {
    msg_.segmented_cloud_col_ind = std::move(arg);
    return Init_CloudInfo_segmented_cloud_range(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_segmented_cloud_ground_flag
{
public:
  explicit Init_CloudInfo_segmented_cloud_ground_flag(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_col_ind segmented_cloud_ground_flag(::cloud_msgs::msg::CloudInfo::_segmented_cloud_ground_flag_type arg)
  {
    msg_.segmented_cloud_ground_flag = std::move(arg);
    return Init_CloudInfo_segmented_cloud_col_ind(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_orientation_diff
{
public:
  explicit Init_CloudInfo_orientation_diff(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_segmented_cloud_ground_flag orientation_diff(::cloud_msgs::msg::CloudInfo::_orientation_diff_type arg)
  {
    msg_.orientation_diff = std::move(arg);
    return Init_CloudInfo_segmented_cloud_ground_flag(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_end_orientation
{
public:
  explicit Init_CloudInfo_end_orientation(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_orientation_diff end_orientation(::cloud_msgs::msg::CloudInfo::_end_orientation_type arg)
  {
    msg_.end_orientation = std::move(arg);
    return Init_CloudInfo_orientation_diff(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_start_orientation
{
public:
  explicit Init_CloudInfo_start_orientation(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_end_orientation start_orientation(::cloud_msgs::msg::CloudInfo::_start_orientation_type arg)
  {
    msg_.start_orientation = std::move(arg);
    return Init_CloudInfo_end_orientation(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_end_ring_index
{
public:
  explicit Init_CloudInfo_end_ring_index(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_start_orientation end_ring_index(::cloud_msgs::msg::CloudInfo::_end_ring_index_type arg)
  {
    msg_.end_ring_index = std::move(arg);
    return Init_CloudInfo_start_orientation(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_start_ring_index
{
public:
  explicit Init_CloudInfo_start_ring_index(::cloud_msgs::msg::CloudInfo & msg)
  : msg_(msg)
  {}
  Init_CloudInfo_end_ring_index start_ring_index(::cloud_msgs::msg::CloudInfo::_start_ring_index_type arg)
  {
    msg_.start_ring_index = std::move(arg);
    return Init_CloudInfo_end_ring_index(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

class Init_CloudInfo_header
{
public:
  Init_CloudInfo_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CloudInfo_start_ring_index header(::cloud_msgs::msg::CloudInfo::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_CloudInfo_start_ring_index(msg_);
  }

private:
  ::cloud_msgs::msg::CloudInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::cloud_msgs::msg::CloudInfo>()
{
  return cloud_msgs::msg::builder::Init_CloudInfo_header();
}

}  // namespace cloud_msgs

#endif  // CLOUD_MSGS__MSG__DETAIL__CLOUD_INFO__BUILDER_HPP_

// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from asurt_msgs:msg/KeyPoints.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__KEY_POINTS__BUILDER_HPP_
#define ASURT_MSGS__MSG__DETAIL__KEY_POINTS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "asurt_msgs/msg/detail/key_points__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace asurt_msgs
{

namespace msg
{

namespace builder
{

class Init_KeyPoints_keypoints
{
public:
  explicit Init_KeyPoints_keypoints(::asurt_msgs::msg::KeyPoints & msg)
  : msg_(msg)
  {}
  ::asurt_msgs::msg::KeyPoints keypoints(::asurt_msgs::msg::KeyPoints::_keypoints_type arg)
  {
    msg_.keypoints = std::move(arg);
    return std::move(msg_);
  }

private:
  ::asurt_msgs::msg::KeyPoints msg_;
};

class Init_KeyPoints_object_count
{
public:
  explicit Init_KeyPoints_object_count(::asurt_msgs::msg::KeyPoints & msg)
  : msg_(msg)
  {}
  Init_KeyPoints_keypoints object_count(::asurt_msgs::msg::KeyPoints::_object_count_type arg)
  {
    msg_.object_count = std::move(arg);
    return Init_KeyPoints_keypoints(msg_);
  }

private:
  ::asurt_msgs::msg::KeyPoints msg_;
};

class Init_KeyPoints_frame_id
{
public:
  Init_KeyPoints_frame_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_KeyPoints_object_count frame_id(::asurt_msgs::msg::KeyPoints::_frame_id_type arg)
  {
    msg_.frame_id = std::move(arg);
    return Init_KeyPoints_object_count(msg_);
  }

private:
  ::asurt_msgs::msg::KeyPoints msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::asurt_msgs::msg::KeyPoints>()
{
  return asurt_msgs::msg::builder::Init_KeyPoints_frame_id();
}

}  // namespace asurt_msgs

#endif  // ASURT_MSGS__MSG__DETAIL__KEY_POINTS__BUILDER_HPP_

// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from asurt_msgs:msg/Event.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__EVENT__BUILDER_HPP_
#define ASURT_MSGS__MSG__DETAIL__EVENT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "asurt_msgs/msg/detail/event__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace asurt_msgs
{

namespace msg
{

namespace builder
{

class Init_Event_details_json
{
public:
  explicit Init_Event_details_json(::asurt_msgs::msg::Event & msg)
  : msg_(msg)
  {}
  ::asurt_msgs::msg::Event details_json(::asurt_msgs::msg::Event::_details_json_type arg)
  {
    msg_.details_json = std::move(arg);
    return std::move(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

class Init_Event_source
{
public:
  explicit Init_Event_source(::asurt_msgs::msg::Event & msg)
  : msg_(msg)
  {}
  Init_Event_details_json source(::asurt_msgs::msg::Event::_source_type arg)
  {
    msg_.source = std::move(arg);
    return Init_Event_details_json(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

class Init_Event_event_type
{
public:
  explicit Init_Event_event_type(::asurt_msgs::msg::Event & msg)
  : msg_(msg)
  {}
  Init_Event_source event_type(::asurt_msgs::msg::Event::_event_type_type arg)
  {
    msg_.event_type = std::move(arg);
    return Init_Event_source(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

class Init_Event_category
{
public:
  explicit Init_Event_category(::asurt_msgs::msg::Event & msg)
  : msg_(msg)
  {}
  Init_Event_event_type category(::asurt_msgs::msg::Event::_category_type arg)
  {
    msg_.category = std::move(arg);
    return Init_Event_event_type(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

class Init_Event_severity
{
public:
  explicit Init_Event_severity(::asurt_msgs::msg::Event & msg)
  : msg_(msg)
  {}
  Init_Event_category severity(::asurt_msgs::msg::Event::_severity_type arg)
  {
    msg_.severity = std::move(arg);
    return Init_Event_category(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

class Init_Event_stamp
{
public:
  Init_Event_stamp()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Event_severity stamp(::asurt_msgs::msg::Event::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return Init_Event_severity(msg_);
  }

private:
  ::asurt_msgs::msg::Event msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::asurt_msgs::msg::Event>()
{
  return asurt_msgs::msg::builder::Init_Event_stamp();
}

}  // namespace asurt_msgs

#endif  // ASURT_MSGS__MSG__DETAIL__EVENT__BUILDER_HPP_

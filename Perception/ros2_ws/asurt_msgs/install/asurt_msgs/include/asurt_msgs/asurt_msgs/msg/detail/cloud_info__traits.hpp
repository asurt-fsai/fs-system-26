// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from asurt_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#ifndef ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__TRAITS_HPP_
#define ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "asurt_msgs/msg/detail/cloud_info__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace asurt_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const CloudInfo & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: start_ring_index
  {
    if (msg.start_ring_index.size() == 0) {
      out << "start_ring_index: []";
    } else {
      out << "start_ring_index: [";
      size_t pending_items = msg.start_ring_index.size();
      for (auto item : msg.start_ring_index) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: end_ring_index
  {
    if (msg.end_ring_index.size() == 0) {
      out << "end_ring_index: []";
    } else {
      out << "end_ring_index: [";
      size_t pending_items = msg.end_ring_index.size();
      for (auto item : msg.end_ring_index) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: start_orientation
  {
    out << "start_orientation: ";
    rosidl_generator_traits::value_to_yaml(msg.start_orientation, out);
    out << ", ";
  }

  // member: end_orientation
  {
    out << "end_orientation: ";
    rosidl_generator_traits::value_to_yaml(msg.end_orientation, out);
    out << ", ";
  }

  // member: orientation_diff
  {
    out << "orientation_diff: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_diff, out);
    out << ", ";
  }

  // member: segmented_cloud_ground_flag
  {
    if (msg.segmented_cloud_ground_flag.size() == 0) {
      out << "segmented_cloud_ground_flag: []";
    } else {
      out << "segmented_cloud_ground_flag: [";
      size_t pending_items = msg.segmented_cloud_ground_flag.size();
      for (auto item : msg.segmented_cloud_ground_flag) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: segmented_cloud_col_ind
  {
    if (msg.segmented_cloud_col_ind.size() == 0) {
      out << "segmented_cloud_col_ind: []";
    } else {
      out << "segmented_cloud_col_ind: [";
      size_t pending_items = msg.segmented_cloud_col_ind.size();
      for (auto item : msg.segmented_cloud_col_ind) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: segmented_cloud_range
  {
    if (msg.segmented_cloud_range.size() == 0) {
      out << "segmented_cloud_range: []";
    } else {
      out << "segmented_cloud_range: [";
      size_t pending_items = msg.segmented_cloud_range.size();
      for (auto item : msg.segmented_cloud_range) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CloudInfo & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: start_ring_index
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.start_ring_index.size() == 0) {
      out << "start_ring_index: []\n";
    } else {
      out << "start_ring_index:\n";
      for (auto item : msg.start_ring_index) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: end_ring_index
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.end_ring_index.size() == 0) {
      out << "end_ring_index: []\n";
    } else {
      out << "end_ring_index:\n";
      for (auto item : msg.end_ring_index) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: start_orientation
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "start_orientation: ";
    rosidl_generator_traits::value_to_yaml(msg.start_orientation, out);
    out << "\n";
  }

  // member: end_orientation
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "end_orientation: ";
    rosidl_generator_traits::value_to_yaml(msg.end_orientation, out);
    out << "\n";
  }

  // member: orientation_diff
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation_diff: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_diff, out);
    out << "\n";
  }

  // member: segmented_cloud_ground_flag
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.segmented_cloud_ground_flag.size() == 0) {
      out << "segmented_cloud_ground_flag: []\n";
    } else {
      out << "segmented_cloud_ground_flag:\n";
      for (auto item : msg.segmented_cloud_ground_flag) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: segmented_cloud_col_ind
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.segmented_cloud_col_ind.size() == 0) {
      out << "segmented_cloud_col_ind: []\n";
    } else {
      out << "segmented_cloud_col_ind:\n";
      for (auto item : msg.segmented_cloud_col_ind) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: segmented_cloud_range
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.segmented_cloud_range.size() == 0) {
      out << "segmented_cloud_range: []\n";
    } else {
      out << "segmented_cloud_range:\n";
      for (auto item : msg.segmented_cloud_range) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CloudInfo & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace asurt_msgs

namespace rosidl_generator_traits
{

[[deprecated("use asurt_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const asurt_msgs::msg::CloudInfo & msg,
  std::ostream & out, size_t indentation = 0)
{
  asurt_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use asurt_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const asurt_msgs::msg::CloudInfo & msg)
{
  return asurt_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<asurt_msgs::msg::CloudInfo>()
{
  return "asurt_msgs::msg::CloudInfo";
}

template<>
inline const char * name<asurt_msgs::msg::CloudInfo>()
{
  return "asurt_msgs/msg/CloudInfo";
}

template<>
struct has_fixed_size<asurt_msgs::msg::CloudInfo>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<asurt_msgs::msg::CloudInfo>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<asurt_msgs::msg::CloudInfo>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ASURT_MSGS__MSG__DETAIL__CLOUD_INFO__TRAITS_HPP_

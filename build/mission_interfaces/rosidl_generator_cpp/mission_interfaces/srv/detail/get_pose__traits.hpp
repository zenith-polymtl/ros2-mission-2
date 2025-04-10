// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__SRV__DETAIL__GET_POSE__TRAITS_HPP_
#define MISSION_INTERFACES__SRV__DETAIL__GET_POSE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "mission_interfaces/srv/detail/get_pose__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace mission_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetPose_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetPose_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetPose_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace mission_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use mission_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const mission_interfaces::srv::GetPose_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  mission_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use mission_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const mission_interfaces::srv::GetPose_Request & msg)
{
  return mission_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<mission_interfaces::srv::GetPose_Request>()
{
  return "mission_interfaces::srv::GetPose_Request";
}

template<>
inline const char * name<mission_interfaces::srv::GetPose_Request>()
{
  return "mission_interfaces/srv/GetPose_Request";
}

template<>
struct has_fixed_size<mission_interfaces::srv::GetPose_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<mission_interfaces::srv::GetPose_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<mission_interfaces::srv::GetPose_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace mission_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetPose_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << ", ";
  }

  // member: position_x
  {
    out << "position_x: ";
    rosidl_generator_traits::value_to_yaml(msg.position_x, out);
    out << ", ";
  }

  // member: position_y
  {
    out << "position_y: ";
    rosidl_generator_traits::value_to_yaml(msg.position_y, out);
    out << ", ";
  }

  // member: position_z
  {
    out << "position_z: ";
    rosidl_generator_traits::value_to_yaml(msg.position_z, out);
    out << ", ";
  }

  // member: orientation_x
  {
    out << "orientation_x: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_x, out);
    out << ", ";
  }

  // member: orientation_y
  {
    out << "orientation_y: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_y, out);
    out << ", ";
  }

  // member: orientation_z
  {
    out << "orientation_z: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_z, out);
    out << ", ";
  }

  // member: orientation_w
  {
    out << "orientation_w: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_w, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetPose_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }

  // member: position_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_x: ";
    rosidl_generator_traits::value_to_yaml(msg.position_x, out);
    out << "\n";
  }

  // member: position_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_y: ";
    rosidl_generator_traits::value_to_yaml(msg.position_y, out);
    out << "\n";
  }

  // member: position_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_z: ";
    rosidl_generator_traits::value_to_yaml(msg.position_z, out);
    out << "\n";
  }

  // member: orientation_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation_x: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_x, out);
    out << "\n";
  }

  // member: orientation_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation_y: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_y, out);
    out << "\n";
  }

  // member: orientation_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation_z: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_z, out);
    out << "\n";
  }

  // member: orientation_w
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation_w: ";
    rosidl_generator_traits::value_to_yaml(msg.orientation_w, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetPose_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace mission_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use mission_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const mission_interfaces::srv::GetPose_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  mission_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use mission_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const mission_interfaces::srv::GetPose_Response & msg)
{
  return mission_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<mission_interfaces::srv::GetPose_Response>()
{
  return "mission_interfaces::srv::GetPose_Response";
}

template<>
inline const char * name<mission_interfaces::srv::GetPose_Response>()
{
  return "mission_interfaces/srv/GetPose_Response";
}

template<>
struct has_fixed_size<mission_interfaces::srv::GetPose_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<mission_interfaces::srv::GetPose_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<mission_interfaces::srv::GetPose_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<mission_interfaces::srv::GetPose>()
{
  return "mission_interfaces::srv::GetPose";
}

template<>
inline const char * name<mission_interfaces::srv::GetPose>()
{
  return "mission_interfaces/srv/GetPose";
}

template<>
struct has_fixed_size<mission_interfaces::srv::GetPose>
  : std::integral_constant<
    bool,
    has_fixed_size<mission_interfaces::srv::GetPose_Request>::value &&
    has_fixed_size<mission_interfaces::srv::GetPose_Response>::value
  >
{
};

template<>
struct has_bounded_size<mission_interfaces::srv::GetPose>
  : std::integral_constant<
    bool,
    has_bounded_size<mission_interfaces::srv::GetPose_Request>::value &&
    has_bounded_size<mission_interfaces::srv::GetPose_Response>::value
  >
{
};

template<>
struct is_service<mission_interfaces::srv::GetPose>
  : std::true_type
{
};

template<>
struct is_service_request<mission_interfaces::srv::GetPose_Request>
  : std::true_type
{
};

template<>
struct is_service_response<mission_interfaces::srv::GetPose_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // MISSION_INTERFACES__SRV__DETAIL__GET_POSE__TRAITS_HPP_

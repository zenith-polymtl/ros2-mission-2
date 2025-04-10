// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__SRV__DETAIL__GET_POSE__BUILDER_HPP_
#define MISSION_INTERFACES__SRV__DETAIL__GET_POSE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "mission_interfaces/srv/detail/get_pose__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace mission_interfaces
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::mission_interfaces::srv::GetPose_Request>()
{
  return ::mission_interfaces::srv::GetPose_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace mission_interfaces


namespace mission_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetPose_Response_orientation_w
{
public:
  explicit Init_GetPose_Response_orientation_w(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  ::mission_interfaces::srv::GetPose_Response orientation_w(::mission_interfaces::srv::GetPose_Response::_orientation_w_type arg)
  {
    msg_.orientation_w = std::move(arg);
    return std::move(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_orientation_z
{
public:
  explicit Init_GetPose_Response_orientation_z(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_orientation_w orientation_z(::mission_interfaces::srv::GetPose_Response::_orientation_z_type arg)
  {
    msg_.orientation_z = std::move(arg);
    return Init_GetPose_Response_orientation_w(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_orientation_y
{
public:
  explicit Init_GetPose_Response_orientation_y(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_orientation_z orientation_y(::mission_interfaces::srv::GetPose_Response::_orientation_y_type arg)
  {
    msg_.orientation_y = std::move(arg);
    return Init_GetPose_Response_orientation_z(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_orientation_x
{
public:
  explicit Init_GetPose_Response_orientation_x(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_orientation_y orientation_x(::mission_interfaces::srv::GetPose_Response::_orientation_x_type arg)
  {
    msg_.orientation_x = std::move(arg);
    return Init_GetPose_Response_orientation_y(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_position_z
{
public:
  explicit Init_GetPose_Response_position_z(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_orientation_x position_z(::mission_interfaces::srv::GetPose_Response::_position_z_type arg)
  {
    msg_.position_z = std::move(arg);
    return Init_GetPose_Response_orientation_x(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_position_y
{
public:
  explicit Init_GetPose_Response_position_y(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_position_z position_y(::mission_interfaces::srv::GetPose_Response::_position_y_type arg)
  {
    msg_.position_y = std::move(arg);
    return Init_GetPose_Response_position_z(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_position_x
{
public:
  explicit Init_GetPose_Response_position_x(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_position_y position_x(::mission_interfaces::srv::GetPose_Response::_position_x_type arg)
  {
    msg_.position_x = std::move(arg);
    return Init_GetPose_Response_position_y(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_message
{
public:
  explicit Init_GetPose_Response_message(::mission_interfaces::srv::GetPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetPose_Response_position_x message(::mission_interfaces::srv::GetPose_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return Init_GetPose_Response_position_x(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

class Init_GetPose_Response_success
{
public:
  Init_GetPose_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetPose_Response_message success(::mission_interfaces::srv::GetPose_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_GetPose_Response_message(msg_);
  }

private:
  ::mission_interfaces::srv::GetPose_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::mission_interfaces::srv::GetPose_Response>()
{
  return mission_interfaces::srv::builder::Init_GetPose_Response_success();
}

}  // namespace mission_interfaces

#endif  // MISSION_INTERFACES__SRV__DETAIL__GET_POSE__BUILDER_HPP_

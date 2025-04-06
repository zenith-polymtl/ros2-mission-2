// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from mission_interfaces:msg/ApproachInfo.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__BUILDER_HPP_
#define MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "mission_interfaces/msg/detail/approach_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace mission_interfaces
{

namespace msg
{

namespace builder
{

class Init_ApproachInfo_status
{
public:
  explicit Init_ApproachInfo_status(::mission_interfaces::msg::ApproachInfo & msg)
  : msg_(msg)
  {}
  ::mission_interfaces::msg::ApproachInfo status(::mission_interfaces::msg::ApproachInfo::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::mission_interfaces::msg::ApproachInfo msg_;
};

class Init_ApproachInfo_z
{
public:
  explicit Init_ApproachInfo_z(::mission_interfaces::msg::ApproachInfo & msg)
  : msg_(msg)
  {}
  Init_ApproachInfo_status z(::mission_interfaces::msg::ApproachInfo::_z_type arg)
  {
    msg_.z = std::move(arg);
    return Init_ApproachInfo_status(msg_);
  }

private:
  ::mission_interfaces::msg::ApproachInfo msg_;
};

class Init_ApproachInfo_y
{
public:
  explicit Init_ApproachInfo_y(::mission_interfaces::msg::ApproachInfo & msg)
  : msg_(msg)
  {}
  Init_ApproachInfo_z y(::mission_interfaces::msg::ApproachInfo::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_ApproachInfo_z(msg_);
  }

private:
  ::mission_interfaces::msg::ApproachInfo msg_;
};

class Init_ApproachInfo_x
{
public:
  Init_ApproachInfo_x()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ApproachInfo_y x(::mission_interfaces::msg::ApproachInfo::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_ApproachInfo_y(msg_);
  }

private:
  ::mission_interfaces::msg::ApproachInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::mission_interfaces::msg::ApproachInfo>()
{
  return mission_interfaces::msg::builder::Init_ApproachInfo_x();
}

}  // namespace mission_interfaces

#endif  // MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__BUILDER_HPP_

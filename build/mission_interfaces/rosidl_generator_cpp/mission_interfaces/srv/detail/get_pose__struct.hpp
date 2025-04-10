// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_HPP_
#define MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__mission_interfaces__srv__GetPose_Request __attribute__((deprecated))
#else
# define DEPRECATED__mission_interfaces__srv__GetPose_Request __declspec(deprecated)
#endif

namespace mission_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetPose_Request_
{
  using Type = GetPose_Request_<ContainerAllocator>;

  explicit GetPose_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit GetPose_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    mission_interfaces::srv::GetPose_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const mission_interfaces::srv::GetPose_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      mission_interfaces::srv::GetPose_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      mission_interfaces::srv::GetPose_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__mission_interfaces__srv__GetPose_Request
    std::shared_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__mission_interfaces__srv__GetPose_Request
    std::shared_ptr<mission_interfaces::srv::GetPose_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetPose_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetPose_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetPose_Request_

// alias to use template instance with default allocator
using GetPose_Request =
  mission_interfaces::srv::GetPose_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace mission_interfaces


#ifndef _WIN32
# define DEPRECATED__mission_interfaces__srv__GetPose_Response __attribute__((deprecated))
#else
# define DEPRECATED__mission_interfaces__srv__GetPose_Response __declspec(deprecated)
#endif

namespace mission_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetPose_Response_
{
  using Type = GetPose_Response_<ContainerAllocator>;

  explicit GetPose_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
      this->position_x = 0.0;
      this->position_y = 0.0;
      this->position_z = 0.0;
      this->orientation_x = 0.0;
      this->orientation_y = 0.0;
      this->orientation_z = 0.0;
      this->orientation_w = 0.0;
    }
  }

  explicit GetPose_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
      this->position_x = 0.0;
      this->position_y = 0.0;
      this->position_z = 0.0;
      this->orientation_x = 0.0;
      this->orientation_y = 0.0;
      this->orientation_z = 0.0;
      this->orientation_w = 0.0;
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;
  using _position_x_type =
    double;
  _position_x_type position_x;
  using _position_y_type =
    double;
  _position_y_type position_y;
  using _position_z_type =
    double;
  _position_z_type position_z;
  using _orientation_x_type =
    double;
  _orientation_x_type orientation_x;
  using _orientation_y_type =
    double;
  _orientation_y_type orientation_y;
  using _orientation_z_type =
    double;
  _orientation_z_type orientation_z;
  using _orientation_w_type =
    double;
  _orientation_w_type orientation_w;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }
  Type & set__position_x(
    const double & _arg)
  {
    this->position_x = _arg;
    return *this;
  }
  Type & set__position_y(
    const double & _arg)
  {
    this->position_y = _arg;
    return *this;
  }
  Type & set__position_z(
    const double & _arg)
  {
    this->position_z = _arg;
    return *this;
  }
  Type & set__orientation_x(
    const double & _arg)
  {
    this->orientation_x = _arg;
    return *this;
  }
  Type & set__orientation_y(
    const double & _arg)
  {
    this->orientation_y = _arg;
    return *this;
  }
  Type & set__orientation_z(
    const double & _arg)
  {
    this->orientation_z = _arg;
    return *this;
  }
  Type & set__orientation_w(
    const double & _arg)
  {
    this->orientation_w = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    mission_interfaces::srv::GetPose_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const mission_interfaces::srv::GetPose_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      mission_interfaces::srv::GetPose_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      mission_interfaces::srv::GetPose_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__mission_interfaces__srv__GetPose_Response
    std::shared_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__mission_interfaces__srv__GetPose_Response
    std::shared_ptr<mission_interfaces::srv::GetPose_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetPose_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    if (this->position_x != other.position_x) {
      return false;
    }
    if (this->position_y != other.position_y) {
      return false;
    }
    if (this->position_z != other.position_z) {
      return false;
    }
    if (this->orientation_x != other.orientation_x) {
      return false;
    }
    if (this->orientation_y != other.orientation_y) {
      return false;
    }
    if (this->orientation_z != other.orientation_z) {
      return false;
    }
    if (this->orientation_w != other.orientation_w) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetPose_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetPose_Response_

// alias to use template instance with default allocator
using GetPose_Response =
  mission_interfaces::srv::GetPose_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace mission_interfaces

namespace mission_interfaces
{

namespace srv
{

struct GetPose
{
  using Request = mission_interfaces::srv::GetPose_Request;
  using Response = mission_interfaces::srv::GetPose_Response;
};

}  // namespace srv

}  // namespace mission_interfaces

#endif  // MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_HPP_

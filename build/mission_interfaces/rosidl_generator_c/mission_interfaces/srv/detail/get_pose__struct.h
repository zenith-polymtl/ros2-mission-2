// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_H_
#define MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/GetPose in the package mission_interfaces.
typedef struct mission_interfaces__srv__GetPose_Request
{
  uint8_t structure_needs_at_least_one_member;
} mission_interfaces__srv__GetPose_Request;

// Struct for a sequence of mission_interfaces__srv__GetPose_Request.
typedef struct mission_interfaces__srv__GetPose_Request__Sequence
{
  mission_interfaces__srv__GetPose_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mission_interfaces__srv__GetPose_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetPose in the package mission_interfaces.
typedef struct mission_interfaces__srv__GetPose_Response
{
  bool success;
  rosidl_runtime_c__String message;
  double position_x;
  double position_y;
  double position_z;
  double orientation_x;
  double orientation_y;
  double orientation_z;
  double orientation_w;
} mission_interfaces__srv__GetPose_Response;

// Struct for a sequence of mission_interfaces__srv__GetPose_Response.
typedef struct mission_interfaces__srv__GetPose_Response__Sequence
{
  mission_interfaces__srv__GetPose_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mission_interfaces__srv__GetPose_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MISSION_INTERFACES__SRV__DETAIL__GET_POSE__STRUCT_H_

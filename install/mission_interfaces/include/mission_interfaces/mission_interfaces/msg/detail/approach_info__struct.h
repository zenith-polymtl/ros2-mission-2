// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from mission_interfaces:msg/ApproachInfo.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__STRUCT_H_
#define MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'status'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/ApproachInfo in the package mission_interfaces.
typedef struct mission_interfaces__msg__ApproachInfo
{
  double x;
  double y;
  double z;
  rosidl_runtime_c__String status;
} mission_interfaces__msg__ApproachInfo;

// Struct for a sequence of mission_interfaces__msg__ApproachInfo.
typedef struct mission_interfaces__msg__ApproachInfo__Sequence
{
  mission_interfaces__msg__ApproachInfo * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mission_interfaces__msg__ApproachInfo__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__STRUCT_H_

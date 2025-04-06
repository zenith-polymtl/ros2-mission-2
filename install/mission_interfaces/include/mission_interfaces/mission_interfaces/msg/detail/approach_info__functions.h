// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from mission_interfaces:msg/ApproachInfo.idl
// generated code does not contain a copyright notice

#ifndef MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__FUNCTIONS_H_
#define MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "mission_interfaces/msg/rosidl_generator_c__visibility_control.h"

#include "mission_interfaces/msg/detail/approach_info__struct.h"

/// Initialize msg/ApproachInfo message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * mission_interfaces__msg__ApproachInfo
 * )) before or use
 * mission_interfaces__msg__ApproachInfo__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__init(mission_interfaces__msg__ApproachInfo * msg);

/// Finalize msg/ApproachInfo message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
void
mission_interfaces__msg__ApproachInfo__fini(mission_interfaces__msg__ApproachInfo * msg);

/// Create msg/ApproachInfo message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * mission_interfaces__msg__ApproachInfo__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
mission_interfaces__msg__ApproachInfo *
mission_interfaces__msg__ApproachInfo__create();

/// Destroy msg/ApproachInfo message.
/**
 * It calls
 * mission_interfaces__msg__ApproachInfo__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
void
mission_interfaces__msg__ApproachInfo__destroy(mission_interfaces__msg__ApproachInfo * msg);

/// Check for msg/ApproachInfo message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__are_equal(const mission_interfaces__msg__ApproachInfo * lhs, const mission_interfaces__msg__ApproachInfo * rhs);

/// Copy a msg/ApproachInfo message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__copy(
  const mission_interfaces__msg__ApproachInfo * input,
  mission_interfaces__msg__ApproachInfo * output);

/// Initialize array of msg/ApproachInfo messages.
/**
 * It allocates the memory for the number of elements and calls
 * mission_interfaces__msg__ApproachInfo__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__Sequence__init(mission_interfaces__msg__ApproachInfo__Sequence * array, size_t size);

/// Finalize array of msg/ApproachInfo messages.
/**
 * It calls
 * mission_interfaces__msg__ApproachInfo__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
void
mission_interfaces__msg__ApproachInfo__Sequence__fini(mission_interfaces__msg__ApproachInfo__Sequence * array);

/// Create array of msg/ApproachInfo messages.
/**
 * It allocates the memory for the array and calls
 * mission_interfaces__msg__ApproachInfo__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
mission_interfaces__msg__ApproachInfo__Sequence *
mission_interfaces__msg__ApproachInfo__Sequence__create(size_t size);

/// Destroy array of msg/ApproachInfo messages.
/**
 * It calls
 * mission_interfaces__msg__ApproachInfo__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
void
mission_interfaces__msg__ApproachInfo__Sequence__destroy(mission_interfaces__msg__ApproachInfo__Sequence * array);

/// Check for msg/ApproachInfo message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__Sequence__are_equal(const mission_interfaces__msg__ApproachInfo__Sequence * lhs, const mission_interfaces__msg__ApproachInfo__Sequence * rhs);

/// Copy an array of msg/ApproachInfo messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_mission_interfaces
bool
mission_interfaces__msg__ApproachInfo__Sequence__copy(
  const mission_interfaces__msg__ApproachInfo__Sequence * input,
  mission_interfaces__msg__ApproachInfo__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MISSION_INTERFACES__MSG__DETAIL__APPROACH_INFO__FUNCTIONS_H_

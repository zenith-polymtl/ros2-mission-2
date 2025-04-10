// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice
#include "mission_interfaces/srv/detail/get_pose__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
mission_interfaces__srv__GetPose_Request__init(mission_interfaces__srv__GetPose_Request * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
mission_interfaces__srv__GetPose_Request__fini(mission_interfaces__srv__GetPose_Request * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
mission_interfaces__srv__GetPose_Request__are_equal(const mission_interfaces__srv__GetPose_Request * lhs, const mission_interfaces__srv__GetPose_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // structure_needs_at_least_one_member
  if (lhs->structure_needs_at_least_one_member != rhs->structure_needs_at_least_one_member) {
    return false;
  }
  return true;
}

bool
mission_interfaces__srv__GetPose_Request__copy(
  const mission_interfaces__srv__GetPose_Request * input,
  mission_interfaces__srv__GetPose_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

mission_interfaces__srv__GetPose_Request *
mission_interfaces__srv__GetPose_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Request * msg = (mission_interfaces__srv__GetPose_Request *)allocator.allocate(sizeof(mission_interfaces__srv__GetPose_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(mission_interfaces__srv__GetPose_Request));
  bool success = mission_interfaces__srv__GetPose_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
mission_interfaces__srv__GetPose_Request__destroy(mission_interfaces__srv__GetPose_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    mission_interfaces__srv__GetPose_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
mission_interfaces__srv__GetPose_Request__Sequence__init(mission_interfaces__srv__GetPose_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Request * data = NULL;

  if (size) {
    data = (mission_interfaces__srv__GetPose_Request *)allocator.zero_allocate(size, sizeof(mission_interfaces__srv__GetPose_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = mission_interfaces__srv__GetPose_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        mission_interfaces__srv__GetPose_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
mission_interfaces__srv__GetPose_Request__Sequence__fini(mission_interfaces__srv__GetPose_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      mission_interfaces__srv__GetPose_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

mission_interfaces__srv__GetPose_Request__Sequence *
mission_interfaces__srv__GetPose_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Request__Sequence * array = (mission_interfaces__srv__GetPose_Request__Sequence *)allocator.allocate(sizeof(mission_interfaces__srv__GetPose_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = mission_interfaces__srv__GetPose_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
mission_interfaces__srv__GetPose_Request__Sequence__destroy(mission_interfaces__srv__GetPose_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    mission_interfaces__srv__GetPose_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
mission_interfaces__srv__GetPose_Request__Sequence__are_equal(const mission_interfaces__srv__GetPose_Request__Sequence * lhs, const mission_interfaces__srv__GetPose_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!mission_interfaces__srv__GetPose_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
mission_interfaces__srv__GetPose_Request__Sequence__copy(
  const mission_interfaces__srv__GetPose_Request__Sequence * input,
  mission_interfaces__srv__GetPose_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(mission_interfaces__srv__GetPose_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    mission_interfaces__srv__GetPose_Request * data =
      (mission_interfaces__srv__GetPose_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!mission_interfaces__srv__GetPose_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          mission_interfaces__srv__GetPose_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!mission_interfaces__srv__GetPose_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

bool
mission_interfaces__srv__GetPose_Response__init(mission_interfaces__srv__GetPose_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    mission_interfaces__srv__GetPose_Response__fini(msg);
    return false;
  }
  // position_x
  // position_y
  // position_z
  // orientation_x
  // orientation_y
  // orientation_z
  // orientation_w
  return true;
}

void
mission_interfaces__srv__GetPose_Response__fini(mission_interfaces__srv__GetPose_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
  // position_x
  // position_y
  // position_z
  // orientation_x
  // orientation_y
  // orientation_z
  // orientation_w
}

bool
mission_interfaces__srv__GetPose_Response__are_equal(const mission_interfaces__srv__GetPose_Response * lhs, const mission_interfaces__srv__GetPose_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  // position_x
  if (lhs->position_x != rhs->position_x) {
    return false;
  }
  // position_y
  if (lhs->position_y != rhs->position_y) {
    return false;
  }
  // position_z
  if (lhs->position_z != rhs->position_z) {
    return false;
  }
  // orientation_x
  if (lhs->orientation_x != rhs->orientation_x) {
    return false;
  }
  // orientation_y
  if (lhs->orientation_y != rhs->orientation_y) {
    return false;
  }
  // orientation_z
  if (lhs->orientation_z != rhs->orientation_z) {
    return false;
  }
  // orientation_w
  if (lhs->orientation_w != rhs->orientation_w) {
    return false;
  }
  return true;
}

bool
mission_interfaces__srv__GetPose_Response__copy(
  const mission_interfaces__srv__GetPose_Response * input,
  mission_interfaces__srv__GetPose_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  // position_x
  output->position_x = input->position_x;
  // position_y
  output->position_y = input->position_y;
  // position_z
  output->position_z = input->position_z;
  // orientation_x
  output->orientation_x = input->orientation_x;
  // orientation_y
  output->orientation_y = input->orientation_y;
  // orientation_z
  output->orientation_z = input->orientation_z;
  // orientation_w
  output->orientation_w = input->orientation_w;
  return true;
}

mission_interfaces__srv__GetPose_Response *
mission_interfaces__srv__GetPose_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Response * msg = (mission_interfaces__srv__GetPose_Response *)allocator.allocate(sizeof(mission_interfaces__srv__GetPose_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(mission_interfaces__srv__GetPose_Response));
  bool success = mission_interfaces__srv__GetPose_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
mission_interfaces__srv__GetPose_Response__destroy(mission_interfaces__srv__GetPose_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    mission_interfaces__srv__GetPose_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
mission_interfaces__srv__GetPose_Response__Sequence__init(mission_interfaces__srv__GetPose_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Response * data = NULL;

  if (size) {
    data = (mission_interfaces__srv__GetPose_Response *)allocator.zero_allocate(size, sizeof(mission_interfaces__srv__GetPose_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = mission_interfaces__srv__GetPose_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        mission_interfaces__srv__GetPose_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
mission_interfaces__srv__GetPose_Response__Sequence__fini(mission_interfaces__srv__GetPose_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      mission_interfaces__srv__GetPose_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

mission_interfaces__srv__GetPose_Response__Sequence *
mission_interfaces__srv__GetPose_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mission_interfaces__srv__GetPose_Response__Sequence * array = (mission_interfaces__srv__GetPose_Response__Sequence *)allocator.allocate(sizeof(mission_interfaces__srv__GetPose_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = mission_interfaces__srv__GetPose_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
mission_interfaces__srv__GetPose_Response__Sequence__destroy(mission_interfaces__srv__GetPose_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    mission_interfaces__srv__GetPose_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
mission_interfaces__srv__GetPose_Response__Sequence__are_equal(const mission_interfaces__srv__GetPose_Response__Sequence * lhs, const mission_interfaces__srv__GetPose_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!mission_interfaces__srv__GetPose_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
mission_interfaces__srv__GetPose_Response__Sequence__copy(
  const mission_interfaces__srv__GetPose_Response__Sequence * input,
  mission_interfaces__srv__GetPose_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(mission_interfaces__srv__GetPose_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    mission_interfaces__srv__GetPose_Response * data =
      (mission_interfaces__srv__GetPose_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!mission_interfaces__srv__GetPose_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          mission_interfaces__srv__GetPose_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!mission_interfaces__srv__GetPose_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}

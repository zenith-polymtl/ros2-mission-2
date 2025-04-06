// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from mission_interfaces:srv/GetPose.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "mission_interfaces/srv/detail/get_pose__rosidl_typesupport_introspection_c.h"
#include "mission_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "mission_interfaces/srv/detail/get_pose__functions.h"
#include "mission_interfaces/srv/detail/get_pose__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  mission_interfaces__srv__GetPose_Request__init(message_memory);
}

void mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_fini_function(void * message_memory)
{
  mission_interfaces__srv__GetPose_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_member_array[1] = {
  {
    "structure_needs_at_least_one_member",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Request, structure_needs_at_least_one_member),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_members = {
  "mission_interfaces__srv",  // message namespace
  "GetPose_Request",  // message name
  1,  // number of fields
  sizeof(mission_interfaces__srv__GetPose_Request),
  mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_member_array,  // message members
  mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_type_support_handle = {
  0,
  &mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_mission_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Request)() {
  if (!mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_type_support_handle.typesupport_identifier) {
    mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &mission_interfaces__srv__GetPose_Request__rosidl_typesupport_introspection_c__GetPose_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "mission_interfaces/srv/detail/get_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "mission_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "mission_interfaces/srv/detail/get_pose__functions.h"
// already included above
// #include "mission_interfaces/srv/detail/get_pose__struct.h"


// Include directives for member types
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  mission_interfaces__srv__GetPose_Response__init(message_memory);
}

void mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_fini_function(void * message_memory)
{
  mission_interfaces__srv__GetPose_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_member_array[9] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "position_x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, position_x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "position_y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, position_y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "position_z",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, position_z),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "orientation_x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, orientation_x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "orientation_y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, orientation_y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "orientation_z",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, orientation_z),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "orientation_w",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mission_interfaces__srv__GetPose_Response, orientation_w),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_members = {
  "mission_interfaces__srv",  // message namespace
  "GetPose_Response",  // message name
  9,  // number of fields
  sizeof(mission_interfaces__srv__GetPose_Response),
  mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_member_array,  // message members
  mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_type_support_handle = {
  0,
  &mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_mission_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Response)() {
  if (!mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_type_support_handle.typesupport_identifier) {
    mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &mission_interfaces__srv__GetPose_Response__rosidl_typesupport_introspection_c__GetPose_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "mission_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "mission_interfaces/srv/detail/get_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_members = {
  "mission_interfaces__srv",  // service namespace
  "GetPose",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_Request_message_type_support_handle,
  NULL  // response message
  // mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_Response_message_type_support_handle
};

static rosidl_service_type_support_t mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_type_support_handle = {
  0,
  &mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_mission_interfaces
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose)() {
  if (!mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_type_support_handle.typesupport_identifier) {
    mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mission_interfaces, srv, GetPose_Response)()->data;
  }

  return &mission_interfaces__srv__detail__get_pose__rosidl_typesupport_introspection_c__GetPose_service_type_support_handle;
}

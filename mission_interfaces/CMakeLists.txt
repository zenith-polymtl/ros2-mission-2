cmake_minimum_required(VERSION 3.8)
project(mission_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)


# Generate messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/GetPose.srv"
  "msg/ApproachInfo.msg"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# Export dependencies for downstream packages
ament_export_dependencies(rosidl_default_runtime)
ament_package()

cmake_minimum_required(VERSION 3.25)

project(xar_ck3_native_bridge VERSION 0.1.0 LANGUAGES CXX)

if(NOT WIN32)
  message(FATAL_ERROR "xar_ck3_native_bridge currently targets Windows only")
endif()

if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "xar_ck3_native_bridge must be built for x64")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(xar_bridge_protocol STATIC
  src/protocol.cpp
)
target_include_directories(xar_bridge_protocol PUBLIC include)
target_compile_definitions(xar_bridge_protocol PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

add_library(xar_bridge_injector STATIC
  src/injector.cpp
)
target_include_directories(xar_bridge_injector PUBLIC include)
target_compile_definitions(xar_bridge_injector PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

add_library(xar_ck3_bridge SHARED
  src/bridge.cpp
  src/ck3_11906.cpp
)
target_link_libraries(xar_ck3_bridge PRIVATE xar_bridge_protocol bcrypt)
target_compile_definitions(xar_ck3_bridge PRIVATE
  XAR_BRIDGE_VERSION="${PROJECT_VERSION}"
)
set_target_properties(xar_ck3_bridge PROPERTIES
  OUTPUT_NAME "xar_ck3_bridge"
)

add_executable(xar_ck3_bridge_host
  src/host.cpp
)
target_link_libraries(xar_ck3_bridge_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_attach_host
  src/attach_host.cpp
)
target_link_libraries(xar_ck3_bridge_attach_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_injector
  src/injector_main.cpp
)
target_link_libraries(xar_ck3_bridge_injector PRIVATE xar_bridge_injector)

add_executable(xar_ck3_bridge_target
  src/target.cpp
)

if(MSVC)
  foreach(target
      xar_bridge_protocol
      xar_bridge_injector
      xar_ck3_bridge
      xar_ck3_bridge_host
      xar_ck3_bridge_attach_host
      xar_ck3_bridge_injector
      xar_ck3_bridge_target)
    target_compile_options(${target} PRIVATE /W4 /permissive- /EHsc)
  endforeach()
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(xar_ck3_game_access_test
    src/ck3_11906.cpp
    src/ck3_11906_test.cpp
  )
  target_include_directories(xar_ck3_game_access_test PRIVATE include)
  target_link_libraries(xar_ck3_game_access_test PRIVATE bcrypt)
  target_compile_definitions(xar_ck3_game_access_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(xar_ck3_game_access_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_game_access_fixture
    COMMAND xar_ck3_game_access_test
  )

  add_test(
    NAME xar_ck3_native_bridge_suspended_injection
    COMMAND xar_ck3_bridge_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_suspended_injection
    PROPERTIES TIMEOUT 30)

  add_test(
    NAME xar_ck3_native_bridge_running_attach
    COMMAND xar_ck3_bridge_attach_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_running_attach
    PROPERTIES TIMEOUT 30)
endif()

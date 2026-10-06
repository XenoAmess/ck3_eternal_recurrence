cmake_minimum_required(VERSION 3.24)
project(xar_religion_observers_12004_first_fixture LANGUAGES CXX)
get_filename_component(XAR_RELIGION_12004_DEFAULT_ROOT
  "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
set(XAR_RELIGION_12004_SOURCE_ROOT "${XAR_RELIGION_12004_DEFAULT_ROOT}"
  CACHE PATH "Applied actual .4 religion candidate repository root")
set(XAR_RELIGION_12004_RUNTIME_LIBRARY "" CACHE FILEPATH
  "Root-built actual migrated xar_ck3_12002_runtime library")
if(NOT XAR_RELIGION_12004_RUNTIME_LIBRARY)
  message(FATAL_ERROR "Pass the real runtime library with all four religion query flags enabled")
endif()
set(native "${XAR_RELIGION_12004_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_library(xar_religion_12004_actual_runtime STATIC IMPORTED)
set_target_properties(xar_religion_12004_actual_runtime PROPERTIES
  IMPORTED_LOCATION "${XAR_RELIGION_12004_RUNTIME_LIBRARY}")
add_executable(xar_ck3_12004_religion_bindings_mailbox_test
  "${native}/src/protocol.cpp"
  "${native}/src/ck3_12004_religion_bindings_mailbox_test.cpp")
target_include_directories(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
  "${native}/include")
target_compile_definitions(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1=1
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1)
target_link_libraries(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
  xar_religion_12004_actual_runtime user32 bcrypt)
if(MSVC)
  target_compile_options(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
    /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
  target_link_options(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
    /OPT:REF)
endif()
enable_testing()
add_test(NAME xar_ck3_12004_religion_bindings_mailbox_test
  COMMAND xar_ck3_12004_religion_bindings_mailbox_test
    "${CMAKE_BINARY_DIR}/religion-12004-wire")

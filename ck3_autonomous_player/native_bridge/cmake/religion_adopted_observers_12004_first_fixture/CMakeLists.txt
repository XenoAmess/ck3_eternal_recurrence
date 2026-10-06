cmake_minimum_required(VERSION 3.24)
project(xar_religion_adopted_observers_12004_first_fixture LANGUAGES CXX)
get_filename_component(XAR_RELIGION_12004_ADOPTED_DEFAULT_ROOT
  "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
set(XAR_RELIGION_12004_ADOPTED_SOURCE_ROOT "${XAR_RELIGION_12004_ADOPTED_DEFAULT_ROOT}"
  CACHE PATH "Applied actual .4 religion adopted restoration repository root")
set(XAR_RELIGION_12004_ADOPTED_RUNTIME_LIBRARY "" CACHE FILEPATH
  "Root-built actual migrated runtime with the existing adopted query options")
if(NOT XAR_RELIGION_12004_ADOPTED_RUNTIME_LIBRARY)
  message(FATAL_ERROR "Pass the actual migrated runtime library with all eight query options enabled")
endif()
set(native "${XAR_RELIGION_12004_ADOPTED_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
add_library(xar_religion_12004_adopted_actual_runtime STATIC IMPORTED)
set_target_properties(xar_religion_12004_adopted_actual_runtime PROPERTIES
  IMPORTED_LOCATION "${XAR_RELIGION_12004_ADOPTED_RUNTIME_LIBRARY}")
enable_testing()
foreach(family IN ITEMS costs_eligibility draft_bindings adopted_observers)
  set(target "xar_ck3_12004_religion_${family}_mailbox_test")
  add_executable(${target}
    "${native}/src/protocol.cpp"
    "${native}/src/ck3_12004_religion_${family}_mailbox_test.cpp")
  target_include_directories(${target} PRIVATE "${native}/include")
  target_compile_features(${target} PRIVATE cxx_std_20)
  target_compile_definitions(${target} PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1=1)
  target_link_libraries(${target} PRIVATE
    xar_religion_12004_adopted_actual_runtime user32 bcrypt)
  if(MSVC)
    target_compile_options(${target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
    target_link_options(${target} PRIVATE /OPT:REF)
  endif()
  add_test(NAME ${target} COMMAND ${target}
    "${CMAKE_BINARY_DIR}/religion-12004-adopted-wire")
endforeach()

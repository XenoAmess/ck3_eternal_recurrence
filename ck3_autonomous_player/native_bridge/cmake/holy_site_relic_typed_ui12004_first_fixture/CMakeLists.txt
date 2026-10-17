cmake_minimum_required(VERSION 3.24)
project(xar_relic_typed_ui12004_first_fixture LANGUAGES CXX)
if(NOT XAR_REPO_SOURCE_ROOT OR NOT EXISTS "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004.hpp")
 message(FATAL_ERROR "Explicit XAR_REPO_SOURCE_ROOT is required; no source tree copy")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OBJECT_PATH_MAX 240)
get_filename_component(_native "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(_base "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
if(MSVC AND XAR_RELIC_PURE_FIXTURE_SOURCE)
 add_executable(xar_relic_ui12004_isolated_packet_test
  "${_native}/src/ck3_12004_holy_site_relic_actions.cpp"
  "${_native}/src/ck3_12004_holy_site_relic_actions_json.cpp"
  "${_native}/src/holy_site_relic_request12004.cpp"
  "${_native}/src/ck3_12004_holy_site_relic_actions_test.cpp"
  "${XAR_RELIC_PURE_FIXTURE_SOURCE}"
  "${_base}/src/protocol.cpp")
 target_include_directories(xar_relic_ui12004_isolated_packet_test PRIVATE "${_native}/include" "${_base}/include" "${_base}/src")
 target_compile_definitions(xar_relic_ui12004_isolated_packet_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004=1 XAR_RELIC_FULL_UI_PACKET_FIXTURE=1)
 target_compile_options(xar_relic_ui12004_isolated_packet_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
endif()
add_executable(xar_relic_ui12004_test
 "${_native}/src/ck3_12004_holy_site_relic_actions.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_actions_json.cpp"
 "${_native}/src/holy_site_relic_request12004.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_actions_test.cpp"
 "${_base}/src/protocol.cpp")
# New navigation hooks compile without linking or touching another runtime.
add_library(xar_relic_ui12004_nav_compile OBJECT
 "${_native}/src/holy_site_relic_navigation12004.cpp"
 "${_native}/src/ingame_ui_navigation_v1.cpp")
add_library(xar_relic_ui12004_action_nav_compile OBJECT "${_native}/src/holy_site_relic_navigation12004.cpp")
target_compile_definitions(xar_relic_ui12004_action_nav_compile PRIVATE XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004=1)
foreach(_target xar_relic_ui12004_test xar_relic_ui12004_nav_compile xar_relic_ui12004_action_nav_compile)
 target_include_directories(${_target} PRIVATE "${_native}/include" "${_base}/include" "${_base}/src")
 target_compile_definitions(${_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004=1)
 if(MSVC)
  target_compile_options(${_target} PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
 endif()
endforeach()
if(XAR_ACTION_CONTEXT_SOURCE_ROOT)
 add_library(xar_relic_ui12004_preview_adapter_compile OBJECT
  "${XAR_ACTION_CONTEXT_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/holy_site_relic_action_preview_adapter12004.cpp")
 target_include_directories(xar_relic_ui12004_preview_adapter_compile PRIVATE
  "${_native}/include" "${XAR_ACTION_CONTEXT_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include" "${_base}/include")
 target_compile_definitions(xar_relic_ui12004_preview_adapter_compile PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
 if(MSVC)
  target_compile_options(xar_relic_ui12004_preview_adapter_compile PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
 endif()
endif()

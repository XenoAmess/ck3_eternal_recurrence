cmake_minimum_required(VERSION 3.24)
project(relic_owner_binding_focused12004 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OBJECT_PATH_MAX 240)
if(NOT XAR_UI_BASE_STAGE OR NOT XAR_REPO_SOURCE_ROOT OR NOT XAR_PURE_FORMATTER_SOURCE)
 message(FATAL_ERROR "Explicit small source references are required; no complete tree copy")
endif()
get_filename_component(_native "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(_old "${XAR_UI_BASE_STAGE}/ck3_autonomous_player/native_bridge")
set(_base "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
add_executable(xar_relic_owner12004_test
 "${_native}/src/ck3_12004_holy_site_relic_actions.cpp"
 "${_native}/src/holy_site_relic_owner_binding_focused_test.cpp"
 "${_old}/src/ck3_12004_holy_site_relic_actions_json.cpp"
 "${_old}/src/holy_site_relic_request12004.cpp"
 "${XAR_PURE_FORMATTER_SOURCE}"
 "${_base}/src/protocol.cpp")
target_include_directories(xar_relic_owner12004_test PRIVATE "${_old}/include" "${_base}/include" "${_old}/src")
target_compile_definitions(xar_relic_owner12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
 XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004=1 XAR_RELIC_FULL_UI_PACKET_FIXTURE=1)
if(MSVC)
 target_compile_options(xar_relic_owner12004_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
endif()

cmake_minimum_required(VERSION 3.24)
project(xar_holy_site_relic_permissions_fixture LANGUAGES CXX)
set(XAR_REPO_SOURCE_ROOT "" CACHE PATH "Existing source root supplying unchanged bridge headers and model binder")
if(NOT EXISTS "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_holy_site_relic_context.hpp")
 message(FATAL_ERROR "Explicit XAR_REPO_SOURCE_ROOT required")
endif()
get_filename_component(_candidate_native "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
add_executable(xar_ck3_12004_holy_site_relic_permissions_test
 "${_candidate_native}/src/ck3_12004_holy_site_relic_permissions_test.cpp"
 "${_candidate_native}/src/ck3_12004_holy_site_relic_permissions.cpp"
 "${_candidate_native}/src/ck3_12004_holy_site_relic_permissions_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_context.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_character_modifier_2c4d1d0_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/conception_modifier_context_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_scaled_key_2c4d530_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp")
target_include_directories(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE
 "${_candidate_native}/include" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include")
target_compile_features(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE cxx_std_20)
if(WIN32)
 target_compile_definitions(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
endif()
if(MSVC)
 target_compile_options(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
endif()

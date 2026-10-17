cmake_minimum_required(VERSION 3.24)
project(xar_relic_action_context_fixture LANGUAGES CXX)
set(XAR_REPO_SOURCE_ROOT "" CACHE PATH "Existing source supplying immutable permission/model files")
set(XAR_PERMISSIONS_FIXTURE_SOURCE "" CACHE PATH "Existing frozen owned-memory test constructor source")
get_filename_component(_native "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
if(NOT EXISTS "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_permissions.cpp" OR NOT EXISTS "${XAR_PERMISSIONS_FIXTURE_SOURCE}/ck3_12004_holy_site_relic_permissions_test.cpp")
 message(FATAL_ERROR "Explicit existing production source and frozen input fixture required")
endif()
add_executable(xar_ck3_12004_holy_site_relic_action_context_test
 "${_native}/src/ck3_12004_holy_site_relic_action_context_test.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_action_context.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_action_context_json.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_permissions.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_permissions_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_context.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_character_modifier_2c4d1d0_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/conception_modifier_context_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_scaled_key_2c4d530_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp")
target_include_directories(xar_ck3_12004_holy_site_relic_action_context_test PRIVATE "${_native}/include" "${XAR_PERMISSIONS_FIXTURE_SOURCE}" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include")
target_compile_features(xar_ck3_12004_holy_site_relic_action_context_test PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_holy_site_relic_action_context_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
target_compile_options(xar_ck3_12004_holy_site_relic_action_context_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
target_link_libraries(xar_ck3_12004_holy_site_relic_action_context_test PRIVATE bcrypt)
add_library(xar_relic_action_context_mailbox_compile OBJECT "${_native}/src/ck3_12002_religion_mailbox.cpp")
target_include_directories(xar_relic_action_context_mailbox_compile PRIVATE "${_native}/include" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src")
target_compile_features(xar_relic_action_context_mailbox_compile PRIVATE cxx_std_20)
target_compile_definitions(xar_relic_action_context_mailbox_compile PRIVATE XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1 NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
target_compile_options(xar_relic_action_context_mailbox_compile PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
add_executable(xar_ck3_12004_holy_site_relic_window_binding_test
 "${_native}/src/ck3_12004_holy_site_relic_window_binding_test.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_action_context.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_action_context_json.cpp"
 "${_native}/src/ck3_12004_holy_site_relic_permissions.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_permissions_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_context.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate_json.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_character_modifier_2c4d1d0_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/conception_modifier_context_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/construction_scaled_key_2c4d530_12004.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix.cpp"
 "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp")
target_include_directories(xar_ck3_12004_holy_site_relic_window_binding_test PRIVATE "${_native}/include" "${XAR_PERMISSIONS_FIXTURE_SOURCE}" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include")
target_compile_features(xar_ck3_12004_holy_site_relic_window_binding_test PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_holy_site_relic_window_binding_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
target_compile_options(xar_ck3_12004_holy_site_relic_window_binding_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
target_link_libraries(xar_ck3_12004_holy_site_relic_window_binding_test PRIVATE bcrypt)

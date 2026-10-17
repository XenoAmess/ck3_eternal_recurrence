cmake_minimum_required(VERSION 3.24)
project(xar_holy_site_creation12004_first LANGUAGES CXX)
set(XAR_REPO_SOURCE_ROOT "" CACHE PATH "Unchanged existing bridge headers")
if(NOT EXISTS "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_context.hpp")
 message(FATAL_ERROR "Explicit existing source root required")
endif()
get_filename_component(_native "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
add_executable(xar_holy_site_creation12004_test
 "${_native}/src/holy_site_creation12004.cpp"
 "${_native}/src/holy_site_creation12004_json.cpp"
 "${_native}/tests/holy_site_creation12004_test.cpp")
target_include_directories(xar_holy_site_creation12004_test PRIVATE
 "${_native}/include" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include")
target_compile_features(xar_holy_site_creation12004_test PRIVATE cxx_std_20)
target_compile_definitions(xar_holy_site_creation12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
if(MSVC)
 target_compile_options(xar_holy_site_creation12004_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
endif()

# Compile only the newly hooked existing mailbox plus the new owner adapter.
# No old test target, bridge, game EXE or runtime package is built here.
add_library(xar_holy_site_creation12004_mailbox_compile OBJECT
 "${_native}/src/ck3_12002_religion_mailbox.cpp"
 "${_native}/src/holy_site_creation12004_mailbox.cpp")
target_include_directories(xar_holy_site_creation12004_mailbox_compile PRIVATE
 "${_native}/include" "${XAR_REPO_SOURCE_ROOT}/ck3_autonomous_player/native_bridge/include")
target_compile_features(xar_holy_site_creation12004_mailbox_compile PRIVATE cxx_std_20)
target_compile_definitions(xar_holy_site_creation12004_mailbox_compile PRIVATE
 NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
 XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
 XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1=1)
if(MSVC)
 target_compile_options(xar_holy_site_creation12004_mailbox_compile PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
endif()

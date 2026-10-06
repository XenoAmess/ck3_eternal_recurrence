cmake_minimum_required(VERSION 3.24)
project(xar_target_rite_tenet_first_fixture LANGUAGES CXX)
get_filename_component(XAR_TARGET_TENET_DEFAULT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../.." ABSOLUTE)
set(XAR_TARGET_TENET_SOURCE_ROOT "${XAR_TARGET_TENET_DEFAULT_ROOT}" CACHE PATH "Applied candidate repository root")
set(native "${XAR_TARGET_TENET_SOURCE_ROOT}/ck3_autonomous_player/native_bridge")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(xar_ck3_12003_target_rite_tenet_comparison_mailbox_test
  "${native}/src/protocol.cpp"
  "${native}/src/ck3_12002.cpp"
  "${native}/src/ck3_12002_query_mailbox.cpp"
  "${native}/src/ck3_12003_abi_profile.cpp"
  "${native}/src/ck3_12003_adapter.cpp"
  "${native}/src/main_thread_query_mailbox_v1.cpp"
  "${native}/src/ck3_12002_religion_context.cpp"
  "${native}/src/religion_doctrine12002_tenet_rows.cpp"
  "${native}/src/ck3_12003_target_rite_tenet_comparison.cpp"
  "${native}/src/religion_reform12002_tenet_sources.cpp"
  "${native}/src/religion_reform12002_window.cpp"
  "${native}/src/religion_doctrine12002_tenet_rows_mailbox.cpp"
  "${native}/src/ck3_12003_target_rite_tenet_comparison_mailbox_test.cpp")
target_include_directories(xar_ck3_12003_target_rite_tenet_comparison_mailbox_test PRIVATE "${native}/include")
target_link_libraries(xar_ck3_12003_target_rite_tenet_comparison_mailbox_test PRIVATE user32)
target_compile_definitions(xar_ck3_12003_target_rite_tenet_comparison_mailbox_test PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1
  XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1)
if(MSVC)
  target_compile_options(xar_ck3_12003_target_rite_tenet_comparison_mailbox_test PRIVATE
    /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
endif()
enable_testing()
add_test(NAME xar_ck3_12003_target_rite_tenet_comparison_mailbox_test
  COMMAND xar_ck3_12003_target_rite_tenet_comparison_mailbox_test
    "${CMAKE_BINARY_DIR}/target-rite-tenet-comparison-wire")

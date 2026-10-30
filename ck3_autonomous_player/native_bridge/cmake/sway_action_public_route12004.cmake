# Public Sway action Handler -> registered slot58 -> real queue/pump -> shared action -> fresh receipt/serializer.
# Native bindings/callbacks are owned-memory test seams; Game and actual4 image factory are not exercised.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_sway_action_public_route12004_test
    tests/sway_action_public_route12004_test.cpp
    src/ck3_12002.cpp
    src/ck3_12002_context.cpp
    src/ck3_12002_commands.cpp
    src/active_scheme_semantic_action_v1_private.cpp
    src/ck3_12002_sway_command.cpp
    src/ck3_12002_sway_state.cpp
    src/ck3_12002_sway_handler.cpp
    src/ck3_12002_sway_mailbox.cpp
    src/ck3_12002_sway_serializer.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/protocol.cpp
  )
  target_include_directories(xar_ck3_sway_action_public_route12004_test BEFORE PRIVATE include research)
  target_compile_features(xar_ck3_sway_action_public_route12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_action_public_route12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_link_libraries(xar_ck3_sway_action_public_route12004_test PRIVATE kernel32 user32 version)
  if(MSVC)
    target_compile_options(xar_ck3_sway_action_public_route12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    target_link_options(xar_ck3_sway_action_public_route12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  endif()
  add_test(NAME xar_ck3_sway_action_public_route12004
    COMMAND xar_ck3_sway_action_public_route12004_test "${CMAKE_CURRENT_BINARY_DIR}/sway-action-public-route12004-wire")
  set_tests_properties(xar_ck3_sway_action_public_route12004 PROPERTIES TIMEOUT 30)
endif()

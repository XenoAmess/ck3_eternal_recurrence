
# Real current4 signed reason ingress; owned-memory native I/O, no CK3.
if(BUILD_TESTING AND WIN32 AND MSVC)
  add_executable(xar_sway_invalidation_reason_signed12004_test
    tests/sway_invalidation_reason_signed12004_test.cpp
    src/sway_invalidation_branch_12004.cpp
    src/sway_complete_branch_12004.cpp
    src/ck3_12002_sway_completion_execution.cpp
    src/ck3_12002_sway_completion_invalidation_reason.cpp
    src/ck3_12002_sway_completion_invalidation_reason_handler.cpp
    src/ck3_12002_sway_completion_invalidation_reason_mailbox.cpp
    src/ck3_12002_sway_completion_invalidation_reason_serializer.cpp
    src/ck3_12002.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/protocol.cpp)
  target_include_directories(xar_sway_invalidation_reason_signed12004_test PRIVATE include research)
  target_compile_features(xar_sway_invalidation_reason_signed12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_sway_invalidation_reason_signed12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_compile_options(xar_sway_invalidation_reason_signed12004_test PRIVATE
    /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
  target_link_options(xar_sway_invalidation_reason_signed12004_test PRIVATE /OPT:REF)
  target_link_libraries(xar_sway_invalidation_reason_signed12004_test PRIVATE user32)
  add_test(NAME xar_sway_invalidation_reason_signed12004_test
    COMMAND xar_sway_invalidation_reason_signed12004_test "${CMAKE_CURRENT_BINARY_DIR}/sway-invalidation-signed-wire")
  set_tests_properties(xar_sway_invalidation_reason_signed12004_test PROPERTIES TIMEOUT 30)
endif()

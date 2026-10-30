# Public material handler -> real queue/pump -> entry/read/finish -> caller JSON.
# Image binding is a test-only owned-memory seam. All route code is production.
if(BUILD_TESTING AND WIN32)
  add_library(xar_ck3_sway_opinion_mailbox_factory12004_test OBJECT
    src/ck3_12004_sway.cpp)
  target_compile_definitions(xar_ck3_sway_opinion_mailbox_factory12004_test PRIVATE
    BindSwayOutcomeOpinionImage12004=RealBindSwayOutcomeOpinionImage12004)

  add_executable(xar_ck3_sway_opinion_mailbox_route12004_test
    tests/sway_opinion_mailbox_route12004_test.cpp
    src/ck3_12002_sway_outcome.cpp
    src/ck3_12002_sway_outcome_mailbox.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12002.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/protocol.cpp
    $<TARGET_OBJECTS:xar_ck3_sway_opinion_mailbox_factory12004_test>)
  foreach(_target IN ITEMS xar_ck3_sway_opinion_mailbox_factory12004_test
      xar_ck3_sway_opinion_mailbox_route12004_test)
    target_include_directories(${_target} BEFORE PRIVATE include research)
    target_compile_features(${_target} PRIVATE cxx_std_20)
    target_compile_definitions(${_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
    if(MSVC)
      target_compile_options(${_target} PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    endif()
  endforeach()
  target_link_libraries(xar_ck3_sway_opinion_mailbox_route12004_test PRIVATE user32)
  if(MSVC)
    target_link_options(xar_ck3_sway_opinion_mailbox_route12004_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_sway_opinion_mailbox_route12004
    COMMAND xar_ck3_sway_opinion_mailbox_route12004_test
      "${CMAKE_CURRENT_BINARY_DIR}/sway-opinion-mailbox-route12004-wire")
  set_tests_properties(xar_ck3_sway_opinion_mailbox_route12004 PROPERTIES TIMEOUT 30)
endif()

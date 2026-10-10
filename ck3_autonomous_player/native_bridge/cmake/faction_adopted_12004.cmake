# SOURCE / NOTRUN. Entry includes after the existing runtime and bridge targets.
# The default event-window binder reaches this read-only environment binder
# even when the independent private faction query and gift route stay OFF.
target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_12004_faction_alerts.cpp)
if(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE src/ck3_12004_faction_mailbox.cpp)
endif()
if(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_campaign_root_faction.cpp
    src/ck3_12004_gift_opinion.cpp
    src/ck3_12004_faction_gift.cpp)
  target_sources(xar_ck3_bridge PRIVATE src/ck3_12004_faction_gift_router.cpp)
endif()
if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  add_executable(xar_ck3_12004_faction_adopted_whole_test
    tests/ck3_12004_faction_adopted_whole_test.cpp
    src/ck3_12004_faction_mailbox.cpp
    src/ck3_12004_faction_gift_router.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/faction_gift_mitigation_action_v1.cpp)
  target_link_libraries(xar_ck3_12004_faction_adopted_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32)
  target_include_directories(xar_ck3_12004_faction_adopted_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_faction_adopted_whole_test PRIVATE cxx_std_20)
  # Substitute only the synthetic transport boundary. The production typed
  # collectors, whole handlers, envelope and serializers are linked unchanged.
  target_compile_definitions(xar_ck3_12004_faction_adopted_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    TrySubmitMainThreadQueryV1=FactionAdoptedFixtureSubmit12004
    WaitForMainThreadQueryV1=FactionAdoptedFixtureWait12004
    ReclaimMainThreadQueryV1=FactionAdoptedFixtureReclaim12004)
  if(MSVC)
    target_compile_options(xar_ck3_12004_faction_adopted_whole_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_faction_adopted_whole
    COMMAND xar_ck3_12004_faction_adopted_whole_test
      "${CMAKE_CURRENT_BINARY_DIR}/faction-adopted-12004-whole")

  # New continuation worlds only; the qualified original matrix is not run.
  add_executable(xar_ck3_12004_faction_candidate_continue_whole_test
    tests/ck3_12004_faction_candidate_continue_whole_test.cpp
    src/ck3_12004_faction_mailbox.cpp
    src/ck3_12004_faction_gift_router.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/faction_gift_mitigation_action_v1.cpp)
  target_link_libraries(xar_ck3_12004_faction_candidate_continue_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32)
  target_include_directories(xar_ck3_12004_faction_candidate_continue_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_faction_candidate_continue_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_faction_candidate_continue_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    TrySubmitMainThreadQueryV1=FactionAdoptedFixtureSubmit12004
    WaitForMainThreadQueryV1=FactionAdoptedFixtureWait12004
    ReclaimMainThreadQueryV1=FactionAdoptedFixtureReclaim12004)
  if(MSVC)
    target_compile_options(xar_ck3_12004_faction_candidate_continue_whole_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_faction_candidate_continue_whole
    COMMAND xar_ck3_12004_faction_candidate_continue_whole_test
      "${CMAKE_CURRENT_BINARY_DIR}/faction-candidate-continue-12004-whole")
endif()

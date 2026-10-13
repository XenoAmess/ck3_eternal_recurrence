# Use the same real Bridge closure as fixture_real_link_closure_12004.cmake.
# Only the three new danger-order worlds run; old fixture main is not invoked.
if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  add_executable(xar_ck3_12004_faction_danger_priority_whole_test
    tests/ck3_12004_faction_danger_priority_whole_test.cpp
    src/ck3_12004_faction_mailbox.cpp
    src/ck3_12004_faction_gift_router.cpp)
  # Keep the two handler TUs under the fixture's transport aliases; all other
  # providers come from the actual Bridge object set without source duplicates.
  target_sources(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE
    "$<FILTER:$<TARGET_OBJECTS:xar_ck3_bridge>,EXCLUDE,(^|[/\\\\])ck3_12004_faction_(mailbox|gift_router)[.]cpp[.](obj|o)$>")
  target_link_libraries(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    TrySubmitMainThreadQueryV1=FactionAdoptedFixtureSubmit12004
    WaitForMainThreadQueryV1=FactionAdoptedFixtureWait12004
    ReclaimMainThreadQueryV1=FactionAdoptedFixtureReclaim12004)
  if(MSVC)
    target_compile_options(xar_ck3_12004_faction_danger_priority_whole_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_faction_danger_priority_whole
    COMMAND xar_ck3_12004_faction_danger_priority_whole_test
      "${CMAKE_CURRENT_BINARY_DIR}/faction-danger-priority-12004-whole")
endif()

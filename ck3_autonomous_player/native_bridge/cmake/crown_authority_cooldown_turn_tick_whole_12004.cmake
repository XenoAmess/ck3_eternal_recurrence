# New TurnTick companion FIRST only; the historical law-wire main is not run.
if(NOT BUILD_TESTING OR NOT WIN32 OR
   NOT XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
  return()
endif()
if(TARGET xar_crown_authority_cooldown_turn_tick_whole_fixture_12004)
  return()
endif()

set(XAR_CROWN_TURN_TICK_WHOLE_OUTPUT_DIR
    "${CMAKE_CURRENT_BINARY_DIR}/crown_turn_tick_12004_new_whole_wires"
    CACHE PATH "Output for only the six new TurnTick cases and same-readback legacy wire")
add_executable(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
    "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12002_realm_law_wire_test.cpp"
    $<TARGET_OBJECTS:xar_ck3_bridge>)
target_include_directories(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
    PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../include")
target_compile_features(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
    PRIVATE cxx_std_20)
target_compile_definitions(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
target_link_libraries(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
    PRIVATE xar_bridge_protocol xar_ck3_12002_runtime bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
if(MSVC)
  target_compile_options(xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
      PRIVATE /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
endif()
add_test(NAME crown_authority_cooldown_turn_tick_whole_fixture_12004
    COMMAND xar_crown_authority_cooldown_turn_tick_whole_fixture_12004
      --turn-tick-context-wire-dir "${XAR_CROWN_TURN_TICK_WHOLE_OUTPUT_DIR}")

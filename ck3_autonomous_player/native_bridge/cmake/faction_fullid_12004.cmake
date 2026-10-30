# Full faction identity uses its own signed public / raw private domain.
if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  set(target xar_ck3_12004_faction_fullid_whole_test)
  # Keep the production whole serializer in its original mailbox TU.
  # The public legacy Handle path is outside this fixture and aborts if entered.
  # These providers are the exact existing 16-object narrow fixture closure.
  add_executable(${target}
    tests/faction_fullid/faction_fullid_whole09.cpp
    tests/faction_fullid/faction_fullid_legacy_abort129.cpp
    src/ck3_12004_faction_gift_router.cpp
    src/ck3_12004_faction_mailbox.cpp
    src/ck3_12002_faction_alerts.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/faction_gift_mitigation_action_v1.cpp
    src/current_first_heir_relationship_v1.cpp
    src/observed_heir_marriage_private_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_action_v1.cpp
    src/religion_ui12004.cpp
    src/religion_ui12004_navigation.cpp
    src/appointment_window_snapshot_v1.cpp
    src/holy_site_relic_navigation12004.cpp
    src/ck3_12004_holy_site_relic_actions_json.cpp
    src/holy_site_relic_request12004.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/appointment_character_level12004.cpp
    src/ck3_12004_holy_site_relic_actions.cpp
    src/ck3_12004_holy_site_ui.cpp
    src/ck3_12004_holy_site_adoption_entry.cpp
    src/holy_site_relic_action_preview_adapter12004.cpp)
  target_link_libraries(${target} PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32)
  target_include_directories(${target} PRIVATE include src research)
  target_compile_features(${target} PRIVATE cxx_std_20)
  target_compile_definitions(${target} PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    TrySubmitMainThreadQueryV1=FactionIdentityFixtureSubmit12004
    WaitForMainThreadQueryV1=FactionIdentityFixtureWait12004
    ReclaimMainThreadQueryV1=FactionIdentityFixtureReclaim12004)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG /utf-8 /Gy)
    target_link_options(${target} PRIVATE /OPT:REF /OPT:ICF)
  endif()
  set(raw_zero 0)
  set(raw_min 2147483648)
  set(raw_generation81 2164260864)
  set(raw_high 4278190080)
  set(raw_mixed 2147483648)
  set(raw_stale_zero 0)
  set(raw_stale_min 2147483648)
  set(raw_stale_generation81 2164260864)
  set(raw_stale_high 4278190080)
  set(raw_absent 4294967295)
  foreach(case IN ITEMS zero min generation81 high mixed stale_zero stale_min stale_generation81 stale_high absent)
    set(mode normal)
    if(case STREQUAL "mixed")
      set(mode mixed)
    elseif(case MATCHES "^stale_")
      set(mode stale)
    endif()
    add_test(NAME xar_ck3_12004_faction_fullid_${case}
      COMMAND ${target} ${raw_${case}} ${mode}
        "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/${case}")
  endforeach()
endif()

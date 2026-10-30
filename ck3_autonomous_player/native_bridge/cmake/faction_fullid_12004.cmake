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
    tests/faction_fullid/faction_fullid_ci_main133.cpp
    tests/faction_fullid/faction_fullid_legacy_abort129.cpp
    tests/faction_fullid/faction_fullid_native_liege17.cpp
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
    XAR_CK3_FACTION_FULLID_ENTRY=FactionFullIdTargetingMain09
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
  # County joined/exposure scenarios share this target and native allocator assets.
  foreach(case IN ITEMS fid-zero fid-zero-stale fid-min fid-min-stale fid-81 fid-81-stale fid-ff fid-ff-stale joined-absent joined-duplicate title-zero joined-empty joined-mixed)
    add_test(NAME xar_ck3_12004_faction_fullid_county_${case}
      COMMAND ${target} --county ${case}
        "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/county/${case}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/faction_fullid/native-allocator-assets")
  endforeach()
  # Character cases use the same fixture TU and original whole serializer.
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-actor-min
    COMMAND ${target} --character-public 2147483648 67108866 leader
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-actor-min")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-actor-zero
    COMMAND ${target} --character-public 0 67108866 leader
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-actor-zero")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-leader-min
    COMMAND ${target} --character-public 50331649 2147483648 leader
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-leader-min")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-leader-zero
    COMMAND ${target} --character-public 50331649 0 leader
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-leader-zero")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-member-min
    COMMAND ${target} --character-public 50331649 2147483648 member
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-member-min")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-member-zero
    COMMAND ${target} --character-public 50331649 0 member
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-member-zero")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_candidate-mixed-members
    COMMAND ${target} --character-public 50331649 2147483648 mixed-members
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/candidate-mixed-members")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-absent-actor
    COMMAND ${target} --character-public 0 67108866 absent-actor
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-absent-actor")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-absent-member
    COMMAND ${target} --character-public 50331649 0 absent-member
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-absent-member")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-duplicate-member
    COMMAND ${target} --character-public 50331649 0 duplicate-member
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-duplicate-member")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-stale-actor-min
    COMMAND ${target} --character-public 2147483648 67108866 stale-actor
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-stale-actor-min")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-stale-actor-zero
    COMMAND ${target} --character-public 0 67108866 stale-actor
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-stale-actor-zero")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-stale-recipient-min
    COMMAND ${target} --character-public 50331649 2147483648 stale-recipient
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-stale-recipient-min")
  add_test(NAME xar_ck3_12004_faction_fullid_character_public_control-stale-recipient-zero
    COMMAND ${target} --character-public 50331649 0 stale-recipient
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/character-public/control-stale-recipient-zero")
  # Surrender leader identity and the unchanged positive war domain.
  add_test(NAME xar_ck3_12004_faction_fullid_surrender_leader-zero
    COMMAND ${target} --character-surrender 0 ordinary
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/surrender/leader-zero")
  add_test(NAME xar_ck3_12004_faction_fullid_surrender_leader-min
    COMMAND ${target} --character-surrender 2147483648 ordinary
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/surrender/leader-min")
  add_test(NAME xar_ck3_12004_faction_fullid_surrender_war-zero
    COMMAND ${target} --character-surrender 0 war-zero
      "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/surrender/war-zero")
  # Native liege CI137 entry
  foreach(selector IN ITEMS holder-zero top-min roundtrip-refusal)
    add_test(NAME xar_ck3_12004_faction_fullid_native_liege_${selector}
      COMMAND ${target} --native-liege ${selector}
        "${CMAKE_CURRENT_BINARY_DIR}/faction-fullid/native-liege/${selector}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/faction_fullid/native-allocator-assets"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/faction_fullid/native-liege-assets/new-028BFC50-028BFCC6.bin")
  endforeach()
endif()
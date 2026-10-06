# Adopted actual-.4 domains: source registration and new fixture recipes only.
# Entry includes this once after Runtime/Protocol/Bridge, CTest and the existing
# Snapshot/Army/base-religion/Commander leaves. Formal qualification is Root-only.
# Existing 117 option settings are unchanged; this leaf defines no feature option.
#
# The Snapshot foundation already registers family_relationships and Commander.
# Owned domain leaves below register their own religion/holy-war/prisoner TUs.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_hired_troop_shared_bindings.cpp
  src/ck3_12004_holy_order_bindings.cpp
  src/ck3_12004_mercenary_bindings.cpp
  src/ck3_12004_battle.cpp
  src/ck3_12004_battle_journal.cpp
  src/ck3_12004_war.cpp
  src/ck3_12004_diplomacy.cpp
  src/ck3_12004_war_cash_claim_terms.cpp
  src/ck3_12004_war_declarations.cpp
  src/ck3_12004_family.cpp
  src/ck3_12004_family_subject.cpp
  src/ck3_12004_family_ranked.cpp
  src/ck3_12004_family_obligations_alliance.cpp
  src/ck3_12004_family_break_penalty.cpp
  src/ck3_12004_family_actions.cpp
  src/ck3_12004_phase_character.cpp
  src/ck3_12004_gift_opinion.cpp
  src/ck3_12004_epidemic.cpp
  src/ck3_12004_succession_modal.cpp
  src/ck3_12004_frontend_bookmark.cpp
  src/frontend_bookmark_model_result_v1.cpp)

# Keep the literal owned registration/fixture declarations, in dependency order.
include("${CMAKE_CURRENT_LIST_DIR}/religion_adopted_observers_12004.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/ordinary_holy_war_12004_first_fixture.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/prisoner_collection_12004.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/prisoner_ransom_action_12004.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/death_succession_modal_whole_fixture_12004.cmake")

# External Sway recipe projected from ROOT-ENTRY-SWAY.cmake, unchanged.
# External recipe for the shared CMake owner. AUTHORED_NOTRUN.
# Requires Entry's committed actual4 command/snapshot foundation d2ced923.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_sway.cpp")

if(WIN32 AND XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1 AND
   XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1 AND
   XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
  add_executable(xar_ck3_12004_sway_whole_producer_test
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_sway_whole_producer_test.cpp")
  target_link_libraries(xar_ck3_12004_sway_whole_producer_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  target_include_directories(xar_ck3_12004_sway_whole_producer_test PRIVATE include)
  target_compile_features(xar_ck3_12004_sway_whole_producer_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_sway_whole_producer_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12004_sway_whole_producer_test PRIVATE
      /O2 /W4 /WX /EHsc /permissive- /utf-8 /Gy)
    target_link_options(xar_ck3_12004_sway_whole_producer_test PRIVATE
      /OPT:REF /INCREMENTAL:NO)
  endif()
  add_test(NAME ck3_12004_sway_whole_producer
    COMMAND $<TARGET_FILE:xar_ck3_12004_sway_whole_producer_test>
      "${CMAKE_CURRENT_BINARY_DIR}/ck3_12004_sway_whole_wire")
endif()

# External Epidemic16-TU recipe projected from epidemic-whole-first-hook.cmake.
# Source-only integration hook for the exclusive entry/CMake owner.
# AUTHORED_NOTRUN. This fragment has not been configured or compiled.
if(WIN32 AND BUILD_TESTING)
  add_executable(xar_ck3_12004_epidemic_whole_query_test
    src/ck3_12004_epidemic_whole_query_test.cpp
    src/ck3_12004_epidemic.cpp
    src/ck3_12004_abi_profile.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12002.cpp
    src/ck3_12002_phase_definitions.cpp
    src/ck3_12002_epidemic_recovery.cpp
    src/ck3_12002_epidemic_recovery_mailbox.cpp
    src/ck3_12002_epidemic_treatment_presence.cpp
    src/ck3_12002_epidemic_treatment_mailbox.cpp
    src/player_epidemic_recovery_v1.cpp
    src/player_epidemic_treatment_presence_v1.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12002_thread_runtime.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/protocol.cpp)
  target_include_directories(xar_ck3_12004_epidemic_whole_query_test PRIVATE include)
  target_compile_definitions(xar_ck3_12004_epidemic_whole_query_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1
    XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1
    XAR_EPIDEMIC_RECOVERY_MAILBOX_STANDALONE_NATIVE_ADAPTER)
  if(MSVC)
    target_compile_options(xar_ck3_12004_epidemic_whole_query_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  endif()
  target_link_libraries(xar_ck3_12004_epidemic_whole_query_test PRIVATE user32)
  add_test(NAME xar_ck3_native_bridge_12004_epidemic_whole_query
    COMMAND xar_ck3_12004_epidemic_whole_query_test
      "${CMAKE_CURRENT_BINARY_DIR}/fixtures/ck3_12004_epidemic_whole_query")
endif()

# Actual Activity target: four authored fixture TUs and the exact reported
# production dependencies from ROOT-HOOK-AND-NATIVE-TARGET.md.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_activity_feast_migration_test
    tests/activity_feast_migration_12004_test.cpp
    tests/activity_planner_start_12004_fixture.cpp
    tests/activity_guest_cost_12004_fixture.cpp
    tests/activity_hosted_resources_12004_fixture.cpp
    src/ck3_12002_feast_planner_native.cpp
    src/ck3_12002_feast_planner.cpp
    src/activity_planner_diag_v1.cpp
    src/activity_feast_stage5_start_v1.cpp
    src/activity_cost_slot12_passive_v1.cpp
    src/activity_stage5_gold_cost_v1.cpp
    src/activity_stage5_feast_full_cost_v1.cpp
    src/activity_stage5_feast_guest_join_v1.cpp
    src/activity_feast_guest_rule_toggle_v1.cpp
    src/activity_hosted_identity_v1.cpp
    src/activity_feast_resource_balance_v1.cpp
    src/ck3_12004_phase_character.cpp
    src/ck3_12004_gift_opinion.cpp
    src/ck3_12004_abi_profile.cpp)
  target_include_directories(xar_ck3_12004_activity_feast_migration_test PRIVATE include)
  target_compile_features(xar_ck3_12004_activity_feast_migration_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_activity_feast_migration_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(xar_ck3_12004_activity_feast_migration_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  if(MSVC)
    target_compile_options(xar_ck3_12004_activity_feast_migration_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12004_activity_feast_migration_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_activity_feast_migration_test>)
endif()

# Literal Hire target/source/runtime link and one fresh JSON output argument
# from ROOT-SHARED-HOOKS-AND-FIRST-RECIPE.json.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_hired_troop_migration_test
    src/ck3_12004_hired_troop_migration_test.cpp)
  target_include_directories(xar_ck3_12004_hired_troop_migration_test PRIVATE include)
  target_compile_features(xar_ck3_12004_hired_troop_migration_test PRIVATE cxx_std_20)
  target_link_libraries(xar_ck3_12004_hired_troop_migration_test PRIVATE
    xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(xar_ck3_12004_hired_troop_migration_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12004_hired_troop_migration_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_hired_troop_migration_test>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_hired_troop_migration_wire.json")
endif()

# Exact four-source Frontend target closure from ROOT-DELIVERY.json.
# Runtime supplies the centrally adopted actual-.4 core/GUI dependencies.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_frontend_bookmark_12004_fixture
    src/frontend_bookmark_12004_fixture.cpp
    src/frontend_bookmark_model_probe_v1.cpp
    src/frontend_bookmark_model_result_v1.cpp
    src/ck3_12004_frontend_bookmark.cpp)
  target_include_directories(xar_ck3_frontend_bookmark_12004_fixture PRIVATE include)
  target_compile_features(xar_ck3_frontend_bookmark_12004_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_frontend_bookmark_12004_fixture PRIVATE
    XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=1)
  target_link_libraries(xar_ck3_frontend_bookmark_12004_fixture PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  if(MSVC)
    target_compile_options(xar_ck3_frontend_bookmark_12004_fixture PRIVATE /W4 /WX)
  endif()
  add_test(NAME xar_ck3_frontend_bookmark_12004_fixture
    COMMAND $<TARGET_FILE:xar_ck3_frontend_bookmark_12004_fixture>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/frontend_bookmark_12004")
endif()

# Generic GUI actual-.4 production sources from sealed ROOT-DELIVERY8545.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_ingame_ui.cpp
  src/frontend_gui_result_v1.cpp
  src/ingame_ui_mailbox_v1.cpp)

# Changed existing model probe references the genuine actual-.4 binder.
# This is future source/link compatibility, not a historical test replay.
if(TARGET xar_ck3_frontend_bookmark_model_probe_v1_test)
  target_sources(xar_ck3_frontend_bookmark_model_probe_v1_test PRIVATE
    src/ck3_12004_frontend_bookmark.cpp)
endif()

# Sole new seven-frame producer, using the proven whole-foundation closure.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_generic_gui_12004_fixture
    src/generic_gui_12004_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_link_libraries(xar_ck3_generic_gui_12004_fixture PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_generic_gui_12004_fixture PRIVATE include)
  target_compile_features(xar_ck3_generic_gui_12004_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_generic_gui_12004_fixture PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  if(MSVC)
    target_compile_options(xar_ck3_generic_gui_12004_fixture PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_generic_gui_12004_fixture
    COMMAND $<TARGET_FILE:xar_ck3_generic_gui_12004_fixture>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_generic_gui_12004")
endif()

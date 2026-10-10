# Source-closed Native71 continuation leaves used by the production providers.
# Each new TU belongs to the shared runtime; xar_ck3_bridge already links it.
# Existing piety, Knight consumption and historical capture registrations remain
# in their original include files.
# Three delivered standalone leaves use their adjacent header's basename; their
# canonical headers live alongside the other bridge headers after adoption.
target_include_directories(xar_ck3_12002_runtime PRIVATE include/xar_bridge)
include(cmake/conception_natural_pair_observer_12004.cmake)
target_sources(xar_ck3_12002_runtime PRIVATE
  src/person_installed_transfer_stage_12004.cpp
  src/entry_final_occurrence_12004.cpp
  src/entry_final_cache_postimage_12004.cpp
  src/entry_final_outer_refresh_12004.cpp
  src/person_transfer_block10_12004.cpp
  src/person_transfer_block78_12004.cpp
  src/person_transfer_blocke0_12004.cpp
  src/person_transfer_block248_12004.cpp
  src/army_pre_date_prepared_roster_12004.cpp
  src/army_daily_assault_preparation_12004.cpp
  src/army_assault_group_placement_12004.cpp
  src/calendar_month_flag_12004.cpp
  src/army_monthfirst_cleanup_stage_12004.cpp
  src/army_pre_date_prefix_stage_12004.cpp
  src/army_late_context_copy12004.cpp
  src/ck3_12004_army_late_context_builder_inputs.cpp)

option(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1
  "Observe actual4 Army late event dispatches and copied incoming contexts" ON)
if(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_actual_army_late_event_journal.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1=1)
endif()

if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/conception_pair_value_inputs_12004.cpp
    src/conception_extended_gate_12004.cpp
    src/conception_candidate_pending_12004.cpp
    src/conception_pair_shortcircuit_12004.cpp
    src/conception_pair_shortcircuit_observer_12004.cpp
    src/conception_second_value_12004.cpp
    src/conception_first_value_12004.cpp
    src/ck3_12004_conception_pair_max_input.cpp
    src/conception_offspring_count_12004.cpp
    src/conception_pair_list_bonus_12004.cpp
    src/conception_related_pair_12004.cpp
    src/conception_last_child_date_12004.cpp
    src/conception_secondary_context_12004.cpp)
endif()

# New authored fixtures remain selectable; none participates in the default build.
# Root registers the new 57 lineage fixture in its existing Knight include.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_group_b_refresh_wire EXCLUDE_FROM_ALL
    tests/group_b_refresh_wire_test.cpp)
  target_link_libraries(xar_ck3_12004_group_b_refresh_wire PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12004_group_b_refresh_wire PRIVATE include)
  target_compile_features(xar_ck3_12004_group_b_refresh_wire PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_group_b_refresh_wire PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_group_b_refresh_wire PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_group_b_refresh_wire
    COMMAND $<TARGET_FILE:xar_ck3_12004_group_b_refresh_wire>
      "${CMAKE_CURRENT_BINARY_DIR}/group-b-refresh-wire")

  add_executable(xar_army_late_context_builder12004_test EXCLUDE_FROM_ALL
    src/army_late_context_builder12004_test.cpp)
  target_link_libraries(xar_army_late_context_builder12004_test PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_army_late_context_builder12004_test PRIVATE include)
  target_compile_features(xar_army_late_context_builder12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_army_late_context_builder12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_army_late_context_builder12004_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_army_late_context_builder12004
    COMMAND $<TARGET_FILE:xar_army_late_context_builder12004_test>)

  if(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1)
    add_executable(xar_actual_army_late_event_journal12004_fixture EXCLUDE_FROM_ALL
      src/ck3_12004_actual_army_late_event_journal_fixture.cpp)
    target_link_libraries(xar_actual_army_late_event_journal12004_fixture PRIVATE
      xar_ck3_12002_runtime kernel32)
    target_include_directories(xar_actual_army_late_event_journal12004_fixture PRIVATE
      include)
    target_compile_features(xar_actual_army_late_event_journal12004_fixture PRIVATE
      cxx_std_20)
    target_compile_definitions(xar_actual_army_late_event_journal12004_fixture PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(xar_actual_army_late_event_journal12004_fixture PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
    endif()
    add_test(NAME xar_actual_army_late_event_journal12004
      COMMAND $<TARGET_FILE:xar_actual_army_late_event_journal12004_fixture>)
  endif()

  if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    # The new wire writer emits its packet to stdout. The focused recipe captures
    # that packet for the new Python cause consumer through its existing env input.
    add_executable(sway_completion_causal_wire_12004_test EXCLUDE_FROM_ALL
      src/sway_completion_causal_wire_12004_test.cpp)
    target_link_libraries(sway_completion_causal_wire_12004_test PRIVATE
      xar_ck3_12002_runtime)
    target_include_directories(sway_completion_causal_wire_12004_test PRIVATE include)
    target_compile_features(sway_completion_causal_wire_12004_test PRIVATE cxx_std_20)
    target_compile_definitions(sway_completion_causal_wire_12004_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(sway_completion_causal_wire_12004_test PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
    endif()
  endif()
endif()
include(cmake/native71_compiled_effect_observer_12004.cmake)
include(cmake/person_installed_transfer_capture_12004.cmake)
include(cmake/native71_continuation_focused_targets_12004.cmake)
include(cmake/person_transfer_physical_postimage_12004.cmake)
include(cmake/conception_full_provider_12004.cmake)
include(cmake/army_natural_connected_phase_12004.cmake)
include(cmake/entry_final_side_connected_capture_12004.cmake)
include(cmake/lifestyle_current_perk_source_12004.cmake)
include(cmake/prisoner_selected_quote_source_12004.cmake)
include(cmake/construction_owner_mode3_source_12004.cmake)

# Permanently tracked authored fixtures; only explicit target builds select them.
if(BUILD_TESTING AND WIN32)
  # The effective55 fixture is a two-TU DTO/serializer transport with active asserts.
  # It has no runtime/provider link; Root captures stdout for its Python strict focus.
  add_executable(xar_current_household_conception_wire_focus EXCLUDE_FROM_ALL
    tests/current_household_conception_wire_focus.cpp
    src/current_first_heir_relationship_v1.cpp)
  target_include_directories(xar_current_household_conception_wire_focus PRIVATE include)
  target_compile_features(xar_current_household_conception_wire_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_current_household_conception_wire_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
  if(MSVC)
    target_compile_options(xar_current_household_conception_wire_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()

  add_executable(knight_installed_transfer_consumption_12004_test EXCLUDE_FROM_ALL
    tests/knight_installed_transfer_consumption_12004_fixture.cpp)
  target_link_libraries(knight_installed_transfer_consumption_12004_test PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(knight_installed_transfer_consumption_12004_test PRIVATE include)
  target_compile_features(knight_installed_transfer_consumption_12004_test PRIVATE cxx_std_20)
  target_compile_definitions(knight_installed_transfer_consumption_12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(knight_installed_transfer_consumption_12004_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME knight_installed_transfer_consumption_12004
    COMMAND $<TARGET_FILE:knight_installed_transfer_consumption_12004_test>
      "${CMAKE_CURRENT_BINARY_DIR}/knight-installed-transfer-consumption-wire")
endif()

# The shared46/47 default-context compound has one permanent main and bool companion.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_conception_default_context_compound_focus EXCLUDE_FROM_ALL
    tests/conception_default_context_compound_focus.cpp
    tests/conception_first_default_join_12004_focus.cpp
    src/conception_modifier_context_12004.cpp
    src/conception_first_value_12004.cpp
    src/conception_second_value_12004.cpp)
  target_include_directories(xar_conception_default_context_compound_focus PRIVATE include)
  target_compile_features(xar_conception_default_context_compound_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_conception_default_context_compound_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    set_property(TARGET xar_conception_default_context_compound_focus
      PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    target_compile_options(xar_conception_default_context_compound_focus PRIVATE
      /Od /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
endif()

# The new guarded-source contract regression is a standalone copied DTO/wire focus.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_current_household_conception_guarded_source_focus EXCLUDE_FROM_ALL
    tests/current_household_conception_guarded_source_focus.cpp
    src/current_first_heir_relationship_v1.cpp
    src/conception_pair_shortcircuit_12004.cpp
    src/conception_pair_shortcircuit_observer_12004.cpp)
  target_include_directories(xar_current_household_conception_guarded_source_focus PRIVATE include)
  target_compile_features(xar_current_household_conception_guarded_source_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_current_household_conception_guarded_source_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
  if(MSVC)
    set_property(TARGET xar_current_household_conception_guarded_source_focus
      PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    target_compile_options(xar_current_household_conception_guarded_source_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # Root retains stdout and invokes the new guarded-source Python strict cell.
endif()

# Owned natural-conception journal transport: one new main and current serializer.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_current_household_conception_natural_wire_focus EXCLUDE_FROM_ALL
    tests/current_household_conception_natural_wire_focus.cpp
    src/current_first_heir_relationship_v1.cpp)
  target_include_directories(xar_current_household_conception_natural_wire_focus PRIVATE include)
  target_compile_features(xar_current_household_conception_natural_wire_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_current_household_conception_natural_wire_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1
    XAR_NATIVE71_CONCEPTION_PAIR_PROVIDER_PASSIVE_12004=1)
  if(MSVC)
    set_property(TARGET xar_current_household_conception_natural_wire_focus
      PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    target_compile_options(xar_current_household_conception_natural_wire_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # Main reads tests/fixtures/conception_pair_passive_12004_joined_journal.json.
endif()

# Guardian sidecar path/transport boundary: one new main and existing protocol implementation.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_guardian_factory_sidecar_transport_focus EXCLUDE_FROM_ALL
    tests/guardian_factory_sidecar_transport_focus.cpp
    src/protocol.cpp)
  target_include_directories(xar_guardian_factory_sidecar_transport_focus PRIVATE include)
  target_compile_features(xar_guardian_factory_sidecar_transport_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_guardian_factory_sidecar_transport_focus PRIVATE NOMINMAX)
  if(MSVC)
    set_property(TARGET xar_guardian_factory_sidecar_transport_focus
      PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    target_compile_options(xar_guardian_factory_sidecar_transport_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # The permanent Python driver invokes the native executable once through its mock endpoint.
endif()

# The actual nonwar guard diagnostic uses one fixture TU and inline production helper.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_nonwar_private_snapshot_guard_diagnostics_v1_fixture EXCLUDE_FROM_ALL
    src/nonwar_private_snapshot_guard_diagnostics_v1_fixture.cpp)
  target_include_directories(xar_nonwar_private_snapshot_guard_diagnostics_v1_fixture PRIVATE include)
  target_compile_features(xar_nonwar_private_snapshot_guard_diagnostics_v1_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_nonwar_private_snapshot_guard_diagnostics_v1_fixture PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_nonwar_private_snapshot_guard_diagnostics_v1_fixture PRIVATE /EHsc)
  endif()
endif()

# Actual Activity three-input compound:14 formedobjects plus qualified fullcost provider.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_activity_actual_three_bindings_connected_test EXCLUDE_FROM_ALL
    tests/activity_actual_three_bindings_connected_12004_main.cpp
    tests/activity_actual_three_bindings_connected_12004.cpp
    src/activity_planner_diag_v1.cpp
    src/activity_stage5_gold_cost_v1.cpp
    src/activity_stage5_feast_guest_join_v1.cpp
    src/activity_stage5_canstart_read_v1.cpp
    src/activity_cost_slot12_passive_v1.cpp
    src/ck3_12002_activity_feast_cost_private_transport_v1.cpp
    src/activity_feast_stage5_start_private_serializer_v1.cpp
    src/activity_stage5_canstart_failure_display_v1.cpp
    src/activity_feast_guest_candidate_v1.cpp
    src/activity_feast_guest_rule_toggle_v1.cpp
    src/activity_feast_guest_rule_provenance_v1.cpp
    src/activity_feast_stage5_start_v1.cpp
    src/activity_stage5_feast_full_cost_v1.cpp)
  target_include_directories(xar_ck3_12004_activity_actual_three_bindings_connected_test PRIVATE include src)
  target_compile_features(xar_ck3_12004_activity_actual_three_bindings_connected_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_activity_actual_three_bindings_connected_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
    WIN32
    _WINDOWS
    _ITERATOR_DEBUG_LEVEL=0
    XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_GATE_READ_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_LOCATION_READ_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1=1
    XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1=1)
  target_link_libraries(xar_ck3_12004_activity_actual_three_bindings_connected_test PRIVATE
    xar_ck3_12002_runtime kernel32 user32 advapi32)
  if(MSVC)
    set_property(TARGET xar_ck3_12004_activity_actual_three_bindings_connected_test PROPERTY
      MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
    target_compile_options(xar_ck3_12004_activity_actual_three_bindings_connected_test PRIVATE
      /O2 /EHsc /W4 /WX /permissive- /utf-8 /UNDEBUG)
  endif()
  # Only the new three-input export runs;stdout is retained for its strict Python consumer.
endif()

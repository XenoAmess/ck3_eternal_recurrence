# Natural Army provider symbols always compile once; installer flags gate Bridge entry only.
# Header presence markers describe available declarations and never enable installation.
target_sources(xar_ck3_bridge PRIVATE
  src/actual_army_assault_placement_observer_12004.cpp
  src/actual_army_daily_assault_preparation_observer_12004.cpp
  src/actual_army_pre_date_prefix_observer_12004.cpp
  src/army_actual_monthfirst_cleanup_12004.cpp
  src/army_gathering_due_natural_stage_12004.cpp
  src/army_natural_phase_json_12004.cpp
  src/army_natural_phase_observer_12004.cpp
  src/army_natural_phase_scope_12004.cpp
  src/army_position_2c09410_12004.cpp
  src/army_regular_core_passive_12004.cpp)

target_sources(xar_ck3_12002_runtime PRIVATE
  src/army_assault_group_release_observer_12004.cpp
  src/army_position_2c09280_12004.cpp
  src/army_position_2c3a0e0_readonly_12004.cpp
  src/army_position_helper_2c09360_12004.cpp
  src/army_position_relation_28b2800_12004.cpp
  src/army_position_relation_28bc250_12004.cpp
  src/army_position_same_war_side_12004.cpp
  src/army_position_selected_actor_12004.cpp
  src/army_position_war_membership_12004.cpp
  src/ck3_12004_actual_assault_budget_journal.cpp
  src/ck3_12004_actual_assault_consumer_journal.cpp)

option(XAR_NATIVE71_ARMY_NATURAL_PHASE_12004
  "Install the natural Army phase and preparation, assault, budget and cleanup children" ON)
if(XAR_NATIVE71_ARMY_NATURAL_PHASE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_NATIVE71_ARMY_NATURAL_PHASE_12004=1)
endif()

option(XAR_ENABLE_ARMY_REGULAR_CORE_PASSIVE_12004
  "Install the natural Army regular core observer" ON)
if(XAR_ENABLE_ARMY_REGULAR_CORE_PASSIVE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_REGULAR_CORE_PASSIVE_12004=1)
endif()

option(XAR_ENABLE_ARMY_PRE_DATE_PREFIX_PASSIVE_12004
  "Install the natural Army pre-date prefix observer" ON)
if(XAR_ENABLE_ARMY_PRE_DATE_PREFIX_PASSIVE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_PRE_DATE_PREFIX_PASSIVE_12004=1)
endif()

option(XAR_ENABLE_ARMY_ASSAULT_PLACEMENT_PASSIVE_12004
  "Install the natural Army assault placement observer" ON)
if(XAR_ENABLE_ARMY_ASSAULT_PLACEMENT_PASSIVE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_ASSAULT_PLACEMENT_PASSIVE_12004=1)
endif()

option(XAR_ENABLE_ARMY_ASSAULT_GROUP_RELEASE_PASSIVE_12004
  "Install the natural Army assault group release observer" ON)
if(XAR_ENABLE_ARMY_ASSAULT_GROUP_RELEASE_PASSIVE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_ASSAULT_GROUP_RELEASE_PASSIVE_12004=1)
endif()

option(XAR_ENABLE_ARMY_GATHERING_DUE_PASSIVE_12004
  "Install the natural Army gathering due observer" ON)
if(XAR_ENABLE_ARMY_GATHERING_DUE_PASSIVE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_GATHERING_DUE_PASSIVE_12004=1)
endif()

option(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004
  "Include owned natural Army phase journals in the Bridge strength query" ON)
if(XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ARMY_OBSERVED_PHASE_QUERY_12004=1)
endif()

if(BUILD_TESTING AND WIN32)
  # Exact authored48-TU compound, including two existing minimum link dependencies.
  add_executable(xar_army_natural_connected_phase_focus EXCLUDE_FROM_ALL
    src/army_natural_phase_json_12004.cpp
    src/army_natural_phase_observer_12004.cpp
    src/army_natural_phase_scope_12004.cpp
    tests/army_natural_connected_phase_focus.cpp
    tests/army_natural_phase_install_focus_12004.cpp
    tests/army_natural_phase_scope_focus_12004.cpp
    src/army_regular_core_passive_12004.cpp
    src/army_regular_core_passive_12004_new_focus.cpp
    src/actual_army_daily_assault_preparation_observer_12004.cpp
    tests/actual_army_daily_assault_preparation_observer_12004_focus.cpp
    src/actual_army_assault_placement_observer_12004.cpp
    src/actual_army_assault_placement_observer_12004_test.cpp
    src/actual_assault_consumer_natural_12004_focus.cpp
    src/ck3_12004_actual_assault_consumer_journal.cpp
    src/ck3_12004_actual_assault_budget_journal.cpp
    tests/actual_assault_budget_focus_12004.cpp
    src/army_assault_group_release_observer_12004.cpp
    src/army_assault_group_release_observer_12004_focus.cpp
    src/army_gathering_due_natural_stage_12004.cpp
    tests/army_gathering_due_natural_focus_12004.cpp
    src/army_actual_monthfirst_cleanup_12004.cpp
    tests/army_actual_monthfirst_cleanup_natural_focus_12004.cpp
    src/actual_army_pre_date_prefix_observer_12004.cpp
    tests/army_pre_date_prefix_natural_focus_12004.cpp
    src/army_position_same_war_side_12004.cpp
    tests/army_position_same_war_side_12004_test.cpp
    src/army_position_2c09280_12004.cpp
    src/army_position_2c09280_12004_focus.cpp
    src/army_position_relation_28bc250_12004.cpp
    tests/army_position_relation_natural_focus_12004.cpp
    src/army_position_helper_2c09360_12004.cpp
    tests/army_position_helper_natural_focus_12004.cpp
    src/army_position_selected_actor_12004.cpp
    tests/army_position_selected_actor_natural_focus_12004.cpp
    src/army_position_2c09410_12004.cpp
    tests/army_position_2c09410_natural_focus_12004.cpp
    src/army_position_war_membership_12004.cpp
    src/army_position_war_membership_12004_new_phase_cases.cpp
    src/army_position_relation_28b2800_12004.cpp
    src/army_position_relation_28b2800_12004_new_focus.cpp
    src/army_position_2c3a0e0_readonly_12004.cpp
    src/army_position_2c3a0e0_readonly_12004_case_export.cpp
    src/ck3_12004_person_first_title_vector.cpp
    src/person_natural_lineage_clock_12004.cpp
    src/army_daily_assault_preparation_12004.cpp
    tests/army_observed_phase_packet_12004.cpp
    src/army_assault_group_placement_12004.cpp
    src/ck3_12004_person_local_titles.cpp)
  target_include_directories(xar_army_natural_connected_phase_focus PRIVATE include tests)
  target_compile_features(xar_army_natural_connected_phase_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_army_natural_connected_phase_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(xar_army_natural_connected_phase_focus PRIVATE kernel32)
  if(MSVC)
    set_property(TARGET xar_army_natural_connected_phase_focus PROPERTY
      MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
    target_compile_options(xar_army_natural_connected_phase_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # Sole argv: --army-natural-connected-phase.
endif()


# Disabled unless an explicitly controlled no-load recording build requests it.
option(XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004
  "Install exact 1.20.0.4 passive boarding payment observers" OFF)
if(XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004)
  if(NOT XAR_NATIVE71_ARMY_NATURAL_PHASE_12004)
    message(FATAL_ERROR "Payment observation requires installed natural Army phase parents")
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    src/war_payment_passive_12004.cpp
    src/war_payment_runtime_12004.cpp
    src/war_payment_json_12004.cpp
    src/war_payment_window_12004.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004=1)
endif()

# Explicit offline regression; not part of the default CTest inventory.
if(BUILD_TESTING AND MSVC AND WIN32)
  set(_payment_focus_dir "${CMAKE_CURRENT_SOURCE_DIR}/tests/war_payment_snapshot_unavailable")
  add_executable(xar_test_war_payment_snapshot_unavailable EXCLUDE_FROM_ALL
    "${_payment_focus_dir}/payment_snapshot_unavailable_focus.cpp"
    src/war_payment_passive_12004.cpp src/war_payment_window_12004.cpp)
  target_include_directories(xar_test_war_payment_snapshot_unavailable PRIVATE include)
  target_compile_features(xar_test_war_payment_snapshot_unavailable PRIVATE cxx_std_20)
  target_compile_definitions(xar_test_war_payment_snapshot_unavailable PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_PAYMENT_WINDOW_FIXTURE=1)
  target_compile_options(xar_test_war_payment_snapshot_unavailable PRIVATE
    /O2 /EHsc /W4 /WX /Gy /utf-8)
  set_source_files_properties("${_payment_focus_dir}/payment_snapshot_unavailable_focus.cpp"
    PROPERTIES COMPILE_OPTIONS /wd4505)
  set_property(TARGET xar_test_war_payment_snapshot_unavailable PROPERTY
    MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
  target_link_options(xar_test_war_payment_snapshot_unavailable PRIVATE /OPT:REF /OPT:ICF)
  target_link_libraries(xar_test_war_payment_snapshot_unavailable PRIVATE kernel32 user32)
endif()

# Raw four-input capture for one source-proved ADD caller; no military inference.
option(XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004
  "Capture exact-caller raw wallet context and bounded OS parent frames" OFF)
if(XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004)
  if(NOT XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004)
    message(FATAL_ERROR "Generic wallet context requires the existing passive payment observer")
  endif()
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004=1)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004=1)
endif()

# Optional sixth entry in the existing payment installer; never a new producer.
option(XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004
  "Observe only natural selector4 calls at exact4 28B9490" OFF)
if(XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004)
  if(NOT XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004)
    message(FATAL_ERROR "Raw selector4 getter needs the existing payment window/journal")
  endif()
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004=1)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004=1)
endif()

# Deliberate synthetic ABI/retention fixture only. No default build/CTest run.
if(BUILD_TESTING AND WIN32 AND MSVC)
  add_executable(xar_test_war_payment_raw4_getter EXCLUDE_FROM_ALL
    tests/war_payment_raw4_getter/raw4_fixture.cpp
    src/war_payment_passive_12004.cpp src/war_payment_runtime_12004.cpp
    src/war_payment_json_12004.cpp)
  target_include_directories(xar_test_war_payment_raw4_getter PRIVATE include)
  target_compile_features(xar_test_war_payment_raw4_getter PRIVATE cxx_std_20)
  target_compile_definitions(xar_test_war_payment_raw4_getter PRIVATE
    XAR_ENABLE_WAR_PAYMENT_RAW4_GETTER_12004=1 NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(xar_test_war_payment_raw4_getter PRIVATE /EHsc /W4 /WX /utf-8)
  target_link_libraries(xar_test_war_payment_raw4_getter PRIVATE kernel32)
endif()

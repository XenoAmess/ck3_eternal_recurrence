cmake_minimum_required(VERSION 3.25)

project(xar_ck3_native_bridge VERSION 0.1.0 LANGUAGES CXX)

# Ninja discovers MSVC header dependencies by matching /showIncludes output.
# CMake 4.3 can misdecode the Simplified-Chinese prefix as mojibake while
# cl.exe and Ninja exchange UTF-8, leaving every object with zero header deps.
# Repair only that observed detection result; other compiler UI languages keep
# their own prefix.
if(
  MSVC AND
  CMAKE_CXX_CL_SHOWINCLUDES_PREFIX STREQUAL
    "娉ㄦ剰: 鍖呭惈鏂囦欢:  "
)
  set(CMAKE_CXX_CL_SHOWINCLUDES_PREFIX "注意: 包含文件:  ")
  set(CMAKE_CL_SHOWINCLUDES_PREFIX "${CMAKE_CXX_CL_SHOWINCLUDES_PREFIX}")
endif()

if(NOT WIN32)
  message(FATAL_ERROR "xar_ck3_native_bridge currently targets Windows only")
endif()

if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "xar_ck3_native_bridge must be built for x64")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(
  XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1
  "Install the exact-build no-suppression particle2 startup stage recorder"
  OFF
)

add_library(xar_bridge_protocol STATIC
  src/protocol.cpp
)
target_include_directories(xar_bridge_protocol PUBLIC include)
target_compile_definitions(xar_bridge_protocol PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

add_library(xar_bridge_injector STATIC
  src/injector.cpp
)
target_include_directories(xar_bridge_injector PUBLIC include)
target_compile_definitions(xar_bridge_injector PUBLIC
  NOMINMAX
  WIN32_LEAN_AND_MEAN
  UNICODE
  _UNICODE
)

add_library(xar_ck3_bridge SHARED
  src/actual_contact_scope_v1_mailbox.cpp
  src/battle_control_snapshot_v1_mailbox.cpp
  src/battle_reinforcement_assignment_v1_mailbox.cpp
  src/battle_terminal_journal_v1.cpp
  src/battle_terminal_transition_v1_mailbox.cpp
  src/battle_transition_v1_mailbox.cpp
  src/bridge.cpp
  src/ck3_11906.cpp
  src/ck3_11906_adapter.cpp
  src/combat_phase_event_trace_detour_v1.cpp
  src/combat_phase_event_trace_managed_v1.cpp
  src/combat_phase_event_trace_ring_v1.cpp
  src/combat_phase_event_trace_wire_v1.cpp
  src/combat_simulation_inputs_v3_mailbox.cpp
  src/combat_v3.cpp
  src/combat_v3_serializer.cpp
  src/combat_v3_test_only.cpp
  src/game_adapter.cpp
  src/main_thread_query_mailbox_v1.cpp
  src/route_contact_horizon_v1_mailbox.cpp
  src/startup_dx11_render_context_draw_guard_v1.cpp
  src/startup_localize_current_root_guard_v1.cpp
  src/startup_particle2_consumer_null_guard_v1.cpp
  src/startup_particle2_null_guard_v1.cpp
  src/startup_particle2_stage_recorder_v1.cpp
  src/war_entry_assessments_v1.cpp
  src/war_entry_assessments_v1_serializer.cpp
  src/war_entry_assessments_v1_mailbox.cpp
)
target_link_libraries(xar_ck3_bridge PRIVATE xar_bridge_protocol bcrypt)
target_compile_definitions(xar_ck3_bridge PRIVATE
  XAR_BRIDGE_VERSION="${PROJECT_VERSION}"
)
if(XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1=1
  )
endif()
set_target_properties(xar_ck3_bridge PROPERTIES
  OUTPUT_NAME "xar_ck3_bridge"
)

add_executable(xar_ck3_bridge_host
  src/host.cpp
)
target_link_libraries(xar_ck3_bridge_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_attach_host
  src/attach_host.cpp
)
target_link_libraries(xar_ck3_bridge_attach_host PRIVATE xar_bridge_protocol)

add_executable(xar_ck3_bridge_injector
  src/injector_main.cpp
)
target_link_libraries(xar_ck3_bridge_injector PRIVATE xar_bridge_injector)

add_executable(xar_ck3_bridge_target
  src/target.cpp
)

if(MSVC)
  foreach(target
      xar_bridge_protocol
      xar_bridge_injector
      xar_ck3_bridge
      xar_ck3_bridge_host
      xar_ck3_bridge_attach_host
      xar_ck3_bridge_injector
      xar_ck3_bridge_target)
    target_compile_options(${target} PRIVATE /W4 /permissive- /EHsc)
  endforeach()
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(xar_ck3_game_access_test
    src/actual_contact_scope_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox.cpp
    src/ck3_11906.cpp
    src/ck3_11906_test.cpp
    src/route_contact_horizon_v1_mailbox.cpp
  )
  target_include_directories(xar_ck3_game_access_test PRIVATE include)
  target_link_libraries(xar_ck3_game_access_test PRIVATE bcrypt)
  target_compile_definitions(xar_ck3_game_access_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
    XAR_CK3_WAR_EXIT_TERMS_OFFLINE_RE_TEST
  )
  if(MSVC)
    target_compile_options(xar_ck3_game_access_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_game_access_fixture
    COMMAND xar_ck3_game_access_test
  )

  add_executable(xar_ck3_adapter_registry_test
    src/actual_contact_scope_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox.cpp
    src/combat_simulation_inputs_v3_mailbox.cpp
    src/game_adapter.cpp
    src/ck3_11906_adapter.cpp
    src/ck3_11906.cpp
    src/combat_v3.cpp
    src/route_contact_horizon_v1_mailbox.cpp
    src/war_entry_assessments_v1.cpp
    src/game_adapter_test.cpp
  )
  target_include_directories(xar_ck3_adapter_registry_test PRIVATE include)
  target_link_libraries(xar_ck3_adapter_registry_test PRIVATE bcrypt)
  target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(xar_ck3_adapter_registry_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_adapter_registry
    COMMAND xar_ck3_adapter_registry_test
  )

  add_executable(xar_ck3_battle_control_snapshot_v1_mailbox_test
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_control_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_control_snapshot_v1_mailbox
    COMMAND xar_ck3_battle_control_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_battle_transition_v1_mailbox_test
    src/battle_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_transition_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_transition_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_transition_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_transition_v1_mailbox
    COMMAND xar_ck3_battle_transition_v1_mailbox_test
  )

  add_executable(xar_ck3_battle_reinforcement_assignment_v1_mailbox_test
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_reinforcement_assignment_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_reinforcement_assignment_v1_mailbox
    COMMAND xar_ck3_battle_reinforcement_assignment_v1_mailbox_test
  )

  add_executable(xar_ck3_battle_terminal_transition_v1_mailbox_test
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_terminal_transition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_battle_terminal_transition_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_battle_terminal_transition_v1_mailbox
    COMMAND xar_ck3_battle_terminal_transition_v1_mailbox_test
  )

  add_executable(xar_ck3_combat_v3_test_only_serializer_test
    src/combat_v3_test_only.cpp
    src/combat_v3_test_only_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_v3_test_only_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_v3_test_only_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_test_only_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_test_only_serializer
    COMMAND xar_ck3_combat_v3_test_only_serializer_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_inputs_v3_test_only_golden.json
  )

  add_executable(xar_ck3_combat_v3_serializer_test
    src/combat_v3_serializer.cpp
    src/combat_v3_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_v3_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_v3_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_serializer
    COMMAND xar_ck3_combat_v3_serializer_test
  )

  add_executable(xar_ck3_combat_v3_source_contract_test
    src/combat_v3_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_v3_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_v3_source_contract
    COMMAND xar_ck3_combat_v3_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_v3.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_simulation_inputs_v3_mailbox.cpp
  )

  add_executable(xar_ck3_combat_phase_event_trace_v1_source_contract_test
    src/combat_phase_event_trace_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_v1_source_contract
    COMMAND xar_ck3_combat_phase_event_trace_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_phase_event_trace_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/combat_phase_event_trace_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/combat_phase_event_trace_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_event_trace_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/combat-phase-event-trace.md
  )

  add_executable(xar_ck3_combat_phase_event_trace_ring_v1_test
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_phase_event_trace_ring_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_ring_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_ring_v1
    COMMAND xar_ck3_combat_phase_event_trace_ring_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/combat_phase_event_trace_ring_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/src/combat_phase_event_trace_ring_v1.cpp
  )

  add_executable(xar_ck3_combat_phase_event_trace_detour_v1_test
    src/combat_phase_event_trace_detour_v1.cpp
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_phase_event_trace_detour_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_detour_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_detour_v1
    COMMAND xar_ck3_combat_phase_event_trace_detour_v1_test
  )

  add_executable(xar_ck3_combat_phase_event_trace_wire_v1_test
    src/combat_phase_event_trace_wire_v1.cpp
    src/combat_phase_event_trace_wire_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_wire_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_wire_v1
    COMMAND xar_ck3_combat_phase_event_trace_wire_v1_test
  )

  add_executable(xar_ck3_combat_phase_event_trace_managed_v1_test
    src/combat_phase_event_trace_detour_v1.cpp
    src/combat_phase_event_trace_managed_v1.cpp
    src/combat_phase_event_trace_ring_v1.cpp
    src/combat_phase_event_trace_wire_v1.cpp
    src/combat_phase_event_trace_managed_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_combat_phase_event_trace_managed_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_combat_phase_event_trace_managed_v1
    COMMAND xar_ck3_combat_phase_event_trace_managed_v1_test
  )

  add_executable(xar_ck3_main_thread_query_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/main_thread_query_mailbox_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_main_thread_query_mailbox_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_main_thread_query_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_main_thread_query_mailbox_v1
    COMMAND xar_ck3_main_thread_query_mailbox_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/main_thread_query_mailbox_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/main_thread_query_mailbox_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/main-thread-query-mailbox.md
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_war_entry_assessments_v1_test
    src/war_entry_assessments_v1.cpp
    src/war_entry_assessments_v1_serializer.cpp
    src/war_entry_assessments_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1
    COMMAND xar_ck3_war_entry_assessments_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/war_entry_assessments_v1_golden.json
  )

  add_executable(xar_ck3_war_entry_assessments_v1_source_contract_test
    src/war_entry_assessments_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1_source_contract
    COMMAND xar_ck3_war_entry_assessments_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/war_entry_assessments_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/war_entry_assessments_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/war_entry_assessments_v1_golden.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/war-declaration.md
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
  )

  add_executable(xar_ck3_war_entry_assessments_v1_mailbox_test
    src/main_thread_query_mailbox_v1.cpp
    src/war_entry_assessments_v1.cpp
    src/war_entry_assessments_v1_mailbox.cpp
    src/war_entry_assessments_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_entry_assessments_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_entry_assessments_v1_mailbox
    COMMAND xar_ck3_war_entry_assessments_v1_mailbox_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/war_entry_assessments_v1_mailbox.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/war_entry_assessments_v1_mailbox_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/war-declaration.md
  )

  add_executable(xar_ck3_exit_terms_v2_test_only_serializer_test
    src/war_exit_terms_v2_test_only.cpp
    src/war_exit_terms_wire.cpp
    src/war_exit_terms_v2_test_only_test.cpp
  )
  target_include_directories(
    xar_ck3_exit_terms_v2_test_only_serializer_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_exit_terms_v2_test_only_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_exit_terms_v2_test_only_serializer
    COMMAND xar_ck3_exit_terms_v2_test_only_serializer_test
      ${CMAKE_CURRENT_SOURCE_DIR}/../tests/fixtures/war_termination_exit_terms_v2_synthetic.json
  )

  add_executable(xar_ck3_startup_particle2_stage_recorder_v1_test
    src/startup_particle2_stage_recorder_v1.cpp
    src/startup_particle2_stage_recorder_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_stage_recorder_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_stage_recorder_v1
    COMMAND xar_ck3_startup_particle2_stage_recorder_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_stage_recorder_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_stage_recorder_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_stage_recorder_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_stage_recorder_v1_source_contract.json
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_particle2_null_guard_v1_test
    src/startup_particle2_null_guard_v1.cpp
    src/startup_particle2_null_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_null_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_null_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_null_guard_v1
    COMMAND xar_ck3_startup_particle2_null_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_null_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_null_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_null_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_null_guard_v1_source_contract.json
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
  )

  add_executable(xar_ck3_startup_particle2_consumer_null_guard_v1_test
    src/startup_particle2_consumer_null_guard_v1.cpp
    src/startup_particle2_consumer_null_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_particle2_consumer_null_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_particle2_consumer_null_guard_v1
    COMMAND xar_ck3_startup_particle2_consumer_null_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_particle2_consumer_null_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_particle2_consumer_null_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_particle2_consumer_null_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_particle2_consumer_null_guard_v1_source_contract.json
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_dx11_render_context_draw_guard_v1_test
    src/startup_dx11_render_context_draw_guard_v1.cpp
    src/startup_dx11_render_context_draw_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_dx11_render_context_draw_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_dx11_render_context_draw_guard_v1
    COMMAND xar_ck3_startup_dx11_render_context_draw_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_dx11_render_context_draw_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_dx11_render_context_draw_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_dx11_render_context_draw_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_dx11_render_context_draw_guard_v1_source_contract.json
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_startup_localize_current_root_guard_v1_test
    src/startup_localize_current_root_guard_v1.cpp
    src/startup_localize_current_root_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_localize_current_root_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_localize_current_root_guard_v1
    COMMAND xar_ck3_startup_localize_current_root_guard_v1_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/startup_localize_current_root_guard_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/startup_localize_current_root_guard_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/startup_localize_current_root_guard_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/startup_localize_current_root_guard_v1_source_contract.json
      "${CMAKE_CURRENT_SOURCE_DIR}/../../Crusader Kings III/binaries/ck3.exe"
      ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_test(
    NAME xar_ck3_native_bridge_suspended_injection
    COMMAND xar_ck3_bridge_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_suspended_injection
    PROPERTIES TIMEOUT 30)

  add_test(
    NAME xar_ck3_native_bridge_running_attach
    COMMAND xar_ck3_bridge_attach_host
      $<TARGET_FILE:xar_ck3_bridge>
      $<TARGET_FILE:xar_ck3_bridge_injector>
      $<TARGET_FILE:xar_ck3_bridge_target>
  )
  set_tests_properties(xar_ck3_native_bridge_running_attach
    PROPERTIES TIMEOUT 30)
endif()

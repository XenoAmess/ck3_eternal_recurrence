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

option(
  XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1
  "Install the existing exact-build startup containment chain"
  OFF
)

option(
  XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1
  "Skip only the proven null-RDI startup widget flag call on the exact build"
  OFF
)

option(
  XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1
  "Skip only the proven null-RBX startup call on the exact build"
  OFF
)

option(
  XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1
  "Observe the exact-build cold-map VFS ctor, moved variant, and poll state"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1
  "Enable the read-only scoreboard production-evidence candidate without advertising production capability"
  OFF
)

option(
  XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1
  "Advertise the read-only projects/metrics provider only in a private paused-live candidate"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1
  "Write the private GEN-034 truce reader result before production reset"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1
  "Install the private exact-build G2 truce evaluator callsite observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1
  "Install the private exact-vtable G2 truce preview traversal observer"
  OFF
)

option(
  XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2
  "Evaluate the private G2 target only inside its exact native leaf-preview context"
  OFF
)

if(
  XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 AND
  XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1
)
  message(FATAL_ERROR
    "The native callsite observer cannot be combined with direct evaluator capture")
endif()
if(
  XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2 AND
  (XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1)
)
  message(FATAL_ERROR
    "The leaf-context capture is a standalone private candidate")
endif()

option(
  XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1
  "Build the private exact-build Raiktor spawn-army debugger capture"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1
  "Install the private exact-build phase-two completion observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1
  "Install the private exact-build phase-two wrapper entry observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1
  "Install the private exact-build phase-two post-call observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1
  "Install the private exact-build phase-two post-call list identity observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1
  "Install the private exact-build phase-two producer identity observer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1
  "Correlate the private phase-two producer selection with its completion consumer"
  OFF
)

option(
  XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1
  "Classify post-publish phase-two wrapper and exact consumer call edges"
  OFF
)

if(
  XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1 AND
  XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1
)
  message(FATAL_ERROR
    "The two private phase-two post-call observers share RVA 0x3407DA1")
endif()

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
  src/cold_map_vfs_observer_v1.cpp
  src/actual_contact_scope_v1_mailbox.cpp
  src/battle_control_snapshot_v1_mailbox.cpp
  src/battle_reinforcement_assignment_v1_mailbox.cpp
  src/battle_terminal_journal_v1.cpp
  src/battle_terminal_transition_v1_mailbox.cpp
  src/battle_transition_v1_mailbox.cpp
  src/bridge.cpp
  src/campaign_root_context_v1.cpp
  src/campaign_root_context_v1_mailbox.cpp
  src/campaign_root_context_v1_serializer.cpp
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
  src/event_window_context_v1.cpp
  src/event_window_context_v1_mailbox.cpp
  src/event_window_context_v1_serializer.cpp
  src/game_adapter.cpp
  src/g2_truce_native_callsite_observer_v1.cpp
  src/g2_truce_preview_entry_observer_v1.cpp
  src/loaded_feature_manifest_v1.cpp
  src/loaded_feature_manifest_v1_mailbox.cpp
  src/loaded_feature_manifest_v1_serializer.cpp
  src/main_thread_query_mailbox_v1.cpp
  src/pending_character_interaction_context_v1.cpp
  src/pending_character_interaction_context_v1_mailbox.cpp
  src/pending_character_interaction_context_v1_serializer.cpp
  src/phase2_completion_observer_v1.cpp
  src/phase2_post_call_list_identity_observer_v1.cpp
  src/phase2_post_call_observer_v1.cpp
  src/phase2_producer_identity_observer_v1.cpp
  src/phase2_wrapper_entry_observer_v1.cpp
  src/phase2_wrapper_consumer_edge_observer_v1.cpp
  src/route_contact_horizon_v1_mailbox.cpp
  src/raiktor_war_bound_regiment_v1.cpp
  src/raiktor_surrender_truce_v1.cpp
  src/startup_dx11_render_context_draw_guard_v1.cpp
  src/startup_localize_current_root_guard_v1.cpp
  src/startup_rbx_null_call_guard_v1.cpp
  src/startup_widget_null_flag_call_guard_v1.cpp
  src/startup_particle2_consumer_null_guard_v1.cpp
  src/startup_particle2_null_guard_v1.cpp
  src/startup_particle2_stage_recorder_v1.cpp
  src/tactical_daily_sentinel_v1.cpp
  src/title_map_navigation_v1.cpp
  src/title_map_navigation_v1_camera.cpp
  src/title_map_navigation_v1_mailbox.cpp
  src/title_map_navigation_v1_serializer.cpp
  src/war_entry_assessments_v1.cpp
  src/war_entry_assessments_v1_serializer.cpp
  src/war_entry_assessments_v1_mailbox.cpp
  src/zhongguo_case_snapshot_v1.cpp
  src/zhongguo_case_snapshot_v1_mailbox.cpp
  src/zhongguo_case_snapshot_v1_serializer.cpp
  src/zhongguo_ai_owned_case_snapshot_v1.cpp
  src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
  src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
  src/zhongguo_b2_pip_snapshot_v1.cpp
  src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
  src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
  src/zhongguo_incident_snapshot_v1.cpp
  src/zhongguo_incident_snapshot_v1_mailbox.cpp
  src/zhongguo_incident_snapshot_v1_serializer.cpp
  src/zhongguo_manager_governance_snapshot_v1.cpp
  src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp
  src/zhongguo_manager_governance_snapshot_v1_serializer.cpp
  src/zhongguo_manager_subordinate_selector_v1.cpp
  src/zhongguo_manager_subordinate_selector_v1_serializer.cpp
  src/zhongguo_promotion_compensation_postcondition_v1.cpp
  src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
  src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
  src/zhongguo_projects_metrics_postcondition_v1.cpp
  src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
  src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
  src/zhongguo_scoreboard_action_v1.cpp
  src/zhongguo_scoreboard_action_v1_mailbox.cpp
  src/zhongguo_scoreboard_production_v1.cpp
  src/zhongguo_scoreboard_state_v1.cpp
  src/zhongguo_scoreboard_state_v1_mailbox.cpp
  src/zhongguo_scoreboard_state_v1_serializer.cpp
  src/zhongguo_workforce_collective_snapshot_v1.cpp
  src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
  src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
  src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
  src/zhongguo_result_case_snapshot_v1.cpp
  src/zhongguo_result_case_snapshot_v1_mailbox.cpp
  src/zhongguo_result_case_snapshot_v1_serializer.cpp
)
target_link_libraries(xar_ck3_bridge PRIVATE xar_bridge_protocol bcrypt)
target_compile_definitions(xar_ck3_bridge PRIVATE
  XAR_BRIDGE_VERSION="${PROJECT_VERSION}"
)
if(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1)
  # The fifth caller-local guard is meaningful only after the four previously
  # live-proven startup faults are contained.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1)
  # This successor seam is reached only after all five previous live-proven
  # startup faults are contained in the same exact-build bridge.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
  )
endif()
if(XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1)
  # Read-only successor observer. It is reached in the frozen G2 startup
  # candidate only after the six independently live-proven guards.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1=1
    XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1)
  # Candidate-only read-only verifier diagnostics. The action result and
  # hello capability list remain fail-closed until a retained live artifact
  # is reviewed and production promotion is made as a separate source change.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1=1
  )
endif()
if(XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1)
  # Private candidate-only exposure of the already wired read-only provider.
  # The default build remains unadvertised until a retained paused-live
  # source -> action -> provider-result artifact is reviewed separately.
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1 OR
   XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
  )
endif()
if(XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1=1
    XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1=1
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

if(XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1)
  add_executable(xar_ck3_raiktor_war_bound_private_capture_v1
    research/raiktor_war_bound_private_capture_v1.cpp
  )
  target_compile_definitions(
    xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  target_link_libraries(
    xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_war_bound_private_capture_v1 PRIVATE
      /W4 /permissive- /EHsc)
  endif()
endif()

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
  if(XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1)
    add_test(
      NAME xar_ck3_native_bridge_raiktor_war_bound_private_capture_v1
      COMMAND xar_ck3_raiktor_war_bound_private_capture_v1 --self-test
    )
  endif()

  add_executable(xar_bridge_protocol_test
    src/protocol_test.cpp
  )
  target_include_directories(xar_bridge_protocol_test PRIVATE include)
  target_link_libraries(xar_bridge_protocol_test PRIVATE xar_bridge_protocol)
  if(MSVC)
    target_compile_options(xar_bridge_protocol_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_protocol
    COMMAND xar_bridge_protocol_test
  )

  add_executable(xar_ck3_event_window_context_v1_serializer_test
    src/event_window_context_v1_serializer.cpp
    src/event_window_context_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_event_window_context_v1_serializer_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_event_window_context_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_event_window_context_v1_serializer
    COMMAND xar_ck3_event_window_context_v1_serializer_test
  )

  add_executable(xar_ck3_event_window_context_v1_test
    src/battle_terminal_journal_v1.cpp
    src/ck3_11906.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/event_window_context_v1.cpp
    src/event_window_context_v1_mailbox.cpp
    src/event_window_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_event_window_context_v1_test PRIVATE include)
  target_link_libraries(
    xar_ck3_event_window_context_v1_test PRIVATE bcrypt)
  target_compile_definitions(
    xar_ck3_event_window_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_event_window_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_event_window_context_v1
    COMMAND xar_ck3_event_window_context_v1_test
  )

  add_executable(xar_ck3_game_access_test
    src/actual_contact_scope_v1_mailbox.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    src/battle_reinforcement_assignment_v1_mailbox.cpp
    src/battle_terminal_journal_v1.cpp
    src/battle_terminal_transition_v1_mailbox.cpp
    src/battle_transition_v1_mailbox.cpp
    src/ck3_11906.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
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
    src/campaign_root_context_v1.cpp
    src/campaign_root_context_v1_mailbox.cpp
    src/combat_simulation_inputs_v3_mailbox.cpp
    src/game_adapter.cpp
    src/loaded_feature_manifest_v1.cpp
    src/loaded_feature_manifest_v1_mailbox.cpp
    src/pending_character_interaction_context_v1.cpp
    src/pending_character_interaction_context_v1_mailbox.cpp
    src/ck3_11906_adapter.cpp
    src/ck3_11906.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/combat_v3.cpp
    src/route_contact_horizon_v1_mailbox.cpp
    src/tactical_daily_sentinel_v1.cpp
    src/war_entry_assessments_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_case_snapshot_v1_mailbox.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
    src/zhongguo_b2_pip_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
    src/zhongguo_incident_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1_mailbox.cpp
    src/zhongguo_manager_governance_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp
    src/zhongguo_manager_subordinate_selector_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_mailbox.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_state_v1_mailbox.cpp
    src/zhongguo_workforce_collective_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
    src/zhongguo_result_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1_mailbox.cpp
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

  add_executable(xar_ck3_tactical_daily_sentinel_v1_test
    src/tactical_daily_sentinel_v1.cpp
    src/tactical_daily_sentinel_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_tactical_daily_sentinel_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_tactical_daily_sentinel_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_tactical_daily_sentinel_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_tactical_daily_sentinel_v1
    COMMAND xar_ck3_tactical_daily_sentinel_v1_test
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

  add_executable(xar_ck3_campaign_root_context_v1_test
    src/campaign_root_context_v1.cpp
    src/campaign_root_context_v1_serializer.cpp
    src/campaign_root_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1
    COMMAND xar_ck3_campaign_root_context_v1_test
  )

  add_executable(xar_ck3_campaign_root_context_v1_mailbox_test
    src/campaign_root_context_v1_mailbox.cpp
    src/campaign_root_context_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1_mailbox
    COMMAND xar_ck3_campaign_root_context_v1_mailbox_test
  )

  add_executable(xar_ck3_campaign_root_context_v1_source_contract_test
    src/campaign_root_context_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_campaign_root_context_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_campaign_root_context_v1_source_contract
    COMMAND xar_ck3_campaign_root_context_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/campaign_root_context_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/campaign_root_context_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/campaign_root_context_v1_source_contract.json
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_case_snapshot_v1_serializer.cpp
    src/zhongguo_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_mailbox_test
    src/zhongguo_case_snapshot_v1_mailbox.cpp
    src/zhongguo_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
    src/zhongguo_ai_owned_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
    src/zhongguo_ai_owned_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_ai_owned_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_ai_owned_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_ai_owned_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-ai-owned-case-snapshot-v1.md
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b1_runtime.py
  )

  add_executable(xar_ck3_zhongguo_case_snapshot_v1_source_contract_test
    src/zhongguo_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_case_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b1_runtime.py
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1.cpp
    src/zhongguo_result_case_snapshot_v1_serializer.cpp
    src/zhongguo_result_case_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1.cpp
    src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
    src/zhongguo_b2_pip_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test
    src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
    src/zhongguo_b2_pip_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test
    src/zhongguo_b2_pip_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_b2_pip_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_b2_pip_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_b2_pip_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/tools/gen_361_b2_runtime.py
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-b2-pip-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1.cpp
    src/zhongguo_incident_snapshot_v1_serializer.cpp
    src/zhongguo_incident_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_manager_governance_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1.cpp
    src/zhongguo_manager_governance_snapshot_v1_serializer.cpp
    src/zhongguo_manager_governance_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_manager_governance_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_manager_governance_snapshot_v1
    COMMAND xar_ck3_zhongguo_manager_governance_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_manager_subordinate_selector_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_ai_owned_case_snapshot_v1.cpp
    src/zhongguo_manager_subordinate_selector_v1.cpp
    src/zhongguo_manager_subordinate_selector_v1_serializer.cpp
    src/zhongguo_manager_subordinate_selector_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_manager_subordinate_selector_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_manager_subordinate_selector_v1
    COMMAND xar_ck3_zhongguo_manager_subordinate_selector_v1_test
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test
    src/zhongguo_incident_snapshot_v1_mailbox.cpp
    src/zhongguo_incident_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test
    src/zhongguo_incident_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  set(ZG361_INCIDENT_PRODUCER_SHARDS
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_capture_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_policy_debt_consume_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_policy_debt_stage_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_portfolio_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_apply_192_198_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_apply_199_204_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_debt_192_198_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_debt_199_204_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_lifecycle_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_x_probe_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_apply_205_210_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_apply_211_216_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_debt_205_210_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_debt_211_216_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_y_lifecycle_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_yz_probe_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_217_222_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_apply_223_228_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_deadline_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_debt_217_222_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_debt_223_228_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_dispatch_effects.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_incident_platform_z_lifecycle_effects.txt
  )
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_incident_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_incident_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_incident_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_incident_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_incident_snapshot_v1_source_contract.json
      ${ZG361_INCIDENT_PRODUCER_SHARDS}
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-incident-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_scoreboard_state_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_scoreboard_state_v1.cpp
    src/zhongguo_scoreboard_state_v1_serializer.cpp
    src/zhongguo_scoreboard_state_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_state_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_state_v1
    COMMAND xar_ck3_zhongguo_scoreboard_state_v1_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_action_v1_test
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_action_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_action_v1
    COMMAND xar_ck3_zhongguo_scoreboard_action_v1_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_production_v1_test
    src/zhongguo_scoreboard_production_v1.cpp
    src/zhongguo_scoreboard_production_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_production_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_production_v1
    COMMAND xar_ck3_zhongguo_scoreboard_production_v1_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_production_v1_candidate_test
    src/zhongguo_scoreboard_production_v1.cpp
    src/zhongguo_scoreboard_production_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1=1)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_production_v1_candidate_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_production_v1_candidate
    COMMAND xar_ck3_zhongguo_scoreboard_production_v1_candidate_test
  )

  add_executable(xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test
    src/zhongguo_scoreboard_action_v1.cpp
    src/zhongguo_scoreboard_action_v1_mailbox.cpp
    src/zhongguo_scoreboard_action_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_scoreboard_action_v1_mailbox
    COMMAND xar_ck3_zhongguo_scoreboard_action_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_workforce_collective_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1.cpp
    src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
    src/zhongguo_workforce_collective_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1
    COMMAND xar_ck3_zhongguo_workforce_collective_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1
    COMMAND xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_test
  )

  add_executable(xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_promotion_compensation_postcondition_v1
    COMMAND xar_ck3_zhongguo_promotion_compensation_postcondition_v1_test
  )

  add_executable(
    xar_ck3_zg_promo_comp_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp
    src/zhongguo_promotion_compensation_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_promo_comp_mailbox_v1_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_promo_comp_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_promo_comp_mailbox_v1_test
      PRIVATE /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_promotion_compensation_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_promo_comp_mailbox_v1_test
  )

  add_executable(xar_ck3_zhongguo_projects_metrics_postcondition_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
    src/zhongguo_projects_metrics_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_projects_metrics_postcondition_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_projects_metrics_postcondition_v1
    COMMAND xar_ck3_zhongguo_projects_metrics_postcondition_v1_test
  )

  add_executable(xar_ck3_zg_projects_metrics_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1.cpp
    src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp
    src/zhongguo_projects_metrics_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_projects_metrics_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_projects_metrics_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_projects_metrics_mailbox_v1_test
  )

  add_executable(xar_ck3_zg_career_hc_workforce_v1_test
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_career_hc_workforce_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_career_hc_workforce_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_career_hc_workforce_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_career_hc_workforce_postcondition_v1
    COMMAND xar_ck3_zg_career_hc_workforce_v1_test
  )

  add_executable(xar_ck3_zg_career_hc_workforce_mailbox_v1_test
    src/main_thread_query_mailbox_v1.cpp
    src/zhongguo_case_snapshot_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_serializer.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp
    src/zhongguo_career_hc_workforce_postcondition_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zg_career_hc_workforce_mailbox_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_career_hc_workforce_postcondition_v1_mailbox
    COMMAND xar_ck3_zg_career_hc_workforce_mailbox_v1_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
    src/zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_normal_exit_snapshot_v1_source_contract
    COMMAND
      xar_ck3_zhongguo_workforce_normal_exit_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_workforce_normal_exit_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_workforce_normal_exit_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-workforce-normal-exit-snapshot-v1.md
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_workforce_normal_exit_fact_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_workforce_rehire_fact_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_b2_075_exit_offer_effects.txt
  )

  add_executable(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
    src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
    src/zhongguo_workforce_collective_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_workforce_collective_snapshot_v1_mailbox_test
  )

  add_executable(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
    src/zhongguo_workforce_collective_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_workforce_collective_snapshot_v1_source_contract
    COMMAND
      xar_ck3_zhongguo_workforce_collective_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_workforce_collective_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_workforce_collective_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../docs/ck3-native-ai/zhongguo-workforce-collective-snapshot-v1.md
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test
    src/zhongguo_result_case_snapshot_v1_mailbox.cpp
    src/zhongguo_result_case_snapshot_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1_mailbox
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_mailbox_test
  )

  add_executable(xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
    src/zhongguo_result_case_snapshot_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
    PRIVATE include)
  if(MSVC)
    target_compile_options(
      xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1_source_contract
    COMMAND xar_ck3_zhongguo_result_case_snapshot_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/zhongguo_result_case_snapshot_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/zhongguo_result_case_snapshot_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/zhongguo_result_case_snapshot_v1_source_contract.json
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/common/scripted_effects/zg361_effects.txt
      ${CMAKE_CURRENT_SOURCE_DIR}/../../mod_zhongguo_style/events/zg361_events.txt
  )

  add_executable(xar_ck3_title_map_navigation_v1_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1
    COMMAND xar_ck3_title_map_navigation_v1_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_camera_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_camera.cpp
    src/title_map_navigation_v1_camera_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_camera_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_camera_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_camera_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_camera
    COMMAND xar_ck3_title_map_navigation_v1_camera_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_serializer_test
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_camera.cpp
    src/title_map_navigation_v1_serializer.cpp
    src/title_map_navigation_v1_serializer_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_serializer_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_serializer_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_serializer_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_serializer
    COMMAND xar_ck3_title_map_navigation_v1_serializer_test
  )

  add_executable(xar_ck3_title_map_navigation_v1_mailbox_test
    src/main_thread_query_mailbox_v1.cpp
    src/title_map_navigation_v1.cpp
    src/title_map_navigation_v1_mailbox.cpp
    src/title_map_navigation_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_title_map_navigation_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_title_map_navigation_v1_mailbox
    COMMAND xar_ck3_title_map_navigation_v1_mailbox_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_test
    src/loaded_feature_manifest_v1.cpp
    src/loaded_feature_manifest_v1_serializer.cpp
    src/loaded_feature_manifest_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1
    COMMAND xar_ck3_loaded_feature_manifest_v1_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_mailbox_test
    src/loaded_feature_manifest_v1_mailbox.cpp
    src/loaded_feature_manifest_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1_mailbox
    COMMAND xar_ck3_loaded_feature_manifest_v1_mailbox_test
  )

  add_executable(xar_ck3_loaded_feature_manifest_v1_source_contract_test
    src/loaded_feature_manifest_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_loaded_feature_manifest_v1_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_loaded_feature_manifest_v1_source_contract
    COMMAND xar_ck3_loaded_feature_manifest_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/loaded_feature_manifest_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1_mailbox.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/main_thread_query_mailbox_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/main_thread_query_mailbox_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_11906_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/loaded_feature_manifest_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/loaded_feature_manifest_v1_source_contract.json
  )

  add_executable(xar_ck3_pending_character_interaction_context_v1_test
    src/pending_character_interaction_context_v1.cpp
    src/pending_character_interaction_context_v1_serializer.cpp
    src/pending_character_interaction_context_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_character_interaction_context_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_character_interaction_context_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_character_interaction_context_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1
    COMMAND xar_ck3_pending_character_interaction_context_v1_test
  )

  add_executable(xar_ck3_pending_character_interaction_context_v1_mailbox_test
    src/pending_character_interaction_context_v1_mailbox.cpp
    src/pending_character_interaction_context_v1_mailbox_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_character_interaction_context_v1_mailbox_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1_mailbox
    COMMAND xar_ck3_pending_character_interaction_context_v1_mailbox_test
  )

  add_executable(xar_ck3_pending_interaction_v1_source_contract_test
    src/pending_character_interaction_context_v1_source_contract_test.cpp
  )
  target_include_directories(
    xar_ck3_pending_interaction_v1_source_contract_test
    PRIVATE include)
  target_compile_definitions(
    xar_ck3_pending_interaction_v1_source_contract_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_pending_interaction_v1_source_contract_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_pending_character_interaction_context_v1_source_contract
    COMMAND xar_ck3_pending_interaction_v1_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/include/xar_bridge/pending_character_interaction_context_v1.hpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/pending_character_interaction_context_v1.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/src/pending_character_interaction_context_v1_serializer.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/research/pending_character_interaction_context_v1_abi.json
      ${CMAKE_CURRENT_SOURCE_DIR}/research/fixtures/pending_character_interaction_context_v1_source_contract.json
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
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_war_termination_same_frame_source_contract_test
    src/war_termination_same_frame_source_contract_test.cpp
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_war_termination_same_frame_source_contract_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_war_termination_same_frame_source_contract
    COMMAND xar_ck3_war_termination_same_frame_source_contract_test
      ${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp
  )

  add_executable(xar_ck3_raiktor_surrender_six_domain_v1_test
    src/raiktor_surrender_six_domain_v1.cpp
    src/raiktor_surrender_six_domain_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_surrender_six_domain_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_surrender_six_domain_v1
    COMMAND xar_ck3_raiktor_surrender_six_domain_v1_test
  )

  add_executable(xar_ck3_raiktor_surrender_truce_v1_test
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_surrender_truce_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_surrender_truce_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 OR
     XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2)
    target_compile_definitions(
      xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
      XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_V1=1
    )
  endif()
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_surrender_truce_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_surrender_truce_v1
    COMMAND xar_ck3_raiktor_surrender_truce_v1_test
  )

  add_executable(xar_ck3_g2_truce_native_callsite_observer_v1_test
    src/g2_truce_native_callsite_observer_v1.cpp
    src/g2_truce_native_callsite_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_g2_truce_native_callsite_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_g2_truce_native_callsite_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_g2_truce_native_callsite_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_g2_truce_native_callsite_observer_v1
    COMMAND xar_ck3_g2_truce_native_callsite_observer_v1_test
  )

  add_executable(xar_ck3_g2_truce_preview_entry_observer_v1_test
    src/g2_truce_preview_entry_observer_v1.cpp
    src/g2_truce_preview_entry_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_g2_truce_preview_entry_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_g2_truce_preview_entry_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_g2_truce_preview_entry_observer_v1_test
      PRIVATE /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_g2_truce_preview_entry_observer_v1
    COMMAND xar_ck3_g2_truce_preview_entry_observer_v1_test
  )

  add_executable(xar_ck3_raiktor_war_bound_regiment_v1_test
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_war_bound_regiment_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_raiktor_war_bound_regiment_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_raiktor_war_bound_regiment_v1
    COMMAND xar_ck3_raiktor_war_bound_regiment_v1_test
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

  add_executable(xar_ck3_startup_widget_null_flag_call_guard_v1_test
    src/startup_widget_null_flag_call_guard_v1.cpp
    src/startup_widget_null_flag_call_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_widget_null_flag_call_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_widget_null_flag_call_guard_v1
    COMMAND xar_ck3_startup_widget_null_flag_call_guard_v1_test
  )

  add_executable(xar_ck3_startup_rbx_null_call_guard_v1_test
    src/startup_rbx_null_call_guard_v1.cpp
    src/startup_rbx_null_call_guard_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_startup_rbx_null_call_guard_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_startup_rbx_null_call_guard_v1
    COMMAND xar_ck3_startup_rbx_null_call_guard_v1_test
  )

  add_executable(xar_ck3_phase2_completion_observer_v1_test
    src/phase2_completion_observer_v1.cpp
    src/phase2_completion_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_completion_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_completion_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_completion_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_completion_observer_v1
    COMMAND xar_ck3_phase2_completion_observer_v1_test
  )

  add_executable(xar_ck3_phase2_wrapper_entry_observer_v1_test
    src/phase2_wrapper_entry_observer_v1.cpp
    src/phase2_wrapper_entry_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_wrapper_entry_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_wrapper_entry_observer_v1
    COMMAND xar_ck3_phase2_wrapper_entry_observer_v1_test
  )

  add_executable(xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test
    src/phase2_wrapper_consumer_edge_observer_v1.cpp
    src/phase2_wrapper_consumer_edge_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_wrapper_consumer_edge_observer_v1
    COMMAND xar_ck3_phase2_wrapper_consumer_edge_observer_v1_test
  )

  add_executable(xar_ck3_phase2_post_call_observer_v1_test
    src/phase2_post_call_observer_v1.cpp
    src/phase2_post_call_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_post_call_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_post_call_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_post_call_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_post_call_observer_v1
    COMMAND xar_ck3_phase2_post_call_observer_v1_test
  )

  add_executable(xar_ck3_phase2_post_call_list_identity_observer_v1_test
    src/phase2_post_call_list_identity_observer_v1.cpp
    src/phase2_post_call_list_identity_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_post_call_list_identity_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_post_call_list_identity_observer_v1
    COMMAND xar_ck3_phase2_post_call_list_identity_observer_v1_test
  )

  add_executable(xar_ck3_phase2_producer_identity_observer_v1_test
    src/phase2_producer_identity_observer_v1.cpp
    src/phase2_producer_identity_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_phase2_producer_identity_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_phase2_producer_identity_observer_v1
    COMMAND xar_ck3_phase2_producer_identity_observer_v1_test
  )

  add_executable(xar_ck3_cold_map_vfs_observer_v1_test
    src/cold_map_vfs_observer_v1.cpp
    src/cold_map_vfs_observer_v1_test.cpp
  )
  target_include_directories(
    xar_ck3_cold_map_vfs_observer_v1_test PRIVATE include)
  target_compile_definitions(
    xar_ck3_cold_map_vfs_observer_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
  )
  if(MSVC)
    target_compile_options(
      xar_ck3_cold_map_vfs_observer_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(
    NAME xar_ck3_native_bridge_cold_map_vfs_observer_v1
    COMMAND xar_ck3_cold_map_vfs_observer_v1_test
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

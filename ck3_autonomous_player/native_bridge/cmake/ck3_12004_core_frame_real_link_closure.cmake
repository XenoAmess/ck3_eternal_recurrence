# Source-only target delta for Root review; NOT CONFIGURED OR BUILT.
# Include after the real xar_ck3_12004_core_frame_v1_test declaration.
# Keep production implementations and inherited Runtime/Protocol PUBLIC usage.
target_sources(xar_ck3_12004_core_frame_v1_test PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/src/game_adapter.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/current_first_heir_relationship_v1.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/observed_heir_marriage_private_v1.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/actual_contact_scope_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/battle_control_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/battle_reinforcement_assignment_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/battle_terminal_transition_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/battle_transition_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/campaign_root_context_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/loaded_feature_manifest_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/pending_character_interaction_context_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/player_faction_alerts_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/route_contact_horizon_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/set_played_character_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/steward_develop_county_candidates_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/tactical_daily_sentinel_v1.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/war_entry_assessments_v1.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b1_cycle_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_career_hc_workforce_postcondition_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_case_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_compensation_af5_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_incident_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_manager_governance_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_promotion_source_progress_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_result_case_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_scoreboard_action_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_scoreboard_state_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_collective_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/zhongguo_workforce_owner_snapshot_v1_mailbox.cpp"
)
target_link_libraries(xar_ck3_12004_core_frame_v1_test PRIVATE
  xar_bridge_protocol)
if(MSVC)
  target_compile_options(xar_ck3_12004_core_frame_v1_test PRIVATE /Gy)
  target_link_options(xar_ck3_12004_core_frame_v1_test PRIVATE /OPT:REF)
endif()

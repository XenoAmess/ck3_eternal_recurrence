#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/battle_terminal_journal_v1.hpp"
#include "xar_bridge/actual_contact_scope_v1_mailbox.hpp"
#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <new>
#include <optional>
#include <string>
#include <string_view>

namespace {

using xar::ck3_11906::Bindings;

constexpr std::int32_t kInitialPendingInteractionId = 0x01000001;
constexpr std::int32_t kSignedPendingInteractionId =
    static_cast<std::int32_t>(0x81000001U);
constexpr std::int32_t kStaleSignedPendingInteractionId =
    static_cast<std::int32_t>(0x82000001U);

std::array<std::byte, 0x78> g_player{};
std::array<std::byte, 0x1C2> g_active_event{};
std::array<std::byte, 0x1C0> g_event_data{};
std::array<std::byte, 0x40> g_pending_storage{};
std::array<std::byte, 0x20> g_pending_slots{};
std::array<std::byte, 0x5C8> g_unrelated_pending_interaction{};
std::array<std::byte, 0x5C8> g_pending_interaction{};
std::array<std::byte, 0x40> g_character_storage{};
std::array<std::byte, 0x70> g_character_slots{};
std::array<std::byte, 0x1D0> g_played_character{};
std::array<std::byte, 0x1D0> g_target_character{};
std::array<std::byte, 0x1D0> g_dead_character{};
std::array<std::byte, 0x1D0> g_generation_mismatch_character{};
std::array<std::byte, 0x1D0> g_ally_character{};
std::array<std::byte, 0x200> g_played_land_status{};
std::array<std::byte, 0x40> g_combat_retreat_rule_state{};
std::array<std::byte, 0x300> g_played_character_extension{};
std::array<std::byte, 0x300> g_target_character_extension{};
std::array<std::byte, 0x290> g_dead_character_extension{};
std::array<std::byte, 0x30> g_played_legitimacy_data{};
std::array<std::byte, 0x30> g_target_legitimacy_data{};
std::array<std::byte, 0x08> g_dead_prison_relation{};
std::array<std::byte, 0x40> g_played_family_data{};
std::array<std::int32_t, 2> g_played_spouse_ids{};
std::array<std::byte, 0xE0> g_player_character_entry{};
std::array<std::byte, sizeof(void *)> g_player_character_entries{};
std::array<std::byte, 0x40> g_war_storage{};
std::array<std::byte, 0x20> g_war_slots{};
std::array<std::byte, 0x360> g_war{};
std::array<std::int32_t, 4> g_war_targeted_title_ids{};
std::array<std::byte, 0x40> g_landed_title_storage{};
std::array<std::byte, 0xB0> g_landed_title_slots{};
std::array<std::byte, 0x290> g_targeted_title{};
std::array<std::byte, 0x290> g_targeted_duchy_a_title{};
std::array<std::byte, 0x290> g_targeted_duchy_b_title{};
std::array<std::byte, 0x290> g_capital_county_title{};
std::array<std::byte, 0x290> g_second_county_title{};
std::array<std::byte, 0x290> g_third_county_title{};
std::array<std::byte, 0x290> g_capital_barony_title{};
std::array<std::byte, 0x290> g_second_capital_barony_title{};
std::array<std::byte, 0x290> g_third_capital_barony_title{};
std::array<std::byte, 0x88> g_targeted_title_template{};
std::array<std::byte, 0x88> g_targeted_duchy_a_template{};
std::array<std::byte, 0x88> g_targeted_duchy_b_template{};
std::array<std::byte, 0x88> g_capital_county_template{};
std::array<std::byte, 0x88> g_second_county_template{};
std::array<std::byte, 0x88> g_third_county_template{};
std::array<std::byte, 0x88> g_capital_barony_template{};
std::array<std::byte, 0x88> g_second_capital_barony_template{};
std::array<std::byte, 0x88> g_third_capital_barony_template{};
std::array<std::int32_t, 2> g_targeted_title_vassal_ids{};
std::array<std::int32_t, 2> g_targeted_duchy_a_vassal_ids{};
std::array<std::int32_t, 1> g_targeted_duchy_b_vassal_ids{};
std::array<std::int32_t, 1> g_capital_county_vassal_ids{};
std::array<std::int32_t, 1> g_second_county_vassal_ids{};
std::array<std::int32_t, 1> g_third_county_vassal_ids{};
std::array<std::int32_t, 1> g_targeted_title_succession_ids{};
std::array<std::byte, 0x10> g_attacker_participant{};
std::array<std::byte, 0x10> g_third_attacker_participant{};
std::array<std::byte, 0x10> g_defender_participant{};
std::array<std::byte, 2 * sizeof(void *)> g_attacker_participants{};
std::array<std::byte, sizeof(void *)> g_defender_participants{};
std::array<std::byte, 0x40> g_army_storage{};
std::array<std::byte, 0x40> g_army_slots{};
std::array<std::byte, 0x40> g_siege_storage{};
std::array<std::byte, 0x20> g_siege_slots{};
std::array<std::byte, 0x450> g_siege{};
std::array<std::byte, 0x200> g_player_army{};
std::array<std::byte, 0x200> g_enemy_army{};
std::array<std::byte, 0x200> g_third_army{};
std::array<std::byte, 0x40> g_internal_army_storage{};
std::array<std::byte, 0x140> g_internal_army_slots{};
std::array<std::byte, 0x130> g_player_internal_army{};
std::array<std::byte, 0x130> g_enemy_internal_army{};
std::array<std::byte, 0x130> g_third_internal_army{};
std::array<std::int32_t, 2> g_player_regiment_ids{};
std::array<std::int32_t, 2> g_enemy_regiment_ids{};
std::array<std::byte, 0x40> g_regiment_storage{};
std::array<std::byte, 0x50> g_regiment_slots{};
std::array<std::byte, 0x150> g_player_regiment_0{};
std::array<std::byte, 0x150> g_player_regiment_1{};
std::array<std::byte, 0x150> g_enemy_regiment_0{};
std::array<std::byte, 0x150> g_enemy_regiment_1{};
std::array<std::uintptr_t, 2> g_regiment_identity_vtable{};
std::array<std::uintptr_t, 2> g_character_validity_vtable{};
std::array<std::uintptr_t, 1> g_database_object_validity_vtable{};
std::array<std::uintptr_t, 1> g_database_object_absent_vtable{};
std::array<std::uintptr_t, 1> g_combat_type_validity_vtable{};
std::array<std::byte, 0x2B0> g_bowmen_type{};
std::array<std::byte, 0x2B0> g_armored_horsemen_type{};
std::array<std::byte, 0x2B0> g_absent_maa_type{};
std::array<std::byte, 0xA10> g_player_regiment_0_inner_type{};
std::array<std::byte, 0xA10> g_player_regiment_1_inner_type{};
std::array<std::byte, 0xA10> g_enemy_regiment_0_inner_type{};
std::array<std::byte, 0xA10> g_enemy_regiment_1_inner_type{};
std::array<std::byte, 0x20> g_player_counter_targets{};
std::array<std::byte, 0x20> g_enemy_counter_targets{};
std::array<std::byte, 0xF18> g_combat_rules{};
std::array<std::byte, 0x100> g_played_knight_link{};
std::array<std::byte, 0x100> g_target_knight_link{};
constexpr char g_armored_horsemen_key[] = "armored_horsemen";
std::array<std::byte, 0x778> g_hills_terrain{};
std::array<std::byte, 0x778> g_plains_terrain{};
std::array<std::byte, 0x40> g_combat_storage{};
std::array<std::byte, 0x20> g_combat_slots{};
std::array<std::byte, 0x718> g_player_combat{};
std::array<std::byte, 0x40> g_contact_combat_storage{};
std::array<std::byte, 0x40> g_contact_combat_slots{};
std::array<std::byte, 0x718> g_contact_combat_0{};
std::array<std::byte, 0x718> g_contact_combat_1{};
std::array<std::int32_t, 1> g_contact_combat_0_attacker_armies{};
std::array<std::int32_t, 1> g_contact_combat_0_defender_armies{};
std::array<std::int32_t, 2> g_contact_combat_1_attacker_armies{};
std::array<std::int32_t, 1> g_contact_combat_1_defender_armies{};
std::array<std::byte, 0x60> g_battle_attacker_levy_entry{};
std::array<std::byte, 0x60> g_battle_attacker_maa_entry{};
std::array<std::byte, 0x60> g_battle_defender_levy_entry{};
std::array<std::byte, 0x60> g_battle_defender_maa_entry{};
std::array<std::byte, 0x18> g_battle_attacker_hard_row{};
std::array<std::byte, 0x18> g_battle_defender_hard_row{};
std::array<std::byte, 0x40> g_contact_battle_result_storage{};
std::array<std::byte, 0x20> g_contact_battle_result_slots{};
std::array<std::byte, 0xC8> g_contact_battle_result{};
std::array<std::uintptr_t, 2> g_contact_battle_result_vtable{};
std::array<std::uintptr_t, 7> g_contact_province_vtable{};
bool g_contact_prior_province_valid = true;
bool g_battle_mutate_on_side_strength = false;
std::int32_t g_battle_side_strength_calls = 0;
std::int32_t g_battle_regiment_strength_calls = 0;
bool g_can_order_combat_retreat_result = true;
bool g_can_order_combat_retreat_arguments_valid = true;
std::int32_t g_can_order_combat_retreat_calls = 0;
std::int32_t g_minimum_days_before_manual_retreat = 14;
std::array<std::byte, 0x10> g_player_move_route_info_0{};
std::array<std::byte, 0x10> g_player_move_route_info_1{};
std::array<std::byte, 0x10> g_player_move_route_info_2{};
std::array<void *, 3> g_player_move_path{};
std::array<std::byte, 0x10> g_preview_move_route_info_0{};
std::array<std::byte, 0x10> g_preview_move_route_info_1{};
std::array<std::byte, 0x10> g_preview_move_route_info_2{};
std::array<std::byte, 0x10> g_enemy_move_route_info_0{};
std::array<void *, 1> g_enemy_move_path{};
std::array<void *, 3> g_preview_move_path{};
std::array<std::byte, 0x10> g_boundary_move_route_info_0{};
std::array<std::byte, 0x10> g_boundary_move_route_info_1{};
std::array<std::byte, 0x10> g_boundary_move_route_info_2{};
std::array<std::byte, 0x10> g_boundary_move_route_info_3{};
std::array<void *, 4> g_boundary_move_path{};
std::array<std::byte, 0x40> g_ai_coordinator_storage{};
std::array<std::byte, 0x20> g_ai_coordinator_slots{};
std::array<std::byte, 0x70> g_ai_coordinator{};
std::array<std::byte, 0x08> g_ai_coordinator_fallback{};
std::array<std::byte, 0x98> g_ai_unit_stack{};
std::array<std::byte, 0x58> g_ai_selected_subunit{};
std::array<std::byte, 0x58> g_ai_sibling_subunit{};
std::array<void *, 1> g_ai_coordinator_unit_stacks{};
std::array<void *, 3> g_ai_support_provinces{};
std::array<std::int32_t, 2> g_ai_parent_cunit_ids{};
std::array<void *, 2> g_ai_parent_subunits{};
std::array<std::int32_t, 1> g_ai_selected_cunit_ids{};
std::array<std::int32_t, 1> g_ai_sibling_cunit_ids{};
void *g_ai_coordinator_storage_pointer = nullptr;
void *g_ai_coordinator_fallback_pointer = nullptr;
std::int32_t g_route_edge_duration_calls = 0;
bool g_route_edge_duration_drift = false;
std::int64_t g_route_edge_duration_raw = 150'000;
std::array<std::byte, 0x20> g_player_province{};
std::array<std::byte, 0x20> g_enemy_province{};
std::array<std::byte, 0x20> g_enemy_default_raise_province{};
std::array<std::byte, 0xC0> g_player_map_node{};
std::array<std::byte, 0xC0> g_enemy_map_node{};
std::array<std::byte, 0xC0> g_route_map_node_4{};
std::array<std::byte, 0xC0> g_route_map_node_5{};
std::array<std::byte, 0x10> g_route_origin_info_2{};
std::array<std::byte, 0x10> g_route_origin_info_3{};
std::array<std::byte, 0x10> g_route_origin_info_4{};
std::array<std::byte, 0x10> g_route_origin_info_5{};
std::array<std::byte, 2 * 0x30> g_route_adjacencies_2{};
std::array<std::byte, 0x30> g_route_adjacencies_3{};
std::array<std::byte, 2 * 0x30> g_route_adjacencies_4{};
std::array<std::byte, 2 * 0x30> g_route_adjacencies_5{};
std::array<std::byte, 0x30> g_player_target_adjacency{};
std::array<std::byte, 0x30> g_enemy_target_adjacency{};
std::array<std::byte, 0x20> g_contact_province_gate{};
std::array<std::byte, 0x1C8> g_contact_game_mode_root{};
std::array<std::byte, 0x30> g_contact_game_mode{};
std::array<std::int32_t, 3> g_contact_province_unit_ids{};
std::array<std::int32_t, 2> g_contact_province_combat_ids{};
std::array<std::byte, 0x860> g_war_objective_province{};
std::array<std::byte, 0x860> g_second_war_objective_province{};
std::array<std::byte, 0x860> g_third_war_objective_province{};
std::array<std::byte, 7 * sizeof(void *)> g_provinces{};
std::array<std::byte, 0x78> g_casus_belli_database{};
std::array<void *, 2> g_casus_belli_types{};
std::array<std::byte, 0x1720> g_casus_belli_type_0{};
std::array<std::byte, 0x1720> g_casus_belli_type_1{};
constexpr char g_casus_belli_key_0[] = "claim_cb";
constexpr char g_casus_belli_key_1[] = "county_conquest_cb";
constexpr char g_raiktor_casus_belli_key[] = "raiktor_claim_cb";
std::array<std::byte, 0x220> g_casus_belli_rule_0{};
std::array<std::byte, 0x220> g_casus_belli_rule_1{};
std::array<std::byte, 0x18> g_casus_belli_scratch{};
std::array<std::byte, 0x1100> g_character_interaction_database{};
std::array<std::byte, 2 * 0x98> g_casus_belli_configurations{};
std::array<std::int32_t, 2> g_casus_belli_titles_0{};
std::array<std::int32_t, 2> g_casus_belli_titles_1{};
std::array<std::byte, 0x2A60> g_declare_war_interaction{};
std::array<std::byte, 8> g_arrange_marriage_interaction{};
std::array<std::byte, 0x30> g_war_declaration{};
std::array<std::int32_t, 8> g_war_declaration_titles{};
std::array<std::byte, 8> g_enforce_demands_marker{};
std::array<std::byte, 8> g_surrender_marker{};
std::array<std::byte, 8> g_white_peace_marker{};
std::array<std::byte, 0x2A50> g_victory_interaction{};
std::array<std::byte, 0x2A50> g_surrender_interaction{};
std::array<std::byte, 0x2A50> g_white_peace_interaction{};
std::array<std::byte, 8> g_auto_accept_trigger{};
std::array<std::uintptr_t, 1> g_character_claim_vtable{};
std::array<void *, 128> g_effect_preview_collector_vtable{};
std::array<void *, 12> g_white_peace_loaded_effect_vtable{};
std::array<void *, 12> g_defeat_loaded_effect_vtable{};
std::array<void *, 12> g_scripted_effect_vtable{};
std::array<void *, 12> g_context_effect_vtable{};
std::array<void *, 1> g_scripted_effect_template_vtable{};
std::array<void *, 1> g_hidden_effect_vtable{};
std::array<std::byte, 0xA0> g_truce_scripted_effect{};
std::array<std::byte, 0x128> g_truce_scripted_effect_template{};
std::array<std::byte, 0x60> g_truce_scripted_default_effect{};
std::array<std::byte, 0x60> g_truce_hidden_effect{};
std::array<std::byte, 0x100> g_truce_context_effect{};
std::array<void *, 13> g_exit_root_effect_children{};
std::array<void *, 19> g_defeat_root_effect_children{};
std::array<void *, 6> g_truce_scripted_default_children{};
std::array<void *, 1> g_truce_hidden_children{};
std::array<void *, 1> g_truce_context_children{};
std::array<std::byte, 0x118> g_prestige_effect_node{};
std::array<std::byte, 0x118> g_legitimacy_effect_node{};
std::array<std::byte, 0x118> g_stress_effect_node{};
std::array<std::byte, 0x118> g_attacker_contribution_effect_node{};
std::array<std::byte, 0x118> g_defender_contribution_effect_node{};
std::array<std::byte, 0x118> g_gold_transfer_effect_node{};
std::array<std::byte, 0x118> g_truce_effect_node{};
std::array<std::byte, 0x118> g_unknown_effect_node{};
std::array<void *, 128> g_raiktor_preview_collector_vtable{};
std::array<void *, 1> g_raiktor_loaded_effect_vtable{};
std::array<void *, 1> g_raiktor_add_hook_effect_vtable{};
std::array<void *, 1> g_raiktor_add_hook_no_toast_effect_vtable{};
std::array<void *, 1> g_raiktor_hook_type_vtable{};
std::array<std::byte, sizeof(void *)> g_raiktor_loaded_effect{};
std::array<std::byte, 0x80> g_raiktor_add_hook_effect_node{};
std::array<std::byte, 0x80> g_raiktor_no_toast_effect_node{};
std::array<std::byte, 0x40> g_raiktor_hook_type_database{};
std::array<std::byte, 0x40> g_raiktor_hook_type_database_after{};
std::array<std::byte, 0x40> g_raiktor_favor_hook_type{};
std::array<std::byte, 0x40> g_raiktor_hook_type_fallback{};
std::array<std::byte, 0x08> g_raiktor_effect_context{};
std::array<std::byte, 0x08> g_raiktor_theocracy_argument{};
std::array<std::byte, 0x08> g_raiktor_unknown_forwarded_argument{};
std::array<std::byte, 0x10> g_exit_attacker_scope{};
std::array<std::byte, 0x10> g_exit_defender_scope{};
std::array<std::byte, 0x10> g_exit_ally_scope{};
std::array<std::byte, 0x08> g_effect_context_data_100{};
std::array<std::byte, 0x08> g_effect_context_data_18{};
std::array<void *, 3> g_effect_context_allocator_vtable{};
std::array<std::byte, sizeof(void *)> g_effect_context_allocator{};
std::array<std::byte, 0x20> g_exit_terms_variable_container{};
std::array<std::byte, 0x20> g_exit_terms_variable_row{};
std::array<std::byte, 0x20> g_global_variable_container{};
std::array<std::byte, 12 * 0x20> g_global_variable_entries{};
std::array<std::byte, 8> g_string_table_marker{};
void *g_pending_storage_pointer = nullptr;
void *g_character_storage_pointer = nullptr;
void *g_army_storage_pointer = nullptr;
void *g_internal_army_storage_pointer = nullptr;
void *g_regiment_storage_pointer = nullptr;
void *g_combat_storage_pointer = nullptr;
void *g_contact_combat_storage_pointer = nullptr;
void *g_contact_battle_result_storage_pointer = nullptr;
void *g_contact_battle_result_fallback_pointer = nullptr;
void *g_contact_game_mode_pointer = nullptr;
void *g_siege_storage_pointer = nullptr;
void *g_expected_event_manager = nullptr;
bool g_has_active_event = true;
bool g_has_local_player = false;
std::int32_t g_current_event_calls = 0;
std::int32_t g_war_participant_calls = 0;
std::int32_t g_settlement_accessor_calls = 0;
bool g_submit_called = false;
bool g_submit_result = true;
bool g_pending_visibility_result = true;
bool g_pending_accept_validation_result = true;
std::int32_t g_expected_pending_command_id = kInitialPendingInteractionId;
std::int32_t g_pending_visibility_calls = 0;
std::int32_t g_pending_visibility_fail_on_call = -1;
std::int32_t g_pending_mutate_generation_on_call = -1;
std::int32_t g_pending_clear_notification_on_call = -1;
std::int32_t g_pending_accept_validation_calls = 0;
bool g_raise_construct_called = false;
bool g_raise_validate_called = false;
bool g_raise_validate_result = true;
bool g_raise_destroy_called = false;
bool g_move_path_initialized = false;
bool g_move_destroy_called = false;
std::int32_t g_move_mode_result = 5;
bool g_preview_origin_available = true;
void *g_preview_effective_origin = nullptr;
bool g_preview_origin_called = false;
std::uint8_t g_preview_origin_mode_is_one = 0xFF;
bool g_preview_path_context_constructed = false;
bool g_preview_route_built = false;
bool g_preview_route_build_result = true;
std::int32_t g_preview_route_count = 3;
std::int32_t g_route_duration_calls = 0;
bool g_route_duration_prefix_zeroed = true;
bool g_route_duration_failure = false;
bool g_route_duration_late_zero_speed_accumulation = false;
bool g_route_duration_zero_current_edge_correction = false;
std::int64_t g_route_land_speed_raw = 100'000;
std::int64_t g_route_naval_speed_raw = 100'000;
std::int64_t g_route_current_edge_speed_raw = 100'000;
std::int32_t g_player_army_state_code = 2;
std::int32_t g_enemy_army_state_code = 6;
std::int32_t g_army_current_soldiers_calls = 0;
std::int32_t g_army_maximum_soldiers_calls = 0;
std::int32_t g_effective_stats_calls = 0;
void *g_effective_stats_failed_regiment = nullptr;
std::int32_t g_character_modifier_calls = 0;
std::int32_t g_counter_current_chunk_calls = 0;
std::int32_t g_counter_resolution_calls = 0;
bool g_knight_effectiveness_context_available = true;
bool g_holding_defender_result = true;
void *g_last_holding_defender_owner = nullptr;
std::int32_t g_commander_min_roll = 0;
std::int32_t g_commander_max_roll = 10;
std::int32_t g_knight_damage_per_prowess = 50;
std::int32_t g_knight_toughness_per_prowess = 10;
std::int32_t g_minimum_combat_width = 100;
std::int64_t g_base_combat_width_ratio = 100'000;
bool g_siege_alive = true;
std::int64_t g_siege_progress_raw = 25'000;
std::int64_t g_siege_total_work_raw = 10'000'000;
std::int32_t g_siege_days_left = 12;
std::int64_t g_assault_daily_progress_raw = 340'000;
std::int32_t g_assault_daily_casualties = 16;
bool g_assault_progress_available = true;
bool g_start_assault_validate_allowed = true;
bool g_stop_assault_validate_allowed = true;
bool g_start_assault_validate_called = false;
bool g_stop_assault_validate_called = false;
bool g_assault_clone_called = false;
bool g_assault_destroy_called = false;
std::array<std::byte, 0x30> g_assault_cloned_command{};
bool g_character_command_kind_allowed = true;
bool g_army_move_mode_allowed = true;
bool g_move_validation_allowed = true;
bool g_disband_validate_called = false;
bool g_disband_validate_result = true;
bool g_split_validate_called = false;
bool g_split_validate_result = true;
bool g_split_clone_called = false;
bool g_split_destroy_called = false;
std::array<std::byte, 0x30> g_split_cloned_command{};
bool g_merge_factory_called = false;
bool g_merge_append_called = false;
bool g_merge_validate_called = false;
bool g_merge_validate_result = true;
bool g_merge_clone_called = false;
bool g_merge_destroy_called = false;
bool g_merge_source_array_destroyed = false;
std::byte *g_merge_factory_command = nullptr;
std::int32_t *g_merge_owned_source_ids = nullptr;
std::int32_t g_merge_cloned_destination_id = -1;
std::array<std::int32_t, 1> g_merge_cloned_source_ids{};
std::int32_t g_casus_belli_evaluation_calls = 0;
std::int32_t g_casus_belli_configuration_destroy_calls = 0;
bool g_interaction_construct_called = false;
bool g_interaction_refresh_called = false;
bool g_interaction_finalize_called = false;
bool g_interaction_validate_result = true;
bool g_send_interaction_construct_called = false;
std::int32_t g_interaction_destroy_calls = 0;
bool g_interaction_default_construct_called = false;
bool g_war_resolution_construct_called = false;
bool g_war_resolution_attacker_victory = false;
bool g_war_resolution_context_available = true;
std::int32_t g_war_resolution_construct_calls = 0;
std::array<bool, 4> g_war_resolution_absolute_outcomes{};
std::int32_t g_war_score_result = 37;
std::int32_t g_character_claim_read_calls = 0;
std::int32_t g_character_claim_destroy_calls = 0;
bool g_character_claim_title_mismatch = false;
bool g_character_claim_malformed_bool = false;
bool g_exit_terms_fixture_active = false;
bool g_exit_terms_unknown_node = false;
bool g_exit_terms_malformed_contribution = false;
bool g_exit_terms_duplicate_truce = false;
bool g_exit_terms_income_mismatch = false;
bool g_exit_terms_factor_malformed = false;
bool g_exit_terms_collector_lifecycle_valid = true;
bool g_exit_terms_context_lifecycle_valid = true;
std::uint8_t g_exit_terms_answer_status_override = 0xFF;
void *g_exit_terms_effect_context = nullptr;
std::int32_t g_exit_terms_effect_context_construct_calls = 0;
std::int32_t g_exit_terms_effect_context_populate_calls = 0;
std::int32_t g_exit_terms_collector_construct_calls = 0;
std::int32_t g_exit_terms_collector_destroy_calls = 0;
std::int32_t g_exit_terms_traverse_calls = 0;
std::int32_t g_exit_terms_forward_calls = 0;
std::int32_t g_exit_terms_projected_root_preview_calls = 0;
std::array<std::int32_t, 2> g_exit_terms_projected_callback_counts{};
std::int32_t g_exit_terms_hidden_truce_preview_calls = 0;
std::int32_t g_exit_terms_context_teardown_stage = 0;
std::int32_t g_exit_terms_truce_duration_calls = 0;
std::int32_t g_exit_terms_primary_title_calls = 0;
std::int32_t g_exit_terms_monthly_income_calls = 0;
std::int32_t g_exit_terms_answer_calls = 0;
std::vector<std::int32_t> g_exit_terms_answer_destroy_counts;
std::int32_t g_exit_terms_factor_identifier_id = 82;
void *g_raiktor_hook_type_database_pointer = nullptr;
void *g_raiktor_hook_type_fallback_pointer = nullptr;
bool g_raiktor_emit_primary = true;
bool g_raiktor_emit_theocracy = true;
bool g_raiktor_emit_duplicate_primary = false;
bool g_raiktor_emit_theocracy_first = false;
bool g_raiktor_emit_no_toast = false;
bool g_raiktor_emit_wrong_first_scope = false;
bool g_raiktor_emit_wrong_second_scope = false;
bool g_raiktor_emit_payload = false;
bool g_raiktor_emit_unknown_forwarded_argument = false;
bool g_raiktor_lookup_returns_fallback = false;
bool g_raiktor_drift_database = false;
bool g_raiktor_drift_loaded_root = false;
std::byte *g_war_bound_cleanup_drift_target = nullptr;
std::array<std::byte, sizeof(void *)>
    g_war_bound_cleanup_drift_payload{};
std::size_t g_war_bound_cleanup_drift_size = 0;

void ApplyWarBoundCleanupBetweenSamplesDrift() noexcept {
  if (g_war_bound_cleanup_drift_target != nullptr &&
      g_war_bound_cleanup_drift_size > 0 &&
      g_war_bound_cleanup_drift_size <=
          g_war_bound_cleanup_drift_payload.size()) {
    std::memcpy(g_war_bound_cleanup_drift_target,
                g_war_bound_cleanup_drift_payload.data(),
                g_war_bound_cleanup_drift_size);
  }
}
bool g_raiktor_collector_lifecycle_valid = true;
std::int32_t g_raiktor_collector_construct_calls = 0;
std::int32_t g_raiktor_collector_destroy_calls = 0;
std::int32_t g_raiktor_traverse_calls = 0;
std::int32_t g_raiktor_forward_calls = 0;
std::int32_t g_raiktor_hash_calls = 0;
std::int32_t g_raiktor_lookup_calls = 0;
std::int32_t g_white_peace_construct_calls = 0;
std::uint8_t g_last_special_interaction_index = 0;
std::int32_t g_last_special_actor_character_id = -1;
std::int32_t g_last_special_recipient_character_id = -1;
std::int32_t g_auto_accept_trigger_calls = 0;
std::int32_t g_marriage_context_construct_calls = 0;
std::int32_t g_marriage_redirect_calls = 0;
std::int32_t g_marriage_legacy_context_construct_calls = 0;
bool g_marriage_redirect_ready = false;
bool g_marriage_validate_result = true;
bool g_global_variable_container_available = true;
std::int32_t g_script_identifier_lookup_calls = 0;
constexpr std::int32_t kMarriageMatchmakerCharacterId = 0x01000007;
constexpr std::uint16_t kFixtureCharacterEventTargetKind = 4;
constexpr std::int32_t kFixtureDeadCharacterId = 0x01000004;
constexpr std::int32_t kFixtureAllyCharacterId = 0x01000006;
constexpr std::int64_t kFixtureFixedPointScale = 100'000;
constexpr std::array<std::string_view, 12> kSettlementGlobalNames{
    "xa_settlement_ready",
    "xa_settlement_commit_serial",
    "xa_settlement_source_character",
    "xa_settlement_final_score",
    "xa_settlement_score_before_reject",
    "xa_settlement_record_candidate",
    "xa_settlement_old_record",
    "xa_settlement_record_delta",
    "xa_settlement_blessing_count",
    "xa_settlement_refusal_count",
    "xa_settlement_contract_progress",
    "xa_settlement_record_written",
};
enum class ExpectedCommand {
  pause,
  resume,
  speed,
  event_option,
  auto_save,
  reply_accept,
  reply_reject,
  reply_acknowledge,
  raise_troops,
  move_army,
  disband_army,
  split_army_half,
  merge_armies,
  start_assault,
  stop_assault,
  declare_war,
  arrange_marriage,
  enforce_demands,
  surrender_war,
  offer_white_peace,
};
ExpectedCommand g_expected_command = ExpectedCommand::pause;

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &target, std::size_t offset,
           Value value) {
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

template <typename Value>
void StoreBytes(void *target, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte *>(target) + offset, &value,
              sizeof(value));
}

template <typename Value>
Value LoadBytes(const void *source, std::size_t offset) {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(source) + offset,
              sizeof(value));
  return value;
}

void FixtureSetGlobalNumeric(std::size_t index, std::int64_t raw) {
  auto *const entry =
      g_global_variable_entries.data() + index * 0x20;
  StoreBytes(entry, 0x08, static_cast<std::int32_t>(1'000 + index));
  StoreBytes(entry, 0x10, std::uint16_t{1});
  StoreBytes(entry, 0x18, raw);
}

void FixtureSetGlobalCharacter(std::size_t index,
                               std::int32_t character_id) {
  auto *const entry =
      g_global_variable_entries.data() + index * 0x20;
  StoreBytes(entry, 0x08, static_cast<std::int32_t>(1'000 + index));
  StoreBytes(entry, 0x10, kFixtureCharacterEventTargetKind);
  StoreBytes(entry, 0x18, character_id);
}

void *FixtureGetGlobalVariableContainer() {
  ++g_settlement_accessor_calls;
  return g_global_variable_container_available
             ? g_global_variable_container.data()
             : nullptr;
}

xar::ck3_11906::GetGlobalVariableContainer
    g_global_variable_container_accessor =
        FixtureGetGlobalVariableContainer;

void *FixtureGetScriptIdentifierTable() {
  return g_string_table_marker.data();
}

std::int32_t *FixtureLookupScriptIdentifierId(void *table,
                                              std::int32_t *output,
                                              const void *opaque_view) {
  ++g_script_identifier_lookup_calls;
  if (table != g_string_table_marker.data() || output == nullptr ||
      opaque_view == nullptr) {
    return nullptr;
  }
  const char *data = nullptr;
  std::int32_t size = 0;
  std::memcpy(&data, opaque_view, sizeof(data));
  std::memcpy(&size, static_cast<const std::byte *>(opaque_view) + 0x08,
              sizeof(size));
  if (data == nullptr || size < 0) {
    *output = -1;
    return output;
  }
  const std::string_view name(data, static_cast<std::size_t>(size));
  for (std::size_t index = 0; index < kSettlementGlobalNames.size();
       ++index) {
    if (name == kSettlementGlobalNames[index]) {
      *output = static_cast<std::int32_t>(1'000 + index);
      return output;
    }
  }
  *output = -1;
  return output;
}

bool FixtureIsEventTargetValid(const void *event_target) {
  if (event_target == nullptr) {
    return false;
  }
  std::uint16_t kind = 0;
  std::int32_t character_id = -1;
  std::memcpy(&kind, event_target, sizeof(kind));
  std::memcpy(&character_id,
              static_cast<const std::byte *>(event_target) + 0x08,
              sizeof(character_id));
  return kind == kFixtureCharacterEventTargetKind &&
         character_id != -1 && character_id != kFixtureDeadCharacterId;
}

void *FixtureResolveEventTargetObject(const void *event_target) {
  if (event_target == nullptr) {
    return nullptr;
  }
  std::int32_t character_id = -1;
  std::memcpy(&character_id,
              static_cast<const std::byte *>(event_target) + 0x08,
              sizeof(character_id));
  // Model the engine resolver's post-storage gameplay-liveness rejection:
  // the dead object remains generation-valid in storage but cannot be exposed
  // as a live gameplay object.
  return character_id == kFixtureDeadCharacterId ? nullptr
                                                  : g_played_character.data();
}

void *FixtureGetLocalPlayer(void *) {
  return g_has_local_player ? g_player.data() : nullptr;
}

void *FixtureGetCurrentEvent(void *event_manager) {
  ++g_current_event_calls;
  if (event_manager != g_expected_event_manager || !g_has_active_event) {
    return nullptr;
  }
  return g_active_event.data();
}

bool FixtureIsPendingCharacterInteractionForCharacter(
    void *pending_interaction, void *character) {
  ++g_pending_visibility_calls;
  if (g_pending_visibility_calls ==
      g_pending_mutate_generation_on_call) {
    Store(g_pending_interaction, 0x10, std::int32_t{0x02000001});
  }
  if (g_pending_visibility_calls ==
      g_pending_clear_notification_on_call) {
    Store(g_pending_interaction, 0x5C6, std::uint8_t{0});
  }
  return g_pending_visibility_result &&
         g_pending_visibility_calls != g_pending_visibility_fail_on_call &&
         pending_interaction == g_pending_interaction.data() &&
         character == g_played_character.data();
}

bool FixtureValidateReplyCharacterInteractionCommand(void *opaque_command) {
  ++g_pending_accept_validation_calls;
  const auto *command = static_cast<const std::byte *>(opaque_command);
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t pending_id = -1;
  std::int32_t reply = -1;
  std::memcpy(&primary, command, sizeof(primary));
  std::memcpy(&secondary, command + 0x18, sizeof(secondary));
  std::memcpy(&pending_id, command + 0x20, sizeof(pending_id));
  std::memcpy(&reply, command + 0x24, sizeof(reply));
  return g_pending_accept_validation_result && primary == 0x99999999 &&
         secondary == 0xAAAAAAAA &&
         pending_id == g_expected_pending_command_id &&
         reply == 0;
}

bool FixtureContainsWarParticipant(void *container,
                                   std::int32_t character_id) {
  ++g_war_participant_calls;
  auto *const bytes = static_cast<std::byte *>(container);
  void *entries = nullptr;
  std::int32_t count = 0;
  std::memcpy(&entries, bytes + 0x08, sizeof(entries));
  std::memcpy(&count, bytes + 0x14, sizeof(count));
  for (std::int32_t index = 0; entries != nullptr && index < count; ++index) {
    void *entry = nullptr;
    std::memcpy(&entry, static_cast<std::byte *>(entries) +
                            static_cast<std::size_t>(index) * sizeof(void *),
                sizeof(entry));
    std::int32_t candidate_id = -1;
    if (entry != nullptr) {
      std::memcpy(&candidate_id, static_cast<std::byte *>(entry) + 0x08,
                  sizeof(candidate_id));
    }
    if (candidate_id == character_id) {
      return true;
    }
  }
  return false;
}

std::int32_t FixtureGetWarScore(void *war, void *context) {
  return war == g_war.data() && context == nullptr ? g_war_score_result : 0;
}

std::int32_t FixtureGetImprisonmentWarScore(void *war, void *context) {
  return war == g_war.data() && context == nullptr ? 4 : 0;
}

std::int32_t FixtureGetBattleWarScoreBase(void *war, void *context) {
  return war == g_war.data() && context == nullptr ? 10 : 0;
}

std::int32_t FixtureGetBattleWarScoreSide(void *war, bool side,
                                         void *context) {
  if (war != g_war.data() || context != nullptr) {
    return 0;
  }
  return side ? 2 : 3;
}

std::uint64_t FixtureGetOccupationWarScoreSide(void *war, bool side,
                                               void *context) {
  if (war != g_war.data() || context != nullptr) {
    return 0;
  }
  return static_cast<std::uint32_t>(side ? 3 : 8);
}

std::int32_t FixtureGetTickingWarScoreSide(void *war, bool side,
                                          void *context, bool mode) {
  if (war != g_war.data() || context != nullptr || mode == side) {
    return 0;
  }
  return side ? 2 : 7;
}

bool FixtureIsNativeComponentAlive(void *component) {
  return g_siege_alive && component == g_siege.data();
}

std::int64_t *FixtureGetSiegeProgress(void *siege,
                                      std::int64_t *output) {
  if (siege != g_siege.data() || output == nullptr) {
    return nullptr;
  }
  *output = g_siege_progress_raw;
  return output;
}

std::int64_t *FixtureGetSiegeTotalWork(void *siege,
                                       std::int64_t *output) {
  if (siege != g_siege.data() || output == nullptr) {
    return nullptr;
  }
  *output = g_siege_total_work_raw;
  return output;
}

std::int32_t FixtureGetSiegeDaysLeft(void *siege) {
  return siege == g_siege.data()
             ? g_siege_days_left
             : std::numeric_limits<std::int32_t>::max();
}

std::int64_t *FixtureReadAssaultDailyProgress(
    void *siege, std::int64_t *output, std::int32_t eligible_besiegers) {
  if (!g_assault_progress_available || siege != g_siege.data() ||
      output == nullptr || eligible_besiegers != 650) {
    return nullptr;
  }
  *output = g_assault_daily_progress_raw;
  return output;
}

std::int32_t FixtureGetAssaultDailyCasualties(void *siege) {
  return siege == g_siege.data() ? g_assault_daily_casualties : -1;
}

bool FixtureValidateStartAssaultCommand(
    std::int32_t command_kind, std::int32_t played_character_id,
    std::int32_t siege_id, void *error_output) {
  std::int32_t breach_level = -1;
  std::uint8_t assault_active = 0xFF;
  std::memcpy(&breach_level, g_siege.data() + 0x3D8,
              sizeof(breach_level));
  std::memcpy(&assault_active, g_siege.data() + 0x44C,
              sizeof(assault_active));
  g_start_assault_validate_called =
      command_kind == 1 && played_character_id == 0x01000002 &&
      siege_id == 0x01000001 && error_output == nullptr;
  return g_start_assault_validate_called &&
         g_start_assault_validate_allowed && breach_level > 0 &&
         breach_level <= 2 && assault_active == 0;
}

bool FixtureValidateStopAssaultCommand(
    std::int32_t command_kind, std::int32_t played_character_id,
    std::int32_t siege_id, void *error_output) {
  std::uint8_t assault_active = 0xFF;
  std::memcpy(&assault_active, g_siege.data() + 0x44C,
              sizeof(assault_active));
  g_stop_assault_validate_called =
      command_kind == 1 && played_character_id == 0x01000002 &&
      siege_id == 0x01000001 && error_output == nullptr;
  return g_stop_assault_validate_called &&
         g_stop_assault_validate_allowed && assault_active == 1;
}

void *FixtureDestroyAssaultCommand(void *opaque_command,
                                   std::int32_t delete_flags) {
  g_assault_destroy_called = opaque_command != nullptr && delete_flags == 0 &&
                             g_assault_clone_called;
  if (opaque_command != nullptr) {
    std::memset(opaque_command, 0xDD, 0x30);
  }
  return opaque_command;
}

bool FixtureIsProvinceOccupied(void *province) {
  std::int32_t occupying_character_id = -1;
  std::memcpy(&occupying_character_id,
              static_cast<std::byte *>(province) + 0x744,
              sizeof(occupying_character_id));
  return occupying_character_id != -1;
}

std::int32_t FixtureGetProvinceFortLevel(void *province) {
  std::int32_t fort_level = -1;
  std::memcpy(&fort_level, static_cast<std::byte *>(province) + 0x858,
              sizeof(fort_level));
  return fort_level;
}

std::int32_t FixtureGetProvinceGarrisonSize(void *province) {
  if (province == g_war_objective_province.data()) {
    return 500;
  }
  if (province == g_second_war_objective_province.data()) {
    return 0;
  }
  return province == g_third_war_objective_province.data() ? 800 : -1;
}

std::int32_t FixtureGetProvinceBesiegingStrength(void *province) {
  if (province == g_war_objective_province.data()) {
    return 650;
  }
  if (province == g_second_war_objective_province.data()) {
    return 0;
  }
  return province == g_third_war_objective_province.data() ? 900 : -1;
}

void *FixtureResolveDefaultRaiseProvince(void *character) {
  if (character == g_played_character.data()) {
    return g_player_province.data();
  }
  return character == g_target_character.data()
             ? g_enemy_default_raise_province.data()
             : nullptr;
}

void *FixtureConstructRaiseTroopsCommand(void *opaque_command,
                                         std::int32_t character_id,
                                         const void *opaque_entry) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  std::int32_t province_id = -1;
  std::int32_t regiment_id = 0;
  std::memcpy(&province_id, opaque_entry, sizeof(province_id));
  std::memcpy(&regiment_id,
              static_cast<const std::byte *>(opaque_entry) + 4,
              sizeof(regiment_id));
  const std::uintptr_t primary = 0xBBBBBBBB;
  const std::uintptr_t secondary = 0xCCCCCCCC;
  const std::int32_t all_regiments = -1;
  const std::int32_t entry_count = 1;
  std::memcpy(command, &primary, sizeof(primary));
  std::memcpy(command + 0x18, &secondary, sizeof(secondary));
  std::memcpy(command + 0x20, &character_id, sizeof(character_id));
  std::memcpy(command + 0x40, &all_regiments, sizeof(all_regiments));
  std::memcpy(command + 0x44, &entry_count, sizeof(entry_count));
  command[0x48] = std::byte{0};
  g_raise_construct_called =
      character_id == 0x01000002 && province_id == 2 && regiment_id == -1;
  return opaque_command;
}

bool FixtureValidateRaiseTroopsCommand(void *opaque_command, void *context) {
  g_raise_validate_called =
      opaque_command != nullptr && context == nullptr;
  return g_raise_validate_result;
}

void *FixtureDestroyRaiseTroopsCommand(void *command,
                                       std::int32_t delete_flags) {
  g_raise_destroy_called = command != nullptr && delete_flags == 0;
  return command;
}

std::int32_t FixtureGetUnitState(void *unit) {
  if (unit == g_player_army.data()) {
    return g_player_army_state_code;
  }
  if (unit == g_enemy_army.data()) {
    return g_enemy_army_state_code;
  }
  return 0;
}

bool FixtureRegimentIdentityValid(void *subobject) {
  return subobject == g_player_regiment_0.data() + 0x08 ||
         subobject == g_player_regiment_1.data() + 0x08 ||
         subobject == g_enemy_regiment_0.data() + 0x08 ||
         subobject == g_enemy_regiment_1.data() + 0x08;
}

bool FixtureCharacterValid(void *subobject) {
  return subobject == g_played_character.data() + 0x10 ||
         subobject == g_target_character.data() + 0x10 ||
         subobject == g_ally_character.data() + 0x10;
}

bool FixtureBattleResultValid(void *object) {
  return object == g_contact_battle_result.data();
}

bool FixtureContactProvinceValid(void *object) {
  if (object == g_war_objective_province.data()) {
    return true;
  }
  return object == g_second_war_objective_province.data() &&
         g_contact_prior_province_valid;
}

bool FixtureIsCharacterHostile(void *left_character,
                               void *right_character, bool mode) {
  if (mode) {
    return false;
  }
  return (left_character == g_played_character.data() &&
          right_character == g_target_character.data()) ||
         (left_character == g_target_character.data() &&
          right_character == g_played_character.data());
}

bool FixtureArmyIsEmptyForContact(void *army) {
  return army != g_player_internal_army.data() &&
         army != g_enemy_internal_army.data() &&
         army != g_third_internal_army.data();
}

bool FixtureArmyIsInCombat(void *army) {
  if (army != g_player_internal_army.data() &&
      army != g_enemy_internal_army.data() &&
      army != g_third_internal_army.data()) {
    return true;
  }
  std::int32_t combat_id = -1;
  std::memcpy(&combat_id, static_cast<std::byte *>(army) + 0x128,
              sizeof(combat_id));
  return combat_id != -1;
}

std::int32_t *FixtureReadProvinceHolderCharacterId(
    void *province, std::int32_t *output) {
  if (province == nullptr || output == nullptr) {
    return nullptr;
  }
  std::memcpy(output, static_cast<std::byte *>(province) + 0x744,
              sizeof(*output));
  return output;
}

bool FixtureClassifyContactDefenderByHolder(void *owner, void *holder) {
  return owner == g_played_character.data() &&
         holder == g_played_character.data();
}

bool FixtureClassifyContactDefenderFallback(void *, void *) {
  return false;
}

bool FixtureDatabaseObjectValid(void *object) {
  return object == g_bowmen_type.data() ||
         object == g_armored_horsemen_type.data();
}

bool FixtureDatabaseObjectAbsent(void *object) {
  return object != nullptr && object == g_absent_maa_type.data() && false;
}

bool FixtureCombatTypeValid(void *object) {
  return object == g_player_regiment_0_inner_type.data() ||
         object == g_enemy_regiment_0_inner_type.data();
}

bool FixtureIsSpecialCombatRegiment(void *regiment) {
  return regiment == g_enemy_regiment_1.data();
}

void *FixtureGetArmyCommander(void *army) {
  if (army == g_player_internal_army.data()) {
    return g_played_character.data();
  }
  return army == g_enemy_internal_army.data() ? nullptr : nullptr;
}

std::int32_t FixtureGetCommanderAdvantage(void *character,
                                          std::int32_t context,
                                          bool include_roll) {
  return character == g_played_character.data() && context == -1 &&
                 !include_roll
             ? 3
             : std::numeric_limits<std::int32_t>::min();
}

void *FixtureGetProvinceTerrain(void *province) {
  if (province == g_player_province.data() ||
      province == g_second_war_objective_province.data()) {
    return g_hills_terrain.data();
  }
  if (province == g_enemy_province.data() ||
      province == g_enemy_default_raise_province.data()) {
    return g_plains_terrain.data();
  }
  return nullptr;
}

void *FixtureEvaluateRegimentStatsAtProvince(void *regiment,
                                             void *output,
                                             void *province) {
  if (output == nullptr ||
      province != g_second_war_objective_province.data() ||
      regiment == g_effective_stats_failed_regiment) {
    return nullptr;
  }
  ++g_effective_stats_calls;
  auto *const bytes = static_cast<std::byte *>(output);
  if (regiment == g_player_regiment_0.data()) {
    StoreBytes(bytes, 0x08, std::int32_t{880});
    StoreBytes(bytes, 0x10, std::int64_t{100'000});
    StoreBytes(bytes, 0x18, std::int64_t{60'000'000});
    StoreBytes(bytes, 0x20, std::int64_t{12'000'000});
    StoreBytes(bytes, 0x28, std::int64_t{300'000});
    StoreBytes(bytes, 0x30, std::int64_t{500'000});
    return output;
  }
  if (regiment == g_player_regiment_1.data()) {
    StoreBytes(bytes, 0x08, std::int32_t{420});
    StoreBytes(bytes, 0x10, std::int64_t{200'000});
    StoreBytes(bytes, 0x18, std::int64_t{600'000});
    StoreBytes(bytes, 0x20, std::int64_t{700'000});
    StoreBytes(bytes, 0x28, std::int64_t{100'000});
    StoreBytes(bytes, 0x30, std::int64_t{200'000});
    return output;
  }
  if (regiment == g_enemy_regiment_0.data()) {
    StoreBytes(bytes, 0x08, std::int32_t{1'100});
    StoreBytes(bytes, 0x10, std::int64_t{300'000});
    StoreBytes(bytes, 0x18, std::int64_t{48'000'000});
    StoreBytes(bytes, 0x20, std::int64_t{9'600'000});
    StoreBytes(bytes, 0x28, std::int64_t{400'000});
    StoreBytes(bytes, 0x30, std::int64_t{600'000});
    return output;
  }
  if (regiment == g_enemy_regiment_1.data()) {
    StoreBytes(bytes, 0x08, std::int32_t{550});
    StoreBytes(bytes, 0x10, std::int64_t{400'000});
    StoreBytes(bytes, 0x18, std::int64_t{900'000});
    StoreBytes(bytes, 0x20, std::int64_t{1'000'000});
    StoreBytes(bytes, 0x28, std::int64_t{200'000});
    StoreBytes(bytes, 0x30, std::int64_t{300'000});
    return output;
  }
  return nullptr;
}

void *FixtureGetCharacterModifierAggregator(void *character) {
  return character == g_played_character.data() ||
                 character == g_target_character.data() ||
                 character == g_dead_character.data()
             ? character
             : nullptr;
}

std::int64_t *FixtureReadCharacterModifier(void *aggregator,
                                           std::int64_t *output,
                                           std::int32_t modifier_index) {
  if (output == nullptr ||
      (aggregator != g_played_character.data() &&
       aggregator != g_target_character.data() &&
       aggregator != g_dead_character.data())) {
    return nullptr;
  }
  ++g_character_modifier_calls;
  if (aggregator == g_dead_character.data()) {
    if (modifier_index == 0x106 || modifier_index == 0x107) {
      *output = 0;
      return output;
    }
    return nullptr;
  }
  if (aggregator == g_target_character.data()) {
    if (modifier_index == 0x106) {
      *output = 30'000;
      return output;
    }
    if (modifier_index == 0x107) {
      *output = 40'000;
      return output;
    }
    return nullptr;
  }
  switch (modifier_index) {
  case 0x106:
    *output = 10'000;
    break;
  case 0x107:
    *output = 20'000;
    break;
  case 0x108:
    *output = -150'000;
    break;
  case 0x109:
    *output = 150'000;
    break;
  case 0x200:
    *output = -150'000;
    break;
  case 0x201:
    *output = 250'000;
    break;
  case 0x202:
    *output = 50'000;
    break;
  case 0x203:
    *output = -150'000;
    break;
  default:
    return nullptr;
  }
  return output;
}

void *FixtureGetCombatRules() { return g_combat_rules.data(); }

std::int32_t FixtureGetCombatSideStrength(void *combat_side) {
  ++g_battle_side_strength_calls;
  if (g_battle_mutate_on_side_strength &&
      combat_side == g_contact_combat_1.data() + 0x20) {
    g_battle_mutate_on_side_strength = false;
    const auto phase_day =
        LoadBytes<std::int32_t>(g_contact_combat_1.data(), 0x6B4);
    Store(g_contact_combat_1, 0x6B4, phase_day + 1);
  }
  if (combat_side == g_contact_combat_1.data() + 0x20) {
    return 123'456;
  }
  if (combat_side == g_contact_combat_1.data() + 0x368) {
    return 654'321;
  }
  return -1;
}

bool FixtureCanOrderCombatRetreat(void *combat, void *selected_army,
                                  void *error_sink) {
  ++g_can_order_combat_retreat_calls;
  g_can_order_combat_retreat_arguments_valid &=
      combat == g_contact_combat_1.data() &&
      selected_army == g_player_internal_army.data() &&
      error_sink == nullptr;
  return g_can_order_combat_retreat_result;
}

void *FixtureGetCombatRetreatRuleState() {
  return g_combat_retreat_rule_state.data();
}

std::int32_t FixtureGetCombatRegimentStrength(void *combat_regiment) {
  ++g_battle_regiment_strength_calls;
  if (combat_regiment == g_battle_attacker_levy_entry.data()) {
    return 11'111;
  }
  if (combat_regiment == g_battle_attacker_maa_entry.data()) {
    return 22'222;
  }
  if (combat_regiment == g_battle_defender_levy_entry.data()) {
    return 33'333;
  }
  if (combat_regiment == g_battle_defender_maa_entry.data()) {
    return 44'444;
  }
  return -1;
}

std::int64_t *FixtureReadCounterCurrentChunk(const void *opaque_entry,
                                             std::int64_t *output) {
  if (opaque_entry == nullptr || output == nullptr) {
    return nullptr;
  }
  ++g_counter_current_chunk_calls;
  std::int32_t regiment_id = -1;
  std::int64_t current_raw = -1;
  std::memcpy(&regiment_id,
              static_cast<const std::byte *>(opaque_entry) + 0x08,
              sizeof(regiment_id));
  std::memcpy(&current_raw,
              static_cast<const std::byte *>(opaque_entry) + 0x18,
              sizeof(current_raw));
  void *inner_type = nullptr;
  switch (regiment_id) {
  case 0x01000001:
    inner_type = g_player_regiment_0_inner_type.data();
    break;
  case 0x01000002:
    inner_type = g_player_regiment_1_inner_type.data();
    break;
  case 0x01000003:
    inner_type = g_enemy_regiment_0_inner_type.data();
    break;
  case 0x01000004:
    inner_type = g_enemy_regiment_1_inner_type.data();
    break;
  default:
    return nullptr;
  }
  std::int32_t stack_size = 0;
  std::memcpy(&stack_size,
              static_cast<std::byte *>(inner_type) + 0x68,
              sizeof(stack_size));
  if (stack_size == 0) {
    *output = -1;
    return output;
  }
  *output = (current_raw * kFixtureFixedPointScale) /
            (static_cast<std::int64_t>(stack_size) *
             kFixtureFixedPointScale);
  return output;
}

struct FixtureNativeArrayHeader {
  void *data;
  std::int32_t capacity;
  std::int32_t count;
};
static_assert(sizeof(FixtureNativeArrayHeader) == 0x10);

void FixtureResolveCounterClasses(void *opaque_countered,
                                  void *opaque_countering,
                                  void *opaque_output,
                                  std::int64_t context_scale) {
  ++g_counter_resolution_calls;
  auto *const countered =
      static_cast<FixtureNativeArrayHeader *>(opaque_countered);
  auto *const countering =
      static_cast<FixtureNativeArrayHeader *>(opaque_countering);
  auto *const output =
      static_cast<FixtureNativeArrayHeader *>(opaque_output);
  if (countered == nullptr || countering == nullptr || output == nullptr ||
      countered->count < 0 || countered->count > countered->capacity ||
      countering->count < 0 || countering->count > countering->capacity ||
      output->data == nullptr || output->capacity != 3 ||
      output->count != 3) {
    return;
  }
  auto *const values = static_cast<std::int64_t *>(output->data);
  if (context_scale == 104'000) {
    values[0] = 100'000;
    values[1] = 80'000;
    values[2] = 60'000;
  } else if (context_scale == 66'000) {
    values[0] = 90'000;
    values[1] = 70'000;
    values[2] = 50'000;
  }
}

std::int64_t *FixtureGetCounterContextScale(
    std::int64_t *output, void *countered_aggregator,
    void *countering_aggregator) {
  if (output == nullptr) {
    return nullptr;
  }
  const auto efficiency =
      countering_aggregator == g_played_character.data()
          ? 10'000
          : countering_aggregator == g_target_character.data() ? 30'000
                                                                : -1;
  const auto resistance =
      countered_aggregator == g_played_character.data()
          ? 20'000
          : countered_aggregator == g_target_character.data() ? 40'000
                                                               : -1;
  if (efficiency < 0 || resistance < 0) {
    return nullptr;
  }
  *output = ((kFixtureFixedPointScale - resistance) *
             (kFixtureFixedPointScale + efficiency)) /
            kFixtureFixedPointScale;
  return output;
}

void *FixtureGetKnightEffectivenessContext(void *character) {
  if (!g_knight_effectiveness_context_available) {
    return nullptr;
  }
  return character == g_played_character.data() ||
                 character == g_target_character.data()
             ? character
             : nullptr;
}

std::int64_t *FixtureReadKnightEffectiveness(
    std::int64_t *output, void *effectiveness_context,
    std::uint64_t mode) {
  if (output == nullptr || mode != 0) {
    return nullptr;
  }
  if (effectiveness_context == g_played_character.data()) {
    *output = 100'000;
    return output;
  }
  if (effectiveness_context == g_target_character.data()) {
    *output = 120'000;
    return output;
  }
  return nullptr;
}

bool FixtureIsHoldingDefender(void *defender_owner,
                              void *target_province) {
  g_last_holding_defender_owner = defender_owner;
  const bool valid_owner = defender_owner == g_played_character.data() ||
                           defender_owner == g_target_character.data();
  return valid_owner &&
         target_province == g_second_war_objective_province.data() &&
         g_holding_defender_result;
}

std::int32_t FixtureGetArmyCurrentSoldiers(
    const void *regiment_id_array, std::uint8_t flags) {
  ++g_army_current_soldiers_calls;
  if (flags != 0) {
    return -1;
  }
  if (regiment_id_array == g_player_internal_army.data() + 0x38) {
    std::int32_t count = -1;
    std::memcpy(&count, g_player_internal_army.data() + 0x44,
                sizeof(count));
    if (count == 0) {
      return 0;
    }
    return 1000;
  }
  if (regiment_id_array == g_enemy_internal_army.data() + 0x38) {
    std::int32_t count = -1;
    std::memcpy(&count, g_enemy_internal_army.data() + 0x44,
                sizeof(count));
    return count == 0 ? 0 : 800;
  }
  if (regiment_id_array == g_third_internal_army.data() + 0x38) {
    return 0;
  }
  return -1;
}

std::int32_t FixtureGetArmyMaximumSoldiers(void *army) {
  ++g_army_maximum_soldiers_calls;
  if (army == g_player_internal_army.data()) {
    std::int32_t count = -1;
    std::memcpy(&count, g_player_internal_army.data() + 0x44,
                sizeof(count));
    return count == 0 ? 0 : 1200;
  }
  if (army == g_enemy_internal_army.data()) {
    std::int32_t count = -1;
    std::memcpy(&count, g_enemy_internal_army.data() + 0x44,
                sizeof(count));
    return count == 0 ? 0 : 1500;
  }
  if (army == g_third_internal_army.data()) {
    return 0;
  }
  return -1;
}

std::int32_t FixtureGetArmyMoveMode(void *army, void *province,
                                    std::int32_t direct_target) {
  const bool supported_destination =
      province == g_enemy_province.data() ||
      province == g_player_province.data() ||
      province == g_enemy_default_raise_province.data();
  return army == g_player_army.data() && supported_destination &&
                 direct_target == 1
             ? g_move_mode_result
             : 2;
}

bool FixtureCanArmyUseMoveMode(void *army, std::int32_t move_mode) {
  return g_army_move_mode_allowed && army == g_player_army.data() &&
         move_mode == g_move_mode_result;
}

bool FixtureCanCharacterUseCommandKind(void *character,
                                       std::int32_t command_kind) {
  return g_character_command_kind_allowed &&
         character == g_played_character.data() && command_kind == 1;
}

bool FixtureCanMoveArmy(std::int32_t command_kind, void *army,
                        std::int32_t move_mode) {
  return g_move_validation_allowed && command_kind == 1 &&
         army == g_player_army.data() && move_mode == g_move_mode_result;
}

void *FixtureResolveMoveOrigin(void *opaque_context) {
  const auto *const context = static_cast<const std::byte *>(opaque_context);
  const std::uint8_t *mode_is_one = nullptr;
  void *army = nullptr;
  void *destination = nullptr;
  std::memcpy(&mode_is_one, context + 0x00, sizeof(mode_is_one));
  std::memcpy(&army, context + 0x08, sizeof(army));
  std::memcpy(&destination, context + 0x10, sizeof(destination));
  g_preview_origin_called = true;
  g_preview_origin_mode_is_one =
      mode_is_one == nullptr ? 0xFF : *mode_is_one;
  const bool valid_destination =
      destination == g_enemy_province.data() ||
      destination == g_player_province.data() ||
      destination == g_enemy_default_raise_province.data();
  return g_preview_origin_available && army == g_player_army.data() &&
                 valid_destination
             ? g_preview_effective_origin
             : nullptr;
}

void *FixtureConstructMovePathContext(void *path_context, void *army) {
  g_preview_path_context_constructed =
      path_context != nullptr && army == g_player_army.data();
  if (g_preview_path_context_constructed) {
    static_cast<std::byte *>(path_context)[0x68] = std::byte{0xA5};
  }
  return path_context;
}

void *FixtureConstructArmyMovePath(void *path_storage) {
  std::memset(path_storage, 0, 0x130);
  auto *const bytes = static_cast<std::byte *>(path_storage);
  StoreBytes(path_storage, 0x10, static_cast<void *>(bytes + 0x18));
  bytes[0x18] = std::byte{0x5A};
  g_move_path_initialized = true;
  return path_storage;
}

bool FixtureBuildArmyMoveRoute(void *path_context, void *origin_province,
                               void *target_province,
                               std::int32_t route_kind,
                               void *path_storage) {
  g_preview_route_built =
      path_context != nullptr &&
      static_cast<std::byte *>(path_context)[0x68] == std::byte{0xA5} &&
      origin_province == g_preview_effective_origin &&
      (target_province == g_enemy_province.data() ||
       target_province == g_player_province.data()) &&
      route_kind == 2 &&
      path_storage != nullptr;
  if (!g_preview_route_built) {
    return false;
  }
  StoreBytes(path_storage, 0x00,
             static_cast<void *>(g_preview_move_path.data()));
  StoreBytes(path_storage, 0x08, g_preview_route_count);
  StoreBytes(path_storage, 0x0C, g_preview_route_count);
  return g_preview_route_build_result;
}

std::int64_t *FixtureReadUnitLandRouteSpeed(void *unit,
                                            std::int64_t *output) {
  if (output == nullptr ||
      (unit != g_player_army.data() && unit != g_enemy_army.data())) {
    return nullptr;
  }
  *output = g_route_land_speed_raw;
  return output;
}

std::int64_t *FixtureReadUnitNavalRouteSpeed(void *unit,
                                             std::int64_t *output) {
  if (output == nullptr ||
      (unit != g_player_army.data() && unit != g_enemy_army.data())) {
    return nullptr;
  }
  *output = g_route_naval_speed_raw;
  return output;
}

std::int64_t *FixtureReadUnitCurrentEdgeSpeed(void *unit,
                                              std::int64_t *output) {
  if (output == nullptr ||
      (unit != g_player_army.data() && unit != g_enemy_army.data())) {
    return nullptr;
  }
  *output = g_route_current_edge_speed_raw;
  return output;
}

std::int64_t *FixtureReadRouteTravelDuration(
    void *unit, std::int64_t *output, const void *path_storage,
    void *origin_province) {
  ++g_route_duration_calls;
  if (output == nullptr || path_storage == nullptr ||
      (unit != g_player_army.data() && unit != g_enemy_army.data()) ||
      origin_province == nullptr) {
    return nullptr;
  }
  const auto *const bytes = static_cast<const std::byte *>(path_storage);
  for (std::size_t index = 0x08; index < 0x0C; ++index) {
    if (bytes[index] != std::byte{}) {
      g_route_duration_prefix_zeroed = false;
      break;
    }
  }
  for (std::size_t index = 0x10; index < 0x130; ++index) {
    if (bytes[index] != std::byte{}) {
      g_route_duration_prefix_zeroed = false;
      break;
    }
  }
  void *province_infos = nullptr;
  std::int32_t count = 0;
  std::memcpy(&province_infos, bytes + 0x00, sizeof(province_infos));
  std::memcpy(&count, bytes + 0x0C, sizeof(count));
  if (count <= 0 || count > 4'096 ||
      (province_infos != g_preview_move_path.data() &&
       province_infos != g_player_move_path.data() &&
       province_infos != g_enemy_move_path.data() &&
       province_infos != g_boundary_move_path.data() &&
       province_infos != g_boundary_move_path.data() + 1)) {
    return nullptr;
  }
  if (g_route_duration_failure) {
    *output = 0xFFFF'FFFFLL;
  } else if (g_route_duration_late_zero_speed_accumulation && count >= 2) {
    *output = static_cast<std::int64_t>(count - 1) * 100'000 +
              0xFFFF'FFFFLL;
  } else if (province_infos == g_player_move_path.data()) {
    *output = static_cast<std::int64_t>(count) * 100'000 - 50'000;
  } else {
    *output = static_cast<std::int64_t>(count) * 100'000;
  }
  if (g_route_duration_zero_current_edge_correction &&
      LoadBytes<std::int64_t>(unit, 0x190) == 0 &&
      g_route_current_edge_speed_raw == 0) {
    void *const active_infos = LoadBytes<void *>(unit, 0x38);
    const auto active_count = LoadBytes<std::int32_t>(unit, 0x44);
    void *const proposed_front = LoadBytes<void *>(province_infos, 0);
    void *const active_front =
        active_count > 0 && active_infos != nullptr
            ? LoadBytes<void *>(active_infos, 0)
            : nullptr;
    if (proposed_front != nullptr && active_front != nullptr &&
        LoadBytes<std::int32_t>(proposed_front, 0) ==
            LoadBytes<std::int32_t>(active_front, 0)) {
      *output -= 0xFFFF'FFFFLL;
    }
  }
  return output;
}

std::int64_t *FixtureReadRouteEdgeDuration(
    void *unit, std::int64_t *output, std::int32_t route_index) {
  ++g_route_edge_duration_calls;
  if (unit != g_player_army.data() || output == nullptr || route_index != 0) {
    return nullptr;
  }
  *output = g_route_edge_duration_raw +
            (g_route_edge_duration_drift
                 ? static_cast<std::int64_t>(g_route_edge_duration_calls)
                 : 0);
  return output;
}

void *FixtureDestroyMoveArmyCommand(void *opaque_command,
                                    std::int32_t delete_flags) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  g_move_destroy_called =
      delete_flags == 0 && command[0x50] == std::byte{0x5A};
  StoreBytes(command + 0x38, 0x00, static_cast<void *>(nullptr));
  StoreBytes(command + 0x38, 0x08, std::int32_t{0});
  StoreBytes(command + 0x38, 0x0C, std::int32_t{0});
  return opaque_command;
}

void *FixtureGetCasusBelliTypeDatabase() {
  return g_casus_belli_database.data();
}

void *FixtureGetCharacterInteractionDatabase() {
  return g_character_interaction_database.data();
}

void FixtureSetNativeIntArray(void *native_array, std::int32_t *data,
                              std::int32_t capacity,
                              std::int32_t count) {
  auto *const bytes = static_cast<std::byte *>(native_array);
  std::memcpy(bytes, &data, sizeof(data));
  std::memcpy(bytes + 0x08, &capacity, sizeof(capacity));
  std::memcpy(bytes + 0x0C, &count, sizeof(count));
}

bool FixtureEvaluateCasusBelli(void *casus_belli_type,
                               void *attacker_character,
                               void *defender_character,
                               void *output_configurations,
                               bool include_blocked, bool unknown_flag,
                               void *evaluation_context) {
  ++g_casus_belli_evaluation_calls;
  if (attacker_character != g_played_character.data() ||
      defender_character != g_target_character.data() || include_blocked ||
      unknown_flag || evaluation_context != nullptr ||
      output_configurations != g_casus_belli_scratch.data()) {
    return false;
  }
  std::memset(g_casus_belli_configurations.data(), 0,
              g_casus_belli_configurations.size());
  auto *const first = g_casus_belli_configurations.data();
  auto *const second = first + 0x98;
  if (casus_belli_type == g_casus_belli_type_0.data()) {
    g_casus_belli_titles_0 = {101, 0};
    g_casus_belli_titles_1 = {102, 103};
    Store(g_casus_belli_configurations, 0x00,
          std::int32_t{0x01000004});
    Store(g_casus_belli_configurations, 0x98,
          std::int32_t{0x01000005});
    FixtureSetNativeIntArray(first + 0x08,
                             g_casus_belli_titles_0.data(), 1, 1);
    FixtureSetNativeIntArray(second + 0x08,
                             g_casus_belli_titles_1.data(), 2, 2);
  } else if (casus_belli_type == g_casus_belli_type_1.data()) {
    g_casus_belli_titles_0 = {201, 0};
    g_casus_belli_titles_1 = {202, 0};
    Store(g_casus_belli_configurations, 0x00,
          std::int32_t{0x01000006});
    Store(g_casus_belli_configurations, 0x98,
          std::int32_t{0x01000007});
    FixtureSetNativeIntArray(first + 0x08,
                             g_casus_belli_titles_0.data(), 1, 1);
    FixtureSetNativeIntArray(second + 0x08,
                             g_casus_belli_titles_1.data(), 1, 1);
  } else {
    return false;
  }
  FixtureSetNativeIntArray(g_casus_belli_scratch.data(),
                           reinterpret_cast<std::int32_t *>(
                               g_casus_belli_configurations.data()),
                           2, 2);
  return true;
}

void FixtureDestroyValidCasusBelliConfiguration(void *) {
  ++g_casus_belli_configuration_destroy_calls;
}

void *FixtureConstructCharacterInteractionContext(
    void *opaque_context, void *interaction,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *extra_context,
    bool initialize_special_data) {
  auto *const context = static_cast<std::byte *>(opaque_context);
  std::memset(context, 0, 0x338);
  std::memcpy(context, &interaction, sizeof(interaction));
  std::memcpy(context + 0x2D8, &actor_character_id,
              sizeof(actor_character_id));
  std::memcpy(context + 0x2DC, &recipient_character_id,
              sizeof(recipient_character_id));
  if (interaction == g_arrange_marriage_interaction.data()) {
    ++g_marriage_legacy_context_construct_calls;
    // Model the original UI's valid intermediate two-role context. Its
    // redirect has already moved the candidate to secondary_recipient; UI
    // selection callbacks may then set secondary_actor and refresh/finalize.
    const std::int32_t no_character = -1;
    std::memcpy(context + 0x2DC, &kMarriageMatchmakerCharacterId,
                sizeof(kMarriageMatchmakerCharacterId));
    std::memcpy(context + 0x2E0, &no_character, sizeof(no_character));
    std::memcpy(context + 0x2E4, &recipient_character_id,
                sizeof(recipient_character_id));
    std::memcpy(context + 0x2E8, &no_character, sizeof(no_character));
    return opaque_context;
  } else if (interaction == g_declare_war_interaction.data()) {
    std::memset(g_war_declaration.data(), 0, g_war_declaration.size());
    const std::uintptr_t declaration_vtable = 0x12121212;
    const std::int32_t no_claimant = -1;
    std::memcpy(g_war_declaration.data(), &declaration_vtable,
                sizeof(declaration_vtable));
    std::memcpy(g_war_declaration.data() + 0x28, &no_claimant,
                sizeof(no_claimant));
    FixtureSetNativeIntArray(g_war_declaration.data() + 0x10,
                             g_war_declaration_titles.data(),
                             static_cast<std::int32_t>(
                                 g_war_declaration_titles.size()),
                             0);
    void *const declaration = g_war_declaration.data();
    std::memcpy(context + 0x330, &declaration, sizeof(declaration));
  } else {
    return nullptr;
  }
  g_interaction_construct_called =
      interaction == g_declare_war_interaction.data() &&
      actor_character_id == 0x01000002 &&
      recipient_character_id == 0x01000003 && extra_context == nullptr &&
      initialize_special_data;
  return opaque_context;
}

void FixtureRedirectCharacterInteractionRoles(
    void *interaction, std::int32_t *actor_character_id,
    std::int32_t *recipient_character_id,
    std::int32_t *secondary_actor_character_id,
    std::int32_t *secondary_recipient_character_id,
    std::int32_t *intermediary_character_id) {
  g_marriage_redirect_ready = false;
  if (interaction != g_arrange_marriage_interaction.data() ||
      actor_character_id == nullptr || recipient_character_id == nullptr ||
      secondary_actor_character_id == nullptr ||
      secondary_recipient_character_id == nullptr ||
      intermediary_character_id == nullptr ||
      *actor_character_id != 0x01000002 ||
      *recipient_character_id != 0x01000003 ||
      *secondary_actor_character_id != 0x01000002 ||
      *secondary_recipient_character_id != 0x01000003 ||
      *intermediary_character_id != -1) {
    return;
  }
  // Model arrange_marriage_interaction's recipient redirect: the command is
  // addressed to the candidate's matchmaker, while the candidate remains the
  // secondary recipient. The all-role path and the original UI's later role
  // updates are expected to converge on these final IDs.
  *recipient_character_id = kMarriageMatchmakerCharacterId;
  ++g_marriage_redirect_calls;
  g_marriage_redirect_ready = true;
}

void *FixtureConstructCharacterInteractionContextAllRoles(
    void *opaque_context, void *interaction,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id,
    std::int32_t secondary_actor_character_id,
    std::int32_t secondary_recipient_character_id,
    std::int32_t intermediary_character_id, void *extra_context) {
  if (!g_marriage_redirect_ready ||
      interaction != g_arrange_marriage_interaction.data() ||
      actor_character_id != 0x01000002 ||
      recipient_character_id != kMarriageMatchmakerCharacterId ||
      secondary_actor_character_id != 0x01000002 ||
      secondary_recipient_character_id != 0x01000003 ||
      intermediary_character_id != -1 || extra_context != nullptr) {
    return nullptr;
  }
  auto *const context = static_cast<std::byte *>(opaque_context);
  std::memset(context, 0, 0x338);
  std::memcpy(context, &interaction, sizeof(interaction));
  std::memcpy(context + 0x2D8, &actor_character_id,
              sizeof(actor_character_id));
  std::memcpy(context + 0x2DC, &recipient_character_id,
              sizeof(recipient_character_id));
  std::memcpy(context + 0x2E0, &secondary_actor_character_id,
              sizeof(secondary_actor_character_id));
  std::memcpy(context + 0x2E4, &secondary_recipient_character_id,
              sizeof(secondary_recipient_character_id));
  std::memcpy(context + 0x2E8, &intermediary_character_id,
              sizeof(intermediary_character_id));
  ++g_marriage_context_construct_calls;
  g_marriage_redirect_ready = false;
  return opaque_context;
}

void FixtureCopyNativeIntArray(void *destination, const void *source) {
  auto *destination_data = static_cast<std::int32_t *>(nullptr);
  auto *source_data = static_cast<const std::int32_t *>(nullptr);
  std::int32_t destination_capacity = 0;
  std::int32_t source_count = 0;
  std::memcpy(&destination_data, destination, sizeof(destination_data));
  std::memcpy(&destination_capacity,
              static_cast<std::byte *>(destination) + 0x08,
              sizeof(destination_capacity));
  std::memcpy(&source_data, source, sizeof(source_data));
  std::memcpy(&source_count,
              static_cast<const std::byte *>(source) + 0x0C,
              sizeof(source_count));
  if (source_count > 0 && source_count <= destination_capacity) {
    std::memcpy(destination_data, source_data,
                static_cast<std::size_t>(source_count) *
                    sizeof(std::int32_t));
  }
  std::memcpy(static_cast<std::byte *>(destination) + 0x0C,
              &source_count, sizeof(source_count));
}

void FixtureAppendNativeIntArrayRange(void *destination,
                                      std::int32_t current_count,
                                      const std::int32_t *begin,
                                      const std::int32_t *end) {
  if (g_merge_factory_command != nullptr &&
      destination == g_merge_factory_command + 0x28) {
    const auto added = static_cast<std::int32_t>(end - begin);
    if (current_count == 0 && added == 1 &&
        g_merge_owned_source_ids == nullptr) {
      auto *const owned = new (std::nothrow) std::int32_t[1];
      if (owned != nullptr) {
        owned[0] = begin[0];
        g_merge_owned_source_ids = owned;
        StoreBytes(destination, 0x00, owned);
        StoreBytes(destination, 0x08, std::int32_t{1});
        StoreBytes(destination, 0x0C, std::int32_t{1});
        g_merge_append_called = true;
      }
    }
    return;
  }
  auto *destination_data = static_cast<std::int32_t *>(nullptr);
  std::int32_t destination_capacity = 0;
  std::memcpy(&destination_data, destination, sizeof(destination_data));
  std::memcpy(&destination_capacity,
              static_cast<std::byte *>(destination) + 0x08,
              sizeof(destination_capacity));
  const auto added = static_cast<std::int32_t>(end - begin);
  const auto new_count = current_count + added;
  if (added > 0 && new_count <= destination_capacity) {
    std::memcpy(destination_data + current_count, begin,
                static_cast<std::size_t>(added) * sizeof(std::int32_t));
  }
  std::memcpy(static_cast<std::byte *>(destination) + 0x0C,
              &new_count, sizeof(new_count));
}

void FixtureRefreshCharacterInteractionContext(void *, bool refresh) {
  g_interaction_refresh_called = refresh;
}

void FixtureFinalizeCharacterInteractionContext(void *) {
  g_interaction_finalize_called = true;
}

void *FixtureDefaultConstructCharacterInteractionContext(
    void *opaque_context) {
  std::memset(opaque_context, 0, 0x338);
  g_interaction_default_construct_called = true;
  return opaque_context;
}

void FixtureConstructWarResolutionInteractionContext(void *opaque_context,
                                                     void *war,
                                                     bool attacker_victory) {
  auto *const context = static_cast<std::byte *>(opaque_context);
  const std::int32_t actor_id = 0x01000002;
  const std::int32_t recipient_id = 0x01000003;
  void *const marker =
      !g_war_resolution_context_available
          ? nullptr
          : (attacker_victory
                 ? static_cast<void *>(g_enforce_demands_marker.data())
                 : static_cast<void *>(g_surrender_marker.data()));
  void *const interaction =
      attacker_victory
          ? static_cast<void *>(g_victory_interaction.data())
          : static_cast<void *>(g_surrender_interaction.data());
  std::memcpy(context, &interaction, sizeof(interaction));
  std::memcpy(context + 0x2D8, &actor_id, sizeof(actor_id));
  std::memcpy(context + 0x2DC, &recipient_id, sizeof(recipient_id));
  std::memcpy(context + 0x330, &marker, sizeof(marker));
  g_war_resolution_construct_called = war == g_war.data();
  g_war_resolution_attacker_victory = attacker_victory;
  if (g_war_resolution_construct_calls <
      static_cast<std::int32_t>(g_war_resolution_absolute_outcomes.size())) {
    g_war_resolution_absolute_outcomes[
        static_cast<std::size_t>(g_war_resolution_construct_calls)] =
        attacker_victory;
  }
  ++g_war_resolution_construct_calls;
}

void *FixtureConstructSpecialCharacterInteractionContext(
    void *opaque_context, std::uint8_t special_index,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id) {
  g_last_special_interaction_index = special_index;
  g_last_special_actor_character_id = actor_character_id;
  g_last_special_recipient_character_id = recipient_character_id;
  std::memset(opaque_context, 0, 0x338);
  auto *const context = static_cast<std::byte *>(opaque_context);
  if (special_index == 3) {
    void *const marker = g_white_peace_marker.data();
    void *const interaction = g_white_peace_interaction.data();
    std::memcpy(context, &interaction, sizeof(interaction));
    std::memcpy(context + 0x2D8, &actor_character_id,
                sizeof(actor_character_id));
    std::memcpy(context + 0x2DC, &recipient_character_id,
                sizeof(recipient_character_id));
    std::memcpy(context + 0x330, &marker, sizeof(marker));
    ++g_white_peace_construct_calls;
  }
  return opaque_context;
}

void *FixtureDestroyCharacterClaim(void *opaque_claim,
                                   std::int32_t delete_flags) {
  if (opaque_claim != nullptr && delete_flags == 0) {
    ++g_character_claim_destroy_calls;
  }
  return opaque_claim;
}

void *FixtureReadCharacterClaim(void *opaque_claim, void *claimant,
                                void *title) {
  ++g_character_claim_read_calls;
  if (opaque_claim == nullptr || claimant != g_played_character.data() ||
      title == nullptr) {
    return nullptr;
  }
  std::memset(opaque_claim, 0, 0x18);
  auto *const claim = static_cast<std::byte *>(opaque_claim);
  std::int32_t title_id = -1;
  std::memcpy(&title_id, static_cast<std::byte *>(title) + 0x10,
              sizeof(title_id));
  bool present = true;
  bool strong = false;
  bool implicit = false;
  switch (title_id & 0x00FFFFFF) {
  case 1:
    break;
  case 2:
    strong = true;
    break;
  case 5:
    implicit = true;
    break;
  case 9:
    present = false;
    break;
  default:
    return nullptr;
  }
  const auto published_title_id =
      g_character_claim_title_mismatch ? title_id + 1 : title_id;
  std::memcpy(claim + 0x08, &published_title_id,
              sizeof(published_title_id));
  if (!present) {
    return opaque_claim;
  }
  void *const vtable = g_character_claim_vtable.data();
  std::memcpy(claim, &vtable, sizeof(vtable));
  const auto strong_raw = static_cast<std::uint8_t>(
      g_character_claim_malformed_bool ? 2 : (strong ? 1 : 0));
  const auto implicit_raw = static_cast<std::uint8_t>(implicit ? 1 : 0);
  const auto present_raw = std::uint8_t{1};
  std::memcpy(claim + 0x0C, &strong_raw, sizeof(strong_raw));
  std::memcpy(claim + 0x0D, &implicit_raw, sizeof(implicit_raw));
  std::memcpy(claim + 0x10, &present_raw, sizeof(present_raw));
  return opaque_claim;
}

struct FixturePreviewFixedPayload {
  std::uint32_t tag = 1;
  std::uint32_t padding = 0;
  std::int64_t raw = 0;
};

using FixtureEffectPreviewCallback = void (*)(
    void *collector, const void *first_scope, const void *second_scope,
    const FixturePreviewFixedPayload *payload, void *effect_node,
    void *forwarded_argument);

void FixtureOriginalEffectPreviewCallback(
    void *, const void *, const void *,
    const FixturePreviewFixedPayload *, void *, void *) {
  ++g_exit_terms_forward_calls;
}

constexpr std::int32_t kFixtureFavorHookStableHash =
    static_cast<std::int32_t>(0x4F5E02C2U);

void FixtureOriginalRaiktorPreviewCallback(
    void *, const void *, const void *,
    const FixturePreviewFixedPayload *, void *, void *) {
  ++g_raiktor_forward_calls;
}

std::int32_t FixtureHashRaiktorHookKey(void *context, const char *data,
                                      std::uint32_t size) {
  ++g_raiktor_hash_calls;
  constexpr std::string_view key = "favor_hook";
  const bool database_valid =
      context == g_raiktor_hook_type_database.data() ||
      context == g_raiktor_hook_type_database_after.data();
  return database_valid && data != nullptr && size == key.size() &&
                 std::memcmp(data, key.data(), key.size()) == 0
             ? kFixtureFavorHookStableHash
             : std::int32_t{0};
}

void *FixtureLookupRaiktorHookType(void *database, std::int32_t hash) {
  ++g_raiktor_lookup_calls;
  const bool database_valid =
      database == g_raiktor_hook_type_database.data() ||
      database == g_raiktor_hook_type_database_after.data();
  if (!database_valid || hash != kFixtureFavorHookStableHash ||
      g_raiktor_lookup_returns_fallback) {
    return g_raiktor_hook_type_fallback.data();
  }
  return g_raiktor_favor_hook_type.data();
}

void *FixtureConstructRaiktorPreviewCollector(void *collector) {
  if (collector == nullptr) {
    return nullptr;
  }
  std::memset(collector, 0, 0xD8);
  StoreBytes(collector, 0x00,
             static_cast<void *>(g_raiktor_preview_collector_vtable.data()));
  ++g_raiktor_collector_construct_calls;
  return collector;
}

void FixtureDestroyRaiktorPreviewCollector(void *collector) {
  g_raiktor_collector_lifecycle_valid =
      g_raiktor_collector_lifecycle_valid && collector != nullptr &&
      LoadBytes<void *>(collector, 0x00) ==
          g_raiktor_preview_collector_vtable.data();
  ++g_raiktor_collector_destroy_calls;
}

void FixtureTraverseRaiktorFavorHook(void *loaded_effect,
                                     void *effect_context,
                                     void *collector) {
  ++g_raiktor_traverse_calls;
  auto **const collector_vtable =
      collector == nullptr ? nullptr
                           : LoadBytes<void **>(collector, 0x00);
  if (loaded_effect != g_raiktor_loaded_effect.data() ||
      effect_context != g_raiktor_effect_context.data() ||
      collector_vtable == nullptr || collector_vtable[1] == nullptr) {
    g_raiktor_collector_lifecycle_valid = false;
    return;
  }
  const auto callback = reinterpret_cast<FixtureEffectPreviewCallback>(
      collector_vtable[1]);

  // An unrelated row proves the narrow observer forwards and ignores other
  // effect families, including ones anchored on the primary characters.
  callback(collector, g_exit_attacker_scope.data(),
           g_exit_defender_scope.data(), nullptr,
           g_unknown_effect_node.data(), nullptr);

  void *const node =
      g_raiktor_emit_no_toast
          ? static_cast<void *>(g_raiktor_no_toast_effect_node.data())
          : static_cast<void *>(g_raiktor_add_hook_effect_node.data());
  const FixturePreviewFixedPayload payload{1, 0, 0};
  const void *const first_scope =
      g_raiktor_emit_wrong_first_scope
          ? static_cast<const void *>(g_exit_ally_scope.data())
          : static_cast<const void *>(g_exit_attacker_scope.data());
  const void *const second_scope =
      g_raiktor_emit_wrong_second_scope
          ? static_cast<const void *>(g_exit_attacker_scope.data())
          : static_cast<const void *>(g_exit_defender_scope.data());
  const auto emit_hook = [&](void *forwarded_argument) {
    callback(collector, first_scope, second_scope,
             g_raiktor_emit_payload ? &payload : nullptr, node,
             forwarded_argument);
  };
  if (g_raiktor_emit_theocracy && g_raiktor_emit_theocracy_first) {
    emit_hook(g_raiktor_theocracy_argument.data());
  }
  if (g_raiktor_emit_primary) {
    emit_hook(g_raiktor_emit_unknown_forwarded_argument
                  ? static_cast<void *>(
                        g_raiktor_unknown_forwarded_argument.data())
                  : nullptr);
  }
  if (g_raiktor_emit_duplicate_primary) {
    emit_hook(nullptr);
  }
  if (g_raiktor_emit_theocracy && !g_raiktor_emit_theocracy_first) {
    emit_hook(g_raiktor_theocracy_argument.data());
  }
  if (g_raiktor_drift_database) {
    g_raiktor_hook_type_database_pointer =
        g_raiktor_hook_type_database_after.data();
  }
  if (g_raiktor_drift_loaded_root) {
    Store(g_raiktor_loaded_effect, 0x00,
          static_cast<void *>(g_raiktor_add_hook_effect_vtable.data()));
  }
}

void FixtureFreeEffectContextArray(void *allocator, void *data,
                                   std::uint64_t alignment) {
  const bool allocator_valid =
      allocator == g_effect_context_allocator.data() && alignment == 8;
  if (data == g_effect_context_data_100.data() &&
      g_exit_terms_context_teardown_stage == 2) {
    g_exit_terms_context_teardown_stage = 3;
  } else if (data == g_effect_context_data_18.data() &&
             g_exit_terms_context_teardown_stage == 3) {
    g_exit_terms_context_teardown_stage = 4;
  } else {
    g_exit_terms_context_lifecycle_valid = false;
  }
  g_exit_terms_context_lifecycle_valid =
      g_exit_terms_context_lifecycle_valid && allocator_valid;
}

void *FixtureConstructWarEffectContext(void *opaque_context) {
  if (opaque_context == nullptr) {
    return nullptr;
  }
  std::memset(opaque_context, 0, 0x170);
  StoreBytes(opaque_context, 0x18,
             static_cast<void *>(g_effect_context_data_18.data()));
  StoreBytes(opaque_context, 0x24, std::int32_t{1});
  StoreBytes(opaque_context, 0x28,
             static_cast<void *>(g_effect_context_allocator.data()));
  StoreBytes(opaque_context, 0x100,
             static_cast<void *>(g_effect_context_data_100.data()));
  StoreBytes(opaque_context, 0x108, std::int32_t{1});
  StoreBytes(opaque_context, 0x110,
             static_cast<void *>(g_effect_context_allocator.data()));
  g_exit_terms_effect_context = opaque_context;
  g_exit_terms_projected_root_preview_calls = 0;
  g_exit_terms_projected_callback_counts.fill(0);
  g_exit_terms_context_teardown_stage = 0;
  ++g_exit_terms_effect_context_construct_calls;
  return opaque_context;
}

void FixturePopulateWarEffectContext(void *opaque_context, void *war,
                                     bool unknown_flag) {
  if (opaque_context != g_exit_terms_effect_context ||
      war != g_war.data() || unknown_flag) {
    g_exit_terms_context_lifecycle_valid = false;
  }
  ++g_exit_terms_effect_context_populate_calls;
}

void *FixtureConstructEffectPreviewCollector(void *opaque_collector) {
  if (opaque_collector == nullptr) {
    return nullptr;
  }
  std::memset(opaque_collector, 0, 0xD8);
  void *const vtable = g_effect_preview_collector_vtable.data();
  std::memcpy(opaque_collector, &vtable, sizeof(vtable));
  ++g_exit_terms_collector_construct_calls;
  return opaque_collector;
}

void FixtureDestroyEffectPreviewCollector(void *opaque_collector) {
  void *vtable = nullptr;
  if (opaque_collector != nullptr) {
    std::memcpy(&vtable, opaque_collector, sizeof(vtable));
  }
  g_exit_terms_collector_lifecycle_valid =
      g_exit_terms_collector_lifecycle_valid &&
      vtable == g_effect_preview_collector_vtable.data();
  ++g_exit_terms_collector_destroy_calls;
}

void FixtureLoadedEffectSlot58(void *loaded_effect, void *,
                               std::uint32_t mode, void *collector) {
  void **vtable = nullptr;
  if (collector != nullptr) {
    std::memcpy(&vtable, collector, sizeof(vtable));
  }
  if (mode != 0 || vtable == nullptr || vtable[1] == nullptr) {
    g_exit_terms_collector_lifecycle_valid = false;
    return;
  }
  const auto callback =
      reinterpret_cast<FixtureEffectPreviewCallback>(vtable[1]);
  const auto emit_resource =
      [callback, collector](void *scope, std::int64_t raw, void *node) {
        const FixturePreviewFixedPayload payload{1, 0, raw};
        callback(collector, scope, nullptr, &payload, node, nullptr);
      };
  const auto emit_truce = [callback, collector]() {
    callback(collector, g_exit_attacker_scope.data(),
             g_exit_defender_scope.data(), nullptr,
             g_truce_effect_node.data(), nullptr);
  };

  if (loaded_effect == g_truce_context_effect.data()) {
    ++g_exit_terms_hidden_truce_preview_calls;
    emit_truce();
    if (g_exit_terms_duplicate_truce) {
      emit_truce();
    }
    return;
  }

  const auto projected_outcome_index =
      static_cast<std::size_t>(g_exit_terms_projected_root_preview_calls);
  const bool projected_outcome_valid = projected_outcome_index < 2;
  void *const projected_root_children =
      loaded_effect == nullptr
          ? nullptr
          : LoadBytes<void *>(loaded_effect, 0x40);
  void *const projected_scripted_effect =
      projected_root_children == nullptr
          ? nullptr
          : LoadBytes<void *>(projected_root_children,
                              8 * sizeof(void *));
  void *const projected_template =
      projected_scripted_effect == nullptr
          ? nullptr
          : LoadBytes<void *>(projected_scripted_effect, 0x60);
  void *const projected_default_effect =
      projected_template == nullptr
          ? nullptr
          : LoadBytes<void *>(projected_template, 0x120);
  void *const projected_default_children =
      projected_default_effect == nullptr
          ? nullptr
          : LoadBytes<void *>(projected_default_effect, 0x40);
  bool projection_valid =
      projected_outcome_valid &&
      loaded_effect != nullptr &&
      loaded_effect != g_casus_belli_type_0.data() + 0x9C8 &&
      loaded_effect != g_casus_belli_type_0.data() + 0xA28 &&
      LoadBytes<void *>(loaded_effect, 0x00) ==
          g_white_peace_loaded_effect_vtable.data() &&
      LoadBytes<std::int32_t>(loaded_effect, 0x48) == 13 &&
      LoadBytes<std::int32_t>(loaded_effect, 0x4C) == 10 &&
      projected_root_children != nullptr &&
      projected_scripted_effect != nullptr &&
      projected_scripted_effect != g_truce_scripted_effect.data() &&
      LoadBytes<void *>(projected_scripted_effect, 0x00) ==
          g_scripted_effect_vtable.data() &&
      LoadBytes<std::int32_t>(projected_scripted_effect, 0x94) == 0 &&
      projected_template != nullptr &&
      projected_template != g_truce_scripted_effect_template.data() &&
      LoadBytes<void *>(projected_template, 0x00) ==
          g_scripted_effect_template_vtable.data() &&
      projected_default_effect != nullptr &&
      projected_default_effect != g_truce_scripted_default_effect.data() &&
      LoadBytes<void *>(projected_default_effect, 0x00) ==
          g_white_peace_loaded_effect_vtable.data() &&
      LoadBytes<std::int32_t>(projected_default_effect, 0x48) == 6 &&
      LoadBytes<std::int32_t>(projected_default_effect, 0x4C) == 5 &&
      projected_default_children != nullptr &&
      LoadBytes<void *>(projected_default_children,
                        2 * sizeof(void *)) ==
          g_truce_context_effect.data();
  for (std::size_t index = 0; index < 10 && projection_valid; ++index) {
    if (index != 8) {
      projection_valid =
          LoadBytes<void *>(projected_root_children,
                            index * sizeof(void *)) ==
          g_exit_root_effect_children[index];
    }
  }
  for (std::size_t index = 0; index < 5 && projection_valid; ++index) {
    if (index != 2) {
      projection_valid =
          LoadBytes<void *>(projected_default_children,
                            index * sizeof(void *)) ==
          g_truce_scripted_default_children[index];
    }
  }
  if (!projection_valid) {
    g_exit_terms_collector_lifecycle_valid = false;
    return;
  }
  ++g_exit_terms_projected_root_preview_calls;
  const auto callbacks_before = g_exit_terms_forward_calls;

  const FixturePreviewFixedPayload attacker_contribution{1, 0, 10'500'000};
  callback(collector, g_exit_attacker_scope.data(), nullptr,
           &attacker_contribution,
           g_attacker_contribution_effect_node.data(),
           g_exit_terms_malformed_contribution
               ? nullptr
               : static_cast<void *>(g_string_table_marker.data()));
  const FixturePreviewFixedPayload defender_contribution{1, 0, 10'500'000};
  callback(collector, g_exit_defender_scope.data(), nullptr,
           &defender_contribution,
           g_defender_contribution_effect_node.data(),
           static_cast<void *>(g_string_table_marker.data()));

  if (g_exit_terms_unknown_node) {
    emit_resource(g_exit_attacker_scope.data(), 1,
                  g_unknown_effect_node.data());
  }
  // Stock claim_cb walks allies and may use contribution-specific effect
  // node vtables.  Both a known and an unknown third-party row must be
  // forwarded to the native collector but stay outside the primary grid.
  emit_resource(g_exit_ally_scope.data(), 2'000'000,
                g_prestige_effect_node.data());
  emit_resource(g_exit_ally_scope.data(), 3'000'000,
                g_unknown_effect_node.data());
  if (projected_outcome_index == 0) {
    emit_resource(g_exit_attacker_scope.data(), -3'500'000,
                  g_prestige_effect_node.data());
    emit_resource(g_exit_attacker_scope.data(), 3'400'000,
                  g_stress_effect_node.data());
  } else if (projected_outcome_index == 1) {
    emit_resource(g_exit_attacker_scope.data(), -7'000'000,
                  g_prestige_effect_node.data());
    emit_resource(g_exit_defender_scope.data(), 7'000'000,
                  g_prestige_effect_node.data());
    emit_resource(g_exit_defender_scope.data(), 5'000'000,
                  g_legitimacy_effect_node.data());
    const FixturePreviewFixedPayload gold{1, 0, 15'000'000};
    callback(collector, g_exit_attacker_scope.data(),
             g_exit_defender_scope.data(), &gold,
             g_gold_transfer_effect_node.data(), nullptr);
  } else {
    g_exit_terms_collector_lifecycle_valid = false;
  }
  FixtureLoadedEffectSlot58(g_truce_context_effect.data(), nullptr, mode,
                            collector);
  g_exit_terms_projected_callback_counts[projected_outcome_index] =
      g_exit_terms_forward_calls - callbacks_before;
}

void FixtureTraverseLoadedEffect(void *loaded_effect, void *effect_context,
                                 void *collector) {
  ++g_exit_terms_traverse_calls;
  void **root_vtable = nullptr;
  if (loaded_effect != nullptr) {
    std::memcpy(&root_vtable, loaded_effect, sizeof(root_vtable));
  }
  if (effect_context != g_exit_terms_effect_context ||
      root_vtable == nullptr || root_vtable[11] == nullptr) {
    g_exit_terms_collector_lifecycle_valid = false;
    return;
  }

  std::memset(g_exit_terms_variable_container.data(), 0,
              g_exit_terms_variable_container.size());
  std::memset(g_exit_terms_variable_row.data(), 0,
              g_exit_terms_variable_row.size());
  Store(g_exit_terms_variable_container, 0x00,
        static_cast<void *>(g_exit_terms_variable_row.data()));
  Store(g_exit_terms_variable_container, 0x08, std::int32_t{1});
  Store(g_exit_terms_variable_container, 0x0C, std::int32_t{1});
  Store(g_exit_terms_variable_row, 0x00,
        g_exit_terms_factor_identifier_id);
  Store(g_exit_terms_variable_row, 0x08,
        static_cast<std::uint16_t>(g_exit_terms_factor_malformed ? 2 : 1));
  Store(g_exit_terms_variable_row, 0x0A, std::uint16_t{0});
  Store(g_exit_terms_variable_row, 0x10, std::int64_t{700'000});
  Store(g_exit_terms_variable_row, 0x18, std::uint8_t{0});
  std::array<std::byte, 0x30> wrapper{};
  Store(wrapper, 0x18,
        static_cast<void *>(g_exit_terms_variable_container.data()));

  using LoadedEffectSlot58 = void (*)(void *, void *, std::uint32_t, void *);
  reinterpret_cast<LoadedEffectSlot58>(root_vtable[11])(
      loaded_effect, wrapper.data(), 0, collector);
}

void FixtureDestroyEffectContext118(void *subobject) {
  if (g_exit_terms_effect_context == nullptr ||
      subobject != static_cast<std::byte *>(g_exit_terms_effect_context) +
                       0x118 ||
      g_exit_terms_context_teardown_stage != 0) {
    g_exit_terms_context_lifecycle_valid = false;
    return;
  }
  g_exit_terms_context_teardown_stage = 1;
}

void FixtureDestroyEffectContextArrayRow(void *subobject) {
  if (g_exit_terms_effect_context == nullptr ||
      subobject != static_cast<std::byte *>(g_exit_terms_effect_context) +
                       0x100 ||
      g_exit_terms_context_teardown_stage != 1) {
    g_exit_terms_context_lifecycle_valid = false;
    return;
  }
  g_exit_terms_context_teardown_stage = 2;
}

std::int32_t FixtureEvaluateTruceDurationDays(
    void *script_value, void *effect_context, void *evaluation_context) {
  ++g_exit_terms_truce_duration_calls;
  if (script_value != g_truce_effect_node.data() + 0x108 ||
      effect_context != g_exit_terms_effect_context ||
      evaluation_context !=
          static_cast<std::byte *>(g_exit_terms_effect_context) + 0x28) {
    return -1;
  }
  return 1'825;
}

void *FixtureGetCharacterPrimaryTitle(void *character) {
  ++g_exit_terms_primary_title_calls;
  if (character == g_played_character.data()) {
    return g_targeted_title.data();
  }
  return character == g_target_character.data()
             ? static_cast<void *>(g_targeted_duchy_a_title.data())
             : nullptr;
}

std::int64_t *FixtureReadMonthlyGoldIncome(
    std::int64_t *output, void *character, void *optional_breakdown,
    void *evaluation_context) {
  ++g_exit_terms_monthly_income_calls;
  if (output == nullptr || optional_breakdown != nullptr ||
      evaluation_context != nullptr) {
    return nullptr;
  }
  void *extension = nullptr;
  std::memcpy(&extension, static_cast<std::byte *>(character) + 0x1A8,
              sizeof(extension));
  if (extension == nullptr) {
    *output = 0;
    return output;
  }
  std::memcpy(output, static_cast<std::byte *>(extension) + 0x2B0,
              sizeof(*output));
  if (g_exit_terms_income_mismatch &&
      character == g_played_character.data()) {
    ++*output;
  }
  return output;
}

std::uint8_t FixtureEvaluateCharacterInteractionAnswer(
    void *opaque_context, std::uint8_t answer_mode, std::uint8_t flag,
    void *error_sink_a, void *error_sink_b) {
  ++g_exit_terms_answer_calls;
  g_exit_terms_answer_destroy_counts.push_back(
      g_interaction_destroy_calls);
  if (opaque_context == nullptr || answer_mode != 1 || flag != 0 ||
      error_sink_a != nullptr || error_sink_b != nullptr) {
    return 3;
  }
  if (g_exit_terms_answer_status_override != 0xFF) {
    return g_exit_terms_answer_status_override;
  }
  void *special_data = nullptr;
  std::memcpy(&special_data,
              static_cast<std::byte *>(opaque_context) + 0x330,
              sizeof(special_data));
  if (special_data == g_white_peace_marker.data()) {
    return 0;
  }
  return special_data == g_surrender_marker.data() ? 1 : 3;
}

bool FixtureValidateCharacterInteractionContext(void *opaque_context,
                                                void *error_output) {
  const auto *const context = static_cast<const std::byte *>(opaque_context);
  void *interaction = nullptr;
  std::memcpy(&interaction, context, sizeof(interaction));
  if (interaction == g_arrange_marriage_interaction.data()) {
    std::int32_t actor_id = -1;
    std::int32_t recipient_id = -1;
    std::int32_t actor_to_match_id = -1;
    std::int32_t recipient_to_match_id = -1;
    std::memcpy(&actor_id, context + 0x2D8, sizeof(actor_id));
    std::memcpy(&recipient_id, context + 0x2DC,
                sizeof(recipient_id));
    std::memcpy(&actor_to_match_id, context + 0x2E0,
                sizeof(actor_to_match_id));
    std::memcpy(&recipient_to_match_id, context + 0x2E4,
                sizeof(recipient_to_match_id));
    return g_marriage_validate_result && error_output == nullptr &&
           actor_id == 0x01000002 &&
           recipient_id == kMarriageMatchmakerCharacterId &&
           actor_to_match_id == actor_id &&
           recipient_to_match_id == 0x01000003;
  }
  void *declaration = nullptr;
  std::memcpy(&declaration, context + 0x330, sizeof(declaration));
  if (declaration == g_enforce_demands_marker.data() ||
      declaration == g_surrender_marker.data() ||
      declaration == g_white_peace_marker.data()) {
    return g_interaction_validate_result && error_output == nullptr;
  }
  const void *const expected_special_data =
      static_cast<void *>(g_war_declaration.data());
  return g_interaction_validate_result && error_output == nullptr &&
         declaration == expected_special_data;
}

std::int64_t *FixtureReadCharacterInteractionAnswerScore(
    void *opaque_context, std::int64_t *output) {
  if (opaque_context == nullptr || output == nullptr) {
    return nullptr;
  }
  void *special_data = nullptr;
  std::memcpy(&special_data,
              static_cast<std::byte *>(opaque_context) + 0x330,
              sizeof(special_data));
  if (special_data == g_surrender_marker.data()) {
    *output = g_exit_terms_fixture_active ? 86'000'000 : 10'000'000;
  } else if (special_data == g_white_peace_marker.data()) {
    *output = g_exit_terms_fixture_active ? 1'100'000 : -2'500'000;
  } else if (special_data == g_enforce_demands_marker.data()) {
    *output = 3'700'000;
  } else {
    return nullptr;
  }
  return output;
}

bool FixtureEvaluateCharacterInteractionTrigger(
    void *trigger, const void *event_target_scope) {
  if (trigger != g_auto_accept_trigger.data() ||
      event_target_scope == nullptr) {
    return false;
  }
  ++g_auto_accept_trigger_calls;
  return true;
}

void *FixtureConstructSendCharacterInteractionCommand(
    void *opaque_command, const void *opaque_context) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  const std::uintptr_t primary = 0x13131313;
  const std::uintptr_t secondary = 0x14141414;
  std::memset(command, 0, 0x368);
  std::memcpy(command, &primary, sizeof(primary));
  std::memcpy(command + 0x18, &secondary, sizeof(secondary));
  std::memcpy(command + 0x20, opaque_context, 0x338);
  g_send_interaction_construct_called = true;
  return opaque_command;
}

void FixtureDestroyCharacterInteractionContext(void *) {
  ++g_interaction_destroy_calls;
}

bool FixtureValidateDisbandArmyCommand(std::int32_t command_kind,
                                       std::int32_t command_target_id,
                                       void *error_output) {
  g_disband_validate_called = command_kind == 1 &&
                              command_target_id == 0x02000011 &&
                              error_output == nullptr;
  return g_disband_validate_called && g_disband_validate_result;
}

bool FixtureValidateSplitArmyHalfCommand(std::int32_t command_kind,
                                          std::int32_t source_army_id,
                                          std::int32_t played_character_id,
                                          void *error_output) {
  g_split_validate_called =
      command_kind == 1 && source_army_id == 0x02000011 &&
      played_character_id == 0x01000002 && error_output == nullptr;
  return g_split_validate_called && g_split_validate_result;
}

void *FixtureDestroySplitArmyHalfCommand(void *opaque_command,
                                         std::int32_t delete_flags) {
  g_split_destroy_called = opaque_command != nullptr && delete_flags == 0 &&
                           g_split_clone_called;
  if (opaque_command != nullptr) {
    std::memset(opaque_command, 0xDD, 0x30);
  }
  return opaque_command;
}

void *FixtureCreateMergeArmiesCommand() {
  auto *const command = new (std::nothrow) std::byte[0x40];
  if (command == nullptr) {
    return nullptr;
  }
  std::memset(command, 0, 0x40);
  StoreBytes(command, 0x00, std::uintptr_t{0x17171717});
  StoreBytes(command, 0x18, std::uintptr_t{0x18181818});
  StoreBytes(command, 0x24, std::int32_t{-1});
  StoreBytes(command, 0x38, reinterpret_cast<void *>(0x19191919));
  g_merge_factory_called = true;
  g_merge_factory_command = command;
  return command;
}

bool FixtureValidateMergeArmiesCommand(void *opaque_command,
                                       void *error_output) {
  const auto *const command = static_cast<const std::byte *>(opaque_command);
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t kind = -1;
  std::int32_t destination_id = -1;
  std::int32_t *source_ids = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
  std::memcpy(&primary, command + 0x00, sizeof(primary));
  std::memcpy(&secondary, command + 0x18, sizeof(secondary));
  std::memcpy(&kind, command + 0x20, sizeof(kind));
  std::memcpy(&destination_id, command + 0x24,
              sizeof(destination_id));
  std::memcpy(&source_ids, command + 0x28, sizeof(source_ids));
  std::memcpy(&capacity, command + 0x30, sizeof(capacity));
  std::memcpy(&count, command + 0x34, sizeof(count));
  std::memcpy(&allocator, command + 0x38, sizeof(allocator));
  g_merge_validate_called =
      opaque_command == g_merge_factory_command && error_output == nullptr &&
      primary == 0x17171717 && secondary == 0x18181818 && kind == 1 &&
      destination_id == 0x01000001 && source_ids != nullptr &&
      source_ids == g_merge_owned_source_ids && capacity == 1 && count == 1 &&
      source_ids[0] == 0x01000002 &&
      allocator == reinterpret_cast<void *>(0x19191919);
  return g_merge_validate_called && g_merge_validate_result;
}

void *FixtureDestroyMergeArmiesCommand(void *opaque_command,
                                       std::int32_t delete_flags) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  std::int32_t *source_ids = nullptr;
  if (command != nullptr) {
    std::memcpy(&source_ids, command + 0x28, sizeof(source_ids));
  }
  g_merge_destroy_called = command == g_merge_factory_command &&
                           delete_flags == 1;
  if (source_ids != nullptr && source_ids == g_merge_owned_source_ids) {
    source_ids[0] = std::numeric_limits<std::int32_t>::min();
    delete[] source_ids;
    g_merge_owned_source_ids = nullptr;
    g_merge_source_array_destroyed = true;
  }
  if (command != nullptr) {
    std::memset(command, 0xDD, 0x40);
    delete[] command;
  }
  g_merge_factory_command = nullptr;
  return nullptr;
}

bool FixtureSubmit(void *manager, void *opaque_command, std::uint32_t flags) {
  const auto *command = static_cast<const std::byte *>(opaque_command);
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t player_id = -1;
  std::memcpy(&primary, command, sizeof(primary));
  std::memcpy(&secondary, command + 0x18, sizeof(secondary));
  std::memcpy(&player_id, command + 0x20, sizeof(player_id));
  const auto paused = static_cast<std::uint8_t>(command[0x24]);
  const auto command_flags = static_cast<std::uint8_t>(command[0x08]);
  if (g_expected_command == ExpectedCommand::pause ||
      g_expected_command == ExpectedCommand::resume) {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x11111111 &&
                      secondary == 0x22222222 && command_flags == 0x08 &&
                      player_id == 41 &&
                      paused ==
                          (g_expected_command == ExpectedCommand::pause ? 1 : 0);
  } else if (g_expected_command == ExpectedCommand::speed) {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x33333333 &&
                      secondary == 0x44444444 && command_flags == 0 &&
                      player_id == 4;
  } else if (g_expected_command == ExpectedCommand::event_option) {
    std::int32_t option_index = -1;
    std::memcpy(&option_index, command + 0x24, sizeof(option_index));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x55555555 &&
                      secondary == 0x66666666 && command_flags == 0 &&
                      player_id == 77 && option_index == 2;
  } else if (g_expected_command == ExpectedCommand::auto_save) {
    std::uint64_t save_name_size = 0;
    std::uint64_t save_name_capacity = 0;
    std::memcpy(&save_name_size, command + 0x30, sizeof(save_name_size));
    std::memcpy(&save_name_capacity, command + 0x38,
                sizeof(save_name_capacity));
    const std::string save_name(reinterpret_cast<const char *>(command + 0x20),
                                save_name_size);
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x77777777 &&
                      secondary == 0x88888888 && command_flags == 0x20 &&
                      save_name == xar::ck3_11906::kCheckpointSaveName &&
                      save_name_capacity == 15;
  } else if (g_expected_command == ExpectedCommand::reply_accept ||
             g_expected_command == ExpectedCommand::reply_reject ||
             g_expected_command == ExpectedCommand::reply_acknowledge) {
    std::int32_t reply = -1;
    std::memcpy(&reply, command + 0x24, sizeof(reply));
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x99999999 && secondary == 0xAAAAAAAA &&
        command_flags == 0 && player_id == g_expected_pending_command_id &&
        reply == (g_expected_command == ExpectedCommand::reply_accept
                      ? 0
                      : g_expected_command == ExpectedCommand::reply_reject
                            ? 1
                            : 4);
  } else if (g_expected_command == ExpectedCommand::raise_troops) {
    std::int32_t all_regiments = 0;
    std::int32_t entry_count = 0;
    std::memcpy(&all_regiments, command + 0x40, sizeof(all_regiments));
    std::memcpy(&entry_count, command + 0x44, sizeof(entry_count));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0xBBBBBBBB &&
                      secondary == 0xCCCCCCCC && player_id == 0x01000002 &&
                      all_regiments == -1 && entry_count == 1 &&
                      command[0x48] == std::byte{0};
  } else if (g_expected_command == ExpectedCommand::move_army) {
    std::int32_t army_id = -1;
    std::int32_t destination = -1;
    std::int32_t move_mode = -1;
    std::int32_t route_kind = -1;
    std::int32_t direct_target = -1;
    std::memcpy(&army_id, command + 0x24, sizeof(army_id));
    std::memcpy(&destination, command + 0x28, sizeof(destination));
    std::memcpy(&move_mode, command + 0x2C, sizeof(move_mode));
    std::memcpy(&route_kind, command + 0x30, sizeof(route_kind));
    std::memcpy(&direct_target, command + 0x34, sizeof(direct_target));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 0x0E && primary == 0xDDDDDDDD &&
                      secondary == 0xEEEEEEEE && command_flags == 0 &&
                      player_id == 1 && army_id == 0x01000001 &&
                      destination == 3 && move_mode == 5 &&
                      route_kind == 2 && direct_target == 1 &&
                      command[0x50] == std::byte{0x5A};
  } else if (g_expected_command == ExpectedCommand::disband_army) {
    std::int32_t command_kind = -1;
    std::int32_t command_target_id = -1;
    std::memcpy(&command_kind, command + 0x20, sizeof(command_kind));
    std::memcpy(&command_target_id, command + 0x24,
                sizeof(command_target_id));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 0x0E && primary == 0xFFFFFFFF &&
                      secondary == 0xABABABAB && command_flags == 0 &&
                      command_kind == 1 && command_target_id == 0x02000011;
  } else if (g_expected_command == ExpectedCommand::split_army_half) {
    std::int32_t command_kind = -1;
    std::int32_t played_character_id = -1;
    std::int32_t source_army_id = -1;
    std::memcpy(&command_kind, command + 0x20, sizeof(command_kind));
    std::memcpy(&played_character_id, command + 0x24,
                sizeof(played_character_id));
    std::memcpy(&source_army_id, command + 0x28,
                sizeof(source_army_id));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 0x0E && primary == 0x15151515 &&
                      secondary == 0x16161616 && command_flags == 0 &&
                      command_kind == 1 &&
                      played_character_id == 0x01000002 &&
                      source_army_id == 0x02000011;
    if (g_submit_called) {
      std::memcpy(g_split_cloned_command.data(), command,
                  g_split_cloned_command.size());
      g_split_clone_called = true;
    }
  } else if (g_expected_command == ExpectedCommand::merge_armies) {
    std::int32_t command_kind = -1;
    std::int32_t destination_id = -1;
    std::int32_t *source_ids = nullptr;
    std::int32_t capacity = 0;
    std::int32_t count = 0;
    void *allocator = nullptr;
    std::memcpy(&command_kind, command + 0x20, sizeof(command_kind));
    std::memcpy(&destination_id, command + 0x24,
                sizeof(destination_id));
    std::memcpy(&source_ids, command + 0x28, sizeof(source_ids));
    std::memcpy(&capacity, command + 0x30, sizeof(capacity));
    std::memcpy(&count, command + 0x34, sizeof(count));
    std::memcpy(&allocator, command + 0x38, sizeof(allocator));
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x17171717 && secondary == 0x18181818 &&
        command_flags == 0 && command_kind == 1 &&
        destination_id == 0x01000001 && source_ids != nullptr &&
        source_ids == g_merge_owned_source_ids && capacity == 1 &&
        count == 1 && source_ids[0] == 0x01000002 &&
        allocator == reinterpret_cast<void *>(0x19191919);
    if (g_submit_called) {
      // Model primary-vtable +0x40 / RVA 0x26C26B0: the queued command owns a
      // copied array value, not the original command's soon-to-be-freed data.
      g_merge_cloned_destination_id = destination_id;
      g_merge_cloned_source_ids[0] = source_ids[0];
      g_merge_clone_called = true;
    }
  } else if (g_expected_command == ExpectedCommand::start_assault ||
             g_expected_command == ExpectedCommand::stop_assault) {
    std::int32_t command_kind = -1;
    std::int32_t played_character_id = -1;
    std::int32_t siege_id = -1;
    std::memcpy(&command_kind, command + 0x20, sizeof(command_kind));
    std::memcpy(&played_character_id, command + 0x24,
                sizeof(played_character_id));
    std::memcpy(&siege_id, command + 0x28, sizeof(siege_id));
    const bool starting =
        g_expected_command == ExpectedCommand::start_assault;
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == (starting ? 0x1A1A1A1A : 0x1C1C1C1C) &&
        secondary == (starting ? 0x1B1B1B1B : 0x1D1D1D1D) &&
        command_flags == 0 && command_kind == 1 &&
        played_character_id == 0x01000002 && siege_id == 0x01000001;
    if (g_submit_called) {
      // Model primary +0x40: the queue owns a complete 0x30-byte clone, while
      // the bridge must destroy its original stack object after the bool ACK.
      std::memcpy(g_assault_cloned_command.data(), command,
                  g_assault_cloned_command.size());
      g_assault_clone_called = true;
    }
  } else if (g_expected_command == ExpectedCommand::declare_war) {
    std::int32_t actor_id = -1;
    std::int32_t recipient_id = -1;
    void *declaration = nullptr;
    std::memcpy(&actor_id, command + 0x20 + 0x2D8,
                sizeof(actor_id));
    std::memcpy(&recipient_id, command + 0x20 + 0x2DC,
                sizeof(recipient_id));
    std::memcpy(&declaration, command + 0x20 + 0x330,
                sizeof(declaration));
    void *casus_belli_type = nullptr;
    std::int32_t claimant_id = -1;
    std::int32_t title_count = 0;
    std::int32_t *title_data = nullptr;
    if (declaration != nullptr) {
      const auto *const declaration_bytes =
          static_cast<const std::byte *>(declaration);
      std::memcpy(&casus_belli_type, declaration_bytes + 0x08,
                  sizeof(casus_belli_type));
      std::memcpy(&title_data, declaration_bytes + 0x10,
                  sizeof(title_data));
      std::memcpy(&title_count, declaration_bytes + 0x1C,
                  sizeof(title_count));
      std::memcpy(&claimant_id, declaration_bytes + 0x28,
                  sizeof(claimant_id));
    }
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x13131313 && secondary == 0x14141414 &&
        command_flags == 0 && actor_id == 0x01000002 &&
        recipient_id == 0x01000003 &&
        declaration == g_war_declaration.data() &&
        casus_belli_type == g_casus_belli_type_0.data() &&
        claimant_id == 0x01000005 && title_count == 2 &&
        title_data != nullptr && title_data[0] == 102 &&
        title_data[1] == 103;
  } else if (g_expected_command == ExpectedCommand::arrange_marriage) {
    std::int32_t actor_id = -1;
    std::int32_t recipient_id = -1;
    std::int32_t actor_to_match_id = -1;
    std::int32_t recipient_to_match_id = -1;
    std::memcpy(&actor_id, command + 0x20 + 0x2D8,
                sizeof(actor_id));
    std::memcpy(&recipient_id, command + 0x20 + 0x2DC,
                sizeof(recipient_id));
    std::memcpy(&actor_to_match_id, command + 0x20 + 0x2E0,
                sizeof(actor_to_match_id));
    std::memcpy(&recipient_to_match_id, command + 0x20 + 0x2E4,
                sizeof(recipient_to_match_id));
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x13131313 && secondary == 0x14141414 &&
        command_flags == 0 && actor_id == 0x01000002 &&
        recipient_id == kMarriageMatchmakerCharacterId &&
        actor_to_match_id == actor_id &&
        recipient_to_match_id == 0x01000003;
  } else if (g_expected_command == ExpectedCommand::enforce_demands ||
             g_expected_command == ExpectedCommand::surrender_war ||
             g_expected_command == ExpectedCommand::offer_white_peace) {
    std::int32_t actor_id = -1;
    std::int32_t recipient_id = -1;
    void *special_data = nullptr;
    std::memcpy(&actor_id, command + 0x20 + 0x2D8,
                sizeof(actor_id));
    std::memcpy(&recipient_id, command + 0x20 + 0x2DC,
                sizeof(recipient_id));
    std::memcpy(&special_data, command + 0x20 + 0x330,
                sizeof(special_data));
    void *const expected_marker =
        g_expected_command == ExpectedCommand::surrender_war
            ? static_cast<void *>(g_surrender_marker.data())
            : g_expected_command == ExpectedCommand::offer_white_peace
                  ? static_cast<void *>(g_white_peace_marker.data())
                  : static_cast<void *>(g_enforce_demands_marker.data());
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x13131313 && secondary == 0x14141414 &&
        command_flags == 0 && actor_id == 0x01000002 &&
        recipient_id == 0x01000003 &&
        special_data == expected_marker;
  }
  return g_submit_called && g_submit_result;
}

int Fail(const char *message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

} // namespace

int main() {
  xar::game::ActualContactScopeRequest parsed_contact_request{};
  if (!xar::ck3_11906::ParseActualContactScopeV1Step(
          "query-actual-contact-scope-v1-16777217-at-3",
          parsed_contact_request) ||
      parsed_contact_request.subject_army_id != 16'777'217 ||
      parsed_contact_request.target_province_id != 3) {
    return Fail("actual-contact canonical parser rejected a valid scope");
  }
  constexpr std::array<std::string_view, 5> invalid_contact_steps{
      "query-actual-contact-scope-v1-016777217-at-3",
      "query-actual-contact-scope-v1-16777217-at-03",
      "query-actual-contact-scope-v1-16777217-at-0",
      "query-actual-contact-scope-v1-16777217-at-3-at-4",
      "query-actual-contact-scope-v1-2147483648-at-3",
  };
  for (const auto invalid : invalid_contact_steps) {
    if (xar::ck3_11906::ParseActualContactScopeV1Step(
            invalid, parsed_contact_request)) {
      return Fail("actual-contact parser accepted a non-canonical scope");
    }
  }
  std::uint64_t parsed_contact_revision = 0;
  if (!xar::ck3_11906::ParseActualContactExpectedRevisionV1(
          "{\"expected_revision\":4294967297}",
          parsed_contact_revision) ||
      parsed_contact_revision != 4'294'967'297ULL ||
      xar::ck3_11906::ParseActualContactExpectedRevisionV1(
          "{\"expected_revision\":7,\"expected_revision\":8}",
          parsed_contact_revision)) {
    return Fail("actual-contact revision parser lost strict uint64 binding");
  }
  xar::ck3_11906::ActualContactScopeMailboxContextV1 forged_contact_query{};
  xar::ck3_11906::MainThreadExecutionStampV1 forged_contact_stamp{};
  if (xar::ck3_11906::ExecuteActualContactScopeMailboxQueryV1(
          &forged_contact_query, forged_contact_stamp) ||
      forged_contact_query.completion !=
          xar::ck3_11906::ActualContactScopeMailboxCompletionV1::
              infrastructure_rejected) {
    return Fail("actual-contact executor accepted a direct worker-thread call");
  }

  xar::game::RouteContactHorizonRequest parsed_route_request{};
  if (!xar::ck3_11906::ParseRouteContactHorizonV1Step(
          "query-route-contact-horizon-v1-16777217-to-3-h-2-16777218-33554433",
          parsed_route_request) ||
      parsed_route_request.subject_army_id != 16'777'217 ||
      parsed_route_request.target_province_id != 3 ||
      parsed_route_request.hostile_army_ids !=
          std::vector<std::int32_t>{16'777'218, 33'554'433}) {
    return Fail("route-contact canonical step parser rejected a valid scope");
  }
  constexpr std::array<std::string_view, 7> invalid_route_steps{
      "query-route-contact-horizon-v1-016777217-to-3-h-1-16777218",
      "query-route-contact-horizon-v1-16777217-to-03-h-1-16777218",
      "query-route-contact-horizon-v1-16777217-to-3-h-2-16777218",
      "query-route-contact-horizon-v1-16777217-to-3-h-2-16777218-16777218",
      "query-route-contact-horizon-v1-16777217-to-3-h-1-16777217",
      "query-route-contact-horizon-v1-16777217-to-3-h-0-16777218",
      "query-route-contact-horizon-v1-16777217-to-3-h-2-33554433-16777218",
  };
  for (const auto invalid : invalid_route_steps) {
    if (xar::ck3_11906::ParseRouteContactHorizonV1Step(
            invalid, parsed_route_request)) {
      return Fail("route-contact parser accepted a non-canonical scope");
    }
  }
  std::uint64_t parsed_expected_revision = 0;
  if (!xar::ck3_11906::ParseRouteContactExpectedRevisionV1(
          "{\"type\":\"execute_step\",\"expected_revision\":4294967297,"
          "\"step\":\"query-route-contact-horizon-v1-16777217-to-3-h-1-16777218\"}",
          parsed_expected_revision) ||
      parsed_expected_revision != 4'294'967'297ULL) {
    return Fail("route-contact revision parser narrowed uint64 state");
  }
  if (!xar::ck3_11906::ParseRouteContactExpectedRevisionV1(
          "{\"type\": \"execute_step\", \"expected_revision\": "
          "4294967297 , \"step\": \"route\"}",
          parsed_expected_revision) ||
      parsed_expected_revision != 4'294'967'297ULL) {
    return Fail("route-contact revision parser rejected JSON whitespace");
  }
  constexpr std::array<std::string_view, 5> invalid_route_envelopes{
      "{\"type\":\"execute_step\"}",
      "{\"expected_revision\":0}",
      "{\"expected_revision\":01}",
      "{\"expected_revision\":\"7\"}",
      "{\"expected_revision\":7,\"expected_revision\":8}",
  };
  for (const auto invalid : invalid_route_envelopes) {
    if (xar::ck3_11906::ParseRouteContactExpectedRevisionV1(
            invalid, parsed_expected_revision)) {
      return Fail("route-contact parser accepted an ambiguous revision");
    }
  }
  xar::game::Snapshot route_scope_snapshot{};
  route_scope_snapshot.paused = true;
  parsed_route_request.subject_army_id = 16'777'217;
  parsed_route_request.target_province_id = 3;
  parsed_route_request.hostile_army_ids = {16'777'218, 33'554'433};
  xar::game::ArmySnapshot route_scope_subject{};
  route_scope_subject.army_id = 16'777'217;
  route_scope_subject.controllable = true;
  route_scope_snapshot.player_armies.push_back(route_scope_subject);
  route_scope_snapshot.active_wars.resize(2);
  xar::game::ArmySnapshot first_scope_enemy{};
  first_scope_enemy.army_id = 16'777'218;
  xar::game::ArmySnapshot second_scope_enemy{};
  second_scope_enemy.army_id = 33'554'433;
  xar::game::ArmySnapshot retreating_scope_enemy{};
  retreating_scope_enemy.army_id = 50'331'649;
  retreating_scope_enemy.retreating = true;
  route_scope_snapshot.active_wars[0].enemy_armies = {
      first_scope_enemy, retreating_scope_enemy};
  route_scope_snapshot.active_wars[1].enemy_armies = {
      second_scope_enemy};
  if (!xar::ck3_11906::RouteContactHostileScopeMatchesSnapshotV1(
          route_scope_snapshot, parsed_route_request)) {
    return Fail("route-contact preflight omitted another active war's enemy");
  }
  parsed_route_request.hostile_army_ids = {16'777'218};
  if (xar::ck3_11906::RouteContactHostileScopeMatchesSnapshotV1(
          route_scope_snapshot, parsed_route_request)) {
    return Fail("route-contact preflight accepted an incomplete hostile union");
  }
  xar::ck3_11906::RouteContactHorizonMailboxContextV1 forged_route_query{};
  xar::ck3_11906::MainThreadExecutionStampV1 forged_route_stamp{};
  if (xar::ck3_11906::ExecuteRouteContactHorizonMailboxQueryV1(
          &forged_route_query, forged_route_stamp) ||
      forged_route_query.completion !=
          xar::ck3_11906::RouteContactHorizonMailboxCompletionV1::
              infrastructure_rejected) {
    return Fail("route-contact executor accepted a direct worker-thread call");
  }
  using RouteCompletion =
      xar::ck3_11906::RouteContactHorizonMailboxCompletionV1;
  using RouteStatus = xar::game::RouteContactHorizonStatus;
  using RouteWait = xar::ck3_11906::MainThreadQueryWaitResultV1;
  if (xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::executor_failed, RouteCompletion::not_executed,
          RouteStatus::unavailable, false) !=
          "application-main route-contact executor failed before recording completion" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::executor_failed,
          RouteCompletion::infrastructure_rejected,
          RouteStatus::unavailable, false) !=
          "application-main route-contact executor gate rejected execution" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::infrastructure_failed, RouteCompletion::available,
          RouteStatus::available, false) !=
          "application-main route-contact boundary drifted after execution" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::timeout_cancelled_before_execution,
          RouteCompletion::not_executed, RouteStatus::unavailable, false) !=
          "application-main route-contact query timed out before execution" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::completed, RouteCompletion::query_unavailable,
          RouteStatus::timeline_unavailable, false) !=
          "CK3 route arrival timeline is unavailable" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::completed, RouteCompletion::query_unavailable,
          RouteStatus::unavailable, false) !=
          "CK3 route-contact reader is unavailable" ||
      xar::ck3_11906::RouteContactHorizonFailureMessageV1(
          RouteWait::completed, RouteCompletion::available,
          RouteStatus::available, false) !=
          "route-contact completion snapshot changed") {
    return Fail("route-contact failure stages collapsed into a generic error");
  }
  xar::game::RouteContactHorizonSnapshot diagnostic_route_failure{};
  diagnostic_route_failure.status = RouteStatus::timeline_unavailable;
  diagnostic_route_failure.timeline_failure.role =
      xar::game::RouteContactTimelineFailureRole::subject;
  diagnostic_route_failure.timeline_failure.army_id = 150'995'107;
  diagnostic_route_failure.timeline_failure.path_kind =
      xar::game::RouteContactTimelinePathKind::committed_active;
  diagnostic_route_failure.timeline_failure.stage =
      xar::game::RouteContactTimelineFailureStage::current_edge_speed;
  if (xar::ck3_11906::RouteContactHorizonFailureDetailV1(
          RouteWait::completed, RouteCompletion::query_unavailable,
          diagnostic_route_failure, false) !=
          "CK3 route arrival timeline is unavailable (role=subject, "
          "army_id=150995107, path=committed_active, "
          "stage=current_edge_speed)" ||
      xar::ck3_11906::RouteContactHorizonFailureDetailV1(
          RouteWait::infrastructure_failed, RouteCompletion::query_unavailable,
          diagnostic_route_failure, false) !=
          "application-main route-contact boundary drifted after execution" ||
      xar::ck3_11906::RouteContactHorizonFailureDetailV1(
          RouteWait::completed, RouteCompletion::query_unavailable,
          diagnostic_route_failure, false)
              .size() >
          xar::ck3_11906::
              kRouteContactHorizonV1FailureDetailMaximumBytes) {
    return Fail("route-contact timeline provenance was not failure-only");
  }

  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x28> jomini_state{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x1100> game_data{};
  void *game_state_pointer = game_state.data();
  void *jomini_state_pointer = jomini_state.data();
  Store(game_state, 0x08, std::int32_t{43'823'104});
  Store(game_state, 0x70, std::int32_t{3});
  Store(game_state, 0xA0, static_cast<void *>(game_data.data()));
  Store(jomini_state, 0x18, static_cast<void *>(players.data()));
  Store(jomini_state, 0x20, std::uint8_t{0});
  Store(players, 0x1F0, std::int32_t{41});
  Store(g_player, 0x70, std::int32_t{41});
  Store(g_active_event, 0x1B0, static_cast<void *>(g_event_data.data()));
  Store(g_active_event, 0x1BC, std::int32_t{77});
  Store(g_event_data, 0x1BC, std::int32_t{3});
  g_expected_event_manager = game_data.data();

  constexpr std::int32_t played_character_id = 0x01000002;
  constexpr std::int32_t enemy_character_id = 0x01000003;
  Store(game_data, 0x158,
        static_cast<void *>(g_player_character_entries.data()));
  Store(game_data, 0x164, std::int32_t{1});
  Store(g_player_character_entries, 0,
        static_cast<void *>(g_player_character_entry.data()));
  Store(g_player_character_entry, 0xB0, played_character_id);
  Store(g_player_character_entry, 0xD8, std::int32_t{41});
  Store(g_character_storage, 0x20,
        static_cast<void *>(g_character_slots.data()));
  Store(g_character_storage, 0x2C, std::int32_t{6});
  Store(g_character_slots, 0x28,
        static_cast<void *>(g_played_character.data()));
  Store(g_character_slots, 0x38,
        static_cast<void *>(g_target_character.data()));
  Store(g_character_slots, 0x48,
        static_cast<void *>(g_dead_character.data()));
  Store(g_character_slots, 0x58,
        static_cast<void *>(g_generation_mismatch_character.data()));
  Store(g_character_slots, 0x68,
        static_cast<void *>(g_ally_character.data()));
  Store(g_played_character, 0x18, played_character_id);
  Store(g_played_character, 0x1A0,
        static_cast<void *>(g_played_family_data.data()));
  Store(g_played_character, 0x1C8, static_cast<void *>(nullptr));
  Store(g_target_character, 0x18, enemy_character_id);
  Store(g_target_character, 0x1C8, static_cast<void *>(nullptr));
  Store(g_dead_character, 0x18, kFixtureDeadCharacterId);
  Store(g_dead_character, 0x1C8,
        static_cast<void *>(g_dead_character.data()));
  Store(g_generation_mismatch_character, 0x18,
        std::int32_t{0x01000006});
  Store(g_generation_mismatch_character, 0x1C8,
        static_cast<void *>(nullptr));
  Store(g_ally_character, 0x18, kFixtureAllyCharacterId);
  Store(g_ally_character, 0x1C8, static_cast<void *>(nullptr));
  g_character_validity_vtable[1] =
      reinterpret_cast<std::uintptr_t>(&FixtureCharacterValid);
  Store(g_played_character, 0x10,
        static_cast<void *>(g_character_validity_vtable.data()));
  Store(g_target_character, 0x10,
        static_cast<void *>(g_character_validity_vtable.data()));
  Store(g_ally_character, 0x10,
        static_cast<void *>(g_character_validity_vtable.data()));
  Store(g_played_character, 0xE8, std::int32_t{12});
  Store(g_target_character, 0xE8, std::int32_t{8});
  Store(g_played_character, 0x1B0,
        static_cast<void *>(g_played_knight_link.data()));
  Store(g_target_character, 0x1B0,
        static_cast<void *>(g_target_knight_link.data()));
  Store(g_played_character, 0x1A8,
        static_cast<void *>(g_played_character_extension.data()));
  Store(g_target_character, 0x1A8,
        static_cast<void *>(g_target_character_extension.data()));
  Store(g_played_character, 0x1C0,
        static_cast<void *>(g_played_legitimacy_data.data()));
  Store(g_target_character, 0x1C0,
        static_cast<void *>(g_target_legitimacy_data.data()));
  Store(g_played_character_extension, 0x100,
        std::int64_t{35'000'000});
  Store(g_played_character_extension, 0x110,
        std::int64_t{5'000'000});
  Store(g_played_character_extension, 0x118,
        std::int64_t{30'000'000});
  Store(g_played_character_extension, 0x130,
        std::int64_t{12'000'000});
  Store(g_played_character_extension, 0x138,
        std::int64_t{100'000'000});
  Store(g_played_character_extension, 0x2B0,
        std::int64_t{500'000});
  Store(g_target_character_extension, 0x100,
        std::int64_t{80'000'000});
  Store(g_target_character_extension, 0x110,
        std::int64_t{9'000'000});
  Store(g_target_character_extension, 0x118,
        std::int64_t{60'000'000});
  Store(g_target_character_extension, 0x130,
        std::int64_t{45'000'000});
  Store(g_target_character_extension, 0x138,
        std::int64_t{200'000'000});
  Store(g_target_character_extension, 0x2B0,
        std::int64_t{800'000});
  Store(g_played_character_extension, 0x2F8, std::int32_t{42});
  Store(g_target_character_extension, 0x2F8, std::int32_t{87});
  Store(g_played_legitimacy_data, 0x28, std::int64_t{8'000'000});
  Store(g_target_legitimacy_data, 0x28, std::int64_t{7'000'000});
  constexpr std::int32_t stale_enemy_character_id = 0x02000003;
  Store(g_played_family_data, 0x10, enemy_character_id);
  Store(g_played_family_data, 0x14, enemy_character_id);
  g_played_spouse_ids = {enemy_character_id, stale_enemy_character_id};
  Store(g_played_family_data, 0x20,
        static_cast<void *>(g_played_spouse_ids.data()));
  Store(g_played_family_data, 0x28, std::int32_t{2});
  Store(g_played_family_data, 0x2C, std::int32_t{2});
  g_character_storage_pointer = g_character_storage.data();

  Store(g_exit_attacker_scope, 0x00, std::uint16_t{4});
  Store(g_exit_attacker_scope, 0x08, played_character_id);
  Store(g_exit_defender_scope, 0x00, std::uint16_t{4});
  Store(g_exit_defender_scope, 0x08, enemy_character_id);
  Store(g_exit_ally_scope, 0x00, std::uint16_t{4});
  Store(g_exit_ally_scope, 0x08, kFixtureAllyCharacterId);
  g_effect_preview_collector_vtable[1] =
      reinterpret_cast<void *>(&FixtureOriginalEffectPreviewCallback);
  const auto prestige_vtable =
      reinterpret_cast<std::uintptr_t>(g_prestige_effect_node.data());
  const auto legitimacy_vtable =
      reinterpret_cast<std::uintptr_t>(g_legitimacy_effect_node.data());
  const auto stress_vtable =
      reinterpret_cast<std::uintptr_t>(g_stress_effect_node.data());
  const auto attacker_contribution_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_attacker_contribution_effect_node.data());
  const auto defender_contribution_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_defender_contribution_effect_node.data());
  const auto gold_vtable = reinterpret_cast<std::uintptr_t>(
      g_gold_transfer_effect_node.data());
  const auto truce_vtable =
      reinterpret_cast<std::uintptr_t>(g_truce_effect_node.data());
  const auto unknown_vtable =
      reinterpret_cast<std::uintptr_t>(g_unknown_effect_node.data());
  Store(g_prestige_effect_node, 0x00, prestige_vtable);
  Store(g_legitimacy_effect_node, 0x00, legitimacy_vtable);
  Store(g_stress_effect_node, 0x00, stress_vtable);
  Store(g_attacker_contribution_effect_node, 0x00,
        attacker_contribution_vtable);
  Store(g_defender_contribution_effect_node, 0x00,
        defender_contribution_vtable);
  Store(g_gold_transfer_effect_node, 0x00, gold_vtable);
  Store(g_truce_effect_node, 0x00, truce_vtable);
  Store(g_unknown_effect_node, 0x00, unknown_vtable);
  g_raiktor_preview_collector_vtable[1] =
      reinterpret_cast<void *>(&FixtureOriginalRaiktorPreviewCallback);
  Store(g_raiktor_loaded_effect, 0x00,
        static_cast<void *>(g_raiktor_loaded_effect_vtable.data()));
  Store(g_raiktor_add_hook_effect_node, 0x00,
        static_cast<void *>(g_raiktor_add_hook_effect_vtable.data()));
  Store(g_raiktor_add_hook_effect_node, 0x60,
        static_cast<void *>(g_raiktor_favor_hook_type.data()));
  Store(g_raiktor_add_hook_effect_node, 0x6C, std::uint8_t{2});
  Store(g_raiktor_no_toast_effect_node, 0x00,
        static_cast<void *>(
            g_raiktor_add_hook_no_toast_effect_vtable.data()));
  Store(g_raiktor_no_toast_effect_node, 0x60,
        static_cast<void *>(g_raiktor_favor_hook_type.data()));
  Store(g_raiktor_no_toast_effect_node, 0x6C, std::uint8_t{2});
  Store(g_raiktor_favor_hook_type, 0x00,
        static_cast<void *>(g_raiktor_hook_type_vtable.data()));
  Store(g_raiktor_favor_hook_type, 0x10, std::int32_t{3});
  Store(g_raiktor_favor_hook_type, 0x14,
        kFixtureFavorHookStableHash);
  constexpr char favor_hook_key[] = "favor_hook";
  std::memcpy(g_raiktor_favor_hook_type.data() + 0x18,
              favor_hook_key, sizeof(favor_hook_key));
  Store(g_raiktor_favor_hook_type, 0x28,
        std::size_t{sizeof(favor_hook_key) - 1});
  Store(g_raiktor_favor_hook_type, 0x30, std::size_t{15});
  g_raiktor_hook_type_database_pointer =
      g_raiktor_hook_type_database.data();
  g_raiktor_hook_type_fallback_pointer =
      g_raiktor_hook_type_fallback.data();
  g_white_peace_loaded_effect_vtable[11] =
      reinterpret_cast<void *>(&FixtureLoadedEffectSlot58);
  g_defeat_loaded_effect_vtable[11] =
      reinterpret_cast<void *>(&FixtureLoadedEffectSlot58);
  g_context_effect_vtable[11] =
      reinterpret_cast<void *>(&FixtureLoadedEffectSlot58);
  Store(g_casus_belli_type_0, 0x9C8,
        static_cast<void *>(g_white_peace_loaded_effect_vtable.data()));
  Store(g_casus_belli_type_0, 0xA28,
        static_cast<void *>(g_white_peace_loaded_effect_vtable.data()));

  g_exit_root_effect_children.fill(g_unknown_effect_node.data());
  g_exit_root_effect_children[8] = g_truce_scripted_effect.data();
  g_defeat_root_effect_children.fill(g_unknown_effect_node.data());
  g_defeat_root_effect_children[9] = g_truce_scripted_effect.data();
  g_truce_scripted_default_children.fill(g_unknown_effect_node.data());
  g_truce_scripted_default_children[2] = g_truce_hidden_effect.data();
  g_truce_hidden_children[0] = g_truce_context_effect.data();
  g_truce_context_children[0] = g_truce_effect_node.data();
  Store(g_casus_belli_type_0, 0x9C8 + 0x40,
        static_cast<void *>(g_exit_root_effect_children.data()));
  Store(g_casus_belli_type_0, 0x9C8 + 0x48, std::int32_t{13});
  Store(g_casus_belli_type_0, 0x9C8 + 0x4C, std::int32_t{10});
  Store(g_casus_belli_type_0, 0xA28 + 0x40,
        static_cast<void *>(g_defeat_root_effect_children.data()));
  Store(g_casus_belli_type_0, 0xA28 + 0x48, std::int32_t{19});
  Store(g_casus_belli_type_0, 0xA28 + 0x4C, std::int32_t{14});
  Store(g_truce_scripted_effect, 0x00,
        static_cast<void *>(g_scripted_effect_vtable.data()));
  Store(g_truce_scripted_effect, 0x60,
        static_cast<void *>(g_truce_scripted_effect_template.data()));
  Store(g_truce_scripted_effect, 0x94, std::int32_t{0});
  Store(g_truce_scripted_effect_template, 0x00,
        static_cast<void *>(g_scripted_effect_template_vtable.data()));
  Store(g_truce_scripted_effect_template, 0x120,
        static_cast<void *>(g_truce_scripted_default_effect.data()));
  Store(g_truce_scripted_default_effect, 0x00,
        static_cast<void *>(g_white_peace_loaded_effect_vtable.data()));
  Store(g_truce_scripted_default_effect, 0x40,
        static_cast<void *>(g_truce_scripted_default_children.data()));
  Store(g_truce_scripted_default_effect, 0x48, std::int32_t{6});
  Store(g_truce_scripted_default_effect, 0x4C, std::int32_t{5});
  Store(g_truce_hidden_effect, 0x00,
        static_cast<void *>(g_hidden_effect_vtable.data()));
  Store(g_truce_hidden_effect, 0x40,
        static_cast<void *>(g_truce_hidden_children.data()));
  Store(g_truce_hidden_effect, 0x48, std::int32_t{1});
  Store(g_truce_hidden_effect, 0x4C, std::int32_t{1});
  Store(g_truce_context_effect, 0x00,
        static_cast<void *>(g_context_effect_vtable.data()));
  Store(g_truce_context_effect, 0x40,
        static_cast<void *>(g_truce_context_children.data()));
  Store(g_truce_context_effect, 0x48, std::int32_t{1});
  Store(g_truce_context_effect, 0x4C, std::int32_t{1});
  Store(g_truce_context_effect, 0x60,
        static_cast<void *>(g_exit_attacker_scope.data()));
  Store(g_truce_context_effect, 0x6C, std::int32_t{1});
  g_effect_context_allocator_vtable[2] =
      reinterpret_cast<void *>(&FixtureFreeEffectContextArray);
  Store(g_effect_context_allocator, 0x00,
        static_cast<void *>(g_effect_context_allocator_vtable.data()));

  Store(g_global_variable_container, 0x10,
        static_cast<void *>(g_global_variable_entries.data()));
  Store(g_global_variable_container, 0x1C, std::int32_t{12});
  FixtureSetGlobalNumeric(0, 0);
  FixtureSetGlobalNumeric(1, kFixtureFixedPointScale);
  FixtureSetGlobalCharacter(2, kFixtureDeadCharacterId);
  FixtureSetGlobalNumeric(3, 12'345'678);
  FixtureSetGlobalNumeric(4, 9'876'543);
  FixtureSetGlobalNumeric(5, 42 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(6, 50 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(7, -8 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(8, 3 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(9, 2 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(10, 7 * kFixtureFixedPointScale);
  FixtureSetGlobalNumeric(11, kFixtureFixedPointScale);

  constexpr std::int32_t player_army_id = 0x01000001;
  constexpr std::int32_t enemy_army_id = 0x01000002;
  constexpr std::int32_t third_army_id = 0x01000003;
  constexpr std::int32_t player_internal_army_id = 0x02000011;
  constexpr std::int32_t enemy_internal_army_id = 0x02000012;
  constexpr std::int32_t third_internal_army_id = 0x02000013;
  constexpr std::int32_t ai_coordinator_id = 0x07000001;
  constexpr std::uintptr_t ai_coordinator_vtable = 0x71000010;
  constexpr std::uintptr_t ai_unit_stack_vtable = 0x71000020;
  constexpr std::uintptr_t ai_subunit_stack_vtable = 0x71000030;
  constexpr std::int32_t player_regiment_0_id = 0x01000001;
  constexpr std::int32_t player_regiment_1_id = 0x01000002;
  constexpr std::int32_t enemy_regiment_0_id = 0x01000003;
  constexpr std::int32_t enemy_regiment_1_id = 0x01000004;
  constexpr std::int32_t active_combat_id = 0x01000001;
  constexpr std::int32_t contact_combat_0_id = 0x01000002;
  constexpr std::int32_t contact_combat_1_id = 0x01000003;
  constexpr std::int32_t contact_battle_result_id = 0x01000001;
  constexpr std::int32_t active_war_id = 0x01000001;
  constexpr std::int32_t targeted_title_id = 0x01000001;
  constexpr std::int32_t targeted_duchy_a_title_id = 0x01000002;
  constexpr std::int32_t targeted_duchy_b_title_id = 0x01000003;
  constexpr std::int32_t capital_county_title_id = 0x01000004;
  constexpr std::int32_t second_county_title_id = 0x01000005;
  constexpr std::int32_t third_county_title_id = 0x01000006;
  constexpr std::int32_t capital_barony_title_id = 0x01000007;
  constexpr std::int32_t second_capital_barony_title_id = 0x01000008;
  constexpr std::int32_t third_capital_barony_title_id = 0x01000009;
  constexpr std::int32_t war_objective_province_id = 1;
  constexpr std::int32_t second_war_objective_province_id = 5;
  constexpr std::int32_t third_war_objective_province_id = 6;
  constexpr std::int32_t active_siege_id = 0x01000001;
  Store(g_war_objective_province, 0x10, war_objective_province_id);
  Store(g_second_war_objective_province, 0x10,
        second_war_objective_province_id);
  Store(g_third_war_objective_province, 0x10,
        third_war_objective_province_id);
  Store(g_war_objective_province, 0x744, std::int32_t{-1});
  Store(g_second_war_objective_province, 0x744, enemy_character_id);
  Store(g_third_war_objective_province, 0x744, std::int32_t{-1});
  Store(g_war_objective_province, 0x790, active_siege_id);
  Store(g_second_war_objective_province, 0x790, std::int32_t{-1});
  Store(g_third_war_objective_province, 0x790, std::int32_t{-1});
  Store(g_war_objective_province, 0x858, std::int32_t{2});
  Store(g_second_war_objective_province, 0x858, std::int32_t{0});
  Store(g_third_war_objective_province, 0x858, std::int32_t{3});
  Store(g_player_province, 0x10, std::int32_t{2});
  Store(g_enemy_province, 0x10, std::int32_t{3});
  Store(g_enemy_default_raise_province, 0x10, std::int32_t{4});
  Store(g_player_province, 0x08,
        static_cast<void *>(g_player_map_node.data()));
  Store(g_enemy_province, 0x08,
        static_cast<void *>(g_enemy_map_node.data()));
  Store(g_player_map_node, 0x50,
        static_cast<void *>(g_player_target_adjacency.data()));
  Store(g_player_map_node, 0x5C, std::int32_t{1});
  Store(g_player_target_adjacency, 0x00, std::int32_t{2});
  Store(g_player_target_adjacency, 0x04,
        second_war_objective_province_id);
  Store(g_enemy_map_node, 0x50,
        static_cast<void *>(g_enemy_target_adjacency.data()));
  Store(g_enemy_map_node, 0x5C, std::int32_t{1});
  Store(g_enemy_target_adjacency, 0x00, std::int32_t{2});
  Store(g_enemy_target_adjacency, 0x04,
        second_war_objective_province_id);
  g_preview_effective_origin = g_player_province.data();
  Store(g_provinces, 2 * sizeof(void *),
        static_cast<void *>(g_player_province.data()));
  Store(g_provinces, 3 * sizeof(void *),
        static_cast<void *>(g_enemy_province.data()));
  Store(g_provinces, 4 * sizeof(void *),
        static_cast<void *>(g_enemy_default_raise_province.data()));
  Store(g_provinces, 1 * sizeof(void *),
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_provinces, 5 * sizeof(void *),
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_provinces, 6 * sizeof(void *),
        static_cast<void *>(g_third_war_objective_province.data()));
  Store(game_data, 0x140, static_cast<void *>(g_provinces.data()));
  Store(game_data, 0x14C, std::int32_t{7});

  Store(g_player_army, 0x10, player_army_id);
  Store(g_player_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_player_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_player_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_player_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_player_move_route_info_2, 0x00, std::int32_t{3});
  g_player_move_path = {g_player_move_route_info_0.data(),
                        g_player_move_route_info_1.data(),
                        g_player_move_route_info_2.data()};
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_preview_move_route_info_2, 0x00, std::int32_t{3});
  g_preview_move_path = {g_preview_move_route_info_0.data(),
                         g_preview_move_route_info_1.data(),
                         g_preview_move_route_info_2.data()};
  Store(g_player_army, 0x38,
        static_cast<void *>(g_player_move_path.data()));
  Store(g_player_army, 0x40, std::int32_t{3});
  Store(g_player_army, 0x44, std::int32_t{3});
  Store(g_player_army, 0x170, std::int32_t{0});
  Store(g_player_army, 0x174, played_character_id);
  Store(g_player_army, 0x178, player_internal_army_id);
  Store(g_player_army, 0x190, std::int64_t{100'000});
  Store(g_enemy_army, 0x10, enemy_army_id);
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_enemy_army, 0x170, std::int32_t{1});
  Store(g_enemy_army, 0x174, enemy_character_id);
  Store(g_enemy_army, 0x178, enemy_internal_army_id);
  Store(g_enemy_army, 0x190, std::int64_t{100'000});
  Store(g_third_army, 0x10, third_army_id);
  Store(g_third_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_third_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_third_army, 0x170, std::int32_t{0});
  Store(g_third_army, 0x174, played_character_id);
  Store(g_third_army, 0x178, third_internal_army_id);
  Store(g_army_slots, 0x18, static_cast<void *>(g_player_army.data()));
  Store(g_army_slots, 0x28, static_cast<void *>(g_enemy_army.data()));
  Store(g_army_storage, 0x20, static_cast<void *>(g_army_slots.data()));
  Store(g_army_storage, 0x2C, std::int32_t{4});
  g_army_storage_pointer = g_army_storage.data();

  g_player_regiment_ids = {player_regiment_0_id, player_regiment_1_id};
  g_enemy_regiment_ids = {enemy_regiment_0_id, enemy_regiment_1_id};
  Store(g_player_internal_army, 0x10, player_internal_army_id);
  Store(g_player_internal_army, 0x38,
        static_cast<void *>(g_player_regiment_ids.data()));
  Store(g_player_internal_army, 0x40, std::int32_t{2});
  Store(g_player_internal_army, 0x44, std::int32_t{2});
  Store(g_player_internal_army, 0x120, played_character_id);
  Store(g_player_internal_army, 0x124, player_army_id);
  Store(g_player_internal_army, 0x128, active_combat_id);
  Store(g_enemy_internal_army, 0x10, enemy_internal_army_id);
  Store(g_enemy_internal_army, 0x38,
        static_cast<void *>(g_enemy_regiment_ids.data()));
  Store(g_enemy_internal_army, 0x40, std::int32_t{2});
  Store(g_enemy_internal_army, 0x44, std::int32_t{2});
  Store(g_enemy_internal_army, 0x120, std::int32_t{-1});
  Store(g_enemy_internal_army, 0x124, enemy_army_id);
  Store(g_enemy_internal_army, 0x128, std::int32_t{-1});
  Store(g_third_internal_army, 0x10, third_internal_army_id);
  Store(g_third_internal_army, 0x38, static_cast<void *>(nullptr));
  Store(g_third_internal_army, 0x40, std::int32_t{0});
  Store(g_third_internal_army, 0x44, std::int32_t{0});
  Store(g_third_internal_army, 0x120, std::int32_t{-1});
  Store(g_third_internal_army, 0x124, third_army_id);
  Store(g_third_internal_army, 0x128, std::int32_t{-1});
  Store(g_internal_army_slots, 0x118,
        static_cast<void *>(g_player_internal_army.data()));
  Store(g_internal_army_slots, 0x128,
        static_cast<void *>(g_enemy_internal_army.data()));
  Store(g_internal_army_slots, 0x138,
        static_cast<void *>(g_third_internal_army.data()));
  Store(g_internal_army_storage, 0x20,
        static_cast<void *>(g_internal_army_slots.data()));
  Store(g_internal_army_storage, 0x2C, std::int32_t{20});
  g_internal_army_storage_pointer = g_internal_army_storage.data();

  g_ai_coordinator_unit_stacks = {g_ai_unit_stack.data()};
  g_ai_support_provinces = {
      g_second_war_objective_province.data(),
      g_second_war_objective_province.data(),
      g_third_war_objective_province.data()};
  g_ai_parent_cunit_ids = {player_army_id, enemy_army_id};
  g_ai_parent_subunits = {
      g_ai_selected_subunit.data(), g_ai_sibling_subunit.data()};
  g_ai_selected_cunit_ids = {player_army_id};
  g_ai_sibling_cunit_ids = {enemy_army_id};
  Store(g_ai_coordinator, 0x00, ai_coordinator_vtable);
  Store(g_ai_coordinator, 0x10, ai_coordinator_id);
  Store(g_ai_coordinator, 0x50,
        static_cast<void *>(g_ai_coordinator_unit_stacks.data()));
  Store(g_ai_coordinator, 0x58, std::int32_t{1});
  Store(g_ai_coordinator, 0x5C, std::int32_t{1});
  Store(g_ai_coordinator_slots, 0x18,
        static_cast<void *>(g_ai_coordinator.data()));
  Store(g_ai_coordinator_storage, 0x20,
        static_cast<void *>(g_ai_coordinator_slots.data()));
  Store(g_ai_coordinator_storage, 0x2C, std::int32_t{2});
  g_ai_coordinator_storage_pointer = g_ai_coordinator_storage.data();
  g_ai_coordinator_fallback_pointer = g_ai_coordinator_fallback.data();

  Store(g_ai_unit_stack, 0x00, ai_unit_stack_vtable);
  Store(g_ai_unit_stack, 0x08,
        static_cast<void *>(g_ai_support_provinces.data()));
  Store(g_ai_unit_stack, 0x10, std::int32_t{3});
  Store(g_ai_unit_stack, 0x14, std::int32_t{3});
  Store(g_ai_unit_stack, 0x28,
        static_cast<void *>(g_ai_parent_cunit_ids.data()));
  Store(g_ai_unit_stack, 0x30, std::int32_t{2});
  Store(g_ai_unit_stack, 0x34, std::int32_t{2});
  Store(g_ai_unit_stack, 0x40,
        static_cast<void *>(g_ai_parent_subunits.data()));
  Store(g_ai_unit_stack, 0x48, std::int32_t{2});
  Store(g_ai_unit_stack, 0x4C, std::int32_t{2});
  Store(g_ai_unit_stack, 0x58, static_cast<void *>(g_ai_coordinator.data()));

  Store(g_ai_selected_subunit, 0x00, ai_subunit_stack_vtable);
  Store(g_ai_selected_subunit, 0x10,
        static_cast<void *>(g_ai_selected_cunit_ids.data()));
  Store(g_ai_selected_subunit, 0x18, std::int32_t{1});
  Store(g_ai_selected_subunit, 0x1C, std::int32_t{1});
  Store(g_ai_selected_subunit, 0x28, std::int64_t{9'999'999});
  Store(g_ai_selected_subunit, 0x34, std::uint8_t{1});
  Store(g_ai_selected_subunit, 0x38, std::int64_t{2'300'000});
  Store(g_ai_selected_subunit, 0x40,
        static_cast<void *>(g_ai_unit_stack.data()));
  Store(g_ai_selected_subunit, 0x48,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_ai_selected_subunit, 0x50, std::uint8_t{0x12});

  Store(g_ai_sibling_subunit, 0x00, ai_subunit_stack_vtable);
  Store(g_ai_sibling_subunit, 0x10,
        static_cast<void *>(g_ai_sibling_cunit_ids.data()));
  Store(g_ai_sibling_subunit, 0x18, std::int32_t{1});
  Store(g_ai_sibling_subunit, 0x1C, std::int32_t{1});
  Store(g_ai_sibling_subunit, 0x28, std::int64_t{3'100'000});
  Store(g_ai_sibling_subunit, 0x40,
        static_cast<void *>(g_ai_unit_stack.data()));
  Store(g_ai_sibling_subunit, 0x48,
        static_cast<void *>(g_third_war_objective_province.data()));
  Store(g_ai_sibling_subunit, 0x50, std::uint8_t{0x01});
  Store(g_player_army, 0x1C4, ai_coordinator_id);
  Store(g_player_army, 0x1D0,
        static_cast<void *>(g_ai_selected_subunit.data()));
  Store(g_enemy_army, 0x1D0,
        static_cast<void *>(g_ai_sibling_subunit.data()));

  g_regiment_identity_vtable[1] =
      reinterpret_cast<std::uintptr_t>(&FixtureRegimentIdentityValid);
  const auto initialize_regiment = [](auto &regiment, std::int32_t id,
                                      std::int32_t current,
                                      std::int32_t maximum,
                                      std::int64_t base_power) {
    Store(regiment, 0x08,
          static_cast<void *>(g_regiment_identity_vtable.data()));
    Store(regiment, 0x10, id);
    Store(regiment, 0x38, current);
    Store(regiment, 0x3C, maximum);
    Store(regiment, 0x40, base_power);
  };
  initialize_regiment(g_player_regiment_0, player_regiment_0_id, 600, 800,
                      std::int64_t{100'000'000});
  initialize_regiment(g_player_regiment_1, player_regiment_1_id, 400, 400,
                      std::int64_t{50'000'000});
  initialize_regiment(g_enemy_regiment_0, enemy_regiment_0_id, 500, 1000,
                      std::int64_t{150'000'000});
  initialize_regiment(g_enemy_regiment_1, enemy_regiment_1_id, 300, 500,
                      std::int64_t{90'000'000});
  Store(g_player_regiment_0, 0x140, player_internal_army_id);
  Store(g_player_regiment_1, 0x140, player_internal_army_id);
  Store(g_enemy_regiment_0, 0x140, enemy_internal_army_id);
  Store(g_enemy_regiment_1, 0x140, enemy_internal_army_id);
  Store(g_player_regiment_0, 0x148, played_character_id);
  Store(g_player_regiment_1, 0x148, std::int32_t{-1});
  Store(g_enemy_regiment_0, 0x148, enemy_character_id);
  Store(g_enemy_regiment_1, 0x148, std::int32_t{-1});
  Store(g_played_knight_link, 0xF8, player_regiment_0_id);
  Store(g_target_knight_link, 0xF8, enemy_regiment_0_id);
  g_database_object_validity_vtable[0] =
      reinterpret_cast<std::uintptr_t>(&FixtureDatabaseObjectValid);
  g_database_object_absent_vtable[0] =
      reinterpret_cast<std::uintptr_t>(&FixtureDatabaseObjectAbsent);
  g_combat_type_validity_vtable[0] =
      reinterpret_cast<std::uintptr_t>(&FixtureCombatTypeValid);
  Store(g_bowmen_type, 0x00,
        static_cast<void *>(g_database_object_validity_vtable.data()));
  std::memcpy(g_bowmen_type.data() + 0x18, "bowmen", 7);
  Store(g_bowmen_type, 0x28, std::size_t{6});
  Store(g_bowmen_type, 0x30, std::size_t{15});
  Store(g_armored_horsemen_type, 0x00,
        static_cast<void *>(g_database_object_validity_vtable.data()));
  Store(g_armored_horsemen_type, 0x18, g_armored_horsemen_key);
  Store(g_armored_horsemen_type, 0x28,
        std::size_t{sizeof(g_armored_horsemen_key) - 1});
  Store(g_armored_horsemen_type, 0x30,
        std::size_t{sizeof(g_armored_horsemen_key) - 1});
  Store(g_absent_maa_type, 0x00,
        static_cast<void *>(g_database_object_absent_vtable.data()));
  Store(g_player_regiment_0, 0x118,
        static_cast<void *>(g_bowmen_type.data()));
  Store(g_player_regiment_1, 0x118,
        static_cast<void *>(g_absent_maa_type.data()));
  Store(g_enemy_regiment_0, 0x118,
        static_cast<void *>(g_armored_horsemen_type.data()));
  Store(g_enemy_regiment_1, 0x118, static_cast<void *>(nullptr));

  const auto initialize_inner_type = [](auto &inner_type,
                                        std::int32_t class_index,
                                        void *targets,
                                        std::int32_t target_count,
                                        bool fights_in_main_phase) {
    Store(inner_type, 0x00,
          static_cast<void *>(g_combat_type_validity_vtable.data()));
    Store(inner_type, 0x68, std::int32_t{100});
    Store(inner_type, 0x270, class_index);
    Store(inner_type, 0x2B8, targets);
    Store(inner_type, 0x2C4, target_count);
    Store(inner_type, 0xA0A,
          static_cast<std::uint8_t>(fights_in_main_phase ? 1 : 0));
  };
  Store(g_player_counter_targets, 0x00, std::int32_t{1});
  Store(g_player_counter_targets, 0x08, std::int64_t{50'000});
  Store(g_enemy_counter_targets, 0x00, std::int32_t{0});
  Store(g_enemy_counter_targets, 0x08, std::int64_t{75'000});
  initialize_inner_type(g_player_regiment_0_inner_type, 0,
                        g_player_counter_targets.data(), 1, true);
  initialize_inner_type(g_player_regiment_1_inner_type, -1, nullptr, 0,
                        false);
  initialize_inner_type(g_enemy_regiment_0_inner_type, 1,
                        g_enemy_counter_targets.data(), 1, true);
  initialize_inner_type(g_enemy_regiment_1_inner_type, 2, nullptr, 0,
                        false);
  Store(g_player_regiment_0, 0x18,
        static_cast<void *>(g_player_regiment_0_inner_type.data()));
  Store(g_player_regiment_1, 0x18,
        static_cast<void *>(g_player_regiment_1_inner_type.data()));
  Store(g_enemy_regiment_0, 0x18,
        static_cast<void *>(g_enemy_regiment_0_inner_type.data()));
  Store(g_enemy_regiment_1, 0x18,
        static_cast<void *>(g_enemy_regiment_1_inner_type.data()));
  Store(g_combat_rules, 0xF14, std::int32_t{3});

  std::memcpy(g_hills_terrain.data() + 0x18, "hills", 6);
  Store(g_hills_terrain, 0x28, std::size_t{5});
  Store(g_hills_terrain, 0x30, std::size_t{15});
  Store(g_hills_terrain, 0x58, std::int64_t{80'000});
  Store(g_hills_terrain, 0x76E, std::uint16_t{0x200});
  Store(g_hills_terrain, 0x770, std::uint16_t{0x201});
  std::memcpy(g_plains_terrain.data() + 0x18, "plains", 7);
  Store(g_plains_terrain, 0x28, std::size_t{6});
  Store(g_plains_terrain, 0x30, std::size_t{15});
  Store(g_plains_terrain, 0x58, std::int64_t{100'000});
  Store(g_plains_terrain, 0x76E, std::uint16_t{0x202});
  Store(g_plains_terrain, 0x770, std::uint16_t{0x203});
  Store(g_regiment_slots, 0x18,
        static_cast<void *>(g_player_regiment_0.data()));
  Store(g_regiment_slots, 0x28,
        static_cast<void *>(g_player_regiment_1.data()));
  Store(g_regiment_slots, 0x38,
        static_cast<void *>(g_enemy_regiment_0.data()));
  Store(g_regiment_slots, 0x48,
        static_cast<void *>(g_enemy_regiment_1.data()));
  Store(g_regiment_storage, 0x20,
        static_cast<void *>(g_regiment_slots.data()));
  Store(g_regiment_storage, 0x2C, std::int32_t{5});
  g_regiment_storage_pointer = g_regiment_storage.data();

  Store(g_player_combat, 0x08, active_combat_id);
  Store(g_player_combat, 0x6B0, std::int32_t{1});
  Store(g_player_combat, 0x6B4, std::int32_t{4});
  Store(g_player_combat, 0x6B8,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_player_combat, 0x6C0, std::int32_t{1'200});
  Store(g_player_combat, 0x6C4, std::int32_t{960});
  Store(g_player_combat, 0x6C8, std::int64_t{-5'000'000'000});
  Store(g_player_combat, 0x6D0, std::int32_t{7});
  Store(g_player_combat, 0x6D4, std::int32_t{3});
  Store(g_player_combat, 0x710, std::int64_t{6'000'000'000});
  Store(g_combat_slots, 0x18,
        static_cast<void *>(g_player_combat.data()));
  Store(g_combat_storage, 0x20,
        static_cast<void *>(g_combat_slots.data()));
  Store(g_combat_storage, 0x2C, std::int32_t{2});
  g_combat_storage_pointer = g_combat_storage.data();

  g_contact_combat_0_attacker_armies = {enemy_internal_army_id};
  g_contact_combat_0_defender_armies = {third_internal_army_id};
  g_contact_combat_1_attacker_armies = {third_internal_army_id};
  g_contact_combat_1_defender_armies = {enemy_internal_army_id};
  const auto initialize_contact_combat =
      [&](auto &combat, std::int32_t combat_id,
          std::int32_t attacker_primary_character_id,
          std::int32_t defender_primary_character_id,
          auto &attacker_army_ids, auto &defender_army_ids) {
        Store(combat, 0x08, combat_id);
        Store(combat, 0x20 + 0x10,
              static_cast<void *>(attacker_army_ids.data()));
        Store(combat, 0x20 + 0x18, std::int32_t{1});
        Store(combat, 0x20 + 0x1C, std::int32_t{1});
        Store(combat, 0x20 + 0x70, attacker_primary_character_id);
        Store(combat, 0x20 + 0xB8,
              static_cast<void *>(combat.data()));
        Store(combat, 0x368 + 0x10,
              static_cast<void *>(defender_army_ids.data()));
        Store(combat, 0x368 + 0x18, std::int32_t{1});
        Store(combat, 0x368 + 0x1C, std::int32_t{1});
        Store(combat, 0x368 + 0x70, defender_primary_character_id);
        Store(combat, 0x368 + 0xB8,
              static_cast<void *>(combat.data()));
        Store(combat, 0x6B8,
              static_cast<void *>(g_war_objective_province.data()));
        Store(combat, 0x6E0, std::int32_t{-1});
        Store(combat, 0x704, std::uint8_t{0});
        Store(combat, 0x708, std::int32_t{-1});
      };
  initialize_contact_combat(
      g_contact_combat_0, contact_combat_0_id, enemy_character_id,
      played_character_id, g_contact_combat_0_attacker_armies,
      g_contact_combat_0_defender_armies);
  initialize_contact_combat(
      g_contact_combat_1, contact_combat_1_id, played_character_id,
      enemy_character_id, g_contact_combat_1_attacker_armies,
      g_contact_combat_1_defender_armies);
  Store(g_contact_combat_slots, 0x28,
        static_cast<void *>(g_contact_combat_0.data()));
  Store(g_contact_combat_slots, 0x38,
        static_cast<void *>(g_contact_combat_1.data()));
  Store(g_contact_combat_storage, 0x20,
        static_cast<void *>(g_contact_combat_slots.data()));
  Store(g_contact_combat_storage, 0x2C, std::int32_t{4});
  g_contact_combat_storage_pointer = g_contact_combat_storage.data();
  g_contact_battle_result_vtable[1] =
      reinterpret_cast<std::uintptr_t>(&FixtureBattleResultValid);
  Store(g_contact_battle_result, 0x00,
        static_cast<void *>(g_contact_battle_result_vtable.data()));
  Store(g_contact_battle_result, 0x08, contact_battle_result_id);
  Store(g_contact_battle_result, 0xC4, std::int32_t{0});
  Store(g_contact_battle_result, 0x28, std::uint8_t{1});
  Store(g_contact_battle_result, 0x2C, std::int32_t{43'822'744});
  Store(g_contact_battle_result_slots, 0x18,
        static_cast<void *>(g_contact_battle_result.data()));
  Store(g_contact_battle_result_storage, 0x20,
        static_cast<void *>(g_contact_battle_result_slots.data()));
  Store(g_contact_battle_result_storage, 0x2C, std::int32_t{2});
  g_contact_battle_result_storage_pointer =
      g_contact_battle_result_storage.data();
  g_contact_battle_result_fallback_pointer =
      g_contact_battle_result.data();
  Store(g_contact_game_mode_root, 0x1C0,
        static_cast<void *>(g_contact_game_mode.data()));
  g_contact_game_mode_pointer = g_contact_game_mode_root.data();
  Store(g_contact_province_gate, 0x1B, std::uint8_t{1});

  Store(g_siege, 0x08, active_siege_id);
  Store(g_siege, 0x200,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_siege, 0x208, player_internal_army_id);
  Store(g_siege, 0x3D0, std::int64_t{2'500'000});
  Store(g_siege, 0x3D8, std::int32_t{1});
  Store(g_siege, 0x44C, std::uint8_t{0});
  Store(g_siege_slots, 0x18, static_cast<void *>(g_siege.data()));
  Store(g_siege_storage, 0x20,
        static_cast<void *>(g_siege_slots.data()));
  Store(g_siege_storage, 0x2C, std::int32_t{2});
  g_siege_storage_pointer = g_siege_storage.data();

  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_attacker_participants, 0,
        static_cast<void *>(g_attacker_participant.data()));
  Store(g_defender_participants, 0,
        static_cast<void *>(g_defender_participant.data()));
  Store(g_war, 0x08, active_war_id);
  Store(g_war, 0x28, static_cast<void *>(g_attacker_participants.data()));
  Store(g_war, 0x30, std::int32_t{1});
  Store(g_war, 0x34, std::int32_t{1});
  Store(g_war, 0x88, static_cast<void *>(g_defender_participants.data()));
  Store(g_war, 0x90, std::int32_t{1});
  Store(g_war, 0x94, std::int32_t{1});
  Store(g_war, 0xE0, std::int32_t{43'822'864});
  Store(g_war, 0x100,
        static_cast<void *>(g_casus_belli_type_0.data()));
  g_war_targeted_title_ids = {
      targeted_title_id, targeted_duchy_a_title_id,
      second_county_title_id, third_capital_barony_title_id};
  Store(g_war, 0x270,
        static_cast<void *>(g_war_targeted_title_ids.data()));
  Store(g_war, 0x278, std::int32_t{4});
  Store(g_war, 0x27C, std::int32_t{4});
  Store(g_war, 0x288, played_character_id);
  Store(g_war, 0x28C, enemy_character_id);
  Store(g_war, 0x290, played_character_id);
  Store(g_war, 0x358, static_cast<void *>(nullptr));
  Store(g_war_slots, 0x18, static_cast<void *>(g_war.data()));
  Store(g_war_storage, 0x20, static_cast<void *>(g_war_slots.data()));
  Store(g_war_storage, 0x2C, std::int32_t{2});
  Store(game_data, 0x220, static_cast<void *>(g_war_storage.data()));

  Store(g_landed_title_slots, 0x18,
        static_cast<void *>(g_targeted_title.data()));
  Store(g_landed_title_slots, 0x28,
        static_cast<void *>(g_targeted_duchy_a_title.data()));
  Store(g_landed_title_slots, 0x38,
        static_cast<void *>(g_targeted_duchy_b_title.data()));
  Store(g_landed_title_slots, 0x48,
        static_cast<void *>(g_capital_county_title.data()));
  Store(g_landed_title_slots, 0x58,
        static_cast<void *>(g_second_county_title.data()));
  Store(g_landed_title_slots, 0x68,
        static_cast<void *>(g_third_county_title.data()));
  Store(g_landed_title_slots, 0x78,
        static_cast<void *>(g_capital_barony_title.data()));
  Store(g_landed_title_slots, 0x88,
        static_cast<void *>(g_second_capital_barony_title.data()));
  Store(g_landed_title_slots, 0x98,
        static_cast<void *>(g_third_capital_barony_title.data()));
  Store(g_landed_title_storage, 0x20,
        static_cast<void *>(g_landed_title_slots.data()));
  Store(g_landed_title_storage, 0x2C, std::int32_t{11});
  Store(game_data, 0x320,
        static_cast<void *>(g_landed_title_storage.data()));

  Store(g_targeted_title, 0x10, targeted_title_id);
  Store(g_targeted_title, 0x160,
        static_cast<void *>(g_targeted_title_template.data()));
  Store(g_targeted_title_template, 0x5C, std::int32_t{4});
  g_targeted_title_vassal_ids = {targeted_duchy_a_title_id,
                                 targeted_duchy_b_title_id};
  Store(g_targeted_title, 0x240,
        static_cast<void *>(g_targeted_title_vassal_ids.data()));
  Store(g_targeted_title, 0x248, std::int32_t{2});
  Store(g_targeted_title, 0x24C, std::int32_t{2});

  Store(g_targeted_duchy_a_title, 0x10, targeted_duchy_a_title_id);
  Store(g_targeted_duchy_a_title, 0x160,
        static_cast<void *>(g_targeted_duchy_a_template.data()));
  Store(g_targeted_duchy_a_template, 0x5C, std::int32_t{3});
  g_targeted_duchy_a_vassal_ids = {capital_county_title_id,
                                   second_county_title_id};
  Store(g_targeted_duchy_a_title, 0x240,
        static_cast<void *>(g_targeted_duchy_a_vassal_ids.data()));
  Store(g_targeted_duchy_a_title, 0x248, std::int32_t{2});
  Store(g_targeted_duchy_a_title, 0x24C, std::int32_t{2});

  Store(g_targeted_duchy_b_title, 0x10, targeted_duchy_b_title_id);
  Store(g_targeted_duchy_b_title, 0x160,
        static_cast<void *>(g_targeted_duchy_b_template.data()));
  Store(g_targeted_duchy_b_template, 0x5C, std::int32_t{3});
  g_targeted_duchy_b_vassal_ids = {third_county_title_id};
  Store(g_targeted_duchy_b_title, 0x240,
        static_cast<void *>(g_targeted_duchy_b_vassal_ids.data()));
  Store(g_targeted_duchy_b_title, 0x248, std::int32_t{1});
  Store(g_targeted_duchy_b_title, 0x24C, std::int32_t{1});

  Store(g_capital_county_title, 0x10, capital_county_title_id);
  Store(g_capital_county_title, 0x160,
        static_cast<void *>(g_capital_county_template.data()));
  Store(g_capital_county_template, 0x5C, std::int32_t{2});
  g_capital_county_vassal_ids = {capital_barony_title_id};
  Store(g_capital_county_title, 0x240,
        static_cast<void *>(g_capital_county_vassal_ids.data()));
  Store(g_capital_county_title, 0x248, std::int32_t{1});
  Store(g_capital_county_title, 0x24C, std::int32_t{1});

  Store(g_second_county_title, 0x10, second_county_title_id);
  Store(g_second_county_title, 0x160,
        static_cast<void *>(g_second_county_template.data()));
  Store(g_second_county_template, 0x5C, std::int32_t{2});
  g_second_county_vassal_ids = {second_capital_barony_title_id};
  Store(g_second_county_title, 0x240,
        static_cast<void *>(g_second_county_vassal_ids.data()));
  Store(g_second_county_title, 0x248, std::int32_t{1});
  Store(g_second_county_title, 0x24C, std::int32_t{1});

  Store(g_third_county_title, 0x10, third_county_title_id);
  Store(g_third_county_title, 0x160,
        static_cast<void *>(g_third_county_template.data()));
  Store(g_third_county_template, 0x5C, std::int32_t{2});
  g_third_county_vassal_ids = {third_capital_barony_title_id};
  Store(g_third_county_title, 0x240,
        static_cast<void *>(g_third_county_vassal_ids.data()));
  Store(g_third_county_title, 0x248, std::int32_t{1});
  Store(g_third_county_title, 0x24C, std::int32_t{1});

  Store(g_capital_barony_title, 0x10, capital_barony_title_id);
  Store(g_capital_barony_title, 0x160,
        static_cast<void *>(g_capital_barony_template.data()));
  Store(g_capital_barony_template, 0x5C, std::int32_t{1});
  Store(g_capital_barony_template, 0x80, war_objective_province_id);

  Store(g_second_capital_barony_title, 0x10,
        second_capital_barony_title_id);
  Store(g_second_capital_barony_title, 0x160,
        static_cast<void *>(g_second_capital_barony_template.data()));
  Store(g_second_capital_barony_template, 0x5C, std::int32_t{1});
  Store(g_second_capital_barony_template, 0x80,
        second_war_objective_province_id);

  Store(g_third_capital_barony_title, 0x10,
        third_capital_barony_title_id);
  Store(g_third_capital_barony_title, 0x160,
        static_cast<void *>(g_third_capital_barony_template.data()));
  Store(g_third_capital_barony_template, 0x5C, std::int32_t{1});
  Store(g_third_capital_barony_template, 0x80,
        third_war_objective_province_id);

  g_casus_belli_types = {g_casus_belli_type_0.data(),
                         g_casus_belli_type_1.data()};
  Store(g_casus_belli_database, 0x68,
        static_cast<void *>(g_casus_belli_types.data()));
  Store(g_casus_belli_database, 0x74, std::int32_t{2});
  Store(g_casus_belli_type_0, 0x38,
        static_cast<void *>(g_casus_belli_rule_0.data()));
  Store(g_casus_belli_type_1, 0x38,
        static_cast<void *>(g_casus_belli_rule_1.data()));
  Store(g_casus_belli_type_1, 0x10, std::int32_t{1});
  std::memcpy(g_casus_belli_type_0.data() + 0x18, g_casus_belli_key_0,
              sizeof(g_casus_belli_key_0));
  Store(g_casus_belli_type_0, 0x28,
        std::size_t{sizeof(g_casus_belli_key_0) - 1});
  Store(g_casus_belli_type_0, 0x30, std::size_t{15});
  Store(g_casus_belli_type_0, 0x1718, std::uint32_t{1U << 7U});
  Store(g_casus_belli_type_1, 0x18, g_casus_belli_key_1);
  Store(g_casus_belli_type_1, 0x28,
        std::size_t{sizeof(g_casus_belli_key_1) - 1});
  Store(g_casus_belli_type_1, 0x30,
        std::size_t{sizeof(g_casus_belli_key_1) - 1});
  Store(g_casus_belli_type_1, 0x1718, std::uint32_t{1U << 20U});
  // The interaction offsets are relative to CCharacterInteractionDatabase,
  // not to CK3GameData. Keep non-null traps at the obsolete base so this
  // fixture fails if that live-crash regression returns.
  Store(game_data, 0xF48, static_cast<void *>(g_enforce_demands_marker.data()));
  Store(game_data, 0xF78, static_cast<void *>(g_enforce_demands_marker.data()));
  Store(g_character_interaction_database, 0xF48,
        static_cast<void *>(g_arrange_marriage_interaction.data()));
  Store(g_character_interaction_database, 0xF78,
        static_cast<void *>(g_declare_war_interaction.data()));
  Store(g_surrender_interaction, 0x2580,
        static_cast<void *>(g_auto_accept_trigger.data()));
  Store(g_surrender_interaction, 0x2A48, std::uint8_t{0});
  Store(g_white_peace_interaction, 0x2580,
        static_cast<void *>(nullptr));
  Store(g_white_peace_interaction, 0x2A48, std::uint8_t{0});
  Store(g_victory_interaction, 0x2580,
        static_cast<void *>(nullptr));
  Store(g_victory_interaction, 0x2A48, std::uint8_t{1});

  Bindings bindings{};
  bindings.enabled = true;
  bindings.game_state_slot = &game_state_pointer;
  bindings.jomini_state_slot = &jomini_state_pointer;
  bindings.command_manager = reinterpret_cast<void *>(0x1234);
  bindings.pause_primary_vtable = 0x11111111;
  bindings.pause_secondary_vtable = 0x22222222;
  bindings.set_speed_primary_vtable = 0x33333333;
  bindings.set_speed_secondary_vtable = 0x44444444;
  bindings.select_event_option_primary_vtable = 0x55555555;
  bindings.select_event_option_secondary_vtable = 0x66666666;
  bindings.auto_save_primary_vtable = 0x77777777;
  bindings.auto_save_secondary_vtable = 0x88888888;
  bindings.reply_character_interaction_primary_vtable = 0x99999999;
  bindings.reply_character_interaction_secondary_vtable = 0xAAAAAAAA;
  bindings.raise_troops_primary_vtable = 0xBBBBBBBB;
  bindings.raise_troops_secondary_vtable = 0xCCCCCCCC;
  bindings.move_army_primary_vtable = 0xDDDDDDDD;
  bindings.move_army_secondary_vtable = 0xEEEEEEEE;
  bindings.disband_army_primary_vtable = 0xFFFFFFFF;
  bindings.disband_army_secondary_vtable = 0xABABABAB;
  bindings.split_army_half_primary_vtable = 0x15151515;
  bindings.split_army_half_secondary_vtable = 0x16161616;
  bindings.merge_armies_primary_vtable = 0x17171717;
  bindings.merge_armies_secondary_vtable = 0x18181818;
  bindings.start_assault_primary_vtable = 0x1A1A1A1A;
  bindings.start_assault_secondary_vtable = 0x1B1B1B1B;
  bindings.stop_assault_primary_vtable = 0x1C1C1C1C;
  bindings.stop_assault_secondary_vtable = 0x1D1D1D1D;
  bindings.send_character_interaction_primary_vtable = 0x13131313;
  bindings.send_character_interaction_secondary_vtable = 0x14141414;
  bindings.war_declaration_vtable = 0x12121212;
  g_character_claim_vtable[0] =
      reinterpret_cast<std::uintptr_t>(&FixtureDestroyCharacterClaim);
  bindings.character_claim_vtable =
      reinterpret_cast<std::uintptr_t>(g_character_claim_vtable.data());
  bindings.effect_preview_collector_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_effect_preview_collector_vtable.data());
  bindings.jomini_effect_vtable = reinterpret_cast<std::uintptr_t>(
      g_white_peace_loaded_effect_vtable.data());
  bindings.jomini_scripted_effect_vtable =
      reinterpret_cast<std::uintptr_t>(g_scripted_effect_vtable.data());
  bindings.jomini_scripted_effect_template_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_scripted_effect_template_vtable.data());
  bindings.hidden_effect_vtable =
      reinterpret_cast<std::uintptr_t>(g_hidden_effect_vtable.data());
  bindings.jomini_context_effect_vtable =
      reinterpret_cast<std::uintptr_t>(g_context_effect_vtable.data());
  bindings.prestige_effect_vtable = prestige_vtable;
  bindings.prestige_experience_effect_vtable =
      prestige_vtable + sizeof(void *);
  bindings.piety_effect_vtable = prestige_vtable + 2 * sizeof(void *);
  bindings.piety_experience_effect_vtable =
      prestige_vtable + 3 * sizeof(void *);
  bindings.legitimacy_effect_vtable = legitimacy_vtable;
  bindings.stress_impact_effect_vtable = stress_vtable;
  bindings.add_from_contribution_attackers_effect_vtable =
      attacker_contribution_vtable;
  bindings.add_from_contribution_defenders_effect_vtable =
      defender_contribution_vtable;
  bindings.gold_transfer_effect_vtable = gold_vtable;
  bindings.truce_effect_vtable = truce_vtable;
  bindings.hook_type_primary_vtable =
      reinterpret_cast<std::uintptr_t>(g_raiktor_hook_type_vtable.data());
  bindings.add_hook_effect_vtable = reinterpret_cast<std::uintptr_t>(
      g_raiktor_add_hook_effect_vtable.data());
  bindings.add_hook_no_toast_effect_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_raiktor_add_hook_no_toast_effect_vtable.data());
  bindings.add_hook_theocracy_approve_argument =
      reinterpret_cast<std::uintptr_t>(
          g_raiktor_theocracy_argument.data());
  bindings.cb_prestige_factor_identifier_id =
      &g_exit_terms_factor_identifier_id;
  bindings.pending_character_interaction_storage_slot =
      &g_pending_storage_pointer;
  bindings.character_storage_slot = &g_character_storage_pointer;
  bindings.hook_type_database_slot =
      &g_raiktor_hook_type_database_pointer;
  bindings.hook_type_fallback_slot =
      &g_raiktor_hook_type_fallback_pointer;
  bindings.army_storage_slot = &g_army_storage_pointer;
  bindings.army_internal_storage_slot =
      &g_internal_army_storage_pointer;
  bindings.regiment_storage_slot = &g_regiment_storage_pointer;
  bindings.combat_storage_slot = &g_combat_storage_pointer;
  bindings.ai_war_coordinator_storage_slot =
      &g_ai_coordinator_storage_pointer;
  bindings.ai_war_coordinator_fallback_slot =
      &g_ai_coordinator_fallback_pointer;
  bindings.ai_war_coordinator_vtable = ai_coordinator_vtable;
  bindings.ai_unit_stack_vtable = ai_unit_stack_vtable;
  bindings.ai_subunit_stack_vtable = ai_subunit_stack_vtable;
  bindings.battle_result_storage_slot =
      &g_contact_battle_result_storage_pointer;
  bindings.battle_result_fallback_slot =
      &g_contact_battle_result_fallback_pointer;
  bindings.siege_storage_slot = &g_siege_storage_pointer;
  bindings.contact_game_mode_slot = &g_contact_game_mode_pointer;
  bindings.global_variable_container_accessor_slot =
      &g_global_variable_container_accessor;
  bindings.valid_casus_belli_configuration_scratch =
      g_casus_belli_scratch.data();
  bindings.player_character_manager_offset = 0x100;
  bindings.war_manager_offset = 0x200;
  bindings.landed_title_manager_offset = 0x300;
  bindings.arrange_marriage_interaction_offset = 0xF48;
  bindings.declare_war_interaction_offset = 0xF78;
  bindings.submit_command = FixtureSubmit;
  bindings.hash_stable_key = FixtureHashRaiktorHookKey;
  bindings.lookup_hook_type = FixtureLookupRaiktorHookType;
  bindings.get_local_player = FixtureGetLocalPlayer;
  bindings.get_current_event = FixtureGetCurrentEvent;
  bindings.is_pending_character_interaction_for_character =
      FixtureIsPendingCharacterInteractionForCharacter;
  bindings.validate_reply_character_interaction_command =
      FixtureValidateReplyCharacterInteractionCommand;
  bindings.contains_war_participant = FixtureContainsWarParticipant;
  bindings.get_war_score = FixtureGetWarScore;
  bindings.get_imprisonment_war_score =
      FixtureGetImprisonmentWarScore;
  bindings.get_battle_war_score_base = FixtureGetBattleWarScoreBase;
  bindings.get_battle_war_score_side = FixtureGetBattleWarScoreSide;
  bindings.get_occupation_war_score_side =
      FixtureGetOccupationWarScoreSide;
  bindings.get_ticking_war_score_side = FixtureGetTickingWarScoreSide;
  bindings.is_native_component_alive = FixtureIsNativeComponentAlive;
  bindings.get_siege_progress = FixtureGetSiegeProgress;
  bindings.get_siege_total_work = FixtureGetSiegeTotalWork;
  bindings.get_siege_days_left = FixtureGetSiegeDaysLeft;
  bindings.read_assault_daily_progress =
      FixtureReadAssaultDailyProgress;
  bindings.get_assault_daily_casualties =
      FixtureGetAssaultDailyCasualties;
  bindings.validate_start_assault_command =
      FixtureValidateStartAssaultCommand;
  bindings.validate_stop_assault_command =
      FixtureValidateStopAssaultCommand;
  bindings.destroy_assault_command = FixtureDestroyAssaultCommand;
  bindings.is_province_occupied = FixtureIsProvinceOccupied;
  bindings.get_province_fort_level = FixtureGetProvinceFortLevel;
  bindings.get_province_garrison_size = FixtureGetProvinceGarrisonSize;
  bindings.get_province_besieging_strength =
      FixtureGetProvinceBesiegingStrength;
  bindings.resolve_default_raise_province =
      FixtureResolveDefaultRaiseProvince;
  bindings.get_unit_state = FixtureGetUnitState;
  bindings.get_army_current_soldiers =
      FixtureGetArmyCurrentSoldiers;
  bindings.get_army_maximum_soldiers =
      FixtureGetArmyMaximumSoldiers;
  bindings.get_army_commander = FixtureGetArmyCommander;
  bindings.get_commander_advantage = FixtureGetCommanderAdvantage;
  bindings.get_province_terrain = FixtureGetProvinceTerrain;
  bindings.evaluate_regiment_stats_at_province =
      FixtureEvaluateRegimentStatsAtProvince;
  bindings.is_special_combat_regiment = FixtureIsSpecialCombatRegiment;
  bindings.get_character_modifier_aggregator =
      FixtureGetCharacterModifierAggregator;
  bindings.read_character_modifier = FixtureReadCharacterModifier;
  bindings.get_combat_rules = FixtureGetCombatRules;
  bindings.get_combat_side_strength = FixtureGetCombatSideStrength;
  bindings.get_combat_regiment_strength =
      FixtureGetCombatRegimentStrength;
  bindings.read_counter_current_chunk = FixtureReadCounterCurrentChunk;
  bindings.resolve_counter_classes = FixtureResolveCounterClasses;
  bindings.get_counter_context_scale = FixtureGetCounterContextScale;
  bindings.get_knight_effectiveness_context =
      FixtureGetKnightEffectivenessContext;
  bindings.read_knight_effectiveness = FixtureReadKnightEffectiveness;
  bindings.is_holding_defender = FixtureIsHoldingDefender;
  bindings.commander_min_roll = &g_commander_min_roll;
  bindings.commander_max_roll = &g_commander_max_roll;
  bindings.knight_damage_per_prowess = &g_knight_damage_per_prowess;
  bindings.knight_toughness_per_prowess =
      &g_knight_toughness_per_prowess;
  bindings.minimum_combat_width = &g_minimum_combat_width;
  bindings.base_combat_width_ratio = &g_base_combat_width_ratio;
  bindings.construct_raise_troops_command =
      FixtureConstructRaiseTroopsCommand;
  bindings.validate_raise_troops_command =
      FixtureValidateRaiseTroopsCommand;
  bindings.destroy_raise_troops_command =
      FixtureDestroyRaiseTroopsCommand;
  bindings.get_army_move_mode = FixtureGetArmyMoveMode;
  bindings.can_character_use_command_kind =
      FixtureCanCharacterUseCommandKind;
  bindings.can_army_use_move_mode = FixtureCanArmyUseMoveMode;
  bindings.can_move_army = FixtureCanMoveArmy;
  bindings.can_order_combat_retreat = FixtureCanOrderCombatRetreat;
  bindings.get_combat_retreat_rule_state =
      FixtureGetCombatRetreatRuleState;
  bindings.minimum_days_before_manual_retreat =
      &g_minimum_days_before_manual_retreat;
  bindings.resolve_move_origin = FixtureResolveMoveOrigin;
  bindings.construct_move_path_context = FixtureConstructMovePathContext;
  bindings.construct_army_move_path = FixtureConstructArmyMovePath;
  bindings.build_army_move_route = FixtureBuildArmyMoveRoute;
  bindings.read_unit_land_route_speed =
      FixtureReadUnitLandRouteSpeed;
  bindings.read_unit_naval_route_speed =
      FixtureReadUnitNavalRouteSpeed;
  bindings.read_unit_current_edge_speed =
      FixtureReadUnitCurrentEdgeSpeed;
  bindings.read_route_travel_duration =
      FixtureReadRouteTravelDuration;
  bindings.read_route_edge_duration = FixtureReadRouteEdgeDuration;
  bindings.destroy_move_army_command = FixtureDestroyMoveArmyCommand;
  bindings.validate_disband_army_command =
      FixtureValidateDisbandArmyCommand;
  bindings.validate_split_army_half_command =
      FixtureValidateSplitArmyHalfCommand;
  bindings.destroy_split_army_half_command =
      FixtureDestroySplitArmyHalfCommand;
  bindings.create_merge_armies_command =
      FixtureCreateMergeArmiesCommand;
  bindings.validate_merge_armies_command =
      FixtureValidateMergeArmiesCommand;
  bindings.destroy_merge_armies_command =
      FixtureDestroyMergeArmiesCommand;
  bindings.get_casus_belli_type_database =
      FixtureGetCasusBelliTypeDatabase;
  bindings.get_character_interaction_database =
      FixtureGetCharacterInteractionDatabase;
  bindings.evaluate_casus_belli = FixtureEvaluateCasusBelli;
  bindings.destroy_valid_casus_belli_configuration =
      FixtureDestroyValidCasusBelliConfiguration;
  bindings.construct_character_interaction_context =
      FixtureConstructCharacterInteractionContext;
  bindings.redirect_character_interaction_roles =
      FixtureRedirectCharacterInteractionRoles;
  bindings.construct_character_interaction_context_all_roles =
      FixtureConstructCharacterInteractionContextAllRoles;
  bindings.copy_native_int_array = FixtureCopyNativeIntArray;
  bindings.append_native_int_array_range =
      FixtureAppendNativeIntArrayRange;
  bindings.refresh_character_interaction_context =
      FixtureRefreshCharacterInteractionContext;
  bindings.finalize_character_interaction_context =
      FixtureFinalizeCharacterInteractionContext;
  bindings.validate_character_interaction_context =
      FixtureValidateCharacterInteractionContext;
  bindings.read_character_interaction_answer_score =
      FixtureReadCharacterInteractionAnswerScore;
  bindings.evaluate_character_interaction_trigger =
      FixtureEvaluateCharacterInteractionTrigger;
  bindings.construct_send_character_interaction_command =
      FixtureConstructSendCharacterInteractionCommand;
  bindings.destroy_character_interaction_context =
      FixtureDestroyCharacterInteractionContext;
  bindings.default_construct_character_interaction_context =
      FixtureDefaultConstructCharacterInteractionContext;
  bindings.construct_war_resolution_interaction_context =
      FixtureConstructWarResolutionInteractionContext;
  bindings.construct_special_character_interaction_context =
      FixtureConstructSpecialCharacterInteractionContext;
  bindings.read_character_claim = FixtureReadCharacterClaim;
  bindings.construct_war_effect_context = FixtureConstructWarEffectContext;
  bindings.populate_war_effect_context = FixturePopulateWarEffectContext;
  bindings.construct_effect_preview_collector =
      FixtureConstructEffectPreviewCollector;
  bindings.destroy_effect_preview_collector =
      FixtureDestroyEffectPreviewCollector;
  bindings.traverse_loaded_effect = FixtureTraverseLoadedEffect;
  bindings.destroy_effect_context_118 = FixtureDestroyEffectContext118;
  bindings.destroy_effect_context_array_row =
      FixtureDestroyEffectContextArrayRow;
  bindings.evaluate_truce_duration_days =
      FixtureEvaluateTruceDurationDays;
  bindings.get_character_primary_title = FixtureGetCharacterPrimaryTitle;
  bindings.read_monthly_gold_income = FixtureReadMonthlyGoldIncome;
  bindings.evaluate_character_interaction_answer =
      FixtureEvaluateCharacterInteractionAnswer;
  bindings.get_script_identifier_table = FixtureGetScriptIdentifierTable;
  bindings.lookup_script_identifier_id = FixtureLookupScriptIdentifierId;
  bindings.is_event_target_valid = FixtureIsEventTargetValid;
  bindings.resolve_event_target_object =
      FixtureResolveEventTargetObject;
  bindings.is_character_hostile = FixtureIsCharacterHostile;
  bindings.is_army_empty_for_contact = FixtureArmyIsEmptyForContact;
  bindings.is_army_in_combat = FixtureArmyIsInCombat;
  bindings.read_province_holder_character_id =
      FixtureReadProvinceHolderCharacterId;
  bindings.classify_contact_defender_by_holder =
      FixtureClassifyContactDefenderByHolder;
  bindings.classify_contact_defender_fallback =
      FixtureClassifyContactDefenderFallback;

  if (bindings.army_storage_slot != &g_army_storage_pointer ||
      *bindings.army_storage_slot != g_army_storage.data()) {
    return Fail("army storage binding was not a single-dereference slot");
  }
  if (bindings.army_internal_storage_slot !=
          &g_internal_army_storage_pointer ||
      *bindings.army_internal_storage_slot !=
          g_internal_army_storage.data() ||
      bindings.regiment_storage_slot != &g_regiment_storage_pointer ||
      *bindings.regiment_storage_slot != g_regiment_storage.data()) {
    return Fail("army-strength storage bindings were not exact slots");
  }

  xar::ck3_11906::Snapshot snapshot{};
  snapshot.has_active_event = true;
  snapshot.active_event_instance_id = 999;
  snapshot.active_event_option_count = 999;
  snapshot.has_pending_character_interaction = true;
  snapshot.pending_character_interaction_id = 999;
  snapshot.pending_sender_character_id = 999;
  snapshot.pending_auto_accept_notification = true;
  snapshot.active_wars.push_back({});
  snapshot.player_armies.push_back({});
  snapshot.has_one_life_settlement = true;
  snapshot.one_life_settlement.commit_serial = 999;
  g_current_event_calls = 0;
  g_war_participant_calls = 0;
  g_settlement_accessor_calls = 0;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("fixture snapshot was unavailable");
  }
  if (snapshot.date_raw != 43'823'104 || snapshot.speed != 4 ||
      snapshot.paused || snapshot.player_id != 41 ||
      snapshot.map_ready ||
      snapshot.has_played_character || snapshot.played_character_id != -1 ||
      snapshot.played_character_alive ||
      snapshot.played_character_betrothed_id != -1 ||
      snapshot.played_character_primary_spouse_id != -1 ||
      !snapshot.played_character_spouse_ids.empty() ||
      snapshot.has_active_event || snapshot.active_event_instance_id != -1 ||
      snapshot.active_event_option_count != 0 ||
      snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != -1 ||
      snapshot.pending_sender_character_id != -1 ||
      snapshot.pending_auto_accept_notification ||
      !snapshot.active_wars.empty() || !snapshot.player_armies.empty() ||
      snapshot.has_one_life_settlement ||
      snapshot.one_life_settlement.commit_serial != 0 ||
      g_current_event_calls != 0 || g_war_participant_calls != 0 ||
      g_settlement_accessor_calls != 0) {
    return Fail("fixture snapshot fields did not match the pinned offsets");
  }
  g_has_local_player = true;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.map_ready || !snapshot.has_played_character ||
      snapshot.played_character_id != played_character_id ||
      !snapshot.played_character_alive ||
      snapshot.played_character_betrothed_id != enemy_character_id ||
      snapshot.played_character_primary_spouse_id != enemy_character_id ||
      snapshot.played_character_spouse_ids !=
          std::vector<std::int32_t>{enemy_character_id} ||
      snapshot.player_armies.size() != 1 ||
      snapshot.player_armies[0].army_id != player_army_id ||
      snapshot.player_armies[0].owner_character_id != played_character_id ||
      !snapshot.player_armies[0].has_current_province ||
      snapshot.player_armies[0].current_province_id != 2 ||
      !snapshot.player_armies[0].route_province_ids.empty() ||
      !snapshot.player_armies[0].move_target_observable ||
      snapshot.player_armies[0].move_target_province_id != 3 ||
      snapshot.player_armies[0].army_state_code != 2 ||
      snapshot.player_armies[0].army_state != "combat" ||
      !snapshot.player_armies[0].in_combat ||
      snapshot.player_armies[0].retreating ||
      !snapshot.player_armies[0].controllable ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_id != active_war_id ||
      snapshot.active_wars[0].player_side !=
          xar::ck3_11906::PlayerWarSide::attacker ||
      snapshot.active_wars[0].primary_opponent_character_id !=
          enemy_character_id ||
      !snapshot.active_wars[0].player_is_primary_war_leader ||
      snapshot.active_wars[0].targeted_title_ids !=
          std::vector<std::int32_t>{
              targeted_title_id, targeted_duchy_a_title_id,
              second_county_title_id, third_capital_barony_title_id} ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{war_objective_province_id,
                                    second_war_objective_province_id,
                                    third_war_objective_province_id} ||
      snapshot.active_wars[0].enemy_primary_default_raise_province_id != 4 ||
      snapshot.active_wars[0].player_relative_war_score != 37 ||
      snapshot.active_wars[0].allied_armies.size() != 1 ||
      !snapshot.active_wars[0].allied_armies[0].route_province_ids.empty() ||
      snapshot.active_wars[0].enemy_armies.size() != 1 ||
      snapshot.active_wars[0].enemy_armies[0].army_id != enemy_army_id ||
      snapshot.active_wars[0].enemy_armies[0].current_province_id != 3 ||
      !snapshot.active_wars[0].enemy_armies[0].route_province_ids.empty() ||
      snapshot.active_wars[0].enemy_armies[0].move_target_observable ||
      snapshot.active_wars[0].enemy_armies[0].move_target_province_id != -1 ||
      snapshot.active_wars[0].enemy_armies[0].army_state_code != 6 ||
      snapshot.active_wars[0].enemy_armies[0].army_state != "retreating" ||
      snapshot.active_wars[0].enemy_armies[0].in_combat ||
      !snapshot.active_wars[0].enemy_armies[0].retreating) {
    return Fail("map-ready did not follow the resolved local player");
  }
  if (snapshot.active_wars[0].objective_province_states.size() != 3) {
    return Fail("exact war objectives omitted Province state rows");
  }
  Store(g_player_army, 0x18, std::int32_t{1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.player_armies.empty() || snapshot.active_wars.size() != 1 ||
      !snapshot.active_wars[0].allied_armies.empty() ||
      snapshot.active_wars[0].enemy_armies.size() != 1) {
    return Fail("CFleet carrier CUnit leaked into tactical army snapshots");
  }
  Store(g_player_army, 0x18, std::int32_t{0});
  Store(g_player_internal_army, 0x124, third_army_id);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.player_armies.empty() || snapshot.active_wars.size() != 1 ||
      !snapshot.active_wars[0].allied_armies.empty() ||
      snapshot.active_wars[0].enemy_armies.size() != 1) {
    return Fail("non-canonical CUnit-to-CArmy backlink was published");
  }
  Store(g_player_internal_army, 0x124, player_army_id);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.player_armies.size() != 1 ||
      snapshot.player_armies[0].army_id != player_army_id) {
    return Fail("canonical tactical army did not recover after fixture restore");
  }
  const auto &running_objective_state =
      snapshot.active_wars[0].objective_province_states[0];
  if (!running_objective_state.occupation_observable ||
      !running_objective_state.fort_level_observable ||
      running_objective_state.garrison_size_observable ||
      running_objective_state.besieging_strength_observable ||
      running_objective_state.siege_observable ||
      running_objective_state.assault_observable) {
    return Fail("running snapshot traversed a mutable siege subgraph");
  }

  std::vector<xar::ck3_11906::ArmyStrengthSnapshot> army_strengths;
  const xar::game::CombatSimulationInputsRequest combat_request{
      second_war_objective_province_id,
      2,
      {player_army_id},
      {enemy_army_id},
  };
  xar::ck3_11906::CombatSimulationInputsSnapshot combat_inputs{};
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::requires_paused ||
      !army_strengths.empty()) {
    return Fail("running map exposed mutable army-strength data");
  }
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::requires_paused ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("running map exposed mutable combat simulation inputs");
  }

  Store(jomini_state, 0x20, std::uint8_t{1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].objective_province_states.size() != 3) {
    return Fail("paused objective Province state was unavailable");
  }
  g_army_current_soldiers_calls = 0;
  g_army_maximum_soldiers_calls = 0;
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::available ||
      army_strengths.size() != 2 ||
      !army_strengths[0].available ||
      army_strengths[0].army_id != player_army_id ||
      !army_strengths[0].native_carmy_id_observable ||
      army_strengths[0].native_carmy_id != player_internal_army_id ||
      army_strengths[0].scope_role !=
          xar::ck3_11906::ArmyStrengthScopeRole::player ||
      army_strengths[0].war_ids !=
          std::vector<std::int32_t>{active_war_id} ||
      army_strengths[0].regiment_count != 2 ||
      army_strengths[0].current_soldiers != 1000 ||
      army_strengths[0].maximum_soldiers != 1200 ||
      army_strengths[0].ai_base_power_raw != 150'000'000 ||
      army_strengths[0].ai_base_power_scale !=
          kFixtureFixedPointScale ||
      !army_strengths[0].unavailable_reason.empty() ||
      !army_strengths[1].available ||
      army_strengths[1].army_id != enemy_army_id ||
      army_strengths[1].native_carmy_id != enemy_internal_army_id ||
      army_strengths[1].scope_role !=
          xar::ck3_11906::ArmyStrengthScopeRole::active_war_enemy ||
      army_strengths[1].war_ids !=
          std::vector<std::int32_t>{active_war_id} ||
      army_strengths[1].regiment_count != 2 ||
      army_strengths[1].current_soldiers != 800 ||
      army_strengths[1].maximum_soldiers != 1500 ||
      army_strengths[1].ai_base_power_raw != 240'000'000 ||
      g_army_current_soldiers_calls != 2 ||
      g_army_maximum_soldiers_calls != 2) {
    return Fail("paused army-strength aggregate drifted from exact ABI");
  }

  // Freeze the production actual-contact mirror against the exact stored
  // ordering semantics.  These are read-only predictions: no join/create
  // helper is present in Bindings and no fixture object is mutated by the
  // reader itself.
  g_contact_province_unit_ids = {player_army_id, enemy_army_id,
                                 third_army_id};
  g_contact_province_combat_ids = {contact_combat_0_id,
                                   contact_combat_1_id};
  Store(g_war_objective_province, 0x08,
        static_cast<void *>(g_player_map_node.data()));
  g_contact_province_vtable[6] =
      reinterpret_cast<std::uintptr_t>(&FixtureContactProvinceValid);
  Store(g_war_objective_province, 0x00,
        static_cast<void *>(g_contact_province_vtable.data()));
  Store(g_second_war_objective_province, 0x00,
        static_cast<void *>(g_contact_province_vtable.data()));
  Store(g_war_objective_province, 0x20,
        static_cast<void *>(g_contact_province_gate.data()));
  Store(g_war_objective_province, 0x748,
        static_cast<void *>(g_contact_province_unit_ids.data()));
  Store(g_war_objective_province, 0x750, std::int32_t{3});
  Store(g_war_objective_province, 0x754, std::int32_t{3});
  Store(g_war_objective_province, 0x760,
        static_cast<void *>(g_contact_province_combat_ids.data()));
  Store(g_war_objective_province, 0x768, std::int32_t{2});
  Store(g_war_objective_province, 0x76C, std::int32_t{1});
  Store(g_war_objective_province, 0x858, std::int32_t{0});
  Store(g_player_army, 0x20,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_third_army, 0x20,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_third_army, 0x174, enemy_character_id);
  Store(g_army_slots, 0x38, static_cast<void *>(g_third_army.data()));
  Store(g_enemy_army, 0x170, std::int32_t{0});
  Store(g_player_internal_army, 0x128, std::int32_t{-1});
  g_contact_combat_0_defender_armies = {enemy_internal_army_id};
  Store(g_contact_combat_0, 0x6E0, std::int32_t{0});
  Store(g_contact_combat_0, 0x704, std::uint8_t{1});
  Store(g_contact_combat_0, 0x708, contact_battle_result_id);
  g_player_army_state_code = 1;
  g_enemy_army_state_code = 1;
  bindings.combat_storage_slot = &g_contact_combat_storage_pointer;

  const xar::game::ActualContactScopeRequest actual_contact_request{
      player_army_id, war_objective_province_id};
  xar::game::ActualContactScopeSnapshot actual_contact{};
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.status !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.date_raw != 43'823'104 ||
      actual_contact.subject_army_id != player_army_id ||
      actual_contact.subject_native_carmy_id != player_internal_army_id ||
      actual_contact.subject_owner_character_id != played_character_id ||
      actual_contact.target_province_id != war_objective_province_id ||
      actual_contact.province_unit_army_ids !=
          std::vector<std::int32_t>{player_army_id, enemy_army_id,
                                    third_army_id} ||
      actual_contact.province_combat_ids !=
          std::vector<std::int32_t>{contact_combat_0_id} ||
      actual_contact.transition_kind != "create_new" ||
      actual_contact.selected_combat_id != -1 ||
      actual_contact.selected_combat_array_index != -1 ||
      actual_contact.join_side != "none" ||
      actual_contact.defender_seed_character_id != enemy_character_id ||
      actual_contact.initiator_is_defender ||
      actual_contact.adjacency_kind_raw != 2 ||
      actual_contact.loser_excluded_native_carmy_ids !=
          std::vector<std::int32_t>{enemy_internal_army_id} ||
      actual_contact.opponent_army_ids !=
          std::vector<std::int32_t>{enemy_army_id, third_army_id} ||
      actual_contact.attacker_army_ids !=
          std::vector<std::int32_t>{player_army_id} ||
      actual_contact.defender_army_ids !=
          std::vector<std::int32_t>{enemy_army_id, third_army_id} ||
      !actual_contact.actual_contact_scope_ready ||
      !actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact create mirror lost Province order or side polarity");
  }

  // A gathering army can pass the native empty-army gate while every valid
  // regiment currently has zero soldiers.  Native finds a hostile seed, then
  // stops before construction; the public no-transition shape must not retain
  // that intermediate seed or claim a combat-v3 participant scope.
  Store(g_player_internal_army, 0x5C, std::int32_t{1});
  Store(g_player_regiment_0, 0x38, std::int32_t{0});
  Store(g_player_regiment_1, 0x38, std::int32_t{0});
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.transition_kind != "none" ||
      actual_contact.defender_seed_character_id != -1 ||
      !actual_contact.opponent_army_ids.empty() ||
      !actual_contact.attacker_army_ids.empty() ||
      !actual_contact.defender_army_ids.empty() ||
      !actual_contact.actual_contact_scope_ready ||
      actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact zero-strength stop leaked an intermediate seed");
  }
  Store(g_player_regiment_0, 0x38, std::int32_t{600});
  Store(g_player_regiment_1, 0x38, std::int32_t{400});
  Store(g_player_internal_army, 0x5C, std::int32_t{0});

  g_contact_prior_province_valid = false;
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.transition_kind != "create_new" ||
      actual_contact.adjacency_kind_raw != 0 ||
      !actual_contact.actual_contact_scope_ready ||
      !actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact adjacency used an identity-invalid Province edge");
  }
  g_contact_prior_province_valid = true;

  Store(g_third_army, 0x174, played_character_id);
  g_contact_combat_0_defender_armies = {third_internal_army_id};
  Store(g_contact_combat_0, 0x6E0, std::int32_t{-1});
  Store(g_contact_combat_0, 0x704, std::uint8_t{0});
  Store(g_contact_combat_0, 0x708, std::int32_t{-1});
  Store(g_war_objective_province, 0x76C, std::int32_t{2});
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.status !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.province_unit_army_ids !=
          std::vector<std::int32_t>{player_army_id, enemy_army_id,
                                    third_army_id} ||
      actual_contact.province_combat_ids !=
          std::vector<std::int32_t>{contact_combat_0_id,
                                    contact_combat_1_id} ||
      actual_contact.transition_kind != "join_existing" ||
      actual_contact.selected_combat_id != contact_combat_1_id ||
      actual_contact.selected_combat_array_index != 1 ||
      actual_contact.join_side != "attacker" ||
      actual_contact.attacker_army_ids !=
          std::vector<std::int32_t>{third_army_id, player_army_id} ||
      actual_contact.defender_army_ids !=
          std::vector<std::int32_t>{enemy_army_id} ||
      !actual_contact.opponent_army_ids.empty() ||
      !actual_contact.actual_contact_scope_ready ||
      !actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact join mirror did not select the last compatible combat");
  }

  // The read-only reinforcement capability follows the exact AI coordinator
  // graph and only calls the two frozen route-duration leaves. Stored order
  // and route duplicates are semantic; no future CombatID is synthesized.
  Store(g_player_map_node, 0xB0,
        static_cast<void *>(g_route_origin_info_2.data()));
  Store(g_route_origin_info_2, 0x09, std::uint8_t{1});
  Store(g_route_origin_info_2, 0x0B, std::uint8_t{0});
  Store(g_player_move_route_info_0, 0x00,
        second_war_objective_province_id);
  Store(g_player_move_route_info_0, 0x09, std::uint8_t{1});
  Store(g_player_move_route_info_0, 0x0B, std::uint8_t{0});
  Store(g_player_army, 0x40, std::int32_t{1});
  Store(g_player_army, 0x44, std::int32_t{1});
  Store(g_player_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_second_war_objective_province, 0x760,
        static_cast<void *>(g_contact_province_combat_ids.data()));
  Store(g_second_war_objective_province, 0x768, std::int32_t{2});
  Store(g_second_war_objective_province, 0x76C, std::int32_t{2});
  Store(g_contact_combat_0, 0x6B8,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_contact_combat_1, 0x6B8,
        static_cast<void *>(g_second_war_objective_province.data()));
  xar::game::Snapshot reinforcement_world{};
  reinforcement_world.paused = true;
  reinforcement_world.date_raw = 43'823'104;
  const xar::game::BattleReinforcementAssignmentRequest
      reinforcement_request{player_army_id};
  xar::game::BattleReinforcementAssignmentSnapshot reinforcement{};
  g_route_edge_duration_calls = 0;
  if (xar::ck3_11906::ReadBattleReinforcementAssignmentV1(
          bindings, reinforcement_world, reinforcement_request,
          reinforcement) !=
          xar::game::BattleReinforcementAssignmentStatus::available ||
      !reinforcement.battle_reinforcement_assignment_ready ||
      !reinforcement.unavailable_reason.empty() ||
      reinforcement.selected_public_cunit_id != player_army_id ||
      reinforcement.selected_native_carmy_id != player_internal_army_id ||
      reinforcement.coordinator_id != ai_coordinator_id ||
      reinforcement.unit_stack_stored_index != 0 ||
      reinforcement.subunit_stored_index != 0 ||
      !reinforcement.signal.has_value() ||
      reinforcement.signal->asking_for_help ||
      !reinforcement.signal->assigned_to_help ||
      !reinforcement.signal->asking_changed_last_evaluation ||
      reinforcement.signal->request_power_basis_raw.has_value() ||
      reinforcement.signal->cross_coordinator_request_valid_raw != 1 ||
      reinforcement.signal->cross_coordinator_request_power_raw !=
          std::optional<std::int64_t>{2'300'000} ||
      reinforcement.signal->first_route_edge_remaining_duration_q100000 !=
          std::optional<std::int64_t>{150'000} ||
      !reinforcement.assignment.has_value() ||
      reinforcement.assignment->assignment_target_province_id !=
          second_war_objective_province_id ||
      reinforcement.assignment->target_provenance !=
          "native_help_override" ||
      reinforcement.assignment->combat_binding_status !=
          "unbound_until_contact" ||
      reinforcement.assignment->active_combat_id.has_value() ||
      !reinforcement.route.has_value() ||
      reinforcement.route->route_province_ids !=
          std::vector<std::int32_t>{second_war_objective_province_id} ||
      reinforcement.route->route_alignment != "aligned_to_assignment" ||
      reinforcement.route->arrival_date_raws !=
          std::optional<std::vector<std::int32_t>>{{43'823'128}} ||
      reinforcement.route->assignment_eta_date_raw !=
          std::optional<std::int32_t>{43'823'128} ||
      !reinforcement.native_order.has_value() ||
      reinforcement.native_order
              ->support_search_province_ids_in_stored_order !=
          std::vector<std::int32_t>{
              second_war_objective_province_id,
              second_war_objective_province_id,
              third_war_objective_province_id} ||
      reinforcement.native_order->parent_subunits_in_stored_order.size() != 2 ||
      reinforcement.native_order->parent_subunits_in_stored_order[0]
              .public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{player_army_id} ||
      reinforcement.native_order->parent_subunits_in_stored_order[1]
              .public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{enemy_army_id} ||
      !reinforcement.contact_projection.has_value() ||
      reinforcement.contact_projection->status != "available" ||
      reinforcement.contact_projection
              ->current_target_compatible_combat_ids_in_stored_order !=
          std::vector<std::int32_t>{
              contact_combat_0_id, contact_combat_1_id} ||
      reinforcement.contact_projection->contact_if_now_selected_combat_id !=
          contact_combat_1_id ||
      g_route_edge_duration_calls != 2) {
    return Fail(
        "battle-reinforcement lost AI assignment, route, or contact order");
  }

  Store(g_player_army, 0x30,
        static_cast<void *>(g_third_war_objective_province.data()));
  if (xar::ck3_11906::ReadBattleReinforcementAssignmentV1(
          bindings, reinforcement_world, reinforcement_request,
          reinforcement) !=
          xar::game::BattleReinforcementAssignmentStatus::available ||
      reinforcement.route->route_alignment != "not_aligned" ||
      reinforcement.route->assignment_eta_date_raw.has_value()) {
    return Fail("battle-reinforcement fabricated ETA for a mismatched route");
  }
  Store(g_player_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));

  Store(g_ai_selected_subunit, 0x48, static_cast<void *>(nullptr));
  if (xar::ck3_11906::ReadBattleReinforcementAssignmentV1(
          bindings, reinforcement_world, reinforcement_request,
          reinforcement) !=
          xar::game::BattleReinforcementAssignmentStatus::unavailable ||
      reinforcement.unavailable_reason != "parent_membership_mismatch" ||
      reinforcement.battle_reinforcement_assignment_ready ||
      reinforcement.signal.has_value() || reinforcement.route.has_value()) {
    return Fail("battle-reinforcement accepted assigned flag without target");
  }
  Store(g_ai_selected_subunit, 0x48,
        static_cast<void *>(g_second_war_objective_province.data()));

  g_route_edge_duration_calls = 0;
  g_route_edge_duration_drift = true;
  if (xar::ck3_11906::ReadBattleReinforcementAssignmentV1(
          bindings, reinforcement_world, reinforcement_request,
          reinforcement) !=
          xar::game::BattleReinforcementAssignmentStatus::unavailable ||
      reinforcement.unavailable_reason != "state_changed" ||
      reinforcement.battle_reinforcement_assignment_ready) {
    return Fail("battle-reinforcement accepted route input drift");
  }
  g_route_edge_duration_drift = false;
  g_route_edge_duration_calls = 0;

  Store(g_contact_combat_0, 0x6B8,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_contact_combat_1, 0x6B8,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_second_war_objective_province, 0x760,
        static_cast<void *>(nullptr));
  Store(g_second_war_objective_province, 0x768, std::int32_t{0});
  Store(g_second_war_objective_province, 0x76C, std::int32_t{0});
  Store(g_player_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_player_army, 0x40, std::int32_t{3});
  Store(g_player_army, 0x44, std::int32_t{3});

  // Materialize the predicted join exactly as the native mutator would: the
  // incoming CArmy is tail-appended to attacker, every participant links the
  // same positive CombatID, and the Combat remains in the Province's sorted
  // table. The same query must now publish actual—not predicted—side order.
  g_contact_combat_1_attacker_armies = {
      third_internal_army_id, player_internal_army_id};
  Store(g_contact_combat_1, 0x20 + 0x18, std::int32_t{2});
  Store(g_contact_combat_1, 0x20 + 0x1C, std::int32_t{2});
  Store(g_player_internal_army, 0x128, contact_combat_1_id);
  Store(g_enemy_internal_army, 0x128, contact_combat_1_id);
  Store(g_third_internal_army, 0x128, contact_combat_1_id);
  g_player_army_state_code = 2;
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::available ||
      actual_contact.scope_kind != "post_contact_observation" ||
      actual_contact.transition_kind != "in_combat" ||
      actual_contact.target_province_id != war_objective_province_id ||
      actual_contact.selected_combat_id != contact_combat_1_id ||
      actual_contact.selected_combat_array_index != 1 ||
      actual_contact.join_side != "none" ||
      actual_contact.attacker_army_ids !=
          std::vector<std::int32_t>{third_army_id, player_army_id} ||
      actual_contact.defender_army_ids !=
          std::vector<std::int32_t>{enemy_army_id} ||
      !actual_contact.actual_contact_scope_ready ||
      !actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact post-contact observation lost CombatID or side order");
  }

  // Materialize a complete paused live-battle graph on the same exact
  // CCombat identity spine.  Each retained-entry bucket has one row so the
  // fixture freezes native order, conditional per-entry hard casualties,
  // participant-owner history, and both read-only strength leaves.
  const auto initialize_battle_entry =
      [](auto &entry, std::int32_t regiment_id,
         std::int64_t starting_raw, std::int64_t current_raw,
         std::int64_t soft_raw, std::int32_t maximum,
         std::int64_t siege_raw, std::int64_t damage_raw,
         std::int64_t toughness_raw, std::int64_t pursuit_raw,
         std::int64_t screen_raw) {
        entry.fill(std::byte{0});
        Store(entry, 0x08, regiment_id);
        Store(entry, 0x10, starting_raw);
        Store(entry, 0x18, current_raw);
        Store(entry, 0x20, soft_raw);
        Store(entry, 0x30, maximum);
        Store(entry, 0x38, siege_raw);
        Store(entry, 0x40, damage_raw);
        Store(entry, 0x48, toughness_raw);
        Store(entry, 0x50, pursuit_raw);
        Store(entry, 0x58, screen_raw);
      };
  initialize_battle_entry(
      g_battle_attacker_levy_entry, player_regiment_0_id,
      60'000'000, 50'000'000, 4'000'000, 600, 100'000,
      60'000'000, 12'000'000, 300'000, 500'000);
  initialize_battle_entry(
      g_battle_attacker_maa_entry, player_regiment_1_id,
      40'000'000, 0, 5'000'000, 400, 200'000, 600'000,
      700'000, 100'000, 200'000);
  initialize_battle_entry(
      g_battle_defender_levy_entry, enemy_regiment_0_id,
      50'000'000, 40'000'000, 3'000'000, 500, 300'000,
      48'000'000, 9'600'000, 400'000, 600'000);
  initialize_battle_entry(
      g_battle_defender_maa_entry, enemy_regiment_1_id,
      30'000'000, 0, 2'000'000, 300, 400'000, 900'000,
      1'000'000, 200'000, 300'000);
  g_battle_attacker_hard_row.fill(std::byte{0});
  Store(g_battle_attacker_hard_row, 0x08, played_character_id);
  Store(g_battle_attacker_hard_row, 0x10, std::int64_t{7'000'000});
  g_battle_defender_hard_row.fill(std::byte{0});
  Store(g_battle_defender_hard_row, 0x08, enemy_character_id);
  Store(g_battle_defender_hard_row, 0x10, std::int64_t{9'000'000});

  g_contact_combat_1_attacker_armies = {player_internal_army_id, 0};
  g_contact_combat_1_defender_armies = {enemy_internal_army_id};
  const auto initialize_battle_side =
      [&](std::size_t side_offset, void *army_ids,
          std::int32_t army_capacity, std::int32_t primary_character_id,
          std::int32_t selected_commander_id, void *levy_entry,
          void *maa_entry, void *hard_row,
          std::int64_t stored_current_raw,
          std::int64_t stored_levy_current_raw) {
        Store(g_contact_combat_1, side_offset + 0x10, army_ids);
        Store(g_contact_combat_1, side_offset + 0x18, army_capacity);
        Store(g_contact_combat_1, side_offset + 0x1C,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x28, levy_entry);
        Store(g_contact_combat_1, side_offset + 0x30,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x34,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x40, maa_entry);
        Store(g_contact_combat_1, side_offset + 0x48,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x4C,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x58, hard_row);
        Store(g_contact_combat_1, side_offset + 0x60,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x64,
              std::int32_t{1});
        Store(g_contact_combat_1, side_offset + 0x70,
              primary_character_id);
        Store(g_contact_combat_1, side_offset + 0x74,
              selected_commander_id);
        Store(g_contact_combat_1, side_offset + 0x98,
              stored_current_raw);
        Store(g_contact_combat_1, side_offset + 0xA0,
              stored_levy_current_raw);
        Store(g_contact_combat_1, side_offset + 0xB8,
              static_cast<void *>(g_contact_combat_1.data()));
        Store(g_contact_combat_1, side_offset + 0xC0,
              std::uint8_t{0});
        Store(g_contact_combat_1, side_offset + 0xC1,
              std::uint8_t{0});
        Store(g_contact_combat_1, side_offset + 0xC2,
              std::uint8_t{0});
      };
  initialize_battle_side(
      0x20, g_contact_combat_1_attacker_armies.data(), 2,
      played_character_id, played_character_id,
      g_battle_attacker_levy_entry.data(),
      g_battle_attacker_maa_entry.data(),
      g_battle_attacker_hard_row.data(), 50'000'000, 50'000'000);
  initialize_battle_side(
      0x368, g_contact_combat_1_defender_armies.data(), 1,
      enemy_character_id, -1, g_battle_defender_levy_entry.data(),
      g_battle_defender_maa_entry.data(),
      g_battle_defender_hard_row.data(), 40'000'000, 40'000'000);
  Store(g_contact_combat_1, 0x6B0, std::int32_t{1});
  Store(g_contact_combat_1, 0x6B4, std::int32_t{4});
  Store(g_contact_combat_1, 0x6B8,
        static_cast<void *>(g_war_objective_province.data()));
  Store(g_contact_combat_1, 0x6C0, std::int32_t{1'200});
  Store(g_contact_combat_1, 0x6C4, std::int32_t{960});
  Store(g_contact_combat_1, 0x6C8, std::int64_t{5'000'000'000});
  Store(g_contact_combat_1, 0x6D0, std::int32_t{7});
  Store(g_contact_combat_1, 0x6D4, std::int32_t{3});
  Store(g_contact_combat_1, 0x6E0, std::int32_t{0});
  Store(g_contact_combat_1, 0x6E4, std::int32_t{2});
  Store(g_contact_combat_1, 0x700, std::int32_t{-1});
  Store(g_contact_combat_1, 0x704, std::uint8_t{1});
  Store(g_contact_combat_1, 0x705, std::uint8_t{0});
  Store(g_contact_combat_1, 0x708, contact_battle_result_id);
  Store(g_contact_combat_1, 0x710, std::int64_t{-6'000'000'000});
  Store(g_player_internal_army, 0x128, contact_combat_1_id);
  Store(g_enemy_internal_army, 0x128, contact_combat_1_id);
  Store(g_played_character, 0x1B8, static_cast<void *>(nullptr));
  g_battle_side_strength_calls = 0;
  g_battle_regiment_strength_calls = 0;
  g_can_order_combat_retreat_calls = 0;
  g_can_order_combat_retreat_arguments_valid = true;
  g_can_order_combat_retreat_result = true;

  const xar::game::BattleControlRequest battle_request{player_army_id};
  xar::game::BattleControlSnapshot battle{};
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.status !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.observed_date_raw != 43'823'104 ||
      battle.subject_public_cunit_id != player_army_id ||
      battle.subject_native_carmy_id != player_internal_army_id ||
      battle.combat_id != contact_combat_1_id ||
      battle.province_id != war_objective_province_id ||
      battle.selected_public_cunit_id != player_army_id ||
      battle.selected_native_carmy_id != player_internal_army_id ||
      battle.selected_owner_character_id != played_character_id ||
      battle.combat_province_id != war_objective_province_id ||
      battle.side_index != 0 || battle.side_scope != "full_side" ||
      battle.affected_public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{player_army_id} ||
      !battle.unaffected_same_side_public_cunit_ids_in_stored_order.empty() ||
      battle.side_flags.disallow_retreat ||
      battle.side_flags.allow_early_retreat ||
      battle.side_flags.skip_pursuit ||
      battle.legality.status != "available" ||
      !battle.legality.native_boolean ||
      battle.legality.phase_raw != 1 || battle.legality.phase != "main" ||
      battle.legality.retreat_elapsed_baseline_date_raw != 43'822'744 ||
      battle.legality.elapsed_whole_days != 15 ||
      battle.legality.minimum_elapsed_whole_days_exclusive != 14 ||
      !battle.legality.landless_gate_allows_retreat ||
      !battle.legality.legal_now ||
      !battle.legality.reason_codes_in_native_order.empty() ||
      !battle.legality.native_reason_keys_in_native_order.empty() ||
      battle.legality.earliest_day_gate_date_raw !=
          std::optional<std::int64_t>{43'823'088} ||
      battle.phase != "main" || battle.phase_raw != 1 ||
      battle.phase_day != 4 || battle.winner_side != "attacker" ||
      battle.winner_raw != 0 || battle.forced_winner_side != "none" ||
      battle.forced_winner_raw != -1 || !battle.finalized ||
      battle.battle_result_id != contact_battle_result_id ||
      battle.base_combat_width != 1'200 ||
      battle.final_combat_width != 960 ||
      battle.roll_cadence_counter != 2 ||
      battle.base_advantage_raw != 5'000'000'000 ||
      battle.resolved_advantage_raw != -6'000'000'000 ||
      !battle.battle_control_ready ||
      g_battle_side_strength_calls != 4 ||
      g_battle_regiment_strength_calls != 8 ||
      g_can_order_combat_retreat_calls != 2 ||
      !g_can_order_combat_retreat_arguments_valid) {
    return Fail("battle-control paused frame lost exact CCombat fields");
  }
  if (battle.attacker.side_index != 0 ||
      battle.attacker.role != "attacker" ||
      battle.attacker.primary_participant_character_id !=
          played_character_id ||
      battle.attacker.selected_commander_character_id !=
          played_character_id ||
      battle.attacker.current_roll_points != 7 ||
      battle.attacker.ordered_armies !=
          std::vector<xar::game::BattleControlArmyIdentitySnapshot>{
              {player_internal_army_id, player_army_id,
               played_character_id, contact_combat_1_id}} ||
      battle.attacker.levy_entries.size() != 1 ||
      battle.attacker.men_at_arms_entries.size() != 1 ||
      battle.attacker.stored_current_fighting_raw != 50'000'000 ||
      battle.attacker.stored_levy_current_fighting_raw != 50'000'000 ||
      !battle.attacker.stored_current_matches_derived ||
      !battle.attacker.stored_levy_current_matches_derived ||
      battle.attacker.derived_current_fighting_raw != 50'000'000 ||
      battle.attacker.derived_soft_casualties_raw != 9'000'000 ||
      battle.attacker.derived_main_fighting_entry_hard_casualties_raw !=
          6'000'000 ||
      battle.attacker.non_main_start_minus_current_minus_soft_raw !=
          35'000'000 ||
      battle.attacker.participant_hard_ledger !=
          std::vector<xar::game::BattleControlParticipantHardSnapshot>{
              {0, played_character_id, 7'000'000}} ||
      battle.attacker.participant_hard_total_raw != 7'000'000 ||
      battle.attacker.side_strength_raw != 123'456 ||
      battle.attacker.side_strength_scale != 100'000) {
    return Fail("battle-control attacker side lost native order or totals");
  }
  const auto &attacker_main = battle.attacker.levy_entries[0];
  const auto &attacker_reserve = battle.attacker.men_at_arms_entries[0];
  if (attacker_main.bucket != "levy" || attacker_main.bucket_index != 0 ||
      attacker_main.regiment_id != player_regiment_0_id ||
      attacker_main.native_carmy_id != player_internal_army_id ||
      attacker_main.public_cunit_id != player_army_id ||
      attacker_main.owner_character_id != played_character_id ||
      attacker_main.starting_raw != 60'000'000 ||
      attacker_main.current_fighting_raw != 50'000'000 ||
      attacker_main.soft_casualties_raw != 4'000'000 ||
      !attacker_main.fights_in_main_phase ||
      !attacker_main.hard_casualties_available ||
      attacker_main.hard_casualties_raw != 6'000'000 ||
      attacker_main.effective_max_size != 600 ||
      attacker_main.effective_siege_raw != 100'000 ||
      attacker_main.effective_damage_raw != 60'000'000 ||
      attacker_main.effective_toughness_raw != 12'000'000 ||
      attacker_main.effective_pursuit_raw != 300'000 ||
      attacker_main.effective_screen_raw != 500'000 ||
      attacker_main.entry_strength_raw != 11'111 ||
      attacker_reserve.bucket != "men_at_arms" ||
      attacker_reserve.bucket_index != 0 ||
      attacker_reserve.regiment_id != player_regiment_1_id ||
      attacker_reserve.fights_in_main_phase ||
      attacker_reserve.hard_casualties_available ||
      attacker_reserve.hard_casualties_raw != 0 ||
      attacker_reserve.entry_strength_raw != 22'222) {
    return Fail(
        "battle-control fabricated per-entry hard casualties for reserve");
  }
  if (battle.defender.side_index != 1 ||
      battle.defender.role != "defender" ||
      battle.defender.primary_participant_character_id !=
          enemy_character_id ||
      battle.defender.selected_commander_character_id != -1 ||
      battle.defender.current_roll_points != 3 ||
      battle.defender.ordered_armies !=
          std::vector<xar::game::BattleControlArmyIdentitySnapshot>{
              {enemy_internal_army_id, enemy_army_id,
               enemy_character_id, contact_combat_1_id}} ||
      battle.defender.levy_entries.size() != 1 ||
      battle.defender.men_at_arms_entries.size() != 1 ||
      !battle.defender.levy_entries[0].hard_casualties_available ||
      battle.defender.levy_entries[0].hard_casualties_raw != 7'000'000 ||
      battle.defender.men_at_arms_entries[0].hard_casualties_available ||
      !battle.defender.stored_current_matches_derived ||
      !battle.defender.stored_levy_current_matches_derived ||
      battle.defender.derived_current_fighting_raw != 40'000'000 ||
      battle.defender.derived_soft_casualties_raw != 5'000'000 ||
      battle.defender.derived_main_fighting_entry_hard_casualties_raw !=
          7'000'000 ||
      battle.defender.non_main_start_minus_current_minus_soft_raw !=
          28'000'000 ||
      battle.defender.participant_hard_ledger !=
          std::vector<xar::game::BattleControlParticipantHardSnapshot>{
              {0, enemy_character_id, 9'000'000}} ||
      battle.defender.participant_hard_total_raw != 9'000'000 ||
      battle.defender.side_strength_raw != 654'321) {
    return Fail("battle-control defender projection drifted from ABI");
  }

  // Generation byte 0x81 makes the full CombatID negative as a signed
  // int32, while preserving storage slot index 3.  The native resolver uses
  // unsigned low-24 indexing and exact dword identity, so the read-only
  // projection must preserve this ID instead of treating it as absent.
  constexpr std::int32_t signed_generation_combat_id = -2'130'706'429;
  Store(g_contact_combat_1, 0x08, signed_generation_combat_id);
  Store(g_player_internal_army, 0x128, signed_generation_combat_id);
  Store(g_enemy_internal_army, 0x128, signed_generation_combat_id);
  g_contact_province_combat_ids[1] = signed_generation_combat_id;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.combat_id != signed_generation_combat_id ||
      battle.attacker.ordered_armies[0].combat_backlink_id !=
          signed_generation_combat_id ||
      battle.defender.ordered_armies[0].combat_backlink_id !=
          signed_generation_combat_id) {
    return Fail("battle-control rejected a signed full CombatID");
  }
  const xar::game::BattleTransitionRequest signed_transition_request{
      signed_generation_combat_id};
  xar::game::BattleTransitionSnapshot signed_transition{};
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          bindings, signed_transition_request, signed_transition) !=
          xar::game::BattleTransitionSnapshotStatus::available ||
      signed_transition.combat_id != signed_generation_combat_id) {
    return Fail("battle-transition rejected a signed full CombatID");
  }
  Store(g_contact_combat_1, 0x08, contact_combat_1_id);
  Store(g_player_internal_army, 0x128, contact_combat_1_id);
  Store(g_enemy_internal_army, 0x128, contact_combat_1_id);
  g_contact_province_combat_ids[1] = contact_combat_1_id;

  // BattleResultID uses the same low-24 slot plus full-dword generation
  // identity contract.  Preserve a legal sign-bit generation instead of
  // conflating it with the sole missing sentinel -1.
  constexpr std::int32_t signed_generation_battle_result_id =
      -2'130'706'431;
  Store(g_contact_battle_result, 0x08,
        signed_generation_battle_result_id);
  Store(g_contact_combat_1, 0x708,
        signed_generation_battle_result_id);
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.battle_result_id != signed_generation_battle_result_id) {
    return Fail("battle-control rejected a signed full BattleResultID");
  }
  const xar::game::BattleTransitionRequest result_transition_request{
      contact_combat_1_id};
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          bindings, result_transition_request, signed_transition) !=
          xar::game::BattleTransitionSnapshotStatus::available ||
      signed_transition.battle_result_id !=
          signed_generation_battle_result_id) {
    return Fail("battle-transition rejected a signed full BattleResultID");
  }
  Store(g_contact_battle_result, 0x08, contact_battle_result_id);
  Store(g_contact_combat_1, 0x708, contact_battle_result_id);

  // The exact day gate is strict: elapsed day 14 fails, while the selected
  // side's early override bypasses only that gate.
  Store(g_contact_battle_result, 0x2C, std::int32_t{43'822'768});
  g_can_order_combat_retreat_result = false;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.legality.elapsed_whole_days != 14 ||
      battle.legality.legal_now || battle.legality.native_boolean ||
      battle.legality.reason_codes_in_native_order !=
          std::vector<std::string>{"too_early"} ||
      battle.legality.native_reason_keys_in_native_order !=
          std::vector<std::string>{
              "COMBAT_NO_RETREAT_TOO_EARLY"} ||
      battle.legality.earliest_day_gate_date_raw !=
          std::optional<std::int64_t>{43'823'112}) {
    return Fail("battle-control lost the strict retreat day-14 boundary");
  }
  Store(g_contact_combat_1, 0x20 + 0xC1, std::uint8_t{1});
  g_can_order_combat_retreat_result = true;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      !battle.side_flags.allow_early_retreat ||
      !battle.legality.legal_now || !battle.legality.native_boolean ||
      !battle.legality.reason_codes_in_native_order.empty()) {
    return Fail("battle-control did not apply the selected-side early gate");
  }

  // All four failures are projected from one frame in native order even
  // though the required null-sink native call returns at its first failure.
  Store(g_contact_combat_1, 0x20 + 0xC0, std::uint8_t{1});
  Store(g_contact_combat_1, 0x20 + 0xC1, std::uint8_t{0});
  Store(g_contact_combat_1, 0x20 + 0xC2, std::uint8_t{1});
  Store(g_contact_combat_1, 0x6B0, std::int32_t{2});
  Store(g_played_character, 0x1B8,
        static_cast<void *>(g_played_land_status.data()));
  Store(g_played_land_status, 0x1F8, std::int32_t{-1});
  Store(g_combat_retreat_rule_state, 0x38, std::uint32_t{0});
  g_can_order_combat_retreat_result = false;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      !battle.side_flags.disallow_retreat ||
      battle.side_flags.allow_early_retreat ||
      !battle.side_flags.skip_pursuit ||
      battle.legality.phase_raw != 2 ||
      battle.legality.phase != "pursuit" ||
      battle.legality.landless_gate_allows_retreat ||
      battle.legality.legal_now || battle.legality.native_boolean ||
      battle.legality.reason_codes_in_native_order !=
          std::vector<std::string>{
              "disallowed", "too_early", "pursuit_or_done", "landless"} ||
      battle.legality.native_reason_keys_in_native_order !=
          std::vector<std::string>{
              "COMBAT_NO_RETREAT_DISALLOWED",
              "COMBAT_NO_RETREAT_TOO_EARLY",
              "COMBAT_NO_RETREAT_PURSUIT",
              "COMBAT_NO_RETREAT_LANDLESS"}) {
    return Fail("battle-control retreat reasons drifted from native order");
  }
  Store(g_contact_combat_1, 0x20 + 0xC0, std::uint8_t{0});
  Store(g_contact_combat_1, 0x20 + 0xC2, std::uint8_t{0});
  Store(g_contact_combat_1, 0x6B0, std::int32_t{1});
  Store(g_played_character, 0x1B8, static_cast<void *>(nullptr));
  Store(g_contact_battle_result, 0x2C, std::int32_t{43'822'744});
  g_can_order_combat_retreat_result = true;

  // A legal missing BattleResultID follows the native fallback baseline. A
  // stale positive generation remains a stronger BattleControl identity
  // failure and is tested below.
  Store(g_contact_combat_1, 0x708, std::int32_t{-1});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.battle_result_id != -1 ||
      battle.legality.retreat_elapsed_baseline_date_raw != 43'822'744 ||
      !battle.legality.legal_now) {
    return Fail("battle-control did not use the legal BattleResult fallback");
  }
  Store(g_contact_combat_1, 0x708, contact_battle_result_id);

  // Mirror 0x2308850's owner scan without calling it. The selected Army need
  // not be first; public IDs remain in the native side's stored order.
  Store(g_character_storage, 0x2C, std::int32_t{7});
  Store(g_third_army, 0x174, kFixtureAllyCharacterId);
  Store(g_third_internal_army, 0x128, contact_combat_1_id);
  g_contact_combat_1_attacker_armies = {
      third_internal_army_id, player_internal_army_id};
  Store(g_contact_combat_1, 0x20 + 0x1C, std::int32_t{2});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.side_index != 0 || battle.side_scope != "owner_subset" ||
      battle.affected_public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{player_army_id} ||
      battle.unaffected_same_side_public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{third_army_id}) {
    return Fail("battle-control owner-subset projection lost stored order");
  }
  g_contact_combat_1_attacker_armies = {player_internal_army_id, 0};
  Store(g_contact_combat_1, 0x20 + 0x1C, std::int32_t{1});
  Store(g_third_internal_army, 0x128, std::int32_t{-1});
  Store(g_third_army, 0x174, played_character_id);
  Store(g_character_storage, 0x2C, std::int32_t{6});

  // The native dates are signed dwords, but the derived calendar lower bound
  // is intentionally int64 and may exceed INT32_MAX without narrowing.
  Store(game_state, 0x08, std::numeric_limits<std::int32_t>::max());
  Store(g_contact_battle_result, 0x2C,
        std::numeric_limits<std::int32_t>::max());
  g_can_order_combat_retreat_result = false;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      battle.legality.elapsed_whole_days != 0 ||
      battle.legality.earliest_day_gate_date_raw !=
          std::optional<std::int64_t>{2'147'484'000LL} ||
      *battle.legality.earliest_day_gate_date_raw <=
          std::numeric_limits<std::int32_t>::max() ||
      battle.legality.reason_codes_in_native_order !=
          std::vector<std::string>{"too_early"}) {
    return Fail("battle-control narrowed the retreat date boundary");
  }
  Store(game_state, 0x08, std::int32_t{43'823'104});
  Store(g_contact_battle_result, 0x2C, std::int32_t{43'822'744});
  g_can_order_combat_retreat_result = true;

  // The computed raw gates must agree with the exact null-sink native result.
  g_can_order_combat_retreat_result = false;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::state_changed ||
      battle.battle_control_ready ||
      battle.diagnostic_reason != "retreat_projection_failed") {
    return Fail("battle-control accepted a native retreat legality mismatch");
  }
  g_can_order_combat_retreat_result = true;

  Bindings missing_retreat_binding = bindings;
  missing_retreat_binding.can_order_combat_retreat = nullptr;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          missing_retreat_binding, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::unavailable ||
      battle.battle_control_ready) {
    return Fail("battle-control fabricated unavailable retreat legality");
  }

  // The native strength leaf mutates phase-day after sample A.  A reader
  // that does not compare the two complete frames would incorrectly publish
  // a hybrid snapshot.
  g_battle_mutate_on_side_strength = true;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::state_changed ||
      battle.battle_control_ready ||
      battle.diagnostic_reason != "double_sample_mismatch") {
    return Fail("battle-control accepted a changing double sample");
  }
  Store(g_contact_combat_1, 0x6B4, std::int32_t{4});

  Store(g_contact_battle_result, 0x08,
        std::int32_t{0x02000001});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::state_changed ||
      battle.battle_control_ready ||
      battle.diagnostic_reason != "battle_result_resolution_failed") {
    return Fail("battle-control accepted stale BattleResult generation");
  }
  Store(g_contact_battle_result, 0x08, contact_battle_result_id);

  Store(g_contact_combat_1, 0x705, std::uint8_t{1});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::state_changed ||
      battle.battle_control_ready ||
      battle.diagnostic_reason != "combat_daily_dispatch_in_progress") {
    return Fail("battle-control sampled inside daily dispatch");
  }
  Store(g_contact_combat_1, 0x705, std::uint8_t{0});

  Store(g_contact_combat_1, 0x20 + 0xB8,
        static_cast<void *>(nullptr));
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::state_changed ||
      battle.battle_control_ready ||
      battle.diagnostic_reason !=
          "active_combat_identity_attacker_side_ids_failed") {
    return Fail("battle-control accepted a stale CCombatSide back-pointer");
  }
  Store(g_contact_combat_1, 0x20 + 0xB8,
        static_cast<void *>(g_contact_combat_1.data()));

  Store(g_contact_combat_1, 0x20 + 0x98,
        std::int64_t{49'999'999});
  Store(g_contact_combat_1, 0x20 + 0xA0,
        std::int64_t{49'999'998});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::available ||
      !battle.battle_control_ready ||
      battle.attacker.stored_current_fighting_raw != 49'999'999 ||
      battle.attacker.stored_levy_current_fighting_raw != 49'999'998 ||
      battle.attacker.derived_current_fighting_raw != 50'000'000 ||
      battle.attacker.stored_current_matches_derived ||
      battle.attacker.stored_levy_current_matches_derived) {
    return Fail("battle-control lost stable stale-cache discriminants");
  }
  Store(g_contact_combat_1, 0x20 + 0x98,
        std::int64_t{50'000'000});
  Store(g_contact_combat_1, 0x20 + 0xA0,
        std::int64_t{50'000'000});

  Store(jomini_state, 0x20, std::uint8_t{0});
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::requires_paused ||
      battle.battle_control_ready) {
    return Fail("running map exposed mutable battle-control state");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});

  if (!xar::ck3_11906::InitializeBattleTerminalJournalStorageV1(bindings)) {
    return Fail("battle-terminal fixture could not publish normal terminal event");
  }
  if (!xar::ck3_11906::CaptureBattleTerminalJournalEntryV1(
          g_contact_combat_1.data(), false)) {
    const auto failed_terminal =
        xar::ck3_11906::LookupBattleTerminalJournalV1(
            contact_combat_1_id, 0);
    std::cerr << "battle-terminal fixture capture flags="
              << failed_terminal.event.capture_failure_flags
              << " combat=" << failed_terminal.event.combat_id
              << " result=" << failed_terminal.event.battle_result_id
              << " province=" << failed_terminal.event.province_id
              << " winner=" << failed_terminal.event.winner_raw
              << " attacker_primary="
              << failed_terminal.event.attacker_primary_participant_character_id
              << " defender_primary="
              << failed_terminal.event.defender_primary_participant_character_id
              << " attacker_count="
              << failed_terminal.event.attacker_public_cunit_count
              << " defender_count="
              << failed_terminal.event.defender_public_cunit_count << '\n';
    return Fail("battle-terminal fixture could not publish normal terminal event");
  }
  Store(g_player_internal_army, 0x128, std::int32_t{-1});
  g_player_army_state_code = 1;
  g_contact_province_combat_ids[0] = contact_combat_1_id;
  xar::game::Snapshot terminal_world{};
  xar::game::BattleTerminalTransitionSnapshotV1 terminal_transition{};
  const xar::game::BattleTerminalTransitionRequestV1 terminal_request{
      contact_combat_1_id, player_army_id, std::nullopt};
  if (!xar::ck3_11906::ReadSnapshot(bindings, terminal_world) ||
      xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      !terminal_transition.battle_terminal_transition_ready ||
      terminal_transition.subject.combat_backlink_id.has_value() ||
      terminal_transition.subject.active_combat_id.has_value() ||
      terminal_transition.subject.ai_membership_status !=
          xar::game::BattleTerminalAiMembershipStatusV1::observed ||
      terminal_transition.subject.coordinator_id != ai_coordinator_id ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::
              subject_assignment_reopened) {
    std::cerr << "battle-terminal post status="
              << static_cast<unsigned>(terminal_transition.status)
              << " reason=" << terminal_transition.unavailable_reason
              << " ready="
              << terminal_transition.battle_terminal_transition_ready
              << " backlink="
              << terminal_transition.subject.combat_backlink_id.value_or(-99)
              << " active="
              << terminal_transition.subject.active_combat_id.value_or(-99)
              << '\n';
    return Fail("battle-terminal did not canonicalize native -1 backlink to null");
  }
  g_contact_combat_0_attacker_armies = {third_internal_army_id};
  g_contact_combat_0_defender_armies = {enemy_internal_army_id};
  Store(g_contact_combat_0, 0x704, std::uint8_t{0});
  Store(g_enemy_internal_army, 0x128, contact_combat_0_id);
  Store(g_third_internal_army, 0x128, contact_combat_0_id);
  g_contact_province_combat_ids[0] = contact_combat_0_id;
  if (xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      terminal_transition.successor.matching_combat_ids_in_native_order !=
          std::vector<std::int32_t>{contact_combat_0_id} ||
      terminal_transition.successor.selected_successor_combat_id.has_value() ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::unavailable) {
    return Fail("battle-terminal sole residual match was misattributed to subject");
  }
  Store(g_contact_combat_0, 0x368 + 0x1C, std::int32_t{0});
  Store(g_player_internal_army, 0x128, contact_combat_0_id);
  Store(g_player_army, 0x170, std::int32_t{1});
  xar::game::Snapshot active_terminal_world{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, active_terminal_world) ||
      xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, active_terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      terminal_transition.subject.active_combat_id != contact_combat_0_id ||
      terminal_transition.subject.movement_or_retreat_state_raw != 1 ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::unavailable) {
    std::cerr << "battle-terminal unmatched-active status="
              << static_cast<unsigned>(terminal_transition.status)
              << " reason=" << terminal_transition.unavailable_reason
              << " active="
              << terminal_transition.subject.active_combat_id.value_or(-99)
              << " movement="
              << terminal_transition.subject.movement_or_retreat_state_raw
                     .value_or(-99)
              << " successor="
              << static_cast<unsigned>(terminal_transition.successor.state)
              << " matches="
              << terminal_transition.successor
                     .matching_combat_ids_in_native_order.size()
              << '\n';
    return Fail("battle-terminal unmatched active combat became retreat state");
  }
  Store(g_contact_combat_0, 0x368 + 0x1C, std::int32_t{1});
  Store(g_player_internal_army, 0x128, std::int32_t{-1});
  Store(g_player_army, 0x170, std::int32_t{0});
  Store(g_contact_combat_0, 0x704, std::uint8_t{1});
  Store(g_enemy_internal_army, 0x128, contact_combat_1_id);
  Store(g_third_internal_army, 0x128, std::int32_t{-1});
  g_contact_combat_0_attacker_armies = {enemy_internal_army_id};
  g_contact_province_combat_ids[0] = contact_combat_1_id;
  Store(g_player_army, 0x1C4, std::int32_t{0});
  Store(g_player_army, 0x1D0, static_cast<void *>(nullptr));
  if (xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      !terminal_transition.battle_terminal_transition_ready ||
      terminal_transition.subject.ai_membership_status !=
          xar::game::BattleTerminalAiMembershipStatusV1::unavailable ||
      terminal_transition.subject.coordinator_id.has_value() ||
      terminal_transition.subject.unit_stack_stored_index.has_value() ||
      terminal_transition.subject.subunit_stored_index.has_value() ||
      terminal_transition.subject.blocked_by_active_combat != false ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::unavailable) {
    return Fail("battle-terminal partial player AI membership poisoned core state");
  }
  Store(g_player_army, 0x1C4, std::int32_t{-1});
  if (xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      terminal_transition.subject.ai_membership_status !=
          xar::game::BattleTerminalAiMembershipStatusV1::none ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::no_successor) {
    return Fail("battle-terminal exact no-membership lost no-successor proof");
  }
  const xar::game::BattleTerminalTransitionRequestV1 missing_subject_request{
      contact_combat_1_id, 0x02000001, std::nullopt};
  if (xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, missing_subject_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::available ||
      terminal_transition.subject.exists ||
      terminal_transition.subject.ai_membership_status !=
          xar::game::BattleTerminalAiMembershipStatusV1::none ||
      terminal_transition.successor.state !=
          xar::game::BattleTerminalSuccessorStateV1::subject_missing) {
    return Fail("battle-terminal missing subject lost canonical membership none");
  }
  Store(g_player_army, 0x1C4, ai_coordinator_id);
  Store(g_player_army, 0x1D0,
        static_cast<void *>(g_ai_selected_subunit.data()));
  Store(g_contact_combat_1, 0x6E0, std::int32_t{2});
  if (xar::ck3_11906::CaptureBattleTerminalJournalEntryV1(
          g_contact_combat_1.data(), false) ||
      xar::ck3_11906::ReadBattleTerminalTransitionV1(
          bindings, terminal_world, terminal_request,
          terminal_transition) !=
          xar::game::BattleTerminalTransitionStatusV1::unavailable ||
      terminal_transition.unavailable_reason != "identity_unavailable" ||
      terminal_transition.terminal_journal.event_sequence.has_value() ||
      terminal_transition.terminal_journal.event_status !=
          xar::game::BattleTerminalJournalEventStatusV1::not_observed ||
      terminal_transition.terminal_journal.oldest_available_sequence != 1 ||
      terminal_transition.terminal_journal.latest_sequence != 2) {
    return Fail("battle-terminal unavailable leaked an observed journal event");
  }
  Store(g_contact_combat_1, 0x6E0, std::int32_t{0});
  g_contact_province_combat_ids[0] = contact_combat_0_id;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::subject_not_in_combat ||
      battle.battle_control_ready) {
    return Fail("battle-control did not distinguish an idle subject");
  }
  Store(g_player_internal_army, 0x128, contact_combat_1_id);
  Store(g_player_army, 0x170, std::int32_t{1});
  g_player_army_state_code = 6;
  if (xar::ck3_11906::ReadBattleControlSnapshot(
          bindings, battle_request, battle) !=
          xar::game::BattleControlSnapshotStatus::subject_retreating ||
      battle.battle_control_ready) {
    return Fail("battle-control did not reject a retreating subject");
  }

  // The direct full-CombatID lifecycle reader deliberately has no selected
  // Army or retreat-legality gate. This is the production postcondition path
  // for the stable frame above, where CK3 still reports both in_combat and
  // retreating on the public CUnit.
  const xar::game::BattleTransitionRequest transition_request{
      contact_combat_1_id};
  xar::game::BattleTransitionSnapshot transition{};
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          bindings, transition_request, transition) !=
          xar::game::BattleTransitionSnapshotStatus::available ||
      transition.status !=
          xar::game::BattleTransitionSnapshotStatus::available ||
      !transition.battle_transition_ready ||
      transition.observed_date_raw != 43'823'104 ||
      transition.combat_id != contact_combat_1_id ||
      transition.province_id != war_objective_province_id ||
      transition.phase != "main" || transition.phase_raw != 1 ||
      transition.phase_day != 4 ||
      transition.winner_side != "attacker" || transition.winner_raw != 0 ||
      transition.forced_winner_side != "none" ||
      transition.forced_winner_raw != -1 || !transition.finalized ||
      transition.battle_result_id != contact_battle_result_id ||
      transition.attacker_public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{player_army_id} ||
      transition.defender_public_cunit_ids_in_stored_order !=
          std::vector<std::int32_t>{enemy_army_id}) {
    return Fail("battle-transition lost the retreating CombatID lifecycle");
  }
  const xar::game::BattleTransitionRequest missing_transition_request{
      0x02000003};
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          bindings, missing_transition_request, transition) !=
          xar::game::BattleTransitionSnapshotStatus::combat_not_found ||
      transition.status !=
          xar::game::BattleTransitionSnapshotStatus::combat_not_found ||
      !transition.battle_transition_ready ||
      transition.combat_id != missing_transition_request.combat_id ||
      transition.province_id != -1 || !transition.phase.empty() ||
      !transition.attacker_public_cunit_ids_in_stored_order.empty() ||
      !transition.defender_public_cunit_ids_in_stored_order.empty()) {
    return Fail("battle-transition lost the full-generation not-found state");
  }
  Store(g_contact_combat_1, 0x705, std::uint8_t{1});
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          bindings, transition_request, transition) !=
          xar::game::BattleTransitionSnapshotStatus::state_changed ||
      transition.battle_transition_ready) {
    return Fail("battle-transition sampled inside daily dispatch");
  }
  Store(g_contact_combat_1, 0x705, std::uint8_t{0});
  Bindings missing_transition_binding = bindings;
  missing_transition_binding.combat_storage_slot = nullptr;
  if (xar::ck3_11906::ReadBattleTransitionSnapshot(
          missing_transition_binding, transition_request, transition) !=
          xar::game::BattleTransitionSnapshotStatus::unavailable ||
      transition.battle_transition_ready) {
    return Fail("battle-transition fabricated unavailable lifecycle state");
  }
  Store(g_player_army, 0x170, std::int32_t{0});
  g_player_army_state_code = 2;

  Store(g_enemy_internal_army, 0x128, std::int32_t{-1});
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::state_changed ||
      actual_contact.actual_contact_scope_ready ||
      actual_contact.combat_v3_participant_scope_ready) {
    return Fail(
        "actual-contact accepted a side participant without Combat backlink");
  }
  Store(g_player_internal_army, 0x128, std::int32_t{-1});
  Store(g_enemy_internal_army, 0x128, std::int32_t{-1});
  Store(g_third_internal_army, 0x128, std::int32_t{-1});
  g_contact_combat_1_attacker_armies = {third_internal_army_id, 0};
  Store(g_contact_combat_1, 0x20 + 0x18, std::int32_t{1});
  Store(g_contact_combat_1, 0x20 + 0x1C, std::int32_t{1});
  g_player_army_state_code = 1;

  g_contact_province_unit_ids = {enemy_army_id, player_army_id,
                                 third_army_id};
  if (xar::ck3_11906::ReadActualContactScope(
          bindings, actual_contact_request, actual_contact) !=
          xar::game::ActualContactScopeStatus::state_changed ||
      actual_contact.actual_contact_scope_ready ||
      actual_contact.combat_v3_participant_scope_ready) {
    return Fail("actual-contact reader accepted a noncanonical Province order");
  }

  bindings.combat_storage_slot = &g_combat_storage_pointer;
  Store(g_army_slots, 0x38, static_cast<void *>(nullptr));
  Store(g_player_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_third_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x170, std::int32_t{1});
  Store(g_player_internal_army, 0x128, active_combat_id);
  g_player_army_state_code = 2;
  g_enemy_army_state_code = 6;
  Store(g_war_objective_province, 0x08, static_cast<void *>(nullptr));
  Store(g_war_objective_province, 0x20, static_cast<void *>(nullptr));
  Store(g_war_objective_province, 0x748, static_cast<void *>(nullptr));
  Store(g_war_objective_province, 0x750, std::int32_t{0});
  Store(g_war_objective_province, 0x754, std::int32_t{0});
  Store(g_war_objective_province, 0x760, static_cast<void *>(nullptr));
  Store(g_war_objective_province, 0x768, std::int32_t{0});
  Store(g_war_objective_province, 0x76C, std::int32_t{0});
  Store(g_war_objective_province, 0x858, std::int32_t{2});

  // Freeze one explicit hypothetical contact. The final entry edge is
  // Province 2 -> target 5; current positions and move orders are irrelevant.
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));
  g_last_holding_defender_owner = nullptr;
  g_effective_stats_calls = 0;
  g_counter_current_chunk_calls = 0;
  g_counter_resolution_calls = 0;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      combat_inputs.target_province_id !=
          second_war_objective_province_id ||
      combat_inputs.scenario.attacker_entry_province_id != 2 ||
      combat_inputs.scenario.attacker_army_ids !=
          std::vector<std::int32_t>{player_army_id} ||
      combat_inputs.scenario.defender_army_ids !=
          std::vector<std::int32_t>{enemy_army_id} ||
      combat_inputs.scenario.attacker_side != "player_or_allied" ||
      combat_inputs.scenario.defender_side != "enemy" ||
      combat_inputs.armies.size() != 2 ||
      combat_inputs.armies[0].encounter_role != "attacker" ||
      combat_inputs.armies[1].encounter_role != "defender" ||
      !combat_inputs.target_province.available ||
      combat_inputs.target_province.province_id !=
          second_war_objective_province_id ||
      !combat_inputs.target_province.terrain.available ||
      combat_inputs.target_province.terrain.key != "hills" ||
      combat_inputs.target_province.terrain.combat_width_multiplier_raw !=
          80'000 ||
      !combat_inputs.target_province.crossing.available ||
      combat_inputs.target_province.crossing.kind != "river" ||
      !combat_inputs.target_province.defender_context.available ||
      combat_inputs.target_province.defender_context.defender_side !=
          "enemy" ||
      combat_inputs.target_province.defender_context.holding_defender_status !=
          xar::game::CombatObservationStatus::available ||
      !combat_inputs.target_province.defender_context.holding_defender ||
      g_last_holding_defender_owner != g_target_character.data() ||
      !combat_inputs.target_province.precontact_width.available ||
      combat_inputs.target_province.precontact_width.base != 900 ||
      combat_inputs.target_province.precontact_width.final != 720 ||
      !combat_inputs.input_observation_ready ||
      combat_inputs.monte_carlo_ready ||
      combat_inputs.missing_required_domains !=
          std::vector<std::string>{
              "damage_to_casualty_allocation", "pursuit_transition",
              "battle_end_and_retreat_transition",
              "phase_event_rng_and_effects"}) {
    return Fail("target-first combat input envelope drifted");
  }
  const auto &player_combat_army = combat_inputs.armies[0];
  const auto &enemy_combat_army = combat_inputs.armies[1];
  if (!player_combat_army.available ||
      player_combat_army.army_id != player_army_id ||
      player_combat_army.native_carmy_id != player_internal_army_id ||
      !player_combat_army.current_province_observable ||
      player_combat_army.current_province_id != 2 ||
      player_combat_army.owner.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_combat_army.owner.character_id != played_character_id ||
      player_combat_army.owner.counter_efficiency_raw != 10'000 ||
      player_combat_army.owner.counter_resistance_raw != 20'000 ||
      player_combat_army.commander.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_combat_army.commander.character_id != played_character_id ||
      !player_combat_army.commander.generic_advantage_observable ||
      player_combat_army.commander.generic_advantage_points != 3 ||
      !player_combat_army.commander.battle_context.available ||
      player_combat_army.commander.battle_context.province_id !=
          second_war_objective_province_id ||
      player_combat_army.commander.battle_context.effective_min_roll != -2 ||
      player_combat_army.commander.battle_context.effective_max_roll != 13 ||
      !player_combat_army.regiments_observable ||
      player_combat_army.regiments.size() != 2) {
    return Fail("player combat army context drifted from exact ABI");
  }
  const auto &player_bowmen = player_combat_army.regiments[0];
  const auto &player_absent_type = player_combat_army.regiments[1];
  if (!player_bowmen.available || !player_bowmen.identity_valid ||
      player_bowmen.current_soldiers != 600 ||
      player_bowmen.maximum_soldiers != 800 ||
      player_bowmen.maa_type.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_bowmen.maa_type.key != "bowmen" ||
      player_bowmen.kind.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_bowmen.kind.value != "men_at_arms" ||
      !player_bowmen.kind.fights_in_main_phase ||
      !player_bowmen.effective_stats.available ||
      player_bowmen.effective_stats.source_target_province_id !=
          second_war_objective_province_id ||
      player_bowmen.effective_stats.max_size != 880 ||
      player_bowmen.effective_stats.siege_value_raw != 100'000 ||
      player_bowmen.effective_stats.damage_raw != 60'000'000 ||
      player_bowmen.effective_stats.toughness_raw != 12'000'000 ||
      player_bowmen.counter.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_bowmen.counter.class_index != 0 ||
      player_bowmen.counter.current_chunk_raw != 600'000 ||
      player_bowmen.counter.targets.size() != 1 ||
      player_bowmen.counter.targets[0].class_index != 1 ||
      player_bowmen.counter.targets[0].effectiveness_raw != 50'000 ||
      !player_absent_type.available || !player_absent_type.identity_valid ||
      player_absent_type.maa_type.status !=
          xar::ck3_11906::CombatObservationStatus::absent ||
      player_absent_type.kind.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      player_absent_type.kind.value != "levy" ||
      player_absent_type.kind.fights_in_main_phase ||
      !player_absent_type.effective_stats.available ||
      player_absent_type.effective_stats.max_size != 420 ||
      player_absent_type.counter.status !=
          xar::ck3_11906::CombatObservationStatus::absent) {
    return Fail("per-regiment type/effective/counter projection drifted");
  }
  if (!enemy_combat_army.available ||
      enemy_combat_army.army_id != enemy_army_id ||
      enemy_combat_army.owner.status !=
          xar::ck3_11906::CombatObservationStatus::available ||
      enemy_combat_army.owner.character_id != enemy_character_id ||
      enemy_combat_army.owner.counter_efficiency_raw != 30'000 ||
      enemy_combat_army.owner.counter_resistance_raw != 40'000 ||
      enemy_combat_army.commander.status !=
          xar::ck3_11906::CombatObservationStatus::absent ||
      !enemy_combat_army.commander.battle_context.available ||
      enemy_combat_army.commander.battle_context.effective_min_roll != 0 ||
      enemy_combat_army.commander.battle_context.effective_max_roll != 0 ||
      enemy_combat_army.regiments.size() != 2 ||
      enemy_combat_army.regiments[0].maa_type.key !=
          g_armored_horsemen_key ||
      enemy_combat_army.regiments[0].kind.value != "men_at_arms" ||
      !enemy_combat_army.regiments[0].kind.fights_in_main_phase ||
      enemy_combat_army.regiments[1].maa_type.status !=
          xar::ck3_11906::CombatObservationStatus::absent ||
      enemy_combat_army.regiments[1].kind.value != "men_at_arms" ||
      enemy_combat_army.regiments[1].kind.fights_in_main_phase ||
      enemy_combat_army.regiments[1].counter.current_chunk_raw != 300'000) {
    return Fail("enemy combat army context drifted from exact ABI");
  }
  if (!player_combat_army.knights.available ||
      player_combat_army.knights.members.size() != 1 ||
      !player_combat_army.knights.members[0].eligible ||
      !player_combat_army.knights.members[0]
           .participant_army_membership_verified ||
      player_combat_army.knights.members[0].character_id !=
          played_character_id ||
      player_combat_army.knights.members[0].source_regiment_id !=
          player_regiment_0_id ||
      player_combat_army.knights.members[0].army_id !=
          player_internal_army_id ||
      player_combat_army.knights.members[0].prowess != 12 ||
      player_combat_army.knights.members[0].knight_effectiveness_raw !=
          100'000 ||
      player_combat_army.knights.members[0].effective_damage_raw !=
          60'000'000 ||
      player_combat_army.knights.members[0].effective_toughness_raw !=
          12'000'000 ||
      !enemy_combat_army.knights.available ||
      enemy_combat_army.knights.members.size() != 1 ||
      enemy_combat_army.knights.members[0].character_id !=
          enemy_character_id ||
      enemy_combat_army.knights.members[0].prowess != 8 ||
      enemy_combat_army.knights.members[0].knight_effectiveness_raw !=
          120'000 ||
      enemy_combat_army.knights.members[0].effective_damage_raw !=
          48'000'000 ||
      enemy_combat_army.knights.members[0].effective_toughness_raw !=
          9'600'000) {
    return Fail("knight identity/effectiveness projection drifted");
  }
  if (combat_inputs.counter_resolutions.size() != 2 ||
      !combat_inputs.counter_resolutions[0].available ||
      combat_inputs.counter_resolutions[0].countered_side !=
          "player_or_allied" ||
      combat_inputs.counter_resolutions[0].countering_side != "enemy" ||
      combat_inputs.counter_resolutions[0].context_scale_raw != 104'000 ||
      combat_inputs.counter_resolutions[0]
              .damage_retention_by_class_raw !=
          std::vector<std::int64_t>{100'000, 80'000, 60'000} ||
      !combat_inputs.counter_resolutions[1].available ||
      combat_inputs.counter_resolutions[1].context_scale_raw != 66'000 ||
      combat_inputs.counter_resolutions[1]
              .damage_retention_by_class_raw !=
          std::vector<std::int64_t>{90'000, 70'000, 50'000} ||
      combat_inputs.ongoing_combats.size() != 1 ||
      !combat_inputs.ongoing_combats[0].available ||
      combat_inputs.ongoing_combats[0].combat_id != active_combat_id ||
      combat_inputs.ongoing_combats[0].province_id !=
          second_war_objective_province_id ||
      combat_inputs.ongoing_combats[0].base_combat_width != 1'200 ||
      combat_inputs.ongoing_combats[0].final_combat_width != 960 ||
      combat_inputs.ongoing_combats[0].orientation !=
          "native_side_0_attacker_side_1_defender" ||
      combat_inputs.ongoing_combats[0].base_advantage != -5'000'000'000 ||
      combat_inputs.ongoing_combats[0].resolved_advantage != 6'000'000'000 ||
      g_effective_stats_calls != 4 ||
      g_counter_current_chunk_calls != 3 ||
      g_counter_resolution_calls != 2) {
    return Fail("counter resolution or live CCombat projection drifted");
  }

  Store(g_player_army, 0x30, static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x20, static_cast<void *>(g_enemy_province.data()));
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      combat_inputs.target_province.crossing.kind != "river") {
    return Fail("hypothetical contact depended on move target or current side");
  }
  Store(g_player_army, 0x30,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));

  constexpr std::array<std::string_view, 4> expected_crossing_kinds{
      "none", "strait", "river", "large_river"};
  for (std::int32_t edge_kind = 0; edge_kind < 4; ++edge_kind) {
    Store(g_player_target_adjacency, 0x00, edge_kind);
    if (xar::ck3_11906::ReadCombatSimulationInputs(
            bindings, combat_request, combat_inputs) !=
            xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
        !combat_inputs.target_province.crossing.available ||
        combat_inputs.target_province.crossing.kind !=
            expected_crossing_kinds[static_cast<std::size_t>(edge_kind)] ||
        !combat_inputs.target_province.defender_context.available ||
        combat_inputs.target_province.defender_context.defender_side !=
            "enemy") {
      return Fail("contact adjacency enum or attacker/defender orientation drifted");
    }
  }
  for (std::int32_t edge_kind = 4; edge_kind <= 6; ++edge_kind) {
    Store(g_player_target_adjacency, 0x00, edge_kind);
    if (xar::ck3_11906::ReadCombatSimulationInputs(
            bindings, combat_request, combat_inputs) !=
            xar::ck3_11906::ReadCombatSimulationInputsResult::invalid_encounter ||
        combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
      return Fail("non-contact adjacency encoding was accepted");
    }
  }
  Store(g_player_target_adjacency, 0x00, std::int32_t{2});

  // Reversing the explicit partitions must reverse the semantic defender;
  // current native positions remain observational only.
  const xar::game::CombatSimulationInputsRequest reversed_combat_request{
      second_war_objective_province_id,
      3,
      {enemy_army_id},
      {player_army_id},
  };
  Store(g_player_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  g_last_holding_defender_owner = nullptr;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, reversed_combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      !combat_inputs.target_province.defender_context.available ||
      combat_inputs.target_province.defender_context.defender_side !=
          "player_or_allied" ||
      g_last_holding_defender_owner != g_played_character.data()) {
    return Fail("reversed contact side did not preserve side0 attacker mapping");
  }
  Store(g_player_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));

  g_holding_defender_result = false;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      !combat_inputs.target_province.defender_context.available ||
      combat_inputs.target_province.defender_context.holding_defender) {
    return Fail("valid false holding predicate was confused with unavailable");
  }
  g_holding_defender_result = true;

  Store(g_player_map_node, 0x5C, std::int32_t{0});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::invalid_encounter ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("missing origin-target edge was accepted as no crossing");
  }
  Store(g_player_map_node, 0x5C, std::int32_t{1});

  Store(g_army_slots, 0x38, static_cast<void *>(g_third_army.data()));
  const xar::game::CombatSimulationInputsRequest three_combat_request{
      second_war_objective_province_id,
      2,
      {player_army_id, third_army_id},
      {enemy_army_id},
  };
  // A selected attacker's actual Province adjacency is irrelevant; only the
  // explicit final-edge entry Province participates in crossing derivation.
  Store(g_enemy_target_adjacency, 0x00, std::int32_t{3});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, three_combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      combat_inputs.armies.size() != 3 ||
      combat_inputs.target_province.crossing.kind != "river") {
    return Fail("hypothetical contact depended on an army's actual origin");
  }
  Store(g_player_target_adjacency, 0x00, std::int32_t{3});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, three_combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      combat_inputs.target_province.crossing.kind != "large_river") {
    return Fail("explicit entry edge did not control crossing kind");
  }
  Store(g_player_target_adjacency, 0x00, std::int32_t{2});
  Store(g_enemy_target_adjacency, 0x00, std::int32_t{2});

  Store(g_player_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_third_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_third_army, 0x174, kFixtureDeadCharacterId);
  Store(g_third_attacker_participant, 0x08, kFixtureDeadCharacterId);
  Store(g_attacker_participants, sizeof(void *),
        static_cast<void *>(g_third_attacker_participant.data()));
  Store(g_war, 0x34, std::int32_t{2});
  const xar::game::CombatSimulationInputsRequest mixed_defender_request{
      second_war_objective_province_id,
      3,
      {enemy_army_id},
      {player_army_id, third_army_id},
  };
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, mixed_defender_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      combat_inputs.armies.size() != 3 ||
      !combat_inputs.target_province.defender_context.available ||
      combat_inputs.target_province.defender_context.defender_side !=
          "player_or_allied" ||
      combat_inputs.target_province.defender_context.holding_defender_status !=
          xar::game::CombatObservationStatus::available ||
      g_last_holding_defender_owner != g_played_character.data() ||
      combat_inputs.counter_resolutions.size() != 2 ||
      !combat_inputs.counter_resolutions[0].available ||
      !combat_inputs.counter_resolutions[1].available) {
    return Fail("explicit mixed-owner insertion order was not projected");
  }
  Store(g_war, 0x34, std::int32_t{1});
  Store(g_attacker_participants, sizeof(void *),
        static_cast<void *>(nullptr));
  Store(g_third_army, 0x174, played_character_id);
  Store(g_player_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_third_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_second_war_objective_province.data()));
  Store(g_army_slots, 0x38, static_cast<void *>(g_third_army.data()));

  const xar::game::CombatSimulationInputsRequest no_attacker_request{
      second_war_objective_province_id, 2, {}, {enemy_army_id}};
  const xar::game::CombatSimulationInputsRequest duplicate_combat_request{
      second_war_objective_province_id,
      2,
      {player_army_id},
      {player_army_id},
  };
  const xar::game::CombatSimulationInputsRequest same_coalition_request{
      second_war_objective_province_id,
      2,
      {player_army_id},
      {third_army_id},
  };
  const xar::game::CombatSimulationInputsRequest out_of_scope_combat_request{
      second_war_objective_province_id,
      2,
      {player_army_id},
      {std::int32_t{0x01000004}},
  };
  auto missing_target_request = combat_request;
  missing_target_request.target_province_id = 7;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, no_attacker_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::invalid_arguments ||
      xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, duplicate_combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::invalid_arguments ||
      xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, same_coalition_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::invalid_encounter ||
      xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, out_of_scope_combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::army_not_in_scope ||
      xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, missing_target_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::target_province_not_found) {
    return Fail("combat input target/army admission was not strict");
  }
  Store(g_army_slots, 0x38, static_cast<void *>(nullptr));
  g_knight_effectiveness_context_available = false;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::unavailable ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("knight effectiveness context failure was not atomic");
  }
  g_knight_effectiveness_context_available = true;
  g_knight_damage_per_prowess = 51;
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::unavailable ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("knight contribution define drift was not rejected");
  }
  g_knight_damage_per_prowess = 50;
  Store(g_played_knight_link, 0xF8, enemy_regiment_0_id);
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::unavailable ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("knight regiment backlink failure was not atomic");
  }
  Store(g_played_knight_link, 0xF8, player_regiment_0_id);

  g_effective_stats_failed_regiment = g_player_regiment_1.data();
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.armies.size() != 2 ||
      combat_inputs.armies[0].regiments[1].available ||
      combat_inputs.armies[0].regiments[1].effective_stats.available ||
      combat_inputs.armies[0].regiments[1].effective_stats.damage_raw != 0 ||
      combat_inputs.armies[0].regiments[1].unavailable_reason !=
          "effective_stats_helper_failed" ||
      !combat_inputs.armies[0].knights.available ||
      !combat_inputs.counter_resolutions[0].available) {
    return Fail("target-effective helper failure was not row-atomic");
  }
  g_effective_stats_failed_regiment = nullptr;

  Store(g_bowmen_type, 0x28, std::size_t{0});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.armies[0].regiments[0].available ||
      combat_inputs.armies[0].regiments[0].maa_type.status !=
          xar::ck3_11906::CombatObservationStatus::unavailable ||
      !combat_inputs.armies[0].regiments[0].maa_type.key.empty() ||
      combat_inputs.armies[0].regiments[0].unavailable_reason !=
          "maa_type_key_unavailable" ||
      !combat_inputs.counter_resolutions[0].available) {
    return Fail("invalid MAA key was guessed or partially published");
  }
  Store(g_bowmen_type, 0x28, std::size_t{6});

  Store(g_player_internal_army, 0x120, std::int32_t{0x02000002});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.armies[0].commander.status !=
          xar::ck3_11906::CombatObservationStatus::unavailable ||
      combat_inputs.armies[0].commander.character_id != -1 ||
      combat_inputs.armies[0].commander.generic_advantage_observable) {
    return Fail("commander generation mismatch was coerced to absent");
  }
  Store(g_player_internal_army, 0x120, played_character_id);

  Store(g_hills_terrain, 0x58, std::int64_t{0});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      !combat_inputs.target_province.terrain.available ||
      combat_inputs.target_province.terrain.combat_width_multiplier_raw != 0 ||
      !combat_inputs.target_province.precontact_width.available ||
      combat_inputs.target_province.precontact_width.final != 100) {
    return Fail("zero terrain multiplier was confused with unavailable");
  }
  Store(g_hills_terrain, 0x58, std::int64_t{80'000});
  Store(g_hills_terrain, 0x28, std::size_t{4'097});
  Store(g_hills_terrain, 0x30, std::size_t{4'097});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.target_province.available ||
      combat_inputs.target_province.terrain.available ||
      !combat_inputs.target_province.terrain.key.empty() ||
      combat_inputs.target_province.terrain.combat_width_multiplier_raw != 0 ||
      combat_inputs.target_province.precontact_width.available) {
    return Fail("invalid terrain key did not null the complete terrain row");
  }
  Store(g_hills_terrain, 0x28, std::size_t{5});
  Store(g_hills_terrain, 0x30, std::size_t{15});

  Store(g_player_internal_army, 0x128, std::int32_t{-1});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::available ||
      !combat_inputs.ongoing_combats.empty()) {
    return Fail("no live CCombat was confused with a zero-filled row");
  }
  Store(g_player_internal_army, 0x128, active_combat_id);

  Store(g_player_internal_army, 0x128, std::int32_t{-2});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.input_observation_ready ||
      combat_inputs.ongoing_combats.size() != 1 ||
      combat_inputs.ongoing_combats[0].available ||
      !combat_inputs.ongoing_combats[0].combat_id_observable ||
      combat_inputs.ongoing_combats[0].combat_id != -2 ||
      combat_inputs.ongoing_combats[0].unavailable_reason !=
          "combat_not_found") {
    return Fail("signed CCombatID was not preserved as an opaque identity");
  }
  Store(g_player_internal_army, 0x128, active_combat_id);

  Store(g_player_regiment_0_inner_type, 0x68, std::int32_t{0});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.armies[0].regiments[0].counter.status !=
          xar::ck3_11906::CombatObservationStatus::unavailable ||
      combat_inputs.armies[0].regiments[0].counter.current_chunk_raw != 0 ||
      combat_inputs.counter_resolutions[0].available) {
    return Fail("counter chunk sentinel was coerced to zero");
  }
  Store(g_player_regiment_0_inner_type, 0x68, std::int32_t{100});

  Store(g_enemy_regiment_0, 0x148, played_character_id);
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::unavailable ||
      combat_inputs != xar::ck3_11906::CombatSimulationInputsSnapshot{}) {
    return Fail("duplicate knight CharacterID was not rejected atomically");
  }
  Store(g_enemy_regiment_0, 0x148, enemy_character_id);
  Store(g_enemy_regiment_1, 0x10, std::int32_t{0x02000004});
  if (xar::ck3_11906::ReadCombatSimulationInputs(
          bindings, combat_request, combat_inputs) !=
          xar::ck3_11906::ReadCombatSimulationInputsResult::partial ||
      combat_inputs.input_observation_ready ||
      combat_inputs.armies.size() != 2 ||
      combat_inputs.armies[1].available ||
      !combat_inputs.armies[1].native_carmy_id_observable ||
      combat_inputs.armies[1].native_carmy_id != enemy_internal_army_id ||
      combat_inputs.armies[1].regiments_observable ||
      !combat_inputs.armies[1].regiments.empty() ||
      combat_inputs.armies[1].knights.available ||
      combat_inputs.armies[1].unavailable_reason != "regiment_not_found" ||
      std::find(combat_inputs.missing_required_domains.begin(),
                combat_inputs.missing_required_domains.end(),
                "regiment_composition") ==
          combat_inputs.missing_required_domains.end()) {
    return Fail("combat regiment graph failure did not retain a partial row");
  }
  Store(g_enemy_regiment_1, 0x10, enemy_regiment_1_id);
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));

  Store(g_enemy_regiment_1, 0x10, std::int32_t{0x02000004});
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::partial ||
      army_strengths.size() != 2 || !army_strengths[0].available ||
      army_strengths[1].available ||
      army_strengths[1].native_carmy_id != enemy_internal_army_id ||
      army_strengths[1].regiment_count != 0 ||
      army_strengths[1].current_soldiers != 0 ||
      army_strengths[1].maximum_soldiers != 0 ||
      army_strengths[1].ai_base_power_raw != 0 ||
      army_strengths[1].unavailable_reason != "regiment_not_found") {
    return Fail("regiment generation mismatch did not fail one row closed");
  }
  Store(g_enemy_regiment_1, 0x10, enemy_regiment_1_id);

  Store(g_player_internal_army, 0x44, std::int32_t{-1});
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::partial ||
      army_strengths[0].available ||
      army_strengths[0].unavailable_reason != "regiment_array_invalid" ||
      !army_strengths[1].available) {
    return Fail("invalid regiment array was partially aggregated");
  }
  Store(g_player_internal_army, 0x44, std::int32_t{2});

  Store(g_player_internal_army, 0x40, std::int32_t{1});
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::partial ||
      army_strengths[0].available ||
      army_strengths[0].unavailable_reason != "regiment_array_invalid" ||
      !army_strengths[1].available) {
    return Fail("regiment count beyond capacity was accepted");
  }
  Store(g_player_internal_army, 0x40, std::int32_t{2});

  Store(g_player_regiment_0, 0x08, static_cast<void *>(nullptr));
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::partial ||
      army_strengths[0].available ||
      army_strengths[0].unavailable_reason !=
          "identity_predicate_unavailable") {
    return Fail("missing identity predicate did not fail one row closed");
  }
  Store(g_player_regiment_0, 0x08,
        static_cast<void *>(g_regiment_identity_vtable.data()));

  Store(g_player_internal_army, 0x38, static_cast<void *>(nullptr));
  Store(g_player_internal_army, 0x40, std::int32_t{0});
  Store(g_player_internal_army, 0x44, std::int32_t{0});
  if (xar::ck3_11906::ReadArmyStrengths(bindings, army_strengths) !=
          xar::ck3_11906::ReadArmyStrengthsResult::available ||
      army_strengths[0].regiment_count != 0 ||
      army_strengths[0].current_soldiers != 0 ||
      army_strengths[0].maximum_soldiers != 0 ||
      army_strengths[0].ai_base_power_raw != 0) {
    return Fail("valid empty regiment array was confused with unavailable");
  }
  Store(g_player_internal_army, 0x38,
        static_cast<void *>(g_player_regiment_ids.data()));
  Store(g_player_internal_army, 0x40, std::int32_t{2});
  Store(g_player_internal_army, 0x44, std::int32_t{2});

  const auto &active_siege_state =
      snapshot.active_wars[0].objective_province_states[0];
  const auto &occupied_state =
      snapshot.active_wars[0].objective_province_states[1];
  const auto &idle_state =
      snapshot.active_wars[0].objective_province_states[2];
  if (active_siege_state.province_id != war_objective_province_id ||
      !active_siege_state.occupation_observable ||
      active_siege_state.is_occupied ||
      active_siege_state.occupying_character_id != -1 ||
      !active_siege_state.fort_level_observable ||
      active_siege_state.fort_level != 2 ||
      !active_siege_state.garrison_size_observable ||
      active_siege_state.garrison_size != 500 ||
      !active_siege_state.besieging_strength_observable ||
      active_siege_state.besieging_strength != 650 ||
      !active_siege_state.siege_observable ||
      !active_siege_state.has_active_siege ||
      active_siege_state.siege_id != active_siege_id ||
      active_siege_state.besieging_army_id != player_army_id ||
      !active_siege_state.player_army_besieging ||
      active_siege_state.siege_progress_fraction.raw != 25'000 ||
      active_siege_state.siege_progress_fraction.scale !=
          kFixtureFixedPointScale ||
      active_siege_state.siege_current_work.raw != 2'500'000 ||
      active_siege_state.siege_total_work.raw != 10'000'000 ||
      !active_siege_state.siege_days_left_observable ||
      active_siege_state.siege_days_left != 12 ||
      !active_siege_state.assault_observable ||
      active_siege_state.breach_level != 1 ||
      active_siege_state.assault_in_progress ||
      !active_siege_state.can_start_assault ||
      active_siege_state.can_stop_assault ||
      active_siege_state.assault_daily_progress.raw != 340'000 ||
      active_siege_state.assault_daily_progress.scale !=
          kFixtureFixedPointScale ||
      active_siege_state.assault_daily_casualties != 16) {
    return Fail("active objective siege projection drifted");
  }
  if (occupied_state.province_id != second_war_objective_province_id ||
      !occupied_state.occupation_observable || !occupied_state.is_occupied ||
      occupied_state.occupying_character_id != enemy_character_id ||
      !occupied_state.fort_level_observable || occupied_state.fort_level != 0 ||
      !occupied_state.garrison_size_observable ||
      occupied_state.garrison_size != 0 ||
      !occupied_state.besieging_strength_observable ||
      occupied_state.besieging_strength != 0 ||
      !occupied_state.siege_observable || occupied_state.has_active_siege ||
      occupied_state.siege_id != -1 || occupied_state.assault_observable) {
    return Fail("occupied/no-siege objective state was not explicit");
  }
  if (idle_state.province_id != third_war_objective_province_id ||
      !idle_state.occupation_observable || idle_state.is_occupied ||
      !idle_state.fort_level_observable || idle_state.fort_level != 3 ||
      !idle_state.garrison_size_observable || idle_state.garrison_size != 800 ||
      !idle_state.besieging_strength_observable ||
      idle_state.besieging_strength != 900 || !idle_state.siege_observable ||
      idle_state.has_active_siege || idle_state.assault_observable) {
    return Fail("idle objective Province state projection drifted");
  }

  Store(g_war_objective_province, 0x790, std::int32_t{-1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.active_wars[0].objective_province_states[0].siege_observable ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .has_active_siege ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .assault_observable) {
    return Fail("no-active-siege was confused with unavailable siege state");
  }
  Store(g_war_objective_province, 0x790, active_siege_id);

  Store(g_siege, 0x08, std::int32_t{0x02000001});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0].objective_province_states[0].siege_observable) {
    return Fail("siege projection ignored SiegeID generation");
  }
  Store(g_siege, 0x08, active_siege_id);

  Store(g_siege, 0x200,
        static_cast<void *>(g_second_war_objective_province.data()));
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0].objective_province_states[0].siege_observable) {
    return Fail("siege projection ignored the Province backlink");
  }
  Store(g_siege, 0x200,
        static_cast<void *>(g_war_objective_province.data()));

  g_siege_alive = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0].objective_province_states[0].siege_observable) {
    return Fail("siege projection ignored native component liveness");
  }
  g_siege_alive = true;

  g_siege_progress_raw = -1;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0].objective_province_states[0].siege_observable) {
    return Fail("invalid native siege fraction was partially published");
  }
  g_siege_progress_raw = 25'000;

  g_siege_days_left = std::numeric_limits<std::int32_t>::max();
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.active_wars[0].objective_province_states[0].siege_observable ||
      !snapshot.active_wars[0]
           .objective_province_states[0]
           .has_active_siege ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .siege_days_left_observable) {
    return Fail("stalled siege INT_MAX was exposed as a real day count");
  }
  g_siege_days_left = 12;

  Store(g_siege, 0x3D8, std::int32_t{3});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.active_wars[0].objective_province_states[0].siege_observable ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .assault_observable) {
    return Fail("invalid breach level did not fail the assault subdomain closed");
  }
  Store(g_siege, 0x3D8, std::int32_t{1});

  g_assault_progress_available = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.active_wars[0].objective_province_states[0].siege_observable ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .assault_observable) {
    return Fail("failed daily projection partially published assault state");
  }
  g_assault_progress_available = true;

  Store(g_siege, 0x44C, std::uint8_t{2});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .assault_observable) {
    return Fail("invalid assault flag was coerced into a public bool");
  }
  Store(g_siege, 0x44C, std::uint8_t{0});

  Store(g_siege, 0x3D8, std::int32_t{0});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("intact-wall assault projection was unavailable");
  }
  const auto &intact_assault_state =
      snapshot.active_wars[0].objective_province_states[0];
  if (!intact_assault_state.assault_observable ||
      intact_assault_state.breach_level != 0 ||
      intact_assault_state.assault_in_progress ||
      intact_assault_state.can_start_assault ||
      intact_assault_state.can_stop_assault ||
      intact_assault_state.assault_daily_progress.raw != 0 ||
      intact_assault_state.assault_daily_casualties != 0) {
    return Fail("intact walls did not publish a closed zero projection");
  }
  Store(g_siege, 0x3D8, std::int32_t{1});

  Store(g_second_war_objective_province, 0x744,
        std::int32_t{0x02000003});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0]
          .objective_province_states[1]
          .occupation_observable) {
    return Fail("occupation projection ignored CharacterID generation");
  }
  Store(g_second_war_objective_province, 0x744, enemy_character_id);

  Store(g_enemy_army, 0x178, player_internal_army_id);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0]
              .objective_province_states[0]
              .besieging_army_id != player_army_id ||
      !snapshot.active_wars[0]
           .objective_province_states[0]
           .player_army_besieging) {
    return Fail("non-canonical CArmy-to-CUnit join polluted siege identity");
  }
  Store(g_enemy_army, 0x178, enemy_internal_army_id);

  Store(jomini_state, 0x20, std::uint8_t{0});
  Store(g_player_move_route_info_1, 0x00, std::int32_t{7});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.player_armies.size() != 1 ||
      !snapshot.player_armies[0].route_province_ids.empty() ||
      !snapshot.player_armies[0].move_target_observable ||
      snapshot.player_armies[0].move_target_province_id != 3) {
    return Fail("running snapshot traversed beyond the legacy route tail");
  }

  Store(jomini_state, 0x20, std::uint8_t{1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.player_armies.size() != 1 ||
      !snapshot.player_armies[0].route_province_ids.empty() ||
      snapshot.player_armies[0].move_target_observable ||
      snapshot.player_armies[0].move_target_province_id != -1) {
    return Fail("unit route published a partial invalid province path");
  }
  Store(g_player_move_route_info_1, 0x00, std::int32_t{5});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.player_armies.size() != 1 ||
      snapshot.player_armies[0].route_province_ids !=
          std::vector<std::int32_t>{4, 5, 3} ||
      !snapshot.player_armies[0].move_target_observable ||
      snapshot.player_armies[0].move_target_province_id != 3) {
    return Fail("paused snapshot omitted the complete native unit route");
  }

  Store(g_player_army, 0x40, std::int32_t{4'097});
  Store(g_player_army, 0x44, std::int32_t{4'097});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.player_armies.size() != 1 ||
      !snapshot.player_armies[0].route_province_ids.empty() ||
      snapshot.player_armies[0].move_target_observable ||
      snapshot.player_armies[0].move_target_province_id != -1) {
    return Fail("unit route traversal was not bounded");
  }
  Store(g_player_army, 0x40, std::int32_t{3});
  Store(g_player_army, 0x44, std::int32_t{3});
  Store(jomini_state, 0x20, std::uint8_t{0});

  constexpr std::array<std::string_view, 9> expected_unit_state_names{
      "regular",   "combat", "sieging", "embarked", "gathering",
      "retreating", "moving", "raiding", "bartering",
  };
  for (std::int32_t state_code = 1; state_code <= 9; ++state_code) {
    g_player_army_state_code = state_code;
    if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
        snapshot.player_armies.size() != 1 ||
        snapshot.player_armies[0].army_state_code != state_code ||
        snapshot.player_armies[0].army_state !=
            expected_unit_state_names[static_cast<std::size_t>(state_code - 1)] ||
        snapshot.player_armies[0].in_combat != (state_code == 2)) {
      return Fail("unit state code-to-name projection drifted");
    }
  }
  g_player_army_state_code = 2;

  std::array<std::int32_t, 1> single_targeted_title_id{
      targeted_title_id};
  Store(g_war, 0x270,
        static_cast<void *>(single_targeted_title_id.data()));
  Store(g_war, 0x278, std::int32_t{1});
  Store(g_war, 0x27C, std::int32_t{1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{war_objective_province_id,
                                    second_war_objective_province_id,
                                    third_war_objective_province_id}) {
    return Fail("kingdom target did not project every county capital");
  }
  single_targeted_title_id[0] = targeted_duchy_a_title_id;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{war_objective_province_id,
                                    second_war_objective_province_id}) {
    return Fail("duchy target did not project every county capital");
  }
  single_targeted_title_id[0] = second_county_title_id;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{second_war_objective_province_id}) {
    return Fail("county target did not project its capital barony province");
  }
  single_targeted_title_id[0] = third_capital_barony_title_id;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{third_war_objective_province_id}) {
    return Fail("barony target did not project its own province");
  }
  single_targeted_title_id[0] = targeted_title_id;
  Store(g_targeted_title, 0x10, std::int32_t{0x02000001});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].targeted_title_ids !=
          std::vector<std::int32_t>{targeted_title_id} ||
      !snapshot.active_wars[0].war_objective_province_ids.empty() ||
      !snapshot.active_wars[0].objective_province_states.empty()) {
    return Fail("war objective projection ignored TitleID generation");
  }
  Store(g_targeted_title, 0x10, targeted_title_id);

  Store(g_second_county_title, 0x10, std::int32_t{0x02000005});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      !snapshot.active_wars[0].war_objective_province_ids.empty() ||
      !snapshot.active_wars[0].objective_province_states.empty()) {
    return Fail(
        "war objective projection published a partial stale hierarchy");
  }
  Store(g_second_county_title, 0x10, second_county_title_id);

  Store(g_targeted_title, 0x248, std::int32_t{4'097});
  Store(g_targeted_title, 0x24C, std::int32_t{4'097});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      !snapshot.active_wars[0].war_objective_province_ids.empty() ||
      !snapshot.active_wars[0].objective_province_states.empty()) {
    return Fail("war objective hierarchy traversal was not bounded");
  }
  Store(g_targeted_title, 0x248, std::int32_t{2});
  Store(g_targeted_title, 0x24C, std::int32_t{2});
  Store(g_war, 0x270,
        static_cast<void *>(g_war_targeted_title_ids.data()));
  Store(g_war, 0x278, std::int32_t{4});
  Store(g_war, 0x27C, std::int32_t{4});

  // The hierarchy may legitimately expose more exact Province IDs than the
  // rich-state heartbeat budget. Build 257 complete county-capital branches
  // and require an atomic empty state array rather than a 256-row prefix.
  {
    constexpr std::size_t budget_province_count = 257;
    constexpr std::size_t root_title_index = 1;
    constexpr std::size_t first_county_title_index = 2;
    constexpr std::size_t first_barony_title_index =
        first_county_title_index + budget_province_count;
    constexpr std::size_t budget_title_capacity =
        first_barony_title_index + budget_province_count;
    std::vector<std::array<std::byte, 0x250>> budget_titles(
        budget_title_capacity);
    std::vector<std::array<std::byte, 0x88>> budget_title_templates(
        budget_title_capacity);
    std::vector<std::array<std::int32_t, 1>> budget_county_children(
        budget_province_count);
    std::vector<std::int32_t> budget_root_children(
        budget_province_count);
    std::vector<std::byte> budget_title_slots(
        budget_title_capacity * 0x10);
    std::array<std::byte, 0x40> budget_title_storage{};
    std::vector<std::array<std::byte, 0x20>> budget_provinces(
        budget_province_count + 1);
    std::vector<void *> budget_province_pointers(
        budget_province_count + 1, nullptr);

    const auto component_id = [](std::size_t index) {
      return static_cast<std::int32_t>(0x01000000U |
                                       static_cast<std::uint32_t>(index));
    };
    const auto root_title_id = component_id(root_title_index);
    Store(budget_titles[root_title_index], 0x10, root_title_id);
    Store(budget_titles[root_title_index], 0x160,
          static_cast<void *>(
              budget_title_templates[root_title_index].data()));
    Store(budget_title_templates[root_title_index], 0x5C,
          std::int32_t{3});
    StoreBytes(budget_title_slots.data(), root_title_index * 0x10 + 0x08,
               static_cast<void *>(budget_titles[root_title_index].data()));

    for (std::size_t index = 0; index < budget_province_count; ++index) {
      const auto county_index = first_county_title_index + index;
      const auto barony_index = first_barony_title_index + index;
      const auto county_id = component_id(county_index);
      const auto barony_id = component_id(barony_index);
      const auto province_id = static_cast<std::int32_t>(index + 1);
      budget_root_children[index] = county_id;
      budget_county_children[index][0] = barony_id;

      Store(budget_titles[county_index], 0x10, county_id);
      Store(budget_titles[county_index], 0x160,
            static_cast<void *>(budget_title_templates[county_index].data()));
      Store(budget_title_templates[county_index], 0x5C,
            std::int32_t{2});
      Store(budget_titles[county_index], 0x240,
            static_cast<void *>(budget_county_children[index].data()));
      Store(budget_titles[county_index], 0x248, std::int32_t{1});
      Store(budget_titles[county_index], 0x24C, std::int32_t{1});
      StoreBytes(budget_title_slots.data(), county_index * 0x10 + 0x08,
                 static_cast<void *>(budget_titles[county_index].data()));

      Store(budget_titles[barony_index], 0x10, barony_id);
      Store(budget_titles[barony_index], 0x160,
            static_cast<void *>(budget_title_templates[barony_index].data()));
      Store(budget_title_templates[barony_index], 0x5C,
            std::int32_t{1});
      Store(budget_title_templates[barony_index], 0x80, province_id);
      StoreBytes(budget_title_slots.data(), barony_index * 0x10 + 0x08,
                 static_cast<void *>(budget_titles[barony_index].data()));

      Store(budget_provinces[index + 1], 0x10, province_id);
      budget_province_pointers[index + 1] =
          budget_provinces[index + 1].data();
    }
    Store(budget_titles[root_title_index], 0x240,
          static_cast<void *>(budget_root_children.data()));
    Store(budget_titles[root_title_index], 0x248,
          static_cast<std::int32_t>(budget_root_children.size()));
    Store(budget_titles[root_title_index], 0x24C,
          static_cast<std::int32_t>(budget_root_children.size()));
    Store(budget_title_storage, 0x20,
          static_cast<void *>(budget_title_slots.data()));
    Store(budget_title_storage, 0x2C,
          static_cast<std::int32_t>(budget_title_capacity));
    Store(game_data, 0x140,
          static_cast<void *>(budget_province_pointers.data()));
    Store(game_data, 0x14C,
          static_cast<std::int32_t>(budget_province_pointers.size()));
    Store(game_data, 0x320,
          static_cast<void *>(budget_title_storage.data()));
    std::array<std::int32_t, 1> budget_target{root_title_id};
    Store(g_war, 0x270, static_cast<void *>(budget_target.data()));
    Store(g_war, 0x278, std::int32_t{1});
    Store(g_war, 0x27C, std::int32_t{1});

    const bool budget_was_atomic =
        xar::ck3_11906::ReadSnapshot(bindings, snapshot) &&
        snapshot.active_wars.size() == 1 &&
        snapshot.active_wars[0].war_objective_province_ids.size() ==
            budget_province_count &&
        snapshot.active_wars[0].war_objective_province_ids.front() == 1 &&
        snapshot.active_wars[0].war_objective_province_ids.back() ==
            static_cast<std::int32_t>(budget_province_count) &&
        snapshot.active_wars[0].objective_province_states.empty();

    Store(game_data, 0x140, static_cast<void *>(g_provinces.data()));
    Store(game_data, 0x14C, std::int32_t{7});
    Store(game_data, 0x320,
          static_cast<void *>(g_landed_title_storage.data()));
    Store(g_war, 0x270,
          static_cast<void *>(g_war_targeted_title_ids.data()));
    Store(g_war, 0x278, std::int32_t{4});
    Store(g_war, 0x27C, std::int32_t{4});
    if (!budget_was_atomic) {
      return Fail("257 objective states exceeded the atomic heartbeat budget");
    }
  }

  FixtureSetGlobalNumeric(0, kFixtureFixedPointScale);
  g_script_identifier_lookup_calls = 0;
  const void *const dead_source_event_target =
      g_global_variable_entries.data() + 2 * 0x20 + 0x10;
  if (FixtureIsEventTargetValid(dead_source_event_target) ||
      FixtureResolveEventTargetObject(dead_source_event_target) != nullptr) {
    return Fail(
        "fixture did not model the dead source's liveness-gated resolver");
  }
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_one_life_settlement ||
      !snapshot.one_life_settlement.ready ||
      snapshot.one_life_settlement.commit_serial != 1 ||
      snapshot.one_life_settlement.source_character_id != 0x01000004 ||
      snapshot.one_life_settlement.final_score.raw != 12'345'678 ||
      snapshot.one_life_settlement.final_score.scale !=
          kFixtureFixedPointScale ||
      snapshot.one_life_settlement.score_before_reject.raw != 9'876'543 ||
      snapshot.one_life_settlement.score_before_reject.scale !=
          kFixtureFixedPointScale ||
      snapshot.one_life_settlement.record_candidate != 42 ||
      snapshot.one_life_settlement.old_record != 50 ||
      snapshot.one_life_settlement.record_delta != -8 ||
      snapshot.one_life_settlement.blessing_count != 3 ||
      snapshot.one_life_settlement.refusal_count != 2 ||
      snapshot.one_life_settlement.contract_progress != 7 ||
      !snapshot.one_life_settlement.record_written ||
      g_script_identifier_lookup_calls != 13) {
    return Fail(
        "one-life settlement lost exact globals or rejected its dead source");
  }

  Store(g_global_variable_container, 0x1C, std::int32_t{11});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("incomplete published settlement was exposed");
  }
  Store(g_global_variable_container, 0x1C, std::int32_t{12});
  FixtureSetGlobalNumeric(7, -8 * kFixtureFixedPointScale - 1);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("non-integral semantic settlement integer was coerced");
  }
  FixtureSetGlobalNumeric(7, -8 * kFixtureFixedPointScale);
  FixtureSetGlobalCharacter(2, std::int32_t{0x01000001});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("non-character settlement source was exposed");
  }
  FixtureSetGlobalCharacter(2, kFixtureDeadCharacterId);
  Bindings no_settlement_bindings = bindings;
  no_settlement_bindings.global_variable_container_accessor_slot = nullptr;
  if (!xar::ck3_11906::ReadSnapshot(no_settlement_bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("missing settlement bindings did not degrade to null");
  }
  no_settlement_bindings = bindings;
  no_settlement_bindings.lookup_script_identifier_id = nullptr;
  if (!xar::ck3_11906::ReadSnapshot(no_settlement_bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("missing script-identifier lookup did not degrade to null");
  }
  FixtureSetGlobalNumeric(0, 0);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_one_life_settlement) {
    return Fail("ready=0 settlement payload was exposed");
  }
  Bindings no_opponent_fallback = bindings;
  no_opponent_fallback.resolve_default_raise_province = nullptr;
  xar::ck3_11906::Snapshot no_opponent_fallback_snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(no_opponent_fallback,
                                    no_opponent_fallback_snapshot) ||
      no_opponent_fallback_snapshot.active_wars.size() != 1 ||
      no_opponent_fallback_snapshot.active_wars[0]
              .primary_opponent_character_id != enemy_character_id ||
      !no_opponent_fallback_snapshot.active_wars[0]
           .player_is_primary_war_leader ||
      no_opponent_fallback_snapshot.active_wars[0]
              .enemy_primary_default_raise_province_id != -1) {
    return Fail("optional opponent fallback did not stay adapter-local");
  }
  Store(g_played_family_data, 0x10, stale_enemy_character_id);
  Store(g_played_family_data, 0x14, stale_enemy_character_id);
  g_played_spouse_ids[0] = stale_enemy_character_id;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.played_character_betrothed_id != -1 ||
      snapshot.played_character_primary_spouse_id != -1 ||
      !snapshot.played_character_spouse_ids.empty()) {
    return Fail("played-character relationships ignored CharacterID generation");
  }
  Store(g_played_family_data, 0x10, enemy_character_id);
  Store(g_played_family_data, 0x14, enemy_character_id);
  g_played_spouse_ids[0] = enemy_character_id;
  Store(g_attacker_participant, 0x08, enemy_character_id);
  Store(g_defender_participant, 0x08, played_character_id);
  Store(g_war, 0x288, enemy_character_id);
  Store(g_war, 0x28C, played_character_id);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].player_side !=
          xar::ck3_11906::PlayerWarSide::defender ||
      snapshot.active_wars[0].primary_opponent_character_id !=
          enemy_character_id ||
      !snapshot.active_wars[0].player_is_primary_war_leader ||
      snapshot.active_wars[0].enemy_primary_default_raise_province_id != 4 ||
      snapshot.active_wars[0].player_relative_war_score != -37 ||
      snapshot.active_wars[0].allied_armies.size() != 1 ||
      snapshot.active_wars[0].allied_armies[0].army_id != player_army_id ||
      snapshot.active_wars[0].enemy_armies.size() != 1 ||
      snapshot.active_wars[0].enemy_armies[0].army_id != enemy_army_id) {
    return Fail("defender war score and army sides did not project relatively");
  }
  Store(g_war, 0x28C, std::int32_t{0x01000004});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].player_is_primary_war_leader ||
      snapshot.active_wars[0].primary_opponent_character_id !=
          enemy_character_id ||
      snapshot.active_wars[0].enemy_primary_default_raise_province_id != 4) {
    return Fail("war projection did not distinguish a non-primary player");
  }
  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_war, 0x288, played_character_id);
  Store(g_war, 0x28C, enemy_character_id);
  Store(g_played_character, 0x1C8,
        reinterpret_cast<void *>(0x12345678));
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_played_character || snapshot.played_character_alive) {
    return Fail("played-character death data did not project alive=false");
  }
  Store(g_played_character, 0x1C8, static_cast<void *>(nullptr));
  g_has_local_player = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSaveCheckpoint(bindings).status !=
          xar::ck3_11906::SaveCheckpointStatus::map_not_ready ||
      g_submit_called) {
    return Fail("save-checkpoint ignored the early map-ready gate");
  }
  g_has_local_player = true;
  g_expected_command = ExpectedCommand::auto_save;
  const auto save_result = xar::ck3_11906::SubmitSaveCheckpoint(bindings);
  if (save_result.status !=
          xar::ck3_11906::SaveCheckpointStatus::submitted ||
      save_result.date_raw != 43'823'104 || !g_submit_called) {
    return Fail("save-checkpoint did not submit the pinned autosave command");
  }
  g_expected_command = ExpectedCommand::pause;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("pause-map did not construct and submit the pinned command");
  }

  g_expected_command = ExpectedCommand::speed;
  g_submit_called = false;
  if (!xar::ck3_11906::SubmitSetSpeed(bindings, 5) || !g_submit_called ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 0) ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 6)) {
    return Fail("set-speed did not construct the pinned command for 1..5");
  }

  g_expected_command = ExpectedCommand::event_option;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSelectEventOption(bindings, 2) !=
          xar::ck3_11906::SelectEventOptionResult::submitted ||
      !g_submit_called) {
    return Fail("event option did not construct and submit the pinned command");
  }
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSelectEventOption(bindings, -1) !=
          xar::ck3_11906::SelectEventOptionResult::option_out_of_range ||
      xar::ck3_11906::SubmitSelectEventOption(bindings, 3) !=
          xar::ck3_11906::SelectEventOptionResult::option_out_of_range ||
      g_submit_called) {
    return Fail("event option accepted an index outside the active event");
  }

  g_has_active_event = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_active_event || snapshot.active_event_instance_id != -1 ||
      snapshot.active_event_option_count != 0 ||
      xar::ck3_11906::SubmitSelectEventOption(bindings, 0) !=
          xar::ck3_11906::SelectEventOptionResult::no_active_event) {
    return Fail("no-active-event state was not represented explicitly");
  }
  g_has_active_event = true;

  Store(g_pending_storage, 0x20,
        static_cast<void *>(g_pending_slots.data()));
  Store(g_pending_storage, 0x2C, std::int32_t{2});
  Store(g_pending_slots, 0x08,
        static_cast<void *>(g_unrelated_pending_interaction.data()));
  Store(g_pending_slots, 0x18,
        static_cast<void *>(g_pending_interaction.data()));
  Store(g_unrelated_pending_interaction, 0x10,
        std::int32_t{0x01000000});
  Store(g_unrelated_pending_interaction, 0x2F0, std::int32_t{1234567});
  Store(g_unrelated_pending_interaction, 0x2F4, enemy_character_id);
  Store(g_unrelated_pending_interaction, 0x5C0, std::int32_t{0});
  Store(g_unrelated_pending_interaction, 0x5C6, std::uint8_t{0});
  Store(g_pending_interaction, 0x10, std::int32_t{0x01000001});
  Store(g_pending_interaction, 0x2F0, std::int32_t{8675309});
  Store(g_pending_interaction, 0x2F4, played_character_id);
  Store(g_pending_interaction, 0x5C0, std::int32_t{0});
  Store(g_pending_interaction, 0x5C6, std::uint8_t{0});
  g_pending_storage_pointer = g_pending_storage.data();
  g_pending_visibility_calls = 0;
  g_pending_accept_validation_calls = 0;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != 0x01000001 ||
      snapshot.pending_sender_character_id != 8675309 ||
      snapshot.pending_auto_accept_notification ||
      g_pending_visibility_calls != 1 ||
      g_pending_accept_validation_calls != 1) {
    return Fail("pending snapshot did not skip the other player's request");
  }
  Store(g_pending_interaction, 0x2F4, enemy_character_id);
  Store(g_pending_interaction, 0x300, played_character_id);
  Store(g_pending_interaction, 0x5C0, std::int32_t{1});
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != 0x01000001) {
    return Fail("alternate pending recipient routing was not recognized");
  }
  Store(g_pending_interaction, 0x2F4, played_character_id);
  Store(g_pending_interaction, 0x5C0, std::int32_t{0});
  g_pending_visibility_result = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_pending_character_interaction) {
    return Fail("native pending visibility failure remained actionable");
  }
  g_pending_visibility_result = true;
  g_expected_command = ExpectedCommand::reply_accept;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::submitted ||
      !g_submit_called) {
    return Fail("pending interaction accept command layout did not match");
  }
  g_expected_command = ExpectedCommand::reply_reject;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::reject) !=
          xar::ck3_11906::ReplyPendingInteractionResult::submitted ||
      !g_submit_called) {
    return Fail("pending interaction reject command layout did not match");
  }
  g_pending_accept_validation_result = false;
  g_submit_called = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_pending_character_interaction ||
      xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::
              no_pending_interaction ||
      g_submit_called) {
    return Fail("native reply validation failure remained actionable");
  }
  g_pending_accept_validation_result = true;
  Store(g_pending_interaction, 0x5C6, std::uint8_t{1});
  g_pending_visibility_calls = 0;
  g_pending_accept_validation_calls = 0;
  g_submit_called = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != 0x01000001 ||
      !snapshot.pending_auto_accept_notification ||
      g_pending_visibility_calls != 1 ||
      g_pending_accept_validation_calls != 0 ||
      xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::
              acknowledgement_required ||
      g_submit_called) {
    return Fail("notification discovery did not preserve the ACK-only channel");
  }
  g_expected_pending_command_id = kSignedPendingInteractionId;
  Store(g_pending_interaction, 0x10, kSignedPendingInteractionId);
  g_pending_visibility_calls = 0;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id !=
          kSignedPendingInteractionId ||
      !snapshot.pending_auto_accept_notification ||
      g_pending_visibility_calls != 1) {
    return Fail("signed pending generation was not preserved in snapshot");
  }
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(bindings, -1) !=
      xar::ck3_11906::AcknowledgePendingInteractionResult::unavailable) {
    return Fail("notification ACK accepted the native invalid sentinel");
  }
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::
              requires_paused ||
      g_submit_called) {
    return Fail("notification ACK did not require a paused snapshot");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kStaleSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::
              pending_interaction_mismatch ||
      g_submit_called) {
    return Fail("notification ACK accepted a stale generation");
  }
  g_pending_visibility_calls = 0;
  g_pending_mutate_generation_on_call = 1;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::state_changed ||
      g_submit_called) {
    return Fail("notification ACK missed same-frame generation drift");
  }
  g_pending_mutate_generation_on_call = -1;
  Store(g_pending_interaction, 0x10, kSignedPendingInteractionId);
  g_pending_visibility_calls = 0;
  g_pending_visibility_fail_on_call = 2;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::
              not_for_played_character ||
      g_pending_visibility_calls != 2 || g_submit_called) {
    return Fail("notification ACK missed same-frame local-route drift");
  }
  g_pending_visibility_fail_on_call = -1;
  g_pending_visibility_calls = 0;
  g_pending_clear_notification_on_call = 2;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::state_changed ||
      g_pending_visibility_calls != 2 || g_submit_called) {
    return Fail("notification ACK missed same-frame channel drift");
  }
  g_pending_clear_notification_on_call = -1;
  Store(g_pending_interaction, 0x5C6, std::uint8_t{1});
  g_expected_command = ExpectedCommand::reply_acknowledge;
  g_pending_visibility_calls = 0;
  g_pending_accept_validation_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::submitted ||
      !g_submit_called || g_pending_accept_validation_calls != 0) {
    return Fail("notification ACK did not submit fixed enum 4 by full ID");
  }
  g_submit_result = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::
              queue_rejected ||
      !g_submit_called) {
    return Fail("notification ACK hid native queue rejection");
  }
  g_submit_result = true;
  Store(g_pending_interaction, 0x5C6, std::uint8_t{0});
  g_submit_called = false;
  if (xar::ck3_11906::SubmitAcknowledgePendingInteraction(
          bindings, kSignedPendingInteractionId) !=
          xar::ck3_11906::AcknowledgePendingInteractionResult::
              acknowledgement_not_required ||
      g_submit_called) {
    return Fail("ordinary pending request entered the ACK channel");
  }
  Store(jomini_state, 0x20, std::uint8_t{0});
  g_pending_storage_pointer = nullptr;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_pending_character_interaction ||
      xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::
              no_pending_interaction) {
    return Fail("no-pending-interaction state was not explicit");
  }

  g_expected_command = ExpectedCommand::raise_troops;
  g_submit_called = false;
  g_raise_construct_called = false;
  g_raise_validate_called = false;
  g_raise_destroy_called = false;
  if (xar::ck3_11906::SubmitRaiseTroopsDefault(bindings) !=
          xar::ck3_11906::RaiseTroopsResult::submitted ||
      !g_raise_construct_called || !g_raise_validate_called ||
      !g_submit_called || !g_raise_destroy_called) {
    return Fail("raise-troops did not use the native construct/validate queue");
  }
  g_raise_validate_result = false;
  g_submit_called = false;
  g_raise_destroy_called = false;
  if (xar::ck3_11906::SubmitRaiseTroopsDefault(bindings) !=
          xar::ck3_11906::RaiseTroopsResult::validation_failed ||
      g_submit_called || !g_raise_destroy_called) {
    return Fail("raise-troops submitted after native validation failed");
  }
  g_raise_validate_result = true;

  g_submit_called = false;
  g_preview_origin_called = false;
  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  auto route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::requires_paused ||
      g_preview_origin_called || g_preview_path_context_constructed ||
      g_preview_route_built || g_move_path_initialized ||
      g_move_destroy_called || g_submit_called) {
    return Fail("move preview called the planner while the map was running");
  }

  Store(jomini_state, 0x20, std::uint8_t{1});
  g_move_mode_result = 1;
  g_preview_origin_called = false;
  g_preview_origin_mode_is_one = 0xFF;
  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.army_id != player_army_id ||
      route_preview.origin_province_id != 2 ||
      route_preview.target_province_id != 3 ||
      route_preview.route_province_ids !=
          std::vector<std::int32_t>{4, 5, 3} ||
      !g_preview_origin_called || g_preview_origin_mode_is_one != 1 ||
      !g_preview_path_context_constructed || !g_preview_route_built ||
      !g_move_path_initialized || !g_move_destroy_called || g_submit_called) {
    return Fail("move preview did not copy and clean the native route");
  }

  // A travelling CUnit still reports the Province it is leaving as current,
  // while CK3's origin resolver advances to the first remaining route entry.
  // The public origin remains the paused-snapshot current Province and the
  // effective origin is prepended without simplifying a native loop back.
  g_preview_effective_origin = g_enemy_default_raise_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{2});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{3});
  g_preview_route_count = 2;
  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.origin_province_id != 2 ||
      route_preview.target_province_id != 3 ||
      route_preview.route_province_ids !=
          std::vector<std::int32_t>{4, 2, 3} ||
      !g_preview_path_context_constructed || !g_preview_route_built ||
      !g_move_path_initialized || !g_move_destroy_called || g_submit_called) {
    return Fail("in-flight move preview did not normalize its effective origin");
  }

  Store(g_preview_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{2});
  Store(g_preview_move_route_info_2, 0x00, std::int32_t{3});
  g_preview_route_count = 3;
  g_preview_route_built = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.origin_province_id != 2 ||
      route_preview.route_province_ids !=
          std::vector<std::int32_t>{4, 4, 2, 3} ||
      !g_preview_route_built || !g_move_destroy_called || g_submit_called) {
    return Fail("in-flight move preview simplified a native duplicate/loop");
  }

  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 4);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.origin_province_id != 2 ||
      route_preview.target_province_id != 4 ||
      route_preview.route_province_ids !=
          std::vector<std::int32_t>{4} ||
      g_preview_path_context_constructed || g_preview_route_built ||
      !g_move_path_initialized || !g_move_destroy_called || g_submit_called) {
    return Fail("effective-origin target preview did not expose one remaining hop");
  }

  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{2});
  g_preview_route_count = 1;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 2);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.origin_province_id != 2 ||
      route_preview.target_province_id != 2 ||
      route_preview.route_province_ids !=
          std::vector<std::int32_t>{4, 2} ||
      !g_preview_path_context_constructed || !g_preview_route_built ||
      !g_move_path_initialized || !g_move_destroy_called || g_submit_called) {
    return Fail("in-flight current target did not finish the edge and route back");
  }

  g_preview_effective_origin = g_second_war_objective_province.data();
  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::origin_unavailable ||
      route_preview.origin_province_id != -1 ||
      g_preview_path_context_constructed || g_preview_route_built ||
      g_move_path_initialized || g_move_destroy_called || g_submit_called) {
    return Fail("move preview accepted an origin outside current/route-front");
  }

  g_preview_effective_origin = g_player_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{5});
  g_preview_route_count = 3;
  g_preview_path_context_constructed = false;
  g_preview_route_built = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 2);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::available ||
      route_preview.origin_province_id != 2 ||
      route_preview.target_province_id != 2 ||
      !route_preview.route_province_ids.empty() ||
      g_preview_path_context_constructed || g_preview_route_built ||
      !g_move_path_initialized || !g_move_destroy_called || g_submit_called) {
    return Fail("same-province preview unnecessarily invoked the route planner");
  }

  g_preview_route_build_result = false;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::route_unavailable ||
      !g_preview_route_built || !g_move_destroy_called || g_submit_called) {
    return Fail("failed move preview did not destroy its partial native path");
  }
  g_preview_route_build_result = true;

  Store(g_preview_move_route_info_1, 0x00, std::int32_t{99});
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::route_unavailable ||
      !g_move_destroy_called || g_submit_called) {
    return Fail("move preview published an unresolved intermediate province");
  }
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{5});

  g_preview_route_count = 4'097;
  g_move_destroy_called = false;
  route_preview =
      xar::ck3_11906::PreviewMoveArmy(bindings, player_army_id, 3);
  if (route_preview.status !=
          xar::ck3_11906::PreviewMoveArmyStatus::route_unavailable ||
      !g_move_destroy_called || g_submit_called) {
    return Fail("move preview route traversal was not bounded");
  }
  g_preview_route_count = 3;

  // Route timing is a separate application-main query in production.  The
  // native fixture exercises its atomic reader directly: every helper call
  // receives a zeroed 0x130 shallow prefix, exact Q100000 durations use CK3's
  // half-up nonnegative day rounding, and a full hostile scope is mandatory.
  // Install the exact Province adjacency graph and MovePath land/water rows
  // consumed by the duration ABI; the combat fixture above uses a narrower
  // one-edge graph that is deliberately insufficient for route projection.
  Store(g_enemy_default_raise_province, 0x08,
        static_cast<void *>(g_route_map_node_4.data()));
  Store(g_second_war_objective_province, 0x08,
        static_cast<void *>(g_route_map_node_5.data()));
  Store(g_player_map_node, 0x50,
        static_cast<void *>(g_route_adjacencies_2.data()));
  Store(g_player_map_node, 0x5C, std::int32_t{2});
  Store(g_enemy_map_node, 0x50,
        static_cast<void *>(g_route_adjacencies_3.data()));
  Store(g_enemy_map_node, 0x5C, std::int32_t{1});
  Store(g_route_map_node_4, 0x50,
        static_cast<void *>(g_route_adjacencies_4.data()));
  Store(g_route_map_node_4, 0x5C, std::int32_t{2});
  Store(g_route_map_node_5, 0x50,
        static_cast<void *>(g_route_adjacencies_5.data()));
  Store(g_route_map_node_5, 0x5C, std::int32_t{2});
  Store(g_player_map_node, 0xB0,
        static_cast<void *>(g_route_origin_info_2.data()));
  Store(g_enemy_map_node, 0xB0,
        static_cast<void *>(g_route_origin_info_3.data()));
  Store(g_route_map_node_4, 0xB0,
        static_cast<void *>(g_route_origin_info_4.data()));
  Store(g_route_map_node_5, 0xB0,
        static_cast<void *>(g_route_origin_info_5.data()));
  Store(g_route_origin_info_2, 0x00, std::int32_t{2});
  Store(g_route_origin_info_3, 0x00, std::int32_t{3});
  Store(g_route_origin_info_4, 0x00, std::int32_t{4});
  Store(g_route_origin_info_5, 0x00, std::int32_t{5});
  for (auto *const info : {g_route_origin_info_2.data(),
                           g_route_origin_info_3.data(),
                           g_route_origin_info_4.data(),
                           g_route_origin_info_5.data(),
                           g_player_move_route_info_0.data(),
                           g_player_move_route_info_1.data(),
                           g_player_move_route_info_2.data(),
                           g_preview_move_route_info_0.data(),
                           g_preview_move_route_info_1.data(),
                           g_preview_move_route_info_2.data(),
                           g_enemy_move_route_info_0.data()}) {
    StoreBytes(info, 0x09, std::uint8_t{1});
    StoreBytes(info, 0x0B, std::uint8_t{0});
  }
  Store(g_route_adjacencies_2, 0x04, std::int32_t{4});
  Store(g_route_adjacencies_2, 0x30 + 0x04, std::int32_t{3});
  Store(g_route_adjacencies_3, 0x04, std::int32_t{2});
  Store(g_route_adjacencies_4, 0x04, std::int32_t{5});
  Store(g_route_adjacencies_4, 0x30 + 0x04, std::int32_t{2});
  Store(g_route_adjacencies_5, 0x04, std::int32_t{3});
  Store(g_route_adjacencies_5, 0x30 + 0x04, std::int32_t{4});
  Store(jomini_state, 0x20, std::uint8_t{1});
  g_enemy_army_state_code = 1;
  Store(g_enemy_army, 0x170, std::int32_t{0});
  g_player_army_state_code = 7;
  g_move_mode_result = 1;
  g_preview_effective_origin = g_player_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_preview_move_route_info_2, 0x00, std::int32_t{3});
  g_preview_route_count = 3;
  g_preview_route_built = false;
  g_route_duration_calls = 0;
  g_route_duration_prefix_zeroed = true;
  g_route_duration_failure = false;
  g_route_duration_late_zero_speed_accumulation = false;
  g_route_land_speed_raw = 100'000;
  g_route_naval_speed_raw = 100'000;
  g_route_current_edge_speed_raw = 100'000;
  xar::game::RouteContactHorizonRequest route_contact_request{};
  route_contact_request.subject_army_id = player_army_id;
  route_contact_request.target_province_id = 3;
  route_contact_request.hostile_army_ids = {enemy_army_id};
  xar::game::RouteContactHorizonSnapshot route_contact{};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.status !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.date_raw != 43'823'104 ||
      route_contact.horizon_start_date_raw != 43'823'104 ||
      route_contact.horizon_end_date_raw != 43'823'128 ||
      !route_contact.one_day_contact_free ||
      !route_contact.conflicts.empty() ||
      !route_contact.subject_route.timeline_observable ||
      route_contact.subject_route.current_province_id != 2 ||
      route_contact.subject_route.effective_origin_province_id != 4 ||
      route_contact.subject_route.route_province_ids !=
          std::vector<std::int32_t>{4, 5, 3} ||
      route_contact.subject_route.arrival_date_raws !=
          std::vector<std::int32_t>{43'823'128, 43'823'152,
                                    43'823'176} ||
      route_contact.hostile_routes.size() != 1 ||
      !route_contact.hostile_routes[0].timeline_observable ||
      route_contact.hostile_routes[0].army_id != enemy_army_id ||
      route_contact.hostile_routes[0].current_province_id != 3 ||
      !route_contact.hostile_routes[0].route_province_ids.empty() ||
      !route_contact.hostile_routes[0].arrival_date_raws.empty() ||
      g_preview_route_built ||
      g_route_duration_calls != 3 ||
      !g_route_duration_prefix_zeroed) {
    return Fail(
        "active route-contact timeline did not preserve the committed path");
  }

  // A regular subject with an exactly empty active MovePath occupies its
  // current Province for the whole one-day horizon.  The reader must not ask
  // CK3 to construct a move back to that same Province: production returns a
  // route-unavailable move mode for this otherwise observable hold.
  Store(g_player_army, 0x38, static_cast<void *>(nullptr));
  Store(g_player_army, 0x40, std::int32_t{0});
  Store(g_player_army, 0x44, std::int32_t{0});
  g_player_army_state_code = 1;
  g_move_mode_result = 2;
  route_contact_request.target_province_id = 2;
  g_preview_route_built = false;
  g_route_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      !route_contact.one_day_contact_free ||
      !route_contact.conflicts.empty() ||
      !route_contact.subject_route.timeline_observable ||
      route_contact.subject_route.current_province_id != 2 ||
      route_contact.subject_route.effective_origin_province_id != 2 ||
      !route_contact.subject_route.route_province_ids.empty() ||
      !route_contact.subject_route.arrival_date_raws.empty() ||
      g_preview_route_built || g_route_duration_calls != 0) {
    return Fail("stationary same-current route-contact was not observable");
  }

  // A valid stationary subject must still report which hostile active
  // timeline failed.  Model a progressed hostile edge whose cached and
  // recalculated current-edge speeds are both zero; the public error must not
  // collapse this into an unattributed timeline_unavailable result.
  Store(g_enemy_move_route_info_0, 0x00, std::int32_t{2});
  g_enemy_move_path = {g_enemy_move_route_info_0.data()};
  Store(g_enemy_army, 0x38,
        static_cast<void *>(g_enemy_move_path.data()));
  Store(g_enemy_army, 0x40, std::int32_t{1});
  Store(g_enemy_army, 0x44, std::int32_t{1});
  Store(g_enemy_army, 0x168, std::int64_t{1});
  Store(g_enemy_army, 0x190, std::int64_t{0});
  g_enemy_army_state_code = 7;
  g_route_current_edge_speed_raw = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      !route_contact.subject_route.timeline_observable ||
      route_contact.timeline_failure.role !=
          xar::game::RouteContactTimelineFailureRole::hostile ||
      route_contact.timeline_failure.army_id != enemy_army_id ||
      route_contact.timeline_failure.path_kind !=
          xar::game::RouteContactTimelinePathKind::hostile_active ||
      route_contact.timeline_failure.stage !=
          xar::game::RouteContactTimelineFailureStage::current_edge_speed) {
    return Fail("hostile route-timeline failure provenance was unavailable");
  }
  Store(g_enemy_army, 0x38, static_cast<void *>(nullptr));
  Store(g_enemy_army, 0x40, std::int32_t{0});
  Store(g_enemy_army, 0x44, std::int32_t{0});
  Store(g_enemy_army, 0x168, std::int64_t{0});
  Store(g_enemy_army, 0x190, std::int64_t{100'000});
  g_enemy_army_state_code = 1;
  g_route_current_edge_speed_raw = 100'000;

  Store(g_player_army, 0x38,
        static_cast<void *>(g_player_move_path.data()));
  Store(g_player_army, 0x40, std::int32_t{3});
  Store(g_player_army, 0x44, std::int32_t{3});
  g_player_army_state_code = 7;
  g_move_mode_result = 1;
  route_contact_request.target_province_id = 3;

  // 0x2247320 cannot represent the exact Province boundary where progress,
  // cached speed, and recalculated current-edge speed are all zero: despite
  // zero progress it subtracts the zero-extended 0xffffffff failure value.
  // Model the four-row committed suffix from the production blocker.  The
  // adapter must read its first edge through 0x22475E0, then give only the
  // non-shared-front tail to the full-route helper.
  Store(g_boundary_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_boundary_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_boundary_move_route_info_2, 0x00, std::int32_t{3});
  Store(g_boundary_move_route_info_3, 0x00, std::int32_t{2});
  for (auto *const info : {g_boundary_move_route_info_0.data(),
                           g_boundary_move_route_info_1.data(),
                           g_boundary_move_route_info_2.data(),
                           g_boundary_move_route_info_3.data()}) {
    StoreBytes(info, 0x09, std::uint8_t{1});
    StoreBytes(info, 0x0B, std::uint8_t{0});
  }
  g_boundary_move_path = {g_boundary_move_route_info_0.data(),
                          g_boundary_move_route_info_1.data(),
                          g_boundary_move_route_info_2.data(),
                          g_boundary_move_route_info_3.data()};
  Store(g_player_army, 0x38,
        static_cast<void *>(g_boundary_move_path.data()));
  Store(g_player_army, 0x40, std::int32_t{4});
  Store(g_player_army, 0x44, std::int32_t{4});
  Store(g_player_army, 0x168, std::int64_t{0});
  Store(g_player_army, 0x190, std::int64_t{0});
  g_route_current_edge_speed_raw = 0;
  g_route_edge_duration_raw = 50'000;
  g_route_duration_zero_current_edge_correction = true;
  route_contact_request.target_province_id = 2;

  std::array<std::byte, 0x130> boundary_full_prefix{};
  Store(boundary_full_prefix, 0x00,
        static_cast<void *>(g_boundary_move_path.data()));
  Store(boundary_full_prefix, 0x0C, std::int32_t{4});
  std::int64_t boundary_full_duration = 0;
  g_route_duration_calls = 0;
  if (FixtureReadRouteTravelDuration(
          g_player_army.data(), &boundary_full_duration,
          boundary_full_prefix.data(), g_player_province.data()) !=
          &boundary_full_duration ||
      boundary_full_duration != 400'000 - 0xFFFF'FFFFLL ||
      g_route_duration_calls != 1) {
    return Fail("route fixture did not model zero-speed correction sentinel");
  }

  g_route_duration_calls = 0;
  g_route_edge_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      !route_contact.one_day_contact_free ||
      route_contact.subject_route.route_province_ids !=
          std::vector<std::int32_t>{4, 5, 3, 2} ||
      route_contact.subject_route.arrival_date_raws !=
          std::vector<std::int32_t>{43'823'128, 43'823'152,
                                    43'823'176, 43'823'200} ||
      g_route_edge_duration_calls != 1 || g_route_duration_calls != 3) {
    return Fail("zero-progress boundary did not use edge-plus-tail timeline");
  }

  // A one-row committed route needs only the exact first-edge helper.
  Store(g_player_army, 0x40, std::int32_t{1});
  Store(g_player_army, 0x44, std::int32_t{1});
  route_contact_request.target_province_id = 4;
  g_route_duration_calls = 0;
  g_route_edge_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.subject_route.route_province_ids !=
          std::vector<std::int32_t>{4} ||
      route_contact.subject_route.arrival_date_raws !=
          std::vector<std::int32_t>{43'823'128} ||
      g_route_edge_duration_calls != 1 || g_route_duration_calls != 0) {
    return Fail("one-edge zero-progress boundary invoked its absent tail");
  }

  // Do not disguise an active suffix whose second row repeats the current
  // front as a non-shared tail.  It remains unavailable.
  Store(g_boundary_move_route_info_1, 0x00, std::int32_t{4});
  Store(g_player_army, 0x40, std::int32_t{2});
  Store(g_player_army, 0x44, std::int32_t{2});
  g_route_duration_calls = 0;
  g_route_edge_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_contact.subject_route.timeline_observable ||
      g_route_duration_calls != 0) {
    return Fail("repeated active front was treated as a non-shared tail");
  }

  // Once any distance has been travelled, zero current-edge speed is a real
  // timing ambiguity.  The boundary fallback must remain closed.
  Store(g_boundary_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_player_army, 0x40, std::int32_t{4});
  Store(g_player_army, 0x44, std::int32_t{4});
  Store(g_player_army, 0x168, std::int64_t{1});
  route_contact_request.target_province_id = 2;
  g_route_duration_calls = 0;
  g_route_edge_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_contact.subject_route.timeline_observable ||
      route_contact.timeline_failure.role !=
          xar::game::RouteContactTimelineFailureRole::subject ||
      route_contact.timeline_failure.army_id != player_army_id ||
      route_contact.timeline_failure.path_kind !=
          xar::game::RouteContactTimelinePathKind::committed_active ||
      route_contact.timeline_failure.stage !=
          xar::game::RouteContactTimelineFailureStage::current_edge_speed ||
      g_route_edge_duration_calls != 0 || g_route_duration_calls != 0) {
    return Fail("progressed route accepted a zero current-edge speed");
  }

  // Exercise the real typed executor reset path, not just the direct reader:
  // unavailable business data is cleared, while the first attributed
  // timeline failure must survive for the worker's bounded error detail.
  xar::ck3_11906::MainThreadQueryMailboxV1 route_failure_mailbox{};
  xar::ck3_11906::RouteContactHorizonMailboxContextV1 route_failure_query{};
  route_failure_query.mailbox = &route_failure_mailbox;
  route_failure_query.ticket.sequence = 1;
  route_failure_query.bindings = bindings;
  route_failure_query.request = route_contact_request;
  const auto fixture_thread_id = GetCurrentThreadId();
  route_failure_mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  route_failure_mailbox.published_sequence.store(1);
  route_failure_mailbox.owner_thread_id.store(fixture_thread_id);
  route_failure_mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  route_failure_mailbox.executor =
      &xar::ck3_11906::ExecuteRouteContactHorizonMailboxQueryV1;
  route_failure_mailbox.executor_context = &route_failure_query;
  xar::ck3_11906::MainThreadExecutionStampV1 route_failure_stamp{};
  route_failure_stamp.pump_epoch = 1;
  route_failure_stamp.thread_id = fixture_thread_id;
  route_failure_stamp.tls_initialized_flag_address = 1;
  route_failure_stamp.tls_initialized = 1;
  route_failure_stamp.tls_context = 1;
  route_failure_stamp.tls_main_thread_marker = 1;
  route_failure_stamp.jomini_state = 1;
  route_failure_stamp.game_state = 1;
  route_failure_stamp.date_raw = 43'823'104;
  route_failure_stamp.paused = true;
  if (!xar::ck3_11906::ExecuteRouteContactHorizonMailboxQueryV1(
          &route_failure_query, route_failure_stamp) ||
      route_failure_query.completion !=
          xar::ck3_11906::RouteContactHorizonMailboxCompletionV1::
              query_unavailable ||
      route_failure_query.result.status !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_failure_query.result.subject_army_id != -1 ||
      !route_failure_query.result.hostile_army_ids.empty() ||
      route_failure_query.result.subject_route.timeline_observable ||
      !route_failure_query.result.hostile_routes.empty() ||
      route_failure_query.result.timeline_failure.role !=
          xar::game::RouteContactTimelineFailureRole::subject ||
      route_failure_query.result.timeline_failure.army_id != player_army_id ||
      route_failure_query.result.timeline_failure.path_kind !=
          xar::game::RouteContactTimelinePathKind::committed_active ||
      route_failure_query.result.timeline_failure.stage !=
          xar::game::RouteContactTimelineFailureStage::current_edge_speed ||
      xar::ck3_11906::RouteContactHorizonFailureDetailV1(
          RouteWait::completed, RouteCompletion::query_unavailable,
          route_failure_query.result, false) !=
          "CK3 route arrival timeline is unavailable (role=subject, "
          "army_id=16777217, path=committed_active, "
          "stage=current_edge_speed)") {
    return Fail("route-contact mailbox erased timeline failure provenance");
  }

  Store(g_player_army, 0x38,
        static_cast<void *>(g_player_move_path.data()));
  Store(g_player_army, 0x40, std::int32_t{3});
  Store(g_player_army, 0x44, std::int32_t{3});
  Store(g_player_army, 0x168, std::int64_t{0});
  Store(g_player_army, 0x190, std::int64_t{100'000});
  g_route_current_edge_speed_raw = 100'000;
  g_route_edge_duration_raw = 150'000;
  g_route_duration_zero_current_edge_correction = false;
  route_contact_request.target_province_id = 3;

  // The native duration helper silently skips an unresolvable adjacency.
  // Reject the complete route before making any timing ABI call, including
  // when the missing edge is later than an otherwise valid first segment.
  Store(g_route_adjacencies_4, 0x04, std::int32_t{99});
  g_route_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_contact.subject_route.timeline_observable ||
      g_route_duration_calls != 0) {
    return Fail("route timing called the ABI with a missing later adjacency");
  }
  Store(g_route_adjacencies_4, 0x04, std::int32_t{5});

  // A later zero-speed edge contributes uint32 0xffffffff to the already
  // accumulated Q100000 duration, so the final value is not the bare sentinel
  // and used to pass the range/monotonic checks.  Model land->water->water:
  // embark is fixed-cost, but the second segment requires positive naval
  // speed and must fail before the duration ABI can return that sum.
  Store(g_player_move_route_info_0, 0x09, std::uint8_t{0});
  Store(g_player_move_route_info_0, 0x0B, std::uint8_t{1});
  Store(g_player_move_route_info_1, 0x09, std::uint8_t{0});
  Store(g_player_move_route_info_1, 0x0B, std::uint8_t{1});
  g_route_naval_speed_raw = 0;
  g_route_duration_late_zero_speed_accumulation = true;
  g_route_duration_calls = 0;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_contact.subject_route.timeline_observable ||
      g_route_duration_calls != 0) {
    return Fail("route timing accepted a later zero-speed accumulated value");
  }
  Store(g_player_move_route_info_0, 0x09, std::uint8_t{1});
  Store(g_player_move_route_info_0, 0x0B, std::uint8_t{0});
  Store(g_player_move_route_info_1, 0x09, std::uint8_t{1});
  Store(g_player_move_route_info_1, 0x0B, std::uint8_t{0});
  g_route_naval_speed_raw = 100'000;
  g_route_duration_late_zero_speed_accumulation = false;

  // At the one-day boundary, entering a Province occupied by a hostile is
  // conservatively contact even though normal occupancy is [enter, leave).
  Store(g_player_move_route_info_2, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{3});
  g_preview_route_count = 1;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.one_day_contact_free ||
      route_contact.conflicts.size() != 1 ||
      route_contact.conflicts[0].kind != "same_province" ||
      route_contact.conflicts[0].hostile_army_id != enemy_army_id ||
      route_contact.conflicts[0].province_id != 3 ||
      route_contact.conflicts[0].overlap_start_date_raw != 43'823'128 ||
      route_contact.conflicts[0].overlap_end_date_raw != 43'823'128) {
    return Fail("route-contact did not close the exact arrival boundary");
  }

  // Simultaneous reverse traversal is contact as well; exact-boundary
  // occupancy conflicts may coexist with the explicit opposing-edge row.
  Store(g_enemy_move_route_info_0, 0x00, std::int32_t{2});
  g_enemy_move_path = {g_enemy_move_route_info_0.data()};
  Store(g_enemy_army, 0x38,
        static_cast<void *>(g_enemy_move_path.data()));
  Store(g_enemy_army, 0x40, std::int32_t{1});
  Store(g_enemy_army, 0x44, std::int32_t{1});
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.one_day_contact_free ||
      std::none_of(
          route_contact.conflicts.begin(), route_contact.conflicts.end(),
          [enemy_army_id](
              const xar::game::RouteContactConflictSnapshot &conflict) {
            return conflict.kind == "opposing_edge" &&
                   conflict.hostile_army_id == enemy_army_id &&
                   conflict.subject_from_province_id == 2 &&
                   conflict.subject_to_province_id == 3 &&
                   conflict.hostile_from_province_id == 3 &&
                   conflict.hostile_to_province_id == 2 &&
                   conflict.overlap_start_date_raw == 43'823'104 &&
                   conflict.overlap_end_date_raw == 43'823'128;
          })) {
    return Fail("route-contact omitted simultaneous opposing-edge contact");
  }
  Store(g_enemy_army, 0x38, static_cast<void *>(nullptr));
  Store(g_enemy_army, 0x40, std::int32_t{0});
  Store(g_enemy_army, 0x44, std::int32_t{0});

  // Mid-edge replanning first accounts for the committed active edge, then
  // adds each candidate-tail duration before doing canonical day rounding.
  g_route_duration_calls = 0;
  g_preview_effective_origin = g_enemy_default_raise_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{2});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{3});
  g_preview_route_count = 2;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::available ||
      route_contact.subject_route.effective_origin_province_id != 4 ||
      route_contact.subject_route.route_province_ids !=
          std::vector<std::int32_t>{4, 2, 3} ||
      route_contact.subject_route.arrival_date_raws !=
          std::vector<std::int32_t>{43'823'128, 43'823'152,
                                    43'823'176}) {
    return Fail("mid-edge route timeline omitted committed-edge duration");
  }

  g_preview_effective_origin = g_player_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{3});
  g_preview_route_count = 1;
  g_route_duration_failure = true;
  route_contact = {};
  if (xar::ck3_11906::ReadRouteContactHorizon(
          bindings, route_contact_request, route_contact) !=
          xar::game::RouteContactHorizonStatus::timeline_unavailable ||
      route_contact.subject_route.timeline_observable) {
    return Fail("route timing accepted the native 0xffffffff failure value");
  }
  g_route_duration_failure = false;
  g_preview_effective_origin = g_player_province.data();
  Store(g_preview_move_route_info_0, 0x00, std::int32_t{4});
  Store(g_preview_move_route_info_1, 0x00, std::int32_t{5});
  Store(g_preview_move_route_info_2, 0x00, std::int32_t{3});
  g_preview_route_count = 3;
  g_enemy_army_state_code = 6;
  Store(g_enemy_army, 0x170, std::int32_t{1});
  g_player_army_state_code = 2;
  g_move_mode_result = 5;
  Store(jomini_state, 0x20, std::uint8_t{0});

  g_expected_command = ExpectedCommand::move_army;
  g_submit_called = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::submitted ||
      !g_move_path_initialized || !g_submit_called ||
      !g_move_destroy_called) {
    return Fail("move-army did not use the native mode/path/queue layout");
  }
  g_move_mode_result = 2;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::move_mode_unavailable ||
      g_submit_called) {
    return Fail("move-army did not expose native move-mode rejection");
  }
  g_move_mode_result = 5;
  g_character_command_kind_allowed = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::character_state_rejected ||
      g_submit_called) {
    return Fail("move-army did not expose native character-state rejection");
  }
  g_character_command_kind_allowed = true;
  g_army_move_mode_allowed = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::army_state_rejected ||
      g_submit_called) {
    return Fail("move-army did not expose native army-state rejection");
  }
  g_army_move_mode_allowed = true;
  g_move_validation_allowed = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::validation_failed ||
      g_submit_called) {
    return Fail("move-army did not expose native command validation failure");
  }
  g_move_validation_allowed = true;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, enemy_army_id, 2) !=
          xar::ck3_11906::MoveArmyResult::army_not_controllable ||
      xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 99) !=
          xar::ck3_11906::MoveArmyResult::province_not_found ||
      g_submit_called) {
    return Fail("move-army ignored controllability or province resolution");
  }

  g_expected_command = ExpectedCommand::disband_army;
  g_submit_called = false;
  g_disband_validate_called = false;
  g_disband_validate_result = true;
  if (xar::ck3_11906::SubmitDisbandArmy(bindings, player_army_id) !=
          xar::ck3_11906::DisbandArmyResult::submitted ||
      !g_disband_validate_called || !g_submit_called) {
    return Fail("disband-army did not validate and submit the player command");
  }
  g_submit_called = false;
  g_disband_validate_called = false;
  g_disband_validate_result = false;
  if (xar::ck3_11906::SubmitDisbandArmy(bindings, player_army_id) !=
          xar::ck3_11906::DisbandArmyResult::army_not_controllable ||
      !g_disband_validate_called || g_submit_called) {
    return Fail("disband-army queued a command rejected by CK3 validation");
  }
  g_disband_validate_result = true;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDisbandArmy(bindings, enemy_army_id) !=
          xar::ck3_11906::DisbandArmyResult::army_not_controllable ||
      g_submit_called) {
    return Fail("disband-army accepted a non-player army");
  }

  g_expected_command = ExpectedCommand::split_army_half;
  g_submit_called = false;
  g_split_validate_called = false;
  g_split_validate_result = true;
  g_split_clone_called = false;
  g_split_destroy_called = false;
  g_split_cloned_command.fill(std::byte{0});
  if (xar::ck3_11906::SubmitSplitArmyHalf(bindings, player_army_id) !=
          xar::ck3_11906::SplitArmyHalfResult::split_submitted ||
      !g_split_validate_called || !g_submit_called ||
      !g_split_clone_called || !g_split_destroy_called) {
    return Fail("split-army-half did not validate, clone, queue, and destroy");
  }
  std::uintptr_t split_clone_primary = 0;
  std::uintptr_t split_clone_secondary = 0;
  std::int32_t split_clone_kind = -1;
  std::int32_t split_clone_actor_id = -1;
  std::int32_t split_clone_source_army_id = -1;
  std::memcpy(&split_clone_primary, g_split_cloned_command.data() + 0x00,
              sizeof(split_clone_primary));
  std::memcpy(&split_clone_secondary, g_split_cloned_command.data() + 0x18,
              sizeof(split_clone_secondary));
  std::memcpy(&split_clone_kind, g_split_cloned_command.data() + 0x20,
              sizeof(split_clone_kind));
  std::memcpy(&split_clone_actor_id, g_split_cloned_command.data() + 0x24,
              sizeof(split_clone_actor_id));
  std::memcpy(&split_clone_source_army_id,
              g_split_cloned_command.data() + 0x28,
              sizeof(split_clone_source_army_id));
  if (split_clone_primary != 0x15151515 ||
      split_clone_secondary != 0x16161616 || split_clone_kind != 1 ||
      split_clone_actor_id != played_character_id ||
      split_clone_source_army_id != player_internal_army_id) {
    return Fail("split-army-half clone lost the public-to-internal ID payload");
  }

  // Queue submission is the complete synchronous bridge result. The fixture
  // intentionally does not execute CK3's cloned command, so the adapter must
  // not fabricate a sibling CUnit or claim a split postcondition.
  xar::ck3_11906::Snapshot post_split_submission{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, post_split_submission) ||
      post_split_submission.player_armies.size() != 1 ||
      post_split_submission.player_armies[0].army_id != player_army_id) {
    return Fail("split submission guessed a sibling CUnit postcondition");
  }

  g_submit_called = false;
  g_submit_result = false;
  g_split_validate_called = false;
  g_split_clone_called = false;
  g_split_destroy_called = false;
  if (xar::ck3_11906::SubmitSplitArmyHalf(bindings, player_army_id) !=
          xar::ck3_11906::SplitArmyHalfResult::submission_failed ||
      !g_split_validate_called || !g_submit_called ||
      !g_split_clone_called || !g_split_destroy_called) {
    return Fail("split-army-half hid queue rejection or leaked its original");
  }
  g_submit_result = true;

  g_submit_called = false;
  g_split_validate_called = false;
  g_split_validate_result = false;
  g_split_clone_called = false;
  g_split_destroy_called = false;
  if (xar::ck3_11906::SubmitSplitArmyHalf(bindings, player_army_id) !=
          xar::ck3_11906::SplitArmyHalfResult::validator_rejected ||
      !g_split_validate_called || g_submit_called || g_split_clone_called ||
      g_split_destroy_called) {
    return Fail("split-army-half queued a command rejected by CK3 validation");
  }
  g_split_validate_result = true;
  g_split_validate_called = false;
  if (xar::ck3_11906::SubmitSplitArmyHalf(bindings, enemy_army_id) !=
          xar::ck3_11906::SplitArmyHalfResult::army_not_controllable ||
      g_split_validate_called || g_submit_called) {
    return Fail("split-army-half accepted a non-player army");
  }
  if (xar::ck3_11906::SubmitSplitArmyHalf(bindings, 0x02000001) !=
          xar::ck3_11906::SplitArmyHalfResult::army_not_found ||
      g_split_validate_called || g_submit_called) {
    return Fail("split-army-half ignored the public CUnit generation");
  }

  // Reuse the second generation-valid CUnit as a second player army only for
  // this slice. The public IDs stay distinct while owner/province/state are
  // made compatible; CK3's complete validator remains the authority for all
  // merge gates.
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_enemy_army, 0x170, std::int32_t{0});
  Store(g_enemy_army, 0x174, played_character_id);
  g_player_army_state_code = 3;
  g_enemy_army_state_code = 3;

  g_expected_command = ExpectedCommand::merge_armies;
  g_submit_called = false;
  g_merge_factory_called = false;
  g_merge_append_called = false;
  g_merge_validate_called = false;
  g_merge_validate_result = true;
  g_merge_clone_called = false;
  g_merge_destroy_called = false;
  g_merge_source_array_destroyed = false;
  g_merge_cloned_destination_id = -1;
  g_merge_cloned_source_ids.fill(-1);
  if (xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, enemy_army_id) !=
          xar::ck3_11906::MergeArmiesResult::merge_submitted ||
      !g_merge_factory_called || !g_merge_append_called ||
      !g_merge_validate_called || !g_submit_called ||
      !g_merge_clone_called || !g_merge_destroy_called ||
      !g_merge_source_array_destroyed ||
      g_merge_factory_command != nullptr ||
      g_merge_owned_source_ids != nullptr ||
      g_merge_cloned_destination_id != player_army_id ||
      g_merge_cloned_source_ids[0] != enemy_army_id) {
    return Fail("merge-armies did not deep-copy, validate, queue, and clean up");
  }

  // Submission alone does not execute the fixture's queued clone. Its owned
  // source copy survives original cleanup, while the current snapshot still
  // contains both public CUnit IDs until an executor/postcondition observes
  // the source disappear.
  xar::ck3_11906::Snapshot post_merge_submission{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, post_merge_submission) ||
      post_merge_submission.player_armies.size() != 2 ||
      post_merge_submission.player_armies[0].army_id != player_army_id ||
      post_merge_submission.player_armies[1].army_id != enemy_army_id ||
      g_merge_cloned_source_ids[0] != enemy_army_id) {
    return Fail("merge submission fabricated an immediate source postcondition");
  }

  g_submit_called = false;
  g_submit_result = false;
  g_merge_factory_called = false;
  g_merge_append_called = false;
  g_merge_validate_called = false;
  g_merge_clone_called = false;
  g_merge_destroy_called = false;
  g_merge_source_array_destroyed = false;
  if (xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, enemy_army_id) !=
          xar::ck3_11906::MergeArmiesResult::submission_failed ||
      !g_merge_factory_called || !g_merge_append_called ||
      !g_merge_validate_called || !g_submit_called ||
      !g_merge_clone_called || !g_merge_destroy_called ||
      !g_merge_source_array_destroyed ||
      g_merge_factory_command != nullptr ||
      g_merge_owned_source_ids != nullptr) {
    return Fail("merge-armies hid queue rejection or leaked its original");
  }
  g_submit_result = true;

  g_submit_called = false;
  g_merge_factory_called = false;
  g_merge_append_called = false;
  g_merge_validate_called = false;
  g_merge_validate_result = false;
  g_merge_clone_called = false;
  g_merge_destroy_called = false;
  g_merge_source_array_destroyed = false;
  if (xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, enemy_army_id) !=
          xar::ck3_11906::MergeArmiesResult::validator_rejected ||
      !g_merge_factory_called || !g_merge_append_called ||
      !g_merge_validate_called || g_submit_called || g_merge_clone_called ||
      !g_merge_destroy_called || !g_merge_source_array_destroyed ||
      g_merge_factory_command != nullptr ||
      g_merge_owned_source_ids != nullptr) {
    return Fail("merge-armies leaked or queued after validator rejection");
  }
  g_merge_validate_result = true;

  g_merge_factory_called = false;
  g_merge_validate_called = false;
  if (xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, player_army_id) !=
          xar::ck3_11906::MergeArmiesResult::same_army ||
      g_merge_factory_called || g_merge_validate_called) {
    return Fail("merge-armies accepted identical public CUnit IDs");
  }

  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x170, std::int32_t{1});
  Store(g_enemy_army, 0x174, enemy_character_id);
  g_player_army_state_code = 2;
  g_enemy_army_state_code = 6;
  if (xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, enemy_army_id) !=
          xar::ck3_11906::MergeArmiesResult::source_not_controllable ||
      xar::ck3_11906::SubmitMergeArmies(
          bindings, enemy_army_id, player_army_id) !=
          xar::ck3_11906::MergeArmiesResult::destination_not_controllable ||
      xar::ck3_11906::SubmitMergeArmies(
          bindings, 0x02000001, player_army_id) !=
          xar::ck3_11906::MergeArmiesResult::destination_not_found ||
      xar::ck3_11906::SubmitMergeArmies(
          bindings, player_army_id, 0x02000002) !=
          xar::ck3_11906::MergeArmiesResult::source_not_found ||
      g_merge_factory_called || g_merge_validate_called) {
    return Fail("merge-armies ignored generation or controllability gates");
  }

  Store(g_siege, 0x3D8, std::int32_t{1});
  Store(g_siege, 0x44C, std::uint8_t{0});
  g_expected_command = ExpectedCommand::start_assault;
  g_submit_called = false;
  g_submit_result = true;
  g_start_assault_validate_allowed = true;
  g_start_assault_validate_called = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  g_assault_cloned_command.fill(std::byte{0});
  if (xar::ck3_11906::SubmitStartAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StartAssaultResult::start_submitted ||
      !g_start_assault_validate_called || !g_submit_called ||
      !g_assault_clone_called || !g_assault_destroy_called) {
    return Fail("start-assault did not validate, clone, queue, and destroy");
  }
  std::uintptr_t assault_clone_primary = 0;
  std::uintptr_t assault_clone_secondary = 0;
  std::int32_t assault_clone_kind = -1;
  std::int32_t assault_clone_actor = -1;
  std::int32_t assault_clone_siege = -1;
  std::memcpy(&assault_clone_primary,
              g_assault_cloned_command.data() + 0x00,
              sizeof(assault_clone_primary));
  std::memcpy(&assault_clone_secondary,
              g_assault_cloned_command.data() + 0x18,
              sizeof(assault_clone_secondary));
  std::memcpy(&assault_clone_kind,
              g_assault_cloned_command.data() + 0x20,
              sizeof(assault_clone_kind));
  std::memcpy(&assault_clone_actor,
              g_assault_cloned_command.data() + 0x24,
              sizeof(assault_clone_actor));
  std::memcpy(&assault_clone_siege,
              g_assault_cloned_command.data() + 0x28,
              sizeof(assault_clone_siege));
  if (assault_clone_primary != 0x1A1A1A1A ||
      assault_clone_secondary != 0x1B1B1B1B ||
      assault_clone_kind != 1 ||
      assault_clone_actor != played_character_id ||
      assault_clone_siege != active_siege_id) {
    return Fail("start-assault clone lost its exact native payload");
  }
  // Queue acceptance does not execute the fixture clone or fabricate the
  // Start postcondition in the same snapshot.
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars[0]
          .objective_province_states[0]
          .assault_in_progress) {
    return Fail("start-assault ACK fabricated an applied postcondition");
  }

  g_submit_called = false;
  g_submit_result = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  if (xar::ck3_11906::SubmitStartAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StartAssaultResult::submission_failed ||
      !g_submit_called || !g_assault_clone_called ||
      !g_assault_destroy_called) {
    return Fail("start-assault hid queue rejection or leaked its original");
  }
  g_submit_result = true;
  g_submit_called = false;
  g_start_assault_validate_allowed = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  if (xar::ck3_11906::SubmitStartAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StartAssaultResult::validator_rejected ||
      g_submit_called || g_assault_clone_called || g_assault_destroy_called) {
    return Fail("start-assault queued after complete validator rejection");
  }
  g_start_assault_validate_allowed = true;
  if (xar::ck3_11906::SubmitStartAssault(bindings, 0x02000001) !=
      xar::ck3_11906::StartAssaultResult::siege_not_found) {
    return Fail("start-assault ignored the full SiegeID generation");
  }
  Store(g_war_objective_province, 0x790, std::int32_t{-1});
  if (xar::ck3_11906::SubmitStartAssault(bindings, active_siege_id) !=
      xar::ck3_11906::StartAssaultResult::siege_not_found) {
    return Fail("start-assault ignored the Province/Siege backlink");
  }
  Store(g_war_objective_province, 0x790, active_siege_id);

  Store(g_siege, 0x44C, std::uint8_t{1});
  if (xar::ck3_11906::SubmitStartAssault(bindings, active_siege_id) !=
      xar::ck3_11906::StartAssaultResult::assault_already_active) {
    return Fail("start-assault did not report an already-active siege");
  }
  g_expected_command = ExpectedCommand::stop_assault;
  g_submit_called = false;
  g_stop_assault_validate_allowed = true;
  g_stop_assault_validate_called = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  g_assault_cloned_command.fill(std::byte{0});
  if (xar::ck3_11906::SubmitStopAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StopAssaultResult::stop_submitted ||
      !g_stop_assault_validate_called || !g_submit_called ||
      !g_assault_clone_called || !g_assault_destroy_called) {
    return Fail("stop-assault did not validate, clone, queue, and destroy");
  }
  std::memcpy(&assault_clone_primary,
              g_assault_cloned_command.data() + 0x00,
              sizeof(assault_clone_primary));
  std::memcpy(&assault_clone_secondary,
              g_assault_cloned_command.data() + 0x18,
              sizeof(assault_clone_secondary));
  if (assault_clone_primary != 0x1C1C1C1C ||
      assault_clone_secondary != 0x1D1D1D1D) {
    return Fail("stop-assault clone used the Start command class");
  }

  g_submit_called = false;
  g_submit_result = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  if (xar::ck3_11906::SubmitStopAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StopAssaultResult::submission_failed ||
      !g_submit_called || !g_assault_clone_called ||
      !g_assault_destroy_called) {
    return Fail("stop-assault hid queue rejection or leaked its original");
  }
  g_submit_result = true;
  g_submit_called = false;
  g_stop_assault_validate_allowed = false;
  g_assault_clone_called = false;
  g_assault_destroy_called = false;
  if (xar::ck3_11906::SubmitStopAssault(bindings, active_siege_id) !=
          xar::ck3_11906::StopAssaultResult::validator_rejected ||
      g_submit_called || g_assault_clone_called || g_assault_destroy_called) {
    return Fail("stop-assault queued after complete validator rejection");
  }
  g_stop_assault_validate_allowed = true;
  Store(g_siege, 0x44C, std::uint8_t{0});
  if (xar::ck3_11906::SubmitStopAssault(bindings, active_siege_id) !=
      xar::ck3_11906::StopAssaultResult::assault_not_active) {
    return Fail("stop-assault did not report an inactive siege");
  }
  if (xar::ck3_11906::SubmitStopAssault(bindings, 0x02000001) !=
      xar::ck3_11906::StopAssaultResult::siege_not_found) {
    return Fail("stop-assault ignored the full SiegeID generation");
  }

  g_casus_belli_evaluation_calls = 0;
  std::vector<xar::ck3_11906::DeclarableWarSnapshot> declarations;
  if (xar::ck3_11906::ReadDeclarableWarsForTarget(
          bindings, enemy_character_id, declarations) !=
          xar::ck3_11906::ReadDeclarableWarsResult::available ||
      g_casus_belli_evaluation_calls != 2 ||
      declarations.size() != 3 ||
      declarations[0].target_character_id != enemy_character_id ||
      declarations[0].casus_belli_index != 0 ||
      declarations[0].casus_belli_key != g_casus_belli_key_0 ||
      declarations[0].configuration_index != 0 ||
      declarations[0].claimant_character_id != 0x01000004 ||
      declarations[0].target_title_ids != std::vector<std::int32_t>{101} ||
      declarations[1].casus_belli_index != 0 ||
      declarations[1].casus_belli_key != g_casus_belli_key_0 ||
      declarations[1].configuration_index != 1 ||
      declarations[1].claimant_character_id != 0x01000005 ||
      declarations[1].target_title_ids !=
          (std::vector<std::int32_t>{102, 103}) ||
      declarations[2].casus_belli_index != 1 ||
      declarations[2].casus_belli_key != g_casus_belli_key_1 ||
      declarations[2].configuration_index != -1 ||
      declarations[2].claimant_character_id != -1 ||
      declarations[2].target_title_ids !=
          (std::vector<std::int32_t>{201, 202})) {
    return Fail("target-scoped native CB enumeration did not stay at one CB database pass");
  }
  std::vector<xar::ck3_11906::DeclarableWarSnapshot> global_declarations;
  if (!xar::ck3_11906::ReadDeclarableWars(bindings,
                                          global_declarations) ||
      global_declarations != declarations) {
    return Fail("global declaration scan did not retain exact target choices");
  }
  std::vector<xar::ck3_11906::DeclarableWarSnapshot> missing_declarations;
  if (xar::ck3_11906::ReadDeclarableWarsForTarget(
          bindings, 0x01000009, missing_declarations) !=
          xar::ck3_11906::ReadDeclarableWarsResult::target_not_found ||
      !missing_declarations.empty()) {
    return Fail("missing declaration target was not rejected explicitly");
  }

  auto stale_declaration = declarations[1];
  stale_declaration.target_title_ids[0] = 999;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDeclareWar(bindings, stale_declaration) !=
          xar::ck3_11906::DeclareWarResult::declaration_unavailable ||
      g_submit_called) {
    return Fail("stale declaration tuple was not rejected on re-enumeration");
  }

  g_interaction_validate_result = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDeclareWar(bindings, declarations[2]) !=
          xar::ck3_11906::DeclareWarResult::validation_failed ||
      g_submit_called || g_interaction_destroy_calls != 1 ||
      g_war_declaration_titles[0] != 201 ||
      g_war_declaration_titles[1] != 202) {
    return Fail("combined declaration did not use native append/validation");
  }
  g_interaction_validate_result = true;

  g_expected_command = ExpectedCommand::declare_war;
  g_interaction_construct_called = false;
  g_interaction_refresh_called = false;
  g_interaction_finalize_called = false;
  g_send_interaction_construct_called = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDeclareWar(bindings, declarations[1]) !=
          xar::ck3_11906::DeclareWarResult::submitted ||
      !g_interaction_construct_called || !g_interaction_refresh_called ||
      !g_interaction_finalize_called ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2) {
    return Fail("declare-war did not use native context/validate/queue lifecycle");
  }

  std::vector<xar::ck3_11906::ArrangeMarriageChoice> marriage_choices;
  xar::ck3_11906::ArrangeMarriageQueryDiagnostics marriage_diagnostics{};
  g_marriage_context_construct_calls = 0;
  g_marriage_redirect_calls = 0;
  g_marriage_legacy_context_construct_calls = 0;
  g_marriage_redirect_ready = false;
  g_interaction_refresh_called = false;
  g_interaction_finalize_called = false;
  g_interaction_destroy_calls = 0;
  if (xar::ck3_11906::ReadArrangeMarriageChoices(
          bindings, marriage_choices, marriage_diagnostics) !=
          xar::ck3_11906::ReadArrangeMarriageChoicesResult::available ||
      marriage_choices.size() != 1 ||
      marriage_choices[0].played_character_id != played_character_id ||
      marriage_choices[0].candidate_character_id != enemy_character_id ||
      g_marriage_redirect_calls != 1 ||
      g_marriage_context_construct_calls != 1 ||
      g_marriage_legacy_context_construct_calls != 0 ||
      !g_interaction_refresh_called || !g_interaction_finalize_called ||
      g_interaction_destroy_calls != 1 ||
      marriage_diagnostics.storage_capacity != 6 ||
      marriage_diagnostics.slots_scanned != 6 ||
      marriage_diagnostics.empty_slots != 2 ||
      marriage_diagnostics.self_candidates != 1 ||
      marriage_diagnostics.dead_candidates != 1 ||
      marriage_diagnostics.generation_mismatch_candidates != 1 ||
      marriage_diagnostics.live_candidates != 1 ||
      marriage_diagnostics.contexts_constructed != 1 ||
      marriage_diagnostics.context_construct_failures != 0 ||
      marriage_diagnostics.native_validate_true != 1 ||
      marriage_diagnostics.native_validate_false != 0 ||
      !marriage_diagnostics.validation_false_samples.empty()) {
    return Fail("arrange-marriage query did not retain the exact valid pair");
  }

  g_marriage_validate_result = false;
  std::vector<xar::ck3_11906::ArrangeMarriageChoice>
      rejected_marriage_choices;
  xar::ck3_11906::ArrangeMarriageQueryDiagnostics
      rejected_marriage_diagnostics{};
  if (xar::ck3_11906::ReadArrangeMarriageChoices(
          bindings, rejected_marriage_choices,
          rejected_marriage_diagnostics) !=
          xar::ck3_11906::ReadArrangeMarriageChoicesResult::available ||
      !rejected_marriage_choices.empty() ||
      rejected_marriage_diagnostics.contexts_constructed != 1 ||
      rejected_marriage_diagnostics.native_validate_true != 0 ||
      rejected_marriage_diagnostics.native_validate_false != 1 ||
      rejected_marriage_diagnostics.validation_false_samples.size() != 1) {
    return Fail("arrange-marriage query diagnostics lost validator failure");
  }
  const auto &validation_sample =
      rejected_marriage_diagnostics.validation_false_samples[0];
  if (validation_sample.slot_index != 3 ||
      validation_sample.candidate_character_id != enemy_character_id ||
      validation_sample.actor_character_id != played_character_id ||
      validation_sample.recipient_character_id !=
          kMarriageMatchmakerCharacterId ||
      validation_sample.secondary_actor_character_id !=
          played_character_id ||
      validation_sample.secondary_recipient_character_id !=
          enemy_character_id ||
      validation_sample.intermediary_character_id != -1) {
    return Fail("arrange-marriage query diagnostics lost redirected roles");
  }
  g_marriage_validate_result = true;

  auto stale_marriage_choice = marriage_choices[0];
  stale_marriage_choice.played_character_id = 0x02000002;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitArrangeMarriage(
          bindings, stale_marriage_choice) !=
          xar::ck3_11906::ArrangeMarriageResult::choice_unavailable ||
      g_submit_called) {
    return Fail("stale arrange-marriage actor generation was not rejected");
  }

  g_marriage_validate_result = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitArrangeMarriage(
          bindings, marriage_choices[0]) !=
          xar::ck3_11906::ArrangeMarriageResult::choice_unavailable ||
      g_submit_called || g_interaction_destroy_calls != 1) {
    return Fail("stale arrange-marriage choice bypassed native validation");
  }
  g_marriage_validate_result = true;

  g_expected_command = ExpectedCommand::arrange_marriage;
  g_marriage_context_construct_calls = 0;
  g_marriage_redirect_calls = 0;
  g_marriage_legacy_context_construct_calls = 0;
  g_marriage_redirect_ready = false;
  g_interaction_refresh_called = false;
  g_interaction_finalize_called = false;
  g_send_interaction_construct_called = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitArrangeMarriage(
          bindings, marriage_choices[0]) !=
          xar::ck3_11906::ArrangeMarriageResult::submitted ||
      g_marriage_redirect_calls != 1 ||
      g_marriage_context_construct_calls != 1 ||
      g_marriage_legacy_context_construct_calls != 0 ||
      !g_interaction_refresh_called || !g_interaction_finalize_called ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2) {
    return Fail("arrange-marriage did not use native context/queue lifecycle");
  }

  xar::ck3_11906::WarTerminationOptionsSnapshot termination_options{};
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
      xar::ck3_11906::ReadWarTerminationOptionsResult::requires_paused) {
    return Fail("war-termination query ran while the map was not paused");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});
  g_war_resolution_construct_calls = 0;
  g_white_peace_construct_calls = 0;
  g_auto_accept_trigger_calls = 0;
  g_interaction_destroy_calls = 0;
  g_exit_terms_answer_calls = 0;
  g_exit_terms_answer_destroy_counts.clear();
  g_send_interaction_construct_called = false;
  g_submit_called = false;
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
      xar::ck3_11906::ReadWarTerminationOptionsResult::available) {
    return Fail("war-termination query was unavailable");
  }
  if (g_exit_terms_answer_calls != 3 ||
      g_exit_terms_answer_destroy_counts !=
          std::vector<std::int32_t>{0, 1, 2}) {
    std::cerr << "answer calls=" << g_exit_terms_answer_calls
              << " destroy-counts=";
    for (const auto count : g_exit_terms_answer_destroy_counts) {
      std::cerr << count << ',';
    }
    std::cerr << '\n';
    return Fail("recipient response ran after native context teardown");
  }
  if (!termination_options.surrender.recipient_response.observable ||
      termination_options.surrender.recipient_response.decision_status_raw !=
          1 ||
      !termination_options.surrender.recipient_response.would_accept_now) {
    return Fail("surrender final recipient response was not typed");
  }
  if (!termination_options.white_peace.recipient_response.observable ||
      termination_options.white_peace.recipient_response
              .decision_status_raw != 0 ||
      !termination_options.white_peace.recipient_response.would_accept_now) {
    return Fail("white-peace final recipient response was not typed");
  }
  if (termination_options.victory.recipient_response.observable) {
    return Fail("invalid victory final recipient response was published");
  }
  if (
      termination_options.war_id != active_war_id ||
      termination_options.player_side !=
          xar::ck3_11906::PlayerWarSide::attacker ||
      !termination_options.player_is_primary_war_leader ||
      termination_options.player_relative_war_score != 37 ||
      !termination_options.war_duration_days_observable ||
      termination_options.war_duration_days != 10 ||
      !termination_options.absolute_war_scores_observable ||
      termination_options.attacker_war_score != 37 ||
      termination_options.defender_war_score != -37 ||
      !termination_options.war_score_breakdown.observable ||
      termination_options.war_score_breakdown.imprisonment != 4 ||
      termination_options.war_score_breakdown.battles != 11 ||
      termination_options.war_score_breakdown.occupation != 5 ||
      termination_options.war_score_breakdown.ticking != 5 ||
      !termination_options.active_casus_belli_observable ||
      !termination_options.active_casus_belli_present ||
      !termination_options.active_casus_belli_identity_observable ||
      termination_options.active_casus_belli_database_index != 0 ||
      termination_options.active_casus_belli_key != "claim_cb" ||
      !termination_options.white_peace_permission_observable ||
      !termination_options.cb_allows_white_peace ||
      termination_options.surrender.outcome != "attacker_defeat" ||
      !termination_options.surrender.context_constructed ||
      !termination_options.surrender.native_validator_observable ||
      !termination_options.surrender.native_validator_passed ||
      !termination_options.surrender.ai_acceptance_observable ||
      termination_options.surrender.ai_acceptance.raw != 10'000'000 ||
      termination_options.surrender.ai_acceptance.scale != 100'000 ||
      !termination_options.surrender.auto_accept_observable ||
      !termination_options.surrender.auto_accept ||
      termination_options.white_peace.outcome != "white_peace" ||
      !termination_options.white_peace.context_constructed ||
      !termination_options.white_peace.native_validator_passed ||
      !termination_options.white_peace.ai_acceptance_observable ||
      termination_options.white_peace.ai_acceptance.raw != -2'500'000 ||
      !termination_options.white_peace.auto_accept_observable ||
      termination_options.white_peace.auto_accept ||
      termination_options.victory.outcome != "attacker_victory" ||
      !termination_options.victory.context_constructed ||
      !termination_options.victory.native_validator_passed ||
      !termination_options.victory.ai_acceptance_observable ||
      termination_options.victory.ai_acceptance.raw != 3'700'000 ||
      !termination_options.victory.auto_accept_observable ||
      !termination_options.victory.auto_accept ||
      g_war_resolution_construct_calls != 2 ||
      g_war_resolution_absolute_outcomes[0] ||
      !g_war_resolution_absolute_outcomes[1] ||
      g_white_peace_construct_calls != 1 ||
      g_auto_accept_trigger_calls != 2 ||
      g_interaction_destroy_calls != 3 ||
      g_send_interaction_construct_called || g_submit_called) {
    return Fail("war-termination query lost paused native result contexts");
  }

  // A positive ai_acceptance diagnostic is not the final answer.  Status 2
  // is an exact rejection and must remain false even for the +100 surrender
  // score in this fixture.
  g_exit_terms_answer_status_override = 2;
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
          xar::ck3_11906::ReadWarTerminationOptionsResult::available ||
      termination_options.surrender.ai_acceptance.raw != 10'000'000 ||
      !termination_options.surrender.recipient_response.observable ||
      termination_options.surrender.recipient_response.decision_status_raw !=
          2 ||
      termination_options.surrender.recipient_response.would_accept_now) {
    return Fail("war-termination final rejection was inferred from raw score");
  }
  g_exit_terms_answer_status_override = 0xFF;

  // Validator-false contexts keep the overall options query available but
  // publish an explicit unavailable recipient response.
  g_interaction_validate_result = false;
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
          xar::ck3_11906::ReadWarTerminationOptionsResult::available ||
      termination_options.surrender.recipient_response.observable ||
      termination_options.white_peace.recipient_response.observable ||
      termination_options.victory.recipient_response.observable) {
    return Fail("validator rejection made recipient response look available");
  }
  g_interaction_validate_result = true;

  Store(g_casus_belli_type_0, 0x1718, std::uint32_t{0});
  g_war_resolution_construct_calls = 0;
  g_white_peace_construct_calls = 0;
  g_interaction_destroy_calls = 0;
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
          xar::ck3_11906::ReadWarTerminationOptionsResult::available ||
      termination_options.cb_allows_white_peace ||
      termination_options.white_peace.context_constructed ||
      termination_options.white_peace.native_validator_observable ||
      g_war_resolution_construct_calls != 2 ||
      g_white_peace_construct_calls != 0 ||
      g_interaction_destroy_calls != 2) {
    return Fail("war-termination query fabricated forbidden white peace");
  }
  Store(g_casus_belli_type_0, 0x1718, std::uint32_t{1U << 7U});

  Store(g_war, 0x288, enemy_character_id);
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
          xar::ck3_11906::ReadWarTerminationOptionsResult::available ||
      termination_options.player_is_primary_war_leader ||
      termination_options.surrender.context_constructed ||
      termination_options.white_peace.context_constructed ||
      termination_options.victory.context_constructed) {
    return Fail("war-termination query gave a non-leader result contexts");
  }
  Store(g_war, 0x288, played_character_id);

  Store(g_attacker_participant, 0x08, enemy_character_id);
  Store(g_defender_participant, 0x08, played_character_id);
  Store(g_war, 0x288, enemy_character_id);
  Store(g_war, 0x28C, played_character_id);
  g_war_score_result = 0;
  g_war_resolution_construct_calls = 0;
  g_white_peace_construct_calls = 0;
  if (xar::ck3_11906::ReadWarTerminationOptions(
          bindings, active_war_id, termination_options) !=
          xar::ck3_11906::ReadWarTerminationOptionsResult::available ||
      termination_options.player_side !=
          xar::ck3_11906::PlayerWarSide::defender ||
      termination_options.player_relative_war_score != 0 ||
      termination_options.attacker_war_score != 0 ||
      termination_options.defender_war_score != 0 ||
      termination_options.surrender.outcome != "attacker_victory" ||
      !termination_options.surrender.context_constructed ||
      !termination_options.surrender.ai_acceptance_observable ||
      termination_options.surrender.ai_acceptance.raw != 10'000'000 ||
      !termination_options.surrender.recipient_response.observable ||
      !termination_options.surrender.recipient_response.would_accept_now ||
      termination_options.victory.outcome != "attacker_defeat" ||
      !termination_options.victory.context_constructed ||
      !termination_options.victory.ai_acceptance_observable ||
      termination_options.victory.ai_acceptance.raw != 3'700'000 ||
      termination_options.victory.recipient_response.observable ||
      g_war_resolution_construct_calls != 2 ||
      g_war_resolution_absolute_outcomes[0] ||
      !g_war_resolution_absolute_outcomes[1] ||
      g_white_peace_construct_calls != 1) {
    return Fail("war-termination query changed player-relative contexts");
  }
  g_war_score_result = 37;
  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_war, 0x288, played_character_id);
  Store(g_war, 0x28C, enemy_character_id);

  xar::ck3_11906::WarTerminationTermsSnapshot termination_terms{};
  g_character_claim_read_calls = 0;
  g_character_claim_destroy_calls = 0;
  g_character_claim_title_mismatch = false;
  g_character_claim_malformed_bool = false;
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
          xar::ck3_11906::ReadWarTerminationTermsResult::available ||
      termination_terms.war_id != active_war_id ||
      termination_terms.active_casus_belli_database_index != 0 ||
      termination_terms.active_casus_belli_key != "claim_cb" ||
      termination_terms.claimant_character_id != played_character_id ||
      termination_terms.target_title_ids !=
          std::vector<std::int32_t>{
              targeted_title_id, targeted_duchy_a_title_id,
              second_county_title_id, third_capital_barony_title_id} ||
      termination_terms.claims.size() != 4 ||
      termination_terms.claims[0].state != "weak_explicit" ||
      !termination_terms.claims[0].present ||
      termination_terms.claims[0].strong ||
      termination_terms.claims[0].implicit ||
      termination_terms.claims[1].state != "strong_explicit" ||
      !termination_terms.claims[1].present ||
      !termination_terms.claims[1].strong ||
      termination_terms.claims[1].implicit ||
      termination_terms.claims[2].state != "weak_implicit" ||
      !termination_terms.claims[2].present ||
      termination_terms.claims[2].strong ||
      !termination_terms.claims[2].implicit ||
      termination_terms.claims[3].state != "absent" ||
      termination_terms.claims[3].present ||
      termination_terms.attacker_victory.declared_title_disposition !=
          "transfer_to_claimant_via_conquest_claim" ||
      termination_terms.attacker_victory.claim_disposition !=
          "resolve_with_add_claim_on_loss" ||
      termination_terms.white_peace.declared_title_disposition !=
          "unchanged" ||
      termination_terms.white_peace.claim_disposition !=
          "retain_and_strengthen_weak" ||
      termination_terms.attacker_defeat.declared_title_disposition !=
          "unchanged" ||
      termination_terms.attacker_defeat.claim_disposition !=
          "remove_declared_target_claims" ||
      g_character_claim_read_calls != 4 ||
      g_character_claim_destroy_calls != 3 || g_submit_called) {
    return Fail("claim terms lost native claimant/target/claim semantics");
  }

  const auto claim_reads_before_raiktor = g_character_claim_read_calls;
  const auto claim_destroys_before_raiktor =
      g_character_claim_destroy_calls;
  Store(g_casus_belli_type_1, 0x18, g_raiktor_casus_belli_key);
  Store(g_casus_belli_type_1, 0x28,
        std::size_t{sizeof(g_raiktor_casus_belli_key) - 1});
  Store(g_casus_belli_type_1, 0x30,
        std::size_t{sizeof(g_raiktor_casus_belli_key) - 1});
  Store(g_war, 0x100,
        static_cast<void *>(g_casus_belli_type_1.data()));
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
          xar::ck3_11906::ReadWarTerminationTermsResult::available ||
      termination_terms.active_casus_belli_database_index != 1 ||
      termination_terms.active_casus_belli_key != "raiktor_claim_cb" ||
      termination_terms.claimant_character_id != played_character_id ||
      termination_terms.target_title_ids !=
          std::vector<std::int32_t>{
              targeted_title_id, targeted_duchy_a_title_id,
              second_county_title_id, third_capital_barony_title_id} ||
      termination_terms.claims.size() != 4 ||
      !termination_terms.attacker_victory.declared_title_disposition.empty() ||
      !termination_terms.white_peace.claim_disposition.empty() ||
      termination_terms.attacker_defeat.declared_title_disposition !=
          "unchanged" ||
      termination_terms.attacker_defeat.claim_disposition !=
          "remove_declared_target_claims" ||
      !termination_terms.raiktor_surrender.has_value() ||
      termination_terms.raiktor_surrender->claim_disposition !=
          termination_terms.attacker_defeat ||
      termination_terms.raiktor_surrender->gold_reparations_factor != 3 ||
      termination_terms.raiktor_surrender->gold_reparations_direction !=
          "primary_attacker_to_primary_defender" ||
      termination_terms.raiktor_surrender->attacker_fame_scale != -10 ||
      termination_terms.raiktor_surrender->attacker_fame_resource !=
          "prestige" ||
      termination_terms.raiktor_surrender->attacker_legitimacy_delta.raw !=
          0 ||
      termination_terms.raiktor_surrender->attacker_legitimacy_delta.scale !=
          100'000 ||
      termination_terms.raiktor_surrender->attacker_influence_delta.raw != 0 ||
      termination_terms.raiktor_surrender->attacker_influence_delta.scale !=
          100'000 ||
      termination_terms.raiktor_surrender->hostages_allowed ||
      termination_terms.raiktor_surrender->unobserved_dynamic_effects.size() !=
          14 ||
      g_character_claim_read_calls != claim_reads_before_raiktor + 4 ||
      g_character_claim_destroy_calls !=
          claim_destroys_before_raiktor + 3 ||
      g_submit_called) {
    return Fail("raiktor surrender terms lost the narrow source-bound slice");
  }

  Store(g_casus_belli_type_1, 0x18, g_casus_belli_key_1);
  Store(g_casus_belli_type_1, 0x28,
        std::size_t{sizeof(g_casus_belli_key_1) - 1});
  Store(g_casus_belli_type_1, 0x30,
        std::size_t{sizeof(g_casus_belli_key_1) - 1});
  const auto claim_calls_before_unsupported = g_character_claim_read_calls;
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
          xar::ck3_11906::ReadWarTerminationTermsResult::
              unsupported_casus_belli ||
      termination_terms.war_id != active_war_id ||
      termination_terms.active_casus_belli_database_index != 1 ||
      termination_terms.active_casus_belli_key != "county_conquest_cb" ||
      termination_terms.claimant_character_id != -1 ||
      !termination_terms.target_title_ids.empty() ||
      !termination_terms.claims.empty() ||
      g_character_claim_read_calls != claim_calls_before_unsupported) {
    return Fail("non-claim CB did not return a narrow typed unsupported row");
  }
  Store(g_war, 0x100,
        static_cast<void *>(g_casus_belli_type_0.data()));

  Store(g_war, 0x290, std::int32_t{0x02000002});
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
      xar::ck3_11906::ReadWarTerminationTermsResult::unavailable) {
    return Fail("claim terms accepted a stale claimant generation");
  }
  Store(g_war, 0x290, played_character_id);

  g_character_claim_title_mismatch = true;
  const auto destroy_calls_before_mismatch =
      g_character_claim_destroy_calls;
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
          xar::ck3_11906::ReadWarTerminationTermsResult::unavailable ||
      g_character_claim_destroy_calls !=
          destroy_calls_before_mismatch + 1) {
    return Fail("claim terms accepted a mismatched native claim title");
  }
  g_character_claim_title_mismatch = false;

  g_character_claim_malformed_bool = true;
  const auto destroy_calls_before_malformed =
      g_character_claim_destroy_calls;
  if (xar::ck3_11906::ReadWarTerminationTerms(
          bindings, active_war_id, termination_terms) !=
          xar::ck3_11906::ReadWarTerminationTermsResult::unavailable ||
      g_character_claim_destroy_calls !=
          destroy_calls_before_malformed + 1) {
    return Fail("claim terms accepted a malformed native claim boolean");
  }
  g_character_claim_malformed_bool = false;

  // The production v2 query is available-only: one paused read must dry-run
  // both loaded result effects, observe finance/PoW/recipient response, and
  // then prove every borrowed identity and claim getter stable a second time.
  Store(g_war, 0x278, std::int32_t{4});
  Store(g_war, 0x27C, std::int32_t{1});
  g_targeted_title_succession_ids[0] = kFixtureDeadCharacterId;
  Store(g_targeted_title, 0x278,
        static_cast<void *>(g_targeted_title_succession_ids.data()));
  Store(g_targeted_title, 0x280, std::int32_t{1});
  Store(g_targeted_title, 0x284, std::int32_t{1});
  Store(g_dead_character, 0x1A8,
        static_cast<void *>(g_dead_character_extension.data()));
  Store(g_dead_character_extension, 0x288,
        static_cast<void *>(g_dead_prison_relation.data()));
  Store(g_dead_prison_relation, 0x00, enemy_character_id);

  g_exit_terms_fixture_active = true;
  Store(g_character_storage, 0x2C, std::int32_t{7});
  g_exit_terms_unknown_node = false;
  g_exit_terms_malformed_contribution = false;
  g_exit_terms_duplicate_truce = false;
  g_exit_terms_income_mismatch = false;
  g_exit_terms_factor_malformed = false;
  g_exit_terms_collector_lifecycle_valid = true;
  g_exit_terms_context_lifecycle_valid = true;
  g_exit_terms_answer_status_override = 0xFF;
  g_exit_terms_effect_context_construct_calls = 0;
  g_exit_terms_effect_context_populate_calls = 0;
  g_exit_terms_collector_construct_calls = 0;
  g_exit_terms_collector_destroy_calls = 0;
  g_exit_terms_traverse_calls = 0;
  g_exit_terms_forward_calls = 0;
  g_exit_terms_projected_root_preview_calls = 0;
  g_exit_terms_projected_callback_counts.fill(0);
  g_exit_terms_hidden_truce_preview_calls = 0;
  g_exit_terms_context_teardown_stage = 0;
  g_exit_terms_truce_duration_calls = 0;
  g_exit_terms_primary_title_calls = 0;
  g_exit_terms_monthly_income_calls = 0;
  g_exit_terms_answer_calls = 0;
  g_character_claim_read_calls = 0;
  g_character_claim_destroy_calls = 0;
  g_interaction_destroy_calls = 0;

  xar::ck3_11906::WarTerminationExitTermsSnapshot exit_terms{};
  if (xar::ck3_11906::ReadWarTerminationExitTerms(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason() !=
          "loaded_effect_preview_disabled_after_live_crash_rva_0x334C668" ||
      g_exit_terms_effect_context_construct_calls != 0 ||
      g_exit_terms_effect_context_populate_calls != 0 ||
      g_exit_terms_collector_construct_calls != 0 ||
      g_exit_terms_traverse_calls != 0 ||
      g_exit_terms_projected_root_preview_calls != 0 ||
      g_exit_terms_hidden_truce_preview_calls != 0) {
    return Fail(
        "production exit-terms v2 did not fail closed before loaded effects");
  }

  // GEN-034 uses a deliberately isolated visitor over Raiktor's original
  // visible surrender root.  It must not enter the disabled broad reader,
  // call an execution slot, or alter the ordinary claim_cb golden.
  Bindings raiktor_hook_bindings = bindings;
  raiktor_hook_bindings.effect_preview_collector_vtable =
      reinterpret_cast<std::uintptr_t>(
          g_raiktor_preview_collector_vtable.data());
  raiktor_hook_bindings.construct_effect_preview_collector =
      FixtureConstructRaiktorPreviewCollector;
  raiktor_hook_bindings.destroy_effect_preview_collector =
      FixtureDestroyRaiktorPreviewCollector;
  raiktor_hook_bindings.traverse_loaded_effect =
      FixtureTraverseRaiktorFavorHook;

  const auto reset_raiktor_hook_fixture = [&] {
    g_raiktor_emit_primary = true;
    g_raiktor_emit_theocracy = true;
    g_raiktor_emit_duplicate_primary = false;
    g_raiktor_emit_theocracy_first = false;
    g_raiktor_emit_no_toast = false;
    g_raiktor_emit_wrong_first_scope = false;
    g_raiktor_emit_wrong_second_scope = false;
    g_raiktor_emit_payload = false;
    g_raiktor_emit_unknown_forwarded_argument = false;
    g_raiktor_lookup_returns_fallback = false;
    g_raiktor_drift_database = false;
    g_raiktor_drift_loaded_root = false;
    g_raiktor_collector_lifecycle_valid = true;
    g_raiktor_collector_construct_calls = 0;
    g_raiktor_collector_destroy_calls = 0;
    g_raiktor_traverse_calls = 0;
    g_raiktor_forward_calls = 0;
    g_raiktor_hash_calls = 0;
    g_raiktor_lookup_calls = 0;
    g_raiktor_hook_type_database_pointer =
        g_raiktor_hook_type_database.data();
    g_raiktor_hook_type_fallback_pointer =
        g_raiktor_hook_type_fallback.data();
    Store(g_raiktor_loaded_effect, 0x00,
          static_cast<void *>(g_raiktor_loaded_effect_vtable.data()));
    Store(g_raiktor_add_hook_effect_node, 0x00,
          static_cast<void *>(g_raiktor_add_hook_effect_vtable.data()));
    Store(g_raiktor_add_hook_effect_node, 0x60,
          static_cast<void *>(g_raiktor_favor_hook_type.data()));
    Store(g_raiktor_add_hook_effect_node, 0x6C, std::uint8_t{2});
    Store(g_raiktor_favor_hook_type, 0x00,
          static_cast<void *>(g_raiktor_hook_type_vtable.data()));
    Store(g_raiktor_favor_hook_type, 0x14,
          kFixtureFavorHookStableHash);
    std::memset(g_raiktor_favor_hook_type.data() + 0x18, 0, 0x20);
    std::memcpy(g_raiktor_favor_hook_type.data() + 0x18,
                favor_hook_key, sizeof(favor_hook_key));
    Store(g_raiktor_favor_hook_type, 0x28,
          std::size_t{sizeof(favor_hook_key) - 1});
    Store(g_raiktor_favor_hook_type, 0x30, std::size_t{15});
  };

  reset_raiktor_hook_fixture();
  bool favor_hook_applies = false;
  const auto raiktor_root_vtable_before =
      LoadBytes<void *>(g_raiktor_loaded_effect.data(), 0x00);
  if (!xar::ck3_11906::ReadRaiktorFavorHookPresenceForOfflineReFixture(
          raiktor_hook_bindings, g_raiktor_loaded_effect.data(),
          g_raiktor_effect_context.data(), played_character_id,
          enemy_character_id, favor_hook_applies) ||
      !favor_hook_applies ||
      LoadBytes<void *>(g_raiktor_loaded_effect.data(), 0x00) !=
          raiktor_root_vtable_before ||
      g_raiktor_collector_construct_calls != 1 ||
      g_raiktor_collector_destroy_calls != 1 ||
      g_raiktor_traverse_calls != 1 || g_raiktor_forward_calls != 3 ||
      g_raiktor_hash_calls != 2 || g_raiktor_lookup_calls != 2 ||
      !g_raiktor_collector_lifecycle_valid || g_submit_called ||
      g_exit_terms_effect_context_construct_calls != 0 ||
      g_exit_terms_traverse_calls != 0) {
    return Fail(
        "Raiktor favor-hook observer lost the exact primary/optional rows");
  }

  reset_raiktor_hook_fixture();
  g_raiktor_emit_theocracy = false;
  favor_hook_applies = false;
  if (!xar::ck3_11906::ReadRaiktorFavorHookPresenceForOfflineReFixture(
          raiktor_hook_bindings, g_raiktor_loaded_effect.data(),
          g_raiktor_effect_context.data(), played_character_id,
          enemy_character_id, favor_hook_applies) ||
      !favor_hook_applies || g_raiktor_forward_calls != 2 ||
      !g_raiktor_collector_lifecycle_valid) {
    return Fail(
        "Raiktor favor-hook observer required the optional theocracy row");
  }

  reset_raiktor_hook_fixture();
  g_raiktor_emit_primary = false;
  g_raiktor_emit_theocracy = false;
  favor_hook_applies = true;
  if (!xar::ck3_11906::ReadRaiktorFavorHookPresenceForOfflineReFixture(
          raiktor_hook_bindings, g_raiktor_loaded_effect.data(),
          g_raiktor_effect_context.data(), played_character_id,
          enemy_character_id, favor_hook_applies) ||
      favor_hook_applies || g_raiktor_forward_calls != 1 ||
      g_raiktor_hash_calls != 2 || g_raiktor_lookup_calls != 2 ||
      !g_raiktor_collector_lifecycle_valid) {
    return Fail("Raiktor favor-hook observer fabricated an absent row");
  }

  reset_raiktor_hook_fixture();
  favor_hook_applies = true;
  if (!xar::ck3_11906::ReadRaiktorFavorHookPresenceForOfflineReFixture(
          raiktor_hook_bindings, g_raiktor_loaded_effect.data(),
          g_raiktor_effect_context.data(), played_character_id,
          played_character_id, favor_hook_applies) ||
      favor_hook_applies || g_raiktor_collector_construct_calls != 0 ||
      g_raiktor_traverse_calls != 0 || g_raiktor_hash_calls != 0 ||
      g_raiktor_lookup_calls != 0) {
    return Fail(
        "Raiktor claimant-equals-attacker did not short-circuit to false");
  }

  const auto rejects_raiktor_hook_drift =
      [&](auto configure, std::string_view case_name) {
        reset_raiktor_hook_fixture();
        configure();
        bool observed = true;
        const bool returned =
            xar::ck3_11906::
                ReadRaiktorFavorHookPresenceForOfflineReFixture(
                    raiktor_hook_bindings,
                    g_raiktor_loaded_effect.data(),
                    g_raiktor_effect_context.data(),
                    played_character_id, enemy_character_id, observed);
        if (returned || observed ||
            !g_raiktor_collector_lifecycle_valid || g_submit_called) {
          std::cerr << "Raiktor hook drift accepted: " << case_name
                    << " returned=" << returned
                    << " observed=" << observed
                    << " lifecycle="
                    << g_raiktor_collector_lifecycle_valid << '\n';
          return false;
        }
        return true;
      };
  if (!rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_no_toast = true; }, "no_toast_family") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_wrong_first_scope = true; },
          "attacker_scope") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_wrong_second_scope = true; },
          "claimant_scope") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_payload = true; }, "nonnull_payload") ||
      !rejects_raiktor_hook_drift(
          [] {
            Store(g_raiktor_add_hook_effect_node, 0x60,
                  static_cast<void *>(
                      g_raiktor_hook_type_fallback.data()));
          },
          "node_type_pointer") ||
      !rejects_raiktor_hook_drift(
          [] {
            Store(g_raiktor_add_hook_effect_node, 0x6C,
                  std::uint8_t{1});
          },
          "node_mode") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_unknown_forwarded_argument = true; },
          "forwarded_argument") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_duplicate_primary = true; },
          "duplicate_primary") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_emit_theocracy_first = true; },
          "optional_before_primary") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_lookup_returns_fallback = true; },
          "hook_type_fallback") ||
      !rejects_raiktor_hook_drift(
          [] {
            Store(g_raiktor_favor_hook_type, 0x14,
                  std::int32_t{0});
          },
          "hook_type_hash") ||
      !rejects_raiktor_hook_drift(
          [] {
            g_raiktor_favor_hook_type[0x18] =
                std::byte{static_cast<unsigned char>('x')};
          },
          "hook_type_key") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_drift_database = true; },
          "database_pointer_drift") ||
      !rejects_raiktor_hook_drift(
          [] { g_raiktor_drift_loaded_root = true; },
          "loaded_root_vtable_drift")) {
    return Fail("Raiktor favor-hook observer accepted ABI/source drift");
  }
  reset_raiktor_hook_fixture();

  // GEN-034 war-bound troop identity is the owner-scoped persistent
  // CRegimentID plus the exact full WarID and keep=false. It is deliberately
  // not a Raiktor/event provenance claim: group names, public ArmyIDs and the
  // authored 3,000-soldier total are absent from this fixture and API.
  constexpr std::int32_t persistent_regiment_a_id = 0x03000001;
  constexpr std::int32_t persistent_regiment_b_id = 0x04000002;
  constexpr std::int32_t other_war_regiment_id = 0x05000003;
  constexpr std::int32_t kept_regiment_id = 0x06000004;
  constexpr std::int32_t same_slot_stale_persistent_id = 0x07000001;
  constexpr std::int32_t current_regiment_a0_id = 0x11000001;
  constexpr std::int32_t current_regiment_a3_id = 0x12000002;
  constexpr std::int32_t current_regiment_b6_id = 0x13000003;
  constexpr std::int32_t same_slot_stale_current_id = 0x14000002;
  constexpr std::int32_t merged_carmy_id = 0x21000001;
  constexpr std::int32_t split_carmy_id = 0x22000002;
  constexpr std::int32_t same_slot_stale_carmy_id = 0x23000001;
  constexpr std::int32_t same_slot_other_war_id = 0x02000001;

  std::array<std::byte, 0x40> persistent_regiment_storage{};
  std::array<std::byte, 5 * 0x10> persistent_regiment_slots{};
  std::array<std::byte, 0x150> persistent_regiment_a{};
  std::array<std::byte, 0x150> persistent_regiment_b{};
  std::array<std::byte, 0x150> other_war_regiment{};
  std::array<std::byte, 0x150> kept_regiment{};
  std::array<std::byte, 0x40> current_regiment_storage{};
  std::array<std::byte, 4 * 0x10> current_regiment_slots{};
  std::array<std::byte, 0x150> current_regiment_a0{};
  std::array<std::byte, 0x150> current_regiment_a3{};
  std::array<std::byte, 0x150> current_regiment_b6{};
  std::array<std::byte, 0x40> war_bound_carmy_storage{};
  std::array<std::byte, 3 * 0x10> war_bound_carmy_slots{};
  std::array<std::byte, 0x50> merged_carmy{};
  std::array<std::byte, 0x50> split_carmy{};
  std::array<std::int32_t, 3> merged_carmy_regiment_ids{
      current_regiment_a0_id, current_regiment_a3_id,
      same_slot_stale_current_id};
  std::array<std::int32_t, 1> split_carmy_regiment_ids{
      current_regiment_b6_id};
  std::array<std::byte, 0x2A0> war_bound_military_state{};
  std::array<std::byte, 2 * 0x38> war_bound_groups{};
  std::array<std::int32_t, 2> war_bound_group_0_ids{
      persistent_regiment_a_id, other_war_regiment_id};
  std::array<std::int32_t, 3> war_bound_group_1_ids{
      persistent_regiment_b_id, kept_regiment_id,
      persistent_regiment_a_id};

  const auto initialize_persistent_regiment =
      [](auto &regiment, std::int32_t regiment_id,
         std::int32_t bound_war_id, std::uint8_t keep) {
        Store(regiment, 0x10, regiment_id);
        Store(regiment, 0x13C, bound_war_id);
        Store(regiment, 0x142, keep);
        for (std::int32_t index = 0;
             index < static_cast<std::int32_t>(
                         xar::ck3_11906::
                             kWarBoundRegimentCompositionRowCount);
             ++index) {
          const auto row_offset =
              std::size_t{0x18} + static_cast<std::size_t>(index) * 0x24;
          Store(regiment, row_offset + 0x08, regiment_id);
          Store(regiment, row_offset + 0x0C, index);
          Store(regiment, row_offset + 0x10, std::int32_t{-1});
        }
      };
  initialize_persistent_regiment(
      persistent_regiment_a, persistent_regiment_a_id, active_war_id, 0);
  initialize_persistent_regiment(
      persistent_regiment_b, persistent_regiment_b_id, active_war_id, 0);
  initialize_persistent_regiment(
      other_war_regiment, other_war_regiment_id,
      same_slot_other_war_id, 0);
  initialize_persistent_regiment(
      kept_regiment, kept_regiment_id, active_war_id, 1);
  Store(persistent_regiment_a, 0x18 + 0 * 0x24 + 0x10,
        current_regiment_a0_id);
  Store(persistent_regiment_a, 0x18 + 3 * 0x24 + 0x10,
        current_regiment_a3_id);
  Store(persistent_regiment_b, 0x18 + 6 * 0x24 + 0x10,
        current_regiment_b6_id);

  Store(persistent_regiment_slots, 0x18,
        static_cast<void *>(persistent_regiment_a.data()));
  Store(persistent_regiment_slots, 0x28,
        static_cast<void *>(persistent_regiment_b.data()));
  Store(persistent_regiment_slots, 0x38,
        static_cast<void *>(other_war_regiment.data()));
  Store(persistent_regiment_slots, 0x48,
        static_cast<void *>(kept_regiment.data()));
  Store(persistent_regiment_storage, 0x20,
        static_cast<void *>(persistent_regiment_slots.data()));
  Store(persistent_regiment_storage, 0x2C, std::int32_t{5});

  const auto initialize_current_regiment =
      [](auto &regiment, std::int32_t regiment_id,
         std::int32_t carmy_id) {
        Store(regiment, 0x10, regiment_id);
        Store(regiment, 0x140, carmy_id);
      };
  initialize_current_regiment(current_regiment_a0,
                              current_regiment_a0_id,
                              merged_carmy_id);
  initialize_current_regiment(current_regiment_a3,
                              current_regiment_a3_id,
                              merged_carmy_id);
  initialize_current_regiment(current_regiment_b6,
                              current_regiment_b6_id,
                              split_carmy_id);
  Store(current_regiment_slots, 0x18,
        static_cast<void *>(current_regiment_a0.data()));
  Store(current_regiment_slots, 0x28,
        static_cast<void *>(current_regiment_a3.data()));
  Store(current_regiment_slots, 0x38,
        static_cast<void *>(current_regiment_b6.data()));
  Store(current_regiment_storage, 0x20,
        static_cast<void *>(current_regiment_slots.data()));
  Store(current_regiment_storage, 0x2C, std::int32_t{4});

  Store(merged_carmy, 0x10, merged_carmy_id);
  Store(merged_carmy, 0x38,
        static_cast<void *>(merged_carmy_regiment_ids.data()));
  Store(merged_carmy, 0x40, std::int32_t{3});
  Store(merged_carmy, 0x44, std::int32_t{2});
  Store(split_carmy, 0x10, split_carmy_id);
  Store(split_carmy, 0x38,
        static_cast<void *>(split_carmy_regiment_ids.data()));
  Store(split_carmy, 0x40, std::int32_t{1});
  Store(split_carmy, 0x44, std::int32_t{1});
  Store(war_bound_carmy_slots, 0x18,
        static_cast<void *>(merged_carmy.data()));
  Store(war_bound_carmy_slots, 0x28,
        static_cast<void *>(split_carmy.data()));
  Store(war_bound_carmy_storage, 0x20,
        static_cast<void *>(war_bound_carmy_slots.data()));
  Store(war_bound_carmy_storage, 0x2C, std::int32_t{3});

  Store(war_bound_groups, 0x20,
        static_cast<void *>(war_bound_group_0_ids.data()));
  Store(war_bound_groups, 0x28, std::int32_t{2});
  Store(war_bound_groups, 0x2C, std::int32_t{2});
  Store(war_bound_groups, 0x38 + 0x20,
        static_cast<void *>(war_bound_group_1_ids.data()));
  Store(war_bound_groups, 0x38 + 0x28, std::int32_t{3});
  Store(war_bound_groups, 0x38 + 0x2C, std::int32_t{3});
  Store(war_bound_military_state, 0x290,
        static_cast<void *>(war_bound_groups.data()));
  Store(war_bound_military_state, 0x298, std::int32_t{2});
  Store(war_bound_military_state, 0x29C, std::int32_t{2});

  void *persistent_regiment_storage_pointer =
      persistent_regiment_storage.data();
  void *current_regiment_storage_pointer = current_regiment_storage.data();
  void *war_bound_carmy_storage_pointer = war_bound_carmy_storage.data();
  Bindings war_bound_bindings = bindings;
  war_bound_bindings.persistent_regiment_storage_slot =
      &persistent_regiment_storage_pointer;
  war_bound_bindings.regiment_storage_slot =
      &current_regiment_storage_pointer;
  war_bound_bindings.army_internal_storage_slot =
      &war_bound_carmy_storage_pointer;
  const auto previous_military_state =
      LoadBytes<void *>(g_played_character.data(), 0x1B8);
  Store(g_played_character, 0x1B8,
        static_cast<void *>(war_bound_military_state.data()));
  g_submit_called = false;

  xar::ck3_11906::WarBoundRegimentObservation war_bound{};
  const auto absent_current =
      xar::ck3_11906::WarBoundRegimentCurrentRow{};
  if (!xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, active_war_id, played_character_id,
          war_bound) ||
      war_bound.provenance !=
          xar::ck3_11906::WarBoundRegimentProvenance::
              war_bound_not_event_specific ||
      war_bound.owner_character_id != played_character_id ||
      war_bound.war_id != active_war_id ||
      war_bound.regiments.size() != 2 ||
      war_bound.regiments[0].persistent_regiment_id !=
          persistent_regiment_a_id ||
      war_bound.regiments[0].bound_war_id != active_war_id ||
      war_bound.regiments[0].war_keep_on_attacker_victory ||
      war_bound.regiments[0].current_rows[0] !=
          xar::ck3_11906::WarBoundRegimentCurrentRow{
              current_regiment_a0_id, merged_carmy_id} ||
      war_bound.regiments[0].current_rows[1] != absent_current ||
      war_bound.regiments[0].current_rows[3] !=
          xar::ck3_11906::WarBoundRegimentCurrentRow{
              current_regiment_a3_id, merged_carmy_id} ||
      war_bound.regiments[1].persistent_regiment_id !=
          persistent_regiment_b_id ||
      war_bound.regiments[1].current_rows[5] != absent_current ||
      war_bound.regiments[1].current_rows[6] !=
          xar::ck3_11906::WarBoundRegimentCurrentRow{
              current_regiment_b6_id, split_carmy_id}) {
    return Fail(
        "war-bound regiment observer lost full identity, seven rows or merge state");
  }

  // The cleanup observer consumes only the frozen full-generation IDs. An
  // ended/missing War is deliberately neither its selector nor its success
  // criterion.
  Store(g_war, 0x358, static_cast<void *>(g_war.data()));
  xar::ck3_11906::FrozenWarBoundRegimentCleanupObservation cleanup{};
  const auto cleanup_absent_current =
      xar::ck3_11906::FrozenWarBoundCurrentCleanupSnapshot{};
  if (!xar::ck3_11906::
          ReadFrozenWarBoundRegimentCleanupObservation(
              war_bound_bindings, war_bound, cleanup) ||
      cleanup.provenance !=
          xar::ck3_11906::WarBoundRegimentProvenance::
              war_bound_not_event_specific ||
      cleanup.status !=
          xar::ck3_11906::WarBoundRegimentCleanupStatus::still_alive ||
      cleanup.owner_character_id != played_character_id ||
      cleanup.war_id != active_war_id || cleanup.regiments.size() != 2 ||
      cleanup.regiments[0].persistent_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[0]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[0].raised_carmy_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[0]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::
              still_attached ||
      cleanup.regiments[0].current_rows[1] !=
          cleanup_absent_current ||
      cleanup.regiments[0].current_rows[3]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::
              still_attached ||
      cleanup.regiments[1].current_rows[6].raised_carmy_id !=
          split_carmy_id ||
      cleanup.regiments[1].current_rows[6]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::
              still_attached) {
    return Fail(
        "frozen war-bound cleanup observer treated war_not_found as cleanup");
  }
  Store(g_war, 0x358, static_cast<void *>(nullptr));

  // A new generation in the same low-24-bit persistent slot means the exact
  // frozen persistent ID was destroyed; current raised rows can still prove
  // that cleanup as a whole is incomplete.
  Store(persistent_regiment_a, 0x10,
        same_slot_stale_persistent_id);
  cleanup = {};
  const bool persistent_slot_reuse_returned =
      xar::ck3_11906::ReadFrozenWarBoundRegimentCleanupObservation(
          war_bound_bindings, war_bound, cleanup);
  Store(persistent_regiment_a, 0x10, persistent_regiment_a_id);
  if (!persistent_slot_reuse_returned ||
      cleanup.status !=
          xar::ck3_11906::WarBoundRegimentCleanupStatus::still_alive ||
      cleanup.regiments[0].persistent_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[0]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive) {
    return Fail(
        "frozen cleanup confused persistent low-24 reuse with exact survival");
  }

  // The same rule independently applies to a frozen CArmyRegiment ID. The
  // live frozen CArmy must also prove that the old full ID left its roster.
  Store(current_regiment_a3, 0x10,
        same_slot_stale_current_id);
  merged_carmy_regiment_ids[1] = same_slot_stale_current_id;
  cleanup = {};
  const bool current_generation_reuse_returned =
      xar::ck3_11906::ReadFrozenWarBoundRegimentCleanupObservation(
          war_bound_bindings, war_bound, cleanup);
  Store(current_regiment_a3, 0x10, current_regiment_a3_id);
  merged_carmy_regiment_ids[1] = current_regiment_a3_id;
  if (!current_generation_reuse_returned ||
      cleanup.regiments[0].current_rows[3]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[3].raised_carmy_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[3]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::detached) {
    return Fail(
        "frozen cleanup accepted a stale current-regiment generation");
  }

  // CArmy generation is frozen independently. Here the current regiment IDs
  // survive and now point at a new generation in the same low-24 slot; that
  // cannot resurrect the frozen CArmy generation.
  Store(merged_carmy, 0x10, same_slot_stale_carmy_id);
  Store(current_regiment_a0, 0x140, same_slot_stale_carmy_id);
  Store(current_regiment_a3, 0x140, same_slot_stale_carmy_id);
  cleanup = {};
  const bool carmy_generation_reuse_returned =
      xar::ck3_11906::ReadFrozenWarBoundRegimentCleanupObservation(
          war_bound_bindings, war_bound, cleanup);
  Store(merged_carmy, 0x10, merged_carmy_id);
  Store(current_regiment_a0, 0x140, merged_carmy_id);
  Store(current_regiment_a3, 0x140, merged_carmy_id);
  if (!carmy_generation_reuse_returned ||
      cleanup.regiments[0].current_rows[0]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[0].raised_carmy_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[0]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::
              frozen_army_destroyed) {
    return Fail("frozen cleanup accepted a stale CArmy generation");
  }

  // Partial destruction remains still_alive and publishes the exact split:
  // persistent A and row A0 are gone, row A3 is still attached to the merged
  // CArmy, and the unrelated/shared CArmy object itself stays alive.
  Store(persistent_regiment_slots, 0x18, static_cast<void *>(nullptr));
  Store(current_regiment_slots, 0x18, static_cast<void *>(nullptr));
  merged_carmy_regiment_ids[0] = current_regiment_a3_id;
  Store(merged_carmy, 0x44, std::int32_t{1});
  cleanup = {};
  const bool partial_cleanup_returned =
      xar::ck3_11906::ReadFrozenWarBoundRegimentCleanupObservation(
          war_bound_bindings, war_bound, cleanup);
  Store(persistent_regiment_slots, 0x18,
        static_cast<void *>(persistent_regiment_a.data()));
  Store(current_regiment_slots, 0x18,
        static_cast<void *>(current_regiment_a0.data()));
  merged_carmy_regiment_ids[0] = current_regiment_a0_id;
  merged_carmy_regiment_ids[1] = current_regiment_a3_id;
  Store(merged_carmy, 0x44, std::int32_t{2});
  if (!partial_cleanup_returned ||
      cleanup.status !=
          xar::ck3_11906::WarBoundRegimentCleanupStatus::still_alive ||
      cleanup.regiments[0].persistent_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[0]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[0]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::detached ||
      cleanup.regiments[0].current_rows[3]
              .current_army_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[3]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::
              still_attached) {
    return Fail("frozen cleanup collapsed partial destruction");
  }

  // Complete frozen-ID cleanup does not require a merged CArmy to disappear;
  // it requires every persistent/current exact generation to be gone and
  // every surviving frozen CArmy roster to be detached from those IDs.
  Store(persistent_regiment_slots, 0x18, static_cast<void *>(nullptr));
  Store(persistent_regiment_slots, 0x28, static_cast<void *>(nullptr));
  Store(current_regiment_slots, 0x18, static_cast<void *>(nullptr));
  Store(current_regiment_slots, 0x28, static_cast<void *>(nullptr));
  Store(current_regiment_slots, 0x38, static_cast<void *>(nullptr));
  Store(merged_carmy, 0x44, std::int32_t{0});
  Store(split_carmy, 0x44, std::int32_t{0});
  cleanup = {};
  const bool destroyed_cleanup_returned =
      xar::ck3_11906::ReadFrozenWarBoundRegimentCleanupObservation(
          war_bound_bindings, war_bound, cleanup);
  Store(persistent_regiment_slots, 0x18,
        static_cast<void *>(persistent_regiment_a.data()));
  Store(persistent_regiment_slots, 0x28,
        static_cast<void *>(persistent_regiment_b.data()));
  Store(current_regiment_slots, 0x18,
        static_cast<void *>(current_regiment_a0.data()));
  Store(current_regiment_slots, 0x28,
        static_cast<void *>(current_regiment_a3.data()));
  Store(current_regiment_slots, 0x38,
        static_cast<void *>(current_regiment_b6.data()));
  Store(merged_carmy, 0x44, std::int32_t{2});
  Store(split_carmy, 0x44, std::int32_t{1});
  if (!destroyed_cleanup_returned ||
      cleanup.status !=
          xar::ck3_11906::WarBoundRegimentCleanupStatus::destroyed ||
      cleanup.regiments[0].persistent_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[1].persistent_regiment_state !=
          xar::ck3_11906::FrozenWarBoundIdState::destroyed ||
      cleanup.regiments[0].current_rows[0].raised_carmy_state !=
          xar::ck3_11906::FrozenWarBoundIdState::still_alive ||
      cleanup.regiments[0].current_rows[0]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::detached ||
      cleanup.regiments[1].current_rows[6]
              .frozen_carmy_roster_evidence !=
          xar::ck3_11906::FrozenWarBoundArmyRosterEvidence::detached) {
    return Fail(
        "frozen cleanup inferred survival from an empty merged CArmy shell");
  }

  const auto rejects_frozen_cleanup =
      [&](auto configure, auto restore, std::string_view case_name) {
        configure();
        auto rejected = cleanup;
        const bool returned =
            xar::ck3_11906::
                ReadFrozenWarBoundRegimentCleanupObservation(
                    war_bound_bindings, war_bound, rejected);
        restore();
        if (returned ||
            rejected != xar::ck3_11906::
                            FrozenWarBoundRegimentCleanupObservation{}) {
          std::cerr << "Frozen war-bound cleanup drift accepted: "
                    << case_name << '\n';
          return false;
        }
        return true;
      };
  if (!rejects_frozen_cleanup(
          [&] {
            Store(current_regiment_storage, 0x2C,
                  std::int32_t{1'000'001});
          },
          [&] {
            Store(current_regiment_storage, 0x2C, std::int32_t{4});
          },
          "current_store_header") ||
      !rejects_frozen_cleanup(
          [&] { Store(merged_carmy, 0x44, std::int32_t{4}); },
          [&] { Store(merged_carmy, 0x44, std::int32_t{2}); },
          "frozen_carmy_roster_header") ||
      !rejects_frozen_cleanup(
          [&] { Store(jomini_state, 0x20, std::uint8_t{0}); },
          [&] { Store(jomini_state, 0x20, std::uint8_t{1}); },
          "running_frame")) {
    return Fail("frozen cleanup accepted unavailable native state");
  }

  // Force an unrelated roster addition between otherwise identical samples.
  // The public state remains still_attached, so only the captured native
  // identity/roster sample can detect this drift.
  const std::int32_t drifted_merged_roster_count = 3;
  g_war_bound_cleanup_drift_target = merged_carmy.data() + 0x44;
  g_war_bound_cleanup_drift_size = sizeof(drifted_merged_roster_count);
  std::memcpy(g_war_bound_cleanup_drift_payload.data(),
              &drifted_merged_roster_count,
              sizeof(drifted_merged_roster_count));
  cleanup = {};
  const bool roster_drift_returned =
      xar::ck3_11906::
          ReadFrozenWarBoundRegimentCleanupObservationForOfflineReFixture(
              war_bound_bindings, war_bound, cleanup,
              &ApplyWarBoundCleanupBetweenSamplesDrift);
  Store(merged_carmy, 0x44, std::int32_t{2});
  g_war_bound_cleanup_drift_target = nullptr;
  g_war_bound_cleanup_drift_size = 0;
  if (roster_drift_returned ||
      cleanup != xar::ck3_11906::
                     FrozenWarBoundRegimentCleanupObservation{}) {
    return Fail("frozen cleanup published a drifting CArmy roster");
  }

  // The same seam proves game_state identity is rechecked between samples.
  void *const null_game_state = nullptr;
  g_war_bound_cleanup_drift_target =
      reinterpret_cast<std::byte *>(&game_state_pointer);
  g_war_bound_cleanup_drift_size = sizeof(null_game_state);
  std::memcpy(g_war_bound_cleanup_drift_payload.data(), &null_game_state,
              sizeof(null_game_state));
  cleanup = {};
  const bool game_state_drift_returned =
      xar::ck3_11906::
          ReadFrozenWarBoundRegimentCleanupObservationForOfflineReFixture(
              war_bound_bindings, war_bound, cleanup,
              &ApplyWarBoundCleanupBetweenSamplesDrift);
  game_state_pointer = game_state.data();
  g_war_bound_cleanup_drift_target = nullptr;
  g_war_bound_cleanup_drift_size = 0;
  if (game_state_drift_returned ||
      cleanup != xar::ck3_11906::
                     FrozenWarBoundRegimentCleanupObservation{}) {
    return Fail("frozen cleanup published across game_state drift");
  }

  const auto rejects_war_bound_drift =
      [&](auto configure, auto restore, std::string_view case_name) {
        configure();
        xar::ck3_11906::WarBoundRegimentObservation observed = war_bound;
        const bool returned =
            xar::ck3_11906::
                ReadPrimaryAttackerWarBoundRegimentObservation(
                war_bound_bindings, active_war_id,
                played_character_id, observed);
        restore();
        if (returned ||
            observed != xar::ck3_11906::WarBoundRegimentObservation{}) {
          std::cerr << "War-bound regiment drift accepted: "
                    << case_name << '\n';
          return false;
        }
        return true;
      };
  if (!rejects_war_bound_drift(
          [&] {
            war_bound_group_0_ids[0] =
                same_slot_stale_persistent_id;
          },
          [&] {
            war_bound_group_0_ids[0] = persistent_regiment_a_id;
          },
          "persistent_generation") ||
      !rejects_war_bound_drift(
          [&] {
            Store(persistent_regiment_a,
                  0x18 + 3 * 0x24 + 0x10,
                  same_slot_stale_current_id);
          },
          [&] {
            Store(persistent_regiment_a,
                  0x18 + 3 * 0x24 + 0x10,
                  current_regiment_a3_id);
          },
          "current_generation") ||
      !rejects_war_bound_drift(
          [&] {
            Store(current_regiment_a0, 0x140,
                  same_slot_stale_carmy_id);
          },
          [&] {
            Store(current_regiment_a0, 0x140, merged_carmy_id);
          },
          "carmy_generation") ||
      !rejects_war_bound_drift(
          [&] { Store(merged_carmy, 0x44, std::int32_t{1}); },
          [&] { Store(merged_carmy, 0x44, std::int32_t{2}); },
          "carmy_membership") ||
      !rejects_war_bound_drift(
          [&] {
            Store(war_bound_military_state, 0x29C,
                  std::int32_t{3});
          },
          [&] {
            Store(war_bound_military_state, 0x29C,
                  std::int32_t{2});
          },
          "group_header") ||
      !rejects_war_bound_drift(
          [&] { Store(war_bound_groups, 0x2C, std::int32_t{3}); },
          [&] { Store(war_bound_groups, 0x2C, std::int32_t{2}); },
          "nested_header") ||
      !rejects_war_bound_drift(
          [&] {
            Store(persistent_regiment_a, 0x18 + 0x08,
                  persistent_regiment_b_id);
          },
          [&] {
            Store(persistent_regiment_a, 0x18 + 0x08,
                  persistent_regiment_a_id);
          },
          "row_owner") ||
      !rejects_war_bound_drift(
          [&] {
            Store(persistent_regiment_b,
                  0x18 + 6 * 0x24 + 0x0C, std::int32_t{5});
          },
          [&] {
            Store(persistent_regiment_b,
                  0x18 + 6 * 0x24 + 0x0C, std::int32_t{6});
          },
          "row_ordinal") ||
      !rejects_war_bound_drift(
          [&] { Store(kept_regiment, 0x142, std::uint8_t{2}); },
          [&] { Store(kept_regiment, 0x142, std::uint8_t{1}); },
          "keep_boolean") ||
      !rejects_war_bound_drift(
          [&] {
            war_bound_bindings.persistent_regiment_storage_slot =
                nullptr;
          },
          [&] {
            war_bound_bindings.persistent_regiment_storage_slot =
                &persistent_regiment_storage_pointer;
          },
          "persistent_storage_binding")) {
    return Fail("war-bound regiment observer accepted stale native state");
  }

  war_bound = {};
  if (xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, active_war_id, enemy_character_id,
          war_bound) ||
      war_bound != xar::ck3_11906::WarBoundRegimentObservation{}) {
    return Fail("war-bound regiment observer accepted a non-attacker owner");
  }
  if (xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, active_war_id,
          std::int32_t{0x02000002}, war_bound) ||
      war_bound != xar::ck3_11906::WarBoundRegimentObservation{}) {
    return Fail("war-bound regiment observer accepted a stale owner generation");
  }
  if (xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, same_slot_other_war_id,
          played_character_id, war_bound) ||
      war_bound != xar::ck3_11906::WarBoundRegimentObservation{}) {
    return Fail("war-bound regiment observer accepted a stale War generation");
  }
  Store(g_war, 0x358, static_cast<void *>(g_war.data()));
  if (xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, active_war_id, played_character_id,
          war_bound) ||
      war_bound != xar::ck3_11906::WarBoundRegimentObservation{}) {
    return Fail("war-bound regiment observer accepted an ended War");
  }
  Store(g_war, 0x358, static_cast<void *>(nullptr));
  Store(jomini_state, 0x20, std::uint8_t{0});
  if (xar::ck3_11906::ReadPrimaryAttackerWarBoundRegimentObservation(
          war_bound_bindings, active_war_id, played_character_id,
          war_bound) ||
      war_bound != xar::ck3_11906::WarBoundRegimentObservation{}) {
    return Fail("war-bound regiment observer read a running frame");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});
  Store(g_played_character, 0x1B8, previous_military_state);
  if (g_submit_called) {
    return Fail("war-bound regiment observer submitted a native command");
  }

  const auto exit_terms_result =
      xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms);
  const auto exit_terms_reason = std::string(
      xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason());
  if (exit_terms_result !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      !exit_terms_reason.starts_with(
          "dry_preview.hidden_truce.attacker_defeat_shape:") ||
      exit_terms_reason.find("root_span=14/19") == std::string::npos ||
      exit_terms_reason.find("root_children=0=") == std::string::npos ||
      exit_terms_reason.find("/13=") == std::string::npos ||
      exit_terms_reason.find("child9=") == std::string::npos ||
      exit_terms_reason.find("selector_count=0") == std::string::npos ||
      exit_terms_reason.find("template=") == std::string::npos ||
      exit_terms_reason.find("default_span=5/6") == std::string::npos ||
      g_exit_terms_effect_context_construct_calls != 1 ||
      g_exit_terms_effect_context_populate_calls != 1 ||
      g_exit_terms_collector_construct_calls != 2 ||
      g_exit_terms_collector_destroy_calls != 2 ||
      g_exit_terms_traverse_calls != 2 ||
      g_exit_terms_forward_calls != 7 ||
      g_exit_terms_projected_root_preview_calls != 1 ||
      g_exit_terms_projected_callback_counts !=
          std::array<std::int32_t, 2>{7, 0} ||
      g_exit_terms_hidden_truce_preview_calls != 1 ||
      g_exit_terms_context_teardown_stage != 4 ||
      !g_exit_terms_context_lifecycle_valid ||
      !g_exit_terms_collector_lifecycle_valid ||
      g_exit_terms_truce_duration_calls != 1 ||
      g_exit_terms_primary_title_calls != 2 ||
      g_exit_terms_monthly_income_calls != 2 ||
      g_exit_terms_answer_calls != 0 ||
      g_character_claim_read_calls != 1 ||
      g_character_claim_destroy_calls != 1 ||
      g_interaction_destroy_calls != 0 || g_submit_called) {
    std::cerr << "exit_terms_result="
              << static_cast<std::int32_t>(exit_terms_result)
              << " reason=" << exit_terms_reason
              << " claim_reads=" << g_character_claim_read_calls
              << " claim_dtors=" << g_character_claim_destroy_calls
              << " collectors=" << g_exit_terms_collector_construct_calls
              << '/' << g_exit_terms_collector_destroy_calls
              << " traverses=" << g_exit_terms_traverse_calls
              << " forwards=" << g_exit_terms_forward_calls
              << " projected=" << g_exit_terms_projected_root_preview_calls
              << " callback_counts="
              << g_exit_terms_projected_callback_counts[0] << '/'
              << g_exit_terms_projected_callback_counts[1]
              << " hidden_truce="
              << g_exit_terms_hidden_truce_preview_calls
              << " teardown=" << g_exit_terms_context_teardown_stage
              << " truce=" << g_exit_terms_truce_duration_calls
              << " titles=" << g_exit_terms_primary_title_calls
              << " income_calls=" << g_exit_terms_monthly_income_calls
              << " answers=" << g_exit_terms_answer_calls << '\n';
    return Fail(
        "exit terms v2 did not stop after one WP projection and one "
        "read-only defeat shape capture");
  }

  const auto rejects_exit_terms_shape_drift =
      [&](auto mutate, auto restore, std::string_view expected_reason) {
        mutate();
        g_exit_terms_context_lifecycle_valid = true;
        const auto result =
            xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
            bindings, active_war_id, exit_terms);
        const auto reason =
            xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason();
        const bool rejected =
            result == xar::ck3_11906::ReadWarTerminationExitTermsResult::
                          unavailable &&
            exit_terms ==
                xar::ck3_11906::WarTerminationExitTermsSnapshot{} &&
            reason == expected_reason &&
            g_exit_terms_context_teardown_stage == 4 &&
            g_exit_terms_context_lifecycle_valid;
        restore();
        return rejected;
      };
  const auto root_child7 = g_exit_root_effect_children[7];
  const auto root_child8 = g_exit_root_effect_children[8];
  const auto default_child1 = g_truce_scripted_default_children[1];
  const auto default_child2 = g_truce_scripted_default_children[2];
  const auto root_vtable =
      static_cast<void *>(g_white_peace_loaded_effect_vtable.data());
  const auto alternate_vtable =
      static_cast<void *>(g_defeat_loaded_effect_vtable.data());
  const auto scripted_vtable =
      static_cast<void *>(g_scripted_effect_vtable.data());
  const auto template_vtable =
      static_cast<void *>(g_scripted_effect_template_vtable.data());
  const auto hidden_vtable =
      static_cast<void *>(g_hidden_effect_vtable.data());
  const auto truce_node_vtable = LoadBytes<std::uintptr_t>(
      g_truce_effect_node.data(), 0x00);
  const auto unknown_node_vtable = LoadBytes<std::uintptr_t>(
      g_unknown_effect_node.data(), 0x00);
  const auto context_slot58 = g_context_effect_vtable[11];

  if (!rejects_exit_terms_shape_drift(
          [&] { StoreBytes(g_casus_belli_type_0.data(), 0x9C8,
                           alternate_vtable); },
          [&] { StoreBytes(g_casus_belli_type_0.data(), 0x9C8,
                           root_vtable); },
          "dry_preview.hidden_truce.root_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_casus_belli_type_0, 0x9C8 + 0x4C,
                       std::int32_t{9}); },
          [&] { Store(g_casus_belli_type_0, 0x9C8 + 0x4C,
                       std::int32_t{10}); },
          "dry_preview.hidden_truce.root_span") ||
      !rejects_exit_terms_shape_drift(
          [&] {
            g_exit_root_effect_children[7] = root_child8;
            g_exit_root_effect_children[8] = root_child7;
          },
          [&] {
            g_exit_root_effect_children[7] = root_child7;
            g_exit_root_effect_children[8] = root_child8;
          },
          "dry_preview.hidden_truce.root_child8") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_scripted_effect, 0x00,
                       alternate_vtable); },
          [&] { Store(g_truce_scripted_effect, 0x00,
                       scripted_vtable); },
          "dry_preview.hidden_truce.root_child8") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_scripted_effect, 0x94,
                       std::int32_t{1}); },
          [&] { Store(g_truce_scripted_effect, 0x94,
                       std::int32_t{0}); },
          "dry_preview.hidden_truce.selector_count") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_scripted_effect_template, 0x00,
                       hidden_vtable); },
          [&] { Store(g_truce_scripted_effect_template, 0x00,
                       template_vtable); },
          "dry_preview.hidden_truce.template_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_scripted_default_effect, 0x00,
                       alternate_vtable); },
          [&] { Store(g_truce_scripted_default_effect, 0x00,
                       root_vtable); },
          "dry_preview.hidden_truce.default_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_scripted_default_effect, 0x48,
                       std::int32_t{5}); },
          [&] { Store(g_truce_scripted_default_effect, 0x48,
                       std::int32_t{6}); },
          "dry_preview.hidden_truce.default_span") ||
      !rejects_exit_terms_shape_drift(
          [&] {
            g_truce_scripted_default_children[1] = default_child2;
            g_truce_scripted_default_children[2] = default_child1;
          },
          [&] {
            g_truce_scripted_default_children[1] = default_child1;
            g_truce_scripted_default_children[2] = default_child2;
          },
          "dry_preview.hidden_truce.hidden_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_hidden_effect, 0x4C,
                       std::int32_t{0}); },
          [&] { Store(g_truce_hidden_effect, 0x4C,
                       std::int32_t{1}); },
          "dry_preview.hidden_truce.hidden_span") ||
      !rejects_exit_terms_shape_drift(
          [&] { g_truce_hidden_children[0] = g_truce_effect_node.data(); },
          [&] { g_truce_hidden_children[0] =
                    g_truce_context_effect.data(); },
          "dry_preview.hidden_truce.context_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_context_effect, 0x48,
                       std::int32_t{0}); },
          [&] { Store(g_truce_context_effect, 0x48,
                       std::int32_t{1}); },
          "dry_preview.hidden_truce.context_span") ||
      !rejects_exit_terms_shape_drift(
          [&] { Store(g_truce_context_effect, 0x6C,
                       std::int32_t{0}); },
          [&] { Store(g_truce_context_effect, 0x6C,
                       std::int32_t{1}); },
          "dry_preview.hidden_truce.context_scope") ||
      !rejects_exit_terms_shape_drift(
          [&] { StoreBytes(g_truce_effect_node.data(), 0x00,
                           unknown_node_vtable); },
          [&] { StoreBytes(g_truce_effect_node.data(), 0x00,
                           truce_node_vtable); },
          "dry_preview.hidden_truce.truce_vtable") ||
      !rejects_exit_terms_shape_drift(
          [&] { g_context_effect_vtable[11] =
                    reinterpret_cast<void *>(1); },
          [&] { g_context_effect_vtable[11] = context_slot58; },
          "dry_preview.hidden_truce.preview_slot") ||
      !rejects_exit_terms_shape_drift(
          [&] { g_exit_root_effect_children[0] = nullptr; },
          [&] { g_exit_root_effect_children[0] =
                    g_unknown_effect_node.data(); },
          "dry_preview.hidden_truce.projection_root_child") ||
      !rejects_exit_terms_shape_drift(
          [&] { g_truce_scripted_default_children[0] = nullptr; },
          [&] { g_truce_scripted_default_children[0] =
                    g_unknown_effect_node.data(); },
          "dry_preview.hidden_truce.projection_default_child")) {
    return Fail("exit terms v2 accepted a compiled hidden-truce shape drift");
  }

  g_exit_terms_income_mismatch = true;
  const auto income_calls_before_mismatch =
      g_exit_terms_monthly_income_calls;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      !xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason()
           .starts_with(
               "dry_preview.hidden_truce.attacker_defeat_shape:") ||
      g_exit_terms_monthly_income_calls !=
          income_calls_before_mismatch + 2) {
    return Fail(
        "exit terms v2 did not preserve the authoritative income read "
        "before its defeat-shape gate");
  }
  g_exit_terms_income_mismatch = false;

  g_exit_terms_unknown_node = true;
  g_exit_terms_context_lifecycle_valid = true;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      !xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason()
           .starts_with(
               "dry_preview.capture_row_unknown:effect_vtable_rva=0x") ||
      g_exit_terms_context_teardown_stage != 4 ||
      !g_exit_terms_context_lifecycle_valid) {
    return Fail("exit terms v2 accepted an unknown loaded-effect node");
  }
  g_exit_terms_unknown_node = false;

  g_exit_terms_malformed_contribution = true;
  g_exit_terms_context_lifecycle_valid = true;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason() !=
          "dry_preview.attacker_contribution_row" ||
      g_exit_terms_context_teardown_stage != 4 ||
      !g_exit_terms_context_lifecycle_valid) {
    return Fail(
        "exit terms v2 accepted a malformed contribution-only preview row");
  }
  g_exit_terms_malformed_contribution = false;

  g_exit_terms_duplicate_truce = true;
  g_exit_terms_context_lifecycle_valid = true;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason() !=
          "dry_preview.hidden_truce.projected_preview_count" ||
      g_exit_terms_context_teardown_stage != 4 ||
      !g_exit_terms_context_lifecycle_valid) {
    return Fail("exit terms v2 hidden preview accepted duplicate truce");
  }
  g_exit_terms_duplicate_truce = false;

  g_exit_terms_factor_malformed = true;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{} ||
      xar::ck3_11906::LastWarTerminationExitTermsUnavailableReason() !=
          "dry_preview.factor_row") {
    return Fail("exit terms v2 accepted a malformed identifier82 payload");
  }
  g_exit_terms_factor_malformed = false;

  g_exit_terms_answer_status_override = 3;
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{}) {
    return Fail("exit terms v2 published native recipient status 3");
  }
  g_exit_terms_answer_status_override = 0xFF;

  Store(g_targeted_title, 0x284, std::int32_t{2});
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
          xar::ck3_11906::ReadWarTerminationExitTermsResult::unavailable ||
      exit_terms != xar::ck3_11906::WarTerminationExitTermsSnapshot{}) {
    return Fail("exit terms v2 accepted a malformed succession span");
  }
  Store(g_targeted_title, 0x284, std::int32_t{1});

  Store(jomini_state, 0x20, std::uint8_t{0});
  if (xar::ck3_11906::ReadWarTerminationExitTermsForOfflineReFixture(
          bindings, active_war_id, exit_terms) !=
      xar::ck3_11906::ReadWarTerminationExitTermsResult::requires_paused) {
    return Fail("exit terms v2 traversed effects while the map was running");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});

  g_exit_terms_fixture_active = false;
  Store(g_character_storage, 0x2C, std::int32_t{6});
  Store(g_targeted_title, 0x278, static_cast<void *>(nullptr));
  Store(g_targeted_title, 0x280, std::int32_t{0});
  Store(g_targeted_title, 0x284, std::int32_t{0});
  Store(g_dead_character, 0x1A8, static_cast<void *>(nullptr));
  Store(g_war, 0x27C, std::int32_t{4});

  g_expected_command = ExpectedCommand::offer_white_peace;
  Store(jomini_state, 0x20, std::uint8_t{0});
  g_white_peace_construct_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
          xar::ck3_11906::OfferWhitePeaceResult::requires_paused ||
      g_white_peace_construct_calls != 0 || g_submit_called) {
    return Fail("offer-white-peace ran while the map was not paused");
  }
  Store(jomini_state, 0x20, std::uint8_t{1});

  Store(g_war, 0x288, enemy_character_id);
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
      xar::ck3_11906::OfferWhitePeaceResult::player_not_war_leader) {
    return Fail("offer-white-peace accepted a participating non-war-leader");
  }
  Store(g_war, 0x288, played_character_id);

  Store(g_casus_belli_type_0, 0x1718, std::uint32_t{0});
  g_white_peace_construct_calls = 0;
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
          xar::ck3_11906::OfferWhitePeaceResult::white_peace_not_allowed ||
      g_white_peace_construct_calls != 0) {
    return Fail("offer-white-peace ignored the active CB permission bit");
  }
  Store(g_casus_belli_type_0, 0x1718, std::uint32_t{1U << 7U});

  g_interaction_validate_result = false;
  g_interaction_destroy_calls = 0;
  g_white_peace_construct_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
          xar::ck3_11906::OfferWhitePeaceResult::validation_failed ||
      g_submit_called || g_white_peace_construct_calls != 1 ||
      g_interaction_destroy_calls != 1 ||
      g_last_special_interaction_index != 3 ||
      g_last_special_actor_character_id != played_character_id ||
      g_last_special_recipient_character_id != enemy_character_id) {
    return Fail("offer-white-peace bypassed its native context validator");
  }
  g_interaction_validate_result = true;

  g_submit_result = false;
  g_interaction_destroy_calls = 0;
  g_send_interaction_construct_called = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
          xar::ck3_11906::OfferWhitePeaceResult::submission_failed ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2) {
    return Fail("offer-white-peace lost the native queue rejection");
  }
  g_submit_result = true;

  g_interaction_destroy_calls = 0;
  g_white_peace_construct_calls = 0;
  g_send_interaction_construct_called = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitOfferWhitePeace(bindings, active_war_id) !=
          xar::ck3_11906::OfferWhitePeaceResult::submitted ||
      g_white_peace_construct_calls != 1 ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2 ||
      g_last_special_interaction_index != 3 ||
      g_last_special_actor_character_id != played_character_id ||
      g_last_special_recipient_character_id != enemy_character_id) {
    return Fail("offer-white-peace did not submit the typed native context");
  }

  g_expected_command = ExpectedCommand::surrender_war;
  g_interaction_validate_result = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSurrenderWar(bindings, active_war_id) !=
          xar::ck3_11906::SurrenderWarResult::validation_failed ||
      g_submit_called || g_interaction_destroy_calls != 1 ||
      g_war_resolution_attacker_victory) {
    return Fail("surrender-war bypassed native validation");
  }
  g_interaction_validate_result = true;
  g_war_resolution_context_available = false;
  g_interaction_destroy_calls = 0;
  if (xar::ck3_11906::SubmitSurrenderWar(bindings, active_war_id) !=
          xar::ck3_11906::SurrenderWarResult::context_unavailable ||
      g_interaction_destroy_calls != 1) {
    return Fail("surrender-war accepted an empty native context");
  }
  g_war_resolution_context_available = true;
  g_submit_result = false;
  g_interaction_destroy_calls = 0;
  if (xar::ck3_11906::SubmitSurrenderWar(bindings, active_war_id) !=
          xar::ck3_11906::SurrenderWarResult::submission_failed ||
      g_interaction_destroy_calls != 2) {
    return Fail("surrender-war lost the native queue rejection");
  }
  g_submit_result = true;
  g_interaction_default_construct_called = false;
  g_war_resolution_construct_called = false;
  g_war_resolution_attacker_victory = true;
  g_send_interaction_construct_called = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSurrenderWar(bindings, active_war_id) !=
          xar::ck3_11906::SurrenderWarResult::submitted ||
      !g_interaction_default_construct_called ||
      !g_war_resolution_construct_called ||
      g_war_resolution_attacker_victory ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2) {
    return Fail("surrender-war did not submit absolute attacker defeat");
  }

  if (xar::ck3_11906::SubmitEnforceDemands(bindings, 0x01000009) !=
      xar::ck3_11906::EnforceDemandsResult::war_not_found) {
    return Fail("enforce-demands accepted a missing war component");
  }
  Store(g_attacker_participant, 0x08, enemy_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  if (xar::ck3_11906::SubmitEnforceDemands(bindings, active_war_id) !=
      xar::ck3_11906::EnforceDemandsResult::player_not_participant) {
    return Fail("enforce-demands accepted a war belonging to other players");
  }
  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_war, 0x288, enemy_character_id);
  Store(g_war, 0x28C, std::int32_t{0x01000004});
  if (xar::ck3_11906::SubmitEnforceDemands(bindings, active_war_id) !=
      xar::ck3_11906::EnforceDemandsResult::player_not_war_leader) {
    return Fail("enforce-demands accepted a participating non-war-leader");
  }
  Store(g_war, 0x288, played_character_id);
  Store(g_war, 0x28C, enemy_character_id);

  g_expected_command = ExpectedCommand::enforce_demands;
  g_interaction_validate_result = false;
  g_war_resolution_attacker_victory = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitEnforceDemands(bindings, active_war_id) !=
          xar::ck3_11906::EnforceDemandsResult::validation_failed ||
      g_submit_called || g_interaction_destroy_calls != 1 ||
      !g_war_resolution_attacker_victory) {
    return Fail("enforce-demands submitted after native validation failed");
  }
  g_interaction_validate_result = true;
  g_interaction_default_construct_called = false;
  g_war_resolution_construct_called = false;
  g_war_resolution_attacker_victory = false;
  g_send_interaction_construct_called = false;
  g_interaction_destroy_calls = 0;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitEnforceDemands(bindings, active_war_id) !=
          xar::ck3_11906::EnforceDemandsResult::submitted ||
      !g_interaction_default_construct_called ||
      !g_war_resolution_construct_called ||
      !g_war_resolution_attacker_victory ||
      !g_send_interaction_construct_called || !g_submit_called ||
      g_interaction_destroy_calls != 2) {
    return Fail("enforce-demands did not use native war-context queue lifecycle");
  }

  // The war-resolution context boolean is player-relative for both sides.
  // A primary defender must still surrender with false and enforce with true.
  Store(g_attacker_participant, 0x08, enemy_character_id);
  Store(g_defender_participant, 0x08, played_character_id);
  Store(g_war, 0x288, enemy_character_id);
  Store(g_war, 0x28C, played_character_id);
  g_expected_command = ExpectedCommand::surrender_war;
  g_war_resolution_attacker_victory = true;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSurrenderWar(bindings, active_war_id) !=
          xar::ck3_11906::SurrenderWarResult::submitted ||
      g_war_resolution_attacker_victory || !g_submit_called) {
    return Fail("primary defender surrender did not construct player defeat");
  }
  g_expected_command = ExpectedCommand::enforce_demands;
  g_war_resolution_attacker_victory = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitEnforceDemands(bindings, active_war_id) !=
          xar::ck3_11906::EnforceDemandsResult::submitted ||
      !g_war_resolution_attacker_victory || !g_submit_called) {
    return Fail("primary defender enforce did not construct player victory");
  }
  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_war, 0x288, played_character_id);
  Store(g_war, 0x28C, enemy_character_id);

  Store(jomini_state, 0x20, std::uint8_t{1});
  g_expected_command = ExpectedCommand::pause;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::already_paused ||
      g_submit_called) {
    return Fail("already-paused fixture should be idempotent");
  }

  g_expected_command = ExpectedCommand::resume;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("resume-map did not submit paused=false");
  }
  Store(jomini_state, 0x20, std::uint8_t{0});
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::already_running ||
      g_submit_called) {
    return Fail("already-running fixture should be idempotent");
  }

  bindings.enabled = false;
  if (xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("disabled build binding exposed game state");
  }
  std::cout << "PASS: snapshot=1 active_event_snapshot=1 "
               "pause_resume_command_layout=1 "
               "set_speed_zero_based_mapping=1 "
               "select_event_option_layout=1 auto_save_layout=1 "
               "pending_interaction_local_player_filter=1 "
               "pending_interaction_native_reply_validation=1 "
               "reply_character_interaction_layout=1 "
                "played_character_snapshot=1 alive_dead_projection=1 "
                "one_life_settlement_snapshot=1 "
                "dead_source_liveness_resolver_independent=1 "
               "fixed_point_scale=100000 "
               "war_army_snapshot=1 relative_war_score=1 "
               "army_strength_query=1 army_strength_partial_rows=1 "
               "combat_simulation_inputs_query=1 "
               "actual_contact_scope_v1=1 "
               "army_storage_pointer_slot=1 "
               "raise_troops_command=1 move_army_preview=1 "
               "move_army_command=1 "
               "disband_army_command=1 "
               "split_army_half_command=1 "
               "merge_armies_command=1 "
               "assault_snapshot=1 assault_commands=1 "
               "declarable_war_enumeration=1 "
               "declare_war_command=1 "
               "arrange_marriage_query=1 "
               "arrange_marriage_command=1 "
               "war_termination_query=1 surrender_war_command=1 "
               "offer_white_peace_command=1 "
               "enforce_demands_war_leader_filter=1 "
               "enforce_demands_command=1 "
               "map_ready_gate=1 exact_build_gate=1\n";
  return 0;
}

#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

struct Bindings;

// This is a frozen research contract, not an advertised capability.  The
// concrete command grammar is reserved here so that a later bridge hookup
// cannot silently change the request identity.
inline constexpr std::string_view kCombatPhaseEventTraceV1Capability =
    "game.command.query-combat-phase-event-trace-v1-N";
inline constexpr std::string_view kCombatPhaseEventTraceV1StepPrefix =
    "query-combat-phase-event-trace-v1-";
inline constexpr bool kCombatPhaseEventTraceV1CapabilityAdvertised = false;

inline constexpr std::int32_t kCombatPhaseEventTraceV1RowCount = 13;
inline constexpr std::int64_t kCombatPhaseEventTraceV1FixedScale = 100'000;
inline constexpr std::string_view kRandomSideKnightOrderPolicyV1 =
    "ccombat_side_knight_source_then_tail_swap_remove_v1";

inline constexpr std::array<std::string_view, 13>
    kCombatPhaseEventTraceV1StockKeys{
        "commander_none",
        "commander_wounded",
        "commander_maimed",
        "commander_killed",
        "knight_none",
        "knight_berserker_attack",
        "knight_become_berserker",
        "knight_shieldmaiden_attack",
        "knight_becomes_incapable",
        "knight_wounded",
        "knight_maimed",
        "knight_killed",
        "knight_qualify_for_accolade",
    };

inline constexpr std::array<std::int32_t, 13>
    kCombatPhaseEventTraceV1StockTypes{
        0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    };

inline constexpr std::array<std::int32_t, 13>
    kCombatPhaseEventTraceV1TypeLoadIndices{
        0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7, 8,
    };

} // namespace xar::ck3_11906

namespace xar::game {

struct PresentFullIdV1 {
  bool present = false;
  std::int32_t value = -1;

  friend bool operator==(const PresentFullIdV1 &,
                         const PresentFullIdV1 &) = default;
};

// A value row is evaluated for differential observation even when the stock
// selector would have short-circuited after a false trigger.  The two flags
// retain that distinction and prevent the differential from being mistaken
// for the selector's RNG/control-flow trace.
struct CombatPhaseEventNativeRowV1 {
  std::int32_t global_load_index = -1;
  std::int32_t type_load_index = -1;
  std::string event_key;
  std::string event_type;
  bool empty_effect = false;
  bool selector_role_applicable = false;
  bool trigger_valid = false;
  bool chance_evaluated_for_differential = false;
  bool selector_would_evaluate_chance = false;
  std::int64_t chance_raw = 0;
  std::int32_t int_weight = 0;
  bool positive_weight = false;
  bool selector_eligible = false;

  friend bool operator==(const CombatPhaseEventNativeRowV1 &,
                         const CombatPhaseEventNativeRowV1 &) = default;
};

// This first reader deliberately publishes only the directly closed mutable
// core.  It is not the final transition bundle: injury/trait ranks, trait-track
// XP, accolade progress, the thirteen unlock variables and participant detach
// state remain explicit production gates in the ABI ledger.
struct CombatPhaseEventCharacterCoreStateV1 {
  std::int32_t character_id = -1;
  bool native_valid = false;
  bool death_marker_present = false;
  bool alive = false;
  std::int32_t martial = 0;
  std::int32_t learning = 0;
  std::int32_t prowess = 0;
  PresentFullIdV1 current_regiment;
  bool current_regiment_back_reference_matches = false;
  std::string state_bundle_stage =
      "core_identity_skills_and_regiment_membership";
  bool transition_state_complete = false;

  friend bool
  operator==(const CombatPhaseEventCharacterCoreStateV1 &,
             const CombatPhaseEventCharacterCoreStateV1 &) = default;
};

struct CombatPhaseEventCharacterTraceV1 {
  std::int32_t character_id = -1;
  std::int32_t side_index = -1;
  bool ordered_army_commander = false;
  bool selected_side_commander = false;
  bool ordered_knight = false;
  std::vector<std::int32_t> source_army_ids;
  std::vector<std::int32_t> source_regiment_ids;
  CombatPhaseEventCharacterCoreStateV1 core_state;
  std::array<CombatPhaseEventNativeRowV1, 13> event_rows;

  friend bool operator==(const CombatPhaseEventCharacterTraceV1 &,
                         const CombatPhaseEventCharacterTraceV1 &) = default;
};

struct CombatPhaseEventCommanderSlotV1 {
  std::int32_t source_army_id = -1;
  PresentFullIdV1 character;

  friend bool operator==(const CombatPhaseEventCommanderSlotV1 &,
                         const CombatPhaseEventCommanderSlotV1 &) = default;
};

struct CombatPhaseEventKnightSlotV1 {
  std::int32_t source_regiment_id = -1;
  std::int32_t source_army_id = -1;
  PresentFullIdV1 character;

  friend bool operator==(const CombatPhaseEventKnightSlotV1 &,
                         const CombatPhaseEventKnightSlotV1 &) = default;
};

struct CombatPhaseEventRetainedScheduleRowV1 {
  std::int32_t side_index = -1;
  std::int32_t retained_order = -1;
  std::string dispatch_role;
  std::string event_key;
  PresentFullIdV1 source_regiment;
  PresentFullIdV1 current_character;
  bool current_combat_association_matches = false;
  std::string lifecycle_state =
      "retained_row_occurrence_requires_managed_before_after";

  friend bool
  operator==(const CombatPhaseEventRetainedScheduleRowV1 &,
             const CombatPhaseEventRetainedScheduleRowV1 &) = default;
};

struct CombatPhaseEventSideTraceV1 {
  std::int32_t side_index = -1;
  bool is_attacker = false;
  std::vector<std::int32_t> ordered_army_ids;
  std::vector<CombatPhaseEventCommanderSlotV1> ordered_commander_slots;
  std::vector<std::int32_t> ordered_commander_character_ids;
  std::vector<CombatPhaseEventKnightSlotV1> ordered_knight_slots;
  std::vector<std::int32_t> ordered_knight_character_ids;
  PresentFullIdV1 selected_commander;
  std::string retained_commander_schedule_state;
  std::vector<CombatPhaseEventRetainedScheduleRowV1>
      retained_nonempty_schedule_rows;

  friend bool operator==(const CombatPhaseEventSideTraceV1 &,
                         const CombatPhaseEventSideTraceV1 &) = default;
};

struct CombatPhaseEventCadenceCharacterV1 {
  std::int32_t character_id = -1;
  std::int32_t side_index = -1;
  bool selected_commander_role = false;
  bool knight_role = false;
  std::uint32_t unsigned_sum = 0;
  std::uint32_t residue = 0;
  bool schedule_due = false;

  friend bool operator==(const CombatPhaseEventCadenceCharacterV1 &,
                         const CombatPhaseEventCadenceCharacterV1 &) = default;
};

struct CombatPhaseEventCadenceV1 {
  std::int32_t native_date_raw = 0;
  std::int32_t epoch_raw = 0x029C55A8;
  std::int32_t date_units_per_day = 24;
  std::int32_t day_index = 0;
  std::uint32_t period_days = 0;
  bool current_phase_fires_events = false;
  std::array<std::int32_t, 2> side_fire_order{0, 1};
  std::int32_t global_rng_draws_per_side_fire = 1;
  std::vector<CombatPhaseEventCadenceCharacterV1> characters;

  friend bool operator==(const CombatPhaseEventCadenceV1 &,
                         const CombatPhaseEventCadenceV1 &) = default;
};

struct CombatPhaseEventGlobalRngV1 {
  std::uint32_t counter = 0;
  std::uint32_t salt = 0;
  std::uint32_t owner_thread_token = 0;
  std::uint32_t next_draw31 = 0;
  bool wrapper_and_state_identity_stable = false;
  bool unchanged_by_probe = false;

  friend bool operator==(const CombatPhaseEventGlobalRngV1 &,
                         const CombatPhaseEventGlobalRngV1 &) = default;
};

// The list builder and the random-in-list effect do not preserve source order
// after a failed limit.  They append CCombatSide knight rows in source order,
// then reject a row by moving the current tail into that row and rechecking the
// same index.  Keeping this as a named contract prevents an offline evaluator
// from silently substituting stable erase.
struct CombatPhaseEventRandomSideKnightOrderV1 {
  std::string policy = "ccombat_side_knight_source_then_tail_swap_remove_v1";
  std::string source_materialization =
      "ccombat_side_plus_0x40_stride_0x60_regiment_to_character_source_order";
  std::string limit_compaction =
      "rejected_row_replaced_by_current_tail_then_same_index_rechecked";
  std::string materialize_call_schedule =
      "source_predicate_plus_0x60_then_plus_0x220_array_with_shared_plus_0x140";
  std::string predicate_evaluation_order =
      "shared_r8_then_source_rdx_empty_trigger_is_true";
  std::string selection_iteration = "post_compaction_vector_order";
  std::string weight_quantization =
      "signed_low_int32_no_clamp_positive_q100000_remainder_rounds_up";
  bool exact_build_chain_static_closed = true;
  bool source_vector_runtime_reader_ready = false;
  bool combat_inputs_v3_source_vector_equivalence_ready = false;
  bool ast_policy_implementation_verified = false;

  friend bool
  operator==(const CombatPhaseEventRandomSideKnightOrderV1 &,
             const CombatPhaseEventRandomSideKnightOrderV1 &) = default;
};

// These rows are retained by the Battle result object.  They are exact
// read-only records, but a row is intentionally not labelled as originating
// from one of the thirteen phase events until a managed boundary delta proves
// that association.
struct CombatPhaseRetainedBattleEventV1 {
  std::int32_t retained_order = -1;
  PresentFullIdV1 left_character;
  PresentFullIdV1 right_character;
  std::string stable_key;
  std::int32_t type_raw = 0;
  std::int32_t side_index = -1;
  bool is_attacker_side = false;
  bool target_right = false;
  bool character_identities_resolve = false;
  std::string storage_association = "combat_battle_result_exact_generation";
  std::string phase_event_origin =
      "unclassified_without_managed_boundary_delta";

  friend bool operator==(const CombatPhaseRetainedBattleEventV1 &,
                         const CombatPhaseRetainedBattleEventV1 &) = default;
};

struct CombatPhaseBattleEventLedgerV1 {
  PresentFullIdV1 battle_result;
  bool storage_identity_matches = false;
  bool retained_storage_reader_ready = false;
  std::vector<CombatPhaseRetainedBattleEventV1> retained_rows;

  friend bool operator==(const CombatPhaseBattleEventLedgerV1 &,
                         const CombatPhaseBattleEventLedgerV1 &) = default;
};

// This is a frozen contract for the future controlled one-day trace.  The six
// intermediate records are native call-boundary captures, not UI pauses.  A
// bounded hook must copy them into preallocated query-owned storage and return
// without pausing CK3 or re-entering the bridge.  Only the final record is a
// normal paused query.  The explicit sequence keeps date polling from
// masquerading as an after-side0/after-side1 observation.
struct CombatPhaseEventManagedBoundaryContractV1 {
  std::string contract = "native_daily_phase_event_boundaries_v1";
  std::array<std::string, 7> required_snapshot_sequence{
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "native_capture_after_side1_schedule_return_0x27FB5AC",
      "native_capture_before_side0_phase_fire_entry_0x23C9900",
      "native_capture_after_side0_phase_fire_return_0x2309EF7",
      "native_capture_before_side1_phase_fire_entry_0x23C9900",
      "native_capture_after_side1_phase_fire_return_0x2309EFF",
      "paused_next_day_stable_query",
  };
  std::vector<std::string> required_delta_domains{
      "retained_schedule_rows",
      "retained_battle_event_rows",
      "schedule_local_rng_state_and_counter",
      "global_rng_state_and_counter",
      "character_full_mutable_state",
      "combat_side_participant_membership",
      "side_strength_and_advantage",
  };
  std::string capture_transport =
      "preallocated_query_owned_ring_buffer_no_pause_no_bridge_reentry";
  std::string side_fire_identity_rule =
      "0x23C9900_entry_correlated_by_actual_side_pointer_and_return_site";
  std::string sequence_correlation_rule =
      "same_full_generation_combat_id_native_date_and_daily_sequence_token";
  std::string occurrence_label_rule =
      "only_native_boundary_delta_may_label_occurred_skipped_or_no_op";
  bool same_combat_generation_required = true;
  bool same_loaded_event_table_required = true;
  bool native_boundary_hook_required = true;
  bool native_boundary_hook_ready = false;
  bool controlled_daily_before_after_ready = false;

  friend bool
  operator==(const CombatPhaseEventManagedBoundaryContractV1 &,
             const CombatPhaseEventManagedBoundaryContractV1 &) = default;
};

struct CombatPhaseEventOccurrenceBoundaryV1 {
  std::string pure_snapshot_semantics =
      "retained_schedule_and_generic_battle_event_rows_only";
  std::string occurrence_state =
      "not_observed_without_managed_daily_before_after";
  bool managed_daily_before_after_required = true;
  bool managed_daily_before_after_ready = false;
  bool battle_event_storage_reader_ready = false;
  std::string retained_battle_event_semantics =
      "generic_battle_ledger_not_phase_origin_without_boundary_delta";

  friend bool
  operator==(const CombatPhaseEventOccurrenceBoundaryV1 &,
             const CombatPhaseEventOccurrenceBoundaryV1 &) = default;
};

struct CombatPhaseEventTraceV1 {
  bool evaluator_probe_ready = false;
  bool production_trace_ready = false;
  std::int32_t combat_id = -1;
  std::int32_t date_raw = 0;
  std::int32_t target_province_id = -1;
  std::int32_t phase_raw = -1;
  std::string phase;
  std::int32_t phase_day = -1;
  PresentFullIdV1 winner_side;
  std::array<CombatPhaseEventSideTraceV1, 2> sides;
  std::vector<CombatPhaseEventCharacterTraceV1> characters;
  CombatPhaseEventCadenceV1 cadence;
  CombatPhaseEventGlobalRngV1 global_rng;
  CombatPhaseEventRandomSideKnightOrderV1 random_side_knight_order;
  CombatPhaseBattleEventLedgerV1 battle_events;
  CombatPhaseEventManagedBoundaryContractV1 managed_boundary_contract;
  CombatPhaseEventOccurrenceBoundaryV1 occurrence_boundary;
  bool real_combat_side_scope = false;
  bool all_scope_teardowns_complete = false;
  bool same_paused_frame_stable = false;
  std::vector<std::string> missing_production_readers;
  std::string unavailable_reason;

  friend bool operator==(const CombatPhaseEventTraceV1 &,
                         const CombatPhaseEventTraceV1 &) = default;
};

enum class ReadCombatPhaseEventTraceV1Result {
  available,
  evaluator_probe_available,
  requires_paused,
  invalid_combat_id,
  combat_not_found,
  combat_state_invalid,
  event_database_unavailable,
  event_table_mismatch,
  roster_unavailable,
  schedule_unavailable,
  battle_event_storage_unavailable,
  rng_unavailable,
  character_state_unavailable,
  native_evaluator_unavailable,
  scope_teardown_failed,
  atomicity_failed,
  unavailable,
};

} // namespace xar::game

namespace xar::ck3_11906 {

// Research-only exact-build reader.  It never invokes the weighted selector,
// schedule builder, event dispatcher, effect executor or RNG draw entrypoint.
// A future production command may call this only after the missing transition
// readers listed in the output and ABI ledger are closed.
game::ReadCombatPhaseEventTraceV1Result ReadCombatPhaseEventTraceV1Probe(
    const Bindings &bindings, std::int32_t combat_id,
    game::CombatPhaseEventTraceV1 &output) noexcept;

} // namespace xar::ck3_11906

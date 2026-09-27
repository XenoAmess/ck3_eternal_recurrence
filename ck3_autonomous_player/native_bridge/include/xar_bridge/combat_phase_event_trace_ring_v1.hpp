#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace xar::ck3_11906 {

// Research-only capture transport for the seven records frozen by
// native_daily_phase_event_boundaries_v1.  None of these constants advertise
// a bridge capability.  The capture plan and every record are fixed-width POD
// so the two native hooks can only perform bounded reads/copies while CK3 is
// on the original call stack.
inline constexpr std::uint32_t kCombatPhaseEventTraceRingV1AbiVersion = 1;
inline constexpr std::size_t kCombatPhaseEventTraceRingV1RecordCount = 7;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumArmiesPerSide = 256;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumTrackedArmies = 512;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide = 2'048;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumHardOwnersPerSide = 256;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumTrackedRegiments = 4'096;
inline constexpr std::size_t kCombatPhaseEventTraceRingV1MaximumCharacters =
    4'096;
inline constexpr std::size_t kCombatPhaseEventTraceRingV1MaximumAccolades =
    4'096;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumAccoladeThresholds = 64;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1MaximumBattleEvents = 4'096;
inline constexpr std::size_t
    kCombatPhaseEventTraceRingV1BattleEventKeyBytes = 128;

inline constexpr std::uintptr_t kCombatPhaseEventScheduleFunctionRva =
    0x23C8750;
inline constexpr std::uintptr_t kCombatPhaseEventFireFunctionRva = 0x23C9900;
inline constexpr std::uintptr_t kCombatPhaseEffectDispatchFunctionRva = 0x3380A00;
inline constexpr std::uintptr_t kCombatPhaseKnightSelectFunctionRva = 0x33E8D40;
// The first three complete instructions after 0x2F08780's early-exit branch.
// The entry itself contains a relative branch and cannot use the 15-byte
// position-independent trampoline shared by the other research hooks.
inline constexpr std::uintptr_t kCombatRandomListWeightHookRva = 0x2F08789;
inline constexpr std::uintptr_t kCombatOutgoingDamageFunctionRva = 0x23CB1D0;
inline constexpr std::uintptr_t kCombatJoinWrapperFunctionRva = 0x23040A0;
inline constexpr std::uintptr_t kCombatPostCounterAttackCaptureRva = 0x23CB435;
inline constexpr std::uintptr_t kCombatOutgoingDamageSide0ReturnRva =
    0x2309F98;
inline constexpr std::uintptr_t kCombatOutgoingDamageSide1ReturnRva =
    0x2309FB4;
inline constexpr std::uintptr_t kCombatPhaseEventScheduleSide0ReturnRva =
    0x27FB594;
inline constexpr std::uintptr_t kCombatPhaseEventScheduleSide1ReturnRva =
    0x27FB5AC;
inline constexpr std::uintptr_t kCombatPhaseEventFireSide0ReturnRva =
    0x2309EF7;
inline constexpr std::uintptr_t kCombatPhaseEventFireSide1ReturnRva =
    0x2309EFF;

enum class CombatPhaseEventTraceBoundaryV1 : std::uint32_t {
  before_side0_schedule = 0,
  after_side1_schedule = 1,
  before_side0_phase_fire = 2,
  after_side0_phase_fire = 3,
  before_side1_phase_fire = 4,
  after_side1_phase_fire = 5,
  paused_next_day_stable_query = 6,
};

inline constexpr std::array<const char *, 7>
    kCombatPhaseEventTraceBoundaryNamesV1{
        "native_capture_before_side0_schedule_call_0x27FB58F",
        "native_capture_after_side1_schedule_return_0x27FB5AC",
        "native_capture_before_side0_phase_fire_entry_0x23C9900",
        "native_capture_after_side0_phase_fire_return_0x2309EF7",
        "native_capture_before_side1_phase_fire_entry_0x23C9900",
        "native_capture_after_side1_phase_fire_return_0x2309EFF",
        "paused_next_day_stable_query",
    };

enum CombatPhaseEventTraceCaptureFailureV1 : std::uint32_t {
  trace_capture_failure_none = 0,
  trace_capture_failure_not_armed = 1U << 0,
  trace_capture_failure_reentry = 1U << 1,
  trace_capture_failure_ring_full = 1U << 2,
  trace_capture_failure_sequence = 1U << 3,
  trace_capture_failure_identity = 1U << 4,
  trace_capture_failure_container = 1U << 5,
  trace_capture_failure_capacity = 1U << 6,
  trace_capture_failure_string = 1U << 7,
  trace_capture_failure_memory_fault = 1U << 8,
  trace_capture_failure_original_trampoline = 1U << 9,
  trace_capture_failure_final_query = 1U << 10,
  trace_capture_failure_rng_scope = 1U << 11,
  trace_capture_failure_outgoing_damage = 1U << 12,
  trace_capture_failure_post_counter_attack = 1U << 13,
  trace_capture_failure_effect_root = 1U << 14,
  trace_capture_failure_knight_select = 1U << 15,
  trace_capture_failure_effect_node = 1U << 16,
  trace_capture_failure_random_list_weight = 1U << 17,
  trace_capture_failure_join_width = 1U << 18,
  trace_capture_failure_join_full_entry = 1U << 19,
};

inline constexpr std::size_t kCombatPhaseEffectRootMaximumRecordsV1 = 64;

struct CombatPhaseEffectRootRecordV1 {
  std::int32_t side_index = -1;
  std::int32_t native_event_load_index = -1;
  std::uintptr_t node_identity = 0;
  std::uint32_t node_hash = 0;
  std::uint32_t counter_before = 0;
  std::uint32_t salt_before = 0;
  std::uint32_t counter_after = 0;
  std::uint32_t salt_after = 0;
};

inline constexpr std::size_t kCombatPhaseEffectNodeMaximumRecordsV1 = 256;

struct CombatPhaseEffectNodeRecordV1 {
  std::int32_t side_index = -1;
  std::int32_t native_event_load_index = -1;
  std::uint32_t call_index = 0;
  std::uint32_t depth = 0;
  std::uintptr_t node_identity = 0;
  std::uintptr_t parent_node_identity = 0;
  std::uint32_t node_hash = 0;
  std::uint32_t node_vtable_rva = 0;
  std::uint32_t counter_before = 0;
  std::uint32_t salt_before = 0;
  std::uint32_t counter_after = 0;
  std::uint32_t salt_after = 0;
};

inline constexpr std::size_t kCombatRandomListWeightMaximumRecordsV1 = 64;
inline constexpr std::size_t kCombatRandomListWeightMaximumEntriesV1 = 16;

struct CombatRandomListWeightRecordV1 {
  std::int32_t side_index = -1;
  std::int32_t native_event_load_index = -1;
  std::uintptr_t effect_node_identity = 0;
  std::uint32_t entry_count = 0;
  std::int32_t pick_count = 0;
  std::array<std::int32_t, kCombatRandomListWeightMaximumEntriesV1>
      weights{};
  std::array<std::uintptr_t, kCombatRandomListWeightMaximumEntriesV1>
      entry_node_identities{};
  std::uint32_t selected_entry_count = 0;
  std::array<std::uintptr_t, kCombatRandomListWeightMaximumEntriesV1>
      selected_entry_identities{};
  std::uint32_t child_counter_before = 0;
  std::uint32_t child_salt_before = 0;
  std::uint32_t child_counter_after = 0;
  std::uint32_t child_salt_after = 0;
};

// Three candidate-specific samples in chronological order: wrapper entry,
// wrapper return (after the merge), and first side-0 outgoing calculator call.
struct CombatJoinWidthRecordV1 {
  std::uint32_t boundary = 0;
  std::uint32_t thread_id = 0;
  std::int32_t native_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t army_id = -1;
  std::int32_t side_index = -1; // Unknown until native side roster is updated.
  std::int32_t phase_day = -1;
  std::int32_t base_width = 0;
  std::int32_t final_width = 0;
  std::int32_t outgoing_width_argument = -1;
  std::array<std::int64_t, 2> side_fighting_total_raw{};
};

// Private, default-off diagnosis for the first target-join capture failure.
// The value is evidence of the guard that rejected a sample, not a game rule.
enum CombatJoinWidthFailureCodeV1 : std::uint32_t {
  join_width_failure_none = 0,
  join_width_failure_order = 1,
  join_width_failure_army_id = 2,
  join_width_failure_date_object = 3,
  join_width_failure_combat_id = 4,
  join_width_failure_owner_thread = 5,
  join_width_failure_side_backpointer = 6,
  join_width_failure_side_roster = 7,
  join_width_failure_side_identity = 8,
  join_width_failure_width_argument = 9,
  join_width_failure_memory_fault = 10,
  join_width_failure_cross_boundary_date = 11,
};

// Private 080 wrapper entry/return snapshot. Counts are published only after
// the entire bounded read succeeds; a failed read never claims a partial list.
enum CombatJoinFullEntryFailureCodeV1 : std::uint32_t {
  join_full_entry_failure_none = 0,
  join_full_entry_failure_width_gate = 1,
  join_full_entry_failure_order = 2,
  join_full_entry_failure_identity = 3,
  join_full_entry_failure_date_or_thread = 4,
  join_full_entry_failure_container = 5,
  join_full_entry_failure_capacity = 6,
  join_full_entry_failure_duplicate = 7,
  join_full_entry_failure_arithmetic = 8,
  join_full_entry_failure_memory_fault = 9,
};

struct CombatJoinFullEntryRegimentV1 {
  std::int32_t regiment_id = -1;
  std::int32_t army_id = -1;
  std::uint32_t bucket = 0;
  std::uint32_t bucket_index = 0;
  std::int64_t starting_raw = 0;
  std::int64_t current_raw = 0;
  std::int64_t soft_raw = 0;
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;
};

struct CombatJoinFullEntrySideV1 {
  std::int64_t cached_fighting_total_raw = 0;
  std::int64_t cached_first_bucket_raw = 0;
  std::int64_t entry_current_sum_raw = 0;
  std::int64_t cache_minus_entry_raw = 0;
  std::uint32_t army_count = 0;
  std::array<std::int32_t,
             kCombatPhaseEventTraceRingV1MaximumArmiesPerSide> army_ids{};
  std::uint32_t entry_count = 0;
  std::array<CombatJoinFullEntryRegimentV1,
             kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide> entries{};
};

struct CombatJoinFullEntryIncomingRegimentV1 {
  std::int32_t regiment_id = -1;
  std::int32_t basic_soldiers = 0;
};

struct CombatJoinFullEntryRecordV1 {
  std::uint32_t boundary = 0; // 0 wrapper entry; 1 normal return.
  std::uint32_t thread_id = 0;
  std::int32_t native_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t incoming_army_id = -1;
  std::int32_t joined_side_index = -1; // Only resolved at normal return.
  std::array<CombatJoinFullEntrySideV1, 2> sides{};
  std::uint32_t incoming_regiment_count = 0;
  std::array<CombatJoinFullEntryIncomingRegimentV1,
             kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide>
      incoming_regiments{};
};

inline constexpr std::size_t kCombatPhaseKnightSelectMaximumRecordsV1 = 64;

struct CombatPhaseKnightSelectRecordV1 {
  std::int32_t side_index = -1;
  std::int32_t native_event_load_index = -1;
  std::int32_t candidate_count = -1;
  std::int32_t selected_index = -1;
  std::uintptr_t selected_candidate_word0 = 0;
  std::uintptr_t selected_candidate_word1 = 0;
  std::uint32_t counter_before = 0;
  std::uint32_t salt_before = 0;
  std::uint32_t counter_after = 0;
  std::uint32_t salt_after = 0;
};

struct CombatPhaseEventTraceObjectRefV1 {
  std::int32_t full_id = -1;
  std::uintptr_t object = 0;

  friend bool operator==(const CombatPhaseEventTraceObjectRefV1 &,
                         const CombatPhaseEventTraceObjectRefV1 &) = default;
};

struct CombatPhaseEventTraceAccoladePlanRowV1 {
  std::int32_t accolade_id = -1;
  std::uintptr_t accolade = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t acclaimed_knight_character_id = -1;
  std::uintptr_t acclaimed_knight = 0;

  friend bool
  operator==(const CombatPhaseEventTraceAccoladePlanRowV1 &,
             const CombatPhaseEventTraceAccoladePlanRowV1 &) = default;
};

struct CombatPhaseEventTraceCapturePlanV1 {
  std::uint32_t abi_version = kCombatPhaseEventTraceRingV1AbiVersion;
  std::uint64_t managed_daily_sequence_token = 0;
  std::uintptr_t module_base = 0;
  std::int32_t combat_id = -1;
  std::uintptr_t combat = 0;
  // Private, explicit opt-in. The default seven-boundary wire is unchanged.
  bool capture_runtime_random_list_weights = false;
  // Private candidate-specific join probe. No field is added to default wire.
  bool capture_runtime_join_width = false;
  bool capture_runtime_join_full_entries = false;
  std::int32_t candidate_joining_army_id = -1;
  std::uint32_t owner_thread_id = 0;
  std::array<std::uintptr_t, 2> sides{};

  // These are addresses of native pointer slots, not snapshots of their
  // contents. The paused frame need not own an RNG state. The original tick
  // hook latches the first state owned by its current thread; later non-null
  // states must match it. Null schedule/final records remain explicit.
  std::uintptr_t phase_event_database_slot = 0;
  std::uintptr_t expected_phase_event_database = 0;
  // Paused-only copy of the exact 13 native event-object pointers in load
  // order. Hook records keep opaque identities; wire projection resolves
  // them after drain without dereferencing an event object on the game stack.
  bool loaded_event_row_objects_available = false;
  std::array<std::uintptr_t, 13> loaded_event_row_objects{};
  std::uintptr_t current_date_slot = 0;
  std::uintptr_t expected_current_date_object = 0;
  std::uintptr_t global_rng_wrapper_slot = 0;
  std::uintptr_t expected_global_rng_wrapper = 0;
  std::uintptr_t expected_global_rng_state = 0;

  std::int32_t battle_result_id = -1;
  std::uintptr_t battle_result = 0;
  std::uintptr_t expected_battle_event_vtable = 0;

  // The managed paused reader resolves these full-generation objects before
  // arming the ring.  Arrays must be strictly increasing by full_id.  Hook
  // code performs only a bounded binary search and direct identity reads; it
  // never resolves a component through CK3 stores or calls a game helper.
  std::uint32_t army_count = 0;
  std::array<CombatPhaseEventTraceObjectRefV1,
             kCombatPhaseEventTraceRingV1MaximumTrackedArmies>
      armies{};
  std::uint32_t regiment_count = 0;
  std::array<CombatPhaseEventTraceObjectRefV1,
             kCombatPhaseEventTraceRingV1MaximumTrackedRegiments>
      regiments{};
  std::uint32_t character_count = 0;
  std::array<CombatPhaseEventTraceObjectRefV1,
             kCombatPhaseEventTraceRingV1MaximumCharacters>
      characters{};

  // 0x251B780 reads an int64 threshold vector from module+0x4F62B98 and
  // count from module+0x4F62BA4.  The paused arm phase copies the bounded
  // vector; every hook record revalidates both native slots and every value,
  // then mirrors the descending rank scan without calling the helper.
  std::uintptr_t accolade_rank_threshold_data_slot = 0;
  std::uintptr_t expected_accolade_rank_threshold_data = 0;
  std::uintptr_t accolade_rank_threshold_count_slot = 0;
  std::uint32_t accolade_rank_threshold_count = 0;
  std::array<std::int64_t,
             kCombatPhaseEventTraceRingV1MaximumAccoladeThresholds>
      accolade_rank_thresholds_raw{};
  std::uint32_t accolade_count = 0;
  std::array<CombatPhaseEventTraceAccoladePlanRowV1,
             kCombatPhaseEventTraceRingV1MaximumAccolades>
      accolades{};

  friend bool operator==(const CombatPhaseEventTraceCapturePlanV1 &,
                         const CombatPhaseEventTraceCapturePlanV1 &) = default;
};

struct CombatPhaseEventTraceArmyRowV1 {
  std::int32_t army_id = -1;
  std::int32_t commander_character_id = -1;
  std::int32_t combat_id = -1;

  friend bool operator==(const CombatPhaseEventTraceArmyRowV1 &,
                         const CombatPhaseEventTraceArmyRowV1 &) = default;
};

struct CombatPhaseEventTraceKnightRowV1 {
  std::int32_t regiment_id = -1;
  std::int32_t army_id = -1;
  std::int32_t character_id = -1;

  friend bool operator==(const CombatPhaseEventTraceKnightRowV1 &,
                         const CombatPhaseEventTraceKnightRowV1 &) = default;
};

struct CombatPhaseEventTraceScheduleRowV1 {
  std::uintptr_t event_identity = 0;
  std::int32_t regiment_id = -1;
  std::int32_t current_character_id = -1;

  friend bool operator==(const CombatPhaseEventTraceScheduleRowV1 &,
                         const CombatPhaseEventTraceScheduleRowV1 &) = default;
};

struct CombatPhaseEventTraceRegimentRowV1 {
  std::int32_t regiment_id = -1;
  std::int32_t army_id = -1;
  std::int32_t bucket_index = -1;
  bool men_at_arms = false;
  bool fights_in_main_phase = false;
  std::int64_t starting_raw = 0;
  std::int64_t current_fighting_raw = 0;
  std::int64_t soft_casualties_raw = 0;
  // Only retained main-phase fighters have a derivable per-entry hard loss.
  bool hard_casualties_available = false;
  std::int64_t hard_casualties_raw = 0;
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;

  friend bool operator==(const CombatPhaseEventTraceRegimentRowV1 &,
                         const CombatPhaseEventTraceRegimentRowV1 &) = default;
};

struct CombatPhaseEventTraceHardOwnerRowV1 {
  std::int32_t character_id = -1;
  std::int64_t hard_casualties_raw = 0;

  friend bool operator==(const CombatPhaseEventTraceHardOwnerRowV1 &,
                         const CombatPhaseEventTraceHardOwnerRowV1 &) = default;
};

struct CombatPhaseEventTraceSideRecordV1 {
  std::uintptr_t side = 0;
  std::int32_t side_index = -1;
  std::int32_t selected_commander_character_id = -1;
  std::int64_t current_fighting_total_raw = 0;
  std::int64_t first_fighting_subtotal_raw = 0;
  std::uintptr_t scheduled_commander_event_identity = 0;
  std::uint32_t army_count = 0;
  std::array<CombatPhaseEventTraceArmyRowV1,
             kCombatPhaseEventTraceRingV1MaximumArmiesPerSide>
      armies{};
  // Native bucket order is levy rows followed by men-at-arms rows.
  std::uint32_t regiment_count = 0;
  std::array<CombatPhaseEventTraceRegimentRowV1,
             kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide>
      regiments{};
  std::uint32_t hard_owner_count = 0;
  std::array<CombatPhaseEventTraceHardOwnerRowV1,
             kCombatPhaseEventTraceRingV1MaximumHardOwnersPerSide>
      hard_owners{};
  std::uint32_t knight_count = 0;
  std::array<CombatPhaseEventTraceKnightRowV1,
             kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide>
      knights{};
  std::uint32_t scheduled_knight_count = 0;
  std::array<CombatPhaseEventTraceScheduleRowV1,
             kCombatPhaseEventTraceRingV1MaximumRegimentsPerSide>
      scheduled_knights{};

  friend bool operator==(const CombatPhaseEventTraceSideRecordV1 &,
                         const CombatPhaseEventTraceSideRecordV1 &) = default;
};

struct CombatPhaseEventTraceCharacterCoreRecordV1 {
  std::int32_t character_id = -1;
  std::uintptr_t character = 0;
  bool death_marker_present = false;
  std::int32_t martial = 0;
  std::int32_t learning = 0;
  std::int32_t prowess = 0;
  std::int32_t current_regiment_id = -1;
  bool current_regiment_back_reference_matches = false;

  friend bool
  operator==(const CombatPhaseEventTraceCharacterCoreRecordV1 &,
             const CombatPhaseEventTraceCharacterCoreRecordV1 &) = default;
};

struct CombatPhaseEventTraceBattleEventRecordV1 {
  std::int32_t left_character_id = -1;
  std::int32_t right_character_id = -1;
  std::int32_t type_raw = 0;
  std::int32_t side_index = -1;
  bool target_right = false;
  std::uint16_t stable_key_size = 0;
  std::array<char, kCombatPhaseEventTraceRingV1BattleEventKeyBytes>
      stable_key{};

  friend bool operator==(const CombatPhaseEventTraceBattleEventRecordV1 &,
                         const CombatPhaseEventTraceBattleEventRecordV1 &) =
      default;
};

struct CombatPhaseEventTraceAccoladeRecordV1 {
  std::int32_t accolade_id = -1;
  std::uintptr_t accolade = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t acclaimed_knight_character_id = -1;
  std::int64_t glory_raw = 0;
  std::int32_t rank_native_mirror = 1;
  bool participant_link_identity_matches = false;

  friend bool operator==(const CombatPhaseEventTraceAccoladeRecordV1 &,
                         const CombatPhaseEventTraceAccoladeRecordV1 &) =
      default;
};

struct CombatPhaseEventTraceRingRecordV1 {
  std::uint32_t abi_version = kCombatPhaseEventTraceRingV1AbiVersion;
  CombatPhaseEventTraceBoundaryV1 boundary =
      CombatPhaseEventTraceBoundaryV1::before_side0_schedule;
  std::uint32_t capture_failure_flags = trace_capture_failure_none;
  std::uint64_t managed_daily_sequence_token = 0;
  std::uintptr_t caller_return_address = 0;
  std::uintptr_t combat = 0;
  std::uintptr_t trigger_side = 0;
  std::uintptr_t phase_event_database = 0;
  std::uintptr_t current_date_object = 0;
  std::uintptr_t global_rng_wrapper = 0;
  std::uintptr_t global_rng_state = 0;
  std::uintptr_t battle_result = 0;
  std::int32_t combat_id = -1;
  std::int32_t native_date_raw = 0;
  std::int32_t phase_raw = -1;
  std::int32_t phase_day = -1;
  std::int32_t winner_side_raw = -1;
  std::int32_t battle_result_id = -1;
  std::int64_t base_advantage_raw = 0;
  std::int64_t resolved_advantage_raw = 0;
  std::array<std::int32_t, 2> advantage_rolls_raw{};

  bool schedule_local_rng_present = false;
  std::uint32_t schedule_local_rng_word0 = 0;
  std::uint32_t schedule_local_rng_word1 = 0;
  std::uint32_t global_rng_counter = 0;
  std::uint32_t global_rng_salt = 0;
  std::uint32_t global_rng_owner_thread_token = 0;

  std::array<CombatPhaseEventTraceSideRecordV1, 2> sides{};
  std::uint32_t character_count = 0;
  std::array<CombatPhaseEventTraceCharacterCoreRecordV1,
             kCombatPhaseEventTraceRingV1MaximumCharacters>
      characters{};
  std::uint32_t battle_event_count = 0;
  std::array<CombatPhaseEventTraceBattleEventRecordV1,
             kCombatPhaseEventTraceRingV1MaximumBattleEvents>
      battle_events{};
  std::uint32_t accolade_count = 0;
  std::array<CombatPhaseEventTraceAccoladeRecordV1,
             kCombatPhaseEventTraceRingV1MaximumAccolades>
      accolades{};

  // Ordered retained regiment current/soft and owner-hard rows are copied,
  // but outgoing damage/conversion and complete event-effect feedback are not.
  // Keep this false until those inputs and a managed live parity fixture close.
  bool full_mutable_transition_bundle_complete = false;

  friend bool operator==(const CombatPhaseEventTraceRingRecordV1 &,
                         const CombatPhaseEventTraceRingRecordV1 &) = default;
};

struct CombatPhaseEventTraceRingV1 {
  std::atomic<std::uint32_t> armed{0};
  std::atomic<std::uint32_t> capture_in_progress{0};
  std::atomic<std::uint32_t> committed_count{0};
  std::atomic<std::uint32_t> outgoing_damage_count{0};
  std::atomic<std::uint32_t> post_counter_attack_count{0};
  std::atomic<std::uint32_t> effect_root_count{0};
  std::atomic<std::uint32_t> effect_node_call_count{0};
  std::atomic<std::uint32_t> effect_node_draw_count{0};
  std::atomic<std::uint32_t> random_list_weight_count{0};
  std::atomic<std::uint32_t> join_width_count{0};
  std::atomic<std::uint32_t> join_width_join_thread_id{0};
  std::atomic<std::uint32_t> join_width_first_failure_code{
      join_width_failure_none};
  std::atomic<std::uint32_t> join_full_entry_count{0};
  std::atomic<std::uint32_t> join_full_entry_first_failure_code{
      join_full_entry_failure_none};
  std::atomic<std::uint32_t> knight_select_count{0};
  std::atomic<std::uint32_t> failure_flags{trace_capture_failure_none};
  CombatPhaseEventTraceCapturePlanV1 plan{};
  std::array<std::int64_t, 2> outgoing_damage_raw{};
  std::array<std::int64_t, 2> post_counter_attack_raw{};
  std::array<CombatPhaseEffectRootRecordV1,
             kCombatPhaseEffectRootMaximumRecordsV1> effect_roots{};
  std::array<CombatPhaseEffectNodeRecordV1,
             kCombatPhaseEffectNodeMaximumRecordsV1> effect_node_draws{};
  std::array<CombatRandomListWeightRecordV1,
             kCombatRandomListWeightMaximumRecordsV1> random_list_weights{};
  std::array<CombatJoinWidthRecordV1, 3> join_widths{};
  std::array<CombatJoinFullEntryRecordV1, 2> join_full_entries{};
  std::array<CombatPhaseKnightSelectRecordV1,
             kCombatPhaseKnightSelectMaximumRecordsV1> knight_selects{};
  std::array<CombatPhaseEventTraceRingRecordV1,
             kCombatPhaseEventTraceRingV1RecordCount>
      records{};
};

struct CombatPhaseEventTraceRingDrainV1 {
  bool loaded_event_row_objects_available = false;
  std::array<std::uintptr_t, 13> loaded_event_row_objects{};
  std::uint32_t failure_flags = trace_capture_failure_none;
  std::uint32_t record_count = 0;
  std::uint32_t outgoing_damage_count = 0;
  std::array<std::int64_t, 2> outgoing_damage_raw{};
  bool outgoing_damage_pair_complete = false;
  std::uint32_t post_counter_attack_count = 0;
  std::array<std::int64_t, 2> post_counter_attack_raw{};
  bool post_counter_attack_pair_complete = false;
  std::uint32_t effect_root_count = 0;
  std::array<CombatPhaseEffectRootRecordV1,
             kCombatPhaseEffectRootMaximumRecordsV1> effect_roots{};
  std::uint32_t effect_node_call_count = 0;
  std::uint32_t effect_node_draw_count = 0;
  std::array<CombatPhaseEffectNodeRecordV1,
             kCombatPhaseEffectNodeMaximumRecordsV1> effect_node_draws{};
  bool runtime_random_list_weights_requested = false;
  std::uint32_t random_list_weight_count = 0;
  std::array<CombatRandomListWeightRecordV1,
             kCombatRandomListWeightMaximumRecordsV1> random_list_weights{};
  bool runtime_join_width_requested = false;
  std::uint32_t join_width_count = 0;
  std::uint32_t join_width_first_failure_code = join_width_failure_none;
  std::array<CombatJoinWidthRecordV1, 3> join_widths{};
  bool runtime_join_full_entries_requested = false;
  std::uint32_t join_full_entry_count = 0;
  std::uint32_t join_full_entry_first_failure_code =
      join_full_entry_failure_none;
  std::array<CombatJoinFullEntryRecordV1, 2> join_full_entries{};
  std::uint32_t knight_select_count = 0;
  std::array<CombatPhaseKnightSelectRecordV1,
             kCombatPhaseKnightSelectMaximumRecordsV1> knight_selects{};
  bool exact_boundary_sequence = false;
  bool same_full_generation_combat = false;
  bool same_native_date = false;
  bool expected_one_day_date_split = false;
  bool same_loaded_event_table = false;
  bool side_and_return_site_identity = false;
  bool schedule_phase_day_then_single_increment = false;
  bool bounded_capture_complete = false;
  bool full_mutable_transition_bundle_complete = false;
  bool production_trace_ready = false;
  std::array<CombatPhaseEventTraceRingRecordV1,
             kCombatPhaseEventTraceRingV1RecordCount>
      records{};
};

using CombatPhaseEventScheduleOriginalV1 = std::uintptr_t (*)(
    void *side, std::uint32_t *schedule_local_rng, void *target_province);
using CombatPhaseEventFireOriginalV1 = std::uintptr_t (*)(void *side);
using CombatPhaseEffectDispatchOriginalV1 = std::uintptr_t (*)(
    void *node, void *context);
using CombatPhaseKnightSelectOriginalV1 = std::int32_t (*)(
    void *selector, void *candidates, void *context);
using CombatRandomListWeightOriginalV1 = std::uintptr_t (*)(
    void *entries, void *weights, void *context, std::int32_t pick_count);
using CombatOutgoingDamageOriginalV1 = std::uintptr_t (*)(
    void *side, std::int64_t *output, std::int32_t final_width,
    std::int64_t advantage_multiplier_raw, void *opposite_side);
using CombatJoinWrapperOriginalV1 = std::uintptr_t (*)(void *combat,
                                                       void *incoming_army);

// Arm/disarm are managed-driver operations performed while CK3 is paused.
// The caller owns the ring storage for the entire sequence.  Arm copies and
// validates the fixed plan before atomically publishing the ring to hooks.
bool ArmCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring,
    const CombatPhaseEventTraceCapturePlanV1 &plan) noexcept;
void CancelCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring) noexcept;
bool IsCombatPhaseEventTraceRingV1Armed() noexcept;

// Explicit boundary entrypoint used by the exact-build trampolines and by the
// offline ABI test.  It allocates nothing and calls no CK3 helper.
bool CaptureCombatPhaseEventTraceBoundaryV1(
    CombatPhaseEventTraceBoundaryV1 boundary, void *combat,
    void *trigger_side, const std::uint32_t *schedule_local_rng,
    std::uintptr_t caller_return_address) noexcept;
// Copies one original outgoing-damage result after the native calculator
// returns and before either side's casualty application.  This does not
// claim a simulated win probability or change the original result.
bool CaptureCombatOutgoingDamageV1(
    void *side, void *opposite_side, const std::int64_t *output,
    std::uintptr_t caller_return_address) noexcept;
bool CaptureCombatJoinWidthV1(void *combat, void *incoming_army,
                              bool after_original) noexcept;
bool CaptureCombatJoinFullEntryV1(void *combat, void *incoming_army,
                                  bool after_original) noexcept;
bool CaptureCombatFirstSide0OutgoingWidthV1(
    void *side, std::int32_t width,
    std::uintptr_t caller_return_address) noexcept;
// Validates the prearmed Combat/side against the original main-tick caller
// captured by the outer outgoing-damage hook on the same thread. The inner
// trampoline's own return address points into that hook, not CK3.
bool CaptureCombatPostCounterAttackV1(
    void *side, std::int64_t attack_raw, std::uintptr_t outer_side,
    std::uintptr_t original_caller_return_address) noexcept;
// Called only by the exact 0x23CB435 internal trampoline, after it replays
// the original 16 position-independent bytes. R14 is then the side's
// post-counter attack accumulator before 0.03/advantage/width scaling.
extern "C" void __fastcall XarCaptureCombatPostCounterAttackV1(
    void *side, std::int64_t attack_raw) noexcept;

// Called only after the managed driver has regained a stable pause.  It adds
// record seven with the same bounded reader and then validates/drains the
// complete sequence.  No production capability consumes this yet.
bool CompleteAndDrainCombatPhaseEventTraceRingV1(
    CombatPhaseEventTraceRingV1 &ring,
    CombatPhaseEventTraceRingDrainV1 &output) noexcept;

// Binding original trampolines does not itself enable a capability.  The
// exact-build installer calls this only after proving both prologues and every
// required call-site anchor and constructing executable trampolines.
bool BindCombatPhaseEventTraceOriginalTrampolinesV1(
    CombatPhaseEventScheduleOriginalV1 schedule,
    CombatPhaseEventFireOriginalV1 fire,
    CombatOutgoingDamageOriginalV1 outgoing_damage) noexcept;
bool BindCombatPhaseEffectDispatchOriginalV1(
    CombatPhaseEffectDispatchOriginalV1 dispatch) noexcept;
bool BindCombatPhaseKnightSelectOriginalV1(
    CombatPhaseKnightSelectOriginalV1 select) noexcept;
bool BindCombatRandomListWeightOriginalV1(
    CombatRandomListWeightOriginalV1 select) noexcept;
bool BindCombatJoinWrapperOriginalV1(CombatJoinWrapperOriginalV1 join) noexcept;

extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventScheduleHookV1(void *side,
                                  std::uint32_t *schedule_local_rng,
                                  void *target_province) noexcept;
extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventFireHookV1(void *side) noexcept;
extern "C" std::uintptr_t __fastcall XarCombatPhaseEffectDispatchHookV1(
    void *node, void *context) noexcept;
extern "C" std::int32_t __fastcall XarCombatPhaseKnightSelectHookV1(
    void *selector, void *candidates, void *context) noexcept;
extern "C" std::uintptr_t __fastcall XarCombatRandomListWeightHookV1(
    void *entries, void *weights, void *context,
    std::int32_t pick_count) noexcept;
extern "C" std::uintptr_t __fastcall XarCombatOutgoingDamageHookV1(
    void *side, std::int64_t *output, std::int32_t final_width,
    std::int64_t advantage_multiplier_raw, void *opposite_side) noexcept;
extern "C" std::uintptr_t __fastcall XarCombatJoinWrapperHookV1(
    void *combat, void *incoming_army) noexcept;

static_assert(std::is_trivially_copyable_v<
              CombatPhaseEventTraceCapturePlanV1>);
static_assert(std::is_trivially_copyable_v<
              CombatPhaseEventTraceRingRecordV1>);

} // namespace xar::ck3_11906

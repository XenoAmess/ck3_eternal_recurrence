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
  std::array<std::uintptr_t, 2> sides{};

  // These are addresses of native pointer slots, not snapshots of their
  // contents.  Each capture re-reads the slots so a mid-sequence loaded-table,
  // date-object, RNG-wrapper or RNG-state replacement fails correlation.
  std::uintptr_t phase_event_database_slot = 0;
  std::uintptr_t expected_phase_event_database = 0;
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

  // Only the already closed identity/skill/regiment core is copied today.
  // This deliberately remains false until injury/trait ranks, trait-track XP,
  // accolade progress, unlock variables and participant detach readers are
  // added and a managed live delta fixture passes.
  bool full_mutable_transition_bundle_complete = false;

  friend bool operator==(const CombatPhaseEventTraceRingRecordV1 &,
                         const CombatPhaseEventTraceRingRecordV1 &) = default;
};

struct CombatPhaseEventTraceRingV1 {
  std::atomic<std::uint32_t> armed{0};
  std::atomic<std::uint32_t> capture_in_progress{0};
  std::atomic<std::uint32_t> committed_count{0};
  std::atomic<std::uint32_t> failure_flags{trace_capture_failure_none};
  CombatPhaseEventTraceCapturePlanV1 plan{};
  std::array<CombatPhaseEventTraceRingRecordV1,
             kCombatPhaseEventTraceRingV1RecordCount>
      records{};
};

struct CombatPhaseEventTraceRingDrainV1 {
  std::uint32_t failure_flags = trace_capture_failure_none;
  std::uint32_t record_count = 0;
  bool exact_boundary_sequence = false;
  bool same_full_generation_combat = false;
  bool same_native_date = false;
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
    CombatPhaseEventFireOriginalV1 fire) noexcept;

extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventScheduleHookV1(void *side,
                                  std::uint32_t *schedule_local_rng,
                                  void *target_province) noexcept;
extern "C" std::uintptr_t __fastcall
XarCombatPhaseEventFireHookV1(void *side) noexcept;

static_assert(std::is_trivially_copyable_v<
              CombatPhaseEventTraceCapturePlanV1>);
static_assert(std::is_trivially_copyable_v<
              CombatPhaseEventTraceRingRecordV1>);

} // namespace xar::ck3_11906

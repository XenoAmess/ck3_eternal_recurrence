#pragma once

#include "xar_bridge/person_natural_lineage_clock_12004.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kArmyNaturalPreDateRva12004 = 0x2A99DA0;
inline constexpr std::uintptr_t kArmyNaturalPostDateRva12004 = 0x2A9A570;
inline constexpr std::uintptr_t kArmyNaturalOriginalRosterCaptureRva12004 = 0x2A99E76;
inline constexpr std::uintptr_t kArmyNaturalPreparationReturnRva12004 = 0x2A9A086;
inline constexpr std::uintptr_t kArmyNaturalCoreReturnRva12004 = 0x2A9A8E2;
inline constexpr std::uintptr_t kArmyNaturalAssaultReturnRva12004 = 0x2A9A8EA;

using ArmyNaturalPhaseEvent12004 = PersonInstalledTransferEvent12004;
enum class ArmyNaturalPhaseKind12004 : std::uint8_t { unknown, pre_date, post_date };
enum class ArmyNaturalRosterBoundary12004 : std::uint8_t {
  unavailable, parent_entry, pre_date_prefix_return
};
using ArmyNaturalPhaseRead12004 = bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using ArmyNaturalPhaseEventReader12004 = ArmyNaturalPhaseEvent12004 (*)(void *) noexcept;

struct ArmyNaturalPhaseRoster12004 {
  ArmyNaturalRosterBoundary12004 boundary = ArmyNaturalRosterBoundary12004::unavailable;
  std::uintptr_t capture_rva = 0;
  ArmyNaturalPhaseEvent12004 capture_event;
  std::optional<std::uintptr_t> begin_identity;
  std::optional<std::uintptr_t> end_identity;
  std::optional<std::int32_t> count;
  bool complete = false;
  std::vector<std::uint32_t> ordered_full_ids;
};

// A copy of a naturally executing parent on this thread. Tokens are process-local
// identities; entry_event, never a local journal ordinal, identifies the parent.
struct ArmyNaturalPhaseScope12004 {
  bool observed = false;
  ArmyNaturalPhaseKind12004 phase = ArmyNaturalPhaseKind12004::unknown;
  std::uintptr_t actual_entry_rva = 0;
  std::uintptr_t caller_return_rva = 0;
  std::uintptr_t primary_manager_identity = 0;
  std::uintptr_t secondary_manager_identity = 0;
  std::uintptr_t game_state_identity = 0;
  std::optional<std::uintptr_t> session_identity;
  ArmyNaturalPhaseEvent12004 entry_event;
  std::optional<std::uint64_t> date_raw;
  std::optional<std::uint64_t> prefix_date_raw;
  std::optional<std::uint32_t> absolute_day_raw;
  std::optional<std::uint8_t> entry_c0_raw;
  // Entry C0 is not the later post-date saved C0 without a literal boundary.
  std::optional<std::uint8_t> saved_c0_raw;
  std::optional<bool> saved_mask02_admitted;
  std::uintptr_t saved_c0_observed_rva = 0;
  ArmyNaturalPhaseEvent12004 saved_c0_event;
  ArmyNaturalPhaseRoster12004 original_army_roster;
};

// One adapter to the existing process-lifetime clock owned by continuation 13.
ArmyNaturalPhaseEvent12004 NextArmyNaturalPhaseEvent12004(void * = nullptr) noexcept;
ArmyNaturalPhaseScope12004 CopyActiveArmyNaturalPhaseScope12004() noexcept;

struct ArmyNaturalPhaseBindings12004 {
  void *read_context = nullptr;
  ArmyNaturalPhaseRead12004 read = nullptr;
  void *event_context = nullptr;
  ArmyNaturalPhaseEventReader12004 next_event = nullptr;
  std::uintptr_t game_state_identity = 0;
  // Root supplies a source-proved current game/load epoch, if one is available.
  // A process clock, pointer or journal ordinal must not substitute for it.
  std::optional<std::uintptr_t> session_identity;
  std::size_t maximum_roster_occurrences = 65536;
};

#if defined(_MSC_VER)
using ArmyNaturalPhaseOriginal12004 = std::uintptr_t(__fastcall *)(void *);
#else
using ArmyNaturalPhaseOriginal12004 = std::uintptr_t (*)(void *);
#endif

struct ArmyNaturalPhaseRecord12004 {
  ArmyNaturalPhaseScope12004 scope;
  bool original_called = false;
  bool original_returned = false;
  std::uintptr_t raw_return_bits = 0;
  ArmyNaturalPhaseEvent12004 returned_event;
  std::optional<std::uint64_t> returned_date_raw;
  std::optional<std::uint32_t> returned_absolute_day_raw;
  std::optional<std::uint8_t> returned_c0_raw;
  std::optional<bool> same_clock_thread_order;
};

// Readonly observations around exactly one original callback; native RAX is opaque.
ArmyNaturalPhaseRecord12004 InvokeArmyNaturalPhaseScope12004(
    const ArmyNaturalPhaseBindings12004 &, ArmyNaturalPhaseOriginal12004,
    void *secondary_manager, ArmyNaturalPhaseKind12004, std::uintptr_t caller_return_rva) noexcept;

// Called only at the actual prefix return (return PC 2A99E76), before the caller
// executes its literal original-roster loads. A query snapshot cannot call this.
bool ObserveArmyNaturalPhaseOriginalRoster12004(std::uintptr_t primary_manager,
    std::uintptr_t actual_return_rva,
    std::optional<std::uint64_t> actual_prefix_date_raw = std::nullopt) noexcept;
// The source save point is 2A9A65D after loading GameState+C0, before the AND.
// Root's literal boundary supplies the actual saved register byte, not a getter.
bool ObserveArmyNaturalPhaseSavedC012004(std::uintptr_t secondary_manager,
    std::uintptr_t actual_save_rva, std::uint8_t actual_saved_c0) noexcept;
// A child entry thunk may copy the actual caller R13b after the AND. Full C0
// remains unknown. Accepted literal child return PCs are 672, 67D, 8E2, 8EA.
bool ObserveArmyNaturalPhaseSavedMask12004(std::uintptr_t secondary_manager,
    std::uintptr_t actual_child_return_rva, std::uint8_t actual_saved_mask) noexcept;

std::vector<ArmyNaturalPhaseRecord12004> ReadArmyNaturalPhaseJournal12004();
struct ArmyNaturalPhaseJournalStatus12004 {
  bool read_complete = false;
  std::size_t capacity = 64;
  std::size_t retained_records = 0;
  std::uint64_t appended_records = 0;
  std::uint64_t overwritten_records = 0;
  std::uint64_t failed_appends = 0;
  std::uint64_t clear_operations = 0;
};
ArmyNaturalPhaseJournalStatus12004 ReadArmyNaturalPhaseJournalStatus12004() noexcept;
void ClearArmyNaturalPhaseJournal12004() noexcept;

// A query must supply its own currently captured manager/state. A matching
// process clock alone is not proof that a historical record belongs to it.
// This checks actual process/context identity. Loaded-game epoch is independent.
bool ArmyNaturalPhaseCurrentContextMatches12004(const ArmyNaturalPhaseScope12004 &,
    std::uintptr_t current_primary_manager, std::uintptr_t current_game_state,
    std::uintptr_t current_clock_identity) noexcept;
std::optional<bool> ArmyNaturalPhaseSessionMatches12004(const ArmyNaturalPhaseScope12004 &,
    std::optional<std::uintptr_t> current_session_identity) noexcept;

} // namespace xar::ck3_12004

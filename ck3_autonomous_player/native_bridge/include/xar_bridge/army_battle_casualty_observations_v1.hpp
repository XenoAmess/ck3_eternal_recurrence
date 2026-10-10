#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::game {

inline constexpr std::size_t kArmyBattleCasualtyJournalCapacityV1 = 256;

struct ArmyBattleCasualtyOwnerResolutionV1 {
  bool reference_demanded = false;
  std::optional<std::int32_t> requested_full_id;
  std::optional<std::int32_t> resolved_full_id;
  std::optional<bool> used_fallback;
  bool read_complete = false;
};

struct ArmyBattleCasualtyObservationV1 {
  std::uint64_t sequence = 0;
  std::uint64_t entry_identity = 0;
  std::optional<std::int32_t> entry_army_regiment_id;
  std::int64_t soft_request_raw = 0;
  std::int64_t hard_request_raw = 0;
  std::optional<std::int32_t> observed_date_raw;
  std::optional<std::int64_t> before_fighting_raw;
  std::optional<std::int64_t> before_soft_raw;
  std::optional<std::int64_t> after_fighting_raw;
  std::optional<std::int64_t> after_soft_raw;
  bool same_entry_after = false;
  std::uint32_t nested_writer_event_count = 0;
  std::optional<std::uint64_t> writer_sequence;
  std::optional<std::int32_t> writer_army_regiment_id;
  std::optional<std::int64_t> writer_request_raw;
  bool entry_writer_association_proven = false;
  bool physical_capture_complete = false;
  std::optional<std::int64_t> actual_physical_soldier_debit;
  ArmyBattleCasualtyOwnerResolutionV1 owner_army;
  ArmyBattleCasualtyOwnerResolutionV1 owner_unit;
  // This is the actual Unit+174 whole DWORD used by the ledger call. It is
  // neither a Character lookup outcome nor a Person death observation.
  std::optional<std::int32_t> owner_character_id;
  std::uint64_t original_return_identity = 0;
  std::optional<std::int64_t> owner_hard_ledger_after_raw;
};

struct ArmyBattleCasualtyObservationsV1 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::vector<ArmyBattleCasualtyObservationV1> events;
};

} // namespace xar::game

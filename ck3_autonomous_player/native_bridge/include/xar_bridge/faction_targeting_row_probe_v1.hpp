#pragma once

#include "xar_bridge/faction_targeting_row_observer_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kFactionTargetingRowProbePrivateKeyV1 =
    "g2_faction_targeting_row_probe_v1";
inline constexpr bool kFactionTargetingRowProbePublicByDefaultV1 = false;

enum class FactionTargetingRowProbeTerminalV1 : std::uint8_t {
  unavailable = 0,
  known_empty = 1,
  ready = 2,
};

enum FactionTargetingRowProbeUnavailableReasonV1 : std::uint32_t {
  faction_targeting_row_probe_unavailable_none = 0,
  faction_targeting_row_probe_unavailable_observer_not_installed = 1U << 0,
  faction_targeting_row_probe_unavailable_observer_failure = 1U << 1,
  faction_targeting_row_probe_unavailable_no_generation = 1U << 2,
  faction_targeting_row_probe_unavailable_odd_generation = 1U << 3,
  faction_targeting_row_probe_unavailable_stale_binding = 1U << 4,
  faction_targeting_row_probe_unavailable_invalid_capture = 1U << 5,
  faction_targeting_row_probe_unavailable_unpaused = 1U << 6,
};

struct FactionTargetingRowProbeBindingV1 {
  bool paused = false;
  std::uint64_t proof_epoch = 0;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0;
};

struct FactionTargetingRowProbeFactionV1 {
  std::uint32_t faction_id = 0;
  std::uint32_t target_character_id = 0;
  bool leader_present = false;
  std::uint32_t leader_character_id = 0;
  bool leader_present_in_character_members = false;
  std::uint32_t character_member_count = 0;
  std::array<std::uint32_t,
             kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1>
      character_member_ids{};
};

struct FactionTargetingRowProbeResultV1 {
  FactionTargetingRowProbeTerminalV1 terminal =
      FactionTargetingRowProbeTerminalV1::unavailable;
  std::uint32_t unavailable_reasons =
      faction_targeting_row_probe_unavailable_none;
  std::uint32_t observer_failure_flags =
      faction_targeting_row_observer_failure_none;
  std::uint64_t published_generation = 0;
  FactionTargetingRowProbeBindingV1 required_binding{};
  FactionTargetingRowProbeBindingV1 observed_binding{};
  std::uint32_t faction_count = 0;
  std::array<FactionTargetingRowProbeFactionV1,
             kFactionTargetingRowObserverMaximumRowsV1>
      factions{};
};

// The diagnostics input must be one transactionally snapshotted value from
// ReadFactionTargetingRowObserverDiagnosticsV1. The probe admits only a
// nonzero even generation and a caller binding that is still paused.
FactionTargetingRowProbeResultV1 ProbeFactionTargetingRowsV1(
    const FactionTargetingRowObserverDiagnosticsV1 &observer,
    const FactionTargetingRowProbeBindingV1 &required_binding) noexcept;

std::string_view FactionTargetingRowProbeTerminalNameV1(
    FactionTargetingRowProbeTerminalV1 terminal) noexcept;

} // namespace xar::bridge

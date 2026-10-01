#pragma once

#include "xar_bridge/activity_hosted_identity_v1.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"

#include <cstdint>

namespace xar::bridge {

inline constexpr std::uintptr_t kFeastOutcome12002PrestigeGetterRva = 0x28BE040;
inline constexpr std::uintptr_t kFeastOutcome12002StressGetterRva = 0x28BC580;
inline constexpr std::size_t kFeastOutcome12002PrestigeOffset = 0x130;
inline constexpr std::size_t kFeastOutcome12002StressOffset = 0x2F8;

struct FeastOutcomeValuesV1 {
  ActivityHostedIdentityFrameV1 frame{};
  bool prestige_available = false;
  std::int64_t prestige_raw = 0; // Signed Q100000.
  bool stress_available = false;
  std::int32_t stress_points = 0; // Native integer points, not Q100000.
  bool reveler_available = false;
  bool reveler_present = false;
  bool reveler_xp_available = false;
  std::int64_t reveler_xp_raw = 0; // Signed Q100000; absent trait is not applicable.

  friend bool operator==(const FeastOutcomeValuesV1 &,
                         const FeastOutcomeValuesV1 &) = default;
};

struct FeastOutcomeEnvironmentV1 {
  ActivityHostedIdentityEnvironmentV1 identity{};
  // Fixture or SEH-owned native overrides; otherwise binds the existing
  // exact 1.20 trait database/presence/track query implementation.
  ck3_12002::phase_character::Bindings traits{};
};

enum class FeastOutcomeStatusV1 {
  observed,
  observed_partial,
  exact_build_rejected,
  frame_rejected,
  actor_unavailable,
  snapshot_changed,
};

struct FeastOutcomeResultV1 {
  FeastOutcomeStatusV1 status = FeastOutcomeStatusV1::exact_build_rejected;
  FeastOutcomeValuesV1 value{};
};

// Independent actor counters only. This does not execute an effect, infer a
// reward delta, claim Feast causality, or equate native completion with gain.
FeastOutcomeResultV1 ReadFeastOutcomeValues12002(
    const FeastOutcomeEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept;

} // namespace xar::bridge

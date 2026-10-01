#pragma once

#include "xar_bridge/activity_hosted_identity_v1.hpp"

#include <array>
#include <cstdint>

namespace xar::bridge {

// Same ordering and Q100000 units as kActivityFeastCostKeysV1.
// Gold and piety have exact actor-field sources for 1.19.0.6 and 1.20.0.2.
// Treasury and barter goods do not have a qualified actor getter here. Their
// availability stays false; a zero-cost slot requires no balance observation.
struct ActivityFeastResourceBalancesV1 {
  ActivityHostedIdentityFrameV1 frame{};
  std::array<bool, 4> available{};
  std::array<std::int64_t, 4> raw{};
};

enum class ActivityFeastBalanceStatusV1 {
  observed_partial,
  exact_build_rejected,
  frame_rejected,
  actor_unavailable,
  frame_changed,
};

struct ActivityFeastBalanceResultV1 {
  ActivityFeastBalanceStatusV1 status =
      ActivityFeastBalanceStatusV1::exact_build_rejected;
  ActivityFeastResourceBalancesV1 value{};
};

ActivityFeastBalanceResultV1 ReadActivityFeastResourceBalancesV1(
    const ActivityHostedIdentityEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept;

} // namespace xar::bridge

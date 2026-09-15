#pragma once

#include "player_construction_view_probe_v1.hpp"

namespace xar::ck3::shared {

// Caller owns this stack context for one synchronous application-main query.
struct PlayerConstructionViewProcessAccessV1 final {
  std::uintptr_t module_base = 0U;
};

[[nodiscard]] PlayerConstructionViewProbeSourceV1
BindCurrentProcessPlayerConstructionViewProbeSourceV1(
    PlayerConstructionViewProcessAccessV1& access) noexcept;

}  // namespace xar::ck3::shared

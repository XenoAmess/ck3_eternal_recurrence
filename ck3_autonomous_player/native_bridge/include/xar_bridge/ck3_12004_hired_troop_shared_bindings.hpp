#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"
#include <cstdint>
#include <string_view>

namespace xar::ck3_12004::hired_troops {
using CanAfford = bool (*)(const std::int64_t *, void *, void *);
using ReasonDestroy = void (*)(void *);
struct SharedBindings12004 {
  bool enabled = false;
  CanAfford can_afford = nullptr;
  ReasonDestroy reason_destroy = nullptr;
  ck3_12002::CommandBindings commands{};
};

// Exact actual4 helpers; the central command binder supplies its separately
// source-closed native manager/queue. No prior image binder or SHA alias.
SharedBindings12004 BindHiredTroopSharedImage12004(
    std::uintptr_t image_base, std::string_view actual_sha256) noexcept;
} // namespace xar::ck3_12004::hired_troops

#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12002 {

bool IsGovernmentRuntimeAdapterQuery12002(std::string_view step) noexcept;

// Candidate-only bridge caller. The worker retains the operation until the
// fixed application-main executor finishes, including an already-running wait.
// All native reads and current snapshot captures happen inside that executor.
bool ReadGovernmentRuntimeAdapterOnApplicationMain12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002

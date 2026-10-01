#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {
struct ActivityCostSlot12ObserverV1;
struct ActivityGuestRuleProvenanceObserverV1;
}

namespace xar::ck3_12002 {

// These private steps keep the existing wire grammar and remain absent from
// the default capability list. The selected adapter supplies every snapshot.
bool IsActivityFeastPrivateStep12002(std::string_view step) noexcept;
bool HandleActivityFeastPrivate12002(
    const game::GameAdapter &native_adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure,
    bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr,
    bridge::ActivityGuestRuleProvenanceObserverV1 *provenance = nullptr) noexcept;

} // namespace xar::ck3_12002

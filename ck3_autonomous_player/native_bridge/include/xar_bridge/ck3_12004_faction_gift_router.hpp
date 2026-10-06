#pragma once

#include "xar_bridge/ck3_12004_faction_gift.hpp"
#include "xar_bridge/ck3_12004_campaign_root_faction.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_faction_gift_router.hpp"

#include <optional>
#include <string>
#include <unordered_set>

namespace xar::ck3_12004 {

// Process-local state for the existing Python-owned durable gift ledger.
// A queue ACK remains pending until an independent receipt query verifies it.
using FactionGiftPrivateState12004 = ck3_12002::FactionGiftPrivateState12002;

// Offline router fixtures replace only native stores/call bindings and the
// already-tested campaign/targeting producers. They still run the real gift
// observation reader, final validator, owning command and receipt algorithms.
// Production callers leave this null; it is admitted only by a fixture mailbox.
struct FactionGiftPrivateFixtureBindings12004 {
  CampaignRootFactionBindings12004 campaign{};
  PlayerFactionAlertsNativeEnvironmentV1 factions{};
  FactionGiftBindings12004 gift{};
  void *context = nullptr;
  bool (*read_campaign)(void *, const game::CampaignRootFrameV1 &,
      game::CampaignRootContextV1 &) noexcept = nullptr;
  bool (*read_alerts)(void *, const game::PlayerFactionAlertsFrameV1 &,
      game::PlayerFactionAlertsV1 &) noexcept = nullptr;
};

// Uses the same leader-before-member and direct-landed-vassal selection as
// the existing private gift route. A county-only faction has no recipient.
bool SelectFactionGiftPrivateCandidate12004(
    const game::CampaignRootContextV1 &, const game::PlayerFactionAlertsV1 &,
    std::uint32_t &source_faction_id, std::uint32_t &recipient_character_id) noexcept;

// Register this fixed identity in the actual .4 executor list, only in the private
// gift build. All native provider calls execute inside this callback.
bool ExecuteFactionGiftPrivateMailbox12004(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

// Handles the existing preview, submit, receipt, and cold-recovery step names.
// A false return provides a protocol error in failure; otherwise serialized
// is the complete command_result frame consumed by the current Python route.
bool HandleFactionGiftPrivate12004(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    FactionGiftPrivateState12004 &, std::string &serialized,
    std::string &failure,
    const FactionGiftPrivateFixtureBindings12004 *fixture_bindings = nullptr) noexcept;

} // namespace xar::ck3_12004

#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include "xar_bridge/ck3_12004_player_heir_candidate_v1.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004::campaign_player_heir_candidate_v1 {

// Private additive material for the EXISTING campaign-root query. This does
// not change Snapshot/CampaignRootContextV1 or establish SDK source custody.
struct Component {
  std::uint64_t snapshot_revision = 0;
  bool parent_frame_bound = false;
  player_heir_candidate_v1::Observation observation{};
};

// Default off returns nullopt without reading. An opted-in original campaign
// executor calls this after its ordinary root read and before its unchanged
// FinishQueryMailbox guard. No new mailbox ticket, RPC or opcode is created.
std::optional<Component> ReadForCampaignRoot(
    const player_heir_candidate_v1::Bindings &bindings,
    const game::CampaignRootContextV1 &parent,
    std::uint64_t expected_snapshot_revision) noexcept;

// Append only to the existing canonical serializer's object. Missing component
// (including a legacy producer or default-off build) preserves the exact bytes.
// Rechecks the copied parent binding; optional failure never changes root
// status/readiness. Contains no pointers or self-asserted SDK provenance.
std::string AppendToCanonicalRoot(
    std::string payload, const game::CampaignRootContextV1 &parent,
    const Component *component);

} // namespace xar::ck3_12004::campaign_player_heir_candidate_v1

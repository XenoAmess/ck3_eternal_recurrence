#include "xar_bridge/campaign_player_heir_candidate_component12004_v1.hpp"

namespace xar::ck3_12004::campaign_player_heir_candidate_v1 {
namespace {
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
bool ParentReady(const game::CampaignRootContextV1 &p,
                 std::uint64_t revision) noexcept {
  return revision != 0 && p.snapshot_revision == revision &&
         p.status == game::CampaignRootContextStatusV1::available &&
         p.readiness.same_frame_ready && p.local_player_id &&
         *p.local_player_id != -1 && p.player_character_id &&
         *p.player_character_id != -1 && p.player_character_alive == true;
}

bool Matches(const CoreSnapshotPrefix &f,
             const game::CampaignRootContextV1 &p) noexcept {
  return f.clock.paused && f.map_ready && f.has_played_character &&
         f.played_character_alive && f.clock.date_raw == p.date_raw &&
         f.local_player_id == *p.local_player_id &&
         f.played_character_id == *p.player_character_id;
}

void ClearCandidate(Component &out, std::string_view reason) noexcept {
  out.parent_frame_bound = false;
  auto &o = out.observation;
  o.available = false;
  o.unavailable_reason = reason;
  o.identity_and_frame_stable = false;
  o.candidate_present = false;
  o.candidate_character_id = -1;
  o.candidate_alive = false;
  o.lineage_available = false;
  o.candidate_lineage = {};
  o.lineage_unavailable_reason = {};
}
#endif
} // namespace

std::optional<Component> ReadForCampaignRoot(
    const player_heir_candidate_v1::Bindings &bindings,
    const game::CampaignRootContextV1 &parent,
    std::uint64_t expected_snapshot_revision) noexcept {
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
  Component out{};
  out.snapshot_revision = expected_snapshot_revision;
  out.observation.source_fixture = bindings.offline_fixture;
  if (!ParentReady(parent, expected_snapshot_revision)) {
    ClearCandidate(out, "parent_root_frame_unavailable");
    return out; // Do not invoke the getter for an unavailable/stale root.
  }
  out.observation = player_heir_candidate_v1::Read(bindings); // Once only.
  const auto &o = out.observation;
  if (!o.available || !o.identity_and_frame_stable) return out;
  if (!Matches(o.before, parent) || !Matches(o.after, parent) ||
      o.actor_character_id != *parent.player_character_id) {
    ClearCandidate(out, "parent_root_frame_changed");
    return out;
  }
  // Null/dead candidates can be coherent observations. They confer no player
  // continuation/D0 qualification, nor completeness of a backup domain.
  out.parent_frame_bound = true;
  return out;
#else
  (void)bindings;
  (void)parent;
  (void)expected_snapshot_revision;
  return std::nullopt;
#endif
}
} // namespace xar::ck3_12004::campaign_player_heir_candidate_v1

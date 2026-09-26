#include "player_construction_view_probe_v1_mailbox.hpp"
#include "player_construction_view_probe_v1_process.hpp"
#include "player_world_building_definition_source_v1_process.hpp"
#include "player_world_building_action_candidate_v1.hpp"
#include "domain_construction_application_main_runtime_v1.hpp"

#include <iostream>

// Link-only fixtures for the unrelated executor in the same source unit.
// The test calls solely the production serializer below.
namespace xar::ck3::shared {
PlayerConstructionViewProbeResultV1 ProbePlayerConstructionViewCacheV1(
    const PlayerConstructionViewProbeAdmissionV1 &,
    const PlayerConstructionViewProbeSourceV1 &) noexcept { return {}; }
PlayerConstructionViewProbeSourceV1
BindCurrentProcessPlayerConstructionViewProbeSourceV1(
    PlayerConstructionViewProcessAccessV1 &) noexcept { return {}; }
} // namespace xar::ck3::shared

namespace xar::ck3_11906 {
PlayerWorldBuildingActionCandidateV1 SelectPlayerWorldBuildingActionCandidateV1(
    const PlayerWorldBuildingSourceResultV1 &,
    std::uint64_t, std::int64_t) noexcept { return {}; }
PlayerHeldConstructionModelResultV1 ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t, bool, const CampaignRootAccessV1 &,
    const PlayerHeldConstructionModelRequestV1 &) noexcept { return {}; }
PlayerWorldBuildingSourceResultV1 ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t, bool, const PlayerWorldBuildingSourceAccessV1 &,
    const PlayerWorldBuildingSourceRequestV1 &) noexcept { return {}; }
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
NativePlayerBuildingFinalLegalityV1
BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1 &) noexcept { return nullptr; }
NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1 &) noexcept { return nullptr; }
} // namespace xar::ck3_11906

namespace xar::ck3::shared {
bool SubmitPlayerWorldBuildingDirectActionV1(
    PlayerWorldBuildingDirectActionStateV1 &,
    const PlayerWorldBuildingDirectActionRequestV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept { return false; }
}

int main() {
  xar::ck3_11906::PlayerConstructionViewProbeMailboxContextV1 query{};
  query.expected_revision = 3;
  query.expected_snapshot.date_raw = 53178312;
  query.player_world_building_source_executed = true;
  auto &world = query.player_world_building_sources;
  world.failure =
      xar::ck3_11906::PlayerWorldBuildingFailureV1::definition_identity;
  auto &diagnostic = world.definition_identity_diagnostic;
  diagnostic.registry_count = 47;
  diagnostic.failed_index = 9;
  diagnostic.stage =
      xar::ck3_11906::PlayerWorldDefinitionIdentityStageV1::vtable_mismatch;
  diagnostic.has_observed_vtable_rva = true;
  diagnostic.observed_vtable_rva = 0x44046D0;
  std::cout <<
      xar::ck3_11906::SerializePlayerConstructionViewProbePrivateV1(query)
      << '\n';
  world = {};
  world.source_available = true;
  world.snapshot_revision = 3;
  world.date_raw = 53178312;
  world.player_character_id = 29829;
  world.legal_samples.push_back({2103, 2635, 24, 1,
                                 "common_tradeport_01"});
  std::cout <<
      xar::ck3_11906::SerializePlayerConstructionViewProbePrivateV1(query)
      << '\n';
  world.completed_buildings_observed = true;
  world.positive_income_coverage_complete = true;
  world.completed_buildings.push_back({2103, 2635, 24, 1});
  std::cout <<
      xar::ck3_11906::SerializePlayerConstructionViewProbePrivateV1(query);
}

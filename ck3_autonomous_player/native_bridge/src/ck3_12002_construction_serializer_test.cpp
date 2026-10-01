#include "ck3_12002_construction_mailbox.hpp"
#include "ck3_12002_construction.hpp"
#include "ck3_12002_construction_submit_binding.hpp"
#include "player_construction_view_probe_v1_process.hpp"

#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>

// These symbols only satisfy references from unused executors in the three
// serializer source units. Any accidental native execution aborts this test.
namespace {
[[noreturn]] void UnusedNativeExecutor() noexcept { std::abort(); }
}

namespace xar::ck3::shared {
PlayerConstructionViewProbeResultV1 ProbePlayerConstructionViewCacheV1(
    const PlayerConstructionViewProbeAdmissionV1&,
    const PlayerConstructionViewProbeSourceV1&) noexcept {
  UnusedNativeExecutor();
}
PlayerConstructionViewProbeSourceV1
BindCurrentProcessPlayerConstructionViewProbeSourceV1(
    PlayerConstructionViewProcessAccessV1&) noexcept {
  UnusedNativeExecutor();
}
bool SubmitPlayerWorldBuildingDirectActionV1(
    PlayerWorldBuildingDirectActionStateV1&,
    const PlayerWorldBuildingDirectActionRequestV1&,
    const ck3_11906::MainThreadExecutionStampV1&) noexcept {
  UnusedNativeExecutor();
}
}  // namespace xar::ck3::shared

namespace xar::ck3_11906 {
PlayerWorldBuildingActionCandidateV1 SelectPlayerWorldBuildingActionCandidateV1(
    const PlayerWorldBuildingSourceResultV1&,
    std::uint64_t, std::int64_t) noexcept { UnusedNativeExecutor(); }
PlayerHeldConstructionModelResultV1 ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t, bool, const CampaignRootAccessV1&,
    const PlayerHeldConstructionModelRequestV1&) noexcept {
  UnusedNativeExecutor();
}
PlayerWorldBuildingSourceResultV1 ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t, bool, const PlayerWorldBuildingSourceAccessV1&,
    const PlayerWorldBuildingSourceRequestV1&) noexcept {
  UnusedNativeExecutor();
}
bool ReadSnapshot(const Bindings&, game::Snapshot&) noexcept {
  UnusedNativeExecutor();
}
NativePlayerBuildingFinalLegalityV1
BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1&) noexcept { UnusedNativeExecutor(); }
NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1&) noexcept { UnusedNativeExecutor(); }
}  // namespace xar::ck3_11906

namespace xar::ck3_12002 {
bool ReadCoreSnapshot(const CoreBindings&, CoreSnapshotPrefix&) noexcept {
  UnusedNativeExecutor();
}
PlayerWorldBuildingSourceResultV1 ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t, bool, const PlayerWorldBuildingSourceAccessV1&,
    const PlayerWorldBuildingSourceRequestV1&) noexcept {
  UnusedNativeExecutor();
}
NativePlayerBuildingFinalLegalityV1
BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1&) noexcept { UnusedNativeExecutor(); }
NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1&) noexcept { UnusedNativeExecutor(); }
ConstructionNativeCallsV1
BindCurrentProcessDomainConstructionExactNativeCallsV1(
    std::uintptr_t) noexcept { UnusedNativeExecutor(); }
bool SubmitPlayerWorldBuildingDirectActionV1(
    ConstructionActionStateV1&, const ConstructionActionRequestV1&,
    const ck3_11906::MainThreadExecutionStampV1&) noexcept {
  UnusedNativeExecutor();
}
}  // namespace xar::ck3_12002

namespace {
xar::ck3_12002::ConstructionMailboxContextV1 MakeContext() {
  xar::ck3_12002::ConstructionMailboxContextV1 context{};
  auto& query = context.query;
  query.expected_revision = 3;
  query.expected_snapshot.date_raw = 53168784;
  query.execution_stamp.pump_epoch = 91;
  query.player_world_building_source_executed = true;
  auto& world = query.player_world_building_sources;
  world.source_available = true;
  world.snapshot_revision = 3;
  world.date_raw = 53168784;
  world.player_character_id = 29829;
  world.definition_source_count = 47;
  world.final_legality_checks = 94;
  world.native_final_legality_evaluated = true;
  world.native_cost_evaluated = true;
  world.native_cost_checks = 1;
  world.player_gold_observed = true;
  world.player_gold_raw = 50035659;
  world.positive_income_coverage_complete = true;
  world.completed_buildings_observed = true;
  world.directly_held_barony_provinces.push_back({2103, 2635});
  world.active_constructions.push_back({2103, 2635, false, -1, -1, -1});
  xar::ck3_11906::PlayerWorldBuildingLegalSampleV1 sample{};
  sample.barony_title_id = 2103;
  sample.province_id = 2635;
  sample.building_type_id = 24;
  sample.slot_index = 1;
  sample.building_key = "farm_estates_01";
  sample.native_cost_observed = true;
  sample.cost_raw_native[0] = 15000000;
  sample.cost_raw_slots[0] = 15000000;
  world.legal_samples.push_back(sample);
  return context;
}

void CheckCommon(const std::string& json) {
  assert(json.find("\"game_version\":\"1.20.0.2\"") != std::string::npos);
  assert(json.find("\"source_binding\":\"direct-world-building-manager\"") !=
         std::string::npos);
  assert(json.find("\"gui_cache_sampled\":false") != std::string::npos);
  assert(json.find("\"status\":\"source_available\"") != std::string::npos);
  assert(json.find("\"executor_invocations\":0") != std::string::npos);
  assert(json.find("1.19.0.6") == std::string::npos);
}
}  // namespace

int main() {
  auto context = MakeContext();
  const auto read_only =
      xar::ck3_12002::SerializeConstructionMailboxV1(context);
  CheckCommon(read_only);
  assert(read_only.find("\"private_action\"") == std::string::npos);
  assert(read_only.find("\"status\":\"unavailable\"") != std::string::npos);
  assert(read_only.find("\"effective_visible\":null") != std::string::npos);
  std::cout << read_only << '\n';

  auto& query = context.query;
  query.request_private_action = true;
  auto& candidate = query.private_action_candidate;
  candidate.ready = true;
  candidate.failure = xar::ck3_11906::PlayerWorldBuildingActionFailureV1::none;
  candidate.snapshot_revision = 3;
  candidate.proof_epoch = 91;
  candidate.date_raw = 53168784;
  candidate.actor_character_id = 29829;
  candidate.barony_title_id = 2103;
  candidate.province_id = 2635;
  candidate.building_type_id = 24;
  candidate.slot_index = 1;
  candidate.player_gold_before_raw = 50035659;
  candidate.stock_gold_cost_raw = 15000000;
  candidate.gold_reserve_after_raw = 35035659;
  candidate.stock_cost_raw_native =
      query.player_world_building_sources.legal_samples.front().cost_raw_native;
  auto& action = query.private_action_state;
  action.phase =
      xar::ck3::shared::PlayerWorldBuildingDirectActionPhaseV1::pending_receipt;
  action.production_native_path = true;  // A DTO ACK fixture, not live evidence.
  action.validator_calls = 1;
  action.materialize_calls = 1;
  action.receiver_calls = 1;
  action.receiver_command_sequence = 7001;
  action.submitted = candidate;
  const auto pending =
      xar::ck3_12002::SerializeConstructionMailboxV1(context);
  CheckCommon(pending);
  assert(pending.find("\"status\":\"pending_receipt\"") != std::string::npos);
  assert(pending.find("\"applied\":false") != std::string::npos);
  std::cout << pending << '\n';
}

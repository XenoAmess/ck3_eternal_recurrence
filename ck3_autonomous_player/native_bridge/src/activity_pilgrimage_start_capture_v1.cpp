#include "xar_bridge/activity_pilgrimage_start_capture_v1.hpp"
#include "xar_bridge/activity_feast_resource_balance_v1.hpp"

namespace xar::bridge {

namespace {
bool ForwardStartMemory(void *opaque, std::uintptr_t address, void *output,
                        std::size_t size) noexcept {
  if (opaque == nullptr) return false;
  const auto &sources = *static_cast<ActivityPilgrimageStartCaptureSourcesV1 *>(opaque);
  const auto &d = sources.cost.diagnostic;
  return d.read_memory != nullptr &&
         d.read_memory(d.context, address, output, size);
}
} // namespace

ActivityPilgrimageStage5StartEnvironmentV1
BuildActivityPilgrimageStage5StartEnvironmentV1(
    ActivityPilgrimageStartCaptureSourcesV1 &sources) noexcept {
  const auto &d = sources.cost.diagnostic;
  return {sources.cost.enabled && sources.hosted.enabled,
          d.admitted_executable_sha256, d.module_base, &sources,
          &ForwardStartMemory, &CaptureActivityPilgrimageStage5V1, nullptr};
}

bool CaptureActivityPilgrimageStage5V1(
    void *opaque, const ActivityPlannerDiagFrameV1 &expected,
    ActivityPilgrimageStage5SnapshotV1 &output) noexcept {
  output = {};
  if (opaque == nullptr) return false;
  const auto &sources = *static_cast<ActivityPilgrimageStartCaptureSourcesV1 *>(opaque);
  const auto &diagnostic = sources.cost.diagnostic;
  if (!sources.cost.enabled || !sources.hosted.enabled ||
      !IsActivity12004BuildV1(diagnostic.admitted_executable_sha256) ||
      sources.hosted.admitted_executable_sha256 != diagnostic.admitted_executable_sha256 ||
      sources.hosted.module_base != diagnostic.module_base ||
      diagnostic.module_base == 0 || diagnostic.read_frame == nullptr ||
      sources.read_destination == nullptr) return false;
  ActivityPlannerDiagFrameV1 initial{};
  if (!diagnostic.read_frame(diagnostic.context, initial) || initial != expected)
    return false;
  const auto quote = ReadActivityTypedPlannerFullCostV1(
      sources.cost, expected, kOrdinaryPilgrimagePiousContractV1);
  if (quote.status != ActivityTypedFullCostStatusV1::observed) return false;
  ActivityPilgrimageDestinationStateV1 before{}, after{};
  if (!sources.read_destination(sources.destination_context, before) ||
      before.frame != expected || before.planner != quote.quote.planner ||
      before.activity_type != quote.quote.activity_type || before.stage != 5 ||
      before.configuration_row_count != 1 || before.phase == 0 ||
      before.province_id == 0 ||
      before.selection != quote.quote.selection ||
      !MatchesActivityTypedPlannerSelectionV1(before.selection, expected,
          before.planner, before.activity_type, 5,
          kOrdinaryPilgrimagePiousContractV1)) return false;
  const ActivityHostedIdentityFrameV1 hosted_frame{expected.revision,
      expected.date_raw, expected.actor_character_id,
      expected.application_main_thread, expected.paused,
      expected.map_ready, expected.actor_alive};
  const auto balances = ReadActivityFeastResourceBalancesV1(sources.hosted, hosted_frame);
  if (balances.status != ActivityFeastBalanceStatusV1::observed_partial ||
      balances.value.frame != hosted_frame) return false;
  const auto hosted = ReadActivityHostedIdentityV1(sources.hosted, hosted_frame);
  if (hosted.status != ActivityHostedIdentityStatusV1::observed ||
      hosted.frame != hosted_frame) return false;
  ActivityPlannerDiagFrameV1 final{};
  if (!sources.read_destination(sources.destination_context, after) || after != before ||
      !diagnostic.read_frame(diagnostic.context, final) || final != expected)
    return false;
  ActivityPilgrimageStage5SnapshotV1 candidate{};
  candidate.quote = quote.quote;
  candidate.destination = {true, quote.quote.kind, expected, before.planner,
      before.activity_type, before.stage, before.configuration_row_count,
      before.province_id};
  candidate.balance_frame = expected;
  for (std::size_t name = 0; name < quote.quote.known_name_resource_indices.size(); ++name) {
    const auto resource = quote.quote.known_name_resource_indices[name];
    if (resource >= candidate.balance_raw.size()) return false;
    candidate.balance_available[resource] = balances.value.available[name];
    candidate.balance_raw[resource] = balances.value.raw[name];
  }
  candidate.hosted = hosted;
  output = candidate;
  return true;
}

} // namespace xar::bridge

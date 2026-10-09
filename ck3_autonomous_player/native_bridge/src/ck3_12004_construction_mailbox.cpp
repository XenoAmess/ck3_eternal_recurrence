#include "ck3_12004_construction_mailbox.hpp"
#include "ck3_12004_construction_submit_binding.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <windows.h>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
using Stamp = ck3_11906::MainThreadExecutionStampV1;
using Completion = ck3_11906::PlayerConstructionViewProbeMailboxCompletionV1;

bool Main(void *opaque) noexcept {
  return ck3_12002::IsQueryOwningThread(opaque);
}

bool Capture(void *opaque, game::CampaignRootFrameV1 &frame) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  if (envelope == nullptr || envelope->expected_snapshot_revision == 0 ||
      !ck3_12002::CaptureQuerySnapshot(envelope, snapshot)) return false;
  frame = {envelope->expected_snapshot_revision, snapshot.date_raw,
           snapshot.paused, snapshot.map_ready, snapshot.has_played_character,
           snapshot.played_character_alive, snapshot.played_character_id};
  return true;
}

bool Memory(void *opaque, const void *address, void *output, std::size_t size) noexcept {
  if (!Main(opaque) || address == nullptr || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try { std::memcpy(output, address, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool Same(ConstructionMailboxContext12004 &owner) noexcept {
  game::Snapshot snapshot{};
  return ck3_12002::CaptureQuerySnapshot(&owner.envelope, snapshot);
}
} // namespace

bool ExecuteConstructionMailbox12004(void *context, const Stamp &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(context);
  auto *owner = envelope == nullptr ? nullptr :
      static_cast<ConstructionMailboxContext12004 *>(envelope->typed_context);
  if (owner == nullptr || &owner->envelope != envelope) return false;
  auto &q = owner->query;
  if (envelope->game == nullptr ||
      !game::IsCk3_12004Descriptor(envelope->game->descriptor()) ||
      !owner->bindings.enabled || !owner->bindings.core.enabled ||
      q.module_base == 0 || q.module_base != owner->bindings.module_base ||
      q.expected_revision == 0 || q.expected_revision != envelope->expected_snapshot_revision ||
      q.completion != Completion::not_executed || q.executor_invocations != 0 ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteConstructionMailbox12004)) {
    q.completion = Completion::infrastructure_rejected;
    return false;
  }
  ++q.executor_invocations;
  q.execution_stamp = stamp;
  // This uses the same direct-world reader and unchanged software receipt shape;
  // neither the old HoldingView ABI nor a standalone zero revision is queried.
  PlayerWorldBuildingSourceAccessV1 access{};
  access.campaign = {envelope, &Capture, &Main, &Memory, nullptr};
  PlayerWorldBuildingNativeCallAccessV1 native{q.module_base, true};
  access.final_legality = ck3_12004::BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(native);
  access.final_legality_context = &native;
  access.native_cost = ck3_12004::BindCurrentProcessPlayerWorldBuildingCostV1(native);
  access.native_cost_context = &native;
  q.player_world_building_source_executed = true;
  // Eight held provinces can exhaust 512 legality checks before the finite
  // positive-income definitions finish. The reader keeps the unvalued tail
  // at its old 512 total checks while honoring the existing 4096 ceiling here.
  q.player_world_building_sources = ck3_12004::ReadPlayerWorldBuildingDefinitionSourcesV1(
      q.module_base, true, access,
      {q.expected_revision, -1, 4096, kConstructionWorldLegalSampleBudgetV1});
  if (q.player_world_building_sources.source_available && Same(*owner)) {
    if (q.request_private_action) {
      q.private_action_candidate = ck3_11906::SelectPlayerWorldBuildingActionCandidateV1(
          q.player_world_building_sources, stamp.pump_epoch, q.minimum_gold_reserve_raw);
      if (q.private_action_candidate.ready) {
        ConstructionActionRequestV1 request{};
        request.exact_build_admitted = true;
        request.session_live = true;
        request.module_base = q.module_base;
        request.source = &q.player_world_building_sources;
        request.candidate = &q.private_action_candidate;
        request.native_calls = ck3_12004::BindCurrentProcessDomainConstructionExactNativeCallsV1(q.module_base);
        (void)ck3_12004::SubmitPlayerWorldBuildingDirectActionV1(q.private_action_state, request, stamp);
      }
    }
  }
  if (!ck3_12002::FinishQueryMailbox(*envelope)) {
    q.player_world_building_sources = {};
    q.player_world_building_sources.failure = PlayerWorldBuildingFailureV1::frame_changed;
  }
  q.completion = Completion::completed;
  return true;
}

std::string HandleConstruction12004(const ConstructionMailboxContext12004 &context) {
  if (context.envelope.game == nullptr) return {};
  auto json = game::Render12004BuildIdentity(
      ck3_11906::SerializePlayerConstructionViewProbePrivateV1(context.query),
      context.envelope.game->descriptor());
  if (!json.empty() && json.back() == '}') {
    json.pop_back();
    json += ",\"game_version\":\"1.20.0.4\",\"source_binding\":\"direct-world-building-manager\",\"gui_cache_sampled\":false}";
  }
  return json;
}
} // namespace xar::ck3_12004

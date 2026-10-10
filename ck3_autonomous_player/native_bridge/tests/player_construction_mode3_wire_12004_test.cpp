#include "player_construction_view_probe_v1_mailbox.hpp"

#include <stdexcept>
#include <string>
#include <utility>

namespace xar::ck3_12004 {
namespace {
void RequireMode3Wire(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
} // namespace

// The sole03d new main supplies the actual held reader packet and independent
// ordinary-world material. This fragment invents neither raw inputs nor world
// admission flags. It has no main and uses the existing production serializer.
std::string SerializeConstructionMode3CurrentWireForNewCase12004(
    const PlayerHeldConstructionMode3InputResultV1& observed,
    const PlayerWorldBuildingSourceResultV1& world,
    std::uint64_t proof_epoch) {
  RequireMode3Wire(observed.current_frame_observed && !observed.holdings.empty(),
      "new03d actual held packet has a copied current holding");
  RequireMode3Wire(proof_epoch != 0 && world.source_available &&
      world.failure == PlayerWorldBuildingFailureV1::none,
      "new wire receives independent ordinary world admission");
  ck3_11906::PlayerConstructionViewProbeMailboxContextV1 query{};
  query.expected_revision = world.snapshot_revision;
  query.expected_snapshot.date_raw = world.date_raw;
  query.expected_snapshot.played_character_id = world.player_character_id;
  query.execution_stamp.pump_epoch = proof_epoch;
  query.executor_invocations = 1;
  query.player_world_building_source_executed = true;
  query.player_world_building_sources = world;
  RequireMode3Wire(ck3::shared::AttachPlayerConstructionNativeMode3InputsV1(
      query.result, query.player_world_building_sources, observed),
      "actual mode3 and independent ordinary world share revision/date/player");
  const auto& owned = *query.result.native_mode3_inputs;
  for (const auto& holding : owned.holdings) {
    const auto& input = holding.inputs;
    RequireMode3Wire(input.province_pointer == 0 && input.slots_pointer == 0 &&
        input.context_pointer == 0 && input.context_object_848 == 0 &&
        input.returned_receiver_pointer == 0,
        "all borrowed addresses are scrubbed before private query survives callback");
  }
  const auto wire = ck3_11906::SerializePlayerConstructionViewProbePrivateV1(query);
  RequireMode3Wire(wire.find("\"native_mode3_inputs\":{") != std::string::npos &&
      wire.find("\"province_pointer\"") == std::string::npos &&
      wire.find("\"returned_receiver_pointer\"") == std::string::npos,
      "actual retained packet reaches full existing serializer without borrowed address keys");

  auto mismatched = observed;
  ++mismatched.snapshot_revision;
  ck3::shared::PlayerConstructionViewProbeResultV1 rejected{};
  RequireMode3Wire(!ck3::shared::AttachPlayerConstructionNativeMode3InputsV1(
      rejected, world, std::move(mismatched)) && rejected.native_mode3_inputs &&
      !rejected.native_mode3_inputs->current_frame_observed &&
      rejected.native_mode3_inputs->holdings.empty() &&
      rejected.native_mode3_inputs->failure == PlayerHeldConstructionModelFailureV1::frame_changed,
      "wrong native revision becomes local nullable mode3 material");
  auto failed_after = observed;
  failed_after.current_frame_observed = false;
  failed_after.failure = PlayerHeldConstructionModelFailureV1::frame_changed;
  RequireMode3Wire(!ck3::shared::AttachPlayerConstructionNativeMode3InputsV1(
      rejected, world, std::move(failed_after)) &&
      !rejected.native_mode3_inputs->current_frame_observed &&
      rejected.native_mode3_inputs->holdings.empty(),
      "after-reader failure cannot publish before-reader numeric holdings");
  RequireMode3Wire(ck3_11906::SerializePlayerConstructionViewProbePrivateV1(query) == wire,
      "later rejected packets do not alter previously owned raw query material");
  return wire;
}
} // namespace xar::ck3_12004

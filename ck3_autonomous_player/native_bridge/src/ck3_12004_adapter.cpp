#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_family_relationships.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/ck3_12004_world.hpp"
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"

#include <windows.h>
#include <array>
#include <utility>

namespace xar::game {
namespace {
void ReplaceIdentityToken(std::string &serialized, std::string_view from,
                          std::string_view to) {
  std::size_t at = 0;
  while ((at = serialized.find(from, at)) != std::string::npos) {
    serialized.replace(at, from.size(), to);
    at += to.size();
  }
}
} // namespace

const AdapterDescriptor &Ck3_12004AdapterDescriptor() noexcept {
  static constexpr auto capabilities = std::to_array<std::string_view>({
      "game.query.core-frame.v1",
      "game.state.snapshot", "game.state.xar-one-life-settlement",
      "game.state.map-ready", "game.state.played-character",
      "game.state.active-event", "game.state.pending-character-interaction",
      "game.state.active-wars", "game.state.war-primary-opponent",
      "game.state.war-objectives", "game.state.war-objective-occupation",
      "game.state.war-objective-fort-level", "game.state.war-objective-garrison",
      "game.state.war-objective-siege-progress", "game.state.war-objective-assault",
      "game.state.player-armies", "game.state.army-routes",
      "game.command.query-army-strengths-v1",
      ck3_12003::kArmyCommanderCandidatesCapability,
      "game.command.query-player-mercenary-context-v1",
      "game.command.hire-mercenary-v1", "game.command.hire-holy-order-v1",
      "game.command.pause-map", "game.command.resume-map",
      "game.command.set-speed-1", "game.command.set-speed-2",
      "game.command.set-speed-3", "game.command.set-speed-4",
      "game.command.set-speed-5", "game.command.save-checkpoint"});
  static const AdapterDescriptor descriptor{
      ck3_12004::kAdapterId, ck3_12004::kGameVersion,
      ck3_12004::kExecutableSha256, ck3_12002::kCheckpointSaveName,
      capabilities};
  return descriptor;
}

Ck3_12004AdapterBindings BindCk3_12004AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  Ck3_12004AdapterBindings bindings{};
  bindings.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  if (!bindings.core.enabled) return bindings;
  bindings.commands = ck3_12004::BindCommandImage12004(
      image_base, executable_sha256);
  bindings.armies = ck3_12004::BindArmyImage12004(image_base, executable_sha256);
  bindings.owned_regiments.persistent_regiment_storage_slot =
      bindings.armies.persistent_regiment_storage_slot;
  bindings.owned_regiments.read_type = ck3_12002::ReadOwnedRegimentTypeV1;
  bindings.world = ck3_12004::BindWorldImage12004(image_base, executable_sha256);
  bindings.provinces = ck3_12004::BindProvinceImage12004(
      image_base, executable_sha256, bindings.armies);
  try {
    bindings.snapshot_foundation12004 =
        std::make_shared<const ck3_12004::SnapshotFoundationBindings>(
            ck3_12004::BindSnapshotFoundationImage(image_base, executable_sha256));
  } catch (...) {
    // The independent core observation remains available if the software
    // snapshot bundle cannot be allocated.
    bindings.snapshot_foundation12004.reset();
  }
  return bindings;
}

bool ReadCk3_12004Snapshot(const Ck3_12004AdapterBindings &bindings,
                         Snapshot &output) noexcept {
  output = {};
  ck3_12004::CoreSnapshotPrefix prefix{};
  if (bindings.read_core_snapshot == nullptr ||
      !bindings.read_core_snapshot(bindings.core, prefix)) return false;
  Snapshot observed{};
  observed.date_raw = prefix.clock.date_raw;
  observed.speed = prefix.clock.speed;
  observed.paused = prefix.clock.paused;
  observed.player_id = prefix.local_player_id;
  observed.map_ready = prefix.map_ready;
  observed.has_played_character = prefix.has_played_character;
  observed.played_character_id = prefix.played_character_id;
  observed.played_character_alive = prefix.played_character_alive;
  if (!prefix.map_ready) {
    output = std::move(observed);
    return true;
  }
  const auto &foundation = bindings.snapshot_foundation12004;
  if (!foundation) return false;
  if (prefix.has_played_character) {
    ck3_12004::ActorResourceBalances resources{};
    if (!ck3_12004::ReadActorResourceBalances(
            bindings.core, prefix.played_character_id, resources)) return false;
    observed.played_character_gold.raw = resources.gold_raw;
    observed.played_character_prestige.raw = resources.prestige_raw;
    observed.played_character_piety.raw = resources.piety_raw;
    observed.played_character_stress_points = resources.stress_points;
    PlayedCharacterRelationships12002 relationships{};
    if (!ck3_12004::ReadPlayedCharacterRelationships(
            bindings.core, prefix.played_character_id, relationships)) return false;
    observed.played_character_betrothed_id = relationships.betrothed_character_id;
    observed.played_character_primary_spouse_id =
        relationships.primary_spouse_character_id;
    observed.played_character_spouse_ids =
        std::move(relationships.spouse_character_ids);
  }
  auto events = foundation->events;
  events.core = bindings.core;
  if (!ck3_12004::ReadEventsSnapshot(events, observed) ||
      ck3_12004::ReadWorldSnapshot12004(bindings.world, bindings.armies,
          bindings.provinces, prefix, observed) !=
              ck3_12004::WorldReadResult::available) return false;
  const auto settlement = ck3_12004::ReadSettlement(
      foundation->settlement, bindings.core, observed);
  if (settlement != ck3_12004::SettlementReadResult::published &&
      settlement != ck3_12004::SettlementReadResult::not_published) return false;
  output = std::move(observed);
  return true;
}

std::unique_ptr<GameAdapter> CreateCk3_12004AdapterFromBindings(
    Ck3_12004AdapterBindings bindings) noexcept {
  bindings.read_core_snapshot = ck3_12004::ReadCoreSnapshot;
  return CreateCrozierAdapterFromBindings(
      std::move(bindings), Ck3_12004AdapterDescriptor());
}

std::unique_ptr<GameAdapter> CreateCk3_12004Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12004AdapterFromBindings(BindCk3_12004AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      executable_sha256));
}

std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (!IsCk3_12004Descriptor(descriptor)) return serialized;
  serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
  for (const auto old_version : {"1.20.0.2", "1.20.0.3"}) {
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"" + old_version + "\"",
          std::string("\"") + key + "\":\"1.20.0.4\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"ck3-" + old_version + "-",
          std::string("\"") + key + "\":\"ck3-1.20.0.4-");
    }
    ReplaceIdentityToken(serialized,
        std::string("\"adapter_id\":\"ck3-") + old_version + "-msvc-x64\"",
        "\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\"");
    ReplaceIdentityToken(serialized,
        std::string("\"played-character-event-icon-indicators-") + old_version + "-v1\"",
        "\"played-character-event-icon-indicators-1.20.0.4-v1\"");
  }
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12004_");
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12003_", "\"schema\":\"ck3_12004_");
  for (const auto old_hash : {std::string_view(ck3_12002::kExecutableSha256),
                            std::string_view(ck3_12003::kExecutableSha256)}) {
    ReplaceIdentityToken(serialized, std::string("\"") + std::string(old_hash) + "\"",
        std::string("\"") + ck3_12004::kExecutableSha256 + "\"");
  }
  for (const auto old_hash : {
      "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"}) {
    ReplaceIdentityToken(serialized, std::string("\"") + old_hash + "\"",
        "\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"");
  }
  return serialized;
}
} // namespace xar::game

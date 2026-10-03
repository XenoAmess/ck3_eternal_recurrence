#include "xar_bridge/ck3_12003_army_reserve.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include <array>
#include <cstring>

namespace xar::ck3_12003 {
namespace {
struct CompositionCleanup {
  const PlayerArmyReserveBindingsV1 &bindings;
  void *composition;
  ~CompositionCleanup() { bindings.destroy_contents(composition); }
};
} // namespace
PlayerArmyReserveBindingsV1 BindPlayerArmyReserveImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  PlayerArmyReserveBindingsV1 bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return bindings;
  bindings.construct_empty = reinterpret_cast<decltype(bindings.construct_empty)>(image_base + 0xC6D5B0);
  bindings.initialize_owner = reinterpret_cast<decltype(bindings.initialize_owner)>(image_base + 0x25A7120);
  bindings.count_all_unraised = reinterpret_cast<decltype(bindings.count_all_unraised)>(image_base + 0x25A6790);
  bindings.destroy_contents = reinterpret_cast<decltype(bindings.destroy_contents)>(image_base + 0xB03250);
  bindings.enabled = true;
  return bindings;
}
bool ReadPlayerUnraisedTroopsV1(const PlayerArmyReserveBindingsV1 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    ck3_12002::PlayerDefaultRaiseObservationV1 &output) noexcept {
  output.unraised_soldiers.reset();
  output.unraised_troops_ready = false;
  output.unraised_troops_failure = "reserve_bindings_unavailable";
  if (!bindings.enabled || bindings.construct_empty == nullptr ||
      bindings.initialize_owner == nullptr || bindings.count_all_unraised == nullptr ||
      bindings.destroy_contents == nullptr || world.read_snapshot == nullptr ||
      world.resolve_character == nullptr) return false;
  game::Snapshot current{};
  if (!world.read_snapshot(world.context,current) || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive || current.played_character_id <= 0 ||
      current.played_character_id != output.actor.character_id ||
      current.date_raw != output.date_raw) {
    output.unraised_troops_failure = "actor_frame_unavailable";
    return false;
  }
  void *const actor = world.resolve_character(world.context,current.played_character_id);
  std::int32_t full_id = -1;
  if (actor != nullptr)
    std::memcpy(&full_id,static_cast<const std::byte *>(actor)+0x18,sizeof(full_id));
  if (actor == nullptr || full_id != current.played_character_id) {
    output.unraised_troops_failure = "character_unavailable";
    return false;
  }
  // Exact native object allocation/zero/constructor and non-deleting cleanup
  // are sealed by the .3 ArmyComposition lifetime proof. The count receiver
  // is this composition, never CCharacter or CArmyRegiment.
  alignas(16) std::array<std::byte,0xB8> storage{};
  void *const composition = storage.data();
  if (bindings.construct_empty(composition) != composition) {
    output.unraised_troops_failure = "temporary_composition_unavailable";
    return false;
  }
  CompositionCleanup cleanup{bindings,composition};
  bindings.initialize_owner(composition,actor);
  const auto soldiers = bindings.count_all_unraised(composition);
  if (soldiers < 0) {
    output.unraised_troops_failure = "native_headcount_invalid";
    return false;
  }
  output.unraised_soldiers = soldiers;
  output.unraised_troops_ready = true;
  output.unraised_troops_failure = "none";
  return true;
}
} // namespace xar::ck3_12003

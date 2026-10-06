#include "xar_bridge/ck3_12004_world.hpp"

namespace xar::ck3_12004 {
namespace {
// Complete actual paired .3/.4 bodies and source-use operands:
// army-family-12004/world-mapping/WORLD-PROFILE-SOURCE-CLOSED.json.
constexpr std::uintptr_t kContainsParticipantRva = 0x2494B40;
constexpr std::uintptr_t kWarScoreRva = 0x249AC20;
constexpr std::uintptr_t kCharacterCapitalRva = 0x28B1CB0;
constexpr std::uintptr_t kRaiseProvinceSelectorRva = 0x24A5190;
} // namespace

WorldBindings BindWorldImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  WorldBindings result{};
  if (!image_base || executable_sha256 != kExecutableSha256) return result;
  result.game_state_slot =
      reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(image_base + kCharacterStorageSlotRva);
  result.contains_war_participant =
      reinterpret_cast<decltype(result.contains_war_participant)>(
          image_base + kContainsParticipantRva);
  result.get_war_score = reinterpret_cast<decltype(result.get_war_score)>(
      image_base + kWarScoreRva);
  result.get_character_capital =
      reinterpret_cast<decltype(result.get_character_capital)>(
          image_base + kCharacterCapitalRva);
  result.resolve_raise_province =
      reinterpret_cast<decltype(result.resolve_raise_province)>(
          image_base + kRaiseProvinceSelectorRva);
  result.enabled = true;
  return result;
}

void *ResolveWar12004(const WorldBindings &bindings,
    std::int32_t war_id) noexcept {
  return ck3_12002::ResolveWar(bindings, war_id);
}
bool ReadWarParticipantIds12004(const void *side,
    std::vector<std::int32_t> &out) noexcept {
  return ck3_12002::ReadWarParticipantIds(side, out);
}
bool ReadWarTargetTitleIds12004(const void *war,
    std::vector<std::int32_t> &out) noexcept {
  return ck3_12002::ReadWarTargetTitleIds(war, out);
}
WorldReadResult ReadActiveWars12004(const WorldBindings &bindings,
    std::int32_t player_character_id, std::span<const game::ArmySnapshot> armies,
    std::vector<game::ActiveWarSnapshot> &out) noexcept {
  return ck3_12002::ReadActiveWars(bindings, player_character_id, armies, out);
}
WorldReadResult ReadWorldSnapshot12004(const WorldBindings &bindings,
    const ck3_12002::ArmyBindings &armies, const ck3_12002::ProvinceBindings &provinces,
    const CoreSnapshotPrefix &core, game::Snapshot &out) noexcept {
  return ck3_12002::ReadWorldSnapshot(bindings, armies, provinces, core, out);
}

} // namespace xar::ck3_12004

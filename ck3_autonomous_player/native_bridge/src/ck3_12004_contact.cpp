#include "xar_bridge/ck3_12004_contact.hpp"

#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/ck3_12004_routes.hpp"

namespace xar::ck3_12004 {

ck3_12002::RouteBindings BindContactImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256)
    return {};

  // H1 owns the actual .4 route callbacks used by the existing contact readers.
  // This factory adds their separately closed readonly contact dependencies.
  auto result = BindRouteImage12004(image_base, executable_sha256);
  const auto core = BindCoreImage(image_base, executable_sha256);
  const auto army = BindArmyImage12004(image_base, executable_sha256);
  if (!result.enabled || !core.enabled || !army.enabled)
    return {};

  result.game_state_slot = core.game_state_slot;
  result.jomini_state_slot = core.jomini_state_slot;
  result.army_storage_slot = army.unit_storage_slot;
  result.army_internal_storage_slot = army.internal_army_storage_slot;
  result.regiment_storage_slot = army.regiment_storage_slot;
  result.character_storage_slot = core.character_storage_slot;
  result.combat_storage_slot =
      reinterpret_cast<void **>(image_base + kBattleCombatStorageRva);
  result.battle_result_storage_slot =
      reinterpret_cast<void **>(image_base + kBattleResultStorageRva);
  // Arrival's paired native field witness: root -> +1C0 -> +28 mode byte.
  result.contact_game_mode_slot =
      reinterpret_cast<void **>(image_base + 0x5CB87F8);

  // Full readonly callback proofs: arrival HOSTILE/EMPTY receipts, native-main
  // map05 in-combat, commander-supply domain-scoped06 holder, native-main
  // map06 holder classifier, and contact/fallback-first01 (423-byte body).
  result.is_character_hostile =
      reinterpret_cast<ck3_12002::RouteBindings::Hostile>(
          image_base + 0x2C09620);
  result.is_army_empty_for_contact =
      reinterpret_cast<ck3_12002::RouteBindings::ArmyPredicate>(
          image_base + 0x24E83A0);
  result.is_army_in_combat =
      reinterpret_cast<ck3_12002::RouteBindings::ArmyPredicate>(
          image_base + 0x24E8340);
  result.read_province_holder_character_id =
      reinterpret_cast<ck3_12002::RouteBindings::ProvinceHolder>(
          image_base + 0x247D010);
  result.classify_contact_defender_by_holder =
      reinterpret_cast<ck3_12002::RouteBindings::DefenderPredicate>(
          image_base + 0x2C097F0);
  result.classify_contact_defender_fallback =
      reinterpret_cast<ck3_12002::RouteBindings::DefenderPredicate>(
          image_base + 0x2C164C0);
  return result;
}

} // namespace xar::ck3_12004

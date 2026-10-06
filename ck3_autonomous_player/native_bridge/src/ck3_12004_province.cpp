#include "xar_bridge/ck3_12004_province.hpp"

namespace xar::ck3_12004 {

ck3_12002::ProvinceBindings BindProvinceImage12004(
    std::uintptr_t base, std::string_view sha,
    const ck3_12002::ArmyBindings &actual_armies) noexcept {
  ck3_12002::ProvinceBindings result{};
  if (base == 0 || sha != kExecutableSha256) return result;
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  result.character_storage_slot =
      reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  result.unit_storage_slot =
      reinterpret_cast<void **>(base + kProvinceUnitStorageSlotRva);
  result.province_fallback_slot =
      reinterpret_cast<void **>(base + kProvinceFallbackSlotRva);
  result.siege_storage_slot =
      reinterpret_cast<void **>(base + kProvinceSiegeStorageSlotRva);
  result.landed_title_storage_slot =
      reinterpret_cast<void **>(base + kObjectiveTitleStorageSlotRva);
  result.title_province =
      reinterpret_cast<ck3_12002::ObjectiveTitleProvinceGetter>(base + 0x230F8E0);
  result.is_occupied =
      reinterpret_cast<ck3_12002::ProvinceOccupiedGetter>(base + 0x247D0C0);
  result.fort_level =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x247AB70);
  result.garrison_size =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x247F350);
  result.besieging_strength =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x247F1B0);
  result.eligible_regiment_siege_work =
      reinterpret_cast<ck3_12002::ProvinceFixedGetter>(base + 0x247ECC0);
  result.highest_eligible_siege_tier =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x247EFA0);
  result.siege_progress =
      reinterpret_cast<ck3_12002::SiegeFixedGetter>(base + 0x251C9A0);
  result.siege_total_work =
      reinterpret_cast<ck3_12002::SiegeFixedGetter>(base + 0x251DD00);
  result.siege_days_left =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x251CAE0);
  result.siege_armies = actual_armies;
  result.siege_army_excluded =
      reinterpret_cast<ck3_12002::SiegeArmyExclusionPredicate>(base + 0x24E8340);
  result.siege_army_province_eligible =
      reinterpret_cast<ck3_12002::SiegeArmyProvinceEligibilityPredicate>(
          base + 0x2C16670);
  result.siege_ordinary_daily_progress =
      reinterpret_cast<ck3_12002::SiegeOrdinaryDailyGetter>(base + 0x251F150);
  result.siege_current_phase_length =
      reinterpret_cast<ck3_12002::SiegePhaseLengthGetter>(base + 0x251E780);
  result.siege_is_blocked =
      reinterpret_cast<ck3_12002::SiegeBlockedPredicate>(base + 0x251CF50);
  result.assault_daily_progress =
      reinterpret_cast<ck3_12002::SiegeDailyAssaultGetter>(base + 0x25207D0);
  result.assault_daily_casualties =
      reinterpret_cast<ck3_12002::ProvinceIntGetter>(base + 0x25205A0);
  result.validate_start_assault =
      reinterpret_cast<ck3_12002::SiegeAssaultValidator>(base + 0x29738A0);
  result.validate_stop_assault =
      reinterpret_cast<ck3_12002::SiegeAssaultValidator>(base + 0x2973A50);
  return result;
}

} // namespace xar::ck3_12004

#include "xar_bridge/ck3_12002_province.hpp"

#include <cstring>
#include <algorithm>
#include <limits>

namespace xar::ck3_12002 {
namespace {
template <class T> T Read(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}
void *Component(void **slot, std::int32_t id, std::size_t id_offset) noexcept {
  if (slot == nullptr || *slot == nullptr || id == -1) return nullptr;
  const auto storage = *slot;
  const auto capacity = Read<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  const auto data = Read<void *>(storage, 0x20);
  if (data == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const auto object = Read<void *>(data, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Read<std::int32_t>(object, id_offset) == id ? object : nullptr;
}
} // namespace

ProvinceBindings BindProvinceImage(std::uintptr_t base, std::string_view sha) noexcept {
  ProvinceBindings result{};
  if (base == 0 || sha != kExecutableSha256) return result;
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  result.character_storage_slot = reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  result.unit_storage_slot = reinterpret_cast<void **>(base + kProvinceUnitStorageSlotRva);
  result.siege_storage_slot = reinterpret_cast<void **>(base + kProvinceSiegeStorageSlotRva);
  result.landed_title_storage_slot = reinterpret_cast<void **>(base + kObjectiveTitleStorageSlotRva);
  result.title_province = reinterpret_cast<ObjectiveTitleProvinceGetter>(base + 0x230F900);
  result.is_occupied = reinterpret_cast<ProvinceOccupiedGetter>(base + 0x247D0E0);
  result.fort_level = reinterpret_cast<ProvinceIntGetter>(base + 0x247AB90);
  result.garrison_size = reinterpret_cast<ProvinceIntGetter>(base + 0x247F370);
  result.besieging_strength = reinterpret_cast<ProvinceIntGetter>(base + 0x247F1D0);
  result.siege_progress = reinterpret_cast<SiegeFixedGetter>(base + 0x251C9C0);
  result.siege_total_work = reinterpret_cast<SiegeFixedGetter>(base + 0x251DD20);
  result.siege_days_left = reinterpret_cast<ProvinceIntGetter>(base + 0x251CB00);
  result.siege_armies = BindArmyImage(base, sha);
  result.siege_ordinary_daily_progress =
      reinterpret_cast<SiegeOrdinaryDailyGetter>(base + 0x251F170);
  result.siege_current_phase_length =
      reinterpret_cast<SiegePhaseLengthGetter>(base + 0x251E7A0);
  result.siege_is_blocked = reinterpret_cast<SiegeBlockedPredicate>(base + 0x251CF70);
  result.assault_daily_progress = reinterpret_cast<SiegeDailyAssaultGetter>(base + 0x25207F0);
  result.assault_daily_casualties = reinterpret_cast<ProvinceIntGetter>(base + 0x25205C0);
  result.validate_start_assault = reinterpret_cast<SiegeAssaultValidator>(base + 0x29738C0);
  result.validate_stop_assault = reinterpret_cast<SiegeAssaultValidator>(base + 0x2973A70);
  return result;
}

void *ResolveObjectiveProvince(const ProvinceBindings &b, std::int32_t id) noexcept {
  if (!b.enabled || b.game_state_slot == nullptr || *b.game_state_slot == nullptr || id < 1) return nullptr;
  const auto game_data = Read<void *>(*b.game_state_slot, 0xA0);
  if (game_data == nullptr) return nullptr;
  const auto count = Read<std::int32_t>(game_data, kObjectiveProvinceCountOffset);
  const auto data = Read<void *>(game_data, kObjectiveProvinceArrayOffset);
  if (data == nullptr || count <= 1 || id >= count) return nullptr;
  const auto province = Read<void *>(data, static_cast<std::size_t>(id) * sizeof(void *));
  return province != nullptr && Read<std::int32_t>(province, 0x10) == id &&
         Read<std::uint32_t>(province, kObjectiveProvinceMagicOffset) == 0x50726F76U ? province : nullptr;
}

void *ResolveObjectiveSiege(const ProvinceBindings &b, std::int32_t id) noexcept {
  if (!b.enabled) return nullptr;
  const auto siege = Component(b.siege_storage_slot, id, 8);
  return siege != nullptr && Read<std::uint32_t>(siege, 0xC) == 0x53696765U ? siege : nullptr;
}

void *ResolveObjectiveTitle(const ProvinceBindings &b, std::int32_t id) noexcept {
  return b.enabled ? Component(b.landed_title_storage_slot, id, 0x10) : nullptr;
}

bool CollectObjectiveProvinceIds(const ProvinceBindings &b,
    std::span<const std::int32_t> targeted, std::vector<std::int32_t> &out) noexcept {
  out.clear();
  if (!b.enabled || b.title_province == nullptr || targeted.size() > 4096) return false;
  try {
    std::vector<std::int32_t> visited, collected;
    std::size_t remaining_title_budget = 4096;
    auto collect = [&](auto &&self, std::int32_t id, std::size_t depth, bool root) -> bool {
      if (depth > 8 || remaining_title_budget == 0 ||
          std::find(visited.begin(), visited.end(), id) != visited.end()) return false;
      const auto title = ResolveObjectiveTitle(b, id);
      if (title == nullptr) return false;
      --remaining_title_budget;
      visited.push_back(id);
      const auto definition = Read<void *>(title, kObjectiveTitleTemplateOffset);
      if (definition == nullptr) return false;
      const auto tier = Read<std::int32_t>(definition, kObjectiveTitleTemplateTierOffset);
      if (tier == 1 || tier == 2) {
        if (tier == 1 && !root) return false;
        const auto province = b.title_province(title);
        if (province == nullptr) return false;
        const auto province_id = Read<std::int32_t>(province, 0x10);
        if (ResolveObjectiveProvince(b, province_id) != province) return false;
        if (std::find(collected.begin(), collected.end(), province_id) == collected.end()) {
          if (collected.size() >= 4096) return false;
          collected.push_back(province_id);
        }
        return true;
      }
      if (tier < 3 || tier > 5) return false;
      const auto children = Read<void *>(title, kObjectiveTitleChildrenOffset);
      const auto capacity = Read<std::int32_t>(title, kObjectiveTitleChildrenOffset + 8);
      const auto count = Read<std::int32_t>(title, kObjectiveTitleChildrenOffset + 12);
      if (count < 0 || capacity < count || capacity > 4096 || (count > 0 && children == nullptr)) return false;
      for (std::int32_t index = 0; index < count; ++index) {
        if (!self(self, Read<std::int32_t>(children, static_cast<std::size_t>(index) * 4), depth + 1, false)) return false;
      }
      return true;
    };
    for (const auto id : targeted) {
      // Separate targeted roots can legitimately overlap. The recursion's
      // cycle tracking is per root; the work budget and province set are shared.
      visited.clear();
      if (!collect(collect, id, 0, true)) return false;
    }
    out.swap(collected);
    return true;
  } catch (...) {
    out.clear();
    return false;
  }
}

game::WarObjectiveProvinceState ReadObjectiveProvince(
    const ProvinceBindings &b, std::int32_t id,
    const std::vector<game::ArmySnapshot> &armies,
    std::int32_t played_id, bool rich) noexcept {
  game::WarObjectiveProvinceState out{};
  out.province_id = id;
  const auto province = ResolveObjectiveProvince(b, id);
  if (province == nullptr) return out;
  if (b.is_occupied != nullptr) {
    const bool occupied = b.is_occupied(province);
    const auto occupant = Read<std::int32_t>(province, kObjectiveProvinceOccupationIdOffset);
    if (!occupied || Component(b.character_storage_slot, occupant, 0x18) != nullptr) {
      out.occupation_observable = true;
      out.is_occupied = occupied;
      if (occupied) out.occupying_character_id = occupant;
    }
  }
  if (b.fort_level != nullptr) {
    const auto value = b.fort_level(province);
    if (value >= 0) { out.fort_level_observable = true; out.fort_level = value; }
  }
  if (!rich) return out;
  if (b.garrison_size != nullptr) {
    const auto value = b.garrison_size(province);
    if (value >= 0) { out.garrison_size_observable = true; out.garrison_size = value; }
  }
  if (b.besieging_strength != nullptr) {
    const auto value = b.besieging_strength(province);
    if (value >= 0) { out.besieging_strength_observable = true; out.besieging_strength = value; }
  }
  if (b.siege_storage_slot == nullptr || b.siege_progress == nullptr ||
      b.siege_total_work == nullptr || b.siege_days_left == nullptr) return out;
  const auto siege_id = Read<std::int32_t>(province, kObjectiveProvinceActiveSiegeIdOffset);
  if (siege_id == -1) { out.siege_observable = true; return out; }
  const auto siege = ResolveObjectiveSiege(b, siege_id);
  if (siege == nullptr || Read<void *>(siege, kObjectiveSiegeProvinceOffset) != province) return out;
  std::int64_t progress{}, total{};
  if (b.siege_progress(siege, &progress) != &progress ||
      b.siege_total_work(siege, &total) != &total) return out;
  const auto current = Read<std::int64_t>(siege, kObjectiveSiegeCurrentWorkOffset);
  if (progress < 0 || progress > 100'000 || total < 0 || current < 0) return out;
  out.siege_observable = true;
  out.has_active_siege = true;
  out.siege_id = siege_id;
  out.siege_progress_fraction.raw = progress;
  out.siege_current_work.raw = current;
  out.siege_total_work.raw = total;
  const auto internal_id = Read<std::int32_t>(siege, kObjectiveSiegeArmyIdOffset);
  std::size_t matches = 0;
  std::int32_t unit_id = -1;
  for (const auto &army : armies) {
    const auto unit = Component(b.unit_storage_slot, army.army_id, 0x10);
    if (unit == nullptr || internal_id == -1 || Read<std::int32_t>(unit, 0x178) != internal_id) continue;
    ++matches;
    unit_id = army.army_id;
    out.player_army_besieging = out.player_army_besieging || army.controllable;
  }
  if (matches == 1) out.besieging_army_id = unit_id;
  const auto days = b.siege_days_left(siege);
  if (days >= 0 && days != std::numeric_limits<std::int32_t>::max()) {
    out.siege_days_left_observable = true;
    out.siege_days_left = days;
  }
  // These fields belong to the validated active Siege, independently of the
  // assault subdomain. +0x20 is last prepare's cache; fresh phase uses its getter.
  const auto prepared_phase = Read<std::int64_t>(
      siege, kObjectiveSiegePreparedPhaseLengthOffset);
  if (prepared_phase >= 0) {
    out.siege_prepared_phase_length_observable = true;
    out.siege_prepared_phase_length.raw = prepared_phase;
  }
  const auto phase_counter = Read<std::int32_t>(
      siege, kObjectiveSiegePhaseCounterOffset);
  if (phase_counter >= 0) {
    out.siege_phase_counter_observable = true;
    out.siege_phase_counter = phase_counter;
  }
  if (b.siege_is_blocked != nullptr) {
    out.siege_can_advance_observable = true;
    out.siege_can_advance = !b.siege_is_blocked(siege);
  }
  const auto internal_army = ResolveInternalArmy(b.siege_armies, internal_id);
  if (internal_army != nullptr) {
    const auto commander_id = Read<std::int32_t>(
        internal_army, kObjectiveSiegeArmyCommanderOffset);
    // -1 is the native no-commander ID, not an invented missing modifier value.
    // A nonempty commander ID must still resolve in the current character graph.
    if (commander_id == -1 ||
        Component(b.character_storage_slot, commander_id, 0x18) != nullptr) {
      std::int64_t ordinary_daily{}, current_phase{};
      if (b.siege_ordinary_daily_progress != nullptr &&
          b.siege_ordinary_daily_progress(siege, &ordinary_daily, commander_id,
                                         internal_id, nullptr) == &ordinary_daily &&
          ordinary_daily >= 0) {
        out.siege_ordinary_daily_progress_observable = true;
        out.siege_ordinary_daily_progress.raw = ordinary_daily;
      }
      if (b.siege_current_phase_length != nullptr &&
          b.siege_current_phase_length(siege, &current_phase, commander_id,
                                      nullptr) == &current_phase &&
          current_phase >= 0) {
        out.siege_current_phase_length_observable = true;
        out.siege_current_phase_length.raw = current_phase;
      }
    }
  }
  if (!out.besieging_strength_observable || b.assault_daily_progress == nullptr ||
      b.assault_daily_casualties == nullptr || b.validate_start_assault == nullptr ||
      b.validate_stop_assault == nullptr || played_id == -1) return out;
  const auto breach = Read<std::int32_t>(siege, kObjectiveSiegeBreachOffset);
  const auto active = Read<std::uint8_t>(siege, kObjectiveSiegeAssaultOffset);
  if (breach < 0 || breach > 2 || active > 1) return out;
  std::int64_t daily{};
  std::int32_t casualties{};
  if (breach > 0) {
    if (b.assault_daily_progress(siege, &daily, out.besieging_strength) != &daily || daily < 0) return out;
    casualties = b.assault_daily_casualties(siege);
    if (casualties < 0) return out;
  }
  out.assault_observable = true;
  out.breach_level = breach;
  out.assault_in_progress = active != 0;
  out.can_start_assault = b.validate_start_assault(1, played_id, siege_id, nullptr);
  out.can_stop_assault = b.validate_stop_assault(1, played_id, siege_id, nullptr);
  out.assault_daily_progress.raw = daily;
  out.assault_daily_casualties = casualties;
  return out;
}

} // namespace xar::ck3_12002

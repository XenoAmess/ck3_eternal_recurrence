#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_current_daily_assault_loss.hpp"
#include "xar_bridge/ck3_12003_current_fleet_supply_tick_inputs.hpp"
#include "xar_bridge/ck3_12003_current_province_besieging_contributors.hpp"
#include "xar_bridge/army_strength_query_diagnostic_v1.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"
#include "xar_bridge/ck3_12003_ordered_besieging_fixed_chunk0_preparation.hpp"
#include "xar_bridge/ck3_12003_current_helper_domain_inputs.hpp"
#include "xar_bridge/ck3_12003_current_helper_point_store_inputs.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}

constexpr std::int32_t kMaximumCapacity = 1'000'000;
constexpr std::int32_t kMaximumRoute = 4'096;
constexpr std::int32_t kMaximumRegiments = 65'536;
constexpr std::size_t kMaximumDatabaseObjectKeyBytes = 4'096;
constexpr std::size_t kMsvcStringInlineCapacity = 15;

void ReadMaaTypeCompositionV1(
    void *maa_type, game::ArmyRegimentStrengthSnapshot &output) noexcept {
  // The existing combat reader uses this ArRg -> GDbo type/key path. Exact .3
  // province tier getter 0x247EFC0 reads the same type's signed +0x2A0 operand.
  if (maa_type == nullptr ||
      Load<std::uint32_t>(maa_type, 0x38) != 0x4744624FU) {
    output.maa_type_status = game::ArmyRegimentTypeStatusV1::absent;
    return;
  }
  const auto *const storage = static_cast<const std::byte *>(maa_type) + 0x18;
  const auto size = Load<std::size_t>(storage, 0x10);
  const auto capacity = Load<std::size_t>(storage, 0x18);
  if (size == 0 || size > capacity ||
      size > kMaximumDatabaseObjectKeyBytes) {
    output.composition_unavailable_reason = "maa_type_key_unavailable";
    return;
  }
  const char *const data = capacity <= kMsvcStringInlineCapacity
                              ? reinterpret_cast<const char *>(storage)
                              : Load<const char *>(storage, 0x00);
  if (data == nullptr) {
    output.composition_unavailable_reason = "maa_type_key_unavailable";
    return;
  }
  output.maa_type_key.assign(data, size);
  output.siege_tier = Load<std::int32_t>(maa_type, 0x2A0);
  output.maa_type_status = game::ArmyRegimentTypeStatusV1::available;
}

void ReadRegimentComposition(
    void *regiment, game::ArmyRegimentStrengthSnapshot &output) noexcept {
  ReadMaaTypeCompositionV1(Load<void *>(regiment, 0x18), output);
}

bool Storage(void **slot, void *&objects, std::int32_t &capacity) noexcept {
  objects = nullptr;
  capacity = 0;
  if (slot == nullptr || *slot == nullptr) return false;
  objects = Load<void *>(*slot, 0x20);
  capacity = Load<std::int32_t>(*slot, 0x2C);
  return capacity >= 0 && capacity <= kMaximumCapacity &&
         (capacity == 0 || objects != nullptr);
}

void *Resolve(void **slot, std::int32_t id,
              game::ArmyNativeResolutionSnapshotV1 *observation = nullptr) noexcept {
  if (observation != nullptr) {
    *observation = {};
    observation->available = true;
    observation->raw_reference = id;
  }
  if (id == -1) {
    if (observation != nullptr)
      observation->branch = game::ArmyNativeResolutionBranchV1::reference_absent;
    return nullptr;
  }
  void *objects = nullptr;
  std::int32_t capacity = 0;
  if (!Storage(slot, objects, capacity)) {
    if (observation != nullptr) {
      observation->branch = game::ArmyNativeResolutionBranchV1::storage_unavailable;
      // A failed Storage with capacity0 did not reach the header read. An actual
      // header capacity0 is accepted by Storage and observed below before OOB.
      if (capacity != 0) observation->storage_capacity = capacity;
    }
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
  if (observation != nullptr) {
    observation->reference_index = static_cast<std::int32_t>(index);
    observation->storage_capacity = capacity;
  }
  if (index >= static_cast<std::uint32_t>(capacity)) {
    if (observation != nullptr)
      observation->branch = game::ArmyNativeResolutionBranchV1::index_out_of_range;
    return nullptr;
  }
  void *object = Load<void *>(objects, index * 0x10ULL + 0x08);
  if (object == nullptr) {
    if (observation != nullptr)
      observation->branch = game::ArmyNativeResolutionBranchV1::entry_empty;
    return nullptr;
  }
  const auto entry_id = Load<std::int32_t>(object, 0x10);
  if (observation != nullptr) observation->entry_full_id = entry_id;
  if (entry_id != id) {
    if (observation != nullptr)
      observation->branch = game::ArmyNativeResolutionBranchV1::full_id_mismatch;
    return nullptr;
  }
  if (observation != nullptr)
    observation->branch = game::ArmyNativeResolutionBranchV1::resolved;
  return object;
}

void *Province(void *game_data, std::int32_t id) noexcept {
  if (game_data == nullptr || id < 1) return nullptr;
  void *array = Load<void *>(game_data, 0x140);
  const auto count = Load<std::int32_t>(game_data, 0x14C);
  if (array == nullptr || count <= 1 || id >= count) return nullptr;
  void *province = Load<void *>(array, static_cast<std::size_t>(id) * 8);
  return province != nullptr && Load<std::int32_t>(province, 0x10) == id
             ? province : nullptr;
}

std::string_view StateName(std::int32_t code) noexcept {
  switch (code) {
  case 1: return "regular";
  case 2: return "combat";
  case 3: return "sieging";
  case 4: return "embarked";
  case 5: return "gathering";
  case 6: return "retreating";
  case 7: return "moving";
  case 8: return "raiding";
  case 9: return "bartering";
  default: return "unknown";
  }
}

void Route(void *game_data, void *unit, game::ArmySnapshot &row) {
  row.route_province_ids.clear();
  row.route_read_status = game::ArmyRouteReadStatus::invalid_header;
  row.route_source_count.reset();
  row.move_target_observable = false;
  row.move_target_province_id = -1;
  void *data = Load<void *>(unit, 0x38);
  const auto capacity = Load<std::int32_t>(unit, 0x40);
  const auto count = Load<std::int32_t>(unit, 0x44);
  if (capacity < 0 || count < 0 || count > capacity || count > kMaximumRoute)
    return;
  row.route_source_count = count;
  if (count == 0) {
    row.route_read_status = game::ArmyRouteReadStatus::complete_empty;
    return;
  }
  row.route_read_status = game::ArmyRouteReadStatus::unresolved_entry;
  if (data == nullptr) return;
  std::vector<std::int32_t> route;
  route.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    void *info = Load<void *>(data, static_cast<std::size_t>(i) * 8);
    if (info == nullptr) return;
    const auto id = Load<std::int32_t>(info, 0);
    if (Province(game_data, id) == nullptr) return;
    route.push_back(id);
  }
  row.route_province_ids = std::move(route);
  row.route_read_status = game::ArmyRouteReadStatus::complete_nonempty;
  if (!row.route_province_ids.empty()) {
    row.move_target_observable = true;
    row.move_target_province_id = row.route_province_ids.back();
  }
}

game::ArmyMovementProgressSnapshot MovementProgress(
    const ArmyBindings &bindings, void *unit) {
  game::ArmyMovementProgressSnapshot result{};
  result.accumulated_movement_weight_raw = Load<std::int64_t>(unit, 0x168);
  result.cached_edge_speed_raw = Load<std::int64_t>(unit, 0x190);
  if (bindings.get_unit_state != nullptr)
    result.unit_state_raw = bindings.get_unit_state(unit);

  // Reuse the existing complete-route read. Empty is observed absence of a
  // current edge, not a guessed zero duration. State 7 alone does not prove a path.
  void *game_data = nullptr;
  if (bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr)
    game_data = Load<void *>(*bindings.game_state_slot, 0xA0);
  game::ArmySnapshot route{};
  Route(game_data, unit, route);
  if (route.route_read_status == game::ArmyRouteReadStatus::complete_empty) {
    result.status = game::ArmyMovementProgressStatus::not_applicable;
    return result;
  }
  if (route.route_read_status != game::ArmyRouteReadStatus::complete_nonempty) {
    result.unavailable_reason = "current_route_unavailable";
    return result;
  }

  constexpr std::int64_t unavailable = 0xFFFF'FFFFLL;
  if (bindings.get_unit_normalized_edge_progress != nullptr) {
    std::int64_t raw = 0;
    if (bindings.get_unit_normalized_edge_progress(unit, &raw) == &raw &&
        raw != unavailable)
      result.normalized_edge_progress_raw = raw;
  }
  if (bindings.get_unit_first_route_edge_duration != nullptr) {
    std::int64_t raw = 0;
    if (bindings.get_unit_first_route_edge_duration(unit, &raw, 0) == &raw &&
        raw != unavailable)
      result.first_route_edge_remaining_duration_raw = raw;
  }
  const bool progress = result.normalized_edge_progress_raw.has_value();
  const bool duration = result.first_route_edge_remaining_duration_raw.has_value();
  if (progress && duration) {
    result.status = game::ArmyMovementProgressStatus::available;
  } else if (progress || duration) {
    result.status = game::ArmyMovementProgressStatus::partial;
    result.unavailable_reason = progress ? "first_route_edge_duration_unavailable"
                                         : "normalized_edge_progress_unavailable";
  } else {
    result.unavailable_reason = "movement_getters_unavailable";
  }
  return result;
}

bool AddSoldiers(std::int64_t &sum, std::int32_t value) noexcept {
  if (value < 0 || sum > std::numeric_limits<std::int32_t>::max() - value)
    return false;
  sum += value;
  return true;
}

bool AddPower(std::int64_t &sum, std::int64_t value) noexcept {
  if ((value > 0 && sum > std::numeric_limits<std::int64_t>::max() - value) ||
      (value < 0 && sum < std::numeric_limits<std::int64_t>::min() - value))
    return false;
  sum += value;
  return true;
}

game::ArmyRegimentReplenishmentSnapshot Replenishment(
    const ArmyBindings &bindings, void *army_regiment, std::int32_t army_regiment_id) {
  game::ArmyRegimentReplenishmentSnapshot result{};
  result.army_regiment_id = army_regiment_id;
  // Native D14960 resolves this representative persistent regiment from the
  // FIRST DATA RECORD. +20 is data, not an array of record pointers. Further
  // record stride is not closed; the DTO preserves +2C count and coverage.
  const auto count = Load<std::int32_t>(army_regiment, 0x2C);
  if (count < 0) {
    result.unavailable_reason = "army_regiment_record_count_invalid";
    return result;
  }
  result.native_data_record_count = count;
  if (count == 0) {
    result.unavailable_reason = "army_regiment_first_record_absent";
    return result;
  }
  void *data = Load<void *>(army_regiment, 0x20);
  if (data == nullptr) {
    result.unavailable_reason = "army_regiment_first_record_unreadable";
    return result;
  }
  const auto persistent_id = Load<std::int32_t>(data, 0x08);
  void *persistent = Resolve(bindings.persistent_regiment_storage_slot, persistent_id);
  if (persistent == nullptr) {
    result.unavailable_reason = "persistent_regiment_not_found";
    return result;
  }
  if (Load<std::uint32_t>(persistent, 0x14) != 0x52656769U) {
    result.unavailable_reason = "persistent_regiment_identity_invalid";
    return result;
  }
  std::vector<void *> matching;
  for (std::int32_t index = 0; index < 7; ++index) {
    void *chunk = static_cast<std::byte *>(persistent) + 0x18 +
                  static_cast<std::size_t>(index) * 0x24;
    if (Load<std::int32_t>(chunk, 0x10) != army_regiment_id) continue;
    if (Load<std::int32_t>(chunk, 0x08) != persistent_id) {
      result.chunks.clear();
      result.unavailable_reason = "regiment_chunk_backlink_mismatch";
      return result;
    }
    const auto current = Load<std::int32_t>(chunk, 0x04);
    const auto maximum = Load<std::int32_t>(chunk, 0x00);
    if (current < 0 || maximum < 0) {
      result.chunks.clear();
      result.unavailable_reason = "regiment_chunk_soldiers_invalid";
      return result;
    }
    matching.push_back(chunk);
    game::ArmyRegimentReplenishmentChunk row{};
    row.persistent_regiment_id = persistent_id;
    row.chunk_index = index;
    row.current_soldiers = current;
    row.maximum_soldiers = maximum;
    row.state_raw = Load<std::int32_t>(chunk, 0x18);
    result.chunks.push_back(row);
  }
  if (matching.empty()) {
    result.unavailable_reason = "first_record_army_regiment_chunk_not_found";
    return result;
  }
  std::int64_t monthly_fraction = 0;
  bindings.get_regiment_monthly_replenishment_fraction(persistent, &monthly_fraction);
  for (std::size_t index = 0; index < matching.size(); ++index) {
    auto &row = result.chunks[index];
    // 262C700 may return true before its internal 2657F10 call. Preserve the
    // two native answers separately; no artificial conjunction or forecast.
    row.native_can_replenish = bindings.can_regiment_replenish(persistent, matching[index]);
    row.native_chunk_can_replenish = bindings.can_chunk_replenish(matching[index]);
    row.persistent_monthly_replenishment_fraction_raw = monthly_fraction;
  }
  result.available = true;
  return result;
}

game::ArmyLossApplicationInputsV1 LossApplicationInputs(
    const ArmyBindings &bindings, void *army, std::int32_t whole_soldiers) {
  game::ArmyLossApplicationInputsV1 result{};
  if (bindings.get_army_current_soldiers == nullptr ||
      bindings.siege_loss_rate_raw == nullptr ||
      bindings.raid_loss_rate_raw == nullptr ||
      bindings.get_army_whole_loss_budget == nullptr ||
      bindings.get_army_supply_loss_budget == nullptr ||
      bindings.is_army_siege_active == nullptr) {
    result.unavailable_reason = "loss_application_bindings_unavailable";
    return result;
  }
  result.raid_association_id = Load<std::int32_t>(army, 0x1E8);
  result.raid_active = result.raid_association_id != -1;
  result.siege_active = bindings.is_army_siege_active(army);
  result.siege_rate_raw = *bindings.siege_loss_rate_raw;
  result.raid_rate_raw = *bindings.raid_loss_rate_raw;
  result.whole_soldiers = whole_soldiers;
  void *descriptor = static_cast<std::byte *>(army) + 0x38;
  result.definition_le_zero_soldiers =
      bindings.get_army_current_soldiers(descriptor, 1);
  result.supply_eligible_soldiers =
      bindings.get_army_current_soldiers(descriptor, 2);
  result.definition_le_zero_supply_eligible_soldiers =
      bindings.get_army_current_soldiers(descriptor, 3);
  result.current_supply_loss_budget = bindings.get_army_supply_loss_budget(army);
  // Inactive modes are legitimate native zero branches. The loaded rate stays
  // observable even then, and independent integer budgets are never combined
  // through the UI's current aggregate attrition fraction.
  result.siege_loss_budget = result.siege_active
      ? bindings.get_army_whole_loss_budget(result.siege_rate_raw, army) : 0;
  result.raid_loss_budget = result.raid_active
      ? bindings.get_army_whole_loss_budget(result.raid_rate_raw, army) : 0;
  result.available = true;
  return result;
}

// Same generation lookup as the closed native leaves, with their actual
// fallback object. Char FullID is+18; Fleet FullID is+10.
void *ResolveBudgetObject(void **slot, void **fallback, std::int32_t id,
                          std::size_t id_offset, bool *used_fallback = nullptr) noexcept {
  void *objects = nullptr;
  std::int32_t capacity = 0;
  if (Storage(slot, objects, capacity)) {
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
    if (index < static_cast<std::uint32_t>(capacity)) {
      void *object = Load<void *>(objects, static_cast<std::size_t>(index) * 0x10 + 8);
      if (object != nullptr && Load<std::int32_t>(object, id_offset) == id) {
        if (used_fallback != nullptr) *used_fallback = false;
        return object;
      }
    }
  }
  if (used_fallback != nullptr) *used_fallback = true;
  return fallback == nullptr ? nullptr : *fallback;
}

template <class T>
std::optional<std::vector<T>> LoadedBudgetVector(
    const T **slot, const std::int32_t *count_pointer) {
  if (slot == nullptr || count_pointer == nullptr) return std::nullopt;
  const auto count = *count_pointer;
  // Native nonpositive counts select the invalid-index/zero component branch.
  if (count <= 0) return std::vector<T>{};
  if (*slot == nullptr) return std::nullopt;
  return std::vector<T>(*slot, *slot + count);
}

game::ArmyMonthlyLossBudgetInputsV1 MonthlyBudgetSample(
    const ArmyBindings &bindings, void *army, void *unit) {
  const auto &native = bindings.monthly_loss_budget_bindings;
  game::ArmyMonthlyLossBudgetInputsV1 result{};
  result.unit_native_170_raw = Load<std::int32_t>(unit, 0x170);
  result.army_gathering_count_raw = Load<std::int32_t>(army, 0x5C);
  if (native.is_unit_in_combat != nullptr)
    result.native_unit_in_combat = native.is_unit_in_combat(unit);
  if (native.is_unit_gathering != nullptr)
    result.native_unit_gathering = native.is_unit_gathering(unit);
  result.loaded_supply_state_levels = LoadedBudgetVector(
      native.supply_state_levels_slot, native.supply_state_levels_count);
  result.loaded_supply_state_fractions_raw = LoadedBudgetVector(
      native.supply_state_fractions_slot, native.supply_state_fractions_count);
  if (native.is_army_fleet_supply_active != nullptr) {
    if (!native.is_army_fleet_supply_active(army)) {
      result.native_fleet_supply_loss_suppressed = false;
    } else if (native.fleet_storage_slot != nullptr &&
               native.fleet_date_sentinel != nullptr &&
               bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr) {
      void *fleet = ResolveBudgetObject(native.fleet_storage_slot,
          native.fleet_fallback_slot, Load<std::int32_t>(army, 0x12C), 0x10);
      if (fleet != nullptr) {
        const auto date = Load<std::int32_t>(fleet, 0x20);
        const auto current_date = Load<std::int32_t>(*bindings.game_state_slot, 8);
        result.native_fleet_supply_loss_suppressed =
            date != *native.fleet_date_sentinel && date > current_date;
      }
    }
  }
  if (native.character_storage_slot != nullptr) {
    void *character = ResolveBudgetObject(native.character_storage_slot,
        native.character_fallback_slot, Load<std::int32_t>(army, 0x120), 0x18);
    if (character != nullptr) {
      result.commander_valid = Load<std::uint32_t>(character, 0x1C) == 0x43686172U &&
                               Load<std::int32_t>(character, 0x18) != -1;
      if (*result.commander_valid) {
        //24E0EB0 resolves this validated Army+124 Unit and returns Unit+20,
        // or the native province fallback. The ordinal belongs to that frame.
        void *province = Load<void *>(unit, 0x20);
        if (province == nullptr && native.province_fallback_slot != nullptr)
          province = *native.province_fallback_slot;
        void *province_type = province == nullptr ? nullptr : Load<void *>(province, 0x20);
        void *definition = province_type == nullptr ? nullptr : Load<void *>(province_type, 0xB8);
        if (definition != nullptr) {
          result.commander_supply_modifier_id = Load<std::uint16_t>(definition, 0x770);
          if (native.get_character_modifier_aggregator != nullptr &&
              native.read_character_modifier != nullptr) {
            void *context = native.get_character_modifier_aggregator(character);
            std::int64_t raw = 0;
            if (context != nullptr && native.read_character_modifier(
                    static_cast<std::byte *>(context) + 0x68, &raw,
                    *result.commander_supply_modifier_id) == &raw)
              result.commander_supply_modifier_raw = raw;
          }
        }
      }
    }
  }
  result.available = result.native_unit_in_combat.has_value() &&
      result.native_unit_gathering.has_value() &&
      result.loaded_supply_state_levels.has_value() &&
      result.loaded_supply_state_fractions_raw.has_value() &&
      result.native_fleet_supply_loss_suppressed.has_value() &&
      result.commander_valid.has_value() &&
      (!*result.commander_valid || (result.commander_supply_modifier_id.has_value() &&
                                   result.commander_supply_modifier_raw.has_value()));
  if (!result.available)
    result.unavailable_reason = "monthly_loss_budget_operands_unavailable";
  return result;
}

game::ArmyMonthlyLossBudgetInputsV1 MonthlyBudgetInputs(
    const ArmyBindings &bindings, void *army, void *unit) {
  const auto first = MonthlyBudgetSample(bindings, army, unit);
  const auto second = MonthlyBudgetSample(bindings, army, unit);
  if (first == second) return second;
  game::ArmyMonthlyLossBudgetInputsV1 unavailable{};
  unavailable.unavailable_reason = "monthly_loss_budget_inputs_changed_during_read";
  return unavailable;
}

std::optional<std::vector<std::int32_t>> CallerIdList(const void *descriptor) {
  if (descriptor == nullptr) return std::nullopt;
  const auto count = Load<std::int32_t>(descriptor, 0xC);
  if (count <= 0) return std::vector<std::int32_t>{};
  const auto *ids = Load<const std::int32_t *>(descriptor, 0);
  if (ids == nullptr) return std::nullopt;
  return std::vector<std::int32_t>(ids, ids + count);
}

game::ArmyMonthlyCallerEffectInputsV1 MonthlyCallerSample(
    const ArmyBindings &bindings, void *army, void *unit) {
  const auto &native = bindings.monthly_caller_effect_bindings;
  game::ArmyMonthlyCallerEffectInputsV1 result{};
  result.army_byte_22_raw = Load<std::uint8_t>(army, 0x22);
  const auto actor = Load<std::int32_t>(unit, 0x174);
  result.unit_actor_character_id = actor;
  if (bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr) {
    result.current_date_storage_raw64 = Load<std::int64_t>(*bindings.game_state_slot, 8);
    void *manager = Load<void *>(*bindings.game_state_slot, 0xA0);
    if (manager != nullptr)
      result.manager_army_id_list_2a5a8 = CallerIdList(
          static_cast<std::byte *>(manager) + 0x2A5A8);
  }
  void *character = ResolveBudgetObject(native.character_storage_slot,
      native.character_fallback_slot, actor, 0x18);
  if (character != nullptr) {
    void *realm = Load<void *>(character, 0x1C0);
    const void *descriptor = realm == nullptr ? native.empty_war_ids_descriptor
        : static_cast<std::byte *>(realm) + 0x318;
    const auto ids = CallerIdList(descriptor);
    if (ids) {
      result.war_counter_rows.emplace();
      result.war_counter_rows->reserve(ids->size());
      for (std::size_t index = 0; index < ids->size(); ++index) {
        game::ArmyMonthlyCallerWarCounterRowV1 row{};
        row.stored_index = static_cast<std::int32_t>(index);
        row.war_reference_id = (*ids)[index];
        bool fallback = false;
        void *war = ResolveBudgetObject(native.war_storage_slot,
            native.war_fallback_slot, row.war_reference_id, 8, &fallback);
        if (war != nullptr) {
          row.resolved_war_id = Load<std::int32_t>(war, 8);
          row.used_fallback = fallback;
          if (native.contains_war_participant != nullptr) {
            // Caller asks attacker first; a match bypasses the defender query.
            void *side = static_cast<std::byte *>(war) + 0x20;
            if (native.contains_war_participant(side, actor)) {
              row.native_selected_side = 0;
            } else {
              side = static_cast<std::byte *>(war) + 0x80;
              row.native_selected_side = native.contains_war_participant(side, actor) ? 1 : -1;
            }
            if (*row.native_selected_side != -1)
              row.native_counter_30_raw = Load<std::int32_t>(side, 0x30);
            row.available = true;
          }
        }
        if (!row.available) row.unavailable_reason = "monthly_caller_war_counter_unavailable";
        result.war_counter_rows->push_back(row);
      }
    }
  }
  result.available = result.current_date_storage_raw64.has_value() &&
      result.manager_army_id_list_2a5a8.has_value() && result.war_counter_rows.has_value();
  if (result.war_counter_rows)
    for (const auto &row : *result.war_counter_rows) result.available &= row.available;
  if (!result.available) result.unavailable_reason = "monthly_caller_effect_operands_unavailable";
  return result;
}

game::ArmyMonthlyCallerEffectInputsV1 MonthlyCallerInputs(
    const ArmyBindings &bindings, void *army, void *unit) {
  const auto first = MonthlyCallerSample(bindings, army, unit);
  const auto second = MonthlyCallerSample(bindings, army, unit);
  if (first == second) return second;
  game::ArmyMonthlyCallerEffectInputsV1 result{};
  result.unavailable_reason = "monthly_caller_effect_inputs_changed_during_read";
  return result;
}

game::ArmyDailyQueueInputsV1 DailyQueueSample(const ArmyBindings &bindings) {
  game::ArmyDailyQueueInputsV1 result{};
  if (bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr) {
    void *manager = Load<void *>(*bindings.game_state_slot, 0xA0);
    if (manager != nullptr)
      result.manager_army_id_list_2a5a8 = CallerIdList(
          static_cast<std::byte *>(manager) + 0x2A5A8);
  }
  if (result.manager_army_id_list_2a5a8) {
    result.initial_army_resolution_rows.emplace();
    const auto &ids = *result.manager_army_id_list_2a5a8;
    result.initial_army_resolution_rows->reserve(ids.size());
    for (std::size_t index = 0; index < ids.size(); ++index) {
      game::ArmyDailyQueueInitialResolutionRowV1 row{};
      row.stored_index = static_cast<std::int32_t>(index);
      row.raw_army_reference_id = ids[index];
      bool fallback = false;
      void *army = ResolveBudgetObject(bindings.internal_army_storage_slot,
          bindings.monthly_daily_queue_bindings.army_fallback_slot,
          row.raw_army_reference_id, 0x10, &fallback);
      if (army != nullptr) {
        row.resolved_army_id = Load<std::int32_t>(army, 0x10);
        row.used_fallback = fallback;
        row.army_magic_14_raw = Load<std::uint32_t>(army, 0x14);
        row.native_army_identity_valid = *row.army_magic_14_raw == 0x41726D79U &&
                                         *row.resolved_army_id != -1;
        row.available = true;
      } else row.unavailable_reason = "daily_queue_initial_army_resolution_unavailable";
      result.initial_army_resolution_rows->push_back(row);
    }
  }
  result.available = result.manager_army_id_list_2a5a8.has_value() &&
                     result.initial_army_resolution_rows.has_value();
  if (result.initial_army_resolution_rows)
    for (const auto &row : *result.initial_army_resolution_rows) result.available &= row.available;
  if (!result.available) result.unavailable_reason = "daily_queue_initial_operands_unavailable";
  return result;
}

game::ArmyDailyQueueInputsV1 DailyQueueInputs(const ArmyBindings &bindings) {
  const auto first = DailyQueueSample(bindings);
  const auto second = DailyQueueSample(bindings);
  if (first == second) return second;
  game::ArmyDailyQueueInputsV1 result{};
  result.unavailable_reason = "daily_queue_initial_inputs_changed_during_read";
  return result;
}

game::ArmyFirstRemovalCleanupInputsV1 EmptyCleanupInputs() {
  game::ArmyFirstRemovalCleanupInputsV1 result{};
  for (const auto *offset : {"50", "68", "80", "98", "c8", "158"})
    result.id_lists.push_back({offset, std::nullopt});
  return result;
}

game::ArmyFirstRemovalCleanupInputsV1 FirstRemovalCleanupSample(
    const ArmyBindings &bindings) {
  auto result = EmptyCleanupInputs();
  void *game_data = nullptr;
  if (bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr)
    game_data = Load<void *>(*bindings.game_state_slot, 0xA0);
  if (game_data == nullptr) {
    result.unavailable_reason = "first_removal_manager_unavailable";
    return result;
  }
  auto *manager = static_cast<std::byte *>(game_data) + 0x2A540;
  constexpr std::array<std::size_t, 6> offsets{0x50, 0x68, 0x80, 0x98, 0xC8, 0x158};
  for (std::size_t index = 0; index < offsets.size(); ++index)
    result.id_lists[index].ordered_army_ids = CallerIdList(manager + offsets[index]);
  const auto record_count = Load<std::int32_t>(manager, 0xBC);
  const auto *records = Load<const std::byte *>(manager, 0xB0);
  if (record_count <= 0 || records != nullptr) {
    result.records_b0.emplace();
    for (std::int32_t index = 0; index < record_count; ++index)
      result.records_b0->push_back(Load<std::array<std::uint32_t, 4>>(
          records, static_cast<std::size_t>(index) * 0x10));
  }

  // The queue helper resolves the passed Army once;2A98200 independently
  // resolves that object's FullID again. Those are distinct physical roles.
  const auto queue = DailyQueueSample(bindings);
  if (queue.manager_army_id_list_2a5a8 && queue.initial_army_resolution_rows) {
    result.candidate_found = false;
    for (const auto &row : *queue.initial_army_resolution_rows) {
      if (!row.available) { result.candidate_found.reset(); break; }
      if (*row.native_army_identity_valid) {
        result.candidate_found = true;
        result.candidate_stored_index = row.stored_index;
        result.argument_army_id = row.resolved_army_id;
        break;
      }
    }
  }
  if (result.candidate_found == true) {
    bool fallback = false;
    void *cleanup_army = ResolveBudgetObject(bindings.internal_army_storage_slot,
        bindings.monthly_daily_queue_bindings.army_fallback_slot,
        *result.argument_army_id, 0x10, &fallback);
    if (cleanup_army != nullptr) {
      result.cleanup_resolved_army_id = Load<std::int32_t>(cleanup_army, 0x10);
      result.cleanup_used_fallback = fallback;
      result.selected_bucket_index =
          static_cast<std::uint32_t>(*result.cleanup_resolved_army_id) % 30U;
      const auto bucket_offset = 0x198 + 0x18 * static_cast<std::size_t>(*result.selected_bucket_index);
      const auto count = Load<std::int32_t>(manager, bucket_offset + 0xC);
      const auto *pointers = Load<void *const *>(manager, bucket_offset);
      if (count <= 0 || pointers != nullptr) {
        result.selected_bucket_rows.emplace();
        for (std::int32_t index = 0; index < count; ++index) {
          game::ArmyManagerCleanupBucketRowV1 row{};
          row.stored_index = index;
          void *object = pointers[index];
          if (object != nullptr) row.observed_army_id = Load<std::int32_t>(object, 0x10);
          row.native_same_cleanup_army_pointer = object == cleanup_army;
          result.selected_bucket_rows->push_back(row);
        }
      }
    }
  }
  result.available = result.candidate_found.has_value();
  if (result.candidate_found == true) {
    result.available &= result.cleanup_resolved_army_id.has_value() &&
        result.selected_bucket_rows.has_value() && result.records_b0.has_value();
    for (const auto &row : result.id_lists) result.available &= row.ordered_army_ids.has_value();
  }
  if (!result.available) result.unavailable_reason = "first_removal_cleanup_operands_unavailable";
  return result;
}

game::ArmyFirstRemovalCleanupInputsV1 FirstRemovalCleanupInputs(
    const ArmyBindings &bindings) {
  const auto first = FirstRemovalCleanupSample(bindings);
  const auto second = FirstRemovalCleanupSample(bindings);
  if (first == second) return second;
  auto result = EmptyCleanupInputs();
  result.unavailable_reason = "first_removal_cleanup_inputs_changed_during_read";
  return result;
}

game::ArmyCountyEntryInputsV1 CountyEntryInputs(
    const ArmyBindings &bindings, void *army, void *unit,
    std::int32_t whole_soldiers) {
  game::ArmyCountyEntryInputsV1 result{};
  if (bindings.county_entry_minimum_soldiers == nullptr ||
      bindings.get_county_entry_loss_budget == nullptr ||
      bindings.get_county_entry_loss_fraction == nullptr ||
      bindings.get_county_entry_multiplier == nullptr) {
    result.unavailable_reason = "county_entry_budget_bindings_unavailable";
    return result;
  }
  std::int64_t fraction = 0, multiplier = 0;
  const auto *fraction_out = bindings.get_county_entry_loss_fraction(army, &fraction);
  const auto *multiplier_out = bindings.get_county_entry_multiplier(&multiplier, army);
  const auto budget = bindings.get_county_entry_loss_budget(army, nullptr);
  if (fraction_out != &fraction || multiplier_out != &multiplier ||
      budget < 0 || budget > whole_soldiers) {
    result.unavailable_reason = "county_entry_budget_native_output_invalid";
    return result;
  }
  result.available = true;
  result.whole_soldiers = whole_soldiers;
  result.current_loss_budget = budget;
  result.effective_fraction_raw = fraction;
  result.minimum_multiplier_raw = multiplier;
  result.loaded_minimum_soldiers = *bindings.county_entry_minimum_soldiers;
  result.condition_unavailable_reason = "county_entry_condition_bindings_unavailable";
  if (bindings.county_entry_condition == nullptr ||
      bindings.county_entry_character_storage_slot == nullptr) return result;
  result.condition_unavailable_reason = "county_entry_game_data_unavailable";
  if (bindings.game_state_slot == nullptr || *bindings.game_state_slot == nullptr)
    return result;
  void *game_data = Load<void *>(*bindings.game_state_slot, 0xA0);
  game::ArmySnapshot route{};
  Route(game_data, unit, route);
  if (route.route_read_status != game::ArmyRouteReadStatus::complete_nonempty) {
    result.condition_unavailable_reason =
        route.route_read_status == game::ArmyRouteReadStatus::complete_empty
            ? "no_stored_route" : "stored_route_unavailable";
    return result;
  }
  void *source = Load<void *>(unit, 0x20);
  result.condition_unavailable_reason = "current_province_unavailable";
  if (source == nullptr ||
      Province(game_data, Load<std::int32_t>(source, 0x10)) != source) return result;
  void *target = Province(game_data, route.route_province_ids.front());
  result.condition_unavailable_reason = "route_first_province_unavailable";
  if (target == nullptr) return result;
  // AEAA20(CArmy+124) is the same full-generation CUnit already resolved here.
  // Its +174 actor is a CCharacter; unlike CUnit, character FullID is at +18.
  const auto actor_id = Load<std::int32_t>(unit, 0x174);
  void *objects = nullptr;
  std::int32_t capacity = 0;
  result.condition_unavailable_reason = "actor_character_unresolved";
  if (actor_id < 0 ||
      !Storage(bindings.county_entry_character_storage_slot, objects, capacity))
    return result;
  const auto index = static_cast<std::uint32_t>(actor_id) & 0xFFFFFF;
  if (index >= static_cast<std::uint32_t>(capacity)) return result;
  void *actor = Load<void *>(objects, index * 0x10ULL + 0x08);
  if (actor == nullptr || Load<std::int32_t>(actor, 0x18) != actor_id) return result;
  const std::int32_t mode = Load<std::uint8_t>(army, 0x1D4) == 0 ? 1 : 0;
  result.condition_passes = bindings.county_entry_condition(actor, source, target, mode);
  result.condition_available = true;
  result.condition_unavailable_reason.clear();
  result.actor_character_id = actor_id;
  result.source_province_id = Load<std::int32_t>(source, 0x10);
  result.target_province_id = route.route_province_ids.front();
  result.mode = mode;
  return result;
}

game::ArmyStrengthSnapshot Strength(const ArmyBindings &bindings,
                                   const ArmyStrengthScope &scope) {
  game::ArmyStrengthSnapshot result{};
  result.army_id = scope.army_id;
  result.scope_role = scope.role;
  result.war_ids = scope.war_ids;
  void *unit = Resolve(bindings.unit_storage_slot, scope.army_id);
  if (unit == nullptr) {
    result.unavailable_reason = "public_cunit_not_found";
    return result;
  }
  const auto internal_id = Load<std::int32_t>(unit, 0x178);
  result.native_army_resolution_v1.emplace();
  void *army = Resolve(bindings.internal_army_storage_slot, internal_id,
                       &*result.native_army_resolution_v1);
  if (army == nullptr) {
    result.unavailable_reason = "native_carmy_not_found";
    return result;
  }
  result.native_carmy_id_observable = true;
  result.native_carmy_id = internal_id;
  void *ids = Load<void *>(army, 0x38);
  const auto capacity = Load<std::int32_t>(army, 0x40);
  const auto count = Load<std::int32_t>(army, 0x44);
  if (capacity < 0 || capacity > kMaximumRegiments || count < 0 ||
      count > capacity || (count > 0 && ids == nullptr)) {
    result.unavailable_reason = "regiment_array_invalid";
    return result;
  }
  std::int64_t current = 0, maximum = 0, power = 0;
  std::vector<game::ArmyRegimentStrengthSnapshot> regiment_strengths;
  regiment_strengths.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    const auto id = Load<std::int32_t>(ids, static_cast<std::size_t>(i) * 4);
    void *regiment = Resolve(bindings.regiment_storage_slot, id);
    if (regiment == nullptr) {
      result.unavailable_reason = "regiment_not_found";
      return result;
    }
    // 1.20 removed the 1.19 identity virtual predicate. Native getters now
    // compare the component magic and full ID directly (2A957A6/2C3E943).
    if (Load<std::uint32_t>(regiment, 0x14) != 0x41725267U ||
        Load<std::int32_t>(regiment, 0x10) == -1) {
      result.unavailable_reason = "regiment_identity_invalid";
      return result;
    }
    const auto current_value = Load<std::int32_t>(regiment, 0x38);
    const auto maximum_value = Load<std::int32_t>(regiment, 0x3C);
    if (!AddSoldiers(current, current_value) ||
        !AddSoldiers(maximum, maximum_value)) {
      result.unavailable_reason = current_value < 0 || maximum_value < 0
                                      ? "soldier_value_invalid"
                                      : "aggregate_overflow";
      return result;
    }
    if (!AddPower(power, Load<std::int64_t>(regiment, 0x40))) {
      result.unavailable_reason = "aggregate_overflow";
      return result;
    }
    game::ArmyRegimentStrengthSnapshot regiment_strength{};
    regiment_strength.army_regiment_id = id;
    regiment_strength.current_soldiers = current_value;
    regiment_strength.maximum_soldiers = maximum_value;
    if (bindings.is_regiment_supply_loss_eligible != nullptr) {
      g_army_strength_query_diagnostic_v1.reader.store("regiment_supply_loss_eligibility");
      regiment_strength.native_supply_loss_eligible =
          bindings.is_regiment_supply_loss_eligible(regiment);
      regiment_strength.supply_loss_eligibility_unavailable_reason.clear();
    }
    if (bindings.regiment_composition_enabled) {
      ReadRegimentComposition(regiment, regiment_strength);
    } else {
      regiment_strength.composition_unavailable_reason =
          "regiment_composition_not_bound";
    }
    regiment_strengths.push_back(std::move(regiment_strength));
  }
  g_army_strength_query_diagnostic_v1.reader.store("current_soldiers_getter");
  const auto native_current = bindings.get_army_current_soldiers(
      static_cast<std::byte *>(army) + 0x38, 0);
  g_army_strength_query_diagnostic_v1.reader.store("maximum_soldiers_getter");
  const auto native_maximum = bindings.get_army_maximum_soldiers(army);
  g_army_strength_query_diagnostic_v1.reader.store("scope_row_fields");
  if (native_current < 0 || native_maximum < 0 || native_current != current ||
      native_maximum != maximum) {
    result.unavailable_reason = "native_helper_mismatch";
    return result;
  }
  result.available = true;
  result.regiment_count = count;
  result.current_soldiers = native_current;
  result.maximum_soldiers = native_maximum;
  result.ai_base_power_raw = power;
  result.regiment_strengths = std::move(regiment_strengths);
  // Exact .3 selector 0x2587254 consumes this signed Q100000 operand.
  // The reviewed .2/.3 adapter binding owns the executable identity gate.
  if (Load<std::int32_t>(army, 0x124) == scope.army_id) {
    if (bindings.timing_bindings.enabled)
      result.army_update_clock_v1 = ck3_12003::ReadArmySupplyTiming(
          bindings, bindings.timing_bindings, army);
    if (bindings.current_movement_progress_enabled)
      result.current_movement_progress = MovementProgress(bindings, unit);
    if (bindings.get_army_gathering_days_left != nullptr &&
        bindings.get_unit_state != nullptr) {
      const auto state = bindings.get_unit_state(unit);
      if (state == 5) {
        // Native EAX is whole remaining game days, already clamped at zero.
        // The receiver is the resolved CArmy, never its public CUnit.
        result.gathering_days_left = bindings.get_army_gathering_days_left(army);
        result.gathering_days_status = game::ArmyGatheringDaysStatus::available;
      } else if (state >= 1 && state <= 9) {
        result.gathering_days_status = game::ArmyGatheringDaysStatus::not_gathering;
      }
    }
    if (bindings.get_merge_destination_weight_part_a != nullptr &&
        bindings.get_merge_destination_weight_part_b != nullptr) {
      std::int64_t part_a = 0, part_b = 0;
      const auto *returned_a = bindings.get_merge_destination_weight_part_a(
          army, &part_a, 0);
      const auto *returned_b = bindings.get_merge_destination_weight_part_b(
          army, &part_b);
      const auto source_weight = std::int64_t{native_current} * 100'000;
      // The two native filters are disjoint subsets of the validated array.
      // An unexpected operand remains unobserved; ordinary strength survives.
      if (returned_a == &part_a && returned_b == &part_b && part_a >= 0 &&
          part_b >= 0 && part_a <= source_weight &&
          part_b <= source_weight - part_a) {
        result.merge_supply_destination_weight_raw = part_a + part_b;
      }
    }
    result.current_supply_raw = Load<std::int64_t>(army, 0x180);
    if (bindings.get_army_supply_capacity != nullptr) {
      std::int64_t raw = 0;
      bindings.get_army_supply_capacity(&raw, army, nullptr);
      result.current_supply_capacity_raw = raw;
    }
    if (bindings.get_army_attrition_fraction != nullptr) {
      std::int64_t raw = 0;
      bindings.get_army_attrition_fraction(army, &raw, nullptr);
      result.current_attrition_fraction_raw = raw;
    }
    if (bindings.get_army_monthly_supply_change != nullptr &&
        bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr) {
      void *game_data = Load<void *>(*bindings.game_state_slot, 0xA0);
      void *province = Load<void *>(unit, 0x20);
      if (province != nullptr &&
          Province(game_data, Load<std::int32_t>(province, 0x10)) == province) {
        std::int64_t raw = 0;
        bindings.get_army_monthly_supply_change(army, &raw, province, nullptr);
        result.current_supply_change_monthly_raw = raw;
      }
    }
    if (bindings.loss_application_inputs_enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("loss_application_inputs_getters");
      result.loss_application_inputs_v1 =
          LossApplicationInputs(bindings, army, native_current);
    }
    if (bindings.monthly_loss_budget_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("monthly_loss_budget_inputs_readonly");
      result.monthly_loss_budget_inputs_v1 = MonthlyBudgetInputs(bindings, army, unit);
    }
    if (bindings.monthly_caller_effect_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("monthly_caller_effect_inputs_readonly");
      result.monthly_caller_effect_inputs_v1 = MonthlyCallerInputs(bindings, army, unit);
    }
    if (bindings.monthly_daily_queue_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("daily_queue_initial_inputs_readonly");
      result.monthly_daily_queue_inputs_v1 = DailyQueueInputs(bindings);
    }
    if (bindings.monthly_first_removal_cleanup_inputs_enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("first_removal_cleanup_inputs_readonly");
      result.monthly_first_removal_cleanup_inputs_v1 = FirstRemovalCleanupInputs(bindings);
    }
    if (bindings.monthly_current_helper_domain_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_helper_domain_inputs_readonly");
      result.monthly_current_helper_domain_inputs_v1 =
          ReadCurrentHelperDomainInputs12003(bindings, army);
    }
    if (bindings.monthly_current_helper_point_store_inputs_enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_helper_point_store_inputs_readonly");
      result.monthly_current_helper_point_store_inputs_v1 =
           ReadCurrentHelperPointStoreInputs12003(bindings, army);
    }
    if (bindings.current_province_supply_contributor_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_province_supply_contributors_readonly");
      void *province = Load<void *>(unit, 0x20);
      void *game_data = bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr
          ? Load<void *>(*bindings.game_state_slot, 0xA0) : nullptr;
      if (province != nullptr &&
          Province(game_data, Load<std::int32_t>(province, 0x10)) != province) province = nullptr;
      result.current_province_supply_contributors_v1 =
          ck3_12003::ReadCurrentProvinceSupplyContributors12003(bindings, army, unit, province);
    }
    if (bindings.current_province_besieging_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_province_besieging_contributors_readonly");
      void *province = Load<void *>(unit, 0x20);
      if (province == nullptr && bindings.current_province_besieging_bindings.province_fallback_slot != nullptr)
        province = *bindings.current_province_besieging_bindings.province_fallback_slot;
      void *game_data = bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr
          ? Load<void *>(*bindings.game_state_slot, 0xA0) : nullptr;
      if (province != nullptr &&
          Province(game_data, Load<std::int32_t>(province, 0x10)) != province) province = nullptr;
      result.current_province_besieging_contributors_v1 =
          ck3_12003::ReadCurrentProvinceBesiegingContributors12003(bindings, province);
    }
    if (bindings.current_land_resupply_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_land_resupply_readonly");
      void *province = Load<void *>(unit, 0x20);
      void *game_data = bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr
          ? Load<void *>(*bindings.game_state_slot, 0xA0) : nullptr;
      if (province != nullptr &&
          Province(game_data, Load<std::int32_t>(province, 0x10)) != province) province = nullptr;
      result.current_land_resupply_v1 = ck3_12003::ReadCurrentLandResupply12003(
          bindings.current_land_resupply_bindings, army, unit, province);
      if (bindings.current_land_supply_rate_bindings.enabled) {
        g_army_strength_query_diagnostic_v1.reader.store("current_land_supply_rate_inputs_readonly");
        result.current_land_supply_rate_inputs_v1 = ck3_12003::ReadCurrentLandSupplyRateInputs12003(
            bindings.current_land_supply_rate_bindings, army, unit, province,
            &*result.current_land_resupply_v1);
      }
    }
    if (bindings.current_fleet_supply_tick_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("current_fleet_supply_tick_inputs_readonly");
      void *province = Load<void *>(unit, 0x20);
      void *game_data = bindings.game_state_slot != nullptr && *bindings.game_state_slot != nullptr
          ? Load<void *>(*bindings.game_state_slot, 0xA0) : nullptr;
      if (province != nullptr &&
          Province(game_data, Load<std::int32_t>(province, 0x10)) != province) province = nullptr;
      std::optional<bool> native_fleet_branch;
      if (result.current_land_resupply_v1 &&
          result.current_land_resupply_v1->native_land_branch_applicable.has_value())
        native_fleet_branch = !*result.current_land_resupply_v1->native_land_branch_applicable;
      std::optional<std::int32_t> native_date;
      if (result.army_update_clock_v1) native_date = result.army_update_clock_v1->current_date_raw;
      std::optional<std::int64_t> divisor_floor, max_loss;
      if (result.current_land_supply_rate_inputs_v1) {
        divisor_floor = result.current_land_supply_rate_inputs_v1->loaded_divisor_floor_raw;
        max_loss = result.current_land_supply_rate_inputs_v1->loaded_max_loss_raw;
      }
      result.current_fleet_supply_tick_inputs_v1 = ck3_12003::ReadCurrentFleetSupplyTickInputs12003(
          bindings.current_fleet_supply_tick_bindings, bindings, army, unit, province,
          native_fleet_branch, native_date, divisor_floor, max_loss);
    }
    if (bindings.county_entry_inputs_enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("county_entry_current_inputs_getters");
      result.county_entry_inputs_v1 = CountyEntryInputs(bindings, army, unit, native_current);
    }
    if (bindings.persistent_regiment_storage_slot != nullptr &&
        bindings.can_regiment_replenish != nullptr &&
        bindings.can_chunk_replenish != nullptr &&
        bindings.get_regiment_monthly_replenishment_fraction != nullptr) {
      result.regiment_replenishment.emplace();
      result.regiment_replenishment_records_v1.emplace();
      result.regiment_replenishment_records_v1->reserve(static_cast<std::size_t>(count));
      result.regiment_replenishment->reserve(static_cast<std::size_t>(count));
      for (std::int32_t i = 0; i < count; ++i) {
        const auto id = Load<std::int32_t>(ids, static_cast<std::size_t>(i) * 4);
        result.regiment_replenishment->push_back(
            Replenishment(bindings, Resolve(bindings.regiment_storage_slot, id), id));
        result.regiment_replenishment_records_v1->push_back(
            ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(
                bindings, Resolve(bindings.regiment_storage_slot, id), id));
      }
      result.fixed_chunk0_preparation_inputs_v1 =
          ck3_12003::ReadFixedChunk0PreparationInputsV1(bindings, result);
    }
    if (bindings.scoped_ordered_refill_bindings.enabled) {
      g_army_strength_query_diagnostic_v1.reader.store("scoped_ordered_refill_inputs_readonly");
      const auto records = result.regiment_replenishment_records_v1
          ? std::span<const game::ArmyRegimentReplenishmentRecordsSnapshotV1>(*result.regiment_replenishment_records_v1)
          : std::span<const game::ArmyRegimentReplenishmentRecordsSnapshotV1>{};
      result.scoped_ordered_refill_inputs_v1 =
          ck3_12003::ReadScopedOrderedRefillInputs12003(bindings, army, unit, records);
    }
    if (bindings.ordered_besieging_refill_bindings.enabled && result.current_province_besieging_contributors_v1) {
      g_army_strength_query_diagnostic_v1.reader.store("ordered_besieging_refill_inputs_readonly");
      result.ordered_besieging_refill_inputs_v1 = ck3_12003::ReadOrderedBesiegingRefillInputs12003(
          bindings, army, unit, *result.current_province_besieging_contributors_v1);
      g_army_strength_query_diagnostic_v1.reader.store("ordered_B_fixed_chunk0_preparation_readonly");
      result.ordered_besieging_fixed_chunk0_preparation_inputs_v1 =
          ck3_12003::ReadOrderedBesiegingFixedChunk0PreparationInputs12003(
              bindings, *result.ordered_besieging_refill_inputs_v1);
    }
  }
  return result;
}

int Priority(game::ArmyStrengthScopeRole role) {
  return role == game::ArmyStrengthScopeRole::player ? 2 :
         role == game::ArmyStrengthScopeRole::active_war_ally ? 1 : 0;
}

void AppendScope(std::vector<ArmyStrengthScope> &scope, std::int32_t id,
                 game::ArmyStrengthScopeRole role, std::int32_t war) {
  auto existing = std::find_if(scope.begin(), scope.end(),
                              [id](const auto &item) { return item.army_id == id; });
  if (existing == scope.end()) {
    scope.push_back({id, role, {}});
    existing = std::prev(scope.end());
  } else if (Priority(role) > Priority(existing->role)) existing->role = role;
  if (war != -1 && std::find(existing->war_ids.begin(), existing->war_ids.end(),
                            war) == existing->war_ids.end())
    existing->war_ids.push_back(war);
}

} // namespace

void ReadOwnedRegimentTypeV1(
    void *, void *maa_type,
    ck3_12003::OwnedRegimentTypeSnapshotV1 &output) noexcept {
  game::ArmyRegimentStrengthSnapshot observed;
  ReadMaaTypeCompositionV1(maa_type, observed);
  switch (observed.maa_type_status) {
  case game::ArmyRegimentTypeStatusV1::available:
    output.status = ck3_12003::OwnedRegimentTypeStatusV1::available;
    break;
  case game::ArmyRegimentTypeStatusV1::absent:
    output.status = ck3_12003::OwnedRegimentTypeStatusV1::absent;
    break;
  case game::ArmyRegimentTypeStatusV1::unavailable:
    output.status = ck3_12003::OwnedRegimentTypeStatusV1::unavailable;
    break;
  }
  output.maa_type_key = std::move(observed.maa_type_key);
  output.siege_tier = observed.siege_tier;
  output.unavailable_reason = std::move(observed.composition_unavailable_reason);
}

ArmyBindings BindArmyImage(std::uintptr_t image_base,
                          std::string_view executable_sha256) noexcept {
  ArmyBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(image_base + 0x5C68C50);
  result.unit_storage_slot = reinterpret_cast<void **>(image_base + kUnitStorageSlotRva12002);
  result.internal_army_storage_slot = reinterpret_cast<void **>(image_base + kInternalArmyStorageSlotRva12002);
  result.regiment_storage_slot = reinterpret_cast<void **>(image_base + kRegimentStorageSlotRva12002);
  result.get_unit_state = reinterpret_cast<decltype(result.get_unit_state)>(image_base + kUnitStateRva12002);
  result.get_army_current_soldiers = reinterpret_cast<decltype(result.get_army_current_soldiers)>(image_base + kArmyCurrentSoldiersRva12002);
  result.get_army_maximum_soldiers = reinterpret_cast<decltype(result.get_army_maximum_soldiers)>(image_base + kArmyMaximumSoldiersRva12002);
  return result;
}

void *ResolveArmyUnit(const ArmyBindings &bindings,
                      std::int32_t unit_id) noexcept {
  return bindings.enabled ? Resolve(bindings.unit_storage_slot, unit_id)
                          : nullptr;
}

void *ResolveInternalArmy(const ArmyBindings &bindings,
                          std::int32_t internal_army_id) noexcept {
  return bindings.enabled
             ? Resolve(bindings.internal_army_storage_slot, internal_army_id)
             : nullptr;
}

bool ReadArmyGathering(const ArmyBindings &bindings, std::int32_t unit_id,
                       bool &gathering) noexcept {
  gathering = false;
  void *unit = ResolveArmyUnit(bindings, unit_id);
  if (unit == nullptr || bindings.get_unit_state == nullptr) return false;
  const auto state = bindings.get_unit_state(unit);
  if (state < 1 || state > 9) return false;
  gathering = state == 5;
  return true;
}

bool ReadArmiesForCharacters(const ArmyBindings &bindings,
                            std::span<const std::int32_t> owners,
                            std::vector<game::ArmySnapshot> &output,
                            std::int32_t controlled_owner) noexcept {
  output.clear();
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      *bindings.game_state_slot == nullptr || bindings.get_unit_state == nullptr)
    return false;
  void *objects = nullptr;
  std::int32_t capacity = 0;
  if (!Storage(bindings.unit_storage_slot, objects, capacity)) return false;
  void *game_data = Load<void *>(*bindings.game_state_slot, 0xA0);
  if (game_data == nullptr) return false;
  for (std::int32_t i = 0; i < capacity; ++i) {
    void *unit = Load<void *>(objects, static_cast<std::size_t>(i) * 0x10 + 8);
    if (unit == nullptr) continue;
    const auto id = Load<std::int32_t>(unit, 0x10);
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0xFFFFFF) !=
                       static_cast<std::uint32_t>(i)) continue;
    const auto owner = Load<std::int32_t>(unit, 0x174);
    if (!owners.empty() && std::find(owners.begin(), owners.end(), owner) == owners.end()) continue;
    game::ArmySnapshot row{};
    row.army_id = id;
    row.owner_character_id = owner;
    row.controllable = controlled_owner != -1 && owner == controlled_owner;
    void *province = Load<void *>(unit, 0x20);
    if (province != nullptr) {
      const auto province_id = Load<std::int32_t>(province, 0x10);
      if (Province(game_data, province_id) == province) {
        row.has_current_province = true;
        row.current_province_id = province_id;
      }
    }
    const auto state = bindings.get_unit_state(unit);
    if (state >= 1 && state <= 9) row.army_state_code = state;
    row.army_state = StateName(row.army_state_code);
    row.in_combat = row.army_state_code == 2;
    row.retreating = Load<std::int32_t>(unit, 0x170) > 0;
    Route(game_data, unit, row);
    output.push_back(std::move(row));
  }
  return true;
}

game::ReadArmyStrengthsResult ReadArmyStrengthsForScope(
    const ArmyBindings &bindings, std::span<const ArmyStrengthScope> scope,
    std::vector<game::ArmyStrengthSnapshot> &output) noexcept {
  auto &diagnostic = g_army_strength_query_diagnostic_v1;
  diagnostic.reader.store("scope_bindings");
  diagnostic.scope_rows.store(static_cast<std::int64_t>(scope.size()));
  output.clear();
  if (!bindings.enabled || bindings.unit_storage_slot == nullptr ||
      bindings.internal_army_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.get_army_current_soldiers == nullptr ||
      bindings.get_army_maximum_soldiers == nullptr)
    return game::ReadArmyStrengthsResult::unavailable;
  bool partial = false;
  std::optional<game::ArmyCurrentDailyAssaultTableV1> current_daily_assault_table;
  if (!scope.empty() && bindings.current_daily_assault_table_bindings.enabled) {
    diagnostic.reader.store("current_daily_assault_table_readonly");
    current_daily_assault_table = ck3_12003::ReadCurrentDailyAssaultTable12003(
        bindings.current_daily_assault_table_bindings);
  }
  std::optional<game::ArmyCurrentDailyAssaultLossInputsV1> current_daily_assault_loss;
  if (current_daily_assault_table && bindings.current_daily_assault_loss_inputs_enabled) {
    diagnostic.reader.store("current_daily_assault_loss_readonly");
    current_daily_assault_loss = ck3_12003::ReadCurrentDailyAssaultLossInputs12003(
        bindings, *current_daily_assault_table);
  }
  std::optional<game::ArmyCurrentDailyAssaultRosterAdmissionV1> current_daily_assault_roster_admission;
  std::optional<game::ArmyPreDateDatedAppendInputsV1> current_pre_date_dated_append;
  std::optional<game::ArmyCurrentPostAdmissionRefreshInputsV1> current_post_admission_refresh;
  std::optional<game::ArmyCurrentCondition30InputsV1> current_army_condition30;
  std::optional<game::ArmyCurrentFlag20InputsV1> current_army_flag20;
  std::optional<game::ArmyCurrentFlag21InputsV1> current_army_flag21;
  std::optional<game::ArmyCurrentFlag31InputsV1> current_army_flag31;
  std::optional<game::ArmyCurrentPreDatePendingUpdateInputsV1> current_pre_date_pending_update;
  std::optional<game::ArmyCurrentPreDateCharacterPrefixInputsV1> current_pre_date_character_prefix;
  std::optional<game::ArmyCurrentAssaultRemovalReferenceInputsV1> current_assault_removal_references;
  std::optional<game::ArmyCurrentCandidateDetachmentMapperInputsV1> current_candidate_detachment_mapper;
  for (const auto &entry : scope) {
    diagnostic.army_id.store(entry.army_id);
    diagnostic.reader.store("scope_row");
    auto row = Strength(bindings, entry);
    if (!current_pre_date_dated_append && bindings.current_pre_date_dated_append_bindings.common.enabled) {
      diagnostic.reader.store("pre_date_dated_append_readonly");
      current_pre_date_dated_append = ck3_12003::ReadPreDateDatedAppend12003(
          bindings.current_pre_date_dated_append_bindings,
          row.monthly_first_removal_cleanup_inputs_v1 ? &*row.monthly_first_removal_cleanup_inputs_v1 : nullptr,
          row.army_update_clock_v1 ? &*row.army_update_clock_v1 : nullptr);
    }
    row.current_pre_date_dated_append_inputs_v1 = current_pre_date_dated_append;
    if (!current_daily_assault_roster_admission &&
        bindings.current_daily_assault_roster_admission_bindings.enabled) {
      diagnostic.reader.store("current_daily_assault_roster_admission_readonly");
      current_daily_assault_roster_admission = ck3_12003::ReadCurrentDailyAssaultRosterAdmission12003(
          bindings.current_daily_assault_roster_admission_bindings,
          row.monthly_daily_queue_inputs_v1 ? &*row.monthly_daily_queue_inputs_v1 : nullptr);
    }
    if (!current_pre_date_pending_update && current_daily_assault_roster_admission &&
        bindings.current_pre_date_pending_update_bindings.common.enabled) {
      diagnostic.reader.store("current_pre_date_pending_update_readonly");
      current_pre_date_pending_update = ck3_12003::ReadCurrentPreDatePendingUpdateInputs12003(
          bindings.current_pre_date_pending_update_bindings, *current_daily_assault_roster_admission,
          row.monthly_daily_queue_inputs_v1 ? &*row.monthly_daily_queue_inputs_v1 : nullptr);
    }
    if (!current_post_admission_refresh && current_daily_assault_roster_admission &&
        bindings.current_post_admission_refresh_bindings.common.enabled) {
      diagnostic.reader.store("current_post_admission_refresh_readonly");
      current_post_admission_refresh = ck3_12003::ReadCurrentPostAdmissionRefreshInputs12003(
          bindings.current_post_admission_refresh_bindings, *current_daily_assault_roster_admission,
          current_pre_date_pending_update ? &*current_pre_date_pending_update : nullptr,
          current_daily_assault_table ? &*current_daily_assault_table : nullptr);
    }
    if (!current_army_condition30 && current_post_admission_refresh &&
        bindings.current_army_condition30_bindings.common.enabled) {
      diagnostic.reader.store("current_army_condition30_readonly");
      current_army_condition30 = ck3_12003::ReadCurrentArmyCondition30Inputs12003(
          bindings.current_army_condition30_bindings, *current_post_admission_refresh);
    }
    row.current_army_condition30_inputs_v1 = current_army_condition30;
    if (!current_army_flag20 && current_post_admission_refresh &&
        bindings.current_army_flag20_bindings.common.enabled) {
      diagnostic.reader.store("current_army_flag20_readonly");
      current_army_flag20 = ck3_12003::ReadCurrentArmyFlag20Inputs12003(
          bindings.current_army_flag20_bindings, *current_post_admission_refresh);
    }
    row.current_army_flag20_inputs_v1 = current_army_flag20;
    if (!current_army_flag21 && current_post_admission_refresh &&
        bindings.current_army_flag21_bindings.common.enabled) {
      diagnostic.reader.store("current_army_flag21_readonly");
      current_army_flag21 = ck3_12003::ReadCurrentArmyFlag21Inputs12003(
          bindings.current_army_flag21_bindings, *current_post_admission_refresh);
    }
    row.current_army_flag21_inputs_v1 = current_army_flag21;
    if (!current_army_flag31 && current_post_admission_refresh &&
        bindings.current_army_flag31_bindings.common.enabled) {
      diagnostic.reader.store("current_army_flag31_readonly");
      current_army_flag31 = ck3_12003::ReadCurrentArmyFlag31Inputs12003(
          bindings.current_army_flag31_bindings, *current_post_admission_refresh);
    }
    row.current_army_flag31_inputs_v1 = current_army_flag31;
    row.current_post_admission_refresh_inputs_v1 = current_post_admission_refresh;
    row.current_pre_date_pending_update_inputs_v1 = current_pre_date_pending_update;
    if (!current_pre_date_character_prefix && current_daily_assault_roster_admission &&
        bindings.current_pre_date_character_prefix_bindings.common.enabled) {
      diagnostic.reader.store("current_pre_date_character_prefix_readonly");
      current_pre_date_character_prefix = ck3_12003::ReadCurrentPreDateCharacterPrefixInputs12003(
          bindings.current_pre_date_character_prefix_bindings, *current_daily_assault_roster_admission,
          current_pre_date_pending_update ? &*current_pre_date_pending_update : nullptr,
          row.monthly_first_removal_cleanup_inputs_v1 ? &*row.monthly_first_removal_cleanup_inputs_v1 : nullptr);
    }
    row.current_pre_date_character_prefix_inputs_v1 = current_pre_date_character_prefix;
    row.current_daily_assault_table_v1 = current_daily_assault_table;
    row.current_daily_assault_loss_inputs_v1 = current_daily_assault_loss;
    row.current_daily_assault_roster_admission_v1 = current_daily_assault_roster_admission;
    if (!current_assault_removal_references && bindings.current_assault_removal_reference_bindings.enabled) {
      diagnostic.reader.store("current_assault_removal_references_readonly");
      current_assault_removal_references = ck3_12003::ReadCurrentAssaultRemovalReferenceInputs12003(
          bindings.current_assault_removal_reference_bindings,
          row.monthly_daily_queue_inputs_v1 ? &*row.monthly_daily_queue_inputs_v1 : nullptr,
          row.monthly_first_removal_cleanup_inputs_v1 ? &*row.monthly_first_removal_cleanup_inputs_v1 : nullptr,
          current_daily_assault_table ? &*current_daily_assault_table : nullptr);
    }
    if (!current_candidate_detachment_mapper && bindings.current_candidate_detachment_mapper_bindings.enabled) {
      diagnostic.reader.store("current_candidate_detachment_mapper_readonly");
      current_candidate_detachment_mapper = ck3_12003::ReadCurrentCandidateDetachmentMapper12003(
          bindings.current_candidate_detachment_mapper_bindings,
          current_assault_removal_references ? &*current_assault_removal_references : nullptr);
    }
    row.current_candidate_detachment_mapper_inputs_v1 = current_candidate_detachment_mapper;
    row.current_assault_removal_reference_inputs_v1 = current_assault_removal_references;
    partial = partial || !row.available;
    output.push_back(std::move(row));
  }
  return partial ? game::ReadArmyStrengthsResult::partial
                 : game::ReadArmyStrengthsResult::available;
}

game::ReadArmyStrengthsResult ReadArmyStrengths(
    const ArmyBindings &bindings, const game::Snapshot &snapshot,
    std::vector<game::ArmyStrengthSnapshot> &output) noexcept {
  output.clear();
  g_army_strength_query_diagnostic_v1.reader.store("fullscope_admission");
  if (!bindings.enabled) return game::ReadArmyStrengthsResult::unavailable;
  if (!snapshot.paused) return game::ReadArmyStrengthsResult::requires_paused;
  if (!snapshot.has_played_character)
    return game::ReadArmyStrengthsResult::no_played_character;
  std::vector<ArmyStrengthScope> scope;
  for (const auto &army : snapshot.player_armies)
    AppendScope(scope, army.army_id, game::ArmyStrengthScopeRole::player, -1);
  for (const auto &war : snapshot.active_wars) {
    for (const auto &army : war.allied_armies)
      AppendScope(scope, army.army_id, game::ArmyStrengthScopeRole::active_war_ally, war.war_id);
    for (const auto &army : war.enemy_armies)
      AppendScope(scope, army.army_id, game::ArmyStrengthScopeRole::active_war_enemy, war.war_id);
  }
  return ReadArmyStrengthsForScope(bindings, scope, output);
}

game::ArmyProvinceSupplySnapshot ReadArmyProvinceSupplyForPreview(
    const ArmyBindings &bindings, const MilitaryWorldAccess &world,
    const game::PreviewMoveArmyResult &preview) noexcept {
  game::ArmyProvinceSupplySnapshot output{};
  output.army_id = preview.army_id;
  output.current.role = game::ArmyProvinceSupplyRole::current;
  output.current.province_id = preview.origin_province_id;
  output.target.role = game::ArmyProvinceSupplyRole::target;
  output.target.province_id = preview.target_province_id;
  const auto unavailable = [&](const char *reason) {
    output.unavailable_reason = reason;
    output.current.unavailable_reason = reason;
    output.target.unavailable_reason = reason;
    return output;
  };
  if (preview.status != game::PreviewMoveArmyStatus::available)
    return unavailable("route_preview_unavailable");
  if (!bindings.enabled || bindings.get_province_supply_limit == nullptr ||
      bindings.get_province_supply_usage == nullptr ||
      world.resolve_character == nullptr || world.resolve_province == nullptr)
    return unavailable("native_province_supply_bindings_unavailable");
  void *const unit = ResolveArmyUnit(bindings, preview.army_id);
  if (unit == nullptr) return unavailable("public_cunit_not_found");
  const auto native_id = Load<std::int32_t>(unit, 0x178);
  void *const army = ResolveInternalArmy(bindings, native_id);
  if (army == nullptr) return unavailable("native_carmy_not_found");
  output.native_carmy_id = native_id;
  if (Load<std::int32_t>(army, 0x124) != preview.army_id)
    return unavailable("native_carmy_backlink_unresolved");
  const auto owner_id = Load<std::int32_t>(unit, 0x174);
  void *const owner = world.resolve_character(world.context, owner_id);
  if (owner == nullptr) return unavailable("army_owner_character_unresolved");
  output.owner_character_id = owner_id;
  const auto commander_id = Load<std::int32_t>(army, 0x120);
  void *commander = commander_id == -1 ? nullptr
      : world.resolve_character(world.context, commander_id);
  if (commander != nullptr) {
    output.commander_character_id = commander_id;
  } else {
    // Native 24E5A74 uses the canonical CCharacter fallback object. The limit
    // leaf dereferences its commander argument, so an absent ID is not nullptr.
    commander = bindings.province_supply_character_fallback_slot == nullptr
        ? nullptr : *bindings.province_supply_character_fallback_slot;
    if (commander == nullptr)
      return unavailable("native_commander_fallback_unavailable");
  }
  const auto read_province = [&](game::ArmyProvinceSupplyRow &row) {
    void *const province = world.resolve_province(world.context, row.province_id);
    if (province == nullptr) {
      row.unavailable_reason = "province_not_found";
      return;
    }
    if (row.role == game::ArmyProvinceSupplyRole::current &&
        Load<void *>(unit, 0x20) != province) {
      row.unavailable_reason = "current_province_scope_changed";
      return;
    }
    // Both native leaves return whole signed EAX values. Zero and INT32_MAX
    // remain successful values. Usage's mode 0 keeps currently present routes.
    row.native_supply_limit_soldiers =
        bindings.get_province_supply_limit(province, owner, commander, nullptr);
    row.native_supply_usage_soldiers =
        bindings.get_province_supply_usage(province, owner, 0, nullptr);
    row.available = true;
  };
  read_province(output.current);
  if (output.current.available &&
      output.current.province_id == output.target.province_id) {
    output.target = output.current;
    output.target.role = game::ArmyProvinceSupplyRole::target;
  } else {
    read_province(output.target);
  }
  if (output.current.available && output.target.available) {
    output.status = game::ArmyProvinceSupplyStatus::available;
  } else {
    output.status = output.current.available || output.target.available
        ? game::ArmyProvinceSupplyStatus::partial
        : game::ArmyProvinceSupplyStatus::unavailable;
    output.unavailable_reason = "province_supply_scope_incomplete";
  }
  return output;
}

} // namespace xar::ck3_12002

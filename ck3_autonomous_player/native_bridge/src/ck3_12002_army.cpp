#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_query_diagnostic_v1.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

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

void ReadRegimentComposition(
    void *regiment, game::ArmyRegimentStrengthSnapshot &output) noexcept {
  // The existing combat reader uses this ArRg -> GDbo type/key path. Exact .3
  // province tier getter 0x247EFC0 reads the same type's signed +0x2A0 operand.
  void *const maa_type = Load<void *>(regiment, 0x18);
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
  for (const auto &entry : scope) {
    diagnostic.army_id.store(entry.army_id);
    diagnostic.reader.store("scope_row");
    auto row = Strength(bindings, entry);
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

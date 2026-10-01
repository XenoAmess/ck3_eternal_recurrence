#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002.hpp"

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

bool Storage(void **slot, void *&objects, std::int32_t &capacity) noexcept {
  objects = nullptr;
  capacity = 0;
  if (slot == nullptr || *slot == nullptr) return false;
  objects = Load<void *>(*slot, 0x20);
  capacity = Load<std::int32_t>(*slot, 0x2C);
  return capacity >= 0 && capacity <= kMaximumCapacity &&
         (capacity == 0 || objects != nullptr);
}

void *Resolve(void **slot, std::int32_t id) noexcept {
  if (id == -1) return nullptr;
  void *objects = nullptr;
  std::int32_t capacity = 0;
  if (!Storage(slot, objects, capacity)) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *object = Load<void *>(objects, index * 0x10ULL + 0x08);
  return object != nullptr && Load<std::int32_t>(object, 0x10) == id
             ? object : nullptr;
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
  void *data = Load<void *>(unit, 0x38);
  const auto capacity = Load<std::int32_t>(unit, 0x40);
  const auto count = Load<std::int32_t>(unit, 0x44);
  if (capacity < 0 || count < 0 || count > capacity || count > kMaximumRoute ||
      (count > 0 && data == nullptr)) return;
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
  if (!row.route_province_ids.empty()) {
    row.move_target_observable = true;
    row.move_target_province_id = row.route_province_ids.back();
  }
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
  void *army = Resolve(bindings.internal_army_storage_slot, internal_id);
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
  }
  const auto native_current = bindings.get_army_current_soldiers(
      static_cast<std::byte *>(army) + 0x38, 0);
  const auto native_maximum = bindings.get_army_maximum_soldiers(army);
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
  output.clear();
  if (!bindings.enabled || bindings.unit_storage_slot == nullptr ||
      bindings.internal_army_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.get_army_current_soldiers == nullptr ||
      bindings.get_army_maximum_soldiers == nullptr)
    return game::ReadArmyStrengthsResult::unavailable;
  bool partial = false;
  for (const auto &entry : scope) {
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

} // namespace xar::ck3_12002

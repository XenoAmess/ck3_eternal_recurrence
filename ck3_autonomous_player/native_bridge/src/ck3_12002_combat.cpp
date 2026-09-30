#include "xar_bridge/ck3_12002_combat.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
namespace xar::ck3_12002 {
using namespace game;
namespace {
constexpr std::size_t kArmyCurrentProvinceOffset = 0x20;
constexpr std::size_t kArmyIdOffset = 0x10;
constexpr std::size_t kArmyOwnerCharacterIdOffset = 0x174;
constexpr std::size_t kCharacterEffectiveProwessOffset = 0xEC;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kCharacterKnightLinkOffset = 0x1B8;
constexpr std::size_t kCharacterKnightLinkRegimentIdOffset = 0xF8;
constexpr std::size_t kCombatBaseAdvantageOffset = 0x6C8;
constexpr std::size_t kCombatBaseWidthOffset = 0x6C0;
constexpr std::size_t kCombatFinalWidthOffset = 0x6C4;
constexpr std::size_t kCombatIdOffset = 0x08;
constexpr std::size_t kCombatPhaseDayOffset = 0x6B4;
constexpr std::size_t kCombatPhaseOffset = 0x6B0;
constexpr std::size_t kCombatProvinceOffset = 0x6B8;
constexpr std::size_t kCombatResolvedAdvantageOffset = 0x710;
constexpr std::size_t kCombatRulesCounterClassCountOffset = 0xEFC;
constexpr std::size_t kCombatSide0RollOffset = 0x6D0;
constexpr std::size_t kCombatSide1RollOffset = 0x6D4;
constexpr std::int32_t kCommanderMaxRollModifierIndex = 0x116;
constexpr std::int32_t kCommanderMinRollModifierIndex = 0x115;
constexpr std::size_t kComponentStorageCapacityOffset = 0x2C;
constexpr std::size_t kComponentStorageSlotObjectOffset = 0x08;
constexpr std::size_t kComponentStorageSlotSize = 0x10;
constexpr std::size_t kComponentStorageSlotsOffset = 0x20;
constexpr std::int32_t kCounterEfficiencyModifierIndex = 0x113;
constexpr std::int32_t kCounterResistanceModifierIndex = 0x114;
constexpr std::size_t kDatabaseObjectKeyOffset = 0x18;
constexpr std::size_t kEncounterMaaStatsDamageOffset = 0x18;
constexpr std::size_t kEncounterMaaStatsMaximumOffset = 0x08;
constexpr std::size_t kEncounterMaaStatsPursuitOffset = 0x28;
constexpr std::size_t kEncounterMaaStatsScreenOffset = 0x30;
constexpr std::size_t kEncounterMaaStatsSiegeOffset = 0x10;
constexpr std::size_t kEncounterMaaStatsToughnessOffset = 0x20;
constexpr std::int64_t kFixedPointScale = 100'000;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kInternalArmyCombatIdOffset = 0x128;
constexpr std::size_t kInternalArmyCommanderCharacterIdOffset = 0x120;
constexpr std::size_t kInternalArmyIdOffset = 0x10;
constexpr std::size_t kInternalArmyRegimentCapacityOffset = 0x40;
constexpr std::size_t kInternalArmyRegimentCountOffset = 0x44;
constexpr std::size_t kInternalArmyRegimentIdsOffset = 0x38;
constexpr std::size_t kInternalArmyUnitIdOffset = 0x124;
constexpr std::size_t kMapAdjacencyKindOffset = 0x00;
constexpr std::size_t kMapAdjacencyStride = 0x30;
constexpr std::size_t kMapAdjacencyTargetProvinceIdOffset = 0x04;
constexpr std::size_t kMapNodeAdjacencyCountOffset = 0x5C;
constexpr std::size_t kMapNodeAdjacencyDataOffset = 0x50;
constexpr std::int32_t kMaximumArmyRegiments = 65'536;
constexpr std::int32_t kMaximumComponentCapacity = 1'000'000;
constexpr std::int32_t kMaximumCounterClasses = 4'096;
constexpr std::int32_t kMaximumCounterTargets = 4'096;
constexpr std::size_t kMaximumDatabaseObjectKeyBytes = 4'096;
constexpr std::int32_t kMaximumProvinceAdjacencies = 4'096;
constexpr std::size_t kMsvcStringInlineCapacity = 15;
constexpr std::size_t kProvinceIdOffset = 0x10;
constexpr std::size_t kProvinceMapNodeOffset = 0x08;
constexpr std::size_t kRegimentArmyIdOffset = 0x140;
constexpr std::size_t kRegimentCounterClassOffset = 0x260;
constexpr std::size_t kRegimentCounterTargetClassOffset = 0x00;
constexpr std::size_t kRegimentCounterTargetEffectivenessOffset = 0x08;
constexpr std::size_t kRegimentCounterTargetStride = 0x10;
constexpr std::size_t kRegimentCounterTargetsCountOffset = 0x2B4;
constexpr std::size_t kRegimentCounterTargetsDataOffset = 0x2A8;
constexpr std::size_t kRegimentCurrentSoldiersOffset = 0x38;
constexpr std::size_t kRegimentIdOffset = 0x10;
constexpr std::size_t kRegimentInnerTypeOffset = 0x18;
constexpr std::size_t kRegimentKnightCharacterIdOffset = 0x148;
constexpr std::size_t kRegimentMaaTypeOffset = 0x18;
constexpr std::size_t kRegimentMainPhaseEligibilityOffset = 0x98A;
constexpr std::size_t kRegimentMaximumSoldiersOffset = 0x3C;
constexpr std::size_t kTerrainCombatWidthMultiplierOffset = 0x58;
constexpr std::size_t kTerrainCommanderMaxRollModifierIndexOffset = 0x778;
constexpr std::size_t kTerrainCommanderMinRollModifierIndexOffset = 0x776;
constexpr std::size_t kUnitArmyIdOffset = 0x178;
template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
 T result{}; std::memcpy(&result, static_cast<const std::byte *>(object)+offset,sizeof(T));return result;
}
template <typename T> void StoreAt(void *object,std::size_t offset,T value) noexcept {
 std::memcpy(static_cast<std::byte *>(object)+offset,&value,sizeof(T));
}
bool ReadDatabaseObjectKey(const void *database_object,
                           std::size_t key_offset,
                           std::string &output) noexcept {
  if (database_object == nullptr) {
    return false;
  }
  const auto *const string_storage =
      static_cast<const std::byte *>(database_object) + key_offset;
  const auto size = LoadAt<std::size_t>(string_storage, 0x10);
  const auto capacity = LoadAt<std::size_t>(string_storage, 0x18);
  if (size > capacity || size > kMaximumDatabaseObjectKeyBytes) {
    return false;
  }
  const char *data = nullptr;
  if (capacity <= kMsvcStringInlineCapacity) {
    data = reinterpret_cast<const char *>(string_storage);
  } else {
    data = LoadAt<const char *>(string_storage, 0x00);
  }
  if (size > 0 && data == nullptr) {
    return false;
  }
  output.assign(data == nullptr ? "" : data, size);
  return true;
}
void *ResolveProvince(void *game_state, std::int32_t province_id) noexcept {
  if (game_state == nullptr || province_id < 1) {
    return nullptr;
  }
  void *const game_data =
      LoadAt<void *>(game_state, kGameStateGameDataOffset);
  if (game_data == nullptr) {
    return nullptr;
  }
  void *const provinces =
      LoadAt<void *>(game_data, kGameDataProvinceArrayOffset);
  const std::int32_t province_count =
      LoadAt<std::int32_t>(game_data, kGameDataProvinceCountOffset);
  if (provinces == nullptr || province_count <= 1 ||
      province_id >= province_count) {
    return nullptr;
  }
  void *const province = LoadAt<void *>(
      provinces, static_cast<std::size_t>(province_id) * sizeof(void *));
  if (province == nullptr ||
      LoadAt<std::int32_t>(province, kProvinceIdOffset) != province_id) {
    return nullptr;
  }
  return province;
}
struct ArmyStrengthScopeEntry {
  std::int32_t army_id = -1;
  ArmyStrengthScopeRole role = ArmyStrengthScopeRole::active_war_enemy;
  std::vector<std::int32_t> war_ids;
};

int ArmyStrengthRolePriority(ArmyStrengthScopeRole role) noexcept {
  switch (role) {
  case ArmyStrengthScopeRole::player:
    return 3;
  case ArmyStrengthScopeRole::active_war_ally:
    return 2;
  case ArmyStrengthScopeRole::active_war_enemy:
    return 1;
  }
  return 0;
}

void AppendArmyStrengthScope(
    std::vector<ArmyStrengthScopeEntry> &scope, std::int32_t army_id,
    ArmyStrengthScopeRole role, std::int32_t war_id) {
  auto existing = std::find_if(
      scope.begin(), scope.end(), [army_id](const auto &candidate) {
        return candidate.army_id == army_id;
      });
  if (existing == scope.end()) {
    scope.push_back({army_id, role, {}});
    existing = scope.end() - 1;
  } else if (ArmyStrengthRolePriority(role) >
             ArmyStrengthRolePriority(existing->role)) {
    // Upgrade the semantic role without moving the row. This preserves the
    // first-seen order while keeping player > ally > enemy classification.
    existing->role = role;
  }
  if (war_id != -1 &&
      std::find(existing->war_ids.begin(), existing->war_ids.end(), war_id) ==
          existing->war_ids.end()) {
    existing->war_ids.push_back(war_id);
  }
}

std::vector<ArmyStrengthScopeEntry>
BuildArmyStrengthScope(const Snapshot &snapshot) {
  std::vector<ArmyStrengthScopeEntry> result;
  for (const auto &army : snapshot.player_armies) {
    AppendArmyStrengthScope(result, army.army_id,
                            ArmyStrengthScopeRole::player, -1);
  }
  for (const auto &war : snapshot.active_wars) {
    for (const auto &army : war.allied_armies) {
      AppendArmyStrengthScope(result, army.army_id,
                              ArmyStrengthScopeRole::active_war_ally,
                              war.war_id);
    }
    for (const auto &army : war.enemy_armies) {
      AppendArmyStrengthScope(result, army.army_id,
                              ArmyStrengthScopeRole::active_war_enemy,
                              war.war_id);
    }
  }
  return result;
}

void *ResolveStoredComponent(void **storage_slot, std::int32_t component_id,
                             std::size_t component_id_offset) noexcept {
  if (storage_slot == nullptr || component_id == -1) {
    return nullptr;
  }
  void *const storage = *storage_slot;
  if (storage == nullptr) {
    return nullptr;
  }
  void *const slots = LoadAt<void *>(storage, kComponentStorageSlotsOffset);
  const auto capacity =
      LoadAt<std::int32_t>(storage, kComponentStorageCapacityOffset);
  const auto index =
      static_cast<std::uint32_t>(component_id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 ||
      capacity > kMaximumComponentCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  const auto slot_offset = static_cast<std::size_t>(index) *
                               kComponentStorageSlotSize +
                           kComponentStorageSlotObjectOffset;
  void *const component = LoadAt<void *>(slots, slot_offset);
  if (component == nullptr ||
      LoadAt<std::int32_t>(component, component_id_offset) != component_id) {
    return nullptr;
  }
  return component;
}

bool CheckedAddNonnegative(std::int64_t &sum,
                           std::int32_t value) noexcept {
  if (value < 0 ||
      sum > static_cast<std::int64_t>(
                std::numeric_limits<std::int32_t>::max()) -
                value) {
    return false;
  }
  sum += value;
  return true;
}

bool CheckedAddSigned(std::int64_t &sum, std::int64_t value) noexcept {
  if ((value > 0 &&
       sum > std::numeric_limits<std::int64_t>::max() - value) ||
      (value < 0 &&
       sum < std::numeric_limits<std::int64_t>::min() - value)) {
    return false;
  }
  sum += value;
  return true;
}

bool CheckedMultiplySigned(std::int64_t left, std::int64_t right,
                           std::int64_t &output) noexcept {
  if (left == 0 || right == 0) {
    output = 0;
    return true;
  }
  if ((left == -1 && right == std::numeric_limits<std::int64_t>::min()) ||
      (right == -1 && left == std::numeric_limits<std::int64_t>::min())) {
    return false;
  }
  if (left > 0) {
    if ((right > 0 &&
         left > std::numeric_limits<std::int64_t>::max() / right) ||
        (right < 0 &&
         right < std::numeric_limits<std::int64_t>::min() / left)) {
      return false;
    }
  } else if ((right > 0 &&
              left < std::numeric_limits<std::int64_t>::min() / right) ||
             (right < 0 &&
              left < std::numeric_limits<std::int64_t>::max() / right)) {
    return false;
  }
  output = left * right;
  return true;
}

bool ReadCharacterIdentity(void *object, bool &value) noexcept {
  if (object == nullptr) {
    return false;
  }
  // The former virtual validity slot is absent in this build. This is the
  // same inline Character tag/full-ID predicate used by the native resolver.
  value = LoadAt<std::uint32_t>(object, 0x1C) == 0x43686172U &&
          LoadAt<std::int32_t>(object, kCharacterIdOffset) != -1;
  return true;
}

bool ReadRegimentIdentity(void *regiment, bool &identity_valid) noexcept {
  if (regiment == nullptr) return false;
  identity_valid = LoadAt<std::uint32_t>(regiment, 0x14) == 0x41725267U &&
                   LoadAt<std::int32_t>(regiment, kRegimentIdOffset) != -1;
  return true;
}


bool ReadDatabaseObjectValidity(void *object, bool &valid) noexcept {
  if (object == nullptr) {
    valid = false;
    return true;
  }
  // CMenAtArmsType slot zero is a database initialization validator in
  // 1.20.0.2. Native stats and serialization recognize the GDbo identity tag.
  valid = LoadAt<std::uint32_t>(object, 0x38) == 0x4744624FU;
  return true;
}

bool ReadCombatMaaType(void *regiment,
                       game::CombatMaaTypeSnapshot &output) noexcept {
  output = {};
  void *const maa_type = LoadAt<void *>(regiment, kRegimentMaaTypeOffset);
  if (maa_type == nullptr) {
    output.status = CombatObservationStatus::absent;
    return true;
  }
  bool valid = false;
  if (!ReadDatabaseObjectValidity(maa_type, valid)) {
    output.unavailable_reason = "maa_type_validity_unavailable";
    return false;
  }
  if (!valid) {
    output.status = CombatObservationStatus::absent;
    return true;
  }
  if (!ReadDatabaseObjectKey(maa_type, kDatabaseObjectKeyOffset,
                             output.key) ||
      output.key.empty()) {
    output.key.clear();
    output.unavailable_reason = "maa_type_key_unavailable";
    return false;
  }
  output.status = CombatObservationStatus::available;
  return true;
}

bool ReadCombatRegimentKind(
    const CombatBindings &bindings, void *regiment, std::int32_t regiment_id,
    game::CombatRegimentKindSnapshot &output) noexcept {
  output = {};
  output.unavailable_reason = "combat_type_unavailable";
  void *const combat_type =
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset);
  if (combat_type == nullptr) {
    return false;
  }
  bool type_valid = false;
  if (!ReadDatabaseObjectValidity(combat_type, type_valid)) {
    output.unavailable_reason = "combat_type_validity_unavailable";
    return false;
  }
  const bool special = bindings.is_special_combat_regiment(regiment);
  if (ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset) != combat_type) {
    output.unavailable_reason = "regiment_generation_changed";
    return false;
  }
  output.status = CombatObservationStatus::available;
  output.value = !type_valid && !special ? "levy" : "men_at_arms";
  output.fights_in_main_phase =
      LoadAt<std::uint8_t>(combat_type,
                           kRegimentMainPhaseEligibilityOffset) != 0;
  if (ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset) != combat_type) {
    output = {};
    output.unavailable_reason = "regiment_generation_changed";
    return false;
  }
  output.unavailable_reason.clear();
  return true;
}

CombatCommanderSnapshot ReadCombatCommander(
    const CombatBindings &bindings, void *internal_army) noexcept {
  CombatCommanderSnapshot output{};
  const auto commander_id = LoadAt<std::int32_t>(
      internal_army, kInternalArmyCommanderCharacterIdOffset);
  if (commander_id == -1) {
    output.status = CombatObservationStatus::absent;
    return output;
  }
  if (commander_id < 0) {
    output.unavailable_reason = "commander_id_invalid";
    return output;
  }
  void *const commander = ResolveStoredComponent(
      bindings.character_storage_slot, commander_id, kCharacterIdOffset);
  if (commander == nullptr) {
    output.unavailable_reason = "commander_not_found";
    return output;
  }
  bool commander_valid = false;
  if (!ReadCharacterIdentity(commander, commander_valid) ||
      !commander_valid) {
    output.unavailable_reason = "commander_not_valid";
    return output;
  }
  if (bindings.get_army_commander(internal_army) != commander) {
    output.unavailable_reason = "native_commander_helper_mismatch";
    return output;
  }
  output.character_id = commander_id;
  output.generic_advantage_points =
      bindings.get_commander_advantage(commander, -1, false);
  output.generic_advantage_observable = true;
  output.status = CombatObservationStatus::available;
  return output;
}

bool ResolveCombatModifierOwner(const CombatBindings &bindings,
                                void *expected_unit,
                                void *internal_army,
                                void *&owner) noexcept {
  owner = nullptr;
  const auto unit_id =
      LoadAt<std::int32_t>(internal_army, kInternalArmyUnitIdOffset);
  void *const linked_unit = ResolveStoredComponent(
      bindings.army_storage_slot, unit_id, kArmyIdOffset);
  if (linked_unit == nullptr || linked_unit != expected_unit) {
    return false;
  }
  const auto owner_id =
      LoadAt<std::int32_t>(linked_unit, kArmyOwnerCharacterIdOffset);
  owner = ResolveStoredComponent(bindings.character_storage_slot, owner_id,
                                 kCharacterIdOffset);
  return owner != nullptr;
}

bool ReadEncounterEffectiveStats(
    const CombatBindings &bindings, void *regiment, void *target_province,
    std::int32_t regiment_id, std::int32_t target_province_id,
    game::CombatEffectiveStatsSnapshot &output) noexcept {
  output = {};
  if (target_province == nullptr ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(target_province, kProvinceIdOffset) !=
          target_province_id) {
    output.unavailable_reason = "encounter_province_unavailable";
    return false;
  }

  alignas(8) std::array<std::byte, 0x38> native_stats{};
  if (bindings.evaluate_regiment_stats_at_province(
          regiment, native_stats.data(), target_province) !=
          native_stats.data() ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(regiment, kRegimentIdOffset) != regiment_id ||
      LoadAt<std::int32_t>(target_province, kProvinceIdOffset) !=
          target_province_id) {
    output.unavailable_reason = "effective_stats_helper_failed";
    return false;
  }
  output.source_target_province_id = target_province_id;
  output.max_size = LoadAt<std::int32_t>(
      native_stats.data(), kEncounterMaaStatsMaximumOffset);
  output.siege_value_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsSiegeOffset);
  output.damage_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsDamageOffset);
  output.toughness_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsToughnessOffset);
  output.pursuit_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsPursuitOffset);
  output.screen_raw = LoadAt<std::int64_t>(
      native_stats.data(), kEncounterMaaStatsScreenOffset);
  if (output.max_size < 0) {
    output = {};
    output.unavailable_reason = "effective_stats_invalid";
    return false;
  }
  output.available = true;
  output.unavailable_reason.clear();
  return true;
}

struct NativeArrayHeader {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};
static_assert(sizeof(NativeArrayHeader) == 0x10);

bool ReadCharacterModifierRaw(const CombatBindings &bindings, void *aggregator,
                              std::int32_t modifier_index,
                              std::int64_t &output) noexcept;

bool ReadCounterClassCount(const CombatBindings &bindings,
                           std::int32_t &class_count) noexcept {
  class_count = 0;
  void *const rules = bindings.get_combat_rules();
  if (rules == nullptr) {
    return false;
  }
  class_count = LoadAt<std::int32_t>(
      rules, kCombatRulesCounterClassCountOffset);
  return class_count > 0 && class_count <= kMaximumCounterClasses;
}

bool ReadCombatOwner(const CombatBindings &bindings, void *owner_character,
                     std::int32_t owner_character_id,
                     game::CombatOwnerSnapshot &output) noexcept {
  output = {};
  output.character_id = owner_character_id;
  if (owner_character == nullptr || owner_character_id < 0) {
    output.unavailable_reason = "counter_modifier_owner_unavailable";
    return false;
  }
  void *const aggregator =
      bindings.get_character_modifier_aggregator(owner_character);
  if (aggregator == nullptr ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCounterEfficiencyModifierIndex,
                                output.counter_efficiency_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCounterResistanceModifierIndex,
                                output.counter_resistance_raw)) {
    output.unavailable_reason = "counter_modifiers_unavailable";
    return false;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             owner_character_id,
                             kCharacterIdOffset) != owner_character) {
    output = {};
    output.unavailable_reason = "counter_modifier_owner_generation_changed";
    return false;
  }
  output.status = CombatObservationStatus::available;
  output.unavailable_reason.clear();
  return true;
}

bool ReadCombatCounter(const CombatBindings &bindings, void *regiment,
                       std::int32_t regiment_id,
                       std::int32_t current_soldiers,
                       std::int32_t class_count,
                       game::CombatCounterSnapshot &output) noexcept {
  output = {};
  void *const inner_type =
      LoadAt<void *>(regiment, kRegimentInnerTypeOffset);
  if (inner_type == nullptr) {
    output.unavailable_reason = "regiment_inner_type_unavailable";
    return false;
  }
  const auto class_index = LoadAt<std::int32_t>(
      inner_type, kRegimentCounterClassOffset);
  if (class_index < 0) {
    output.status = CombatObservationStatus::absent;
    output.unavailable_reason.clear();
    return true;
  }
  if (class_index >= class_count) {
    output.unavailable_reason = "counter_class_out_of_range";
    return false;
  }

  void *const targets = LoadAt<void *>(
      inner_type, kRegimentCounterTargetsDataOffset);
  const auto target_count = LoadAt<std::int32_t>(
      inner_type, kRegimentCounterTargetsCountOffset);
  if (target_count < 0 || target_count > kMaximumCounterTargets ||
      (target_count > 0 && targets == nullptr)) {
    output.unavailable_reason = "counter_targets_invalid";
    return false;
  }
  output.targets.reserve(static_cast<std::size_t>(target_count));
  for (std::int32_t index = 0; index < target_count; ++index) {
    const auto *const target =
        static_cast<const std::byte *>(targets) +
        static_cast<std::size_t>(index) * kRegimentCounterTargetStride;
    game::CombatCounterTargetSnapshot row{};
    row.class_index = LoadAt<std::int32_t>(
        target, kRegimentCounterTargetClassOffset);
    row.effectiveness_raw = LoadAt<std::int64_t>(
        target, kRegimentCounterTargetEffectivenessOffset);
    if (row.class_index < 0 || row.class_index >= class_count) {
      output.targets.clear();
      output.unavailable_reason = "counter_target_class_out_of_range";
      return false;
    }
    output.targets.push_back(row);
  }

  alignas(8) std::array<std::byte, 0x60> synthetic_entry{};
  StoreAt(synthetic_entry.data(), 0x08, regiment_id);
  StoreAt(synthetic_entry.data(), 0x18,
          static_cast<std::int64_t>(current_soldiers) * kFixedPointScale);
  std::int64_t current_chunk_raw = -1;
  if (bindings.read_counter_current_chunk(
          synthetic_entry.data(), &current_chunk_raw) !=
          &current_chunk_raw ||
      current_chunk_raw < 0 ||
      ResolveStoredComponent(bindings.regiment_storage_slot, regiment_id,
                             kRegimentIdOffset) != regiment ||
      LoadAt<std::int32_t>(regiment, kRegimentIdOffset) != regiment_id) {
    output.targets.clear();
    output.unavailable_reason = "counter_current_chunk_unavailable";
    return false;
  }
  output.class_index = class_index;
  output.current_chunk_raw = current_chunk_raw;
  output.status = CombatObservationStatus::available;
  output.unavailable_reason.clear();
  return true;
}

bool ReadCombatRegiments(const CombatBindings &bindings, void *internal_army,
                         void *target_province,
                         std::int32_t target_province_id,
                         std::int32_t counter_class_count,
                         std::vector<CombatRegimentSnapshot> &output,
                         bool &has_unavailable_subdomain,
                         std::string &unavailable_reason) noexcept {
  output.clear();
  void *const regiment_ids = LoadAt<void *>(
      internal_army, kInternalArmyRegimentIdsOffset);
  const auto regiment_capacity = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCapacityOffset);
  const auto regiment_count = LoadAt<std::int32_t>(
      internal_army, kInternalArmyRegimentCountOffset);
  if (regiment_capacity < 0 ||
      regiment_capacity > kMaximumArmyRegiments || regiment_count < 0 ||
      regiment_count > regiment_capacity ||
      (regiment_count > 0 && regiment_ids == nullptr)) {
    unavailable_reason = "regiment_array_invalid";
    return false;
  }

  std::vector<CombatRegimentSnapshot> rows;
  rows.reserve(static_cast<std::size_t>(regiment_count));
  for (std::int32_t index = 0; index < regiment_count; ++index) {
    CombatRegimentSnapshot row{};
    row.regiment_id = LoadAt<std::int32_t>(
        regiment_ids, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, row.regiment_id, kRegimentIdOffset);
    if (regiment == nullptr) {
      unavailable_reason = "regiment_not_found";
      return false;
    }
    if (!ReadRegimentIdentity(regiment, row.identity_valid)) {
      unavailable_reason = "identity_predicate_unavailable";
      return false;
    }
    if (!row.identity_valid) {
      unavailable_reason = "regiment_identity_invalid";
      return false;
    }
    row.current_soldiers = LoadAt<std::int32_t>(
        regiment, kRegimentCurrentSoldiersOffset);
    row.maximum_soldiers = LoadAt<std::int32_t>(
        regiment, kRegimentMaximumSoldiersOffset);
    if (row.current_soldiers < 0 || row.maximum_soldiers < 0) {
      unavailable_reason = "soldier_value_invalid";
      return false;
    }
    if (!ReadCombatMaaType(regiment, row.maa_type)) {
      row.unavailable_reason = row.maa_type.unavailable_reason;
      has_unavailable_subdomain = true;
    } else {
      row.available = true;
    }
    if (!ReadCombatRegimentKind(bindings, regiment, row.regiment_id,
                                row.kind)) {
      has_unavailable_subdomain = true;
      row.available = false;
      row.unavailable_reason = row.kind.unavailable_reason;
    }
    if (!ReadEncounterEffectiveStats(bindings, regiment, target_province,
                                     row.regiment_id, target_province_id,
                                     row.effective_stats)) {
      has_unavailable_subdomain = true;
      row.available = false;
      row.unavailable_reason = row.effective_stats.unavailable_reason;
    }
    if (!ReadCombatCounter(bindings, regiment, row.regiment_id,
                           row.current_soldiers, counter_class_count,
                           row.counter)) {
      has_unavailable_subdomain = true;
    }
    rows.push_back(std::move(row));
  }
  output = std::move(rows);
  return true;
}

bool ReadCombatKnights(
    const CombatBindings &bindings, std::int32_t internal_army_id,
    const std::vector<CombatRegimentSnapshot> &regiments,
    std::vector<std::int32_t> &seen_knight_character_ids,
    std::vector<std::int32_t> &seen_knight_regiment_ids,
    game::CombatKnightsSnapshot &output) noexcept {
  output = {};
  for (const auto &regiment_row : regiments) {
    void *const regiment = ResolveStoredComponent(
        bindings.regiment_storage_slot, regiment_row.regiment_id,
        kRegimentIdOffset);
    if (regiment == nullptr) {
      output.unavailable_reason = "knight_source_regiment_unavailable";
      return false;
    }
    const auto knight_character_id = LoadAt<std::int32_t>(
        regiment, kRegimentKnightCharacterIdOffset);
    if (knight_character_id == -1) {
      continue;
    }
    if (!regiment_row.effective_stats.available) {
      output.unavailable_reason = "knight_effective_stats_unavailable";
      return false;
    }
    if (knight_character_id < 0 ||
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset) !=
            internal_army_id ||
        std::find(seen_knight_character_ids.begin(),
                  seen_knight_character_ids.end(),
                  knight_character_id) !=
            seen_knight_character_ids.end() ||
        std::find(seen_knight_regiment_ids.begin(),
                  seen_knight_regiment_ids.end(),
                  regiment_row.regiment_id) !=
            seen_knight_regiment_ids.end()) {
      output.unavailable_reason = "knight_identity_or_membership_invalid";
      return false;
    }
    void *const character = ResolveStoredComponent(
        bindings.character_storage_slot, knight_character_id,
        kCharacterIdOffset);
    bool character_valid = false;
    if (character == nullptr ||
        !ReadCharacterIdentity(character, character_valid) ||
        !character_valid) {
      output.unavailable_reason = "knight_character_unavailable";
      return false;
    }
    void *const knight_link =
        LoadAt<void *>(character, kCharacterKnightLinkOffset);
    if (knight_link == nullptr ||
        LoadAt<std::int32_t>(
            knight_link, kCharacterKnightLinkRegimentIdOffset) !=
            regiment_row.regiment_id) {
      output.unavailable_reason = "knight_character_regiment_backlink_invalid";
      return false;
    }

    game::CombatKnightSnapshot knight{};
    knight.character_id = knight_character_id;
    knight.source_regiment_id = regiment_row.regiment_id;
    knight.army_id = internal_army_id;
    knight.prowess = LoadAt<std::int32_t>(
        character, kCharacterEffectiveProwessOffset);
    const auto effective_prowess =
        std::max<std::int64_t>(1, knight.prowess);
    void *const effectiveness_context =
        bindings.get_knight_effectiveness_context(character);
    if (effectiveness_context == nullptr ||
        bindings.read_knight_effectiveness(
            &knight.knight_effectiveness_raw, effectiveness_context, 0) !=
            &knight.knight_effectiveness_raw ||
        knight.knight_effectiveness_raw < 0) {
      output.unavailable_reason = "knight_effectiveness_unavailable";
      return false;
    }
    if (ResolveStoredComponent(bindings.regiment_storage_slot,
                               regiment_row.regiment_id,
                               kRegimentIdOffset) != regiment ||
        ResolveStoredComponent(bindings.character_storage_slot,
                               knight_character_id,
                               kCharacterIdOffset) != character ||
        LoadAt<std::int32_t>(regiment,
                             kRegimentKnightCharacterIdOffset) !=
            knight_character_id ||
        LoadAt<std::int32_t>(regiment, kRegimentArmyIdOffset) !=
            internal_army_id ||
        LoadAt<void *>(character, kCharacterKnightLinkOffset) != knight_link ||
        LoadAt<std::int32_t>(
            knight_link, kCharacterKnightLinkRegimentIdOffset) !=
            regiment_row.regiment_id) {
      output.unavailable_reason = "knight_generation_changed";
      return false;
    }
    const auto damage_raw = regiment_row.effective_stats.damage_raw;
    const auto toughness_raw = regiment_row.effective_stats.toughness_raw;
    std::int64_t per_prowess_raw = 0;
    std::int64_t expected_damage_raw = 0;
    std::int64_t expected_toughness_raw = 0;
    if (!CheckedMultiplySigned(knight.knight_effectiveness_raw,
                               effective_prowess, per_prowess_raw) ||
        !CheckedMultiplySigned(per_prowess_raw,
                               *bindings.knight_damage_per_prowess,
                               expected_damage_raw) ||
        !CheckedMultiplySigned(per_prowess_raw,
                               *bindings.knight_toughness_per_prowess,
                               expected_toughness_raw)) {
      output.unavailable_reason = "knight_effectiveness_overflow";
      return false;
    }
    if (damage_raw != expected_damage_raw ||
        toughness_raw != expected_toughness_raw) {
      output.unavailable_reason = "knight_effectiveness_crosscheck_failed";
      return false;
    }
    knight.effective_damage_raw = damage_raw;
    knight.effective_toughness_raw = toughness_raw;
    knight.eligible = true;
    knight.participant_army_membership_verified = true;
    seen_knight_character_ids.push_back(knight_character_id);
    seen_knight_regiment_ids.push_back(regiment_row.regiment_id);
    output.members.push_back(knight);
  }
  std::sort(output.members.begin(), output.members.end(),
            [](const auto &left, const auto &right) {
              if (left.army_id != right.army_id) {
                return left.army_id < right.army_id;
              }
              if (left.source_regiment_id != right.source_regiment_id) {
                return left.source_regiment_id < right.source_regiment_id;
              }
              return left.character_id < right.character_id;
            });
  output.available = true;
  output.unavailable_reason.clear();
  return true;
}

game::CombatPrecontactWidthSnapshot ReadPrecontactCombatWidth(
    const CombatBindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    const game::CombatTerrainSnapshot &terrain) noexcept {
  game::CombatPrecontactWidthSnapshot output{};
  if (!terrain.available) {
    output.unavailable_reason = "target_terrain_unavailable";
    return output;
  }
  std::int64_t friendly_total_raw = 0;
  std::int64_t enemy_total_raw = 0;
  for (const auto &army : armies) {
    if (!army.available || !army.regiments_observable) {
      output.unavailable_reason = "contact_participants_unavailable";
      return output;
    }
    auto &side_total =
        army.scope_role == ArmyStrengthScopeRole::active_war_enemy
            ? enemy_total_raw
            : friendly_total_raw;
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        output.unavailable_reason = "contact_regiment_identity_invalid";
        return output;
      }
      std::int64_t regiment_current_raw = 0;
      if (!CheckedMultiplySigned(regiment.current_soldiers,
                                 kFixedPointScale,
                                 regiment_current_raw) ||
          !CheckedAddSigned(side_total, regiment_current_raw)) {
        output.unavailable_reason = "contact_participant_total_overflow";
        return output;
      }
    }
  }
  std::int64_t combined_total_raw = friendly_total_raw;
  if (!CheckedAddSigned(combined_total_raw, enemy_total_raw)) {
    output.unavailable_reason = "contact_participant_total_overflow";
    return output;
  }
  const auto average_total_raw = combined_total_raw / 2;
  std::int64_t ratio_product = 0;
  if (!CheckedMultiplySigned(average_total_raw,
                             *bindings.base_combat_width_ratio,
                             ratio_product)) {
    output.unavailable_reason = "base_combat_width_overflow";
    return output;
  }
  const auto candidate_raw = ratio_product / kFixedPointScale;
  const auto candidate_width = candidate_raw / kFixedPointScale;
  const auto base_width = std::max<std::int64_t>(1, candidate_width);
  std::int64_t final_product = 0;
  if (!CheckedMultiplySigned(
          base_width, terrain.combat_width_multiplier_raw,
          final_product)) {
    output.unavailable_reason = "final_combat_width_overflow";
    return output;
  }
  const auto terrain_width = final_product / kFixedPointScale;
  const auto final_width = std::max<std::int64_t>(
      *bindings.minimum_combat_width, terrain_width);
  if (base_width > std::numeric_limits<std::int32_t>::max() ||
      final_width < std::numeric_limits<std::int32_t>::min() ||
      final_width > std::numeric_limits<std::int32_t>::max()) {
    output.unavailable_reason = "combat_width_out_of_range";
    return output;
  }
  output.base = static_cast<std::int32_t>(base_width);
  output.final = static_cast<std::int32_t>(final_width);
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}

enum class ReadContactGeographyResult {
  available,
  invalid_encounter,
  unavailable,
};

enum class ReadAdjacencyKindResult {
  available,
  invalid_encounter,
  unavailable,
};

ReadAdjacencyKindResult ReadProvinceAdjacencyKind(
    void *origin_province, std::int32_t target_province_id,
    std::int32_t &kind) noexcept {
  kind = -1;
  if (origin_province == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const map_node =
      LoadAt<void *>(origin_province, kProvinceMapNodeOffset);
  if (map_node == nullptr) {
    return ReadAdjacencyKindResult::unavailable;
  }
  void *const adjacency_data =
      LoadAt<void *>(map_node, kMapNodeAdjacencyDataOffset);
  const auto adjacency_count = LoadAt<std::int32_t>(
      map_node, kMapNodeAdjacencyCountOffset);
  if (adjacency_count < 0 ||
      adjacency_count > kMaximumProvinceAdjacencies ||
      (adjacency_count > 0 && adjacency_data == nullptr)) {
    return ReadAdjacencyKindResult::unavailable;
  }
  bool found = false;
  for (std::int32_t index = 0; index < adjacency_count; ++index) {
    const auto *const edge =
        static_cast<const std::byte *>(adjacency_data) +
        static_cast<std::size_t>(index) * kMapAdjacencyStride;
    if (LoadAt<std::int32_t>(
            edge, kMapAdjacencyTargetProvinceIdOffset) !=
        target_province_id) {
      continue;
    }
    if (found) {
      return ReadAdjacencyKindResult::unavailable;
    }
    found = true;
    kind = LoadAt<std::int32_t>(edge, kMapAdjacencyKindOffset);
  }
  if (!found) {
    return ReadAdjacencyKindResult::invalid_encounter;
  }
  return ReadAdjacencyKindResult::available;
}

ReadContactGeographyResult ReadContactGeography(
    const CombatBindings &bindings, void *game_state, void *target_province,
    std::int32_t target_province_id, std::int32_t attacker_entry_province_id,
    bool attacker_enemy_side,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    game::CombatCrossingSnapshot &crossing,
    game::CombatDefenderContextSnapshot &defender_context) noexcept {
  crossing = {};
  defender_context = {};
  void *const attacker_entry_province =
      ResolveProvince(game_state, attacker_entry_province_id);
  if (attacker_entry_province == nullptr) {
    crossing.unavailable_reason = "attacker_entry_province_unavailable";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  std::int32_t edge_kind = -1;
  const auto edge_result = ReadProvinceAdjacencyKind(
      attacker_entry_province, target_province_id, edge_kind);
  if (edge_result != ReadAdjacencyKindResult::available) {
    crossing.unavailable_reason =
        edge_result == ReadAdjacencyKindResult::invalid_encounter
            ? "entry_target_edge_missing"
            : "entry_target_adjacency_unavailable";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return edge_result == ReadAdjacencyKindResult::invalid_encounter
               ? ReadContactGeographyResult::invalid_encounter
               : ReadContactGeographyResult::unavailable;
  }

  switch (edge_kind) {
  case 0:
    crossing.kind = "none";
    break;
  case 1:
    crossing.kind = "strait";
    break;
  case 2:
    crossing.kind = "river";
    break;
  case 3:
    crossing.kind = "large_river";
    break;
  case 4:
    crossing.unavailable_reason = "impassable_entry_target_edge";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::invalid_encounter;
  case 5:
  case 6:
    crossing.unavailable_reason = "non_contact_adjacency_encoding";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::invalid_encounter;
  default:
    crossing.unavailable_reason = "adjacency_kind_out_of_range";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }

  if (ResolveProvince(game_state, attacker_entry_province_id) !=
          attacker_entry_province ||
      ResolveProvince(game_state, target_province_id) != target_province) {
    crossing = {};
    defender_context = {};
    crossing.unavailable_reason = "hypothetical_contact_identity_changed";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  crossing.available = true;
  crossing.unavailable_reason.clear();
  defender_context.available = true;
  defender_context.defender_side =
      attacker_enemy_side ? "player_or_allied" : "enemy";
  defender_context.unavailable_reason.clear();

  std::int32_t defender_owner_character_id = -1;
  for (const auto &army : armies) {
    if (army.encounter_role != "defender") {
      continue;
    }
    if (army.owner.status != CombatObservationStatus::available) {
      defender_context.holding_unavailable_reason =
          "defender_owner_unavailable";
      return ReadContactGeographyResult::available;
    }
    // CCombat side population establishes the primary participant from the
    // first inserted army. A hypothetical side uses explicit request order as
    // that insertion order; current Province participant order is irrelevant.
    defender_owner_character_id = army.owner.character_id;
    break;
  }
  if (defender_owner_character_id == -1) {
    defender_context.holding_unavailable_reason = "defender_side_missing";
    return ReadContactGeographyResult::available;
  }
  void *const defender_owner = ResolveStoredComponent(
      bindings.character_storage_slot, defender_owner_character_id,
      kCharacterIdOffset);
  if (defender_owner == nullptr) {
    defender_context.holding_unavailable_reason =
        "defender_owner_generation_changed";
    return ReadContactGeographyResult::available;
  }
  const bool holding_defender =
      bindings.is_holding_defender(defender_owner, target_province);
  if (ResolveProvince(game_state, attacker_entry_province_id) !=
          attacker_entry_province ||
      ResolveProvince(game_state, target_province_id) != target_province) {
    crossing = {};
    defender_context = {};
    crossing.unavailable_reason = "hypothetical_contact_identity_changed";
    defender_context.unavailable_reason = crossing.unavailable_reason;
    return ReadContactGeographyResult::unavailable;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             defender_owner_character_id,
                             kCharacterIdOffset) != defender_owner) {
    defender_context.holding_unavailable_reason =
        "holding_context_identity_changed";
    return ReadContactGeographyResult::available;
  }
  defender_context.holding_defender_status =
      CombatObservationStatus::available;
  defender_context.holding_defender = holding_defender;
  defender_context.holding_unavailable_reason.clear();
  return ReadContactGeographyResult::available;
}

bool AppendOngoingCombat(const CombatBindings &bindings, void *game_state,
                         void *internal_army,
                         std::vector<OngoingCombatInputsSnapshot> &output,
                         bool &has_unavailable_subdomain) noexcept {
  const auto combat_id = LoadAt<std::int32_t>(
      internal_army, kInternalArmyCombatIdOffset);
  if (combat_id == -1) {
    return true;
  }
  OngoingCombatInputsSnapshot row{};
  if (combat_id < 0) {
    row.unavailable_reason = "combat_id_invalid";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  const auto existing = std::find_if(
      output.begin(), output.end(), [combat_id](const auto &candidate) {
        return candidate.combat_id_observable &&
               candidate.combat_id == combat_id;
      });
  if (existing != output.end()) {
    return true;
  }
  row.combat_id_observable = true;
  row.combat_id = combat_id;
  void *const combat = ResolveStoredComponent(
      bindings.combat_storage_slot, combat_id, kCombatIdOffset);
  if (combat == nullptr) {
    row.unavailable_reason = "combat_not_found";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  void *const province = LoadAt<void *>(combat, kCombatProvinceOffset);
  if (province == nullptr) {
    row.unavailable_reason = "combat_province_unavailable";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.province_id = LoadAt<std::int32_t>(province, kProvinceIdOffset);
  if (ResolveProvince(game_state, row.province_id) != province) {
    row.province_id = -1;
    row.unavailable_reason = "combat_province_unavailable";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.phase = LoadAt<std::int32_t>(combat, kCombatPhaseOffset);
  row.phase_day = LoadAt<std::int32_t>(combat, kCombatPhaseDayOffset);
  row.base_combat_width =
      LoadAt<std::int32_t>(combat, kCombatBaseWidthOffset);
  row.final_combat_width =
      LoadAt<std::int32_t>(combat, kCombatFinalWidthOffset);
  row.side_0_roll = LoadAt<std::int32_t>(combat, kCombatSide0RollOffset);
  row.side_1_roll = LoadAt<std::int32_t>(combat, kCombatSide1RollOffset);
  row.base_advantage =
      LoadAt<std::int64_t>(combat, kCombatBaseAdvantageOffset);
  row.resolved_advantage =
      LoadAt<std::int64_t>(combat, kCombatResolvedAdvantageOffset);
  if (row.phase < 0 || row.phase > 3 || row.phase_day < 0 ||
      row.base_combat_width < 0 || row.final_combat_width < 0) {
    row.province_id = -1;
    row.unavailable_reason = "combat_state_invalid";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  if (ResolveStoredComponent(bindings.combat_storage_slot, combat_id,
                             kCombatIdOffset) != combat) {
    row.province_id = -1;
    row.unavailable_reason = "combat_generation_changed";
    has_unavailable_subdomain = true;
    output.push_back(std::move(row));
    return true;
  }
  row.available = true;
  output.push_back(std::move(row));
  return true;
}

CombatCandidateProvinceSnapshot ReadCombatCandidateProvince(
    const CombatBindings &bindings, void *game_state,
    std::int32_t province_id) noexcept {
  CombatCandidateProvinceSnapshot output{};
  output.province_id = province_id;
  void *const province = ResolveProvince(game_state, province_id);
  if (province == nullptr) {
    output.unavailable_reason = "province_not_found";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  void *const terrain = bindings.get_province_terrain(province);
  if (terrain == nullptr ||
      !ReadDatabaseObjectKey(terrain, kDatabaseObjectKeyOffset,
                             output.terrain.key) ||
      output.terrain.key.empty()) {
    output.terrain.key.clear();
    output.unavailable_reason = "terrain_unavailable";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  output.terrain.combat_width_multiplier_raw = LoadAt<std::int64_t>(
      terrain, kTerrainCombatWidthMultiplierOffset);
  if (ResolveProvince(game_state, province_id) != province ||
      bindings.get_province_terrain(province) != terrain) {
    output.terrain = {};
    output.unavailable_reason = "terrain_generation_changed";
    output.terrain.unavailable_reason = output.unavailable_reason;
    return output;
  }
  output.terrain.available = true;
  output.available = true;
  return output;
}

bool ReadCharacterModifierRaw(const CombatBindings &bindings, void *aggregator,
                              std::int32_t modifier_index,
                              std::int64_t &output) noexcept {
  output = 0;
  return bindings.read_character_modifier(aggregator, &output,
                                          modifier_index) == &output;
}

CombatCommanderContextSnapshot ReadCommanderRollContext(
    const CombatBindings &bindings, std::int32_t province_id, void *terrain,
    const CombatCommanderSnapshot &commander) noexcept {
  CombatCommanderContextSnapshot output{};
  output.province_id = province_id;
  if (commander.status == CombatObservationStatus::absent) {
    output.available = true;
    output.unavailable_reason.clear();
    return output;
  }
  if (commander.status != CombatObservationStatus::available) {
    output.unavailable_reason = "commander_unavailable";
    return output;
  }
  void *const character = ResolveStoredComponent(
      bindings.character_storage_slot, commander.character_id,
      kCharacterIdOffset);
  if (character == nullptr || terrain == nullptr) {
    output.unavailable_reason = "commander_context_object_unavailable";
    return output;
  }
  void *const aggregator =
      bindings.get_character_modifier_aggregator(character);
  if (aggregator == nullptr) {
    output.unavailable_reason = "commander_modifier_aggregator_unavailable";
    return output;
  }

  const auto terrain_min_index = static_cast<std::int32_t>(
      LoadAt<std::uint16_t>(
          terrain, kTerrainCommanderMinRollModifierIndexOffset));
  const auto terrain_max_index = static_cast<std::int32_t>(
      LoadAt<std::uint16_t>(
          terrain, kTerrainCommanderMaxRollModifierIndexOffset));
  std::int64_t character_min_raw = 0;
  std::int64_t character_max_raw = 0;
  std::int64_t terrain_min_raw = 0;
  std::int64_t terrain_max_raw = 0;
  if (!ReadCharacterModifierRaw(bindings, aggregator,
                                kCommanderMinRollModifierIndex,
                                character_min_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator,
                                kCommanderMaxRollModifierIndex,
                                character_max_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator, terrain_min_index,
                                terrain_min_raw) ||
      !ReadCharacterModifierRaw(bindings, aggregator, terrain_max_index,
                                terrain_max_raw)) {
    output.unavailable_reason = "commander_modifier_unavailable";
    return output;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             commander.character_id,
                             kCharacterIdOffset) != character) {
    output.unavailable_reason = "commander_generation_changed";
    return output;
  }

  const auto minimum =
      static_cast<std::int64_t>(*bindings.commander_min_roll) +
      character_min_raw / kFixedPointScale +
      terrain_min_raw / kFixedPointScale;
  const auto maximum =
      static_cast<std::int64_t>(*bindings.commander_max_roll) +
      character_max_raw / kFixedPointScale +
      terrain_max_raw / kFixedPointScale;
  if (minimum < std::numeric_limits<std::int32_t>::min() ||
      minimum > std::numeric_limits<std::int32_t>::max() ||
      maximum < std::numeric_limits<std::int32_t>::min() ||
      maximum > std::numeric_limits<std::int32_t>::max()) {
    output.unavailable_reason = "commander_roll_bounds_overflow";
    return output;
  }
  output.effective_min_roll = static_cast<std::int32_t>(minimum);
  output.effective_max_roll = static_cast<std::int32_t>(maximum);
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}

CombatArmyInputsSnapshot ReadCombatArmyInputsRow(
    const CombatBindings &bindings, void *game_state, void *target_province,
    void *target_terrain, std::int32_t target_province_id,
    std::int32_t counter_class_count,
    const ArmyStrengthScopeEntry &scope_entry,
    std::vector<OngoingCombatInputsSnapshot> &ongoing_combats,
    bool &has_unavailable_subdomain) noexcept {
  CombatArmyInputsSnapshot output{};
  output.army_id = scope_entry.army_id;
  output.scope_role = scope_entry.role;
  output.war_ids = scope_entry.war_ids;

  void *const unit = ResolveStoredComponent(
      bindings.army_storage_slot, scope_entry.army_id, kArmyIdOffset);
  if (unit == nullptr) {
    output.unavailable_reason = "public_cunit_not_found";
    return output;
  }
  void *const current_province =
      LoadAt<void *>(unit, kArmyCurrentProvinceOffset);
  if (current_province != nullptr) {
    const auto current_province_id =
        LoadAt<std::int32_t>(current_province, kProvinceIdOffset);
    if (ResolveProvince(game_state, current_province_id) == current_province) {
      output.current_province_observable = true;
      output.current_province_id = current_province_id;
    }
  }

  const auto internal_army_id =
      LoadAt<std::int32_t>(unit, kUnitArmyIdOffset);
  void *const internal_army = ResolveStoredComponent(
      bindings.army_internal_storage_slot, internal_army_id,
      kInternalArmyIdOffset);
  if (internal_army == nullptr) {
    output.unavailable_reason = "native_carmy_not_found";
    return output;
  }
  output.native_carmy_id_observable = true;
  output.native_carmy_id = internal_army_id;
  void *modifier_owner = nullptr;
  if (!ResolveCombatModifierOwner(bindings, unit, internal_army,
                                  modifier_owner)) {
    output.unavailable_reason = "modifier_owner_not_found";
    return output;
  }
  const auto owner_character_id =
      LoadAt<std::int32_t>(unit, kArmyOwnerCharacterIdOffset);
  if (!ReadCombatOwner(bindings, modifier_owner, owner_character_id,
                       output.owner)) {
    has_unavailable_subdomain = true;
  }
  output.commander = ReadCombatCommander(bindings, internal_army);
  if (output.commander.status == CombatObservationStatus::unavailable) {
    has_unavailable_subdomain = true;
  }
  output.commander.battle_context = ReadCommanderRollContext(
      bindings, target_province_id, target_terrain, output.commander);
  if (!output.commander.battle_context.available) {
    has_unavailable_subdomain = true;
  }

  std::string regiment_failure;
  if (!ReadCombatRegiments(bindings, internal_army, target_province,
                           target_province_id, counter_class_count,
                           output.regiments,
                           has_unavailable_subdomain, regiment_failure)) {
    output.regiments.clear();
    output.unavailable_reason = std::move(regiment_failure);
    return output;
  }
  output.regiments_observable = true;
  if (!AppendOngoingCombat(bindings, game_state, internal_army,
                           ongoing_combats,
                           has_unavailable_subdomain)) {
    output.unavailable_reason = "combat_observation_failed";
    return output;
  }
  output.available = true;
  return output;
}

bool BuildCounterSideEntries(
    const CombatBindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies, bool enemy_side,
    std::vector<std::array<std::byte, 0x60>> &entries,
    std::int32_t &modifier_owner_character_id,
    std::string &unavailable_reason) noexcept {
  entries.clear();
  modifier_owner_character_id = -1;
  bool found_side_army = false;
  for (const auto &army : armies) {
    const bool is_enemy =
        army.scope_role == ArmyStrengthScopeRole::active_war_enemy;
    if (is_enemy != enemy_side) {
      continue;
    }
    found_side_army = true;
    if (!army.available || !army.regiments_observable ||
        army.owner.status != CombatObservationStatus::available) {
      unavailable_reason = "counter_side_army_unavailable";
      return false;
    }
    if (modifier_owner_character_id == -1) {
      modifier_owner_character_id = army.owner.character_id;
    }
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        unavailable_reason = "counter_regiment_identity_invalid";
        return false;
      }
      if (regiment.counter.status == CombatObservationStatus::unavailable) {
        unavailable_reason = "counter_operand_unavailable";
        return false;
      }
      void *const native_regiment = ResolveStoredComponent(
          bindings.regiment_storage_slot, regiment.regiment_id,
          kRegimentIdOffset);
      if (native_regiment == nullptr) {
        unavailable_reason = "counter_regiment_generation_mismatch";
        return false;
      }
      entries.emplace_back();
      auto &entry = entries.back();
      StoreAt(entry.data(), 0x08, regiment.regiment_id);
      StoreAt(entry.data(), 0x18,
              static_cast<std::int64_t>(regiment.current_soldiers) *
                  kFixedPointScale);
    }
  }
  if (!found_side_army || modifier_owner_character_id < 0) {
    unavailable_reason = "counter_side_missing";
    return false;
  }
  return true;
}

game::CombatCounterResolutionSnapshot ReadCounterResolution(
    const CombatBindings &bindings,
    const std::vector<CombatArmyInputsSnapshot> &armies,
    std::int32_t class_count, bool countered_enemy_side) noexcept {
  game::CombatCounterResolutionSnapshot output{};
  output.countered_side =
      countered_enemy_side ? "enemy" : "player_or_allied";
  output.countering_side =
      countered_enemy_side ? "player_or_allied" : "enemy";
  output.class_count = class_count;

  std::vector<std::array<std::byte, 0x60>> countered_entries;
  std::vector<std::array<std::byte, 0x60>> countering_entries;
  if (!BuildCounterSideEntries(
          bindings, armies, countered_enemy_side, countered_entries,
          output.countered_modifier_owner_character_id,
          output.unavailable_reason) ||
      !BuildCounterSideEntries(
          bindings, armies, !countered_enemy_side, countering_entries,
          output.countering_modifier_owner_character_id,
          output.unavailable_reason)) {
    return output;
  }

  void *const countered_owner = ResolveStoredComponent(
      bindings.character_storage_slot,
      output.countered_modifier_owner_character_id, kCharacterIdOffset);
  void *const countering_owner = ResolveStoredComponent(
      bindings.character_storage_slot,
      output.countering_modifier_owner_character_id, kCharacterIdOffset);
  void *const countered_aggregator =
      countered_owner == nullptr
          ? nullptr
          : bindings.get_character_modifier_aggregator(countered_owner);
  void *const countering_aggregator =
      countering_owner == nullptr
          ? nullptr
          : bindings.get_character_modifier_aggregator(countering_owner);
  if (countered_aggregator == nullptr || countering_aggregator == nullptr ||
      bindings.get_counter_context_scale(
          &output.context_scale_raw, countered_aggregator,
          countering_aggregator) != &output.context_scale_raw ||
      output.context_scale_raw < 0) {
    output.unavailable_reason = "counter_context_scale_unavailable";
    return output;
  }

  NativeArrayHeader countered_header{
      countered_entries.empty() ? nullptr : countered_entries.data(),
      static_cast<std::int32_t>(countered_entries.size()),
      static_cast<std::int32_t>(countered_entries.size())};
  NativeArrayHeader countering_header{
      countering_entries.empty() ? nullptr : countering_entries.data(),
      static_cast<std::int32_t>(countering_entries.size()),
      static_cast<std::int32_t>(countering_entries.size())};
  output.damage_retention_by_class_raw.assign(
      static_cast<std::size_t>(class_count), kFixedPointScale);
  NativeArrayHeader output_header{
      output.damage_retention_by_class_raw.data(), class_count, class_count};
  bindings.resolve_counter_classes(
      &countered_header, &countering_header, &output_header,
      output.context_scale_raw);
  if (output_header.data != output.damage_retention_by_class_raw.data() ||
      output_header.capacity != class_count ||
      output_header.count != class_count) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_resolution_output_reallocated";
    return output;
  }
  const auto validate_entries = [&bindings](const auto &entries) {
    for (const auto &entry : entries) {
      const auto regiment_id =
          LoadAt<std::int32_t>(entry.data(), 0x08);
      if (ResolveStoredComponent(bindings.regiment_storage_slot,
                                 regiment_id,
                                 kRegimentIdOffset) == nullptr) {
        return false;
      }
    }
    return true;
  };
  if (!validate_entries(countered_entries) ||
      !validate_entries(countering_entries)) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_regiment_generation_changed";
    return output;
  }
  if (ResolveStoredComponent(bindings.character_storage_slot,
                             output.countered_modifier_owner_character_id,
                             kCharacterIdOffset) != countered_owner ||
      ResolveStoredComponent(bindings.character_storage_slot,
                             output.countering_modifier_owner_character_id,
                             kCharacterIdOffset) != countering_owner) {
    output.damage_retention_by_class_raw.clear();
    output.unavailable_reason = "counter_owner_generation_changed";
    return output;
  }
  output.available = true;
  output.unavailable_reason.clear();
  return output;
}


} // namespace

CombatBindings BindCombatImage(std::uintptr_t image_base,
                              std::string_view executable_sha256) noexcept {
  CombatBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return result;
  }
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.army_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1E380);
  result.army_internal_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1DE48);
  result.regiment_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1F340);
  result.character_storage_slot = reinterpret_cast<void **>(image_base + kCharacterStorageSlotRva);
  result.combat_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1DE70);
  result.get_army_commander = reinterpret_cast<GetArmyCommander>(image_base + 0x24E9ED0);
  result.get_commander_advantage = reinterpret_cast<GetCommanderAdvantage>(image_base + 0xC6DED0);
  result.get_province_terrain = reinterpret_cast<GetProvinceTerrain>(image_base + 0x247E590);
  result.evaluate_regiment_stats_at_province = reinterpret_cast<EvaluateRegimentStatsAtProvince>(image_base + 0x26344C0);
  result.is_special_combat_regiment = reinterpret_cast<IsSpecialCombatRegiment>(image_base + 0x2634880);
  result.get_character_modifier_aggregator = reinterpret_cast<GetCharacterModifierAggregator>(image_base + 0x28C3AE0);
  result.read_character_modifier = reinterpret_cast<ReadCharacterModifier>(image_base + 0x2303700);
  result.get_combat_rules = reinterpret_cast<GetCombatRules>(image_base + 0x899E40);
  result.read_counter_current_chunk = reinterpret_cast<ReadCounterCurrentChunk>(image_base + 0x2657970);
  result.resolve_counter_classes = reinterpret_cast<ResolveCounterClasses>(image_base + 0x2653F10);
  result.get_counter_context_scale = reinterpret_cast<GetCounterContextScale>(image_base + 0x2C533E0);
  result.get_knight_effectiveness_context = reinterpret_cast<GetKnightEffectivenessContext>(image_base + 0x28BFC70);
  result.read_knight_effectiveness = reinterpret_cast<ReadKnightEffectiveness>(image_base + 0x2C06B00);
  result.is_holding_defender = reinterpret_cast<IsHoldingDefender>(image_base + 0x2C09D30);
  result.commander_min_roll = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699BC);
  result.commander_max_roll = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699B8);
  result.knight_damage_per_prowess = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699A8);
  result.knight_toughness_per_prowess = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699B0);
  result.minimum_combat_width = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699C8);
  result.base_combat_width_ratio = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69BA8);
  return result;
}

ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const CombatBindings &bindings, const Snapshot &current,
    const CombatSimulationInputsRequest &request,
    CombatSimulationInputsSnapshot &output) noexcept {
  output = {};
  const auto total_army_count = request.attacker_army_ids.size() +
                                request.defender_army_ids.size();
  if (request.target_province_id <= 0 ||
      request.attacker_entry_province_id <= 0 ||
      request.target_province_id == request.attacker_entry_province_id ||
      request.attacker_army_ids.empty() ||
      request.defender_army_ids.empty() ||
      request.attacker_army_ids.size() > 63 ||
      request.defender_army_ids.size() > 63 || total_army_count > 64) {
    return ReadCombatSimulationInputsResult::invalid_arguments;
  }
  std::vector<std::int32_t> army_ids;
  army_ids.reserve(total_army_count);
  army_ids.insert(army_ids.end(), request.attacker_army_ids.begin(),
                  request.attacker_army_ids.end());
  army_ids.insert(army_ids.end(), request.defender_army_ids.begin(),
                  request.defender_army_ids.end());
  for (std::size_t index = 0; index < army_ids.size(); ++index) {
    if (army_ids[index] <= 0 ||
        std::find(army_ids.begin(), army_ids.begin() + index,
                  army_ids[index]) != army_ids.begin() + index) {
      return ReadCombatSimulationInputsResult::invalid_arguments;
    }
  }
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.army_storage_slot == nullptr ||
      bindings.army_internal_storage_slot == nullptr ||
      bindings.regiment_storage_slot == nullptr ||
      bindings.character_storage_slot == nullptr ||
      bindings.combat_storage_slot == nullptr ||
      bindings.get_army_commander == nullptr ||
      bindings.get_commander_advantage == nullptr ||
      bindings.get_province_terrain == nullptr ||
      bindings.evaluate_regiment_stats_at_province == nullptr ||
      bindings.is_special_combat_regiment == nullptr ||
      bindings.get_character_modifier_aggregator == nullptr ||
      bindings.read_character_modifier == nullptr ||
      bindings.get_combat_rules == nullptr ||
      bindings.read_counter_current_chunk == nullptr ||
      bindings.resolve_counter_classes == nullptr ||
      bindings.get_counter_context_scale == nullptr ||
      bindings.get_knight_effectiveness_context == nullptr ||
      bindings.read_knight_effectiveness == nullptr ||
      bindings.is_holding_defender == nullptr ||
      bindings.commander_min_roll == nullptr ||
      bindings.commander_max_roll == nullptr ||
      bindings.knight_damage_per_prowess == nullptr ||
      bindings.knight_toughness_per_prowess == nullptr ||
      bindings.minimum_combat_width == nullptr ||
      bindings.base_combat_width_ratio == nullptr) {
    return ReadCombatSimulationInputsResult::unavailable;
  }

  if (!current.paused) {
    return ReadCombatSimulationInputsResult::requires_paused;
  }
  if (!current.has_played_character || !current.played_character_alive) {
    return ReadCombatSimulationInputsResult::no_played_character;
  }
  void *const game_state = *bindings.game_state_slot;
  if (game_state == nullptr) {
    return ReadCombatSimulationInputsResult::unavailable;
  }
  void *const target_province =
      ResolveProvince(game_state, request.target_province_id);
  if (target_province == nullptr) {
    return ReadCombatSimulationInputsResult::target_province_not_found;
  }
  if (ResolveProvince(game_state, request.attacker_entry_province_id) ==
      nullptr) {
    return ReadCombatSimulationInputsResult::invalid_encounter;
  }
  std::int32_t counter_class_count = 0;
  if (!ReadCounterClassCount(bindings, counter_class_count)) {
    return ReadCombatSimulationInputsResult::unavailable;
  }

  output.target_province_id = request.target_province_id;
  output.scenario.attacker_entry_province_id =
      request.attacker_entry_province_id;
  output.scenario.attacker_army_ids = request.attacker_army_ids;
  output.scenario.defender_army_ids = request.defender_army_ids;
  output.input_observation_ready = false;
  output.monte_carlo_ready = false;
  output.missing_required_domains.clear();

  const auto scope = BuildArmyStrengthScope(current);
  std::vector<const ArmyStrengthScopeEntry *> selected_scope;
  selected_scope.reserve(army_ids.size());
  for (const auto army_id : army_ids) {
    const auto entry = std::find_if(
        scope.begin(), scope.end(), [army_id](const auto &candidate) {
          return candidate.army_id == army_id;
        });
    if (entry == scope.end()) {
      output = {};
      return ReadCombatSimulationInputsResult::army_not_in_scope;
    }
    selected_scope.push_back(&*entry);
  }

  std::vector<std::int32_t> common_wars;
  if (!selected_scope.empty()) {
    common_wars = selected_scope.front()->war_ids;
  }
  for (const auto *entry : selected_scope) {
    std::erase_if(common_wars, [entry](std::int32_t war_id) {
      return std::find(entry->war_ids.begin(), entry->war_ids.end(), war_id) ==
             entry->war_ids.end();
    });
  }
  const auto is_enemy_scope = [](const ArmyStrengthScopeEntry *entry) {
    return entry->role == ArmyStrengthScopeRole::active_war_enemy;
  };
  const bool attacker_enemy_side = is_enemy_scope(selected_scope.front());
  const auto attacker_count = request.attacker_army_ids.size();
  for (std::size_t index = 0; index < selected_scope.size(); ++index) {
    const bool expected_enemy =
        index < attacker_count ? attacker_enemy_side : !attacker_enemy_side;
    if (is_enemy_scope(selected_scope[index]) != expected_enemy) {
      output = {};
      return ReadCombatSimulationInputsResult::invalid_encounter;
    }
  }
  if (common_wars.empty()) {
    output = {};
    return ReadCombatSimulationInputsResult::invalid_encounter;
  }
  output.scenario.attacker_side =
      attacker_enemy_side ? "enemy" : "player_or_allied";
  output.scenario.defender_side =
      attacker_enemy_side ? "player_or_allied" : "enemy";

  output.target_province = ReadCombatCandidateProvince(
      bindings, game_state, request.target_province_id);
  void *const target_terrain = bindings.get_province_terrain(target_province);
  output.armies.reserve(selected_scope.size());
  bool has_unavailable_subdomain = false;
  bool partial = !output.target_province.available;
  for (std::size_t index = 0; index < selected_scope.size(); ++index) {
    const auto *entry = selected_scope[index];
    output.armies.push_back(ReadCombatArmyInputsRow(
        bindings, game_state, target_province, target_terrain,
        request.target_province_id, counter_class_count, *entry,
        output.ongoing_combats,
        has_unavailable_subdomain));
    output.armies.back().encounter_role =
        index < attacker_count ? "attacker" : "defender";
    partial = partial || !output.armies.back().available;
  }
  std::vector<std::int32_t> seen_knight_character_ids;
  std::vector<std::int32_t> seen_knight_regiment_ids;
  for (auto &army : output.armies) {
    if (!army.native_carmy_id_observable || !army.regiments_observable) {
      army.knights = {};
      army.knights.unavailable_reason =
          "knight_source_composition_unavailable";
      has_unavailable_subdomain = true;
      continue;
    }
    void *const internal_army = ResolveStoredComponent(
        bindings.army_internal_storage_slot, army.native_carmy_id,
        kInternalArmyIdOffset);
    if (internal_army == nullptr ||
        !ReadCombatKnights(bindings, army.native_carmy_id,
                           army.regiments, seen_knight_character_ids,
                           seen_knight_regiment_ids, army.knights)) {
      output = {};
      return ReadCombatSimulationInputsResult::unavailable;
    }
  }
  const auto geography_result = ReadContactGeography(
      bindings, game_state, target_province, request.target_province_id,
      request.attacker_entry_province_id, attacker_enemy_side,
      output.armies, output.target_province.crossing,
      output.target_province.defender_context);
  if (geography_result != ReadContactGeographyResult::available) {
    if (geography_result == ReadContactGeographyResult::invalid_encounter) {
      output = {};
      return ReadCombatSimulationInputsResult::invalid_encounter;
    }
    has_unavailable_subdomain = true;
  }
  output.target_province.precontact_width = ReadPrecontactCombatWidth(
      bindings, output.armies, output.target_province.terrain);
  if (!output.target_province.precontact_width.available) {
    has_unavailable_subdomain = true;
  }
  output.counter_resolutions.push_back(ReadCounterResolution(
      bindings, output.armies, counter_class_count, false));
  output.counter_resolutions.push_back(ReadCounterResolution(
      bindings, output.armies, counter_class_count, true));
  for (const auto &resolution : output.counter_resolutions) {
    has_unavailable_subdomain =
        has_unavailable_subdomain || !resolution.available;
  }
  const auto append_missing_domain = [&output](std::string_view domain) {
    if (std::find(output.missing_required_domains.begin(),
                  output.missing_required_domains.end(), domain) ==
        output.missing_required_domains.end()) {
      output.missing_required_domains.emplace_back(domain);
    }
  };
  if (!output.target_province.available ||
      !output.target_province.terrain.available) {
    append_missing_domain("target_terrain");
  }
  if (!output.target_province.crossing.available) {
    append_missing_domain("crossing");
  }
  if (!output.target_province.defender_context.available ||
      output.target_province.defender_context.holding_defender_status !=
          CombatObservationStatus::available) {
    append_missing_domain("attacker_defender_holding");
  }
  if (!output.target_province.precontact_width.available) {
    append_missing_domain("contact_combat_width");
  }
  for (const auto &army : output.armies) {
    if (!army.available || !army.native_carmy_id_observable ||
        army.owner.status != CombatObservationStatus::available) {
      append_missing_domain("army_identity_and_owner");
    }
    if (army.commander.status == CombatObservationStatus::unavailable ||
        !army.commander.battle_context.available) {
      append_missing_domain("commander_and_roll_bounds");
    }
    if (!army.regiments_observable) {
      append_missing_domain("regiment_composition");
    }
    for (const auto &regiment : army.regiments) {
      if (!regiment.identity_valid) {
        append_missing_domain("regiment_identity");
      }
      if (regiment.maa_type.status == CombatObservationStatus::unavailable) {
        append_missing_domain("regiment_maa_type");
      }
      if (regiment.kind.status != CombatObservationStatus::available) {
        append_missing_domain("regiment_kind_and_main_phase_eligibility");
      }
      if (!regiment.effective_stats.available) {
        append_missing_domain("effective_regiment_stats");
      }
      if (regiment.counter.status == CombatObservationStatus::unavailable) {
        append_missing_domain("counter_operands");
      }
    }
    if (!army.knights.available) {
      append_missing_domain("knights");
    }
  }
  for (const auto &combat : output.ongoing_combats) {
    if (!combat.available) {
      append_missing_domain("ongoing_combat_context");
    }
  }
  for (const auto &resolution : output.counter_resolutions) {
    if (!resolution.available) {
      append_missing_domain("counter_resolutions");
    }
  }
  output.input_observation_ready = output.missing_required_domains.empty();
  append_missing_domain("damage_to_casualty_allocation");
  append_missing_domain("pursuit_transition");
  append_missing_domain("battle_end_and_retreat_transition");
  append_missing_domain("phase_event_rng_and_effects");
  partial = partial || has_unavailable_subdomain ||
            !output.input_observation_ready;
  return partial ? ReadCombatSimulationInputsResult::partial
                 : ReadCombatSimulationInputsResult::available;
}
} // namespace xar::ck3_12002

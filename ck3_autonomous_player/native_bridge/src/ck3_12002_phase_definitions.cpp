#include "xar_bridge/ck3_12002_phase_definitions.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool KeyEquals(const void *object, std::size_t offset,
               std::string_view expected) noexcept {
  if (!object) return false;
  const auto *key = static_cast<const std::byte *>(object) + offset;
  const auto size = Load<std::size_t>(key, 0x10);
  const auto capacity = Load<std::size_t>(key, 0x18);
  if (size != expected.size() || capacity < size) return false;
  const char *data = capacity < 16 ? reinterpret_cast<const char *>(key)
                                 : Load<const char *>(key, 0);
  return data && std::memcmp(data, expected.data(), size) == 0;
}

bool ResolveRuleToken(const PhaseDefinitionBindings &b, std::string_view key,
                      void *&output) noexcept {
  output = nullptr;
  if (!b.enabled || !b.rule_token_registry || !*b.rule_token_registry ||
      !b.rule_token_fallback || !b.hash_rule_key || !b.lookup_rule_token ||
      key.size() > std::numeric_limits<std::uint32_t>::max()) return false;
  auto *registry = *b.rule_token_registry;
  auto hash = b.hash_rule_key(registry, key.data(),
                             static_cast<std::uint32_t>(key.size()));
  auto *token = b.lookup_rule_token(registry, hash);
  if (!token || token == *b.rule_token_fallback || !KeyEquals(token, 0x18, key))
    return false;
  output = token;
  return true;
}
} // namespace

PhaseDefinitionBindings BindPhaseDefinitionsImage(
    std::uintptr_t base, std::string_view hash) noexcept {
  PhaseDefinitionBindings b{};
  if (!base || hash != kExecutableSha256) return b;
  b.enabled = true;
  b.maa_type_registry = reinterpret_cast<void **>(base + kPhaseMaaTypeRegistrySlot);
  b.rule_service = reinterpret_cast<void **>(base + kPhaseGameRuleServiceSlot);
  b.rule_token_registry = reinterpret_cast<void **>(base + kPhaseRuleTokenRegistrySlot);
  b.rule_token_fallback = reinterpret_cast<void **>(base + kPhaseRuleTokenFallbackSlot);
  b.hash_rule_key = reinterpret_cast<PhaseRuleKeyHash>(base + kPhaseRuleKeyHashRva);
  b.lookup_rule_token = reinterpret_cast<PhaseRuleTokenLookup>(base + kPhaseRuleTokenLookupRva);
  b.variable_table = reinterpret_cast<PhaseVariableIdentifierTable>(base + kPhaseVariableIdentifierTableRva);
  b.lookup_variable_identifier = reinterpret_cast<PhaseVariableIdentifierLookup>(base + kPhaseVariableIdentifierLookupRva);
  b.variable_identifier_name = reinterpret_cast<PhaseVariableIdentifierName>(base + kPhaseVariableIdentifierNameRva);
  b.lookup_script_identifier = reinterpret_cast<PhaseScriptIdentifierLookup>(base + kPhaseScriptIdentifierLookupRva);
  b.script_identifier_name = reinterpret_cast<PhaseScriptIdentifierName>(base + kPhaseScriptIdentifierNameRva);
  b.variable_context = reinterpret_cast<PhaseVariableContext>(base + kPhaseVariableContextRva);
  b.commander_min_roll = reinterpret_cast<const std::int32_t *>(base + kPhaseCommanderMinRollSlot);
  b.commander_max_roll = reinterpret_cast<const std::int32_t *>(base + kPhaseCommanderMaxRollSlot);
  b.knight_damage_per_prowess = reinterpret_cast<const std::int32_t *>(base + kPhaseKnightDamageSlot);
  b.knight_toughness_per_prowess = reinterpret_cast<const std::int32_t *>(base + kPhaseKnightToughnessSlot);
  b.minimum_combat_width = reinterpret_cast<const std::int32_t *>(base + kPhaseMinimumCombatWidthSlot);
  b.base_combat_width_ratio = reinterpret_cast<const std::int64_t *>(base + kPhaseBaseWidthRatioSlot);
  return b;
}

bool ReadPhaseMaaBaseTypes(const PhaseDefinitionBindings &b,
                          std::vector<PhaseMaaBaseType> &output) noexcept {
  output.clear();
  if (!b.enabled || !b.maa_type_registry || !*b.maa_type_registry) return false;
  auto *registry = *b.maa_type_registry;
  auto *data = Load<void *>(registry, kPhaseMaaBaseTypeDataOffset);
  auto count = Load<std::int32_t>(registry, kPhaseMaaBaseTypeCountOffset);
  if (count < 0 || count > 65'536 || (count && !data)) return false;
  constexpr std::array<std::string_view, 10> keys{
      "skirmishers", "archers", "pikemen", "heavy_infantry", "light_cavalry",
      "heavy_cavalry", "camel_cavalry", "elephant_cavalry", "archer_cavalry", "gunpowder"};
  std::vector<PhaseMaaBaseType> rows;
  rows.reserve(keys.size());
  for (auto expected : keys) {
    const void *found = nullptr;
    for (std::int32_t i = 0; i < count; ++i) {
      auto *row = static_cast<const std::byte *>(data) +
                  static_cast<std::size_t>(i) * kPhaseMaaBaseTypeStride;
      if (!KeyEquals(row, 8, expected)) continue;
      if (found) return false;
      found = row;
    }
    if (!found) return false;
    rows.push_back({std::string(expected), Load<std::int32_t>(found, 0)});
  }
  output = std::move(rows);
  return true;
}

bool ReadPhaseDifficulty(const PhaseDefinitionBindings &b,
                         PhaseDifficulty &output) noexcept {
  output = {};
  void *easy = nullptr;
  void *very_easy = nullptr;
  if (!ResolveRuleToken(b, "easy_difficulty", easy) ||
      !ResolveRuleToken(b, "very_easy_difficulty", very_easy) ||
      easy == very_easy || !b.rule_service || !*b.rule_service) return false;
  auto *service = *b.rule_service;
  auto *vtable = Load<void *>(service, 0);
  if (!vtable) return false;
  auto reader = Load<void *(*)(void *)>(vtable, 0x10);
  if (!reader) return false;
  auto *selected = reader(service);
  if (!selected) return false;
  auto *data = Load<void *>(selected, 8);
  auto count = Load<std::int32_t>(selected, 0x14);
  if (count < 0 || count > 65'536 || (count && !data)) return false;
  std::int32_t easy_count = 0, very_easy_count = 0;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *token = Load<void *>(data, static_cast<std::size_t>(i) * 8);
    if (!token) return false;
    if (token == easy) ++easy_count;
    else if (token == very_easy) ++very_easy_count;
  }
  if (easy_count > 1 || very_easy_count > 1 || (easy_count && very_easy_count))
    return false;
  output = {easy_count == 1, very_easy_count == 1};
  return true;
}

bool ResolvePhaseScriptIdentifier(const PhaseDefinitionBindings &b,
                                  std::string_view key,
                                  std::int32_t &identifier) noexcept {
  identifier = -1;
  if (!b.enabled || !b.lookup_script_identifier || !b.script_identifier_name)
    return false;
  PhaseStringView64 view{key.data(), static_cast<std::int64_t>(key.size())};
  auto candidate = b.lookup_script_identifier(&view);
  if (candidate < 0 || candidate == 12) return false;
  auto *round_trip = b.script_identifier_name(candidate);
  if (!round_trip || *round_trip != key) return false;
  identifier = candidate;
  return true;
}

bool ResolvePhaseVariableIdentifier(const PhaseDefinitionBindings &b,
                                    std::string_view key,
                                    std::int32_t &identifier) noexcept {
  identifier = -1;
  if (!b.enabled || !b.variable_table || !b.lookup_variable_identifier ||
      !b.variable_identifier_name ||
      key.size() > std::numeric_limits<std::int32_t>::max()) return false;
  auto *table = b.variable_table();
  if (!table) return false;
  PhaseStringView32 view{key.data(), static_cast<std::int32_t>(key.size()), 0};
  std::int32_t candidate = -1;
  if (!b.lookup_variable_identifier(table, &candidate, &view) || candidate < 0)
    return false;
  auto *round_trip = b.variable_identifier_name(table, candidate);
  if (!round_trip || *round_trip != key) return false;
  identifier = candidate;
  return true;
}

bool ReadPhaseCombatDefines(const PhaseDefinitionBindings &b,
                           PhaseCombatDefines &output) noexcept {
  output = {};
  if (!b.enabled || !b.commander_min_roll || !b.commander_max_roll ||
      !b.knight_damage_per_prowess || !b.knight_toughness_per_prowess ||
      !b.minimum_combat_width || !b.base_combat_width_ratio) return false;
  output = {*b.commander_min_roll, *b.commander_max_roll,
            *b.knight_damage_per_prowess, *b.knight_toughness_per_prowess,
            *b.minimum_combat_width, *b.base_combat_width_ratio};
  return true;
}

bool ReadPhaseArmyMaa(const PhaseDefinitionBindings &b,
                      const game::CombatArmyInputsSnapshot &base,
                      game::CombatPhaseArmyV3 &output) noexcept {
  output = {};
  if (!b.enabled || !base.available || !base.native_carmy_id_observable ||
      !base.regiments_observable || !b.resolve_regiment) return false;
  std::vector<PhaseMaaBaseType> enums;
  if (!ReadPhaseMaaBaseTypes(b, enums)) return false;
  std::array<std::int64_t, 10> counts{};
  std::int64_t total = 0, crossbows = 0;
  for (const auto &regiment : base.regiments) {
    if (!regiment.available || !regiment.identity_valid ||
        regiment.maa_type.status == game::CombatObservationStatus::unavailable)
      return false;
    if (regiment.maa_type.status == game::CombatObservationStatus::absent) continue;
    auto *native = b.resolve_regiment(b.regiment_context, regiment.regiment_id);
    if (!native || Load<std::int32_t>(native, 0x10) != regiment.regiment_id ||
        Load<std::int32_t>(native, 0x140) != base.native_carmy_id) return false;
    auto *type = Load<void *>(native, 0x18);
    if (!type) return false;
    // Native base-type count trigger 0x2B37AF0 reads the inner type at
    // regiment+0x18, then its base enum at +0x260 (old +0x270).
    auto base_enum = Load<std::int32_t>(type, 0x260);
    ++total;
    for (std::size_t index = 0; index < enums.size(); ++index)
      if (base_enum == enums[index].value) ++counts[index];
    auto key = regiment.maa_type.key;
    if (key == "crossbowmen" || key == "shenbigong" ||
        key == "accolade_maa_crossbowers") ++crossbows;
  }
  game::CombatPhaseArmyV3 result;
  result.army_id = base.army_id;
  result.native_carmy_id = base.native_carmy_id;
  result.encounter_role = base.encounter_role;
  if (base.regiments.size() > static_cast<std::size_t>(
          std::numeric_limits<std::int64_t>::max() / 100'000)) return false;
  result.maa_regiment_count_raw = total * 100'000;
  // Archers are divided into crossbows and the remaining archer family,
  // following the compiled phase-event leaf operands.
  for (std::size_t index = 0; index < enums.size(); ++index) {
    if (enums[index].key == "archers") continue;
    result.maa_counts_raw.push_back({enums[index].key + "_raw", counts[index] * 100'000});
  }
  result.maa_counts_raw.push_back({"crossbow_family_raw", crossbows * 100'000});
  result.maa_counts_raw.push_back({"non_crossbow_archers_raw", (counts[1] - crossbows) * 100'000});
  output = std::move(result);
  return true;
}
} // namespace xar::ck3_12002

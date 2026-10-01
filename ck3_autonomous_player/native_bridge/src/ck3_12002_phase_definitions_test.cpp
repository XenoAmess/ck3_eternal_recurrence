#include "xar_bridge/ck3_12002_phase_definitions.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>

using namespace xar::ck3_12002;
namespace {
template <typename T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(T));
}
void PutKey(void *p, std::size_t offset, std::string_view key) {
  auto *s = static_cast<std::byte *>(p) + offset;
  std::size_t capacity = key.size() < 16 ? 15 : key.size();
  if (capacity == 15) std::memcpy(s, key.data(), key.size());
  else Put<const char *>(s, 0, key.data());
  Put<std::size_t>(s, 0x10, key.size());
  Put<std::size_t>(s, 0x18, capacity);
}
std::array<std::byte, 0x60> easy_token{}, very_easy_token{};
std::array<std::byte, 0x20> selection{};
std::array<std::array<std::byte, 0x150>, 2> regiments{};
int registry_cookie = 0;
void *Select(void *service) { assert(service); return selection.data(); }
std::int32_t Hash(void *registry, const char *key, std::uint32_t size) {
  assert(registry == &registry_cookie);
  std::string_view text{key, size};
  if (text == "easy_difficulty") return 71;
  if (text == "very_easy_difficulty") return 82;
  assert(false); return 0;
}
void *Token(void *registry, std::int32_t hash) {
  assert(registry == &registry_cookie);
  return hash == 71 ? easy_token.data() : very_easy_token.data();
}
const std::string script_key = "government_is_nomadic";
const std::string variable_key = "conqueror";
std::int32_t ScriptLookup(const PhaseStringView64 *view) {
  assert(view && view->size == static_cast<std::int64_t>(script_key.size()));
  return std::string_view(view->data, view->size) == script_key ? 99 : 12;
}
const std::string *ScriptName(std::int32_t id) {
  return id == 99 ? &script_key : nullptr;
}
void *VariableTable() { return &registry_cookie; }
std::int32_t *VariableLookup(void *table, std::int32_t *out,
                             const PhaseStringView32 *view) {
  assert(table == &registry_cookie && view && view->pad == 0);
  assert(std::string_view(view->data, view->size) == variable_key);
  *out = 0x01000006;
  return out;
}
const std::string *VariableName(void *table, std::int32_t id) {
  assert(table == &registry_cookie);
  return id == 0x01000006 ? &variable_key : nullptr;
}
void *ResolveRegiment(void *, std::int32_t id) {
  if (id == 44) return regiments[0].data();
  if (id == 45) return regiments[1].data();
  return nullptr;
}
} // namespace

int main() {
  constexpr std::uintptr_t base = 0x140000000;
  auto native = BindPhaseDefinitionsImage(base, kExecutableSha256);
  assert(native.enabled);
  assert(reinterpret_cast<std::uintptr_t>(native.maa_type_registry) == base + 0x5C67558);
  assert(reinterpret_cast<std::uintptr_t>(native.rule_token_registry) == base + 0x5D34358);
  assert(reinterpret_cast<std::uintptr_t>(native.commander_min_roll) == base + 0x5C699BC);
  assert(reinterpret_cast<std::uintptr_t>(native.base_combat_width_ratio) == base + 0x5C69BA8);
  assert(!BindPhaseDefinitionsImage(base, "1.19.0.6").enabled);
  assert(!BindPhaseDefinitionsImage(0, kExecutableSha256).enabled);

  PhaseDefinitionBindings b{};
  b.enabled = true;
  std::array<std::byte, 0xF20> registry{};
  std::array<std::array<std::byte, 0x58>, 11> rows{};
  constexpr std::array<std::string_view, 10> keys{
      "skirmishers", "archers", "pikemen", "heavy_infantry", "light_cavalry",
      "heavy_cavalry", "camel_cavalry", "elephant_cavalry", "archer_cavalry", "gunpowder"};
  for (std::size_t i = 0; i < keys.size(); ++i) {
    // Deliberately reorder loaded enum rows, and use ids unlike row indices.
    auto index = keys.size() - 1 - i;
    Put<std::int32_t>(rows[index].data(), 0, static_cast<std::int32_t>(300 + i));
    PutKey(rows[index].data(), 8, keys[i]);
  }
  Put<void *>(registry.data(), 0xEF0, rows.data());
  Put<std::int32_t>(registry.data(), 0xEFC, 10);
  // The old offsets contain incompatible data and must never be consulted.
  Put<void *>(registry.data(), 0xF08, nullptr);
  Put<std::int32_t>(registry.data(), 0xF14, -1);
  void *registry_pointer = registry.data();
  b.maa_type_registry = &registry_pointer;
  std::vector<PhaseMaaBaseType> enums;
  assert(ReadPhaseMaaBaseTypes(b, enums) && enums.size() == 10);
  for (std::size_t i = 0; i < keys.size(); ++i)
    assert(enums[i].key == keys[i] && enums[i].value == static_cast<std::int32_t>(300 + i));
  rows[10] = rows[9];
  Put<std::int32_t>(registry.data(), 0xEFC, 11);
  assert(!ReadPhaseMaaBaseTypes(b, enums) && enums.empty());
  Put<std::int32_t>(registry.data(), 0xEFC, 9);
  assert(!ReadPhaseMaaBaseTypes(b, enums));
  Put<std::int32_t>(registry.data(), 0xEFC, 10);
  std::array<std::array<std::byte, 0x280>, 2> inner_types{};
  for (std::size_t i = 0; i < 2; ++i) {
    Put<std::int32_t>(regiments[i].data(), 0x10, static_cast<std::int32_t>(44 + i));
    Put<std::int32_t>(regiments[i].data(), 0x140, 3);
    Put<void *>(regiments[i].data(), 0x18, inner_types[i].data());
    Put<std::int32_t>(inner_types[i].data(), 0x260, static_cast<std::int32_t>(301 - i));
    Put<std::int32_t>(inner_types[i].data(), 0x270, 309); // old offset decoy
  }
  xar::game::CombatArmyInputsSnapshot army;
  army.available = true;
  army.army_id = 21;
  army.native_carmy_id_observable = true;
  army.native_carmy_id = 3;
  army.encounter_role = "attacker";
  army.regiments_observable = true;
  army.regiments.resize(3);
  for (std::size_t i = 0; i < 3; ++i) {
    auto &regiment = army.regiments[i];
    regiment.available = true;
    regiment.identity_valid = true;
    regiment.regiment_id = static_cast<std::int32_t>(44 + i);
    regiment.maa_type.status = i == 2 ? xar::game::CombatObservationStatus::absent
                                    : xar::game::CombatObservationStatus::available;
    regiment.maa_type.key = i == 0 ? "crossbowmen" : "light_footmen";
  }
  b.resolve_regiment = ResolveRegiment;
  xar::game::CombatPhaseArmyV3 phase_army;
  assert(ReadPhaseArmyMaa(b, army, phase_army));
  assert(phase_army.maa_regiment_count_raw == 200000 && phase_army.army_id == 21);
  assert(phase_army.maa_counts_raw.size() == 11);
  for (const auto &row : phase_army.maa_counts_raw) {
    if (row.key == "skirmishers_raw" || row.key == "crossbow_family_raw") assert(row.value == 100000);
    else assert(row.value == 0);
  }
  Put<std::int32_t>(regiments[0].data(), 0x140, 4);
  assert(!ReadPhaseArmyMaa(b, army, phase_army));
  Put<std::int32_t>(regiments[0].data(), 0x140, 3);

  PutKey(easy_token.data(), 0x18, "easy_difficulty");
  PutKey(very_easy_token.data(), 0x18, "very_easy_difficulty");
  void *token_registry = &registry_cookie, *fallback = nullptr;
  std::array<std::uintptr_t, 3> vtable{0, 0, reinterpret_cast<std::uintptr_t>(&Select)};
  void *service_vtable = vtable.data();
  void *service = &service_vtable;
  b.rule_service = &service;
  b.rule_token_registry = &token_registry;
  b.rule_token_fallback = &fallback;
  b.hash_rule_key = Hash;
  b.lookup_rule_token = Token;
  std::array<void *, 2> selected{easy_token.data(), very_easy_token.data()};
  Put<void *>(selection.data(), 8, selected.data());
  Put<std::int32_t>(selection.data(), 0x14, 1);
  PhaseDifficulty difficulty;
  assert(ReadPhaseDifficulty(b, difficulty) && difficulty.easy && !difficulty.very_easy);
  selected[0] = very_easy_token.data();
  assert(ReadPhaseDifficulty(b, difficulty) && !difficulty.easy && difficulty.very_easy);
  selected[0] = easy_token.data();
  Put<std::int32_t>(selection.data(), 0x14, 2);
  assert(!ReadPhaseDifficulty(b, difficulty) && !difficulty.easy && !difficulty.very_easy);
  selected[1] = easy_token.data();
  assert(!ReadPhaseDifficulty(b, difficulty));
  Put<std::int32_t>(selection.data(), 0x14, 0);
  assert(ReadPhaseDifficulty(b, difficulty) && !difficulty.easy && !difficulty.very_easy);
  fallback = easy_token.data();
  assert(!ReadPhaseDifficulty(b, difficulty));
  fallback = nullptr;

  b.lookup_script_identifier = ScriptLookup;
  b.script_identifier_name = ScriptName;
  b.variable_table = VariableTable;
  b.lookup_variable_identifier = VariableLookup;
  b.variable_identifier_name = VariableName;
  std::int32_t id = -1;
  assert(ResolvePhaseScriptIdentifier(b, script_key, id) && id == 99);
  assert(ResolvePhaseVariableIdentifier(b, variable_key, id) && id == 0x01000006);
  b.script_identifier_name = [](std::int32_t) -> const std::string * { return &variable_key; };
  assert(!ResolvePhaseScriptIdentifier(b, script_key, id) && id == -1);

  std::int32_t min_roll = -1, max_roll = 9, damage = 100, toughness = 10, width = 100;
  std::int64_t ratio = 50000;
  b.commander_min_roll = &min_roll;
  b.commander_max_roll = &max_roll;
  b.knight_damage_per_prowess = &damage;
  b.knight_toughness_per_prowess = &toughness;
  b.minimum_combat_width = &width;
  b.base_combat_width_ratio = &ratio;
  PhaseCombatDefines defines;
  assert(ReadPhaseCombatDefines(b, defines));
  assert(defines.commander_min_roll == -1 && defines.commander_max_roll == 9 &&
         defines.knight_damage_per_prowess == 100 && defines.knight_toughness_per_prowess == 10 &&
         defines.minimum_combat_width == 100 && defines.base_combat_width_ratio == 50000);
  b.enabled = false;
  assert(!ReadPhaseCombatDefines(b, defines));
  assert(!ResolvePhaseVariableIdentifier(b, variable_key, id));
  std::cout << "PASS phase definitions: exact-build bindings, relocated Maa rows, difficulty selection, identifier round trips and combat defines; synthetic objects only\n";
}

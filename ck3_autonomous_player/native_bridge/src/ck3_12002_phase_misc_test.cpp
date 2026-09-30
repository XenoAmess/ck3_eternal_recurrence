#include "xar_bridge/ck3_12002_phase_misc.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12002;
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T, std::size_t N>
void Put(Bytes<N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
void Check(bool condition, const char *message) {
  if (!condition) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}
struct Fixture;
Fixture *current = nullptr;
struct Fixture {
  Bytes<0x200> player{}, employer{}, liege{}, knight{}, promised{};
  Bytes<0x580> extension{};
  Bytes<0xE0> relations{};
  Bytes<0x70> accolade{};
  Bytes<0x420> attribute{};
  Bytes<0x120> court_position{};
  Bytes<0x80> government{}, modifier{}, court_type{}, court_database{};
  Bytes<0x30> character_store{}, accolade_store{}, court_store{};
  Bytes<0x60> character_slots{}, accolade_slots{}, court_slots{};
  Bytes<0x30> player_context{}, employer_context{}, liege_context{};
  Bytes<0x100> player_variables{}, employer_variables{}, liege_variables{};
  Bytes<0x90> modifiers{};
  Bytes<0x30> attribute_rows{};
  std::array<std::int32_t, 3> categories{31, 27, 30};
  std::array<std::int32_t, 3> flags{11, 15, 21};
  std::array<std::int32_t, 1> court_ids{0x01000003};
  std::array<void *, 1> court_types{court_type.data()};
  std::vector<std::string> variables;
  std::string script_name = "government_is_nomadic";
  std::string modifier_key = "ai_extreme_conqueror_modifier";
  std::string court_key = "garuda_court_position";
  void *character_store_pointer = character_store.data();
  void *accolade_store_pointer = accolade_store.data();
  void *court_store_pointer = court_store.data();
  void *court_database_pointer = court_database.data();
  void *modifier_database_pointer = modifier.data();
  void *null_fallback = nullptr;
  PhaseMiscBindings bindings;
  PhaseMiscDefinitionContext definitions;
  int parameter_calls = 0;
  bool can_acclaim = false;

  static void *VariableTable() { return current; }
  static std::int32_t *VariableLookup(void *, std::int32_t *out,
                                     const PhaseStringView32 *key) {
    std::string_view view(key->data, key->size);
    for (std::size_t i = 0; i < current->variables.size(); ++i)
      if (current->variables[i] == view) { *out = static_cast<std::int32_t>(i + 20); return out; }
    return nullptr;
  }
  static const std::string *VariableName(void *, std::int32_t id) {
    return id >= 20 && id < static_cast<std::int32_t>(current->variables.size() + 20)
        ? &current->variables[id - 20] : nullptr;
  }
  static std::int32_t ScriptLookup(const PhaseStringView64 *key) {
    return std::string_view(key->data, static_cast<std::size_t>(key->size)) ==
           current->script_name ? 15 : -1;
  }
  static const std::string *ScriptName(std::int32_t id) {
    return id == 15 ? &current->script_name : nullptr;
  }
  static std::int32_t Hash(void *, const char *key, std::uint32_t size) {
    return std::string_view(key, size) == current->modifier_key ? 42 : -1;
  }
  static void *ModifierLookup(void *, std::int32_t id) {
    return id == 42 ? current->modifier.data() : nullptr;
  }
  static void *Context(const PhaseVariableTarget *target) {
    if (target->kind != 4) return nullptr;
    if (target->payload == 0x01000001) return current->player_context.data();
    if (target->payload == 0x01000002) return current->employer_context.data();
    if (target->payload == 0x01000003) return current->liege_context.data();
    return nullptr;
  }
  static bool CanAcclaim(void *character, void *second, void *third) {
    Check(character == current->player.data() && !second && !third, "can-acclaim ABI");
    return current->can_acclaim;
  }
  static bool Parameter(void *accolade, std::int32_t id) {
    Check(accolade == current->accolade.data(), "parameter ABI");
    ++current->parameter_calls;
    return id % 2 == 0;
  }
  static void *Government(void *character) {
    return character == current->player.data() ? current->government.data() : nullptr;
  }
  template <std::size_t N>
  static void Variable(Bytes<N> &rows, std::size_t index, std::int32_t id,
                       std::uint16_t kind, std::int64_t payload) {
    Put(rows, index * 0x20 + 8, id);
    Put(rows, index * 0x20 + 0x10, kind);
    Put(rows, index * 0x20 + 0x18, payload);
  }
  Fixture() {
    current = this;
    variables = {"conqueror", "hold_court_8050_knight", "hold_court_8050_promise",
                 "accolade_progress", "men_at_arms"};
    for (const char *key : {"skirmisher", "archer", "crossbowmen", "pike", "vanguard",
                           "outrider", "lancer", "camelry", "elephantry", "horse_archer",
                           "gunpowder", "fanatic", "valiant"})
      variables.push_back(std::string(key) + "_attribute_unlock");
    for (const char *key : {"accolade_defends_family_low", "accolade_defends_family_medium",
                           "accolade_defends_family_high", "accolade_increase_hostile_knight_death_low",
                           "accolade_increase_hostile_knight_death_medium", "accolade_increase_hostile_knight_death_high"})
      variables.push_back(key);
    Put(player, 0x18, 0x01000001); Put(employer, 0x18, 0x01000002);
    Put(liege, 0x18, 0x01000003); Put(knight, 0x18, 0x01000004);
    Put(promised, 0x18, 0x01000005);
    Put(player, 0x1B0, extension.data()); Put(player, 0x1B8, relations.data());
    // Changed ABI members carry meaningful decoys at the old offsets.
    Put(extension, 0x568, std::int32_t{-1}); Put(extension, 0x570, 0x01000001);
    Put(character_store, 0x20, character_slots.data()); Put(character_store, 0x2C, 6);
    Put(accolade_store, 0x20, accolade_slots.data()); Put(accolade_store, 0x2C, 6);
    Put(court_store, 0x20, court_slots.data()); Put(court_store, 0x2C, 6);
    Put(character_slots, 0x18, player.data()); Put(character_slots, 0x28, employer.data());
    Put(character_slots, 0x38, liege.data()); Put(character_slots, 0x48, knight.data());
    Put(character_slots, 0x58, promised.data());
    Put(accolade_slots, 0x18, accolade.data()); Put(court_slots, 0x38, court_position.data());
    Put(player_context, 0x10, player_variables.data()); Put(player_context, 0x1C, 3);
    Put(employer_context, 0x10, employer_variables.data()); Put(employer_context, 0x1C, 1);
    Put(liege_context, 0x10, liege_variables.data()); Put(liege_context, 0x1C, 1);
    Variable(player_variables, 0, 20, 1, 0); // Presence is true even when numeric value is zero.
    Variable(player_variables, 1, 21, 4, 0x01000004);
    Variable(player_variables, 2, 25, 1, 0);
    Variable(employer_variables, 0, 22, 4, 0x01000005);
    Variable(liege_variables, 0, 23, 1, 3'000'000);
    Put(extension, 0x188, modifiers.data()); Put(extension, 0x194, 2);
    Put(modifiers, 0x48, modifier.data());
    Put(accolade, 8, 0x01000001); Put(accolade, 0xC, std::uint32_t{0x4163636F});
    Put(accolade, 0x58, attribute_rows.data()); Put(accolade, 0x64, 1);
    Put(attribute_rows, 0x10, attribute.data());
    Put(attribute, 0x38, std::uint32_t{0x4744624F});
    categories[1] = 24;
    Put(attribute, 0x3A8, categories.data()); Put(attribute, 0x3B4, 3);
    Put(attribute, 0x3E8, static_cast<void *>(nullptr)); Put(attribute, 0x3F4, 0);
    Put(government, 0x50, flags.data()); Put(government, 0x5C, 3);
    Put(relations, 0xD0, court_ids.data()); Put(relations, 0xDC, 1);
    Put(court_position, 8, 0x01000003); Put(court_position, 0x110, court_type.data());
    Put(court_database, 0x50, court_types.data()); Put(court_database, 0x5C, 1);
    std::memcpy(modifier.data() + 0x18, &modifier_key, sizeof(modifier_key));
    std::memcpy(court_type.data() + 0x18, &court_key, sizeof(court_key));
    bindings.enabled = true; bindings.identifiers.enabled = true;
    bindings.identifiers.variable_table = VariableTable;
    bindings.identifiers.lookup_variable_identifier = VariableLookup;
    bindings.identifiers.variable_identifier_name = VariableName;
    bindings.identifiers.lookup_script_identifier = ScriptLookup;
    bindings.identifiers.script_identifier_name = ScriptName;
    bindings.identifiers.variable_context = Context;
    bindings.identifiers.hash_rule_key = Hash;
    bindings.character_store = &character_store_pointer;
    bindings.character_fallback = &null_fallback;
    bindings.accolade_store = &accolade_store_pointer;
    bindings.accolade_fallback = &null_fallback;
    bindings.court_position_store = &court_store_pointer;
    bindings.court_position_fallback = &null_fallback;
    bindings.court_type_database = &court_database_pointer;
    bindings.court_type_fallback = &null_fallback;
    bindings.modifier_database = &modifier_database_pointer;
    bindings.modifier_fallback = &null_fallback;
    bindings.lookup_modifier = ModifierLookup;
    bindings.can_be_acclaimed = CanAcclaim;
    bindings.accolade_has_parameter = Parameter;
    bindings.character_government = Government;
    Check(BuildPhaseMiscDefinitions(bindings, definitions), "resolve all 27 nonreligious definitions");
    Check(definitions.attribute_variable_ids.size() == 13 &&
          definitions.accolade_parameter_ids.size() == 6, "complete contract vectors");
  }
  xar::game::CombatPhaseCharacterV3 Output() const {
    xar::game::CombatPhaseCharacterV3 out;
    out.character_id = 0x01000001;
    out.employer = {true, 0x01000002}; out.liege = {true, 0x01000003};
    out.martial = 41;
    return out;
  }
  bool Read(xar::game::CombatPhaseCharacterV3 &out) {
    return ReadPhaseCharacterMisc(bindings, definitions, player.data(), out);
  }
};
} // namespace

int main() {
  using namespace xar::ck3_12002;
  const auto addresses = BindPhaseMiscImage(0x140000000, kExecutableSha256);
  Check(addresses.enabled &&
        reinterpret_cast<std::uintptr_t>(addresses.can_be_acclaimed) == 0x142B91300,
        "exact image binding");
  Check(!BindPhaseMiscImage(0x140000000, "old-build").enabled, "build selection");
  {
    Fixture f; auto out = f.Output();
    Check(f.Read(out), "complete changed-offset reader");
    Check(out.conqueror_variable_present && out.attribute_unlock_variables[0].value &&
          !out.attribute_unlock_variables[1].value, "presence semantics");
    Check(out.hold_court_8050_knight.value == 0x01000004 &&
          out.employer_hold_court_8050_promise.value == 0x01000005 &&
          out.liege_accolade_progress_raw == 2'000'000, "related character variables and upper clamp");
    Check(out.ai_extreme_conqueror_modifier && out.is_acclaimed &&
          out.accolade_has_men_at_arms_category && !out.can_be_acclaimed &&
          out.government_is_nomadic && out.garuda_court_position &&
          f.parameter_calls == 6 && out.accolade_parameters[0].value &&
          !out.accolade_parameters[1].value && out.martial == 41,
          "native callbacks, definitions and other-leaf preservation");
    Fixture::Variable(f.liege_variables, 0, 23, 1, -100'000);
    Check(f.Read(out) && out.liege_accolade_progress_raw == -100'000,
          "progress retains native negative value");
  }
  {
    Fixture f; auto out = f.Output();
    Put(f.liege, 0x1D0, f.knight.data());
    Check(f.Read(out) && out.liege_accolade_progress_raw == 0,
          "dead liege with stale saved progress contributes zero");
    Fixture::Variable(f.liege_variables, 0, 23, 4, 0x01000004);
    Check(f.Read(out) && out.liege_accolade_progress_raw == 0,
          "dead liege does not evaluate stale variable target");
  }
  {
    Fixture f; auto out = f.Output();
    Put(f.extension, 0x570, std::int32_t{-1}); Put(f.relations, 0xDC, 0);
    Put(f.extension, 0x194, 0); Put(f.government, 0x5C, 0);
    f.can_acclaim = true;
    Check(f.Read(out) && !out.accolade.present && !out.is_acclaimed &&
          out.can_be_acclaimed && !out.ai_extreme_conqueror_modifier &&
          !out.garuda_court_position && !out.government_is_nomadic &&
          f.parameter_calls == 0, "legitimate absent and zero values");
    Put(f.player, 0x1B0, static_cast<void *>(nullptr));
    Check(f.Read(out), "absent extension");
  }
  {
    Fixture f; auto out = f.Output();
    Fixture::Variable(f.player_variables, 1, 21, 1, 0x01000004);
    Check(!f.Read(out), "typed character variable rejects numeric target");
  }
  {
    Fixture f; auto out = f.Output(); Put(f.knight, 0x18, 0x02000004);
    Check(!f.Read(out), "variable character generation identity");
  }
  {
    Fixture f; auto out = f.Output();
    Fixture::Variable(f.player_variables, 3, 20, 1, 1); Put(f.player_context, 0x1C, 4);
    Check(!f.Read(out), "ambiguous variable row");
  }
  {
    Fixture f; auto out = f.Output(); Put(f.accolade, 8, 0x02000001);
    Check(!f.Read(out), "accolade generation identity");
  }
  {
    Fixture f; auto out = f.Output(); Put(f.accolade, 0xC, std::uint32_t{0});
    Check(!f.Read(out), "native accolade identity magic");
  }
  {
    Fixture f; auto out = f.Output(); Put(f.attribute, 0x38, std::uint32_t{0});
    Check(!f.Read(out), "native attribute validation");
  }
  {
    Fixture f; auto out = f.Output(); Put(f.court_position, 8, 0x02000003);
    Check(!f.Read(out), "court position generation identity");
  }
  {
    Fixture f; PhaseMiscDefinitionContext definitions;
    Put(f.court_database, 0x50, static_cast<void *>(nullptr));
    Check(!BuildPhaseMiscDefinitions(f.bindings, definitions), "new court definition span is required");
  }
  std::cout << "phase_misc: 13 fixture scenarios passed (static-ready; no running game accessed)\n";
}

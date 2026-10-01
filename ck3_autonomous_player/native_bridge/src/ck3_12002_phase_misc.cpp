#include "xar_bridge/ck3_12002_phase_misc.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
bool ValidSpan(const void *data, std::int32_t count) noexcept {
  return count >= 0 && count <= 65'536 && (!count || data);
}
bool KeyEquals(const void *object, std::string_view expected) noexcept {
  if (!object) return false;
  auto *key = static_cast<const std::byte *>(object) + 0x18;
  auto size = Load<std::size_t>(key, 0x10);
  auto capacity = Load<std::size_t>(key, 0x18);
  if (size != expected.size() || capacity < size) return false;
  auto *data = capacity < 16 ? reinterpret_cast<const char *>(key)
                            : Load<const char *>(key, 0);
  return data && std::memcmp(data, expected.data(), size) == 0;
}
void *Resolve(void **store_slot, void **fallback_slot, std::int32_t id,
              std::size_t identity_offset) noexcept {
  if (id < 0 || !store_slot || !*store_slot || !fallback_slot) return nullptr;
  auto *store = *store_slot;
  auto *slots = Load<void *>(store, 0x20);
  auto capacity = Load<std::int32_t>(store, 0x2C);
  auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFF;
  if (!slots || capacity <= 0 || index >= static_cast<std::uint32_t>(capacity))
    return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && object != *fallback_slot &&
                 Load<std::int32_t>(object, identity_offset) == id
             ? object : nullptr;
}
bool IntSpanContains(const void *span, std::int32_t id, bool &output,
                     bool sorted) noexcept {
  output = false;
  if (id < 0) return false;
  auto *data = Load<void *>(span, 0);
  auto count = Load<std::int32_t>(span, 0xC);
  if (!ValidSpan(data, count)) return false;
  std::int32_t previous = -1;
  for (std::int32_t i = 0; i < count; ++i) {
    auto value = Load<std::int32_t>(data, static_cast<std::size_t>(i) * 4);
    if (sorted && (value < 0 || (i && value <= previous))) return false;
    previous = value;
    if (value == id) output = true;
  }
  return true;
}
struct VariableValue {
  bool present = false;
  std::uint16_t kind = 0;
  std::int64_t payload = 0;
};
bool FindVariable(void *context, std::int32_t id, VariableValue &output) noexcept {
  output = {};
  if (!context || id < 0) return false;
  auto *data = Load<void *>(context, 0x10);
  auto count = Load<std::int32_t>(context, 0x1C);
  if (!ValidSpan(data, count)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *row = static_cast<const std::byte *>(data) +
                static_cast<std::size_t>(i) * 0x20;
    if (Load<std::int32_t>(row, 8) != id) continue;
    if (output.present) return false;
    output = {true, Load<std::uint16_t>(row, 0x10),
              Load<std::int64_t>(row, 0x18)};
  }
  return true;
}
void *VariableContext(const PhaseMiscBindings &b, std::int32_t id) noexcept {
  if (id < 0 || !b.identifiers.variable_context) return nullptr;
  const PhaseVariableTarget target{4, {}, id};
  return b.identifiers.variable_context(&target);
}
bool CharacterVariable(const PhaseMiscBindings &b, void *context,
                       std::int32_t id, game::OptionalFullIdV3 &output) noexcept {
  output = {};
  VariableValue value;
  if (!FindVariable(context, id, value)) return false;
  if (!value.present) return true;
  if (value.kind != 4 || value.payload <= 0 ||
      value.payload > std::numeric_limits<std::int32_t>::max()) return false;
  auto full_id = static_cast<std::int32_t>(value.payload);
  if (!Resolve(b.character_store, b.character_fallback, full_id, 0x18))
    return false;
  output = {true, full_id};
  return true;
}
bool ReadVariables(const PhaseMiscBindings &b,
                   const PhaseMiscDefinitionContext &d, void *character,
                   game::CombatPhaseCharacterV3 &out) noexcept {
  auto *context = VariableContext(b, out.character_id);
  VariableValue value;
  if (!FindVariable(context, d.conqueror_variable_id, value)) return false;
  out.conqueror_variable_present = value.present;
  out.attribute_unlock_variables.clear();
  for (const auto &entry : d.attribute_variable_ids) {
    if (!FindVariable(context, static_cast<std::int32_t>(entry.value), value))
      return false;
    out.attribute_unlock_variables.push_back({entry.key, value.present});
  }
  if (!CharacterVariable(b, context, d.hold_court_knight_variable_id,
                         out.hold_court_8050_knight)) return false;
  out.employer_hold_court_8050_promise = {};
  if (out.employer.present &&
      !CharacterVariable(b, VariableContext(b, out.employer.value),
                         d.hold_court_promise_variable_id,
                         out.employer_hold_court_8050_promise)) return false;
  out.liege_accolade_progress_raw = 0;
  if (out.liege.present) {
    auto *liege = Resolve(b.character_store, b.character_fallback,
                          out.liege.value, 0x18);
    if (!liege) return false;
    // The 1.20 accolade_progress script value requires is_alive before
    // evaluating has_variable/var; a dead liege's saved value is ignored.
    if (!Load<void *>(liege, kPhaseMiscCharacterDeathDataOffset)) {
      if (!FindVariable(VariableContext(b, out.liege.value),
                        d.accolade_progress_variable_id, value)) return false;
      if (value.present) {
        if (value.kind != 1) return false;
        out.liege_accolade_progress_raw =
            std::min<std::int64_t>(value.payload, 2'000'000);
      }
    }
  }
  out.ai_extreme_conqueror_modifier = false;
  auto *extension = Load<void *>(character, kPhaseMiscCharacterExtensionOffset);
  if (!extension) return true;
  auto *data = Load<void *>(extension, 0x188);
  auto count = Load<std::int32_t>(extension, 0x194);
  if (!ValidSpan(data, count)) return false;
  for (std::int32_t i = 0; i < count; ++i)
    if (Load<void *>(data, static_cast<std::size_t>(i) * 0x48) ==
        d.extreme_conqueror_modifier) out.ai_extreme_conqueror_modifier = true;
  return true;
}
bool ReadAccolade(const PhaseMiscBindings &b,
                  const PhaseMiscDefinitionContext &d, void *character,
                  game::CombatPhaseCharacterV3 &out) noexcept {
  out.accolade = {};
  out.is_acclaimed = false;
  out.accolade_has_men_at_arms_category = false;
  out.accolade_parameters.clear();
  auto *extension = Load<void *>(character, kPhaseMiscCharacterExtensionOffset);
  auto id = extension ? Load<std::int32_t>(extension, kPhaseMiscAccoladeIdOffset)
                      : -1;
  if (id != -1) {
    auto *accolade = Resolve(b.accolade_store, b.accolade_fallback, id, 8);
    if (!accolade || Load<std::uint32_t>(accolade, 0xC) != 0x4163636F)
      return false;
    // CIsAcclaimedTrigger 0x2AFB700 checks Acco magic + full ID. Its
    // CAccolade primary vtable has no boolean function at +8 in this build.
    out.accolade = {true, id};
    out.is_acclaimed = true;
    auto *rows = Load<void *>(accolade, 0x58);
    auto count = Load<std::int32_t>(accolade, 0x64);
    if (!ValidSpan(rows, count)) return false;
    for (std::int32_t i = 0; i < count; ++i) {
      auto *attribute = Load<void *>(rows, static_cast<std::size_t>(i) * 0x18 + 0x10);
      // Native HasAccoladeCategory/HasParameter both validate GDbO.
      if (!attribute || Load<std::uint32_t>(attribute, 0x38) != 0x4744624F)
        return false;
      bool has_category = false;
      if (!IntSpanContains(static_cast<const std::byte *>(attribute) +
                               kPhaseMiscAccoladeCategoriesOffset,
                           d.men_at_arms_category_id, has_category, false))
        return false;
      out.accolade_has_men_at_arms_category |= has_category;
    }
    for (const auto &entry : d.accolade_parameter_ids)
      out.accolade_parameters.push_back({entry.key,
          b.accolade_has_parameter(accolade, static_cast<std::int32_t>(entry.value))});
  } else {
    for (const auto &entry : d.accolade_parameter_ids)
      out.accolade_parameters.push_back({entry.key, false});
  }
  out.can_be_acclaimed = b.can_be_acclaimed(character, nullptr, nullptr);
  return true;
}
bool ReadCourtPosition(const PhaseMiscBindings &b,
                        const PhaseMiscDefinitionContext &d, void *character,
                        game::CombatPhaseCharacterV3 &out) noexcept {
  out.garuda_court_position = false;
  auto *relations = Load<void *>(character, kPhaseMiscCharacterRelationsOffset);
  if (!relations) return true;
  auto *ids = Load<void *>(relations, 0xD0);
  auto count = Load<std::int32_t>(relations, 0xDC);
  if (!ValidSpan(ids, count)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto id = Load<std::int32_t>(ids, static_cast<std::size_t>(i) * 4);
    auto *position = Resolve(b.court_position_store, b.court_position_fallback, id, 8);
    if (!position) return false;
    auto *type = Load<void *>(position, 0x110);
    if (!type) return false;
    if (type == d.garuda_court_position_type) out.garuda_court_position = true;
  }
  return true;
}
} // namespace

PhaseMiscBindings BindPhaseMiscImage(std::uintptr_t base,
                                    std::string_view hash) noexcept {
  PhaseMiscBindings b;
  if (!base || hash != kExecutableSha256) return b;
  b.enabled = true;
  b.identifiers = BindPhaseDefinitionsImage(base, hash);
  b.character_store = reinterpret_cast<void **>(base + kPhaseMiscCharacterStoreSlot);
  b.character_fallback = reinterpret_cast<void **>(base + kPhaseMiscCharacterFallbackSlot);
  b.accolade_store = reinterpret_cast<void **>(base + kPhaseMiscAccoladeStoreSlot);
  b.accolade_fallback = reinterpret_cast<void **>(base + kPhaseMiscAccoladeFallbackSlot);
  b.court_position_store = reinterpret_cast<void **>(base + kPhaseMiscCourtPositionStoreSlot);
  b.court_position_fallback = reinterpret_cast<void **>(base + kPhaseMiscCourtPositionFallbackSlot);
  b.court_type_database = reinterpret_cast<void **>(base + kPhaseMiscCourtTypeDatabaseSlot);
  b.court_type_fallback = reinterpret_cast<void **>(base + kPhaseMiscCourtTypeFallbackSlot);
  b.modifier_database = reinterpret_cast<void **>(base + kPhaseMiscModifierDatabaseSlot);
  b.modifier_fallback = reinterpret_cast<void **>(base + kPhaseMiscModifierFallbackSlot);
  b.lookup_modifier = reinterpret_cast<PhaseMiscLookupDefinition>(base + kPhaseMiscModifierLookupRva);
  b.can_be_acclaimed = reinterpret_cast<PhaseMiscCanBeAcclaimed>(base + kPhaseMiscCanBeAcclaimedRva);
  b.accolade_has_parameter = reinterpret_cast<PhaseMiscAccoladeHasParameter>(base + kPhaseMiscAccoladeHasParameterRva);
  b.character_government = reinterpret_cast<PhaseMiscCharacterGovernment>(base + kPhaseMiscCharacterGovernmentRva);
  return b;
}

bool BuildPhaseMiscDefinitions(const PhaseMiscBindings &b,
                               PhaseMiscDefinitionContext &output) noexcept {
  output = {};
  if (!b.enabled || !b.identifiers.enabled || !b.modifier_database ||
      !*b.modifier_database || !b.modifier_fallback || !b.lookup_modifier ||
      !b.identifiers.hash_rule_key || !b.court_type_database ||
      !*b.court_type_database || !b.court_type_fallback) return false;
  PhaseMiscDefinitionContext d;
  constexpr std::string_view key = "ai_extreme_conqueror_modifier";
  auto *database = *b.modifier_database;
  auto hash = b.identifiers.hash_rule_key(database, key.data(),
                                        static_cast<std::uint32_t>(key.size()));
  d.extreme_conqueror_modifier = b.lookup_modifier(database, hash);
  if (!d.extreme_conqueror_modifier ||
      d.extreme_conqueror_modifier == *b.modifier_fallback ||
      !KeyEquals(d.extreme_conqueror_modifier, key)) return false;
  database = *b.court_type_database;
  auto *rows = Load<void *>(database, kPhaseMiscDatabaseObjectsOffset);
  auto count = Load<std::int32_t>(database, kPhaseMiscDatabaseCountOffset);
  if (!ValidSpan(rows, count)) return false;
  for (std::int32_t i = 0; i < count; ++i) {
    auto *type = Load<void *>(rows, static_cast<std::size_t>(i) * 8);
    if (!KeyEquals(type, "garuda_court_position")) continue;
    if (d.garuda_court_position_type || type == *b.court_type_fallback) return false;
    d.garuda_court_position_type = type;
  }
  if (!d.garuda_court_position_type) return false;
  if (!ResolvePhaseScriptIdentifier(b.identifiers, "government_is_nomadic",
                                    d.government_is_nomadic_id)) return false;
  auto variable = [&](std::string_view name, std::int32_t &id) {
    return ResolvePhaseVariableIdentifier(b.identifiers, name, id);
  };
  if (!variable("men_at_arms", d.men_at_arms_category_id) ||
      !variable("conqueror", d.conqueror_variable_id) ||
      !variable("hold_court_8050_knight", d.hold_court_knight_variable_id) ||
      !variable("hold_court_8050_promise", d.hold_court_promise_variable_id) ||
      !variable("accolade_progress", d.accolade_progress_variable_id)) return false;
  constexpr std::array<std::string_view, 13> attribute_keys{
      "skirmisher", "archer", "crossbowmen", "pike", "vanguard", "outrider",
      "lancer", "camelry", "elephantry", "horse_archer", "gunpowder", "fanatic", "valiant"};
  for (auto short_key : attribute_keys) {
    std::int32_t id = -1;
    if (!variable(std::string(short_key) + "_attribute_unlock", id)) return false;
    d.attribute_variable_ids.push_back({std::string(short_key), id});
  }
  constexpr std::array<std::string_view, 6> parameter_keys{
      "accolade_defends_family_low", "accolade_defends_family_medium",
      "accolade_defends_family_high", "accolade_increase_hostile_knight_death_low",
      "accolade_increase_hostile_knight_death_medium",
      "accolade_increase_hostile_knight_death_high"};
  for (auto parameter : parameter_keys) {
    std::int32_t id = -1;
    if (!variable(parameter, id)) return false;
    d.accolade_parameter_ids.push_back({std::string(parameter), id});
  }
  output = std::move(d);
  return true;
}

bool ReadPhaseCharacterMisc(const PhaseMiscBindings &b,
                            const PhaseMiscDefinitionContext &d,
                            void *character,
                            game::CombatPhaseCharacterV3 &out) noexcept {
  if (!b.enabled || !character || out.character_id < 0 ||
      Load<std::int32_t>(character, 0x18) != out.character_id ||
      !d.extreme_conqueror_modifier || !d.garuda_court_position_type ||
      !b.can_be_acclaimed || !b.accolade_has_parameter ||
      !b.character_government || d.attribute_variable_ids.size() != 13 ||
      d.accolade_parameter_ids.size() != 6) return false;
  if (!ReadVariables(b, d, character, out) || !ReadAccolade(b, d, character, out))
    return false;
  auto *government = b.character_government(character);
  if (!government ||
      !IntSpanContains(static_cast<const std::byte *>(government) +
                           kPhaseMiscGovernmentFlagsOffset,
                       d.government_is_nomadic_id, out.government_is_nomadic, true))
    return false;
  return ReadCourtPosition(b, d, character, out);
}
bool ReadPhaseCharacterMisc(const PhaseMiscBindings &b, void *character,
                            game::CombatPhaseCharacterV3 &out) noexcept {
  PhaseMiscDefinitionContext definitions;
  return BuildPhaseMiscDefinitions(b, definitions) &&
         ReadPhaseCharacterMisc(b, definitions, character, out);
}
} // namespace xar::ck3_12002

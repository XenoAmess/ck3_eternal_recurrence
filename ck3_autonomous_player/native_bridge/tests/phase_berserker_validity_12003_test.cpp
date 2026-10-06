#include "xar_bridge/ck3_12003_phase_berserker_validity_inputs.hpp"
#include "xar_bridge/phase_berserker_validity_inputs_v1_serializer.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>

namespace {
template <std::size_t N> struct Object {
  alignas(std::max_align_t) std::array<std::byte, N> data{};
  void *get() { return data.data(); }
};
template <typename T> void Store(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
struct Definition {
  Object<0x40> object;
  std::string key;
  void Set(std::string value) {
    key = std::move(value);
    std::memset(static_cast<std::byte *>(object.get()) + 0x18, 0, 0x20);
    if (key.size() < 16) std::memcpy(static_cast<std::byte *>(object.get()) + 0x18, key.data(), key.size());
    else Store(object.get(), 0x18, key.data());
    Store(object.get(), 0x28, static_cast<std::uint64_t>(key.size()));
    Store(object.get(), 0x30, static_cast<std::uint64_t>(key.size() < 16 ? 15 : key.size()));
  }
};
void *returned_rite = nullptr, *returned_faith = nullptr, *returned_religion = nullptr;
void *expected_character = nullptr;
unsigned trait_calls = 0;
void *GetRite(void *character) { Check(character == expected_character, "Rite source must be this knight"); return returned_rite; }
void *GetCharacterFaith(void *character) { Check(character == expected_character, "Faith source must be this knight"); return returned_faith; }
void *GetRiteFaith(void *) { return returned_faith; }
void *GetReligion(void *) { return returned_religion; }
bool HasTrait(void *character, const void *definition) {
  Check(character == expected_character, "presence receiver must be the concrete knight");
  ++trait_calls;
  const auto id = xar::ck3_12003::phase_berserker::Load<std::int32_t>(definition, 0x10);
  const auto *ids = xar::ck3_12003::phase_berserker::Load<const std::int32_t *>(character, 0xF8);
  const auto count = xar::ck3_12003::phase_berserker::Load<std::int32_t>(character, 0x104);
  for (std::int32_t index = 0; index < count; ++index) if (ids[index] == id) return true;
  return false;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Object<0x120> character;
    Object<0x40> culture, culture_storage, culture_slots, culture_fallback;
    Object<0x140> culture_template;
    Object<0x80> resolved;
    Object<0x4D0> rite, rite_fallback;
    Object<0xA0> faith;
    Object<0x30> religion;
    Object<0x70> trait_database;
    std::array<Definition, 5> pillar_definitions;
    std::array<Definition, 3> trait_definitions;
    Definition religion_definition;
    std::array<void *, 5> pillars{};
    std::array<void *, 3> traits{};
    std::array<std::int32_t, 1> present_ids{};
    const std::array<std::string, 5> selected_keys{
        "heritage_north_germanic", "ethos_bellicose", "language_norse", "martial_custom_male_only", "naming_list_norse"};
    for (std::size_t index = 0; index < pillars.size(); ++index) {
      pillar_definitions[index].Set(selected_keys[index]); pillars[index] = pillar_definitions[index].object.get();
    }
    for (std::size_t index = 0; index < traits.size(); ++index) {
      trait_definitions[index].Set(std::string(xar::ck3_12003::phase_berserker::kTraitKeys[index]));
      Store(trait_definitions[index].object.get(), 0x10, static_cast<std::int32_t>(501 + index));
      traits[index] = trait_definitions[index].object.get();
    }
    religion_definition.Set("christianity_religion");
    Store(character.get(), 0x18, std::uint32_t{77});
    Store(character.get(), 0xB0, std::uint32_t{0xE1000001});
    Store(character.get(), 0xB4, std::uint32_t{0xF1000001});
    Store(character.get(), 0xF8, present_ids.data());
    Store(character.get(), 0x104, std::int32_t{0});
    Store(culture_storage.get(), 0x20, culture_slots.get());
    Store(culture_storage.get(), 0x2C, std::uint32_t{2});
    Store(culture_slots.get(), 0x18, culture.get());
    Store(culture.get(), 0x10, std::uint32_t{0xE1000001});
    Store(culture.get(), 0x20, culture_template.get());
    Store(culture_template.get(), 0x128, resolved.get());
    Store(resolved.get(), 0x70, pillars.data());
    Store(rite.get(), 8, std::uint32_t{0xF1000001});
    Store(rite.get(), 0x4B8, std::uint32_t{0xD1000002});
    Store(faith.get(), 8, std::uint32_t{0xD1000002});
    Store(faith.get(), 0x8C, std::uint32_t{0xC1000003});
    Store(religion.get(), 8, std::uint32_t{0xC1000003});
    Store(religion.get(), 0x20, religion_definition.object.get());
    Store(trait_database.get(), 0x50, traits.data());
    Store(trait_database.get(), 0x5C, std::int32_t{3});
    void *culture_storage_slot = culture_storage.get(), *culture_fallback_slot = culture_fallback.get();
    void *trait_database_slot = trait_database.get(), *rite_fallback_slot = rite_fallback.get();
    returned_rite = rite.get(); returned_faith = faith.get(); returned_religion = religion.get();
    expected_character = character.get();
    xar::ck3_12003::phase_berserker::Bindings bindings{};
    bindings.enabled = true;
    bindings.culture_store = &culture_storage_slot; bindings.culture_fallback = &culture_fallback_slot;
    bindings.trait_database = &trait_database_slot; bindings.rite_fallback = &rite_fallback_slot;
    bindings.traits.enabled = true; bindings.traits.character_has_trait = HasTrait;
    bindings.character_rite = GetRite; bindings.character_faith = GetCharacterFaith;
    bindings.rite_faith = GetRiteFaith; bindings.faith_religion = GetReligion;
    std::vector<std::pair<std::string, xar::game::PhaseBerserkerValidityInputsV1>> samples;
    const auto record = [&](const char *name) {
      const auto leaf = xar::ck3_12003::phase_berserker::Read(bindings, character.get(), 77);
      Check(leaf.has_value(), "enabled knight must publish the additive leaf");
      samples.emplace_back(name, *leaf); return *leaf;
    };
    auto leaf = record("north_germanic_full_generation");
    Check(leaf.culture.heritage_north_germanic == true && leaf.religion.germanic == false &&
              leaf.culture.culture_id == 0xE1000001U && leaf.religion.faith_id == 0xD1000002U,
          "actual keys/full-generation source chain must survive");
    for (const auto &trait : leaf.traits) Check(trait.value == false, "empty actual owned trait IDs must give observed false");
    pillar_definitions[0].Set("heritage_other"); religion_definition.Set("germanic_religion");
    leaf = record("germanic_religion_other_heritage");
    Check(leaf.culture.heritage_north_germanic == false && leaf.religion.germanic == true, "OR sources must remain independent");
    religion_definition.Set("christianity_religion");
    leaf = record("neither_heritage_nor_religion");
    Check(leaf.culture.heritage_north_germanic == false && leaf.religion.germanic == false, "known nonmatching keys must give false");
    present_ids[0] = 501; Store(character.get(), 0x104, std::int32_t{1});
    leaf = record("craven_exclusion_present");
    Check(leaf.traits[0].value == true && leaf.traits[1].value == false && leaf.traits[2].value == false,
          "actual loaded ordinal must drive only the corresponding named trait");
    Store(character.get(), 0x104, std::int32_t{0});
    Store(character.get(), 0xB0, std::uint32_t{0xFFFFFFFF});
    leaf = record("native_culture_fallback");
    Check(leaf.culture.resolution == "native_fallback" && !leaf.culture.heritage_north_germanic &&
              leaf.culture.unavailable_reason == "native_fallback_heritage_unobserved" &&
              leaf.religion.germanic == false && leaf.traits[0].value == false,
          "actual Culture fallback must not discard other domains or become false");
    Store(character.get(), 0xB0, std::uint32_t{0xE1000001});
    pillar_definitions[0].Set("heritage_north_germanic");
    returned_rite = rite_fallback.get(); Store(character.get(), 0xB4, std::uint32_t{0xFFFFFFFF});
    leaf = record("native_rite_fallback");
    Check(leaf.religion.resolution == "native_fallback" && !leaf.religion.germanic &&
              leaf.religion.unavailable_reason == "native_fallback_religion_unobserved" &&
              leaf.culture.heritage_north_germanic == true && leaf.traits[0].value == false,
          "actual Rite fallback must preserve independent Culture and traits");
    returned_rite = rite.get(); Store(character.get(), 0xB4, std::uint32_t{0xF1000001});
    Store(trait_database.get(), 0x5C, std::int32_t{2});
    leaf = record("calm_definition_unresolved");
    Check(leaf.traits[0].value == false && leaf.traits[1].value == false && !leaf.traits[2].value &&
              leaf.traits[2].unavailable_reason == "trait_definition_unresolved" && leaf.culture.available,
          "one unresolved trait must remain independently nullable");
    Store(trait_database.get(), 0x5C, std::int32_t{3});
    Store(culture.get(), 0x20, static_cast<void *>(nullptr));
    Store(religion.get(), 0x20, static_cast<void *>(nullptr));
    present_ids[0] = 502; Store(character.get(), 0x104, std::int32_t{1});
    leaf = record("two_domain_failures_known_berserker");
    Check(!leaf.culture.heritage_north_germanic && !leaf.religion.germanic && leaf.traits[1].value == true,
          "Culture/Religion failure must not discard a known exclusion trait");
    Store(culture.get(), 0x20, culture_template.get()); Store(religion.get(), 0x20, religion_definition.object.get());
    Store(character.get(), 0x104, std::int32_t{0});
    Store(character.get(), 0xB0, std::uint32_t{0}); Store(culture.get(), 0x10, std::uint32_t{0});
    Store(culture_slots.get(), 8, culture.get());
    Store(character.get(), 0xB4, std::uint32_t{0}); Store(rite.get(), 8, std::uint32_t{0});
    Store(rite.get(), 0x4B8, std::uint32_t{0}); Store(faith.get(), 8, std::uint32_t{0});
    Store(faith.get(), 0x8C, std::uint32_t{0}); Store(religion.get(), 8, std::uint32_t{0});
    religion_definition.Set("germanic_religion");
    leaf = record("legal_zero_source_identities");
    Check(leaf.culture.culture_id == 0U && leaf.religion.rite_id == 0U && leaf.religion.faith_id == 0U &&
              leaf.religion.religion_id == 0U && leaf.religion.germanic == true,
          "zero source identities must remain legal values");
    Check(trait_calls == 26, "nine samples must use only the three concrete presence calls, with one unresolved key");
    Check(!xar::ck3_12003::phase_berserker::Read({}, character.get(), 77), "legacy unbound builds omit the leaf");
    Check(argc == 2, "supply the new fixture output directory");
    const std::filesystem::path directory{argv[1]}; std::filesystem::create_directories(directory);
    std::string wire = "{\"samples\":[";
    for (std::size_t index = 0; index < samples.size(); ++index) {
      if (index) wire += ',';
      wire += "{\"case\":\"" + samples[index].first + "\",\"phase_berserker_validity_inputs_v1\":";
      xar::game::AppendPhaseBerserkerValidityInputsV1(wire, samples[index].second); wire += '}';
    }
    wire += "]}";
    std::ofstream output(directory / "ck3_12003_phase_berserker_validity_inputs_wire.json", std::ios::binary);
    output << wire; Check(output.good(), "new native wire must be written");
    std::cout << "9 source-shaped remaining-validity samples; 1 JSON wire\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}

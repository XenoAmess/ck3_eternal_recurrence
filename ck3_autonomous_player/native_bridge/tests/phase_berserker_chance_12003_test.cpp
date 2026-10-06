#include "xar_bridge/ck3_12003_phase_berserker_chance_inputs.hpp"
#include "xar_bridge/phase_berserker_chance_inputs_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
template<std::size_t N> struct Object {
  alignas(std::max_align_t) std::array<std::byte, N> bytes{};
  void *get() { return bytes.data(); }
};
template<class T> void Store(void *object, std::size_t offset, const T &value) {
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
void *expected_character = nullptr;
bool human = false;
unsigned trait_calls = 0;
Object<0x10> empty_perks;
bool IsHuman(std::int32_t id) { Check(id == 77, "same full source CharacterID"); return human; }
bool HasTrait(void *character, const void *definition) {
  Check(character == expected_character, "trait presence receiver must be this knight");
  ++trait_calls;
  using xar::ck3_12003::phase_berserker_chance::Load;
  const auto *data = Load<const std::int32_t *>(character, 0xF8);
  const auto count = Load<std::int32_t>(character, 0x104);
  const auto wanted = Load<std::int32_t>(definition, 0x10);
  for (std::int32_t index = 0; index < count; ++index) if (data[index] == wanted) return true;
  return false;
}
void *CharacterPerks(void *character) {
  Check(character == expected_character, "owned perks receiver must be this knight");
  auto *extension = xar::ck3_12003::phase_berserker_chance::Load<std::byte *>(character, 0x1B0);
  return extension ? extension + 0x220 : empty_perks.get();
}
}

int main(int argc, char **argv) {
  try {
    Object<0x200> character;
    Object<0x580> extension;
    Object<0x40> house, accolade, house_fallback, dynasty_fallback, accolade_fallback;
    Object<0x190> dynasty;
    Object<0x40> house_storage, dynasty_storage, accolade_storage;
    Object<0x20> house_slots, dynasty_slots, accolade_slots;
    Object<0x70> trait_database, character_perk_database, dynasty_perk_database;
    std::array<Definition, 18> trait_definitions;
    std::array<void *, 18> traits{};
    Definition stalwart, warfare;
    stalwart.Set("stalwart_leader_perk"); warfare.Set("warfare_legacy_3");
    std::array<void *, 1> stalwart_definitions{stalwart.object.get()}, warfare_definitions{warfare.object.get()};
    std::array<std::int32_t, 18> present_traits{};
    for (std::size_t index = 0; index < traits.size(); ++index) {
      trait_definitions[index].Set(std::string(xar::game::kPhaseBerserkerChanceTraitKeysV1[index]));
      Store(trait_definitions[index].object.get(), 0x10, static_cast<std::int32_t>(801 + index));
      traits[index] = trait_definitions[index].object.get();
    }
    Store(character.get(), 0x18, std::uint32_t{77}); Store(character.get(), 0x1C, std::uint32_t{0x43686172});
    Store(character.get(), 0x158, std::uint32_t{0xE1000001}); Store(character.get(), 0x1B0, extension.get());
    Store(character.get(), 0xF8, present_traits.data());
    Store(house.get(), 0x10, std::uint32_t{0xE1000001}); Store(house.get(), 0x2C, std::uint32_t{0xF1000001});
    Store(dynasty.get(), 0x10, std::uint32_t{0xF1000001});
    Store(accolade.get(), 8, std::uint32_t{0xC1000001}); Store(accolade.get(), 0xC, std::uint32_t{0x4163636F});
    Store(extension.get(), 0x570, std::uint32_t{0xFFFFFFFF});
    Store(extension.get(), 0x220, stalwart_definitions.data()); Store(extension.get(), 0x22C, std::int32_t{0});
    Store(dynasty.get(), 0x178, warfare_definitions.data()); Store(dynasty.get(), 0x184, std::int32_t{0});
    const auto storage = [&](void *store, void *slots, void *object) {
      Store(store, 0x20, slots); Store(store, 0x2C, std::uint32_t{2});
      Store(slots, 0x18, object); Store(slots, 8, object);
    };
    storage(house_storage.get(), house_slots.get(), house.get());
    storage(dynasty_storage.get(), dynasty_slots.get(), dynasty.get());
    storage(accolade_storage.get(), accolade_slots.get(), accolade.get());
    Store(trait_database.get(), 0x50, traits.data()); Store(trait_database.get(), 0x5C, std::int32_t{18});
    Store(character_perk_database.get(), 0x50, stalwart_definitions.data()); Store(character_perk_database.get(), 0x5C, std::int32_t{1});
    Store(dynasty_perk_database.get(), 0x50, warfare_definitions.data()); Store(dynasty_perk_database.get(), 0x5C, std::int32_t{1});
    void *trait_slot = trait_database.get(), *perk_slot = character_perk_database.get(), *warfare_slot = dynasty_perk_database.get();
    void *house_store = house_storage.get(), *dynasty_store = dynasty_storage.get(), *accolade_store = accolade_storage.get();
    void *house_fb = house_fallback.get(), *dynasty_fb = dynasty_fallback.get(), *accolade_fb = accolade_fallback.get();
    xar::ck3_12003::phase_berserker_chance::Bindings bindings{};
    bindings.enabled = true; bindings.character.enabled = true;
    bindings.character.character_has_trait = HasTrait; bindings.character.is_human_player_character = IsHuman;
    bindings.trait_database = &trait_slot; bindings.character_perk_database = &perk_slot; bindings.dynasty_perk_database = &warfare_slot;
    bindings.house_store = &house_store; bindings.house_fallback = &house_fb;
    bindings.dynasty_store = &dynasty_store; bindings.dynasty_fallback = &dynasty_fb;
    bindings.accolade_store = &accolade_store; bindings.accolade_fallback = &accolade_fb;
    bindings.character_perks = CharacterPerks; expected_character = character.get();
    std::vector<std::pair<std::string, xar::game::PhaseBerserkerChanceInputsV1>> samples;
    const auto record = [&](const char *name) {
      auto value = xar::ck3_12003::phase_berserker_chance::Read(bindings, character.get(), 77);
      Check(value.has_value(), "enabled source publishes the new chance leaf"); samples.emplace_back(name, *value); return *value;
    };
    auto leaf = record("known_empty_ai");
    Check(leaf.is_ai.value == true && leaf.stalwart.presence.value == false &&
          leaf.dynasty.warfare_legacy_3.presence.value == false && leaf.acclaimed.is_acclaimed.value == false, "known empty domains are observed false");
    human = true; Store(extension.get(), 0x22C, std::int32_t{1}); Store(dynasty.get(), 0x184, std::int32_t{1});
    Store(extension.get(), 0x570, std::uint32_t{0xC1000001});
    present_traits[0] = 801; present_traits[1] = 802; present_traits[2] = 811; Store(character.get(), 0x104, std::int32_t{3});
    leaf = record("player_stalwart_bonuses");
    Check(leaf.is_ai.value == false && leaf.stalwart.presence.value == true && leaf.dynasty.warfare_legacy_3.presence.value == true &&
          leaf.acclaimed.is_acclaimed.value == true && leaf.traits[0].value == true && leaf.traits[10].value == true, "actual root perks/traits and accolade must be distinct known inputs");
    human = false; present_traits[0] = 813; present_traits[1] = 815; present_traits[2] = 816;
    leaf = record("ai_stalwart_wounded2_maim");
    Check(leaf.is_ai.value == true && leaf.traits[12].value == true && leaf.traits[14].value == true && leaf.traits[15].value == true, "wound and multiple maim operands stay raw independent presence");
    Store(character.get(), 0x158, std::uint32_t{0}); Store(house.get(), 0x10, std::uint32_t{0});
    Store(house.get(), 0x2C, std::uint32_t{0}); Store(dynasty.get(), 0x10, std::uint32_t{0});
    Store(extension.get(), 0x570, std::uint32_t{0}); Store(accolade.get(), 8, std::uint32_t{0});
    leaf = record("legal_zero_root_refs");
    Check(leaf.dynasty.house_id == 0U && leaf.dynasty.dynasty_id == 0U && leaf.acclaimed.accolade_id == 0U, "legal zero refs survive all three identity domains");
    Store(character.get(), 0x158, std::uint32_t{0xFFFFFFFF}); Store(character.get(), 0x1B0, static_cast<void *>(nullptr));
    Store(character.get(), 0x104, std::int32_t{0});
    leaf = record("legal_missing_house_accolade");
    Check(leaf.dynasty.house_resolution == "absent" && leaf.dynasty.warfare_legacy_3.presence.value == false &&
          leaf.acclaimed.resolution == "absent" && leaf.acclaimed.is_acclaimed.value == false && leaf.stalwart.presence.value == false, "actual absent source and canonical empty perks are known false");
    Store(character.get(), 0x158, std::uint32_t{0xE1000001}); Store(house.get(), 0x10, std::uint32_t{0xE1000001});
    Store(house.get(), 0x2C, std::uint32_t{0xF1000001}); Store(dynasty.get(), 0x10, std::uint32_t{0xF1000001});
    Store(character.get(), 0x1B0, extension.get()); Store(extension.get(), 0x570, std::uint32_t{0xC1000001});
    Store(accolade.get(), 8, std::uint32_t{0xC1000001});
    Store(character_perk_database.get(), 0x5C, std::int32_t{0});
    leaf = record("stalwart_definition_unresolved");
    Check(!leaf.stalwart.presence.value && leaf.is_ai.value == true && leaf.acclaimed.is_acclaimed.value == true, "missing one definition cannot discard other domains");
    Store(character_perk_database.get(), 0x5C, std::int32_t{1}); Store(trait_database.get(), 0x5C, std::int32_t{17});
    leaf = record("one_trait_definition_unresolved");
    Check(!leaf.traits[17].value && leaf.traits[0].value == false && leaf.stalwart.presence.value == true, "one unresolved named trait is not false");
    Store(trait_database.get(), 0x5C, std::int32_t{18}); Store(character.get(), 0x158, std::uint32_t{0xE2000001});
    Store(accolade.get(), 0xC, std::uint32_t{0});
    leaf = record("stale_house_wrong_accolade_kind");
    Check(!leaf.dynasty.warfare_legacy_3.presence.value && !leaf.acclaimed.is_acclaimed.value && leaf.traits[0].value == false, "stale generation and wrong kind remain independent unavailable");
    Store(character.get(), 0x158, std::uint32_t{0xE1000001}); Store(accolade.get(), 0xC, std::uint32_t{0x4163636F});
    present_traits[0] = 812; present_traits[1] = 813; Store(character.get(), 0x104, std::int32_t{2});
    leaf = record("multiple_wounded_flags");
    Check(leaf.traits[11].value == true && leaf.traits[12].value == true, "do not collapse actual multiple raw wound operands in native leaf");
    Store(character.get(), 0x104, std::int32_t{0}); bindings.character.is_human_player_character = nullptr;
    leaf = record("identity_unavailable_other_domains_known");
    Check(!leaf.is_ai.value && leaf.stalwart.presence.value == true && leaf.dynasty.warfare_legacy_3.presence.value == true && leaf.acclaimed.is_acclaimed.value == true,
          "identity failure preserves other source reads");
    Check(trait_calls == 179, "ten samples use eighteen actual presence calls except one unresolved definition");
    Check(!xar::ck3_12003::phase_berserker_chance::Read({}, character.get(), 77), "old unbound producer omits leaf");
    Check(argc == 2, "supply new output directory");
    const std::filesystem::path directory{argv[1]}; std::filesystem::create_directories(directory);
    std::string wire = "{\"samples\":[";
    for (std::size_t index = 0; index < samples.size(); ++index) {
      if (index) wire += ',';
      wire += "{\"case\":\"" + samples[index].first + "\",\"phase_berserker_chance_inputs_v1\":";
      xar::game::AppendPhaseBerserkerChanceInputsV1(wire, samples[index].second); wire += '}';
    }
    wire += "]}";
    std::ofstream output(directory / "ck3_12003_phase_berserker_chance_inputs_wire.json", std::ios::binary);
    output << wire; Check(output.good(), "new chance wire written");
    std::cout << "10 new chance input samples; 1 JSON\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}

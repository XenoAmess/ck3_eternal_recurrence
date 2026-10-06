#include "xar_bridge/ck3_12003_phase_warmonger_core.hpp"
#include "xar_bridge/phase_warmonger_core_v1_serializer.hpp"

#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

namespace {
template <std::size_t Size> struct Object {
  alignas(std::max_align_t) std::array<std::byte, Size> bytes{};
  void *get() { return bytes.data(); }
};
template <typename T> void Store(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *returned_rite = nullptr;
const void *expected_core = nullptr;
const void *expected_target = nullptr;
unsigned contains_calls = 0;
void *GetRite(void *) { return returned_rite; }
bool Contains(const void *core, const void *target_slot) {
  Require(core == expected_core, "predicate receiver must be the adopted Rite Core");
  const auto *target = xar::ck3_12003::phase_warmonger::Load<const void *>(target_slot, 0);
  Require(target == expected_target, "predicate RHS must be the loaded warmonger definition");
  ++contains_calls;
  const auto *rows = xar::ck3_12003::phase_warmonger::Load<const void *const *>(core, 0);
  const auto count = xar::ck3_12003::phase_warmonger::Load<std::int32_t>(core, 0xC);
  for (std::int32_t i = 0; i < count; ++i) if (rows[i] == target) return true;
  return false;
}
void Definition(void *object, std::string_view key) {
  Require(key.size() < 16, "fixture key must use the real CString SSO layout");
  std::memcpy(static_cast<std::byte *>(object) + 0x18, key.data(), key.size());
  Store(object, 0x28, static_cast<std::uint64_t>(key.size()));
  Store(object, 0x30, std::uint64_t{15});
  Store(object, 0x38, std::uint32_t{0x4744624F});
}
} // namespace

int main(int argc, char **argv) {
  try {
    using xar::ck3_12003::phase_warmonger::Bindings;
    using xar::ck3_12003::phase_warmonger::Read;
    Object<0xC0> character;
    Object<0x7D0> rite;
    Object<0x7D0> fallback;
    Object<0xF10> database;
    Object<0x40> warmonger;
    Object<0x40> other;
    Definition(warmonger.get(), "tenet_warmonger");
    Definition(other.get(), "tenet_other");
    void *database_slot = database.get();
    void *fallback_slot = fallback.get();
    std::array<const void *, 2> definitions{other.get(), warmonger.get()};
    std::array<const void *, 1> core{warmonger.get()};
    Store(database.get(), 0xEF0, definitions.data());
    Store(database.get(), 0xEFC, std::int32_t{2});
    Store(character.get(), 0x18, std::uint32_t{77});
    Store(character.get(), 0xB4, std::uint32_t{0xF1000001});
    Store(rite.get(), 8, std::uint32_t{0xF1000001});
    Store(rite.get(), 0x758, core.data());
    Store(rite.get(), 0x764, std::int32_t{1});
    returned_rite = rite.get();
    expected_core = static_cast<std::byte *>(rite.get()) + 0x758;
    expected_target = warmonger.get();
    const Bindings bindings{true, GetRite, &database_slot, &fallback_slot, Contains};
    std::vector<std::pair<std::string, xar::game::PhaseWarmongerCoreV1>> samples;
    const auto record = [&](const char *name) -> xar::game::PhaseWarmongerCoreV1 {
      const auto result = Read(bindings, character.get(), 77);
      Require(result.has_value(), "enabled knight occurrence must publish the optional leaf");
      samples.emplace_back(name, *result);
      return *result;
    };

    auto leaf = record("core_present_full_generation");
    Require(leaf.available && leaf.warmonger_core_membership == true, "Core pointer membership must be true");
    Require(leaf.rite_id == 0xF1000001U, "full-generation Rite reference must survive");
    core[0] = other.get();
    // A separate Boolean carrier cannot supply the Core membership operand.
    Store(rite.get(), 0x7B8, warmonger.get());
    Store(rite.get(), 0x7C4, std::int32_t{1});
    leaf = record("core_absent_boolean_carrier_present");
    Require(leaf.available && leaf.warmonger_core_membership == false, "Boolean carrier must not replace Core absence");
    Store(character.get(), 0xB4, std::uint32_t{0});
    Store(rite.get(), 8, std::uint32_t{0});
    Store(rite.get(), 0x758, static_cast<const void *>(nullptr));
    Store(rite.get(), 0x764, std::int32_t{0});
    leaf = record("core_known_empty_rite_zero");
    Require(leaf.available && leaf.rite_id == 0U && leaf.warmonger_core_membership == false,
            "known empty Core and legal Rite zero must survive");
    Require(contains_calls == 3, "all three resolved Core samples must use the exact predicate receiver");

    Store(character.get(), 0xB4, std::uint32_t{0xFFFFFFFF});
    returned_rite = fallback.get();
    leaf = record("native_fallback");
    Require(!leaf.available && !leaf.rite_id && !leaf.warmonger_core_membership &&
                leaf.rite_resolution == "native_fallback" &&
                leaf.unavailable_reason == "native_fallback_core_membership_unobserved",
            "actual native fallback must remain null with its reason");
    returned_rite = rite.get();
    Store(character.get(), 0xB4, std::uint32_t{0});
    Store(database.get(), 0xEFC, std::int32_t{1});
    leaf = record("target_definition_unresolved");
    Require(!leaf.available && !leaf.target_tenet_key && !leaf.warmonger_core_membership &&
                leaf.unavailable_reason == "warmonger_definition_unresolved",
            "unresolved loaded target must remain null");
    Store(other.get(), 0x38, std::uint32_t{0});
    leaf = record("definition_key_unavailable");
    Require(!leaf.available && leaf.unavailable_reason == "tenet_definition_key_unavailable",
            "key copier failure must preserve its real cause");
    Store(other.get(), 0x38, std::uint32_t{0x4744624F});
    Store(database.get(), 0xEFC, std::int32_t{2});
    Store(rite.get(), 0x764, std::int32_t{1});
    leaf = record("core_collection_unavailable");
    Require(!leaf.available && leaf.target_tenet_key == "tenet_warmonger" &&
                leaf.unavailable_reason == "core_tenet_collection_unavailable",
            "unreadable Core must not turn into false");
    Require(contains_calls == 3, "fallback and unresolved inputs must not call a guessed receiver");
    Require(!Read(Bindings{}, character.get(), 77), "legacy unbound builds omit the additive leaf");

    Require(argc == 2, "supply the new fixture output directory");
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    std::string wire = "{\"samples\":[";
    for (std::size_t i = 0; i < samples.size(); ++i) {
      if (i) wire += ',';
      wire += "{\"case\":\"" + samples[i].first + "\",\"phase_warmonger_core_v1\":";
      xar::game::AppendPhaseWarmongerCoreV1(wire, samples[i].second);
      wire += '}';
    }
    wire += "]}";
    std::ofstream output(directory / "ck3_12003_phase_warmonger_core_wire.json", std::ios::binary);
    output << wire;
    Require(output.good(), "new fixture wire must be written");
    std::cout << "7 source-shaped warmonger samples; 1 JSON wire\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

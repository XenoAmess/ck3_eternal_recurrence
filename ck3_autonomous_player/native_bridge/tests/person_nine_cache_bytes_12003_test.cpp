#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_current_person_state_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12002;
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class T, std::size_t N> void Put(Bytes<N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
std::int32_t ZeroCategory(void *) { return 0; }
struct Fixture {
  Bytes<0xA8> gs{}, js{};
  Bytes<0x38> storage{}, carrier{};
  Bytes<0x20> slots{};
  Bytes<0x210> character{};
  Bytes<0x448> scratch{};
  Bytes<0x230> model{}, fallback_model{};
  Bytes<0x240> linked{};
  Bytes<0x328> definition{};
  std::array<std::uint16_t, 2> property_keys{0x225, 0x22A};
  std::array<std::int64_t, 2> property_values{-99999, 300000};
  std::array<std::uint16_t, 9> selected_keys{0x225, 0xFFFF, 0x22A, 0xFFFF, 0x225,
                                          0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF};
  std::array<std::int8_t, 9> cache{127,-128,0,1,-1,100,-100,2,-2};
  void *game_state = gs.data(), *jomini = js.data(), *characters = storage.data();
  void *fallback_definition = definition.data();
  std::int32_t cap = 100, denominator = 100;
  BattleBindings bindings{};
  xar::game::Snapshot scope{};
  Fixture() {
    scope.paused = scope.map_ready = scope.has_played_character = true;
    scope.played_character_id = 0x1000001;
    scope.date_raw = 53265168;
    Put(gs, 8, scope.date_raw);
    Put<std::uint8_t>(js, 0x20, 1);
    Put(storage, 0x20, slots.data());
    Put<std::int32_t>(storage, 0x2C, 2);
    Put(slots, 0x18, character.data());
    Put(character, 0x18, scope.played_character_id);
    Put<std::uint32_t>(character, 0x1C, 0x43686172U);
    Put(character, 0x1B0, scratch.data());
    Put(scratch, 0x258, model.data());
    // Deliberate owner mismatch: AE0 raw context falls back,2949010 does not.
    Put<void *>(model, 8, nullptr);
    Put(model, 0x78, property_keys.data());
    Put<std::int32_t>(model, 0x84, 2);
    Put(model, 0xE0, property_values.data());
    Put(scratch, 0x278, carrier.data());
    Put(scratch, 0x310, cache.data());
    Put(carrier, 0x20, linked.data());
    Put<std::uint32_t>(carrier, 0x28, 0x41495374U);
    Put(linked, 0x238, definition.data());
    Put<std::uint32_t>(definition, 0x38, 0x4744624FU);
    for (std::size_t i = 0; i < 9; ++i) Put(definition, 0x312 + i * 2, selected_keys[i]);
    bindings.enabled = bindings.current_person_state_enabled = true;
    bindings.current_person_raw_numeric_inputs_enabled = true;
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini;
    bindings.character_storage_slot = &characters;
    bindings.current_person_raw_skill_caps.fill(&cap);
    bindings.current_person_raw_factor_denominator = &denominator;
    bindings.current_person_raw_category_getters.fill(ZeroCategory);
    bindings.current_person_raw_fallback_context = fallback_model.data() + 0x10;
    bindings.current_person_nine_cache_definition_fallback_slot = &fallback_definition;
  }
  xar::game::BattleCurrentPersonRawNumericInputsSnapshotV1 Read() {
    const auto prior_character = character;
    const auto prior_scratch = scratch;
    const auto prior_model = model;
    const auto prior_definition = definition;
    const auto prior_cache = cache;
    xar::game::BattleTerminalTransitionRequestV1 request{};
    request.character_ids = {scope.played_character_id};
    xar::game::BattleTerminalTransitionSnapshotV1 out{};
    Require(ReadBattleTerminalTransitionV1(bindings, scope, request, out) ==
        xar::game::BattleTerminalTransitionStatusV1::available,
        "production current-person query unavailable");
    Require(out.character_observations && out.character_observations->size() == 1 &&
        (*out.character_observations)[0].current_person_state.has_value(),
        "requested current-person observation absent");
    Require(character == prior_character && scratch == prior_scratch && model == prior_model &&
        definition == prior_definition && cache == prior_cache,
        "readonly producer ran cache construction");
    return *(*out.character_observations)[0].current_person_state->raw_numeric_inputs;
  }
};
}
int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    BattleBindings installed{};
    installed.enabled = true;
    constexpr std::uintptr_t base = 0x180000000ULL;
    EnableBattleCurrentPerson12003(installed, base, xar::ck3_12003::kExecutableSha256);
    Require(reinterpret_cast<std::uintptr_t>(installed.current_person_nine_cache_definition_fallback_slot) ==
        base + 0x5D1F7B8, "exact-build native definition fallback binding changed");
    std::ofstream output(argv[1], std::ios::binary);
    Require(output.good(), "fixture wire path unavailable");
    output << '[';
    for (int index = 0; index < 8; ++index) {
      Fixture fixture;
      if (index == 1) Put<void *>(fixture.carrier, 0x20, nullptr);
      if (index == 2) {
        Put<std::uint32_t>(fixture.carrier, 0x28, 0);
        Put<void *>(fixture.carrier, 0x20, reinterpret_cast<void *>(1));
      }
      if (index == 3) Put<std::uint32_t>(fixture.definition, 0x38, 0);
      if (index == 4) Put<void *>(fixture.scratch, 0x278, nullptr);
      if (index == 5) Put<void *>(fixture.scratch, 0x310, nullptr);
      if (index == 6) Put<void *>(fixture.scratch, 0x258, nullptr);
      if (index == 7) Put<void *>(fixture.character, 0x1B0, nullptr);
      const auto raw = fixture.Read();
      const auto &nine = *raw.nine_cache_byte_inputs;
      Require(raw.raw_numeric_inputs_ready && nine.ready == (index != 4 && index != 6),
          "nine-byte inputs changed independent numeric availability");
      if (index != 7) Require(raw.context_source == "fallback_static",
          "fixture no longer proves actualmodel versus AE0 fallback");
      if (index < 6) Require(nine.aggregate_properties && nine.aggregate_properties->count == 2 &&
          nine.aggregate_properties->values_q64 && (*nine.aggregate_properties->values_q64)[0] == -99999,
          "observer substituted earlier fallback aggregate");
      if (index == 0 || index == 1) Require(nine.selected_definition_keys_u16 &&
          *nine.selected_definition_keys_u16 == std::vector<std::uint16_t>(fixture.selected_keys.begin(), fixture.selected_keys.end()) &&
          nine.used_native_definition_fallback == (index == 1),
          "positionalkeys/FFFF/fallback selection changed");
      if (index == 2) Require(!nine.linked20_present && !nine.selected_definition_keys_u16,
          "false first guard demanded linked or definition operands");
      if (index == 3) Require(!nine.selected_definition_keys_u16,
          "false second guard demanded definition operands");
      if (index == 5) Require(nine.current_cache_present == false && !nine.current_cache_bytes && nine.ready,
          "current-byte absence blocked independent source inputs");
      if (index == 7) Require(!nine.model_present && !nine.current_cache_present && nine.status == "available",
          "null scratch manufactured cache operands");
      if (index) output << ',';
      output << xar::bridge::battle_current_person_state_v1_detail::SerializeRawNumericInputs(raw);
    }
    output << "]\n";
    Require(output.good(), "production serializer wire write failed");
    std::cout << "nine-cache-byte GREEN (8 production-reader samples)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "nine-cache-byte RED: " << error.what() << '\n';
    return 1;
  }
}

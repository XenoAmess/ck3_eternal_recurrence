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
  Bytes<0x38> storage{};
  Bytes<0x20> slots{};
  Bytes<0x210> character{};
  Bytes<0x448> scratch{};
  Bytes<0x230> model{};
  void *game_state = gs.data(), *jomini = js.data(), *characters = storage.data();
  std::int32_t cap = 100, denominator = 100;
  std::int32_t low0 = 10, low1 = -32768, high0 = 20, high1 = -32767;
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
    Put<std::int16_t>(character, 0x68, 9);
    Put(scratch, 0x258, model.data());
    Put(model, 8, character.data());
    Put<std::int64_t>(scratch, 0x2D8, 50);
    Put<std::int64_t>(scratch, 0x2E8, -20);
    Put<std::int64_t>(scratch, 0x430, 999);
    Put<std::int64_t>(scratch, 0x438, -888);
    Put<std::int64_t>(scratch, 0x2E0, 777);
    Put<std::int64_t>(scratch, 0x2F0, -666);
    Put<std::uint8_t>(scratch, 0x440, 2);
    bindings.enabled = bindings.current_person_state_enabled = true;
    bindings.current_person_raw_numeric_inputs_enabled = true;
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini;
    bindings.character_storage_slot = &characters;
    bindings.current_person_raw_skill_caps.fill(&cap);
    bindings.current_person_raw_factor_denominator = &denominator;
    bindings.current_person_raw_category_getters.fill(ZeroCategory);
    bindings.current_person_auxiliary_low_thresholds = {&low0, &low1};
    bindings.current_person_auxiliary_high_thresholds = {&high0, &high1};
    bindings.current_person_raw_fallback_context = model.data() + 0x10;
  }
  xar::game::BattleCurrentPersonStateSnapshotV1 Read() {
    const auto prior_character = character;
    const auto prior_scratch = scratch;
    const auto prior_model = model;
    xar::game::BattleTerminalTransitionRequestV1 request{};
    request.character_ids = {scope.played_character_id};
    xar::game::BattleTerminalTransitionSnapshotV1 out{};
    Require(ReadBattleTerminalTransitionV1(bindings, scope, request, out) ==
        xar::game::BattleTerminalTransitionStatusV1::available,
        "production current-person query unavailable");
    Require(out.character_observations && out.character_observations->size() == 1 &&
        (*out.character_observations)[0].current_person_state.has_value(),
        "requested current-person observation absent");
    Require(character == prior_character && scratch == prior_scratch && model == prior_model,
        "readonly producer changed preparation state");
    return *(*out.character_observations)[0].current_person_state;
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
    Require(reinterpret_cast<std::uintptr_t>(installed.current_person_auxiliary_low_thresholds[0]) == base + 0x5C6A15C &&
        reinterpret_cast<std::uintptr_t>(installed.current_person_auxiliary_low_thresholds[1]) == base + 0x5C69D10 &&
        reinterpret_cast<std::uintptr_t>(installed.current_person_auxiliary_high_thresholds[0]) == base + 0x5C69D18 &&
        reinterpret_cast<std::uintptr_t>(installed.current_person_auxiliary_high_thresholds[1]) == base + 0x5C69D14,
        "exact-build selected threshold binding changed");
    Fixture fixture;
    std::ofstream output(argv[1], std::ios::binary);
    Require(output.good(), "fixture wire path unavailable");
    output << '[';
    for (int index = 0; index < 6; ++index) {
      if (index == 0) fixture.bindings.current_person_auxiliary_high_thresholds[0] = nullptr;
      if (index == 1) {
        Put<std::int16_t>(fixture.character, 0x68, 10);
        fixture.bindings.current_person_auxiliary_high_thresholds[0] = &fixture.high0;
      }
      if (index == 2) {
        Put<std::uint8_t>(fixture.character, 0x1A1, 255);
        Put<std::int16_t>(fixture.character, 0x68, -32768);
      }
      if (index == 3) fixture.bindings.current_person_auxiliary_low_thresholds[1] = nullptr;
      if (index == 4) {
        fixture.bindings.current_person_auxiliary_low_thresholds[1] = &fixture.low1;
        Put<void *>(fixture.model, 8, nullptr);
      }
      if (index == 5) Put<void *>(fixture.character, 0x1B0, nullptr);
      auto state = fixture.Read();
      const auto &raw = *state.raw_numeric_inputs;
      const auto &aux = *raw.auxiliary_scratch_inputs;
      Require(raw.raw_numeric_inputs_ready && aux.ready == (index != 3),
          "auxiliary observation changed independent numeric availability");
      if (index == 0) Require(!aux.selected_high_threshold_raw,
          "first low branch demanded high threshold");
      if (index == 2 || index == 4) Require(aux.selector_flag_raw == 255 &&
          aux.selector_metric_raw == -32768 && aux.selected_high_threshold_raw == -32767,
          "nonzero selector or signed16 comparison changed");
      if (index != 5) Require(aux.prepared430_q64 == 999 && aux.copied430_q64 == 777 &&
          aux.prepared438_q64 == -888 && aux.copied438_q64 == -666 && aux.ready440_raw == 2,
          "prepared/copy/current ready byte identities merged");
      if (index == 4) Require(raw.context_source == "fallback_static",
          "actual current fallback context was not reused");
      if (index == 5) Require(!aux.base430_q64 && !aux.selector_metric_raw &&
          raw.scratch_present == false && aux.status == "available",
          "null scratch invented a prepared result");
      if (index) output << ',';
      output << xar::bridge::battle_current_person_state_v1_detail::SerializeRawNumericInputs(raw);
    }
    output << "]\n";
    Require(output.good(), "production serializer wire write failed");
    std::cout << "auxiliary-scratch GREEN (6 production-reader samples)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "auxiliary-scratch RED: " << error.what() << '\n';
    return 1;
  }
}

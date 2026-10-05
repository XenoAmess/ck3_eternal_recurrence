#include "xar_bridge/ck3_12002_battle.hpp"
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
struct Fixture;
Fixture *active = nullptr;
void *Provider();
void *Government(void *character);
std::int32_t UndemandedIndex(void *) { throw std::runtime_error("initial false flag called tier getter"); }
struct Fixture {
  Bytes<0xA8> gs{}, js{};
  Bytes<0x38> characters_store{}, title_store{};
  Bytes<0x20> character_slots{};
  Bytes<0x80> title_slots{};
  Bytes<0x210> character{}, other_owner{};
  // The same production query also reads the custody pointer at scratch+288.
  Bytes<0x290> scratch{};
  Bytes<0x300> model{};
  Bytes<0x200> landed{};
  Bytes<0x10> static_header{};
  std::array<Bytes<0x1E0>, 6> titles{};
  Bytes<0x1E0> fallback{};
  std::array<Bytes<0x80>, 7> templates{};
  Bytes<0x1010> provider{};
  std::array<Bytes<0xC0>, 7> group_definitions{};
  std::array<void *, 7> group_table{};
  Bytes<0x48> government_false{}, government_true{};
  std::array<std::int32_t, 7> ids{0,0,0x1000002,0x1000003,0x1000004,0x1000005,0x2000002};
  void *game_state = gs.data(), *jomini = js.data(), *characters = characters_store.data();
  void *title_storage = title_store.data(), *fallback_title = fallback.data();
  int government_calls = 0, sample_government_calls = 0, provider_calls = 0;
  bool missing_government = false, missing_provider = false;
  BattleBindings bindings{};
  xar::game::Snapshot scope{};
  Fixture() {
    active = this;
    scope.paused = scope.map_ready = scope.has_played_character = true;
    scope.played_character_id = 0x1000001;
    scope.date_raw = 53265168;
    Put(gs, 8, scope.date_raw);
    Put<std::uint8_t>(js, 0x20, 1);
    Put(characters_store, 0x20, character_slots.data());
    Put<std::uint32_t>(characters_store, 0x2C, 2);
    Put(character_slots, 0x18, character.data());
    Put(character, 0x18, scope.played_character_id);
    Put<std::uint32_t>(character, 0x1C, 0x43686172U);
    Put(character, 0x1B0, scratch.data());
    Put(character, 0x1C0, landed.data());
    Put(other_owner, 0x18, std::int32_t{-2147483647});
    Put(scratch, 0x258, model.data());
    Put(model, 8, character.data());
    Put<std::uint32_t>(model, 0x2F0, 0x43684D64U);
    Put(landed, 0x1E0, ids.data());
    Put<std::int32_t>(landed, 0x1EC, static_cast<std::int32_t>(ids.size()));
    Put(title_store, 0x20, title_slots.data());
    Put<std::uint32_t>(title_store, 0x2C, 8);
    for (std::size_t i = 0; i < titles.size(); ++i) {
      const auto full_id = i == 0 ? std::int32_t{0} : static_cast<std::int32_t>(0x1000000U + i);
      Put(titles[i], 0x10, full_id);
      Put(title_slots, i * 0x10 + 8, titles[i].data());
      Put(titles[i], 0x48, templates[i].data());
      Put<std::int32_t>(titles[i], 0x12C, -1);
    }
    Put<std::int32_t>(templates[2], 0x64, 6);
    Put<std::uint8_t>(titles[3], 0x1D8, 9);
    Put<void *>(titles[3], 0x48, reinterpret_cast<void *>(1));
    Put<std::uint8_t>(titles[4], 0x130, 4);
    Put<void *>(titles[4], 0x48, reinterpret_cast<void *>(1));
    Put<std::int32_t>(titles[5], 0x12C, 0);
    Put<void *>(titles[5], 0x48, reinterpret_cast<void *>(1));
    Put<std::int32_t>(fallback, 0x10, -1);
    Put<std::int32_t>(fallback, 0x12C, -1);
    Put(fallback, 0x48, templates[6].data());
    Put<std::int32_t>(templates[6], 0x64, 2);
    Put<std::uint64_t>(government_true, 0x40, 1ULL << 14);
    for (std::size_t i = 0; i < group_table.size(); ++i) group_table[i] = group_definitions[i].data();
    Put(provider, 0x1000, group_table.data());
    bindings.enabled = bindings.current_person_state_enabled = true;
    bindings.current_person_context_branch_inputs_enabled = true;
    bindings.game_state_slot = &game_state;
    bindings.jomini_state_slot = &jomini;
    bindings.character_storage_slot = &characters;
    bindings.current_person_context_provider = Provider;
    bindings.current_person_context_government = Government;
    bindings.current_person_context_selected_index = UndemandedIndex;
    bindings.current_person_context_static_header = static_header.data();
    bindings.current_person_context_record_storage_slot = &title_storage;
    bindings.current_person_context_record_fallback_slot = &fallback_title;
  }
  xar::game::BattleCurrentPersonContextBranchInputsSnapshotV1 Read() {
    const auto prior_character = character, prior_owner = other_owner;
    const auto prior_scratch = scratch;
    const auto prior_model = model;
    const auto prior_landed = landed;
    const auto prior_titles = titles;
    const auto prior_fallback = fallback;
    xar::game::BattleTerminalTransitionRequestV1 request{};
    request.character_ids = {scope.played_character_id};
    xar::game::BattleTerminalTransitionSnapshotV1 out{};
    Require(ReadBattleTerminalTransitionV1(bindings, scope, request, out) ==
        xar::game::BattleTerminalTransitionStatusV1::available,
        "production current-person query unavailable");
    Require(out.character_observations && out.character_observations->size() == 1 &&
        (*out.character_observations)[0].current_person_state &&
        (*out.character_observations)[0].current_person_state->context_branch_inputs,
        "current title census family absent");
    Require(character == prior_character && other_owner == prior_owner && scratch == prior_scratch &&
        model == prior_model && landed == prior_landed && titles == prior_titles && fallback == prior_fallback,
        "readonly producer changed source memory");
    return *(*out.character_observations)[0].current_person_state->context_branch_inputs;
  }
};
void *Provider() {
  // ReadBattleTerminalTransitionV1 takes two complete samples. Each branch
  // starts with this provider read, so the per-sample government sequence must
  // start at initial-false again while the total call count remains observable.
  active->sample_government_calls = 0;
  ++active->provider_calls;
  return active->missing_provider ? nullptr : active->provider.data();
}
void *Government(void *character) {
  Require(character == active->character.data(), "government getter receiver changed to Title owner");
  ++active->government_calls;
  const auto call = active->sample_government_calls++;
  if (active->missing_government) return nullptr;
  return call == 0 ? active->government_false.data() : active->government_true.data();
}
}

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    std::ofstream output(argv[1], std::ios::binary);
    Require(output.good(), "fixture output unavailable");
    output << '[';
    for (int index = 0; index < 10; ++index) {
      Fixture f;
      if (index == 1) Put(f.model, 8, f.other_owner.data());
      if (index == 2) {
        Put<void *>(f.character, 0x1C0, nullptr);
        Put<void *>(f.static_header, 0, reinterpret_cast<void *>(1));
      }
      if (index == 3) f.fallback_title = nullptr;
      if (index == 4) Put<std::int32_t>(f.templates[0], 0x64, 7);
      if (index == 5) f.missing_government = true;
      if (index == 6) Put<void *>(f.scratch, 0x258, nullptr);
      if (index == 7) Put<std::int32_t>(f.landed, 0x1EC, -1);
      if (index == 8) f.missing_provider = true;
      if (index == 9) Put<void *>(f.titles[0], 0x48, nullptr);
      const auto branch = f.Read();
      const auto &raw = *branch.census_inputs;
      Require(raw.ready == (index != 3 && index != 5 && index != 7 && index != 9),
          "independent raw census availability changed");
      Require(branch.ready == (index == 0 || index == 1 || index == 2 || index == 6),
          "existing seven-count/property readiness changed");
      if (index == 0 || index == 1 || index == 6 || index == 8) {
        Require(branch.group_counts == std::array<std::optional<std::int32_t>, 7>{2,0,1,0,0,0,1},
            "old group counts changed or duplicate/fallback was dropped");
        Require(f.provider_calls == 2 && f.government_calls == 10,
            "two stable production samples repeated census/government calls");
        const auto &rows = *raw.title_occurrences;
        Require(rows.size() == 7 && rows[0].requested_full_title_id_raw_i32 == 0 &&
            rows[1].requested_full_title_id_raw_i32 == 0 && rows[6].resolution == "fallback" &&
            rows[6].resolved_full_title_id_raw_i32 == -1,
            "raw native order or actual fallback identity was replaced");
        Require(!rows[3].qualifier_130_raw_u8 && !rows[4].qualifier_12c_raw_i32 &&
            !rows[5].government_bit14 && !rows[3].template_tier_raw_i32,
            "short circuit demanded later raw operands");
      }
      if (index == 1) Require(raw.model_owner_matches_character == false &&
          raw.model_owner_full_character_id_raw_i32 == -2147483647 && !raw.model_magic_raw_u32,
          "model mismatch substituted queried actor or demanded magic");
      if (index == 2) Require(raw.header_source == "static" && raw.title_occurrences->empty() &&
          f.provider_calls == 2 && f.government_calls == 2,
          "empty static census demanded body operands");
      if (index == 4) Require((*raw.title_occurrences)[0].template_tier_raw_i32 == 7 &&
          !branch.group_counts[0], "outside tier was clamped or lost");
      if (index == 6) Require(raw.model_present == false && !raw.model_owner_present,
          "null model manufactured receiver operands");
      if (index) output << ',';
      output << xar::bridge::battle_current_person_state_v1_detail::SerializeContextBranchInputs(branch);
    }
    output << "]\n";
    Require(output.good(), "production serializer output failed");
    std::cout << "title-census GREEN (10 production-reader samples)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "title-census RED: " << error.what() << '\n';
    return 1;
  }
}

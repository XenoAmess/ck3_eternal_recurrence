#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
template <class T, class Bytes> void Put(Bytes &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
template <class T> T Get(const void *bytes, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(bytes) + offset, sizeof value);
  return value;
}
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
std::int32_t Current(void *, std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
std::int32_t PublicState(void *) { return 3; }
void *attacker_side = nullptr, *defender_side = nullptr;
std::int32_t expected_actor = 0;
int attacker_calls = 0, defender_calls = 0;
bool unstable = false;
bool Contains(const void *side, std::int32_t actor) {
  Check(actor == expected_actor, "membership gets raw Unit actor including -1");
  if (side == attacker_side) ++attacker_calls;
  if (side == defender_side) ++defender_calls;
  if (unstable && side == attacker_side) {
    const auto before = Get<std::int32_t>(side, 0x30);
    const auto after = before + 1;
    std::memcpy(static_cast<std::byte *>(attacker_side) + 0x30, &after, sizeof after);
  }
  const auto count = Get<std::int32_t>(side, 0x14);
  const auto members = Get<void *const *>(side, 8);
  for (std::int32_t i = 0; i < count; ++i)
    if (Get<std::int32_t>(members[i], 8) == actor) return true;
  return false;
}
void Emit(const std::filesystem::path &directory, const char *label,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i != 0) out += ','; out += std::to_string(values[i]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "retained production serializer wire"); file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t actor_id = 0x03000001, w1_id = 0x04000001, w2_id = 0x04000002;
  constexpr std::int32_t w3_id = 0x04000003, w4_id = 0x04000004;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{}, character{}, fallback_character{};
  std::array<std::byte, 0x330> realm{};
  std::array<std::byte, 0x360> w1{}, w2{}, w3{}, w4{}, fallback_war{};
  std::array<std::byte, 0x20> member{}, fallback_member{}, empty_descriptor{};
  std::array<std::byte, 0xB0> state{};
  std::vector<std::byte> manager(0x2A5C0);
  std::array<std::byte, 0x30> units{}, armies{}, characters{}, wars{}, regiments{};
  std::array<std::byte, 0x50> unit_slots{}, army_slots{}, character_slots{}, war_slots{};
  std::array<std::int32_t, 6> war_ids{w1_id, w1_id, w2_id, 0x05000003, -1, w4_id};
  std::array<std::int32_t, 3> queued_ids{army_id, -1, army_id};
  std::array<void *, 1> members{member.data()}, fallback_members{fallback_member.data()};
  Put(unit, 0x10, unit_id); Put(unit, 0x178, army_id); Put(unit, 0x174, actor_id);
  Put(army, 0x10, army_id); Put(army, 0x124, unit_id); Put(army, 0x22, std::uint8_t{7});
  Put(character, 0x18, actor_id); Put(character, 0x1C, std::uint32_t{0});
  Put(character, 0x1C0, static_cast<void *>(realm.data()));
  Put(fallback_character, 0x18, std::int32_t{-1});
  Put(realm, 0x318, static_cast<void *>(war_ids.data()));
  Put(realm, 0x320, std::int32_t{6}); Put(realm, 0x324, std::int32_t{6});
  Put(member, 8, actor_id); Put(fallback_member, 8, std::int32_t{-1});
  Put(w1, 8, w1_id); Put(w2, 8, w2_id); Put(w3, 8, w3_id); Put(w4, 8, w4_id);
  Put(fallback_war, 8, std::int32_t{-1});
  Put(w1, 0x358, std::uint8_t{1}); // World reader's ended flag must not filter this caller.
  const auto side = [&](auto &war, std::size_t offset, auto &list, std::int32_t counter) {
    Put(war, offset + 8, static_cast<void *>(list.data()));
    Put(war, offset + 0x14, std::int32_t{1}); Put(war, offset + 0x30, counter);
  };
  side(w1, 0x20, members, 2'147'483'647); side(w1, 0x80, members, 99);
  side(w2, 0x80, members, -2); side(fallback_war, 0x80, members, 17);
  Put(state, 8, std::int64_t{0x1000000F0LL});
  Put(state, 0xA0, static_cast<void *>(manager.data()));
  Put(manager, 0x2A5A8, static_cast<void *>(queued_ids.data()));
  Put(manager, 0x2A5B0, std::int32_t{3}); Put(manager, 0x2A5B4, std::int32_t{3});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(character_slots, 0x18, static_cast<void *>(character.data()));
  Put(war_slots, 0x18, static_cast<void *>(w1.data()));
  Put(war_slots, 0x28, static_cast<void *>(w2.data()));
  Put(war_slots, 0x38, static_cast<void *>(w3.data()));
  Put(war_slots, 0x48, static_cast<void *>(w4.data()));
  for (auto *storage : {&units, &armies, &characters, &wars}) Put(*storage, 0x2C, std::int32_t{5});
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(characters, 0x20, static_cast<void *>(character_slots.data()));
  Put(wars, 0x20, static_cast<void *>(war_slots.data()));
  void *units_pointer = units.data(), *armies_pointer = armies.data();
  void *characters_pointer = characters.data(), *wars_pointer = wars.data(), *state_pointer = state.data();
  void *regiments_pointer = regiments.data();
  void *fallback_character_pointer = fallback_character.data(), *fallback_war_pointer = fallback_war.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.unit_storage_slot = &units_pointer;
  bindings.internal_army_storage_slot = &armies_pointer; bindings.game_state_slot = &state_pointer;
  bindings.regiment_storage_slot = &regiments_pointer;
  bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
  bindings.get_unit_state = PublicState;
  auto &caller = bindings.monthly_caller_effect_bindings;
  caller.enabled = true; caller.character_storage_slot = &characters_pointer;
  caller.character_fallback_slot = &fallback_character_pointer;
  caller.war_storage_slot = &wars_pointer; caller.war_fallback_slot = &fallback_war_pointer;
  caller.empty_war_ids_descriptor = empty_descriptor.data(); caller.contains_war_participant = Contains;
  attacker_side = w1.data() + 0x20; defender_side = w1.data() + 0x80; expected_actor = actor_id;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent strength stays available"); return rows[0];
  };
  const auto army_before = army, character_before = character;
  const auto w1_before = w1, fallback_before = fallback_war;
  auto row = read(); const auto &inputs = *row.monthly_caller_effect_inputs_v1;
  Check(inputs.available && inputs.army_byte_22_raw == 7 &&
        inputs.current_date_storage_raw64 == 0x1000000F0LL &&
        inputs.unit_actor_character_id == actor_id, "direct byte/date64/raw actor exact operands");
  const auto &observed = *inputs.war_counter_rows;
  Check(observed.size() == 6 && observed[0].war_reference_id == w1_id &&
        observed[1].war_reference_id == w1_id && observed[0].native_selected_side == 0 &&
        observed[0].native_counter_30_raw == 2'147'483'647 &&
        observed[2].native_selected_side == 1 && observed[2].native_counter_30_raw == -2,
        "ordered duplicate ended-War and attacker priority preserved");
  Check(attacker_calls == 4 && defender_calls == 0, "both memberships do not query defender after attacker match");
  Check(observed[3].used_fallback == true && observed[4].used_fallback == true &&
        observed[3].resolved_war_id == -1 && observed[4].native_counter_30_raw == 17 &&
        observed[5].native_selected_side == -1 && !observed[5].native_counter_30_raw,
        "generation fallback alias and neither-side null preserved");
  Check(*inputs.manager_army_id_list_2a5a8 == std::vector<std::int32_t>(queued_ids.begin(), queued_ids.end()),
        "raw queue order including duplicate and -1 preserved");
  Check(army == army_before && character == character_before && w1 == w1_before &&
        fallback_war == fallback_before, "observer never invokes effects");
  Emit(directory, "ordered-counters", row);
  Put(unit, 0x174, std::int32_t{-1}); expected_actor = -1;
  row = read();
  Check(row.monthly_caller_effect_inputs_v1->available &&
        row.monthly_caller_effect_inputs_v1->war_counter_rows->empty(),
        "raw -1 actor uses fallback Character and global empty descriptor");
  Emit(directory, "fallback-actor-empty", row);
  Put(fallback_character, 0x1C0, static_cast<void *>(realm.data()));
  side(fallback_war, 0x80, fallback_members, 17);
  row = read();
  Check(row.monthly_caller_effect_inputs_v1->war_counter_rows->at(3).native_selected_side == 1,
        "fallback Character realm is consumed without magic or identity gate");
  Emit(directory, "fallback-actor-realm", row);
  Put(unit, 0x174, actor_id); expected_actor = actor_id;
  side(fallback_war, 0x80, members, 17); caller.contains_war_participant = nullptr;
  row = read();
  Check(!row.monthly_caller_effect_inputs_v1->available &&
        row.monthly_caller_effect_inputs_v1->war_counter_rows->at(0).resolved_war_id == w1_id &&
        !row.monthly_caller_effect_inputs_v1->war_counter_rows->at(0).native_selected_side &&
        row.monthly_caller_effect_inputs_v1->manager_army_id_list_2a5a8.has_value(),
        "stable partial keeps independent operands");
  Emit(directory, "partial-membership", row); caller.contains_war_participant = Contains;
  Put(state, 0xA0, static_cast<void *>(nullptr)); row = read();
  Check(!row.monthly_caller_effect_inputs_v1->available &&
        row.monthly_caller_effect_inputs_v1->war_counter_rows->at(0).available &&
        !row.monthly_caller_effect_inputs_v1->manager_army_id_list_2a5a8,
        "missing manager does not erase war counter observation");
  Emit(directory, "partial-manager", row); Put(state, 0xA0, static_cast<void *>(manager.data()));
  Put(w1, 0x50, std::int32_t{0}); unstable = true; row = read();
  Check(!row.monthly_caller_effect_inputs_v1->available &&
        row.monthly_caller_effect_inputs_v1->unavailable_reason == "monthly_caller_effect_inputs_changed_during_read" &&
        !row.monthly_caller_effect_inputs_v1->army_byte_22_raw && !row.monthly_caller_effect_inputs_v1->war_counter_rows,
        "new operand double sample clears changed frame");
  Emit(directory, "changed-inputs", row); unstable = false;
  caller.enabled = false;
  Check(!read().monthly_caller_effect_inputs_v1, "older binder leaves block absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required"); Cases(argv[1]);
    std::cout << "PASS: finite monthly caller readonly operands and six production wires\n"; return 0;
  } catch (const std::exception &error) { std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1; }
}

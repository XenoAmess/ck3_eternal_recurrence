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
template<class T, class Bytes> void Put(Bytes &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
std::int32_t Current(void *, std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
void Emit(const std::filesystem::path &directory, const char *label,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t index = 0; index < values.size(); ++index) {
          if (index != 0) out += ',';
          out += std::to_string(values[index]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "new point-store production wire output");
  file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t containing_id = 0x03000001, receiver_id = 0x04000002, invalid_id = 0x05000003;
  constexpr std::int32_t character_id = 0x06000001, other_character_id = 0x06000002, absent_character_id = 0x06000003;
  constexpr auto raw_target_a = static_cast<std::int32_t>(0x99000001U);
  constexpr auto raw_target_b = static_cast<std::int32_t>(0x88000002U);
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x208> army{};
  std::array<std::byte, 0x160> containing{}, receiver{}, invalid{};
  std::array<std::byte, 0x1D0> character{}, other_character{}, absent_character{}, character_fallback{};
  std::array<std::byte, 0x2B8> character_child{};
  std::array<std::byte, 0x110> shared_child{};
  std::array<std::byte, 0x38> first_group{}, second_group{};
  std::array<void *, 2> groups{first_group.data(), second_group.data()};
  std::array<std::array<std::int32_t, 4>, 4> first_records{{
      {0, 0, containing_id, 0}, {0, 0, containing_id, 1},
      {0, 0, containing_id, 2}, {0, 0, invalid_id, 0}}};
  std::array<std::array<std::int32_t, 4>, 1> second_records{{{0, 0, containing_id, 0}}};
  std::array<std::int32_t, 4> first_characters{character_id, other_character_id, -1, absent_character_id};
  std::array<std::int32_t, 1> second_characters{character_id};
  std::array<std::int32_t, 5> memberships{raw_target_a, 9, raw_target_a, raw_target_b, 11};
  std::array<std::byte, 0x30> units{}, armies{}, raised{}, persistent{}, characters{};
  std::array<std::byte, 0x40> unit_slots{}, army_slots{}, persistent_slots{}, character_slots{};
  Put(unit, 0x10, unit_id); Put(unit, 0x178, army_id);
  Put(army, 0x10, army_id); Put(army, 0x14, std::uint32_t{0x41726D79});
  Put(army, 0x124, unit_id); Put(army, 0x50, static_cast<void *>(groups.data()));
  Put(army, 0x5C, std::int32_t{2});
  Put(first_group, 8, static_cast<void *>(first_records.data())); Put(first_group, 0x14, std::int32_t{4});
  Put(first_group, 0x10, std::int32_t{4});
  Put(second_group, 8, static_cast<void *>(second_records.data())); Put(second_group, 0x14, std::int32_t{1});
  Put(second_group, 0x10, std::int32_t{1});
  Put(first_group, 0x20, static_cast<void *>(first_characters.data())); Put(first_group, 0x2C, std::int32_t{4});
  Put(first_group, 0x28, std::int32_t{4});
  Put(second_group, 0x20, static_cast<void *>(second_characters.data())); Put(second_group, 0x2C, std::int32_t{1});
  Put(second_group, 0x28, std::int32_t{1});
  Put(containing, 0x10, containing_id); Put(containing, 0x14, std::uint32_t{0x52656769});
  Put(containing, 0x20, raw_target_a); Put(containing, 0x44, raw_target_b);
  for (const auto offset : {0x18U, 0x3CU}) {
    Put(containing, offset + 0x14, std::uint8_t{9});
    Put(containing, offset + 0x18, std::int32_t{4});
  }
  Put(containing, 0x74, std::uint8_t{7}); Put(containing, 0x78, std::int32_t{1});
  Put(receiver, 0x10, receiver_id); Put(receiver, 0x14, std::uint32_t{0x52656769});
  Put(receiver, 0x138, std::int32_t{0}); Put(receiver, 0x130, std::int32_t{-1});
  Put(receiver, 0x12C, character_id);
  Put(invalid, 0x10, invalid_id);
  Put(character, 0x18, character_id); Put(other_character, 0x18, other_character_id);
  Put(absent_character, 0x18, absent_character_id); Put(character_fallback, 0x18, std::int32_t{-1});
  // No Char magic: the actual point loop has no such gate. All three source
  // C8/C0 routes reach the same B8 child, including the fallback ID-1 object.
  Put(character, 0x1C8, static_cast<void *>(shared_child.data()));
  Put(character, 0x1C0, static_cast<void *>(character_child.data()));
  Put(other_character, 0x1C0, static_cast<void *>(character_child.data()));
  for (auto *object : {&character, &other_character, &character_fallback})
    Put(*object, 0x1B8, static_cast<void *>(shared_child.data()));
  Put(shared_child, 0x108, std::uint8_t{7}); Put(shared_child, 0xFC, std::int32_t{42});
  Put(character_child, 0x2A8, static_cast<void *>(memberships.data()));
  Put(character_child, 0x2B0, std::int32_t{5});
  Put(character_child, 0x2B4, std::int32_t{5});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(persistent_slots, 0x18, static_cast<void *>(containing.data()));
  Put(persistent_slots, 0x28, static_cast<void *>(receiver.data()));
  Put(persistent_slots, 0x38, static_cast<void *>(invalid.data()));
  Put(character_slots, 0x18, static_cast<void *>(character.data()));
  Put(character_slots, 0x28, static_cast<void *>(other_character.data()));
  Put(character_slots, 0x38, static_cast<void *>(absent_character.data()));
  const auto registry = [&](auto &storage, auto &slots) {
    Put(storage, 0x20, static_cast<void *>(slots.data())); Put(storage, 0x2C, std::uint32_t{4});
  };
  registry(units, unit_slots); registry(armies, army_slots); registry(persistent, persistent_slots); registry(characters, character_slots);
  void *unit_pointer = units.data(), *army_pointer = armies.data(), *raised_pointer = raised.data();
  void *army_fallback_pointer = army.data();
  void *persistent_pointer = persistent.data(), *persistent_fallback = receiver.data();
  void *character_pointer = characters.data(), *character_fallback_pointer = character_fallback.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.unit_storage_slot = &unit_pointer;
  bindings.internal_army_storage_slot = &army_pointer; bindings.regiment_storage_slot = &raised_pointer;
  bindings.persistent_regiment_storage_slot = &persistent_pointer;
  bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
  bindings.monthly_daily_queue_bindings.army_fallback_slot = &army_fallback_pointer;
  bindings.monthly_current_helper_domain_bindings.enabled = true;
  bindings.monthly_current_helper_domain_bindings.persistent_regiment_fallback_slot = &persistent_fallback;
  bindings.monthly_current_helper_domain_bindings.character_storage_slot = &character_pointer;
  bindings.monthly_current_helper_domain_bindings.character_fallback_slot = &character_fallback_pointer;
  bindings.monthly_current_helper_point_store_inputs_enabled = true;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent strength stays available"); return rows[0];
  };
  const auto army_before = army;
  const auto containing_before = containing, receiver_before = receiver, invalid_before = invalid;
  const auto character_before = character, other_before = other_character, fallback_before = character_fallback;
  const auto group_before = first_group, second_group_before = second_group;
  const auto memberships_before = memberships;
  const auto child_before = shared_child;
  auto row = read(); const auto &inputs = *row.monthly_current_helper_point_store_inputs_v1;
  Check(inputs.available && inputs.helper_same_current_army_pointer == true &&
        inputs.helper_used_fallback == false && inputs.helper_resolved_army_id == army_id &&
        inputs.groups->size() == 2, "source helper resolves current FullID and captures two groups");
  const auto &records = *inputs.groups->at(0).record_rows;
  Check(records[0].data_owner_regiment_reference_id == raw_target_a && records[1].data_owner_regiment_reference_id == raw_target_b &&
        records[0].receiver_regiment_resolved_id == receiver_id && records[0].receiver_regiment_used_fallback == true &&
        records[0].membership_alias_ordinal == records[1].membership_alias_ordinal &&
        records[0].ordered_persistent_regiment_ids_2a8 == std::vector<std::int32_t>(memberships.begin(), memberships.end()) &&
        records[2].data_state_18_raw == 1 && records[2].data_byte_14_raw == 7 &&
        records[3].record_regiment_magic_14_raw == std::uint32_t{0} && !records[3].data_record_present &&
        inputs.groups->at(1).record_rows->at(0).data_alias_ordinal == records[0].data_alias_ordinal,
        "raw target differs from fallback receiver; real nonempty vector and repeated DATA/header aliases");
  const auto &chars = *inputs.groups->at(0).character_rows;
  Check(chars[0].character_child_1c8_present == true && chars[1].character_child_1c8_present == false &&
        chars[1].character_child_1c0_present == true && chars[2].character_child_1c0_present == false &&
        chars[2].character_used_fallback == true && chars[2].character_resolved_id == -1 &&
        chars[0].child_1b8_alias_ordinal == chars[2].child_1b8_alias_ordinal &&
        chars[0].child_byte_108_raw == 7 && chars[0].child_character_reference_fc_raw == std::int32_t{42} &&
        chars[3].character_child_1b8_present == false,
        "three C8/C0 paths and fallback ID-1 share active B8; absent B8 is observed independently");
  Check(army == army_before && containing == containing_before && receiver == receiver_before && invalid == invalid_before &&
        character == character_before && other_character == other_before && character_fallback == fallback_before &&
        first_group == group_before && second_group == second_group_before && memberships == memberships_before && shared_child == child_before,
        "observer never clears DATA, removes membership, changes child fields or releases groups");
  Emit(directory, "nonempty-aliases", row);
  Put(character_child, 0x2A8, static_cast<void *>(nullptr)); row = read();
  Check(row.monthly_current_helper_point_store_inputs_v1->available &&
        !row.monthly_current_helper_point_store_inputs_v1->groups->at(0).record_rows->at(0).ordered_persistent_regiment_ids_2a8,
        "captured traversal retains missing membership operand while independent DATA and child values remain observable");
  Emit(directory, "partial-membership", row);
  Put(character_child, 0x2A8, static_cast<void *>(memberships.data()));
  Put(first_group, 0x2C, std::int32_t{-1}); row = read();
  Check(!row.monthly_current_helper_point_store_inputs_v1->available &&
        !row.monthly_current_helper_point_store_inputs_v1->groups->at(0).character_rows &&
        row.monthly_current_helper_point_store_inputs_v1->groups->at(0).record_rows,
        "negative character end cannot masquerade as a source zero-count skip; record observations remain");
  Emit(directory, "negative-character-traversal", row);
  Put(army, 0x5C, std::int32_t{0}); row = read();
  Check(row.monthly_current_helper_point_store_inputs_v1->available &&
        row.monthly_current_helper_point_store_inputs_v1->groups->empty(), "zero groups prove no point calls");
  Emit(directory, "empty-groups", row);
  bindings.monthly_current_helper_point_store_inputs_enabled = false;
  Check(!read().monthly_current_helper_point_store_inputs_v1, "older producer family remains absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: current helper point-store inputs and four new production wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
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
  Check(static_cast<bool>(file), "new current-helper production wire output");
  file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t containing_id = 0x03000001, receiver_id = 0x04000002;
  constexpr std::int32_t title_id = 0x05000001, character_id = 0x06000001;
  constexpr std::int32_t domain_id = 0x07000001;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x208> army{};
  std::array<std::byte, 0x160> containing{}, receiver{};
  std::array<std::byte, 0x138> title{}, title_fallback{};
  std::array<std::byte, 0x1D0> character{}, character_fallback{};
  std::array<std::byte, 0xB70> character_child{};
  std::array<std::byte, 0x50> domain{}, domain_fallback{};
  std::array<std::byte, 0x180> domain_data{};
  std::array<std::byte, 0x38> group{};
  std::array<void *, 1> groups{group.data()};
  std::array<std::array<std::int32_t, 4>, 2> records{{
      {0, 0, containing_id, 0}, {0, 0, containing_id, 1}}};
  std::array<std::byte, 0x30> units{}, armies{}, raised{}, persistent{}, titles{}, characters{}, domains{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, persistent_slots{}, title_slots{}, character_slots{}, domain_slots{};
  Put(unit, 0x10, unit_id); Put(unit, 0x178, army_id);
  Put(army, 0x10, army_id); Put(army, 0x14, std::uint32_t{0x41726D79});
  Put(army, 0x124, unit_id); Put(army, 0x50, static_cast<void *>(groups.data()));
  Put(army, 0x5C, std::int32_t{1});
  Put(group, 8, static_cast<void *>(records.data())); Put(group, 0x14, std::int32_t{2});
  Put(containing, 0x10, containing_id); Put(containing, 0x14, std::uint32_t{0x52656769});
  for (const auto offset : {0x18U, 0x3CU}) {
    Put(containing, offset + 8, receiver_id); Put(containing, offset + 0x18, std::int32_t{4});
    Put(containing, offset + 0x14, std::uint8_t{1});
  }
  Put(receiver, 0x10, receiver_id); Put(receiver, 0x14, std::uint32_t{0x52656769});
  Put(receiver, 0x138, std::int32_t{4}); Put(receiver, 0x130, title_id);
  Put(receiver, 0x12C, std::int32_t{-1}); Put(receiver, 0x128, std::int32_t{5});
  Put(receiver, 0x18, std::int32_t{2}); Put(receiver, 0x1C, std::int32_t{5});
  Put(receiver, 0x3C, std::int32_t{9}); Put(receiver, 0x40, std::int32_t{0});
  Put(receiver, 0x54, std::int32_t{3});
  for (auto *object : {&title, &title_fallback}) {
    Put(*object, 0x10, title_id); Put(*object, 0x128, character_id);
  }
  Put(character, 0x18, character_id); Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(character, 0x1C8, static_cast<void *>(character_child.data()));
  Put(character_fallback, 0x18, std::int32_t{-1});
  Put(character_child, 0xB68, domain_id);
  Put(domain, 8, domain_id); Put(domain, 0xC, std::uint32_t{0x446F6D69});
  Put(domain, 0x20, character_id); Put(domain, 0x30, static_cast<void *>(domain_data.data()));
  Put(domain, 0x48, std::int64_t{200000}); Put(domain_data, 0x17E, std::uint8_t{7});
  Put(domain_fallback, 8, std::int32_t{-1});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(persistent_slots, 0x18, static_cast<void *>(containing.data()));
  Put(persistent_slots, 0x28, static_cast<void *>(receiver.data()));
  Put(title_slots, 0x18, static_cast<void *>(title.data()));
  Put(character_slots, 0x18, static_cast<void *>(character.data()));
  Put(domain_slots, 0x18, static_cast<void *>(domain.data()));
  const auto registry = [&](auto &storage, auto &slots) {
    Put(storage, 0x20, static_cast<void *>(slots.data())); Put(storage, 0x2C, std::uint32_t{3});
  };
  registry(units, unit_slots); registry(armies, army_slots); registry(persistent, persistent_slots);
  registry(titles, title_slots); registry(characters, character_slots); registry(domains, domain_slots);
  void *unit_pointer = units.data(), *army_pointer = armies.data(), *raised_pointer = raised.data();
  void *persistent_pointer = persistent.data(), *persistent_fallback = containing.data();
  void *title_pointer = titles.data(), *title_fallback_pointer = title_fallback.data();
  void *character_pointer = characters.data(), *character_fallback_pointer = character_fallback.data();
  void *domain_pointer = domains.data(), *domain_fallback_pointer = domain_fallback.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.unit_storage_slot = &unit_pointer;
  bindings.internal_army_storage_slot = &army_pointer; bindings.regiment_storage_slot = &raised_pointer;
  bindings.persistent_regiment_storage_slot = &persistent_pointer;
  bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
  bindings.monthly_current_helper_domain_bindings = {true, &persistent_fallback,
      &title_pointer, &title_fallback_pointer, &character_pointer, &character_fallback_pointer,
      &domain_pointer, &domain_fallback_pointer};
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent strength stays available"); return rows[0];
  };
  const auto army_before = army;
  const auto containing_before = containing, receiver_before = receiver;
  const auto group_before = group;
  const auto domain_before = domain;
  const auto title_before = title;
  const auto character_before = character;
  const auto records_before = records;
  auto row = read(); const auto &inputs = *row.monthly_current_helper_domain_inputs_v1;
  Check(inputs.available && inputs.entry_army_id == army_id && inputs.group_count_5c_raw == 1 &&
        inputs.rows->size() == 2, "current groups captured in source order");
  const auto &first = inputs.rows->at(0), &second = inputs.rows->at(1);
  Check(first.record_regiment_resolved_id == containing_id && first.receiver_regiment_resolved_id == receiver_id &&
        first.owner_title_resolved_id == title_id && first.owner_title_used_fallback == false &&
        first.selected_character_reference_id == character_id && first.domain_flag_17e_raw == 7 &&
        first.count_base_128_raw == 5 && first.count_records->size() == 7 &&
        first.count_records->at(1).state_18_raw == 3 && first.domain_alias_ordinal == 0 &&
        second.domain_alias_ordinal == 0 && first.domain_value_48_raw64 == 200000,
        "actual DATA owner, Title holder, seven count records and physical Domain alias");
  Check(army == army_before && containing == containing_before && receiver == receiver_before &&
        group == group_before && domain == domain_before && title == title_before &&
        character == character_before && records == records_before,
        "new observer never clears DATA byte14, updates Domain or releases groups");
  Emit(directory, "ordered-nonzero", row);
  Put(receiver, 0x130, std::int32_t{0x08000001}); row = read();
  Check(row.monthly_current_helper_domain_inputs_v1->rows->at(0).owner_title_used_fallback == true,
        "Title generation mismatch uses actual Title fallback, not Army storage");
  Emit(directory, "title-fallback", row);
  Put(receiver, 0x128, std::numeric_limits<std::int32_t>::max()); row = read();
  Check(row.monthly_current_helper_domain_inputs_v1->rows->at(0).count_base_128_raw ==
        std::numeric_limits<std::int32_t>::max(), "signed native count base is never clamped");
  Emit(directory, "count-wrap", row);
  Put(domain, 0x30, static_cast<void *>(nullptr)); row = read();
  Check(row.monthly_current_helper_domain_inputs_v1->available &&
        row.monthly_current_helper_domain_inputs_v1->rows->at(0).domain_data_30_present == false &&
        !row.monthly_current_helper_domain_inputs_v1->rows->at(0).domain_flag_17e_raw,
        "valid Domain null receiver does not fabricate predicate false");
  Emit(directory, "partial-predicate", row);
  Put(army, 0x5C, std::int32_t{0}); row = read();
  Check(row.monthly_current_helper_domain_inputs_v1->available &&
        row.monthly_current_helper_domain_inputs_v1->rows->empty(), "zero group count proves no Domain calls");
  Emit(directory, "no-domain-calls", row);
  bindings.monthly_current_helper_domain_bindings.enabled = false;
  Check(!read().monthly_current_helper_domain_inputs_v1, "older producer families stay absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: current helper Domain inputs and five new production wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}

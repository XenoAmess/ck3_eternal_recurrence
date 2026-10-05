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
  Check(static_cast<bool>(file), "new production wire output"); file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x208> army{}, fallback{}, same_id_other{};
  std::array<std::byte, 0xB0> state{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{}, unit_slots{}, army_slots{};
  std::vector<std::byte> data(0x2AA00);
  std::array<std::int32_t, 2> queue{army_id, army_id};
  std::array<std::int32_t, 4> stable{army_id, 9, army_id, 10};
  std::array<std::int32_t, 4> swap{army_id, 9, army_id, 10};
  std::array<std::array<std::uint32_t, 4>, 4> records{{
      {static_cast<std::uint32_t>(army_id), 1U, 2U, 3U},
      {9U, 11U, 12U, 13U},
      {static_cast<std::uint32_t>(army_id), 21U, 22U, 23U},
      {10U, 31U, 32U, 33U}}};
  std::array<void *, 4> bucket{army.data(), same_id_other.data(), nullptr, army.data()};
  Put(unit, 0x10, unit_id); Put(unit, 0x178, army_id);
  for (auto *object : {&army, &fallback, &same_id_other}) {
    Put(*object, 0x10, army_id); Put(*object, 0x14, std::uint32_t{0x41726D79});
  }
  Put(army, 0x124, unit_id); Put(state, 0xA0, static_cast<void *>(data.data()));
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(units, 0x20, static_cast<void *>(unit_slots.data())); Put(units, 0x2C, std::int32_t{3});
  Put(armies, 0x20, static_cast<void *>(army_slots.data())); Put(armies, 0x2C, std::int32_t{3});
  constexpr std::size_t primary = 0x2A540;
  const auto list = [&](std::size_t offset, auto &values) {
    Put(data, primary + offset, static_cast<void *>(values.data()));
    Put(data, primary + offset + 8, static_cast<std::int32_t>(values.size()));
    Put(data, primary + offset + 0xC, static_cast<std::int32_t>(values.size()));
  };
  list(0x50, stable); list(0x68, queue);
  for (const auto offset : {0x80U, 0x98U, 0xC8U, 0x158U}) list(offset, swap);
  list(0xB0, records);
  const auto phase = static_cast<std::uint32_t>(army_id) % 30U;
  const auto bucket_offset = 0x198 + 0x18 * static_cast<std::size_t>(phase);
  list(bucket_offset, bucket);
  void *units_pointer = units.data(), *armies_pointer = armies.data();
  void *regiments_pointer = regiments.data(), *state_pointer = state.data();
  void *fallback_pointer = fallback.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.unit_storage_slot = &units_pointer;
  bindings.internal_army_storage_slot = &armies_pointer;
  bindings.regiment_storage_slot = &regiments_pointer; bindings.game_state_slot = &state_pointer;
  bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
  bindings.monthly_daily_queue_bindings = {true, &fallback_pointer};
  bindings.monthly_first_removal_cleanup_inputs_enabled = true;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent strength remains available"); return rows[0];
  };
  const auto data_before = data;
  const auto army_before = army, fallback_before = fallback, other_before = same_id_other;
  const auto stable_before = stable, swap_before = swap;
  const auto records_before = records; const auto queue_before = queue; const auto bucket_before = bucket;
  auto row = read(); const auto &inputs = *row.monthly_first_removal_cleanup_inputs_v1;
  Check(inputs.available && inputs.candidate_found == true && inputs.candidate_stored_index == 0 &&
        inputs.argument_army_id == army_id && inputs.cleanup_resolved_army_id == army_id &&
        inputs.cleanup_used_fallback == false && inputs.selected_bucket_index == phase,
        "first candidate and second FullID lookup are exact");
  const auto &observed_bucket = *inputs.selected_bucket_rows;
  Check(observed_bucket.size() == 4 && observed_bucket[0].native_same_cleanup_army_pointer &&
        !observed_bucket[1].native_same_cleanup_army_pointer &&
        observed_bucket[1].observed_army_id == army_id && !observed_bucket[2].observed_army_id &&
        !observed_bucket[2].native_same_cleanup_army_pointer &&
        observed_bucket[3].native_same_cleanup_army_pointer &&
        *inputs.records_b0 == std::vector<std::array<std::uint32_t, 4>>(records.begin(), records.end()),
        "bucket physical equality differs from FullID equality; opaque words preserved");
  Check(data == data_before && army == army_before && fallback == fallback_before &&
        same_id_other == other_before && stable == stable_before && swap == swap_before &&
        records == records_before && queue == queue_before && bucket == bucket_before,
        "observer never removes memberships, drains queue or invokes Army cleanup");
  Emit(directory, "first-cleanup", row);

  queue[0] = 0x03000001;
  bucket[1] = fallback.data();
  row = read();
  Check(row.monthly_daily_queue_inputs_v1->initial_army_resolution_rows->at(0).used_fallback == true &&
        row.monthly_first_removal_cleanup_inputs_v1->cleanup_used_fallback == false &&
        !row.monthly_first_removal_cleanup_inputs_v1->selected_bucket_rows->at(1).native_same_cleanup_army_pointer,
        "passed fallback and helper regular Army are distinct physical roles");
  Emit(directory, "distinct-helper-resolution", row);

  Put(data, primary + bucket_offset, static_cast<void *>(nullptr)); row = read();
  Check(!row.monthly_first_removal_cleanup_inputs_v1->available &&
        !row.monthly_first_removal_cleanup_inputs_v1->selected_bucket_rows &&
        row.monthly_first_removal_cleanup_inputs_v1->id_lists[0].ordered_army_ids &&
        row.monthly_first_removal_cleanup_inputs_v1->records_b0,
        "missing bucket leaves independent observed list and record families useful");
  Emit(directory, "partial-bucket", row);

  Put(data, primary + 0x74, std::int32_t{0}); row = read();
  Check(row.monthly_first_removal_cleanup_inputs_v1->available &&
        row.monthly_first_removal_cleanup_inputs_v1->candidate_found == false &&
        !row.monthly_first_removal_cleanup_inputs_v1->argument_army_id,
        "empty queue proves no cleanup call without requiring bucket fields");
  Emit(directory, "empty-queue", row);
  bindings.monthly_first_removal_cleanup_inputs_enabled = false;
  Check(!read().monthly_first_removal_cleanup_inputs_v1, "older fixture families stay absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: first manager cleanup operands and four new production wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}

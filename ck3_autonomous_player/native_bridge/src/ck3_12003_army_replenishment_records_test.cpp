#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"

#include <array>
#include <charconv>
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
using xar::ck3_12002::ArmyBindings;
using xar::ck3_12002::ArmyStrengthScope;
using xar::game::ArmyStrengthSnapshot;
using xar::game::ArmyRegimentReplenishmentRecordsStatusV1;

constexpr std::int32_t kPublicId = 301989997;
constexpr std::int32_t kNativeId = 201326670;
constexpr std::int32_t kArmyRegimentId = 117440517;
constexpr std::int32_t kPartialArmyRegimentId = 117440518;
constexpr std::array<std::int32_t, 3> kPersistentIds{
    301989889, 570425346, 838860803};
constexpr std::array<std::int32_t, 3> kOrdinals{0, 2, 4};
std::size_t checks = 0;

void Require(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
template <class T> T Get(const void *bytes, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(bytes) + offset, sizeof value);
  return value;
}

struct Fixture {
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x60> army_regiment{}, partial_army_regiment{};
  std::array<std::array<std::byte, 0x200>, 3> persistent{};
  std::array<std::byte, 3 * 0x10> records{};
  std::array<std::byte, 0x10> partial_record{};
  std::array<std::int32_t, 2> regiment_ids{kArmyRegimentId, kPartialArmyRegimentId};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{},
      persistent_storage{};
  std::array<std::byte, 110 * 0x10> unit_slots{};
  std::array<std::byte, 79 * 0x10> army_slots{};
  std::array<std::byte, 7 * 0x10> regiment_slots{};
  std::array<std::byte, 4 * 0x10> persistent_slots{};
  void *unit_storage_ptr = unit_storage.data();
  void *army_storage_ptr = army_storage.data();
  void *regiment_storage_ptr = regiment_storage.data();
  void *persistent_storage_ptr = persistent_storage.data();
  ArmyBindings bindings{};
  std::array<std::int64_t, 3> fresh_fraction{5000, 7500, 12500};
  std::array<bool, 3> regiment_eligible{false, true, false};
  std::array<bool, 3> chunk_eligible{false, false, true};
  std::int32_t regiment_count = 1;
  std::int32_t current = 0;
  std::int32_t maximum = 0;
  std::int32_t current_calls = 0;
  std::int32_t maximum_calls = 0;
  bool receivers_valid = true;
};
Fixture *active = nullptr;

std::size_t PersistentIndex(void *persistent) {
  for (std::size_t index = 0; index < active->persistent.size(); ++index) {
    if (persistent == active->persistent[index].data()) return index;
  }
  active->receivers_valid = false;
  return active->persistent.size();
}
std::size_t ChunkIndex(void *chunk) {
  for (std::size_t index = 0; index < active->persistent.size(); ++index) {
    if (chunk == active->persistent[index].data() + 0x18 +
        static_cast<std::size_t>(kOrdinals[index]) * 0x24) return index;
  }
  active->receivers_valid = false;
  return active->persistent.size();
}
std::int32_t State(void *unit) {
  active->receivers_valid = active->receivers_valid && unit == active->unit.data();
  return 1;
}
std::int32_t Current(void *ids_array, std::uint8_t flags) {
  active->receivers_valid = active->receivers_valid &&
      ids_array == active->army.data() + 0x38 && flags == 0 &&
      Get<void *>(ids_array, 0) == active->regiment_ids.data() &&
      Get<std::int32_t>(ids_array, 0x0C) == active->regiment_count;
  ++active->current_calls;
  return active->current;
}
std::int32_t Maximum(void *army) {
  active->receivers_valid = active->receivers_valid &&
      army == active->army.data() && Get<std::int32_t>(army, 0x44) == active->regiment_count;
  ++active->maximum_calls;
  return active->maximum;
}
bool CanRegiment(void *persistent, void *chunk) {
  const auto p = PersistentIndex(persistent);
  const auto c = ChunkIndex(chunk);
  active->receivers_valid = active->receivers_valid && p == c;
  return p < active->regiment_eligible.size() && active->regiment_eligible[p];
}
bool CanChunk(void *chunk) {
  const auto index = ChunkIndex(chunk);
  return index < active->chunk_eligible.size() && active->chunk_eligible[index];
}
std::int64_t *FreshFraction(void *persistent, std::int64_t *out) {
  const auto index = PersistentIndex(persistent);
  *out = index < active->fresh_fraction.size() ? active->fresh_fraction[index] : 0;
  return out;
}

void Prepare(Fixture &f, bool empty) {
  active = &f;
  f.regiment_count = empty ? 2 : 1;
  f.current = empty ? 0 : 125;
  f.maximum = empty ? 0 : 260;
  Put(f.unit, 0x10, kPublicId);
  Put(f.unit, 0x178, kNativeId);
  Put(f.army, 0x10, kNativeId);
  Put(f.army, 0x124, kPublicId);
  Put(f.army, 0x38, static_cast<void *>(f.regiment_ids.data()));
  Put(f.army, 0x40, f.regiment_count);
  Put(f.army, 0x44, f.regiment_count);
  Put(f.army_regiment, 0x10, kArmyRegimentId);
  Put(f.army_regiment, 0x14, std::uint32_t{0x41725267U});
  Put(f.army_regiment, 0x38, f.current);
  Put(f.army_regiment, 0x3C, f.maximum);
  Put(f.army_regiment, 0x20, empty ? nullptr : static_cast<void *>(f.records.data()));
  Put(f.army_regiment, 0x28, empty ? std::int32_t{0} : std::int32_t{3});
  Put(f.army_regiment, 0x2C, empty ? std::int32_t{0} : std::int32_t{3});
  Put(f.unit_slots, 109 * 0x10 + 8, static_cast<void *>(f.unit.data()));
  Put(f.army_slots, 78 * 0x10 + 8, static_cast<void *>(f.army.data()));
  Put(f.regiment_slots, 5 * 0x10 + 8, static_cast<void *>(f.army_regiment.data()));
  Put(f.unit_storage, 0x20, static_cast<void *>(f.unit_slots.data()));
  Put(f.unit_storage, 0x2C, std::int32_t{110});
  Put(f.army_storage, 0x20, static_cast<void *>(f.army_slots.data()));
  Put(f.army_storage, 0x2C, std::int32_t{79});
  Put(f.regiment_storage, 0x20, static_cast<void *>(f.regiment_slots.data()));
  Put(f.regiment_storage, 0x2C, std::int32_t{7});
  Put(f.persistent_storage, 0x20, static_cast<void *>(f.persistent_slots.data()));
  Put(f.persistent_storage, 0x2C, std::int32_t{4});
  constexpr std::array<std::int32_t, 3> maximum{100, 100, 60};
  constexpr std::array<std::int32_t, 3> current{100, 25, 0};
  constexpr std::array<std::int32_t, 3> states{0, 0, 3};
  for (std::size_t index = 0; index < f.persistent.size(); ++index) {
    auto &persistent = f.persistent[index];
    Put(persistent, 0x10, kPersistentIds[index]);
    Put(persistent, 0x14, std::uint32_t{0x52656769U});
    Put(persistent, 0x148, index == 2 ? std::int64_t{2500} : std::int64_t{0});
    const auto chunk = 0x18 + static_cast<std::size_t>(kOrdinals[index]) * 0x24;
    Put(persistent, chunk, maximum[index]);
    Put(persistent, chunk + 4, current[index]);
    Put(persistent, chunk + 8, kPersistentIds[index]);
    Put(persistent, chunk + 0xC, kOrdinals[index]);
    Put(persistent, chunk + 0x10, kArmyRegimentId);
    Put(persistent, chunk + 0x18, states[index]);
    Put(f.persistent_slots, (index + 1) * 0x10 + 8,
        static_cast<void *>(persistent.data()));
    Put(f.records, index * 0x10 + 8, kPersistentIds[index]);
    Put(f.records, index * 0x10 + 0xC, kOrdinals[index]);
  }
  if (empty) {
    Put(f.partial_army_regiment, 0x10, kPartialArmyRegimentId);
    Put(f.partial_army_regiment, 0x14, std::uint32_t{0x41725267U});
    Put(f.partial_army_regiment, 0x20, static_cast<void *>(f.partial_record.data()));
    Put(f.partial_army_regiment, 0x28, std::int32_t{1});
    Put(f.partial_army_regiment, 0x2C, std::int32_t{1});
    Put(f.partial_record, 8, kPersistentIds[1]);
    Put(f.partial_record, 0xC, kOrdinals[1]);
    // Its stored persistent/ordinal exists, but chunk+0x10 names the other
    // real ArRg. Preserve that input and typed partial result without repair.
    Put(f.regiment_slots, 6 * 0x10 + 8,
        static_cast<void *>(f.partial_army_regiment.data()));
  }
  f.bindings.enabled = true;
  f.bindings.unit_storage_slot = &f.unit_storage_ptr;
  f.bindings.internal_army_storage_slot = &f.army_storage_ptr;
  f.bindings.regiment_storage_slot = &f.regiment_storage_ptr;
  f.bindings.persistent_regiment_storage_slot = &f.persistent_storage_ptr;
  f.bindings.get_unit_state = State;
  f.bindings.get_army_current_soldiers = Current;
  f.bindings.get_army_maximum_soldiers = Maximum;
  f.bindings.can_regiment_replenish = CanRegiment;
  f.bindings.can_chunk_replenish = CanChunk;
  f.bindings.get_regiment_monthly_replenishment_fraction = FreshFraction;
}

std::string Number(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto converted = std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) throw std::runtime_error("integer serialization");
  return std::string(buffer.data(), converted.ptr);
}
void Int32Array(std::string &output, const std::vector<std::int32_t> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) output += ',';
    output += Number(values[index]);
  }
  output += ']';
}
void JsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}
std::string Wire(const ArmyStrengthSnapshot &row) {
  std::string output;
  xar::game::AppendArmyStrengthV1(output, row, Number, Int32Array, JsonString);
  return output;
}
ArmyStrengthSnapshot Read(Fixture &f) {
  const std::array<ArmyStrengthScope, 1> scope{{
      {kPublicId, xar::game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<ArmyStrengthSnapshot> rows;
  const auto result = xar::ck3_12002::ReadArmyStrengthsForScope(f.bindings, scope, rows);
  Require(result == xar::game::ReadArmyStrengthsResult::available &&
              rows.size() == 1 && rows.front().available,
          "production parent Strength reader stays available");
  const auto &row = rows.front();
  Require(row.army_id == kPublicId && row.native_carmy_id_observable &&
              row.native_carmy_id == kNativeId && row.regiment_count == f.regiment_count &&
              row.current_soldiers == f.current && row.maximum_soldiers == f.maximum,
          "public/native binding and parent strengths remain intact");
  Require(f.receivers_valid && f.current_calls == 1 && f.maximum_calls == 1,
          "production parent and native predicate/getter receivers are exact");
  Require(row.regiment_replenishment_records_v1.has_value() &&
              row.regiment_replenishment_records_v1->size() ==
                  static_cast<std::size_t>(f.regiment_count),
          "production parent publishes each complete-DATA regiment sibling");
  return row;
}
void Write(const std::filesystem::path &path, const std::string &wire) {
  std::ofstream file(path, std::ios::binary);
  file << "{\"army_strengths\":[" << wire << "]}\n";
  Require(static_cast<bool>(file), "production serialized fixture JSON written");
}

void FirstAndNonfirst(const std::filesystem::path &output_dir) {
  Fixture f;
  Prepare(f, false);
  const auto row = Read(f);
  const auto &snapshot = row.regiment_replenishment_records_v1->front();
  Require(snapshot.status == ArmyRegimentReplenishmentRecordsStatusV1::available &&
              snapshot.unavailable_reason.empty() &&
              snapshot.army_regiment_id == kArmyRegimentId &&
              snapshot.native_data_record_count == 3 && snapshot.records.size() == 3,
          "all physical DATA records are observed in storage order");
  for (std::size_t index = 0; index < snapshot.records.size(); ++index) {
    const auto &record = snapshot.records[index];
    Require(record.available && record.unavailable_reason.empty() &&
                record.record_index == static_cast<std::int32_t>(index) &&
                record.persistent_regiment_id == kPersistentIds[index] &&
                record.chunk_index == kOrdinals[index],
            "each record retains its own full persistent ID and stored ordinal");
  }
  const auto &first = snapshot.records[0];
  const auto &nonfirst = snapshot.records[1];
  const auto &special = snapshot.records[2];
  Require(first.current_soldiers == 100 && first.maximum_soldiers == 100 &&
              first.effective_current_soldiers == 100,
          "first physical record is full");
  Require(nonfirst.current_soldiers == 25 && nonfirst.maximum_soldiers == 100 &&
              nonfirst.effective_current_soldiers == 25,
          "nonfirst physical record deficit is independently visible");
  Require(nonfirst.native_can_replenish == true &&
              nonfirst.native_chunk_can_replenish == false &&
              special.native_can_replenish == false &&
              special.native_chunk_can_replenish == true,
          "two native eligibility answers remain independent");
  Require(first.persistent_monthly_replenishment_fraction_raw == 5000 &&
              nonfirst.persistent_monthly_replenishment_fraction_raw == 7500 &&
              nonfirst.persistent_prepared_replenishment_fraction_raw.has_value() &&
              nonfirst.persistent_prepared_replenishment_fraction_raw == 0 &&
              nonfirst.fraction_scale == 100000,
          "nonfirst fresh fraction uses its own persistent receiver; prepared zero is retained");
  Require(special.current_soldiers == 0 && special.maximum_soldiers == 60 &&
              special.effective_current_soldiers == 60 && special.state_raw == 3,
          "state3 physical zero is distinct from native effective maximum");
  const auto wire = Wire(row);
  Require(wire.find("\"regiment_replenishment_records_v1\":[") != std::string::npos &&
              wire.find("\"source\":\"native_all_data_records\"") != std::string::npos &&
              wire.find("\"record_index\":1") != std::string::npos &&
              wire.find("\"persistent_regiment_id\":570425346") != std::string::npos,
          "production serializer publishes the nonfirst mapping");
  Require(wire.find("\"persistent_prepared_replenishment_fraction_raw\":0") != std::string::npos &&
              wire.find("\"persistent_monthly_replenishment_fraction_raw\":7500") != std::string::npos &&
              wire.find("\"effective_current_soldiers\":60") != std::string::npos,
          "production serializer retains independent cached/current fractions and effective count");
  Write(output_dir / "first-and-nonfirst.json", wire);
}

void EmptyRecords(const std::filesystem::path &output_dir) {
  Fixture f;
  Prepare(f, true);
  const auto row = Read(f);
  const auto &snapshot = row.regiment_replenishment_records_v1->front();
  Require(snapshot.status == ArmyRegimentReplenishmentRecordsStatusV1::available &&
              snapshot.unavailable_reason.empty() &&
              snapshot.army_regiment_id == kArmyRegimentId &&
              snapshot.native_data_record_count == 0 && snapshot.records.empty(),
          "count0 is available empty full-DATA observation");
  const auto &partial = row.regiment_replenishment_records_v1->at(1);
  Require(partial.status == ArmyRegimentReplenishmentRecordsStatusV1::partial &&
              partial.army_regiment_id == kPartialArmyRegimentId &&
              partial.native_data_record_count == 1 && partial.records.size() == 1,
          "one genuine record mismatch remains partial without failing parent");
  const auto &record = partial.records.front();
  Require(!record.available && record.record_index == 0 &&
              record.persistent_regiment_id == kPersistentIds[1] &&
              record.chunk_index == kOrdinals[1] &&
              record.unavailable_reason ==
                  "regiment_data_record_chunk_backlink_mismatch" &&
              !record.current_soldiers.has_value() &&
              !record.persistent_monthly_replenishment_fraction_raw.has_value() &&
              !record.persistent_prepared_replenishment_fraction_raw.has_value(),
          "partial record retains stored identity/index with genuinely unavailable values");
  const auto wire = Wire(row);
  Require(wire.find("\"native_data_record_count\":0") != std::string::npos &&
              wire.find("\"records\":[]") != std::string::npos &&
              wire.find("\"army_regiment_first_record_absent\"") != std::string::npos,
          "new legal empty observation and legacy first-record absence coexist");
  Require(wire.find("\"regiment_data_record_chunk_backlink_mismatch\"") != std::string::npos &&
              wire.find("\"persistent_prepared_replenishment_fraction_raw\":null") != std::string::npos,
          "production serializer preserves partial record reason and nullable value");
  Require(wire.find("\"persistent_regiment_id\":0") == std::string::npos &&
              wire.find("\"persistent_prepared_replenishment_fraction_raw\":0") == std::string::npos,
          "empty records do not synthesize a persistent ID or prepared value");
  Write(output_dir / "empty-records.json", wire);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "production full-DATA fixture output directory required");
    const std::filesystem::path output_dir(argv[1]);
    std::filesystem::create_directories(output_dir);
    FirstAndNonfirst(output_dir);
    EmptyRecords(output_dir);
    std::cout << "PASS: 2 new complete-DATA production-reader/wire cases; "
              << checks << " explicit checks\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

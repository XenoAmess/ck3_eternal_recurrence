#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

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
using xar::game::ArmySupplyTimingStatus;

constexpr std::int32_t kNativeId = 201326670; // Native CArmy slot78.
constexpr std::int32_t kRegisteredPublicId = 301989997; // CUnit slot109; ID%30=7.
constexpr std::int32_t kMissingPublicId = 30; // ID%30=0 must not create membership.
constexpr std::size_t kManagerSecondary = 0x2A548;
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
  std::memcpy(&value, static_cast<const std::byte *>(bytes) + offset,
              sizeof value);
  return value;
}

struct Fixture {
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 110 * 0x10> unit_slots{};
  std::array<std::byte, 79 * 0x10> army_slots{};
  std::array<std::byte, 0xB0> game_state{};
  std::array<std::byte, kManagerSecondary + 0x190 + 30 * 0x18> game_data{};
  std::array<void *, 1> members{};
  void *unit_storage_ptr = unit_storage.data();
  void *army_storage_ptr = army_storage.data();
  void *regiment_storage_ptr = regiment_storage.data();
  void *game_state_ptr = game_state.data();
  ArmyBindings bindings{};
  std::int32_t public_id = kRegisteredPublicId;
  std::int32_t grace_days = 0;
  std::int32_t state_calls = 0;
  std::int32_t current_calls = 0;
  std::int32_t maximum_calls = 0;
  bool receivers_valid = true;
};

Fixture *active = nullptr;

std::int32_t State(void *unit) {
  active->receivers_valid = active->receivers_valid && unit == active->unit.data();
  ++active->state_calls;
  return 1;
}

std::int32_t Current(void *ids_array, std::uint8_t flags) {
  active->receivers_valid = active->receivers_valid &&
      ids_array == active->army.data() + 0x38 && flags == 0 &&
      Get<void *>(ids_array, 0) == nullptr &&
      Get<std::int32_t>(ids_array, 0x0C) == 0;
  ++active->current_calls;
  return 0;
}

std::int32_t Maximum(void *army) {
  active->receivers_valid = active->receivers_valid &&
      army == active->army.data() && Get<std::int32_t>(army, 0x44) == 0;
  ++active->maximum_calls;
  return 0;
}

void Prepare(Fixture &f, std::int32_t public_id, bool registered,
             std::int32_t grace_days) {
  active = &f;
  f.public_id = public_id;
  f.grace_days = grace_days;
  Put(f.unit, 0x10, public_id);
  Put(f.unit, 0x178, kNativeId);
  Put(f.army, 0x10, kNativeId);
  Put(f.army, 0x124, public_id);
  const auto unit_slot = static_cast<std::size_t>(public_id & 0x00FFFFFF);
  Put(f.unit_slots, unit_slot * 0x10 + 8, static_cast<void *>(f.unit.data()));
  Put(f.army_slots, 78 * 0x10 + 8, static_cast<void *>(f.army.data()));
  Put(f.unit_storage, 0x20, static_cast<void *>(f.unit_slots.data()));
  Put(f.unit_storage, 0x2C, std::int32_t{110});
  Put(f.army_storage, 0x20, static_cast<void *>(f.army_slots.data()));
  Put(f.army_storage, 0x2C, std::int32_t{79});
  Put(f.game_state, 0x8, std::int32_t{0});
  Put(f.game_state, 0x9C, std::int32_t{0});
  Put(f.game_state, 0xA0, static_cast<void *>(f.game_data.data()));
  Put(f.army, 0x188, std::int64_t{0});
  Put(f.army, 0x190, std::int64_t{0});
  if (registered) {
    f.members[0] = f.army.data();
    Put(f.game_data, kManagerSecondary + 0x190,
        static_cast<void *>(f.members.data()));
    Put(f.game_data, kManagerSecondary + 0x198, std::int32_t{1});
    Put(f.game_data, kManagerSecondary + 0x19C, std::int32_t{1});
  }
  // The other bucket headers are genuine empty pointer/capacity/count tuples.
  f.bindings.enabled = true;
  f.bindings.unit_storage_slot = &f.unit_storage_ptr;
  f.bindings.internal_army_storage_slot = &f.army_storage_ptr;
  f.bindings.regiment_storage_slot = &f.regiment_storage_ptr;
  f.bindings.game_state_slot =
      reinterpret_cast<decltype(f.bindings.game_state_slot)>(&f.game_state_ptr);
  f.bindings.get_unit_state = State;
  f.bindings.get_army_current_soldiers = Current;
  f.bindings.get_army_maximum_soldiers = Maximum;
  f.bindings.timing_bindings = xar::ck3_12003::ArmySupplyTimingBindings{true,
                                                                    &f.grace_days};
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
      {f.public_id, xar::game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<ArmyStrengthSnapshot> rows;
  const auto result = xar::ck3_12002::ReadArmyStrengthsForScope(f.bindings, scope, rows);
  Require(result == xar::game::ReadArmyStrengthsResult::available &&
              rows.size() == 1 && rows.front().available,
          "production parent Strength reader stays available");
  const auto &row = rows.front();
  Require(row.army_id == f.public_id && row.native_carmy_id_observable &&
              row.native_carmy_id == kNativeId && row.regiment_count == 0 &&
              row.current_soldiers == 0 && row.maximum_soldiers == 0,
          "parent strength zero and public/native bindings remain intact");
  Require(f.receivers_valid && f.current_calls == 1 && f.maximum_calls == 1,
          "actual production strength getters use exact receivers");
  Require(row.army_update_clock_v1.has_value(),
          "production parent reader publishes timing sibling");
  return row;
}

void Write(const std::filesystem::path &path, const std::string &wire) {
  std::ofstream file(path, std::ios::binary);
  file << "{\"army_strengths\":[" << wire << "]}\n";
  Require(static_cast<bool>(file), "production serialized fixture JSON written");
}

void RegisteredPhaseZero(const std::filesystem::path &output_dir) {
  Fixture f;
  Prepare(f, kRegisteredPublicId, true, 0);
  const auto unit_before = f.unit;
  const auto army_before = f.army;
  const auto row = Read(f);
  const auto &clock = *row.army_update_clock_v1;
  Require(clock.status == ArmySupplyTimingStatus::available && clock.ready &&
              clock.unavailable_reason.empty(),
          "native pointer-matched membership is available and ready");
  Require(clock.current_date_raw == 0 && clock.native_day_index == 0 &&
              clock.selected_bucket_phase == 0 && clock.observed_army_bucket_phase == 0,
          "legal date/day/phase zero remains observable");
  Require(kRegisteredPublicId % 30 == 7 && clock.observed_army_bucket_phase != 7,
          "observed native pointer bucket does not follow public ID modulus");
  Require(clock.last_supply_update_date_storage_raw64 == 0 &&
              clock.last_supply_update_date_raw == 0 &&
              clock.grace_anchor_date_storage_raw64 == 0 &&
              clock.grace_anchor_date_raw == 0 && clock.loaded_grace_days == 0,
          "legal zero storage dates, low dates and loaded grace are retained");
  const auto wire = Wire(row);
  Require(wire.find("\"army_update_clock_v1\":{") != std::string::npos &&
              wire.find("\"status\":\"available\",\"ready\":true") != std::string::npos &&
              wire.find("\"observed_army_bucket_phase\":0") != std::string::npos &&
              wire.find("\"current_date_raw\":0") != std::string::npos &&
              wire.find("\"loaded_grace_days\":0") != std::string::npos,
          "actual shared serializer retains available timing zeros");
  Require(wire.find("\"army_id\":301989997") != std::string::npos &&
              wire.find("\"native_carmy_id\":201326670") != std::string::npos &&
              wire.find("\"war_ids\":[]") != std::string::npos,
          "serialized parent row retains public/native/war bindings");
  Require(f.unit == unit_before && f.army == army_before,
          "registered production timing observation leaves native objects unchanged");
  Write(output_dir / "phase-zero.json", wire);
}

void NotRegisteredKeepsBindings(const std::filesystem::path &output_dir) {
  Fixture f;
  Prepare(f, kMissingPublicId, false, 7);
  Put(f.army, 0x188, std::int64_t{8589934592});
  Put(f.army, 0x190, std::int64_t{12884901888});
  const auto unit_before = f.unit;
  const auto army_before = f.army;
  const auto row = Read(f);
  const auto &clock = *row.army_update_clock_v1;
  Require(clock.status == ArmySupplyTimingStatus::not_registered && clock.ready &&
              clock.unavailable_reason.empty(),
          "complete empty native buckets are valid observed nonmembership");
  Require(kMissingPublicId % 30 == 0 &&
              !clock.observed_army_bucket_phase.has_value(),
          "missing actual pointer is not synthesized into public ID bucket0");
  Require(clock.current_date_raw == 0 && clock.native_day_index == 0 &&
              clock.selected_bucket_phase == 0 && clock.loaded_grace_days == 7,
          "other available clock values survive nonmembership");
  Require(clock.last_supply_update_date_storage_raw64 == 8589934592 &&
              clock.last_supply_update_date_raw == 0 &&
              clock.grace_anchor_date_storage_raw64 == 12884901888 &&
              clock.grace_anchor_date_raw == 0,
          "storage64 is retained separately from legal date low32 zero");
  const auto wire = Wire(row);
  Require(wire.find("\"status\":\"not_registered\",\"ready\":true") != std::string::npos &&
              wire.find("\"observed_army_bucket_phase\":null") != std::string::npos &&
              wire.find("\"loaded_grace_days\":7") != std::string::npos &&
              wire.find("\"last_supply_update_date_storage_raw64\":8589934592") != std::string::npos,
          "actual shared serializer preserves nullable membership and independent values");
  Require(wire.find("\"army_id\":30") != std::string::npos &&
              wire.find("\"native_carmy_id\":201326670") != std::string::npos &&
              wire.find("\"war_ids\":[]") != std::string::npos,
          "nonmembership keeps serialized parent binding intact");
  Require(f.unit == unit_before && f.army == army_before,
          "nonmembership production timing observation remains readonly");
  Write(output_dir / "not-registered.json", wire);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "production timing fixture output directory required");
    const std::filesystem::path output_dir(argv[1]);
    std::filesystem::create_directories(output_dir);
    RegisteredPhaseZero(output_dir);
    NotRegisteredKeepsBindings(output_dir);
    std::cout << "PASS: 2 new timing production-reader/wire cases; "
              << checks << " explicit checks\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

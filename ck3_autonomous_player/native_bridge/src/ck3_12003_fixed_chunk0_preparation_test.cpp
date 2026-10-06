#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr std::int32_t kArRg = 117440517;
constexpr std::int32_t kRegi = 301989889;
void *persistent_receiver = nullptr;
void *physical_chunk0 = nullptr;
bool fixed_permission = false;
bool fraction_readable = true;
std::int64_t fraction_raw = 10000;
int fixed_calls = 0;
int fraction_calls = 0;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template<class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
template<class T, std::size_t N>
T Get(const std::array<std::byte, N> &bytes, std::size_t offset) {
  T value{};
  std::memcpy(&value, bytes.data() + offset, sizeof value);
  return value;
}
bool Permission(void *persistent, void *chunk) {
  Require(persistent == persistent_receiver, "permission receiver is containing persistent");
  if (chunk == physical_chunk0) { ++fixed_calls; return fixed_permission; }
  return true; // DATA chunk1 differs from preparation's fixed physicalchunk0.
}
bool ChunkPermission(void *) { return false; }
std::int64_t *Fraction(void *persistent, std::int64_t *out) {
  Require(persistent == persistent_receiver, "fresh getter has containing receiver");
  ++fraction_calls;
  if (!fraction_readable) return nullptr;
  *out = fraction_raw;
  return out;
}

struct Fixture {
  std::array<std::byte, 0x60> raised{};
  std::array<std::byte, 0x200> persistent{};
  std::array<std::byte, 0x40> definition{};
  std::array<std::byte, 0x20> data{};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x20> slots{};
  void *storage_ptr = nullptr;
  xar::ck3_12002::ArmyBindings bindings{};

  Fixture() {
    persistent_receiver = persistent.data();
    physical_chunk0 = persistent.data() + 0x18;
    storage_ptr = storage.data();
    Put(raised, 0x10, kArRg);
    Put(raised, 0x14, std::uint32_t{0x41725267U});
    Put(raised, 0x20, static_cast<void *>(data.data()));
    Put(raised, 0x28, std::int32_t{2});
    Put(raised, 0x2C, std::int32_t{2});
    for (const std::size_t offset : {std::size_t{0}, std::size_t{0x10}}) {
      Put(data, offset + 8, kRegi);
      Put(data, offset + 0xC, std::int32_t{1});
    }
    Put(persistent, 0x10, kRegi);
    Put(persistent, 0x14, std::uint32_t{0x52656769U});
    for (std::int32_t index = 0; index < 2; ++index) {
      const auto base = std::size_t{0x18} + static_cast<std::size_t>(index) * 0x24;
      Put(persistent, base, std::int32_t{100});
      Put(persistent, base + 4, std::int32_t{80});
      Put(persistent, base + 8, kRegi);
      Put(persistent, base + 0xC, index);
      Put(persistent, base + 0x10, kArRg);
    }
    Put(persistent, 0x118, static_cast<void *>(definition.data()));
    Put(persistent, 0x138, std::int32_t{0});
    Put(persistent, 0x148, std::int64_t{0});
    Put(definition, 0x38, std::uint32_t{0x11111111U});
    Put(slots, 0x18, static_cast<void *>(persistent.data()));
    Put(storage, 0x20, static_cast<void *>(slots.data()));
    Put(storage, 0x2C, std::int32_t{2});
    bindings.enabled = true;
    bindings.persistent_regiment_storage_slot = &storage_ptr;
    bindings.can_regiment_replenish = Permission;
    bindings.can_chunk_replenish = ChunkPermission;
    bindings.get_regiment_monthly_replenishment_fraction = Fraction;
  }

  xar::game::ArmyStrengthSnapshot Capture(bool empty = false) {
    xar::game::ArmyStrengthSnapshot strength{};
    strength.available = true;
    strength.army_id = 11;
    strength.native_carmy_id_observable = true;
    strength.native_carmy_id = 12;
    strength.current_soldiers = empty ? 0 : 160;
    strength.maximum_soldiers = empty ? 0 : 200;
    strength.regiment_count = empty ? 0 : 1;
    strength.regiment_replenishment_records_v1.emplace();
    if (!empty) strength.regiment_replenishment_records_v1->push_back(
        xar::ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(
            bindings, raised.data(), kArRg));
    fixed_calls = 0;
    fraction_calls = 0;
    strength.fixed_chunk0_preparation_inputs_v1 =
        xar::ck3_12003::ReadFixedChunk0PreparationInputsV1(bindings, strength);
    Require(Get<std::int64_t>(persistent, 0x148) == 0,
            "readonly preparation capture never writes148");
    if (!empty && strength.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0]
            .containing_guard_138_raw.has_value()) {
      Require(fixed_calls == 1 && fraction_calls == 1,
              "one physical persistent input despite duplicate selected DATA references");
    }
    return strength;
  }
};

void Emit(const std::filesystem::path &directory, std::string_view name,
          const xar::game::ArmyStrengthSnapshot &strength) {
  std::string wire;
  xar::game::AppendArmyStrengthV1(wire, strength,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &ids) {
        out += '[';
        bool first = true;
        for (const auto id : ids) { if (!first) out += ','; first = false; out += std::to_string(id); }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  Require(wire.find("\"fixed_chunk0_preparation_inputs_v1\":") != std::string::npos,
          "whole production Strength serializer emits the own leaf");
  std::ofstream stream(directory / std::string{name}, std::ios::binary);
  stream << wire << '\n';
  Require(stream.good(), "compiled wire written");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture output_directory");
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    Fixture fixture;
    auto row = fixture.Capture();
    const auto &ordinary = row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0];
    Require(ordinary.containing_guard_138_raw == 0 &&
                ordinary.containing_definition_magic_38 == 0x11111111U &&
                ordinary.native_fixed_chunk0_can_replenish == false && ordinary.fresh_fraction_raw == 10000,
            "ordinary bypass operands keep nativefalse/fresh separate from cache0");
    Emit(directory, "ordinary_bypass.json", row);

    Put(fixture.persistent, 0x138, std::int32_t{1});
    Put(fixture.definition, 0x38, std::uint32_t{0x4744624FU});
    fraction_readable = false;
    row = fixture.Capture();
    Require(row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0].native_fixed_chunk0_can_replenish == false &&
                !row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0].fresh_fraction_raw,
            "false is a read value; failed fresh getter is independently null");
    Emit(directory, "permission_false_missing_unused_fresh.json", row);

    fraction_readable = true;
    fixed_permission = true;
    fraction_raw = -123;
    Put(fixture.definition, 0x38, std::uint32_t{0x11111111U});
    row = fixture.Capture();
    Require(row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0].fresh_fraction_raw == -123,
            "signed fresh fraction survives without clamping");
    Emit(directory, "permission_true_negative_fresh.json", row);

    fixed_permission = false;
    fraction_raw = 0;
    Put(fixture.persistent, 0x138, std::int32_t{0});
    row = fixture.Capture();
    Require(row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0].fresh_fraction_raw == 0,
            "valid fresh zero differs from readfailure");
    Emit(directory, "ordinary_zero_fresh.json", row);

    // Real registry generation mismatch is unresolved, without substituting
    // selected chunk permission or old observed prepared cache.
    Put(fixture.persistent, 0x10, std::int32_t{kRegi + 0x01000000});
    row = fixture.Capture();
    Require(!row.fixed_chunk0_preparation_inputs_v1->persistent_regiments[0].containing_guard_138_raw,
            "unresolved persistent retains unavailable input row");
    Emit(directory, "unavailable_persistent_receiver.json", row);

    row = fixture.Capture(true);
    Require(row.fixed_chunk0_preparation_inputs_v1->referenced_persistent_ids_complete &&
                row.fixed_chunk0_preparation_inputs_v1->persistent_regiments.empty() &&
                row.fixed_chunk0_preparation_inputs_v1->status == xar::game::FixedChunk0PreparationInputStatusV1::available,
            "legal empty completeDATA yields no dummy persistent/prepared input");
    Emit(directory, "empty_scoped_DATA.json", row);
    std::cout << "PASS: six current preparation input wires, readonly cache preserved\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

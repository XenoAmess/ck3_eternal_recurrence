#include "xar_bridge/ck3_12003_scoped_ordered_refill_core.hpp"
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar;
template<std::size_t N> using Blob = std::array<std::byte, N>;
template<class T, class Buffer> void Store(Buffer &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof value);
}
void Require(bool good, const char *message) { if (!good) throw std::runtime_error(message); }
void *valid_arrg = nullptr, *invalid_arrg = nullptr, *resolved_unit = nullptr;
std::int32_t holder_id = 777;
void *ArRgReference(const void *reference) {
  std::int32_t id{}; std::memcpy(&id, reference, sizeof id);
  return id == -1 ? invalid_arrg : valid_arrg;
}
void *UnitReference(const void *) { return resolved_unit; }
bool NotInCombat(void *) { return false; }
bool PositionEligible(void *) { return true; }
std::int32_t *Holder(void *, std::int32_t *out) { *out = holder_id; return out; }
void Text(std::string &out, std::string_view value) {
  out += '"';
  for (char c : value) { if (c == '"' || c == '\\') out += '\\'; out += c; }
  out += '"';
}
auto Number = [](auto value) { return std::to_string(value); };

struct Storage {
  Blob<0x30> header{};
  std::vector<std::byte> entries;
  void *pointer = header.data();
  Storage(std::int32_t id, void *object) : entries((static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16 + 16) {
    Store(header, 0x20, static_cast<void *>(entries.data()));
    Store(header, 0x2C, static_cast<std::int32_t>(entries.size() / 16));
    Store(entries, (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16 + 8, object);
  }
};
struct Fixture {
  Blob<0x2A600> game_data{};
  Blob<0xB0> game_state{};
  Blob<0x160> persistent{};
  Blob<0x40> definition{};
  Blob<0x900> province{};
  Blob<0x180> unit{};
  Blob<0x200> army{};
  Blob<0x150> arrg{};
  Blob<0x20> absent_arrg{};
  Blob<0x20> character{};
  Blob<0x20> other_character{};
  std::array<std::int32_t, 5> persistent_order{90001, 50001, 90002, 50001, 90001};
  std::array<std::int32_t, 4> army_order{99, 12, 99, 12};
  Storage persistent_storage{50001, persistent.data()};
  Storage army_storage{12, army.data()};
  Storage character_storage{888, other_character.data()};
  void *game_state_pointer = game_state.data();
  void *fallback_character = character.data();
  void *fallback_army = army.data();
  void *fallback_persistent = persistent.data();
  void *fallback_province = province.data();
  ck3_12002::ArmyBindings bindings{};
  std::vector<game::ArmyRegimentReplenishmentRecordsSnapshotV1> data;

  Fixture() {
    Store(game_state, 0xA0, static_cast<void *>(game_data.data()));
    Store(game_data, 0x2A570, static_cast<void *>(persistent_order.data()));
    Store(game_data, 0x2A578, std::int32_t{5}); Store(game_data, 0x2A57C, std::int32_t{5});
    Store(game_data, 0x2A590, static_cast<void *>(army_order.data()));
    Store(game_data, 0x2A598, std::int32_t{4}); Store(game_data, 0x2A59C, std::int32_t{4});
    Store(persistent, 0x10, std::int32_t{50001}); Store(persistent, 0x14, std::uint32_t{0x52656769});
    Store(persistent, 0x118, static_cast<void *>(definition.data()));
    Store(persistent, 0x120, static_cast<void *>(province.data()));
    Store(province, 0x10, std::int32_t{1}); Store(province, 0x788, std::int32_t{-1});
    Store(province, 0x73C, std::int32_t{-1}); Store(province, 0x85C, std::uint32_t{0x50726F76});
    Store(unit, 0x10, std::int32_t{11}); Store(unit, 0x20, static_cast<void *>(province.data()));
    Store(unit, 0x174, std::int32_t{777}); Store(unit, 0x178, std::int32_t{12});
    Store(army, 0x10, std::int32_t{12}); Store(army, 0x124, std::int32_t{11}); Store(army, 0x44, std::int32_t{1});
    Store(arrg, 0x10, std::int32_t{11001}); Store(arrg, 0x14, std::uint32_t{0x41725267});
    Store(arrg, 0x140, std::int32_t{12}); Store(absent_arrg, 0x10, std::int32_t{-1});
    Store(character, 0x18, std::int32_t{777});
    Store(other_character, 0x18, std::int32_t{888});
    Store(character_storage.entries, 777 * 16 + 8, static_cast<void *>(character.data()));
    for (std::int32_t index = 0; index < 7; ++index) {
      const auto base = 0x18 + index * 0x24;
      Store(persistent, base, std::int32_t{index == 0 ? 100 : index == 1 ? 20 : 0});
      Store(persistent, base + 4, std::int32_t{index == 0 ? 80 : index == 1 ? 20 : 0});
      Store(persistent, base + 8, std::int32_t{50001}); Store(persistent, base + 0xC, index);
      Store(persistent, base + 0x10, std::int32_t{index == 0 ? 11001 : -1});
    }
    Store(persistent, 0x148, std::int64_t{10000});
    valid_arrg = arrg.data(); invalid_arrg = absent_arrg.data(); resolved_unit = unit.data(); holder_id = 777;
    bindings.enabled = true; bindings.game_state_slot = &game_state_pointer;
    bindings.persistent_regiment_storage_slot = &persistent_storage.pointer;
    bindings.internal_army_storage_slot = &army_storage.pointer;
    auto &native = bindings.scoped_ordered_refill_bindings;
    native.enabled = true; native.persistent_fallback_slot = &fallback_persistent;
    native.army_fallback_slot = &fallback_army; native.character_storage_slot = &character_storage.pointer;
    native.character_fallback_slot = &fallback_character;
    native.unit_position_province_fallback_slot = &fallback_province;
    native.resolve_arrg_reference = ArRgReference; native.resolve_unit_reference = UnitReference;
    native.is_army_in_combat = NotInCombat; native.is_unit_position_eligible = PositionEligible;
    native.read_province_holder = Holder;
    game::ArmyRegimentReplenishmentRecordsSnapshotV1 snapshot{};
    snapshot.status = game::ArmyRegimentReplenishmentRecordsStatusV1::available;
    snapshot.army_regiment_id = 11001; snapshot.native_data_record_count = 2;
    snapshot.native_loss_writer_skipped = false;
    for (std::int32_t index = 0; index < 2; ++index) {
      game::ArmyRegimentReplenishmentRecordV1 record{};
      record.available = true; record.record_index = index; record.persistent_regiment_id = 50001;
      record.chunk_index = 0; record.chunk_army_regiment_id = 11001;
      record.current_soldiers = 80; record.maximum_soldiers = 100; record.effective_current_soldiers = 80;
      record.state_raw = 0; record.native_can_replenish = true; record.native_chunk_can_replenish = true;
      record.persistent_monthly_replenishment_fraction_raw = 90000;
      record.persistent_prepared_replenishment_fraction_raw = 10000;
      snapshot.records.push_back(record);
    }
    data.push_back(snapshot);
  }
  void Fraction(std::int64_t fraction) {
    Store(persistent, 0x148, fraction);
    for (auto &record : data[0].records) record.persistent_prepared_replenishment_fraction_raw = fraction;
  }
  game::ArmyStrengthSnapshot Capture() {
    const auto before = persistent;
    auto inputs = ck3_12003::ReadScopedOrderedRefillInputs12003(bindings, army.data(), unit.data(), data);
    Require(persistent == before, "readonly collector mutated physical/prepared inputs");
    game::ArmyStrengthSnapshot row{};
    row.available = true; row.army_id = 11; row.native_carmy_id_observable = true; row.native_carmy_id = 12;
    row.regiment_count = 1; row.current_soldiers = 160; row.maximum_soldiers = 200;
    row.current_supply_change_monthly_raw = 700000;
    row.regiment_strengths.emplace(); game::ArmyRegimentStrengthSnapshot strength{};
    strength.army_regiment_id = 11001; strength.current_soldiers = 160; strength.maximum_soldiers = 200;
    row.regiment_strengths->push_back(strength);
    row.regiment_replenishment_records_v1 = data; row.scoped_ordered_refill_inputs_v1 = std::move(inputs);
    return row;
  }
};
void Wire(const std::filesystem::path &directory, const char *name, const xar::game::ArmyStrengthSnapshot &row) {
  if (directory.empty()) return;
  std::filesystem::create_directories(directory);
  std::string output = "{\"status\":\"available\",\"army_strengths\":[";
  xar::game::AppendArmyStrengthV1(output, row, Number,
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t index = 0; index < values.size(); ++index) {
          if (index != 0) out += ',';
          out += Number(values[index]);
        }
        out += ']';
      }, Text);
  output += "],\"native_readiness\":{\"current_strength\":true,\"full_monthly\":false}}\n";
  std::ofstream file(directory / name, std::ios::binary); file << output;
  Require(static_cast<bool>(file), "new native wire could not be written");
}
} // namespace

int main(int argc, char **argv) {
  try {
    std::filesystem::path directory;
    if (argc == 3 && std::string_view(argv[1]) == "--wire-dir") directory = argv[2];
    constexpr std::uintptr_t image = 0x140000000ULL;
    const auto bound = xar::ck3_12003::BindScopedOrderedRefillInputs12003(image, xar::ck3_12003::kExecutableSha256);
    Require(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.resolve_arrg_reference) == image + 0xC171A0 &&
        reinterpret_cast<std::uintptr_t>(bound.resolve_unit_reference) == image + 0xAEAA20 &&
        reinterpret_cast<std::uintptr_t>(bound.army_fallback_slot) == image + 0x5D1DE50,
        "exact .3 ordered source bindings differ");
    Require(!xar::ck3_12003::BindScopedOrderedRefillInputs12003(image, "other-build").enabled,
            "other build must omit exact .3 observer");
    Fixture fixture;
    auto row = fixture.Capture(); const auto &inputs = *row.scoped_ordered_refill_inputs_v1;
    Require(inputs.status == "available" && inputs.persistent_occurrences.size() == 2 &&
        inputs.persistent_occurrences[0].stored_index == 1 && inputs.persistent_occurrences[1].stored_index == 3 &&
        inputs.persistent_regiments[0].chunks.size() == 7 && inputs.army_refresh_occurrence_indices == std::vector<std::int32_t>{1, 3},
        "real matching order/complete seven capture failed");
    Wire(directory, "ordered-repeat.json", row);
    fixture.Fraction(1); Wire(directory, "qualified-zero-cleanup.json", fixture.Capture());
    fixture.Fraction(0); Wire(directory, "nonpositive-suppression.json", fixture.Capture());
    fixture.Fraction(10000); holder_id = 888;
    auto held = fixture.Capture();
    Require(held.scoped_ordered_refill_inputs_v1->persistent_regiments[0].chunks[0].native_unit_position_eligible == true,
            "independent current native position value was not captured");
    Wire(directory, "native-position-context.json", held);
    Store(fixture.persistent, 0x120, static_cast<void *>(nullptr));
    auto partial = fixture.Capture();
    Require(partial.scoped_ordered_refill_inputs_v1->status == "partial" && partial.current_soldiers == 160,
            "missing required context must preserve independent strength");
    Wire(directory, "partial-owner-context.json", partial);
    std::cout << "scoped ordered refill native observer GREEN\n";
    return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}

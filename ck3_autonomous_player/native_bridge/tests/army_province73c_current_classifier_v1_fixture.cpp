#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    const auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};

struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *table;
  explicit Registry(Memory &m)
      : memory(m), slot(m.Allocate(8U)), fallback_slot(m.Allocate(8U)),
        store(m.Allocate(0x30U)), table(m.Allocate(3U * 16U)) {
    memory.Put(slot, 0U, store);
    memory.Put(store, 0x20U, table);
    memory.Put(store, 0x2CU, std::uint32_t{3U});
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, static_cast<std::size_t>(full & 0xFFFFFFU) * 16U + 8U, object);
    memory.Put(object, full_offset, full);
  }
};

constexpr std::uint32_t kArmy = 0x22000001U, kAssociatedArmy = 0x22000002U;
constexpr std::uint32_t kUnit = 0x11000001U, kAssociatedUnit = 0x11000002U;
constexpr std::uint32_t kCharacter = 0x33000001U, kSiege = 0x44000001U;
const void *expected_character = nullptr, *expected_province = nullptr;
std::int32_t current_classification = 0;
std::size_t native_callback_count = 0U;

std::int32_t CurrentClassification(const void *character, const void *province, const void *third) {
  Require(character == expected_character, "classifier must use the selected associated Character");
  Require(province == expected_province, "classifier must use the original Unit+20 Province");
  Require(third == nullptr, "classifier must retain the actual null third argument");
  ++native_callback_count;
  return current_classification;
}

struct Fixture {
  Memory memory;
  Registry units{memory}, armies{memory}, characters{memory}, sieges{memory};
  ck3_12003::CurrentDailyAssaultRosterAdmissionBindings12003 bindings{};
  void *state_slot = memory.Allocate(8U), *state = memory.Allocate(0xA8U);
  void *data = memory.Allocate(0x2A540U + 0x150U);
  void *manager = static_cast<std::byte *>(data) + 0x2A540U;
  void *roster = memory.Allocate(4U), *pending = memory.Allocate(2U * 0x28U);
  void *army = memory.Allocate(0x210U), *associated_army = memory.Allocate(0x210U);
  void *unit = memory.Allocate(0x180U), *associated_unit = memory.Allocate(0x180U);
  void *province = memory.Allocate(0x858U), *character = memory.Allocate(0x20U);
  void *siege = memory.Allocate(0x450U);

  Fixture() {
    bindings.enabled = true;
    bindings.game_state_slot = state_slot;
    bindings.army_registry_slot = armies.slot; bindings.army_fallback_slot = armies.fallback_slot;
    bindings.unit_registry_slot = units.slot; bindings.unit_fallback_slot = units.fallback_slot;
    bindings.character_registry_slot = characters.slot; bindings.character_fallback_slot = characters.fallback_slot;
    bindings.siege_registry_slot = sieges.slot; bindings.siege_fallback_slot = sieges.fallback_slot;
    bindings.get_current_province73c_classification = CurrentClassification;
    bindings.read_memory = Memory::Read; bindings.read_context = &memory;
    memory.Put(state_slot, 0U, state); memory.Put(state, 0xA0U, data);
    memory.Put(manager, 0x50U, roster); memory.Put(manager, 0x5CU, std::int32_t{1});
    memory.Put(manager, 0x74U, std::int32_t{0}); memory.Put(roster, 0U, kArmy);
    armies.Add(kArmy, army, 0x10U); armies.Add(kAssociatedArmy, associated_army, 0x10U);
    units.Add(kUnit, unit, 0x10U); units.Add(kAssociatedUnit, associated_unit, 0x10U);
    characters.Add(kCharacter, character, 0x18U); sieges.Add(kSiege, siege, 8U);
    memory.Put(army, 0x124U, kUnit);
    memory.Put(unit, 0x18U, std::uint32_t{0U}); memory.Put(unit, 0x20U, province);
    memory.Put(unit, 0x170U, std::int32_t{0}); memory.Put(unit, 0x178U, kAssociatedArmy);
    memory.Put(associated_army, 0x1D4U, std::uint8_t{0U});
    memory.Put(associated_army, 0x1ECU, std::uint8_t{0U});
    memory.Put(associated_army, 0x124U, kAssociatedUnit);
    memory.Put(associated_unit, 0x174U, kCharacter);
    memory.Put(province, 0x10U, std::uint32_t{2619U});
    memory.Put(province, 0x73CU, std::uint32_t{0xFFFFFFFFU});
    memory.Put(province, 0x788U, kSiege); memory.Put(province, 0x850U, std::int32_t{1});
    memory.Put(siege, 0x44CU, std::uint8_t{1U});
    memory.Put(manager, 0x138U, pending); memory.Put(manager, 0x144U, std::int32_t{0});
    memory.Put(manager, 0x148U, std::uint8_t{0U});
    memory.Put(pending, 4U, std::uint8_t{0U}); memory.Put(pending, 0x28U + 4U, std::uint8_t{0xFFU});
    expected_character = character; expected_province = province; native_callback_count = 0U;
  }
};

void JsonString(std::string &out, std::string_view value) {
  out += '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}

void WritePacket(const std::filesystem::path &directory, std::string_view name,
                 const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &roster) {
  game::ArmyStrengthSnapshot row{};
  row.available = true; row.army_id = static_cast<std::int32_t>(kUnit);
  row.native_carmy_id_observable = true; row.native_carmy_id = static_cast<std::int32_t>(kArmy);
  row.regiment_count = 1; row.current_soldiers = 120; row.maximum_soldiers = 150;
  row.ai_base_power_raw = 18'000'000;
  row.current_daily_assault_roster_admission_v1 = roster;
  std::string packet = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"province73c-fixture\",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  game::AppendArmyStrengthV1(packet, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0U; i < values.size(); ++i) {
          if (i) out += ',';
          out += std::to_string(values[i]);
        }
        out += ']';
      }, JsonString);
  packet += "]}}";
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << packet << '\n';
  Require(static_cast<bool>(output), "whole production Army command_result packet write failed");
}

void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto exact = ck3_12003::BindCurrentDailyAssaultRosterAdmission12003(base, ck3_12003::kExecutableSha256);
  Require(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.get_current_province73c_classification) == base + 0x2C099F0U,
          "exact .3 binding must select the closed native classification entry");
  const auto wrong = ck3_12003::BindCurrentDailyAssaultRosterAdmission12003(base, "wrong-build");
  Require(!wrong.enabled && !wrong.get_current_province73c_classification,
          "wrong-build binding must remain unassigned");
}

void ClassificationCase(const std::filesystem::path &directory, std::int32_t classification) {
  Fixture fixture;
  current_classification = classification;
  const auto roster = ck3_12003::ReadCurrentDailyAssaultRosterAdmission12003(fixture.bindings);
  Require(roster.ready && roster.conditional_admission_ready && roster.occurrences.size() == 1U,
          "current synthetic roster must close the classification-dependent admission");
  const auto &occurrence = roster.occurrences[0];
  const auto &gate = occurrence.gate;
  Require(gate.ready && gate.native_2c099f0_returned &&
              gate.native_2c099f0_classification_raw_i32 == classification &&
              gate.verdict == (classification == 0) && native_callback_count == 1U,
          "native raw classification must retain 0/1/2 and use EAX==0 exactly once");
  Require(gate.native_2c099f0_character_identity == gate.associated_character_resolution.object_identity &&
              gate.native_2c099f0_province_identity == gate.original_unit_province_identity &&
              gate.native_2c099f0_third_argument_is_null == true,
          "classification provenance must preserve the selected actual operands");
  Require(occurrence.army_append_ready && occurrence.army_append == (classification == 0) &&
              occurrence.arrg_append_ready && !roster.actual_next_callback_ready &&
              !roster.actual_tomorrow_roster_ready && !roster.full_daily_assault_ready,
          "current conditional append must keep future callback boundaries false");
  WritePacket(directory, "case-" + std::to_string(classification), roster);
}

void UnboundCase(const std::filesystem::path &directory) {
  Fixture fixture;
  fixture.bindings.get_current_province73c_classification = nullptr;
  const auto roster = ck3_12003::ReadCurrentDailyAssaultRosterAdmission12003(fixture.bindings);
  Require(!roster.ready && roster.occurrences.size() == 1U, "unbound demanded classifier must remain partial");
  const auto &gate = roster.occurrences[0].gate;
  Require(!gate.ready && !gate.verdict && !gate.native_2c099f0_returned &&
              !gate.native_2c099f0_classification_raw_i32 && native_callback_count == 0U &&
              gate.unavailable_reason == "province_73c_2c099f0_getter_unbound" &&
              gate.native_2c099f0_character_identity == gate.associated_character_resolution.object_identity &&
              gate.native_2c099f0_province_identity == gate.original_unit_province_identity &&
              gate.native_2c099f0_third_argument_is_null == true,
          "unbound demand must preserve operands and a precise missing reason");
  WritePacket(directory, "case-unbound", roster);
}

void NotDemandedCase(const std::filesystem::path &directory) {
  Fixture fixture;
  fixture.memory.Put(fixture.unit, 0x18U, std::uint32_t{1U});
  const auto roster = ck3_12003::ReadCurrentDailyAssaultRosterAdmission12003(fixture.bindings);
  Require(roster.ready && roster.occurrences.size() == 1U, "decisive original-unit guard must remain available");
  const auto &gate = roster.occurrences[0].gate;
  Require(gate.ready && gate.verdict == false && native_callback_count == 0U &&
              !gate.native_2c099f0_returned && !gate.native_2c099f0_classification_raw_i32 &&
              !gate.native_2c099f0_character_identity && !gate.native_2c099f0_province_identity &&
              !gate.native_2c099f0_third_argument_is_null,
          "unreached sentinel must not fabricate native classification inputs");
  WritePacket(directory, "case-not-demanded", roster);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    ExactBinding();
    ClassificationCase(directory, 0); ClassificationCase(directory, 1); ClassificationCase(directory, 2);
    UnboundCase(directory); NotDemandedCase(directory);
    std::cout << "province73c current classifier fixture GREEN: 5 synthetic whole Army packets\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "province73c current classifier fixture RED: " << error.what() << '\n';
    return 1;
  }
}

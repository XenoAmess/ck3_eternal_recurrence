// SOURCE_PREPARED/NOTRUN. Root owns first build and execution.
// Every scene enters the actual4 whole reader and production row serializer.
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_current_unit_new_date_schedule_inputs.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
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
#include <utility>
#include <vector>

namespace {
using namespace xar;
namespace current = ck3_12004;
constexpr std::int32_t kUnit = 0x01000001;
constexpr std::int32_t kArmy = 0x02000001;
constexpr std::int32_t kRegiment = 0x03000001;
constexpr std::int32_t kDate = 53288448;
constexpr std::uintptr_t kImageBase = 0x140000000ULL;
constexpr std::array<std::string_view, 3> kScenes{
    "gaps_repeats", "empty_zero", "typed_unavailable"};

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture input store out of range");
  std::memcpy(object.data() + offset, &value, sizeof value);
}
struct Inputs {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x2AA00> game_data{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x210> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x18> province{};
  std::array<void *, 2> provinces{};
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  std::array<std::uint32_t, 4> scheduled_unit_ids{
      0x02000001U, static_cast<std::uint32_t>(kUnit), 0xFFFFFFFFU,
      static_cast<std::uint32_t>(kUnit)};
  std::array<std::uintptr_t, 4> secondary_vtable{};
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Counters {
  std::size_t current_soldiers = 0, maximum_soldiers = 0;
  std::size_t supply_capacity = 0, attrition_fraction = 0, monthly_supply = 0;
  bool abi_matches = true;
  std::vector<std::string> events;
};
struct Fixture;
Fixture *active = nullptr;
std::int32_t CurrentSoldiers(void *, std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int64_t *SupplyCapacity(std::int64_t *, void *, void *);
std::int64_t *Attrition(void *, std::int64_t *, void *);
std::int64_t *MonthlySupply(void *, std::int64_t *, void *, void *);

struct Fixture {
  Inputs input{};
  void *game_slot = input.game_state.data();
  void *unit_slot = input.unit_storage.data();
  void *army_slot = input.army_storage.data();
  void *regiment_slot = input.regiment_storage.data();
  current::ArmyBindings bindings{};
  Counters calls{};
  explicit Fixture(std::string_view scene) {
    Store(input.game_state, 8, static_cast<std::int64_t>(kDate));
    Store(input.game_state, 0x9C, std::int32_t{12});
    Store(input.game_state, 0xA0, static_cast<void *>(input.game_data.data()));
    input.provinces = {nullptr, input.province.data()};
    Store(input.game_data, 0x140, static_cast<void *>(input.provinces.data()));
    Store(input.game_data, 0x14C, std::int32_t{2});
    Store(input.province, 0x10, std::int32_t{1});
    Store(input.unit_storage, 0x20, static_cast<void *>(input.unit_slots.data()));
    Store(input.unit_storage, 0x2C, std::int32_t{2});
    Store(input.army_storage, 0x20, static_cast<void *>(input.army_slots.data()));
    Store(input.army_storage, 0x2C, std::int32_t{2});
    Store(input.regiment_storage, 0x20, static_cast<void *>(input.regiment_slots.data()));
    Store(input.regiment_storage, 0x2C, std::int32_t{2});
    Store(input.unit_slots, 0x18, static_cast<void *>(input.unit.data()));
    Store(input.army_slots, 0x18, static_cast<void *>(input.army.data()));
    Store(input.regiment_slots, 0x18, static_cast<void *>(input.regiment.data()));
    Store(input.unit, 0x10, kUnit);
    Store(input.unit, 0x174, std::int32_t{29829});
    Store(input.unit, 0x178, kArmy);
    Store(input.unit, 0x20, static_cast<void *>(input.province.data()));
    Store(input.army, 0x10, kArmy);
    Store(input.army, 0x14, std::uint32_t{0x41726D79});
    Store(input.army, 0x124, kUnit);
    Store(input.army, 0x38, static_cast<void *>(input.regiment_ids.data()));
    Store(input.army, 0x40, std::int32_t{2});
    Store(input.army, 0x44, std::int32_t{2});
    Store(input.army, 0x180, std::int64_t{123450000});
    Store(input.regiment, 0x10, kRegiment);
    Store(input.regiment, 0x14, std::uint32_t{0x41725267});
    Store(input.regiment, 0x38, std::int32_t{50});
    Store(input.regiment, 0x3C, std::int32_t{100});
    Store(input.regiment, 0x40, std::int64_t{25000000});
    bindings.enabled = true;
    bindings.game_state_slot = &game_slot;
    bindings.unit_storage_slot = &unit_slot;
    bindings.internal_army_storage_slot = &army_slot;
    bindings.regiment_storage_slot = &regiment_slot;
    bindings.get_army_current_soldiers = CurrentSoldiers;
    bindings.get_army_maximum_soldiers = MaximumSoldiers;
    bindings.get_army_supply_capacity = SupplyCapacity;
    bindings.get_army_attrition_fraction = Attrition;
    bindings.get_army_monthly_supply_change = MonthlySupply;
    bindings.current_unit_new_date_schedule_bindings =
        current::BindCurrentUnitNewDateSchedule12004(kImageBase, current::kExecutableSha256);
    const auto &binding = bindings.current_unit_new_date_schedule_bindings;
    Check(binding.enabled && binding.expected_new_date_target ==
        kImageBase + current::kUnitNewDateManagerMethodRva12004,
        "exact actual4 readonly schedule binding not selected");
    input.secondary_vtable[3] = binding.expected_new_date_target;
    // A fixture-owned numeric slot target is compared but never called.
    Store(input.game_data, 0x2A508,
        scene == "typed_unavailable" ? static_cast<const void *>(nullptr)
                                    : static_cast<const void *>(input.secondary_vtable.data()));
    Store(input.game_data, 0x2A528,
        scene == "empty_zero" ? static_cast<const void *>(nullptr)
                             : static_cast<const void *>(input.scheduled_unit_ids.data()));
    Store(input.game_data, 0x2A534,
        scene == "empty_zero" ? std::int32_t{0} : std::int32_t{4});
  }
};
std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  auto &f = *active;
  ++f.calls.current_soldiers;
  f.calls.events.emplace_back("army_current_soldiers");
  f.calls.abi_matches &= receiver == f.input.army.data() + 0x38 && flags == 0;
  return 100;
}
std::int32_t MaximumSoldiers(void *receiver) {
  auto &f = *active;
  ++f.calls.maximum_soldiers;
  f.calls.events.emplace_back("army_maximum_soldiers");
  f.calls.abi_matches &= receiver == f.input.army.data();
  return 200;
}
std::int64_t *SupplyCapacity(std::int64_t *out, void *receiver, void *details) {
  auto &f = *active;
  ++f.calls.supply_capacity;
  f.calls.events.emplace_back("army_supply_capacity");
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 200000000;
  return out;
}
std::int64_t *Attrition(void *receiver, std::int64_t *out, void *details) {
  auto &f = *active;
  ++f.calls.attrition_fraction;
  f.calls.events.emplace_back("army_attrition_fraction");
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 1250;
  return out;
}
std::int64_t *MonthlySupply(void *receiver, std::int64_t *out, void *province, void *details) {
  auto &f = *active;
  ++f.calls.monthly_supply;
  f.calls.events.emplace_back("army_monthly_supply_change");
  f.calls.abi_matches &= out && receiver == f.input.army.data() &&
      province == f.input.province.data() && details == nullptr;
  *out = -1200000;
  return out;
}
void AppendString(std::string &out, std::string_view value) {
  out += '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}
void AppendIds(std::string &out, const std::vector<std::int32_t> &ids) {
  out += '[';
  for (std::size_t index = 0; index < ids.size(); ++index) {
    if (index != 0) out += ',';
    out += std::to_string(ids[index]);
  }
  out += ']';
}
void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream file(path, std::ios::binary);
  file << text << '\n';
  Check(static_cast<bool>(file), "new whole fixture artifact write failed");
}
void AssertScene(const Fixture &f, const Inputs &before,
    const game::ArmyStrengthSnapshot &row, std::string_view scene) {
  Check(row.available && row.army_id == kUnit && row.native_carmy_id_observable &&
      row.native_carmy_id == kArmy, "original whole Strength identity changed");
  Check(row.regiment_count == 2 && row.regiment_strengths && row.regiment_strengths->size() == 2 &&
      (*row.regiment_strengths)[0].army_regiment_id == kRegiment &&
      (*row.regiment_strengths)[1].army_regiment_id == kRegiment &&
      row.current_soldiers == 100 && row.maximum_soldiers == 200,
      "original whole repeated roster/totals changed");
  Check(row.current_supply_raw == 123450000 && row.current_supply_capacity_raw == 200000000 &&
      row.current_supply_change_monthly_raw == -1200000 &&
      row.current_attrition_fraction_raw == 1250, "original whole stock/rate observations changed");
  Check(row.current_unit_new_date_schedule_inputs_v1.has_value(),
      "actual4 whole wrapper did not attach current Unit schedule");
  const auto &input = *row.current_unit_new_date_schedule_inputs_v1;
  Check(input.subject_army_id_u32 == static_cast<std::uint32_t>(kUnit) &&
      input.subject_carmy_id_u32 == static_cast<std::uint32_t>(kArmy),
      "schedule did not retain original whole validated subject IDs");
  Check(!input.actual_unit_new_date_callback_observed &&
      !input.actual_movement_or_arrival_observed && !input.earlier_stage_outputs_reconstructed &&
      !input.full_daily_supply_transition_ready && !input.full_monthly_ready,
      "raw scheduling inputs claimed native effects");
  if (scene == "typed_unavailable") {
    Check(input.status == "unavailable" && !input.ready && input.unavailable_reason ==
        "current_unit_new_date_schedule_binding_unavailable" &&
        !input.vector_header_count_i32 && !input.vector_data_present &&
        !input.subject_stored_id_positions && !input.subject_stored_id_occurrence_count_i32,
        "failed typed attachment fabricated vector operands or erased Strength row");
  } else if (scene == "empty_zero") {
    Check(input.status == "available" && input.ready && !input.unavailable_reason &&
        input.vector_header_count_i32 == 0 && input.vector_data_present == false &&
        input.subject_stored_id_positions && input.subject_stored_id_positions->empty() &&
        input.subject_stored_id_occurrence_count_i32 == 0,
        "legal zero-count/null-data vector was not observed as empty");
  } else {
    Check(input.status == "available" && input.ready && !input.unavailable_reason &&
        input.vector_header_count_i32 == 4 && input.vector_data_present == true &&
        input.subject_stored_id_positions &&
        *input.subject_stored_id_positions == std::vector<std::int32_t>({1, 3}) &&
        input.subject_stored_id_occurrence_count_i32 == 2,
        "raw ID generation/gaps/repeats were not preserved");
  }
  Check(f.calls.abi_matches && f.calls.current_soldiers == 1 &&
      f.calls.maximum_soldiers == 1 && f.calls.supply_capacity == 1 &&
      f.calls.attrition_fraction == 1 && f.calls.monthly_supply == 1 &&
      f.calls.events == std::vector<std::string>{"army_current_soldiers", "army_maximum_soldiers",
          "army_supply_capacity", "army_attrition_fraction", "army_monthly_supply_change"},
      "actual whole reader callback ABI/count/order changed");
  Check(f.input == before, "readonly whole reader changed fixture-owned input bytes");
}
std::string SerializeWhole(const game::ArmyStrengthSnapshot &row,
    std::string_view scene, std::size_t sequence) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, std::string("unit-new-date-schedule25-") + std::string(scene));
  out += ",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\","
         "\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  out += std::to_string(sequence);
  out += ",\"army_strengths\":[";
  game::AppendArmyStrengthV1(out, row,
      [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  out += "]}}";
  return game::Render12004BuildIdentity(std::move(out), game::Ck3_12004AdapterDescriptor());
}
std::string Context(const Fixture &f, std::string_view scene, std::size_t sequence) {
  std::string out = "{\"schema\":\"xar.current-unit-new-date-schedule25-native-context.v1\",\"scene\":";
  AppendString(out, scene);
  out += ",\"producer\":\"ReadArmyStrengthsForScope12004 -> AppendArmyStrengthV1 -> Render12004BuildIdentity\","
         "\"query_sequence\":" + std::to_string(sequence) + ",\"actual4_identity\":{\"backend_id\":";
  AppendString(out, current::kAdapterId);
  out += ",\"game_version\":";
  AppendString(out, current::kGameVersion);
  out += ",\"executable_sha256\":";
  AppendString(out, current::kExecutableSha256);
  out += "},\"synthetic_context\":{\"actor_character_id\":29829,"
         "\"native_revision\":1,\"snapshot_id\":\"native:1\","
         "\"date_raw\":53288448,\"paused\":true,\"map_ready\":true,"
         "\"bridge_host_pid\":1200401,\"current_province_id\":1,\"scope_role\":\"player\","
         "\"scope_army_ids\":[16777217],\"war_ids\":[],"
         "\"transport_connection_id\":\"current-unit-new-date-schedule25-12004\","
         "\"episode_id\":\"current-unit-new-date-schedule25-12004\"},"
         "\"heartbeat_published\":false,\"native_inputs\":{\"subject_army_id_u32\":16777217,"
         "\"subject_carmy_id_u32\":33554433,\"raw_stored_unit_ids\":[33554433,16777217,4294967295,16777217],"
         "\"fixture_secondary_vptr_present\":";
  out += scene == "typed_unavailable" ? "false" : "true";
  out += ",\"fixture_vector_count_i32\":";
  out += scene == "empty_zero" ? "0" : "4";
  out += ",\"fixture_vector_data_present\":";
  out += scene == "empty_zero" ? "false" : "true";
  out += "},\"callbacks\":{\"unit_state\":0,\"army_current_soldiers\":";
  out += std::to_string(f.calls.current_soldiers);
  out += ",\"army_maximum_soldiers\":" + std::to_string(f.calls.maximum_soldiers);
  out += ",\"army_supply_capacity\":" + std::to_string(f.calls.supply_capacity);
  out += ",\"army_attrition_fraction\":" + std::to_string(f.calls.attrition_fraction);
  out += ",\"army_monthly_supply_change\":" + std::to_string(f.calls.monthly_supply);
  out += ",\"unit_new_date\":0,\"movement_or_arrival\":0,\"native_daily_date_writer\":0,"
         "\"abi_matches\":";
  out += f.calls.abi_matches ? "true" : "false";
  out += "},\"all_fixture_input_bytes_unchanged\":true,\"assertions_passed\":true,"
         "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
         "\"G2_context_is_metadata_only\":true}";
  return out;
}
} // namespace

int main(int argc, char **argv) {
  std::filesystem::path output;
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
        "usage: xar_ck3_12004_current_unit_new_date_schedule_whole_test --wire-dir <fresh-dir>");
    output = argv[2];
    std::filesystem::create_directories(output);
    std::string aggregate = "{\"schema_version\":1,\"scene_order\":[\"gaps_repeats\","
                            "\"empty_zero\",\"typed_unavailable\"],\"samples\":{";
    for (std::size_t index = 0; index < kScenes.size(); ++index) {
      const auto scene = kScenes[index];
      auto fixture = std::make_unique<Fixture>(scene);
      auto before = std::make_unique<Inputs>(fixture->input);
      active = fixture.get();
      const std::array<current::ArmyStrengthScope, 1> scope{
          current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      const auto result = current::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows);
      Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "actual4 whole Strength reader did not return one available row");
      AssertScene(*fixture, *before, rows.front(), scene);
      const auto wire = SerializeWhole(rows.front(), scene, index + 1);
      Write(output / (std::string(scene) + ".command-result.json"), wire);
      Write(output / (std::string(scene) + ".native-context.json"), Context(*fixture, scene, index + 1));
      if (index != 0) aggregate += ',';
      AppendString(aggregate, scene);
      aggregate += ':';
      aggregate += wire;
      active = nullptr;
    }
    aggregate += "}}";
    Write(output / "current-unit-new-date-schedule25-whole.json", aggregate);
    Write(output / "PRODUCER-RECEIPT.json",
        "{\"schema\":\"xar.current-unit-new-date-schedule25-producer-receipt.v1\","
        "\"status\":\"PASS\",\"scene_count\":3,\"whole_reader_calls\":3,\"whole_serializer_calls\":3,"
        "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
        "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,\"old_GREEN_replayed\":false}");
    std::cout << "three current Unit NewDate schedule whole scenes emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    if (!output.empty()) {
      std::string receipt = "{\"schema\":\"xar.current-unit-new-date-schedule25-producer-receipt.v1\","
                            "\"status\":\"FAIL\",\"error\":";
      AppendString(receipt, error.what());
      receipt += ",\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false}";
      std::ofstream file(output / "PRODUCER-RECEIPT.json", std::ios::binary);
      file << receipt << '\n';
    }
    std::cerr << error.what() << '\n';
    return 1;
  }
}

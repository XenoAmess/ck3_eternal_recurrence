// SOURCE_PREPARED/NOTRUN. Root owns the sole fresh build and execution.
// Actual4 wrapper -> common production Strength collector -> production wire.
// This observes current operands with owned readonly stubs; it never calls
// NewDate, the ADD writer, edge-cost/route-consumption handlers, or Game.
// Route-zero holds operands into the gate slice; the intervening empty-route
// handler from callback entry to this gate is outside the source closure.
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_current_unit_new_date_schedule_inputs.hpp"
#include "xar_bridge/ck3_12004_current_unit_new_date_callback_entry_inputs.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>
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
struct Scene {
  std::string_view name;
  std::int32_t state;
  std::int32_t route_count;
  std::int64_t accumulated_weight;
  std::int64_t cached_speed;
  std::int64_t edge_rate;
  bool subject_scheduled;
  bool edge_getter_bound;
};
constexpr std::array<Scene, 8> kScenes{{
    {"positive_cache", 1, 2, 100, 7, 11, true, true},
    {"fallback_zero", 1, 2, 100, 0, 11, true, true},
    {"fallback_negative_zero_rate", 1, 2, 100, -9, 0, true, true},
    {"wrap_add", 1, 2, std::numeric_limits<std::int64_t>::max(), 1, 11, true, true},
    {"route_zero", 3, 0, 100, 0, 11, true, true},
    {"zero_occurrences", 1, 2, 100, 0, 11, false, true},
    {"unknown_predicate", 2, 2, 100, 7, 11, true, true},
    {"fallback_unavailable", 1, 2, 100, 0, 11, true, false},
}};

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture-owned store out of range");
  std::memcpy(object.data() + offset, &value, sizeof value);
}
struct Inputs {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x2AA00> game_data{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x198> unit{};
  std::array<std::byte, 0x210> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x18> province{};
  std::array<void *, 2> provinces{};
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  std::array<std::array<std::byte, 4>, 2> route_nodes{};
  std::array<void *, 2> route_pointers{};
  std::array<std::uint32_t, 4> scheduled_unit_ids{
      0x02000001U, static_cast<std::uint32_t>(kUnit), 0xFFFFFFFFU,
      static_cast<std::uint32_t>(kUnit)};
  std::array<std::uintptr_t, 4> secondary_vtable{};
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Counters {
  std::size_t current_soldiers = 0, maximum_soldiers = 0;
  std::size_t supply_capacity = 0, attrition_fraction = 0, monthly_supply = 0;
  std::size_t current_edge_speed = 0;
  bool abi_matches = true;
};
struct Fixture;
Fixture *active = nullptr;
std::int32_t CurrentSoldiers(void *, std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int64_t *SupplyCapacity(std::int64_t *, void *, void *);
std::int64_t *Attrition(void *, std::int64_t *, void *);
std::int64_t *MonthlySupply(void *, std::int64_t *, void *, void *);
std::int64_t *CurrentEdgeSpeed(void *, std::int64_t *);

struct Fixture {
  Inputs input{};
  void *game_slot = input.game_state.data();
  void *unit_slot = input.unit_storage.data();
  void *army_slot = input.army_storage.data();
  void *regiment_slot = input.regiment_storage.data();
  current::ArmyBindings bindings{};
  Counters calls{};
  std::int64_t edge_rate;
  explicit Fixture(const Scene &scene) : edge_rate(scene.edge_rate) {
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
    Store(input.unit, 0x14, std::uint32_t{0x556E6974});
    Store(input.unit, 0x174, std::int32_t{29829});
    Store(input.unit, 0x178, kArmy);
    Store(input.unit, 0x170, scene.state);
    Store(input.unit, 0x168, scene.accumulated_weight);
    Store(input.unit, 0x190, scene.cached_speed);
    Store(input.unit, 0x20, static_cast<void *>(input.province.data()));
    Store(input.route_nodes[0], 0, std::int32_t{1});
    Store(input.route_nodes[1], 0, std::int32_t{1});
    input.route_pointers = {input.route_nodes[0].data(), input.route_nodes[1].data()};
    Store(input.unit, 0x38, static_cast<void *>(input.route_pointers.data()));
    Store(input.unit, 0x40, std::int32_t{2});
    Store(input.unit, 0x44, scene.route_count);
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
    bindings.current_unit_new_date_callback_entry_bindings =
        current::BindCurrentUnitNewDateCallbackEntryInputs12004(kImageBase, current::kExecutableSha256);
    bindings.monthly_loss_budget_bindings.enabled = true;
    // Existing production slot type is reused with one fixture-owned getter.
    // The full committed-route timeline remains disabled; no future route,
    // cost/duration or budget callback is installed or invoked.
    bindings.committed_route_bindings.read_unit_current_edge_speed =
        scene.edge_getter_bound ? CurrentEdgeSpeed : nullptr;
    Check(bindings.current_unit_new_date_schedule_bindings.enabled &&
        bindings.current_unit_new_date_callback_entry_bindings.enabled &&
        !bindings.committed_route_bindings.enabled &&
        !bindings.source_derived_next_daily_supply_frame_bindings.enabled,
        "exact4 raw bindings missing or unrelated timeline/calendar enabled");
    input.secondary_vtable[3] =
        bindings.current_unit_new_date_schedule_bindings.expected_new_date_target;
    Store(input.game_data, 0x2A508, static_cast<const void *>(input.secondary_vtable.data()));
    if (!scene.subject_scheduled) {
      input.scheduled_unit_ids[1] = static_cast<std::uint32_t>(kRegiment);
      input.scheduled_unit_ids[3] = static_cast<std::uint32_t>(kRegiment);
    }
    Store(input.game_data, 0x2A528, static_cast<const void *>(input.scheduled_unit_ids.data()));
    Store(input.game_data, 0x2A534, std::int32_t{4});
  }
};
std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  auto &f = *active;
  ++f.calls.current_soldiers;
  f.calls.abi_matches &= receiver == f.input.army.data() + 0x38 && flags == 0;
  return 100;
}
std::int32_t MaximumSoldiers(void *receiver) {
  auto &f = *active;
  ++f.calls.maximum_soldiers;
  f.calls.abi_matches &= receiver == f.input.army.data();
  return 200;
}
std::int64_t *SupplyCapacity(std::int64_t *out, void *receiver, void *details) {
  auto &f = *active;
  ++f.calls.supply_capacity;
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 200000000;
  return out;
}
std::int64_t *Attrition(void *receiver, std::int64_t *out, void *details) {
  auto &f = *active;
  ++f.calls.attrition_fraction;
  f.calls.abi_matches &= out && receiver == f.input.army.data() && details == nullptr;
  *out = 1250;
  return out;
}
std::int64_t *MonthlySupply(void *receiver, std::int64_t *out, void *province, void *details) {
  auto &f = *active;
  ++f.calls.monthly_supply;
  f.calls.abi_matches &= out && receiver == f.input.army.data() &&
      province == f.input.province.data() && details == nullptr;
  *out = -1200000;
  return out;
}
std::int64_t *CurrentEdgeSpeed(void *receiver, std::int64_t *out) {
  auto &f = *active;
  ++f.calls.current_edge_speed;
  f.calls.abi_matches &= receiver == f.input.unit.data() && out != nullptr;
  *out = f.edge_rate;
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
  Check(static_cast<bool>(file), "fresh movement-prefix whole artifact write failed");
}
void AssertScene(const Fixture &f, const Inputs &before,
    const game::ArmyStrengthSnapshot &row, const Scene &scene) {
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
  Check(row.native_army_resolution_v1 &&
      row.native_army_resolution_v1->raw_reference == kArmy,
      "source-used raw Unit178 reference omitted");
  Check(row.current_unit_new_date_schedule_inputs_v1.has_value(), "adopted schedule17 omitted");
  const auto &schedule = *row.current_unit_new_date_schedule_inputs_v1;
  const std::vector<std::int32_t> positions = scene.subject_scheduled
      ? std::vector<std::int32_t>{1, 3} : std::vector<std::int32_t>{};
  Check(schedule.status == "available" && schedule.ready && !schedule.unavailable_reason &&
      schedule.vector_header_count_i32 == 4 && schedule.vector_data_present == true &&
      schedule.subject_stored_id_positions && *schedule.subject_stored_id_positions == positions &&
      schedule.subject_stored_id_occurrence_count_i32 == static_cast<std::int32_t>(positions.size()),
      "original schedule positions/repeats changed");
  Check(!schedule.actual_unit_new_date_callback_observed &&
      !schedule.actual_movement_or_arrival_observed && !schedule.earlier_stage_outputs_reconstructed &&
      !schedule.full_daily_supply_transition_ready && !schedule.full_monthly_ready,
      "raw schedule became a future effect observation");
  Check(row.monthly_loss_budget_inputs_v1.has_value(), "real monthly raw170 collector omitted");
  const auto &budget = *row.monthly_loss_budget_inputs_v1;
  Check(budget.unit_native_170_raw == scene.state &&
      !budget.native_unit_in_combat && !budget.native_unit_gathering &&
      !budget.loaded_supply_state_levels && !budget.loaded_supply_state_fractions_raw,
      "raw170 substituted or unavailable budget fabricated");
  Check(row.current_unit_new_date_callback_entry_inputs_v1.has_value(), "raw44 collector omitted");
  const auto &entry = *row.current_unit_new_date_callback_entry_inputs_v1;
  Check(entry.status == "available" && entry.ready && !entry.unavailable_reason &&
      entry.unit_route_count_i32 == scene.route_count &&
      entry.subject_army_id_u32 == static_cast<std::uint32_t>(kUnit) &&
      entry.subject_carmy_id_u32 == static_cast<std::uint32_t>(kArmy),
      "same-row exact raw44 or subject changed");
  Check(row.current_movement_progress.has_value(), "movement operand collector omitted");
  const auto &movement = *row.current_movement_progress;
  const bool getter_used = scene.route_count > 0 && scene.cached_speed <= 0 && scene.edge_getter_bound;
  const std::optional<std::int64_t> expected_rate = getter_used
      ? std::optional<std::int64_t>{scene.edge_rate} : std::nullopt;
  Check(movement.accumulated_movement_weight_raw == scene.accumulated_weight &&
      movement.cached_edge_speed_raw == scene.cached_speed &&
      movement.current_edge_movement_rate_raw == expected_rate && !movement.unit_state_raw &&
      !movement.normalized_edge_progress_raw && !movement.first_route_edge_remaining_duration_raw &&
      !movement.committed_route_timeline,
      "movement raw inputs changed or unsupported timeline outputs fabricated");
  if (row.source_derived_next_daily_supply_frame_inputs_v1) {
    const auto &date = *row.source_derived_next_daily_supply_frame_inputs_v1;
    Check(!date.source_derived_full_cdate64_ready && !date.source_derived_next_date_storage_raw64,
        "date-free gate unexpectedly required a future full date");
  }
  Check(f.calls.abi_matches && f.calls.current_soldiers == 1 &&
      f.calls.maximum_soldiers == 1 && f.calls.supply_capacity == 1 &&
      f.calls.attrition_fraction == 1 && f.calls.monthly_supply == 1 &&
      f.calls.current_edge_speed == (getter_used ? 1U : 0U),
      "whole reader ABI/count or current getter selection changed");
  Check(f.input == before, "readonly whole reader changed owned Unit/queue/route inputs");
}
std::string SerializeWhole(const game::ArmyStrengthSnapshot &row,
    std::string_view scene, std::size_t sequence) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, std::string("unit-next-movement-prefix-") + std::string(scene));
  out += ",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\","
         "\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  out += std::to_string(sequence);
  out += ",\"army_strengths\":[";
  game::AppendArmyStrengthV1(out, row,
      [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  out += "]}}";
  return game::Render12004BuildIdentity(std::move(out), game::Ck3_12004AdapterDescriptor());
}
std::string Context(const Fixture &f, const Scene &scene, std::size_t sequence) {
  std::string out = "{\"schema\":\"xar.unit-next-movement-prefix-native-context.v1\",\"scene\":";
  AppendString(out, scene.name);
  out += ",\"producer\":\"ReadArmyStrengthsForScope12004 -> production ReadArmyStrengthsForScope -> AppendArmyStrengthV1 -> Render12004BuildIdentity\","
         "\"query_sequence\":" + std::to_string(sequence) + ",\"actual4_identity\":{\"backend_id\":";
  AppendString(out, current::kAdapterId);
  out += ",\"game_version\":";
  AppendString(out, current::kGameVersion);
  out += ",\"executable_sha256\":";
  AppendString(out, current::kExecutableSha256);
  out += "},\"synthetic_context\":{\"actor_character_id\":29829,"
         "\"native_revision\":1,\"snapshot_id\":\"native:1\",\"date_raw\":53288448,"
         "\"paused\":true,\"map_ready\":true,\"bridge_host_pid\":1200401,"
         "\"current_province_id\":1,\"scope_role\":\"player\",\"scope_army_ids\":[16777217],"
         "\"war_ids\":[],\"transport_connection_id\":\"unit-next-movement-prefix-12004\","
         "\"episode_id\":\"unit-next-movement-prefix-12004\"},\"heartbeat_published\":false,"
         "\"native_inputs\":{\"subject_army_id_u32\":16777217,\"subject_carmy_id_u32\":33554433,"
         "\"unit_native_170_raw\":" + std::to_string(scene.state);
  out += ",\"unit_route_count_i32\":" + std::to_string(scene.route_count);
  out += ",\"unit_native_178_raw\":33554433,\"accumulated_movement_weight_raw\":";
  out += std::to_string(scene.accumulated_weight);
  out += ",\"cached_edge_speed_raw\":" + std::to_string(scene.cached_speed);
  out += ",\"fixture_current_edge_movement_rate_raw\":" + std::to_string(scene.edge_rate);
  out += ",\"current_edge_getter_bound\":";
  out += scene.edge_getter_bound ? "true" : "false";
  out += ",\"subject_stored_id_positions\":";
  AppendIds(out, scene.subject_scheduled ? std::vector<std::int32_t>{1, 3}
                                      : std::vector<std::int32_t>{});
  out += ",\"monthly_budget_callbacks_enabled\":false,\"Source23_binding_enabled\":false,"
         "\"full_date_required\":false},\"callbacks\":{\"unit_state\":0,\"current_edge_speed\":";
  out += std::to_string(f.calls.current_edge_speed);
  out += ",\"army_current_soldiers\":" + std::to_string(f.calls.current_soldiers);
  out += ",\"army_maximum_soldiers\":" + std::to_string(f.calls.maximum_soldiers);
  out += ",\"army_supply_capacity\":" + std::to_string(f.calls.supply_capacity);
  out += ",\"army_attrition_fraction\":" + std::to_string(f.calls.attrition_fraction);
  out += ",\"army_monthly_supply_change\":" + std::to_string(f.calls.monthly_supply);
  out += ",\"monthly_budget_helpers\":0,\"unit_new_date\":0,\"movement_or_arrival\":0,"
         "\"native_daily_date_writer\":0,\"abi_matches\":";
  out += f.calls.abi_matches ? "true" : "false";
  out += "},\"all_fixture_input_bytes_unchanged\":true,\"assertions_passed\":true,"
         "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
         "\"full_adapter_snapshot_path_exercised\":false,\"G2_context_is_metadata_only\":true,"
         "\"projection_boundary\":\"first selected supplied gate-entry slice after ADD\","
         "\"route_zero_inputs_held_into_gate\":true,\"intervening_empty_route_handler_closed\":false}";
  return out;
}
} // namespace

int main(int argc, char **argv) {
  std::filesystem::path output;
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
        "usage: xar_ck3_12004_unit_next_movement_prefix_whole_test --wire-dir <fresh-dir>");
    output = argv[2];
    std::filesystem::create_directories(output);
    std::string aggregate = "{\"schema_version\":1,\"scene_order\":[";
    for (std::size_t index = 0; index < kScenes.size(); ++index) {
      if (index != 0) aggregate += ',';
      AppendString(aggregate, kScenes[index].name);
    }
    aggregate += "],\"samples\":{";
    for (std::size_t index = 0; index < kScenes.size(); ++index) {
      const auto &scene = kScenes[index];
      auto fixture = std::make_unique<Fixture>(scene);
      auto before = std::make_unique<Inputs>(fixture->input);
      active = fixture.get();
      const std::array<current::ArmyStrengthScope, 1> scope{
          current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      const auto result = current::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows);
      Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "genuine whole Strength did not produce an available original row");
      AssertScene(*fixture, *before, rows.front(), scene);
      const auto wire = SerializeWhole(rows.front(), scene.name, index + 1);
      Write(output / (std::string(scene.name) + ".command-result.json"), wire);
      Write(output / (std::string(scene.name) + ".native-context.json"), Context(*fixture, scene, index + 1));
      if (index != 0) aggregate += ',';
      AppendString(aggregate, scene.name);
      aggregate += ':';
      aggregate += wire;
      active = nullptr;
    }
    aggregate += "}}";
    Write(output / "unit-next-movement-prefix-whole.json", aggregate);
    Write(output / "PRODUCER-RECEIPT.json",
        "{\"schema\":\"xar.unit-next-movement-prefix-producer-receipt.v1\","
        "\"status\":\"PASS\",\"scene_count\":8,\"whole_reader_calls\":8,\"whole_serializer_calls\":8,"
        "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
        "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
        "\"old_GREEN_replayed\":false,\"full_adapter_snapshot_path_exercised\":false}");
    std::cout << "eight current Unit movement-input whole scenes emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    if (!output.empty()) {
      std::string receipt = "{\"schema\":\"xar.unit-next-movement-prefix-producer-receipt.v1\","
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

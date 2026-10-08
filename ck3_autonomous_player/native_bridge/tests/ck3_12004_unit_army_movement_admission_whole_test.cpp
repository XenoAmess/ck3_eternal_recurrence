// SOURCE_PREPARED/NOTRUN. Root owns the sole fresh build and execution.
// Actual4 wrapper -> common production Strength collector -> production wire.
// This observes current operands with owned readonly stubs; it never calls
// NewDate, the ADD writer, native provider initialization, arrival handlers,
// or Game. New modes install only fixture-owned readonly observers.
// Admission is a current readonly bool input; future Combat/Army context is
// held explicitly by the pure gate-slice projection, not observed as effects.
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
constexpr std::int32_t kActor = 29829;
constexpr std::uint32_t kProvinceMagic = 0x50726F76U;
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
  bool admission_value;
  bool admission_getter_bound;
  bool edge_selection_scene = false;
  std::int64_t first_edge_cost = 0;
  bool first_edge_cost_getter_bound = false;
  std::uint8_t provider_byte_e = 0;
  bool provider_byte_bound = false;
  std::int64_t normalized_progress = 0;
  std::int64_t remaining_duration = 0;
  std::optional<bool> expected_branch_selected;
  bool arrival_transition_scene = false;
  std::int32_t first_route_province_id = 1;
  std::uint32_t first_target_type_tag = 0;
  bool first_target_type_tag_enabled = false;
  std::optional<bool> expected_first_assignment_selected;
  std::optional<std::int32_t> expected_conditional_province_id;
  bool disembark_write_scene = false;
  bool prestore_inputs_enabled = false;
  std::int32_t unit_kind_18 = 0;
  std::uint8_t current_definition_byte_1b = 0;
  std::uint8_t target_definition_byte_1b = 1;
  bool definition_pointers_present = true;
  std::int32_t loaded_disembark_days_rule = 34;
  bool loaded_disembark_days_rule_bound = false;
  bool expected_prestore_call_selected = false;
  bool expected_fixed_days_write_selected = false;
  std::optional<std::int32_t> expected_fixed_days_write_value;
  bool expected_fixed_write_ready = true;
  bool expected_loaded_rule_demanded = false;
};
constexpr std::array<Scene, 4> kScenes{{
    {"admission_true", 2, 2, 100, 7, 11, true, true, true, true},
    {"admission_false", 2, 2, 100, 0, 11, true, true, false, true},
    {"admission_unavailable", 2, 2, 100, 7, 11, true, true, false, false},
    {"admission_bypass_state1", 1, 2, 100, 7, 11, true, true, false, false},
}};

constexpr std::array<Scene, 5> kEdgeSelectionScenes{{
    {"edge_above_cost", 2, 2, 100, 7, 11, true, true, true, true,
     true, 106, true, 0, false, 94339, 85714, true},
    {"edge_equal_hold", 2, 2, 100, 7, 11, true, true, true, true,
     true, 107, true, 0, true, 93457, 100000, false},
    {"edge_below_override", 2, 2, 100, 7, 11, true, true, true, true,
     true, 108, true, 3, true, 92592, 114285, true},
    {"edge_provider_unavailable", 2, 2, 100, 7, 11, true, true, true, true,
     true, 107, true, 0, false, 93457, 100000, std::nullopt},
    {"edge_cost_unavailable", 2, 2, 100, 7, 11, true, true, true, true,
     true, 107, false, 0, true, 93457, 100000, std::nullopt},
}};

constexpr std::array<Scene, 5> kArrivalTransitionScenes{{
    {"arrival_distinct_province", 2, 2, 100, 7, 11, true, true, true, true,
     true, 106, true, 0, true, 94339, 85714, true,
     true, 2, kProvinceMagic, true, true, 2},
    {"arrival_same_province", 2, 2, 100, 7, 11, true, true, true, true,
     true, 106, true, 0, true, 94339, 85714, true,
     true, 1, kProvinceMagic, true, false, 1},
    {"arrival_invalid_target_tag", 2, 2, 100, 7, 11, true, true, true, true,
     true, 106, true, 0, true, 94339, 85714, true,
     true, 2, 0, true, false, 1},
    {"arrival_target_tag_unavailable", 2, 2, 100, 7, 11, true, true, true, true,
     true, 106, true, 0, true, 94339, 85714, true,
     true, 2, kProvinceMagic, false, std::nullopt, std::nullopt},
    {"arrival_not_selected", 2, 2, 100, 7, 11, true, true, true, true,
     true, 107, true, 0, true, 93457, 100000, false,
     true, 2, kProvinceMagic, false, false, 1},
}};

constexpr std::array<Scene, 7> kDisembarkWriteScenes = [] {
  std::array<Scene, 7> scenes{};
  constexpr std::array<std::string_view, 7> names{
      "disembark_rule_positive", "disembark_rule_zero", "disembark_rule_negative",
      "disembark_rule_unavailable", "disembark_target_medium_zero",
      "disembark_unit_kind_bypass", "disembark_arrival_not_selected"};
  for (std::size_t index = 0; index < scenes.size(); ++index) {
    auto &scene = scenes[index];
    scene = kArrivalTransitionScenes[0];
    scene.name = names[index];
    scene.disembark_write_scene = true;
    scene.prestore_inputs_enabled = true;
    scene.loaded_disembark_days_rule_bound = true;
    scene.expected_prestore_call_selected = true;
    scene.expected_fixed_days_write_selected = true;
    scene.expected_fixed_days_write_value = 34;
    scene.expected_loaded_rule_demanded = true;
  }
  scenes[1].loaded_disembark_days_rule = 0;
  scenes[1].expected_fixed_days_write_value = 0;
  scenes[2].loaded_disembark_days_rule = -1;
  scenes[2].expected_fixed_days_write_value = -1;
  scenes[3].loaded_disembark_days_rule_bound = false;
  scenes[3].expected_fixed_days_write_value = std::nullopt;
  scenes[3].expected_fixed_write_ready = false;
  scenes[4].target_definition_byte_1b = 0;
  scenes[4].loaded_disembark_days_rule_bound = false;
  scenes[4].expected_fixed_days_write_selected = false;
  scenes[4].expected_fixed_days_write_value = std::nullopt;
  scenes[4].expected_loaded_rule_demanded = false;
  scenes[5].unit_kind_18 = 1;
  scenes[5].definition_pointers_present = false;
  scenes[5].loaded_disembark_days_rule_bound = false;
  scenes[5].expected_prestore_call_selected = false;
  scenes[5].expected_fixed_days_write_selected = false;
  scenes[5].expected_fixed_days_write_value = std::nullopt;
  scenes[5].expected_loaded_rule_demanded = false;
  scenes[6].first_edge_cost = 107;
  scenes[6].normalized_progress = 93457;
  scenes[6].remaining_duration = 100000;
  scenes[6].expected_branch_selected = false;
  scenes[6].expected_first_assignment_selected = false;
  scenes[6].expected_conditional_province_id = 1;
  scenes[6].prestore_inputs_enabled = false;
  scenes[6].loaded_disembark_days_rule_bound = false;
  scenes[6].expected_prestore_call_selected = false;
  scenes[6].expected_fixed_days_write_selected = false;
  scenes[6].expected_fixed_days_write_value = std::nullopt;
  scenes[6].expected_loaded_rule_demanded = false;
  return scenes;
}();

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
  std::array<std::byte, 0x860> province{}, target_province{}, final_province{};
  std::array<void *, 4> provinces{};
  std::array<std::byte, 0x20> current_province_definition{}, target_province_definition{};
  std::int32_t loaded_disembark_days_rule = 34;
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  std::array<std::array<std::byte, 4>, 2> route_nodes{};
  std::array<void *, 2> route_pointers{};
  std::array<std::uint32_t, 4> scheduled_unit_ids{
      0x02000001U, static_cast<std::uint32_t>(kUnit), 0xFFFFFFFFU,
      static_cast<std::uint32_t>(kUnit)};
  std::array<std::uintptr_t, 4> secondary_vtable{};
  std::uint8_t first_edge_arrival_provider_byte_e = 0;
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Counters {
  std::size_t current_soldiers = 0, maximum_soldiers = 0;
  std::size_t supply_capacity = 0, attrition_fraction = 0, monthly_supply = 0;
  std::size_t current_edge_speed = 0;
  std::size_t army_movement_admission = 0;
  std::size_t first_edge_cost = 0, normalized_progress = 0, remaining_duration = 0;
  std::size_t unit_state = 0, current_army_context_reader = 0;
  std::size_t current_disembark_penalty_days = 0;
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
bool ArmyMovementAdmission(void *);
std::int64_t *FirstEdgeCost(void *, std::int64_t *);
std::int64_t *NormalizedProgress(void *, std::int64_t *);
std::int64_t *FirstEdgeRemainingDuration(void *, std::int64_t *, std::int32_t);
std::int32_t UnitState(void *);
std::int32_t CurrentDisembarkPenaltyDays(const void *);

struct Fixture {
  Inputs input{};
  void *game_slot = input.game_state.data();
  void *unit_slot = input.unit_storage.data();
  void *army_slot = input.army_storage.data();
  void *regiment_slot = input.regiment_storage.data();
  current::ArmyBindings bindings{};
  Counters calls{};
  std::int64_t edge_rate;
  bool admission_value;
  std::int64_t first_edge_cost = 0, normalized_progress = 0, remaining_duration = 0;
  explicit Fixture(const Scene &scene)
      : edge_rate(scene.edge_rate), admission_value(scene.admission_value),
        first_edge_cost(scene.first_edge_cost), normalized_progress(scene.normalized_progress),
        remaining_duration(scene.remaining_duration) {
    Store(input.game_state, 8, static_cast<std::int64_t>(kDate));
    Store(input.game_state, 0x9C, std::int32_t{12});
    Store(input.game_state, 0xA0, static_cast<void *>(input.game_data.data()));
    input.provinces = {nullptr, input.province.data(), nullptr, nullptr};
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
    Store(input.unit, 0x174, kActor);
    Store(input.unit, 0x18, scene.unit_kind_18);
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
    bindings.current_movement_progress_enabled = true;
    bindings.current_unit_new_date_schedule_bindings =
        current::BindCurrentUnitNewDateSchedule12004(kImageBase, current::kExecutableSha256);
    bindings.current_unit_new_date_callback_entry_bindings =
        current::BindCurrentUnitNewDateCallbackEntryInputs12004(kImageBase, current::kExecutableSha256);
    bindings.monthly_loss_budget_bindings.enabled = true;
    // Existing production slot type is reused with one fixture-owned getter.
    // The full committed-route timeline remains disabled. New scenes add
    // current ratio/duration/cost stubs and a borrowed byte, never future calls.
    bindings.read_native_army_movement_admission =
        scene.admission_getter_bound ? ArmyMovementAdmission : nullptr;
    bindings.get_unit_current_edge_movement_rate =
        scene.edge_getter_bound ? CurrentEdgeSpeed : nullptr;
    if (scene.edge_selection_scene) {
      input.first_edge_arrival_provider_byte_e = scene.provider_byte_e;
      bindings.get_unit_normalized_edge_progress = NormalizedProgress;
      bindings.get_unit_first_route_edge_duration = FirstEdgeRemainingDuration;
      bindings.get_unit_first_route_edge_weight_cost =
          scene.first_edge_cost_getter_bound ? FirstEdgeCost : nullptr;
      bindings.unit_first_edge_arrival_provider_byte_e = scene.provider_byte_bound
          ? &input.first_edge_arrival_provider_byte_e : nullptr;
    }
    Check(bindings.current_unit_new_date_schedule_bindings.enabled &&
        bindings.current_unit_new_date_callback_entry_bindings.enabled &&
        (bindings.get_unit_current_edge_movement_rate != nullptr) == scene.edge_getter_bound &&
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
    if (scene.arrival_transition_scene) {
      input.provinces[2] = input.target_province.data();
      input.provinces[3] = input.final_province.data();
      Store(input.game_data, 0x14C, std::int32_t{4});
      Store(input.province, 0x85C, kProvinceMagic);
      Store(input.target_province, 0x10, std::int32_t{2});
      Store(input.target_province, 0x85C, scene.first_target_type_tag);
      Store(input.final_province, 0x10, std::int32_t{3});
      Store(input.final_province, 0x85C, kProvinceMagic);
      Store(input.route_nodes[0], 0, scene.first_route_province_id);
      Store(input.route_nodes[1], 0, std::int32_t{3});
      bindings.get_unit_state = UnitState;
      bindings.first_route_target_province_type_tag_enabled =
          scene.first_target_type_tag_enabled;
    }
    if (scene.disembark_write_scene) {
      Store(input.province, 8, scene.definition_pointers_present
          ? static_cast<const void *>(input.current_province_definition.data()) : nullptr);
      Store(input.target_province, 8, scene.definition_pointers_present
          ? static_cast<const void *>(input.target_province_definition.data()) : nullptr);
      Store(input.current_province_definition, 0x1B, scene.current_definition_byte_1b);
      Store(input.target_province_definition, 0x1B, scene.target_definition_byte_1b);
      input.loaded_disembark_days_rule = scene.loaded_disembark_days_rule;
      Store(input.army, 0x1D0, std::int32_t{12});
      bindings.current_unit_arrival_prestore_inputs_enabled = scene.prestore_inputs_enabled;
      bindings.loaded_disembark_penalty_days_rule = scene.loaded_disembark_days_rule_bound
          ? &input.loaded_disembark_days_rule : nullptr;
      bindings.current_disembark_penalty_enabled = true;
      bindings.get_army_disembark_penalty_days = CurrentDisembarkPenaltyDays;
    }
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
bool ArmyMovementAdmission(void *receiver) {
  auto &f = *active;
  ++f.calls.army_movement_admission;
  f.calls.abi_matches &= receiver == f.input.army.data();
  return f.admission_value;
}
std::int64_t *FirstEdgeCost(void *receiver, std::int64_t *out) {
  auto &f = *active;
  ++f.calls.first_edge_cost;
  f.calls.abi_matches &= receiver == f.input.unit.data() && out != nullptr;
  *out = f.first_edge_cost;
  return out;
}
std::int64_t *NormalizedProgress(void *receiver, std::int64_t *out) {
  auto &f = *active;
  ++f.calls.normalized_progress;
  f.calls.abi_matches &= receiver == f.input.unit.data() && out != nullptr;
  *out = f.normalized_progress;
  return out;
}
std::int64_t *FirstEdgeRemainingDuration(
    void *receiver, std::int64_t *out, std::int32_t index) {
  auto &f = *active;
  ++f.calls.remaining_duration;
  f.calls.abi_matches &= receiver == f.input.unit.data() && out != nullptr && index == 0;
  *out = f.remaining_duration;
  return out;
}
std::int32_t UnitState(void *receiver) {
  auto &f = *active;
  ++f.calls.unit_state;
  f.calls.abi_matches &= receiver == f.input.unit.data();
  return 6;
}
std::int32_t CurrentDisembarkPenaltyDays(const void *receiver) {
  auto &f = *active;
  ++f.calls.current_disembark_penalty_days;
  f.calls.abi_matches &= receiver == f.input.army.data();
  Check(receiver == f.input.army.data(), "current days getter received a different CArmy");
  std::int32_t value = 0;
  std::memcpy(&value, static_cast<const std::byte *>(receiver) + 0x1D0, sizeof value);
  return value;
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
  const std::optional<bool> expected_admission = scene.admission_getter_bound
      ? std::optional<bool>{scene.admission_value} : std::nullopt;
  Check(movement.native_army_movement_admission == expected_admission,
      "same-CArmy native AL bool omitted, false collapsed, or unbound value fabricated");
  const std::optional<std::int64_t> expected_progress = scene.edge_selection_scene
      ? std::optional<std::int64_t>{scene.normalized_progress} : std::nullopt;
  const std::optional<std::int64_t> expected_duration = scene.edge_selection_scene
      ? std::optional<std::int64_t>{scene.remaining_duration} : std::nullopt;
  const std::optional<std::int64_t> expected_cost =
      scene.edge_selection_scene && scene.first_edge_cost_getter_bound
      ? std::optional<std::int64_t>{scene.first_edge_cost} : std::nullopt;
  const std::optional<std::uint8_t> expected_provider =
      scene.edge_selection_scene && scene.provider_byte_bound
      ? std::optional<std::uint8_t>{scene.provider_byte_e} : std::nullopt;
  const std::optional<std::int32_t> expected_unit_state = scene.arrival_transition_scene
      ? std::optional<std::int32_t>{6} : std::nullopt;
  const std::optional<std::uint32_t> expected_target_tag =
      scene.arrival_transition_scene && scene.first_target_type_tag_enabled
      ? std::optional<std::uint32_t>{scene.first_target_type_tag} : std::nullopt;
  Check(movement.first_route_target_province_type_tag_u32 == expected_target_tag,
      "same-query first target tag omitted, zero collapsed, or disabled value fabricated");
  Check(movement.accumulated_movement_weight_raw == scene.accumulated_weight &&
      movement.cached_edge_speed_raw == scene.cached_speed &&
      movement.current_edge_movement_rate_raw == expected_rate &&
      movement.unit_state_raw == expected_unit_state &&
      movement.normalized_edge_progress_raw == expected_progress &&
      movement.first_route_edge_remaining_duration_raw == expected_duration &&
      movement.first_route_edge_weight_cost_raw == expected_cost &&
      movement.first_edge_arrival_provider_byte_e_u8 == expected_provider &&
      !movement.committed_route_timeline,
      "movement raw operands or exact current edge observers changed");
  if (scene.disembark_write_scene) {
    const auto expected_tag = scene.prestore_inputs_enabled
        ? std::optional<std::uint32_t>{kProvinceMagic} : std::nullopt;
    const auto expected_kind = scene.prestore_inputs_enabled
        ? std::optional<std::int32_t>{scene.unit_kind_18} : std::nullopt;
    const auto expected_current_definition =
        scene.prestore_inputs_enabled && scene.definition_pointers_present
        ? std::optional<std::uint8_t>{scene.current_definition_byte_1b} : std::nullopt;
    const auto expected_target_definition =
        scene.prestore_inputs_enabled && scene.definition_pointers_present
        ? std::optional<std::uint8_t>{scene.target_definition_byte_1b} : std::nullopt;
    const auto expected_loaded_rule =
        scene.prestore_inputs_enabled && scene.loaded_disembark_days_rule_bound
        ? std::optional<std::int32_t>{scene.loaded_disembark_days_rule} : std::nullopt;
    Check(movement.current_province_type_tag_u32 == expected_tag &&
        movement.unit_kind_18_raw_i32 == expected_kind &&
        movement.current_province_definition_byte_1b_u8 == expected_current_definition &&
        movement.first_route_target_province_definition_byte_1b_u8 == expected_target_definition &&
        movement.loaded_disembark_penalty_days_rule_i32 == expected_loaded_rule,
        "production prestore raw observations lost zero/negative/null or owned provenance");
    Check(row.current_disembark_penalty_v1 &&
        row.current_disembark_penalty_v1->available &&
        row.current_disembark_penalty_v1->remaining_days == 12,
        "original current disembark days were replaced by conditional future rule");
  }
  if (scene.edge_selection_scene) {
    Check(movement.status == game::ArmyMovementProgressStatus::available,
        "existing current ratio/duration availability lost");
    Check(scene.accumulated_weight + scene.cached_speed == 107,
        "new scene lost its supplied post-ADD prefix107");
  }
  if (row.source_derived_next_daily_supply_frame_inputs_v1) {
    const auto &date = *row.source_derived_next_daily_supply_frame_inputs_v1;
    Check(!date.source_derived_full_cdate64_ready && !date.source_derived_next_date_storage_raw64,
        "date-free gate unexpectedly required a future full date");
  }
  Check(f.calls.abi_matches && f.calls.current_soldiers == 1 &&
      f.calls.maximum_soldiers == 1 && f.calls.supply_capacity == 1 &&
      f.calls.attrition_fraction == 1 && f.calls.monthly_supply == 1 &&
      f.calls.current_edge_speed == (getter_used ? 1U : 0U) &&
      f.calls.army_movement_admission == (scene.admission_getter_bound ? 1U : 0U) &&
      f.calls.first_edge_cost ==
          (scene.edge_selection_scene && scene.first_edge_cost_getter_bound ? 1U : 0U) &&
      f.calls.normalized_progress == (scene.edge_selection_scene ? 1U : 0U) &&
      f.calls.remaining_duration == (scene.edge_selection_scene ? 1U : 0U) &&
      f.calls.unit_state == (scene.arrival_transition_scene ? 2U : 0U) &&
      f.calls.current_army_context_reader == (scene.arrival_transition_scene ? 1U : 0U) &&
      f.calls.current_disembark_penalty_days == (scene.disembark_write_scene ? 1U : 0U),
      "whole reader ABI/count or current getter selection changed");
  Check(f.input == before, "readonly whole reader changed owned Unit/queue/route inputs");
}
std::string SerializeWhole(const game::ArmyStrengthSnapshot &row,
    std::string_view scene, std::size_t sequence, bool edge_selection_scene = false,
    bool arrival_transition_scene = false, bool disembark_write_scene = false) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, std::string(disembark_write_scene ? "unit-first-disembark-write-"
                          : arrival_transition_scene ? "unit-arrival-transition-"
                         : edge_selection_scene ? "unit-first-edge-selection-"
                                                : "unit-army-movement-admission-") +
                    std::string(scene));
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
  std::string out = "{\"schema\":\"xar.unit-army-movement-admission-native-context.v1\",\"scene\":";
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
         "\"war_ids\":[],\"transport_connection_id\":\"unit-army-movement-admission-12004\","
         "\"episode_id\":\"unit-army-movement-admission-12004\"},\"heartbeat_published\":false,"
         "\"native_inputs\":{\"subject_army_id_u32\":16777217,\"subject_carmy_id_u32\":33554433,"
         "\"unit_native_170_raw\":" + std::to_string(scene.state);
  out += ",\"unit_route_count_i32\":" + std::to_string(scene.route_count);
  out += ",\"unit_native_178_raw\":33554433,\"accumulated_movement_weight_raw\":";
  out += std::to_string(scene.accumulated_weight);
  out += ",\"cached_edge_speed_raw\":" + std::to_string(scene.cached_speed);
  out += ",\"fixture_current_edge_movement_rate_raw\":" + std::to_string(scene.edge_rate);
  out += ",\"current_edge_getter_bound\":";
  out += scene.edge_getter_bound ? "true" : "false";
  out += ",\"fixture_native_army_movement_admission\":";
  out += scene.admission_value ? "true" : "false";
  out += ",\"native_army_movement_admission_getter_bound\":";
  out += scene.admission_getter_bound ? "true" : "false";
  out += ",\"subject_stored_id_positions\":";
  AppendIds(out, scene.subject_scheduled ? std::vector<std::int32_t>{1, 3}
                                      : std::vector<std::int32_t>{});
  out += ",\"monthly_budget_callbacks_enabled\":false,\"Source23_binding_enabled\":false,"
         "\"full_date_required\":false},\"callbacks\":{\"unit_state\":0,\"current_edge_speed\":";
  out += std::to_string(f.calls.current_edge_speed);
  out += ",\"native_army_movement_admission\":" + std::to_string(f.calls.army_movement_admission);
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
         "\"post_entry_operands_held_into_gate\":true,\"intervening_empty_route_handler_closed\":false}";
  return out;
}
std::string EdgeSelectionContext(
    const Fixture &f, const Scene &scene, std::size_t sequence) {
  auto out = Context(f, scene, sequence);
  const auto replace = [&](std::string_view from, std::string_view to) {
    for (auto at = out.find(from); at != std::string::npos; at = out.find(from, at + to.size())) {
      out.replace(at, from.size(), to);
    }
  };
  replace("xar.unit-army-movement-admission-native-context.v1",
          "xar.unit-first-edge-selection-native-context.v1");
  replace("unit-army-movement-admission-12004", "unit-first-edge-selection-12004");
  replace("first selected supplied gate-entry slice after ADD",
          "conditional first edge selection after supplied ADD prefix; actual arrival/effects unobserved");
  std::string inputs = ",\"first_route_edge_weight_cost_raw\":";
  inputs += scene.first_edge_cost_getter_bound ? std::to_string(scene.first_edge_cost) : "null";
  inputs += ",\"first_edge_weight_cost_getter_bound\":";
  inputs += scene.first_edge_cost_getter_bound ? "true" : "false";
  inputs += ",\"first_edge_arrival_provider_byte_e_u8\":";
  inputs += scene.provider_byte_bound ? std::to_string(scene.provider_byte_e) : "null";
  inputs += ",\"first_edge_arrival_provider_byte_bound\":";
  inputs += scene.provider_byte_bound ? "true" : "false";
  inputs += ",\"normalized_edge_progress_raw\":" + std::to_string(scene.normalized_progress);
  inputs += ",\"first_route_edge_remaining_duration_raw\":" + std::to_string(scene.remaining_duration);
  inputs += ",\"expected_source_derived_next_progress_prefix_raw\":107";
  inputs += ",\"conditional_first_edge_arrival_branch_selected\":";
  inputs += scene.expected_branch_selected
      ? (*scene.expected_branch_selected ? "true" : "false") : "null";
  const auto input_at = out.find(",\"monthly_budget_callbacks_enabled\":");
  Check(input_at != std::string::npos, "whole native-input context anchor missing");
  out.insert(input_at, inputs);
  std::string callbacks = ",\"first_route_edge_weight_cost\":" + std::to_string(f.calls.first_edge_cost);
  callbacks += ",\"normalized_edge_progress\":" + std::to_string(f.calls.normalized_progress);
  callbacks += ",\"first_route_edge_remaining_duration\":" + std::to_string(f.calls.remaining_duration);
  callbacks += ",\"native_first_edge_provider_getter\":0";
  const auto callback_at = out.find(",\"monthly_budget_helpers\":");
  Check(callback_at != std::string::npos, "whole callback context anchor missing");
  out.insert(callback_at, callbacks);
  Check(!out.empty() && out.back() == '}', "whole context object boundary missing");
  out.pop_back();
  out += ",\"actual_first_edge_arrival_observed\":false,"
         "\"first_edge_consumption_or_clamp_reconstructed\":false,"
         "\"source_derived_branch_is_conditional\":true}";
  return out;
}
std::string_view RouteStatusName(game::ArmyRouteReadStatus status) {
  switch (status) {
  case game::ArmyRouteReadStatus::not_attempted: return "not_attempted";
  case game::ArmyRouteReadStatus::complete_empty: return "complete_empty";
  case game::ArmyRouteReadStatus::complete_nonempty: return "complete_nonempty";
  case game::ArmyRouteReadStatus::target_only: return "target_only";
  case game::ArmyRouteReadStatus::invalid_header: return "invalid_header";
  case game::ArmyRouteReadStatus::unresolved_entry: return "unresolved_entry";
  }
  return "not_attempted";
}
void AssertCurrentArmyContext(const Fixture &f, const Inputs &before,
    const std::vector<game::ArmySnapshot> &rows, const Scene &scene) {
  Check(scene.arrival_transition_scene && rows.size() == 1,
      "original current Army reader did not return one owned Unit");
  const auto &row = rows.front();
  Check(row.army_id == kUnit && row.owner_character_id == kActor &&
      row.controllable && row.has_current_province && row.current_province_id == 1,
      "current Army Unit/owner/current Province identity changed");
  Check(row.route_province_ids ==
          std::vector<std::int32_t>{scene.first_route_province_id, 3} &&
      row.route_read_status == game::ArmyRouteReadStatus::complete_nonempty &&
      row.route_source_count == 2 && row.move_target_observable &&
      row.move_target_province_id == 3,
      "original reader lost full ordered route/status/count");
  Check(row.army_state_code == 6 && row.army_state == "retreating" &&
      !row.in_combat && row.retreating,
      "original current state/raw170 context substituted");
  Check(f.calls.current_army_context_reader == 1 && f.calls.unit_state == 1 &&
      f.calls.abi_matches && f.input == before,
      "current Army reader receiver/count or readonly bytes changed");
}
void AppendCurrentArmyContext(
    std::string &out, const std::vector<game::ArmySnapshot> &rows) {
  out += '[';
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) out += ',';
    const auto &row = rows[index];
    out += "{\"army_id\":" + std::to_string(row.army_id);
    out += ",\"owner_character_id\":" + std::to_string(row.owner_character_id);
    out += ",\"controllable\":";
    out += row.controllable ? "true" : "false";
    out += ",\"has_current_province\":";
    out += row.has_current_province ? "true" : "false";
    out += ",\"current_province_id\":";
    out += row.has_current_province ? std::to_string(row.current_province_id) : "null";
    out += ",\"route_province_ids\":";
    AppendIds(out, row.route_province_ids);
    out += ",\"route_read_status\":";
    AppendString(out, RouteStatusName(row.route_read_status));
    out += ",\"route_source_count\":";
    out += row.route_source_count ? std::to_string(*row.route_source_count) : "null";
    out += ",\"move_target_observable\":";
    out += row.move_target_observable ? "true" : "false";
    out += ",\"move_target_province_id\":";
    out += row.move_target_observable ? std::to_string(row.move_target_province_id) : "null";
    out += ",\"army_state_code\":" + std::to_string(row.army_state_code);
    out += ",\"army_state\":";
    AppendString(out, row.army_state);
    out += ",\"in_combat\":";
    out += row.in_combat ? "true" : "false";
    out += ",\"retreating\":";
    out += row.retreating ? "true" : "false";
    out += '}';
  }
  out += ']';
}
std::string ArrivalTransitionContext(const Fixture &f, const Scene &scene,
    std::size_t sequence, const std::vector<game::ArmySnapshot> &current_armies) {
  auto out = EdgeSelectionContext(f, scene, sequence);
  const auto replace = [&](std::string_view from, std::string_view to) {
    for (auto at = out.find(from); at != std::string::npos; at = out.find(from, at + to.size())) {
      out.replace(at, from.size(), to);
    }
  };
  replace("xar.unit-first-edge-selection-native-context.v1",
          "xar.unit-arrival-transition-native-context.v1");
  replace("unit-first-edge-selection-12004", "unit-arrival-transition-12004");
  replace("conditional first edge selection after supplied ADD prefix; actual arrival/effects unobserved",
          "conditional first local Province assignment after supplied arrival branch; full effects unobserved");
  replace("\"unit_state\":0", "\"unit_state\":" + std::to_string(f.calls.unit_state));
  std::string inputs = ",\"unit_state_raw\":6,\"first_route_target_province_type_tag_u32\":";
  inputs += scene.first_target_type_tag_enabled
      ? std::to_string(scene.first_target_type_tag) : "null";
  inputs += ",\"first_route_target_province_type_tag_enabled\":";
  inputs += scene.first_target_type_tag_enabled ? "true" : "false";
  inputs += ",\"conditional_first_province_assignment_selected\":";
  inputs += scene.expected_first_assignment_selected
      ? (*scene.expected_first_assignment_selected ? "true" : "false") : "null";
  inputs += ",\"conditional_current_province_id_after_first_assignment\":";
  inputs += scene.expected_conditional_province_id
      ? std::to_string(*scene.expected_conditional_province_id) : "null";
  const bool selected = scene.expected_branch_selected.value_or(false);
  inputs += ",\"conditional_unit_168_raw_after_arrival_subtraction\":";
  inputs += std::to_string(selected ? 107 - scene.first_edge_cost : 107);
  inputs += ",\"conditional_route_province_ids_after_first_pop\":";
  AppendIds(inputs, selected ? std::vector<std::int32_t>{3}
                            : std::vector<std::int32_t>{scene.first_route_province_id, 3});
  inputs += ",\"conditional_unit_route_count_i32_after_first_pop\":";
  inputs += selected ? "1" : "2";
  inputs += ",\"conditional_consumed_first_route_province_id\":";
  inputs += selected ? std::to_string(scene.first_route_province_id) : "null";
  inputs += ",\"arrival_transition_input_ready\":";
  inputs += (!selected || scene.first_target_type_tag_enabled) ? "true" : "false";
  inputs += ",\"target_type_tag_demanded_by_conditional_arrival\":";
  inputs += selected ? "true" : "false";
  const auto input_at = out.find(",\"monthly_budget_callbacks_enabled\":");
  Check(input_at != std::string::npos, "arrival native-input context anchor missing");
  out.insert(input_at, inputs);
  const auto callback_at = out.find(",\"monthly_budget_helpers\":");
  Check(callback_at != std::string::npos, "arrival callback context anchor missing");
  out.insert(callback_at, ",\"read_armies_for_characters\":" +
      std::to_string(f.calls.current_army_context_reader) +
      ",\"arrival_helper\":0,\"first_province_writer\":0");
  Check(!out.empty() && out.back() == '}', "arrival context object boundary missing");
  out.pop_back();
  out += ",\"current_army_context\":";
  AppendCurrentArmyContext(out, current_armies);
  out += ",\"current_army_context_producer\":\"ReadArmiesForCharacters12004 -> production ReadArmiesForCharacters\","
         "\"current_army_context_is_current_not_future\":true,"
         "\"full_nativeframe_pipeline_exercised\":false,"
         "\"actual_first_province_assignment_observed\":false,"
         "\"final_helper_return_current_province_projected\":false,"
         "\"full_arrival_helper_reconstructed\":false,"
         "\"full_future_unit_callback_reconstructed\":false,"
         "\"battle_or_day_effects_reconstructed\":false}";
  return out;
}

std::string DisembarkWriteContext(const Fixture &f, const Scene &scene,
    std::size_t sequence, const std::vector<game::ArmySnapshot> &current_armies) {
  auto out = ArrivalTransitionContext(f, scene, sequence, current_armies);
  const auto replace = [&](std::string_view from, std::string_view to) {
    for (auto at = out.find(from); at != std::string::npos; at = out.find(from, at + to.size())) {
      out.replace(at, from.size(), to);
    }
  };
  replace("xar.unit-arrival-transition-native-context.v1",
          "xar.unit-first-disembark-write-native-context.v1");
  replace("unit-arrival-transition-12004", "unit-first-disembark-write-12004");
  replace("conditional first local Province assignment after supplied arrival branch; full effects unobserved",
          "conditional first Army1D0 fixed write before outer Province assignment; full effects unobserved");
  std::string inputs = ",\"current_unit_arrival_prestore_inputs_enabled\":";
  inputs += scene.prestore_inputs_enabled ? "true" : "false";
  inputs += ",\"current_province_type_tag_u32\":";
  inputs += scene.prestore_inputs_enabled ? std::to_string(kProvinceMagic) : "null";
  inputs += ",\"unit_kind_18_raw_i32\":";
  inputs += scene.prestore_inputs_enabled ? std::to_string(scene.unit_kind_18) : "null";
  inputs += ",\"current_province_definition_byte_1b_u8\":";
  inputs += scene.prestore_inputs_enabled && scene.definition_pointers_present
      ? std::to_string(scene.current_definition_byte_1b) : "null";
  inputs += ",\"first_route_target_province_definition_byte_1b_u8\":";
  inputs += scene.prestore_inputs_enabled && scene.definition_pointers_present
      ? std::to_string(scene.target_definition_byte_1b) : "null";
  inputs += ",\"loaded_disembark_penalty_days_rule_i32\":";
  inputs += scene.prestore_inputs_enabled && scene.loaded_disembark_days_rule_bound
      ? std::to_string(scene.loaded_disembark_days_rule) : "null";
  inputs += ",\"loaded_disembark_penalty_days_rule_bound\":";
  inputs += scene.loaded_disembark_days_rule_bound ? "true" : "false";
  inputs += ",\"current_disembark_penalty_remaining_days\":12";
  inputs += ",\"conditional_prestore_24e23e0_call_selected\":";
  inputs += scene.expected_prestore_call_selected ? "true" : "false";
  inputs += ",\"conditional_fixed_disembark_days_write_selected\":";
  inputs += scene.expected_fixed_days_write_selected ? "true" : "false";
  inputs += ",\"conditional_disembark_days_fixed_write_value_i32\":";
  inputs += scene.expected_fixed_days_write_value
      ? std::to_string(*scene.expected_fixed_days_write_value) : "null";
  inputs += ",\"fixed_disembark_write_input_ready\":";
  inputs += scene.expected_fixed_write_ready ? "true" : "false";
  inputs += ",\"loaded_days_rule_demanded_by_conditional_fixed_write\":";
  inputs += scene.expected_loaded_rule_demanded ? "true" : "false";
  const auto input_at = out.find(",\"monthly_budget_callbacks_enabled\":");
  Check(input_at != std::string::npos, "disembark native-input context anchor missing");
  out.insert(input_at, inputs);
  const auto callback_at = out.find(",\"monthly_budget_helpers\":");
  Check(callback_at != std::string::npos, "disembark callback context anchor missing");
  out.insert(callback_at, ",\"current_disembark_penalty_days\":" +
      std::to_string(f.calls.current_disembark_penalty_days) +
      ",\"army_departure_helper\":0,\"fixed_disembark_days_writer\":0");
  Check(!out.empty() && out.back() == '}', "disembark context object boundary missing");
  out.pop_back();
  out += ",\"current_disembark_days_observed_from_original_collector\":true,"
         "\"actual_fixed_disembark_days_write_observed\":false,"
         "\"full_army_departure_callback_reconstructed\":false,"
         "\"conditional_fixed_write_is_first_local_assignment_only\":true}";
  return out;
}

} // namespace

int main(int argc, char **argv) {
  std::filesystem::path output;
  bool edge_selection_mode = false;
  bool arrival_transition_mode = false;
  bool disembark_write_mode = false;
  try {
    Check(argc == 3 && (std::string_view(argv[1]) == "--wire-dir" ||
                       std::string_view(argv[1]) == "--edge-selection-wire-dir" ||
                       std::string_view(argv[1]) == "--arrival-transition-wire-dir" ||
                       std::string_view(argv[1]) == "--disembark-write-wire-dir"),
        "usage: xar_ck3_12004_unit_army_movement_admission_whole_test "
        "--wire-dir <fresh-dir> | --edge-selection-wire-dir <fresh-dir> | "
        "--arrival-transition-wire-dir <fresh-dir> | --disembark-write-wire-dir <fresh-dir>");
    edge_selection_mode = std::string_view(argv[1]) == "--edge-selection-wire-dir";
    arrival_transition_mode = std::string_view(argv[1]) == "--arrival-transition-wire-dir";
    disembark_write_mode = std::string_view(argv[1]) == "--disembark-write-wire-dir";
    const Scene *scenes = disembark_write_mode ? kDisembarkWriteScenes.data()
        : arrival_transition_mode ? kArrivalTransitionScenes.data()
        : edge_selection_mode ? kEdgeSelectionScenes.data() : kScenes.data();
    const auto scene_count = disembark_write_mode ? kDisembarkWriteScenes.size()
        : arrival_transition_mode ? kArrivalTransitionScenes.size()
        : edge_selection_mode ? kEdgeSelectionScenes.size() : kScenes.size();
    output = argv[2];
    std::filesystem::create_directories(output);
    std::string aggregate = "{\"schema_version\":1,\"scene_order\":[";
    for (std::size_t index = 0; index < scene_count; ++index) {
      if (index != 0) aggregate += ',';
      AppendString(aggregate, scenes[index].name);
    }
    aggregate += "],\"samples\":{";
    for (std::size_t index = 0; index < scene_count; ++index) {
      const auto &scene = scenes[index];
      auto fixture = std::make_unique<Fixture>(scene);
      auto before = std::make_unique<Inputs>(fixture->input);
      active = fixture.get();
      std::vector<game::ArmySnapshot> current_armies;
      if (arrival_transition_mode || disembark_write_mode) {
        const std::array<std::int32_t, 1> owners{kActor};
        ++fixture->calls.current_army_context_reader;
        Check(current::ReadArmiesForCharacters12004(
                  fixture->bindings, owners, current_armies, kActor),
            "original current Army reader failed");
        AssertCurrentArmyContext(*fixture, *before, current_armies, scene);
      }
      const std::array<current::ArmyStrengthScope, 1> scope{
          current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      const auto result = current::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows);
      Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "genuine whole Strength did not produce an available original row");
      AssertScene(*fixture, *before, rows.front(), scene);
      const auto wire = SerializeWhole(rows.front(), scene.name, index + 1,
          edge_selection_mode, arrival_transition_mode, disembark_write_mode);
      Write(output / (std::string(scene.name) + ".command-result.json"), wire);
      Write(output / (std::string(scene.name) + ".native-context.json"),
          disembark_write_mode
              ? DisembarkWriteContext(*fixture, scene, index + 1, current_armies)
              : arrival_transition_mode
              ? ArrivalTransitionContext(*fixture, scene, index + 1, current_armies)
              : edge_selection_mode ? EdgeSelectionContext(*fixture, scene, index + 1)
                                    : Context(*fixture, scene, index + 1));
      if (index != 0) aggregate += ',';
      AppendString(aggregate, scene.name);
      aggregate += ':';
      aggregate += wire;
      active = nullptr;
    }
    aggregate += "}}";
    Write(output / (disembark_write_mode ? "unit-first-disembark-write-whole.json"
                 : arrival_transition_mode ? "unit-arrival-transition-whole.json"
                 : edge_selection_mode ? "unit-first-edge-selection-whole.json"
                                       : "unit-army-movement-admission-whole.json"), aggregate);
    if (disembark_write_mode) {
      Write(output / "PRODUCER-RECEIPT.json",
          "{\"schema\":\"xar.unit-first-disembark-write-producer-receipt.v1\","
          "\"status\":\"PASS\",\"scene_count\":7,\"whole_reader_calls\":7,\"whole_serializer_calls\":7,"
          "\"current_army_context_reader_calls\":7,\"current_disembark_penalty_days_getter_calls\":7,"
          "\"current_army_context_from_original_reader\":true,"
          "\"current_disembark_days_from_original_collector\":true,"
          "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
          "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
          "\"native_first_edge_provider_getter_invoked\":false,\"actual_arrival_observed\":false,"
          "\"native_arrival_helper_invoked\":false,\"first_province_writer_invoked\":false,"
          "\"army_departure_helper_invoked\":false,\"fixed_disembark_days_writer_invoked\":false,"
          "\"old_GREEN_replayed\":false,\"old_four_scenes_replayed\":false,"
          "\"old_edge_selection_scenes_replayed\":false,\"old_arrival_transition_scenes_replayed\":false,"
          "\"full_adapter_snapshot_path_exercised\":false,\"full_nativeframe_pipeline_exercised\":false}");
    } else if (arrival_transition_mode) {
      Write(output / "PRODUCER-RECEIPT.json",
          "{\"schema\":\"xar.unit-arrival-transition-producer-receipt.v1\","
          "\"status\":\"PASS\",\"scene_count\":5,\"whole_reader_calls\":5,\"whole_serializer_calls\":5,"
          "\"current_army_context_reader_calls\":5,\"current_army_context_from_original_reader\":true,"
          "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
          "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
          "\"native_first_edge_provider_getter_invoked\":false,\"actual_arrival_observed\":false,"
          "\"native_arrival_helper_invoked\":false,\"first_province_writer_invoked\":false,"
          "\"old_GREEN_replayed\":false,\"old_four_scenes_replayed\":false,"
          "\"old_edge_selection_scenes_replayed\":false,"
          "\"full_adapter_snapshot_path_exercised\":false,\"full_nativeframe_pipeline_exercised\":false}");
    } else if (edge_selection_mode) {
      Write(output / "PRODUCER-RECEIPT.json",
          "{\"schema\":\"xar.unit-first-edge-selection-producer-receipt.v1\","
          "\"status\":\"PASS\",\"scene_count\":5,\"whole_reader_calls\":5,\"whole_serializer_calls\":5,"
          "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
          "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
          "\"native_first_edge_provider_getter_invoked\":false,\"actual_arrival_observed\":false,"
          "\"old_GREEN_replayed\":false,\"old_four_scenes_replayed\":false,"
          "\"full_adapter_snapshot_path_exercised\":false}");
    } else {
      Write(output / "PRODUCER-RECEIPT.json",
          "{\"schema\":\"xar.unit-army-movement-admission-producer-receipt.v1\","
          "\"status\":\"PASS\",\"scene_count\":4,\"whole_reader_calls\":4,\"whole_serializer_calls\":4,"
          "\"fixture_owned_objects_and_callbacks\":true,\"all_fixture_input_bytes_unchanged\":true,"
          "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
          "\"old_GREEN_replayed\":false,\"full_adapter_snapshot_path_exercised\":false}");
    }
    std::cout << (disembark_write_mode ? "seven first disembark write whole scenes emitted\n"
                 : arrival_transition_mode ? "five arrival transition whole scenes emitted\n"
                 : edge_selection_mode ? "five first edge selection whole scenes emitted\n"
                                       : "four current CArmy admission whole scenes emitted\n");
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    if (!output.empty()) {
      std::string receipt = "{\"schema\":";
      AppendString(receipt, disembark_write_mode
          ? "xar.unit-first-disembark-write-producer-receipt.v1"
          : arrival_transition_mode ? "xar.unit-arrival-transition-producer-receipt.v1"
          : edge_selection_mode ? "xar.unit-first-edge-selection-producer-receipt.v1"
                                : "xar.unit-army-movement-admission-producer-receipt.v1");
      receipt += ",\"status\":\"FAIL\",\"error\":";
      AppendString(receipt, error.what());
      receipt += ",\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false}";
      std::ofstream file(output / "PRODUCER-RECEIPT.json", std::ios::binary);
      file << receipt << '\n';
    }
    std::cerr << error.what() << '\n';
    return 1;
  }
}

// AUTHORED_NOTRUN: genuine whole Strength hook + production serializer.
// All objects and callbacks are fixture-owned. Other already-qualified current
// physical operands are explicitly supplied as typed fixture inputs below;
// their native full7 collector is not requalified by this new position fixture.
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 0x01000001, kArmy = 0x02000001;
constexpr std::int32_t kArrg = 0x03000001, kPersistent = 0x04000001;
constexpr std::uintptr_t kBase = 0x140000000ULL;
struct Scene {
  const char *name;
  bool target_allowed, current_allowed, permission_bound;
  bool invalid_magic, owner_zero, stale_owner, other_unit, route_empty;
  std::int64_t prepared;
};
constexpr std::array<Scene, 10> kScenes{{
  {"target_true", true, false, true, false, false, false, false, false, 10000},
  {"target_false", false, true, true, false, false, false, false, false, 10000},
  {"permission_unavailable", false, true, false, false, false, false, false, false, 10000},
  {"invalid_target_magic", false, true, true, true, false, false, false, false, 10000},
  {"owner_ref_zero", true, false, true, false, true, false, false, false, 10000},
  {"stale_owner_fallback", true, false, true, false, false, true, false, false, 10000},
  {"different_associated_unit", true, false, true, false, false, false, true, false, 10000},
  {"empty_route", true, false, true, false, false, false, false, true, 10000},
  {"zero_prepared_missing_permission", false, true, false, false, false, false, false, false, 0},
  {"negative_prepared_missing_permission", false, true, false, false, false, false, false, false, -10000},
}};
void Check(bool ok, const char *message) { if (!ok) throw std::runtime_error(message); }
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture store extent");
  std::memcpy(object.data() + offset, &value, sizeof value);
}
struct Inputs {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0x30> units{}, armies{}, arrgs{}, characters{};
  std::array<std::byte, 0x20> unit_rows{}, army_rows{}, arrg_rows{};
  std::array<std::byte, 0x30> character_rows{};
  std::array<std::byte, 0x198> unit{};
  std::array<std::byte, 0x1F0> army{};
  std::array<std::byte, 0x50> arrg{};
  std::array<std::byte, 0x860> current{}, target{};
  std::array<std::byte, 0x20> owner{}, holder{}, fallback{};
  std::array<void *, 3> provinces{};
  std::array<std::int32_t, 1> arrg_ids{kArrg};
  std::array<std::int32_t, 1> route_ids{2};
  std::array<void *, 1> route_nodes{};
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Fixture;
Fixture *active = nullptr;
std::int32_t Current(void *, std::uint8_t);
std::int32_t Maximum(void *);
std::int32_t State(void *);
std::int32_t *Holder(void *, std::int32_t *);
bool Political(void *, void *);
struct Fixture {
  Inputs input{};
  const Scene &scene;
  void *state = input.state.data(), *units = input.units.data(), *armies = input.armies.data();
  void *arrgs = input.arrgs.data(), *characters = input.characters.data();
  void *fallback = input.fallback.data(), *province_fallback = input.current.data();
  ck3_12004::ArmyBindings bindings{};
  std::size_t holder_calls = 0, political_calls = 0;
  bool abi = true;
  explicit Fixture(const Scene &s) : scene(s) {
    const auto exact = ck3_12004::BindArmyImage12004(kBase, ck3_12004::kExecutableSha256);
    const auto &b = exact.next_route_replenishment_position_bindings;
    Check(b.enabled && reinterpret_cast<std::uintptr_t>(b.character_storage_slot) == kBase + 0x5C67568 &&
        reinterpret_cast<std::uintptr_t>(b.character_fallback_slot) == kBase + 0x5C67570 &&
        reinterpret_cast<std::uintptr_t>(b.read_province_holder) == kBase + 0x247D010 &&
        reinterpret_cast<std::uintptr_t>(b.owner_holder_eligible) == kBase + 0x2C097F0,
        "genuine actual4 Army factory did not bind new readonly family");
    Check(!ck3_12004::BindNextRouteReplenishmentPositionImage12004(kBase, "old-sha").enabled,
        "wrong build admitted");
    Store(input.state, 0xA0, static_cast<void *>(input.data.data()));
    input.provinces = {nullptr, input.current.data(), input.target.data()};
    Store(input.data, 0x140, static_cast<void *>(input.provinces.data()));
    Store(input.data, 0x14C, std::int32_t{3});
    Store(input.current, 0x10, std::int32_t{1});
    Store(input.target, 0x10, std::int32_t{2});
    Store(input.target, 0x85C, s.invalid_magic ? std::uint32_t{0} : std::uint32_t{0x50726F76});
    auto registry = [](auto &header, auto &rows, void *object) {
      Store(header, 0x20, static_cast<void *>(rows.data()));
      Store(header, 0x2C, std::int32_t{2}); Store(rows, 0x18, object);
    };
    registry(input.units, input.unit_rows, input.unit.data());
    registry(input.armies, input.army_rows, input.army.data());
    registry(input.arrgs, input.arrg_rows, input.arrg.data());
    Store(input.characters, 0x20, static_cast<void *>(input.character_rows.data()));
    Store(input.characters, 0x2C, std::int32_t{3});
    Store(input.owner, 0x18, s.owner_zero ? std::int32_t{0} : std::int32_t{0x01000001});
    Store(input.holder, 0x18, std::int32_t{0x02000002});
    Store(input.fallback, 0x18, std::int32_t{-1});
    Store(input.character_rows, s.owner_zero ? 8U : 0x18U, static_cast<void *>(input.owner.data()));
    Store(input.character_rows, 0x28, static_cast<void *>(input.holder.data()));
    Store(input.unit, 0x10, kUnit); Store(input.unit, 0x14, std::uint32_t{0x556E6974});
    Store(input.unit, 0x174, s.stale_owner ? std::int32_t{0x09000001} :
        (s.owner_zero ? std::int32_t{0} : std::int32_t{0x01000001}));
    Store(input.unit, 0x178, kArmy);
    Store(input.unit, 0x20, static_cast<void *>(input.current.data()));
    input.route_nodes[0] = input.route_ids.data();
    Store(input.unit, 0x38, static_cast<void *>(input.route_nodes.data()));
    Store(input.unit, 0x40, std::int32_t{1});
    Store(input.unit, 0x44, s.route_empty ? std::int32_t{0} : std::int32_t{1});
    Store(input.army, 0x10, kArmy); Store(input.army, 0x14, std::uint32_t{0x41726D79});
    Store(input.army, 0x124, kUnit);
    Store(input.army, 0x38, static_cast<void *>(input.arrg_ids.data()));
    Store(input.army, 0x40, std::int32_t{1}); Store(input.army, 0x44, std::int32_t{1});
    Store(input.arrg, 0x10, kArrg); Store(input.arrg, 0x14, std::uint32_t{0x41725267});
    Store(input.arrg, 0x38, std::int32_t{80}); Store(input.arrg, 0x3C, std::int32_t{100});
    bindings.enabled = true; bindings.current_movement_progress_enabled = true;
    bindings.game_state_slot = &state; bindings.unit_storage_slot = &units;
    bindings.internal_army_storage_slot = &armies; bindings.regiment_storage_slot = &arrgs;
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.get_unit_state = State;
    auto &owned = bindings.next_route_replenishment_position_bindings;
    owned.enabled = true; owned.character_storage_slot = &characters;
    owned.character_fallback_slot = &fallback; owned.province_fallback_slot = &province_fallback;
    owned.read_province_holder = Holder; owned.owner_holder_eligible = s.permission_bound ? Political : nullptr;
  }
};
std::int32_t Current(void *p, std::uint8_t flags) {
  active->abi &= p == active->input.army.data() + 0x38 && flags == 0; return 80;
}
std::int32_t Maximum(void *p) { active->abi &= p == active->input.army.data(); return 100; }
std::int32_t State(void *p) { active->abi &= p == active->input.unit.data(); return 7; }
std::int32_t *Holder(void *p, std::int32_t *out) {
  ++active->holder_calls; active->abi &= p == active->input.target.data();
  *out = 0x02000002; return out;
}
bool Political(void *owner, void *holder) {
  ++active->political_calls;
  active->abi &= holder == active->input.holder.data() && owner ==
      (active->scene.stale_owner ? active->input.fallback.data() : active->input.owner.data());
  return active->scene.target_allowed;
}
void AttachHeldPhysicalFixtureInputs(game::ArmyStrengthSnapshot &row, const Scene &scene) {
  // This supplies the independent qualified current DTO, not a claimed fresh
  // full7 native capture or future preparation result.
  row.scoped_ordered_refill_inputs_v1.emplace();
  auto &scope = *row.scoped_ordered_refill_inputs_v1;
  scope.status = "available"; scope.subject_army_id = kUnit; scope.subject_carmy_id = kArmy;
  scope.native_persistent_occurrence_count = 1; scope.native_army_refresh_occurrence_count = 1;
  scope.persistent_occurrences.push_back({0, kPersistent}); scope.army_refresh_occurrence_indices.push_back(0);
  game::ArmyOrderedRefillPersistentV1 persistent{};
  persistent.persistent_regiment_id = kPersistent; persistent.prepared_fraction_raw = scene.prepared;
  for (std::int32_t i = 0; i < 7; ++i) {
    game::ArmyOrderedRefillChunkV1 c{};
    const bool held_other_unit = scene.other_unit && i == 1;
    c.physical_index = i;
    c.current_soldiers = i == 0 || held_other_unit ? 80 : 0;
    c.maximum_soldiers = i == 0 || held_other_unit ? 100 : 0;
    c.owner_persistent_regiment_id = kPersistent; c.owner_resolved_full_id = kPersistent;
    c.owner_guard_138_raw = 1; c.owner_definition_magic_38_raw = 0x4744624F;
    c.q_ordinal_raw = i; c.army_regiment_id_raw = i == 0 ? kArrg : (held_other_unit ? kArrg + 1 : -1);
    c.origin_province_id = 1; c.origin_province_788_raw = -1; c.origin_province_73c_raw = -1;
    c.associated_arrg_resolved_full_id = held_other_unit ? kArrg + 1 : kArrg;
    c.associated_arrg_magic_raw = 0x41725267;
    c.associated_army_raw_full_id = held_other_unit ? kArmy + 1 : kArmy;
    c.associated_army_resolved_full_id = c.associated_army_raw_full_id;
    c.army_byte_1d4_raw = 0; c.army_byte_1ec_raw = 0; c.native_army_in_combat = false;
    c.associated_unit_raw_full_id = held_other_unit ? kUnit + 1 : kUnit;
    c.associated_unit_resolved_full_id = c.associated_unit_raw_full_id; c.unit_170_raw = 0;
    c.unit_position_province_magic_raw = 0x50726F76;
    c.unit_position_owner_resolved_full_id = 0x01000001; c.unit_position_holder_resolved_full_id = 0x03000002;
    c.native_unit_position_eligible = scene.current_allowed;
    persistent.chunks.push_back(c);
  }
  scope.persistent_regiments.push_back(std::move(persistent));
  row.regiment_replenishment_records_v1.emplace();
  game::ArmyRegimentReplenishmentRecordsSnapshotV1 data{};
  data.status = game::ArmyRegimentReplenishmentRecordsStatusV1::available;
  data.army_regiment_id = kArrg; data.native_data_record_count = 1;
  game::ArmyRegimentReplenishmentRecordV1 record{};
  record.available = true; record.record_index = 0; record.persistent_regiment_id = kPersistent;
  record.chunk_index = 0; record.current_soldiers = 80; record.maximum_soldiers = 100;
  record.effective_current_soldiers = 80; record.state_raw = 0; record.chunk_army_regiment_id = kArrg;
  record.native_can_replenish = true; record.native_chunk_can_replenish = scene.current_allowed;
  record.persistent_monthly_replenishment_fraction_raw = scene.prepared;
  record.persistent_prepared_replenishment_fraction_raw = scene.prepared;
  data.records.push_back(record); row.regiment_replenishment_records_v1->push_back(data);
}
void String(std::string &out, std::string_view value) {
  out += '"'; for (char c : value) { if (c == '"' || c == '\\') out += '\\'; out += c; } out += '"';
}
void Ids(std::string &out, const std::vector<std::int32_t> &ids) {
  out += '['; bool comma = false; for (auto id : ids) { if (comma) out += ','; comma = true; out += std::to_string(id); } out += ']';
}
void Write(const std::filesystem::path &path, const std::string &text) {
  std::ofstream stream(path, std::ios::binary); Check(bool(stream), "wire output open failed");
  stream << text; Check(bool(stream), "wire output write failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir", "required fresh wire directory");
    const std::filesystem::path output(argv[2]); std::filesystem::create_directories(output);
    std::string aggregate = "{\"schema_version\":1,\"samples\":{";
    bool comma = false;
    for (const auto &scene : kScenes) {
      auto fixture = std::make_unique<Fixture>(scene);
      auto before = std::make_unique<Inputs>(fixture->input); active = fixture.get();
      const std::array<ck3_12004::ArmyStrengthScope, 1> scope{
          ck3_12004::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      Check(ck3_12004::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows) ==
          game::ReadArmyStrengthsResult::available && rows.size() == 1, "whole Strength unavailable");
      Check(rows[0].next_route_replenishment_position_inputs_v1.has_value(), "same-query position hook missing");
      const auto &position = *rows[0].next_route_replenishment_position_inputs_v1;
      const bool demanded = !scene.route_empty && !scene.invalid_magic && scene.permission_bound;
      Check(fixture->abi && fixture->holder_calls == (demanded ? 1U : 0U) &&
          fixture->political_calls == (demanded ? 1U : 0U), "real holder/political ABI or demand count");
      Check(fixture->input == *before, "readonly query mutated fixture memory");
      if (scene.route_empty) Check(position.status == "not_applicable", "known empty route changed");
      else if (scene.invalid_magic) Check(position.native_first_target_position_eligible == false &&
          !position.owner_requested_full_id, "invalid Province demanded political inputs");
      else if (!scene.permission_bound) Check(position.status == "unavailable" &&
          !position.native_first_target_position_eligible, "missing permission became false/true");
      else Check(position.native_first_target_position_eligible == scene.target_allowed &&
          position.owner_used_fallback == scene.stale_owner, "native target verdict/fallback mismatch");
      if (scene.owner_zero) Check(position.owner_requested_full_id == 0 &&
          position.owner_resolved_full_id == 0, "legal Character full ID zero rejected");
      AttachHeldPhysicalFixtureInputs(rows[0], scene);
      std::string wire = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"fixture\","
          "\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
          "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
      game::AppendArmyStrengthV1(wire, rows[0], [](auto value) { return std::to_string(value); }, Ids, String);
      wire += "]}}";
      wire = game::Render12004BuildIdentity(std::move(wire), game::Ck3_12004AdapterDescriptor());
      Write(output / (std::string(scene.name) + ".command-result.json"), wire);
      if (comma) aggregate += ','; comma = true; String(aggregate, scene.name); aggregate += ':'; aggregate += wire;
      active = nullptr;
    }
    aggregate += "}}"; Write(output / "next-route-replenishment-position-whole.json", aggregate);
    Write(output / "PRODUCER-RECEIPT.json", "{\"status\":\"PASS\",\"whole_strength_queries\":10,"
        "\"new_position_sampler_hook_exercised\":true,\"physical_input_origin\":\"fixture_owned_existing_typed_current_input\","
        "\"old_full7_collector_requalified\":false,\"input_bytes_unchanged\":true,\"native_EXE_callbacks_invoked\":false,"
        "\"actual_arrival_observed\":false,\"actual_prepared_cache_write\":false,\"full_monthly_ready\":false}");
    std::cout << "ten NEW next-route replenishment position whole wires emitted\n"; return 0;
  } catch (const std::exception &error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}

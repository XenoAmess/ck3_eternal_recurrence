// Seven FIRST synthetic cases: new mirror -> production serializers -> whole
// reinforcement wire. Old test matrices and game entry points are not called.
#include "battle_reinforcement_arrival_memory_fixture.hpp"
#include "battle_reinforcement_arrival_whole_wire_12003.hpp"
#include "xar_bridge/battle_reinforcement_arrival_admission_12003_reader.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {
using xar::arrival_first_fixture::Memory;
using xar::arrival_first_fixture::Put;
using xar::game::ArrivalAdmission12003Status;
using xar::game::BattleReinforcementArrivalAdmission12003Snapshot;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

xar::game::BattleReinforcementAssignmentSnapshot BaseFrame(
    const BattleReinforcementArrivalAdmission12003Snapshot &admission,
    bool assigned, bool arrived, bool active) {
  using namespace xar::game;
  BattleReinforcementAssignmentSnapshot base{};
  base.status = BattleReinforcementAssignmentStatus::available;
  base.snapshot_revision = Memory::native_revision;
  base.observed_date_raw = Memory::date_raw;
  base.selected_public_cunit_id = Memory::subject_id;
  base.selected_native_carmy_id = Memory::subject_native_id;
  // Synthetic native assignment membership is metadata of this fixture frame;
  // the new native mirror resolves physical foreign CUnit/CArmy objects itself.
  base.coordinator_id = 0x06000001;
  base.unit_stack_stored_index = 0;
  base.subunit_stored_index = 0;
  base.battle_reinforcement_assignment_ready = true;
  BattleReinforcementSignalSnapshot signal{};
  signal.assigned_to_help = assigned;
  if (!arrived) signal.first_route_edge_remaining_duration_q100000 = 100'000;
  base.signal = signal;
  BattleReinforcementAssignmentStateSnapshot assignment{};
  if (assigned) {
    assignment.assignment_target_province_id = 3;
    assignment.target_provenance = "native_help_override";
  }
  if (active) {
    assignment.active_combat_id = Memory::first_combat_id;
    assignment.combat_binding_status = "already_in_active_combat";
  }
  base.assignment = assignment;
  BattleReinforcementRouteSnapshot route{};
  route.current_province_id = arrived ? 3 : 2;
  if (!arrived || assigned) route.move_target_province_id = 3;
  if (!arrived) route.route_province_ids = {3};
  route.arrival_date_raws = arrived ? std::vector<std::int32_t>{}
      : std::vector<std::int32_t>{Memory::date_raw + 24};
  route.route_alignment = assigned ? "aligned_to_assignment" : "no_assignment";
  if (assigned) route.assignment_eta_date_raw = arrived ? Memory::date_raw
      : Memory::date_raw + 24;
  base.route = route;
  BattleReinforcementNativeOrderSnapshot order{};
  order.support_search_province_ids_in_stored_order = {3};
  BattleReinforcementParentSubunitSnapshot row{};
  row.public_cunit_ids_in_stored_order = {Memory::subject_id};
  row.assigned_to_help = assigned;
  if (assigned) row.assignment_target_province_id = 3;
  order.parent_subunits_in_stored_order = {row};
  base.native_order = order;
  BattleReinforcementContactProjectionSnapshot contact{};
  if (assigned) {
    contact.status = "available";
    contact.current_target_compatible_combat_ids_in_stored_order =
        admission.current_target_compatible_combat_ids_in_stored_order;
    if (!contact.current_target_compatible_combat_ids_in_stored_order.empty())
      contact.contact_if_now_selected_combat_id =
          contact.current_target_compatible_combat_ids_in_stored_order.back();
  }
  base.contact_projection = contact;
  return base;
}

std::string Hello() {
  return "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"0.1.0\","
      "\"pid\":1,\"session_generation\":0,\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\","
      "\"capabilities\":[\"game.state.snapshot\","
      "\"game.command.query-battle-reinforcement-assignment-v1-N\"]}";
}

std::string SemanticSnapshot(bool arrived, bool active, bool retreating) {
  const auto subject = std::to_string(Memory::subject_id);
  const auto owner = std::to_string(Memory::owner_id);
  const std::string province = arrived ? "3" : "2";
  const std::string route = arrived ? "[]" : "[3]";
  return "{\"type\":\"state_snapshot\",\"protocol_version\":1,"
      "\"snapshot_id\":\"native:41\",\"revision\":41,\"state\":{"
      "\"phase\":\"map_hud\",\"date\":\"1066.10.1\",\"date_raw\":53178264,"
      "\"speed\":1,\"paused\":true,\"map_ready\":true,\"history\":[],"
      "\"active_event\":null,\"pending_character_interaction\":null,"
      "\"played_character\":{\"character_id\":29829,\"alive\":true},"
      "\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[{"
      "\"army_id\":" + subject + ",\"owner_character_id\":" + owner +
      ",\"soldiers\":1000,\"current_province_id\":" + province +
      ",\"move_target_province_id\":" + (arrived ? "null" : "3") +
      ",\"route_province_ids\":" + route +
      ",\"controllable\":false,\"in_combat\":" + (active ? "true" : "false") +
      ",\"retreating\":" + (retreating ? "true" : "false") + "}]}}";
}

void Save(const std::filesystem::path &directory, std::string_view name,
          const BattleReinforcementArrivalAdmission12003Snapshot &admission,
          bool assigned, bool arrived, bool active, bool retreating) {
  const auto whole = xar::game::SerializeBattleReinforcementAssignmentWithArrival12003(
      BaseFrame(admission, assigned, arrived, active), admission);
  Require(!whole.empty(), "production reinforcement whole-wire serialization failed");
  const auto step = "query-battle-reinforcement-assignment-v1-" +
      std::to_string(Memory::subject_id);
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Require(stream.good(), "cannot open FIRST native whole-wire file");
  stream << "{\"case_name\":\"" << name << "\",\"fixture\":{"
      "\"synthetic\":true,\"source_baseline\":\"df87fd85\","
      "\"integration_baseline\":\"be06a134b9a5472275e08ea452a8e3542b192fb8\","
      "\"game_version\":\"1.20.0.3\",\"exe_sha256\":"
      "\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"},"
      "\"hello\":" << Hello() << ",\"semantic_snapshot\":"
      << SemanticSnapshot(arrived, active, retreating) << ",\"result\":{"
      "\"step\":\"" << step << "\",\"accepted\":true,\"status\":\"available\","
      "\"query_sequence\":1,\"snapshot_revision\":41,"
      "\"battle_reinforcement_assignment\":" << whole << "}}\n";
  Require(stream.good(), "cannot write FIRST native whole-wire file");
  std::cout << name << " GREEN\n";
}

void RunCase(const std::filesystem::path &directory, std::string_view name) {
  Memory f;
  const bool active = name == "already_participating";
  const bool arrived = active || name == "help_retreating_arrived";
  const bool ordinary = name == "ordinary_last_compatible" ||
                         name == "ordinary_no_compatible";
  const bool retreating = name == "help_retreating_arrived";
  const bool assigned = !ordinary && !active;
  xar::arrival_first_fixture::g_join_defender =
      name == "help_defender_en_route" || name == "ordinary_last_compatible";
  xar::arrival_first_fixture::g_empty = name == "help_empty_en_route";
  if (name != "ordinary_no_compatible") f.AddCombat(0, active);
  if (name == "ordinary_last_compatible") f.AddCombat(1);
  if (arrived) Put(f.unit[0], 0x20, f.province[1].data());
  if (retreating) Put(f.unit[0], 0x170, std::int32_t{1});
  const auto before = f.PhysicalBytes();
  const auto provenance = active ? "current_active_combat" :
      ordinary ? "committed_route_final" : "native_help_override";
  BattleReinforcementArrivalAdmission12003Snapshot admission{};
  const auto status = xar::ck3_12002::ReadBattleReinforcementArrivalAdmission12003(
      f.bindings, f.scope, Memory::subject_id, 3, provenance, admission);
  Require(status == ArrivalAdmission12003Status::available,
          "new FIRST current admission reader did not produce available result");
  Require(f.PhysicalBytes() == before, "current admission mirror mutated owned fixture bytes");
  admission.snapshot_revision = Memory::native_revision;
  Require(admission.subject.public_cunit_id == Memory::subject_id &&
      admission.subject.native_carmy_id == Memory::subject_native_id &&
      admission.subject.owner_character_id == Memory::owner_id &&
      !admission.future_binding, "subject full IDs or current-only semantics changed");
  const auto eligibility = active ? "already_in_active_combat" :
      (retreating || name == "help_empty_en_route") ? "ineligible" : "eligible";
  Require(admission.eligibility_now == eligibility, "FIRST eligibility differs");
  const auto side = name == "ordinary_no_compatible" ? "none" :
      xar::arrival_first_fixture::g_join_defender ? "defender" : "attacker";
  Require(admission.join_side == side, "reverse hostility/actual current side differs");
  Require(admission.subject_current_participation_verified == active,
          "incoming candidate was confused with actual participation");
  if (name == "ordinary_last_compatible") {
    Require(admission.current_target_compatible_combat_ids_in_stored_order ==
                std::vector<std::int32_t>{Memory::first_combat_id, Memory::last_combat_id} &&
            admission.contact_if_now_selected_combat_id == Memory::last_combat_id &&
            admission.selected_combat_stored_index == 1,
            "last stored compatible selection differs");
  } else if (name == "ordinary_no_compatible") {
    Require(!admission.contact_if_now_selected_combat_id &&
                admission.current_target_compatible_combat_ids_in_stored_order.empty(),
            "complete no-compatible observation acquired a future battle");
  } else {
    Require(admission.contact_if_now_selected_combat_id == Memory::first_combat_id,
            "FIRST current selected combat identity differs");
  }
  if (active) {
    Require(admission.current_attacker_public_cunit_ids_in_stored_order ==
                std::vector<std::int32_t>{Memory::subject_id, Memory::subject_id + 1},
            "actual current participation lost stored roster order");
  } else {
    const auto first_unit = name == "ordinary_last_compatible" ?
        Memory::subject_id + 3 : Memory::subject_id + 1;
    const auto expected = name == "ordinary_no_compatible" ?
        std::vector<std::int32_t>{} : std::vector<std::int32_t>{first_unit};
    Require(admission.current_attacker_public_cunit_ids_in_stored_order == expected,
            "projection appended an unjoined subject to current native roster");
  }
  Save(directory, name, admission, assigned, arrived, active, retreating);
}

} // namespace

// Only satisfy the unused owning-thread executor's link references in the
// established production serializer TU. Neither legacy reader is exercised.
namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const Bindings &, const Snapshot &, const BattleReinforcementAssignmentRequest &,
    BattleReinforcementAssignmentSnapshot &) noexcept {
  return BattleReinforcementAssignmentStatus::unavailable;
}
} // namespace xar::ck3_11906

int main(int argc, char **argv) {
  try {
    Require(argc == 2 || argc == 3, "pass FIRST output directory and optional case name");
    const std::filesystem::path directory{argv[1]};
    std::filesystem::create_directories(directory);
    constexpr std::array<std::string_view, 7> cases{
        "help_attacker_en_route", "help_defender_en_route", "ordinary_last_compatible",
        "help_retreating_arrived", "help_empty_en_route", "already_participating",
        "ordinary_no_compatible"};
    for (const auto name : cases)
      if (argc == 2 || name == argv[2]) RunCase(directory, name);
    std::cout << "FIRST new reinforcement arrival whole-wires; old matrix invocations 0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "new reinforcement arrival FIRST RED: " << error.what() << '\n';
    return 1;
  }
}

#include "ck3_12004_player_pilgrimage_execution_private_v1.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cstdlib>

namespace {
using namespace xar::ck3_12002;
using namespace xar::bridge;
#define REQUIRE(x) do { if (!(x)) { std::cerr << "failed " << __LINE__ << ": " #x "\n"; std::abort(); } } while(false)

PlayerPilgrimageExecutionQuery12004V1 Base(PilgrimageExecutionOperation12004V1 op) {
  PlayerPilgrimageExecutionQuery12004V1 q{};
  q.executable_sha256 = xar::ck3_12004::kExecutableSha256;
  q.expected_revision = 77; q.expected_snapshot.date_raw = 500;
  q.expected_snapshot.played_character_id = 100;
  q.expected_snapshot.paused = q.expected_snapshot.map_ready = true;
  q.expected_snapshot.has_played_character = q.expected_snapshot.played_character_alive = true;
  q.completed = true; q.operation = op; q.operation_status = "observed";
  q.ledger_state = ActivityPilgrimageStartStateV1::idle;
  q.planner.diagnostic.status = ActivityPlannerDiagStatusV1::observed;
  q.planner.diagnostic.value.stage = 1; q.planner.selection_observed = true;
  return q;
}
void Quote(PlayerPilgrimageExecutionQuery12004V1 &q) {
  q.cost.status = ActivityTypedFullCostStatusV1::observed;
  auto &v = q.cost.quote;
  v.observed = true; v.kind = ActivityTypedPlannerKindV1::ordinary_pilgrimage_pious;
  v.frame = {77, 500, 100, true, true, true, true};
  v.planner = 0x1100; v.owner = 0x2200; v.activity_type = 0x3300;
  v.planning_stage = 5; v.normal_refresh_sequence = 9; v.configuration_fingerprint = 0xFE1122;
  v.known_name_resource_indices = {3, 7, 2, 9};
  for (const auto index : v.known_name_resource_indices) v.named_cost_verified[index] = true;
  v.configured_cost_raw[3] = 25000000;
  v.diagnostic_aggregate_raw[3] = 123456; // Deliberately NOT configured total.
  v.final_can_start_observed = true; v.final_can_start = true;
  v.selection.observed = true; v.selection.kind = v.kind; v.selection.frame = v.frame;
  v.selection.planner = v.planner; v.selection.activity_type = v.activity_type;
  v.selection.planning_stage = 5; v.selection.native_selected_option = 0x4400;
  v.selection.native_option_id = 12;
  const auto key = kOrdinaryPilgrimagePiousContractV1.special_option_key;
  std::memcpy(v.selection.option_key.data(), key.data(), key.size());
  v.selection.option_key_size = static_cast<std::uint16_t>(key.size());
  q.planner.diagnostic.value.stage = 5;
}
void Write(const std::filesystem::path &root, std::string_view name,
           const PlayerPilgrimageExecutionQuery12004V1 &q, bool submit = false) {
  const auto step = submit ? kPilgrimagePlannerSubmit12004V1 : kPilgrimagePlannerQuery12004V1;
  const auto packet = SerializePlayerPilgrimageExecutionCommandResult12004V1(q,
      "owned-fixture:pilgrimage-execution", step);
  REQUIRE(!packet.empty());
  REQUIRE(packet.find("0x1100") == std::string::npos);
  std::ofstream file(root / (std::string(name) + ".json"), std::ios::binary);
  file << packet << '\n'; REQUIRE(file.good());
}
} // namespace

int main(int argc, char **argv) {
  REQUIRE(argc == 2);
  const std::filesystem::path root(argv[1]);
  REQUIRE(!std::filesystem::exists(root));
  REQUIRE(std::filesystem::create_directories(root));
  auto q = Base(PilgrimageExecutionOperation12004V1::read);
  Write(root, "read", q);
  q = Base(PilgrimageExecutionOperation12004V1::can_select);
  q.planner.destination_operation.can_select_observed = true;
  q.planner.destination_operation.can_select = false;
  Write(root, "can-select-false", q);
  q = Base(PilgrimageExecutionOperation12004V1::quote); Quote(q);
  Write(root, "quote-dynamic-index", q);
  q = Base(PilgrimageExecutionOperation12004V1::start); Quote(q);
  q.operation_status = "submitted_pending";
  q.start.accepted = q.start.invoked = true;
  q.start.state = q.ledger_state = ActivityPilgrimageStartStateV1::submitted_pending;
  Write(root, "start-pending", q, true);
  q.operation_status = "submission_outcome_unknown";
  q.start.state = q.ledger_state = ActivityPilgrimageStartStateV1::submission_outcome_unknown;
  Write(root, "start-unknown", q, true);
  q = Base(PilgrimageExecutionOperation12004V1::post);
  q.operation_status = "post_pending";
  q.ledger_state = ActivityPilgrimageStartStateV1::submission_outcome_unknown;
  q.post.status = ActivityPilgrimageReconcileStatusV1::pending;
  REQUIRE(SerializePlayerPilgrimageExecutionPrivate12004V1(q).find(
      "\"needs_recovery\":true") != std::string::npos);
  Write(root, "post-pending", q);
  q.operation_status = "identity_observed";
  q.ledger_state = ActivityPilgrimageStartStateV1::identity_observed;
  q.post.status = ActivityPilgrimageReconcileStatusV1::identity_observed;
  q.post.identity.activity_id = 0xFE000005;
  q.post.identity.host_character_id = 100;
  q.post.identity.terminal_flags_observed = true;
  const auto key = kOrdinaryPilgrimagePiousContractV1.activity_key;
  std::memcpy(q.post.identity.type_key.data(), key.data(), key.size());
  q.post.identity.type_key_size = static_cast<std::uint8_t>(key.size());
  Write(root, "post-full-generation", q);
  q.post.identity.type_key_size = 255;
  REQUIRE(SerializePlayerPilgrimageExecutionPrivate12004V1(q).empty());
  q = Base(PilgrimageExecutionOperation12004V1::quote);
  q.operation_status = "unavailable"; q.failure = "normal_refresh_not_observed";
  Write(root, "quote-unavailable", q);
  std::ofstream provenance(root / "PROVENANCE.json", std::ios::binary);
  provenance << "{\"producer\":\"actual production execution command-result and cost serializers\","
      "\"owned_result_dtos\":true,\"game_queried\":false,\"native_runtime_qualified\":false,"
      "\"scope\":\"eight real serializer packets; fixture-owned semantic results and envelope nonce\"}\n";
  REQUIRE(provenance.good());
  std::cout << "8 real execution serializer packets; owned DTOs only\n";
}

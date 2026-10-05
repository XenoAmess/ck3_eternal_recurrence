#include "xar_bridge/normal_exit_map_v1.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>

namespace {
using namespace xar::ck3_12003;
unsigned checks = 0;
void Check(bool value, const char *name) {
  ++checks;
  if (!value) throw std::runtime_error(name);
}
std::string Request(std::string_view action) {
  std::string value = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"native-fixture-1\",\"step\":\"normal-exit-map-v1\",\"action\":\"";
  value += action;
  value += "\",\"expected_revision\":29,\"expected_player_character_id\":16777218,\"expected_game_pid\":20264,\"expected_connection_generation\":7,\"expected_process_creation_filetime_100ns\":134356529492116987,\"request_nonce\":\"native-fixture-nonce\",\"source_inventory_sha256\":\"";
  value += std::string(64, 'a'); value += '"';
  if (action != "query_context") {
    value += ",\"expected_exit_context_signature\":\"";
    value += std::string(64, 'b'); value += '"';
  }
  value += '}'; return value;
}
void RejectUnchanged(std::string value) {
  NormalExitMapRequestV1 request{};
  request.request_id = "sentinel";
  request.action = NormalExitMapActionV1::confirm_desktop;
  request.expected_revision = 71;
  std::string reason;
  Check(!ParseNormalExitMapRequestV1(value, request, reason), "invalid request accepted");
  Check(request.request_id == "sentinel" && request.expected_revision == 71 &&
      request.action == NormalExitMapActionV1::confirm_desktop, "rejected request mutated output");
}
}

int main(int argc, char **argv) {
  using namespace xar::ck3_12003;
  try {
    if (argc == 2 && (std::string_view(argv[1]) == "--serialize-query" ||
        std::string_view(argv[1]) == "--serialize-continued-unknown")) {
      // Explicit offline serializer fixture. These values are not observations
      // of a running process and grant no native or exit acceptance credit.
      NormalExitMapObservationV1 fixture{};
      fixture.action = NormalExitMapActionV1::query_context;
      fixture.status = NormalExitMapStatusV1::context_observed;
      fixture.native_revision = 29; fixture.connection_generation = 7;
      fixture.game_pid = 20264; fixture.played_character_id = 16777218;
      fixture.process_creation_filetime_100ns = 134356529492116987;
      fixture.pump_epoch = 41;
      fixture.exact_build_verified = fixture.owner_verified = fixture.process_identity_verified = true;
      fixture.source_abi_pins_verified = fixture.stock_files_verified = true;
      fixture.loaded_source_binding_verified = fixture.frame_verified = true;
      fixture.exit_context_signature = std::string(64, 'b');
      fixture.stage_consumed = {true, false, false};
      for (auto &target : fixture.targets) target.read_complete = true;
      auto &entry = fixture.targets[1];
      entry.root_exists = entry.root_visible = entry.target_exists = entry.target_visible = true;
      entry.target_enabled = entry.unique_target = entry.dispatch_admitted = true;
      entry.target_vtable_rva = 0x01712340;
      fixture.reason = "offline_serializer_fixture_not_live";
      if (std::string_view(argv[1]) == "--serialize-continued-unknown") {
        fixture.action = NormalExitMapActionV1::continue_preparation;
        fixture.status = NormalExitMapStatusV1::dispatch_unknown_claimed;
        fixture.context_signature_verified = true;
        fixture.stage_consumed = {true, true, false};
        auto &entry_dispatch = fixture.dispatches[1];
        entry_dispatch.claim_latched = entry_dispatch.dispatch_invoked = entry_dispatch.native_handled = true;
        entry_dispatch.post_read_complete = true;
      }
      std::cout << SerializeNormalExitMapObservationV1(fixture) << '\n';
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--packet") {
      std::ifstream input(argv[2], std::ios::binary);
      const std::string packet((std::istreambuf_iterator<char>(input)), {});
      if (!input || packet.size() < 4) return 2;
      std::uint32_t length = 0;
      for (std::size_t i = 0; i < 4; ++i)
        length |= static_cast<std::uint32_t>(static_cast<unsigned char>(packet[i])) << (8 * i);
      if (length != packet.size() - 4) return 3;
      NormalExitMapRequestV1 request{}; std::string reason;
      const bool accepted = ParseNormalExitMapRequestV1(std::string_view(packet).substr(4), request, reason);
      std::cout << "{\"accepted\":" << (accepted ? "true" : "false")
          << ",\"action\":\"" << NormalExitMapActionNameV1(request.action)
          << "\",\"native_revision\":" << request.expected_revision
          << ",\"full_player_id\":" << request.expected_player_character_id
          << ",\"pid\":" << request.expected_game_pid
          << ",\"generation\":" << request.expected_connection_generation
          << ",\"creation_filetime\":" << request.expected_process_creation_filetime_100ns
          << ",\"reason\":\"" << reason << "\"}\n";
      return accepted ? 0 : 4;
    }
    if (argc != 1) return 5;
    Check(!kNormalExitMapV1CompiledEnabled, "private feature remains default OFF for contract target");
    std::array<NormalExitMapTargetV1, 3> targets{};
    for (auto &target : targets) target.read_complete = true;
    auto &entry = targets[1];
    entry.root_exists = entry.root_visible = entry.target_exists = entry.target_visible = true;
    entry.target_enabled = entry.unique_target = entry.dispatch_admitted = true;
    entry.target_vtable_rva = 0x01712340;
    for (unsigned bits = 0; bits < 8; ++bits) {
      const std::array<bool, 3> consumed{bool(bits & 1), bool(bits & 2), bool(bits & 4)};
      Check(NormalExitMapContinuePreparationAdmittedV1(consumed, targets, false) == (bits == 1),
          "continuation stage history gate");
    }
    const std::array<bool, 3> menu_only{true, false, false};
    Check(!NormalExitMapContinuePreparationAdmittedV1(menu_only, targets, true), "confirmation already visible");
    for (std::size_t i = 0; i < targets.size(); ++i) {
      auto changed = targets; changed[i].read_complete = false;
      Check(!NormalExitMapContinuePreparationAdmittedV1(menu_only, changed, false), "partial census");
    }
    for (bool NormalExitMapTargetV1::*member : {
        &NormalExitMapTargetV1::root_exists, &NormalExitMapTargetV1::root_visible,
        &NormalExitMapTargetV1::target_exists, &NormalExitMapTargetV1::target_visible,
        &NormalExitMapTargetV1::target_enabled, &NormalExitMapTargetV1::unique_target,
        &NormalExitMapTargetV1::dispatch_admitted}) {
      auto changed = targets; changed[1].*member = false;
      Check(!NormalExitMapContinuePreparationAdmittedV1(menu_only, changed, false), "unqualified fixed entry");
    }
    auto changed = targets; changed[1].target_vtable_rva = 0;
    Check(!NormalExitMapContinuePreparationAdmittedV1(menu_only, changed, false), "unbound entry vtable");
    changed = targets; changed[2].root_visible = true;
    Check(!NormalExitMapContinuePreparationAdmittedV1(menu_only, changed, false), "confirmation census inconsistent");
    NormalExitMapSessionV1 session{};
    Check(ReadNormalExitMapStageConsumptionV1(session) == std::array<bool, 3>{false, false, false}, "initial claims");
    bool expected = false;
    Check(session.claimed[0].compare_exchange_strong(expected, true), "menu CAS");
    session.queried_stage_consumed = ReadNormalExitMapStageConsumptionV1(session);
    Check(session.queried_stage_consumed == menu_only && NormalExitMapStageConsumptionMatchesQueryV1(session), "fresh claims bound");
    session.signature.clear(); session.queried_revision = 999; session.queried_generation = 10;
    Check(ReadNormalExitMapStageConsumptionV1(session) == menu_only, "query reconnect cannot clear claims");
    expected = false;
    Check(session.claimed[1].compare_exchange_strong(expected, true), "only entry CAS");
    Check(!NormalExitMapStageConsumptionMatchesQueryV1(session), "signature claim drift");
    Check(ReadNormalExitMapStageConsumptionV1(session) == std::array<bool, 3>{true, true, false}, "menu remains consumed confirm untouched");
    expected = false;
    Check(!session.claimed[0].compare_exchange_strong(expected, true), "menu replay prevented");
    expected = false;
    Check(!session.claimed[1].compare_exchange_strong(expected, true), "entry replay prevented");
    for (const auto action : {"query_context", "prepare_confirmation", "confirm_desktop", "continue_preparation"}) {
      NormalExitMapRequestV1 request{}; std::string reason;
      Check(ParseNormalExitMapRequestV1(Request(action), request, reason), "production action parser");
      Check(NormalExitMapActionNameV1(request.action) == action, "exact action roundtrip");
    }
    auto packet = Request("continue_preparation");
    auto missing = packet; const auto start = missing.find(",\"expected_exit_context_signature\""); missing.erase(start, missing.size() - start - 1);
    RejectUnchanged(missing);
    auto blank = packet; const auto signature_at = blank.find(std::string(64, 'b')); blank.erase(signature_at, 64); RejectUnchanged(blank);
    auto unknown = packet; unknown.insert(unknown.size() - 1, ",\"stage\":1"); RejectUnchanged(unknown);
    auto duplicate = packet; duplicate.insert(duplicate.size() - 1, ",\"action\":\"continue_preparation\""); RejectUnchanged(duplicate);
    RejectUnchanged(Request("retry_prepare"));
    auto zero = packet; zero.replace(zero.find("\"expected_revision\":29"), std::string("\"expected_revision\":29").size(), "\"expected_revision\":0"); RejectUnchanged(zero);
    NormalExitMapObservationV1 observed{};
    observed.action = NormalExitMapActionV1::continue_preparation;
    observed.stage_consumed = ReadNormalExitMapStageConsumptionV1(session);
    observed.orderly_exit_verified = observed.autosave_verified = true;
    const auto serialized = SerializeNormalExitMapObservationV1(observed);
    Check(serialized.find("\"stage_consumed\":[true,true,false]") != std::string::npos, "actual stage progress serialized");
    Check(serialized.find("\"action\":\"continue_preparation\"") != std::string::npos, "continuation serialized");
    Check(serialized.find("\"orderly_exit_verified\":false") != std::string::npos &&
        serialized.find("\"autosave_verified\":false") != std::string::npos, "no exit or save credit");
    std::cout << "{\"status\":\"SOURCE_L0_COMPILED_PURE_GATES_PASS\",\"checks\":" << checks
        << ",\"native_provider_invoked\":false,\"stage0_replayed\":false,\"game_or_pipe_calls\":0}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 10;
  }
}

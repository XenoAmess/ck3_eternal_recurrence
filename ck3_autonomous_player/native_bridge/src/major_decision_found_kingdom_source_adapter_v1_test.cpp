#include "xar_bridge/major_decision_found_kingdom_source_adapter_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

namespace bridge = xar::bridge;
using Access = bridge::MajorDecisionFoundKingdomSourceAccessV1;
using AdapterFailure =
    bridge::MajorDecisionFoundKingdomSourceAdapterFailureV1;
using CoreFailure = bridge::MajorDecisionFoundKingdomFailureV1;
using Cost = bridge::MajorDecisionFoundKingdomSourceCostV1;
using Database = bridge::MajorDecisionFoundKingdomSourceDatabaseLeaseV1;
using Definition = bridge::MajorDecisionFoundKingdomSourceDefinitionLeaseV1;
using Eligibility = bridge::MajorDecisionFoundKingdomSourceEligibilityV1;
using Frame = bridge::MajorDecisionFoundKingdomFrameV1;
using Player = bridge::MajorDecisionFoundKingdomSourcePlayerLeaseV1;
using Result = bridge::MajorDecisionFoundKingdomSourceResultV1;

struct Fixture {
  std::array<Frame, 2> frames{};
  std::array<Player, 2> players{};
  std::array<Database, 2> databases{};
  std::array<Definition, 2> definitions{};
  std::array<Eligibility, 2> eligibility{};
  std::array<Cost, 2> costs{};
  std::array<bool, 2> affordability{};
  std::array<bool, 2> can_take{};
  std::size_t frame_calls = 0;
  std::size_t player_calls = 0;
  std::size_t database_calls = 0;
  std::size_t definition_calls = 0;
  std::size_t eligibility_calls = 0;
  std::size_t cost_calls = 0;
  std::size_t affordability_calls = 0;
  std::size_t can_take_calls = 0;
  std::size_t fail_frame_call = 0;
  std::size_t fail_player_call = 0;
  std::size_t fail_database_call = 0;
  std::size_t fail_definition_call = 0;
  std::size_t fail_eligibility_call = 0;
  std::size_t fail_cost_call = 0;
  std::size_t fail_affordability_call = 0;
  std::size_t fail_can_take_call = 0;

  Fixture() {
    Frame frame{};
    frame.snapshot_revision = 901;
    frame.native_revision = 19'006;
    frame.proof_epoch = 44;
    frame.date_raw = 56'000'000;
    frame.played_character_id = 32'904;
    frame.application_main_thread = true;
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_alive = true;
    frame.played_character_identity_round_trip = true;
    frames.fill(frame);
    players.fill(Player{true, 0x1000, 32'904});
    databases.fill(Database{true, 0x2000, 71, 5});
    definitions.fill(Definition{
        true, true, 0x3000, 81, 6,
        bridge::kMajorDecisionFoundKingdomDecisionIdV1});
    eligibility.fill(Eligibility{true, true, true});
    costs.fill(Cost{0, 30'000'000, 50'000'000, 20'000'000});
    affordability.fill(true);
    can_take.fill(true);
  }
};

std::size_t Pass(std::size_t calls) noexcept { return calls > 1 ? 1U : 0U; }

bool CaptureFrame(void *context, Frame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.frame_calls == fixture.fail_frame_call) return false;
  output = fixture.frames[Pass(fixture.frame_calls)];
  return true;
}

bool ResolvePlayer(void *context, std::int32_t expected,
                   Player &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.player_calls;
  if (fixture.player_calls == fixture.fail_player_call || expected != 32'904) {
    return false;
  }
  output = fixture.players[Pass(fixture.player_calls)];
  return true;
}

bool ResolveDatabase(void *context, Database &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.database_calls;
  if (fixture.database_calls == fixture.fail_database_call) return false;
  output = fixture.databases[Pass(fixture.database_calls)];
  return true;
}

bool LookupDefinition(void *context, const Database &database,
                      std::string_view decision_id,
                      Definition &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.definition_calls;
  if (fixture.definition_calls == fixture.fail_definition_call ||
      decision_id != bridge::kMajorDecisionFoundKingdomDecisionIdV1) {
    return false;
  }
  const auto pass = Pass(fixture.definition_calls);
  if (database.native_address != fixture.databases[pass].native_address) {
    return false;
  }
  output = fixture.definitions[pass];
  return true;
}

bool EvaluateEligibility(void *context, const Definition &definition,
                         const Player &player,
                         Eligibility &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.eligibility_calls;
  if (fixture.eligibility_calls == fixture.fail_eligibility_call) return false;
  const auto pass = Pass(fixture.eligibility_calls);
  if (definition.native_address != fixture.definitions[pass].native_address ||
      player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.eligibility[pass];
  return true;
}

bool EvaluateCost(void *context, const Definition &definition,
                  const Player &player, Cost &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.cost_calls;
  if (fixture.cost_calls == fixture.fail_cost_call) return false;
  const auto pass = Pass(fixture.cost_calls);
  if (definition.native_address != fixture.definitions[pass].native_address ||
      player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.costs[pass];
  return true;
}

bool EvaluateAffordability(void *context, const Definition &definition,
                           const Player &player, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.affordability_calls;
  if (fixture.affordability_calls == fixture.fail_affordability_call) {
    return false;
  }
  const auto pass = Pass(fixture.affordability_calls);
  if (definition.native_address != fixture.definitions[pass].native_address ||
      player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.affordability[pass];
  return true;
}

bool EvaluateCanTake(void *context, const Definition &definition,
                     const Player &player, bool &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.can_take_calls;
  if (fixture.can_take_calls == fixture.fail_can_take_call) return false;
  const auto pass = Pass(fixture.can_take_calls);
  if (definition.native_address != fixture.definitions[pass].native_address ||
      player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.can_take[pass];
  return true;
}

Access MakeAccess(Fixture &fixture) noexcept {
  Access output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      bridge::kMajorDecisionFoundKingdomExecutableSha256V1;
  output.current_thread_id = 77;
  output.application_main_thread_id = 77;
  output.context = &fixture;
  output.capture_frame = &CaptureFrame;
  output.resolve_player = &ResolvePlayer;
  output.resolve_decision_database = &ResolveDatabase;
  output.lookup_definition = &LookupDefinition;
  output.evaluate_eligibility = &EvaluateEligibility;
  output.evaluate_cost = &EvaluateCost;
  output.evaluate_affordability = &EvaluateAffordability;
  output.evaluate_can_take = &EvaluateCanTake;
  return output;
}

void ExpectFailure(Access access, AdapterFailure expected,
                   CoreFailure core =
                       CoreFailure::source_sample_incomplete) {
  Result output{};
  output.snapshot.status =
      bridge::MajorDecisionFoundKingdomStatusV1::available;
  assert(!bridge::ObserveMajorDecisionFoundKingdomSourceV1(access, output));
  assert(output.failure == expected);
  assert(output.core_failure == core);
  assert(output.snapshot.status ==
         bridge::MajorDecisionFoundKingdomStatusV1::unavailable);
  assert(bridge::MajorDecisionFoundKingdomSourceAdapterFailureNameV1(
             expected) != "unknown");
}

void TestStableTransactionPublishesDynamicNativeValues() {
  Fixture fixture{};
  Result output{};
  assert(bridge::ObserveMajorDecisionFoundKingdomSourceV1(
      MakeAccess(fixture), output));
  assert(output.failure == AdapterFailure::none);
  assert(output.core_failure == CoreFailure::none);
  assert(output.snapshot.status ==
         bridge::MajorDecisionFoundKingdomStatusV1::available);
  assert(output.snapshot.is_shown.value);
  assert(output.snapshot.is_valid.value);
  assert(output.snapshot.is_valid_showing_failures_only.value);
  assert(output.snapshot.evaluated_cost.gold_q100000 == 0);
  assert(output.snapshot.evaluated_cost.treasury_q100000 == 30'000'000);
  assert(output.snapshot.evaluated_cost.prestige_q100000 == 50'000'000);
  assert(output.snapshot.evaluated_cost.piety_q100000 == 20'000'000);
  assert(output.snapshot.is_affordable.value);
  assert(output.snapshot.can_take.value);
  assert(output.snapshot.readiness.semantic_observation_ready);
  assert(!output.snapshot.readiness.effect_preview_ready);
  assert(!output.snapshot.readiness.action_ready);
  assert(!output.snapshot.effect_preview.executable);
  assert(fixture.frame_calls == 2);
  assert(fixture.player_calls == 2);
  assert(fixture.database_calls == 2);
  assert(fixture.definition_calls == 2);
  assert(fixture.eligibility_calls == 2);
  assert(fixture.cost_calls == 2);
  assert(fixture.affordability_calls == 2);
  assert(fixture.can_take_calls == 2);
}

void TestKnownFalseIsNotUnknown() {
  Fixture fixture{};
  fixture.eligibility.fill(Eligibility{true, false, true});
  fixture.can_take.fill(false);
  Result output{};
  assert(bridge::ObserveMajorDecisionFoundKingdomSourceV1(
      MakeAccess(fixture), output));
  assert(output.snapshot.is_valid.state ==
         bridge::MajorDecisionFieldStateV1::known);
  assert(!output.snapshot.is_valid.value);
  assert(output.snapshot.can_take.state ==
         bridge::MajorDecisionFieldStateV1::known);
  assert(!output.snapshot.can_take.value);
  assert(output.snapshot.readiness.semantic_observation_ready);
}

void TestAdmissionCallbacksThreadAndFrameGates() {
  Fixture fixture{};
  auto access = MakeAccess(fixture);
  access.admitted_executable_sha256 = "wrong";
  ExpectFailure(access, AdapterFailure::exact_build_mismatch,
                CoreFailure::exact_build_not_admitted);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.evaluate_cost = nullptr;
  ExpectFailure(access, AdapterFailure::callbacks_unavailable);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.current_thread_id = 78;
  ExpectFailure(access, AdapterFailure::application_main_thread_required,
                CoreFailure::application_main_thread_required);
  assert(fixture.frame_calls == 0);

  fixture = {};
  fixture.frames[0].paused = false;
  fixture.frames[1].paused = false;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::not_paused,
                CoreFailure::not_paused);
  assert(fixture.player_calls == 0);

  fixture = {};
  fixture.frames[0].map_ready = false;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::frame_invalid,
                CoreFailure::map_not_ready);
}

void TestDatabaseDefinitionAndPlayerResolution() {
  Fixture fixture{};
  fixture.fail_player_call = 1;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::played_character_unavailable);

  fixture = {};
  fixture.fail_database_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::decision_database_unavailable);

  fixture = {};
  fixture.fail_definition_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::decision_definition_missing);

  fixture = {};
  fixture.definitions[0].decision_id = "wrong_decision";
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::decision_definition_identity_mismatch,
                CoreFailure::decision_definition_identity_mismatch);

  fixture = {};
  ++fixture.databases[1].generation;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::decision_database_drift,
                CoreFailure::source_sample_drift);

  fixture = {};
  ++fixture.definitions[1].generation;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::decision_definition_drift,
                CoreFailure::source_sample_drift);

  fixture = {};
  ++fixture.players[1].native_address;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::played_character_drift,
                CoreFailure::played_character_identity_mismatch);
}

void TestEveryEvaluatorFailureIsTyped() {
  Fixture fixture{};
  fixture.fail_eligibility_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::eligibility_evaluation_failed);

  fixture = {};
  fixture.fail_cost_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::evaluated_cost_evaluation_failed);

  fixture = {};
  fixture.fail_affordability_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::affordability_evaluation_failed);

  fixture = {};
  fixture.fail_can_take_call = 1;
  ExpectFailure(MakeAccess(fixture),
                AdapterFailure::can_take_evaluation_failed);
}

void TestSourceAndFrameDriftFailClosed() {
  Fixture fixture{};
  ++fixture.costs[1].piety_q100000;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::source_sample_drift,
                CoreFailure::source_sample_drift);

  fixture = {};
  fixture.eligibility[1].is_valid = false;
  fixture.can_take[1] = false;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::source_sample_drift,
                CoreFailure::source_sample_drift);

  fixture = {};
  ++fixture.frames[1].proof_epoch;
  ExpectFailure(MakeAccess(fixture), AdapterFailure::frame_drift,
                CoreFailure::frame_drift);
}

void TestCoreRejectsInvalidNativeTruth() {
  Fixture fixture{};
  fixture.costs[0].gold_q100000 = -1;
  fixture.costs[1] = fixture.costs[0];
  ExpectFailure(MakeAccess(fixture), AdapterFailure::core_rejected,
                CoreFailure::evaluated_cost_invalid);

  fixture = {};
  fixture.affordability.fill(false);
  ExpectFailure(MakeAccess(fixture), AdapterFailure::core_rejected,
                CoreFailure::can_take_invariant_failed);
}

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool ContainsAll(std::string_view text,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (text.find(token) == std::string_view::npos) return false;
  }
  return true;
}

void TestMachineReadableSourceContract(const char *contract_path,
                                       const char *stable_path) {
  const auto contract = ReadAll(contract_path);
  assert(ContainsAll(
      contract,
      {"major_decision_found_kingdom_source_adapter_v1", "static-ready",
       "efaf97ae8e0b88af330d3409a59f869792022b70",
       "lookup_found_kingdom_decision_each_sample",
       "evaluate_three_eligibility_groups_each_sample",
       "evaluate_dynamic_four_resource_cost_each_sample",
       "unknown_only_permitted\": false", "no_effect_callback\": true",
       "decision_execution_permitted\": false",
       "shared_glue_required\": true", "ck3_launched\": false"}));
  const auto stable = ReadAll(stable_path);
  assert(ContainsAll(
      stable,
      {"offline-fixture", "found_kingdom_decision",
       "source_block_sha256_round_trip", "treasury\": 30000000",
       "prestige\": 50000000", "piety\": 20000000",
       "effect_preview_not_provided", "executable\": false"}));
}

void TestFailureVocabularyIsTotal() {
  constexpr std::array failures{
      AdapterFailure::none,
      AdapterFailure::exact_build_mismatch,
      AdapterFailure::callbacks_unavailable,
      AdapterFailure::application_main_thread_required,
      AdapterFailure::frame_unavailable,
      AdapterFailure::not_paused,
      AdapterFailure::frame_invalid,
      AdapterFailure::played_character_unavailable,
      AdapterFailure::played_character_drift,
      AdapterFailure::decision_database_unavailable,
      AdapterFailure::decision_database_drift,
      AdapterFailure::decision_definition_missing,
      AdapterFailure::decision_definition_identity_mismatch,
      AdapterFailure::decision_definition_drift,
      AdapterFailure::eligibility_evaluation_failed,
      AdapterFailure::evaluated_cost_evaluation_failed,
      AdapterFailure::affordability_evaluation_failed,
      AdapterFailure::can_take_evaluation_failed,
      AdapterFailure::source_sample_drift,
      AdapterFailure::frame_drift,
      AdapterFailure::core_rejected,
  };
  for (const auto failure : failures) {
    assert(bridge::MajorDecisionFoundKingdomSourceAdapterFailureNameV1(
               failure) != "unknown");
  }
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 3);
  TestStableTransactionPublishesDynamicNativeValues();
  TestKnownFalseIsNotUnknown();
  TestAdmissionCallbacksThreadAndFrameGates();
  TestDatabaseDefinitionAndPlayerResolution();
  TestEveryEvaluatorFailureIsTyped();
  TestSourceAndFrameDriftFailClosed();
  TestCoreRejectsInvalidNativeTruth();
  TestMachineReadableSourceContract(argv[1], argv[2]);
  TestFailureVocabularyIsTotal();
  std::cout <<
      "major_decision_found_kingdom_source_adapter_v1_test: 9/9 GREEN\n";
  return 0;
}

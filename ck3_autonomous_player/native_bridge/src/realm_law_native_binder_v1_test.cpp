#include "xar_bridge/realm_law_native_binder_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <string>
#include <string_view>

namespace {

namespace bridge = xar::bridge;
using AckStatus = bridge::RealmLawEnactActionAckStatusV1;
using ActionFailure = bridge::RealmLawEnactActionFailureV1;
using Candidate = bridge::RealmLawGovernanceCandidateV1;
using Container = bridge::RealmLawGovernanceSourceContainerLeaseV1;
using Group = bridge::RealmLawGovernanceSourceGroupLeaseV1;
using Player = bridge::RealmLawGovernanceSourcePlayerLeaseV1;
using Presence = bridge::RealmLawGovernancePresenceV1;
using ReceiptFailure = bridge::RealmLawEnactActionReceiptFailureV1;
using ReceiptStatus = bridge::RealmLawEnactActionReceiptStatusV1;

constexpr std::string_view kSignatureManifest =
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

bridge::RealmLawGovernanceKeyV1 Key(std::string_view value) {
  bridge::RealmLawGovernanceKeyV1 output{};
  assert(bridge::AssignRealmLawGovernanceKeyV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 Reason(std::string_view value) {
  bridge::RealmLawGovernanceReasonV1 output{};
  assert(bridge::AssignRealmLawGovernanceReasonV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 NoReason() {
  bridge::RealmLawGovernanceReasonV1 output{};
  output.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceOptionalKeyV1 OptionalKey(
    std::string_view value) {
  return {Presence::present, Key(value)};
}

bridge::RealmLawGovernanceSuccessionShapeV1 SuccessionShape(
    std::int64_t share = 50'000) {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::present;
  output.order_of_succession = Key("inheritance");
  output.title_division = OptionalKey("partition");
  output.traversal_order = OptionalKey("children");
  output.rank = OptionalKey("oldest");
  output.primary_heir_minimum_share = {Presence::present, share};
  return output;
}

Candidate Law(std::string_view key, bool active, bool can_enact,
              std::int64_t share = 50'000) {
  Candidate output{};
  output.law_key = Key(key);
  output.is_active = active;
  output.evaluation_complete = true;
  output.can_have = true;
  output.can_pass = true;
  output.can_enact = can_enact;
  output.blocked_reason = can_enact ? NoReason() : Reason("already_enacted");
  output.costs_complete = true;
  output.cost_count = 1;
  output.costs[0] = {Key("prestige"), 100};
  output.succession = SuccessionShape(share);
  return output;
}

struct Fixture {
  bridge::RealmLawNativeRuntimeProofV1 proof{};
  bridge::RealmLawGovernanceFrameV1 frame{};
  Player player{};
  Container container{};
  Group group{};
  std::array<Candidate, 2> candidates{};
  bridge::RealmLawGovernanceTitleBaselineV1 titles{};
  std::int64_t prestige = 500;
  std::size_t proof_reads = 0;
  std::size_t frame_reads = 0;
  std::size_t player_resolves = 0;
  std::size_t container_resolves = 0;
  std::size_t group_reads = 0;
  std::size_t candidate_reads = 0;
  std::size_t title_reads = 0;
  std::size_t resource_reads = 0;
  std::size_t submit_calls = 0;
  std::size_t succession_variant_after_candidate_read = 0;
  std::size_t resource_variant_after_read = 0;
  bool drift_proof_during_candidate = false;
  bool drift_connection_after_submit = false;
  bridge::RealmLawNativeSubmitDispositionV1 submit_disposition =
      bridge::RealmLawNativeSubmitDispositionV1::submitted;

  Fixture() {
    proof.exact_build_admitted = true;
    assert(bridge::AssignRealmLawNativeDigestV1(
        bridge::kRealmLawNativeBinderV1ExecutableSha256,
        proof.executable_sha256));
    proof.module_base = 0x0000000140000000ULL;
    proof.signatures_complete = true;
    assert(bridge::AssignRealmLawNativeDigestV1(
        kSignatureManifest, proof.signature_manifest_sha256));
    proof.signature_generation = 7;
    proof.connection_generation = 19;
    proof.proof_epoch = 33;
    proof.current_thread_id = 77;
    proof.application_main_thread_id = 77;
    proof.paused = true;

    frame.public_revision = 901;
    frame.native_revision = 19'006;
    frame.proof_epoch = proof.proof_epoch;
    frame.date_raw = 56'000'000;
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_id = 32'904;
    frame.played_character_alive = true;
    frame.played_character_identity_round_trip = true;

    player = {true, 0x1000, 32'904};
    container = {true, 0x2000, 71, 4, 32'904, 1};
    group.identity_round_trip = true;
    group.native_address = 0x3000;
    group.identity = 81;
    group.generation = 5;
    group.group_key = Key("succession_order_laws");
    group.active_law_key = Key("partition_succession_law");
    group.can_change_evaluated = true;
    group.can_change = true;
    group.candidate_count = 2;
    candidates[0] = Law("partition_succession_law", true, false);
    candidates[1] = Law("high_partition_succession_law", false, true);

    titles.primary_title_presence = Presence::present;
    titles.primary_title_id = 101;
    titles.primary_title_successor_count = 2;
    titles.primary_title_successor_character_ids[0] = 201;
    titles.primary_title_successor_character_ids[1] = 301;
    titles.held_title_count = 1;
    titles.held_titles[0].title_id = 101;
    titles.held_titles[0].primary = true;
    titles.held_titles[0].successor_count = 2;
    titles.held_titles[0].successor_character_ids[0] = 201;
    titles.held_titles[0].successor_character_ids[1] = 301;
  }
};

bool ReadProof(void *context,
               bridge::RealmLawNativeRuntimeProofV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.proof_reads;
  output = fixture.proof;
  return true;
}

bool CaptureFrame(void *context,
                  bridge::RealmLawGovernanceFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_reads;
  output = fixture.frame;
  return true;
}

bool ResolvePlayer(void *context, std::int32_t expected,
                   Player &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.player_resolves;
  if (expected != fixture.player.character_id) return false;
  output = fixture.player;
  return true;
}

bool ResolveContainer(void *context, const Player &player,
                      Container &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.container_resolves;
  if (player.native_address != fixture.player.native_address) return false;
  output = fixture.container;
  return true;
}

bool ReadGroup(void *context, const Player &player,
               const Container &container, std::size_t index,
               Group &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.group_reads;
  if (index != 0 || player.native_address != fixture.player.native_address ||
      container.native_address != fixture.container.native_address) {
    return false;
  }
  output = fixture.group;
  return true;
}

bool ReadCandidate(void *context, const Player &player,
                   const Container &container, const Group &group,
                   std::size_t index, Candidate &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.candidate_reads;
  if (index >= fixture.candidates.size() ||
      player.native_address != fixture.player.native_address ||
      container.native_address != fixture.container.native_address ||
      group.identity != fixture.group.identity) {
    return false;
  }
  output = fixture.candidates[index];
  if (index == 1 &&
      fixture.succession_variant_after_candidate_read != 0 &&
      fixture.candidate_reads >=
          fixture.succession_variant_after_candidate_read) {
    ++output.succession.primary_heir_minimum_share.value_raw;
  }
  if (fixture.drift_proof_during_candidate) {
    fixture.drift_proof_during_candidate = false;
    ++fixture.proof.proof_epoch;
  }
  return true;
}

bool ReadTitles(void *context, const Player &player,
                bridge::RealmLawGovernanceTitleBaselineV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.title_reads;
  if (player.native_address != fixture.player.native_address) return false;
  output = fixture.titles;
  return true;
}

bool ReadResources(void *context,
                   const bridge::RealmLawGovernanceSnapshotV1 &snapshot,
                   bridge::RealmLawNativeResourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.resource_reads;
  output = {};
  output.complete = true;
  output.public_revision = snapshot.public_revision;
  output.native_revision = snapshot.native_revision;
  output.connection_generation = fixture.proof.connection_generation;
  output.proof_epoch = snapshot.proof_epoch;
  output.date_raw = snapshot.date_raw;
  output.player_character_id = snapshot.played_character_id;
  output.resource_count = 1;
  const bool variant = fixture.resource_variant_after_read != 0 &&
      fixture.resource_reads >= fixture.resource_variant_after_read;
  output.resources[0] = {Key("prestige"),
                         fixture.prestige - (variant ? 1 : 0)};
  return true;
}

bridge::RealmLawNativeSubmitDispositionV1 Submit(
    void *context,
    const bridge::RealmLawEnactSubmissionV1 &) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submit_calls;
  if (fixture.drift_connection_after_submit) {
    ++fixture.proof.connection_generation;
  }
  return fixture.submit_disposition;
}

bridge::RealmLawNativeBinderOperationsV1 Operations() {
  return {&ReadProof,       &CaptureFrame, &ResolvePlayer,
          &ResolveContainer, &ReadGroup,    &ReadCandidate,
          &ReadTitles,      &ReadResources, &Submit};
}

bridge::RealmLawNativeBinderEnvironmentV1 Environment(Fixture &fixture) {
  bridge::RealmLawNativeBinderEnvironmentV1 output{};
  output.binding_enabled = true;
  output.offline_fixture = true;
  output.module_base = fixture.proof.module_base;
  output.admitted_executable_sha256 =
      bridge::kRealmLawNativeBinderV1ExecutableSha256;
  output.expected_signature_manifest_sha256 = kSignatureManifest;
  output.native_context = &fixture;
  output.operations = Operations();
  return output;
}

std::unique_ptr<bridge::RealmLawNativeBinderStateV1> Bind(Fixture &fixture) {
  auto state = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  assert(bridge::BindRealmLawNativeV1(Environment(fixture), *state));
  return state;
}

bridge::RealmLawEnactActionRequestV1 Request() {
  bridge::RealmLawEnactActionRequestV1 output{};
  output.request_id = "law5-test-1";
  output.group_key = Key("succession_order_laws");
  output.law_key = Key("high_partition_succession_law");
  output.expected_public_revision = 901;
  output.expected_native_revision = 19'006;
  output.expected_proof_epoch = 33;
  output.expected_date_raw = 56'000'000;
  output.expected_player_character_id = 32'904;
  output.budget_count = 1;
  output.budgets[0] = {Key("prestige"), 100};
  return output;
}

bridge::RealmLawEnactActionAckV1 ExecutePending(
    Fixture &fixture, bridge::RealmLawNativeBinderStateV1 &state) {
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             state, Request(), ack) ==
         AckStatus::submitted_verification_pending);
  assert(ack.verification_pending);
  assert(ack.failure == ActionFailure::none);
  assert(fixture.submit_calls == 1);
  return ack;
}

void AdvanceToEnacted(Fixture &fixture, bool charge_resource = true) {
  ++fixture.frame.public_revision;
  ++fixture.frame.native_revision;
  ++fixture.proof.proof_epoch;
  fixture.frame.proof_epoch = fixture.proof.proof_epoch;
  fixture.group.active_law_key = Key("high_partition_succession_law");
  fixture.candidates[0] = Law("partition_succession_law", false, true);
  fixture.candidates[1] = Law("high_partition_succession_law", true, false);
  if (charge_resource) fixture.prestige = 400;
}

void AdvanceWithoutEnact(Fixture &fixture) {
  ++fixture.frame.public_revision;
  ++fixture.frame.native_revision;
  ++fixture.proof.proof_epoch;
  fixture.frame.proof_epoch = fixture.proof.proof_epoch;
}

void TestExactBuildSignatureAndCompleteTableBinding() {
  Fixture fixture{};
  auto state = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  assert(bridge::BindRealmLawNativeV1(Environment(fixture), *state));
  assert(state->attached);
  assert(state->connection_generation == 19);
  assert(state->signature_generation == 7);
  assert(bridge::kRealmLawNativeBinderV1GameVersion == "1.19.0.6");
  assert(!bridge::kRealmLawNativeBinderV1HasFrozenNativeOffsets);
  const auto source = bridge::MakeRealmLawNativeSourceAccessV1(*state);
  const auto action = bridge::MakeRealmLawNativeActionAccessV1(*state);
  assert(source.capture_frame != nullptr && source.read_candidate != nullptr);
  assert(action.capture_observation != nullptr && action.submit != nullptr);

  Fixture wrong_build{};
  auto environment = Environment(wrong_build);
  environment.admitted_executable_sha256 = "wrong";
  auto rejected = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  assert(!bridge::BindRealmLawNativeV1(environment, *rejected));

  Fixture wrong_signature{};
  environment = Environment(wrong_signature);
  environment.expected_signature_manifest_sha256 =
      "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB";
  rejected = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  assert(!bridge::BindRealmLawNativeV1(environment, *rejected));

  Fixture incomplete{};
  environment = Environment(incomplete);
  environment.operations.submit_enact = nullptr;
  rejected = std::make_unique<bridge::RealmLawNativeBinderStateV1>();
  assert(!bridge::BindRealmLawNativeV1(environment, *rejected));
}

void TestBoundLaw3SourcePublishesOnlyStableValues() {
  Fixture fixture{};
  auto state = Bind(fixture);
  auto result = std::make_unique<bridge::RealmLawGovernanceSourceResultV1>();
  assert(bridge::ObserveRealmLawGovernanceSourceV1(
      bridge::MakeRealmLawNativeSourceAccessV1(*state), *result));
  assert(result->snapshot.status ==
         bridge::RealmLawGovernanceSnapshotV1Status::available);
  assert(result->snapshot.groups[0].active_law_key ==
         Key("partition_succession_law"));
  assert(result->snapshot.groups[0].candidates[0].law_key ==
         Key("high_partition_succession_law"));
  assert(result->snapshot.groups[0].candidates[0].can_enact);
  assert(fixture.frame_reads == 2);
  assert(fixture.player_resolves == 2);
  assert(fixture.container_resolves == 2);
  assert(fixture.candidate_reads == 4);
  assert(!state->source_transaction_open);
}

void TestBoundLaw4ActionSubmitsOnceAndKeepsAckPending() {
  Fixture fixture{};
  auto state = Bind(fixture);
  const auto ack = ExecutePending(fixture, *state);
  assert(ack.requested_law_key == Key("high_partition_succession_law"));
  assert(ack.charge_count == 1);
  assert(ack.charges[0].pre_balance_raw == 500);
  assert(state->submit_pending);
  assert(state->action_capture_serial == 2);
  assert(fixture.resource_reads == 3);
  assert(fixture.submit_calls == 1);
}

void TestSignatureGenerationAndProofDriftFailClosed() {
  Fixture signature{};
  auto state = Bind(signature);
  signature.proof.signature_manifest_sha256[0] = 'B';
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, Request(), ack) == AckStatus::rejected_before_submit);
  assert(ack.failure == ActionFailure::observation_unavailable);
  assert(state->integrity_failed);
  assert(signature.submit_calls == 0);

  Fixture generation{};
  state = Bind(generation);
  ++generation.proof.connection_generation;
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, Request(), ack) == AckStatus::rejected_before_submit);
  assert(state->integrity_failed);
  assert(generation.submit_calls == 0);

  Fixture proof{};
  state = Bind(proof);
  proof.drift_proof_during_candidate = true;
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, Request(), ack) == AckStatus::rejected_before_submit);
  assert(state->integrity_failed);
  assert(proof.submit_calls == 0);
}

void TestResourceAndSuccessionDriftNeverReachSubmit() {
  Fixture resource{};
  resource.resource_variant_after_read = 2;
  auto state = Bind(resource);
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, Request(), ack) == AckStatus::rejected_before_submit);
  assert(ack.failure == ActionFailure::state_changed_before_submit);
  assert(resource.submit_calls == 0);

  Fixture succession{};
  succession.succession_variant_after_candidate_read = 5;
  state = Bind(succession);
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, Request(), ack) == AckStatus::rejected_before_submit);
  assert(ack.failure == ActionFailure::state_changed_before_submit);
  assert(succession.submit_calls == 0);
}

void TestReceiptDistinguishesEnactedRejectedAndFailed() {
  Fixture enacted{};
  auto state = Bind(enacted);
  const auto ack = ExecutePending(enacted, *state);
  AdvanceToEnacted(enacted);
  bridge::RealmLawEnactActionReceiptV1 receipt{};
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, ack, receipt) == ReceiptStatus::enacted);
  assert(receipt.effective_law_verified && receipt.resources_verified &&
         receipt.succession_verified);
  assert(receipt.charges[0].post_balance_raw == 400);
  assert(!state->submit_pending);

  Fixture rejected{};
  state = Bind(rejected);
  auto bad_request = Request();
  bad_request.budget_count = 0;
  bridge::RealmLawEnactActionAckV1 rejected_ack{};
  assert(bridge::ExecuteBoundRealmLawNativeEnactV1(
             *state, bad_request, rejected_ack) ==
         AckStatus::rejected_before_submit);
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, rejected_ack, receipt) == ReceiptStatus::rejected);

  Fixture ineffective{};
  state = Bind(ineffective);
  const auto ineffective_ack = ExecutePending(ineffective, *state);
  AdvanceWithoutEnact(ineffective);
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, ineffective_ack, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::effective_law_not_enacted);

  Fixture resource{};
  state = Bind(resource);
  const auto resource_ack = ExecutePending(resource, *state);
  AdvanceToEnacted(resource, false);
  resource.prestige = 401;
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, resource_ack, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::resource_recheck_failed);

  Fixture succession{};
  state = Bind(succession);
  const auto succession_ack = ExecutePending(succession, *state);
  AdvanceToEnacted(succession);
  succession.candidates[1] =
      Law("high_partition_succession_law", true, false, 50'001);
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, succession_ack, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::succession_shape_changed);
}

void TestUnknownOrPostSubmitProofDriftCannotBecomeSuccess() {
  Fixture unknown{};
  unknown.submit_disposition =
      bridge::RealmLawNativeSubmitDispositionV1::submitted_outcome_unknown;
  auto state = Bind(unknown);
  const auto unknown_ack = ExecutePending(unknown, *state);
  assert(unknown_ack.status == AckStatus::submitted_verification_pending);
  assert(unknown.submit_calls == 1);

  Fixture drift{};
  drift.drift_connection_after_submit = true;
  state = Bind(drift);
  const auto drift_ack = ExecutePending(drift, *state);
  assert(drift_ack.status == AckStatus::submitted_verification_pending);
  assert(state->post_submit_integrity_failed);
  assert(state->integrity_failed);
  bridge::RealmLawEnactActionReceiptV1 receipt{};
  assert(bridge::VerifyBoundRealmLawNativeReceiptV1(
             *state, drift_ack, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::post_observation_unavailable);
  assert(drift.submit_calls == 1);
}

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void TestEvidenceDocumentKeepsUnknownOffsetsUnknown(const char *path) {
  const auto text = ReadAll(path);
  for (const auto token :
       {"static-ready private binder", "defines no",
        "RVA, offset, byte signature", "runtime signature-manifest SHA-256",
        "submitted_outcome_unknown", "verification_pending",
        "not `fixture-live` or `production-live primitive`"}) {
    assert(text.find(token) != std::string::npos);
  }
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  static_assert(kSignatureManifest.size() == 64);
  TestExactBuildSignatureAndCompleteTableBinding();
  TestBoundLaw3SourcePublishesOnlyStableValues();
  TestBoundLaw4ActionSubmitsOnceAndKeepsAckPending();
  TestSignatureGenerationAndProofDriftFailClosed();
  TestResourceAndSuccessionDriftNeverReachSubmit();
  TestReceiptDistinguishesEnactedRejectedAndFailed();
  TestUnknownOrPostSubmitProofDriftCannotBecomeSuccess();
  TestEvidenceDocumentKeepsUnknownOffsetsUnknown(argv[1]);
  std::cout << "realm_law_native_binder_v1_test: 8/8 GREEN\n";
  return 0;
}

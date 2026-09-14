#include "xar_bridge/faction_gift_mitigation_action_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using xar::ck3_11906::ExecuteFactionGiftMitigationActionV1;
using xar::ck3_11906::FactionGiftMitigationActionAccessV1;
using xar::ck3_11906::FactionGiftMitigationNativeEnvironmentV1;
using xar::ck3_11906::SerializeFactionGiftMitigationAckV1;
using xar::ck3_11906::SerializeFactionGiftMitigationReceiptV1;
using xar::ck3_11906::VerifyFactionGiftMitigationReceiptV1;
using xar::game::FactionGiftMembershipRoleV1;
using xar::game::FactionGiftMitigationAckStatusV1;
using xar::game::FactionGiftMitigationAckV1;
using xar::game::FactionGiftMitigationFailureClassV1;
using xar::game::FactionGiftMitigationObservationV1;
using xar::game::FactionGiftMitigationReceiptStatusV1;
using xar::game::FactionGiftMitigationReceiptV1;
using xar::game::FactionGiftMitigationRequestV1;

constexpr std::uint32_t kPlayerId = 0x81000011U;
constexpr std::uint32_t kFactionId = 0xA1000022U;
constexpr std::uint32_t kRecipientId = 0xC1000033U;
constexpr std::uint32_t kOtherMemberId = 0x41000044U;
constexpr std::uint64_t kGiftHash = 0xE313B9C7D54A0211ULL;
constexpr std::uint32_t kScale = 100000U;
constexpr std::int64_t kGoldBefore = 500LL * kScale;
constexpr std::int64_t kGiftCost = 50LL * kScale;
constexpr std::int64_t kReserve = 450LL * kScale;

void Check(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

FactionGiftMitigationObservationV1 GoodObservation() {
  FactionGiftMitigationObservationV1 value{};
  value.available = true;
  value.paused = true;
  value.snapshot_revision = 700;
  value.native_snapshot_revision = 1700;
  value.observed_date_raw = 90234;
  value.player_resources_query_complete = true;
  value.player_character_id = kPlayerId;
  value.player_gold_raw = kGoldBefore;
  value.player_gold_scale = kScale;
  value.source_faction_requery_complete = true;
  value.queried_source_faction_id = kFactionId;
  value.source_faction_present = true;
  value.source_faction_target_character_id = kPlayerId;
  value.source_faction_targeting_player = true;
  value.source_faction_at_war = false;
  value.source_faction_leader_character_id = 0xB1000055U;
  value.source_faction_member_character_ids = {kOtherMemberId, kRecipientId};
  value.source_faction_metrics_available = true;
  value.source_faction_power_raw = 62000;
  value.source_faction_discontent_raw = 78000;
  value.source_faction_metric_scale = kScale;
  value.recipient_identity_resolved = true;
  value.recipient_character_id = kRecipientId;
  value.recipient_alive = true;
  value.recipient_is_ai = true;
  value.recipient_is_direct_landed_vassal = true;
  value.recipient_opinion_query_complete = true;
  value.recipient_opinion_of_player = -35;
  value.gift_opinion_present = false;
  value.gift_preview.available = true;
  value.gift_preview.definition_key = "gift_interaction";
  value.gift_preview.definition_stable_hash = kGiftHash;
  value.gift_preview.interaction_legal = true;
  value.gift_preview.auto_accept = true;
  value.gift_preview.gold_cost_raw = kGiftCost;
  value.gift_preview.gold_scale = kScale;
  value.gift_preview.opinion_delta = 40;
  return value;
}

FactionGiftMitigationRequestV1 GoodRequest() {
  FactionGiftMitigationRequestV1 value{};
  value.request_id = "g2-m4-faction10-attempt-1";
  value.idempotency_key = "faction10:700:a1000022:c1000033";
  value.expected_revision = 700;
  value.expected_native_revision = 1700;
  value.expected_date_raw = 90234;
  value.player_character_id = kPlayerId;
  value.source_faction_id = kFactionId;
  value.recipient_character_id = kRecipientId;
  value.membership_role = FactionGiftMembershipRoleV1::character_member;
  value.expected_definition_key = "gift_interaction";
  value.expected_definition_stable_hash = kGiftHash;
  value.expected_gold_cost_raw = kGiftCost;
  value.expected_gold_scale = kScale;
  value.expected_opinion_delta = 40;
  value.minimum_gold_reserve_raw = kReserve;
  value.minimum_gold_reserve_scale = kScale;
  return value;
}

FactionGiftMitigationObservationV1 GoodPostObservation() {
  auto value = GoodObservation();
  value.snapshot_revision += 1;
  value.native_snapshot_revision += 1;
  value.player_gold_raw -= kGiftCost;
  value.recipient_opinion_of_player += 40;
  value.gift_opinion_present = true;
  value.gift_opinion_modifier_value = 40;
  value.gift_preview = {};
  return value;
}

struct Fixture {
  std::vector<FactionGiftMitigationObservationV1> observations{
      GoodObservation(), GoodObservation()};
  std::size_t capture_index = 0;
  bool capture_result = true;
  bool validator_call_result = true;
  bool native_valid = true;
  std::string native_reason;
  bool claim_result = true;
  bool submit_result = true;
  int validate_calls = 0;
  int claim_calls = 0;
  int submit_calls = 0;
  std::uint32_t submitted_player_id = 0;
  std::uint32_t submitted_recipient_id = 0;
  std::uint64_t submitted_definition_hash = 0;
  std::string claimed_key;

  static bool Capture(void *context,
                      FactionGiftMitigationObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    if (!self.capture_result || self.observations.empty()) return false;
    const auto index = std::min(self.capture_index,
                                self.observations.size() - 1);
    output = self.observations[index];
    ++self.capture_index;
    return true;
  }

  static bool Validate(void *context, std::uint32_t player_character_id,
                       std::uint32_t recipient_character_id,
                       std::string_view definition_key, bool &valid,
                       std::string &native_reason_key) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.validate_calls;
    if (player_character_id != kPlayerId ||
        recipient_character_id != kRecipientId ||
        definition_key != "gift_interaction") {
      return false;
    }
    valid = self.native_valid;
    native_reason_key = self.native_reason;
    return self.validator_call_result;
  }

  static bool Claim(void *context,
                    std::string_view idempotency_key) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.claim_calls;
    self.claimed_key.assign(idempotency_key);
    return self.claim_result;
  }

  static bool Submit(void *context, std::uint32_t player_character_id,
                     std::uint32_t recipient_character_id,
                     std::uint64_t definition_stable_hash) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.submit_calls;
    self.submitted_player_id = player_character_id;
    self.submitted_recipient_id = recipient_character_id;
    self.submitted_definition_hash = definition_stable_hash;
    return self.submit_result;
  }

  FactionGiftMitigationActionAccessV1 Access() {
    return {this, &Capture, &Validate, &Claim, &Submit};
  }
};

FactionGiftMitigationNativeEnvironmentV1 FixtureEnvironment() {
  FactionGiftMitigationNativeEnvironmentV1 value{};
  value.exact_build_admitted = true;
  value.offline_fixture_command = true;
  return value;
}

FactionGiftMitigationAckV1 SubmitGood(Fixture &fixture) {
  FactionGiftMitigationAckV1 ack{};
  const auto status = ExecuteFactionGiftMitigationActionV1(
      FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
  Check(status ==
            FactionGiftMitigationAckStatusV1::submitted_verification_pending,
        "valid action must submit for verification");
  return ack;
}

void CheckRejected(const Fixture &fixture,
                   const FactionGiftMitigationAckV1 &ack,
                   FactionGiftMitigationFailureClassV1 failure_class,
                   std::string_view reason) {
  Check(ack.status ==
            FactionGiftMitigationAckStatusV1::rejected_before_submit,
        "expected pre-submit rejection");
  Check(!ack.verification_pending, "rejection cannot be pending");
  Check(ack.failure_class == failure_class, "wrong failure class");
  Check(ack.rejection_reason == reason, "wrong rejection reason");
  Check(fixture.submit_calls == 0, "rejection must make zero submissions");
}

void TestSubmitAckIsPendingAndPreservesFullIds() {
  Fixture fixture;
  const auto request = GoodRequest();
  FactionGiftMitigationAckV1 ack{};
  const auto status = ExecuteFactionGiftMitigationActionV1(
      FixtureEnvironment(), fixture.Access(), request, ack);
  Check(status ==
            FactionGiftMitigationAckStatusV1::submitted_verification_pending,
        "expected pending acknowledgement");
  Check(ack.verification_pending, "ack must require verification");
  Check(fixture.capture_index == 2, "submit needs two bound captures");
  Check(fixture.validate_calls == 1, "native validator must run once");
  Check(fixture.claim_calls == 1, "idempotency must be claimed once");
  Check(fixture.submit_calls == 1, "exactly one submit is allowed");
  Check(fixture.submitted_player_id == kPlayerId,
        "full-generation player id was truncated");
  Check(fixture.submitted_recipient_id == kRecipientId,
        "full-generation recipient id was truncated");
  Check(fixture.submitted_definition_hash == kGiftHash,
        "definition hash changed at submit");
  Check(fixture.claimed_key == request.idempotency_key,
        "wrong idempotency key claimed");
  Check(ack.source_faction_id == kFactionId,
        "full-generation faction id was truncated");
  Check(ack.pre_player_gold_raw == kGoldBefore,
        "pre-submit gold was not bound");

  const auto json = SerializeFactionGiftMitigationAckV1(ack);
  Check(json.find("submitted_verification_pending") != std::string::npos,
        "ack status missing");
  Check(json.find(std::to_string(kRecipientId)) != std::string::npos,
        "serialized full-generation id missing");
  Check(json.find("mitigation_applied") == std::string::npos,
        "ack must not serialize success");
  Check(json.find("postcondition_verified") == std::string::npos,
        "ack must not serialize a postcondition verdict");
}

void TestLeaderAndMemberMustBeRealBoundRowIdentities() {
  {
    Fixture fixture;
    fixture.observations[0].source_faction_leader_character_id = kRecipientId;
    fixture.observations[1] = fixture.observations[0];
    auto request = GoodRequest();
    request.membership_role = FactionGiftMembershipRoleV1::leader;
    FactionGiftMitigationAckV1 ack{};
    const auto status = ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), request, ack);
    Check(status ==
              FactionGiftMitigationAckStatusV1::submitted_verification_pending,
          "real row leader must be accepted");
  }
  {
    Fixture fixture;
    auto request = GoodRequest();
    request.recipient_character_id &= 0x00FFFFFFU;
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), request, ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::recipient_binding,
                  "recipient_not_a_real_eligible_row_identity");
  }
  {
    Fixture fixture;
    fixture.observations[0].source_faction_member_character_ids = {
        kOtherMemberId, kOtherMemberId};
    fixture.observations[1] = fixture.observations[0];
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::faction_binding,
                  "not_a_bound_peacetime_targeting_faction");
  }
}

void TestBudgetPreviewAndDriftFailBeforeSubmit() {
  {
    Fixture fixture;
    fixture.observations[0].player_gold_raw -= 1;
    fixture.observations[1] = fixture.observations[0];
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::budget_gate,
                  "minimum_gold_reserve_not_satisfied");
  }
  {
    Fixture fixture;
    fixture.observations[0].gift_preview.interaction_legal = false;
    fixture.observations[1] = fixture.observations[0];
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::gift_preview_legality,
                  "gift_preview_not_exact_or_legal");
  }
  {
    Fixture fixture;
    fixture.observations[0].gift_opinion_present = true;
    fixture.observations[1] = fixture.observations[0];
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::recipient_binding,
                  "recipient_not_a_real_eligible_row_identity");
  }
  {
    Fixture fixture;
    fixture.observations[1].player_gold_raw -= 1;
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::snapshot_binding,
                  "state_changed_before_submit");
    Check(fixture.claim_calls == 0,
          "drift rejection must precede idempotency claim");
  }
}

void TestNativeGateAndSingleShotClaim() {
  {
    Fixture fixture;
    FactionGiftMitigationAckV1 ack{};
    FactionGiftMitigationNativeEnvironmentV1 environment{};
    environment.exact_build_admitted = true;
    ExecuteFactionGiftMitigationActionV1(
        environment, fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::native_command_dispatch,
                  "native_command_abi_not_certified");
  }
  {
    Fixture fixture;
    fixture.native_valid = false;
    fixture.native_reason = "interaction_blocked";
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::gift_preview_legality,
                  "native_validation_failed");
    Check(ack.native_reason_key == "interaction_blocked",
          "native rejection reason was not preserved");
  }
  {
    Fixture fixture;
    fixture.claim_result = false;
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationActionV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    CheckRejected(fixture, ack,
                  FactionGiftMitigationFailureClassV1::idempotency,
                  "idempotency_key_already_claimed");
    Check(fixture.claim_calls == 1, "claim must be attempted exactly once");
  }
}

void TestReceiptDistinguishesMitigatedAndLeft() {
  Fixture fixture;
  const auto ack = SubmitGood(fixture);
  {
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationReceiptV1(
        ack, GoodPostObservation(), receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::mitigated,
          "verified gift with member retained must be mitigated");
    Check(receipt.mitigation_applied && receipt.postcondition_verified,
          "mitigated receipt needs exact postcondition proof");
    Check(!receipt.threat_resolved && !receipt.recipient_left,
          "retained targeting row must not claim threat resolution");
    const auto json = SerializeFactionGiftMitigationReceiptV1(receipt);
    Check(json.find("\"status\":\"mitigated\"") != std::string::npos,
          "mitigated receipt status missing");
  }
  {
    auto post = GoodPostObservation();
    post.source_faction_member_character_ids.erase(
        std::remove(post.source_faction_member_character_ids.begin(),
                    post.source_faction_member_character_ids.end(),
                    kRecipientId),
        post.source_faction_member_character_ids.end());
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status =
        VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left,
          "recipient exit must be distinguished as left");
    Check(receipt.mitigation_applied && receipt.recipient_left &&
              receipt.threat_resolved,
          "left receipt flags are incomplete");
  }
  {
    auto post = GoodPostObservation();
    post.source_faction_present = false;
    post.source_faction_metrics_available = false;
    post.source_faction_leader_character_id.reset();
    post.source_faction_member_character_ids.clear();
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status =
        VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left,
          "dissolved faction must be distinguished as left");
    Check(receipt.faction_dissolved && receipt.threat_resolved,
          "dissolution flags are incomplete");
  }
}

void TestReceiptRequiresFactionOpinionAndResourceRequeries() {
  Fixture fixture;
  const auto ack = SubmitGood(fixture);
  {
    auto post = GoodPostObservation();
    post.snapshot_revision = ack.pre_snapshot_revision;
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status =
        VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::failed,
          "ACK without a new snapshot must fail");
    Check(!receipt.mitigation_applied,
          "ACK alone must never count as mitigation");
  }
  {
    auto post = GoodPostObservation();
    post.player_gold_raw += 1;
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "gift_gold_delta_not_observed",
          "wrong resource delta must fail");
  }
  {
    auto post = GoodPostObservation();
    post.gift_opinion_present = false;
    post.gift_opinion_modifier_value.reset();
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "recipient_gift_opinion_not_observed",
          "money-only observation must fail");
  }
  {
    auto post = GoodPostObservation();
    post.source_faction_requery_complete = false;
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "same_faction_requery_failed",
          "missing same-faction requery must fail");
  }
  {
    auto post = GoodPostObservation();
    post.queried_source_faction_id ^= 0x01000000U;
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationReceiptV1(ack, post, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "same_faction_requery_failed",
          "generation-changed faction identity must fail");
  }
}

} // namespace

int main() {
  struct TestCase {
    const char *name;
    void (*run)();
  };
  const TestCase tests[] = {
      {"submit_ack_pending_full_ids",
       &TestSubmitAckIsPendingAndPreservesFullIds},
      {"leader_member_bound_rows",
       &TestLeaderAndMemberMustBeRealBoundRowIdentities},
      {"budget_preview_drift", &TestBudgetPreviewAndDriftFailBeforeSubmit},
      {"native_gate_single_shot", &TestNativeGateAndSingleShotClaim},
      {"receipt_mitigated_left", &TestReceiptDistinguishesMitigatedAndLeft},
      {"receipt_requires_requeries",
       &TestReceiptRequiresFactionOpinionAndResourceRequeries},
  };

  int failures = 0;
  for (const auto &test : tests) {
    try {
      test.run();
      std::cout << "PASS " << test.name << '\n';
    } catch (const std::exception &error) {
      ++failures;
      std::cerr << "FAIL " << test.name << ": " << error.what() << '\n';
    }
  }
  std::cout << (sizeof(tests) / sizeof(tests[0]) -
                static_cast<std::size_t>(failures))
            << '/' << (sizeof(tests) / sizeof(tests[0])) << " passed\n";
  return failures == 0 ? 0 : 1;
}

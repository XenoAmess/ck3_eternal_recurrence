#include "xar_bridge/faction_gift_mitigation_source_action_adapter_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using xar::bridge::FactionTargetingRowProbeResultV1;
using xar::bridge::FactionTargetingRowProbeTerminalV1;
using xar::ck3_11906::CaptureFactionGiftMitigationObservationFromSourcesV1;
using xar::ck3_11906::ExecuteFactionGiftMitigationSourceActionAdapterV1;
using xar::ck3_11906::FactionGiftMitigationNativeEnvironmentV1;
using xar::ck3_11906::FactionGiftMitigationSourceActionAccessV1;
using xar::ck3_11906::FactionGiftMitigationSourceDetailsV1;
using xar::ck3_11906::FactionGiftMitigationSourceFrameV1;
using xar::ck3_11906::SerializeFactionGiftMitigationAckV1;
using xar::ck3_11906::VerifyFactionGiftMitigationSourceActionReceiptV1;
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
constexpr std::uint32_t kLeaderId = 0xB1000055U;
constexpr std::uint64_t kDefinitionHash = 0xE313B9C7D54A0211ULL;
constexpr std::uint32_t kScale = 100000U;
constexpr std::int64_t kGoldBefore = 500LL * kScale;
constexpr std::int64_t kGiftCost = 50LL * kScale;

void Check(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

struct SourceFrameFixture {
  FactionTargetingRowProbeResultV1 rows;
  FactionGiftMitigationSourceDetailsV1 details;
};

SourceFrameFixture GoodSourceFrame() {
  SourceFrameFixture frame{};
  frame.rows.terminal = FactionTargetingRowProbeTerminalV1::ready;
  frame.rows.published_generation = 8;
  frame.rows.required_binding.paused = true;
  frame.rows.required_binding.proof_epoch = 88;
  frame.rows.required_binding.snapshot_revision = 700;
  frame.rows.required_binding.date_raw = 90234;
  frame.rows.required_binding.player_character_id = kPlayerId;
  frame.rows.observed_binding = frame.rows.required_binding;
  frame.rows.faction_count = 1;
  auto &row = frame.rows.factions[0];
  row.faction_id = kFactionId;
  row.target_character_id = kPlayerId;
  row.leader_present = true;
  row.leader_character_id = kLeaderId;
  row.leader_present_in_character_members = false;
  row.character_member_count = 2;
  row.character_member_ids[0] = kOtherMemberId;
  row.character_member_ids[1] = kRecipientId;

  frame.details.available = true;
  frame.details.frame.paused = true;
  frame.details.frame.row_published_generation = 8;
  frame.details.frame.proof_epoch = 88;
  frame.details.frame.snapshot_revision = 700;
  frame.details.frame.native_snapshot_revision = 1700;
  frame.details.frame.date_raw = 90234;
  frame.details.frame.player_character_id = kPlayerId;
  frame.details.player_resources_query_complete = true;
  frame.details.player_gold_raw = kGoldBefore;
  frame.details.player_gold_scale = kScale;
  frame.details.source_faction_query_complete = true;
  frame.details.queried_source_faction_id = kFactionId;
  frame.details.source_faction_present = true;
  frame.details.source_faction_at_war = false;
  frame.details.source_faction_metrics_available = true;
  frame.details.source_faction_power_raw = 62000;
  frame.details.source_faction_discontent_raw = 78000;
  frame.details.source_faction_metric_scale = kScale;
  frame.details.recipient_identity_resolved = true;
  frame.details.recipient_character_id = kRecipientId;
  frame.details.recipient_alive = true;
  frame.details.recipient_is_ai = true;
  frame.details.recipient_is_direct_landed_vassal = true;
  frame.details.recipient_opinion_query_complete = true;
  frame.details.recipient_opinion_of_player = -35;
  frame.details.gift_opinion_present = false;
  frame.details.gift_preview.available = true;
  frame.details.gift_preview.definition_key = "gift_interaction";
  frame.details.gift_preview.definition_stable_hash = kDefinitionHash;
  frame.details.gift_preview.interaction_legal = true;
  frame.details.gift_preview.auto_accept = true;
  frame.details.gift_preview.gold_cost_raw = kGiftCost;
  frame.details.gift_preview.gold_scale = kScale;
  frame.details.gift_preview.opinion_delta = 40;
  return frame;
}

SourceFrameFixture GoodPostSourceFrame() {
  auto frame = GoodSourceFrame();
  frame.rows.published_generation = 10;
  frame.rows.required_binding.snapshot_revision = 701;
  frame.rows.observed_binding = frame.rows.required_binding;
  frame.details.frame.row_published_generation = 10;
  frame.details.frame.snapshot_revision = 701;
  frame.details.frame.native_snapshot_revision = 1701;
  frame.details.player_gold_raw = kGoldBefore - kGiftCost;
  frame.details.recipient_opinion_of_player = 5;
  frame.details.gift_opinion_present = true;
  frame.details.gift_opinion_modifier_value = 40;
  frame.details.gift_preview = {};
  return frame;
}

FactionGiftMitigationRequestV1 GoodRequest() {
  FactionGiftMitigationRequestV1 value{};
  value.request_id = "g2-m4-faction11-adapter-1";
  value.idempotency_key = "faction11:700:a1000022:c1000033";
  value.expected_revision = 700;
  value.expected_native_revision = 1700;
  value.expected_date_raw = 90234;
  value.player_character_id = kPlayerId;
  value.source_faction_id = kFactionId;
  value.recipient_character_id = kRecipientId;
  value.membership_role = FactionGiftMembershipRoleV1::character_member;
  value.expected_definition_key = "gift_interaction";
  value.expected_definition_stable_hash = kDefinitionHash;
  value.expected_gold_cost_raw = kGiftCost;
  value.expected_gold_scale = kScale;
  value.expected_opinion_delta = 40;
  value.minimum_gold_reserve_raw = 450LL * kScale;
  value.minimum_gold_reserve_scale = kScale;
  return value;
}

struct Fixture {
  std::vector<SourceFrameFixture> frames{GoodSourceFrame(),
                                         GoodSourceFrame()};
  std::size_t frame_index = 0;
  int row_reads = 0;
  int detail_reads = 0;
  int validate_calls = 0;
  int claim_calls = 0;
  int submit_calls = 0;
  bool rows_readable = true;
  bool details_readable = true;
  bool native_valid = true;
  bool claim_result = true;
  bool submit_result = true;
  std::uint32_t requested_faction_id = 0;
  std::uint32_t requested_recipient_id = 0;
  std::uint32_t submitted_player_id = 0;
  std::uint32_t submitted_recipient_id = 0;
  std::uint64_t submitted_hash = 0;
  FactionGiftMitigationSourceFrameV1 required_detail_frame;

  static bool ReadRows(void *context,
                       FactionTargetingRowProbeResultV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.row_reads;
    if (!self.rows_readable || self.frames.empty()) return false;
    const auto index = (std::min)(self.frame_index, self.frames.size() - 1);
    output = self.frames[index].rows;
    return true;
  }

  static bool ReadDetails(
      void *context,
      const FactionGiftMitigationSourceFrameV1 &required_frame,
      std::uint32_t source_faction_id,
      std::uint32_t recipient_character_id,
      FactionGiftMitigationSourceDetailsV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.detail_reads;
    self.required_detail_frame = required_frame;
    self.requested_faction_id = source_faction_id;
    self.requested_recipient_id = recipient_character_id;
    if (!self.details_readable || self.frames.empty()) return false;
    const auto index = (std::min)(self.frame_index, self.frames.size() - 1);
    output = self.frames[index].details;
    ++self.frame_index;
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
      native_reason_key = "fixture_identity_mismatch";
      valid = false;
      return true;
    }
    valid = self.native_valid;
    native_reason_key = self.native_valid ? "" : "fixture_native_reject";
    return true;
  }

  static bool Claim(void *context,
                    std::string_view idempotency_key) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.claim_calls;
    return !idempotency_key.empty() && self.claim_result;
  }

  static bool Submit(void *context, std::uint32_t player_character_id,
                     std::uint32_t recipient_character_id,
                     std::uint64_t definition_stable_hash) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.submit_calls;
    self.submitted_player_id = player_character_id;
    self.submitted_recipient_id = recipient_character_id;
    self.submitted_hash = definition_stable_hash;
    return self.submit_result;
  }

  FactionGiftMitigationSourceActionAccessV1 Access() {
    return {this, &ReadRows, &ReadDetails, &Validate, &Claim, &Submit};
  }
};

FactionGiftMitigationNativeEnvironmentV1 FixtureEnvironment() {
  FactionGiftMitigationNativeEnvironmentV1 value{};
  value.exact_build_admitted = true;
  value.offline_fixture_command = true;
  return value;
}

FactionGiftMitigationAckV1 ExecuteGood(Fixture &fixture) {
  FactionGiftMitigationAckV1 ack{};
  const auto status = ExecuteFactionGiftMitigationSourceActionAdapterV1(
      FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
  Check(status ==
            FactionGiftMitigationAckStatusV1::submitted_verification_pending,
        "good adapter fixture did not submit");
  return ack;
}

void TestAdapterMapsBoundSourcesAndSubmitsOnce() {
  Fixture fixture;
  const auto ack = ExecuteGood(fixture);
  Check(fixture.row_reads == 2 && fixture.detail_reads == 2,
        "adapter must rebuild two source observations before submit");
  Check(fixture.validate_calls == 1 && fixture.claim_calls == 1 &&
            fixture.submit_calls == 1,
        "adapter did not enforce one validation, claim and submit");
  Check(fixture.requested_faction_id == kFactionId &&
            fixture.requested_recipient_id == kRecipientId,
        "source query lost full-generation identities");
  Check(fixture.required_detail_frame.row_published_generation == 8 &&
            fixture.required_detail_frame.proof_epoch == 88 &&
            fixture.required_detail_frame.snapshot_revision == 700 &&
            fixture.required_detail_frame.date_raw == 90234 &&
            fixture.required_detail_frame.player_character_id == kPlayerId,
        "detail query was not bound to the row frame");
  Check(fixture.submitted_player_id == kPlayerId &&
            fixture.submitted_recipient_id == kRecipientId &&
            fixture.submitted_hash == kDefinitionHash,
        "submit arguments lost their action binding");
  Check(ack.verification_pending && ack.source_faction_id == kFactionId &&
            ack.recipient_character_id == kRecipientId,
        "ACK did not retain full-generation bindings");
  const auto serialized = SerializeFactionGiftMitigationAckV1(ack);
  Check(serialized.find("submitted_verification_pending") !=
            std::string::npos,
        "pending ACK serialization missing");
  Check(serialized.find("mitigation_applied") == std::string::npos &&
            serialized.find("postcondition_verified") == std::string::npos,
        "adapter ACK must not claim success");
}

void TestAdapterRejectsCrossFrameAndIdentityDrift() {
  {
    Fixture fixture;
    fixture.frames[0].details.frame.date_raw += 1;
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              ack.failure_class ==
                  FactionGiftMitigationFailureClassV1::snapshot_binding &&
              fixture.submit_calls == 0,
          "cross-frame details must fail before submit");
  }
  {
    Fixture fixture;
    fixture.frames[0].rows.factions[0].faction_id &= 0x00FFFFFFU;
    fixture.frames[0].details.source_faction_present = false;
    fixture.frames[1] = fixture.frames[0];
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              ack.failure_class ==
                  FactionGiftMitigationFailureClassV1::faction_binding &&
              fixture.submit_calls == 0,
          "generation-truncated faction row must be rejected");
  }
  {
    Fixture fixture;
    fixture.frames[1].details.player_gold_raw -= 1;
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        FixtureEnvironment(), fixture.Access(), GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              ack.rejection_reason == "state_changed_before_submit" &&
              fixture.claim_calls == 0 && fixture.submit_calls == 0,
          "second-source drift must precede claim and submit");
  }
}

void TestAdapterSupportsExactLeaderRole() {
  Fixture fixture;
  for (auto &frame : fixture.frames) {
    frame.rows.factions[0].leader_character_id = kRecipientId;
  }
  auto request = GoodRequest();
  request.membership_role = FactionGiftMembershipRoleV1::leader;
  FactionGiftMitigationAckV1 ack{};
  const auto status = ExecuteFactionGiftMitigationSourceActionAdapterV1(
      FixtureEnvironment(), fixture.Access(), request, ack);
  Check(status ==
            FactionGiftMitigationAckStatusV1::submitted_verification_pending &&
            fixture.submit_calls == 1,
        "exact leader row must pass through the adapter");
}

void TestReceiptRequeriesAndDistinguishesOutcomes() {
  Fixture action_fixture;
  const auto ack = ExecuteGood(action_fixture);
  {
    Fixture post_fixture;
    post_fixture.frames = {GoodPostSourceFrame()};
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        post_fixture.Access(), ack, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::mitigated &&
              receipt.mitigation_applied &&
              receipt.postcondition_verified && !receipt.threat_resolved,
          "retained row with exact gold/opinion proof must be mitigated");
    Check(post_fixture.row_reads == 1 && post_fixture.detail_reads == 1 &&
              post_fixture.submit_calls == 0,
          "receipt must requery once and never resubmit");
  }
  {
    Fixture post_fixture;
    auto post = GoodPostSourceFrame();
    post.rows.factions[0].character_member_count = 1;
    post.rows.factions[0].character_member_ids[1] = 0;
    post_fixture.frames = {post};
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        post_fixture.Access(), ack, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left &&
              receipt.recipient_left && receipt.mitigation_applied &&
              receipt.threat_resolved,
          "recipient missing from requery must be left");
  }
  {
    Fixture post_fixture;
    auto post = GoodPostSourceFrame();
    post.rows.terminal = FactionTargetingRowProbeTerminalV1::known_empty;
    post.rows.faction_count = 0;
    post.details.source_faction_present = false;
    post.details.source_faction_metrics_available = false;
    post_fixture.frames = {post};
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        post_fixture.Access(), ack, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left &&
              receipt.faction_dissolved && receipt.mitigation_applied,
          "known-empty requery must preserve faction dissolution outcome");
  }
}

void TestReceiptFailsWithoutNewResourceOpinionFactionProof() {
  Fixture action_fixture;
  const auto ack = ExecuteGood(action_fixture);
  {
    Fixture stale_fixture;
    stale_fixture.frames = {GoodSourceFrame()};
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        stale_fixture.Access(), ack, receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::failed &&
              !receipt.mitigation_applied,
          "ACK plus stale source must not count as success");
  }
  {
    Fixture money_only_fixture;
    auto post = GoodPostSourceFrame();
    post.details.gift_opinion_present = false;
    post.details.gift_opinion_modifier_value.reset();
    money_only_fixture.frames = {post};
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationSourceActionReceiptV1(
        money_only_fixture.Access(), ack, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "recipient_gift_opinion_not_observed" &&
              !receipt.mitigation_applied,
          "money-only result must fail receipt verification");
  }
  {
    Fixture mismatched_faction_fixture;
    auto post = GoodPostSourceFrame();
    post.details.queried_source_faction_id ^= 0x01000000U;
    mismatched_faction_fixture.frames = {post};
    FactionGiftMitigationReceiptV1 receipt{};
    VerifyFactionGiftMitigationSourceActionReceiptV1(
        mismatched_faction_fixture.Access(), ack, receipt);
    Check(receipt.status == FactionGiftMitigationReceiptStatusV1::failed &&
              receipt.reason == "same_faction_requery_failed",
          "receipt must bind the full-generation source faction id");
  }
}

void TestStandaloneCaptureMapsOnlyCoherentRows() {
  Fixture fixture;
  FactionGiftMitigationObservationV1 observation{};
  Check(CaptureFactionGiftMitigationObservationFromSourcesV1(
            fixture.Access(), kFactionId, kRecipientId, observation),
        "coherent standalone capture failed");
  Check(observation.snapshot_revision == 700 &&
            observation.native_snapshot_revision == 1700 &&
            observation.observed_date_raw == 90234 &&
            observation.player_character_id == kPlayerId &&
            observation.queried_source_faction_id == kFactionId &&
            observation.recipient_character_id == kRecipientId,
        "standalone capture lost frame or full-generation identities");

  Fixture odd_generation_fixture;
  odd_generation_fixture.frames[0].rows.published_generation = 9;
  observation = {};
  Check(!CaptureFactionGiftMitigationObservationFromSourcesV1(
            odd_generation_fixture.Access(), kFactionId, kRecipientId,
            observation) &&
            !observation.available,
        "odd row publication must not form an action observation");
}

} // namespace

int main() {
  struct TestCase {
    const char *name;
    void (*run)();
  };
  const TestCase tests[] = {
      {"maps_sources_submits_once",
       &TestAdapterMapsBoundSourcesAndSubmitsOnce},
      {"rejects_binding_drift", &TestAdapterRejectsCrossFrameAndIdentityDrift},
      {"exact_leader_role", &TestAdapterSupportsExactLeaderRole},
      {"receipt_outcomes", &TestReceiptRequeriesAndDistinguishesOutcomes},
      {"receipt_requires_proof",
       &TestReceiptFailsWithoutNewResourceOpinionFactionProof},
      {"standalone_capture", &TestStandaloneCaptureMapsOnlyCoherentRows},
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
  const auto total = sizeof(tests) / sizeof(tests[0]);
  std::cout << total - static_cast<std::size_t>(failures) << '/' << total
            << " passed\n";
  return failures == 0 ? 0 : 1;
}

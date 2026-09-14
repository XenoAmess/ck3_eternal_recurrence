#include "xar_bridge/faction_gift_mitigation_native_binder_v1.hpp"

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using xar::bridge::FactionTargetingRowProbeResultV1;
using xar::bridge::FactionTargetingRowProbeTerminalV1;
using xar::ck3_11906::BindFactionGiftMitigationNativeCallbacksV1;
using xar::ck3_11906::ExecuteFactionGiftMitigationSourceActionAdapterV1;
using xar::ck3_11906::FactionGiftMitigationNativeBinderEnvironmentV1;
using xar::ck3_11906::FactionGiftMitigationNativeBinderStateV1;
using xar::ck3_11906::FactionGiftMitigationNativeFactionObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeFrameObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativePreviewObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeRecipientObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeUpstreamV1;
using xar::ck3_11906::FactionGiftMitigationSourceFrameV1;
using xar::ck3_11906::MakeFactionGiftMitigationCertifiedActionEnvironmentV1;
using xar::ck3_11906::MakeFactionGiftMitigationNativeSourceActionAccessV1;
using xar::ck3_11906::SerializeFactionGiftMitigationAckV1;
using xar::ck3_11906::VerifyFactionGiftMitigationSourceActionReceiptV1;
using xar::ck3_11906::kFactionGiftMitigationActionV1ExecutableSha256;
using xar::ck3_11906::kFactionGiftMitigationExpectedAnchorsV1;
using xar::game::FactionGiftMembershipRoleV1;
using xar::game::FactionGiftMitigationAckStatusV1;
using xar::game::FactionGiftMitigationAckV1;
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
constexpr std::uintptr_t kModuleBase = 0x140000000ULL;

void Check(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

bool ExtendsRow(const FactionGiftMitigationSourceFrameV1 &row,
                const FactionGiftMitigationSourceFrameV1 &native) {
  return native.paused == row.paused &&
         native.row_published_generation == row.row_published_generation &&
         native.proof_epoch == row.proof_epoch &&
         native.snapshot_revision == row.snapshot_revision &&
         native.native_snapshot_revision != 0 &&
         native.date_raw == row.date_raw &&
         native.player_character_id == row.player_character_id;
}

struct NativeFrameFixture {
  FactionTargetingRowProbeResultV1 rows;
  FactionGiftMitigationNativeFrameObservationV1 frame;
  FactionGiftMitigationNativeFactionObservationV1 faction;
  FactionGiftMitigationNativeRecipientObservationV1 recipient;
  FactionGiftMitigationNativePreviewObservationV1 preview;
};

NativeFrameFixture GoodFrame() {
  NativeFrameFixture value{};
  value.rows.terminal = FactionTargetingRowProbeTerminalV1::ready;
  value.rows.published_generation = 8;
  value.rows.required_binding.paused = true;
  value.rows.required_binding.proof_epoch = 88;
  value.rows.required_binding.snapshot_revision = 700;
  value.rows.required_binding.date_raw = 90234;
  value.rows.required_binding.player_character_id = kPlayerId;
  value.rows.observed_binding = value.rows.required_binding;
  value.rows.faction_count = 1;
  auto &row = value.rows.factions[0];
  row.faction_id = kFactionId;
  row.target_character_id = kPlayerId;
  row.leader_present = true;
  row.leader_character_id = kLeaderId;
  row.character_member_count = 2;
  row.character_member_ids[0] = kOtherMemberId;
  row.character_member_ids[1] = kRecipientId;

  FactionGiftMitigationSourceFrameV1 native_frame{};
  native_frame.paused = true;
  native_frame.row_published_generation = 8;
  native_frame.proof_epoch = 88;
  native_frame.snapshot_revision = 700;
  native_frame.native_snapshot_revision = 1700;
  native_frame.date_raw = 90234;
  native_frame.player_character_id = kPlayerId;

  value.frame.available = true;
  value.frame.frame = native_frame;
  value.frame.player_resources_query_complete = true;
  value.frame.player_gold_raw = kGoldBefore;
  value.frame.player_gold_scale = kScale;

  value.faction.available = true;
  value.faction.frame = native_frame;
  value.faction.query_complete = true;
  value.faction.queried_source_faction_id = kFactionId;
  value.faction.source_faction_present = true;
  value.faction.source_faction_at_war = false;
  value.faction.metrics_available = true;
  value.faction.power_raw = 62000;
  value.faction.discontent_raw = 78000;
  value.faction.metric_scale = kScale;

  value.recipient.available = true;
  value.recipient.frame = native_frame;
  value.recipient.identity_resolved = true;
  value.recipient.recipient_character_id = kRecipientId;
  value.recipient.alive = true;
  value.recipient.is_ai = true;
  value.recipient.is_direct_landed_vassal = true;
  value.recipient.opinion_query_complete = true;
  value.recipient.opinion_of_player = -35;

  value.preview.available = true;
  value.preview.frame = native_frame;
  value.preview.player_character_id = kPlayerId;
  value.preview.recipient_character_id = kRecipientId;
  value.preview.preview.available = true;
  value.preview.preview.definition_key = "gift_interaction";
  value.preview.preview.definition_stable_hash = kDefinitionHash;
  value.preview.preview.interaction_legal = true;
  value.preview.preview.auto_accept = true;
  value.preview.preview.gold_cost_raw = kGiftCost;
  value.preview.preview.gold_scale = kScale;
  value.preview.preview.opinion_delta = 40;
  return value;
}

NativeFrameFixture GoodPostFrame() {
  auto value = GoodFrame();
  value.rows.published_generation = 10;
  value.rows.required_binding.snapshot_revision = 701;
  value.rows.observed_binding = value.rows.required_binding;
  value.frame.frame.row_published_generation = 10;
  value.frame.frame.snapshot_revision = 701;
  value.frame.frame.native_snapshot_revision = 1701;
  value.frame.player_gold_raw = kGoldBefore - kGiftCost;
  value.faction.frame = value.frame.frame;
  value.recipient.frame = value.frame.frame;
  value.recipient.opinion_of_player = 5;
  value.recipient.gift_opinion_present = true;
  value.recipient.gift_opinion_modifier_value = 40;
  value.preview = {};
  value.preview.frame = value.frame.frame;
  return value;
}

FactionGiftMitigationRequestV1 GoodRequest() {
  FactionGiftMitigationRequestV1 value{};
  value.request_id = "g2-m4-faction12-native-binder-1";
  value.idempotency_key = "faction12:700:a1000022:c1000033";
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

FactionGiftMitigationNativeBinderEnvironmentV1 GoodEnvironment() {
  FactionGiftMitigationNativeBinderEnvironmentV1 value{};
  value.exact_build_admitted = true;
  value.executable_sha256 = kFactionGiftMitigationActionV1ExecutableSha256;
  value.module_base = kModuleBase;
  for (std::size_t index = 0;
       index < kFactionGiftMitigationExpectedAnchorsV1.size(); ++index) {
    value.anchors[index].rva =
        kFactionGiftMitigationExpectedAnchorsV1[index].rva;
    value.anchors[index].resolved_address =
        kModuleBase + kFactionGiftMitigationExpectedAnchorsV1[index].rva;
    value.anchors[index].span_sha256.assign(
        kFactionGiftMitigationExpectedAnchorsV1[index].span_sha256);
  }
  return value;
}

struct Fixture {
  std::vector<NativeFrameFixture> frames{GoodFrame(), GoodFrame()};
  std::size_t frame_index = 0;
  int row_reads = 0;
  int frame_reads = 0;
  int faction_reads = 0;
  int recipient_reads = 0;
  int preview_reads = 0;
  int validate_calls = 0;
  int claim_calls = 0;
  int submit_calls = 0;
  bool native_valid = true;
  bool claim_result = true;
  bool submit_result = true;
  std::uint32_t submitted_player_id = 0;
  std::uint32_t submitted_recipient_id = 0;
  std::uint64_t submitted_hash = 0;

  NativeFrameFixture *Current() noexcept {
    if (frames.empty()) return nullptr;
    const auto index = frame_index < frames.size() ? frame_index
                                                   : frames.size() - 1;
    return &frames[index];
  }

  static bool ReadRows(void *context,
                       FactionTargetingRowProbeResultV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.row_reads;
    auto *const current = self.Current();
    if (current == nullptr) return false;
    output = current->rows;
    return true;
  }

  static bool ReadFrame(
      void *context,
      const FactionGiftMitigationSourceFrameV1 &required_row_frame,
      FactionGiftMitigationNativeFrameObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.frame_reads;
    auto *const current = self.Current();
    if (current == nullptr ||
        !ExtendsRow(required_row_frame, current->frame.frame)) {
      return false;
    }
    output = current->frame;
    return true;
  }

  static bool ReadFaction(
      void *context,
      const FactionGiftMitigationSourceFrameV1 &required_native_frame,
      std::uint32_t source_faction_id,
      FactionGiftMitigationNativeFactionObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.faction_reads;
    auto *const current = self.Current();
    if (current == nullptr || current->faction.frame != required_native_frame ||
        source_faction_id != kFactionId) {
      return false;
    }
    output = current->faction;
    return true;
  }

  static bool ReadRecipient(
      void *context,
      const FactionGiftMitigationSourceFrameV1 &required_native_frame,
      std::uint32_t recipient_character_id,
      FactionGiftMitigationNativeRecipientObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.recipient_reads;
    auto *const current = self.Current();
    if (current == nullptr ||
        current->recipient.frame != required_native_frame ||
        recipient_character_id != kRecipientId) {
      return false;
    }
    output = current->recipient;
    return true;
  }

  static bool ReadPreview(
      void *context,
      const FactionGiftMitigationSourceFrameV1 &required_native_frame,
      std::uint32_t player_character_id,
      std::uint32_t recipient_character_id,
      FactionGiftMitigationNativePreviewObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.preview_reads;
    auto *const current = self.Current();
    if (current == nullptr || current->preview.frame != required_native_frame ||
        player_character_id != kPlayerId ||
        recipient_character_id != kRecipientId) {
      return false;
    }
    output = current->preview;
    ++self.frame_index;
    return true;
  }

  static bool ValidateGift(void *context, std::uint32_t player_character_id,
                           std::uint32_t recipient_character_id,
                           std::string_view definition_key,
                           std::uint64_t expected_definition_stable_hash,
                           bool &valid,
                           std::string &native_reason_key) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.validate_calls;
    if (player_character_id != kPlayerId ||
        recipient_character_id != kRecipientId ||
        definition_key != "gift_interaction" ||
        expected_definition_stable_hash != kDefinitionHash) {
      valid = false;
      native_reason_key = "fixture_generic_identity_mismatch";
      return true;
    }
    valid = self.native_valid;
    native_reason_key = self.native_valid ? "" : "fixture_generic_reject";
    return true;
  }

  static bool Claim(void *context,
                    std::string_view idempotency_key) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.claim_calls;
    return !idempotency_key.empty() && self.claim_result;
  }

  static bool SubmitGift(void *context, std::uint32_t player_character_id,
                         std::uint32_t recipient_character_id,
                         std::string_view definition_key,
                         std::uint64_t expected_definition_stable_hash)
      noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.submit_calls;
    self.submitted_player_id = player_character_id;
    self.submitted_recipient_id = recipient_character_id;
    self.submitted_hash = expected_definition_stable_hash;
    return definition_key == "gift_interaction" && self.submit_result;
  }

  FactionGiftMitigationNativeUpstreamV1 Upstream() {
    return {this, &ReadRows, this, &ReadFrame, &ReadFaction, &ReadRecipient,
            &ReadPreview, &ValidateGift, &Claim, &SubmitGift};
  }
};

void BindGood(FactionGiftMitigationNativeBinderStateV1 &state,
              Fixture &fixture) {
  Check(BindFactionGiftMitigationNativeCallbacksV1(
            state, GoodEnvironment(), fixture.Upstream()),
        "exact fixture binder admission failed");
}

FactionGiftMitigationAckV1 ExecuteGood(
    FactionGiftMitigationNativeBinderStateV1 &state, Fixture &fixture) {
  BindGood(state, fixture);
  const auto sources =
      MakeFactionGiftMitigationNativeSourceActionAccessV1(state);
  const auto environment =
      MakeFactionGiftMitigationCertifiedActionEnvironmentV1(state);
  FactionGiftMitigationAckV1 ack{};
  const auto status = ExecuteFactionGiftMitigationSourceActionAdapterV1(
      environment, sources, GoodRequest(), ack);
  Check(status ==
            FactionGiftMitigationAckStatusV1::submitted_verification_pending,
        "bound native fixture did not return pending ACK");
  return ack;
}

void TestExactBuildRvaAndHashGates() {
  Fixture fixture;
  {
    auto environment = GoodEnvironment();
    environment.executable_sha256[0] = '0';
    FactionGiftMitigationNativeBinderStateV1 state{};
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, environment, fixture.Upstream()) && !state.bound,
          "wrong executable hash must fail binding");
  }
  {
    auto environment = GoodEnvironment();
    environment.anchors[3].rva += 1;
    FactionGiftMitigationNativeBinderStateV1 state{};
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, environment, fixture.Upstream()),
          "wrong anchor RVA must fail binding");
  }
  {
    auto environment = GoodEnvironment();
    environment.anchors[5].resolved_address += 1;
    FactionGiftMitigationNativeBinderStateV1 state{};
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, environment, fixture.Upstream()),
          "wrong resolved address must fail binding");
  }
  {
    auto environment = GoodEnvironment();
    environment.anchors[8].span_sha256[0] = '0';
    FactionGiftMitigationNativeBinderStateV1 state{};
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, environment, fixture.Upstream()),
          "wrong anchor span hash must fail binding");
  }
  {
    auto upstream = fixture.Upstream();
    upstream.submit_gift = nullptr;
    FactionGiftMitigationNativeBinderStateV1 state{};
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, GoodEnvironment(), upstream),
          "incomplete generic send chain must fail binding");
  }
  {
    FactionGiftMitigationNativeBinderStateV1 state{};
    BindGood(state, fixture);
    Check(!BindFactionGiftMitigationNativeCallbacksV1(
              state, GoodEnvironment(), fixture.Upstream()),
          "bound one-shot state must not be rebound");
    const auto action_environment =
        MakeFactionGiftMitigationCertifiedActionEnvironmentV1(state);
    Check(action_environment.module_base == kModuleBase &&
              action_environment.exact_build_admitted &&
              action_environment.command_abi_certified &&
              !action_environment.offline_fixture_command,
          "certified action environment is incomplete");
  }
}

void TestBoundCallbacksSubmitExactlyOnceAndAckPending() {
  Fixture fixture;
  FactionGiftMitigationNativeBinderStateV1 state{};
  const auto ack = ExecuteGood(state, fixture);
  Check(fixture.row_reads == 2 && fixture.frame_reads == 2 &&
            fixture.faction_reads == 2 && fixture.recipient_reads == 2 &&
            fixture.preview_reads == 2,
        "pre-submit sources were not freshly rebound twice");
  Check(fixture.validate_calls == 1 && fixture.claim_calls == 1 &&
            fixture.submit_calls == 1,
        "generic interaction chain must submit exactly once");
  Check(fixture.submitted_player_id == kPlayerId &&
            fixture.submitted_recipient_id == kRecipientId &&
            fixture.submitted_hash == kDefinitionHash,
        "generic send lost full-generation identity or definition hash");
  Check(ack.verification_pending && ack.source_faction_id == kFactionId &&
            ack.recipient_character_id == kRecipientId,
        "pending ACK lost full-generation binding");
  const auto json = SerializeFactionGiftMitigationAckV1(ack);
  Check(json.find("submitted_verification_pending") != std::string::npos &&
            json.find("mitigation_applied") == std::string::npos &&
            json.find("postcondition_verified") == std::string::npos,
        "queue ACK was serialized as outcome success");

  auto sources = MakeFactionGiftMitigationNativeSourceActionAccessV1(state);
  Check(!sources.submit_native(sources.context, kPlayerId, kRecipientId,
                               kDefinitionHash) &&
            fixture.submit_calls == 1,
        "binder allowed a second submit");
}

void TestBinderRejectsFrameIdentityAndPreviewDrift() {
  {
    Fixture fixture;
    fixture.frames[0].recipient.frame.native_snapshot_revision += 1;
    FactionGiftMitigationNativeBinderStateV1 state{};
    BindGood(state, fixture);
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        MakeFactionGiftMitigationCertifiedActionEnvironmentV1(state),
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state),
        GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              fixture.submit_calls == 0,
          "cross-frame recipient details must fail before submit");
  }
  {
    Fixture fixture;
    fixture.frames[0].preview.preview.definition_stable_hash ^= 1;
    fixture.frames[1] = fixture.frames[0];
    FactionGiftMitigationNativeBinderStateV1 state{};
    BindGood(state, fixture);
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        MakeFactionGiftMitigationCertifiedActionEnvironmentV1(state),
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state),
        GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              fixture.validate_calls == 0 && fixture.submit_calls == 0,
          "definition hash drift must fail before generic validation");
  }
  {
    Fixture fixture;
    fixture.frames[0].rows.factions[0].character_member_ids[1] &=
        0x00FFFFFFU;
    fixture.frames[1] = fixture.frames[0];
    FactionGiftMitigationNativeBinderStateV1 state{};
    BindGood(state, fixture);
    FactionGiftMitigationAckV1 ack{};
    ExecuteFactionGiftMitigationSourceActionAdapterV1(
        MakeFactionGiftMitigationCertifiedActionEnvironmentV1(state),
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state),
        GoodRequest(), ack);
    Check(ack.status ==
              FactionGiftMitigationAckStatusV1::rejected_before_submit &&
              fixture.submit_calls == 0,
          "generation-truncated member identity must fail");
  }
}

void TestReceiptPerformsRealRequery() {
  Fixture fixture;
  fixture.frames.push_back(GoodPostFrame());
  FactionGiftMitigationNativeBinderStateV1 state{};
  const auto ack = ExecuteGood(state, fixture);
  auto sources = MakeFactionGiftMitigationNativeSourceActionAccessV1(state);
  FactionGiftMitigationReceiptV1 receipt{};
  const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
      sources, ack, receipt);
  Check(status == FactionGiftMitigationReceiptStatusV1::mitigated &&
            receipt.mitigation_applied && receipt.postcondition_verified &&
            !receipt.threat_resolved,
        "fresh native requery did not prove mitigation");
  Check(fixture.row_reads == 3 && fixture.frame_reads == 3 &&
            fixture.faction_reads == 3 && fixture.recipient_reads == 3 &&
            fixture.preview_reads == 3 && fixture.submit_calls == 1,
        "receipt did not fresh-read every source exactly once");
}

void TestReceiptDistinguishesLeftAndFailed() {
  {
    Fixture fixture;
    auto post = GoodPostFrame();
    post.rows.factions[0].character_member_count = 1;
    post.rows.factions[0].character_member_ids[1] = 0;
    fixture.frames.push_back(post);
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto ack = ExecuteGood(state, fixture);
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state), ack,
        receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left &&
              receipt.recipient_left && receipt.threat_resolved &&
              receipt.mitigation_applied,
          "recipient exit was not distinguished as left");
  }
  {
    Fixture fixture;
    auto post = GoodPostFrame();
    post.rows.terminal = FactionTargetingRowProbeTerminalV1::known_empty;
    post.rows.faction_count = 0;
    post.faction.source_faction_present = false;
    post.faction.metrics_available = false;
    fixture.frames.push_back(post);
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto ack = ExecuteGood(state, fixture);
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state), ack,
        receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::left &&
              receipt.faction_dissolved && receipt.mitigation_applied,
          "faction dissolution was not distinguished as left");
  }
  {
    Fixture fixture;
    auto post = GoodPostFrame();
    post.recipient.gift_opinion_present = false;
    post.recipient.gift_opinion_modifier_value.reset();
    fixture.frames.push_back(post);
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto ack = ExecuteGood(state, fixture);
    FactionGiftMitigationReceiptV1 receipt{};
    const auto status = VerifyFactionGiftMitigationSourceActionReceiptV1(
        MakeFactionGiftMitigationNativeSourceActionAccessV1(state), ack,
        receipt);
    Check(status == FactionGiftMitigationReceiptStatusV1::failed &&
              !receipt.mitigation_applied &&
              receipt.reason == "recipient_gift_opinion_not_observed",
          "money-only requery must remain failed");
  }
}

} // namespace

int main() {
  struct TestCase {
    const char *name;
    void (*run)();
  };
  const TestCase tests[] = {
      {"exact_build_rva_hash_gates", &TestExactBuildRvaAndHashGates},
      {"submit_once_ack_pending",
       &TestBoundCallbacksSubmitExactlyOnceAndAckPending},
      {"rejects_frame_identity_preview_drift",
       &TestBinderRejectsFrameIdentityAndPreviewDrift},
      {"receipt_real_requery", &TestReceiptPerformsRealRequery},
      {"receipt_left_failed", &TestReceiptDistinguishesLeftAndFailed},
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

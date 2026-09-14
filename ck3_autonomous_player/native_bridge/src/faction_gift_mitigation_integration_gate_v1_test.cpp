#include "xar_bridge/faction_gift_mitigation_integration_gate_v1.hpp"

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
using xar::ck3_11906::EvaluateFactionGiftMitigationIntegrationGateV1;
using xar::ck3_11906::FactionGiftMitigationIntegrationGateResultV1;
using xar::ck3_11906::FactionGiftMitigationIntegrationGateTerminalV1;
using xar::ck3_11906::FactionGiftMitigationNativeBinderEnvironmentV1;
using xar::ck3_11906::FactionGiftMitigationNativeBinderStateV1;
using xar::ck3_11906::FactionGiftMitigationNativeFactionObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeFrameObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativePreviewObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeRecipientObservationV1;
using xar::ck3_11906::FactionGiftMitigationNativeUpstreamV1;
using xar::ck3_11906::FactionGiftMitigationSourceFrameV1;
using xar::ck3_11906::SerializeFactionGiftMitigationIntegrationGateResultV1;
using xar::ck3_11906::faction_gift_gate_red_action_already_consumed;
using xar::ck3_11906::faction_gift_gate_red_binder_unavailable;
using xar::ck3_11906::faction_gift_gate_red_budget;
using xar::ck3_11906::faction_gift_gate_red_identity_binding;
using xar::ck3_11906::faction_gift_gate_red_observation_drift;
using xar::ck3_11906::faction_gift_gate_red_preview_binding;
using xar::ck3_11906::faction_gift_gate_red_publication_drift;
using xar::ck3_11906::faction_gift_gate_red_resource_binding;
using xar::ck3_11906::kFactionGiftMitigationActionV1ExecutableSha256;
using xar::ck3_11906::kFactionGiftMitigationExpectedAnchorsV1;
using xar::game::FactionGiftMembershipRoleV1;
using xar::game::FactionGiftMitigationRequestV1;

constexpr std::uint32_t kPlayerId = 0x81000011U;
constexpr std::uint32_t kFactionId = 0xA1000022U;
constexpr std::uint32_t kRecipientId = 0xC1000033U;
constexpr std::uint32_t kOtherMemberId = 0x41000044U;
constexpr std::uint32_t kLeaderId = 0xB1000055U;
constexpr std::uint64_t kDefinitionHash = 0xE313B9C7D54A0211ULL;
constexpr std::uint32_t kScale = 100000U;
constexpr std::int64_t kGiftCost = 50LL * kScale;
constexpr std::uintptr_t kModuleBase = 0x140000000ULL;

void Check(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

bool HasFlag(std::uint32_t value, std::uint32_t flag) {
  return (value & flag) != 0;
}

struct GateFrameFixture {
  FactionTargetingRowProbeResultV1 rows;
  FactionGiftMitigationNativeFrameObservationV1 frame;
  FactionGiftMitigationNativeFactionObservationV1 faction;
  FactionGiftMitigationNativeRecipientObservationV1 recipient;
  FactionGiftMitigationNativePreviewObservationV1 preview;
};

GateFrameFixture GoodFrame() {
  GateFrameFixture value{};
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
  value.frame.player_gold_raw = 500LL * kScale;
  value.frame.player_gold_scale = kScale;

  value.faction.available = true;
  value.faction.frame = native_frame;
  value.faction.query_complete = true;
  value.faction.queried_source_faction_id = kFactionId;
  value.faction.source_faction_present = true;
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

void RebindFrame(GateFrameFixture &value, std::uint64_t generation,
                 std::uint64_t proof_epoch) {
  value.rows.published_generation = generation;
  value.rows.required_binding.proof_epoch = proof_epoch;
  value.rows.observed_binding = value.rows.required_binding;
  value.frame.frame.row_published_generation = generation;
  value.frame.frame.proof_epoch = proof_epoch;
  value.faction.frame = value.frame.frame;
  value.recipient.frame = value.frame.frame;
  value.preview.frame = value.frame.frame;
}

FactionGiftMitigationRequestV1 GoodRequest() {
  FactionGiftMitigationRequestV1 value{};
  value.request_id = "g2-m4-faction13-preflight-1";
  value.idempotency_key = "faction13:700:a1000022:c1000033";
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
    const auto &expected = kFactionGiftMitigationExpectedAnchorsV1[index];
    value.anchors[index].rva = expected.rva;
    value.anchors[index].resolved_address = kModuleBase + expected.rva;
    value.anchors[index].span_sha256.assign(expected.span_sha256);
  }
  return value;
}

struct Fixture {
  std::vector<GateFrameFixture> frames{GoodFrame(), GoodFrame()};
  std::size_t frame_index = 0;
  int row_reads = 0;
  int frame_reads = 0;
  int faction_reads = 0;
  int recipient_reads = 0;
  int preview_reads = 0;
  int validate_calls = 0;
  int claim_calls = 0;
  int submit_calls = 0;

  GateFrameFixture *Current() noexcept {
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
      void *context, const FactionGiftMitigationSourceFrameV1 &required,
      FactionGiftMitigationNativeFrameObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.frame_reads;
    auto *const current = self.Current();
    if (current == nullptr ||
        current->frame.frame.row_published_generation !=
            required.row_published_generation ||
        current->frame.frame.proof_epoch != required.proof_epoch ||
        current->frame.frame.snapshot_revision !=
            required.snapshot_revision ||
        current->frame.frame.date_raw != required.date_raw ||
        current->frame.frame.player_character_id !=
            required.player_character_id) {
      return false;
    }
    output = current->frame;
    return true;
  }

  static bool ReadFaction(
      void *context, const FactionGiftMitigationSourceFrameV1 &required,
      std::uint32_t source_faction_id,
      FactionGiftMitigationNativeFactionObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.faction_reads;
    auto *const current = self.Current();
    if (current == nullptr || current->faction.frame != required ||
        source_faction_id != kFactionId) {
      return false;
    }
    output = current->faction;
    return true;
  }

  static bool ReadRecipient(
      void *context, const FactionGiftMitigationSourceFrameV1 &required,
      std::uint32_t recipient_character_id,
      FactionGiftMitigationNativeRecipientObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.recipient_reads;
    auto *const current = self.Current();
    if (current == nullptr || current->recipient.frame != required ||
        recipient_character_id != kRecipientId) {
      return false;
    }
    output = current->recipient;
    return true;
  }

  static bool ReadPreview(
      void *context, const FactionGiftMitigationSourceFrameV1 &required,
      std::uint32_t player_character_id,
      std::uint32_t recipient_character_id,
      FactionGiftMitigationNativePreviewObservationV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.preview_reads;
    auto *const current = self.Current();
    if (current == nullptr || current->preview.frame != required ||
        player_character_id != kPlayerId ||
        recipient_character_id != kRecipientId) {
      return false;
    }
    output = current->preview;
    ++self.frame_index;
    return true;
  }

  static bool Validate(void *context, std::uint32_t, std::uint32_t,
                       std::string_view, std::uint64_t, bool &valid,
                       std::string &) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.validate_calls;
    valid = true;
    return true;
  }

  static bool Claim(void *context, std::string_view) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.claim_calls;
    return true;
  }

  static bool Submit(void *context, std::uint32_t, std::uint32_t,
                     std::string_view, std::uint64_t) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.submit_calls;
    return true;
  }

  FactionGiftMitigationNativeUpstreamV1 Upstream() {
    return {this, &ReadRows, this, &ReadFrame, &ReadFaction, &ReadRecipient,
            &ReadPreview, &Validate, &Claim, &Submit};
  }
};

void BindGood(FactionGiftMitigationNativeBinderStateV1 &state,
              Fixture &fixture) {
  Check(BindFactionGiftMitigationNativeCallbacksV1(
            state, GoodEnvironment(), fixture.Upstream()),
        "fixture binder admission failed");
}

FactionGiftMitigationIntegrationGateResultV1 RunGate(
    FactionGiftMitigationNativeBinderStateV1 &state, Fixture &fixture,
    const FactionGiftMitigationRequestV1 &request = GoodRequest()) {
  BindGood(state, fixture);
  FactionGiftMitigationIntegrationGateResultV1 result{};
  EvaluateFactionGiftMitigationIntegrationGateV1(state, request, result);
  return result;
}

void CheckNoAction(const Fixture &fixture,
                   const FactionGiftMitigationNativeBinderStateV1 &state) {
  Check(fixture.validate_calls == 0 && fixture.claim_calls == 0 &&
            fixture.submit_calls == 0 &&
            !state.idempotency_claim_attempted && !state.submit_attempted,
        "read-only gate invoked an action callback");
}

void TestReadyGateIsStableAndReadOnly() {
  Fixture fixture;
  FactionGiftMitigationNativeBinderStateV1 state{};
  const auto result = RunGate(state, fixture);
  Check(result.terminal ==
            FactionGiftMitigationIntegrationGateTerminalV1::ready &&
            result.red_flags == 0 && result.ready_for_single_submit &&
            !result.action_callbacks_invoked,
        "coherent integration preflight must be READY");
  Check(result.row_published_generation == 8 && result.proof_epoch == 88 &&
            result.snapshot_revision == 700 &&
            result.native_snapshot_revision == 1700 &&
            result.player_character_id == kPlayerId &&
            result.source_faction_id == kFactionId &&
            result.recipient_character_id == kRecipientId,
        "READY output lost generation/proof/identity bindings");
  Check(fixture.row_reads == 4 && fixture.frame_reads == 2 &&
            fixture.faction_reads == 2 && fixture.recipient_reads == 2 &&
            fixture.preview_reads == 2,
        "gate did not take the required independent read samples");
  CheckNoAction(fixture, state);
  const auto json = SerializeFactionGiftMitigationIntegrationGateResultV1(
      result);
  Check(json.find("\"terminal\":\"ready\"") != std::string::npos &&
            json.find("\"ready_for_single_submit\":true") !=
                std::string::npos &&
            json.find("submitted_verification_pending") == std::string::npos &&
            json.find("mitigation_applied") == std::string::npos,
        "preflight serialization was confused with ACK or outcome");
}

void TestPublicationProofDriftIsTypedRed() {
  Fixture fixture;
  RebindFrame(fixture.frames[1], 10, 89);
  FactionGiftMitigationNativeBinderStateV1 state{};
  const auto result = RunGate(state, fixture);
  Check(result.terminal ==
            FactionGiftMitigationIntegrationGateTerminalV1::red &&
            HasFlag(result.red_flags,
                    faction_gift_gate_red_publication_drift) &&
            !result.ready_for_single_submit,
        "publication/proof drift must remain typed RED");
  CheckNoAction(fixture, state);
}

void TestObservationIdentityAndResourceDriftAreTypedRed() {
  {
    Fixture fixture;
    fixture.frames[1].frame.player_gold_raw -= 1;
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto result = RunGate(state, fixture);
    Check(HasFlag(result.red_flags,
                  faction_gift_gate_red_observation_drift),
          "resource drift between captures needs observation RED");
    CheckNoAction(fixture, state);
  }
  {
    Fixture fixture;
    for (auto &frame : fixture.frames) {
      frame.rows.factions[0].character_member_count = 1;
      frame.rows.factions[0].character_member_ids[0] = kOtherMemberId;
      frame.rows.factions[0].character_member_ids[1] = 0;
    }
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto result = RunGate(state, fixture);
    Check(HasFlag(result.red_flags, faction_gift_gate_red_identity_binding),
          "missing full-generation member identity needs typed RED");
    CheckNoAction(fixture, state);
  }
  {
    Fixture fixture;
    for (auto &frame : fixture.frames) {
      frame.frame.player_resources_query_complete = false;
    }
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto result = RunGate(state, fixture);
    Check(HasFlag(result.red_flags, faction_gift_gate_red_resource_binding),
          "incomplete player resource query needs typed RED");
    CheckNoAction(fixture, state);
  }
}

void TestPreviewAndBudgetFailuresAreTypedRed() {
  {
    Fixture fixture;
    for (auto &frame : fixture.frames) {
      frame.preview.preview.definition_stable_hash ^= 1;
    }
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto result = RunGate(state, fixture);
    Check(HasFlag(result.red_flags, faction_gift_gate_red_preview_binding),
          "definition hash drift needs preview RED");
    CheckNoAction(fixture, state);
  }
  {
    Fixture fixture;
    for (auto &frame : fixture.frames) {
      frame.frame.player_gold_raw = 500LL * kScale - 1;
    }
    FactionGiftMitigationNativeBinderStateV1 state{};
    const auto result = RunGate(state, fixture);
    Check(HasFlag(result.red_flags, faction_gift_gate_red_budget),
          "reserve shortage needs budget RED");
    CheckNoAction(fixture, state);
  }
}

void TestUnavailableAndConsumedBindersAreTypedRed() {
  {
    FactionGiftMitigationNativeBinderStateV1 state{};
    FactionGiftMitigationIntegrationGateResultV1 result{};
    EvaluateFactionGiftMitigationIntegrationGateV1(state, GoodRequest(),
                                                    result);
    Check(HasFlag(result.red_flags,
                  faction_gift_gate_red_binder_unavailable),
          "unbound binder needs typed RED");
  }
  {
    Fixture fixture;
    FactionGiftMitigationNativeBinderStateV1 state{};
    BindGood(state, fixture);
    state.submit_attempted = true;
    FactionGiftMitigationIntegrationGateResultV1 result{};
    EvaluateFactionGiftMitigationIntegrationGateV1(state, GoodRequest(),
                                                    result);
    Check(HasFlag(result.red_flags,
                  faction_gift_gate_red_action_already_consumed) &&
              fixture.row_reads == 0 && fixture.submit_calls == 0,
          "consumed one-shot binder must RED before source reads");
  }
}

} // namespace

int main() {
  struct TestCase {
    const char *name;
    void (*run)();
  };
  const TestCase tests[] = {
      {"ready_stable_read_only", &TestReadyGateIsStableAndReadOnly},
      {"publication_proof_red", &TestPublicationProofDriftIsTypedRed},
      {"observation_identity_resource_red",
       &TestObservationIdentityAndResourceDriftAreTypedRed},
      {"preview_budget_red", &TestPreviewAndBudgetFailuresAreTypedRed},
      {"unavailable_consumed_red",
       &TestUnavailableAndConsumedBindersAreTypedRed},
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

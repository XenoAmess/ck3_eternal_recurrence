#include "xar_bridge/player_prisoner_management_source_adapter_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

namespace bridge = xar::bridge;
using Access = bridge::PlayerPrisonerSourceAccessV1;
using Collector = bridge::PlayerPrisonerSourceCollectorLeaseV1;
using CoreFailure = bridge::PlayerPrisonerSnapshotFailureV1;
using Failure = bridge::PlayerPrisonerSourceAdapterFailureV1;
using FieldState = bridge::PlayerPrisonerFieldStateV1;
using Frame = bridge::PlayerPrisonerFrameV1;
using OpaqueFinal = bridge::PlayerPrisonerOpaqueFinalBoolV1;
using Player = bridge::PlayerPrisonerSourcePlayerLeaseV1;
using Preview = bridge::PlayerPrisonerInteractionPreviewV1;
using PreviewKind = bridge::PlayerPrisonerSourcePreviewKindV1;
using Ransom = bridge::PlayerPrisonerRansomPreviewV1;
using Reasons = bridge::PlayerPrisonerSourceNativeReasonsV1;
using Result = bridge::PlayerPrisonerSourceResultV1;
using Row = bridge::PlayerPrisonerSourceRowLeaseV1;
using UnknownReason = bridge::PlayerPrisonerUnknownReasonV1;

OpaqueFinal KnownFinal(bool value) {
  return {FieldState::known, value, UnknownReason::none,
          bridge::PlayerPrisonerNativeReasonSourceV1::native_opaque_final};
}

Preview FinalPreview(bool can_send, std::string_view failure_key = {}) {
  Preview output{};
  output.state = FieldState::known;
  output.unknown_reason = UnknownReason::none;
  output.source = bridge::PlayerPrisonerPreviewSourceV1::
      native_finalized_character_interaction;
  output.shown = true;
  output.valid = true;
  output.can_send = can_send;
  output.failure_reason_key =
      can_send ? bridge::PlayerPrisonerUnknownKeyV1(
                     UnknownReason::not_applicable)
               : bridge::PlayerPrisonerKnownKeyV1(failure_key);
  return output;
}

Ransom FinalRansom(std::int32_t payer, bool can_send, bool accepts) {
  Ransom output{};
  output.interaction = FinalPreview(
      can_send, "ransom_interaction_cannot_send");
  output.payer_character_id = payer;
  output.selected_option_key =
      bridge::PlayerPrisonerKnownKeyV1("gold");
  output.resource_key = bridge::PlayerPrisonerKnownKeyV1("gold");
  output.resource_amount_raw = 50 *
      bridge::kPlayerPrisonerFixedPointOneV1;
  output.acceptance_required = true;
  output.would_accept_now = KnownFinal(accepts);
  return output;
}

struct Fixture {
  std::array<Frame, 2> frames{};
  std::array<Player, 2> players{};
  std::array<Collector, 2> collectors{};
  std::array<std::array<Row, 2>, 2> rows{};
  std::array<std::array<Reasons, 2>, 2> reasons{};
  std::array<std::array<Ransom, 2>, 2> ransoms{};
  std::array<std::array<std::array<Preview, 5>, 2>, 2> previews{};

  std::size_t frame_calls = 0;
  std::size_t player_calls = 0;
  std::size_t collector_calls = 0;
  std::size_t prisoner_calls = 0;
  std::size_t reason_calls = 0;
  std::size_t ransom_calls = 0;
  std::size_t preview_calls = 0;
  std::size_t active_pass = 0;
  std::size_t fail_frame_call = 0;
  std::size_t fail_player_call = 0;
  std::size_t fail_collector_call = 0;
  std::size_t fail_prisoner_call = 0;
  std::size_t fail_reason_call = 0;
  std::size_t fail_ransom_call = 0;
  std::size_t fail_preview_call = 0;

  Fixture() {
    frames.fill(Frame{71, 119006, 904, 53183856, true, true, 101,
                      true, true});
    players.fill(Player{true, 0x71000000, 0xA101, 5, 101, true});
    collectors.fill(
        Collector{true, 0x72000000, 0xB101, 9, 101, true, 2, 2});

    const Row first{true,
                    0x73000000,
                    0xC502,
                    3,
                    502,
                    101,
                    true,
                    bridge::PlayerPrisonerCustodyKindV1::dungeon,
                    180};
    const Row second{true,
                     0x73001000,
                     0xC501,
                     7,
                     501,
                     101,
                     true,
                     bridge::PlayerPrisonerCustodyKindV1::house_arrest,
                     45};
    rows[0] = {first, second};
    rows[1] = rows[0];

    for (std::size_t pass = 0; pass < rows.size(); ++pass) {
      reasons[pass][0] = {KnownFinal(true), KnownFinal(true),
                          KnownFinal(true)};
      reasons[pass][1] = {KnownFinal(true), KnownFinal(false),
                          KnownFinal(false)};
      ransoms[pass][0] = FinalRansom(702, false, false);
      ransoms[pass][1] = FinalRansom(701, true, true);
      for (std::size_t index = 0; index < rows[pass].size(); ++index) {
        previews[pass][index][0] = FinalPreview(true);
        previews[pass][index][1] =
            FinalPreview(index == 0, "execute_prisoner_blocked");
        previews[pass][index][2] =
            FinalPreview(index != 0, "already_in_dungeon");
        previews[pass][index][3] =
            FinalPreview(index == 0, "already_in_house_arrest");
        previews[pass][index][4] =
            FinalPreview(index == 0, "torture_interaction_blocked");
      }
    }
  }

  std::size_t FindRow(std::size_t pass,
                      std::int32_t prisoner_character_id) const {
    for (std::size_t index = 0; index < rows[pass].size(); ++index) {
      if (rows[pass][index].prisoner_character_id ==
          prisoner_character_id) {
        return index;
      }
    }
    return rows[pass].size();
  }
};

bool CaptureFrame(void *context, Frame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.frame_calls == fixture.fail_frame_call) return false;
  output = fixture.frames[fixture.frame_calls > 1 ? 1 : 0];
  return true;
}

bool ResolvePlayer(void *context, std::int32_t expected_character_id,
                   Player &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.player_calls;
  if (fixture.player_calls == fixture.fail_player_call) return false;
  const auto pass = fixture.player_calls > 1 ? 1U : 0U;
  if (fixture.players[pass].character_id != expected_character_id) {
    return false;
  }
  output = fixture.players[pass];
  return true;
}

bool ResolveCollector(void *context, const Player &player,
                      Collector &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.collector_calls;
  if (fixture.collector_calls == fixture.fail_collector_call) return false;
  const auto pass = fixture.collector_calls > 1 ? 1U : 0U;
  if (player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  fixture.active_pass = pass;
  output = fixture.collectors[pass];
  return true;
}

bool ReadPrisoner(void *context, const Player &player,
                  const Collector &collector, std::size_t row_index,
                  Row &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.prisoner_calls;
  if (fixture.prisoner_calls == fixture.fail_prisoner_call) return false;
  const auto pass = fixture.active_pass;
  if (player.native_address != fixture.players[pass].native_address ||
      collector.native_address != fixture.collectors[pass].native_address ||
      row_index >= fixture.rows[pass].size()) {
    return false;
  }
  output = fixture.rows[pass][row_index];
  return true;
}

bool ReadReasons(void *context, const Player &player, const Row &prisoner,
                 Reasons &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.reason_calls;
  if (fixture.reason_calls == fixture.fail_reason_call) return false;
  const auto pass = fixture.active_pass;
  const auto index = fixture.FindRow(pass, prisoner.prisoner_character_id);
  if (player.character_id != 101 || index == fixture.rows[pass].size()) {
    return false;
  }
  output = fixture.reasons[pass][index];
  return true;
}

bool ReadRansom(void *context, const Player &player, const Row &prisoner,
                Ransom &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.ransom_calls;
  if (fixture.ransom_calls == fixture.fail_ransom_call) return false;
  const auto pass = fixture.active_pass;
  const auto index = fixture.FindRow(pass, prisoner.prisoner_character_id);
  if (player.character_id != 101 || index == fixture.rows[pass].size()) {
    return false;
  }
  output = fixture.ransoms[pass][index];
  return true;
}

bool ReadPreview(void *context, const Player &player, const Row &prisoner,
                 PreviewKind kind, Preview &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.preview_calls;
  if (fixture.preview_calls == fixture.fail_preview_call) return false;
  const auto pass = fixture.active_pass;
  const auto index = fixture.FindRow(pass, prisoner.prisoner_character_id);
  const auto kind_index = static_cast<std::size_t>(kind);
  if (player.character_id != 101 || index == fixture.rows[pass].size() ||
      kind_index >= fixture.previews[pass][index].size()) {
    return false;
  }
  output = fixture.previews[pass][index][kind_index];
  return true;
}

Access MakeAccess(Fixture &fixture) {
  Access access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 =
      bridge::kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
  access.current_thread_id = 77;
  access.application_main_thread_id = 77;
  access.context = &fixture;
  access.capture_frame = &CaptureFrame;
  access.resolve_player = &ResolvePlayer;
  access.resolve_collector = &ResolveCollector;
  access.read_prisoner = &ReadPrisoner;
  access.read_native_reasons = &ReadReasons;
  access.read_ransom_preview = &ReadRansom;
  access.read_interaction_preview = &ReadPreview;
  return access;
}

void ExpectFailure(Access access, Failure failure,
                   CoreFailure core_failure) {
  Result result{};
  result.snapshot.status = bridge::PlayerPrisonerSnapshotStatusV1::available;
  result.snapshot.prisoner_count = 1;
  assert(!bridge::ObservePlayerPrisonerManagementSourceV1(access, result));
  assert(result.failure == failure);
  assert(result.core_failure == core_failure);
  assert(result.snapshot.status ==
         bridge::PlayerPrisonerSnapshotStatusV1::unavailable);
  assert(result.snapshot.prisoner_count == 0);
  assert(!bridge::PlayerPrisonerSourceAdapterFailureNameV1(failure).empty());
}

void TestStableCollectorPublishesActionableP0Ransom() {
  Fixture fixture{};
  Result result{};
  assert(bridge::ObservePlayerPrisonerManagementSourceV1(
      MakeAccess(fixture), result));
  assert(result.failure == Failure::none);
  assert(result.core_failure == CoreFailure::none);
  assert(result.snapshot.status ==
         bridge::PlayerPrisonerSnapshotStatusV1::available);
  assert(result.snapshot.played_character_id == 101);
  assert(result.snapshot.prisoner_count == 2);
  assert(result.snapshot.prisoners[0].prisoner_character_id == 501);
  assert(result.snapshot.prisoners[0].ransom.interaction.can_send);
  assert(result.snapshot.prisoners[0].ransom.would_accept_now.value);
  assert(bridge::PlayerPrisonerKeyViewV1(
             result.snapshot.prisoners[0].ransom.resource_key.value) ==
         "gold");
  assert(result.snapshot.readiness.ransom_candidate_available);
  assert(result.snapshot.readiness.semantic_ready);
  assert(!result.snapshot.religious_details_exposed);
  assert(fixture.frame_calls == 2);
  assert(fixture.player_calls == 2);
  assert(fixture.collector_calls == 2);
  assert(fixture.prisoner_calls == 4);
  assert(fixture.reason_calls == 4);
  assert(fixture.ransom_calls == 4);
  assert(fixture.preview_calls == 20);

  fixture.ransoms[0][1].resource_key =
      bridge::PlayerPrisonerKnownKeyV1("destroyed");
  assert(bridge::PlayerPrisonerKeyViewV1(
             result.snapshot.prisoners[0].ransom.resource_key.value) ==
         "gold");
}

void TestAdmissionCallbackAndThreadGatesPrecedeReads() {
  Fixture fixture{};
  auto access = MakeAccess(fixture);
  access.admitted_executable_sha256 = "wrong";
  ExpectFailure(access, Failure::exact_build_mismatch,
                CoreFailure::exact_build_mismatch);
  assert(fixture.frame_calls == 0);

  fixture = Fixture{};
  access = MakeAccess(fixture);
  access.read_ransom_preview = nullptr;
  ExpectFailure(access, Failure::callbacks_unavailable,
                CoreFailure::source_adapter_unavailable);
  assert(fixture.frame_calls == 0);

  fixture = Fixture{};
  access = MakeAccess(fixture);
  access.current_thread_id = 78;
  ExpectFailure(access, Failure::application_main_thread_required,
                CoreFailure::application_main_thread_required);
  assert(fixture.frame_calls == 0);
}

void TestCollectorCompletenessAndCountFailClosed() {
  Fixture fixture{};
  fixture.collectors[0].complete = false;
  ExpectFailure(MakeAccess(fixture), Failure::collector_incomplete,
                CoreFailure::prisoner_collection_incomplete);
  assert(fixture.prisoner_calls == 0);

  fixture = Fixture{};
  fixture.collectors[0].total_count = 3;
  ExpectFailure(MakeAccess(fixture), Failure::collector_count_invalid,
                CoreFailure::prisoner_count_invalid);
  assert(fixture.prisoner_calls == 0);

  fixture = Fixture{};
  fixture.collectors[0].row_count = static_cast<std::uint32_t>(
      bridge::kPlayerPrisonerMaximumRowsV1 + 1);
  fixture.collectors[0].total_count = fixture.collectors[0].row_count;
  ExpectFailure(MakeAccess(fixture), Failure::collector_count_invalid,
                CoreFailure::prisoner_count_invalid);
  assert(fixture.prisoner_calls == 0);
}

void TestPlayerAndCollectorIdentityLifecycleDriftFailClosed() {
  Fixture fixture{};
  fixture.players[1].identity++;
  ExpectFailure(MakeAccess(fixture), Failure::player_identity_drift,
                CoreFailure::player_identity_mismatch);

  fixture = Fixture{};
  fixture.players[1].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::player_lifecycle_drift,
                CoreFailure::player_identity_mismatch);

  fixture = Fixture{};
  fixture.collectors[1].identity++;
  ExpectFailure(MakeAccess(fixture), Failure::collector_identity_drift,
                CoreFailure::source_sample_drift);

  fixture = Fixture{};
  fixture.collectors[1].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::collector_lifecycle_drift,
                CoreFailure::source_sample_drift);
}

void TestPrisonerIdentityLifecycleDriftFailClosed() {
  Fixture fixture{};
  fixture.rows[1][0].identity++;
  ExpectFailure(MakeAccess(fixture), Failure::prisoner_identity_drift,
                CoreFailure::source_sample_drift);

  fixture = Fixture{};
  fixture.rows[1][0].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::prisoner_lifecycle_drift,
                CoreFailure::source_sample_drift);

  fixture = Fixture{};
  fixture.rows[0][0].jailer_character_id = 999;
  ExpectFailure(MakeAccess(fixture), Failure::prisoner_identity_invalid,
                CoreFailure::prisoner_identity_invalid);
}

void TestCollectorAndEvaluatorReadFailuresStayTyped() {
  Fixture fixture{};
  fixture.fail_prisoner_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::prisoner_unavailable,
                CoreFailure::source_adapter_unavailable);

  fixture = Fixture{};
  fixture.fail_reason_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::native_reason_unavailable,
                CoreFailure::source_adapter_unavailable);

  fixture = Fixture{};
  fixture.fail_ransom_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::ransom_preview_unavailable,
                CoreFailure::source_adapter_unavailable);

  fixture = Fixture{};
  fixture.fail_preview_call = 1;
  ExpectFailure(MakeAccess(fixture),
                Failure::interaction_preview_unavailable,
                CoreFailure::source_adapter_unavailable);
}

void TestSampleAndFrameDriftFailClosed() {
  Fixture fixture{};
  fixture.ransoms[1][1].resource_amount_raw++;
  ExpectFailure(MakeAccess(fixture), Failure::source_sample_drift,
                CoreFailure::source_sample_drift);

  fixture = Fixture{};
  fixture.frames[1].native_revision++;
  ExpectFailure(MakeAccess(fixture), Failure::frame_drift,
                CoreFailure::frame_drift);

  fixture = Fixture{};
  fixture.frames[0].paused = false;
  ExpectFailure(MakeAccess(fixture), Failure::not_paused,
                CoreFailure::not_paused);
  assert(fixture.player_calls == 0);
}

void TestNativeFinalSourcesRemainOpaqueAndCoreValidated() {
  Fixture fixture{};
  fixture.reasons[0][0].has_execute_reason.source =
      bridge::PlayerPrisonerNativeReasonSourceV1::unknown;
  fixture.reasons[1][0] = fixture.reasons[0][0];
  ExpectFailure(MakeAccess(fixture), Failure::core_rejected,
                CoreFailure::native_reason_source_invalid);

  assert(bridge::kPlayerPrisonerManagementSourceAdapterV1PrivateKey ==
         "player_prisoner_management_source_adapter_v1");
  assert(bridge::kPlayerPrisonerManagementSourceAdapterV1EvidenceRevision ==
         "player_prisoner_management_snapshot_v1@e9652edd");
  assert(bridge::PlayerPrisonerSourceAdapterFailureNameV1(
             Failure::prisoner_lifecycle_drift) ==
         "prisoner_lifecycle_drift");
}

} // namespace

int main() {
  TestStableCollectorPublishesActionableP0Ransom();
  TestAdmissionCallbackAndThreadGatesPrecedeReads();
  TestCollectorCompletenessAndCountFailClosed();
  TestPlayerAndCollectorIdentityLifecycleDriftFailClosed();
  TestPrisonerIdentityLifecycleDriftFailClosed();
  TestCollectorAndEvaluatorReadFailuresStayTyped();
  TestSampleAndFrameDriftFailClosed();
  TestNativeFinalSourcesRemainOpaqueAndCoreValidated();
  std::cout << "player_prisoner_management_source_adapter_v1_test: 8/8 GREEN\n";
  return 0;
}

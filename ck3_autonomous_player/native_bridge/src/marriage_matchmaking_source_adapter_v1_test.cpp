#include "xar_bridge/marriage_matchmaking_source_adapter_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>

namespace {

namespace bridge = xar::bridge;

constexpr std::uint32_t kSubjectId = 0x01000002;
constexpr std::uint32_t kCandidateAId = 0x01000003;
constexpr std::uint32_t kRecipientId = 0x01000004;
constexpr std::uint32_t kCandidateBId = 0x01000005;
constexpr std::uintptr_t kModuleBase = 0x140000000ULL;

struct NativeRankedRow {
  std::uintptr_t opaque_owner = 0;
  std::int32_t character_id = -1;
  std::int32_t score = 0;
};

static_assert(sizeof(NativeRankedRow) == 16);

struct Fixture {
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::byte, 0x200> subject{};
  std::array<std::byte, 0x200> candidate_a{};
  std::array<std::byte, 0x200> recipient{};
  std::array<std::byte, 0x200> candidate_b{};
  std::array<std::byte, 0x300> living{};
  std::array<std::byte, 0x40> strategy{};
  std::array<std::byte, 0xF60> interaction_database{};
  std::array<std::byte, 8> interaction{};
  std::array<NativeRankedRow, 2> ranked_rows{};
  std::uintptr_t storage_slot = 0;

  std::uint32_t ranked_invoke_calls = 0;
  std::uint32_t ranked_view_calls = 0;
  std::uint32_t ranked_release_calls = 0;
  std::uint32_t redirect_calls = 0;
  std::uint32_t construct_calls = 0;
  std::uint32_t refresh_calls = 0;
  std::uint32_t finalize_calls = 0;
  std::uint32_t validate_calls = 0;
  std::uint32_t ai_accept_calls = 0;
  std::uint32_t outer_answer_calls = 0;
  std::uint32_t outcome_calls = 0;
  std::uint32_t destroy_calls = 0;
  std::uint32_t frame_calls = 0;

  bool strategy_available = true;
  bool drift_container = false;
  bool duplicate_candidate = false;
  bool invalid_redirect = false;
  bool drift_context_roles = false;
  bool drift_candidate_identity = false;
  bool can_send = true;
  bool acceptance_overflow = false;
  bool outcome_available = true;
  std::uint8_t answer_status_raw = 0;
};

struct Harness {
  bridge::MarriageMatchmakingSourceAdapterStateV1 state{};
  Fixture fixture{};
  bridge::MarriageMatchmakingFrameV1 before{};
  bridge::MarriageMatchmakingFrameV1 after{};
};

Fixture *g_fixture = nullptr;

template <typename Value, std::size_t Size>
void Put(std::array<std::byte, Size> &target, std::size_t offset,
         Value value) {
  assert(offset + sizeof(value) <= target.size());
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

template <typename Value>
void PutRaw(void *target, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte *>(target) + offset, &value,
              sizeof(value));
}

void SetCharacter(Fixture &fixture, std::array<std::byte, 0x200> &character,
                  std::uint32_t id, std::uint32_t slot_index) {
  Put(character, bridge::kMarriageCharacterIdOffsetV1,
      static_cast<std::int32_t>(id));
  const auto pointer = reinterpret_cast<std::uintptr_t>(character.data());
  Put(fixture.slots,
      slot_index * bridge::kMarriageCharacterStorageSlotStrideV1 +
          bridge::kMarriageCharacterStorageSlotObjectOffsetV1,
      pointer);
}

void CopySnapshotId(bridge::MarriageMatchmakingFrameV1 &frame,
                    const char *value) {
  const auto size = std::strlen(value);
  assert(size < frame.snapshot_id.size());
  std::memcpy(frame.snapshot_id.data(), value, size);
}

bool DirectMemory(void *, std::uintptr_t address, void *output,
                  std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

void *GetInteractionDatabase() {
  return g_fixture == nullptr ? nullptr
                              : g_fixture->interaction_database.data();
}

void RedirectRoles(void *, std::int32_t *actor, std::int32_t *recipient,
                   std::int32_t *secondary_actor,
                   std::int32_t *secondary_recipient,
                   std::int32_t *intermediary) {
  assert(g_fixture != nullptr && actor != nullptr && recipient != nullptr &&
         secondary_actor != nullptr && secondary_recipient != nullptr &&
         intermediary != nullptr);
  ++g_fixture->redirect_calls;
  *recipient = static_cast<std::int32_t>(kRecipientId);
  *intermediary = -1;
  if (g_fixture->invalid_redirect) {
    *secondary_recipient = static_cast<std::int32_t>(kRecipientId);
  }
}

void *ConstructContext(void *context, void *interaction,
                       std::int32_t actor, std::int32_t recipient,
                       std::int32_t secondary_actor,
                       std::int32_t secondary_recipient,
                       std::int32_t intermediary, void *) {
  assert(g_fixture != nullptr && context != nullptr &&
         interaction == g_fixture->interaction.data());
  ++g_fixture->construct_calls;
  PutRaw(context, 0, interaction);
  PutRaw(context, bridge::kMarriageContextActorIdOffsetV1, actor);
  PutRaw(context, bridge::kMarriageContextRecipientIdOffsetV1, recipient);
  PutRaw(context, bridge::kMarriageContextSecondaryActorIdOffsetV1,
         secondary_actor);
  PutRaw(context, bridge::kMarriageContextSecondaryRecipientIdOffsetV1,
         secondary_recipient);
  PutRaw(context, bridge::kMarriageContextIntermediaryIdOffsetV1,
         intermediary);
  return context;
}

void RefreshContext(void *, bool refresh) {
  assert(g_fixture != nullptr && refresh);
  ++g_fixture->refresh_calls;
}

void FinalizeContext(void *) {
  assert(g_fixture != nullptr);
  ++g_fixture->finalize_calls;
}

bool CompleteCanSend(void *, void *error_output) {
  assert(g_fixture != nullptr && error_output == nullptr);
  ++g_fixture->validate_calls;
  return g_fixture->can_send;
}

std::int64_t *RecipientAiAccept(void *, std::int64_t *output) {
  assert(g_fixture != nullptr && output != nullptr);
  ++g_fixture->ai_accept_calls;
  *output = g_fixture->acceptance_overflow
                ? static_cast<std::int64_t>(
                      (std::numeric_limits<std::int32_t>::max)()) +
                      1
                : 350'000;
  return output;
}

std::uint8_t OuterAnswer(void *context, std::uint8_t answer_mode,
                         std::uint8_t final_answer, void *error_sink_a,
                         void *error_sink_b) {
  assert(g_fixture != nullptr && context != nullptr && answer_mode == 1 &&
         final_answer == 1 && error_sink_a == nullptr &&
         error_sink_b == nullptr);
  ++g_fixture->outer_answer_calls;
  if (g_fixture->drift_context_roles) {
    PutRaw(context, bridge::kMarriageContextRecipientIdOffsetV1,
           static_cast<std::int32_t>(kCandidateAId));
  }
  if (g_fixture->drift_candidate_identity) {
    Put(g_fixture->candidate_a, bridge::kMarriageCharacterIdOffsetV1,
        static_cast<std::int32_t>(0x02000003));
  }
  return g_fixture->answer_status_raw;
}

void DestroyContext(void *) {
  assert(g_fixture != nullptr);
  ++g_fixture->destroy_calls;
}

bool InvokeRanked(
    void *context, const bridge::MarriageNativeRankedInvocationV1 &request,
    std::uintptr_t &container_token) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.ranked_invoke_calls;
  const auto expected_native =
      bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase);
  if (request.subject_character !=
          reinterpret_cast<std::uintptr_t>(fixture.subject.data()) ||
      request.strategy !=
          reinterpret_cast<std::uintptr_t>(fixture.strategy.data()) ||
      request.arrange_marriage_interaction !=
          reinterpret_cast<std::uintptr_t>(fixture.interaction.data()) ||
      request.limit != 8 || request.entry_points != expected_native) {
    return false;
  }
  if (fixture.duplicate_candidate) {
    fixture.ranked_rows[1].character_id =
        fixture.ranked_rows[0].character_id;
  }
  container_token = reinterpret_cast<std::uintptr_t>(&fixture.ranked_rows);
  return true;
}

bool ReadRankedView(
    void *context, std::uintptr_t container_token,
    bridge::MarriageNativeRankedContainerViewV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (container_token !=
      reinterpret_cast<std::uintptr_t>(&fixture.ranked_rows)) {
    return false;
  }
  ++fixture.ranked_view_calls;
  output.row_data =
      reinterpret_cast<std::uintptr_t>(fixture.ranked_rows.data());
  output.capacity = 2;
  output.count = fixture.drift_container && fixture.ranked_view_calls >= 2
                     ? 1
                     : 2;
  return true;
}

void ReleaseRanked(void *context, std::uintptr_t container_token) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  assert(container_token ==
         reinterpret_cast<std::uintptr_t>(&fixture.ranked_rows));
  ++fixture.ranked_release_calls;
}

bool ClassifyOutcome(void *context, std::uintptr_t subject_character,
                     std::uintptr_t candidate_character,
                     const void *finalized_context,
                     bridge::MarriagePredictedOutcomeV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.outcome_calls;
  if (!fixture.outcome_available ||
      subject_character !=
          reinterpret_cast<std::uintptr_t>(fixture.subject.data()) ||
      finalized_context == nullptr) {
    return false;
  }
  if (candidate_character ==
      reinterpret_cast<std::uintptr_t>(fixture.candidate_a.data())) {
    output = bridge::MarriagePredictedOutcomeV1::marriage;
    return true;
  }
  if (candidate_character ==
      reinterpret_cast<std::uintptr_t>(fixture.candidate_b.data())) {
    output = bridge::MarriagePredictedOutcomeV1::betrothal;
    return true;
  }
  return false;
}

void InitHarness(Harness &harness) {
  auto &fixture = harness.fixture;
  fixture.storage_slot =
      reinterpret_cast<std::uintptr_t>(fixture.storage.data());
  Put(fixture.storage, bridge::kMarriageCharacterStorageSlotsOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture.slots.data()));
  Put(fixture.storage, bridge::kMarriageCharacterStorageCapacityOffsetV1,
      std::int32_t{8});
  SetCharacter(fixture, fixture.subject, kSubjectId, 2);
  SetCharacter(fixture, fixture.candidate_a, kCandidateAId, 3);
  SetCharacter(fixture, fixture.recipient, kRecipientId, 4);
  SetCharacter(fixture, fixture.candidate_b, kCandidateBId, 5);
  Put(fixture.subject, bridge::kMarriageCharacterLivingDataOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture.living.data()));
  Put(fixture.living, bridge::kMarriageLivingDataStrategyOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture.strategy.data()));
  Put(fixture.strategy, bridge::kMarriageStrategySourceCharacterOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture.subject.data()));
  Put(fixture.strategy, bridge::kMarriageStrategyReadyOwnerOffsetV1,
      std::uintptr_t{0x11110000});
  Put(fixture.interaction_database,
      bridge::kArrangeMarriageInteractionOffsetV1,
      reinterpret_cast<std::uintptr_t>(fixture.interaction.data()));
  fixture.ranked_rows[0] = {0xAAAA, static_cast<std::int32_t>(kCandidateAId),
                            187'500};
  fixture.ranked_rows[1] = {0xBBBB, static_cast<std::int32_t>(kCandidateBId),
                            25'000};

  auto environment =
      bridge::BindMarriageMatchmakingSourceAdapterEnvironmentV1(
          kModuleBase, true,
          bridge::kMarriageMatchmakingSourceAdapterExecutableSha256V1);
  environment.offline_fixture = true;
  environment.character_storage_slot_address =
      reinterpret_cast<std::uintptr_t>(&fixture.storage_slot);
  environment.memory_context = &fixture;
  environment.read_memory = &DirectMemory;
  environment.ranked_context = &fixture;
  environment.invoke_ranked_source = &InvokeRanked;
  environment.read_ranked_container_view = &ReadRankedView;
  environment.release_ranked_container = &ReleaseRanked;
  environment.outcome_context = &fixture;
  environment.classify_outcome = &ClassifyOutcome;
  environment.get_character_interaction_database = &GetInteractionDatabase;
  environment.redirect_roles = &RedirectRoles;
  environment.construct_context = &ConstructContext;
  environment.refresh_context = &RefreshContext;
  environment.finalize_context = &FinalizeContext;
  environment.complete_can_send = &CompleteCanSend;
  environment.recipient_ai_accept = &RecipientAiAccept;
  environment.outer_answer = &OuterAnswer;
  environment.destroy_context = &DestroyContext;
  harness.state.environment = environment;

  CopySnapshotId(harness.before, "marriage3-fixture-001");
  harness.before.public_revision = 801;
  harness.before.native_revision = 9801;
  harness.before.proof_epoch = 31;
  harness.before.date_raw = 54'700'000;
  harness.before.paused = true;
  harness.before.map_ready = true;
  harness.before.has_played_character = true;
  harness.before.played_character_alive = true;
  harness.before.played_character_id = kSubjectId;
  harness.before.played_character_identity_round_trip = true;
  harness.after = harness.before;
}

bool CaptureFrame(void *context,
                  bridge::MarriageMatchmakingFrameV1 &output) noexcept {
  auto &harness = *static_cast<Harness *>(context);
  output = harness.fixture.frame_calls++ == 0 ? harness.before : harness.after;
  return true;
}

bool IsMainThread(void *) noexcept { return true; }

bridge::MarriageMatchmakingObserverRequestV1 Request() {
  bridge::MarriageMatchmakingObserverRequestV1 request{};
  request.expected_snapshot_id = "marriage3-fixture-001";
  request.expected_public_revision = 801;
  request.expected_native_revision = 9801;
  request.expected_date_raw = 54'700'000;
  request.subject_character_id = kSubjectId;
  request.matchmaker_character_id = kSubjectId;
  request.limit = 8;
  return request;
}

bridge::MarriageMatchmakingObserverEnvironmentV1 ObserverEnvironment() {
  bridge::MarriageMatchmakingObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      bridge::kMarriageMatchmakingObserverExecutableSha256V1;
  environment.module_base = kModuleBase;
  environment.offline_fixture = true;
  environment.native =
      bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase);
  return environment;
}

bridge::MarriageMatchmakingObserverAccessV1 ObserverAccess(Harness &harness) {
  bridge::MarriageMatchmakingObserverAccessV1 access{};
  access.context = &harness;
  access.capture_frame = &CaptureFrame;
  access.is_main_thread = &IsMainThread;
  access.read_ranked_candidates =
      &bridge::ReadMarriageRankedCandidatesFromSourceAdapterV1;
  access.evaluate_candidate =
      &bridge::EvaluateMarriageCandidateFromSourceAdapterV1;
  return access;
}

void TestExactBuildBinding() {
  const auto environment =
      bridge::BindMarriageMatchmakingSourceAdapterEnvironmentV1(
          kModuleBase, true,
          bridge::kMarriageMatchmakingSourceAdapterExecutableSha256V1);
  assert(environment.character_storage_slot_address == 0x14570C130ULL);
  assert(reinterpret_cast<std::uintptr_t>(
             environment.get_character_interaction_database) ==
         0x140831890ULL);
  assert(reinterpret_cast<std::uintptr_t>(environment.redirect_roles) ==
         0x142C3C4C0ULL);
  assert(reinterpret_cast<std::uintptr_t>(environment.construct_context) ==
         0x142C3F000ULL);
  assert(reinterpret_cast<std::uintptr_t>(environment.complete_can_send) ==
         0x142C43F00ULL);
  assert(reinterpret_cast<std::uintptr_t>(environment.recipient_ai_accept) ==
         0x142C44320ULL);
  assert(reinterpret_cast<std::uintptr_t>(environment.outer_answer) ==
         0x142C43B40ULL);
}

void TestRankedSourceAdapter() {
  Harness harness{};
  InitHarness(harness);
  g_fixture = &harness.fixture;
  std::array<bridge::MarriageMatchmakingRankedRowV1,
             bridge::kMarriageMatchmakingMaximumCandidatesV1>
      output{};
  std::uint32_t count = 0;
  assert(bridge::ReadMarriageRankedCandidatesFromSourceAdapterV1(
             &harness.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, 8, output, count) ==
         bridge::MarriageNativeSourceResultV1::available);
  assert(count == 2 && output[0].candidate_character_id == kCandidateAId &&
         output[0].native_candidate_score == 187'500 &&
         output[1].candidate_character_id == kCandidateBId &&
         output[1].native_candidate_score == 25'000);
  assert(harness.fixture.ranked_invoke_calls == 1 &&
         harness.fixture.ranked_view_calls == 3 &&
         harness.fixture.ranked_release_calls == 1);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             harness.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::none);
}

void TestPairEvaluationAdapter() {
  Harness harness{};
  InitHarness(harness);
  g_fixture = &harness.fixture;
  bridge::MarriageMatchmakingPairEvaluationV1 output{};
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &harness.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::available);
  assert(output.roles.actor_character_id == kSubjectId &&
         output.roles.recipient_character_id == kRecipientId &&
         output.roles.secondary_actor_character_id == kSubjectId &&
         output.roles.secondary_recipient_character_id == kCandidateAId &&
         output.roles.intermediary_character_id == 0);
  assert(output.complete_can_send &&
         output.complete_can_send_status_raw == 1 &&
         output.recipient_ai_accept_raw == 350'000 &&
         output.recipient_answer_status_raw == 0 &&
         output.recipient_answer_allows_send &&
         output.predicted_outcome ==
             bridge::MarriagePredictedOutcomeV1::marriage);
  assert(harness.fixture.redirect_calls == 1 &&
         harness.fixture.construct_calls == 1 &&
         harness.fixture.refresh_calls == 1 &&
         harness.fixture.finalize_calls == 1 &&
         harness.fixture.validate_calls == 1 &&
         harness.fixture.ai_accept_calls == 1 &&
         harness.fixture.outer_answer_calls == 1 &&
         harness.fixture.outcome_calls == 1 &&
         harness.fixture.destroy_calls == 1);
  harness.fixture.answer_status_raw = 2;
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &harness.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::available);
  assert(output.recipient_answer_status_raw == 2 &&
         !output.recipient_answer_allows_send);
  harness.fixture.answer_status_raw = 3;
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &harness.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             harness.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             outer_answer_unavailable);
}

void TestFeedsMarriage2SemanticObserver() {
  Harness harness{};
  InitHarness(harness);
  g_fixture = &harness.fixture;
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(bridge::ReadMarriageMatchmakingObserverV1(
      ObserverEnvironment(), ObserverAccess(harness), Request(), output));
  assert(output.candidate_count == 2);
  assert(output.candidates[0].candidate_character_id == kCandidateAId &&
         output.candidates[0].native_candidate_score == 187'500 &&
         output.candidates[0].evaluation.complete_can_send &&
         output.candidates[0].evaluation.recipient_ai_accept_raw == 350'000 &&
         output.candidates[0].evaluation.roles.recipient_character_id ==
             kRecipientId);
  assert(output.candidates[1].candidate_character_id == kCandidateBId &&
         output.candidates[1].evaluation.predicted_outcome ==
             bridge::MarriagePredictedOutcomeV1::betrothal);
  assert(harness.fixture.ranked_invoke_calls == 2 &&
         harness.fixture.ranked_release_calls == 2 &&
         harness.fixture.destroy_calls == 4);
  const auto json = bridge::SerializeMarriageMatchmakingObservationV1(output);
  assert(json.find("\"native_candidate_score\":187500") !=
         std::string::npos);
  assert(json.find("\"recipient_character_id\":16777220") !=
         std::string::npos);
  assert(json.find("\"religion_projection\":"
                   "\"native_final_results_only\"") != std::string::npos);
  assert(json.find("faith") == std::string::npos &&
         json.find("doctrine") == std::string::npos &&
         json.find("tenet") == std::string::npos &&
         json.find("fervor") == std::string::npos);
}

void TestUnavailableStrategyAndContainerRed() {
  Harness strategy{};
  InitHarness(strategy);
  g_fixture = &strategy.fixture;
  Put(strategy.fixture.strategy,
      bridge::kMarriageStrategyReadyOwnerOffsetV1, std::uintptr_t{0});
  std::array<bridge::MarriageMatchmakingRankedRowV1,
             bridge::kMarriageMatchmakingMaximumCandidatesV1>
      output{};
  std::uint32_t count = 0;
  assert(bridge::ReadMarriageRankedCandidatesFromSourceAdapterV1(
             &strategy.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, 8, output, count) ==
         bridge::MarriageNativeSourceResultV1::ranked_source_unavailable);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             strategy.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             strategy_unavailable);

  Harness drift{};
  InitHarness(drift);
  g_fixture = &drift.fixture;
  drift.fixture.drift_container = true;
  assert(bridge::ReadMarriageRankedCandidatesFromSourceAdapterV1(
             &drift.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, 8, output, count) ==
         bridge::MarriageNativeSourceResultV1::failed);
  assert(count == 0 && drift.fixture.ranked_release_calls == 1);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(drift.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             ranked_container_drift);
}

void TestIdentityAndPairRed() {
  Harness duplicate{};
  InitHarness(duplicate);
  g_fixture = &duplicate.fixture;
  duplicate.fixture.duplicate_candidate = true;
  std::array<bridge::MarriageMatchmakingRankedRowV1,
             bridge::kMarriageMatchmakingMaximumCandidatesV1>
      rows{};
  std::uint32_t count = 0;
  assert(bridge::ReadMarriageRankedCandidatesFromSourceAdapterV1(
             &duplicate.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, 8, rows, count) ==
         bridge::MarriageNativeSourceResultV1::failed);
  assert(count == 0 && duplicate.fixture.ranked_release_calls == 1);

  Harness roles{};
  InitHarness(roles);
  g_fixture = &roles.fixture;
  roles.fixture.invalid_redirect = true;
  bridge::MarriageMatchmakingPairEvaluationV1 output{};
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &roles.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(roles.fixture.construct_calls == 0 &&
         roles.fixture.destroy_calls == 0);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(roles.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             context_roles_invalid);

  Harness drift{};
  InitHarness(drift);
  g_fixture = &drift.fixture;
  drift.fixture.drift_context_roles = true;
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &drift.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(drift.fixture.destroy_calls == 1);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(drift.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             context_roles_drift);

  Harness identity{};
  InitHarness(identity);
  g_fixture = &identity.fixture;
  identity.fixture.drift_candidate_identity = true;
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &identity.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(identity.fixture.destroy_calls == 1);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             identity.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             post_evaluation_identity_drift);
}

void TestAcceptanceAndAdmissionRed() {
  Harness overflow{};
  InitHarness(overflow);
  g_fixture = &overflow.fixture;
  overflow.fixture.acceptance_overflow = true;
  bridge::MarriageMatchmakingPairEvaluationV1 output{};
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &overflow.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(overflow.fixture.destroy_calls == 1);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             overflow.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             acceptance_score_overflow);

  Harness admission{};
  InitHarness(admission);
  g_fixture = &admission.fixture;
  admission.state.environment.admitted_executable_sha256 = "wrong";
  assert(bridge::EvaluateMarriageCandidateFromSourceAdapterV1(
             &admission.state,
             bridge::BindMarriageMatchmakingNativeEntryPointsV1(kModuleBase),
             kSubjectId, kSubjectId, kCandidateAId, output) ==
         bridge::MarriageNativeEvaluationResultV1::failed);
  assert(bridge::ReadMarriageMatchmakingSourceAdapterFailureV1(
             admission.state) ==
         bridge::MarriageMatchmakingSourceAdapterFailureV1::
             exact_build_not_admitted);
}

} // namespace

int main() {
  TestExactBuildBinding();
  TestRankedSourceAdapter();
  TestPairEvaluationAdapter();
  TestFeedsMarriage2SemanticObserver();
  TestUnavailableStrategyAndContainerRed();
  TestIdentityAndPairRed();
  TestAcceptanceAndAdmissionRed();
  std::cout << "GREEN: marriage-matchmaking-source-adapter-v1 fixture\n";
  return 0;
}

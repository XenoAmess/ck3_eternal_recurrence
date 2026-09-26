#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;

namespace {

constexpr std::uint32_t kSubjectId = 0x01000001U;
constexpr std::uint32_t kCandidateId = 0x02000002U;
constexpr std::uint32_t kRecipientId = 0x03000003U;
constexpr std::uint32_t kPlayedId = 0x04000004U;
constexpr std::uintptr_t kPrimaryVtable = 0x1111222233334444ULL;
constexpr std::uintptr_t kSecondaryVtable = 0x5555666677778888ULL;

template <typename Value, std::size_t Size>
void Write(std::array<std::byte, Size> &bytes, std::size_t offset,
           Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

template <typename Value>
void WriteAddress(void *base, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}

struct Harness {
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 0x100> slots{};
  std::array<std::byte, 0x200> subject{};
  std::array<std::byte, 0x200> candidate{};
  std::array<std::byte, 0x200> recipient{};
  std::array<std::byte, 0x200> played{};
  std::array<std::byte, 0x50> subject_family{};
  std::array<std::byte, 0x50> candidate_family{};
  std::array<std::byte, 0x1000> database{};
  std::array<std::byte, 0x20> interaction{};
  std::array<std::int32_t, 1> subject_spouses{};
  std::array<std::int32_t, 1> candidate_spouses{};
  std::uintptr_t storage_pointer = 0;
  bool validate = true;
  bool submit = true;
  bool alliance = true;
  bool alliance_reverse = true;
  bridge::MarriageProposalNativeResolutionV1 resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  bridge::MarriageProposalReceiptFrameV1 frame{};
  int redirect_calls = 0;
  int construct_calls = 0;
  int refresh_calls = 0;
  int finalize_calls = 0;
  int validate_calls = 0;
  int command_calls = 0;
  int submit_calls = 0;
  int destroy_calls = 0;
  std::uint32_t submit_flags = 0;
  std::int64_t ai_accept_raw = 100000;
  std::uint8_t answer_raw = 1;

  Harness() {
    storage_pointer = reinterpret_cast<std::uintptr_t>(storage.data());
    Write(storage, bridge::kMarriageCharacterStorageSlotsOffsetV1,
          reinterpret_cast<std::uintptr_t>(slots.data()));
    Write(storage, bridge::kMarriageCharacterStorageCapacityOffsetV1,
          std::int32_t{8});
    InstallCharacter(kSubjectId, subject, subject_family);
    InstallCharacter(kCandidateId, candidate, candidate_family);
    InstallCharacter(kRecipientId, recipient, NoFamily());
    InstallCharacter(kPlayedId, played, NoFamily());
    Write(database, bridge::kArrangeMarriageInteractionOffsetV1,
          reinterpret_cast<std::uintptr_t>(interaction.data()));
    subject_spouses[0] = static_cast<std::int32_t>(kCandidateId);
    candidate_spouses[0] = static_cast<std::int32_t>(kSubjectId);
    InstallMarriage(subject_family, candidate_family);
    frame.available = true;
    frame.paused = true;
    std::memcpy(frame.snapshot_id.data(), "fixture-marriage-frame", 23);
    frame.public_revision = 10;
    frame.native_revision = 20;
    frame.proof_epoch = 30;
    frame.date_raw = 40;
  }

  static std::array<std::byte, 0x50> &NoFamily() {
    static std::array<std::byte, 0x50> empty{};
    return empty;
  }

  template <std::size_t CharacterSize, std::size_t FamilySize>
  void InstallCharacter(std::uint32_t id,
                        std::array<std::byte, CharacterSize> &character,
                        std::array<std::byte, FamilySize> &family) {
    const auto index = id & 0x00FFFFFFU;
    WriteAddress(slots.data(),
                 index * bridge::kMarriageCharacterStorageSlotStrideV1 +
                     bridge::kMarriageCharacterStorageSlotObjectOffsetV1,
                 reinterpret_cast<std::uintptr_t>(character.data()));
    Write(character, bridge::kMarriageCharacterIdOffsetV1,
          static_cast<std::int32_t>(id));
    Write(character, bridge::kMarriageCharacterDeathDataOffsetV1,
          std::uintptr_t{0});
    Write(character, bridge::kMarriageCharacterFamilyDataOffsetV1,
          &family == &NoFamily()
              ? std::uintptr_t{0}
              : reinterpret_cast<std::uintptr_t>(family.data()));
  }

  void InstallMarriage(std::array<std::byte, 0x50> &subject_data,
                       std::array<std::byte, 0x50> &candidate_data) {
    Write(subject_data, bridge::kMarriageFamilyBetrothedIdOffsetV1,
          std::int32_t{-1});
    Write(candidate_data, bridge::kMarriageFamilyBetrothedIdOffsetV1,
          std::int32_t{-1});
    Write(subject_data, bridge::kMarriageFamilyPrimarySpouseIdOffsetV1,
          static_cast<std::int32_t>(kCandidateId));
    Write(candidate_data, bridge::kMarriageFamilyPrimarySpouseIdOffsetV1,
          static_cast<std::int32_t>(kSubjectId));
    InstallSpouseArray(subject_data, subject_spouses.data());
    InstallSpouseArray(candidate_data, candidate_spouses.data());
  }

  void InstallSpouseArray(std::array<std::byte, 0x50> &family,
                          std::int32_t *data) {
    Write(family, bridge::kMarriageFamilySpouseIdsOffsetV1 +
                      bridge::kMarriageNativeArrayDataOffsetV1,
          reinterpret_cast<std::uintptr_t>(data));
    Write(family, bridge::kMarriageFamilySpouseIdsOffsetV1 +
                      bridge::kMarriageNativeArrayCapacityOffsetV1,
          std::int32_t{1});
    Write(family, bridge::kMarriageFamilySpouseIdsOffsetV1 +
                      bridge::kMarriageNativeArrayCountOffsetV1,
          std::int32_t{1});
  }
};

Harness *g_harness = nullptr;

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool ReadZeroMemory(void *, std::uintptr_t, void *output,
                    std::size_t size) noexcept {
  if (output == nullptr || size == 0) return false;
  std::memset(output, 0, size);
  return true;
}

void *GetDatabase() { return g_harness->database.data(); }

void Redirect(void *, std::int32_t *, std::int32_t *recipient,
              std::int32_t *, std::int32_t *, std::int32_t *) {
  ++g_harness->redirect_calls;
  *recipient = static_cast<std::int32_t>(kRecipientId);
}

void *ConstructContext(void *context, void *, std::int32_t actor,
                       std::int32_t recipient, std::int32_t secondary_actor,
                       std::int32_t secondary_recipient,
                       std::int32_t intermediary, void *) {
  ++g_harness->construct_calls;
  WriteAddress(context, bridge::kMarriageContextActorIdOffsetV1, actor);
  WriteAddress(context, bridge::kMarriageContextRecipientIdOffsetV1,
               recipient);
  WriteAddress(context, bridge::kMarriageContextSecondaryActorIdOffsetV1,
               secondary_actor);
  WriteAddress(context,
               bridge::kMarriageContextSecondaryRecipientIdOffsetV1,
               secondary_recipient);
  WriteAddress(context, bridge::kMarriageContextIntermediaryIdOffsetV1,
               intermediary);
  return context;
}

void Refresh(void *, bool refresh) {
  assert(refresh);
  ++g_harness->refresh_calls;
}
void Finalize(void *) { ++g_harness->finalize_calls; }
bool Validate(void *, void *) {
  ++g_harness->validate_calls;
  return g_harness->validate;
}
std::int64_t *AiAccept(void *, std::int64_t *output) {
  *output = g_harness->ai_accept_raw;
  return output;
}
std::uint8_t OuterAnswer(void *, std::uint8_t, std::uint8_t, void *, void *) {
  return g_harness->answer_raw;
}
void Destroy(void *) { ++g_harness->destroy_calls; }

void *ConstructCommand(void *command, const void *context) {
  ++g_harness->command_calls;
  WriteAddress(command, 0, kPrimaryVtable);
  WriteAddress(command, 0x18, kSecondaryVtable);
  std::memcpy(static_cast<std::byte *>(command) +
                  bridge::kMarriageSendInteractionContextOffsetV1,
              context, bridge::kMarriageInteractionContextSizeV1);
  return command;
}

bool Submit(void *manager, void *, std::uint32_t flags) {
  assert(manager == g_harness);
  ++g_harness->submit_calls;
  g_harness->submit_flags = flags;
  return g_harness->submit;
}

bool InvokeRanked(void *, const bridge::MarriageNativeRankedInvocationV1 &,
                  std::uintptr_t &token) noexcept {
  token = 1;
  return true;
}
bool ReadRanked(void *, std::uintptr_t,
                bridge::MarriageNativeRankedContainerViewV1 &) noexcept {
  return true;
}
void ReleaseRanked(void *, std::uintptr_t) noexcept {}
bool Classify(void *, std::uintptr_t, std::uintptr_t, const void *,
              bridge::MarriagePredictedOutcomeV1 &output) noexcept {
  output = bridge::MarriagePredictedOutcomeV1::marriage;
  return true;
}
bool CaptureFrame(void *, bridge::MarriageProposalReceiptFrameV1 &output) noexcept {
  output = g_harness->frame;
  return true;
}
bool ReadAlliance(void *, std::uintptr_t subject, std::uintptr_t candidate,
                  bool &subject_has, bool &candidate_has) noexcept {
  assert((subject == reinterpret_cast<std::uintptr_t>(g_harness->subject.data()) &&
          candidate == reinterpret_cast<std::uintptr_t>(g_harness->candidate.data())) ||
         (subject == reinterpret_cast<std::uintptr_t>(g_harness->played.data()) &&
          candidate == reinterpret_cast<std::uintptr_t>(g_harness->recipient.data())));
  subject_has = g_harness->alliance;
  candidate_has = g_harness->alliance_reverse;
  return true;
}
bool ReadResolution(void *, std::uint32_t subject, std::uint32_t candidate,
                    bridge::MarriageProposalNativeResolutionV1 &output) noexcept {
  assert(subject == kSubjectId && candidate == kCandidateId);
  output = g_harness->resolution;
  return true;
}

void InitializeState(Harness &harness,
                     bridge::MarriageProposalNativeBinderStateV1 &state) {
  g_harness = &harness;
  auto &env = state.environment;
  env.module_base = 1;
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.offline_fixture = true;
  env.source_adapter.exact_build_admitted = true;
  env.source_adapter.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.source_adapter.offline_fixture = true;
  env.source_adapter.module_base = 1;
  env.source_adapter.character_storage_slot_address =
      reinterpret_cast<std::uintptr_t>(&harness.storage_pointer);
  env.source_adapter.read_memory = &ReadMemory;
  env.source_adapter.invoke_ranked_source = &InvokeRanked;
  env.source_adapter.read_ranked_container_view = &ReadRanked;
  env.source_adapter.release_ranked_container = &ReleaseRanked;
  env.source_adapter.classify_outcome = &Classify;
  env.source_adapter.get_character_interaction_database = &GetDatabase;
  env.source_adapter.redirect_roles = &Redirect;
  env.source_adapter.construct_context = &ConstructContext;
  env.source_adapter.refresh_context = &Refresh;
  env.source_adapter.finalize_context = &Finalize;
  env.source_adapter.complete_can_send = &Validate;
  env.source_adapter.recipient_ai_accept = &AiAccept;
  env.source_adapter.outer_answer = &OuterAnswer;
  env.source_adapter.destroy_context = &Destroy;
  env.command_manager = &harness;
  env.submit_command = &Submit;
  env.construct_send_command = &ConstructCommand;
  env.send_command_primary_vtable = kPrimaryVtable;
  env.send_command_secondary_vtable = kSecondaryVtable;
  env.ranked_container_lifecycle_certified = true;
  env.outcome_classifier_certified = true;
  env.capture_receipt_frame = &CaptureFrame;
  env.alliance_readback_certified = true;
  env.read_alliance_pair = &ReadAlliance;
  env.proposal_resolution_certified = true;
  env.read_proposal_resolution = &ReadResolution;
  state.last_failure.store(static_cast<std::uint32_t>(
      bridge::MarriageProposalNativeBinderFailureV1::none));
}

bridge::MarriageProposalSubmissionV1 Submission() {
  bridge::MarriageProposalSubmissionV1 output{};
  output.subject_character_id = kSubjectId;
  output.candidate_character_id = kCandidateId;
  output.native_rank = 1;
  output.native_candidate_score = 200;
  output.roles.actor_character_id = kSubjectId;
  output.roles.recipient_character_id = kRecipientId;
  output.roles.secondary_actor_character_id = kSubjectId;
  output.roles.secondary_recipient_character_id = kCandidateId;
  output.predicted_outcome = bridge::MarriagePredictedOutcomeV1::marriage;
  return output;
}

void TestBindAndCertifiedConfiguration() {
  const auto bound = bridge::BindMarriageProposalNativeBinderEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  assert(reinterpret_cast<std::uintptr_t>(bound.command_manager) ==
         0x10000000U + bridge::kMarriageCommandManagerRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(bound.submit_command) ==
         0x10000000U + bridge::kMarriageSubmitCommandRvaV1);
  assert(reinterpret_cast<std::uintptr_t>(bound.construct_send_command) ==
         0x10000000U +
             bridge::kMarriageConstructSendInteractionCommandRvaV1);

  Harness harness{};
  bridge::MarriageProposalNativeBinderStateV1 state{};
  InitializeState(harness, state);
  bridge::MarriageMatchmakingSourceAdapterStateV1 source{};
  assert(bridge::ConfigureMarriageMatchmakingSourceAdapterFromNativeBinderV1(
             state, source) ==
         bridge::MarriageProposalNativeBindResultV1::available);
  state.environment.ranked_container_lifecycle_certified = false;
  assert(bridge::ConfigureMarriageMatchmakingSourceAdapterFromNativeBinderV1(
             state, source) ==
         bridge::MarriageProposalNativeBindResultV1::blocked);
  assert(bridge::ReadMarriageProposalNativeBinderFailureV1(state) ==
         bridge::MarriageProposalNativeBinderFailureV1::
             ranked_container_lifecycle_not_certified);
  state.environment.ranked_container_lifecycle_certified = true;

  bridge::MarriageProposalActionEnvironmentV1 action{};
  bridge::SubmitMarriageProposalNativeV1 callback = nullptr;
  void *context = nullptr;
  assert(bridge::ConfigureMarriageProposalActionSubmitFromNativeBinderV1(
             state, action, callback, context) ==
         bridge::MarriageProposalNativeBindResultV1::available);
  assert(action.offline_fixture_submit && action.module_base == 0 &&
         callback == &bridge::SubmitMarriageProposalFromNativeBinderV1 &&
         context == &state);
}

void TestSingleSubmitAndNativeFinalValidation() {
  Harness harness{};
  bridge::MarriageProposalNativeBinderStateV1 state{};
  InitializeState(harness, state);
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &state, Submission()) ==
         bridge::MarriageProposalNativeSubmitResultV1::submitted);
  assert(harness.redirect_calls == 1 && harness.construct_calls == 1 &&
         harness.refresh_calls == 1 && harness.finalize_calls == 1 &&
         harness.validate_calls == 1 && harness.command_calls == 1 &&
         harness.submit_calls == 1 && harness.destroy_calls == 2 &&
         harness.submit_flags == bridge::kMarriageSendInteractionFlagsV1);

  Harness rejected{};
  rejected.validate = false;
  bridge::MarriageProposalNativeBinderStateV1 rejected_state{};
  InitializeState(rejected, rejected_state);
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &rejected_state, Submission()) ==
         bridge::MarriageProposalNativeSubmitResultV1::rejected);
  assert(rejected.submit_calls == 0 && rejected.destroy_calls == 1);
  assert(bridge::ReadMarriageProposalNativeBinderFailureV1(rejected_state) ==
         bridge::MarriageProposalNativeBinderFailureV1::
             complete_can_send_rejected);

  Harness queue_rejected{};
  queue_rejected.submit = false;
  bridge::MarriageProposalNativeBinderStateV1 queue_state{};
  InitializeState(queue_rejected, queue_state);
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &queue_state, Submission()) ==
         bridge::MarriageProposalNativeSubmitResultV1::rejected);
  assert(queue_rejected.submit_calls == 1 &&
         queue_rejected.destroy_calls == 2);
}

void TestRanklessObservedHeirNativeAnswer() {
  Harness harness{};
  harness.ai_accept_raw = 3'600'000'000LL;
  harness.answer_raw = 0; // R0082 final native answer, not refusal.
  bridge::MarriageProposalNativeBinderStateV1 state{};
  InitializeState(harness, state);
  auto submission = Submission();
  submission.rankless_observed_heir = true;
  submission.native_rank = 0;
  submission.predicted_outcome =
      bridge::MarriagePredictedOutcomeV1::unavailable;
  submission.roles.actor_character_id = kPlayedId;
  submission.recipient_ai_accept_raw = harness.ai_accept_raw;
  submission.recipient_answer_status_raw = harness.answer_raw;
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &state, submission) ==
         bridge::MarriageProposalNativeSubmitResultV1::submitted);
  assert(harness.submit_calls == 1);

  Harness changed{};
  changed.ai_accept_raw = harness.ai_accept_raw;
  changed.answer_raw = 1;
  bridge::MarriageProposalNativeBinderStateV1 changed_state{};
  InitializeState(changed, changed_state);
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &changed_state, submission) ==
         bridge::MarriageProposalNativeSubmitResultV1::rejected);
  assert(changed.submit_calls == 0);
  assert(bridge::ReadMarriageProposalNativeBinderFailureV1(changed_state) ==
         bridge::MarriageProposalNativeBinderFailureV1::recipient_answer_changed);
}

void TestBilateralReadbackAndExplicitBlockers() {
  Harness harness{};
  bridge::MarriageProposalNativeBinderStateV1 state{};
  InitializeState(harness, state);
  bridge::MarriageProposalBilateralRelationshipV1 bilateral{};
  assert(bridge::ReadMarriageProposalBilateralRelationshipFromNativeBinderV1(
             state, kSubjectId, kCandidateId, bilateral) ==
         bridge::MarriageProposalNativeReadbackResultV1::available);
  assert(bilateral.subject_identity_round_trip &&
         bilateral.candidate_identity_round_trip && bilateral.subject_alive &&
         bilateral.candidate_alive &&
         bilateral.subject_has_candidate_as_spouse &&
         bilateral.candidate_has_subject_as_spouse &&
         !bilateral.subject_has_candidate_as_betrothed &&
         !bilateral.candidate_has_subject_as_betrothed);

  bridge::MarriageProposalRelationshipObservationV1 observation{};
  assert(bridge::ReadMarriageProposalRelationshipObservationFromNativeBinderV1(
             state, kSubjectId, kCandidateId, observation) ==
         bridge::MarriageProposalNativeReadbackResultV1::available);
  assert(observation.available && observation.paused &&
         observation.relationship_state_ready &&
         observation.alliance_state_ready &&
         observation.subject_has_alliance_with_candidate &&
         observation.candidate_has_alliance_with_subject &&
         observation.native_resolution ==
             bridge::MarriageProposalNativeResolutionV1::accepted);

  bool played_has_recipient = false;
  bool recipient_has_played = false;
  assert(bridge::ReadMarriageProposalAlliancePairFromNativeBinderV1(
             state, kPlayedId, kRecipientId, played_has_recipient,
             recipient_has_played) ==
         bridge::MarriageProposalNativeReadbackResultV1::available);
  assert(played_has_recipient && recipient_has_played);
  harness.alliance = false;
  harness.alliance_reverse = false;
  assert(bridge::ReadMarriageProposalAlliancePairFromNativeBinderV1(
             state, kPlayedId, kRecipientId, played_has_recipient,
             recipient_has_played) ==
         bridge::MarriageProposalNativeReadbackResultV1::available);
  assert(!played_has_recipient && !recipient_has_played);
  harness.alliance = true;
  assert(bridge::ReadMarriageProposalAlliancePairFromNativeBinderV1(
             state, kPlayedId, kRecipientId, played_has_recipient,
             recipient_has_played) ==
         bridge::MarriageProposalNativeReadbackResultV1::available);
  assert(played_has_recipient && !recipient_has_played);

  state.environment.alliance_readback_certified = false;
  assert(bridge::ReadMarriageProposalAlliancePairFromNativeBinderV1(
             state, kPlayedId, kRecipientId, played_has_recipient,
             recipient_has_played) ==
         bridge::MarriageProposalNativeReadbackResultV1::blocked);
  assert(bridge::ReadMarriageProposalRelationshipObservationFromNativeBinderV1(
             state, kSubjectId, kCandidateId, observation) ==
         bridge::MarriageProposalNativeReadbackResultV1::blocked);
  assert(bridge::ReadMarriageProposalNativeBinderFailureV1(state) ==
         bridge::MarriageProposalNativeBinderFailureV1::
             alliance_readback_not_certified);
}

void TestVersionAndCommandIdentityFailClosed() {
  Harness harness{};
  bridge::MarriageProposalNativeBinderStateV1 state{};
  InitializeState(harness, state);
  state.environment.admitted_executable_sha256 = "wrong";
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &state, Submission()) ==
         bridge::MarriageProposalNativeSubmitResultV1::unavailable);
  assert(harness.submit_calls == 0);

  InitializeState(harness, state);
  state.environment.send_command_primary_vtable ^= 1;
  assert(bridge::SubmitMarriageProposalFromNativeBinderV1(
             &state, Submission()) ==
         bridge::MarriageProposalNativeSubmitResultV1::unavailable);
  assert(harness.submit_calls == 0);
}

void TestProductionSignatureDriftFailClosed() {
  bridge::MarriageProposalNativeBinderStateV1 state{};
  state.environment = bridge::BindMarriageProposalNativeBinderEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  state.environment.source_adapter.read_memory = &ReadZeroMemory;
  bridge::MarriageProposalActionEnvironmentV1 action{};
  bridge::SubmitMarriageProposalNativeV1 callback = nullptr;
  void *context = nullptr;
  assert(bridge::ConfigureMarriageProposalActionSubmitFromNativeBinderV1(
             state, action, callback, context) ==
         bridge::MarriageProposalNativeBindResultV1::failed);
  assert(bridge::ReadMarriageProposalNativeBinderFailureV1(state) ==
         bridge::MarriageProposalNativeBinderFailureV1::
             native_signature_mismatch);
  assert(callback == nullptr && context == nullptr);
}

} // namespace

int main() {
  TestBindAndCertifiedConfiguration();
  TestSingleSubmitAndNativeFinalValidation();
  TestRanklessObservedHeirNativeAnswer();
  TestBilateralReadbackAndExplicitBlockers();
  TestVersionAndCommandIdentityFailClosed();
  TestProductionSignatureDriftFailClosed();
  std::cout << "marriage proposal native binder v1 tests passed\n";
  return 0;
}

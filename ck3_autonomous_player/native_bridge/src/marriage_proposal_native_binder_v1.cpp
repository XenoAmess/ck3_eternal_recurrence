#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8, "marriage proposal binder is x64-only");

template <typename Value>
bool AddRva(std::uintptr_t base, std::uintptr_t rva, Value &output) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = {};
    return false;
  }
  if constexpr (std::is_pointer_v<Value>) {
    output = reinterpret_cast<Value>(base + rva);
  } else {
    output = static_cast<Value>(base + rva);
  }
  return true;
}

void SetFailure(MarriageProposalNativeBinderStateV1 &state,
                MarriageProposalNativeBinderFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageProposalNativeBinderEnvironmentV1 &environment,
                std::uintptr_t address, void *output, std::size_t size) noexcept {
  const auto &source = environment.source_adapter;
  return source.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 && source.read_memory(source.memory_context, address, output,
                                     size);
}

template <typename Value>
bool ReadAt(const MarriageProposalNativeBinderEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, Value &output) noexcept {
  return base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      ReadMemory(environment, base + offset, &output, sizeof(output));
}

struct NativePrefixV1 {
  std::uintptr_t rva = 0;
  std::array<std::uint8_t, 16> bytes{};
};

constexpr std::array<NativePrefixV1, 15> kNativePrefixes{{
    {kMarriageCandidateEnumeratorRvaV1,
     {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x44, 0x89, 0x48, 0x20,
      0x55, 0x56, 0x57, 0x41, 0x54}},
    {kMarriageCandidateScoreFilterRvaV1,
     {0x40, 0x53, 0x55, 0x56, 0x57, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x20,
      0x48, 0x8B, 0x42, 0x10, 0x49}},
    {kMarriageCandidateGateAndScoreRvaV1,
     {0x40, 0x53, 0x55, 0x41, 0x56, 0x48, 0x83, 0xEC, 0x30, 0x4D, 0x8B,
      0xF1, 0x48, 0x8B, 0xEA, 0x48}},
    {kMarriageGetCharacterInteractionDatabaseRvaV1,
     {0x48, 0x83, 0xEC, 0x38, 0x48, 0x8B, 0x05, 0x65, 0xA8, 0xED, 0x04,
      0x48, 0x85, 0xC0, 0x75, 0x42}},
    {kMarriageRedirectRolesRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10, 0x48,
      0x89, 0x7C, 0x24, 0x18, 0x55}},
    {kMarriageConstructAllRolesContextRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x6C, 0x24, 0x18, 0x48,
      0x89, 0x4C, 0x24, 0x08, 0x56}},
    {kMarriageRefreshContextRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x55,
      0x57, 0x41, 0x54, 0x41, 0x56}},
    {kMarriageFinalizeContextRvaV1,
     {0x40, 0x53, 0x57, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B,
      0x01, 0x48, 0x8B, 0xD9, 0x44}},
    {kMarriageCompleteCanSendRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x81, 0xEC, 0x90, 0x00,
      0x00, 0x00, 0x48, 0x8B, 0xFA}},
    {kMarriageDestroyContextRvaV1,
     {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B, 0xD9, 0x48, 0x8B,
      0x89, 0x30, 0x03, 0x00, 0x00}},
    {kMarriageConstructSendInteractionCommandRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x18, 0x48, 0x89, 0x74, 0x24, 0x20, 0x48,
      0x89, 0x4C, 0x24, 0x08, 0x57}},
    {kMarriageSubmitCommandRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x08, 0x4C, 0x89, 0x4C, 0x24, 0x20, 0x57,
      0x48, 0x83, 0xEC, 0x20, 0x41}},
    {kMarriageRecipientAiAcceptRvaV1,
     {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x81, 0xEC, 0x90, 0x01,
      0x00, 0x00, 0x48, 0x8B, 0xDA}},
    {kMarriageOuterAnswerRvaV1,
     {0x48, 0x8B, 0xC4, 0x4C, 0x89, 0x48, 0x20, 0x44, 0x88, 0x40, 0x18,
      0x88, 0x50, 0x10, 0x53, 0x56}},
    {kMarriageOutcomeDispatchRvaV1,
     {0x40, 0x53, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x60, 0x48, 0x8B, 0xF2,
      0x4C, 0x89, 0xB4, 0x24, 0x80}},
}};

bool ExactAdmission(const MarriageProposalNativeBinderEnvironmentV1 &env) {
  return env.exact_build_admitted &&
      env.admitted_executable_sha256 ==
          kMarriageProposalNativeBinderExecutableSha256V1 &&
      (env.offline_fixture || env.module_base != 0);
}

bool SourceBindingsMatch(
    const MarriageProposalNativeBinderEnvironmentV1 &env) noexcept {
  if (env.offline_fixture) return true;
  const auto expected = BindMarriageMatchmakingSourceAdapterEnvironmentV1(
      env.module_base, env.exact_build_admitted,
      env.admitted_executable_sha256);
  const auto &actual = env.source_adapter;
  return actual.module_base == expected.module_base &&
      actual.character_storage_slot_address ==
          expected.character_storage_slot_address &&
      actual.get_character_interaction_database ==
          expected.get_character_interaction_database &&
      actual.redirect_roles == expected.redirect_roles &&
      actual.construct_context == expected.construct_context &&
      actual.refresh_context == expected.refresh_context &&
      actual.finalize_context == expected.finalize_context &&
      actual.complete_can_send == expected.complete_can_send &&
      actual.recipient_ai_accept == expected.recipient_ai_accept &&
      actual.outer_answer == expected.outer_answer &&
      actual.destroy_context == expected.destroy_context;
}

bool CommandBindingsMatch(
    const MarriageProposalNativeBinderEnvironmentV1 &env) noexcept {
  if (env.offline_fixture) return env.command_manager != nullptr;
  void *manager = nullptr;
  SubmitMarriageCommandV1 submit = nullptr;
  ConstructMarriageSendInteractionCommandV1 construct = nullptr;
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  return AddRva(env.module_base, kMarriageCommandManagerRvaV1, manager) &&
      AddRva(env.module_base, kMarriageSubmitCommandRvaV1, submit) &&
      AddRva(env.module_base, kMarriageConstructSendInteractionCommandRvaV1,
             construct) &&
      AddRva(env.module_base, kMarriageSendInteractionPrimaryVtableRvaV1,
             primary) &&
      AddRva(env.module_base, kMarriageSendInteractionSecondaryVtableRvaV1,
             secondary) &&
      env.command_manager == manager && env.submit_command == submit &&
      env.construct_send_command == construct &&
      env.send_command_primary_vtable == primary &&
      env.send_command_secondary_vtable == secondary;
}

MarriageProposalNativeBinderFailureV1 ValidateCommon(
    const MarriageProposalNativeBinderEnvironmentV1 &env,
    bool require_signatures) noexcept {
  if (!ExactAdmission(env))
    return MarriageProposalNativeBinderFailureV1::exact_build_not_admitted;
  if (env.source_adapter.read_memory == nullptr)
    return MarriageProposalNativeBinderFailureV1::memory_reader_unavailable;
  if (!SourceBindingsMatch(env) || !CommandBindingsMatch(env))
    return MarriageProposalNativeBinderFailureV1::native_binding_mismatch;
  if (require_signatures && !env.offline_fixture) {
    for (const auto &prefix : kNativePrefixes) {
      std::array<std::uint8_t, 16> actual{};
      if (prefix.rva >
              (std::numeric_limits<std::uintptr_t>::max)() - env.module_base ||
          !ReadMemory(env, env.module_base + prefix.rva, actual.data(),
                      actual.size()) ||
          actual != prefix.bytes) {
        return MarriageProposalNativeBinderFailureV1::
            native_signature_mismatch;
      }
    }
  }
  return MarriageProposalNativeBinderFailureV1::none;
}

bool ValidDirectSubmission(const MarriageProposalSubmissionV1 &submission) {
  const bool ranked_direct = !submission.rankless_observed_heir &&
      submission.native_rank != 0 &&
      submission.predicted_outcome != MarriagePredictedOutcomeV1::unavailable;
  const bool observed_heir = submission.rankless_observed_heir &&
      submission.native_rank == 0 &&
      submission.predicted_outcome == MarriagePredictedOutcomeV1::unavailable &&
      submission.roles.actor_character_id != submission.subject_character_id &&
      submission.recipient_answer_status_raw >= 0 &&
      submission.recipient_answer_status_raw <= 1;
  return submission.subject_character_id != 0 &&
      submission.candidate_character_id != 0 &&
      (ranked_direct || observed_heir) &&
      submission.roles.actor_character_id != 0 &&
      submission.roles.recipient_character_id != 0 &&
      submission.roles.secondary_actor_character_id ==
          submission.subject_character_id &&
      submission.roles.secondary_recipient_character_id ==
          submission.candidate_character_id;
}

enum class IdentityResultV1 { available, missing, failed };

struct ResolvedCharacterV1 {
  std::uintptr_t storage = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  std::uintptr_t character = 0;
  bool alive = false;
};

IdentityResultV1 ResolveCharacter(
    const MarriageProposalNativeBinderEnvironmentV1 &env,
    std::uint32_t character_id, ResolvedCharacterV1 &output) noexcept {
  output = {};
  if (!ReadMemory(env, env.source_adapter.character_storage_slot_address,
                  &output.storage, sizeof(output.storage)) ||
      output.storage == 0 ||
      !ReadAt(env, output.storage, kMarriageCharacterStorageSlotsOffsetV1,
              output.slots) ||
      !ReadAt(env, output.storage, kMarriageCharacterStorageCapacityOffsetV1,
              output.capacity) ||
      output.slots == 0 || output.capacity <= 0 ||
      output.capacity > kMarriageMaximumCharacterStorageCapacityV1) {
    return IdentityResultV1::failed;
  }
  const auto index = character_id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(output.capacity))
    return IdentityResultV1::missing;
  const auto slot_offset = static_cast<std::uintptr_t>(index) *
          kMarriageCharacterStorageSlotStrideV1 +
      kMarriageCharacterStorageSlotObjectOffsetV1;
  if (slot_offset >
      (std::numeric_limits<std::uintptr_t>::max)() - output.slots)
    return IdentityResultV1::failed;
  std::int32_t resolved_id = -1;
  if (!ReadMemory(env, output.slots + slot_offset, &output.character,
                  sizeof(output.character)))
    return IdentityResultV1::failed;
  if (output.character == 0) return IdentityResultV1::missing;
  if (!ReadAt(env, output.character, kMarriageCharacterIdOffsetV1,
              resolved_id))
    return IdentityResultV1::failed;
  if (static_cast<std::uint32_t>(resolved_id) != character_id)
    return IdentityResultV1::missing;
  std::uintptr_t death_data = 0;
  if (!ReadAt(env, output.character, kMarriageCharacterDeathDataOffsetV1,
              death_data))
    return IdentityResultV1::failed;
  output.alive = death_data == 0;
  return IdentityResultV1::available;
}

std::int32_t NativeId(std::uint32_t id) noexcept {
  std::int32_t output = -1;
  static_assert(sizeof(output) == sizeof(id));
  std::memcpy(&output, &id, sizeof(output));
  return output;
}

struct NativeRolesV1 {
  std::int32_t actor = -1;
  std::int32_t recipient = -1;
  std::int32_t secondary_actor = -1;
  std::int32_t secondary_recipient = -1;
  std::int32_t intermediary = -1;
  friend bool operator==(const NativeRolesV1 &, const NativeRolesV1 &) =
      default;
};

NativeRolesV1 ToNativeRoles(const MarriageMatchmakingPairRolesV1 &roles) {
  return {NativeId(roles.actor_character_id),
          NativeId(roles.recipient_character_id),
          NativeId(roles.secondary_actor_character_id),
          NativeId(roles.secondary_recipient_character_id),
          roles.intermediary_character_id == 0
              ? -1
              : NativeId(roles.intermediary_character_id)};
}

bool ReadContextRoles(const MarriageProposalNativeBinderEnvironmentV1 &env,
                      std::uintptr_t context, NativeRolesV1 &output) {
  return ReadAt(env, context, kMarriageContextActorIdOffsetV1, output.actor) &&
      ReadAt(env, context, kMarriageContextRecipientIdOffsetV1,
             output.recipient) &&
      ReadAt(env, context, kMarriageContextSecondaryActorIdOffsetV1,
             output.secondary_actor) &&
      ReadAt(env, context, kMarriageContextSecondaryRecipientIdOffsetV1,
             output.secondary_recipient) &&
      ReadAt(env, context, kMarriageContextIntermediaryIdOffsetV1,
             output.intermediary);
}

bool ResolveRoles(const MarriageProposalNativeBinderEnvironmentV1 &env,
                  const NativeRolesV1 &roles) {
  for (const auto id : {roles.actor, roles.recipient, roles.secondary_actor,
                        roles.secondary_recipient, roles.intermediary}) {
    if (id == -1) continue;
    ResolvedCharacterV1 resolved{};
    if (ResolveCharacter(env, static_cast<std::uint32_t>(id), resolved) !=
            IdentityResultV1::available ||
        !resolved.alive)
      return false;
  }
  return true;
}

struct alignas(16) ContextStorageV1 {
  std::array<std::byte, kMarriageInteractionContextSizeV1 + 8> bytes{};
};
struct alignas(8) CommandStorageV1 {
  std::array<std::byte, kMarriageSendInteractionCommandSizeV1> bytes{};
};
static_assert(sizeof(ContextStorageV1) == 0x340);
static_assert(sizeof(CommandStorageV1) == kMarriageSendInteractionCommandSizeV1);

struct FamilySampleV1 {
  bool round_trip = false;
  bool alive = false;
  std::uintptr_t character = 0;
  std::uintptr_t family = 0;
  std::uint32_t betrothed = 0;
  std::uint32_t primary_spouse = 0;
  std::uintptr_t spouse_data = 0;
  std::int32_t spouse_capacity = 0;
  std::int32_t spouse_count = 0;
  bool has_target_as_spouse = false;
  bool has_target_as_betrothed = false;
  friend bool operator==(const FamilySampleV1 &, const FamilySampleV1 &) =
      default;
};

MarriageProposalNativeBinderFailureV1 ReadFamily(
    const MarriageProposalNativeBinderEnvironmentV1 &env,
    std::uint32_t character_id, std::uint32_t target_id,
    FamilySampleV1 &output) {
  output = {};
  ResolvedCharacterV1 resolved{};
  const auto identity = ResolveCharacter(env, character_id, resolved);
  if (identity == IdentityResultV1::failed)
    return MarriageProposalNativeBinderFailureV1::character_storage_unavailable;
  if (identity == IdentityResultV1::missing) return {};
  output.round_trip = true;
  output.alive = resolved.alive;
  output.character = resolved.character;
  if (!resolved.alive) return {};
  if (!ReadAt(env, resolved.character, kMarriageCharacterFamilyDataOffsetV1,
              output.family))
    return MarriageProposalNativeBinderFailureV1::family_array_invalid;
  if (output.family == 0) return {};
  std::int32_t betrothed = -1;
  std::int32_t primary = -1;
  if (!ReadAt(env, output.family, kMarriageFamilyBetrothedIdOffsetV1,
              betrothed) ||
      !ReadAt(env, output.family, kMarriageFamilyPrimarySpouseIdOffsetV1,
              primary) ||
      !ReadAt(env, output.family,
              kMarriageFamilySpouseIdsOffsetV1 +
                  kMarriageNativeArrayDataOffsetV1,
              output.spouse_data) ||
      !ReadAt(env, output.family,
              kMarriageFamilySpouseIdsOffsetV1 +
                  kMarriageNativeArrayCapacityOffsetV1,
              output.spouse_capacity) ||
      !ReadAt(env, output.family,
              kMarriageFamilySpouseIdsOffsetV1 +
                  kMarriageNativeArrayCountOffsetV1,
              output.spouse_count) ||
      output.spouse_capacity < 0 || output.spouse_count < 0 ||
      output.spouse_count > output.spouse_capacity ||
      output.spouse_capacity > kMarriageMaximumSpouseArrayCountV1 ||
      (output.spouse_count != 0 && output.spouse_data == 0))
    return MarriageProposalNativeBinderFailureV1::family_array_invalid;
  output.betrothed = static_cast<std::uint32_t>(betrothed);
  output.primary_spouse = static_cast<std::uint32_t>(primary);
  output.has_target_as_betrothed =
      betrothed != -1 && static_cast<std::uint32_t>(betrothed) == target_id;
  output.has_target_as_spouse =
      primary != -1 && static_cast<std::uint32_t>(primary) == target_id;
  for (const auto relationship_id : {betrothed, primary}) {
    if (relationship_id == -1) continue;
    ResolvedCharacterV1 related{};
    if (ResolveCharacter(env, static_cast<std::uint32_t>(relationship_id),
                         related) != IdentityResultV1::available)
      return MarriageProposalNativeBinderFailureV1::
          family_identity_unavailable;
  }
  for (std::int32_t index = 0; index < output.spouse_count; ++index) {
    std::int32_t spouse_id = -1;
    const auto offset = static_cast<std::uintptr_t>(index) * sizeof(spouse_id);
    if (offset > (std::numeric_limits<std::uintptr_t>::max)() -
                     output.spouse_data ||
        !ReadMemory(env, output.spouse_data + offset, &spouse_id,
                    sizeof(spouse_id)))
      return MarriageProposalNativeBinderFailureV1::family_array_invalid;
    if (spouse_id == -1) continue;
    ResolvedCharacterV1 spouse{};
    if (ResolveCharacter(env, static_cast<std::uint32_t>(spouse_id), spouse) !=
        IdentityResultV1::available)
      return MarriageProposalNativeBinderFailureV1::family_identity_unavailable;
    if (static_cast<std::uint32_t>(spouse_id) == target_id)
      output.has_target_as_spouse = true;
  }
  return {};
}

MarriageProposalNativeReadbackResultV1 ReadBilateralOnce(
    MarriageProposalNativeBinderStateV1 &binder, std::uint32_t subject_id,
    std::uint32_t candidate_id, MarriageProposalBilateralRelationshipV1 &out,
    FamilySampleV1 &subject, FamilySampleV1 &candidate) {
  auto failure = ReadFamily(binder.environment, subject_id, candidate_id,
                            subject);
  if (failure == MarriageProposalNativeBinderFailureV1::none)
    failure = ReadFamily(binder.environment, candidate_id, subject_id,
                         candidate);
  if (failure != MarriageProposalNativeBinderFailureV1::none) {
    SetFailure(binder, failure);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  out = {};
  out.subject_character_id = subject_id;
  out.candidate_character_id = candidate_id;
  out.subject_identity_round_trip = subject.round_trip;
  out.candidate_identity_round_trip = candidate.round_trip;
  out.subject_alive = subject.alive;
  out.candidate_alive = candidate.alive;
  out.subject_has_candidate_as_spouse = subject.has_target_as_spouse;
  out.candidate_has_subject_as_spouse = candidate.has_target_as_spouse;
  out.subject_has_candidate_as_betrothed = subject.has_target_as_betrothed;
  out.candidate_has_subject_as_betrothed = candidate.has_target_as_betrothed;
  return MarriageProposalNativeReadbackResultV1::available;
}

} // namespace

MarriageProposalNativeBinderEnvironmentV1
BindMarriageProposalNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageProposalNativeBinderEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.source_adapter = BindMarriageMatchmakingSourceAdapterEnvironmentV1(
      module_base, exact_build_admitted, admitted_executable_sha256);
  const bool complete =
      AddRva(module_base, kMarriageCommandManagerRvaV1,
             output.command_manager) &&
      AddRva(module_base, kMarriageSubmitCommandRvaV1,
             output.submit_command) &&
      AddRva(module_base, kMarriageConstructSendInteractionCommandRvaV1,
             output.construct_send_command) &&
      AddRva(module_base, kMarriageSendInteractionPrimaryVtableRvaV1,
             output.send_command_primary_vtable) &&
      AddRva(module_base, kMarriageSendInteractionSecondaryVtableRvaV1,
             output.send_command_secondary_vtable);
  if (!complete) {
    output.command_manager = nullptr;
    output.submit_command = nullptr;
    output.construct_send_command = nullptr;
    output.send_command_primary_vtable = 0;
    output.send_command_secondary_vtable = 0;
  }
  return output;
}

MarriageProposalNativeBindResultV1
ConfigureMarriageMatchmakingSourceAdapterFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    MarriageMatchmakingSourceAdapterStateV1 &source_adapter) noexcept {
  auto failure = ValidateCommon(binder.environment, true);
  const auto &source = binder.environment.source_adapter;
  if (failure == MarriageProposalNativeBinderFailureV1::none &&
      (source.character_storage_slot_address == 0 ||
       source.read_memory == nullptr ||
       source.get_character_interaction_database == nullptr ||
       source.redirect_roles == nullptr || source.construct_context == nullptr ||
       source.refresh_context == nullptr || source.finalize_context == nullptr ||
       source.complete_can_send == nullptr ||
       source.recipient_ai_accept == nullptr || source.outer_answer == nullptr ||
       source.destroy_context == nullptr))
    failure = MarriageProposalNativeBinderFailureV1::
        source_adapter_lifecycle_unavailable;
  if (failure == MarriageProposalNativeBinderFailureV1::none &&
      (!binder.environment.ranked_container_lifecycle_certified ||
       binder.environment.source_adapter.invoke_ranked_source == nullptr ||
       binder.environment.source_adapter.read_ranked_container_view ==
           nullptr ||
       binder.environment.source_adapter.release_ranked_container == nullptr))
    failure = MarriageProposalNativeBinderFailureV1::
        ranked_container_lifecycle_not_certified;
  if (failure == MarriageProposalNativeBinderFailureV1::none &&
      (!binder.environment.outcome_classifier_certified ||
       binder.environment.source_adapter.classify_outcome == nullptr))
    failure =
        MarriageProposalNativeBinderFailureV1::outcome_classifier_not_certified;
  if (failure != MarriageProposalNativeBinderFailureV1::none) {
    SetFailure(binder, failure);
    return failure == MarriageProposalNativeBinderFailureV1::
                          ranked_container_lifecycle_not_certified ||
            failure == MarriageProposalNativeBinderFailureV1::
                          outcome_classifier_not_certified
        ? MarriageProposalNativeBindResultV1::blocked
        : MarriageProposalNativeBindResultV1::failed;
  }
  source_adapter.environment = binder.environment.source_adapter;
  source_adapter.last_failure.store(
      static_cast<std::uint32_t>(
          MarriageMatchmakingSourceAdapterFailureV1::none),
      std::memory_order_release);
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeBindResultV1::available;
}

MarriageProposalNativeBindResultV1
ConfigureMarriageProposalActionSubmitFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    MarriageProposalActionEnvironmentV1 &action_environment,
    SubmitMarriageProposalNativeV1 &submit_callback,
    void *&submit_context) noexcept {
  submit_callback = nullptr;
  submit_context = nullptr;
  const auto failure = ValidateCommon(binder.environment, true);
  if (failure != MarriageProposalNativeBinderFailureV1::none ||
      binder.environment.submit_command == nullptr ||
      binder.environment.construct_send_command == nullptr ||
      binder.environment.source_adapter.get_character_interaction_database ==
          nullptr ||
      binder.environment.source_adapter.redirect_roles == nullptr ||
      binder.environment.source_adapter.construct_context == nullptr ||
      binder.environment.source_adapter.refresh_context == nullptr ||
      binder.environment.source_adapter.finalize_context == nullptr ||
      binder.environment.source_adapter.complete_can_send == nullptr ||
      binder.environment.source_adapter.destroy_context == nullptr) {
    const auto actual = failure == MarriageProposalNativeBinderFailureV1::none
        ? MarriageProposalNativeBinderFailureV1::
              action_submit_lifecycle_unavailable
        : failure;
    SetFailure(binder, actual);
    return MarriageProposalNativeBindResultV1::failed;
  }
  const auto action_base = binder.environment.offline_fixture
      ? std::uintptr_t{0}
      : binder.environment.module_base;
  action_environment = BindMarriageProposalActionEnvironmentV1(
      action_base, true, binder.environment.admitted_executable_sha256);
  action_environment.native_submit_certified =
      !binder.environment.offline_fixture;
  action_environment.offline_fixture_submit =
      binder.environment.offline_fixture;
  submit_callback = &SubmitMarriageProposalFromNativeBinderV1;
  submit_context = &binder;
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeBindResultV1::available;
}

MarriageProposalNativeSubmitResultV1 SubmitMarriageProposalFromNativeBinderV1(
    void *context, const MarriageProposalSubmissionV1 &submission) noexcept {
  if (context == nullptr)
    return MarriageProposalNativeSubmitResultV1::unavailable;
  auto &binder = *static_cast<MarriageProposalNativeBinderStateV1 *>(context);
  auto &env = binder.environment;
  auto fail = [&](MarriageProposalNativeBinderFailureV1 failure) {
    SetFailure(binder, failure);
    return MarriageProposalNativeSubmitResultV1::unavailable;
  };
  const auto admission = ValidateCommon(env, true);
  if (admission != MarriageProposalNativeBinderFailureV1::none)
    return fail(admission);
  if (env.command_manager == nullptr || env.submit_command == nullptr ||
      env.construct_send_command == nullptr ||
      env.send_command_primary_vtable == 0 ||
      env.send_command_secondary_vtable == 0 ||
      env.source_adapter.get_character_interaction_database == nullptr ||
      env.source_adapter.redirect_roles == nullptr ||
      env.source_adapter.construct_context == nullptr ||
      env.source_adapter.refresh_context == nullptr ||
      env.source_adapter.finalize_context == nullptr ||
      env.source_adapter.complete_can_send == nullptr ||
      env.source_adapter.destroy_context == nullptr)
    return fail(MarriageProposalNativeBinderFailureV1::
                    action_submit_lifecycle_unavailable);
  if (!ValidDirectSubmission(submission))
    return fail(MarriageProposalNativeBinderFailureV1::invalid_submission);
  const NativeRolesV1 roles = ToNativeRoles(submission.roles);
  if (!ResolveRoles(env, roles))
    return fail(
        MarriageProposalNativeBinderFailureV1::character_identity_unavailable);
  auto *database = env.source_adapter.get_character_interaction_database();
  std::uintptr_t interaction = 0;
  if (database == nullptr ||
      !ReadAt(env, reinterpret_cast<std::uintptr_t>(database),
              kArrangeMarriageInteractionOffsetV1, interaction) ||
      interaction == 0)
    return fail(MarriageProposalNativeBinderFailureV1::interaction_unavailable);
  NativeRolesV1 redirected{
      roles.actor, NativeId(submission.candidate_character_id),
      NativeId(submission.subject_character_id),
      NativeId(submission.candidate_character_id), -1};
  env.source_adapter.redirect_roles(
      reinterpret_cast<void *>(interaction), &redirected.actor,
      &redirected.recipient, &redirected.secondary_actor,
      &redirected.secondary_recipient, &redirected.intermediary);
  if (redirected != roles || !ResolveRoles(env, redirected))
    return fail(
        MarriageProposalNativeBinderFailureV1::redirected_roles_mismatch);

  ContextStorageV1 context_storage{};
  void *const native_context = context_storage.bytes.data();
  if (env.source_adapter.construct_context(
          native_context, reinterpret_cast<void *>(interaction), roles.actor,
          roles.recipient, roles.secondary_actor, roles.secondary_recipient,
          roles.intermediary, nullptr) != native_context)
    return fail(
        MarriageProposalNativeBinderFailureV1::context_construction_failed);
  bool context_constructed = true;
  auto destroy_context = [&]() {
    if (context_constructed) {
      env.source_adapter.destroy_context(native_context);
      context_constructed = false;
    }
  };
  env.source_adapter.refresh_context(native_context, true);
  env.source_adapter.finalize_context(native_context);
  NativeRolesV1 context_roles{};
  if (!ReadContextRoles(env, reinterpret_cast<std::uintptr_t>(native_context),
                        context_roles) ||
      context_roles != roles || !ResolveRoles(env, context_roles)) {
    destroy_context();
    return fail(MarriageProposalNativeBinderFailureV1::context_roles_mismatch);
  }
  if (!env.source_adapter.complete_can_send(native_context, nullptr)) {
    destroy_context();
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::complete_can_send_rejected);
    return MarriageProposalNativeSubmitResultV1::rejected;
  }
  if (submission.rankless_observed_heir) {
    if (env.source_adapter.recipient_ai_accept == nullptr ||
        env.source_adapter.outer_answer == nullptr) {
      destroy_context();
      return fail(MarriageProposalNativeBinderFailureV1::
                      source_adapter_lifecycle_unavailable);
    }
    std::int64_t accept_raw = 0;
    const bool same_answer =
        env.source_adapter.recipient_ai_accept(native_context, &accept_raw) ==
            &accept_raw &&
        accept_raw == submission.recipient_ai_accept_raw &&
        env.source_adapter.outer_answer(native_context, 1, 1, nullptr,
                                        nullptr) ==
            submission.recipient_answer_status_raw;
    if (!same_answer) {
      destroy_context();
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::recipient_answer_changed);
      return MarriageProposalNativeSubmitResultV1::rejected;
    }
  }

  CommandStorageV1 command_storage{};
  void *const command = command_storage.bytes.data();
  if (env.construct_send_command(command, native_context) != command) {
    std::uintptr_t partial_context_vtable = 0;
    if (ReadAt(env, reinterpret_cast<std::uintptr_t>(command),
               kMarriageSendInteractionContextOffsetV1,
               partial_context_vtable) &&
        partial_context_vtable != 0) {
      env.source_adapter.destroy_context(
          command_storage.bytes.data() +
          kMarriageSendInteractionContextOffsetV1);
    }
    destroy_context();
    return fail(
        MarriageProposalNativeBinderFailureV1::command_construction_failed);
  }
  bool command_context_constructed = true;
  auto destroy_command_context = [&]() {
    if (command_context_constructed) {
      env.source_adapter.destroy_context(
          command_storage.bytes.data() +
          kMarriageSendInteractionContextOffsetV1);
      command_context_constructed = false;
    }
  };
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  NativeRolesV1 copied_roles{};
  if (!ReadAt(env, reinterpret_cast<std::uintptr_t>(command), 0, primary) ||
      !ReadAt(env, reinterpret_cast<std::uintptr_t>(command), 0x18,
              secondary) ||
      primary != env.send_command_primary_vtable ||
      secondary != env.send_command_secondary_vtable ||
      !ReadContextRoles(
          env, reinterpret_cast<std::uintptr_t>(command) +
                   kMarriageSendInteractionContextOffsetV1,
          copied_roles) ||
      copied_roles != roles) {
    destroy_command_context();
    destroy_context();
    return fail(MarriageProposalNativeBinderFailureV1::command_identity_mismatch);
  }
  NativeRolesV1 source_roles{};
  std::uintptr_t interaction_after = 0;
  auto *database_after =
      env.source_adapter.get_character_interaction_database();
  if (database_after != database ||
      !ReadAt(env, reinterpret_cast<std::uintptr_t>(database_after),
              kArrangeMarriageInteractionOffsetV1, interaction_after) ||
      interaction_after != interaction ||
      !ReadContextRoles(env, reinterpret_cast<std::uintptr_t>(native_context),
                        source_roles) ||
      source_roles != roles || !ResolveRoles(env, roles)) {
    destroy_command_context();
    destroy_context();
    return fail(MarriageProposalNativeBinderFailureV1::command_identity_mismatch);
  }
  const bool submitted = env.submit_command(
      env.command_manager, command, kMarriageSendInteractionFlagsV1);
  destroy_command_context();
  destroy_context();
  if (!submitted) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::command_queue_rejected);
    return MarriageProposalNativeSubmitResultV1::rejected;
  }
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeSubmitResultV1::submitted;
}

MarriageProposalNativeReadbackResultV1
ReadMarriageProposalBilateralRelationshipFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalBilateralRelationshipV1 &output) noexcept {
  output = {};
  const auto admission = ValidateCommon(binder.environment, true);
  if (admission != MarriageProposalNativeBinderFailureV1::none) {
    SetFailure(binder, admission);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  if (subject_character_id == 0 || candidate_character_id == 0 ||
      subject_character_id == candidate_character_id) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::invalid_submission);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  FamilySampleV1 subject_first{};
  FamilySampleV1 candidate_first{};
  MarriageProposalBilateralRelationshipV1 first{};
  auto result = ReadBilateralOnce(binder, subject_character_id,
                                  candidate_character_id, first,
                                  subject_first, candidate_first);
  if (result != MarriageProposalNativeReadbackResultV1::available)
    return result;
  FamilySampleV1 subject_second{};
  FamilySampleV1 candidate_second{};
  MarriageProposalBilateralRelationshipV1 second{};
  result = ReadBilateralOnce(binder, subject_character_id,
                             candidate_character_id, second,
                             subject_second, candidate_second);
  if (result != MarriageProposalNativeReadbackResultV1::available)
    return result;
  if (first != second || subject_first != subject_second ||
      candidate_first != candidate_second) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::relationship_sample_drift);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  output = second;
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeReadbackResultV1::available;
}

MarriageProposalNativeReadbackResultV1
ReadMarriageProposalAlliancePairFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    std::uint32_t first_character_id, std::uint32_t second_character_id,
    bool &first_has_second, bool &second_has_first) noexcept {
  first_has_second = false;
  second_has_first = false;
  const auto &env = binder.environment;
  const auto admission = ValidateCommon(env, true);
  if (admission != MarriageProposalNativeBinderFailureV1::none) {
    SetFailure(binder, admission);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  if (first_character_id == 0 || second_character_id == 0 ||
      first_character_id == second_character_id) {
    SetFailure(binder, MarriageProposalNativeBinderFailureV1::invalid_submission);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  if (!env.alliance_readback_certified || env.read_alliance_pair == nullptr) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::alliance_readback_not_certified);
    return MarriageProposalNativeReadbackResultV1::blocked;
  }
  ResolvedCharacterV1 first{};
  ResolvedCharacterV1 second{};
  if (ResolveCharacter(env, first_character_id, first) !=
          IdentityResultV1::available ||
      ResolveCharacter(env, second_character_id, second) !=
          IdentityResultV1::available || !first.alive || !second.alive) {
    SetFailure(binder, MarriageProposalNativeBinderFailureV1::alliance_sample_drift);
    return MarriageProposalNativeReadbackResultV1::blocked;
  }
  bool forward = false;
  bool reverse = false;
  if (!env.read_alliance_pair(env.alliance_context, first.character,
                              second.character, forward, reverse)) {
    SetFailure(binder, MarriageProposalNativeBinderFailureV1::alliance_sample_drift);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  ResolvedCharacterV1 first_again{};
  ResolvedCharacterV1 second_again{};
  bool forward_again = false;
  bool reverse_again = false;
  if (ResolveCharacter(env, first_character_id, first_again) !=
          IdentityResultV1::available ||
      ResolveCharacter(env, second_character_id, second_again) !=
          IdentityResultV1::available || !first_again.alive ||
      !second_again.alive || first.character != first_again.character ||
      second.character != second_again.character ||
      !env.read_alliance_pair(env.alliance_context, first_again.character,
                              second_again.character, forward_again,
                              reverse_again) || forward != forward_again ||
      reverse != reverse_again) {
    SetFailure(binder, MarriageProposalNativeBinderFailureV1::alliance_sample_drift);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  first_has_second = forward_again;
  second_has_first = reverse_again;
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeReadbackResultV1::available;
}

MarriageProposalNativeReadbackResultV1
ReadMarriageProposalRelationshipObservationFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalRelationshipObservationV1 &output) noexcept {
  output = {};
  auto &env = binder.environment;
  if (env.capture_receipt_frame == nullptr) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::receipt_frame_source_unavailable);
    return MarriageProposalNativeReadbackResultV1::blocked;
  }
  MarriageProposalReceiptFrameV1 before{};
  if (!env.capture_receipt_frame(env.receipt_frame_context, before) ||
      !before.available || !before.paused) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::receipt_frame_drift);
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  MarriageProposalBilateralRelationshipV1 bilateral{};
  auto result = ReadMarriageProposalBilateralRelationshipFromNativeBinderV1(
      binder, subject_character_id, candidate_character_id, bilateral);
  if (result != MarriageProposalNativeReadbackResultV1::available)
    return result;

  output.available = true;
  output.paused = before.paused;
  output.snapshot_id = before.snapshot_id;
  output.public_revision = before.public_revision;
  output.native_revision = before.native_revision;
  output.proof_epoch = before.proof_epoch;
  output.date_raw = before.date_raw;
  output.subject_character_id = bilateral.subject_character_id;
  output.candidate_character_id = bilateral.candidate_character_id;
  output.subject_identity_round_trip = bilateral.subject_identity_round_trip;
  output.candidate_identity_round_trip = bilateral.candidate_identity_round_trip;
  output.subject_alive = bilateral.subject_alive;
  output.candidate_alive = bilateral.candidate_alive;
  output.relationship_state_ready = true;
  output.subject_has_candidate_as_spouse =
      bilateral.subject_has_candidate_as_spouse;
  output.candidate_has_subject_as_spouse =
      bilateral.candidate_has_subject_as_spouse;
  output.subject_has_candidate_as_betrothed =
      bilateral.subject_has_candidate_as_betrothed;
  output.candidate_has_subject_as_betrothed =
      bilateral.candidate_has_subject_as_betrothed;

  if (!bilateral.subject_identity_round_trip ||
      !bilateral.candidate_identity_round_trip || !bilateral.subject_alive ||
      !bilateral.candidate_alive) {
    output.native_resolution = MarriageProposalNativeResolutionV1::invalidated;
  } else {
    if (!env.alliance_readback_certified || env.read_alliance_pair == nullptr) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::alliance_readback_not_certified);
      output = {};
      return MarriageProposalNativeReadbackResultV1::blocked;
    }
    if (!env.proposal_resolution_certified ||
        env.read_proposal_resolution == nullptr) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::proposal_resolution_not_certified);
      output = {};
      return MarriageProposalNativeReadbackResultV1::blocked;
    }
    ResolvedCharacterV1 subject{};
    ResolvedCharacterV1 candidate{};
    bool subject_alliance_first = false;
    bool candidate_alliance_first = false;
    MarriageProposalNativeResolutionV1 resolution_first =
        MarriageProposalNativeResolutionV1::pending;
    if (ResolveCharacter(env, subject_character_id, subject) !=
            IdentityResultV1::available ||
        ResolveCharacter(env, candidate_character_id, candidate) !=
            IdentityResultV1::available ||
        !env.read_alliance_pair(
            env.alliance_context, subject.character, candidate.character,
            subject_alliance_first, candidate_alliance_first)) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::alliance_sample_drift);
      output = {};
      return MarriageProposalNativeReadbackResultV1::failed;
    }
    if (!env.read_proposal_resolution(
            env.proposal_resolution_context, subject_character_id,
            candidate_character_id, resolution_first)) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::proposal_resolution_drift);
      output = {};
      return MarriageProposalNativeReadbackResultV1::failed;
    }
    ResolvedCharacterV1 subject_second{};
    ResolvedCharacterV1 candidate_second{};
    bool subject_alliance_second = false;
    bool candidate_alliance_second = false;
    MarriageProposalNativeResolutionV1 resolution_second =
        MarriageProposalNativeResolutionV1::pending;
    if (ResolveCharacter(env, subject_character_id, subject_second) !=
            IdentityResultV1::available ||
        ResolveCharacter(env, candidate_character_id, candidate_second) !=
            IdentityResultV1::available ||
        subject_second.character != subject.character ||
        candidate_second.character != candidate.character ||
        !env.read_alliance_pair(
            env.alliance_context, subject_second.character,
            candidate_second.character, subject_alliance_second,
            candidate_alliance_second) ||
        subject_alliance_second != subject_alliance_first ||
        candidate_alliance_second != candidate_alliance_first) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::alliance_sample_drift);
      output = {};
      return MarriageProposalNativeReadbackResultV1::failed;
    }
    if (!env.read_proposal_resolution(
            env.proposal_resolution_context, subject_character_id,
            candidate_character_id, resolution_second) ||
        resolution_second != resolution_first) {
      SetFailure(binder,
                 MarriageProposalNativeBinderFailureV1::proposal_resolution_drift);
      output = {};
      return MarriageProposalNativeReadbackResultV1::failed;
    }
    output.subject_has_alliance_with_candidate = subject_alliance_second;
    output.candidate_has_alliance_with_subject = candidate_alliance_second;
    output.native_resolution = resolution_second;
    output.alliance_state_ready = true;
  }
  MarriageProposalReceiptFrameV1 after{};
  if (!env.capture_receipt_frame(env.receipt_frame_context, after) ||
      after != before) {
    SetFailure(binder,
               MarriageProposalNativeBinderFailureV1::receipt_frame_drift);
    output = {};
    return MarriageProposalNativeReadbackResultV1::failed;
  }
  SetFailure(binder, MarriageProposalNativeBinderFailureV1::none);
  return MarriageProposalNativeReadbackResultV1::available;
}

MarriageProposalNativeBinderFailureV1 ReadMarriageProposalNativeBinderFailureV1(
    const MarriageProposalNativeBinderStateV1 &binder) noexcept {
  return static_cast<MarriageProposalNativeBinderFailureV1>(
      binder.last_failure.load(std::memory_order_acquire));
}

std::string_view MarriageProposalNativeBinderFailureKeyV1(
    MarriageProposalNativeBinderFailureV1 failure) noexcept {
  switch (failure) {
  case MarriageProposalNativeBinderFailureV1::none: return "none";
  case MarriageProposalNativeBinderFailureV1::exact_build_not_admitted: return "exact_build_not_admitted";
  case MarriageProposalNativeBinderFailureV1::native_binding_mismatch: return "native_binding_mismatch";
  case MarriageProposalNativeBinderFailureV1::native_signature_mismatch: return "native_signature_mismatch";
  case MarriageProposalNativeBinderFailureV1::memory_reader_unavailable: return "memory_reader_unavailable";
  case MarriageProposalNativeBinderFailureV1::ranked_container_lifecycle_not_certified: return "ranked_container_lifecycle_not_certified";
  case MarriageProposalNativeBinderFailureV1::outcome_classifier_not_certified: return "outcome_classifier_not_certified";
  case MarriageProposalNativeBinderFailureV1::source_adapter_lifecycle_unavailable: return "source_adapter_lifecycle_unavailable";
  case MarriageProposalNativeBinderFailureV1::action_submit_lifecycle_unavailable: return "action_submit_lifecycle_unavailable";
  case MarriageProposalNativeBinderFailureV1::receipt_frame_source_unavailable: return "receipt_frame_source_unavailable";
  case MarriageProposalNativeBinderFailureV1::alliance_readback_not_certified: return "alliance_readback_not_certified";
  case MarriageProposalNativeBinderFailureV1::proposal_resolution_not_certified: return "proposal_resolution_not_certified";
  case MarriageProposalNativeBinderFailureV1::invalid_submission: return "invalid_submission";
  case MarriageProposalNativeBinderFailureV1::character_storage_unavailable: return "character_storage_unavailable";
  case MarriageProposalNativeBinderFailureV1::character_identity_unavailable: return "character_identity_unavailable";
  case MarriageProposalNativeBinderFailureV1::interaction_unavailable: return "interaction_unavailable";
  case MarriageProposalNativeBinderFailureV1::redirected_roles_mismatch: return "redirected_roles_mismatch";
  case MarriageProposalNativeBinderFailureV1::context_construction_failed: return "context_construction_failed";
  case MarriageProposalNativeBinderFailureV1::context_roles_mismatch: return "context_roles_mismatch";
  case MarriageProposalNativeBinderFailureV1::complete_can_send_rejected: return "complete_can_send_rejected";
  case MarriageProposalNativeBinderFailureV1::recipient_answer_changed: return "recipient_answer_changed";
  case MarriageProposalNativeBinderFailureV1::command_construction_failed: return "command_construction_failed";
  case MarriageProposalNativeBinderFailureV1::command_identity_mismatch: return "command_identity_mismatch";
  case MarriageProposalNativeBinderFailureV1::command_queue_rejected: return "command_queue_rejected";
  case MarriageProposalNativeBinderFailureV1::family_array_invalid: return "family_array_invalid";
  case MarriageProposalNativeBinderFailureV1::family_identity_unavailable: return "family_identity_unavailable";
  case MarriageProposalNativeBinderFailureV1::relationship_sample_drift: return "relationship_sample_drift";
  case MarriageProposalNativeBinderFailureV1::receipt_frame_drift: return "receipt_frame_drift";
  case MarriageProposalNativeBinderFailureV1::alliance_sample_drift: return "alliance_sample_drift";
  case MarriageProposalNativeBinderFailureV1::proposal_resolution_drift: return "proposal_resolution_drift";
  }
  return "unknown";
}

} // namespace xar::bridge

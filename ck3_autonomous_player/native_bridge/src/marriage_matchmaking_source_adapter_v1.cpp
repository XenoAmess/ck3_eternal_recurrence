#include "xar_bridge/marriage_matchmaking_source_adapter_v1.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "marriage matchmaking source adapter is x64-only");

template <typename Value>
bool AddRva(std::uintptr_t module_base, std::uintptr_t rva,
            Value &output) noexcept {
  if (module_base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - module_base) {
    output = {};
    return false;
  }
  if constexpr (std::is_pointer_v<Value>) {
    output = reinterpret_cast<Value>(module_base + rva);
  } else {
    output = static_cast<Value>(module_base + rva);
  }
  return true;
}

void SetFailure(MarriageMatchmakingSourceAdapterStateV1 &state,
                MarriageMatchmakingSourceAdapterFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
                std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return environment.read_memory != nullptr && address != 0 &&
      output != nullptr && size != 0 &&
      environment.read_memory(environment.memory_context, address, output,
                              size);
}

template <typename Value>
bool ReadAt(const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset,
            Value &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    return false;
  }
  return ReadMemory(environment, base + offset, &output, sizeof(output));
}

bool ProductionBindingsMatch(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment) noexcept {
  const auto expected = BindMarriageMatchmakingSourceAdapterEnvironmentV1(
      environment.module_base, environment.exact_build_admitted,
      environment.admitted_executable_sha256);
  return environment.character_storage_slot_address ==
             expected.character_storage_slot_address &&
      environment.get_character_interaction_database ==
          expected.get_character_interaction_database &&
      environment.redirect_roles == expected.redirect_roles &&
      environment.construct_context == expected.construct_context &&
      environment.refresh_context == expected.refresh_context &&
      environment.finalize_context == expected.finalize_context &&
      environment.complete_can_send == expected.complete_can_send &&
      environment.recipient_ai_accept == expected.recipient_ai_accept &&
      environment.outer_answer == expected.outer_answer &&
      environment.destroy_context == expected.destroy_context;
}

MarriageMatchmakingSourceAdapterFailureV1 ValidateAdapter(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    bool require_ranked_bindings, bool require_outcome_binding) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kMarriageMatchmakingSourceAdapterExecutableSha256V1) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        exact_build_not_admitted;
  }
  if (native_entry_points !=
      BindMarriageMatchmakingNativeEntryPointsV1(environment.module_base)) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        native_entry_points_mismatch;
  }
  if (environment.read_memory == nullptr ||
      environment.character_storage_slot_address == 0 ||
      environment.get_character_interaction_database == nullptr ||
      environment.redirect_roles == nullptr ||
      environment.construct_context == nullptr ||
      environment.refresh_context == nullptr ||
      environment.finalize_context == nullptr ||
      environment.complete_can_send == nullptr ||
      environment.recipient_ai_accept == nullptr ||
      environment.outer_answer == nullptr ||
      environment.destroy_context == nullptr ||
      (require_ranked_bindings &&
       (environment.invoke_ranked_source == nullptr ||
        environment.read_ranked_container_view == nullptr ||
        environment.release_ranked_container == nullptr)) ||
      (require_outcome_binding && environment.classify_outcome == nullptr)) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        adapter_bindings_unavailable;
  }
  if (!environment.offline_fixture && !ProductionBindingsMatch(environment)) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        native_entry_points_mismatch;
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

struct ResolvedCharacterV1 {
  std::uintptr_t storage = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  std::uintptr_t character = 0;
};

MarriageMatchmakingSourceAdapterFailureV1 ResolveCharacter(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    std::uint32_t character_id, bool require_alive,
    ResolvedCharacterV1 &output) noexcept {
  output = {};
  if (!ReadMemory(environment, environment.character_storage_slot_address,
                  &output.storage, sizeof(output.storage)) ||
      output.storage == 0 ||
      !ReadAt(environment, output.storage,
              kMarriageCharacterStorageSlotsOffsetV1, output.slots) ||
      !ReadAt(environment, output.storage,
              kMarriageCharacterStorageCapacityOffsetV1, output.capacity) ||
      output.slots == 0 || output.capacity <= 0 ||
      output.capacity > kMarriageMaximumCharacterStorageCapacityV1) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        character_storage_unavailable;
  }
  const auto index = character_id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(output.capacity) ||
      index > ((std::numeric_limits<std::uintptr_t>::max)() -
               kMarriageCharacterStorageSlotObjectOffsetV1) /
          kMarriageCharacterStorageSlotStrideV1) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        character_identity_unavailable;
  }
  const auto slot_offset = static_cast<std::uintptr_t>(index) *
          kMarriageCharacterStorageSlotStrideV1 +
      kMarriageCharacterStorageSlotObjectOffsetV1;
  if (slot_offset >
      (std::numeric_limits<std::uintptr_t>::max)() - output.slots) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        character_identity_unavailable;
  }
  const auto slot_address = output.slots + slot_offset;
  std::int32_t resolved_id = -1;
  if (!ReadMemory(environment, slot_address, &output.character,
                  sizeof(output.character)) ||
      output.character == 0 ||
      !ReadAt(environment, output.character, kMarriageCharacterIdOffsetV1,
              resolved_id) ||
      static_cast<std::uint32_t>(resolved_id) != character_id) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        character_identity_unavailable;
  }
  if (require_alive) {
    std::uintptr_t death_data = 0;
    if (!ReadAt(environment, output.character,
                kMarriageCharacterDeathDataOffsetV1, death_data)) {
      return MarriageMatchmakingSourceAdapterFailureV1::
          character_identity_unavailable;
    }
    if (death_data != 0) {
      return MarriageMatchmakingSourceAdapterFailureV1::character_not_alive;
    }
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

MarriageMatchmakingSourceAdapterFailureV1 ResolveStrategy(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    const ResolvedCharacterV1 &subject, std::uint32_t subject_character_id,
    std::uintptr_t &strategy) noexcept {
  strategy = 0;
  std::uintptr_t living_data = 0;
  std::uintptr_t ready_owner = 0;
  std::uintptr_t source_character = 0;
  if (!ReadAt(environment, subject.character,
              kMarriageCharacterLivingDataOffsetV1, living_data) ||
      living_data == 0 ||
      !ReadAt(environment, living_data, kMarriageLivingDataStrategyOffsetV1,
              strategy) ||
      strategy == 0 ||
      !ReadAt(environment, strategy, kMarriageStrategyReadyOwnerOffsetV1,
              ready_owner) ||
      ready_owner == 0) {
    return MarriageMatchmakingSourceAdapterFailureV1::strategy_unavailable;
  }
  std::int32_t source_id = -1;
  if (!ReadAt(environment, strategy,
              kMarriageStrategySourceCharacterOffsetV1, source_character) ||
      source_character == 0 ||
      !ReadAt(environment, source_character, kMarriageCharacterIdOffsetV1,
              source_id) ||
      source_character != subject.character ||
      static_cast<std::uint32_t>(source_id) != subject_character_id) {
    return MarriageMatchmakingSourceAdapterFailureV1::
        strategy_identity_mismatch;
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

MarriageMatchmakingSourceAdapterFailureV1 ResolveInteraction(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    std::uintptr_t &database, std::uintptr_t &interaction) noexcept {
  database = reinterpret_cast<std::uintptr_t>(
      environment.get_character_interaction_database());
  interaction = 0;
  if (database == 0 ||
      !ReadAt(environment, database, kArrangeMarriageInteractionOffsetV1,
              interaction) ||
      interaction == 0) {
    return MarriageMatchmakingSourceAdapterFailureV1::interaction_unavailable;
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

class RankedContainerLeaseV1 {
public:
  RankedContainerLeaseV1(
      const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
      std::uintptr_t token) noexcept
      : environment_(environment), token_(token) {}
  ~RankedContainerLeaseV1() {
    if (token_ != 0 && environment_.release_ranked_container != nullptr) {
      environment_.release_ranked_container(environment_.ranked_context,
                                             token_);
    }
  }
  RankedContainerLeaseV1(const RankedContainerLeaseV1 &) = delete;
  RankedContainerLeaseV1 &operator=(const RankedContainerLeaseV1 &) = delete;

private:
  const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment_;
  std::uintptr_t token_ = 0;
};

bool ValidContainer(const MarriageNativeRankedContainerViewV1 &view) noexcept {
  return view.capacity >= 0 && view.count >= 0 && view.count <= view.capacity &&
      view.capacity <= kMarriageMaximumNativeRankedRowsV1 &&
      (view.count == 0 || view.row_data != 0);
}

MarriageMatchmakingSourceAdapterFailureV1 ReadRankedRows(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    const MarriageNativeRankedContainerViewV1 &view, std::uint32_t limit,
    std::array<MarriageMatchmakingRankedRowV1,
               kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count,
    std::array<std::uintptr_t, kMarriageMatchmakingMaximumCandidatesV1>
        &candidate_pointers) noexcept {
  output = {};
  candidate_pointers = {};
  output_count = (std::min)(
      static_cast<std::uint32_t>(view.count), limit);
  for (std::uint32_t index = 0; index < output_count; ++index) {
    const auto row_offset =
        static_cast<std::uintptr_t>(index) *
        kMarriageNativeRankedRowStrideV1;
    if (row_offset > (std::numeric_limits<std::uintptr_t>::max)() -
                         view.row_data) {
      return MarriageMatchmakingSourceAdapterFailureV1::
          ranked_row_read_failed;
    }
    const auto row = view.row_data + row_offset;
    std::int32_t candidate_id = -1;
    if (!ReadAt(environment, row,
                kMarriageNativeRankedRowCharacterIdOffsetV1, candidate_id) ||
        !ReadAt(environment, row, kMarriageNativeRankedRowScoreOffsetV1,
                output[index].native_candidate_score) ||
        candidate_id == -1) {
      return MarriageMatchmakingSourceAdapterFailureV1::
          ranked_row_read_failed;
    }
    output[index].candidate_character_id =
        static_cast<std::uint32_t>(candidate_id);
    ResolvedCharacterV1 candidate{};
    const auto resolved = ResolveCharacter(
        environment, output[index].candidate_character_id, true, candidate);
    if (resolved != MarriageMatchmakingSourceAdapterFailureV1::none) {
      return MarriageMatchmakingSourceAdapterFailureV1::
          ranked_candidate_identity_unavailable;
    }
    candidate_pointers[index] = candidate.character;
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (output[prior].candidate_character_id ==
          output[index].candidate_character_id) {
        return MarriageMatchmakingSourceAdapterFailureV1::
            ranked_container_invalid;
      }
    }
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

struct alignas(16) MarriageContextStorageV1 {
  std::array<std::byte, kMarriageInteractionContextSizeV1 + 8> bytes{};
};

static_assert(sizeof(MarriageContextStorageV1) == 0x340);

class MarriageContextLeaseV1 {
public:
  MarriageContextLeaseV1(
      const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
      void *context) noexcept
      : environment_(environment), context_(context) {}
  ~MarriageContextLeaseV1() {
    if (context_ != nullptr && environment_.destroy_context != nullptr) {
      environment_.destroy_context(context_);
    }
  }
  MarriageContextLeaseV1(const MarriageContextLeaseV1 &) = delete;
  MarriageContextLeaseV1 &operator=(const MarriageContextLeaseV1 &) = delete;

private:
  const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment_;
  void *context_ = nullptr;
};

struct NativeRolesV1 {
  std::int32_t actor = -1;
  std::int32_t recipient = -1;
  std::int32_t secondary_actor = -1;
  std::int32_t secondary_recipient = -1;
  std::int32_t intermediary = -1;

  friend bool operator==(const NativeRolesV1 &, const NativeRolesV1 &) =
      default;
};

bool ReadContextRoles(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    std::uintptr_t context, NativeRolesV1 &output) noexcept {
  return ReadAt(environment, context, kMarriageContextActorIdOffsetV1,
                output.actor) &&
      ReadAt(environment, context, kMarriageContextRecipientIdOffsetV1,
             output.recipient) &&
      ReadAt(environment, context, kMarriageContextSecondaryActorIdOffsetV1,
             output.secondary_actor) &&
      ReadAt(environment, context,
             kMarriageContextSecondaryRecipientIdOffsetV1,
             output.secondary_recipient) &&
      ReadAt(environment, context, kMarriageContextIntermediaryIdOffsetV1,
             output.intermediary);
}

bool RolesMatchDirectRequest(const NativeRolesV1 &roles,
                             std::uint32_t subject_character_id,
                             std::uint32_t matchmaker_character_id,
                             std::uint32_t candidate_character_id) noexcept {
  return static_cast<std::uint32_t>(roles.actor) == matchmaker_character_id &&
      roles.recipient != -1 &&
      static_cast<std::uint32_t>(roles.secondary_actor) ==
          subject_character_id &&
      static_cast<std::uint32_t>(roles.secondary_recipient) ==
          candidate_character_id;
}

MarriageMatchmakingSourceAdapterFailureV1 ResolveRoles(
    const MarriageMatchmakingSourceAdapterEnvironmentV1 &environment,
    const NativeRolesV1 &roles,
    std::array<std::uintptr_t, 5> &resolved) noexcept {
  resolved = {};
  const std::array<std::int32_t, 5> ids{
      roles.actor, roles.recipient, roles.secondary_actor,
      roles.secondary_recipient, roles.intermediary};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    if (ids[index] == -1) continue;
    ResolvedCharacterV1 character{};
    const auto failure = ResolveCharacter(
        environment, static_cast<std::uint32_t>(ids[index]), true, character);
    if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
      return MarriageMatchmakingSourceAdapterFailureV1::
          context_roles_invalid;
    }
    resolved[index] = character.character;
  }
  return MarriageMatchmakingSourceAdapterFailureV1::none;
}

} // namespace

MarriageMatchmakingSourceAdapterEnvironmentV1
BindMarriageMatchmakingSourceAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageMatchmakingSourceAdapterEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.module_base = module_base;
  const bool complete =
      AddRva(module_base, kMarriageCharacterStorageSlotRvaV1,
             output.character_storage_slot_address) &&
      AddRva(module_base, kMarriageGetCharacterInteractionDatabaseRvaV1,
             output.get_character_interaction_database) &&
      AddRva(module_base, kMarriageRedirectRolesRvaV1,
             output.redirect_roles) &&
      AddRva(module_base, kMarriageConstructAllRolesContextRvaV1,
             output.construct_context) &&
      AddRva(module_base, kMarriageRefreshContextRvaV1,
             output.refresh_context) &&
      AddRva(module_base, kMarriageFinalizeContextRvaV1,
             output.finalize_context) &&
      AddRva(module_base, kMarriageCompleteCanSendRvaV1,
             output.complete_can_send) &&
      AddRva(module_base, kMarriageRecipientAiAcceptRvaV1,
             output.recipient_ai_accept) &&
      AddRva(module_base, kMarriageOuterAnswerRvaV1,
             output.outer_answer) &&
      AddRva(module_base, kMarriageDestroyContextRvaV1,
             output.destroy_context);
  if (!complete) {
    output = {};
    output.exact_build_admitted = exact_build_admitted;
    output.admitted_executable_sha256 = admitted_executable_sha256;
  }
  return output;
}

MarriageNativeSourceResultV1 ReadMarriageRankedCandidatesFromSourceAdapterV1(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t limit,
    std::array<MarriageMatchmakingRankedRowV1,
               kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count) noexcept {
  output = {};
  output_count = 0;
  if (context == nullptr || subject_character_id == 0 || limit == 0 ||
      limit > kMarriageMatchmakingMaximumCandidatesV1) {
    return MarriageNativeSourceResultV1::failed;
  }
  auto &state = *static_cast<MarriageMatchmakingSourceAdapterStateV1 *>(context);
  const auto &environment = state.environment;
  const auto admission = ValidateAdapter(environment, native_entry_points,
                                         true, false);
  if (admission != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, admission);
    return MarriageNativeSourceResultV1::failed;
  }

  ResolvedCharacterV1 subject_before{};
  auto failure = ResolveCharacter(environment, subject_character_id, true,
                                  subject_before);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeSourceResultV1::failed;
  }
  std::uintptr_t strategy_before = 0;
  failure = ResolveStrategy(environment, subject_before,
                            subject_character_id, strategy_before);
  if (failure ==
      MarriageMatchmakingSourceAdapterFailureV1::strategy_unavailable) {
    SetFailure(state, failure);
    return MarriageNativeSourceResultV1::ranked_source_unavailable;
  }
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeSourceResultV1::failed;
  }
  std::uintptr_t database_before = 0;
  std::uintptr_t interaction_before = 0;
  failure = ResolveInteraction(environment, database_before,
                               interaction_before);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeSourceResultV1::failed;
  }

  const MarriageNativeRankedInvocationV1 invocation{
      subject_before.character, strategy_before, interaction_before, limit,
      native_entry_points};
  std::uintptr_t container_token = 0;
  if (!environment.invoke_ranked_source(environment.ranked_context,
                                        invocation, container_token) ||
      container_token == 0) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_invocation_failed);
    return MarriageNativeSourceResultV1::failed;
  }
  RankedContainerLeaseV1 lease(environment, container_token);

  MarriageNativeRankedContainerViewV1 view_before{};
  if (!environment.read_ranked_container_view(
          environment.ranked_context, container_token, view_before)) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_container_unavailable);
    return MarriageNativeSourceResultV1::failed;
  }
  if (!ValidContainer(view_before)) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_container_invalid);
    return MarriageNativeSourceResultV1::failed;
  }

  std::array<std::uintptr_t, kMarriageMatchmakingMaximumCandidatesV1>
      candidate_pointers_before{};
  failure = ReadRankedRows(environment, view_before, limit, output,
                           output_count, candidate_pointers_before);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }

  MarriageNativeRankedContainerViewV1 view_after{};
  if (!environment.read_ranked_container_view(
          environment.ranked_context, container_token, view_after) ||
      view_before != view_after) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_container_drift);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }
  std::array<MarriageMatchmakingRankedRowV1,
             kMarriageMatchmakingMaximumCandidatesV1>
      rows_after{};
  std::array<std::uintptr_t, kMarriageMatchmakingMaximumCandidatesV1>
      candidate_pointers_after{};
  std::uint32_t count_after = 0;
  failure = ReadRankedRows(environment, view_after, limit, rows_after,
                           count_after, candidate_pointers_after);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none ||
      count_after != output_count || rows_after != output) {
    SetFailure(state, failure == MarriageMatchmakingSourceAdapterFailureV1::none
                          ? MarriageMatchmakingSourceAdapterFailureV1::
                                ranked_container_drift
                          : failure);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }
  if (candidate_pointers_before != candidate_pointers_after) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_candidate_identity_drift);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }

  MarriageNativeRankedContainerViewV1 view_final{};
  if (!environment.read_ranked_container_view(
          environment.ranked_context, container_token, view_final) ||
      view_final != view_before) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          ranked_container_drift);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }
  ResolvedCharacterV1 subject_after{};
  std::uintptr_t strategy_after = 0;
  std::uintptr_t database_after = 0;
  std::uintptr_t interaction_after = 0;
  failure = ResolveCharacter(environment, subject_character_id, true,
                             subject_after);
  if (failure == MarriageMatchmakingSourceAdapterFailureV1::none) {
    failure = ResolveStrategy(environment, subject_after,
                              subject_character_id, strategy_after);
  }
  if (failure == MarriageMatchmakingSourceAdapterFailureV1::none) {
    failure = ResolveInteraction(environment, database_after,
                                 interaction_after);
  }
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none ||
      subject_after.storage != subject_before.storage ||
      subject_after.slots != subject_before.slots ||
      subject_after.capacity != subject_before.capacity ||
      subject_after.character != subject_before.character ||
      strategy_after != strategy_before || database_after != database_before ||
      interaction_after != interaction_before) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          post_evaluation_identity_drift);
    output = {};
    output_count = 0;
    return MarriageNativeSourceResultV1::failed;
  }

  SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::none);
  return MarriageNativeSourceResultV1::available;
}

MarriageNativeEvaluationResultV1
EvaluateMarriageCandidateFromSourceAdapterV1(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id,
    MarriageMatchmakingPairEvaluationV1 &output) noexcept {
  output = {};
  if (context == nullptr || subject_character_id == 0 ||
      matchmaker_character_id != subject_character_id ||
      candidate_character_id == 0 ||
      candidate_character_id == subject_character_id) {
    return MarriageNativeEvaluationResultV1::failed;
  }
  auto &state = *static_cast<MarriageMatchmakingSourceAdapterStateV1 *>(context);
  const auto &environment = state.environment;
  auto failure = ValidateAdapter(environment, native_entry_points,
                                 false, true);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeEvaluationResultV1::failed;
  }

  ResolvedCharacterV1 subject_before{};
  ResolvedCharacterV1 candidate_before{};
  failure = ResolveCharacter(environment, subject_character_id, true,
                             subject_before);
  if (failure == MarriageMatchmakingSourceAdapterFailureV1::none) {
    failure = ResolveCharacter(environment, candidate_character_id, true,
                               candidate_before);
  }
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeEvaluationResultV1::failed;
  }
  std::uintptr_t database_before = 0;
  std::uintptr_t interaction_before = 0;
  failure = ResolveInteraction(environment, database_before,
                               interaction_before);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeEvaluationResultV1::failed;
  }

  NativeRolesV1 redirected{};
  redirected.actor = static_cast<std::int32_t>(matchmaker_character_id);
  redirected.recipient = static_cast<std::int32_t>(candidate_character_id);
  redirected.secondary_actor =
      static_cast<std::int32_t>(subject_character_id);
  redirected.secondary_recipient =
      static_cast<std::int32_t>(candidate_character_id);
  redirected.intermediary = -1;
  environment.redirect_roles(
      reinterpret_cast<void *>(interaction_before), &redirected.actor,
      &redirected.recipient, &redirected.secondary_actor,
      &redirected.secondary_recipient, &redirected.intermediary);
  if (!RolesMatchDirectRequest(redirected, subject_character_id,
                               matchmaker_character_id,
                               candidate_character_id)) {
    SetFailure(state,
               MarriageMatchmakingSourceAdapterFailureV1::context_roles_invalid);
    return MarriageNativeEvaluationResultV1::failed;
  }

  MarriageContextStorageV1 storage{};
  void *const native_context = storage.bytes.data();
  if (environment.construct_context(
          native_context, reinterpret_cast<void *>(interaction_before),
          redirected.actor, redirected.recipient, redirected.secondary_actor,
          redirected.secondary_recipient, redirected.intermediary, nullptr) !=
      native_context) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          context_construction_failed);
    return MarriageNativeEvaluationResultV1::failed;
  }
  MarriageContextLeaseV1 lease(environment, native_context);
  environment.refresh_context(native_context, true);
  environment.finalize_context(native_context);

  NativeRolesV1 roles_before{};
  if (!ReadContextRoles(environment,
                        reinterpret_cast<std::uintptr_t>(native_context),
                        roles_before) ||
      roles_before != redirected ||
      !RolesMatchDirectRequest(roles_before, subject_character_id,
                               matchmaker_character_id,
                               candidate_character_id)) {
    SetFailure(state,
               MarriageMatchmakingSourceAdapterFailureV1::context_roles_invalid);
    return MarriageNativeEvaluationResultV1::failed;
  }
  std::array<std::uintptr_t, 5> role_pointers_before{};
  failure = ResolveRoles(environment, roles_before, role_pointers_before);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return MarriageNativeEvaluationResultV1::failed;
  }

  const bool can_send =
      environment.complete_can_send(native_context, nullptr);
  std::int64_t ai_accept_raw = 0;
  if (environment.recipient_ai_accept(native_context, &ai_accept_raw) !=
      &ai_accept_raw) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          acceptance_score_failed);
    return MarriageNativeEvaluationResultV1::failed;
  }
  if (ai_accept_raw < (std::numeric_limits<std::int32_t>::min)() ||
      ai_accept_raw > (std::numeric_limits<std::int32_t>::max)()) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          acceptance_score_overflow);
    return MarriageNativeEvaluationResultV1::failed;
  }
  const auto answer_raw = environment.outer_answer(
      native_context, 1, 1, nullptr, nullptr);
  if (answer_raw >= 3) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          outer_answer_unavailable);
    return MarriageNativeEvaluationResultV1::failed;
  }
  MarriagePredictedOutcomeV1 outcome =
      MarriagePredictedOutcomeV1::unavailable;
  if (!environment.classify_outcome(
          environment.outcome_context, subject_before.character,
          candidate_before.character, native_context, outcome) ||
      outcome == MarriagePredictedOutcomeV1::unavailable) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          outcome_classification_failed);
    return MarriageNativeEvaluationResultV1::failed;
  }

  NativeRolesV1 roles_after{};
  std::array<std::uintptr_t, 5> role_pointers_after{};
  if (!ReadContextRoles(environment,
                        reinterpret_cast<std::uintptr_t>(native_context),
                        roles_after) ||
      roles_after != roles_before) {
    SetFailure(state,
               MarriageMatchmakingSourceAdapterFailureV1::context_roles_drift);
    return MarriageNativeEvaluationResultV1::failed;
  }
  failure = ResolveRoles(environment, roles_after, role_pointers_after);
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none ||
      role_pointers_after != role_pointers_before) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          post_evaluation_identity_drift);
    return MarriageNativeEvaluationResultV1::failed;
  }
  ResolvedCharacterV1 subject_after{};
  ResolvedCharacterV1 candidate_after{};
  std::uintptr_t database_after = 0;
  std::uintptr_t interaction_after = 0;
  failure = ResolveCharacter(environment, subject_character_id, true,
                             subject_after);
  if (failure == MarriageMatchmakingSourceAdapterFailureV1::none) {
    failure = ResolveCharacter(environment, candidate_character_id, true,
                               candidate_after);
  }
  if (failure == MarriageMatchmakingSourceAdapterFailureV1::none) {
    failure = ResolveInteraction(environment, database_after,
                                 interaction_after);
  }
  if (failure != MarriageMatchmakingSourceAdapterFailureV1::none ||
      subject_after.storage != subject_before.storage ||
      subject_after.slots != subject_before.slots ||
      subject_after.capacity != subject_before.capacity ||
      subject_after.character != subject_before.character ||
      candidate_after.character != candidate_before.character ||
      database_after != database_before ||
      interaction_after != interaction_before) {
    SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::
                          post_evaluation_identity_drift);
    return MarriageNativeEvaluationResultV1::failed;
  }

  output.roles.actor_character_id =
      static_cast<std::uint32_t>(roles_before.actor);
  output.roles.recipient_character_id =
      static_cast<std::uint32_t>(roles_before.recipient);
  output.roles.secondary_actor_character_id =
      static_cast<std::uint32_t>(roles_before.secondary_actor);
  output.roles.secondary_recipient_character_id =
      static_cast<std::uint32_t>(roles_before.secondary_recipient);
  output.roles.intermediary_character_id =
      roles_before.intermediary == -1
          ? 0
          : static_cast<std::uint32_t>(roles_before.intermediary);
  output.complete_can_send = can_send;
  output.complete_can_send_status_raw = can_send ? 1 : 0;
  output.recipient_ai_accept_raw = static_cast<std::int32_t>(ai_accept_raw);
  output.recipient_answer_status_raw =
      static_cast<std::int32_t>(answer_raw);
  output.recipient_answer_allows_send = answer_raw != 2;
  output.predicted_outcome = outcome;
  SetFailure(state, MarriageMatchmakingSourceAdapterFailureV1::none);
  return MarriageNativeEvaluationResultV1::available;
}

MarriageMatchmakingSourceAdapterFailureV1
ReadMarriageMatchmakingSourceAdapterFailureV1(
    const MarriageMatchmakingSourceAdapterStateV1 &state) noexcept {
  return static_cast<MarriageMatchmakingSourceAdapterFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

std::string_view MarriageMatchmakingSourceAdapterFailureKeyV1(
    MarriageMatchmakingSourceAdapterFailureV1 failure) noexcept {
  switch (failure) {
  case MarriageMatchmakingSourceAdapterFailureV1::none:
    return "none";
  case MarriageMatchmakingSourceAdapterFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case MarriageMatchmakingSourceAdapterFailureV1::
      native_entry_points_mismatch:
    return "native_entry_points_mismatch";
  case MarriageMatchmakingSourceAdapterFailureV1::
      adapter_bindings_unavailable:
    return "adapter_bindings_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::
      character_storage_unavailable:
    return "character_storage_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::
      character_identity_unavailable:
    return "character_identity_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::character_not_alive:
    return "character_not_alive";
  case MarriageMatchmakingSourceAdapterFailureV1::strategy_unavailable:
    return "strategy_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::
      strategy_identity_mismatch:
    return "strategy_identity_mismatch";
  case MarriageMatchmakingSourceAdapterFailureV1::interaction_unavailable:
    return "interaction_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::ranked_invocation_failed:
    return "ranked_invocation_failed";
  case MarriageMatchmakingSourceAdapterFailureV1::
      ranked_container_unavailable:
    return "ranked_container_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::ranked_container_invalid:
    return "ranked_container_invalid";
  case MarriageMatchmakingSourceAdapterFailureV1::ranked_container_drift:
    return "ranked_container_drift";
  case MarriageMatchmakingSourceAdapterFailureV1::ranked_row_read_failed:
    return "ranked_row_read_failed";
  case MarriageMatchmakingSourceAdapterFailureV1::
      ranked_candidate_identity_unavailable:
    return "ranked_candidate_identity_unavailable";
  case MarriageMatchmakingSourceAdapterFailureV1::
      ranked_candidate_identity_drift:
    return "ranked_candidate_identity_drift";
  case MarriageMatchmakingSourceAdapterFailureV1::
      context_construction_failed:
    return "context_construction_failed";
  case MarriageMatchmakingSourceAdapterFailureV1::context_roles_invalid:
    return "context_roles_invalid";
  case MarriageMatchmakingSourceAdapterFailureV1::context_roles_drift:
    return "context_roles_drift";
  case MarriageMatchmakingSourceAdapterFailureV1::acceptance_score_failed:
    return "acceptance_score_failed";
  case MarriageMatchmakingSourceAdapterFailureV1::acceptance_score_overflow:
    return "acceptance_score_overflow";
  case MarriageMatchmakingSourceAdapterFailureV1::
      outcome_classification_failed:
    return "outcome_classification_failed";
  case MarriageMatchmakingSourceAdapterFailureV1::
      post_evaluation_identity_drift:
    return "post_evaluation_identity_drift";
  case MarriageMatchmakingSourceAdapterFailureV1::
      outer_answer_unavailable:
    return "outer_answer_unavailable";
  }
  return "unknown";
}

} // namespace xar::bridge

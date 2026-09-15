#pragma once

#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMarriageMatchmakingSourceAdapterPrivateKeyV1 =
        "marriage_matchmaking_source_adapter_v1";
inline constexpr std::string_view
    kMarriageMatchmakingSourceAdapterExecutableSha256V1 =
        kMarriageMatchmakingObserverExecutableSha256V1;

inline constexpr std::uintptr_t kMarriageCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t
    kMarriageGetCharacterInteractionDatabaseRvaV1 = 0x0831890;
inline constexpr std::uintptr_t kMarriageRedirectRolesRvaV1 = 0x2C3C4C0;
inline constexpr std::uintptr_t kMarriageConstructAllRolesContextRvaV1 =
    0x2C3F000;
inline constexpr std::uintptr_t kMarriageRefreshContextRvaV1 = 0x2C40950;
inline constexpr std::uintptr_t kMarriageFinalizeContextRvaV1 = 0x2C40B20;
inline constexpr std::uintptr_t kMarriageDestroyContextRvaV1 = 0x2C3F380;

inline constexpr std::size_t kMarriageCharacterStorageSlotsOffsetV1 = 0x20;
inline constexpr std::size_t kMarriageCharacterStorageCapacityOffsetV1 =
    0x2C;
inline constexpr std::size_t kMarriageCharacterStorageSlotStrideV1 = 0x10;
inline constexpr std::size_t kMarriageCharacterStorageSlotObjectOffsetV1 =
    0x08;
inline constexpr std::size_t kMarriageCharacterIdOffsetV1 = 0x18;
inline constexpr std::size_t kMarriageCharacterLivingDataOffsetV1 = 0x1A8;
inline constexpr std::size_t kMarriageCharacterDeathDataOffsetV1 = 0x1C8;
inline constexpr std::size_t kMarriageLivingDataStrategyOffsetV1 = 0x278;
inline constexpr std::size_t kMarriageStrategySourceCharacterOffsetV1 = 0x18;
inline constexpr std::size_t kMarriageStrategyReadyOwnerOffsetV1 = 0x20;
inline constexpr std::size_t kArrangeMarriageInteractionOffsetV1 = 0xF48;
inline constexpr std::size_t kMarriageInteractionContextSizeV1 = 0x338;
inline constexpr std::size_t kMarriageContextActorIdOffsetV1 = 0x2D8;
inline constexpr std::size_t kMarriageContextRecipientIdOffsetV1 = 0x2DC;
inline constexpr std::size_t kMarriageContextSecondaryActorIdOffsetV1 =
    0x2E0;
inline constexpr std::size_t kMarriageContextSecondaryRecipientIdOffsetV1 =
    0x2E4;
inline constexpr std::size_t kMarriageContextIntermediaryIdOffsetV1 = 0x2E8;
inline constexpr std::int32_t kMarriageMaximumCharacterStorageCapacityV1 =
    2'000'000;
inline constexpr std::int32_t kMarriageMaximumNativeRankedRowsV1 = 4096;

enum class MarriageMatchmakingSourceAdapterFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  native_entry_points_mismatch,
  adapter_bindings_unavailable,
  character_storage_unavailable,
  character_identity_unavailable,
  character_not_alive,
  strategy_unavailable,
  strategy_identity_mismatch,
  interaction_unavailable,
  ranked_invocation_failed,
  ranked_container_unavailable,
  ranked_container_invalid,
  ranked_container_drift,
  ranked_row_read_failed,
  ranked_candidate_identity_unavailable,
  ranked_candidate_identity_drift,
  context_construction_failed,
  context_roles_invalid,
  context_roles_drift,
  acceptance_score_failed,
  acceptance_score_overflow,
  outcome_classification_failed,
  post_evaluation_identity_drift,
  outer_answer_unavailable,
};

struct MarriageNativeRankedContainerViewV1 {
  std::uintptr_t row_data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;

  friend bool operator==(const MarriageNativeRankedContainerViewV1 &,
                         const MarriageNativeRankedContainerViewV1 &) =
      default;
};

struct MarriageNativeRankedInvocationV1 {
  std::uintptr_t subject_character = 0;
  std::uintptr_t strategy = 0;
  std::uintptr_t arrange_marriage_interaction = 0;
  std::uint32_t limit = 0;
  MarriageMatchmakingNativeEntryPointsV1 entry_points{};
};

using MarriageSourceAdapterMemoryReadV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;
using InvokeMarriageNativeRankedSourceV1 = bool (*)(
    void *context, const MarriageNativeRankedInvocationV1 &request,
    std::uintptr_t &container_token) noexcept;
using ReadMarriageNativeRankedContainerViewV1 = bool (*)(
    void *context, std::uintptr_t container_token,
    MarriageNativeRankedContainerViewV1 &output) noexcept;
using ReleaseMarriageNativeRankedContainerV1 = void (*)(
    void *context, std::uintptr_t container_token) noexcept;
using ClassifyMarriageNativeOutcomeV1 = bool (*)(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, const void *finalized_context,
    MarriagePredictedOutcomeV1 &output) noexcept;

using GetMarriageCharacterInteractionDatabaseV1 = void *(*)();
using RedirectMarriageCharacterInteractionRolesV1 = void (*)(
    void *interaction, std::int32_t *actor_character_id,
    std::int32_t *recipient_character_id,
    std::int32_t *secondary_actor_character_id,
    std::int32_t *secondary_recipient_character_id,
    std::int32_t *intermediary_character_id);
using ConstructMarriageCharacterInteractionContextV1 = void *(*)(
    void *context, void *interaction, std::int32_t actor_character_id,
    std::int32_t recipient_character_id,
    std::int32_t secondary_actor_character_id,
    std::int32_t secondary_recipient_character_id,
    std::int32_t intermediary_character_id, void *extra_context);
using RefreshMarriageCharacterInteractionContextV1 = void (*)(
    void *context, bool refresh);
using FinalizeMarriageCharacterInteractionContextV1 = void (*)(void *context);
using ValidateMarriageCharacterInteractionContextV1 = bool (*)(
    void *context, void *error_output);
using ReadMarriageCharacterInteractionAnswerScoreV1 = std::int64_t *(*)(
    void *context, std::int64_t *output);
using EvaluateMarriageCharacterInteractionAnswerV1 = std::uint8_t (*)(
    void *context, std::uint8_t answer_mode, std::uint8_t final_answer,
    void *error_sink_a, void *error_sink_b);
using DestroyMarriageCharacterInteractionContextV1 = void (*)(void *context);

struct MarriageMatchmakingSourceAdapterEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t character_storage_slot_address = 0;

  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;

  void *ranked_context = nullptr;
  InvokeMarriageNativeRankedSourceV1 invoke_ranked_source = nullptr;
  ReadMarriageNativeRankedContainerViewV1 read_ranked_container_view =
      nullptr;
  ReleaseMarriageNativeRankedContainerV1 release_ranked_container = nullptr;

  void *outcome_context = nullptr;
  ClassifyMarriageNativeOutcomeV1 classify_outcome = nullptr;

  GetMarriageCharacterInteractionDatabaseV1
      get_character_interaction_database = nullptr;
  RedirectMarriageCharacterInteractionRolesV1 redirect_roles = nullptr;
  ConstructMarriageCharacterInteractionContextV1 construct_context = nullptr;
  RefreshMarriageCharacterInteractionContextV1 refresh_context = nullptr;
  FinalizeMarriageCharacterInteractionContextV1 finalize_context = nullptr;
  ValidateMarriageCharacterInteractionContextV1 complete_can_send = nullptr;
  ReadMarriageCharacterInteractionAnswerScoreV1 recipient_ai_accept = nullptr;
  EvaluateMarriageCharacterInteractionAnswerV1 outer_answer = nullptr;
  DestroyMarriageCharacterInteractionContextV1 destroy_context = nullptr;
};

struct MarriageMatchmakingSourceAdapterStateV1 {
  MarriageMatchmakingSourceAdapterEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(
          MarriageMatchmakingSourceAdapterFailureV1::none)};
};

MarriageMatchmakingSourceAdapterEnvironmentV1
BindMarriageMatchmakingSourceAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

MarriageNativeSourceResultV1 ReadMarriageRankedCandidatesFromSourceAdapterV1(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t limit,
    std::array<MarriageMatchmakingRankedRowV1,
               kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count) noexcept;

MarriageNativeEvaluationResultV1
EvaluateMarriageCandidateFromSourceAdapterV1(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id,
    MarriageMatchmakingPairEvaluationV1 &output) noexcept;

MarriageMatchmakingSourceAdapterFailureV1
ReadMarriageMatchmakingSourceAdapterFailureV1(
    const MarriageMatchmakingSourceAdapterStateV1 &state) noexcept;

std::string_view MarriageMatchmakingSourceAdapterFailureKeyV1(
    MarriageMatchmakingSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::bridge

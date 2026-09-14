#pragma once

#include "xar_bridge/marriage_matchmaking_source_adapter_v1.hpp"
#include "xar_bridge/marriage_proposal_action_core_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageProposalNativeBinderPrivateKeyV1 =
    "marriage_proposal_native_binder_v1";
inline constexpr std::string_view
    kMarriageProposalNativeBinderExecutableSha256V1 =
        kMarriageProposalActionCoreExecutableSha256V1;

inline constexpr std::uintptr_t kMarriageCommandManagerRvaV1 = 0x57621F0;
inline constexpr std::uintptr_t kMarriageSubmitCommandRvaV1 = 0x0973E00;
inline constexpr std::uintptr_t
    kMarriageConstructSendInteractionCommandRvaV1 = 0x26B3220;
inline constexpr std::uintptr_t
    kMarriageSendInteractionPrimaryVtableRvaV1 = 0x40829F8;
inline constexpr std::uintptr_t
    kMarriageSendInteractionSecondaryVtableRvaV1 = 0x40829C8;

inline constexpr std::size_t kMarriageCharacterFamilyDataOffsetV1 = 0x1A0;
inline constexpr std::size_t kMarriageFamilyBetrothedIdOffsetV1 = 0x10;
inline constexpr std::size_t kMarriageFamilyPrimarySpouseIdOffsetV1 = 0x14;
inline constexpr std::size_t kMarriageFamilySpouseIdsOffsetV1 = 0x20;
inline constexpr std::size_t kMarriageNativeArrayDataOffsetV1 = 0x00;
inline constexpr std::size_t kMarriageNativeArrayCapacityOffsetV1 = 0x08;
inline constexpr std::size_t kMarriageNativeArrayCountOffsetV1 = 0x0C;
inline constexpr std::size_t kMarriageSendInteractionContextOffsetV1 = 0x20;
inline constexpr std::size_t kMarriageSendInteractionCommandSizeV1 = 0x368;
inline constexpr std::uint32_t kMarriageSendInteractionFlagsV1 = 0x0E;
inline constexpr std::int32_t kMarriageMaximumSpouseArrayCountV1 = 1'000'000;

enum class MarriageProposalNativeBinderFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  native_binding_mismatch,
  native_signature_mismatch,
  memory_reader_unavailable,
  ranked_container_lifecycle_not_certified,
  outcome_classifier_not_certified,
  source_adapter_lifecycle_unavailable,
  action_submit_lifecycle_unavailable,
  receipt_frame_source_unavailable,
  alliance_readback_not_certified,
  proposal_resolution_not_certified,
  invalid_submission,
  character_storage_unavailable,
  character_identity_unavailable,
  interaction_unavailable,
  redirected_roles_mismatch,
  context_construction_failed,
  context_roles_mismatch,
  complete_can_send_rejected,
  command_construction_failed,
  command_identity_mismatch,
  command_queue_rejected,
  family_array_invalid,
  family_identity_unavailable,
  relationship_sample_drift,
  receipt_frame_drift,
  alliance_sample_drift,
  proposal_resolution_drift,
};

enum class MarriageProposalNativeBindResultV1 : std::uint32_t {
  available = 0,
  blocked = 1,
  failed = 2,
};

enum class MarriageProposalNativeReadbackResultV1 : std::uint32_t {
  available = 0,
  blocked = 1,
  failed = 2,
};

using ConstructMarriageSendInteractionCommandV1 = void *(*)(
    void *command, const void *context);
using SubmitMarriageCommandV1 = bool (*)(void *manager, void *command,
                                         std::uint32_t channel_flags);

struct MarriageProposalReceiptFrameV1 {
  bool available = false;
  bool paused = false;
  std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;

  friend bool operator==(const MarriageProposalReceiptFrameV1 &,
                         const MarriageProposalReceiptFrameV1 &) = default;
};

using CaptureMarriageProposalReceiptFrameV1 = bool (*)(
    void *context, MarriageProposalReceiptFrameV1 &output) noexcept;
using ReadMarriageProposalAlliancePairV1 = bool (*)(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, bool &subject_has_candidate,
    bool &candidate_has_subject) noexcept;
using ReadMarriageProposalNativeResolutionV1 = bool (*)(
    void *context, std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalNativeResolutionV1 &output) noexcept;

struct MarriageProposalBilateralRelationshipV1 {
  std::uint32_t subject_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  bool subject_identity_round_trip = false;
  bool candidate_identity_round_trip = false;
  bool subject_alive = false;
  bool candidate_alive = false;
  bool subject_has_candidate_as_spouse = false;
  bool candidate_has_subject_as_spouse = false;
  bool subject_has_candidate_as_betrothed = false;
  bool candidate_has_subject_as_betrothed = false;

  friend bool operator==(const MarriageProposalBilateralRelationshipV1 &,
                         const MarriageProposalBilateralRelationshipV1 &) =
      default;
};

struct MarriageProposalNativeBinderEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;

  MarriageMatchmakingSourceAdapterEnvironmentV1 source_adapter{};

  void *command_manager = nullptr;
  SubmitMarriageCommandV1 submit_command = nullptr;
  ConstructMarriageSendInteractionCommandV1 construct_send_command = nullptr;
  std::uintptr_t send_command_primary_vtable = 0;
  std::uintptr_t send_command_secondary_vtable = 0;

  bool ranked_container_lifecycle_certified = false;
  bool outcome_classifier_certified = false;

  void *receipt_frame_context = nullptr;
  CaptureMarriageProposalReceiptFrameV1 capture_receipt_frame = nullptr;

  bool alliance_readback_certified = false;
  void *alliance_context = nullptr;
  ReadMarriageProposalAlliancePairV1 read_alliance_pair = nullptr;

  bool proposal_resolution_certified = false;
  void *proposal_resolution_context = nullptr;
  ReadMarriageProposalNativeResolutionV1 read_proposal_resolution = nullptr;
};

struct MarriageProposalNativeBinderStateV1 {
  MarriageProposalNativeBinderEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(
          MarriageProposalNativeBinderFailureV1::none)};
};

MarriageProposalNativeBinderEnvironmentV1
BindMarriageProposalNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

MarriageProposalNativeBindResultV1
ConfigureMarriageMatchmakingSourceAdapterFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    MarriageMatchmakingSourceAdapterStateV1 &source_adapter) noexcept;

MarriageProposalNativeBindResultV1
ConfigureMarriageProposalActionSubmitFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    MarriageProposalActionEnvironmentV1 &action_environment,
    SubmitMarriageProposalNativeV1 &submit_callback,
    void *&submit_context) noexcept;

MarriageProposalNativeSubmitResultV1
SubmitMarriageProposalFromNativeBinderV1(
    void *context, const MarriageProposalSubmissionV1 &submission) noexcept;

MarriageProposalNativeReadbackResultV1
ReadMarriageProposalBilateralRelationshipFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalBilateralRelationshipV1 &output) noexcept;

MarriageProposalNativeReadbackResultV1
ReadMarriageProposalRelationshipObservationFromNativeBinderV1(
    MarriageProposalNativeBinderStateV1 &binder,
    std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalRelationshipObservationV1 &output) noexcept;

MarriageProposalNativeBinderFailureV1 ReadMarriageProposalNativeBinderFailureV1(
    const MarriageProposalNativeBinderStateV1 &binder) noexcept;
std::string_view MarriageProposalNativeBinderFailureKeyV1(
    MarriageProposalNativeBinderFailureV1 failure) noexcept;

} // namespace xar::bridge

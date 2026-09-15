#pragma once

#include "xar_bridge/marriage_alliance_readback_adapter_v1.hpp"
#include "xar_bridge/marriage_native_outcome_classifier_v1.hpp"
#include "xar_bridge/marriage_proposal_resolution_journal_v1.hpp"
#include "xar_bridge/marriage_ranked_container_adapter_v1.hpp"

#include <atomic>
#include <cstdint>

namespace xar::bridge {

enum class MarriageSharedGlueFailureV1 : std::uint32_t {
  none = 0,
  already_installed,
  invalid_environment,
  ranked_configuration_failed,
  outcome_configuration_failed,
  alliance_configuration_failed,
  resolution_install_failed,
  resolution_configuration_failed,
  resolution_remove_failed,
  resolution_arm_failed,
  invalid_receipt_frame,
};

// Application main publishes a paused frame only after the native command
// edge has produced a new observable snapshot. Arm invalidates the preceding
// frame, so an ACK alone can never become receipt evidence.
struct MarriageSharedReceiptFrameSourceV1 {
  std::atomic_flag lock = ATOMIC_FLAG_INIT;
  MarriageProposalReceiptFrameV1 frame{};
  bool frame_ready = false;
  std::atomic<std::uint32_t> enabled{0};
};

struct MarriageSharedGlueInstallEnvironmentV1 {
  MarriageProposalNativeBinderEnvironmentV1 binder{};
  MarriageRankedContainerAdapterEnvironmentV1 ranked{};
  MarriageNativeOutcomeClassifierEnvironmentV1 outcome{};
  MarriageAllianceReadbackEnvironmentV1 alliance{};
  MarriageProposalResolutionJournalInstallEnvironmentV1 resolution{};
};

struct MarriageSharedGlueStateV1 {
  MarriageProposalNativeBinderStateV1 binder{};
  MarriageRankedContainerAdapterStateV1 ranked{};
  MarriageNativeOutcomeClassifierStateV1 outcome{};
  MarriageAllianceReadbackStateV1 alliance{};
  MarriageProposalResolutionJournalDetourStateV1 resolution{};
  MarriageSharedReceiptFrameSourceV1 receipt_frames{};
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(MarriageSharedGlueFailureV1::none)};
};

bool InstallMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageSharedGlueInstallEnvironmentV1 &environment) noexcept;

bool RemoveMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    bool primary_thread_suspended_proven) noexcept;

// Call at the last application-owned point before entering the native submit
// path. A successful arm clears the previous receipt frame.
bool ArmMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageProposalSubmissionV1 &submission,
    std::uintptr_t interaction_definition) noexcept;

bool PublishMarriageSharedReceiptFrameV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageProposalReceiptFrameV1 &frame) noexcept;

void InvalidateMarriageSharedReceiptFrameV1(
    MarriageSharedGlueStateV1 &state) noexcept;

bool CaptureMarriageSharedReceiptFrameV1(
    void *context, MarriageProposalReceiptFrameV1 &output) noexcept;

MarriageSharedGlueFailureV1 ReadMarriageSharedGlueFailureV1(
    const MarriageSharedGlueStateV1 &state) noexcept;

} // namespace xar::bridge

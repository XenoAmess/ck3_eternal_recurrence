#include "xar_bridge/marriage_shared_glue_v1.hpp"

#include <algorithm>

namespace xar::bridge {
namespace {

class ReceiptFrameLockV1 {
public:
  explicit ReceiptFrameLockV1(
      MarriageSharedReceiptFrameSourceV1 &source) noexcept
      : source_(source) {
    while (source_.lock.test_and_set(std::memory_order_acquire)) {
    }
  }

  ~ReceiptFrameLockV1() { source_.lock.clear(std::memory_order_release); }

  ReceiptFrameLockV1(const ReceiptFrameLockV1 &) = delete;
  ReceiptFrameLockV1 &operator=(const ReceiptFrameLockV1 &) = delete;

private:
  MarriageSharedReceiptFrameSourceV1 &source_;
};

void SetFailure(MarriageSharedGlueStateV1 &state,
                MarriageSharedGlueFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool SameModuleBase(
    const MarriageSharedGlueInstallEnvironmentV1 &environment) noexcept {
  return environment.ranked.module_base == environment.binder.module_base &&
      environment.outcome.module_base == environment.binder.module_base &&
      environment.alliance.module_base == environment.binder.module_base &&
      environment.resolution.module_base == environment.binder.module_base;
}

bool ValidEnvironment(
    const MarriageSharedGlueInstallEnvironmentV1 &environment) noexcept {
  const auto sha = kMarriageProposalNativeBinderExecutableSha256V1;
  return environment.binder.exact_build_admitted &&
      environment.ranked.exact_build_admitted &&
      environment.outcome.exact_build_admitted &&
      environment.alliance.exact_build_admitted &&
      environment.resolution.exact_build_admitted &&
      environment.binder.admitted_executable_sha256 == sha &&
      environment.ranked.admitted_executable_sha256 == sha &&
      environment.outcome.admitted_executable_sha256 == sha &&
      environment.alliance.admitted_executable_sha256 == sha &&
      environment.resolution.admitted_executable_sha256 == sha &&
      environment.ranked.offline_fixture ==
          environment.binder.offline_fixture &&
      environment.outcome.offline_fixture ==
          environment.binder.offline_fixture &&
      environment.alliance.offline_fixture ==
          environment.binder.offline_fixture &&
      environment.resolution.offline_fixture ==
          environment.binder.offline_fixture &&
      SameModuleBase(environment);
}

bool ValidReceiptFrame(const MarriageProposalReceiptFrameV1 &frame) noexcept {
  const auto end = std::find(frame.snapshot_id.begin(), frame.snapshot_id.end(),
                             '\0');
  if (!frame.available || !frame.paused || end == frame.snapshot_id.begin() ||
      end == frame.snapshot_id.end() || frame.public_revision == 0 ||
      frame.native_revision == 0 || frame.proof_epoch == 0 ||
      frame.date_raw <= 0) {
    return false;
  }
  return std::all_of(frame.snapshot_id.begin(), end, [](char character) {
    const auto byte = static_cast<unsigned char>(character);
    return byte >= 0x21 && byte <= 0x7E && character != '"' &&
        character != '\\';
  });
}

void DetachOwnedCallbacks(MarriageSharedGlueStateV1 &state) noexcept {
  auto &environment = state.binder.environment;
  environment.source_adapter.ranked_context = nullptr;
  environment.source_adapter.invoke_ranked_source = nullptr;
  environment.source_adapter.read_ranked_container_view = nullptr;
  environment.source_adapter.release_ranked_container = nullptr;
  environment.ranked_container_lifecycle_certified = false;
  environment.source_adapter.outcome_context = nullptr;
  environment.source_adapter.classify_outcome = nullptr;
  environment.outcome_classifier_certified = false;
  environment.alliance_context = nullptr;
  environment.read_alliance_pair = nullptr;
  environment.alliance_readback_certified = false;
  environment.proposal_resolution_context = nullptr;
  environment.read_proposal_resolution = nullptr;
  environment.proposal_resolution_certified = false;
  environment.receipt_frame_context = nullptr;
  environment.capture_receipt_frame = nullptr;
}

bool FailInstall(MarriageSharedGlueStateV1 &state,
                 MarriageSharedGlueFailureV1 failure) noexcept {
  state.receipt_frames.enabled.store(0, std::memory_order_release);
  DetachOwnedCallbacks(state);
  SetFailure(state, failure);
  return false;
}

} // namespace

bool InstallMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageSharedGlueInstallEnvironmentV1 &environment) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.resolution.installed.load(std::memory_order_acquire) != 0) {
    SetFailure(state, MarriageSharedGlueFailureV1::already_installed);
    return false;
  }
  if (!ValidEnvironment(environment)) {
    SetFailure(state, MarriageSharedGlueFailureV1::invalid_environment);
    return false;
  }

  state.binder.environment = environment.binder;
  state.ranked.environment = environment.ranked;
  state.outcome.environment = environment.outcome;
  state.alliance.environment = environment.alliance;
  InvalidateMarriageSharedReceiptFrameV1(state);
  state.binder.environment.receipt_frame_context = &state.receipt_frames;
  state.binder.environment.capture_receipt_frame =
      &CaptureMarriageSharedReceiptFrameV1;

  if (!ConfigureMarriageRankedContainerAdapterV1(state.ranked,
                                                  state.binder)) {
    return FailInstall(
        state, MarriageSharedGlueFailureV1::ranked_configuration_failed);
  }
  if (!ConfigureMarriageNativeOutcomeClassifierV1(state.outcome,
                                                    state.binder)) {
    return FailInstall(
        state, MarriageSharedGlueFailureV1::outcome_configuration_failed);
  }
  if (!ConfigureMarriageAllianceReadbackV1(state.alliance, state.binder)) {
    return FailInstall(
        state, MarriageSharedGlueFailureV1::alliance_configuration_failed);
  }
  if (!InstallMarriageProposalResolutionJournalV1(state.resolution,
                                                   environment.resolution)) {
    return FailInstall(state,
                       MarriageSharedGlueFailureV1::resolution_install_failed);
  }
  if (!ConfigureMarriageProposalResolutionJournalV1(state.resolution,
                                                     state.binder)) {
    const bool removed = RemoveMarriageProposalResolutionJournalV1(
        state.resolution,
        environment.resolution.primary_thread_suspended_proven);
    return FailInstall(
        state, removed
            ? MarriageSharedGlueFailureV1::resolution_configuration_failed
            : MarriageSharedGlueFailureV1::resolution_remove_failed);
  }

  state.receipt_frames.enabled.store(1, std::memory_order_release);
  state.installed.store(1, std::memory_order_release);
  SetFailure(state, MarriageSharedGlueFailureV1::none);
  return true;
}

bool RemoveMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) {
    SetFailure(state, MarriageSharedGlueFailureV1::none);
    return true;
  }
  state.receipt_frames.enabled.store(0, std::memory_order_release);
  if (!RemoveMarriageProposalResolutionJournalV1(
          state.resolution, primary_thread_suspended_proven)) {
    state.receipt_frames.enabled.store(1, std::memory_order_release);
    SetFailure(state, MarriageSharedGlueFailureV1::resolution_remove_failed);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  DetachOwnedCallbacks(state);
  InvalidateMarriageSharedReceiptFrameV1(state);
  SetFailure(state, MarriageSharedGlueFailureV1::none);
  return true;
}

bool ArmMarriageSharedGlueV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageProposalSubmissionV1 &submission,
    std::uintptr_t interaction_definition) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) {
    SetFailure(state, MarriageSharedGlueFailureV1::resolution_arm_failed);
    return false;
  }
  InvalidateMarriageSharedReceiptFrameV1(state);
  if (!ArmMarriageProposalResolutionJournalV1(
          state.resolution, submission, interaction_definition)) {
    SetFailure(state, MarriageSharedGlueFailureV1::resolution_arm_failed);
    return false;
  }
  SetFailure(state, MarriageSharedGlueFailureV1::none);
  return true;
}

bool PublishMarriageSharedReceiptFrameV1(
    MarriageSharedGlueStateV1 &state,
    const MarriageProposalReceiptFrameV1 &frame) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      state.receipt_frames.enabled.load(std::memory_order_acquire) == 0 ||
      !ValidReceiptFrame(frame)) {
    SetFailure(state, MarriageSharedGlueFailureV1::invalid_receipt_frame);
    return false;
  }
  {
    ReceiptFrameLockV1 guard(state.receipt_frames);
    state.receipt_frames.frame = frame;
    state.receipt_frames.frame_ready = true;
  }
  SetFailure(state, MarriageSharedGlueFailureV1::none);
  return true;
}

void InvalidateMarriageSharedReceiptFrameV1(
    MarriageSharedGlueStateV1 &state) noexcept {
  ReceiptFrameLockV1 guard(state.receipt_frames);
  state.receipt_frames.frame = {};
  state.receipt_frames.frame_ready = false;
}

bool CaptureMarriageSharedReceiptFrameV1(
    void *context, MarriageProposalReceiptFrameV1 &output) noexcept {
  output = {};
  if (context == nullptr) return false;
  auto &source = *static_cast<MarriageSharedReceiptFrameSourceV1 *>(context);
  if (source.enabled.load(std::memory_order_acquire) == 0) return false;
  ReceiptFrameLockV1 guard(source);
  if (source.enabled.load(std::memory_order_acquire) == 0 ||
      !source.frame_ready) {
    return false;
  }
  output = source.frame;
  return true;
}

MarriageSharedGlueFailureV1 ReadMarriageSharedGlueFailureV1(
    const MarriageSharedGlueStateV1 &state) noexcept {
  return static_cast<MarriageSharedGlueFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge

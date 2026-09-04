#pragma once

#include "xar_bridge/raiktor_war_bound_regiment_v1.hpp"

#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRaiktorWarBoundLossCandidateV1BackendId =
    "ck3-1.19.0.6-native-raiktor-war-bound-loss-candidate-v1";
inline constexpr std::string_view kRaiktorWarBoundLossCleanupV1Capability =
    "game.command.query-raiktor-war-bound-loss-cleanup-v1-N";
inline constexpr std::string_view kRaiktorWarBoundLossCleanupV1StepPrefix =
    "query-raiktor-war-bound-loss-cleanup-v1-";

enum class RaiktorWarBoundLossStatusV1 : std::uint8_t {
  unavailable = 0,
  cleanup_still_alive = 1,
  destroyed_boundary_loss_proven = 2,
};

enum class RaiktorWarBoundLossFailureV1 : std::uint8_t {
  none = 0,
  invalid_pre_termination_baseline,
  cleanup_read_unavailable,
  cleanup_contract_rejected,
};

// Private/default-OFF lifecycle state. "Pre" means the exact paused
// checkpoint immediately before a future termination action, not the initial
// spawn count. The current production query already supplies this strict,
// generation-safe observation; no authored soldier value is copied here.
struct RaiktorWarBoundLossBaselineV1 {
  RaiktorWarBoundRegimentObservationV1 frozen_active;
  std::int64_t pre_termination_soldiers = -1;

  friend bool operator==(const RaiktorWarBoundLossBaselineV1 &,
                         const RaiktorWarBoundLossBaselineV1 &) = default;
};

struct RaiktorWarBoundLossResultV1 {
  RaiktorWarBoundLossStatusV1 status =
      RaiktorWarBoundLossStatusV1::unavailable;
  RaiktorWarBoundLossFailureV1 failure =
      RaiktorWarBoundLossFailureV1::invalid_pre_termination_baseline;
  std::int32_t owner_character_id = -1;
  std::int32_t war_id = -1;
  std::int64_t pre_termination_soldiers = -1;
  std::int64_t current_at_pre_termination_soldiers = -1;
  std::int64_t post_termination_soldiers = -1;
  std::int64_t proven_boundary_soldiers_lost = -1;
  WarBoundRegimentCleanupStatus cleanup_status =
      WarBoundRegimentCleanupStatus::unavailable;
  bool pre_termination_checkpoint_ready = false;
  bool postwar_cleanup_ready = false;
  bool proven_boundary_loss_ready = false;
  bool source_specific_attribution_ready = false;
  bool termination_action_bound = false;
  bool public_terms_ready = false;
  RaiktorWarBoundRegimentObservationV1 strict_cleanup;

  friend bool operator==(const RaiktorWarBoundLossResultV1 &,
                         const RaiktorWarBoundLossResultV1 &) = default;
};

std::string_view RaiktorWarBoundLossFailureReasonV1(
    RaiktorWarBoundLossFailureV1 failure) noexcept;

bool FreezeRaiktorWarBoundLossBaselineV1(
    const RaiktorWarBoundRegimentObservationV1 &active,
    RaiktorWarBoundLossBaselineV1 &output) noexcept;

// Converts the exact generic terms projection back into the strict v1
// generation vector before retaining it. The transport/native revision is the
// revision stamped on the terms result that actually exposed this baseline.
bool FreezeRaiktorWarBoundLossBaselineV1(
    const game::WarRaiktorWarBoundCurrentSnapshot &active,
    std::uint64_t transport_native_revision,
    RaiktorWarBoundLossBaselineV1 &output) noexcept;

// Completes the paired read-only boundary. A surviving frozen persistent or
// current generation publishes typed cleanup_still_alive and deliberately
// leaves post/loss unavailable. Only complete destruction of every frozen
// generation proves post=0 and loss=the measured pre-termination baseline.
bool ApplyRaiktorWarBoundLossCleanupV1(
    const RaiktorWarBoundLossBaselineV1 &baseline,
    const RaiktorWarBoundPostwarFrameV1 &first_postwar_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_postwar_frame,
    const FrozenWarBoundRegimentCleanupObservation &cleanup,
    RaiktorWarBoundLossResultV1 &output) noexcept;

#if defined(XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1)
// Candidate-only exact-store reader. It retains no global state, queues no
// command, and is absent from the default DLL. The future runner must retain
// the baseline and independently bind the intervening termination action.
bool ReadRaiktorWarBoundLossCleanupV1(
    const Bindings &bindings,
    const RaiktorWarBoundLossBaselineV1 &baseline,
    const RaiktorWarBoundPostwarFrameV1 &first_postwar_frame,
    const RaiktorWarBoundPostwarFrameV1 &second_postwar_frame,
    RaiktorWarBoundLossResultV1 &output) noexcept;
#endif

// Serializes only the honest generic/source-unattributed cleanup observation.
// Measured boundary loss remains private lifecycle metadata and is not added
// to the public war-termination terms wire.
std::string SerializeRaiktorWarBoundLossCleanupV1(
    const RaiktorWarBoundLossResultV1 &value);

} // namespace xar::ck3_11906

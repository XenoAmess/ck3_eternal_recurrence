#pragma once

#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

// A one-off live candidate may enable the read-only verifier diagnostics, but
// it must not advertise the production action capability. Promotion is a
// separate reviewed source change after a retained exact-build paused
// source -> ACK -> independent later-query artifact has passed review.
#if defined(XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1)
inline constexpr bool
    kZhongguoScoreboardProductionCandidateEnabledV1 = true;
#else
inline constexpr bool
    kZhongguoScoreboardProductionCandidateEnabledV1 = false;
#endif

inline constexpr bool
    kZhongguoScoreboardActionV1ProductionCapabilityAdvertised = false;

inline constexpr std::string_view
    kZhongguoScoreboardActionV1PromotionEvidenceStatus =
        "paused_live_artifact_pending";

enum class ZhongguoScoreboardPostconditionResultV1 : std::uint32_t {
  verified = 0,
  ack_unavailable,
  post_state_unavailable,
  paused_binding_changed,
  provider_binding_changed,
  observation_not_advanced,
  semantic_state_unchanged,
  window_instance_changed,
  widget_projection_invalid,
  explicit_postcondition_failed,
};

struct ZhongguoScoreboardPostconditionProofV1 {
  ZhongguoScoreboardPostconditionResultV1 result =
      ZhongguoScoreboardPostconditionResultV1::ack_unavailable;
  std::string_view reason = "ack_unavailable";
  bool verified = false;
};

// Verify the only admissible production-success witness: an independent
// read-only scoreboard query performed after a verification-pending ACK.  The
// function never dispatches an action and never mutates the provider tracker.
ZhongguoScoreboardPostconditionProofV1
VerifyZhongguoScoreboardReadOnlyPostconditionV1(
    const game::ZhongguoScoreboardActionAckV1 &ack,
    const game::ZhongguoScoreboardStateV1 &post_state,
    std::uint64_t observed_public_revision,
    std::uint64_t observed_connection_generation) noexcept;

} // namespace xar::ck3_11906

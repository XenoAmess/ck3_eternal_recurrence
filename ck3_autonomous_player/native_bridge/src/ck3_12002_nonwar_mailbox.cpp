#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"

namespace xar::ck3_12002 {

void RegisterNonwarMailboxExecutorsV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &environment,
    const NonwarMailboxExecutorsV1 &executors) noexcept {
#if defined(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  environment.permitted_executor_trioquadragintary = executors.lifestyle;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  environment.permitted_executor_duoquadragintary = executors.construction;
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  environment.permitted_executor_octotrigintary = executors.ranked_marriage;
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  environment.permitted_executor_octoquadragintary = executors.alliance_projection;
  environment.permitted_executor_octosexagintary = executors.relationship;
#if defined(XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1)
  environment.permitted_executor_novemsexagintary = executors.marriage_submit;
#endif
#endif
  (void)environment;
  (void)executors;
}

} // namespace xar::ck3_12002

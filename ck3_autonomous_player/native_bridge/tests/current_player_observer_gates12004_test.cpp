#ifdef NDEBUG
#error "Finite assertion fixture must be compiled with NDEBUG undefined"
#endif
#include "current_player_observers12004.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include <cassert>
namespace obs=xar::ck3_12004::current_player_observers;
int main(){
#if defined(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1)
  constexpr bool read=true;
#else
  constexpr bool read=false;
#endif
#if defined(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1)
  constexpr bool action=true;
#else
  constexpr bool action=false;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
  constexpr bool ghw=true;
#else
  constexpr bool ghw=false;
#endif
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_step)==read);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_submit_step)==action);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_post_step)==action);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::ghw_step)==ghw);
  assert(!obs::IsCurrentPlayerObserverStep12004("query-player-ghw-permissions-v1-private-other"));
  xar::ck3_12002::NonwarMailboxExecutorsV1 executors{};
  xar::ck3_12002::PopulateNonwarRouterExecutors12004(executors);
  assert((executors.artifact_personal_read!=nullptr)==(read||action));
  assert((executors.artifact_personal_action!=nullptr)==action);
  assert((executors.ghw_permissions_read!=nullptr)==ghw);
  xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 environment{};
  xar::ck3_12002::RegisterNonwarMailboxExecutorsV1(environment,executors);
  assert(environment.permitted_executor_artifact_personal_read12004==executors.artifact_personal_read);
  assert(environment.permitted_executor_artifact_personal_action12004==executors.artifact_personal_action);
  assert(environment.permitted_executor_ghw_permissions_read12004==executors.ghw_permissions_read);
  if(read&&action)assert(executors.artifact_personal_read!=executors.artifact_personal_action);
}

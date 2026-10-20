#ifdef NDEBUG
#error B11 gate assertions must remain enabled
#endif
#include "b11_five_flag_profile.hpp"
#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "current_player_observers12004.hpp"
#include <array>
#include <cassert>
#include <cstdio>

extern "C" unsigned B11RouterCompiledMask() noexcept;
extern "C" unsigned B11RegistrarCompiledMask() noexcept;
extern "C" unsigned B11ProviderCompiledMask() noexcept;
namespace mt=xar::ck3_11906;
namespace obs=xar::ck3_12004::current_player_observers;
namespace actor=xar::ck3_12004::character_skill_effects;
namespace inventory=xar::ck3_12004::player_inventory_window;

int main() {
  constexpr unsigned mask=XAR_B11_PROFILE_MASK;
  assert(B11RouterCompiledMask()==mask);
  assert(B11RegistrarCompiledMask()==mask);
  assert(B11ProviderCompiledMask()==mask);
  const bool read=(mask&1)!=0,action=(mask&2)!=0,ghw=(mask&4)!=0;
  const bool effects=(mask&8)!=0,window=(mask&16)!=0;
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_step)==read);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_submit_step)==action);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::artifact_post_step)==action);
  assert(obs::IsCurrentPlayerObserverStep12004(obs::ghw_step)==ghw);
  assert(!obs::IsCurrentPlayerObserverStep12004("query-player-ghw-permissions-v1-private-other"));
  xar::ck3_12002::NonwarMailboxExecutorsV1 executors{};
  xar::ck3_12002::PopulateNonwarRouterExecutors12004(executors);
  const std::array<mt::MainThreadQueryExecutorV1,6> actual{
    executors.artifact_personal_read,executors.artifact_personal_action,
    executors.ghw_permissions_read,executors.character_skill_effects,
    executors.inventory_window_read,executors.inventory_window_open};
  const std::array<mt::MainThreadQueryExecutorV1,6> expected{
    read?&obs::ExecuteArtifactPersonalRead12004:nullptr,
    action?&obs::ExecuteArtifactPersonalAction12004:nullptr,
    ghw?&obs::ExecuteGhwPermissionsRead12004:nullptr,
    effects?&actor::Execute:nullptr,
    window?&inventory::ExecuteRead:nullptr,window?&inventory::ExecuteOpen:nullptr};
  assert(actual==expected);
  mt::MainThreadQueryInstallEnvironmentV1 environment{};
  xar::ck3_12002::RegisterNonwarMailboxExecutorsV1(environment,executors);
  const std::array<mt::MainThreadQueryExecutorV1,6> registered{
    environment.permitted_executor_artifact_personal_read12004,
    environment.permitted_executor_artifact_personal_action12004,
    environment.permitted_executor_ghw_permissions_read12004,
    environment.permitted_executor_character_skill_effect12004,
    environment.permitted_executor_player_inventory_window_read12004,
    environment.permitted_executor_player_inventory_window_open12004};
  assert(registered==expected);
  // Adversarial non-null inputs check that real registrar gates themselves,
  // independently of the router returning null for the disabled providers.
  xar::ck3_12002::NonwarMailboxExecutorsV1 supplied{};
  supplied.artifact_personal_read=&obs::ExecuteArtifactPersonalRead12004;
  supplied.artifact_personal_action=&obs::ExecuteArtifactPersonalAction12004;
  supplied.ghw_permissions_read=&obs::ExecuteGhwPermissionsRead12004;
  supplied.character_skill_effects=&actor::Execute;
  supplied.inventory_window_read=&inventory::ExecuteRead;
  supplied.inventory_window_open=&inventory::ExecuteOpen;
  mt::MainThreadQueryInstallEnvironmentV1 independently_gated{};
  xar::ck3_12002::RegisterNonwarMailboxExecutorsV1(independently_gated,supplied);
  assert(independently_gated.permitted_executor_artifact_personal_read12004==expected[0]);
  assert(independently_gated.permitted_executor_artifact_personal_action12004==expected[1]);
  assert(independently_gated.permitted_executor_ghw_permissions_read12004==expected[2]);
  assert(independently_gated.permitted_executor_character_skill_effect12004==expected[3]);
  assert(independently_gated.permitted_executor_player_inventory_window_read12004==expected[4]);
  assert(independently_gated.permitted_executor_player_inventory_window_open12004==expected[5]);
  std::printf("b11_five_flag_consumer profile=%u real_bodies=3\n",mask);
}

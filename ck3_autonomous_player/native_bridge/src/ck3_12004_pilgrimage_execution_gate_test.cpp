#include "ck3_12004_player_pilgrimage_execution_private_v1.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include <cstdlib>
#include <iostream>

namespace {
bool OldExecutor(void *, const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept { return true; }
#define REQUIRE(x) do { if (!(x)) { std::cerr << "failed " << __LINE__ << ": " #x "\n"; std::abort(); } } while(false)
}
int main() {
  using namespace xar::ck3_12002;
#if defined(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1)
  constexpr bool enabled = true;
#else
  constexpr bool enabled = false;
#endif
  REQUIRE(IsPlayerPilgrimageExecutionPrivate12004V1(kPilgrimagePlannerQuery12004V1) == enabled);
  REQUIRE(IsPlayerPilgrimageExecutionPrivate12004V1(kPilgrimagePlannerSubmit12004V1) == enabled);
  REQUIRE(!IsPlayerPilgrimageExecutionPrivate12004V1("query-player-pilgrimage-activities-v1-private"));
  NonwarMailboxExecutorsV1 executors{};
  PopulateNonwarRouterExecutors12004(executors);
  REQUIRE(executors.pilgrimage_execution == (enabled ? &ExecutePlayerPilgrimageExecutionPrivate12004V1 : nullptr));
  xar::ck3_11906::MainThreadQueryInstallEnvironmentV1 env{};
  env.permitted_executor_quattuorsexagintary = &OldExecutor;
  RegisterNonwarMailboxExecutorsV1(env, executors);
  REQUIRE(env.permitted_executor_player_pilgrimage_execution12004 == executors.pilgrimage_execution);
  REQUIRE(env.permitted_executor_quattuorsexagintary == &OldExecutor);
  std::cout << "actual production execution classifier/registration gate " << enabled << "\n";
}

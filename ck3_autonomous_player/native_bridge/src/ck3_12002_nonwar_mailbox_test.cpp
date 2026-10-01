#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"

#include <array>
#include <cassert>
#include <iostream>

namespace {
template <int N>
bool Executor(void *, const xar::ck3_11906::MainThreadExecutionStampV1 &) noexcept {
  return N != 0;
}
}

int main() {
  using namespace xar::ck3_12002;
  using ExecutorType = xar::ck3_11906::MainThreadQueryExecutorV1;
  std::array<ExecutorType, 14> typed{};
  typed.fill(&Executor<1>);
  typed.back() = &Executor<14>;
  auto environment = BindThreadRuntimeImage(0x100000, kExecutableSha256, typed);
  const auto profile = environment.build_profile;
  assert(profile != nullptr && profile == &ThreadRuntimeBuildProfile());
  assert(environment.permitted_executor_semantic12002 == &Executor<14>);
  environment.permitted_executor_quattuordenary = &Executor<114>;
  environment.permitted_executor_quintrigintary = &Executor<135>;
  const NonwarMailboxExecutorsV1 callbacks{
      &Executor<43>, &Executor<42>, &Executor<38>, &Executor<48>,
      &Executor<68>, &Executor<69>};
  RegisterNonwarMailboxExecutorsV1(environment, callbacks);
  assert(environment.build_profile == profile);
  assert(environment.permitted_executor == &Executor<1>);
  assert(environment.permitted_executor_quattuordenary == &Executor<114>);
  assert(environment.permitted_executor_quintrigintary == &Executor<135>);
  assert(environment.permitted_executor_semantic12002 == &Executor<14>);
#if defined(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  assert(environment.permitted_executor_trioquadragintary == callbacks.lifestyle);
#else
  assert(environment.permitted_executor_trioquadragintary == nullptr);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1)
  assert(environment.permitted_executor_duoquadragintary == callbacks.construction);
#else
  assert(environment.permitted_executor_duoquadragintary == nullptr);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1)
  assert(environment.permitted_executor_octotrigintary == callbacks.ranked_marriage);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  assert(environment.permitted_executor_octoquadragintary == callbacks.alliance_projection);
  assert(environment.permitted_executor_octosexagintary == callbacks.relationship);
#if defined(XAR_CK3_ENABLE_G2_M5_HEIR_MARRIAGE_PRIVATE_ACTION_V1)
  assert(environment.permitted_executor_novemsexagintary == callbacks.marriage_submit);
#endif
#endif
  auto wrong = BindThreadRuntimeImage(0x100000, "unsupported", typed);
  assert(wrong.build_profile == nullptr);
  std::cout << "PASS: production nonwar registration, selected private slots, retained14/35/semantic identity, exact12002 profile; no CK3 access\n";
}

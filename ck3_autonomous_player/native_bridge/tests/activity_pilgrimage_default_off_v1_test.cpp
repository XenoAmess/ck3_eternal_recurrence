#include "xar_bridge/activity_pilgrimage_destination_v1.hpp"
#include "xar_bridge/activity_pilgrimage_stage1_v1.hpp"
#include "xar_bridge/activity_pilgrimage_planner_open_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <cstdlib>

// Compile this target without XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1.
#if defined(XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1)
#error Default-off fixture must not enable the pilgrimage private action macro.
#endif
namespace {
bool TrapMemory(void *, std::uintptr_t, void *, std::size_t) noexcept { std::abort(); }
bool TrapFrame(void *, xar::bridge::ActivityPlannerDiagFrameV1 &) noexcept { std::abort(); }
std::uintptr_t TrapCast(void *, std::uintptr_t, std::uintptr_t, std::uintptr_t) noexcept { std::abort(); }
bool TrapVisible(void *, std::uintptr_t, std::uintptr_t, bool &) noexcept { std::abort(); }
bool TrapDispatch(void *, std::uintptr_t, std::uintptr_t) noexcept { std::abort(); }
bool TrapCanPlan(void *, std::uintptr_t, bool &) noexcept { std::abort(); }
}
int main() {
  using namespace xar::bridge;
  ActivityPlannerDiagFrameV1 frame{};
  ActivityPlannerDiagEnvironmentV1 armed{
      true, xar::ck3_12004::kExecutableSha256, 0x140000000, nullptr,
      &TrapMemory, &TrapFrame, &TrapCast, &TrapVisible};
  const auto open = OpenActivityPilgrimagePlannerV1(
      {armed, &TrapDispatch, &TrapCanPlan}, frame);
  ActivityPilgrimageStage1OptionEnvironmentV1 option{};
  option.diagnostic = armed;
  const auto confirm = ConfirmActivityPilgrimageStage1V1(option, frame);
  ActivityPilgrimageDestinationEnvironmentV1 destination{};
  destination.diagnostic = armed;
  const auto select = SelectActivityPilgrimageDestinationV1(destination, frame, 1);
  if (open.native_dispatch_invoked || confirm.submitted || select.submitted)
    std::abort();
}

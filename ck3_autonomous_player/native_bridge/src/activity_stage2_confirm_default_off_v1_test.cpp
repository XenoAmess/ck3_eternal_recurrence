#include "xar_bridge/activity_stage2_confirm_v1.hpp"

#include <cstdlib>
#include <iostream>

int main() {
  xar::bridge::ActivityStage2ConfirmEnvironmentV1 environment{};
  xar::bridge::ActivityPlannerDiagFrameV1 expected{};
  const auto result =
      xar::bridge::ConfirmActivityStage2V1(environment, expected);
  if (result.status !=
          xar::bridge::ActivityStage2ConfirmStatusV1::precondition_rejected ||
      result.submitted) {
    std::cerr << "default-off stage-2 confirm unexpectedly submitted\n";
    std::abort();
  }
  std::cout << "GREEN: private stage-2 confirm disabled by default\n";
}

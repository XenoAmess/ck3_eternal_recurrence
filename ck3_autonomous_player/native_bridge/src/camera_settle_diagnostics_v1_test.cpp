// Portable source fixture; compile/run only in a separately admitted build.
// No Windows, Game, mapping, title, or camera I/O is performed by this target.
#include "xar_bridge/camera_settle_diagnostics_v1.hpp"
#include <iostream>
#include <limits>
using namespace xar::presentation;
int main() {
  const std::array<float, 6> expected{1884, 0, 2362, 100, 1, 0};
  auto current = expected, target = expected;
  int checks = 0;
  auto check = [&](bool value, const char *name) {
    ++checks;
    if (!value) { std::cerr << "FAIL " << name << '\n'; return false; }
    return true;
  };
  auto absent = ObserveCameraSettleV1(expected, false, current, false, target);
  if (!check(absent.reason == 1 && absent.observation_flags == 0 &&
             absent.observed_current == std::array<float, 6>{} &&
             absent.observed_target == std::array<float, 6>{}, "current-read-fail")) return 1;
  auto target_fail = ObserveCameraSettleV1(expected, true, current, false, target);
  if (!check(target_fail.reason == 2 && target_fail.observation_flags == 5 &&
             target_fail.observed_current == current, "target-read-fail")) return 1;
  current[0] = std::numeric_limits<float>::quiet_NaN();
  auto nonfinite = ObserveCameraSettleV1(expected, true, current, true, target);
  if (!check(nonfinite.reason == 3 && nonfinite.observation_flags == 11 &&
             nonfinite.target_difference_mask == 0, "current-nonfinite")) return 1;
  target[2] += 1;
  auto priority = ObserveCameraSettleV1(expected, true, current, true, target);
  if (!check(priority.reason == 3 && priority.target_difference_mask == 0,
             "nonfinite-short-circuit-priority")) return 1;
  current = expected;
  for (std::size_t i = 0; i < 6; ++i) {
    target = expected; target[i] += 1;
    auto changed = ObserveCameraSettleV1(expected, true, current, true, target);
    if (!check(changed.reason == 4 && changed.observation_flags == 15 &&
               changed.target_difference_mask == (1U << i), "exact-component-difference")) return 1;
  }
  target = expected; target[5] = std::numeric_limits<float>::infinity();
  auto inf = ObserveCameraSettleV1(expected, true, current, true, target);
  if (!check(inf.reason == 4 && inf.observation_flags == 7 &&
             inf.target_difference_mask == 32, "target-nonfinite-difference")) return 1;
  target = expected; current[0] -= 50;
  auto moving = ObserveCameraSettleV1(expected, true, current, true, target);
  if (!check(moving.reason == 0 && moving.target_difference_mask == 0,
             "normal-interpolation-is-not-target-change")) return 1;
  current = expected;
  auto settled = ObserveCameraSettleV1(expected, true, current, true, target);
  if (!check(settled.reason == 0 && settled.observation_flags == 15,
             "settled-is-not-diagnostic-failure")) return 1;
  auto unread = ObserveCameraSettleV1(expected, true, current, false, target);
  if (!check(unread.observed_target == std::array<float, 6>{} &&
             !(unread.observation_flags & kSettleTargetReadV1),
             "unread-storage-is-not-observation")) return 1;
  std::cout << "PASS " << checks << " camera-settle-diagnostic checks\n";
  return checks == 14 ? 0 : 1;
}


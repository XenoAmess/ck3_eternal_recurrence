#include "xar_bridge/protocol.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

#include <cstddef>
#include <string>
#include <string_view>

namespace {

std::string ArmStep(std::size_t army_count) {
  std::string step{xar::ck3_11906::kTacticalDailySentinelArmPrefixV1};
  step += "2000000000-to-2000001080-speed-5-mode-terminal-a-";
  step += std::to_string(army_count);
  for (std::size_t index = 0; index < army_count; ++index) {
    step += '-';
    step += std::to_string(1'000'000'000U + index);
  }
  return step;
}

std::string ExecuteRequest(std::string_view step) {
  std::string request =
      "{\"type\":\"execute_step\",\"request_id\":\"sentinel-test\","
      "\"step\":\"";
  request += step;
  request += "\"}";
  return request;
}

bool TestLongSentinelStep(std::size_t army_count) {
  const auto step = ArmStep(army_count);
  if (step.size() <= xar::bridge::kMaximumControlStringBytes ||
      step.size() >
          xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1) {
    return false;
  }
  const auto request = ExecuteRequest(step);
  std::string extracted;
  return xar::bridge::JsonStringField(
             request, "step", extracted,
             xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1) &&
         extracted == step;
}

bool TestMaximumSentinelBound() {
  const auto step = ArmStep(
      xar::ck3_11906::kTacticalDailySentinelMaximumArmiesV1);
  if (step.size() !=
      xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1) {
    return false;
  }
  std::string extracted;
  return !xar::bridge::JsonStringField(
      ExecuteRequest(step + "0"), "step", extracted,
      xar::ck3_11906::kTacticalDailySentinelMaximumArmStepBytesV1);
}

bool TestControlFieldsRemainAt128Bytes() {
  std::string extracted;
  const std::string long_value(
      xar::bridge::kMaximumControlStringBytes + 1U, 'x');
  const std::string long_type = "{\"type\":\"" + long_value + "\"}";
  const std::string long_request_id =
      "{\"request_id\":\"" + long_value + "\"}";
  return !xar::bridge::JsonStringField(
             long_type, "type", extracted,
             xar::bridge::kMaximumControlStringBytes) &&
         !xar::bridge::JsonStringField(
             long_request_id, "request_id", extracted,
             xar::bridge::kMaximumControlStringBytes);
}

} // namespace

int main() {
  return TestLongSentinelStep(6U) &&
                 TestLongSentinelStep(
                     xar::ck3_11906::kTacticalDailySentinelMaximumArmiesV1) &&
                 TestMaximumSentinelBound() &&
                 TestControlFieldsRemainAt128Bytes()
             ? 0
             : 1;
}

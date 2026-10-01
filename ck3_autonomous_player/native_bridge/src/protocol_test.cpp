#include "xar_bridge/protocol.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

#include <cstddef>
#include <string>
#include <string_view>
#include <iostream>

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

bool TestUnsignedField() {
  std::uint64_t value = 0;
  return xar::bridge::JsonUnsignedField(
             "{\"expected_revision\":42,\"tail\":true}",
             "expected_revision", value) &&
         value == 42 &&
         !xar::bridge::JsonUnsignedField(
             "{\"expected_revision\":-1}", "expected_revision", value) &&
         !xar::bridge::JsonUnsignedField(
             "{\"expected_revision\":42x}", "expected_revision", value);
}

bool TestBooleanField() {
  bool value = false;
  return xar::bridge::JsonBooleanField("{\"apply\":true,\"tail\":0}", "apply",
                                       value) &&
         value &&
         xar::bridge::JsonBooleanField("{\"apply\": false}", "apply", value) &&
         !value &&
         !xar::bridge::JsonBooleanField("{\"apply\":1}", "apply", value) &&
         !xar::bridge::JsonBooleanField("{\"apply\":truex}", "apply", value);
}

bool TestBoundedLargeFrames() {
  HANDLE input=nullptr,output=nullptr;
  if (!CreatePipe(&input,&output,nullptr,xar::bridge::kMaximumFrameBytes+4U)) return false;
  bool okay=true;
  for (const auto size : {std::size_t(1'217'950),std::size_t(xar::bridge::kMaximumFrameBytes)}) {
    std::string payload(size,'x');
    payload.front()='{';payload.back()='}';
    if (!xar::bridge::WriteFrame(output,payload)) {okay=false;break;}
    const auto read=xar::bridge::TryReadFrame(input);
    if (read.status!=xar::bridge::ReadStatus::frame || read.payload!=payload) {okay=false;break;}
  }
  const std::string over(xar::bridge::kMaximumFrameBytes+1U,'x');
  okay=!xar::bridge::WriteFrame(output,over)&&okay;
  const std::uint32_t invalid=xar::bridge::kMaximumFrameBytes+1U;
  DWORD written=0;
  okay=WriteFile(output,&invalid,sizeof(invalid),&written,nullptr)&&written==sizeof(invalid)&&okay;
  okay=xar::bridge::TryReadFrame(input).status==xar::bridge::ReadStatus::invalid&&okay;
  CloseHandle(input);CloseHandle(output);
  if(okay)std::cout<<"native local pipe: 1217950 bytes and exact 2 MiB roundtrip, cap+1 write/read rejected; offline only\n";
  return okay;
}

} // namespace

int main() {
  return TestLongSentinelStep(6U) &&
                 TestLongSentinelStep(
                     xar::ck3_11906::kTacticalDailySentinelMaximumArmiesV1) &&
                 TestMaximumSentinelBound() &&
                 TestControlFieldsRemainAt128Bytes() && TestUnsignedField() &&
                  TestBooleanField() && TestBoundedLargeFrames()
             ? 0
             : 1;
}

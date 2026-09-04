#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1_mailbox.hpp"

#include <cstdint>
#include <iostream>
#include <string_view>

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept {
  return false;
}
} // namespace xar::ck3_11906

namespace {

bool Expect(bool condition, std::string_view message) {
  if (!condition) std::cerr << message << '\n';
  return condition;
}
} // namespace

int main() {
  using namespace xar::ck3_11906;
  bool ok = true;
  ok &= Expect(ParseZhongguoCareerHcWorkforcePostconditionV1Step(
                   kZhongguoCareerHcWorkforcePostconditionV1Step),
               "canonical step was rejected");
  ok &= Expect(!ParseZhongguoCareerHcWorkforcePostconditionV1Step(
                   "query-zhongguo-career-hc-workforce"),
               "non-canonical step was accepted");

  constexpr std::string_view valid =
      R"({"type":"execute_step","protocol_version":1,"request_id":"req-1","step":"query-zhongguo-career-hc-workforce-postcondition-v1","expected_revision":41,"owner_character_id":147,"request_nonce":"career-hc.41"})";
  ZhongguoCareerHcWorkforcePostconditionRequestV1 request{};
  std::int32_t owner = -1;
  ok &= Expect(ParseZhongguoCareerHcWorkforcePostconditionRequestV1(
                   valid, request, owner),
               "valid strict mailbox request was rejected");
  ok &= Expect(request.expected_snapshot_revision == 41 &&
                   request.owner_character_id == 147 &&
                   request.request_nonce == "career-hc.41" && owner == 147,
               "valid request fields changed during parsing");

  constexpr std::string_view extra =
      R"({"type":"execute_step","protocol_version":1,"request_id":"req-1","step":"query-zhongguo-career-hc-workforce-postcondition-v1","expected_revision":41,"owner_character_id":147,"request_nonce":"career-hc.41","variable_name":"forbidden"})";
  ok &= Expect(!ParseZhongguoCareerHcWorkforcePostconditionRequestV1(
                   extra, request, owner),
               "generic variable input was accepted");
  ok &= Expect(ZhongguoCareerHcWorkforceFailureMessageV1(
                   MainThreadQueryWaitResultV1::timeout_cancelled_before_execution,
                   ZhongguoCareerHcWorkforceMailboxCompletionV1::not_executed,
                   true) == std::string_view(
                                "application-main career-HC/workforce query "
                                "timed out"),
               "queued timeout failure reason drifted");
  return ok ? 0 : 1;
}

#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1_mailbox.hpp"

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
  ok &= Expect(ParseZhongguoProjectsMetricsPostconditionV1Step(
                   kZhongguoProjectsMetricsPostconditionV1Step),
               "canonical step was rejected");
  ok &= Expect(!ParseZhongguoProjectsMetricsPostconditionV1Step(
                   "query-zhongguo-projects-metrics"),
               "non-canonical step was accepted");

  constexpr std::string_view valid =
      R"({"type":"execute_step","protocol_version":1,"request_id":"req-1","step":"query-zhongguo-projects-metrics-postcondition-v1","expected_revision":41,"owner_character_id":147,"request_nonce":"projects.41"})";
  ZhongguoProjectsMetricsPostconditionRequestV1 request{};
  std::int32_t owner = -1;
  ok &= Expect(ParseZhongguoProjectsMetricsPostconditionRequestV1(
                   valid, request, owner),
               "valid strict mailbox request was rejected");
  ok &= Expect(request.expected_snapshot_revision == 41 &&
                   request.owner_character_id == 147 &&
                   request.request_nonce == "projects.41" && owner == 147,
               "valid request fields changed during parsing");

  constexpr std::string_view extra =
      R"({"type":"execute_step","protocol_version":1,"request_id":"req-1","step":"query-zhongguo-projects-metrics-postcondition-v1","expected_revision":41,"owner_character_id":147,"request_nonce":"projects.41","variable_name":"forbidden"})";
  ok &= Expect(!ParseZhongguoProjectsMetricsPostconditionRequestV1(
                   extra, request, owner),
               "generic variable input was accepted");
  ok &= Expect(ZhongguoProjectsMetricsFailureMessageV1(
                   MainThreadQueryWaitResultV1::timeout_cancelled_before_execution,
                   ZhongguoProjectsMetricsMailboxCompletionV1::not_executed,
                   true) == std::string_view(
                                "application-main projects/metrics query "
                                "timed out"),
               "queued timeout failure reason drifted");
  return ok ? 0 : 1;
}

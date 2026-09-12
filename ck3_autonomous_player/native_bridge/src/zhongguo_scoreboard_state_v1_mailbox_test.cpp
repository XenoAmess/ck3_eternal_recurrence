#include "xar_bridge/zhongguo_scoreboard_state_v1_mailbox.hpp"

#include <iostream>
#include <string_view>

namespace {

bool Expect(bool condition, std::string_view message) {
  if (!condition) std::cerr << message << '\n';
  return condition;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, Snapshot &) noexcept { return false; }

game::ReadZhongguoScoreboardStateResultV1 ReadZhongguoScoreboardStateV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &,
    const ZhongguoScoreboardAccessV1 &,
    const ZhongguoScoreboardStateRequestV1 &,
    game::ZhongguoScoreboardStateV1 &) noexcept {
  return game::ReadZhongguoScoreboardStateResultV1::unavailable;
}

} // namespace xar::ck3_11906

int main() {
  constexpr std::string_view request =
      R"({"type":"execute_step","protocol_version":1,"request_id":"zg361.phase2.promo","step":"query-zhongguo-scoreboard-state-v1","expected_revision":77,"request_nonce":"scoreboard.query","expected_connection_generation":3})";
  xar::ck3_11906::ZhongguoScoreboardStateRequestV1 parsed{};
  bool ok = Expect(
      xar::ck3_11906::ParseZhongguoScoreboardStateRequestV1(request, parsed),
      "execute_step scoreboard state request was rejected");
  ok &= Expect(parsed.expected_snapshot_revision == 77 &&
                   parsed.request_nonce == "scoreboard.query" &&
                   parsed.connection_generation == 3,
               "scoreboard state request fields were not preserved");

  constexpr std::string_view legacy_request =
      R"({"type":"command","protocol_version":1,"request_id":"zg361.phase2.promo","step":"query-zhongguo-scoreboard-state-v1","expected_revision":77,"request_nonce":"scoreboard.query","expected_connection_generation":3})";
  ok &= Expect(
      !xar::ck3_11906::ParseZhongguoScoreboardStateRequestV1(legacy_request,
                                                             parsed),
      "legacy command request type was accepted");
  return ok ? 0 : 1;
}

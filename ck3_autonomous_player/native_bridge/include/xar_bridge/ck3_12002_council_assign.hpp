#pragma once
#include "xar_bridge/council_assign_councillor_action_v1.hpp"
#include "xar_bridge/ck3_12002.hpp"

namespace xar::ck3_12002 {
inline constexpr std::uintptr_t kCouncilAssignHelperRva12002 = 0x115AAA0;
using CouncilAssignEnvironment12002 = ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1;
using CouncilAssignAccess12002 = ck3_11906::CouncilAssignCouncillorActionAccessV1;
using CouncilAssignHelperFixture12002 = ck3_11906::CouncilAssignCouncillorNativeHelperOverrideV1;
struct CouncilAssignSubmit12002 {
  CouncilAssignEnvironment12002 environment{};
  void* fixture_context = nullptr;
  CouncilAssignHelperFixture12002 fixture_helper = nullptr;
  std::uint64_t invocation_count = 0;
};
CouncilAssignEnvironment12002 BindCouncilAssign12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool InvokeCouncilAssign12002(void* context,
    const game::CouncilAssignCouncillorNativeSubmissionV1& submission) noexcept;
game::CouncilAssignCouncillorAckStatusV1 ExecuteCouncilAssign12002(
    const CouncilAssignEnvironment12002& environment,
    const CouncilAssignAccess12002& access,
    const game::CouncilAssignCouncillorActionRequestV1& request,
    game::CouncilAssignCouncillorActionAckV1& ack) noexcept;
} // namespace xar::ck3_12002

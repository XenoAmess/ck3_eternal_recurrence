#pragma once
#include "xar_bridge/council_assign_councillor_action_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {
// Actual 1.20.0.4 helper body and command constructor were mapped in capture01.
inline constexpr std::string_view kCouncilAssignStewardPosition12004 = "councillor_steward";
inline constexpr std::string_view kCouncilAssignChancellorPosition12004 = "councillor_chancellor";
inline constexpr std::string_view kCouncilAssignChaplainPosition12004 = "councillor_court_chaplain";
inline constexpr std::uintptr_t kCouncilAssignHelperRva12004 = 0x115AAA0;
using CouncilAssignEnvironment12004 = ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1;
using CouncilAssignAccess12004 = ck3_11906::CouncilAssignCouncillorActionAccessV1;
using CouncilAssignHelperFixture12004 = ck3_11906::CouncilAssignCouncillorNativeHelperOverrideV1;
struct CouncilAssignSubmit12004 {
  CouncilAssignEnvironment12004 environment{};
  void* fixture_context = nullptr;
  CouncilAssignHelperFixture12004 fixture_helper = nullptr;
  std::uint64_t invocation_count = 0;
};
CouncilAssignEnvironment12004 BindCouncilAssign12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool InvokeCouncilAssign12004(void* context,
    const game::CouncilAssignCouncillorNativeSubmissionV1& submission) noexcept;
game::CouncilAssignCouncillorAckStatusV1 ExecuteCouncilAssign12004(
    const CouncilAssignEnvironment12004& environment,
    const CouncilAssignAccess12004& access,
    const game::CouncilAssignCouncillorActionRequestV1& request,
    game::CouncilAssignCouncillorActionAckV1& ack) noexcept;
} // namespace xar::ck3_12004

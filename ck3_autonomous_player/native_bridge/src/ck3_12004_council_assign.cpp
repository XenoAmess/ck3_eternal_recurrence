#include "xar_bridge/ck3_12004_council_assign.hpp"
#include <limits>

namespace xar::ck3_12004 {
CouncilAssignEnvironment12004 BindCouncilAssign12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  CouncilAssignEnvironment12004 result{};
  result.exact_build_admitted = base != 0 && sha == kExecutableSha256;
  result.admitted_executable_sha256 = sha;
  result.module_base = base;
  result.native_command_abi_certified = result.exact_build_admitted;
  return result;
}
bool InvokeCouncilAssign12004(void* raw,
    const game::CouncilAssignCouncillorNativeSubmissionV1& submission) noexcept {
  if (raw == nullptr) return false;
  auto& adapter = *static_cast<CouncilAssignSubmit12004*>(raw);
  const auto& env = adapter.environment;
  if (!env.exact_build_admitted || env.admitted_executable_sha256 != kExecutableSha256 ||
      !env.native_command_abi_certified || !env.private_candidate_admitted ||
      env.current_thread_id == 0 || env.current_thread_id != env.application_main_thread_id ||
      submission.owner_character_id <= 0 || submission.active_task_id <= 0 ||
      submission.candidate_character_id <= 0 ||
      submission.route == game::CouncilAssignCouncillorRouteV1::none) return false;
  if (env.offline_fixture) {
    if (env.module_base != 0 || adapter.fixture_helper == nullptr) return false;
    adapter.fixture_helper(adapter.fixture_context, submission.candidate_character_id,
                           submission.active_task_id);
  } else {
    if (adapter.fixture_helper != nullptr || env.module_base == 0 ||
        env.module_base > std::numeric_limits<std::uintptr_t>::max()-kCouncilAssignHelperRva12004)
      return false;
    using Helper = void (*)(std::int32_t, std::int32_t);
    reinterpret_cast<Helper>(env.module_base+kCouncilAssignHelperRva12004)(
        submission.candidate_character_id, submission.active_task_id);
  }
  ++adapter.invocation_count;
  return true;
}
game::CouncilAssignCouncillorAckStatusV1 ExecuteCouncilAssign12004(
    const CouncilAssignEnvironment12004& environment,
    const CouncilAssignAccess12004& access,
    const game::CouncilAssignCouncillorActionRequestV1& request,
    game::CouncilAssignCouncillorActionAckV1& ack) noexcept {
  // The helper carries the resolved task ID; Chaplain retains the same native
  // occupied CanConfirm and command-time CanSend appointment authority.
  const auto position = request.position_key == kCouncilAssignChancellorPosition12004 ?
      kCouncilAssignChancellorPosition12004 :
      request.position_key == kCouncilAssignChaplainPosition12004 ?
      kCouncilAssignChaplainPosition12004 :
      kCouncilAssignStewardPosition12004;
  return ck3_11906::ExecuteCouncilAssignCouncillorActionForBuildV1(environment,
      access, request, ack, kExecutableSha256, position);
}
} // namespace xar::ck3_12004

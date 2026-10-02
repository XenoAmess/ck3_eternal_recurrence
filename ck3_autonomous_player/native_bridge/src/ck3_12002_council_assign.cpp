#include "xar_bridge/ck3_12002_council_assign.hpp"
#include "xar_bridge/ck3_12002_council_candidates.hpp"
#include <limits>

namespace xar::ck3_12002 {
CouncilAssignEnvironment12002 BindCouncilAssign12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  CouncilAssignEnvironment12002 result{};
  result.exact_build_admitted = base != 0 && sha == kExecutableSha256;
  result.admitted_executable_sha256 = sha;
  result.module_base = base;
  result.native_command_abi_certified = result.exact_build_admitted;
  return result;
}
bool InvokeCouncilAssign12002(void* raw,
    const game::CouncilAssignCouncillorNativeSubmissionV1& submission) noexcept {
  if (raw == nullptr) return false;
  auto& adapter = *static_cast<CouncilAssignSubmit12002*>(raw);
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
        env.module_base > std::numeric_limits<std::uintptr_t>::max()-kCouncilAssignHelperRva12002)
      return false;
    using Helper = void (*)(std::int32_t, std::int32_t);
    reinterpret_cast<Helper>(env.module_base+kCouncilAssignHelperRva12002)(
        submission.candidate_character_id, submission.active_task_id);
  }
  ++adapter.invocation_count;
  return true;
}
game::CouncilAssignCouncillorAckStatusV1 ExecuteCouncilAssign12002(
    const CouncilAssignEnvironment12002& environment,
    const CouncilAssignAccess12002& access,
    const game::CouncilAssignCouncillorActionRequestV1& request,
    game::CouncilAssignCouncillorActionAckV1& ack) noexcept {
  // Existing Steward routes remain supported; the newly admitted Chancellor
  // path fills a current vacancy through the same native task-bound helper.
  const auto position = request.position_key == kCouncilCandidatesChancellorPosition12002 &&
      !request.expected_has_incumbent ? kCouncilCandidatesChancellorPosition12002 :
      kCouncilCandidatesStewardPosition12002;
  return ck3_11906::ExecuteCouncilAssignCouncillorActionForBuildV1(environment,
      access, request, ack, kExecutableSha256, position);
}
} // namespace xar::ck3_12002

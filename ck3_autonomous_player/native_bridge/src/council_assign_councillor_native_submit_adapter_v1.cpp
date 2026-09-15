#include "xar_bridge/council_assign_councillor_action_v1.hpp"

#include <limits>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

using DirectNativeHelper = void (*)(std::int32_t, std::int32_t);

bool AddRva(std::uintptr_t base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (base == 0 || rva > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + rva;
  return true;
}

bool ValidSubmission(
    const game::CouncilAssignCouncillorNativeSubmissionV1 &value) noexcept {
  if (value.route != game::CouncilAssignCouncillorRouteV1::assign_vacant &&
      value.route != game::CouncilAssignCouncillorRouteV1::replace_incumbent) {
    return false;
  }
  if (value.owner_character_id <= 0 || value.active_task_id <= 0 ||
      value.candidate_character_id <= 0) {
    return false;
  }
  if (value.route == game::CouncilAssignCouncillorRouteV1::assign_vacant) {
    return !value.had_incumbent && value.previous_incumbent_character_id == -1;
  }
  return value.had_incumbent && value.previous_incumbent_character_id > 0 &&
      value.previous_incumbent_character_id != value.candidate_character_id;
}

} // namespace

bool InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
    void *context,
    const game::CouncilAssignCouncillorNativeSubmissionV1 &submission) noexcept {
  auto *adapter =
      static_cast<CouncilAssignCouncillorNativeSubmitAdapterV1 *>(context);
  if (adapter == nullptr || !ValidSubmission(submission)) return false;
  const auto &environment = adapter->environment;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCouncilAssignCouncillorExecutableSha256V1 ||
      !environment.native_command_abi_certified ||
      !environment.private_candidate_admitted ||
      environment.current_thread_id == 0 ||
      environment.current_thread_id != environment.application_main_thread_id) {
    return false;
  }

  if (environment.offline_fixture) {
    if (environment.module_base != 0 || adapter->helper_override == nullptr) {
      return false;
    }
    adapter->helper_override(adapter->override_context,
                             submission.candidate_character_id,
                             submission.active_task_id);
    ++adapter->invocation_count;
    return true;
  }
  if (environment.module_base == 0 || adapter->helper_override != nullptr) {
    return false;
  }
  std::uintptr_t helper_address = 0;
  if (!AddRva(environment.module_base,
              kCouncilAssignCouncillorSendInteractionHelperRvaV1,
              helper_address)) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    reinterpret_cast<DirectNativeHelper>(helper_address)(
        submission.candidate_character_id, submission.active_task_id);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  reinterpret_cast<DirectNativeHelper>(helper_address)(
      submission.candidate_character_id, submission.active_task_id);
#endif
  ++adapter->invocation_count;
  return true;
}

} // namespace xar::ck3_11906

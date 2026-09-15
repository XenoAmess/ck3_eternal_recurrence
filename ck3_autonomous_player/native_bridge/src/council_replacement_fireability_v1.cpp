#include "xar_bridge/council_replacement_fireability_v1.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <limits>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kConfirmationSize = 0x170;
constexpr std::size_t kIncumbentIdOffset = 0x160;
constexpr std::size_t kActiveTaskIdOffset = 0x164;
using NativeCanConfirm = bool (*)(void *);

} // namespace

bool EvaluateCouncilReplacementFireabilityV1(
    const CouncilAssignCouncillorNativeEnvironmentV1 &environment,
    std::int32_t incumbent_character_id, std::int32_t active_task_id,
    bool &can_be_fired,
    CouncilReplacementCanConfirmOverrideV1 fixture_override,
    void *fixture_context) noexcept {
  can_be_fired = false;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCouncilAssignCouncillorExecutableSha256V1 ||
      !environment.native_command_abi_certified ||
      !environment.private_candidate_admitted ||
      environment.current_thread_id == 0 ||
      environment.current_thread_id != environment.application_main_thread_id ||
      incumbent_character_id <= 0 || active_task_id <= 0) {
    return false;
  }

  alignas(16) std::array<std::byte, kConfirmationSize> confirmation{};
  std::memcpy(confirmation.data() + kIncumbentIdOffset,
              &incumbent_character_id, sizeof(incumbent_character_id));
  std::memcpy(confirmation.data() + kActiveTaskIdOffset, &active_task_id,
              sizeof(active_task_id));

  if (environment.offline_fixture) {
    if (environment.module_base != 0 || fixture_override == nullptr) return false;
    can_be_fired = fixture_override(fixture_context, confirmation.data());
    return true;
  }
  if (environment.module_base == 0 || fixture_override != nullptr ||
      kCouncilAssignCouncillorConfirmationCanConfirmRvaV1 >
          (std::numeric_limits<std::uintptr_t>::max)() -
              environment.module_base) {
    return false;
  }
  const auto address = environment.module_base +
                       kCouncilAssignCouncillorConfirmationCanConfirmRvaV1;
#if defined(_MSC_VER)
  __try {
    can_be_fired = reinterpret_cast<NativeCanConfirm>(address)(
        confirmation.data());
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    can_be_fired = false;
    return false;
  }
#else
  can_be_fired = reinterpret_cast<NativeCanConfirm>(address)(
      confirmation.data());
#endif
  return true;
}

} // namespace xar::ck3_11906

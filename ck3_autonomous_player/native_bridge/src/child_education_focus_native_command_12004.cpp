#include "xar_bridge/child_education_focus_native_command_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::ck3_12004::lifestyle {
namespace {

using Result = PlayerLifestyleSelectionNativeDispatchResultV1;

// Actual focus clone 2895BD0 allocates 38 bytes and copies these fields.
// The common seeds match the existing actual4 stack-command foundation.
struct ChildEducationFocusCommand12004 {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t state_byte = 0;
  std::array<std::uint8_t, 3> padding_09{};
  std::uint32_t state_0c = 0;
  std::uint32_t state_10 = 0;
  std::uint32_t state_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uint32_t target_character_full_id = 0xFFFFFFFFU;
  std::uint32_t padding_24 = 0;
  std::uintptr_t education_focus_definition = 0;
  std::uint32_t controller_character_full_id = 0xFFFFFFFFU;
  std::uint32_t padding_34 = 0;
};

static_assert(sizeof(void *) == 8);
static_assert(sizeof(ChildEducationFocusCommand12004) == 0x38);
static_assert(offsetof(ChildEducationFocusCommand12004, primary_vtable) == 0);
static_assert(offsetof(ChildEducationFocusCommand12004, state_byte) == 8);
static_assert(offsetof(ChildEducationFocusCommand12004, secondary_vtable) == 0x18);
static_assert(offsetof(ChildEducationFocusCommand12004, target_character_full_id) == 0x20);
static_assert(offsetof(ChildEducationFocusCommand12004, education_focus_definition) == 0x28);
static_assert(offsetof(ChildEducationFocusCommand12004, controller_character_full_id) == 0x30);

bool NativeFocusValidatorReturned(
    PlayerLifestyleSelectionValidateCommandV1 validator,
    void *command, bool &native_result) noexcept {
#if defined(_MSC_VER)
  __try {
    native_result = validator(command, nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  native_result = validator(command, nullptr);
  return true;
#endif
}

std::optional<bool> InvokeFocusValidatorOnce(
    PlayerLifestyleSelectionValidateCommandV1 validator,
    void *command) noexcept {
  bool native_result = false;
  if (!NativeFocusValidatorReturned(validator, command, native_result)) {
    return std::nullopt;
  }
  return native_result;
}

bool ValidFocusRequest(std::uint32_t child, std::uint32_t controller,
                       std::uintptr_t definition) noexcept {
  return child != 0xFFFFFFFFU && controller != 0xFFFFFFFFU && definition != 0;
}

bool FocusExecutionReady(
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access) noexcept {
  return access.is_application_main_thread != nullptr &&
      access.is_paused != nullptr &&
      access.is_application_main_thread(access.execution_context) &&
      access.is_paused(access.execution_context);
}

ChildEducationFocusCommand12004 MakeFocusCommand(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    std::uint32_t child, std::uint32_t controller,
    std::uintptr_t definition) noexcept {
  ChildEducationFocusCommand12004 command{};
  command.primary_vtable = environment.focus_primary_vtable;
  command.secondary_vtable = environment.focus_secondary_vtable;
  command.target_character_full_id = child;
  command.education_focus_definition = definition;
  command.controller_character_full_id = controller;
  return command;
}

bool InvokeFocusSubmitOnce(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    void *command) noexcept {
#if defined(_MSC_VER)
  __try {
    // The existing exact wrapper synchronously invokes primary-vtable +40,
    // queues the native heap clone and cleans up only that owned clone.
    return environment.submit_command(
        environment.command_manager, command,
        kPlayerLifestyleSelectionCommandChannelFlagsV1);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return environment.submit_command(
      environment.command_manager, command,
      kPlayerLifestyleSelectionCommandChannelFlagsV1);
#endif
}

} // namespace

std::optional<bool> ValidateResolvedChildEducationFocusNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t actual_child_full_id,
    std::uint32_t actual_played_controller_full_id,
    std::uintptr_t resolved_education_focus_definition) noexcept {
  if (!ValidFocusRequest(actual_child_full_id, actual_played_controller_full_id,
                         resolved_education_focus_definition) ||
      !PlayerLifestyleSelectionNativeAdapterEnvironmentReady12004V1(environment) ||
      !FocusExecutionReady(access)) {
    return std::nullopt;
  }
  auto command = MakeFocusCommand(environment, actual_child_full_id,
                                 actual_played_controller_full_id,
                                 resolved_education_focus_definition);
  return InvokeFocusValidatorOnce(environment.validate_focus_command, &command);
}

PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedChildEducationFocusNativeAdapter12004V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t actual_child_full_id,
    std::uint32_t actual_played_controller_full_id,
    std::uintptr_t resolved_education_focus_definition) noexcept {
  if (!ValidFocusRequest(actual_child_full_id, actual_played_controller_full_id,
                         resolved_education_focus_definition)) {
    return Result::invalid_request;
  }
  if (!PlayerLifestyleSelectionNativeAdapterEnvironmentReady12004V1(environment)) {
    return Result::unavailable;
  }
  if (!FocusExecutionReady(access)) {
    return Result::application_main_paused_required;
  }

  auto command = MakeFocusCommand(environment, actual_child_full_id,
                                 actual_played_controller_full_id,
                                 resolved_education_focus_definition);

  const auto legal =
      InvokeFocusValidatorOnce(environment.validate_focus_command, &command);
  if (!legal.has_value()) {
    return Result::unavailable;
  }
  if (!*legal) {
    return Result::command_validator_rejected;
  }
  return InvokeFocusSubmitOnce(environment, &command)
      ? Result::submitted_verification_pending
      : Result::submit_rejected;
}

} // namespace xar::ck3_12004::lifestyle

#include "xar_bridge/ck3_12002_lifestyle.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::ck3_12002::lifestyle {
namespace {

bool SubmitStackCommand(void *manager, void *command, std::uint32_t flags) {
  if (manager == nullptr || command == nullptr) return false;
  const auto base = reinterpret_cast<std::uintptr_t>(manager) - ck3_12002::kCommandManagerRva;
  const auto bindings = ck3_12002::BindCommandImage(base, ck3_12002::kExecutableSha256);
  return ck3_12002::SubmitCommandCopy(bindings, command, flags) ==
      ck3_12002::CommandSubmitResult::submitted;
}

using DispatchResult = PlayerLifestyleSelectionNativeDispatchResultV1;
using Kind = game::PlayerLifestyleSelectionKindV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;

struct PerkSelectionCommandV1 {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t state_byte = 0;
  std::array<std::uint8_t, 3> padding_09{};
  std::uint32_t state_0c = 0;
  std::uint32_t state_10 = 0;
  std::uint32_t state_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::uint32_t padding_24 = 0;
  std::uintptr_t definition = 0;
};

struct FocusSelectionCommandV1 {
  PerkSelectionCommandV1 common{};
  std::uint32_t current_player_id = 0xFFFFFFFFU;
  std::uint32_t padding_34 = 0;
};

static_assert(sizeof(void *) == 8,
              "player lifestyle selection native adapter is x64-only");
static_assert(sizeof(PerkSelectionCommandV1) ==
              kPlayerLifestyleSelectionPerkCommandBytesV1);
static_assert(offsetof(PerkSelectionCommandV1, secondary_vtable) == 0x18);
static_assert(offsetof(PerkSelectionCommandV1, played_character_id) == 0x20);
static_assert(offsetof(PerkSelectionCommandV1, definition) == 0x28);
static_assert(sizeof(FocusSelectionCommandV1) ==
              kPlayerLifestyleSelectionFocusCommandBytesV1);
static_assert(offsetof(FocusSelectionCommandV1, current_player_id) == 0x30);

bool SameFunctionAddress(const void *function, std::uintptr_t address) noexcept {
  return function != nullptr &&
      reinterpret_cast<std::uintptr_t>(function) == address;
}





bool InvokeValidator(PlayerLifestyleSelectionValidateCommandV1 validator,
                     void *command) noexcept {
  if (validator == nullptr || command == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    return validator(command, nullptr);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return validator(command, nullptr);
#endif
}

bool InvokeSubmit(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    void *command) noexcept {
  if (environment.submit_command == nullptr ||
      environment.command_manager == nullptr || command == nullptr) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    // Exactly one invocation. The exact wrapper clones synchronously through
    // primary-vtable +0x40 and owns/destroys only that heap clone.
    return environment.submit_command(
        environment.command_manager, command,
        kPlayerLifestyleSelectionCommandChannelFlagsV1);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    // The wrapper is deliberately never retried after an exception.
    return false;
  }
#else
  return environment.submit_command(
      environment.command_manager, command,
      kPlayerLifestyleSelectionCommandChannelFlagsV1);
#endif
}







} // namespace

PlayerLifestyleSelectionNativeAdapterEnvironmentV1
BindPlayerLifestyleSelectionNativeAdapterEnvironment12002V1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  PlayerLifestyleSelectionNativeAdapterEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.module_base = module_base;
  if (!exact_build_admitted || module_base == 0 ||
      admitted_executable_sha256 !=
          kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1) {
    return output;
  }
  output.command_manager = reinterpret_cast<void *>(
      module_base + kPlayerLifestyleSelectionCommandManagerRvaV1);
  output.submit_command = &SubmitStackCommand;
  output.validate_focus_command =
      reinterpret_cast<PlayerLifestyleSelectionValidateCommandV1>(
          module_base + kPlayerLifestyleSelectionFocusValidatorRvaV1);
  output.validate_perk_command =
      reinterpret_cast<PlayerLifestyleSelectionValidateCommandV1>(
          module_base + kPlayerLifestyleSelectionPerkValidatorRvaV1);
  output.focus_primary_vtable =
      module_base + kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1;
  output.focus_secondary_vtable =
      module_base + kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1;
  output.perk_primary_vtable =
      module_base + kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1;
  output.perk_secondary_vtable =
      module_base + kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1;
  return output;
}

bool PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1
        &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1 ||
      environment.command_manager == nullptr ||
      environment.submit_command == nullptr ||
      environment.validate_focus_command == nullptr ||
      environment.validate_perk_command == nullptr ||
      environment.focus_primary_vtable !=
          environment.module_base +
              kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1 ||
      environment.focus_secondary_vtable !=
          environment.module_base +
              kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1 ||
      environment.perk_primary_vtable !=
          environment.module_base +
              kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1 ||
      environment.perk_secondary_vtable !=
          environment.module_base +
              kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1) {
    return false;
  }
  if (environment.offline_fixture_command) return true;
  return environment.command_manager == reinterpret_cast<void *>(
                                            environment.module_base +
                                            kPlayerLifestyleSelectionCommandManagerRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(environment.submit_command),
          reinterpret_cast<std::uintptr_t>(&SubmitStackCommand)) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(environment.validate_focus_command),
          environment.module_base +
              kPlayerLifestyleSelectionFocusValidatorRvaV1) &&
      SameFunctionAddress(
          reinterpret_cast<const void *>(environment.validate_perk_command),
          environment.module_base +
              kPlayerLifestyleSelectionPerkValidatorRvaV1);
}

PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1
        &environment) noexcept {
  auto output = BindPlayerLifestyleSelectionActionEnvironment12002V1(
      environment.module_base, environment.exact_build_admitted,
      environment.admitted_executable_sha256);
  if (PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(environment)) {
    output.command_abi_certified = !environment.offline_fixture_command;
    output.offline_fixture_command = environment.offline_fixture_command;
  }
  return output;
}



DispatchResult DispatchResolvedPlayerLifestylePerkNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t played_character_id,
    std::uintptr_t resolved_definition) noexcept {
  if (played_character_id == 0xFFFFFFFFU || resolved_definition == 0) {
    return DispatchResult::invalid_request;
  }
  if (!PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(environment)) {
    return DispatchResult::unavailable;
  }
  if (access.is_application_main_thread == nullptr ||
      access.is_paused == nullptr ||
      !access.is_application_main_thread(access.execution_context) ||
      !access.is_paused(access.execution_context)) {
    return DispatchResult::application_main_paused_required;
  }
  PerkSelectionCommandV1 command{};
  command.primary_vtable = environment.perk_primary_vtable;
  command.secondary_vtable = environment.perk_secondary_vtable;
  command.played_character_id = played_character_id;
  command.definition = resolved_definition;
  if (!InvokeValidator(environment.validate_perk_command, &command)) {
    return DispatchResult::command_validator_rejected;
  }
  return InvokeSubmit(environment, &command)
      ? DispatchResult::submitted_verification_pending
      : DispatchResult::submit_rejected;
}

DispatchResult DispatchResolvedPlayerLifestyleFocusNativeAdapter12002V1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t played_character_id,
    std::uintptr_t resolved_definition) noexcept {
  if (played_character_id == 0xFFFFFFFFU || resolved_definition == 0) {
    return DispatchResult::invalid_request;
  }
  if (!PlayerLifestyleSelectionNativeAdapterEnvironmentReady12002V1(environment)) {
    return DispatchResult::unavailable;
  }
  if (access.is_application_main_thread == nullptr ||
      access.is_paused == nullptr ||
      !access.is_application_main_thread(access.execution_context) ||
      !access.is_paused(access.execution_context)) {
    return DispatchResult::application_main_paused_required;
  }
  FocusSelectionCommandV1 command{};
  command.common.primary_vtable = environment.focus_primary_vtable;
  command.common.secondary_vtable = environment.focus_secondary_vtable;
  command.common.played_character_id = played_character_id;
  command.common.definition = resolved_definition;
  command.current_player_id = played_character_id;
  if (!InvokeValidator(environment.validate_focus_command, &command)) {
    return DispatchResult::command_validator_rejected;
  }
  return InvokeSubmit(environment, &command)
      ? DispatchResult::submitted_verification_pending
      : DispatchResult::submit_rejected;
}



std::string_view PlayerLifestyleSelectionNativeDispatchResultKeyV1(
    DispatchResult result) noexcept {
  switch (result) {
  case DispatchResult::unavailable:
    return "unavailable";
  case DispatchResult::invalid_request:
    return "invalid_request";
  case DispatchResult::application_main_paused_required:
    return "application_main_paused_required";
  case DispatchResult::exact_source_binding_mismatch:
    return "exact_source_binding_mismatch";
  case DispatchResult::source_read_rejected:
    return "source_read_rejected";
  case DispatchResult::target_not_stably_resolved:
    return "target_not_stably_resolved";
  case DispatchResult::final_legality_rejected:
    return "final_legality_rejected";
  case DispatchResult::command_validator_rejected:
    return "command_validator_rejected";
  case DispatchResult::submit_rejected:
    return "submit_rejected";
  case DispatchResult::submitted_verification_pending:
    return "submitted_verification_pending";
  }
  return "unavailable";
}

} // namespace xar::ck3_12002::lifestyle

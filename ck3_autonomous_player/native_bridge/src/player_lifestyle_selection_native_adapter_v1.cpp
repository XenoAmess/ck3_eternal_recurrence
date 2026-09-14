#include "xar_bridge/player_lifestyle_selection_native_adapter_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

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

bool ValidStableKey(const StableKey &value) noexcept {
  const auto key = PlayerLifestyleWindowStableKeyViewV1(value);
  if (key.empty()) return false;
  for (const char character : key) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool SourceBindingMatches(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uintptr_t requested_module_base) noexcept {
  const auto &source = access.source_environment;
  return access.source_state != nullptr &&
      access.source_access.read_memory != nullptr &&
      requested_module_base == environment.module_base &&
      source.module_base == environment.module_base &&
      source.exact_build_admitted == environment.exact_build_admitted &&
      source.admitted_executable_sha256 ==
          environment.admitted_executable_sha256 &&
      source.offline_fixture == environment.offline_fixture_command &&
      PlayerLifestyleWindowSourceAdapterEnvironmentReadyV1(source);
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

template <typename Row, std::size_t Size>
const Row *FindUniqueTarget(
    const std::array<Row, Size> &rows, std::uint32_t count,
    const StableKey &target) noexcept {
  if (count > Size) return nullptr;
  const Row *match = nullptr;
  for (std::uint32_t index = 0; index < count; ++index) {
    if (rows[index].key == target) {
      if (match != nullptr) return nullptr;
      match = &rows[index];
    }
  }
  return match;
}

DispatchResult DispatchFocus(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceSampleV1 &source,
    std::uint32_t played_character_id, const StableKey &target) noexcept {
  const auto *row =
      FindUniqueTarget(source.focus_rows, source.focus_count, target);
  if (row == nullptr || row->definition == 0 ||
      !row->pointer_in_captured_focus_span || !row->stable_key_round_trip ||
      !row->final_evaluator_invoked) {
    return DispatchResult::target_not_stably_resolved;
  }
  if (!row->can_select) return DispatchResult::final_legality_rejected;

  FocusSelectionCommandV1 command{};
  command.common.primary_vtable = environment.focus_primary_vtable;
  command.common.secondary_vtable = environment.focus_secondary_vtable;
  command.common.played_character_id = played_character_id;
  command.common.definition = row->definition;
  command.current_player_id = played_character_id;
  if (!InvokeValidator(environment.validate_focus_command, &command)) {
    return DispatchResult::command_validator_rejected;
  }
  return InvokeSubmit(environment, &command)
      ? DispatchResult::submitted_verification_pending
      : DispatchResult::submit_rejected;
}

DispatchResult DispatchPerk(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleWindowSourceSampleV1 &source,
    std::uint32_t played_character_id, const StableKey &target) noexcept {
  const auto *row = FindUniqueTarget(source.perk_rows, source.perk_count,
                                     target);
  if (row == nullptr || row->definition == 0 ||
      !row->pointer_in_exact_perk_database || !row->stable_key_round_trip ||
      !row->final_evaluator_invoked) {
    return DispatchResult::target_not_stably_resolved;
  }
  if (!row->can_select) return DispatchResult::final_legality_rejected;

  PerkSelectionCommandV1 command{};
  command.primary_vtable = environment.perk_primary_vtable;
  command.secondary_vtable = environment.perk_secondary_vtable;
  command.played_character_id = played_character_id;
  command.definition = row->definition;
  if (!InvokeValidator(environment.validate_perk_command, &command)) {
    return DispatchResult::command_validator_rejected;
  }
  return InvokeSubmit(environment, &command)
      ? DispatchResult::submitted_verification_pending
      : DispatchResult::submit_rejected;
}

} // namespace

PlayerLifestyleSelectionNativeAdapterEnvironmentV1
BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
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
  output.submit_command = reinterpret_cast<PlayerLifestyleSelectionSubmitCommandV1>(
      module_base + kPlayerLifestyleSelectionSubmitCommandRvaV1);
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

bool PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(
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
          environment.module_base +
              kPlayerLifestyleSelectionSubmitCommandRvaV1) &&
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
BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1
        &environment) noexcept {
  auto output = BindPlayerLifestyleSelectionActionEnvironmentV1(
      environment.module_base, environment.exact_build_admitted,
      environment.admitted_executable_sha256);
  if (PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(environment)) {
    output.command_abi_certified = !environment.offline_fixture_command;
    output.offline_fixture_command = environment.offline_fixture_command;
  }
  return output;
}

DispatchResult DispatchPlayerLifestyleSelectionNativeAdapterV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uintptr_t requested_module_base,
    std::uint32_t played_character_id, Kind kind,
    const StableKey &target_key) noexcept {
  if ((kind != Kind::focus && kind != Kind::perk) ||
      played_character_id == 0xFFFFFFFFU || !ValidStableKey(target_key)) {
    return DispatchResult::invalid_request;
  }
  if (!PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(environment)) {
    return DispatchResult::unavailable;
  }
  if (access.is_application_main_thread == nullptr ||
      access.is_paused == nullptr ||
      !access.is_application_main_thread(access.execution_context) ||
      !access.is_paused(access.execution_context)) {
    return DispatchResult::application_main_paused_required;
  }
  if (!SourceBindingMatches(environment, access, requested_module_base)) {
    return DispatchResult::exact_source_binding_mismatch;
  }

  PlayerLifestyleWindowSourceSampleV1 source{};
  const auto source_result = ReadPlayerLifestyleWindowSourceAdapterV1(
      *access.source_state, access.source_environment, access.source_access,
      requested_module_base, played_character_id, source);
  if (source_result != PlayerLifestyleWindowSourceReadResultV1::success ||
      source.bound_character_id != played_character_id ||
      !source.character_storage_round_trip) {
    return DispatchResult::source_read_rejected;
  }
  return kind == Kind::focus
      ? DispatchFocus(environment, source, played_character_id, target_key)
      : DispatchPerk(environment, source, played_character_id, target_key);
}

bool SubmitPlayerLifestyleSelectionNativeAdapterV1(
    void *context, Kind kind, const StableKey &target_key) noexcept {
  auto *const adapter =
      static_cast<PlayerLifestyleSelectionNativeAdapterContextV1 *>(context);
  if (adapter == nullptr) return false;
  adapter->last_result = DispatchPlayerLifestyleSelectionNativeAdapterV1(
      adapter->environment, adapter->access, adapter->requested_module_base,
      adapter->played_character_id, kind, target_key);
  return adapter->last_result ==
      DispatchResult::submitted_verification_pending;
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

} // namespace xar::ck3_11906

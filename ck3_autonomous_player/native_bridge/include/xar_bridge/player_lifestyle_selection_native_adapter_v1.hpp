#pragma once

#include "xar_bridge/player_lifestyle_selection_action_v1.hpp"
#include "xar_bridge/player_lifestyle_window_source_adapter_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kPlayerLifestyleSelectionNativeAdapterPrivateKeyV1 =
        "g2_player_lifestyle_selection_native_adapter_v1";
inline constexpr std::string_view
    kPlayerLifestyleSelectionNativeAdapterGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kPlayerLifestyleSelectionNativeAdapterExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr bool
    kPlayerLifestyleSelectionNativeAdapterAdvertisedByDefaultV1 = false;

inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionCommandManagerRvaV1 = 0x57621F0;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionSubmitCommandRvaV1 = 0x0973E00;

inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionPerkPrimaryVtableRvaV1 = 0x4323A50;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionPerkSecondaryVtableRvaV1 = 0x4323A20;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionPerkValidatorRvaV1 = 0x25DFAF0;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionPerkCloneRvaV1 = 0x25EC070;
inline constexpr std::size_t kPlayerLifestyleSelectionPerkCommandBytesV1 =
    0x30;

inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionFocusPrimaryVtableRvaV1 = 0x4323BE0;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionFocusSecondaryVtableRvaV1 = 0x4323BB0;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionFocusValidatorRvaV1 = 0x25DF570;
inline constexpr std::uintptr_t
    kPlayerLifestyleSelectionFocusCloneRvaV1 = 0x25EBF70;
inline constexpr std::size_t kPlayerLifestyleSelectionFocusCommandBytesV1 =
    0x38;
inline constexpr std::uint32_t
    kPlayerLifestyleSelectionCommandChannelFlagsV1 = 0x0E;

using PlayerLifestyleSelectionValidateCommandV1 = bool (*)(
    void *command, void *validation_context);
using PlayerLifestyleSelectionSubmitCommandV1 = bool (*)(
    void *manager, void *command, std::uint32_t channel_flags);
using PlayerLifestyleSelectionExecutionProbeV1 = bool (*)(
    void *context) noexcept;

enum class PlayerLifestyleSelectionNativeDispatchResultV1 : std::uint32_t {
  unavailable = 0,
  invalid_request,
  application_main_paused_required,
  exact_source_binding_mismatch,
  source_read_rejected,
  target_not_stably_resolved,
  final_legality_rejected,
  command_validator_rejected,
  submit_rejected,
  submitted_verification_pending,
};

struct PlayerLifestyleSelectionNativeAdapterEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture_command = false;
  void *command_manager = nullptr;
  PlayerLifestyleSelectionSubmitCommandV1 submit_command = nullptr;
  PlayerLifestyleSelectionValidateCommandV1 validate_focus_command = nullptr;
  PlayerLifestyleSelectionValidateCommandV1 validate_perk_command = nullptr;
  std::uintptr_t focus_primary_vtable = 0;
  std::uintptr_t focus_secondary_vtable = 0;
  std::uintptr_t perk_primary_vtable = 0;
  std::uintptr_t perk_secondary_vtable = 0;
};

struct PlayerLifestyleSelectionNativeAdapterAccessV1 {
  void *execution_context = nullptr;
  PlayerLifestyleSelectionExecutionProbeV1 is_application_main_thread =
      nullptr;
  PlayerLifestyleSelectionExecutionProbeV1 is_paused = nullptr;
  PlayerLifestyleWindowSourceAdapterStateV1 *source_state = nullptr;
  PlayerLifestyleWindowSourceAdapterEnvironmentV1 source_environment{};
  PlayerLifestyleWindowSourceAdapterAccessV1 source_access{};
};

// This is the context passed directly to LIFE6's submit_native callback.
// last_result is diagnostic only and is never evidence that CK3 applied the
// selection.
struct PlayerLifestyleSelectionNativeAdapterContextV1 {
  PlayerLifestyleSelectionNativeAdapterEnvironmentV1 environment{};
  PlayerLifestyleSelectionNativeAdapterAccessV1 access{};
  std::uintptr_t requested_module_base = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  PlayerLifestyleSelectionNativeDispatchResultV1 last_result =
      PlayerLifestyleSelectionNativeDispatchResultV1::unavailable;
};

PlayerLifestyleSelectionNativeAdapterEnvironmentV1
BindPlayerLifestyleSelectionNativeAdapterEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool PlayerLifestyleSelectionNativeAdapterEnvironmentReadyV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1
        &environment) noexcept;

// Converts a ready native adapter into LIFE6's command-ABI admission. The
// returned action environment still produces pending ACKs only.
PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentFromNativeAdapterV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1
        &environment) noexcept;

PlayerLifestyleSelectionNativeDispatchResultV1
DispatchPlayerLifestyleSelectionNativeAdapterV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uintptr_t requested_module_base,
    std::uint32_t played_character_id,
    game::PlayerLifestyleSelectionKindV1 kind,
    const game::PlayerLifestyleWindowStableKeyV1 &target_key) noexcept;

// Private window-independent perk dispatch. `resolved_definition` must come
// from a same-transaction exact database resolver such as LIFE4's stock perk
// legality source. This function performs the stock validator once more and
// submits exactly once; it does not accept focus commands.
PlayerLifestyleSelectionNativeDispatchResultV1
DispatchResolvedPlayerLifestylePerkNativeAdapterV1(
    const PlayerLifestyleSelectionNativeAdapterEnvironmentV1 &environment,
    const PlayerLifestyleSelectionNativeAdapterAccessV1 &access,
    std::uint32_t played_character_id, std::uintptr_t resolved_definition)
    noexcept;

// LIFE6-compatible thunk. true means the exact submit wrapper accepted one
// heap clone for verification. It never means the focus/perk was applied.
bool SubmitPlayerLifestyleSelectionNativeAdapterV1(
    void *context, game::PlayerLifestyleSelectionKindV1 kind,
    const game::PlayerLifestyleWindowStableKeyV1 &target_key) noexcept;

std::string_view PlayerLifestyleSelectionNativeDispatchResultKeyV1(
    PlayerLifestyleSelectionNativeDispatchResultV1 result) noexcept;

} // namespace xar::ck3_11906

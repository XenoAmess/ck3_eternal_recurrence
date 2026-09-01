#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoScoreboardActionV1 : std::uint32_t {
  open = 0,
  switch_managed = 1,
  switch_received = 2,
  switch_system = 3,
  close = 4,
  reopen = 5,
};

enum class ZhongguoScoreboardActionResultV1 : std::uint32_t {
  rejected = 0,
  acknowledged_verification_pending = 1,
};

struct ZhongguoScoreboardActionBindingV1 {
  std::uint64_t revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  std::string provider_session_id;
  std::uint64_t observation_sequence = 0;
  std::uint64_t observed_state_revision = 0;
  std::string tree_fingerprint_v1;
  std::string semantic_fingerprint_v1;
};

struct ZhongguoScoreboardActionRequestV1 {
  std::string request_nonce;
  ZhongguoScoreboardActionV1 action = ZhongguoScoreboardActionV1::open;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_connection_generation = 0;
  std::int32_t expected_player_character_id = -1;
  std::string expected_provider_session_id;
  std::uint64_t expected_observation_sequence = 0;
  std::uint64_t expected_observed_state_revision = 0;
  std::string expected_tree_fingerprint_v1;
  std::string expected_semantic_fingerprint_v1;
  std::string expected_window_instance_pointer;
  std::string expected_target_instance_pointer;
  std::string expected_target_vtable_pointer;
};

struct ZhongguoScoreboardActionTargetV1 {
  std::string stable_identity;
  std::string runtime_name;
  std::string instance_pointer;
  std::string vtable_pointer;
};

struct ZhongguoScoreboardActionPostconditionV1 {
  bool requires_independent_query = true;
  std::uint64_t minimum_observation_sequence = 0;
  std::uint64_t minimum_observed_state_revision = 0;
  std::string expected_provider_session_id;
  std::string expected_tree_fingerprint_v1;
  bool modal_effective_visible = false;
  std::string active_tab;
  bool active_tab_available = false;
  bool list_view_required = false;
  std::string expected_window_instance_pointer;
};

struct ZhongguoScoreboardActionAckV1 {
  ZhongguoScoreboardActionResultV1 result =
      ZhongguoScoreboardActionResultV1::rejected;
  bool accepted = false;
  std::string request_nonce;
  ZhongguoScoreboardActionV1 action = ZhongguoScoreboardActionV1::open;
  ZhongguoScoreboardActionBindingV1 source;
  std::string window_instance_pointer;
  ZhongguoScoreboardActionTargetV1 target;
  ZhongguoScoreboardActionPostconditionV1 expected_postcondition;
  bool native_handled = false;
  bool postcondition_verified = false;
  std::string rejection_reason;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoScoreboardActionV1Capability =
    "game.command.activate-zhongguo-scoreboard-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1Step =
    "activate-zhongguo-scoreboard-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1ConsumerId =
    "xar-autoplayer-zhongguo-scoreboard-action-v1";
inline constexpr std::string_view kZhongguoScoreboardActionV1AllowlistId =
    "zg361-scoreboard-named-widget-action-v1";

inline constexpr std::uintptr_t kZhongguoShortcutManagerActivateRva =
    0x36E1C40;
inline constexpr std::uintptr_t kZhongguoStrictDescendantRva = 0x369E620;
inline constexpr std::uintptr_t kZhongguoDeliverGuiEventRva = 0x36CB4A0;
inline constexpr std::uintptr_t kZhongguoShortcutEventVtableRva = 0x4507A78;
inline constexpr std::uintptr_t kZhongguoButtonBaseSlot13Rva = 0x36C69A0;
inline constexpr std::size_t kZhongguoGuiShortcutManagerOffset = 0x3E0;
inline constexpr std::size_t kZhongguoGuiModalVectorOffset = 0x290;
inline constexpr std::size_t kZhongguoGuiModalCountOffset = 0x29C;
inline constexpr std::size_t kZhongguoWidgetGuiContextOffset = 0xD8;
inline constexpr std::uint8_t kZhongguoWidgetShortcutRejectedMask = 0x0B;
inline constexpr std::size_t kZhongguoPrimaryCallbackGroupOffset = 0x3F8;
inline constexpr std::size_t kZhongguoFallbackCallbackGroupOffset = 0x338;
inline constexpr std::size_t kZhongguoCallbackGroupDataOffset = 0x00;
inline constexpr std::size_t kZhongguoCallbackGroupCountOffset = 0x0C;
inline constexpr std::size_t kZhongguoCallbackStride = 0x48;
inline constexpr std::size_t kZhongguoCallbackObjectOffset = 0x40;
inline constexpr std::size_t kZhongguoCallbackVtableSlot2Offset = 0x10;
inline constexpr std::size_t kZhongguoShortcutPimplSize = 0x50;
inline constexpr std::size_t kZhongguoShortcutPimplTargetOffset = 0x48;
inline constexpr std::size_t kZhongguoShortcutCStringSize = 0x20;
inline constexpr std::size_t kZhongguoShortcutCStringLengthOffset = 0x10;
inline constexpr std::size_t kZhongguoShortcutCStringCapacityOffset = 0x18;
inline constexpr std::uint64_t kZhongguoShortcutCStringEmptyCapacity = 0x0F;
inline constexpr std::size_t kZhongguoExactImageSize = 0x5C2D000;
inline constexpr std::int32_t kZhongguoMaximumModalReceivers = 256;
inline constexpr std::int32_t kZhongguoMaximumCallbacks = 256;

// Exact CPdxGuiShortcutManager path for CK3 1.19.0.6.  The CString and pimpl
// arguments are borrowed for the call; the native routine deep-copies and
// destroys its own event text, while reading only pimpl +0x48 as the target.
using NativeZhongguoShortcutManagerActivateV1 = bool(__fastcall *)(
    void *, std::uint32_t, const void *, void *);
using NativeZhongguoStrictDescendantV1 = bool(__fastcall *)(void *, void *);

struct ZhongguoScoreboardActionDispatchEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **gui_global_slot = nullptr;
  NativeZhongguoShortcutManagerActivateV1 activate_shortcut = nullptr;
  NativeZhongguoStrictDescendantV1 is_strict_descendant = nullptr;
  void *button_base_slot13 = nullptr;
};

using DispatchZhongguoScoreboardActionV1 = bool (*)(
    void *, game::ZhongguoScoreboardActionV1, std::string_view,
    std::string_view, std::string_view, std::string_view,
    bool &) noexcept;

struct ZhongguoScoreboardActionAccessV1 {
  void *context = nullptr;
  DispatchZhongguoScoreboardActionV1 dispatch = nullptr;
};

ZhongguoScoreboardActionDispatchEnvironmentV1
BindZhongguoScoreboardActionDispatchEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

bool DispatchZhongguoScoreboardActionNativeV1(
    void *opaque_environment, game::ZhongguoScoreboardActionV1 action,
    std::string_view stable_identity, std::string_view runtime_name,
    std::string_view instance_pointer,
    std::string_view vtable_pointer, bool &native_handled) noexcept;

game::ZhongguoScoreboardActionResultV1 ExecuteZhongguoScoreboardActionV1(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    const game::ZhongguoScoreboardStateV1 &source,
    const ZhongguoScoreboardActionAccessV1 &access,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept;

std::string SerializeZhongguoScoreboardActionAckV1(
    const game::ZhongguoScoreboardActionAckV1 &ack);

} // namespace xar::ck3_11906

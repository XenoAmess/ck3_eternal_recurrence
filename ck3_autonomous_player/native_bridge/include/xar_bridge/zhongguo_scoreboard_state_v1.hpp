#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoScoreboardStateStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoScoreboardWidgetStateV1 {
  std::string stable_identity;
  std::string runtime_name;
  ZhongguoTypedStringV1 instance_pointer;
  ZhongguoTypedStringV1 vtable_pointer;
  ZhongguoTypedBooleanV1 exists;
  ZhongguoTypedBooleanV1 local_visible;
  ZhongguoTypedBooleanV1 effective_visible;
  ZhongguoTypedBooleanV1 enabled;
  ZhongguoTypedBooleanV1 focused;
  ZhongguoTypedBooleanV1 modal_blocking;
  ZhongguoTypedIntegerV1 screen_x;
  ZhongguoTypedIntegerV1 screen_y;
  ZhongguoTypedIntegerV1 screen_width;
  ZhongguoTypedIntegerV1 screen_height;
  ZhongguoTypedIntegerV1 scroll_min;
  ZhongguoTypedIntegerV1 scroll_max;
  ZhongguoTypedIntegerV1 scroll_value;

  friend bool operator==(const ZhongguoScoreboardWidgetStateV1 &,
                         const ZhongguoScoreboardWidgetStateV1 &) = default;
};

struct ZhongguoScoreboardManagedAclV1 {
  bool surface_available = false;
  bool current_player_can_assess_others = false;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 first_subject_character_id;

  friend bool operator==(const ZhongguoScoreboardManagedAclV1 &,
                         const ZhongguoScoreboardManagedAclV1 &) = default;
};

struct ZhongguoScoreboardReceivedSelfAclV1 {
  bool surface_available = false;
  bool current_player_is_subject = false;
  ZhongguoTypedIntegerV1 first_row_character_id;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 result_case_serial;
  ZhongguoTypedIntegerV1 b1_case_serial;
  ZhongguoTypedIntegerV1 disclosure_acl_mode;
  ZhongguoTypedIntegerV1 disclosure_policy_available;
  ZhongguoTypedIntegerV1 disclosure_policy_id;
  ZhongguoTypedIntegerV1 disclosure_self_mode;
  ZhongguoTypedIntegerV1 disclosure_team_mode;
  ZhongguoTypedIntegerV1 disclosure_evaluator_identity_mode;
  ZhongguoTypedIntegerV1 disclosure_blackbox_risk;

  friend bool operator==(const ZhongguoScoreboardReceivedSelfAclV1 &,
                         const ZhongguoScoreboardReceivedSelfAclV1 &) =
      default;
};

struct ZhongguoScoreboardUnsupportedActionsV1 {
  ZhongguoTypedBooleanV1 activate;
  ZhongguoTypedBooleanV1 close;
  ZhongguoTypedBooleanV1 reopen;

  friend bool operator==(const ZhongguoScoreboardUnsupportedActionsV1 &,
                         const ZhongguoScoreboardUnsupportedActionsV1 &) =
      default;
};

struct ZhongguoScoreboardStateReadinessV1 {
  bool player_binding_ready = false;
  bool gui_root_ready = false;
  bool entry_window_state_ready = false;
  bool acl_ready = false;
  bool same_frame_ready = false;
  bool state_acl_query_ready = false;
  bool full_widget_gate_ready = false;
  bool production_live_ready = false;

  friend bool operator==(const ZhongguoScoreboardStateReadinessV1 &,
                         const ZhongguoScoreboardStateReadinessV1 &) =
      default;
};

struct ZhongguoScoreboardStateV1 {
  ZhongguoScoreboardStateStatusV1 status =
      ZhongguoScoreboardStateStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::array<ZhongguoScoreboardWidgetStateV1, 9> widgets;
  ZhongguoScoreboardManagedAclV1 managed_acl;
  ZhongguoScoreboardReceivedSelfAclV1 received_self_acl;
  ZhongguoScoreboardUnsupportedActionsV1 actions;
  ZhongguoScoreboardStateReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoScoreboardStateV1 &,
                         const ZhongguoScoreboardStateV1 &) = default;
};

enum class ReadZhongguoScoreboardStateResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoScoreboardStateV1Capability =
    "game.command.query-zhongguo-scoreboard-state-v1";
inline constexpr std::string_view kZhongguoScoreboardStateV1Step =
    "query-zhongguo-scoreboard-state-v1";
inline constexpr std::string_view kZhongguoScoreboardStateV1CaseKind =
    "zhongguo.scoreboard.named-state-acl";
inline constexpr std::string_view kZhongguoScoreboardStateV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-scoreboard-state-v1";
inline constexpr std::string_view kZhongguoScoreboardStateV1ConsumerId =
    "xar-autoplayer-zhongguo-scoreboard-state-v1";
inline constexpr std::string_view kZhongguoScoreboardStateV1AllowlistId =
    "zg361-scoreboard-fixed-widget-acl-v1";

inline constexpr std::uintptr_t kZhongguoGuiGlobalSlotRva = 0x576CC68;
inline constexpr std::uintptr_t kZhongguoGuiFindTopLevelWidgetRva = 0x36D0B20;
inline constexpr std::size_t kZhongguoGuiChainFirstOffset = 0x1B8;
inline constexpr std::size_t kZhongguoGuiChainSecondOffset = 0x58;
inline constexpr std::size_t kZhongguoGuiContextOffset = 0x3D0;
inline constexpr std::size_t kZhongguoGuiOwnerOffset = 0x08;
inline constexpr std::size_t kZhongguoWidgetHiddenFlagsOffset = 0xD0;
inline constexpr std::uint8_t kZhongguoWidgetHiddenMask = 0x10;
inline constexpr std::size_t kZhongguoWidgetParentOffset = 0xE8;
inline constexpr std::size_t kZhongguoWidgetChildrenOffset = 0xF0;
inline constexpr std::size_t kZhongguoWidgetChildCountOffset = 0xFC;
inline constexpr std::size_t kZhongguoWidgetNameOffset = 0x1B8;

inline constexpr std::array<std::string_view, 9>
    kZhongguoScoreboardStateV1WidgetNames{
        "zg361_scoreboard_toggle", "zg361_scoreboard_window",
        "zg361_scoreboard_modal", "zg361_scoreboard_panel",
        "zg361_scoreboard_entry_managed", "zg361_scoreboard_entry_received",
        "zg361_scoreboard_entry_system",
        "zg361_scoreboard_modal_backdrop_close",
        "zg361_scoreboard_header_close"};
inline constexpr std::array<std::string_view, 9>
    kZhongguoScoreboardStateV1WidgetIdentities{
        "zg361_open_scoreboard", "zg361_scoreboard_window",
        "zg361_scoreboard_modal", "zg361_scoreboard_panel",
        "zg361_scoreboard_entry_managed", "zg361_scoreboard_entry_received",
        "zg361_scoreboard_entry_system",
        "zg361_scoreboard_modal_backdrop_close",
        "zg361_scoreboard_header_close"};

inline constexpr std::array<std::string_view, 20>
    kZhongguoScoreboardStateV1VariableAllowlist{
        "zg361_sb_m_01_char",
        "zg361_scoreboard_managed_owner",
        "zg361_sb_r_01_char",
        "zg361_sb_self_char",
        "zg361_scoreboard_received_owner",
        "zg361_scoreboard_received_cycle_serial",
        "zg361_scoreboard_received_case_serial",
        "zg361_sb_self_case_owner",
        "zg361_sb_self_cycle_serial",
        "zg361_sb_self_case_serial",
        "zg361_sb_self_b1_case_owner",
        "zg361_sb_self_b1_cycle_serial",
        "zg361_sb_self_b1_case_serial",
        "zg361_sb_self_disclosure_acl_mode",
        "zg361_sb_self_disclosure_policy_available",
        "zg361_sb_self_disclosure_policy_id",
        "zg361_sb_self_disclosure_self_mode",
        "zg361_sb_self_disclosure_team_mode",
        "zg361_sb_self_disclosure_evaluator_identity_mode",
        "zg361_sb_self_disclosure_blackbox_risk"};

using NativeZhongguoFindTopLevelWidgetV1 =
    void *(__fastcall *)(void *, const std::string *);

struct ZhongguoScoreboardNativeEnvironmentV1 {
  ZhongguoCaseNativeEnvironmentV1 variables{};
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **gui_global_slot = nullptr;
  NativeZhongguoFindTopLevelWidgetV1 find_top_level_widget = nullptr;
};

using FindZhongguoFixedWidgetV1 = void *(*)(
    void *, std::string_view) noexcept;

struct ZhongguoScoreboardAccessV1 : ZhongguoCaseAccessV1 {
  FindZhongguoFixedWidgetV1 find_fixed_widget = nullptr;
};

struct ZhongguoScoreboardStateRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoScoreboardStateResultV1 ReadZhongguoScoreboardStateV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    const ZhongguoScoreboardStateRequestV1 &request,
    game::ZhongguoScoreboardStateV1 &output) noexcept;

std::string SerializeZhongguoScoreboardStateV1(
    const game::ZhongguoScoreboardStateV1 &snapshot);

} // namespace xar::ck3_11906

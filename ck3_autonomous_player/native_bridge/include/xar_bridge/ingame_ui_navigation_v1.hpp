#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kIngameUiNavigationV1Step = "navigate-ingame-ui-v1";
inline constexpr std::string_view kIngameUiNavigationV1Capability = "game.command.navigate-ingame-ui-v1";
inline constexpr std::string_view kIngameUiWindowQueryV1Step = "query-ingame-ui-window-v1";
inline constexpr std::string_view kIngameUiWindowQueryV1Capability = "game.command.query-ingame-ui-window-v1";

// Exact 1.19.0.6 EXE registered-GUI paths. The binding never accepts an RVA,
// native pointer, widget name, coordinates, or view enum from the caller.
inline constexpr std::uintptr_t kUiDefaultOnCharacterClickRvaV1 = 0xA04530;
inline constexpr std::uintptr_t kUiSelectUnitRvaV1 = 0xA7F050;
inline constexpr std::uintptr_t kUiOpenViewRvaV1 = 0xA79200;
inline constexpr std::uintptr_t kUiOpenViewDataRvaV1 = 0xA79700;
inline constexpr std::uintptr_t kUiIdAnyTypeGetterRvaV1 = 0x998130;

enum class IngameUiWindowKindV1 : std::uint32_t { character=0, army=1, combat=2, knights=3 };
enum class IngameUiOperationV1 : std::uint32_t { query=0, open_character=1, select_army=2, open_combat=3, open_knights=4,
  hover_left_knights=5, hover_right_knights=6, fit_combat_window=7 };
struct UiFloat2V1 { float x=0, y=0; };
struct UiRectV1 { float x=0, y=0, width=0, height=0; };
struct CombatUiGeometryV1 {
  bool available=false;
  bool stock_margin_source_verified=false;
  bool content_inside_viewport=false;
  bool fit_required=false;
  std::uint32_t combat_id=0;
  std::uint32_t widget_count=0;
  UiRectV1 viewport{},window_rect{},content_union{};
  UiFloat2V1 proposed_translation{};
  std::string unavailable_reason;
};
struct IngameUiRequestV1 {
  IngameUiOperationV1 operation = IngameUiOperationV1::query;
  IngameUiWindowKindV1 window_kind = IngameUiWindowKindV1::character;
  std::uint32_t subject_id = 0;
};
struct IngameUiResultV1 {
  bool available = false;
  bool dispatch_invoked = false;
  bool verification_pending = false;
  bool window_exists = false;
  bool effective_visible = false;
  bool enabled = false;
  bool subject_id_available = false;
  std::uint32_t current_subject_id = 0;
  std::uint32_t native_army_id = 0;
  std::uint32_t owner_character_id = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t played_character_id = -1;
  std::uint64_t pump_epoch = 0;
  std::uint32_t thread_id = 0;
  bool combat_knights_read_available = false;
  std::int32_t left_knight_count = -1;
  std::int32_t right_knight_count = -1;
  std::string left_knight_breakdown;
  std::string right_knight_breakdown;
  bool hover_state_available = false;
  std::string hovered_widget_name;
  std::string hovered_ui_side;
  std::uint32_t hovered_combat_id = 0;
  CombatUiGeometryV1 combat_geometry{};
  NamedGuiTreeInspectionV1 tree{};
  std::string status = "unavailable";
  std::string unavailable_reason;
};

// Only ExecuteFrontendGuiRouteMailboxV1 calls this, after owner/TLS/epoch and
// fresh paused-map snapshot admission. Direct use is not a public bridge slot.
bool ExecuteIngameUiNavigationV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const IngameUiRequestV1 &request, const game::Snapshot &snapshot,
    const MainThreadExecutionStampV1 &stamp, IngameUiResultV1 &output) noexcept;

bool ParseIngameUiRequestV1(std::string_view json, bool query,
                          IngameUiRequestV1 &output) noexcept;
bool ValidateIngameUiRequestV1(const IngameUiRequestV1 &request) noexcept;
// Pure bounded fit policy; production geometry comes only from original GUI
// getters. A successful policy result is not a pixels/full-panel assertion.
bool ComputeCombatUiFitTranslationV1(const UiRectV1 &viewport,
    const UiRectV1 &content,UiFloat2V1 &translation) noexcept;
std::string_view IngameUiWindowNameV1(IngameUiWindowKindV1 kind) noexcept;
std::string SerializeIngameUiResultV1(const IngameUiRequestV1 &request,
                                    const IngameUiResultV1 &result,
                                    std::uint64_t native_revision);
} // namespace xar::ck3_11906

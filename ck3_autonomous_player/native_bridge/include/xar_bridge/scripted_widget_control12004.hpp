#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kScriptedWidgetQueryStep12004 = "query-scripted-widget-controls-v1";
inline constexpr std::string_view kScriptedWidgetActionStep12004 = "activate-scripted-widget-control-v1";
inline constexpr std::string_view kScriptedWidgetQueryCapability12004 = "game.command.query-scripted-widget-controls-v1";
inline constexpr std::string_view kScriptedWidgetActionCapability12004 = "game.command.activate-scripted-widget-control-v1";

struct ScriptedWidgetFrame12004 {
  std::uint32_t game_pid = 0;
  std::int32_t played_character_id = -1, date_raw = 0;
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uintptr_t gui_context = 0, gui_owner = 0;
  bool owner_thread_verified = false, source_abi_pins_verified = false, frame_verified = false;
  bool operator==(const ScriptedWidgetFrame12004 &) const = default;
};

struct ScriptedWidgetRow12004 {
  std::uint64_t widget_id = 0;
  std::string runtime_name, child_path;
  std::uint32_t vtable_rva = 0;
  bool effective_visible = false, enabled = false, clickable = false;
  bool operator==(const ScriptedWidgetRow12004 &) const = default;
};

// Private native witnesses. Wire IDs are row handles; no wire pointer is ever dereferenced.
struct ScriptedWidgetCallback12004 {
  std::uintptr_t object = 0, vtable = 0, slot2 = 0, entry = 0, receiver = 0;
  std::uintptr_t expression_chain = 0, final_user_data = 0;
  std::vector<std::uintptr_t> chain_user_data;
  NamedGuiExpressionDescriptor12004V1 expression{};
  bool operator==(const ScriptedWidgetCallback12004 &) const = default;
};
struct ScriptedWidgetIdentity12004 {
  ScriptedWidgetRow12004 row{};
  std::uintptr_t widget = 0, vtable = 0, context = 0, callback_data = 0;
  std::uint32_t callback_group = 0;
  std::vector<std::uintptr_t> ancestors;
  std::vector<std::uint8_t> ancestor_flags;
  std::vector<ScriptedWidgetCallback12004> callbacks;
  bool operator==(const ScriptedWidgetIdentity12004 &) const = default;
};
struct ScriptedWidgetCapture12004 {
  ScriptedWidgetFrame12004 frame{};
  std::string root_name;
  std::uintptr_t root = 0;
  bool complete = false, truncated = false;
  std::vector<ScriptedWidgetIdentity12004> widgets;
  bool operator==(const ScriptedWidgetCapture12004 &) const = default;
};
struct ScriptedWidgetProvider12004 {
  std::uint64_t query_generation = 0;
  bool valid = false;
  ScriptedWidgetCapture12004 capture{};
};

using ScriptedWidgetCaptureReader12004 = bool (*)(void *, std::string_view,
    ScriptedWidgetCapture12004 &, std::string &) noexcept;
using ScriptedWidgetDispatcher12004 = bool (*)(void *, const ScriptedWidgetIdentity12004 &,
    bool &native_handled, bool &native_dispatch_attempted) noexcept;
struct ScriptedWidgetBackend12004 {
  void *context = nullptr;
  ScriptedWidgetCaptureReader12004 capture = nullptr;
  ScriptedWidgetDispatcher12004 dispatch = nullptr;
};

struct ScriptedWidgetResult12004 {
  bool action = false, available = false, complete = false, truncated = false;
  ScriptedWidgetFrame12004 frame{};
  std::string root_name;
  std::uint64_t query_generation = 0, widget_id = 0;
  std::vector<ScriptedWidgetRow12004> widgets;
  bool dispatch_attempted = false, dispatch_invoked = false, native_handled = false;
  bool verification_pending = false;
  std::string unavailable_reason;
};

bool ScriptedWidgetRootName12004(std::string_view name) noexcept;
bool ParseScriptedWidgetOpaqueId12004(std::string_view text, std::uint64_t &value) noexcept;
bool QueryScriptedWidgetControls12004(ScriptedWidgetProvider12004 &provider,
    const ScriptedWidgetBackend12004 &backend, std::string_view root_name,
    ScriptedWidgetResult12004 &out) noexcept;
bool ActivateScriptedWidgetControl12004(ScriptedWidgetProvider12004 &provider,
    const ScriptedWidgetBackend12004 &backend, std::uint64_t query_generation,
    std::uint64_t widget_id, ScriptedWidgetResult12004 &out) noexcept;

struct ScriptedWidgetControlContext12004 {
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0, connection_generation = 0;
  ScriptedWidgetProvider12004 *provider = nullptr;
  bool action = false;
  std::string root_name;
  std::uint64_t query_generation = 0, widget_id = 0;
  ScriptedWidgetResult12004 result{};
};

// Called only from the existing GUI owner mailbox. Uses the original native button dispatcher.
bool ExecuteScriptedWidgetControl12004(ScriptedWidgetControlContext12004 &query,
    MainThreadQueryMailboxV1 &mailbox, const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept;
std::string SerializeScriptedWidgetControl12004(const ScriptedWidgetResult12004 &out);

} // namespace xar::ck3_11906

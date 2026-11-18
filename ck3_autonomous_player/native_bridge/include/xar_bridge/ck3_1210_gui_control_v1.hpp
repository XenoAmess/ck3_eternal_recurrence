#pragma once

#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <array>
#include <string>
#include <vector>

namespace xar::ck3_1210 {
inline constexpr char kGuiControlClaimSchemaV1[] = "ck3_1210_gui_control_v1";
inline constexpr char kGuiControlResultSchemaV1[] = "ck3_1210_gui_control_result_v1";
inline constexpr char kGuiControlQueryStepV1[] = "query-scripted-widget-controls-v1";
inline constexpr char kGuiControlActivateStepV1[] = "activate-scripted-widget-control-v1";
inline constexpr char kGuiControlQueryCapabilityV1[] = "game.query.scripted-widget-controls.v1";
inline constexpr char kGuiControlActivateCapabilityV1[] = "game.command.activate-scripted-widget-control.v1";
inline constexpr std::size_t kGuiControlMaximumRowsV1 = 2048;

struct GuiControlRequestV1 {
  bool activate = false;
  std::string_view step;
  std::string root_name;
  std::uint64_t native_revision = 0, deadline_unix_ms = 0;
  std::uint64_t query_generation = 0, widget_id = 0;
};
bool ParseGuiControlRequestV1(std::string_view, GuiControlRequestV1 &) noexcept;
bool GuiControlRootNameV1(std::string_view) noexcept;

struct GuiControlRowV1 {
  std::uint64_t widget_id = 0;
  std::string runtime_name, child_path;
  std::uint32_t vtable_rva = 0;
  bool effective_visible = false, enabled = false, clickable = false;
  bool operator==(const GuiControlRowV1 &) const = default;
};
// Private witnesses: neither caller-provided pointers nor arbitrary expressions
// are accepted. Callback rows and source objects are recaptured before dispatch.
struct GuiControlCallbackV1 {
  std::uintptr_t object = 0, vtable = 0, invoke = 0;
  std::array<std::byte, 0x48> binding{};
  std::array<std::byte, 0x10> object_header{};
  std::vector<std::byte> native_source;
  bool operator==(const GuiControlCallbackV1 &) const = default;
};
struct GuiControlIdentityV1 {
  GuiControlRowV1 row;
  std::uintptr_t widget = 0, parent = 0, children = 0, context = 0;
  std::int32_t child_count = 0;
  std::uint8_t flags = 0;
  std::vector<GuiControlCallbackV1> callbacks;
  bool operator==(const GuiControlIdentityV1 &) const = default;
};
struct GuiControlCaptureV1 {
  std::int32_t played_character_id = -1, date_raw = 0;
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uintptr_t logical_owner = 0, application = 0, context = 0;
  std::uintptr_t gui_owner = 0, global_root = 0, root = 0, shortcut_manager = 0;
  std::vector<std::uintptr_t> modal_receivers;
  std::vector<std::uint8_t> modal_flags;
  std::string root_name;
  bool complete = false;
  std::vector<GuiControlIdentityV1> widgets;
  bool operator==(const GuiControlCaptureV1 &) const = default;
};
struct GuiControlProviderV1 {
  std::uint64_t query_generation = 0;
  bool valid = false;
  GuiControlCaptureV1 capture;
};
enum class GuiControlStatusV1 {
  unavailable, available, submitted, expired, stale_full_snapshot, stale_gui,
  disabled, indeterminate
};
struct GuiControlResultV1 {
  GuiControlStatusV1 status = GuiControlStatusV1::unavailable;
  bool application_main_observed = false, full_snapshot_before_verified = false;
  bool source_abi_pins_verified = false, effect_attempted = false, native_handled = false;
  bool verification_pending = false;
  std::uint64_t query_generation = 0;
  std::vector<GuiControlRowV1> widgets;
  std::string unavailable_reason;
};
using GuiControlCaptureReaderV1 = bool (*)(void *, std::string_view,
    GuiControlCaptureV1 &, std::string &) noexcept;
using GuiControlDispatcherV1 = bool (*)(void *, const GuiControlCaptureV1 &,
    const GuiControlIdentityV1 &, bool &, bool &) noexcept;
struct GuiControlBackendV1 {
  void *context = nullptr;
  GuiControlCaptureReaderV1 capture = nullptr;
  GuiControlDispatcherV1 dispatch = nullptr;
};
// Portable admission reducer, used unchanged by the production owner callback.
bool ApplyGuiControlV1(GuiControlProviderV1 &, const GuiControlRequestV1 &,
    const GuiControlBackendV1 &, GuiControlResultV1 &) noexcept;

struct GuiControlBindingsV1 {
  CoreBindings core;
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
};
GuiControlBindingsV1 BindGuiControlImageV1(std::uintptr_t, std::string_view) noexcept;
struct GuiControlContextV1 {
  GuiControlRequestV1 request;
  GuiControlBindingsV1 bindings;
  const game::GameAdapter *game = nullptr, *native_full_adapter = nullptr;
  const game::Snapshot *expected_full_snapshot = nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket;
  GuiControlProviderV1 *provider = nullptr;
  std::uint64_t connection_generation = 0, monotonic_deadline_ms = 0;
  GuiControlResultV1 result;
};
void ArmGuiControlDeadlineV1(GuiControlContextV1 &) noexcept;
bool ExecuteGuiControlMailboxV1(void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeGuiControlCommandResultV1(std::string_view,
    const GuiControlRequestV1 &, const GuiControlResultV1 &);
} // namespace xar::ck3_1210

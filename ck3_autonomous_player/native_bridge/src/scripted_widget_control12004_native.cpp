#include "xar_bridge/scripted_widget_control12004.hpp"
#include "xar_bridge/named_gui_widget_resolution_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"

#include <windows.h>
#include <array>
#include <charconv>
#include <limits>

namespace xar::ck3_11906 {
namespace {
template<class T> bool Read(std::uintptr_t address, std::size_t offset, T &out) noexcept {
  SIZE_T got = 0;
  return address && offset <= (std::numeric_limits<std::uintptr_t>::max)() - address &&
      ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address + offset),
          &out, sizeof(out), &got) && got == sizeof(out);
}
template<std::size_t N> bool Pin(std::uintptr_t base, std::uintptr_t rva,
    const std::array<unsigned char, N> &expected) noexcept {
  std::array<unsigned char, N> actual{}; SIZE_T got = 0;
  return ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(base + rva),
      actual.data(), N, &got) && got == N && actual == expected;
}
bool Pins(std::uintptr_t base) noexcept {
  // 1.20.0.4 / SHA 98702f88...; find-root, native shortcut activation,
  // strict ancestry, and ButtonBase primary activation. Callback/expression
  // bodies are additionally pinned by InspectNamedGuiSubtreeV1.
  return Pin(base, 0x3AAB0E0, std::array<unsigned char,24>{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0}) &&
      Pin(base, 0x3ABC4B0, std::array<unsigned char,24>{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x60,0x49,0x8b,0xf0,0x8b}) &&
      Pin(base, 0x3A78210, std::array<unsigned char,24>{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48}) &&
      Pin(base, 0x3AA0D20, std::array<unsigned char,24>{0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x0f,0xb6,0x89,0xd0,0x00,0x00,0x00,0x80,0xe1,0x02,0x74,0x26,0x44,0x8b,0x42});
}
struct NativeContext {
  ScriptedWidgetControlContext12004 &query;
  MainThreadQueryMailboxV1 &mailbox;
  const MainThreadExecutionStampV1 &stamp;
  const ZhongguoScoreboardNativeEnvironmentV1 &environment;
  ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch;
};
bool Frame(NativeContext &c, ScriptedWidgetFrame12004 &out) noexcept {
  out = {}; out.game_pid = GetCurrentProcessId();
  out.native_revision = c.query.native_revision; out.connection_generation = c.query.connection_generation;
  const auto &e = c.environment;
  if (!c.query.game || !e.exact_build_admitted || e.offline_fixture_function_overrides ||
      !c.dispatch.exact_build_admitted || c.dispatch.offline_fixture_function_overrides ||
      e.gui_abi_revision != GuiAbiRevisionV1::crozier12004 ||
      c.dispatch.gui_abi_revision != GuiAbiRevisionV1::crozier12004 ||
      e.module_base == 0 || e.module_base != c.dispatch.module_base ||
      e.executable_sha256 != ck3_12004::kExecutableSha256 ||
      !game::IsCk3_12004Descriptor(c.query.game->descriptor())) return false;
  out.source_abi_pins_verified = Pins(e.module_base);
  out.owner_thread_verified = IsIngameUiPausedOwnerStampV1(c.mailbox, c.stamp, GetCurrentThreadId());
  if (!out.source_abi_pins_verified || !out.owner_thread_verified) return false;
  game::Snapshot snapshot{};
  if (!game::ReadSnapshot(*c.query.game, snapshot) || snapshot != c.query.expected_snapshot ||
      !snapshot.map_ready || !snapshot.paused || !snapshot.has_played_character ||
      !snapshot.played_character_alive || snapshot.played_character_id <= 0 ||
      snapshot.has_active_event || !out.native_revision || !out.connection_generation) return false;
  out.played_character_id = snapshot.played_character_id; out.date_raw = snapshot.date_raw;
  IngameUiGuiOwnerBindingV1 binding{};
  if (!ReadIngameUiGuiOwnerBindingV1(e, binding) || !binding.context || !binding.owner) return false;
  out.gui_context = reinterpret_cast<std::uintptr_t>(binding.context);
  out.gui_owner = reinterpret_cast<std::uintptr_t>(binding.owner); out.frame_verified = true;
  return true;
}
bool Path(std::string_view p, std::vector<std::uint32_t> &indices) {
  if (p.empty()) return true;
  while (!p.empty()) {
    const auto slash = p.find('/'); const auto part = p.substr(0, slash); std::uint32_t n = 0;
    const auto parsed = std::from_chars(part.data(), part.data() + part.size(), n);
    if (part.empty() || parsed.ec != std::errc{} || parsed.ptr != part.data() + part.size() ||
        n >= kNamedGuiTreeInspectionMaximumWidgetsV1 || indices.size() >= 64) return false;
    indices.push_back(n);
    if (slash == std::string_view::npos) break;
    p.remove_prefix(slash + 1); if (p.empty()) return false;
  }
  return true;
}
bool Identity(NativeContext &c, const NamedGuiWidgetInspectionV1 &row,
    ScriptedWidgetCapture12004 &capture, ScriptedWidgetIdentity12004 &out) {
  const auto &e = c.environment; ZhongguoScoreboardAccessV1 access{};
  std::vector<std::uint32_t> indices;
  if (!Path(row.child_path, indices) || row.vtable_rva > UINT32_MAX) return false;
  bool visible = true, enabled = true; void *last = nullptr, *vt = nullptr;
  for (std::size_t count = 0; count <= indices.size(); ++count) {
    void *root = nullptr, *widget = nullptr; std::uintptr_t context = 0, parent = 0; std::uint8_t flags = 0;
    if (!ResolveFixedGuiChildPathV1(e, access, capture.root_name, indices.data(), count, root, widget) ||
        reinterpret_cast<std::uintptr_t>(root) != capture.root || !widget ||
        !Read(reinterpret_cast<std::uintptr_t>(widget), kZhongguoWidgetGuiContextOffset, context) || context != capture.frame.gui_context ||
        !Read(reinterpret_cast<std::uintptr_t>(widget), kZhongguoWidgetHiddenFlagsOffset, flags) ||
        (last && (!Read(reinterpret_cast<std::uintptr_t>(widget), kZhongguoWidgetParentOffset, parent) || parent != reinterpret_cast<std::uintptr_t>(last)))) return false;
    out.ancestors.push_back(reinterpret_cast<std::uintptr_t>(widget)); out.ancestor_flags.push_back(flags);
    visible = visible && !(flags & 0x18); enabled = enabled && !(flags & 0x06); last = widget;
  }
  std::string name; bool local_visible = false, local_enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, last, name, vt, local_visible, local_enabled) || name != row.runtime_name ||
      reinterpret_cast<std::uintptr_t>(vt) != e.module_base + row.vtable_rva ||
      local_visible != row.effective_visible || local_enabled != row.enabled) return false;
  out.widget = reinterpret_cast<std::uintptr_t>(last); out.vtable = reinterpret_cast<std::uintptr_t>(vt); out.context = capture.frame.gui_context;
  out.row = {0, row.runtime_name, row.child_path, static_cast<std::uint32_t>(row.vtable_rva), visible, enabled, false};
  const auto &b = row.standard_click_binding_12004;
  if (!b.button_base_slot13) return true;
  out.callback_group = b.primary_group ? 0x3F8U : 0x338U; std::uint32_t count = 0;
  if (!Read(out.widget, out.callback_group, out.callback_data) ||
      !Read(out.widget, out.callback_group + 0xCU, count) || count != b.callbacks.size() || (!out.callback_data && count)) return false;
  for (std::size_t i = 0; i < b.callbacks.size(); ++i) {
    const auto &source = b.callbacks[i]; ScriptedWidgetCallback12004 cb{};
    if (!Read(out.callback_data, i * 0x48 + 0x40, cb.object) || !Read(cb.object, 0, cb.vtable) ||
        !Read(cb.vtable, 0x10, cb.slot2) || cb.vtable != e.module_base + source.callback_vtable_rva ||
        cb.slot2 != e.module_base + source.callback_slot2_rva) return false;
    if (source.indirect_target_3aa30e0) {
      if (!Read(cb.object, 8, cb.entry) || !Read(cb.object, 0xF0, cb.receiver) ||
          cb.entry != e.module_base + source.native_target_8_rva || (cb.receiver != 0) != source.receiver_f0_present) return false;
    }
    if (source.expression_descriptor_3a9f960) {
      cb.expression = source.expression_3a9f960;
      if (!Read(cb.object, 0x28, cb.expression_chain) || !Read(cb.object, 0x50, cb.final_user_data)) return false;
      for (std::size_t j = 0; j < cb.expression.chain_calls.size(); ++j) {
        std::uintptr_t data = 0; if (!Read(cb.expression_chain, j * 0x18 + 0x10, data)) return false;
        cb.chain_user_data.push_back(data);
      }
    }
    out.callbacks.push_back(std::move(cb));
  }
  out.row.clickable = visible && enabled && !out.callbacks.empty() &&
      InspectFixedGuiWidgetDispatchAdmissionV1(c.dispatch, last, vt);
  return true;
}
bool Capture(void *opaque, std::string_view root_name, ScriptedWidgetCapture12004 &out,
    std::string &reason) noexcept {
  try {
    auto &c = *static_cast<NativeContext *>(opaque); out = {}; out.root_name.assign(root_name);
    const auto fail = [&](const char *why) { reason = why; return false; };
    if (!Frame(c, out.frame)) return fail("scripted_widget_exact_paused_owner_frame_unavailable");
    ZhongguoScoreboardAccessV1 access{}; void *root = nullptr, *self = nullptr;
    NamedGuiWidgetResolutionV1 resolution = NamedGuiWidgetResolutionV1::missing;
    if (!ResolveNamedGuiWidgetWithResolutionV1(c.environment, access, root_name, root_name,
                                              root, self, resolution) || !root || self != root) {
      switch (resolution) {
      case NamedGuiWidgetResolutionV1::budget_exhausted:
        return fail("scripted_widget_root_lookup_budget_exhausted");
      case NamedGuiWidgetResolutionV1::read_failed:
        return fail("scripted_widget_root_read_failed");
      case NamedGuiWidgetResolutionV1::resource_unavailable:
        return fail("scripted_widget_root_lookup_resource_unavailable");
      case NamedGuiWidgetResolutionV1::invalid_request:
        return fail("scripted_widget_root_resolution_invalid");
      default:
        return fail("scripted_widget_root_unavailable");
      }
    }
    out.root = reinterpret_cast<std::uintptr_t>(root); NamedGuiTreeInspectionV1 tree{};
    if (!InspectNamedGuiSubtreeV1(access, c.environment.module_base, root, root_name, tree, true, false))
      return fail("scripted_widget_tree_unavailable");
    out.truncated = tree.truncated;
    if (!tree.root_available || tree.truncated || tree.widget_count != tree.widgets.size() || !tree.widget_count ||
        !tree.callback_thunk_3aa30e0_pin_verified || !tree.expression_layout_3a9f960_pin_verified)
      return fail("scripted_widget_tree_or_callback_pins_incomplete");
    for (const auto &row : tree.widgets) {
      ScriptedWidgetIdentity12004 identity{};
      if (!Identity(c, row, out, identity)) return fail("scripted_widget_native_identity_changed");
      out.widgets.push_back(std::move(identity));
    }
    ScriptedWidgetFrame12004 completion{};
    if (!Frame(c, completion) || completion != out.frame) return fail("scripted_widget_frame_changed_during_capture");
    out.complete = true; return true;
  } catch (...) { reason = "scripted_widget_native_capture_exception"; return false; }
}
bool Dispatch(void *opaque, const ScriptedWidgetIdentity12004 &target, bool &handled, bool &attempted) noexcept {
  auto &c = *static_cast<NativeContext *>(opaque);
  return DispatchFixedGuiWidgetNativeWithAttemptV1(&c.dispatch, game::ZhongguoScoreboardActionV1::open,
      reinterpret_cast<void *>(target.widget), reinterpret_cast<void *>(target.vtable), handled, attempted);
}
} // namespace
bool ExecuteScriptedWidgetControl12004(ScriptedWidgetControlContext12004 &query,
    MainThreadQueryMailboxV1 &mailbox, const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  NativeContext context{query, mailbox, stamp, environment, dispatch};
  if (!query.provider) return false;
  const ScriptedWidgetBackend12004 backend{&context, Capture, Dispatch};
  const bool completed = query.action ? ActivateScriptedWidgetControl12004(*query.provider, backend,
      query.query_generation, query.widget_id, query.result) :
      QueryScriptedWidgetControls12004(*query.provider, backend, query.root_name, query.result);
  // Rejections still identify the submitted episode, without granting owner,
  // source or frame verification that was not actually observed.
  auto &frame = query.result.frame;
  if (!frame.game_pid) frame.game_pid = GetCurrentProcessId();
  if (frame.played_character_id <= 0) frame.played_character_id = query.expected_snapshot.played_character_id;
  if (!frame.native_revision) frame.native_revision = query.native_revision;
  if (!frame.connection_generation) frame.connection_generation = query.connection_generation;
  if (!frame.frame_verified) frame.date_raw = query.expected_snapshot.date_raw;
  if (query.action && query.result.root_name.empty()) query.result.root_name = query.provider->capture.root_name;
  return completed;
}
} // namespace xar::ck3_11906

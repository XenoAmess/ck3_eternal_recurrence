#include "xar_bridge/holy_site_creation12004_navigation.hpp"
#include "xar_bridge/holy_site_creation12004.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include <windows.h>
#include <algorithm>
#include <utility>

#ifndef XAR_ENABLE_HOLY_SITE_CREATION_UI12004
#define XAR_ENABLE_HOLY_SITE_CREATION_UI12004 0
#endif

#if XAR_ENABLE_HOLY_SITE_CREATION_UI12004
namespace xar::ck3_11906 {
namespace {
namespace creation = ck3_12004::religion::holy_site_creation;
using ReligionContext = ck3_12002::religion::Context;
constexpr std::string_view root_name = "holy_site_creation_window";

template<class T> bool Value(const void* p, std::size_t offset, T& out) noexcept {
  if (!p) return false;
  SIZE_T got = 0;
  return ReadProcessMemory(GetCurrentProcess(),
      static_cast<const unsigned char*>(p) + offset, &out, sizeof(T), &got) && got == sizeof(T);
}
bool Exact(const ZhongguoScoreboardNativeEnvironmentV1& e) noexcept {
  return HolySiteCreationUiEnabled12004() && e.exact_build_admitted &&
      !e.offline_fixture_function_overrides && e.module_base &&
      e.gui_abi_revision == GuiAbiRevisionV1::crozier12004 &&
      e.executable_sha256 == ck3_12004::kExecutableSha256;
}
bool ReadReligion(const ZhongguoScoreboardNativeEnvironmentV1& e,
    const game::Snapshot& snapshot, const MainThreadExecutionStampV1& stamp,
    ReligionContext& context) noexcept {
  const auto b = ck3_12004::religion::BindReligionContextImage12004(
      e.module_base, e.executable_sha256);
  return ck3_12004::religion::ReadPlayedReligionContext12004(b, stamp.pump_epoch, context) &&
      context.available && context.capture_epoch == stamp.pump_epoch &&
      context.played_character_id == snapshot.played_character_id &&
      context.date_raw == snapshot.date_raw && context.faith_id &&
      *context.faith_id != 0xFFFFFFFFU;
}
bool SameReligion(const ReligionContext& a, const ReligionContext& b) noexcept {
  return a.available && b.available && a.capture_epoch == b.capture_epoch &&
      a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.faith_id == b.faith_id && a.rite_id == b.rite_id &&
      a.religion_id == b.religion_id && a.faith_main_rite_id == b.faith_main_rite_id;
}
bool SameModels(const creation::Snapshot& a, const creation::Snapshot& b) noexcept {
  if (!a.available || !b.available || !a.models_complete || !b.models_complete ||
      !a.selection_available || !b.selection_available || a.window != b.window ||
      a.root != b.root || a.gfx != b.gfx || a.handler != b.handler ||
      a.window_faith_id != b.window_faith_id || a.player_faith_id != b.player_faith_id ||
      a.potential_barony_title_ids != b.potential_barony_title_ids ||
      a.enshrinable_artifact_ids != b.enshrinable_artifact_ids ||
      a.selected_artifact_ids != b.selected_artifact_ids ||
      a.selected_type_key != b.selected_type_key ||
      a.selected_barony_title_id != b.selected_barony_title_id ||
      a.native_rarity_sum_observed != b.native_rarity_sum_observed ||
      a.native_rarity_sum_raw != b.native_rarity_sum_raw ||
      a.native_enabled_observed != b.native_enabled_observed ||
      a.native_create_button_enabled != b.native_create_button_enabled ||
      a.bypass_requirements_observed != b.bypass_requirements_observed ||
      a.bypass_requirements_raw != b.bypass_requirements_raw ||
      a.create_tooltip_available != b.create_tooltip_available ||
      a.create_tooltip != b.create_tooltip ||
      a.cached_resource_quote_available != b.cached_resource_quote_available ||
      a.cached_resource_vector_raw != b.cached_resource_vector_raw ||
      a.available_holy_site_types.size() != b.available_holy_site_types.size()) return false;
  for (std::size_t i = 0; i < a.available_holy_site_types.size(); ++i) {
    const auto& x = a.available_holy_site_types[i]; const auto& y = b.available_holy_site_types[i];
    if (x.type_key != y.type_key || x.native_type != y.native_type ||
        x.is_selected != y.is_selected || x.native_can_pick_observed != y.native_can_pick_observed ||
        x.native_can_pick != y.native_can_pick || x.tooltip_available != y.tooltip_available ||
        x.tooltip != y.tooltip) return false;
  }
  return true;
}
bool Capture(const ZhongguoScoreboardNativeEnvironmentV1& e, void* handler,
    const creation::Bindings& b, const ReligionContext& context,
    const IngameUiGuiOwnerBindingV1& expected_owner, IngameUiResultV1& out) {
  creation::Snapshot first{}, last{};
  if (!creation::ReadContext12004(b, handler, context, first)) {
    out.unavailable_reason = first.unavailable_reason; return false;
  }
  if (!first.models_complete || !first.selection_available || !first.root) {
    out.unavailable_reason = "holy_site_creation_models_or_root_unavailable"; return false;
  }
  ZhongguoScoreboardAccessV1 access{}; void* root = nullptr; void* widget = nullptr;
  void* vtable = nullptr; std::string name; bool visible = false, enabled = false;
  NamedGuiTreeInspectionV1 tree{}; void* widget_context = nullptr;
  if (!ResolveNamedGuiWidgetV1(e, access, root_name, root_name, root, widget) ||
      !root || root != widget || root != first.root ||
      !Value(root, 0xD8, widget_context) || widget_context != expected_owner.context ||
      !ReadGuiWidgetRuntimeV1(access, root, name, vtable, visible, enabled) || name != root_name ||
      !InspectNamedGuiSubtreeV1(access, e.module_base, root, root_name, tree) || tree.truncated) {
    out.unavailable_reason = "holy_site_creation_actual_widget_tree_unverified"; return false;
  }
  void* later_vtable = nullptr; std::string later_name; bool later_visible = false, later_enabled = false;
  IngameUiGuiOwnerBindingV1 owner{};
  if (!creation::ReadContext12004(b, handler, context, last) || !SameModels(first, last) ||
      !ReadIngameUiGuiOwnerBindingV1(e, owner) || owner != expected_owner ||
      !ReadGuiWidgetRuntimeV1(access, root, later_name, later_vtable, later_visible, later_enabled) ||
      later_name != name || later_vtable != vtable || later_visible != visible || later_enabled != enabled) {
    out.unavailable_reason = "holy_site_creation_models_owner_or_widget_changed"; return false;
  }
  out.holy_site_creation = std::move(last);
  out.window_exists = true; out.effective_visible = visible; out.enabled = enabled;
  out.subject_id_available = true; out.current_subject_id = context.faith_id.value();
  out.tree = std::move(tree); out.unavailable_reason.clear(); return true;
}
bool RequestedState(const IngameUiRequestV1& r, const creation::Snapshot& s) noexcept {
  switch (r.operation) {
    case IngameUiOperationV1::open_holy_site_creation: return s.player_faith_matches;
    case IngameUiOperationV1::select_holy_site_creation_type:
      return s.selected_type_key && *s.selected_type_key == r.holy_site_creation_type_key;
    case IngameUiOperationV1::select_holy_site_creation_barony:
      return s.selected_barony_title_id && *s.selected_barony_title_id == r.subject_id;
    case IngameUiOperationV1::set_holy_site_creation_artifact_selection:
      return r.holy_site_creation_selected &&
          (std::find(s.selected_artifact_ids.begin(), s.selected_artifact_ids.end(), r.subject_id) !=
              s.selected_artifact_ids.end()) == *r.holy_site_creation_selected;
    default: return false;
  }
}
}

bool HolySiteCreationUiEnabled12004() noexcept {
  return XAR_ENABLE_HOLY_SITE_CREATION_UI12004 != 0;
}
bool ExecuteHolySiteCreationNavigation12004(
    const ZhongguoScoreboardNativeEnvironmentV1& e, void* handler,
    const IngameUiRequestV1& request, const game::Snapshot& snapshot,
    const MainThreadExecutionStampV1& stamp, const IngameUiGuiOwnerBindingV1& gui_binding,
    IngameUiResultV1& out) noexcept {
  try {
    if (!Exact(e) || !handler) {
      out.unavailable_reason = "holy_site_creation_ui_optin_or_exact_binding_unavailable"; return true;
    }
    ReligionContext before{};
    if (!ReadReligion(e, snapshot, stamp, before)) {
      out.unavailable_reason = "holy_site_creation_actual_player_religion_context_unavailable"; return true;
    }
    const auto binding = creation::BindImage12004(e.module_base, e.executable_sha256);
    const bool query = request.operation == IngameUiOperationV1::query;
    const bool open = request.operation == IngameUiOperationV1::open_holy_site_creation;
    IngameUiResultV1 initial{};
    const bool initial_read = Capture(e, handler, binding, before, gui_binding, initial);
    if (query) {
      ReligionContext after{};
      if (!initial_read || !ReadReligion(e, snapshot, stamp, after) || !SameReligion(before, after)) {
        out.unavailable_reason = initial_read ? "holy_site_creation_player_context_changed" : initial.unavailable_reason;
        return true;
      }
      out.holy_site_creation = std::move(initial.holy_site_creation);
      out.window_exists = initial.window_exists; out.effective_visible = initial.effective_visible;
      out.enabled = initial.enabled; out.subject_id_available = initial.subject_id_available;
      out.current_subject_id = initial.current_subject_id; out.tree = std::move(initial.tree);
      out.available = true; out.status = "observed"; out.unavailable_reason.clear(); return true;
    }
    if (!open && (!initial_read || !initial.effective_visible || !initial.enabled)) {
      out.unavailable_reason = initial_read ? "holy_site_creation_selection_requires_visible_enabled_window" : initial.unavailable_reason;
      return true;
    }
    const void* expected_window = nullptr;
    if (!Value(handler, 0x5E8, expected_window) || !expected_window) {
      out.unavailable_reason = "holy_site_creation_registered_window_missing"; return true;
    }
    ReligionContext immediately_before{}; IngameUiGuiOwnerBindingV1 owner{};
    if (!ReadReligion(e, snapshot, stamp, immediately_before) || !SameReligion(before, immediately_before) ||
        !ReadIngameUiGuiOwnerBindingV1(e, owner) || owner != gui_binding) {
      out.unavailable_reason = "holy_site_creation_scope_changed_before_dispatch"; return true;
    }
    creation::UiRequest native{}; native.action = static_cast<creation::UiAction>(request.operation);
    native.type_key = request.holy_site_creation_type_key; native.object_id = request.subject_id;
    native.selected = request.holy_site_creation_selected.value_or(false);
    bool invoked = false, already = false; std::string failure;
    if (open && initial_read && initial.effective_visible && RequestedState(request, initial.holy_site_creation)) {
      already = true; invoked = true;
    } else {
      invoked = creation::InvokeUi12004(binding, handler, immediately_before, native,
          out.native_dispatch_attempted, already, failure);
    }
    out.dispatch_invoked = invoked && out.native_dispatch_attempted;
    out.verification_pending = out.native_dispatch_attempted;
    out.status = out.native_dispatch_attempted ? "verification_pending" : "unavailable";
    ReligionContext after{}; IngameUiResultV1 observed{};
    const bool post = ReadReligion(e, snapshot, stamp, after) && SameReligion(before, after) &&
        Capture(e, handler, binding, after, gui_binding, observed) &&
        observed.holy_site_creation.window == expected_window;
    if (post) {
      out.holy_site_creation = std::move(observed.holy_site_creation);
      out.window_exists = observed.window_exists; out.effective_visible = observed.effective_visible;
      out.enabled = observed.enabled; out.subject_id_available = observed.subject_id_available;
      out.current_subject_id = observed.current_subject_id; out.tree = std::move(observed.tree);
      out.holy_site_creation_ui_postcondition_observed = true;
      out.holy_site_creation_ui_selection_verified = out.effective_visible && RequestedState(request, out.holy_site_creation);
    }
    if (invoked && post && out.holy_site_creation_ui_selection_verified) {
      out.available = true; out.verification_pending = false;
      out.status = already ? "already_selected_verified" : "ui_selection_verified";
      out.unavailable_reason.clear();
    } else {
      out.available = false;
      out.unavailable_reason = !failure.empty() ? failure :
          (out.native_dispatch_attempted ? "holy_site_creation_dispatch_requires_independent_postcondition" :
              "holy_site_creation_ui_not_dispatched");
    }
    return true;
  } catch (...) {
    out.available = false; out.verification_pending = out.native_dispatch_attempted;
    out.status = out.native_dispatch_attempted ? "verification_pending" : "unavailable";
    out.unavailable_reason = "holy_site_creation_navigation_capture_exception"; return true;
  }
}
}
#else
namespace xar::ck3_11906 {
bool HolySiteCreationUiEnabled12004() noexcept { return false; }
bool ExecuteHolySiteCreationNavigation12004(
    const ZhongguoScoreboardNativeEnvironmentV1&, void*, const IngameUiRequestV1&,
    const game::Snapshot&, const MainThreadExecutionStampV1&,
    const IngameUiGuiOwnerBindingV1&, IngameUiResultV1& out) noexcept {
  out.available = false;
  out.unavailable_reason = "holy_site_creation_ui_optin_disabled";
  return true;
}
}
#endif

#include "xar_bridge/scripted_widget_control12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <charconv>
#include <limits>

namespace xar::ck3_11906 {
namespace {
bool Ready(const ScriptedWidgetCapture12004 &v, std::string_view root) {
  return v.root_name == root && v.root != 0 && v.complete && !v.truncated &&
      !v.widgets.empty() && v.widgets.size() <= kNamedGuiTreeInspectionMaximumWidgetsV1 &&
      v.frame.game_pid != 0 && v.frame.played_character_id > 0 && v.frame.native_revision != 0 &&
      v.frame.connection_generation != 0 && v.frame.gui_context != 0 && v.frame.gui_owner != 0 &&
      v.frame.owner_thread_verified && v.frame.source_abi_pins_verified && v.frame.frame_verified;
}
void Quoted(std::string &out, std::string_view text) {
  constexpr char digits[] = "0123456789abcdef";
  out += '"';
  for (const unsigned char c : text) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += digits[c >> 4U]; out += digits[c & 15U]; }
    else out += static_cast<char>(c);
  }
  out += '"';
}
bool Reject(ScriptedWidgetResult12004 &out, std::string_view reason) {
  out.available = false;
  if (!out.action) { out.widgets.clear(); out.query_generation = 0; out.complete = false; }
  out.unavailable_reason.assign(reason); return true;
}
} // namespace

bool ScriptedWidgetRootName12004(std::string_view name) noexcept {
  if (name.empty() || name.size() > 128) return false;
  const auto alpha = [](char c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'); };
  if (!alpha(name.front()) && name.front() != '_') return false;
  for (char c : name) if (!alpha(c) && !(c >= '0' && c <= '9') && c != '_' && c != '.' && c != '-') return false;
  return true;
}
bool ParseScriptedWidgetOpaqueId12004(std::string_view text, std::uint64_t &value) noexcept {
  value = 0;
  if (text.empty() || text.front() == '0') return false;
  const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
  return parsed.ec == std::errc{} && parsed.ptr == text.data() + text.size() && value != 0;
}
bool QueryScriptedWidgetControls12004(ScriptedWidgetProvider12004 &provider,
    const ScriptedWidgetBackend12004 &backend, std::string_view root,
    ScriptedWidgetResult12004 &out) noexcept {
  out = {}; provider.valid = false;
  try {
    out.root_name.assign(root);
    if (!ScriptedWidgetRootName12004(root) || !backend.capture) return Reject(out, "scripted_widget_query_invalid");
    ScriptedWidgetCapture12004 first{}, second{}; std::string reason;
    if (!backend.capture(backend.context, root, first, reason)) {
      out.frame = first.frame; out.truncated = first.truncated;
      return Reject(out, reason.empty() ? "scripted_widget_capture_failed" : reason);
    }
    out.frame = first.frame; out.truncated = first.truncated;
    if (!Ready(first, root)) return Reject(out, "scripted_widget_complete_owner_tree_unavailable");
    if (!backend.capture(backend.context, root, second, reason) || first != second) return Reject(out, "scripted_widget_query_identity_changed");
    if (provider.query_generation == (std::numeric_limits<std::uint64_t>::max)()) return Reject(out, "scripted_widget_query_generation_exhausted");
    for (std::size_t i = 0; i < first.widgets.size(); ++i) {
      first.widgets[i].row.widget_id = static_cast<std::uint64_t>(i) + 1;
      out.widgets.push_back(first.widgets[i].row);
    }
    provider.capture = std::move(first); ++provider.query_generation; provider.valid = true;
    out.query_generation = provider.query_generation; out.complete = true; out.available = true;
    return true;
  } catch (...) { return Reject(out, "scripted_widget_query_exception"); }
}
bool ActivateScriptedWidgetControl12004(ScriptedWidgetProvider12004 &provider,
    const ScriptedWidgetBackend12004 &backend, std::uint64_t generation,
    std::uint64_t id, ScriptedWidgetResult12004 &out) noexcept {
  out = {}; out.action = true; out.query_generation = generation; out.widget_id = id;
  try {
    if (!provider.valid || !generation || generation != provider.query_generation || !id ||
        id > provider.capture.widgets.size() || !backend.capture || !backend.dispatch) return Reject(out, "scripted_widget_reference_stale_or_invalid");
    const auto &saved = provider.capture; out.root_name = saved.root_name; out.frame = saved.frame;
    const auto &target = saved.widgets[static_cast<std::size_t>(id - 1)];
    if (!target.row.clickable) return Reject(out, "scripted_widget_not_currently_clickable");
    ScriptedWidgetCapture12004 fresh{}; std::string reason;
    if (!backend.capture(backend.context, saved.root_name, fresh, reason) || !Ready(fresh, saved.root_name)) return Reject(out, "scripted_widget_fresh_tree_unavailable");
    for (std::size_t i = 0; i < fresh.widgets.size(); ++i) fresh.widgets[i].row.widget_id = static_cast<std::uint64_t>(i) + 1;
    if (fresh != saved) return Reject(out, "scripted_widget_identity_or_frame_changed");
    provider.valid = false; // Before calling any native code: UNKNOWN cannot replay this receipt.
    out.dispatch_invoked = backend.dispatch(backend.context, target, out.native_handled, out.dispatch_attempted);
    out.verification_pending = out.dispatch_attempted;
    if (!out.dispatch_invoked) return Reject(out, out.dispatch_attempted ? "scripted_widget_dispatch_unknown_no_retry" : "scripted_widget_dispatch_admission_failed");
    out.available = true; return true;
  } catch (...) { provider.valid = false; return Reject(out, "scripted_widget_action_exception_no_retry"); }
}
std::string SerializeScriptedWidgetControl12004(const ScriptedWidgetResult12004 &v) {
  std::string out = "{\"schema\":";
  Quoted(out, v.action ? "ck3-native-scripted-widget-control-action-v1" : "ck3-native-scripted-widget-controls-v1");
  const auto text = [&](const char *key, std::string_view value) { out += ",\""; out += key; out += "\":"; Quoted(out, value); };
  const auto number = [&](const char *key, auto value) { out += ",\""; out += key; out += "\":"; out += std::to_string(value); };
  const auto boolean = [&](const char *key, bool value) { out += ",\""; out += key; out += value ? "\":true" : "\":false"; };
  text("step", v.action ? kScriptedWidgetActionStep12004 : kScriptedWidgetQueryStep12004);
  text("game_version", ck3_12004::kGameVersion); text("executable_sha256", ck3_12004::kExecutableSha256);
  boolean("available", v.available); boolean("read_only", !v.action);
  number("game_pid", v.frame.game_pid); number("played_character_id", v.frame.played_character_id); number("date_raw", v.frame.date_raw);
  number("native_revision", v.frame.native_revision); number("connection_generation", v.frame.connection_generation);
  boolean("owner_thread_verified", v.frame.owner_thread_verified); boolean("source_abi_pins_verified", v.frame.source_abi_pins_verified); boolean("frame_verified", v.frame.frame_verified);
  text("root_name", v.root_name); text("query_generation", std::to_string(v.query_generation));
  if (v.action) {
    text("widget_id", std::to_string(v.widget_id)); boolean("dispatch_attempted", v.dispatch_attempted);
    boolean("dispatch_invoked", v.dispatch_invoked); boolean("native_handled", v.native_handled);
    boolean("verification_pending", v.verification_pending); boolean("postcondition_verified", false);
  } else {
    boolean("complete", v.complete); boolean("truncated", v.truncated); out += ",\"widgets\":[";
    bool comma = false;
    for (const auto &row : v.widgets) {
      if (comma) out += ','; comma = true;
      out += "{\"widget_id\":"; Quoted(out, std::to_string(row.widget_id));
      text("runtime_name", row.runtime_name); text("child_path", row.child_path); number("vtable_rva", row.vtable_rva);
      boolean("effective_visible", row.effective_visible); boolean("enabled", row.enabled); boolean("clickable", row.clickable); out += '}';
    }
    out += ']';
  }
  text("unavailable_reason", v.unavailable_reason); out += '}'; return out;
}
} // namespace xar::ck3_11906

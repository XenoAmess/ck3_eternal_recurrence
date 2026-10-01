#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp"

#include <cstring>
#include <sstream>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
bool Copy(std::uintptr_t p, void *out, std::size_t size) noexcept {
  if (!p || !out) return false;
  __try { std::memcpy(out, reinterpret_cast<const void *>(p), size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <typename T> bool Read(std::uintptr_t p, T &out) noexcept { return Copy(p, &out, sizeof(out)); }
struct Key {
  std::array<char, 64> bytes{};
  std::size_t length = 0;
  bool Is(std::string_view s) const noexcept { return length == s.size() && std::memcmp(bytes.data(), s.data(), length) == 0; }
};
bool ReadKey(std::uintptr_t native, Key &out) noexcept {
  std::uint64_t length{}, capacity{};
  if (!Read(native + 0x10, length) || !Read(native + 0x18, capacity) || length > out.bytes.size() || capacity < length) return false;
  std::uintptr_t text = native;
  if (capacity >= 16 && (!Read(native, text) || !text)) return false;
  out.length = static_cast<std::size_t>(length);
  return length == 0 || Copy(text, out.bytes.data(), out.length);
}
bool GlobalKey(SwayInvalidationGlobalKey12002 getter, std::int32_t id,
               const std::string *&out) noexcept {
  if (!getter) return false;
  __try { out = getter(id); return out != nullptr; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Lookup(SwayInvalidationNativeLookup12002 getter, const void *environment,
            std::int32_t id, SwayInvalidationToken12002 &out) noexcept {
  if (!getter || !environment || id < 0) return false;
  __try { return getter(environment, &out, id) == &out; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Core(const CoreBindings &b, CoreSnapshotPrefix &out) noexcept {
  __try { return ReadCoreSnapshot(b, out); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
} // namespace

SwayInvalidationReasonBindings12002 BindSwayInvalidationReasonImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  SwayInvalidationReasonBindings12002 b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true; b.image_base = base;
  b.lookup = reinterpret_cast<SwayInvalidationNativeLookup12002>(base + 0x373B540);
  b.global_key = reinterpret_cast<SwayInvalidationGlobalKey12002>(base + 0x3F4F900);
  b.scheme_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD60);
  b.owner_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD5C);
  b.target_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD58);
  return b;
}
SwayInvalidationReasonCapture12002 CaptureSwayInvalidationReason12002(
    const SwayInvalidationReasonBindings12002 &b, const void *native_effect,
    const void *native_context, SwayInvalidationReasonSource12002 &out) noexcept {
  out = {};
  if (!b.enabled || !b.core.enabled || !b.image_base || !native_effect || !native_context)
    return SwayInvalidationReasonCapture12002::unavailable;
  const auto effect = reinterpret_cast<std::uintptr_t>(native_effect);
  const auto context = reinterpret_cast<std::uintptr_t>(native_context);
  std::uintptr_t table{};
  if (!Read(effect, table)) return SwayInvalidationReasonCapture12002::unavailable;
  if (table != b.image_base + 0x4837428) return SwayInvalidationReasonCapture12002::ignored;
  std::uint8_t mode{};
  std::int32_t command_id{};
  if (!Read(effect + 0x0C, mode) || !Read(effect + 0x08, command_id)) return SwayInvalidationReasonCapture12002::unavailable;
  if (mode != 0) return SwayInvalidationReasonCapture12002::ignored;
  const std::string *native_command{};
  Key command;
  if (!GlobalKey(b.global_key, command_id, native_command) ||
      !ReadKey(reinterpret_cast<std::uintptr_t>(native_command), command)) return SwayInvalidationReasonCapture12002::unavailable;
  if (!command.Is("send_interface_toast")) return SwayInvalidationReasonCapture12002::ignored;
  std::uintptr_t scalar{}, scalar_table{}, title_wrapper{};
  std::uint16_t title_scope{};
  Key title;
  if (!Read(effect + 0x60, title_wrapper) || title_wrapper != b.image_base + 0x48BD0B0 ||
      !Read(effect + 0x68, title_scope) || title_scope != 4 || !Read(effect + 0x70, scalar) || !scalar ||
      !Read(scalar, scalar_table) || scalar_table != b.image_base + 0x4929F08 ||
      !ReadKey(scalar + 0x30, title)) return SwayInvalidationReasonCapture12002::unavailable;
  if (!title.Is("sway_invalidated_title")) return SwayInvalidationReasonCapture12002::ignored;
  std::uintptr_t children{}, child{}, child_table{};
  std::int32_t child_count{};
  if (!Read(effect + 0x30, children) || !Read(effect + 0x3C, child_count)) return SwayInvalidationReasonCapture12002::unavailable;
  if (child_count != 1) return SwayInvalidationReasonCapture12002::ignored;
  if (!children || !Read(children, child) || !child || !Read(child, child_table)) return SwayInvalidationReasonCapture12002::unavailable;
  const bool tooltip = child_table == b.image_base + 0x4931918 || child_table == b.image_base + 0x4931850;
  const bool description = child_table == b.image_base + 0x4931D10;
  if (!tooltip && !description) return SwayInvalidationReasonCapture12002::ignored;
  std::int32_t nested_count{}, child_command_id{};
  std::uint8_t child_mode{};
  if (!Read(child + 0x3C, nested_count) || !Read(child + 0x0C, child_mode) || !Read(child + 8, child_command_id))
    return SwayInvalidationReasonCapture12002::unavailable;
  if (nested_count != 0 || child_mode != 0) return SwayInvalidationReasonCapture12002::ignored;
  const std::string *native_child_command{};
  Key child_command;
  if (!GlobalKey(b.global_key, child_command_id, native_child_command) ||
      !ReadKey(reinterpret_cast<std::uintptr_t>(native_child_command), child_command))
    return SwayInvalidationReasonCapture12002::unavailable;
  if ((tooltip && !child_command.Is("custom_tooltip")) ||
      (description && !child_command.Is("custom_description_no_bullet"))) return SwayInvalidationReasonCapture12002::ignored;
  Key reason;
  if (!ReadKey(child + 0x50, reason)) return SwayInvalidationReasonCapture12002::unavailable;
  if (tooltip && reason.Is("sway_invalidated_dead")) out.branch = SwayInvalidationNotificationBranch12002::target_dead_notification_source;
  else if (tooltip && reason.Is("sway_invalidated_war")) out.branch = SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source;
  else if (description && reason.Is("scheme_target_not_in_diplomatic_range")) out.branch = SwayInvalidationNotificationBranch12002::out_of_range_notification_source;
  else return SwayInvalidationReasonCapture12002::ignored;
  std::uintptr_t root{}, environment{};
  std::int32_t scheme_identifier{}, owner_identifier{}, target_identifier{};
  if (!Read(context, root) || !root || !Read(root, out.root) ||
      !Read(context + 0x18, environment) || !environment ||
      !Read(reinterpret_cast<std::uintptr_t>(b.scheme_identifier), scheme_identifier) ||
      !Read(reinterpret_cast<std::uintptr_t>(b.owner_identifier), owner_identifier) ||
      !Read(reinterpret_cast<std::uintptr_t>(b.target_identifier), target_identifier) ||
      !Lookup(b.lookup, reinterpret_cast<const void *>(environment), scheme_identifier, out.scheme) ||
      !Lookup(b.lookup, reinterpret_cast<const void *>(environment), owner_identifier, out.owner) ||
      !Lookup(b.lookup, reinterpret_cast<const void *>(environment), target_identifier, out.target))
    return SwayInvalidationReasonCapture12002::unavailable;
  if (out.root.kind != 4 || out.owner.kind != 4 || out.target.kind != 4 || out.scheme.kind != 9)
    return SwayInvalidationReasonCapture12002::ignored;
  out.actor_character_id = static_cast<std::uint32_t>(out.owner.payload);
  out.target_character_id = static_cast<std::uint32_t>(out.target.payload);
  out.scheme_id = static_cast<std::uint32_t>(out.scheme.payload);
  if (out.actor_character_id == 0xFFFFFFFFu || out.target_character_id == 0xFFFFFFFFu || out.scheme_id == 0xFFFFFFFFu ||
      static_cast<std::uint32_t>(out.root.payload) != out.actor_character_id) return SwayInvalidationReasonCapture12002::ignored;
  CoreSnapshotPrefix frame{};
  if (!Core(b.core, frame) || !frame.map_ready || !frame.has_played_character || !frame.played_character_alive)
    return SwayInvalidationReasonCapture12002::unavailable;
  if (static_cast<std::uint32_t>(frame.played_character_id) != out.actor_character_id)
    return SwayInvalidationReasonCapture12002::ignored;
  out.date_raw = frame.clock.date_raw; out.selected_notification_branch_observed = true;
  return SwayInvalidationReasonCapture12002::captured;
}
void SwayInvalidationReasonRecorder12002::SetObserverAttached(bool a) noexcept { attached_ = a; }
bool SwayInvalidationReasonRecorder12002::ObserverAttached() const noexcept { return attached_; }
bool SwayInvalidationReasonRecorder12002::Append(const SwayInvalidationReasonSource12002 &s) noexcept {
  if (!attached_ || !s.selected_notification_branch_observed || s.branch == SwayInvalidationNotificationBranch12002::none) return false;
  records_[(first_ + count_) % records_.size()] = {next_sequence_++, s};
  if (count_ < records_.size()) ++count_; else first_ = (first_ + 1) % records_.size();
  return true;
}
bool SwayInvalidationReasonRecorder12002::Query(const SwayInvalidationReasonQuery12002 &request,
    SwayInvalidationReasonQueryResult12002 &out) const noexcept {
  out = {}; out.request = request; out.observer_attached = attached_;
  try {
    if (!attached_) { out.unavailable_reason = "sway_invalidation_reason_sink_not_attached"; return false; }
    if (request.actor_character_id == 0xFFFFFFFFu || request.target_character_id == 0xFFFFFFFFu || request.scheme_id == 0xFFFFFFFFu) {
      out.unavailable_reason = "sway_invalidation_reason_query_identity_unavailable"; return false;
    }
    if (count_) {
      out.earliest_sequence = records_[first_].sequence;
      out.latest_sequence = records_[(first_ + count_ - 1) % records_.size()].sequence;
      out.retention_gap = request.after_sequence != 0 && request.after_sequence < out.earliest_sequence - 1;
    }
    for (std::size_t i = 0; i < count_; ++i) {
      const auto &r = records_[(first_ + i) % records_.size()];
      if (r.sequence > request.after_sequence && r.source.actor_character_id == request.actor_character_id &&
          r.source.target_character_id == request.target_character_id && r.source.scheme_id == request.scheme_id) out.records.push_back(r);
    }
    out.available = true; return true;
  } catch (...) { out.available = false; out.records.clear(); out.unavailable_reason = "sway_invalidation_reason_query_internal_error"; return false; }
}
SwayInvalidationReasonCapture12002 CaptureAndRecordSwayInvalidationReason12002(
    const SwayInvalidationReasonBindings12002 &b, const void *effect, const void *context,
    SwayInvalidationReasonRecorder12002 &recorder) noexcept {
  if (!recorder.ObserverAttached()) return SwayInvalidationReasonCapture12002::unavailable;
  SwayInvalidationReasonSource12002 source;
  const auto result = CaptureSwayInvalidationReason12002(b, effect, context, source);
  if (result == SwayInvalidationReasonCapture12002::captured && !recorder.Append(source))
    return SwayInvalidationReasonCapture12002::unavailable;
  return result;
}
const char *SwayInvalidationNotificationBranchKey12002(SwayInvalidationNotificationBranch12002 b) noexcept {
  switch (b) {
  case SwayInvalidationNotificationBranch12002::target_dead_notification_source: return "target_dead_notification_source";
  case SwayInvalidationNotificationBranch12002::out_of_range_notification_source: return "out_of_range_notification_source";
  case SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source: return "opaque_existing_stock_notification_source";
  default: return "none";
  }
}
const char *SwayInvalidationAuthoredReasonKey12002(SwayInvalidationNotificationBranch12002 b) noexcept {
  switch (b) {
  case SwayInvalidationNotificationBranch12002::target_dead_notification_source: return "sway_invalidated_dead";
  case SwayInvalidationNotificationBranch12002::out_of_range_notification_source: return "scheme_target_not_in_diplomatic_range";
  case SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source: return "sway_invalidated_war";
  default: return "";
  }
}
std::string SerializeSwayInvalidationReason12002(const SwayInvalidationReasonQueryResult12002 &r) {
  std::ostringstream out;
  out << "{\"schema\":\"xar.ck3.sway-invalidation-notification-source.v1\",\"available\":" << (r.available ? "true" : "false")
      << ",\"unavailable_reason\":\"" << r.unavailable_reason << "\",\"read_only\":true,\"observer_attached\":"
      << (r.observer_attached ? "true" : "false") << ",\"actor_character_id\":" << r.request.actor_character_id
      << ",\"target_character_id\":" << r.request.target_character_id << ",\"scheme_instance_id\":" << r.request.scheme_id
      << ",\"after_sequence\":" << r.request.after_sequence << ",\"earliest_sequence\":" << r.earliest_sequence
      << ",\"latest_sequence\":" << r.latest_sequence << ",\"retention_gap\":" << (r.retention_gap ? "true" : "false")
      << ",\"session_records_only\":true,\"message_enqueue_observed\":false,\"render_observed\":false"
      << ",\"material_effect_observed\":false,\"native_end_cause_observed\":false,\"native_terminal_state_observed\":false,\"records\":[";
  bool first = true;
  for (const auto &record : r.records) {
    if (!first) out << ','; first = false;
    const auto &s = record.source;
    out << "{\"sequence\":" << record.sequence << ",\"source_branch\":\"" << SwayInvalidationNotificationBranchKey12002(s.branch)
        << "\",\"authored_command\":\"send_interface_toast\",\"authored_title\":\"sway_invalidated_title\",\"authored_reason_key\":\""
        << SwayInvalidationAuthoredReasonKey12002(s.branch) << "\",\"date_raw\":" << s.date_raw
        << ",\"actor_character_id\":" << s.actor_character_id << ",\"target_character_id\":" << s.target_character_id
        << ",\"scheme_instance_id\":" << s.scheme_id << ",\"scheme_instance_generation\":" << (s.scheme_id >> 24)
        << ",\"root_scope_kind\":" << s.root.kind << ",\"scheme_scope_kind\":" << s.scheme.kind
        << ",\"selected_notification_branch_observed\":true,\"exact_scope_join_ready\":true"
        << ",\"message_enqueue_observed\":false,\"render_observed\":false,\"material_effect_observed\":false"
        << ",\"native_end_cause_observed\":false,\"native_terminal_state_observed\":false}";
  }
  out << "]}"; return out.str();
}
} // namespace xar::ck3_12002

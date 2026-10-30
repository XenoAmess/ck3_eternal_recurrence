#include "xar_bridge/sway_invalidation_branch_12004.hpp"

#include <cstring>
#include <windows.h>

// The title reader and reason reader share the admitted actual.4 parent/frame.
// Neither reader establishes an invalidator-to-end or material-effect relation.

namespace xar::ck3_12004 {
namespace {
using ck3_12002::CoreSnapshotPrefix;
using ck3_12002::SwayExecutionBindings12002;
using ck3_12002::SwayExecutionCaptureResult12002;
using ck3_12002::SwayExecutionScopeToken12002;
using ck3_12002::SwayInvalidationNotificationBranch12002;
using ck3_12002::SwayInvalidationReasonCapture12002;
using ck3_12002::SwayInvalidationReasonSource12002;
using ck3_12002::SwayInvalidationToken12002;

bool Copy(std::uintptr_t address, void *output, std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <class T> bool Read(std::uintptr_t address, T &output) noexcept {
  return Copy(address, &output, sizeof(output));
}
struct Key {
  std::array<char, 64> bytes{};
  std::size_t length = 0;
  bool Is(std::string_view expected) const noexcept {
    return length == expected.size() &&
        std::memcmp(bytes.data(), expected.data(), length) == 0;
  }
};
bool ReadKey(std::uintptr_t value, Key &output) noexcept {
  std::uint64_t length{}, capacity{};
  if (!Read(value + 0x10, length) || !Read(value + 0x18, capacity) ||
      length > output.bytes.size() || capacity < length) return false;
  auto text = value;
  if (capacity >= 16 && (!Read(value, text) || text == 0)) return false;
  output.length = static_cast<std::size_t>(length);
  return length == 0 || Copy(text, output.bytes.data(), output.length);
}
bool Command(const SwayExecutionBindings12002 &b, std::int32_t identifier,
             Key &output) noexcept {
  const std::string *value{};
  __try { value = b.get_global_command_key(identifier); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
  return value != nullptr && ReadKey(reinterpret_cast<std::uintptr_t>(value), output);
}
bool Core(const SwayExecutionBindings12002 &b, CoreSnapshotPrefix &output) noexcept {
  __try { return b.read_core_snapshot(b.core, output); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Table(const SwayExecutionBindings12002 &b, void *&output) noexcept {
  __try { output = b.get_script_identifier_table(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
  return output != nullptr;
}
struct NativeStringView32 {
  const char *data;
  std::int32_t size;
  std::int32_t padding;
};
bool NamedScope(const SwayExecutionBindings12002 &b, void *table,
    const void *environment, std::string_view name,
    SwayExecutionScopeToken12002 &output) noexcept {
  std::int32_t identifier = -1;
  const NativeStringView32 view{name.data(), static_cast<std::int32_t>(name.size()), 0};
  __try {
    if (b.lookup_script_identifier_id(table, &identifier, &view) == nullptr || identifier < 0)
      return false;
    return b.lookup(environment, &output, identifier) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.map_ready == b.map_ready &&
      a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
SwayExecutionCaptureResult12002 Unavailable(SwayInvalidationBranchSource12004 &out,
                                          const char *reason) {
  out.unavailable_reason = reason;
  return SwayExecutionCaptureResult12002::unavailable;
}
SwayExecutionCaptureResult12002 ReasonChild(const SwayExecutionBindings12002 &b,
    std::uintptr_t effect, SwayInvalidationNotificationBranch12002 &branch) noexcept {
  std::uintptr_t children{}, child{}, table{};
  std::int32_t count{};
  if (!Read(effect + 0x30, children) || !Read(effect + 0x3C, count))
    return SwayExecutionCaptureResult12002::unavailable;
  if (count != 1) return SwayExecutionCaptureResult12002::ignored;
  if (children == 0 || !Read(children, child) || child == 0 || !Read(child, table))
    return SwayExecutionCaptureResult12002::unavailable;
  const bool tooltip = table == b.image_base + 0x4931928;
  const bool description = table == b.image_base + 0x4931D20;
  if (!tooltip && !description) return SwayExecutionCaptureResult12002::ignored;
  std::int32_t nested_count{}, command_id{};
  std::uint8_t mode{};
  if (!Read(child + 0x3C, nested_count) || !Read(child + 0x0C, mode) ||
      !Read(child + 0x08, command_id))
    return SwayExecutionCaptureResult12002::unavailable;
  if (nested_count != 0 || mode != 0) return SwayExecutionCaptureResult12002::ignored;
  Key command, reason;
  if (!Command(b, command_id, command)) return SwayExecutionCaptureResult12002::unavailable;
  if ((tooltip && !command.Is("custom_tooltip")) ||
      (description && !command.Is("custom_description_no_bullet")))
    return SwayExecutionCaptureResult12002::ignored;
  if (!ReadKey(child + 0x50, reason)) return SwayExecutionCaptureResult12002::unavailable;
  if (tooltip && reason.Is("sway_invalidated_dead"))
    branch = SwayInvalidationNotificationBranch12002::target_dead_notification_source;
  else if (tooltip && reason.Is("sway_invalidated_war"))
    branch = SwayInvalidationNotificationBranch12002::opaque_existing_stock_notification_source;
  else if (description && reason.Is("scheme_target_not_in_diplomatic_range"))
    branch = SwayInvalidationNotificationBranch12002::out_of_range_notification_source;
  else return SwayExecutionCaptureResult12002::ignored;
  return SwayExecutionCaptureResult12002::captured;
}
SwayInvalidationToken12002 ReasonToken(const SwayExecutionScopeToken12002 &token) noexcept {
  return {token.type, token.subtype, token.reserved, token.payload};
}
SwayExecutionCaptureResult12002 Capture(const SwayExecutionBindings12002 &b,
    std::uintptr_t effect, std::uintptr_t context, SwayInvalidationBranchSource12004 &out,
    SwayInvalidationReasonSource12002 *reason_output = nullptr) {
  if (!b.enabled || !b.core.enabled || b.image_base == 0 || effect == 0 || context == 0 ||
      b.effect_vtable_rvas != kSwayExecutionVtableRvas12004 ||
      b.title_wrapper_vtable_rva != kSwayExecutionTitleWrapperRva12004 ||
      b.scalar_localization_vtable_rva != kSwayExecutionScalarRva12004 ||
      b.lookup == nullptr || b.lookup_script_identifier_id == nullptr ||
      b.get_global_command_key == nullptr || b.get_script_identifier_table == nullptr ||
      b.read_core_snapshot == nullptr)
    return Unavailable(out, "sway_invalidation_current_profile_unavailable");

  std::uintptr_t vtable{};
  if (!Read(effect, vtable)) return Unavailable(out, "sway_invalidation_effect_unavailable");
  if (vtable != b.image_base + kSwayExecutionVtableRvas12004[1])
    return SwayExecutionCaptureResult12002::ignored;
  std::int32_t command_id{};
  std::uint8_t command_domain{};
  Key command;
  if (!Read(effect + 0x08, command_id) || !Read(effect + 0x0C, command_domain))
    return Unavailable(out, "sway_invalidation_command_unavailable");
  if (command_domain != 0)
    return Unavailable(out, "sway_invalidation_dynamic_command_unsupported");
  if (!Command(b, command_id, command))
    return Unavailable(out, "sway_invalidation_command_unavailable");
  if (!command.Is("send_interface_toast")) return SwayExecutionCaptureResult12002::ignored;

  std::uintptr_t wrapper_vtable{}, scalar{}, scalar_vtable{}, delegate{};
  std::uint16_t title_scope_type{};
  Key title;
  if (!Read(effect + 0x60, wrapper_vtable) ||
      wrapper_vtable != b.image_base + kSwayExecutionTitleWrapperRva12004 ||
      !Read(effect + 0x68, title_scope_type) || title_scope_type != 4 ||
      !Read(effect + 0x70, scalar) || scalar == 0 ||
      !Read(scalar, scalar_vtable) ||
      scalar_vtable != b.image_base + kSwayExecutionScalarRva12004 ||
      !Read(scalar + 0x28, delegate) || delegate != 0 || !ReadKey(scalar + 0x30, title))
    return Unavailable(out, "sway_invalidation_authored_scalar_title_unavailable");
  if (!title.Is(kSwayInvalidationTitleKey12004)) return SwayExecutionCaptureResult12002::ignored;

  CoreSnapshotPrefix before{};
  if (!Core(b, before) || !before.map_ready || !before.has_played_character ||
      !before.played_character_alive)
    return Unavailable(out, "sway_invalidation_played_actor_unavailable");
  std::uintptr_t root{}, environment{};
  if (!Read(context, root) || root == 0 || !Read(root, out.root) ||
      !Read(context + 0x18, environment) || environment == 0)
    return Unavailable(out, "sway_invalidation_exact_context_unavailable");
  if (out.root.type != 4 || static_cast<std::uint32_t>(out.root.payload) !=
      static_cast<std::uint32_t>(before.played_character_id))
    return SwayExecutionCaptureResult12002::ignored;
  void *table{};
  if (!Table(b, table) ||
      !NamedScope(b, table, reinterpret_cast<const void *>(environment), "scheme", out.scheme) ||
      !NamedScope(b, table, reinterpret_cast<const void *>(environment), "owner", out.owner) ||
      !NamedScope(b, table, reinterpret_cast<const void *>(environment), "target", out.target))
    return Unavailable(out, "sway_invalidation_native_scope_lookup_unavailable");
  if (out.owner.type != 4 || out.target.type != 4 || out.scheme.type != 9)
    return Unavailable(out, "sway_invalidation_required_named_scope_unavailable");
  out.actor_character_id = static_cast<std::uint32_t>(out.owner.payload);
  out.target_character_id = static_cast<std::uint32_t>(out.target.payload);
  out.scheme_id = static_cast<std::uint32_t>(out.scheme.payload);
  if (out.actor_character_id != static_cast<std::uint32_t>(out.root.payload) ||
      out.actor_character_id == 0xFFFFFFFFu || out.target_character_id == 0xFFFFFFFFu ||
      out.scheme_id == 0xFFFFFFFFu)
    return Unavailable(out, "sway_invalidation_full_scope_join_unavailable");
  auto branch = SwayInvalidationNotificationBranch12002::none;
  if (reason_output != nullptr) {
    const auto result = ReasonChild(b, effect, branch);
    if (result != SwayExecutionCaptureResult12002::captured) return result;
  }
  CoreSnapshotPrefix after{};
  if (!Core(b, after) || !SameFrame(before, after))
    return Unavailable(out, "sway_invalidation_actor_date_changed");
  out.date_raw = before.clock.date_raw;
  out.executing_input_observed = true;
  if (reason_output != nullptr) {
    reason_output->branch = branch;
    reason_output->date_raw = out.date_raw;
    reason_output->actor_character_id = out.actor_character_id;
    reason_output->target_character_id = out.target_character_id;
    reason_output->scheme_id = out.scheme_id;
    reason_output->root = ReasonToken(out.root);
    reason_output->scheme = ReasonToken(out.scheme);
    reason_output->owner = ReasonToken(out.owner);
    reason_output->target = ReasonToken(out.target);
    reason_output->selected_notification_branch_observed = true;
  }
  return SwayExecutionCaptureResult12002::captured;
}
} // namespace

ck3_12002::SwayExecutionBindings12002 BindSwayInvalidationBranchImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  return BindSwayExecutionImage12004(base, sha);
}
ck3_12002::SwayExecutionCaptureResult12002 CaptureSwayInvalidationBranch12004(
    const ck3_12002::SwayExecutionBindings12002 &b, const void *effect,
    const void *context, SwayInvalidationBranchSource12004 &output) noexcept {
  output = {};
  try { return Capture(b, reinterpret_cast<std::uintptr_t>(effect),
                       reinterpret_cast<std::uintptr_t>(context), output); }
  catch (...) { return Unavailable(output, "sway_invalidation_capture_internal_error"); }
}

ck3_12002::SwayInvalidationReasonCapture12002 CaptureSwayInvalidationReason12004(
    const ck3_12002::SwayExecutionBindings12002 &b, const void *effect,
    const void *context, ck3_12002::SwayInvalidationReasonSource12002 &output) noexcept {
  output = {};
  try {
    SwayInvalidationBranchSource12004 parent;
    switch (Capture(b, reinterpret_cast<std::uintptr_t>(effect),
                    reinterpret_cast<std::uintptr_t>(context), parent, &output)) {
    case SwayExecutionCaptureResult12002::ignored:
      return SwayInvalidationReasonCapture12002::ignored;
    case SwayExecutionCaptureResult12002::unavailable:
      return SwayInvalidationReasonCapture12002::unavailable;
    case SwayExecutionCaptureResult12002::captured:
      return SwayInvalidationReasonCapture12002::captured;
    }
  } catch (...) { output = {}; }
  return SwayInvalidationReasonCapture12002::unavailable;
}

} // namespace xar::ck3_12004

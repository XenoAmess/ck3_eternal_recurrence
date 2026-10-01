#include "xar_bridge/ck3_12002_sway_completion_execution.hpp"

#include <cstring>
#include <limits>
#include <sstream>
#include <utility>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
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
bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
  __try { return ReadCoreSnapshot(bindings, output); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Table(EventGetRegistry getter, void *&output) noexcept {
  if (getter == nullptr) return false;
  __try { output = getter(); return output != nullptr; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Identifier(EventResolveIdentifierName resolver, void *table,
    std::int32_t identifier, const std::string *&output) noexcept {
  if (resolver == nullptr || table == nullptr) return false;
  __try { output = resolver(table, identifier); return output != nullptr; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool GlobalCommandKey(SwayExecutionGlobalCommandKeyGetter12002 getter,
    std::int32_t identifier, const std::string *&output) noexcept {
  if (getter == nullptr) return false;
  __try { output = getter(identifier); return output != nullptr; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Lookup(SwayExecutionNativeLookup12002 getter, const void *environment,
    std::int32_t identifier, SwayExecutionScopeToken12002 &output) noexcept {
  if (getter == nullptr || environment == nullptr || identifier < 0) return false;
  __try { return getter(environment, &output, identifier) == &output; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
// All canonical identifiers in this source contract fit inside this buffer.
// Compare original scalar keys, never the localized message renderer output.
struct CopiedKey {
  std::array<char, 64> bytes{};
  std::size_t length = 0;
  bool Is(std::string_view expected) const noexcept {
    return length == expected.size() &&
        std::memcmp(bytes.data(), expected.data(), length) == 0;
  }
};
bool Key(std::uintptr_t native_string, CopiedKey &output) noexcept {
  std::uint64_t length{}, capacity{};
  if (!Read(native_string + 0x10, length) || !Read(native_string + 0x18, capacity) ||
      length > output.bytes.size() || capacity < length) return false;
  std::uintptr_t text = native_string;
  if (capacity >= 16 && (!Read(native_string, text) || text == 0)) return false;
  output.length = static_cast<std::size_t>(length);
  return length == 0 || Copy(text, output.bytes.data(), output.length);
}
bool Name(const SwayExecutionBindings12002 &b, void *table,
    std::int32_t identifier, CopiedKey &output) noexcept {
  const std::string *native{};
  return Identifier(b.resolve_script_identifier_name, table, identifier, native) &&
      Key(reinterpret_cast<std::uintptr_t>(native), output);
}
SwayExecutionCaptureResult12002 Unavailable(SwayExecutionSource12002 &out,
    const char *reason) {
  out.unavailable_reason = reason;
  return SwayExecutionCaptureResult12002::unavailable;
}
bool FrameSame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw &&
      a.played_character_id == b.played_character_id &&
      a.has_played_character == b.has_played_character &&
      a.played_character_alive == b.played_character_alive &&
      a.map_ready == b.map_ready;
}
SwayExecutionCaptureResult12002 Capture(const SwayExecutionBindings12002 &b,
    std::uintptr_t effect, std::uintptr_t context, SwayExecutionSource12002 &out) {
  if (!b.enabled || !b.core.enabled || b.image_base == 0 || effect == 0 || context == 0)
    return Unavailable(out, "sway_execution_build_or_entry_unavailable");
  std::uintptr_t vtable{};
  if (!Read(effect, vtable)) return Unavailable(out, "sway_execution_effect_unavailable");
  if (vtable != b.image_base + kSwayExecutionMessageVtableRva12002 &&
      vtable != b.image_base + kSwayExecutionToastVtableRva12002 &&
      vtable != b.image_base + kSwayExecutionPopupVtableRva12002)
    return SwayExecutionCaptureResult12002::ignored;
  std::int32_t command_id{};
  std::uint8_t command_domain{};
  CopiedKey command;
  if (!Read(effect + 0x08, command_id) || !Read(effect + 0x0C, command_domain))
    return Unavailable(out, "sway_execution_command_identifier_unavailable");
  if (command_domain != 0)
    return Unavailable(out, "sway_execution_dynamic_command_identifier_unsupported");
  const std::string *native_command{};
  if (!GlobalCommandKey(b.get_global_command_key, command_id, native_command) ||
      !Key(reinterpret_cast<std::uintptr_t>(native_command), command))
    return Unavailable(out, "sway_execution_command_identifier_unavailable");
  if (!command.Is("send_interface_message")) return SwayExecutionCaptureResult12002::ignored;
  void *table{};
  if (!Table(b.get_script_identifier_table, table))
    return Unavailable(out, "sway_execution_identifier_table_unavailable");
  std::uint8_t type_state{};
  CopiedKey type;
  if (!Read(effect + 0x5C, type_state))
    return Unavailable(out, "sway_execution_message_type_unavailable");
  if (type_state == 2) {
    std::uintptr_t definition{};
    std::uint32_t marker{};
    if (!Read(effect + 0x50, definition) || definition == 0 ||
        !Read(definition + 0x38, marker) || marker != 0x4744624F ||
        !Key(definition + 0x18, type))
      return Unavailable(out, "sway_execution_resolved_type_unavailable");
  } else if (type_state == 1) {
    std::int32_t type_identifier{};
    if (!Read(effect + 0x58, type_identifier) || !Name(b, table, type_identifier, type))
      return Unavailable(out, "sway_execution_authored_type_unavailable");
  } else {
    return SwayExecutionCaptureResult12002::ignored;
  }
  if (!type.Is("sway_good_message") && !type.Is("sway_bad_message"))
    return SwayExecutionCaptureResult12002::ignored;
  std::uintptr_t title_wrapper_vtable{}, scalar{}, scalar_vtable{};
  std::uint16_t title_scope_type{};
  CopiedKey title;
  if (!Read(effect + 0x60, title_wrapper_vtable) ||
      title_wrapper_vtable != b.image_base + kSwayExecutionTitleWrapperVtableRva12002 ||
      !Read(effect + 0x68, title_scope_type) || title_scope_type != 4 ||
      !Read(effect + 0x70, scalar) || scalar == 0 ||
      !Read(scalar, scalar_vtable) ||
      scalar_vtable != b.image_base + kSwayExecutionScalarLocalizationVtableRva12002 ||
      !Key(scalar + 0x30, title))
    return Unavailable(out, "sway_execution_authored_scalar_title_unavailable");
  if (type.Is("sway_good_message") && title.Is("sway_sway_success_message"))
    out.branch = SwayExecutionSourceBranch12002::hidden_phase_success_source;
  else if (type.Is("sway_bad_message") && title.Is("sway_sway_failed_message"))
    out.branch = SwayExecutionSourceBranch12002::hidden_phase_failure_source;
  else return SwayExecutionCaptureResult12002::ignored;

  CoreSnapshotPrefix before{};
  if (!Core(b.core, before) || !before.map_ready || !before.has_played_character ||
      !before.played_character_alive)
    return Unavailable(out, "sway_execution_played_actor_unavailable");
  std::uintptr_t root{}, environment{};
  if (!Read(context, root) || root == 0 || !Read(root, out.root) ||
      !Read(context + 0x18, environment) || environment == 0)
    return Unavailable(out, "sway_execution_exact_context_unavailable");
  if (out.root.type != 4 || static_cast<std::uint32_t>(out.root.payload) !=
      static_cast<std::uint32_t>(before.played_character_id))
    return SwayExecutionCaptureResult12002::ignored;
  bool owner_found = false, target_found = false, scheme_found = false;
  if (b.lookup != nullptr) {
    std::int32_t scheme_identifier{}, owner_identifier{}, target_identifier{};
    if (!Read(reinterpret_cast<std::uintptr_t>(b.scheme_identifier), scheme_identifier) ||
        !Read(reinterpret_cast<std::uintptr_t>(b.owner_identifier), owner_identifier) ||
        !Read(reinterpret_cast<std::uintptr_t>(b.target_identifier), target_identifier) ||
        !Lookup(b.lookup, reinterpret_cast<const void *>(environment), scheme_identifier, out.scheme) ||
        !Lookup(b.lookup, reinterpret_cast<const void *>(environment), owner_identifier, out.owner) ||
        !Lookup(b.lookup, reinterpret_cast<const void *>(environment), target_identifier, out.target))
      return Unavailable(out, "sway_execution_native_scope_lookup_unavailable");
    scheme_found = out.scheme.type != 0;
    owner_found = out.owner.type != 0;
    target_found = out.target.type != 0;
  } else {
    // Legacy hand-bound Env32 fixture inputs. Production BindImage always
    // supplies the native overlay getter and identifier globals.
    if (b.scheme_identifier != nullptr || b.owner_identifier != nullptr ||
        b.target_identifier != nullptr)
      return Unavailable(out, "sway_execution_native_scope_lookup_unavailable");
    std::uintptr_t data{};
    std::int32_t capacity{}, count{};
    if (!Read(environment, data) || !Read(environment + 0x08, capacity) ||
        !Read(environment + 0x0C, count) || count < 0 || capacity < count ||
        (count > 0 && data == 0))
      return Unavailable(out, "sway_execution_exact_context_unavailable");
    for (std::int32_t i = 0; i < count; ++i) {
      const auto row = data + static_cast<std::size_t>(i) * 0x20;
      std::int32_t identifier{};
      CopiedKey name;
      if (!Read(row, identifier) || !Name(b, table, identifier, name))
        return Unavailable(out, "sway_execution_scope_identifier_unavailable");
      SwayExecutionScopeToken12002 *token = nullptr;
      bool *found = nullptr;
      if (name.Is("owner")) { token = &out.owner; found = &owner_found; }
      else if (name.Is("target")) { token = &out.target; found = &target_found; }
      else if (name.Is("scheme")) { token = &out.scheme; found = &scheme_found; }
      if (token != nullptr) {
        if (*found || !Read(row + 0x08, *token))
          return Unavailable(out, "sway_execution_named_scope_not_unique");
        *found = true;
      }
    }
  }
  if (!owner_found || !target_found || !scheme_found ||
      out.owner.type != 4 || out.target.type != 4 || out.scheme.type != 9)
    return Unavailable(out, "sway_execution_required_named_scope_unavailable");
  out.actor_character_id = static_cast<std::uint32_t>(out.owner.payload);
  out.target_character_id = static_cast<std::uint32_t>(out.target.payload);
  out.scheme_id = static_cast<std::uint32_t>(out.scheme.payload);
  if (out.actor_character_id != static_cast<std::uint32_t>(out.root.payload) ||
      out.actor_character_id == 0xFFFFFFFFu || out.target_character_id == 0xFFFFFFFFu ||
      out.scheme_id == 0xFFFFFFFFu)
    return Unavailable(out, "sway_execution_full_scope_join_unavailable");
  CoreSnapshotPrefix after{};
  if (!Core(b.core, after) || !FrameSame(before, after))
    return Unavailable(out, "sway_execution_actor_date_changed");
  out.date_raw = before.clock.date_raw;
  return SwayExecutionCaptureResult12002::captured;
}
} // namespace

SwayExecutionBindings12002 BindSwayExecutionImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  SwayExecutionBindings12002 b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true; b.image_base = base;
  b.lookup = reinterpret_cast<SwayExecutionNativeLookup12002>(base + 0x373B540);
  b.scheme_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD60);
  b.owner_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD5C);
  b.target_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5D4BD58);
  b.get_global_command_key = reinterpret_cast<SwayExecutionGlobalCommandKeyGetter12002>(
      base + kSwayExecutionGlobalCommandKeyGetterRva12002);
  b.get_script_identifier_table = reinterpret_cast<EventGetRegistry>(
      base + kEventScriptIdentifierTableGetterRva);
  b.resolve_script_identifier_name = reinterpret_cast<EventResolveIdentifierName>(
      base + kEventScriptIdentifierNameResolverRva);
  return b;
}
SwayExecutionCaptureResult12002 CaptureSwayCompletionExecution12002(
    const SwayExecutionBindings12002 &b, const void *effect,
    const void *context, SwayExecutionSource12002 &output) noexcept {
  output = {};
  try { return Capture(b, reinterpret_cast<std::uintptr_t>(effect),
                       reinterpret_cast<std::uintptr_t>(context), output); }
  catch (...) { return Unavailable(output, "sway_execution_capture_internal_error"); }
}
void SwayExecutionRecorder12002::SetObserverAttached(bool attached) noexcept { attached_ = attached; }
bool SwayExecutionRecorder12002::ObserverAttached() const noexcept { return attached_; }
bool SwayExecutionRecorder12002::Append(const SwayExecutionSource12002 &source) noexcept {
  if (!attached_ || source.branch == SwayExecutionSourceBranch12002::none ||
      !source.unavailable_reason.empty()) return false;
  try {
    SwayExecutionRecord12002 record{next_sequence_, source};
    const auto destination = (first_ + count_) % records_.size();
    records_[destination] = std::move(record);
    ++next_sequence_;
    if (count_ < records_.size()) ++count_;
    else first_ = (first_ + 1) % records_.size();
    return true;
  } catch (...) { return false; }
}
bool SwayExecutionRecorder12002::Query(const SwayExecutionQuery12002 &request,
    SwayExecutionQueryResult12002 &output) const noexcept {
  output = {}; output.request = request; output.observer_attached = attached_;
  try {
    if (!attached_) { output.unavailable_reason = "sway_execution_observer_not_attached"; return false; }
    if (request.actor_character_id == 0xFFFFFFFFu || request.target_character_id == 0xFFFFFFFFu ||
        request.scheme_id == 0xFFFFFFFFu) {
      output.unavailable_reason = "sway_execution_query_identity_unavailable"; return false;
    }
    if (count_ != 0) {
      output.earliest_sequence = records_[first_].sequence;
      output.latest_sequence = records_[(first_ + count_ - 1) % records_.size()].sequence;
      output.retention_gap = request.after_sequence != 0 &&
          request.after_sequence < output.earliest_sequence - 1;
    }
    for (std::size_t i = 0; i < count_; ++i) {
      const auto &record = records_[(first_ + i) % records_.size()];
      if (record.sequence > request.after_sequence &&
          record.source.actor_character_id == request.actor_character_id &&
          record.source.target_character_id == request.target_character_id &&
          record.source.scheme_id == request.scheme_id) output.records.push_back(record);
    }
    output.available = true; return true;
  } catch (...) {
    output.available = false; output.unavailable_reason = "sway_execution_query_internal_error";
    output.records.clear(); return false;
  }
}
SwayExecutionCaptureResult12002 CaptureAndRecordSwayCompletionExecution12002(
    const SwayExecutionBindings12002 &b, const void *effect,
    const void *context, SwayExecutionRecorder12002 &recorder) noexcept {
  if (!recorder.ObserverAttached()) return SwayExecutionCaptureResult12002::unavailable;
  SwayExecutionSource12002 source;
  const auto result = CaptureSwayCompletionExecution12002(b, effect, context, source);
  if (result == SwayExecutionCaptureResult12002::captured && !recorder.Append(source))
    return SwayExecutionCaptureResult12002::unavailable;
  return result;
}
const char *SwayExecutionBranchKey12002(SwayExecutionSourceBranch12002 branch) noexcept {
  switch (branch) {
  case SwayExecutionSourceBranch12002::hidden_phase_success_source: return "hidden_phase_success_source";
  case SwayExecutionSourceBranch12002::hidden_phase_failure_source: return "hidden_phase_failure_source";
  default: return "none";
  }
}
std::string SerializeSwayCompletionExecution12002(const SwayExecutionQueryResult12002 &result) {
  std::ostringstream out;
  out << "{\"schema\":\"xar.ck3.sway-completion-execution.v1\",\"available\":"
      << (result.available ? "true" : "false")
      << ",\"unavailable_reason\":\"" << result.unavailable_reason << "\""
      << ",\"read_only\":true,\"observer_attached\":" << (result.observer_attached ? "true" : "false")
      << ",\"actor_character_id\":" << result.request.actor_character_id
      << ",\"target_character_id\":" << result.request.target_character_id
      << ",\"scheme_instance_id\":" << result.request.scheme_id
      << ",\"after_sequence\":" << result.request.after_sequence
      << ",\"earliest_sequence\":" << result.earliest_sequence
      << ",\"latest_sequence\":" << result.latest_sequence
      << ",\"retention_gap\":" << (result.retention_gap ? "true" : "false")
      << ",\"material_effect_observed\":false,\"native_terminal_state_observed\":false,\"records\":[";
  bool first = true;
  for (const auto &record : result.records) {
    if (!first) out << ',';
    first = false;
    const auto &source = record.source;
    out << "{\"sequence\":" << record.sequence << ",\"date_raw\":" << source.date_raw
        << ",\"actor_character_id\":" << source.actor_character_id
        << ",\"target_character_id\":" << source.target_character_id
        << ",\"scheme_instance_id\":" << source.scheme_id
        << ",\"scheme_instance_generation\":" << (source.scheme_id >> 24)
        << ",\"source_branch\":\"" << SwayExecutionBranchKey12002(source.branch)
        << "\",\"stock_event\":\""
        << (source.branch == SwayExecutionSourceBranch12002::hidden_phase_success_source ?
            "sway_outcome.0001" : "sway_outcome.0002")
        << "\",\"executing_input_observed\":true,\"exact_scope_join_ready\":true"
        << ",\"phase_result\":\""
        << (source.branch == SwayExecutionSourceBranch12002::hidden_phase_success_source ? "success" : "failure")
        << "\",\"message_enqueue_observed\":false,\"material_effect_observed\":false"
        << ",\"native_terminal_state_observed\":false}";
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12002

#include "xar_bridge/generic_trigger_receiver_372df10_12004.hpp"
#include "xar_bridge/root_scope_initializer_889f60_12004.hpp"
#include "xar_bridge/source_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kEvaluationFlagRva = 0x5D1DADC;
struct ScopedRead {
  SourceLeafReadOnlyAccess12004 native;
  const GenericTriggerRootScopeView12004 &scope;
};
bool CopyScoped(void *context, const void *address, void *output, std::size_t size) noexcept {
  auto &r = *static_cast<ScopedRead *>(context);
  const auto start = reinterpret_cast<std::uintptr_t>(address);
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (!output || size == 0 || start > maximum - size) return false;
  if (r.scope.storage == GenericTriggerScopeStorage12004::source_projection) {
    const auto base = r.scope.identity;
    const auto extent = r.scope.owned_bytes.size();
    if (base > maximum - extent) return false;
    const auto end = start + size, scope_end = base + extent;
    if (start < scope_end && end > base) {
      if (start < base || end > scope_end) return false;
      const auto offset = static_cast<std::size_t>(start - base);
      for (std::size_t i = 0; i < size; ++i)
        if (r.scope.defined_bytes[offset + i] == 0) return false;
      std::memcpy(output, r.scope.owned_bytes.data() + offset, size);
      return true;
    }
  }
  return r.native.read_memory &&
      r.native.read_memory(r.native.context, address, output, size);
}
template<class T>
std::optional<T> Field(ScopedRead &r, std::uintptr_t base, std::size_t offset) noexcept {
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (!base || offset > maximum - base || sizeof(T) > maximum - (base + offset)) return {};
  T value{};
  if (!CopyScoped(&r, reinterpret_cast<const void *>(base + offset), &value, sizeof(value))) return {};
  return value;
}
bool ScopeShape(const GenericTriggerRootScopeView12004 &s) noexcept {
  if (!s.identity) return false;
  if (s.storage == GenericTriggerScopeStorage12004::borrowed_current_scope)
    return s.owned_bytes.empty() && s.defined_bytes.empty();
  return !s.owned_bytes.empty() && s.owned_bytes.size() == s.defined_bytes.size() &&
      s.identity == reinterpret_cast<std::uintptr_t>(s.owned_bytes.data()) &&
      s.identity <= (std::numeric_limits<std::uintptr_t>::max)() - s.owned_bytes.size();
}
} // namespace

GenericTriggerReceiver372DF10Result12004 ReadGenericTriggerReceiver372DF1012004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceReadFrame12004 &frame,
    std::uintptr_t receiver, const GenericTriggerRootScopeView12004 &scope,
    std::optional<std::uint8_t> copied_flag) noexcept {
  GenericTriggerReceiver372DF10Result12004 out{};
  try {
    out.read_frame = frame;
    out.receiver_identity = receiver;
    out.scope_root_word = scope.copied_root_word;
    out.scope_full_id_payload = scope.copied_full_id_payload;
    out.evaluation_flag_raw_u8 = copied_flag;
    out.scope_is_source_projection = scope.storage == GenericTriggerScopeStorage12004::source_projection;
    if (!out.scope_is_source_projection && scope.identity) out.current_scope_identity = scope.identity;
    if (!SourceReadFrameReady12004(frame)) {
      out.unavailable_reason = "generic_trigger_current_caller_frame_unavailable"; return out;
    }
    out.copied_frame_ready = true;
    if (!receiver || !ScopeShape(scope)) {
      out.unavailable_reason = "generic_trigger_receiver_or_scope_view_unavailable"; return out;
    }
    ScopedRead reader{access, scope};
    if (out.scope_is_source_projection || !out.scope_root_word) {
      const auto word = Field<std::uint16_t>(reader, scope.identity, 0);
      if (out.scope_root_word && word != out.scope_root_word) {
        out.scope_root_word = word;
        out.unavailable_reason = "generic_trigger_projected_root_word_mismatch_or_unknown"; return out;
      }
      out.scope_root_word = word;
    }
    if (out.scope_is_source_projection || !out.scope_full_id_payload) {
      const auto payload = Field<std::uint64_t>(reader, scope.identity, 8);
      if (out.scope_full_id_payload && payload != out.scope_full_id_payload) {
        out.scope_full_id_payload = payload;
        out.unavailable_reason = "generic_trigger_projected_payload_mismatch_or_unknown"; return out;
      }
      out.scope_full_id_payload = payload;
    }
    if (!out.scope_root_word || !out.scope_full_id_payload) {
      out.unavailable_reason = "generic_trigger_scope_scalar_copy_unavailable"; return out;
    }
    if (!out.evaluation_flag_raw_u8)
      out.evaluation_flag_raw_u8 = Field<std::uint8_t>(reader, frame.module_base, kEvaluationFlagRva);
    SourceLeafFrame12004 child{};
    child.read_frame = frame; child.producer_rva = 0x372E000;
    child.receiver_identity = receiver; child.primary_scope_identity = scope.identity;
    child.primary_scope_root_word = out.scope_root_word;
    PrisonerQuoteInternalAliases12004 aliases{};
    aliases.primary_scope = scope.identity; aliases.secondary_scope = std::uintptr_t{0};
    aliases.tertiary_scope = scope.identity; aliases.primary_scope_root_word = out.scope_root_word;
    aliases.evaluation_flag_raw_u8 = out.evaluation_flag_raw_u8;
    // Only the exact source alias shape is modeled. No native stack/support
    // address is supplied, including when the original root is borrowed.
    aliases.physical_aliases_copied = false;
    const SourceLeafReadOnlyAccess12004 guarded{&reader, &CopyScoped};
    const auto raw = ReadPrisonerAutoAcceptTriggerCondition12004(guarded, child, aliases);
    out.trigger_vtable_raw = raw.trigger_vtable; out.slot58_raw = raw.root_kind_getter_slot58;
    out.slot60_raw = raw.root_mask_getter_slot60; out.slotc8_raw = raw.evaluator_slotc8;
    out.descriptor_provider = raw.scope_table_provider;
    // Reuse the one42 copied field set. 63's output schema carries these raw
    // inputs into the shared evaluator; no second root/vptr/slot copy or
    // preferred-kind/mask algorithm is introduced.
    SourceTriggerRootScopeGateResult12004 gate{};
    gate.frame = child; gate.frame.producer_rva = 0x372B4C0;
    gate.trigger_identity = receiver; gate.primary_scope_identity = scope.identity;
    gate.root_scope_kind_raw_u16 = out.scope_root_word; gate.trigger_vptr_raw = raw.trigger_vtable;
    gate.slot58_address_raw = raw.root_kind_getter_slot58; gate.slot60_address_raw = raw.root_mask_getter_slot60;
    gate.raw_copy_ready = out.scope_root_word.has_value() && gate.trigger_vptr_raw.has_value() &&
        gate.slot58_address_raw.has_value() && gate.slot60_address_raw.has_value();
    const auto condition = EvaluatePrisonerAutoAcceptTriggerCondition12004(raw, gate);
    out.copied_inputs_ready = out.evaluation_flag_raw_u8.has_value() && raw.query_frame_ready &&
        raw.parent_alias_shape_matches && *raw.parent_alias_shape_matches &&
        raw.all_attempted_native_reads_complete && gate.raw_copy_ready;
    out.source_value_ready = condition.source_value_ready &&
        condition.source_projected_returned_raw_u8.has_value() &&
        out.evaluation_flag_raw_u8.has_value();
    if (out.source_value_ready) out.raw_al = condition.source_projected_returned_raw_u8;
    out.unavailable_reason = out.evaluation_flag_raw_u8
        ? condition.unavailable_reason : "generic_trigger_evaluation_flag_copy_unavailable";
    return out;
  } catch (...) {
    out.raw_al.reset(); out.source_value_ready = false;
    out.unavailable_reason = "generic_trigger_readonly_projection_exception"; return out;
  }
}

GenericTriggerReceiver372DF10Result12004 ProjectGenericTriggerOwnerScope372DF1012004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceReadFrame12004 &frame,
    std::uintptr_t receiver, std::uint16_t word, std::uint64_t payload,
    std::optional<std::uint8_t> copied_flag) noexcept {
  GenericTriggerReceiver372DF10Result12004 out{};
  try {
    out.read_frame = frame; out.receiver_identity = receiver;
    out.scope_root_word = word; out.scope_full_id_payload = payload;
    out.scope_is_source_projection = true; out.evaluation_flag_raw_u8 = copied_flag;
    if (!SourceReadFrameReady12004(frame)) {
      out.unavailable_reason = "generic_trigger_current_caller_frame_unavailable"; return out;
    }
    // Stable local storage is never copied/moved while its self-pointers are
    // consumed. Unknown initializer holes remain masked, even if physically0.
    std::array<std::byte, kRootScopeInitializer889F60Extent12004> bytes{};
    std::array<std::uint8_t, kRootScopeInitializer889F60Extent12004> mask{};
    const RootScopeInitializer889F60Source12004 source{
        frame.module_base, frame.executable_sha256, true};
    const auto initialized = ProjectOwnedRootScopeInitializer889F6012004(source, bytes, mask);
    if (!initialized.available) {
      out.unavailable_reason = "generic_trigger_scope_initializer_projection_unavailable"; return out;
    }
    std::memcpy(bytes.data(), &word, sizeof(word));
    std::memcpy(bytes.data() + 8, &payload, sizeof(payload));
    GenericTriggerRootScopeView12004 scope{};
    scope.identity = reinterpret_cast<std::uintptr_t>(bytes.data());
    scope.owned_bytes = bytes; scope.defined_bytes = mask;
    scope.copied_root_word = word; scope.copied_full_id_payload = payload;
    return ReadGenericTriggerReceiver372DF1012004(access, frame, receiver, scope, copied_flag);
  } catch (...) {
    out.unavailable_reason = "generic_trigger_scope_projection_exception"; return out;
  }
}

bool TryReadGenericTriggerOwnerScope372DF1012004(
    void *child_context, SourceLeafGuardedRead12004 read_memory, void *read_context,
    std::uintptr_t receiver, std::uint16_t word, std::uint64_t payload,
    std::uint8_t &raw_al) noexcept {
  try {
    auto *context = static_cast<GenericTriggerOwnerScopeChildContext12004 *>(child_context);
    if (context && context->copied_result) {
      context->copied_result->raw_al.reset();
      context->copied_result->source_value_ready = false;
      context->copied_result->native_callback_executed = false;
      context->copied_result->actual_trigger_evaluation_observed = false;
    }
    GenericTriggerReceiver372DF10Result12004 result{};
    result.receiver_identity = receiver; result.scope_root_word = word;
    result.scope_full_id_payload = payload; result.scope_is_source_projection = true;
    if (!context || !context->current_query_frame) {
      result.unavailable_reason = "generic_trigger_current_caller_frame_unavailable";
      if (context && context->copied_result) *context->copied_result = result;
      return false;
    }
    const SourceLeafReadOnlyAccess12004 access{read_context, read_memory};
    result = ProjectGenericTriggerOwnerScope372DF1012004(access,
        *context->current_query_frame, receiver, word, payload, context->copied_evaluation_flag);
    if (context->copied_result) *context->copied_result = result;
    if (!result.source_value_ready || !result.raw_al) return false;
    raw_al = *result.raw_al;
    return true;
  } catch (...) {
    return false;
  }
}
} // namespace xar::ck3_12004

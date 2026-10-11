#include "xar_bridge/religion_creation_price_source_12004.hpp"

#include <windows.h>
#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>

namespace xar::ck3_12004::religion_price_source {
namespace {
using namespace piety_price_raw_inputs;

bool ProcessRead(void *, const void *source, void *destination,
                 std::size_t size) noexcept {
  if (!source || !destination) return false;
  SIZE_T copied = 0;
  return ReadProcessMemory(GetCurrentProcess(), source, destination, size,
                           &copied) != FALSE && copied == size;
}

bool CopyRead(void *opaque, const void *source, void *destination,
              std::size_t size) noexcept {
  auto &probe = *static_cast<ReligionCreationPriceSourceProbe12004 *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (!probe.access.exact_12004_bound || !probe.access.guarded_read ||
      !source || !destination || !size ||
      size - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address)
    return false;
  if (probe.copied_reads.size() >= probe.maximum_read_occurrences ||
      size > probe.maximum_copied_bytes - probe.copied_bytes) {
    probe.copy_budget_exceeded = true;
    return false;
  }
  try {
    ReligionCreationPriceSourceReadAtom12004 atom;
    atom.address = address;
    atom.bytes.resize(size);
    if (!probe.access.guarded_read(probe.access.context, source,
                                  atom.bytes.data(), size)) return false;
    probe.copied_reads.push_back(std::move(atom));
    std::memcpy(destination, probe.copied_reads.back().bytes.data(), size);
    probe.copied_bytes += size;
    return true;
  } catch (...) {
    return false;
  }
}

PietyPriceNumericAccess12004 OwnedAccess(
    ReligionCreationPriceSourceProbe12004 &probe) noexcept {
  return {probe.access.module_base, &probe, CopyRead,
          probe.access.exact_12004_bound};
}

template<class T> bool Field(const PietyPriceNumericAccess12004 &access,
                            std::uintptr_t object, std::size_t offset,
                            std::optional<T> &output) noexcept {
  T value{};
  if (!ReadPietyPriceNumericField12004(access, object, offset, value)) return false;
  output = value;
  return true;
}

// Native compares only the low24 index against the unsigned count, then
// requires the full requested DWORD at the physical object ID member.
ReligionPriceResolvedObject12004 Resolve(
    const PietyPriceNumericAccess12004 &access, std::uintptr_t storage,
    std::optional<std::uint32_t> requested,
    std::optional<std::uintptr_t> fallback, std::size_t id_offset) noexcept {
  ReligionPriceResolvedObject12004 out;
  out.requested_full_id = requested;
  std::uintptr_t candidate = 0;
  bool use_fallback = storage == 0;
  if (!use_fallback) {
    if (!requested) { out.reason = "requested_full_id_unavailable"; return out; }
    std::uint32_t count = 0;
    if (!ReadPietyPriceNumericField12004(access, storage, 0x2C, count)) {
      out.reason = "registry_count_unreadable"; return out;
    }
    const auto index = *requested & 0x00FFFFFFU;
    use_fallback = index >= count;
    if (!use_fallback) {
      std::uintptr_t data = 0;
      if (!ReadPietyPriceNumericField12004(access, storage, 0x20, data) ||
          !ReadPietyPriceNumericField12004(access, data,
              static_cast<std::size_t>(index) * 16 + 8, candidate)) {
        out.reason = "registry_entry_unreadable"; return out;
      }
      use_fallback = candidate == 0;
      if (!use_fallback) {
        std::uint32_t physical_id = 0;
        if (!ReadPietyPriceNumericField12004(access, candidate, id_offset,
                                          physical_id)) {
          out.reason = "candidate_full_id_unreadable"; return out;
        }
        use_fallback = physical_id != *requested;
        if (!use_fallback) out.resolved_full_id = physical_id;
      }
    }
  }
  out.used_fallback = use_fallback;
  if (use_fallback) {
    if (!fallback) { out.reason = "fallback_pointer_unreadable"; return out; }
    candidate = *fallback;
  }
  out.selected_identity = candidate;
  if (!candidate) { out.reason = "selected_object_null"; return out; }
  if (!out.resolved_full_id &&
      !Field(access, candidate, id_offset, out.resolved_full_id)) {
    out.reason = "selected_physical_full_id_unreadable"; return out;
  }
  out.ready = true;
  out.reason = use_fallback ? "literal_fallback_selected" : "full_id_resolved";
  return out;
}

ReligionCreationPriceSourceInputs12004 ReadInputs(
    ReligionCreationPriceSourceProbe12004 &probe,
    std::uintptr_t window) noexcept {
  ReligionCreationPriceSourceInputs12004 out;
  out.window_identity = window;
  const auto access = OwnedAccess(probe);
  if (!window) { out.reason = "current_window_absent"; return out; }
  if (0xB28U > (std::numeric_limits<std::uintptr_t>::max)() - window) {
    out.reason = "price_payload_address_overflow"; return out;
  }
  out.price_payload_identity = window + 0xB28;
  if (!Field(access, window, 0xC8, out.window_source_rite_carrier)) {
    out.reason = "old_window_rite_carrier_unreadable"; return out;
  }
  if (!Field(access, access.module_base, 0x5C67568,
             out.character_storage_identity) ||
      !Field(access, access.module_base, 0x5C67570,
             out.character_fallback_identity)) {
    out.reason = "character_registry_or_fallback_unreadable"; return out;
  }
  std::optional<std::uint32_t> first_request;
  if (*out.character_storage_identity && !Field(access, window, 0xCC, first_request)) {
    out.reason = "first_actor_window_full_id_unreadable"; return out;
  }
  out.first_actor = Resolve(access, *out.character_storage_identity,
      first_request, out.character_fallback_identity, 0x18);
  if (!out.first_actor.ready) { out.reason = out.first_actor.reason; return out; }

  if (!Field(access, access.module_base, 0x5D1E2F8, out.rite_storage_identity)) {
    out.reason = "rite_registry_unreadable"; return out;
  }
  std::optional<std::uint32_t> rite_request;
  if (*out.rite_storage_identity &&
      !Field(access, *out.first_actor.selected_identity, 0xB4, rite_request)) {
    out.reason = "first_actor_current_rite_full_id_unreadable"; return out;
  }
  // Unlike the Character fallback, this global is loaded only on a reached
  // fallback route. Determine the route first and read it only if necessary.
  out.current_rite = Resolve(access, *out.rite_storage_identity,
                            rite_request, std::nullopt, 0x8);
  if (!out.current_rite.ready &&
      out.current_rite.reason == "fallback_pointer_unreadable") {
    if (!Field(access, access.module_base, 0x5C67670, out.rite_fallback_identity)) {
      out.reason = "rite_fallback_pointer_unreadable"; return out;
    }
    // Avoid a second registry traversal: the reached fallback is already known.
    auto selected = Resolve(access, 0, rite_request, out.rite_fallback_identity, 0x8);
    out.current_rite = std::move(selected);
  }
  if (!out.current_rite.ready) { out.reason = out.current_rite.reason; return out; }

  std::optional<std::uint32_t> second_request;
  if (*out.character_storage_identity && !Field(access, window, 0xCC, second_request)) {
    out.reason = "second_actor_window_full_id_unreadable"; return out;
  }
  out.second_actor = Resolve(access, *out.character_storage_identity,
      second_request, out.character_fallback_identity, 0x18);
  if (!out.second_actor.ready) { out.reason = out.second_actor.reason; return out; }
  out.complete = true;
  out.reason = "actual_getter_inputs_copied";
  return out;
}

std::optional<bool> CheckCopiedSpans(
    const ReligionCreationPriceSourceProbe12004 &probe) noexcept {
  if (probe.copy_budget_exceeded) return std::nullopt;
  try {
    std::vector<std::byte> current;
    for (const auto &atom : probe.copied_reads) {
      current.resize(atom.bytes.size());
      if (!probe.access.guarded_read(probe.access.context,
          reinterpret_cast<const void *>(atom.address), current.data(), current.size()))
        return std::nullopt;
      if (current != atom.bytes) return false;
    }
    return true;
  } catch (...) {
    return std::nullopt;
  }
}

std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') { out += '\\'; out += static_cast<char>(value); }
    else if (value < 0x20) { out += "\\u00"; out += hex[value >> 4]; out += hex[value & 15]; }
    else out += static_cast<char>(value);
  }
  return out + '"';
}
template<class T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string Boolean(bool value) { return value ? "true" : "false"; }
std::string Boolean(std::optional<bool> value) {
  return value ? Boolean(*value) : "null";
}
std::string Pointer(std::uintptr_t value) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string text;
  do { text.insert(text.begin(), hex[value & 15]); value >>= 4; } while (value);
  return Quote("0x" + text);
}
std::string Pointer(const std::optional<std::uintptr_t> &value) {
  return value ? Pointer(*value) : "null";
}
std::string Resolved(const ReligionPriceResolvedObject12004 &out) {
  return "{\"ready\":" + Boolean(out.ready) + ",\"reason\":" + Quote(out.reason) +
      ",\"requested_full_id\":" + Number(out.requested_full_id) +
      ",\"selected_identity\":" + Pointer(out.selected_identity) +
      ",\"resolved_full_id\":" + Number(out.resolved_full_id) +
      ",\"used_fallback\":" + Boolean(out.used_fallback) + "}";
}
std::string Inputs(const ReligionCreationPriceSourceInputs12004 &out) {
  return "{\"complete\":" + Boolean(out.complete) + ",\"reason\":" + Quote(out.reason) +
      ",\"window_identity\":" + Pointer(out.window_identity) +
      ",\"price_payload_identity\":" + Pointer(out.price_payload_identity) +
      ",\"window_source_rite_carrier\":" + Number(out.window_source_rite_carrier) +
      ",\"character_storage_identity\":" + Pointer(out.character_storage_identity) +
      ",\"character_fallback_identity\":" + Pointer(out.character_fallback_identity) +
      ",\"rite_storage_identity\":" + Pointer(out.rite_storage_identity) +
      ",\"rite_fallback_identity\":" + Pointer(out.rite_fallback_identity) +
      ",\"first_actor\":" + Resolved(out.first_actor) +
      ",\"current_rite\":" + Resolved(out.current_rite) +
      ",\"second_actor\":" + Resolved(out.second_actor) + "}";
}

std::string ActorTerm(const std::optional<ActorPietyCollectionTermObservation12004> &term) {
  if (!term) return "null";
  const auto &out = *term;
  return "{\"source_ready\":" + Boolean(out.source_ready) +
      ",\"reason\":" + Quote(out.reason) +
      ",\"requested_key_raw_u32\":" + std::to_string(out.requested_key_raw_u32) +
      ",\"collection_still_current\":" + Boolean(out.collection_still_current) +
      ",\"collection_identity\":" + (out.collection_selection ?
          Pointer(out.collection_selection->context_address) : "null") +
      ",\"collection_source_ready\":" + (out.collection_selection ?
          Boolean(out.collection_selection->ready) : "null") +
      ",\"collection_reason\":" + (out.collection_selection ?
          Quote(out.collection_selection->reason) : "null") +
      ",\"term_source_ready\":" + (out.collection_term ?
          Boolean(out.collection_term->source_ready) : "null") +
      ",\"term_reason\":" + (out.collection_term ?
          Quote(out.collection_term->unavailable_reason) : "null") +
      ",\"scaled_term_raw_q64\":" + Number(out.scaled_term_raw_q64) + "}";
}

std::string Base(const std::optional<CreatePietyDynamicBaseCostObservation12004> &base) {
  if (!base) return "null";
  const auto &out = *base;
  std::string rows = "[";
  for (const auto &row : out.ordered_contributions) {
    if (rows.size() != 1) rows += ',';
    std::string child = "null";
    std::visit([&child](const auto &value) {
      using T = std::decay_t<decltype(value)>;
      if constexpr (!std::is_same_v<T, std::monostate>) {
        child = "{\"source_ready\":" + Boolean(value.source_ready) +
            ",\"reason\":" + Quote(value.reason) +
            ",\"selected_expression_identity\":" + Pointer(value.selected_expression_identity) +
            ",\"native_eax_raw\":" + Number(value.native_eax_raw) +
            ",\"dynamic_input_copy_reason\":" + Quote(value.dynamic_input_copy.input_copy_reason) +
            ",\"dynamic_callback_attempted\":" + Boolean(value.dynamic_input_copy.callback_attempted) + "}";
      }
    }, row.child);
    rows += "{\"collection\":" + std::to_string(row.collection) +
        ",\"ordinal\":" + std::to_string(row.ordinal) +
        ",\"full_element_pointer\":" + Pointer(row.full_element_pointer) +
        ",\"native_eax_raw\":" + Number(row.native_eax_raw) +
        ",\"scaled_raw\":" + Number(row.scaled_raw) +
        ",\"contribution_applied\":" + Boolean(row.contribution_applied) +
        ",\"child\":" + child + "}";
  }
  return "{\"complete\":" + Boolean(out.complete) + ",\"reason\":" + Quote(out.reason) +
      ",\"composition_source_ready\":" + Boolean(out.composition_source_ready) +
      ",\"reached_numeric_sources_ready\":" + Boolean(out.reached_numeric_sources_ready) +
      ",\"first_data\":" + Pointer(out.first_data) +
      ",\"first_count_raw\":" + Number(out.first_count_raw) +
      ",\"second_data\":" + Pointer(out.second_data) +
      ",\"second_count_raw\":" + Number(out.second_count_raw) +
      ",\"stopped_collection\":" + Number(out.stopped_collection) +
      ",\"stopped_ordinal\":" + Number(out.stopped_ordinal) +
      ",\"base_price_raw_q64\":" + Number(out.base_price_raw_q64) +
      ",\"ordered_contributions\":" + rows + "]}";
}

std::string RiteTerm(const std::optional<RitePietyPriceTerm2C628A012004> &term) {
  if (!term) return "null";
  const auto &out = *term;
  return "{\"source_ready\":" + Boolean(out.source_ready) +
      ",\"reason\":" + Quote(out.reason) +
      ",\"route\":" + std::to_string(static_cast<unsigned>(out.route)) +
      ",\"native_term_raw_q64\":" + Number(out.native_term_raw_q64) +
      ",\"provider\":" + Pointer(out.provider) +
      ",\"definition_table\":" + Pointer(out.definition_table) +
      ",\"definition\":" + Pointer(out.definition) +
      ",\"definition_enabled_byte_7c\":" + Number(out.definition_enabled_byte_7c) +
      ",\"literal_flag_byte_7b\":" + Number(out.literal_flag_byte_7b) +
      ",\"expression\":" + Pointer(out.expression) +
      ",\"expression_receiver\":" + Pointer(out.expression_receiver) +
      ",\"expression_vtable\":" + Pointer(out.expression_vtable) +
      ",\"expression_virtual_30\":" + Pointer(out.expression_virtual_30) +
      ",\"dynamic_context_operands_copied\":" + Boolean(out.dynamic_context_operands_copied) + "}";
}

std::string Model(const std::optional<CreatePietyFinalPriceSourceObservation12004> &model) {
  if (!model) return "null";
  const auto &out = *model;
  return "{\"source_ready\":" + Boolean(out.source_ready) +
      ",\"actual_original_consumed_values\":false,\"reason\":" + Quote(out.reason) +
      ",\"stopped_stage\":" + std::to_string(static_cast<unsigned>(out.stopped_stage)) +
      ",\"price_payload\":" + Pointer(out.price_payload) +
      ",\"current_rite\":" + Pointer(out.current_rite) +
      ",\"actor\":" + Pointer(out.actor) +
      ",\"actor_full_id_raw_u32\":" + std::to_string(out.actor_full_id_raw_u32) +
      ",\"rite_full_id_carrier_u32\":" + std::to_string(out.rite_full_id_carrier_u32) +
      ",\"unchanged_snapshot_revision\":" + std::to_string(out.unchanged_snapshot_revision) +
      ",\"source_qualified_actor_fallback\":" + Boolean(out.source_qualified_actor_fallback) +
      ",\"create_base\":" + Base(out.create_base) +
      ",\"actor_property_223\":" + ActorTerm(out.actor_property_223) +
      ",\"entered_base_with223_raw_q64\":" + Number(out.entered_base_with223_raw_q64) +
      ",\"rite_term\":" + RiteTerm(out.rite_term) +
      ",\"actor_property_224\":" + ActorTerm(out.actor_property_224) +
      ",\"final_piety_price_raw_q64\":" + Number(out.final_piety_price_raw_q64) + "}";
}
} // namespace

piety_price_raw_inputs::PietyPriceNumericAccess12004
BindReligionCreationPriceSourceAccess12004(
    std::uintptr_t base, std::string_view hash) noexcept {
  if (!base || hash != kReligionPriceSourceExecutableSha25612004) return {};
  return {base, nullptr, ProcessRead, true};
}

ReligionCreationPriceSourceProbe12004 BeginReligionCreationPriceSource12004(
    const PietyPriceNumericAccess12004 &access, std::uintptr_t window,
    const ReligionCreationPriceSourceFrame12004 &frame) noexcept {
  ReligionCreationPriceSourceProbe12004 probe;
  probe.access = access;
  probe.packet.frame = frame;
  probe.packet.before.window_identity = window;
  if (!access.exact_12004_bound || !access.module_base || !access.guarded_read) {
    probe.packet.reason = "actual4_source_access_unavailable";
    probe.packet.before.reason = probe.packet.reason;
    return probe;
  }
  if (!frame.mailbox_before_accepted || !frame.owning_thread_id ||
      !frame.stamp_paused || frame.date_raw != frame.stamp_date_raw) {
    probe.packet.reason = "source_mailbox_frame_not_admitted";
    probe.packet.before.reason = probe.packet.reason;
    return probe;
  }
  probe.packet.before = ReadInputs(probe, window);
  probe.packet.reason = probe.packet.before.reason;
  return probe;
}

ReligionCreationPriceSourcePacket12004 CompleteReligionCreationPriceSource12004(
    ReligionCreationPriceSourceProbe12004 &probe,
    std::optional<bool> selector, bool quote_available) noexcept {
  auto &packet = probe.packet;
  packet.editing_owned_current_rite = quote_available ? selector : std::nullopt;
  try {
    if (packet.before.complete && packet.editing_owned_current_rite &&
        !*packet.editing_owned_current_rite) {
      const auto access = OwnedAccess(probe);
      CreatePietyDynamicBaseCostBindings12004 bindings{};
      bindings.access = access;
      bindings.definition_numeric.access = access;
      bindings.entry_numeric.access = access;
      // Both dynamic operand callbacks intentionally remain absent.
      const auto &inputs = packet.before;
      packet.source_model.emplace(ReadCreatePietyFinalPriceSourceModel12004(
          bindings, *inputs.price_payload_identity,
          *inputs.current_rite.selected_identity, *inputs.second_actor.selected_identity,
          *inputs.second_actor.resolved_full_id, *inputs.current_rite.resolved_full_id,
          packet.frame.snapshot_revision, *inputs.second_actor.used_fallback));
    }
    if (packet.before.complete) {
      packet.after = ReadInputs(probe, packet.before.window_identity);
      packet.input_mappings_still_current = *packet.after == packet.before;
      packet.copied_spans_still_current = CheckCopiedSpans(probe);
    }
    if (!packet.before.complete) packet.reason = packet.before.reason;
    else if (!packet.editing_owned_current_rite) packet.reason = "existing_edit_selector_unavailable";
    else if (*packet.editing_owned_current_rite) packet.reason = "edit_owned_branch_not_projected";
    else if (probe.copy_budget_exceeded) packet.reason = "source_copy_budget_exceeded";
    else if (packet.input_mappings_still_current != std::optional<bool>{true})
      packet.reason = "source_input_mappings_changed_or_unavailable";
    else if (packet.copied_spans_still_current != std::optional<bool>{true})
      packet.reason = "source_copied_spans_changed_or_unavailable";
    else if (!packet.source_model || !packet.source_model->source_ready ||
             !packet.source_model->final_piety_price_raw_q64)
      packet.reason = "source_model_partial";
    else packet.reason = "awaiting_mailbox_finish";
  } catch (...) {
    packet.reason = "source_projection_copy_exception";
  }
  packet.copied_read_count = probe.copied_reads.size();
  packet.copied_bytes = probe.copied_bytes;
  return std::move(packet);
}

void FinishReligionCreationPriceSourceMailbox12004(
    ReligionCreationPriceSourcePacket12004 &packet, bool accepted) noexcept {
  packet.frame.mailbox_after_accepted = accepted;
  packet.source_ready = accepted && packet.reason == "awaiting_mailbox_finish";
  if (packet.source_ready) {
    packet.final_piety_price_raw_q64 = packet.source_model->final_piety_price_raw_q64;
    packet.reason = "same_query_create_source_price_ready";
  } else {
    packet.final_piety_price_raw_q64.reset();
    if (!accepted) packet.reason = "source_mailbox_after_guard_rejected";
  }
}

std::string SerializeReligionCreationPriceSource12004(
    const ReligionCreationPriceSourcePacket12004 &packet) {
  const auto &f = packet.frame;
  const std::string frame = "{\"snapshot_revision\":" + std::to_string(f.snapshot_revision) +
      ",\"query_sequence\":" + std::to_string(f.query_sequence) +
      ",\"capture_epoch\":" + std::to_string(f.capture_epoch) +
      ",\"date_raw\":" + std::to_string(f.date_raw) +
      ",\"played_character_id\":" + std::to_string(f.played_character_id) +
      ",\"owning_thread_id\":" + std::to_string(f.owning_thread_id) +
      ",\"stamp_date_raw\":" + std::to_string(f.stamp_date_raw) +
      ",\"stamp_paused\":" + Boolean(f.stamp_paused) +
      ",\"mailbox_before_accepted\":" + Boolean(f.mailbox_before_accepted) +
      ",\"mailbox_after_accepted\":" + Boolean(f.mailbox_after_accepted) + "}";
  return "{\"schema\":\"religion-creation-price-source-12004-v1\","
      "\"game_version\":\"1.20.0.4\",\"executable_sha256\":" +
      Quote(kReligionPriceSourceExecutableSha25612004) +
      ",\"capture_scope\":" + Quote(f.actual_application_query ?
          "actual_application_query" : "owned_memory_fixture") +
      ",\"source_kind\":\"readonly_source_projection\","
      "\"actual_original_consumed_values\":false,\"source_ready\":" + Boolean(packet.source_ready) +
      ",\"reason\":" + Quote(packet.reason) + ",\"frame\":" + frame +
      ",\"editing_owned_current_rite\":" + Boolean(packet.editing_owned_current_rite) +
      ",\"before\":" + Inputs(packet.before) +
      ",\"after\":" + (packet.after ? Inputs(*packet.after) : "null") +
      ",\"copied_spans_still_current\":" + Boolean(packet.copied_spans_still_current) +
      ",\"input_mappings_still_current\":" + Boolean(packet.input_mappings_still_current) +
      ",\"copied_read_count\":" + std::to_string(packet.copied_read_count) +
      ",\"copied_bytes\":" + std::to_string(packet.copied_bytes) +
      ",\"source_model\":" + Model(packet.source_model) +
      ",\"final_piety_price_raw_q64\":" + Number(packet.final_piety_price_raw_q64) + "}";
}
} // namespace xar::ck3_12004::religion_price_source

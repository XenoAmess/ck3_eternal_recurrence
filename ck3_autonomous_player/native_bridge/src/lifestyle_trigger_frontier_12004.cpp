#include "xar_bridge/lifestyle_trigger_frontier_12004.hpp"

#include <limits>
#include <initializer_list>
#include <string_view>

namespace xar::ck3_12004 {
namespace {
bool Bounded(const LifestyleTriggerFrontierInputs12004 &in,
             std::optional<std::uintptr_t> address, std::size_t width) noexcept {
  if (!in.module_image_size || *in.module_image_size == 0 || !address ||
      *address < in.read_frame.module_base) return false;
  const auto rva = *address - in.read_frame.module_base;
  return rva < *in.module_image_size &&
      width <= static_cast<std::size_t>(*in.module_image_size) - rva;
}
bool InputBound(const LifestyleTriggerFrontierInputs12004 &in) noexcept {
  return SourceReadFrameReady12004(in.read_frame) && in.read_frame.query_sequence != 0 &&
      !in.target_key.empty() && in.command_identity != 0 && in.selected_perk_identity != 0 &&
      in.selected_perk_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 0x80 &&
      in.receiver_identity && *in.receiver_identity == in.selected_perk_identity + 0x80 &&
      Bounded(in, in.vtable_identity, 0xD0);
}
void ClearValue(LifestyleTriggerLaneSource12004 &lane) noexcept {
  lane.source_value_ready = false;
  lane.returned_raw_u8.reset(); lane.returned_raw_u16.reset();
  lane.returned_qword0.reset(); lane.returned_qword1.reset();
  lane.result_source = "unavailable";
}
bool EventReady(const LifestyleTriggerNaturalEvent12004 &event) noexcept {
  return event.clock_identity != 0 && event.sequence != 0 &&
      event.thread_id && *event.thread_id != 0;
}
bool Ordered(const LifestyleTriggerNaturalEvent12004 &a,
             const LifestyleTriggerNaturalEvent12004 &b) noexcept {
  return EventReady(a) && EventReady(b) && a.clock_identity == b.clock_identity &&
      a.thread_id == b.thread_id && a.sequence < b.sequence;
}
bool NaturalMatch(const LifestyleTriggerFrontierInputs12004 &in,
                  const LifestyleTriggerLaneSource12004 &lane) noexcept {
  if (!lane.natural_witness || !lane.target.target_identity) return false;
  const auto &w = *lane.natural_witness;
  return w.read_frame == in.read_frame && w.selected_perk_identity == in.selected_perk_identity &&
      in.receiver_identity && w.receiver_identity == *in.receiver_identity &&
      w.target_identity == *lane.target.target_identity && w.call_rva == lane.call_rva &&
      w.return_rva == lane.return_rva && w.original_matching_call_count == 1 &&
      w.original_call_observed && w.original_return_observed &&
      Ordered(w.query_cursor, w.call_event) && Ordered(w.call_event, w.return_event) &&
      w.returned_raw_u8 == lane.returned_raw_u8 && w.returned_raw_u16 == lane.returned_raw_u16 &&
      w.returned_qword0 == lane.returned_qword0 && w.returned_qword1 == lane.returned_qword1;
}
bool PureMatch(const LifestyleTriggerLaneSource12004 &lane) noexcept {
  if (!lane.closed_target_proof || !lane.target.target_rva) return false;
  const auto &p = *lane.closed_target_proof;
  return p.complete_pure_readonly_body && p.target_rva == *lane.target.target_rva &&
      p.exact_source_sha256.size() == 64 && !p.producer_key.empty();
}
void ValidateLane(const LifestyleTriggerFrontierInputs12004 &in,
                  LifestyleTriggerLaneSource12004 &lane,
                  const LifestyleTriggerTargetCopy12004 &expected,
                  const char *name, std::uintptr_t call, std::uintptr_t ret,
                  unsigned width) noexcept {
  lane.lane = name; lane.call_rva = call; lane.return_rva = ret;
  const bool target_matches = lane.target.target_identity == expected.target_identity &&
      lane.target.target_rva == expected.target_rva &&
      lane.target.slot_identity == expected.slot_identity;
  lane.target = expected;
  lane.raw_target_ready = lane.raw_target_ready && target_matches && InputBound(in) &&
      expected.copied && Bounded(in, expected.target_identity, 1) &&
      expected.target_rva && *expected.target_rva == *expected.target_identity - in.read_frame.module_base;
  const bool correct_width = width == 1
      ? lane.returned_raw_u8.has_value() && !lane.returned_raw_u16 && !lane.returned_qword0 && !lane.returned_qword1
      : width == 2
      ? lane.returned_raw_u16.has_value() && !lane.returned_raw_u8 && !lane.returned_qword0 && !lane.returned_qword1
      : lane.returned_qword0.has_value() && lane.returned_qword1.has_value() &&
          !lane.returned_raw_u8 && !lane.returned_raw_u16;
  const bool qualified_basis = lane.result_source == "closed_pure_target_source"
      ? PureMatch(lane)
      : lane.result_source == "natural_original_once" && NaturalMatch(in, lane);
  if (!lane.source_value_ready || !lane.raw_target_ready || !correct_width || !qualified_basis) {
    ClearValue(lane);
    if (lane.unavailable_reason.empty())
      lane.unavailable_reason = "lifestyle_trigger_lane_output_source_unavailable";
  }
}
LifestyleTriggerTargetCopy12004 DescriptorTarget(const LifestyleTriggerFrontierInputs12004 &in) {
  LifestyleTriggerTargetCopy12004 out{};
  if (!in.descriptor_provider) {
    out.unavailable_reason = "lifestyle_descriptor_source_kind_association_unavailable";
    return out;
  }
  const auto &p = *in.descriptor_provider;
  if (p.frame != in.read_frame || !in.source_context_root_word ||
      p.caller_copied_root_kind_raw_u16 != in.source_context_root_word ||
      !p.selected_descriptor_identity ||
      *p.selected_descriptor_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x10) {
    out.unavailable_reason = "lifestyle_descriptor_same_query_selection_unavailable";
    return out;
  }
  out.slot_identity = *p.selected_descriptor_identity + 0x10;
  out.target_identity = p.descriptor_validator_pointer10;
  out.copied = p.descriptor_validator_pointer_copied;
  if (Bounded(in, out.target_identity, 1))
    out.target_rva = *out.target_identity - in.read_frame.module_base;
  out.unavailable_reason = p.unavailable_reason;
  return out;
}

void String(std::string &out, std::string_view value) {
  static constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const char raw : value) {
    const auto c = static_cast<unsigned char>(raw);
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  out += '"';
}
void Key(std::string &out, std::string_view key, bool &first) {
  if (!first) out += ','; first = false; String(out, key); out += ':';
}
void Value(std::string &out, bool value) { out += value ? "true" : "false"; }
template<class T> void Number(std::string &out, T value) { out += std::to_string(value); }
template<class T> void OptionalNumber(std::string &out, const std::optional<T> &value) {
  if (value) Number(out, *value); else out += "null";
}
void OptionalBool(std::string &out, const std::optional<bool> &value) {
  if (value) Value(out, *value); else out += "null";
}
void Frame(std::string &out, const SourceReadFrame12004 &f) {
  out += '{'; bool first = true;
  Key(out,"executable_sha256",first); String(out,f.executable_sha256);
  Key(out,"module_base",first); Number(out,f.module_base);
  Key(out,"frame_identity",first);
  if (f.frame_identity != 0) Number(out,f.frame_identity); else out += "null";
  Key(out,"snapshot_identity",first); String(out,f.snapshot_identity);
  Key(out,"native_revision",first); Number(out,f.native_revision);
  Key(out,"query_sequence",first);
  if (f.query_sequence != 0) Number(out,f.query_sequence); else out += "null";
  Key(out,"proof_epoch",first); Number(out,f.proof_epoch);
  Key(out,"date_raw",first); OptionalNumber(out,f.date_raw);
  Key(out,"caller_domain",first); String(out,f.caller_domain);
  Key(out,"caller_snapshot_confirmed",first); Value(out,f.caller_snapshot_confirmed);
  out += '}';
}
void Target(std::string &out, const LifestyleTriggerTargetCopy12004 &t) {
  out += '{'; bool first = true;
  Key(out,"slot_identity",first); OptionalNumber(out,t.slot_identity);
  Key(out,"target_identity",first); OptionalNumber(out,t.target_identity);
  Key(out,"target_rva",first); OptionalNumber(out,t.target_rva);
  Key(out,"copied",first); Value(out,t.copied);
  Key(out,"unavailable_reason",first); String(out,t.unavailable_reason);
  out += '}';
}
void Event(std::string &out, const LifestyleTriggerNaturalEvent12004 &e) {
  out += '{'; bool first = true;
  Key(out,"clock_identity",first); Number(out,e.clock_identity);
  Key(out,"sequence",first); Number(out,e.sequence);
  Key(out,"thread_id",first); OptionalNumber(out,e.thread_id);
  out += '}';
}
void Witness(std::string &out, const std::optional<LifestyleTriggerNaturalWitness12004> &w) {
  if (!w) { out += "null"; return; }
  out += '{'; bool first = true;
  Key(out,"read_frame",first); Frame(out,w->read_frame);
  Key(out,"query_cursor",first); Event(out,w->query_cursor);
  Key(out,"call_event",first); Event(out,w->call_event);
  Key(out,"return_event",first); Event(out,w->return_event);
  Key(out,"call_rva",first); Number(out,w->call_rva);
  Key(out,"return_rva",first); Number(out,w->return_rva);
  Key(out,"selected_perk_identity",first); Number(out,w->selected_perk_identity);
  Key(out,"receiver_identity",first); Number(out,w->receiver_identity);
  Key(out,"target_identity",first); Number(out,w->target_identity);
  Key(out,"original_rcx",first); Number(out,w->original_rcx);
  Key(out,"original_rdx",first); Number(out,w->original_rdx);
  Key(out,"original_root_word",first); OptionalNumber(out,w->original_root_word);
  Key(out,"original_full_id_payload",first); OptionalNumber(out,w->original_full_id_payload);
  Key(out,"returned_raw_u8",first); OptionalNumber(out,w->returned_raw_u8);
  Key(out,"returned_raw_u16",first); OptionalNumber(out,w->returned_raw_u16);
  Key(out,"returned_qword0",first); OptionalNumber(out,w->returned_qword0);
  Key(out,"returned_qword1",first); OptionalNumber(out,w->returned_qword1);
  Key(out,"original_matching_call_count",first); Number(out,w->original_matching_call_count);
  Key(out,"original_call_observed",first); Value(out,w->original_call_observed);
  Key(out,"original_return_observed",first); Value(out,w->original_return_observed);
  out += '}';
}
void Proof(std::string &out, const std::optional<LifestyleTriggerClosedTargetProof12004> &p) {
  if (!p) { out += "null"; return; }
  out += '{'; bool first = true;
  Key(out,"target_rva",first); Number(out,p->target_rva);
  Key(out,"exact_source_sha256",first); String(out,p->exact_source_sha256);
  Key(out,"producer_key",first); String(out,p->producer_key);
  Key(out,"complete_pure_readonly_body",first); Value(out,p->complete_pure_readonly_body);
  out += '}';
}
void Lane(std::string &out, const LifestyleTriggerLaneSource12004 &l) {
  out += '{'; bool first = true;
  Key(out,"lane",first); String(out,l.lane);
  Key(out,"call_rva",first); Number(out,l.call_rva);
  Key(out,"return_rva",first); Number(out,l.return_rva);
  Key(out,"target",first); Target(out,l.target);
  Key(out,"raw_target_ready",first); Value(out,l.raw_target_ready);
  Key(out,"source_value_ready",first); Value(out,l.source_value_ready);
  Key(out,"returned_raw_u8",first); OptionalNumber(out,l.returned_raw_u8);
  Key(out,"returned_raw_u16",first); OptionalNumber(out,l.returned_raw_u16);
  Key(out,"returned_qword0",first); OptionalNumber(out,l.returned_qword0);
  Key(out,"returned_qword1",first); OptionalNumber(out,l.returned_qword1);
  Key(out,"result_source",first); String(out,l.result_source);
  Key(out,"closed_target_proof",first); Proof(out,l.closed_target_proof);
  Key(out,"natural_witness",first); Witness(out,l.natural_witness);
  Key(out,"unavailable_reason",first); String(out,l.unavailable_reason);
  out += '}';
}
void Descriptor(std::string &out, const std::optional<TriggerScopeTableProviderRaw3795A6012004> &p) {
  if (!p) { out += "null"; return; }
  out += '{'; bool first = true;
  Key(out,"read_frame",first); Frame(out,p->frame);
  Key(out,"caller_root_kind_raw_u16",first); OptionalNumber(out,p->caller_copied_root_kind_raw_u16);
  Key(out,"table_identity",first); OptionalNumber(out,p->source_return_table_identity);
  Key(out,"initialization_guard_raw_i32",first); OptionalNumber(out,p->initialization_guard_raw_i32);
  Key(out,"table_data_identity",first); OptionalNumber(out,p->table_data_identity);
  Key(out,"capacity_raw_i32",first); OptionalNumber(out,p->capacity_raw_i32);
  Key(out,"count_raw_i32",first); OptionalNumber(out,p->count_raw_i32);
  Key(out,"selected_source_fallback",first); OptionalBool(out,p->selected_source_fallback);
  Key(out,"selected_descriptor_identity",first); OptionalNumber(out,p->selected_descriptor_identity);
  Key(out,"descriptor_validator_pointer10",first); OptionalNumber(out,p->descriptor_validator_pointer10);
  Key(out,"descriptor_selection_inputs_copied",first); Value(out,p->descriptor_selection_inputs_copied);
  Key(out,"descriptor_validator_pointer_copied",first); Value(out,p->descriptor_validator_pointer_copied);
  Key(out,"initializer_semantics_source_closed",first); Value(out,p->initializer_semantics_source_closed);
  Key(out,"native_provider_return_observed",first); Value(out,p->native_provider_return_observed);
  Key(out,"unavailable_reason",first); String(out,p->unavailable_reason);
  out += '}';
}
} // namespace

LifestyleTriggerFrontierPacket12004 BuildLifestylePerkTriggerFrontier12004(
    const SourceLeafReadOnlyAccess12004 &access,
    const LifestyleTriggerFrontierInputs12004 &in) noexcept {
  LifestyleTriggerFrontierPacket12004 out{};
  try {
    out.inputs = in;
    out.copied_input_binding_ready = InputBound(in);
    out.descriptor_al = ReadLifestyleDescriptorFrontier12004(access,in);
    out.root_kind_ax = ReadLifestyleRootKindFrontier12004(access,in);
    out.root_mask_qwords = ReadLifestyleRootMaskFrontier12004(access,in);
    out.final_c8_al = ReadLifestyleFinalC8Frontier12004(access,in);
    ValidateLane(in,out.descriptor_al,DescriptorTarget(in),"descriptor_al",0x372E0AE,0x372E0B0,1);
    ValidateLane(in,out.root_kind_ax,in.slot58,"root_kind_ax",0x372B4D3,0x372B4D6,2);
    ValidateLane(in,out.root_mask_qwords,in.slot60,"root_mask_qwords",0x372B4EE,0x372B4F1,16);
    ValidateLane(in,out.final_c8_al,in.slotc8,"final_c8_al",0x372E34D,0x372E353,1);
  } catch (...) {
    out.copied_input_binding_ready = false;
    out.inputs.unavailable_reason = "lifestyle_trigger_frontier_assembly_unavailable";
    ClearValue(out.descriptor_al); ClearValue(out.root_kind_ax);
    ClearValue(out.root_mask_qwords); ClearValue(out.final_c8_al);
  }
  return out;
}

void FinalizeLifestylePerkTriggerFrontier12004(
    LifestyleTriggerFrontierPacket12004 &p, bool actual_mailbox_accepted) noexcept {
  if (actual_mailbox_accepted && p.inputs.caller_before_after_confirmed &&
      p.inputs.repeated_raw_match && InputBound(p.inputs)) return;
  p.copied_input_binding_ready = false;
  p.inputs.read_frame.caller_snapshot_confirmed = false;
  for (auto *lane : {&p.descriptor_al,&p.root_kind_ax,&p.root_mask_qwords,&p.final_c8_al}) {
    lane->raw_target_ready = false;
    ClearValue(*lane);
    lane->unavailable_reason = "lifestyle_trigger_frontier_current_query_binding_unconfirmed";
  }
}

std::string SerializeLifestylePerkTriggerFrontier12004(
    const std::optional<LifestyleTriggerFrontierPacket12004> &packet) {
  if (!packet) return "null";
  const auto &p = *packet; const auto &in = p.inputs;
  std::string out; out += '{'; bool first = true;
  Key(out,"schema",first); String(out,kLifestyleTriggerFrontierSchema12004);
  Key(out,"read_only",first); Value(out,true);
  Key(out,"copied_input_binding_ready",first); Value(out,p.copied_input_binding_ready);
  Key(out,"inputs",first); out += '{'; bool input_first = true;
  Key(out,"read_frame",input_first); Frame(out,in.read_frame);
  Key(out,"module_image_size",input_first); OptionalNumber(out,in.module_image_size);
  Key(out,"module_time_date_stamp",input_first); OptionalNumber(out,in.module_time_date_stamp);
  Key(out,"public_revision",input_first); Number(out,in.public_revision);
  Key(out,"mailbox_before_accepted",input_first); OptionalBool(out,in.mailbox_before_accepted);
  Key(out,"mailbox_after_accepted",input_first); OptionalBool(out,in.mailbox_after_accepted);
  Key(out,"target_key",input_first); String(out,in.target_key);
  Key(out,"capture_scope",input_first); String(out,in.capture_scope);
  Key(out,"command_identity",input_first); Number(out,in.command_identity);
  Key(out,"selected_perk_identity",input_first); Number(out,in.selected_perk_identity);
  Key(out,"requested_full_character_id",input_first); Number(out,in.requested_full_character_id);
  Key(out,"selected_character_identity",input_first); OptionalNumber(out,in.selected_character_identity);
  Key(out,"selected_character_full_id",input_first); OptionalNumber(out,in.selected_character_full_id);
  Key(out,"receiver_identity",input_first); OptionalNumber(out,in.receiver_identity);
  Key(out,"vtable_identity",input_first); OptionalNumber(out,in.vtable_identity);
  Key(out,"vtable_rva",input_first); OptionalNumber(out,in.vtable_rva);
  Key(out,"slots",input_first); out += '{'; bool slot_first = true;
  Key(out,"slot58",slot_first); Target(out,in.slot58);
  Key(out,"slot60",slot_first); Target(out,in.slot60);
  Key(out,"slotc8",slot_first); Target(out,in.slotc8); out += '}';
  Key(out,"source_context_root_word",input_first); OptionalNumber(out,in.source_context_root_word);
  Key(out,"source_context_full_id_payload",input_first); OptionalNumber(out,in.source_context_full_id_payload);
  Key(out,"context_is_source_projection",input_first); Value(out,in.context_is_source_projection);
  Key(out,"descriptor_provider",input_first); Descriptor(out,in.descriptor_provider);
  Key(out,"caller_before_after_confirmed",input_first); Value(out,in.caller_before_after_confirmed);
  Key(out,"repeated_raw_match",input_first); Value(out,in.repeated_raw_match);
  Key(out,"native_before",input_first); OptionalBool(out,in.native_before);
  Key(out,"native_after",input_first); OptionalBool(out,in.native_after);
  Key(out,"unavailable_reason",input_first); String(out,in.unavailable_reason); out += '}';
  Key(out,"lanes",first); out += '{'; bool lane_first = true;
  Key(out,"descriptor_al",lane_first); Lane(out,p.descriptor_al);
  Key(out,"root_kind_ax",lane_first); Lane(out,p.root_kind_ax);
  Key(out,"root_mask_qwords",lane_first); Lane(out,p.root_mask_qwords);
  Key(out,"final_c8_al",lane_first); Lane(out,p.final_c8_al); out += "}}";
  return out;
}
} // namespace xar::ck3_12004

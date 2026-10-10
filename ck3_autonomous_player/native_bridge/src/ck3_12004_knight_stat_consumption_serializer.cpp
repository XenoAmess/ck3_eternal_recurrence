#include "xar_bridge/knight_stat_consumption_12004.hpp"

#include <ostream>
#include <sstream>
#include <string_view>

namespace xar::ck3_12004 {
namespace {

void String(std::ostream &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
    else if (c < 0x20) out << "\\u00" << hex[c >> 4] << hex[c & 15];
    else out << static_cast<char>(c);
  }
  out << '"';
}

void Reason(std::ostream &out, std::string_view value) {
  if (value.empty()) out << "null";
  else String(out, value);
}

template <typename Value>
void Number(std::ostream &out, const std::optional<Value> &value) {
  if (value) out << +*value;
  else out << "null";
}

template <typename Value>
void Raw64(std::ostream &out, Value value) { out << '"' << value << '"'; }
template <typename Value>
void Raw64(std::ostream &out, const std::optional<Value> &value) {
  if (value) Raw64(out, *value);
  else out << "null";
}

void Pointer(std::ostream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}
void Pointer(std::ostream &out, const std::optional<std::uintptr_t> &value) {
  if (value) Pointer(out, *value);
  else out << "null";
}

void Boolean(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}

void Pc(std::ostream &out, const PersonFollowing2922680Pc &pc) {
  out << "{\"ready\":" << (pc.ready ? "true" : "false") << ",\"reason\":";
  Reason(out, pc.reason);
  out << ",\"admitted\":"; Boolean(out, pc.admitted);
  out << ",\"identity\":"; Pointer(out, pc.identity);
  out << ",\"count_i32\":"; Number(out, pc.count_i32);
  out << ",\"weight_q100000\":"; Raw64(out, pc.weight_q100000);
  out << ",\"properties\":";
  if (!pc.properties) out << "null";
  else {
    out << "{\"keys_u16\":";
    if (!pc.properties->keys_u16) out << "null";
    else {
      out << '[';
      for (std::size_t index = 0; index < pc.properties->keys_u16->size(); ++index) {
        if (index != 0) out << ',';
        out << (*pc.properties->keys_u16)[index];
      }
      out << ']';
    }
    out << ",\"values_q64\":";
    if (!pc.properties->values_q64) out << "null";
    else {
      out << '[';
      for (std::size_t index = 0; index < pc.properties->values_q64->size(); ++index) {
        if (index != 0) out << ',';
        Raw64(out, (*pc.properties->values_q64)[index]);
      }
      out << ']';
    }
    out << '}';
  }
  out << '}';
}

void PreparationStageLineage(std::ostream &out,
                             const EntrySelectedReceiverStage12004 &stage) {
  out << "{\"schema\":"; String(out, kEntrySelectedReceiverStageSchema12004);
  out << ",\"property_key\":"; out << +stage.property_key;
  out << ",\"consumed_return_rva\":"; Raw64(out, stage.consumed_return_rva);
  out << ",\"exact_consumed_callsite\":"; out << (stage.exact_consumed_callsite ? "true" : "false");
  out << ",\"exact_capture_build\":"; out << (stage.exact_capture_build ? "true" : "false");
  out << ",\"observation_stage\":"; String(out, stage.observation_stage);
  out << ",\"preparation_stage\":"; String(out, stage.preparation_stage);
  out << ",\"linked_character_id\":"; Number(out, stage.linked_character_id);
  out << ",\"linked_character_identity\":"; Pointer(out, stage.linked_character_identity);
  out << ",\"selected_character_id\":"; Number(out, stage.selected_character_id);
  out << ",\"selected_character_identity\":"; Pointer(out, stage.selected_character_identity);
  out << ",\"getter_context_identity\":"; Pointer(out, stage.getter_context_identity);
  out << ",\"preparation_capture_observed\":"; out << (stage.preparation_capture_observed ? "true" : "false");
  out << ",\"preparation_capture_complete\":"; out << (stage.preparation_capture_complete ? "true" : "false");
  out << ",\"preparation_raw_counts_ready\":"; out << (stage.preparation_raw_counts_ready ? "true" : "false");
  out << ",\"preparation_stage_observed_mask\":"; out << +stage.preparation_stage_observed_mask;
  out << ",\"preparation_capture_sequence\":"; Raw64(out, stage.preparation_capture_sequence);
  out << ",\"preparation_source_return_rva\":"; Raw64(out, stage.preparation_source_return_rva);
  out << ",\"preparation_capture_thread_id\":"; Number(out, stage.preparation_capture_thread_id);
  out << ",\"preparation_completion_thread_id\":"; Number(out, stage.preparation_completion_thread_id);
  out << ",\"consumption_thread_id\":"; out << +stage.consumption_thread_id;
  out << ",\"preparation_character_identity\":"; Pointer(out, stage.preparation_character_identity);
  out << ",\"preparation_model_identity\":"; Pointer(out, stage.preparation_model_identity);
  out << ",\"preparation_context_identity\":"; Pointer(out, stage.preparation_context_identity);
  out << ",\"preparation_owner_character_identity\":"; Pointer(out, stage.preparation_owner_character_identity);
  out << ",\"preparation_owner_character_id\":"; Number(out, stage.preparation_owner_character_id);
  out << ",\"capture_sequence_matches_record\":"; Boolean(out, stage.capture_sequence_matches_record);
  out << ",\"exact_preparation_source_return\":"; Boolean(out, stage.exact_preparation_source_return);
  out << ",\"selected_matches_capture_identity\":"; Boolean(out, stage.selected_matches_capture_identity);
  out << ",\"selected_matches_capture_id\":"; Boolean(out, stage.selected_matches_capture_id);
  out << ",\"selected_matches_model_owner_identity\":"; Boolean(out, stage.selected_matches_model_owner_identity);
  out << ",\"selected_matches_model_owner_id\":"; Boolean(out, stage.selected_matches_model_owner_id);
  out << ",\"getter_matches_capture_context\":"; Boolean(out, stage.getter_matches_capture_context);
  out << ",\"getter_matches_preparation_model_inline\":"; Boolean(out, stage.getter_matches_preparation_model_inline);
  out << ",\"completion_on_consumption_thread\":"; Boolean(out, stage.completion_on_consumption_thread);
  out << ",\"completed_post_pc_matches_consumed\":"; Boolean(out, stage.completed_post_pc_matches_consumed);
  out << ",\"completed_preparation_lineage_proven\":"; out << (stage.completed_preparation_lineage_proven ? "true" : "false");
  out << ",\"reason\":"; Reason(out, stage.reason);
  out << '}';
}

void NaturalEvent(std::ostream &out, const KnightNaturalLineageEvent12004 &event) {
  out << "{\"clock_identity\":"; Pointer(out, event.clock_identity);
  out << ",\"sequence\":"; Raw64(out, event.sequence);
  out << ",\"thread_id\":"; Number(out, event.thread_id);
  out << '}';
}

void InstalledTransferLineage(std::ostream &out,
                              const KnightInstalledTransferLineage12004 &lineage) {
  out << "{\"schema\":"; String(out, kKnightInstalledTransferLineageSchema12004);
  out << ",\"observation_stage\":\"actual_consumed_getter_return\"";
  out << ",\"getter_begin_event\":"; NaturalEvent(out, lineage.getter_begin_event);
  out << ",\"getter_completed_event\":"; NaturalEvent(out, lineage.getter_completed_event);
  if (lineage.capture_at_consumption)
    out << ",\"capture_at_consumption\":" << *lineage.capture_at_consumption;
  out << ",\"transfer_completed_before_getter\":";
  Boolean(out, lineage.transfer_completed_before_getter);
  out << ",\"selected_matches_transfer_owner\":";
  Boolean(out, lineage.selected_matches_transfer_owner);
  out << ",\"getter_matches_installed_context\":";
  Boolean(out, lineage.getter_matches_installed_context);
  out << ",\"installed_identity_associated\":"
      << (lineage.installed_identity_associated ? "true" : "false");
  out << ",\"reason\":"; Reason(out, lineage.reason);
  out << '}';
}

void Context(std::ostream &out, const KnightConsumedContext12004 &context) {
  out << "{\"property_key\":" << context.property_key << ",\"caller_return_rva\":";
  Raw64(out, context.caller_return_rva);
  out << ",\"selected_character_id\":"; Number(out, context.selected_character_id);
  out << ",\"selected_character_identity\":"; Pointer(out, context.selected_character_identity);
  out << ",\"context_identity\":"; Pointer(out, context.context_identity);
  out << ",\"operand_raw\":"; Raw64(out, context.operand_raw);
  out << ",\"consumed_pc\":"; Pc(out, context.consumed_pc);
  out << ",\"preparation_capture_sequence\":"; Raw64(out, context.preparation_capture_sequence);
  out << ",\"preparation_model_identity\":"; Pointer(out, context.preparation_model_identity);
  out << ",\"preparation_context_identity\":"; Pointer(out, context.preparation_context_identity);
  out << ",\"preparation_owner_character_id\":"; Number(out, context.preparation_owner_character_id);
  out << ",\"context_matches_preparation\":"; Boolean(out, context.context_matches_preparation);
  out << ",\"owner_matches_preparation\":"; Boolean(out, context.owner_matches_preparation);
  out << ",\"pc_matches_preparation_post\":"; Boolean(out, context.pc_matches_preparation_post);
  out << ",\"reason\":"; Reason(out, context.reason);
  if (context.preparation_stage_lineage) {
    out << ",\"preparation_stage_lineage\":";
    PreparationStageLineage(out, *context.preparation_stage_lineage);
  }
  if (context.preparation_capture_at_consumption) {
    out << ",\"preparation_capture_at_consumption\":"
        << SerializePersonSixStageCapture12004(*context.preparation_capture_at_consumption);
  }
  if (context.installed_transfer_lineage) {
    out << ",\"installed_transfer_lineage\":";
    InstalledTransferLineage(out, *context.installed_transfer_lineage);
  }
  out << '}';
}

void Output(std::ostream &out, const KnightConsumedOutput12004 &output) {
  out << "{\"ready\":" << (output.ready ? "true" : "false") << ",\"max_size\":";
  Number(out, output.max_size);
  out << ",\"siege_value_raw\":"; Raw64(out, output.siege_value_raw);
  out << ",\"damage_raw\":"; Raw64(out, output.damage_raw);
  out << ",\"toughness_raw\":"; Raw64(out, output.toughness_raw);
  out << ",\"pursuit_raw\":"; Raw64(out, output.pursuit_raw);
  out << ",\"screen_raw\":"; Raw64(out, output.screen_raw);
  out << ",\"reason\":"; Reason(out, output.reason);
  out << '}';
}

void PhysicalEntryWriteback(
    std::ostream &out, const KnightStatPhysicalEntryWriteback12004 &writeback) {
  out << "{\"writer_sequence\":"; Raw64(out, writeback.writer_sequence);
  out << ",\"entry_identity\":"; Pointer(out, writeback.entry_identity);
  out << ",\"province_identity\":"; Pointer(out, writeback.province_identity);
  out << ",\"regiment_id\":"; Number(out, writeback.regiment_id);
  out << ",\"province_id\":"; Number(out, writeback.province_id);
  out << ",\"original_return_value\":"; Raw64(out, writeback.original_return_value);
  out << ",\"entry_cache\":"; Output(out, writeback.entry_cache);
  out << ",\"output_cache_identity_matches_entry\":"
      << (writeback.output_cache_identity_matches_entry ? "true" : "false");
  out << ",\"wrapper_output_comparison_ready\":"
      << (writeback.wrapper_output_comparison_ready ? "true" : "false");
  out << ",\"wrapper_output_field_matches\":[";
  for (std::size_t index = 0; index < writeback.wrapper_output_field_matches.size(); ++index) {
    if (index != 0) out << ',';
    Boolean(out, writeback.wrapper_output_field_matches[index]);
  }
  out << "],\"wrapper_output_matches_entry_cache\":";
  Boolean(out, writeback.wrapper_output_matches_entry_cache);
  out << ",\"regiment_member_at_query\":"; Boolean(out, writeback.regiment_member_at_query);
  out << ",\"reason\":"; Reason(out, writeback.reason);
  out << '}';
}

void Event(std::ostream &out, const KnightStatConsumptionEvent12004 &event) {
  out << "{\"sequence\":"; Raw64(out, event.sequence);
  out << ",\"thread_id\":" << event.thread_id << ",\"observed_date_raw\":";
  Number(out, event.observed_date_raw);
  out << ",\"wrapper_caller_return_rva\":"; Raw64(out, event.wrapper_caller_return_rva);
  out << ",\"origin\":"; String(out, event.origin);
  out << ",\"regiment_id\":"; Number(out, event.regiment_id);
  out << ",\"target_province_id\":"; Number(out, event.target_province_id);
  out << ",\"linked_character_id\":"; Number(out, event.linked_character_id);
  out << ",\"linked_character_identity\":"; Pointer(out, event.linked_character_identity);
  out << ",\"linked_prowess_points\":"; Number(out, event.linked_prowess_points);
  out << ",\"loaded_damage_multiplier\":"; Number(out, event.loaded_damage_multiplier);
  out << ",\"loaded_toughness_multiplier\":"; Number(out, event.loaded_toughness_multiplier);
  out << ",\"output_cache_identity\":"; Pointer(out, event.output_cache_identity);
  out << ",\"native_return_identity\":"; Pointer(out, event.native_return_identity);
  out << ",\"contexts\":[";
  for (std::size_t index = 0; index < event.contexts.size(); ++index) {
    if (index != 0) out << ',';
    Context(out, event.contexts[index]);
  }
  out << "],\"observed_output\":"; Output(out, event.observed_output);
  out << ",\"entry_association_proven\":" << (event.entry_association_proven ? "true" : "false");
  out << ",\"capture_reason\":"; Reason(out, event.capture_reason);
  if (event.physical_entry_writeback) {
    out << ",\"physical_entry_writeback\":";
    PhysicalEntryWriteback(out, *event.physical_entry_writeback);
  }
  out << '}';
}

} // namespace

std::string SerializeKnightStatConsumptionQuery12004(
    const KnightStatConsumptionQuery12004 &query) {
  std::ostringstream out;
  out << "{\"schema\":"; String(out, kKnightStatConsumptionSchema12004);
  out << ",\"build_version\":"; String(out, query.build_version);
  out << ",\"executable_sha256\":"; String(out, query.executable_sha256);
  out << ",\"configured\":" << (query.configured ? "true" : "false");
  out << ",\"observer_installed\":" << (query.observer_installed ? "true" : "false");
  out << ",\"oldest_available_sequence\":"; Raw64(out, query.oldest_available_sequence);
  out << ",\"latest_sequence\":"; Raw64(out, query.latest_sequence);
  out << ",\"overwritten_events\":"; Raw64(out, query.overwritten_events);
  out << ",\"events\":[";
  for (std::size_t index = 0; index < query.events.size(); ++index) {
    if (index != 0) out << ',';
    Event(out, query.events[index]);
  }
  out << "],\"reason\":"; Reason(out, query.reason);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12004

#include "xar_bridge/combat_scoped_transition_chain_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <string>

namespace xar::ck3_11906 {
namespace {

template <typename T> bool Number(std::string &out, T value) {
  std::array<char, 32> text{};
  const auto result = std::to_chars(text.data(), text.data() + text.size(), value);
  if (result.ec != std::errc{}) return false;
  out.append(text.data(), result.ptr);
  return true;
}
void Bool(std::string &out, bool value) { out += value ? "true" : "false"; }
void Token(std::string &out, std::uintptr_t value) {
  std::array<char, 32> text{};
  const auto result = std::to_chars(text.data(), text.data() + text.size(), value, 16);
  out += "\"process-local-0x";
  out.append(text.data(), result.ptr);
  out += '"';
}
bool Reject(CombatScopedWireDiagnosticV1 *diagnostic, const char *gate,
            const char *field, std::uint64_t observed, std::uint64_t limit,
            std::size_t bytes) {
  if (diagnostic != nullptr) {
    diagnostic->failure_gate = gate; diagnostic->field = field;
    diagnostic->observed = observed; diagnostic->limit = limit;
    diagnostic->output_bytes = bytes;
  }
  return false;
}
bool Key(std::string &out, const CombatScopedStableKeyV1 &key,
         CombatScopedWireDiagnosticV1 *diagnostic, const char *field) {
  if (key.size >= key.bytes.size())
    return Reject(diagnostic,"stable_key_size",field,key.size,key.bytes.size(),out.size());
  out += '"';
  for (std::uint32_t i = 0; i < key.size; ++i) {
    const auto c = key.bytes[i];
    if (c <= 0x20 || c == '"' || c == '\\') {
      if (diagnostic) diagnostic->byte_index=static_cast<std::int32_t>(i);
      return Reject(diagnostic,"stable_key_byte",field,static_cast<unsigned char>(c),0,out.size());
    }
    out += c;
  }
  out += '"';
  return true;
}

const char *Name(CombatScopedChainBoundaryV1 boundary) {
  switch (boundary) {
  case CombatScopedChainBoundaryV1::arm_paused: return "arm_paused";
  case CombatScopedChainBoundaryV1::phase_before: return "phase_before";
  case CombatScopedChainBoundaryV1::phase_after: return "phase_after";
  case CombatScopedChainBoundaryV1::effect_enter: return "effect_enter";
  case CombatScopedChainBoundaryV1::effect_return: return "effect_return";
  case CombatScopedChainBoundaryV1::selector_enter: return "selector_enter";
  case CombatScopedChainBoundaryV1::selector_return: return "selector_return";
  case CombatScopedChainBoundaryV1::death_request_enter: return "death_request_enter";
  case CombatScopedChainBoundaryV1::death_request_return: return "death_request_return";
  case CombatScopedChainBoundaryV1::death_enqueue_enter: return "death_enqueue_enter";
  case CombatScopedChainBoundaryV1::death_enqueue_return: return "death_enqueue_return";
  case CombatScopedChainBoundaryV1::death_commit_enter: return "death_commit_enter";
  case CombatScopedChainBoundaryV1::death_commit_return: return "death_commit_return";
  case CombatScopedChainBoundaryV1::casualty_enter: return "casualty_enter";
  case CombatScopedChainBoundaryV1::casualty_return: return "casualty_return";
  case CombatScopedChainBoundaryV1::next_paused: return "next_paused";
  case CombatScopedChainBoundaryV1::filter_enter: return "filter_enter";
  case CombatScopedChainBoundaryV1::materializer_enter: return "materializer_enter";
  case CombatScopedChainBoundaryV1::materializer_return: return "materializer_return";
  case CombatScopedChainBoundaryV1::predicate_enter: return "predicate_enter";
  case CombatScopedChainBoundaryV1::predicate_return: return "predicate_return";
  case CombatScopedChainBoundaryV1::filter_return: return "filter_return";
  case CombatScopedChainBoundaryV1::list_write_enter: return "list_write_enter";
  case CombatScopedChainBoundaryV1::list_write_return: return "list_write_return";
  }
  return "invalid";
}

bool Character(std::string &out, const CombatScopedCharacterV1 &row,
               CombatScopedWireDiagnosticV1 *diagnostic) {
  if (row.trait_count > row.trait_ids.size())
    return Reject(diagnostic,"count_bound","character.trait_count",row.trait_count,row.trait_ids.size(),out.size());
  out += "{\"character_id\":"; Number(out, row.character_id);
  out += ",\"observed_character_id\":"; Number(out, row.observed_character_id);
  out += ",\"identity_matches\":"; Bool(out, row.identity_matches);
  out += ",\"martial\":"; Number(out, row.martial);
  out += ",\"learning\":"; Number(out, row.learning);
  out += ",\"prowess\":"; Number(out, row.prowess);
  out += ",\"prestige_read\":"; Bool(out, row.prestige_read);
  out += ",\"prestige_currency_raw\":"; Number(out, row.prestige_currency_raw);
  out += ",\"prestige_experience_raw\":"; Number(out, row.prestige_experience_raw);
  out += ",\"regiment_link_token\":"; Token(out, row.regiment_link);
  out += ",\"current_regiment_id\":"; Number(out, row.current_regiment_id);
  out += ",\"current_regiment_identity_matches\":"; Bool(out, row.current_regiment_identity_matches);
  out += ",\"current_regiment_back_reference_matches\":"; Bool(out, row.current_regiment_back_reference_matches);
  out += ",\"death_marker_present\":"; Bool(out, row.death_marker_present);
  out += ",\"death_details_read\":"; Bool(out, row.death_details_read);
  out += ",\"death_date_raw\":"; Number(out, row.death_date_raw);
  out += ",\"death_reason_token\":"; Token(out, row.death_reason);
  out += ",\"death_reason_key\":"; if (!Key(out, row.death_reason_key,diagnostic,"character.death_reason_key")) return false;
  out += ",\"death_killer_character_id\":"; Number(out, row.death_killer_character_id);
  out += ",\"death_artifact_id\":"; Number(out, row.death_artifact_id);
  out += ",\"traits_read\":"; Bool(out, row.traits_read);
  out += ",\"trait_ids\":[";
  for (std::uint32_t i = 0; i < row.trait_count; ++i) {
    if (i) out += ',';
    Number(out, row.trait_ids[i]);
  }
  if(row.trait_track_raw_count>row.trait_track_raw_values.size())
    return Reject(diagnostic,"count_bound","character.trait_track_raw_count",row.trait_track_raw_count,row.trait_track_raw_values.size(),out.size());
  if(row.kill_count>row.kill_character_ids.size())
    return Reject(diagnostic,"count_bound","character.kill_count",row.kill_count,row.kill_character_ids.size(),out.size());
  out += "],\"trait_tracks_read\":";Bool(out,row.trait_tracks_read);
  out += ",\"trait_track_raw_values\":[";
  for(std::uint32_t i=0;i<row.trait_track_raw_count;++i){if(i)out+=',';Number(out,row.trait_track_raw_values[i]);}
  out += "],\"kills_read\":";Bool(out,row.kills_read);
  out += ",\"kill_character_ids\":[";
  for(std::uint32_t i=0;i<row.kill_count;++i){if(i)out+=',';Number(out,row.kill_character_ids[i]);}
  out += "]}";
  return true;
}

bool Record(std::string &out, const CombatScopedChainRecordV1 &row,
            const CombatScopedChainV1 &chain, CombatScopedWireDiagnosticV1 *diagnostic) {
  out += "{\"sequence\":"; Number(out, row.sequence);
  out += ",\"invocation\":"; Number(out, row.invocation);
  out += ",\"parent_invocation\":"; Number(out, row.parent_invocation);
  out += ",\"boundary\":\""; out += Name(row.boundary); out += '"';
  out += ",\"failure_flags\":"; Number(out, row.failure_flags);
  out += ",\"thread_id\":"; Number(out, row.thread_id);
  out += ",\"native_date_raw\":"; Number(out, row.native_date_raw);
  out += ",\"combat_id\":"; Number(out, row.combat_id);
  out += ",\"phase_day\":"; Number(out, row.phase_day);
  out += ",\"side_index\":"; Number(out, row.side_index);
  out += ",\"native_event_load_index\":"; Number(out, row.native_event_load_index);
  out += ",\"node_identity_token\":"; Token(out, row.node_identity);
  out += ",\"node_vtable_rva\":"; Number(out, row.node_vtable_rva);
  out += ",\"node_hash\":"; Number(out, row.node_hash);
  out += ",\"depth\":"; Number(out, row.depth);
  out += ",\"caller_return_token\":"; Token(out, row.caller_return_address);
  out += ",\"casualty_damage_raw\":"; Number(out, row.casualty_damage_raw);
  out += ",\"selected_candidate_index\":"; Number(out, row.selected_candidate_index);
  if (row.selector_candidate_count > row.selector_candidates.size())
    return Reject(diagnostic,"count_bound","selector_candidate_count",row.selector_candidate_count,row.selector_candidates.size(),out.size());
  out += ",\"selector_candidates\":[";
  for (std::uint32_t i = 0; i < row.selector_candidate_count; ++i) {
    if (i) out += ',';
    const auto &candidate = row.selector_candidates[i];
    out += "{\"scope_word0\":"; Number(out, candidate.scope_word0);
    out += ",\"scope_word1_token\":"; Token(out, candidate.scope_word1);
    out += ",\"character_id\":"; Number(out, candidate.character_id);
    out += ",\"character_full_identity_matches\":"; Bool(out, candidate.character_full_identity_matches);
    out += '}';
  }
  out += ']';
  out += ",\"execution_context_token\":";Token(out,row.execution_context);
  out += ",\"native_root_scope_token\":";Token(out,row.native_root_scope);
  out += ",\"native_scope_words\":[";Number(out,row.native_scope_words[0]);out+=',';Number(out,row.native_scope_words[1]);out+=']';
  out += ",\"selector_vector_token\":";Token(out,row.selector_vector);
  out += ",\"selector_data_token\":";Token(out,row.selector_data);
  out += ",\"selector_list_context_token\":";Token(out,row.selector_list_context);
  out += ",\"selector_prefix_count\":";Number(out,row.selector_prefix_count);
  out += ",\"selector_current_index\":";Number(out,row.selector_current_index);
  out += ",\"selector_source_side_index\":";Number(out,row.selector_source_side_index);
  out += ",\"selector_source_combat_identity_matches\":";Bool(out,row.selector_source_combat_identity_matches);
  out += ",\"source_predicate_token\":";Token(out,row.source_predicate);
  out += ",\"shared_predicate_token\":";Token(out,row.shared_predicate);
  out += ",\"source_predicate_count\":";Number(out,row.source_predicate_count);
  out += ",\"shared_predicate_count\":";Number(out,row.shared_predicate_count);
  out += ",\"predicate_token\":";Token(out,row.predicate);
  out += ",\"predicate_role\":";Number(out,row.predicate_role);
  out += ",\"original_predicate_boolean_read\":";Bool(out,row.original_predicate_boolean_read);
  out += ",\"original_predicate_boolean\":";Bool(out,row.original_predicate_boolean);
  out += ",\"original_return_bits\":";Number(out,row.original_return_bits);
  out += ",\"variable_owner_token\":";Token(out,row.variable_owner);
  out += ",\"variable_owner_from_original_getter\":";Bool(out,row.variable_owner_from_original_getter);
  out += ",\"variable_owner_scope_token\":";Token(out,row.variable_owner_scope);
  out += ",\"variable_owner_scope_words\":[";Number(out,row.variable_owner_scope_words[0]);out+=',';Number(out,row.variable_owner_scope_words[1]);out+=']';
  out += ",\"requested_character_full_identity_matches\":";Bool(out,row.requested_character_full_identity_matches);
  out += ",\"variable_key_id\":";Number(out,row.variable_key_id);
  out += ",\"variable_key\":";if(!Key(out,row.variable_key,diagnostic,"variable_key"))return false;
  out += ",\"requested_expiry\":";Number(out,row.requested_expiry);
  out += ",\"requested_scope_words\":[";Number(out,row.requested_scope_words[0]);out+=',';Number(out,row.requested_scope_words[1]);out+=']';
  out += ",\"variable_list_read\":";Bool(out,row.variable_list_read);
  out += ",\"variable_list_present\":";Bool(out,row.variable_list_present);
  out += ",\"list_elapsed_offset\":";Number(out,row.list_elapsed_offset);
  if(row.variable_list_count>row.variable_list_values.size())
    return Reject(diagnostic,"count_bound","variable_list_count",row.variable_list_count,row.variable_list_values.size(),out.size());
  out += ",\"variable_list_values\":[";
  for(std::uint32_t i=0;i<row.variable_list_count;++i){if(i)out+=',';out+="{\"scope_word0\":";Number(out,row.variable_list_values[i][0]);out+=",\"scope_word1\":";Number(out,row.variable_list_values[i][1]);out+=",\"expiration_raw\":";Number(out,row.variable_list_expirations[i]);out+='}';}
  out += ']';
  out += ",\"characters\":[";
  if (diagnostic) diagnostic->character_index=0;
  if (!Character(out, row.characters[0],diagnostic)) return false;
  out += ',';
  if (diagnostic) diagnostic->character_index=1;
  if (!Character(out, row.characters[1],diagnostic)) return false;
  if (diagnostic) diagnostic->character_index=-1;
  out += "]";
  out += ",\"death_victim_id\":"; Number(out, row.death_victim_id);
  out += ",\"death_killer_id\":"; Number(out, row.death_killer_id);
  out += ",\"requested_death_artifact_token\":";Token(out,row.requested_death_artifact);
  out += ",\"requested_artifact_id_read\":";Bool(out,row.requested_artifact_id_read);
  out += ",\"requested_death_artifact_id\":";Number(out,row.requested_death_artifact_id);
  out += ",\"requested_death_date_raw\":"; Number(out, row.requested_death_date_raw);
  out += ",\"requested_death_reason_token\":"; Token(out, row.requested_death_reason);
  out += ",\"death_queue_count\":"; Number(out, row.death_queue_count);
  out += ",\"death_queue_token\":"; Token(out, row.death_queue);
  out += ",\"combat_entries_read\":"; Bool(out, row.combat_entries_read);
  out += ",\"battle_events_read\":";Bool(out,row.battle_events_read);
  out += ",\"battle_event_snapshot_index\":";Number(out,row.battle_event_snapshot_index);
  out += ",\"battle_events\":[";
  if(row.battle_event_snapshot_index>=static_cast<std::int32_t>(chain.battle_event_snapshots.size()))
    return Reject(diagnostic,"snapshot_index_bound","battle_event_snapshot_index",row.battle_event_snapshot_index,chain.battle_event_snapshots.size(),out.size());
  if(row.battle_event_snapshot_index>=0){const auto &snapshot=chain.battle_event_snapshots[row.battle_event_snapshot_index];if(snapshot.count>snapshot.rows.size())
    return Reject(diagnostic,"count_bound","battle_event_snapshot.count",snapshot.count,snapshot.rows.size(),out.size());
    for(std::uint32_t i=0;i<snapshot.count;++i){if(i)out+=',';const auto &v=snapshot.rows[i];
      if (diagnostic) diagnostic->element_index=static_cast<std::int32_t>(i);
      out+="{\"left_character_id\":";Number(out,v.left_character_id);out+=",\"right_character_id\":";Number(out,v.right_character_id);out+=",\"type_raw\":";Number(out,v.type_raw);
      out+=",\"side_index\":";Number(out,v.side_index);out+=",\"target_right\":";Bool(out,v.target_right);out+=",\"key\":";
      CombatScopedStableKeyV1 key{};key.size=v.stable_key_size;if(key.size>=key.bytes.size())
        return Reject(diagnostic,"stable_key_size","battle_event.key",key.size,key.bytes.size(),out.size());
      std::copy(v.stable_key.begin(),v.stable_key.begin()+key.size,key.bytes.begin());if(!Key(out,key,diagnostic,"battle_event.key"))return false;out+='}';
    }
  }
  out += ']';
  out += ",\"entry_snapshot_index\":"; Number(out, row.entry_snapshot_index);
  out += ",\"scoped_regiment_in_side\":[";
  Bool(out, row.scoped_regiment_in_side[0]); out += ',';
  Bool(out, row.scoped_regiment_in_side[1]); out += ']';
  out += ",\"sides\":[";
  if (row.entry_snapshot_index >= static_cast<std::int32_t>(chain.entry_snapshots.size()))
    return Reject(diagnostic,"snapshot_index_bound","entry_snapshot_index",row.entry_snapshot_index,chain.entry_snapshots.size(),out.size());
  for (std::uint32_t side = 0; side < 2 && row.entry_snapshot_index >= 0; ++side) {
    const auto &snapshot = chain.entry_snapshots[static_cast<std::size_t>(row.entry_snapshot_index)];
    if (diagnostic) diagnostic->side_index=static_cast<std::int32_t>(side);
    if (snapshot.entry_count[side] > snapshot.entries[side].size())
      return Reject(diagnostic,"count_bound","entry_snapshot.entry_count",snapshot.entry_count[side],snapshot.entries[side].size(),out.size());
    if (snapshot.owner_hard_count[side] > snapshot.owner_hard[side].size())
      return Reject(diagnostic,"count_bound","entry_snapshot.owner_hard_count",snapshot.owner_hard_count[side],snapshot.owner_hard[side].size(),out.size());
    if (side) out += ',';
    out += "{\"side_index\":"; Number(out, side);
    out += ",\"cached_fighting_total_raw\":"; Number(out, row.side_cache_raw[side]);
    out += ",\"cached_first_bucket_raw\":"; Number(out, row.side_first_bucket_cache_raw[side]);
    out += ",\"entries\":[";
    for (std::uint32_t i = 0; i < snapshot.entry_count[side]; ++i) {
      if (i) out += ',';
      const auto &entry = snapshot.entries[side][i];
      out += "{\"regiment_id\":"; Number(out, entry.regiment_id);
      out += ",\"army_id\":"; Number(out, entry.army_id);
      out += ",\"character_id\":"; Number(out, entry.character_id);
      out += ",\"bucket\":"; Number(out, entry.bucket);
      out += ",\"starting_raw\":"; Number(out, entry.starting_raw);
      out += ",\"current_raw\":"; Number(out, entry.current_raw);
      out += ",\"soft_raw\":"; Number(out, entry.soft_raw);
      out += ",\"effective_damage_raw\":"; Number(out, entry.effective_damage_raw);
      out += ",\"effective_toughness_raw\":"; Number(out, entry.effective_toughness_raw);
      out += '}';
    }
    out += "],\"owner_hard\":[";
    for (std::uint32_t i = 0; i < snapshot.owner_hard_count[side]; ++i) {
      if (i) out += ',';
      const auto &owner = snapshot.owner_hard[side][i];
      out += "{\"character_id\":"; Number(out, owner.character_id);
      out += ",\"hard_casualties_raw\":"; Number(out, owner.hard_casualties_raw);
      out += '}';
    }
    out += "]}";
  }
  out += "]}";
  if (diagnostic) diagnostic->side_index=-1;
  return true;
}

} // namespace

std::string SerializeCombatScopedChainV1(const CombatScopedChainV1 &chain,
                                       CombatScopedWireDiagnosticV1 *diagnostic) {
  if (diagnostic) *diagnostic={};
  // A truncated capture is preserved as RED evidence; never report its list
  // as complete. Individual failed reads also remain visible in the journal.
  const auto count = std::min<std::uint32_t>(chain.count.load(),
      static_cast<std::uint32_t>(chain.records.size()));
  std::string out;
  out.reserve(16 * 1024);
  out += "{\"schema_version\":1,\"scope\":\"declared_two_character_combat_death_write_set\"";
  out += ",\"character_ids\":["; Number(out, chain.character_ids[0]); out += ',';
  Number(out, chain.character_ids[1]); out += ']';
  out += ",\"event_load_index\":"; Number(out, chain.event_load_index);
  out += ",\"combat_id\":"; Number(out, chain.plan != nullptr ? chain.plan->combat_id : -1);
  out += ",\"managed_daily_sequence_token\":";
  Number(out, chain.plan != nullptr ? chain.plan->managed_daily_sequence_token : 0);
  if (chain.trait_definition_count > chain.trait_definitions.size()) {
    Reject(diagnostic,"count_bound","trait_definition_count",chain.trait_definition_count,chain.trait_definitions.size(),out.size());return {};
  }
  out += ",\"prearmed_trait_definitions\":[";
  for (std::uint32_t i = 0; i < chain.trait_definition_count; ++i) {
    if (diagnostic) diagnostic->element_index=static_cast<std::int32_t>(i);
    if (i) out += ',';
    out += "{\"trait_id\":"; Number(out, chain.trait_definitions[i].trait_id);
    out += ",\"key\":"; if (!Key(out, chain.trait_definitions[i].key,diagnostic,"trait_definition.key")) return {};
    out += '}';
  }
  out += ']';
  out += ",\"failure_flags\":"; Number(out, chain.failure_flags.load());
  out += ",\"truncated\":"; Bool(out, chain.count.load() > chain.records.size());
  out += ",\"global_mutable_bundle_complete\":false";
  out += ",\"required_write_domains\":[\"skills\",\"trait_set\",\"trait_tracks\","
         "\"death_date_reason_killer_artifact\",\"prestige_currency_and_accumulated\","
         "\"regiment_link_and_membership\",\"entry_current_soft_stats_and_owner_hard\","
         "\"battle_event_ledger\",\"slain_side_knights\",\"killer_kills\","
         "\"signature_weapon\",\"house_relation\",\"accolade_feedback_branch\"]";
  out += ",\"domain_coverage\":{"
         "\"ordered_effect_invocations\":\"direct_enter_return_including_no_rng_nodes\","
         "\"martial_learning_prowess_trait_set_death_prestige_link\":\"typed_each_journal_boundary\","
         "\"skills\":{\"typed_each_journal_boundary\":[\"martial\",\"learning\",\"prowess\"],"
         "\"all_six_skills\":\"requires_same_process_native_save_before_after_full_delta\"},"
         "\"entry_current_soft_stats_owner_hard\":\"typed_phase_casualty_commit_return_next_paused\","
         "\"battle_event_ledger\":\"same_managed_seven_phase_trace_and_actual_battle_event_effect_before_after_ledger\","
         "\"trait_track_raw_values_killer_kills\":\"typed_each_journal_boundary_full_vector\","
         "\"selector_materializer_filter\":\"original_enter_return_vectors_original_predicate_AL_no_re_evaluation\","
         "\"slain_side_knights\":\"actual_event_context_key_value_expiry_original_list_writer_before_after\","
         "\"signature_weapon_house_original_predicate\":\"independent_same_process_scoped_variable_monitor\","
         "\"no_write_branches_and_all_saved_state\":\"requires_exact_script_writer_inventory_and_same_process_native_save_full_delta\","
         "\"unpublished_intraday_values\":[\"individual_house_start_trigger_subconditions\"]}";
  // Completeness is evaluated against the exact stock event's declared write
  // set and the original seven-phase / outgoing pair in a separate verifier.
  // Emitting a journal alone is never evidence that all those domains closed.
  out += ",\"live_scoped_write_set_verified\":false,\"records\":[";
  for (std::uint32_t i = 0; i < count; ++i) {
    if (diagnostic) {
      diagnostic->record_index=static_cast<std::int32_t>(i);
      diagnostic->sequence=chain.records[i].sequence;diagnostic->invocation=chain.records[i].invocation;
      diagnostic->boundary=static_cast<std::uint32_t>(chain.records[i].boundary);
      diagnostic->character_index=-1;diagnostic->side_index=-1;
      diagnostic->element_index=-1;diagnostic->byte_index=-1;
    }
    if (i) out += ',';
    if (!Record(out, chain.records[i], chain,diagnostic)) return {};
    if (out.size() > 16 * 1024 * 1024) {
      Reject(diagnostic,"scoped_wire_cap","output_bytes",out.size(),16*1024*1024,out.size());return {};
    }
  }
  out += "]}";
  if (diagnostic) diagnostic->output_bytes=out.size();
  return out;
}

} // namespace xar::ck3_11906

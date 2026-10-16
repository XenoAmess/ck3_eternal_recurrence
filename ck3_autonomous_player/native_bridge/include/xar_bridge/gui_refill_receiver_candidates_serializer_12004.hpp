#pragma once
#include "xar_bridge/gui_refill_receiver_candidates_12004.hpp"
namespace xar::game {
template<class Text> inline void AppendGuiRefillReceiverCandidates12004(
    std::string &s,const GuiRefillReceiverCandidates12004V1 &v,Text text) {
  s+="{\"source\":\"native_gui_type635_definition_candidates_12004\",\"status\":";text(s,v.status);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else text(s,v.unavailable_reason);
  const auto numeric=[&](const char *k,auto n){s+=",\"";s+=k;s+="\":";s+=std::to_string(n);};
  const auto optional=[&](const char *k,const auto &n){s+=",\"";s+=k;s+="\":";s+=n?std::to_string(*n):"null";};
  const auto boolean=[&](const char *k,bool b){s+=",\"";s+=k;s+="\":";s+=b?"true":"false";};
  s+=",\"receiver_type_id\":635,\"current_variable_table_observed\":false,\"native_receiver_selected\":false";
  optional("receiver_variable_index",v.receiver_variable_index);optional("declared_type_id",v.declared_type_id);
  boolean("stable_double_read",v.stable_double_read);s+=",\"entries\":[";
  bool first=true;
  for(const auto &e:v.entries){
    if(!first)s+=',';first=false;s+="{\"ancestor_depth\":"+std::to_string(e.ancestor_depth);
    numeric("entry_type_48",e.entry_type_48);numeric("entry_mode_40",static_cast<int>(e.entry_mode_40));numeric("entry_flag_4c",e.entry_flag_4c);
    boolean("direct_value_present",e.direct_value_present);boolean("provider_present",e.provider_present);
    optional("provider_vtable_rva",e.provider_vtable_rva);optional("provider_slot2_rva",e.provider_slot2_rva);
    optional("direct_owner_full_id",e.direct_owner_full_id);boolean("direct_owner_identity_verified",e.direct_owner_identity_verified);s+='}';
  }
  s+=']';
  if(v.failure_diagnostic){
    const auto &d=*v.failure_diagnostic;s+=",\"failure_diagnostic\":{\"stage\":";text(s,d.stage);
    s+=",\"kind\":";text(s,d.kind);numeric("capture_pass",d.capture_pass);numeric("read_ordinal",d.read_ordinal);
    optional("ancestor_depth",d.ancestor_depth);optional("raw_declaration_count",d.raw_declaration_count);
    optional("raw_index_count",d.raw_index_count);optional("raw_definition_entry_count",d.raw_definition_entry_count);
    const auto maybe_bool=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?(*x?"true":"false"):"null";};
    maybe_bool("context_present",d.context_present);maybe_bool("definition_present",d.definition_present);
    optional("local_definition_active_raw",d.local_definition_active_raw);s+='}';
  }
  s+='}';
}
template<class Text> inline void AppendGuiRefillReceiverFrame12004(
    std::string &s,const GuiRefillReceiverFrame12004V1 &v,Text) {
  s+="{\"native_revision\":"+std::to_string(v.native_revision);
  const auto n=[&](const char *k,auto x){s+=",\"";s+=k;s+="\":";s+=std::to_string(x);};
  n("connection_generation",v.connection_generation);n("pump_epoch",v.pump_epoch);n("ticket_sequence",v.ticket_sequence);
  n("game_pid",v.game_pid);n("thread_id",v.thread_id);n("played_character_full_id",v.played_character_full_id);n("date_raw",v.date_raw);
  s+=",\"owner_thread_verified\":true,\"frame_stable\":true,\"gui_owner_stable\":true}";
}
}

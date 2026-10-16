#pragma once
#include "xar_bridge/gui_refill_receiver_candidates_12004.hpp"
namespace xar::game {
inline void AppendGuiRefillReceiverEntry12004(std::string &s,const GuiRefillReceiverEntry12004V1 &e) {
  const auto n=[&](const char *k,auto x){s+=",\"";s+=k;s+="\":";s+=std::to_string(x);};
  const auto o=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?std::to_string(*x):"null";};
  const auto b=[&](const char *k,bool x){s+=",\"";s+=k;s+="\":";s+=x?"true":"false";};
  s+="{\"ancestor_depth\":"+std::to_string(e.ancestor_depth);
  n("entry_type_48",e.entry_type_48);n("entry_mode_40",static_cast<int>(e.entry_mode_40));n("entry_flag_4c",e.entry_flag_4c);
  b("direct_value_present",e.direct_value_present);b("provider_present",e.provider_present);
  o("provider_vtable_rva",e.provider_vtable_rva);o("provider_slot2_rva",e.provider_slot2_rva);
  o("direct_owner_full_id",e.direct_owner_full_id);b("direct_owner_identity_verified",e.direct_owner_identity_verified);s+='}';
}
template<class Text> inline void AppendGuiRefillReceiverFailure12004(std::string &s,const GuiRefillReceiverFailure12004V1 &d,Text text) {
  const auto n=[&](const char *k,auto x){s+=",\"";s+=k;s+="\":";s+=std::to_string(x);};
  const auto o=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?std::to_string(*x):"null";};
  const auto b=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?(*x?"true":"false"):"null";};
  s+="{\"stage\":";text(s,d.stage);s+=",\"kind\":";text(s,d.kind);
  n("capture_pass",d.capture_pass);n("read_ordinal",d.read_ordinal);o("ancestor_depth",d.ancestor_depth);
  o("raw_declaration_count",d.raw_declaration_count);o("raw_index_count",d.raw_index_count);o("raw_definition_entry_count",d.raw_definition_entry_count);
  b("context_present",d.context_present);b("definition_present",d.definition_present);o("local_definition_active_raw",d.local_definition_active_raw);s+='}';
}
template<class Text> inline void AppendGuiRefillLocalDefinitionEntry12004(std::string &s,const GuiRefillLocalDefinitionEntry12004V1 &v,Text text) {
  s+="{\"source\":\"native_gui_type635_local_definition_entry_only_12004\",\"scope\":\"local_definition_entry_only\",\"status\":";text(s,v.status);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else text(s,v.unavailable_reason);
  s+=",\"receiver_type_id\":635,\"ancestor_depth\":0,\"current_variable_table_observed\":false,\"native_receiver_selected\":false";
  const auto o=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?std::to_string(*x):"null";};
  const auto b=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?(*x?"true":"false"):"null";};
  o("receiver_variable_index",v.receiver_variable_index);o("declared_type_id",v.declared_type_id);
  o("raw_definition_entry_count",v.raw_definition_entry_count);o("local_definition_active_raw",v.local_definition_active_raw);
  b("definition_present",v.definition_present);b("local_entry_present",v.local_entry_present);
  s+=",\"stable_double_read\":";s+=v.stable_double_read?"true":"false";s+=",\"entries\":[";
  bool first=true;for(const auto &e:v.entries){if(!first)s+=',';first=false;AppendGuiRefillReceiverEntry12004(s,e);}s+=']';
  if(v.failure_diagnostic){s+=",\"failure_diagnostic\":";AppendGuiRefillReceiverFailure12004(s,*v.failure_diagnostic,text);}s+='}';
}
template<class Text> inline void AppendGuiRefillDefinitionPrefix12004(std::string &s,const GuiRefillDefinitionPrefix12004V1 &v,Text text) {
  s+="{\"source\":\"native_gui_type635_definition_chain_prefix_depth8_12004\",\"scope\":\"visited_definition_prefix_depth8\",\"status\":";text(s,v.status);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else text(s,v.unavailable_reason);
  s+=",\"receiver_type_id\":635,\"depth_limit\":8,\"walk_complete\":false,\"current_variable_table_observed\":false,\"native_receiver_selected\":false";
  s+=",\"receiver_variable_index\":";s+=v.receiver_variable_index?std::to_string(*v.receiver_variable_index):"null";
  s+=",\"declared_type_id\":";s+=v.declared_type_id?std::to_string(*v.declared_type_id):"null";
  s+=",\"frontier_depth\":";s+=v.stable_double_read?"8":"null";
  s+=",\"frontier_context_present\":";s+=v.stable_double_read?"true":"null";
  s+=",\"stable_double_read\":";s+=v.stable_double_read?"true":"false";s+=",\"rows\":[";
  bool first=true;for(const auto &row:v.rows){
    if(!first)s+=',';first=false;s+="{\"ancestor_depth\":"+std::to_string(row.ancestor_depth);
    s+=",\"definition_present\":";s+=row.definition_present?"true":"false";
    s+=",\"raw_definition_entry_count\":";s+=row.raw_definition_entry_count?std::to_string(*row.raw_definition_entry_count):"null";
    s+=",\"entries\":[";if(!row.entries.empty())AppendGuiRefillReceiverEntry12004(s,row.entries.front());s+=']';
    s+=",\"parent_edge\":";text(s,row.parent_edge);s+=",\"parent_present\":";s+=row.parent_present?"true":"false";s+='}';
  }s+="]}";
}
template<class Text> inline void AppendGuiRefillReceiverCandidates12004(std::string &s,const GuiRefillReceiverCandidates12004V1 &v,Text text) {
  s+="{\"source\":\"native_gui_type635_definition_candidates_12004\",\"status\":";text(s,v.status);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else text(s,v.unavailable_reason);
  s+=",\"receiver_type_id\":635,\"current_variable_table_observed\":false,\"native_receiver_selected\":false";
  const auto o=[&](const char *k,const auto &x){s+=",\"";s+=k;s+="\":";s+=x?std::to_string(*x):"null";};
  o("receiver_variable_index",v.receiver_variable_index);o("declared_type_id",v.declared_type_id);
  s+=",\"stable_double_read\":";s+=v.stable_double_read?"true":"false";s+=",\"entries\":[";
  bool first=true;for(const auto &e:v.entries){if(!first)s+=',';first=false;AppendGuiRefillReceiverEntry12004(s,e);}s+=']';
  if(v.failure_diagnostic){s+=",\"failure_diagnostic\":";AppendGuiRefillReceiverFailure12004(s,*v.failure_diagnostic,text);}
  if(v.local_definition_entry_only){s+=",\"local_definition_entry_only\":";AppendGuiRefillLocalDefinitionEntry12004(s,*v.local_definition_entry_only,text);}
  if(v.definition_chain_prefix_depth8){s+=",\"definition_chain_prefix_depth8\":";AppendGuiRefillDefinitionPrefix12004(s,*v.definition_chain_prefix_depth8,text);}s+='}';
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

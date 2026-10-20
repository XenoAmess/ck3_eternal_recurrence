#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "xar_bridge/ck3_12004.hpp"
namespace xar::ck3_12004::player_inventory_window {
namespace {
std::string Text(std::string_view in) {
  constexpr char hex[]="0123456789abcdef";std::string out="\"";
  for(unsigned char c:in){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
    else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
  return out+'"';
}
const char* Bool(bool v){return v?"true":"false";}
std::string View(const PlayerInventoryOpenPost12004& v) {
  if(!v.actor_id||v.actor_id==0xffffffffU)return {};
  const bool current=v.available&&v.current_admission;
  if(v.available&&(!current||!v.pid||!v.generation||!v.revision||!v.capture_epoch||!v.view||!v.owner||!v.actor||!v.handler||!v.gui_context||!v.gui_lookup_owner))return {};
  std::string out="{\"available\":";out+=Bool(current);
  out+=",\"native_revision\":"+std::to_string(v.revision)+",\"capture_epoch\":"+std::to_string(v.capture_epoch);
  out+=",\"date_raw\":"+std::to_string(v.date_raw)+",\"game_pid\":"+std::to_string(v.pid)+",\"connection_generation\":"+std::to_string(v.generation);
  out+=",\"played_character_id\":"+std::to_string(v.actor_id)+",\"selected_character_id\":";
  out+=(current&&v.subject_id!=0xffffffffU)?std::to_string(v.subject_id):"null";
  const auto field=[&](const char* key,bool value){out+=",\"";out+=key;out+="\":";out+=current?Bool(value):"null";};
  field("window_present",v.view!=0);field("root_present",v.root!=0);
  field("native_visible",v.native_visible);field("effective_visible",v.effective_visible);
  field("current_player_selected",v.subject_id==v.actor_id);
  return out+'}';
}
}
std::string Serialize(const Observation& v) {
  if(v.operation!="query"&&v.operation!="open"&&v.operation!="post")return {};
  const auto current=View(v.current),before=v.has_before?View(v.before):std::string{},after=v.has_after?View(v.after):std::string{};
  if(current.empty()||(v.has_before&&before.empty())||(v.has_after&&after.empty())||
      (!v.available&&v.current.available)||
      (v.available&&(!v.current.available||!v.current.current_admission||!v.code_pins_verified||!v.gui_sources_verified))||
      (v.operation=="post"&&!v.intent_found)||
      (v.desired_window_observed&&(v.operation!="post"||!v.available||!v.intent_found||!v.once_consumed||!v.has_before||!v.has_after||!PlayerInventoryOpenDesiredObserved12004(v.before,v.after))))return {};
  std::string s="{\"schema\":\"ck3_12004_player_inventory_window_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Text(kExecutableSha256);
  const auto boolean=[&](const char*key,bool b){s+=",\"";s+=key;s+="\":";s+=Bool(b);};
  s+=",\"operation\":"+Text(v.operation);boolean("read_only",v.read_only);boolean("available",v.available);
  s+=",\"unavailable_reason\":";s+=v.available?"null":Text(v.unavailable_reason.empty()?"inventory_window_unavailable":v.unavailable_reason);
  boolean("loaded_code_pins_verified",v.code_pins_verified);boolean("loaded_gui_sources_verified",v.gui_sources_verified);
  s+=",\"current\":"+current+",\"intent_sequence\":"+std::to_string(v.intent_found?v.intent_sequence:0);
  boolean("intent_found",v.intent_found);boolean("once_intent_consumed",v.once_consumed);boolean("invoked",v.invoked);
  boolean("call_returned",v.call_returned);boolean("needs_recovery",v.needs_recovery);boolean("desired_window_observed",v.desired_window_observed);
  s+=",\"status\":"+Text(v.status)+",\"before\":"+(v.has_before?before:"null")+",\"after\":"+(v.has_after?after:"null");
  return s+",\"artifact_equipped_observed\":false,\"actor_aggregate_observed\":false,\"personal_net_effect_attributed\":false,\"business_outcome_observed\":false,\"automatic_retry\":false}";
}
}

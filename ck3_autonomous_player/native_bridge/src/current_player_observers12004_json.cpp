#include "current_player_observers12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <type_traits>

namespace xar::ck3_12004::current_player_observers {
namespace {
std::string Text(std::string_view input) {
  std::string out="\"";
  constexpr char hex[]="0123456789abcdef";
  for(unsigned char c:input) {
    if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
    else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }
  return out+'"';
}
const char* Bool(bool v){return v?"true":"false";}
template<class T> std::string Nullable(const std::optional<T>& v) {
  if(!v)return "null";
  if constexpr(std::is_same_v<T,bool>)return Bool(*v);
  else return std::to_string(*v);
}
std::string Identity(std::uint32_t id) {
  return id==0xffffffffU?"null":std::to_string(id);
}
const char* ObjectState(religion::ghw_links_candidate::State v) {
  using S=religion::ghw_links_candidate::State;
  switch(v){case S::unknown:return "unknown";case S::absent:return "absent";case S::present:return "present";}
  return "unknown";
}
}
std::string SerializeArtifactPersonalUse12004(const artifact_personal_use::Observation& v) {
  const bool available=v.available;
  if(v.frame.actor_id==artifact_personal_use::absent || v.artifact_id==artifact_personal_use::absent ||
      v.owned_ids.size()>64 || v.slots.size()>64 || v.item_modifier_definition.size()>128 ||
      v.modifier_description.size()>8192 ||
      (available&&(!v.loaded_source_pins_verified||!v.personally_owned||
       std::count(v.owned_ids.begin(),v.owned_ids.end(),v.artifact_id)!=1))) return {};
  std::string s="{\"schema\":\"ck3_12004_player_artifact_personal_use_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  s+=Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
  s+=",\"available\":";s+=Bool(available);
  s+=",\"unavailable_reason\":";s+=available?"null":Text(v.unavailable_reason.empty()?"personal_use_unavailable":v.unavailable_reason);
  s+=",\"loaded_source_pins_verified\":";s+=Bool(v.loaded_source_pins_verified);
  s+=",\"capture_epoch\":"+std::to_string(v.frame.capture_epoch)+",\"date_raw\":"+std::to_string(v.frame.date_raw);
  s+=",\"played_character_id\":"+std::to_string(v.frame.actor_id)+",\"requested_artifact_id\":"+std::to_string(v.artifact_id);
  s+=",\"owned_ids\":";
  if(!available)s+="null";
  else {s+='[';bool comma=false;for(auto id:v.owned_ids){if(id==artifact_personal_use::absent)return {};if(comma)s+=',';comma=true;s+=std::to_string(id);}s+=']';}
  s+=",\"slots\":";
  if(!available)s+="null";
  else {
    s+='[';bool comma=false;
    for(const auto& row:v.slots) {
      if(row.index>=64||row.key.empty()||row.key.size()>63||
         !std::all_of(row.key.begin(),row.key.end(),[](char c){return(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_';}))return {};
      if(comma)s+=',';comma=true;
      s+="{\"index\":"+std::to_string(row.index)+",\"artifact_id\":"+Identity(row.artifact_id)+
        ",\"key\":"+Text(row.key)+",\"personal\":"+Bool(row.personal)+'}';
    }
    s+=']';
  }
  const auto scalar=[&](const char* key,bool value){s+=",\"";s+=key;s+="\":";s+=available?Bool(value):"null";};
  scalar("personally_owned",v.personally_owned);scalar("inventory_artifact",v.inventory_artifact);scalar("equipped",v.equipped);
  s+=",\"native_equipped_observed\":";s+=Bool(available&&v.native_equipped_observed);
  scalar("inventory_view_available",v.inventory_view_available);scalar("inventory_view_visible",v.inventory_view_visible);
  const auto optional=[&](const char* key,const auto& value){s+=",\"";s+=key;s+="\":";s+=available?Nullable(value):"null";};
  optional("equipped_slot_index",v.equipped_slot_index);optional("effective_slot_index",v.effective_slot_index);
  optional("replacing_artifact_id",v.replacing_artifact_id);optional("can_equip_in_effective_slot",v.can_equip_in_effective_slot);optional("can_unequip",v.can_unequip);
  const bool definition=available&&v.item_modifier_definition_available;
  s+=",\"item_modifier_definition\":{\"available\":";s+=Bool(definition);s+=",\"entries\":";
  if(!definition)s+="null";
  else {s+='[';bool comma=false;for(const auto&row:v.item_modifier_definition){if(comma)s+=',';comma=true;s+="{\"key_raw_u16\":"+std::to_string(row.key_raw_u16)+",\"definition_value_raw_q64\":"+std::to_string(row.definition_value_raw_q64)+'}';}s+=']';}
  const bool description=available&&v.modifier_description_available;
  s+="},\"modifier_description\":{\"available\":";s+=Bool(description);s+=",\"text\":";s+=description?Text(v.modifier_description):"null";
  return s+"},\"modifier_names_bound\":false,\"actor_aggregate_observed\":false,\"personal_net_effect_attributed\":false,\"total_payment_observed\":false,\"action_ready\":false,\"business_outcome_observed\":false,\"read_only\":true}";
}
std::string SerializeGhwPermissions12004(const GhwObservation& v) {
  namespace vars=religion::ghw_variables_candidate;
  namespace links=religion::ghw_links_candidate;
  const bool current=v.available&&v.frame_verified&&v.loaded_source_pins_verified;
  if(v.played_character_id<=0 || (v.available&&(!current||!v.capture_epoch||
      !v.faith_id||!v.religion_id||*v.faith_id==0xffffffffU||*v.religion_id==0xffffffffU)))return {};
  if(current&&(!v.variables.frame_verified||!v.variables.stable_two_pass||
      v.variables.capture_epoch!=v.capture_epoch||v.variables.date_raw!=v.date_raw||
       v.variables.played_character_id!=v.played_character_id||
       v.variables.faith_id!=*v.faith_id||v.variables.religion_id!=*v.religion_id))return {};
  std::string s="{\"schema\":\"ck3_12004_player_ghw_permissions_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  s+=Text(kExecutableSha256);s+=",\"available\":";s+=Bool(current);
  s+=",\"unavailable_reason\":";s+=current?"null":Text(v.unavailable_reason.empty()?"ghw_outer_frame_unavailable":v.unavailable_reason);
  s+=",\"capture_epoch\":"+std::to_string(v.capture_epoch)+",\"date_raw\":"+std::to_string(v.date_raw)+",\"played_character_id\":"+std::to_string(v.played_character_id);
  s+=",\"faith_id\":"+(current?Nullable(v.faith_id):"null")+",\"religion_id\":"+(current?Nullable(v.religion_id):"null");
  s+=",\"loaded_source_pins_verified\":";s+=Bool(v.loaded_source_pins_verified);s+=",\"frame_verified\":";s+=Bool(current);
  const auto &a=v.variables;
  s+=",\"variables\":{\"available_any\":";s+=Bool(current&&a.available_any);
  s+=",\"all_fields_observed\":";s+=Bool(current&&a.all_fields_observed);
  s+=",\"frame_verified\":";s+=Bool(current&&a.frame_verified);s+=",\"stable_two_pass\":";s+=Bool(current&&a.stable_two_pass);
  s+=",\"failure\":"+Text(current?vars::FailureKey(a.failure):"input_not_admitted")+
    ",\"remaining_unit\":"+Text(vars::Observation::remaining_unit)+",\"fields\":[";
  for(std::size_t i=0;i<a.fields.size();++i) {
    if(i)s+=',';const auto &f=a.fields[i];const bool observed=current&&f.read_available;
    const char* scope=vars::kScopes[i]==vars::Scope::religion?"religion":vars::kScopes[i]==vars::Scope::faith?"faith":"global";
    s+="{\"key\":"+Text(vars::kKeys[i])+",\"scope\":"+Text(scope)+",\"read_available\":"+Bool(observed);
    const auto optional=[&](const char* key,const auto& value){s+=",\"";s+=key;s+="\":";s+=observed?Nullable(value):"null";};
    optional("present",f.present);optional("timed",f.timed);optional("expiry_raw",f.expiry_raw);optional("current_counter_raw",f.current_counter_raw);
    optional("remaining_raw",f.remaining_raw);optional("value_kind_raw",f.value_kind_raw);optional("numeric_value_raw",f.numeric_value_raw);
    s+=",\"expiry_date_raw\":null,\"failure\":"+Text(current?vars::FailureKey(f.failure):"input_not_admitted")+'}';
  }
  const auto &b=v.object_links;
  s+=" ]},\"object_links\":{\"available\":";s+=Bool(current&&b.available);s+=",\"stable_two_pass\":";s+=Bool(current&&b.stable_two_pass);
  s+=",\"ghw\":"+Text(current?ObjectState(b.ghw):"unknown")+",\"war\":"+Text(current?ObjectState(b.war):"unknown");
  s+=",\"failure\":"+Text(current?links::FailureKey(b.failure):"input_not_admitted");
  s+=",\"ghw_reference_full_id\":"+(current?Nullable(b.ghw_reference_full_id):"null")+",\"war_reference_full_id\":"+(current?Nullable(b.war_reference_full_id):"null");
  s+=",\"faith_has_offensive_ghw\":"+(current?Nullable(b.faith_has_offensive_ghw):"null")+",\"has_war_started\":"+(current?Nullable(b.has_war_started):"null");
  return s+"},\"launch_permission_inferred\":false,\"raw_pointer_fields_persisted\":false,\"read_only\":true}";
}
std::string SerializeArtifactPersonalAction12004(const ArtifactActionObservation& v) {
  const auto& request=v.request;const auto& result=v.result;
  if(v.played_character_id==artifact_personal_use::absent||request.artifact_id==artifact_personal_use::absent||
      request.expected_slot_index>=64||(v.read_only&&!v.intent_found))return {};
  const auto before=SerializeArtifactPersonalUse12004(result.before);
  const auto after=v.after_attempted?SerializeArtifactPersonalUse12004(v.after):std::string{};
  if(v.after_attempted&&after.empty())return {};
  if(v.desired_inventory_state_observed&&(!v.available||!v.read_only||!v.intent_found||!v.after_attempted||!result.once_intent_consumed||
      !artifact_personal_use::DesiredStateObserved12004(result.before,request,v.after)))return {};
  std::string s="{\"schema\":\"ck3_12004_player_artifact_personal_use_action_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  s+=Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
  const auto boolean=[&](const char* key,bool value){s+=",\"";s+=key;s+="\":";s+=Bool(value);};
  boolean("read_only",v.read_only);boolean("available",v.available);
  s+=",\"unavailable_reason\":";s+=v.available?"null":Text(v.unavailable_reason.empty()?"artifact_action_current_frame_unavailable":v.unavailable_reason);
  s+=",\"played_character_id\":"+std::to_string(v.played_character_id)+",\"artifact_id\":"+std::to_string(request.artifact_id);
  boolean("desired_equipped",request.desired_equipped);
  s+=",\"expected_slot_index\":"+std::to_string(request.expected_slot_index)+",\"expected_replacing_artifact_id\":"+Identity(request.expected_replacing_artifact_id);
  s+=",\"intent_sequence\":"+std::to_string(result.once_intent_consumed?request.request_sequence:0);
  boolean("intent_found",v.intent_found);boolean("invoked",result.invoked);boolean("once_intent_consumed",result.once_intent_consumed);
  boolean("dispatch_call_returned",result.dispatch_call_returned);boolean("needs_recovery",result.needs_recovery);
  boolean("desired_inventory_state_observed",v.desired_inventory_state_observed);
  s+=",\"status\":"+Text(v.read_only?v.post_status:result.status);
  const bool has_before=!before.empty();
  s+=",\"before_native_revision\":"+std::to_string(has_before?result.before.frame.revision:0);
  s+=",\"before_connection_generation\":"+std::to_string(has_before?result.before.frame.connection_generation:0);
  s+=",\"before_game_pid\":"+std::to_string(has_before?result.before.frame.bridge_pid:0);
  s+=",\"after_native_revision\":"+std::to_string(v.after_attempted?v.after.frame.revision:0);
  s+=",\"after_connection_generation\":"+std::to_string(v.after_attempted?v.after.frame.connection_generation:0);
  s+=",\"after_game_pid\":"+std::to_string(v.after_attempted?v.after.frame.bridge_pid:0);
  s+=",\"before\":"+(has_before?before:"null")+",\"after\":"+(v.after_attempted?after:"null");
  return s+",\"business_outcome_observed\":false,\"actor_aggregate_observed\":false,\"personal_net_effect_attributed\":false,\"total_payment_observed\":false,\"automatic_retry\":false}";
}
}

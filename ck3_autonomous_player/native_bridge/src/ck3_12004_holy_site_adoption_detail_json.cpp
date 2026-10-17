#include "xar_bridge/ck3_12004_holy_site_adoption_detail.hpp"
namespace xar::ck3_12004::religion::holy_site {
namespace{
std::string Q(std::string_view s){
 constexpr char hex[]="0123456789abcdef";std::string out="\"";
 for(const unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
  else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
 return out+'"';
}
const char*B(bool v)noexcept{return v?"true":"false";}
std::string R(std::uint32_t v){return v==0xFFFFFFFFU?"null":std::to_string(v);}
std::string PlanningFields(const AdoptionDetailSnapshot&v){
 const bool context=v.available&&v.native_detail_context_verified;
 const bool requirements=context&&v.native_requirements_description_available,cost=context&&v.native_cost_description_available;
 const bool quote=context&&v.native_resource_quote_available,cooldown=context&&v.native_decision_cooldown_observed;
 std::string out=",\"native_detail_context_verified\":"+std::string(B(context));
 out+=",\"native_requirements_description_available\":"+std::string(B(requirements))+",\"native_requirements_description\":"+(requirements?Q(v.native_requirements_description):"null")+
  ",\"native_requirements_description_unavailable_reason\":"+(requirements?"null":Q("native_requirements_description_unavailable"));
 out+=",\"native_cost_description_available\":"+std::string(B(cost))+",\"native_cost_description\":"+(cost?Q(v.native_cost_description):"null")+
  ",\"native_cost_description_unavailable_reason\":"+(cost?"null":Q("native_cost_description_unavailable"));
 out+=",\"native_resource_quote_available\":"+std::string(B(quote))+",\"native_resource_quote\":";
 if(quote){out+="{\"raw_scale\":100000,\"resource_vector_raw\":[";
  for(std::size_t i=0;i<v.native_resource_vector_raw.size();++i){if(i)out+=',';out+=std::to_string(v.native_resource_vector_raw[i]);}
  out+="],\"costs_raw\":{\"gold\":"+std::to_string(v.native_resource_vector_raw[0])+",\"prestige\":"+std::to_string(v.native_resource_vector_raw[1])+
   ",\"piety\":"+std::to_string(v.native_resource_vector_raw[2])+",\"treasury\":"+std::to_string(v.native_resource_vector_raw[6])+"},\"native_affordable\":"+B(v.native_affordable)+"}";
 }else out+="null";
 out+=",\"native_decision_cooldown_observed\":"+std::string(B(cooldown))+",\"native_decision_cooldown\":";
 if(cooldown){out+="{\"decision_key\":\"adopt_holy_site_decision\",\"present\":"+std::string(B(v.native_decision_cooldown_present))+
  ",\"expiry_raw\":"+(v.native_decision_cooldown_present?std::to_string(v.native_decision_expiry_raw):"null")+
  ",\"current_counter_raw\":"+std::to_string(v.native_decision_clock_raw)+",\"active\":"+B(v.native_decision_cooldown_active)+
  ",\"counter_unit\":\"native_decision_clock_counter\",\"calendar_conversion_observed\":false}";
 }else out+="null";
 out+=",\"native_planning_unavailable_reason\":"+(v.available&&!v.native_planning_unavailable_reason.empty()?Q(v.native_planning_unavailable_reason):"null");return out;
}
}
std::string SerializeHolySiteAdoptionDetail12004(const AdoptionDetailSnapshot&v){
 const bool normal=v.available&&v.bypass_requirements_observed&&v.bypass_requirements_raw==0;
 return "{\"schema\":\"ck3_12004_holy_site_adoption_detail_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
 ",\"available\":"+B(v.available)+",\"unavailable_reason\":"+(v.unavailable_reason.empty()?"null":Q(v.unavailable_reason))+
 ",\"capture_epoch\":"+std::to_string(v.capture_epoch)+",\"date_raw\":"+std::to_string(v.date_raw)+",\"played_character_id\":"+std::to_string(v.played_character_id)+
 ",\"requested_holy_site_id\":"+R(v.requested_holy_site_id)+",\"detail_present\":"+(v.available?B(v.detail_present):"null")+
 ",\"root_present\":"+(v.available?B(v.root_present):"null")+",\"decision_key\":"+(v.decision_key.empty()?"null":Q(v.decision_key))+
 ",\"detail_actor_id\":"+R(v.detail_actor_id)+",\"current_actor_id\":"+R(v.current_actor_id)+",\"decision_option_id\":"+(v.available?std::to_string(v.decision_option_id):"null")+
 ",\"selected_index\":"+(v.available?std::to_string(v.selected_index):"null")+",\"candidate_count\":"+(v.available?std::to_string(v.candidate_count):"null")+
 ",\"selected_item_token\":"+(v.available?std::to_string(v.selected_item_token):"null")+
 ",\"parameter_holy_site_id\":"+R(v.parameter_holy_site_id)+",\"selected_holy_site_id\":"+R(v.selected_holy_site_id)+
 ",\"parameter_and_selection_match\":"+(v.available?B(v.parameter_and_selection_match):"null")+
 ",\"native_can_confirm\":"+(v.available?B(v.native_can_confirm):"null")+
 ",\"bypass_requirements_observed\":"+B(v.available&&v.bypass_requirements_observed)+
 ",\"bypass_requirements_raw\":"+(v.available&&v.bypass_requirements_observed?std::to_string(v.bypass_requirements_raw):"null")+
 ",\"normal_requirements_legality_observed\":"+B(normal)+",\"normal_requirements_can_confirm\":"+(normal?B(v.native_can_confirm):"null")+
 ",\"confirm_tooltip_available\":"+B(v.available&&v.confirm_tooltip_available)+
 ",\"confirm_tooltip\":"+(v.available&&v.confirm_tooltip_available?Q(v.confirm_tooltip):"null")+
 ",\"confirm_tooltip_unavailable_reason\":"+(v.available&&v.confirm_tooltip_available?"null":Q("native_confirm_tooltip_unavailable"))+
 PlanningFields(v)+",\"rendered_visibility_observed\":false,"
 "\"action_ready\":false,\"read_only\":true,\"decision_confirm_invoked\":false,\"adoption_completed_observed\":false}";
}
std::string SerializeHolySiteAdoptionDetailCommand12004(const AdoptionDetailSnapshot&v,
 std::string_view request_id,std::uint64_t revision,std::int64_t date){
 return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Q(request_id)+
 ",\"ok\":true,\"result\":{\"step\":"+Q(kAdoptionDetailQueryStep)+",\"accepted\":true,\"status\":"+Q(v.available?"observed":"unavailable")+
 ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
 ",\"domain_key\":\"player_holy_site_adoption_detail_v1\",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-adoption-detail-v1\","
 "\"snapshot_revision\":"+std::to_string(revision)+",\"date_raw\":"+std::to_string(date)+",\"player_holy_site_adoption_detail\":"+SerializeHolySiteAdoptionDetail12004(v)+"}}";
}
}

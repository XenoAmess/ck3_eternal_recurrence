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
 ",\"rendered_visibility_observed\":false,\"native_resource_quote_available\":false,\"native_resource_quote\":null,"
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

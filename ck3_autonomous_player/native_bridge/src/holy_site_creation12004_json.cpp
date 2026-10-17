#include "xar_bridge/holy_site_creation12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
namespace xar::ck3_12004::religion::holy_site_creation {
namespace {
std::string Q(std::string_view s){
 constexpr char h[]="0123456789abcdef";std::string out="\"";
 for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
  else if(c<32){out+="\\u00";out+=h[c>>4];out+=h[c&15];}else out+=static_cast<char>(c);}
 return out+'"';
}
const char*B(bool x){return x?"true":"false";}
std::string R(std::uint32_t x){return x==0xFFFFFFFFU?"null":std::to_string(x);}
std::string Ids(const std::vector<std::uint32_t>&v){std::string s="[";for(auto id:v){if(s.size()>1)s+=',';s+=R(id);}return s+']';}
}
std::string SerializeContext12004(const Snapshot&v){
 const bool models=v.available&&v.models_available,selection=v.available&&v.selection_available;
 const bool enabled=v.available&&v.native_enabled_observed,bypass=v.available&&v.bypass_requirements_observed;
 const bool normal=enabled&&bypass&&v.bypass_requirements_raw==0;
 const bool rarity=v.available&&v.native_rarity_sum_observed,tooltip=v.available&&v.create_tooltip_available;
 const bool quote=v.available&&v.cached_resource_quote_available;
 std::string types="[";
 for(const auto&t:v.available_holy_site_types){
  if(types.size()>1)types+=',';
  types+="{\"type_key\":"+Q(t.type_key)+",\"is_selected\":"+B(t.is_selected)+
   ",\"native_can_pick_observed\":"+B(t.native_can_pick_observed)+
   ",\"native_can_pick\":"+(t.native_can_pick_observed?B(t.native_can_pick):"null")+
   ",\"tooltip_available\":"+B(t.tooltip_available)+",\"tooltip\":"+(t.tooltip_available?Q(t.tooltip):"null")+'}';
 }
 types+=']';
 std::string raw="[";
 for(auto n:v.cached_resource_vector_raw){if(raw.size()>1)raw+=',';raw+=std::to_string(n);}raw+=']';
 return "{\"schema\":\"ck3_12004_player_holy_site_creation_context_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
  ",\"available\":"+B(v.available)+",\"unavailable_reason\":"+(v.unavailable_reason.empty()?"null":Q(v.unavailable_reason))+
  ",\"capture_epoch\":"+std::to_string(v.capture_epoch)+",\"date_raw\":"+std::to_string(v.date_raw)+
  ",\"played_character_id\":"+std::to_string(v.played_character_id)+",\"player_faith_id\":"+R(v.player_faith_id)+
  ",\"window_present\":"+(v.available?B(v.window_present):"null")+",\"root_present\":"+(v.available?B(v.root_present):"null")+
  ",\"window_faith_id\":"+R(v.window_faith_id)+",\"player_faith_matches\":"+(v.available?B(v.player_faith_matches):"null")+
  ",\"models_available\":"+B(models)+",\"models_complete\":"+B(models&&v.models_complete)+
  ",\"available_holy_site_types\":"+(models?types:"null")+
  ",\"potential_barony_title_ids\":"+(models?Ids(v.potential_barony_title_ids):"null")+
  ",\"enshrinable_artifact_ids\":"+(models?Ids(v.enshrinable_artifact_ids):"null")+
  ",\"selection_available\":"+B(selection)+",\"selected_type_key\":"+(selection&&v.selected_type_key?Q(*v.selected_type_key):"null")+
  ",\"selected_barony_title_id\":"+(selection&&v.selected_barony_title_id?R(*v.selected_barony_title_id):"null")+
  ",\"selected_artifact_ids\":"+(selection?Ids(v.selected_artifact_ids):"null")+
  ",\"raw_scale\":100000,\"native_rarity_sum_observed\":"+B(rarity)+
  ",\"native_rarity_sum_raw\":"+(rarity?std::to_string(v.native_rarity_sum_raw):"null")+
  ",\"native_enabled_observed\":"+B(enabled)+",\"native_create_button_enabled\":"+(enabled?B(v.native_create_button_enabled):"null")+
  ",\"bypass_requirements_observed\":"+B(bypass)+",\"bypass_requirements_raw\":"+(bypass?std::to_string(v.bypass_requirements_raw):"null")+
  ",\"normal_requirements_legality_observed\":"+B(normal)+",\"normal_requirements_can_create\":"+(normal?B(v.native_create_button_enabled):"null")+
  ",\"create_tooltip_available\":"+B(tooltip)+",\"create_tooltip\":"+(tooltip?Q(v.create_tooltip):"null")+
  ",\"cached_resource_quote_available\":"+B(quote)+",\"cached_resource_vector_raw\":"+(quote?raw:"null")+
  ",\"cached_quote_freshness_observed\":false,\"native_affordability_observed\":false,\"native_affordable\":null,"
  "\"rendered_visibility_observed\":false,\"read_only\":true,\"action_ready\":false,\"create_invoked\":false}";
}
std::string SerializeCommand12004(const Snapshot&v,std::string_view request,std::uint64_t revision,std::int64_t date){
 return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Q(request)+
  ",\"ok\":true,\"result\":{\"step\":"+Q(kQueryStep)+",\"accepted\":true,\"status\":"+Q(v.available?"observed":"unavailable")+
  ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
  ",\"domain_key\":"+Q(kDomainKey)+",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-creation-context-v1\","
  "\"snapshot_revision\":"+std::to_string(revision)+",\"date_raw\":"+std::to_string(date)+
  ",\"player_holy_site_creation_context\":"+SerializeContext12004(v)+"}}";
}
}

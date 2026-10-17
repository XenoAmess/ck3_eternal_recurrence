#include "xar_bridge/ck3_12004_holy_site_decision_cooldown.hpp"
namespace xar::ck3_12004::religion::holy_site {
namespace {
std::string Q(std::string_view value){
 constexpr char hex[]="0123456789abcdef";std::string out="\"";
 for(const unsigned char c:value){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}
  else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}
 return out+'"';
}
const char*B(bool value)noexcept{return value?"true":"false";}
}
std::string SerializeHolySiteDecisionCooldown12004(const DecisionCooldownSnapshot&v){
 std::string out="{\"schema\":\"ck3_12004_holy_site_decision_cooldown_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
  ",\"available\":"+B(v.available)+",\"unavailable_reason\":"+(v.available?"null":Q(v.unavailable_reason))+
  ",\"capture_epoch\":"+std::to_string(v.capture_epoch)+",\"date_raw\":"+std::to_string(v.date_raw)+",\"played_character_id\":"+std::to_string(v.played_character_id)+
  ",\"action\":"+Q(DecisionActionName(v.action))+",\"decision_key\":"+Q(DecisionKey(v.action))+
  ",\"native_decision_cooldown_observed\":"+B(v.available)+",\"native_decision_cooldown\":";
 if(v.available){out+="{\"decision_key\":"+Q(DecisionKey(v.action))+",\"present\":"+B(v.cooldown.present)+
  ",\"expiry_raw\":"+(v.cooldown.present?std::to_string(v.cooldown.expiry_raw):"null")+
  ",\"current_counter_raw\":"+std::to_string(v.cooldown.current_counter_raw)+",\"active\":"+B(v.cooldown.active)+
  ",\"counter_unit\":\"native_decision_clock_counter\",\"calendar_conversion_observed\":false}";
 }else out+="null";
 return out+",\"detail_open_required\":false,\"read_only\":true,\"action_ready\":false,\"decision_confirm_invoked\":false,\"adoption_completed_observed\":false}";
}
std::string SerializeHolySiteDecisionCooldownCommand12004(const DecisionCooldownSnapshot&v,
 std::string_view request_id,std::uint64_t revision,std::int64_t date){
 return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":"+Q(request_id)+
  ",\"ok\":true,\"result\":{\"step\":"+Q(kDecisionCooldownQueryStep)+",\"accepted\":true,\"status\":"+Q(v.available?"observed":"unavailable")+
  ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.4\",\"executable_sha256\":"+Q(ck3_12004::kExecutableSha256)+
  ",\"domain_key\":\"player_holy_site_decision_cooldown_v1\",\"backend_id\":\"ck3-1.20.0.4-native-player-holy-site-decision-cooldown-v1\",\"snapshot_revision\":"+std::to_string(revision)+
  ",\"date_raw\":"+std::to_string(date)+",\"player_holy_site_decision_cooldown\":"+SerializeHolySiteDecisionCooldown12004(v)+"}}";
}
}

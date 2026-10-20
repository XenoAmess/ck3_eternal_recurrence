#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include <array>

namespace xar::ck3_12004::character_skill_effects {
namespace {
constexpr std::array<std::string_view,6> skills{
    "diplomacy","martial","stewardship","intrigue","learning","prowess"};
void Quote(std::string &out,std::string_view text){
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:text){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}out+='"';
}
template<class T>void Number(std::string &out,const std::optional<T> &v){out+=v?std::to_string(*v):"null";}
} // namespace
std::string Serialize(const Query &q){
  const auto &v=q.observation;
  if(!q.completed||q.frame_changed||!q.failure.empty()||q.invocations!=1||q.expected_revision==0||
      q.executable_sha256!=core::kExeSha||q.skill<0||q.skill>=6||q.character_id==0xFFFFFFFFU||
      v.character_id!=q.character_id||v.requested_skill!=q.skill||
      v.frame.revision!=q.expected_revision||v.frame.date_raw!=q.expected_snapshot.date_raw||
      v.frame.played_character_id!=static_cast<std::uint32_t>(q.expected_snapshot.played_character_id)||
      !v.frame.owner_thread||!v.frame.paused||!v.frame.map_ready||
      q.expected_snapshot.played_character_id<=0||
      (v.callback_provenance!=core::CallbackProvenance::unavailable&&
       v.callback_provenance!=core::CallbackProvenance::exact4_native)||
      !v.read_only||v.gameplay_command_submitted||v.skill_cache_refreshed||v.cache_generation_time_known||
      v.site_attribution_observed||v.selected_site_contribution_raw)return {};
  if(v.available){
    if(!v.two_pass_stable||!v.unavailable_reason.empty()||
        v.callback_provenance!=core::CallbackProvenance::exact4_native||
        !v.rite_id||*v.rite_id==0xFFFFFFFFU||!v.faith_id||*v.faith_id==0xFFFFFFFFU||
        !v.current_skill_points||!v.effective_devotion_level||!v.devotion_total_raw||
        !v.actual_skill_breakdown||v.actual_skill_breakdown->size()>core::kMaxBreakdownBytes)return {};
  }else if(v.two_pass_stable||v.unavailable_reason.empty()||v.rite_id||v.faith_id||
      v.current_skill_points||v.effective_devotion_level||v.devotion_total_raw||v.actual_skill_breakdown)return {};
  std::string out="{\"schema\":\"ck3_12004_character_skill_effects_v1\",\"available\":";
  out+=v.available?"true":"false";out+=",\"unavailable_reason\":";
  if(v.available)out+="null";else Quote(out,v.unavailable_reason);
  out+=",\"read_only\":true,\"snapshot_revision\":"+std::to_string(q.expected_revision);
  out+=",\"date_raw\":"+std::to_string(q.expected_snapshot.date_raw)+",\"played_character_id\":"+std::to_string(q.expected_snapshot.played_character_id);
  out+=",\"character_id\":"+std::to_string(q.character_id)+",\"requested_skill\":";Quote(out,skills[static_cast<std::size_t>(q.skill)]);
  out+=",\"requested_skill_enum\":"+std::to_string(q.skill)+",\"rite_id\":";Number(out,v.rite_id);
  out+=",\"faith_id\":";Number(out,v.faith_id);out+=",\"current_skill_points\":";
  if(!v.current_skill_points)out+="null";
  else{out+='{';for(std::size_t i=0;i<skills.size();++i){if(i)out+=',';Quote(out,skills[i]);out+=':';out+=std::to_string(v.current_skill_points->at(i));}out+='}';}
  out+=",\"effective_devotion_level\":";Number(out,v.effective_devotion_level);
  out+=",\"devotion_total_raw\":";Number(out,v.devotion_total_raw);
  out+=",\"actual_skill_breakdown\":";if(v.actual_skill_breakdown)Quote(out,*v.actual_skill_breakdown);else out+="null";
  out+=",\"raw_scale\":100000,\"skill_scale\":1,\"two_pass_stable\":";out+=v.two_pass_stable?"true":"false";
  out+=",\"callback_provenance\":";Quote(out,v.available&&v.callback_provenance==core::CallbackProvenance::exact4_native?"exact4_native":"unavailable");
  out+=",\"skill_cache_refreshed\":false,\"cache_generation_time_known\":false,\"site_attribution_observed\":false,\"selected_site_contribution_raw\":null,";
  out+="\"gameplay_command_submitted\":false,\"raw_pointer_fields_persisted\":false,\"script_cache_rng_effects\":\"unknown\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":";
  Quote(out,core::kExeSha);out+='}';return out;
}
} // namespace xar::ck3_12004::character_skill_effects

#include "character_knight_effectiveness12004_json.inc"

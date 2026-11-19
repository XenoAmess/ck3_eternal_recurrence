#include "xar_bridge/ck3_1210_opening_frame56.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/opening_provenance56.hpp"
#include <limits>
namespace xar::ck3_1210 {namespace {
void Quote(std::string&s,std::string_view v){
 s+='"';constexpr char hex[]="0123456789abcdef";
 for(const unsigned char c:v){if(c=='"' || c==0x5c){s+=static_cast<char>(0x5c);s+=static_cast<char>(c);}
 else if(c<0x20){s+=static_cast<char>(0x5c);s+="u00";s+=hex[c>>4];s+=hex[c&15];}else s+=static_cast<char>(c);}s+='"';
}
bool Valid(const OpeningMailboxContext56&q) noexcept {
 if(!q.completed || !q.observation.available || q.observation.kind!=q.kind || !q.expected_native_revision ||
 (!q.application_main_observed && !q.offline_fixture) || (q.application_main_observed && q.offline_fixture) ||
 !q.ticket_sequence || !q.pump_epoch || !q.thread_id)return false;
 const auto &p=q.observation.frame;
 if(!p.clock.paused || !p.map_ready || !p.has_played_character || !p.played_character_alive || p.played_character_id==-1 ||
 p.clock.date_raw!=q.expected_full.date_raw || p.played_character_id!=q.expected_full.played_character_id)return false;
 if(q.kind==OpeningReadKind56::government_scope){
  if(!q.observation.government || q.observation.lifestyle)return false;const auto &g=*q.observation.government;
  return !g.key.empty() && g.native_flag_count>=0 && g.native_flag_count<=4096 && g.flags.size()==static_cast<std::size_t>(g.native_flag_count);
 }
 if(!q.observation.lifestyle || q.observation.government)return false;const auto &l=*q.observation.lifestyle;
 return !l.focus_key.empty() && !l.lifestyle_key.empty() && l.xp_total_raw>=0 && l.xp_within_level_raw>=0 &&
 l.xp_per_level>0 && l.xp_within_level_raw<static_cast<std::int64_t>(l.xp_per_level)*100000 &&
 l.unspent_perk_points>=0 && l.used_perk_points>=0;
}
}
std::string SerializeOpeningReadonlyData56(const OpeningMailboxContext56&q){
 const bool gov=q.kind==OpeningReadKind56::government_scope,available=Valid(q);
 std::string s="{\"schema\":";Quote(s,gov?kOpeningScopeSchema56:kOpeningCurrentSchema56);
 s+=",\"status\":";Quote(s,available?"available":"unavailable");s+=",\"unavailable_reason\":";
 if(available)s+="null";else Quote(s,q.observation.unavailable_reason.empty()?"opening_frame_unqualified":q.observation.unavailable_reason);
 s+=",\"read_only\":true,\"full_governance_ready\":false,\"action_ready\":false,\"native_revision\":";
 s+=available?std::to_string(q.expected_native_revision):"null";s+=",\"snapshot_id\":";
 if(available)Quote(s,"native:"+std::to_string(q.expected_native_revision));else s+="null";
 s+=",\"date_raw\":";s+=available?std::to_string(q.observation.frame.clock.date_raw):"null";
 s+=",\"player_character_id\":";s+=available?std::to_string(q.observation.frame.played_character_id):"null";
 if(gov){s+=",\"government\":";if(!available)s+="null";else{const auto&g=*q.observation.government;
  s+="{\"key\":";Quote(s,g.key);s+=",\"native_flag_count\":"+std::to_string(g.native_flag_count)+",\"flags\":[";
  bool first=true;for(const auto&flag:g.flags){if(!first)s+=',';first=false;Quote(s,flag);}s+="]}";}
 }else{s+=",\"current_focus\":";if(!available)s+="null";else{const auto&l=*q.observation.lifestyle;
  s+="{\"presence\":\"present\",\"key\":";Quote(s,l.focus_key);s+=",\"lifestyle_key\":";Quote(s,l.lifestyle_key);s+='}';}
  s+=",\"current_lifestyle_progress\":";if(!available)s+="null";else{const auto&l=*q.observation.lifestyle;
   s+="{\"presence\":\"present\",\"lifestyle_key\":";Quote(s,l.lifestyle_key);
   s+=",\"xp_total_raw\":"+std::to_string(l.xp_total_raw)+",\"xp_within_level_raw\":"+std::to_string(l.xp_within_level_raw)+
    ",\"xp_per_level\":"+std::to_string(l.xp_per_level)+",\"unspent_perk_points\":"+std::to_string(l.unspent_perk_points)+
    ",\"used_perk_points\":"+std::to_string(l.used_perk_points)+'}';}
 }
 const char *ready=available?"true":"false";
 s+=std::string(",\"readiness\":{\"same_frame_ready\":")+ready;
 s+=gov?",\"government_key_ready\":":",\"current_focus_ready\":";s+=ready;
 s+=gov?",\"government_flags_ready\":":",\"lifestyle_progress_ready\":";s+=ready;s+='}';
 s+=",\"origin\":{\"source_kind\":";Quote(s,q.offline_fixture?"offline_fixture":q.application_main_observed?"application_main_ticket":"unavailable");
 s+=",\"ticket_sequence\":";s+=q.ticket_sequence?std::to_string(q.ticket_sequence):"null";
 s+=",\"pump_epoch\":";s+=q.pump_epoch?std::to_string(q.pump_epoch):"null";
 s+=",\"thread_id\":";s+=q.thread_id?std::to_string(q.thread_id):"null";
 s+=",\"main_owner_observed\":";s+=q.application_main_observed&&!q.offline_fixture?"true":"false";s+='}';
 s+=",\"provenance\":{\"profile_id\":";Quote(s,gov?"ck3-26757580-lifestyle-scope-v1":"ck3-26757580-lifestyle-current-v1");
 s+=",\"adapter_id\":";Quote(s,hotfix26757580::kAdapterId);s+=",\"game_version\":";Quote(s,kGameVersion);
 s+=",\"executable_sha256\":";Quote(s,hotfix26757580::kExecutableSha256);
 s+=",\"reader_source_sha256\":";Quote(s,opening_provenance56::kReaderSha);
 s+=",\"abi_manifest_sha256\":";Quote(s,opening_provenance56::kAbiSha);s+="}}";return s;
}
std::string SerializeOpeningReadonlyCommand56(std::string_view id,const OpeningMailboxContext56&q){
 std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";Quote(s,id);
 s+=",\"ok\":true,\"result\":";s+=SerializeOpeningReadonlyData56(q);s+='}';return s;
}
}

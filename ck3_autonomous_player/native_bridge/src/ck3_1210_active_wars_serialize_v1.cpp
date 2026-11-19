#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
#include "xar_bridge/ck3_1210_military_production58.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include <algorithm>
#include <array>
#include <limits>
namespace xar::ck3_1210 {
namespace {
void Quote(std::string &s,std::string_view text) {
  constexpr char hex[]="0123456789abcdef";s+=static_cast<char>(34);
  for(const unsigned char c:text) {
    if(c==34 || c==92){s+=static_cast<char>(92);s+=static_cast<char>(c);}
    else if(c<32){s+=static_cast<char>(92);s+="u00";s+=hex[c>>4];s+=hex[c&15];}
    else s+=static_cast<char>(c);
  }
  s+=static_cast<char>(34);
}
const char *Bool(bool value) noexcept{return value?"true":"false";}
void Ids(std::string &s,const std::vector<std::int32_t> &ids) {
  s+='[';bool first=true;for(const auto id:ids){if(!first)s+=',';first=false;s+=std::to_string(id);}s+=']';
}
void Number(std::string &s,const std::optional<std::int32_t> &n) {
  s+=n?std::to_string(*n):"null";
}
bool Valid(const ActiveWarsMailboxContextV1 &q) noexcept {
  const auto &o=q.observation;const auto &f=o.frame;
  const bool offline=IsHotfix(q.output_build) && q.offline_fixture;
  if(IsHotfix(q.output_build) && (q.bindings.core.image_build!=q.output_build ||
      !q.ticket_sequence || !q.pump_epoch || !q.thread_id))return false;
  if((!q.application_main_observed && !offline) || (q.application_main_observed && offline) || !o.available || !o.same_frame_ready || !o.identity_complete ||
      !o.partial || o.full_snapshot_available || o.complete_active_wars_qualified || !o.active_wars ||
      !f.clock.paused || !f.map_ready || !f.has_played_character || !f.played_character_alive ||
      f.played_character_id==-1 || f.local_player_id<0 || f.clock.speed<1 || f.clock.speed>5 || o.war_slots_scanned<0 ||
      o.war_slots_scanned>kActiveWarsStorageLimitV1 || o.active_wars->size()>kActiveWarsOwnedLimitV1 ||
      o.participant_records>kActiveWarsParticipantBudgetV1 ||
      o.active_war_rows>static_cast<std::size_t>(o.war_slots_scanned) ||
      o.ended_war_rows>static_cast<std::size_t>(o.war_slots_scanned)-o.active_war_rows ||
      o.active_wars->size()>o.active_war_rows ||
      o.native_score_calls_attempted>2*o.active_wars->size())return false;
  std::size_t participants=0,raw_rows=0;
  bool scores=true;
  for(const auto &w:*o.active_wars) {
    for(const auto &other:*o.active_wars){if(&other==&w)break;if(other.war_id==w.war_id)return false;}
    const bool attack=w.player_side==ActiveWarPlayerSideV1::attacker;
    if(!attack && w.player_side!=ActiveWarPlayerSideV1::defender)return false;
    const auto contains=[](const auto &ids,std::int32_t id){return std::find(ids.begin(),ids.end(),id)!=ids.end();};
    if(w.war_id==-1 || (static_cast<std::uint32_t>(w.war_id)&0x00FFFFFFU)>=static_cast<std::uint32_t>(o.war_slots_scanned) || w.actual_player_character_id!=f.played_character_id ||
        w.primary_attacker_character_id==-1 || w.primary_defender_character_id==-1 ||
        w.attacker_participant_ids.size()>static_cast<std::size_t>(kActiveWarsSideLimitV1) ||
        w.defender_participant_ids.size()>static_cast<std::size_t>(kActiveWarsSideLimitV1) ||
        contains(w.attacker_participant_ids,-1) || contains(w.defender_participant_ids,-1) ||
        contains(w.attacker_participant_ids,f.played_character_id)!=attack ||
        contains(w.defender_participant_ids,f.played_character_id)==attack ||
        w.primary_opponent_character_id!=(attack?w.primary_defender_character_id:w.primary_attacker_character_id) ||
        w.player_is_primary_war_leader!=((attack?w.primary_attacker_character_id:w.primary_defender_character_id)==f.played_character_id) ||
        w.targeted_titles_observed || w.objectives_observed || w.allied_armies_observed || w.enemy_armies_observed)return false;
    const auto n=w.attacker_participant_ids.size()+w.defender_participant_ids.size();
    if(n>kActiveWarsParticipantBudgetV1-participants)return false;
    participants+=n;if(w.native_attacker_score_raw)++raw_rows;
    if(w.player_relative_war_score) {
      if(!w.native_attacker_score_raw || !w.score_unavailable_reason.empty())return false;
      const std::int64_t relative=attack?static_cast<std::int64_t>(*w.native_attacker_score_raw):-static_cast<std::int64_t>(*w.native_attacker_score_raw);
      if(relative!=*w.player_relative_war_score)return false;
    } else {
      if(w.score_unavailable_reason.empty())return false;
      if(w.native_attacker_score_raw && (attack || *w.native_attacker_score_raw!=(std::numeric_limits<std::int32_t>::min)() ||
          w.score_unavailable_reason!="active_wars_relative_score_overflow"))return false;
      scores=false;
    }
  }
  return o.score_complete==scores && participants<=o.participant_records && o.native_score_calls_attempted>=2*raw_rows;
}
void Rich(std::string &s) {
  constexpr std::array<std::string_view,6> keys{"targeted_title_ids","war_objective_province_ids",
      "objective_province_states","enemy_primary_default_raise_province_id","allied_armies","enemy_armies"};
  s+="{\"";bool first=true;
  for(const auto key:keys){if(!first)s+=",\"";first=false;s+=key;
    s+="\":{\"status\":\"unavailable\",\"unavailable_reason\":\"active_wars_rich_fields_not_observed\"}";}
  s+='}';
}
void Row(std::string &s,const ActiveWarIdentityRowV1 &w) {
  s+="{\"war_id\":"+std::to_string(w.war_id);
  s+=",\"actual_player_character_id\":"+std::to_string(w.actual_player_character_id);
  s+=",\"player_side\":";Quote(s,w.player_side==ActiveWarPlayerSideV1::attacker?"attacker":"defender");
  s+=",\"primary_attacker_character_id\":"+std::to_string(w.primary_attacker_character_id);
  s+=",\"primary_defender_character_id\":"+std::to_string(w.primary_defender_character_id);
  s+=",\"primary_opponent_character_id\":"+std::to_string(w.primary_opponent_character_id);
  s+=",\"player_is_primary_war_leader\":";s+=Bool(w.player_is_primary_war_leader);
  s+=",\"attacker_participant_ids\":";Ids(s,w.attacker_participant_ids);
  s+=",\"defender_participant_ids\":";Ids(s,w.defender_participant_ids);
  s+=",\"native_attacker_score_raw\":";Number(s,w.native_attacker_score_raw);
  s+=",\"player_relative_war_score\":";Number(s,w.player_relative_war_score);
  s+=",\"score_unavailable_reason\":";
  if(w.player_relative_war_score)s+="null";else Quote(s,w.score_unavailable_reason);
  s+=",\"rich\":";Rich(s);s+='}';
}
}
std::string SerializeActiveWarsIdentityResultV1(const ActiveWarsMailboxContextV1 &q) {
  const auto &o=q.observation;const bool hotfix=IsHotfix(q.output_build);const bool known=Valid(q);
  const auto reason=!o.unavailable_reason.empty()?o.unavailable_reason:
      std::string_view("active_wars_frame_inconsistent");
  CoreFrameObservationV1 core{};core.core_available=known;
  core.application_main_observed=q.application_main_observed;core.core=o.frame;core.unavailable_reason=reason;
  std::string s="{\"step\":";Quote(s,hotfix?kActiveWarsHotfixStep58:kActiveWarsIdentityStepV1);
  s+=",\"schema\":";Quote(s,hotfix?kActiveWarsHotfixSchema58:kActiveWarsIdentitySchemaV1);
  s+=",\"game_version\":";Quote(s,kGameVersion);
  s+=",\"executable_sha256\":";Quote(s,ExecutableShaForBuild(q.output_build));
  s+=",\"adapter_id\":";Quote(s,hotfix?hotfix26757580::kAdapterId:kAdapterId);
  s+=",\"backend\":\"ck3-1.21.0-native-headless-main-thread\",\"status\":";Quote(s,known?"partial":"unavailable");
  s+=",\"complete_snapshot\":false,\"application_main_observed\":";s+=Bool(q.application_main_observed);
  s+=",\"identity_available\":";s+=Bool(known);
  s+=",\"same_frame_ready\":";s+=Bool(known);
  s+=",\"score_complete\":";s+=Bool(known && o.score_complete);
  s+=",\"full_snapshot_available\":false,\"complete_active_wars_qualified\":false,\"core_frame\":";
  s+=SerializeCoreFrameV1(core,q.output_build);s+=",\"active_wars\":";
  if(known){s+='[';bool first=true;for(const auto &w:*o.active_wars){if(!first)s+=',';first=false;Row(s,w);}s+=']';}
  else s+="null";
  const auto count=[known](std::size_t n){return known?std::to_string(n):std::string("null");};
  s+=",\"war_slots_scanned\":"+count(static_cast<std::size_t>(o.war_slots_scanned));
  s+=",\"active_war_rows\":"+count(o.active_war_rows);
  s+=",\"ended_war_rows\":"+count(o.ended_war_rows);
  s+=",\"participant_records\":"+count(o.participant_records);
  s+=",\"native_score_calls_attempted\":"+std::to_string(o.native_score_calls_attempted);
  s+=",\"unavailable_reason\":";if(known)s+="null";else Quote(s,reason);
  if(hotfix) {
    s+=",\"read_only\":true,\"action_ready\":false,\"origin\":{\"source_kind\":";
    Quote(s,q.offline_fixture?"offline_fixture":q.application_main_observed?"application_main_ticket":"unavailable");
    s+=",\"ticket_sequence\":";s+=q.ticket_sequence?std::to_string(q.ticket_sequence):"null";
    s+=",\"pump_epoch\":";s+=q.pump_epoch?std::to_string(q.pump_epoch):"null";
    s+=",\"thread_id\":";s+=q.thread_id?std::to_string(q.thread_id):"null";
    s+=",\"main_owner_observed\":";s+=Bool(q.application_main_observed && !q.offline_fixture);s+='}';
  }
  s+='}';return s;
}
std::string SerializeActiveWarsIdentityCommandResultV1(std::string_view id,const ActiveWarsMailboxContextV1 &q) {
  std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";Quote(s,id);
  s+=",\"ok\":true,\"result\":";s+=SerializeActiveWarsIdentityResultV1(q);s+='}';return s;
}
}

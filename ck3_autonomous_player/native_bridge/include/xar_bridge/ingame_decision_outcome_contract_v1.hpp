#pragma once
#include "xar_bridge/game_contract.hpp"
#include <string_view>
namespace xar::ck3_11906 {
inline bool IngameDecisionOutcomeKeySyntaxV1(std::string_view key) noexcept {
  if(key.empty()||key.size()>192)return false;
  for(char c:key)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return false;
  return true;
}
inline bool IngameDecisionOutcomeRequestValidV1(std::string_view outcome,std::string_view event_key) noexcept {
  if(outcome=="decision_closed")return event_key.empty();
  if(outcome!="event_window"||event_key.size()>192)return false;
  const auto dot=event_key.find('.');
  return dot!=std::string_view::npos&&dot>0&&dot+1<event_key.size()&&event_key.find('.',dot+1)==std::string_view::npos&&
      IngameDecisionOutcomeKeySyntaxV1(event_key.substr(0,dot))&&IngameDecisionOutcomeKeySyntaxV1(event_key.substr(dot+1));
}
// Route-local empty-key parser for the compact native protocol. The shared
// JsonStringField intentionally rejects empty strings and remains unchanged.
inline bool IngameDecisionOutcomeEmptyEventKeyWireV1(std::string_view json) noexcept {
  constexpr std::string_view field="\"expected_event_definition_key\":";
  if(json.empty()||json.front()!='{'||json.back()!='}')return false;
  const auto at=json.find(field);
  if(at==std::string_view::npos||json.find(field,at+field.size())!=std::string_view::npos)return false;
  bool quoted=false,escaped=false;std::size_t objects=0,arrays=0;
  for(std::size_t i=0;i<at;++i){
    const char c=json[i];
    if(quoted){if(escaped)escaped=false;else if(c=='\\')escaped=true;else if(c=='"')quoted=false;}
    else if(c=='"')quoted=true;
    else if(c=='{')++objects;
    else if(c=='}'){if(!objects)return false;--objects;}
    else if(c=='[')++arrays;
    else if(c==']'){if(!arrays)return false;--arrays;}
  }
  if(quoted||objects!=1||arrays!=0||at==0||(json[at-1]!='{'&&json[at-1]!=','))return false;
  const auto value=at+field.size();
  return value+2<json.size()&&json[value]=='"'&&json[value+1]=='"'&&
      (json[value+2]==','||json[value+2]=='}');
}
// ReadSnapshot contains business data as well as control-frame data. The current
// generic route admits resource/stress effects, and event fields only for the
// event-window branch. This comparison proves no product effect or event identity.
inline bool IngameDecisionOutcomeFrameMatchesV1(const game::Snapshot &before,
    const game::Snapshot &observed,std::string_view outcome) {
  if(before.has_active_event||before.has_pending_character_interaction||!before.paused||!before.map_ready||!before.has_played_character||
      !before.played_character_alive||before.played_character_id<=0||
      (outcome!="event_window"&&outcome!="decision_closed"))return false;
  auto normalized=observed;
  normalized.played_character_stress_points=before.played_character_stress_points;
  normalized.played_character_gold.raw=before.played_character_gold.raw;
  normalized.played_character_prestige.raw=before.played_character_prestige.raw;
  normalized.played_character_piety.raw=before.played_character_piety.raw;
  if(outcome=="event_window"){
    normalized.has_active_event=before.has_active_event;
    normalized.active_event_instance_id=before.active_event_instance_id;
    normalized.active_event_option_count=before.active_event_option_count;
  }
  return normalized==before;
}
} // namespace xar::ck3_11906

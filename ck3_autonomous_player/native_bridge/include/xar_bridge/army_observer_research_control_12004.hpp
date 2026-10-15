#pragma once
#include "xar_bridge/army_observer_research_sampling_12004.hpp"
#include <array>
#include <string>
#include <string_view>
namespace xar::ck3_12004 {
inline constexpr std::array<std::string_view,9> kArmyResearchFamilies12004{
 "natural_phase","regular_core","daily_assault_preparation","assault_placement",
 "assault_consumer","assault_group_release","gathering","cleanup","pre_date_prefix"};
struct ArmyResearchFamilyState12004 {
 bool installed=false;
 ArmyObserverResearchSamplingState12004 sampling{};
};
using ArmyResearchFamilyStates12004=std::array<ArmyResearchFamilyState12004,9>;
inline bool IsArmyResearchFamily12004(std::string_view family) noexcept {
 if(family=="all")return true;
 for(const auto name:kArmyResearchFamilies12004)if(name==family)return true;
 return false;
}
inline bool ArmyResearchSamplingAccepted12004(std::string_view family,
 std::string_view mode,const ArmyResearchFamilyStates12004 &states) noexcept {
 if(!IsArmyResearchFamily12004(family) || (mode!="query" && mode!="enable" && mode!="disable"))return false;
 for(std::size_t i=0;i<states.size();++i) {
  if(family!="all" && family!=kArmyResearchFamilies12004[i])continue;
  if(mode=="query")continue;
  const auto &row=states[i]; const auto &s=row.sampling;
  if(!row.installed || !s.available)return false;
  if(mode=="enable" && !s.enabled)return false;
  if(mode=="disable" && (s.enabled || s.busy || !s.clear_completed))return false;
 }
 return true;
}
inline std::string SerializeArmyResearchSampling12004(std::string_view family,
 const ArmyResearchFamilyStates12004 &states) {
 std::string out="{";bool first=true;
 const auto boolean=[](bool v){return v?"true":"false";};
 for(std::size_t i=0;i<states.size();++i) {
  if(family!="all" && family!=kArmyResearchFamilies12004[i])continue;
  const auto &row=states[i];const auto &s=row.sampling;
  if(!first)out+=',';first=false;
  out+='"';out+=kArmyResearchFamilies12004[i];out+="\":{\"installed\":";
  out+=boolean(row.installed);out+=",\"available\":";out+=boolean(s.available);
  out+=",\"capture_enabled\":";out+=boolean(s.enabled);
  out+=",\"busy\":";out+=boolean(s.busy);
  out+=",\"clear_completed\":";out+=boolean(s.clear_completed);
  out+=",\"epoch\":"+std::to_string(s.epoch);
  out+=",\"active_captures\":"+std::to_string(s.active_captures);
  out+=",\"retained_records\":"+std::to_string(s.retained_records);
  out+=",\"qualified_records\":"+std::to_string(s.qualified_records);
  out+=",\"status\":\"";
  out+=!row.installed || !s.available?"unavailable":s.enabled?"enabled":s.busy?"busy":s.clear_completed?"disabled":"clear_pending";
  out+="\",\"readiness\":\"";
  out+=!row.installed || !s.available?"unavailable":!s.enabled?"off":s.busy?"inflight":s.qualified_records==0?"awaiting_sample":"retained_observation";
  out+="\"}";
 }
 out+='}';return out;
}
} // namespace xar::ck3_12004

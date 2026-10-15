#pragma once
#include "xar_bridge/army_refill_permission_switch_v1.hpp"
#include <string_view>
namespace xar::game {
template<class Number,class Text> inline void AppendArmyRefillPermissionSwitchV1(
    std::string &out,const ArmyRefillPermissionSwitchV1 &r,Number number,Text text) {
  out+="{\"source\":\"native_regiment_permission_262C6E0_switch_12004\",\"status\":";text(out,r.status);
  out+=",\"unavailable_reason\":";if(r.unavailable_reason.empty())out+="null";else text(out,r.unavailable_reason);
  out+=",\"source_branch\":";text(out,r.source_branch);
  const auto numeric=[&](std::string_view key,const auto &v){out+=',';text(out,key);out+=':';out+=v?number(*v):"null";};
  const auto boolean=[&](std::string_view key,const auto &v){out+=',';text(out,key);out+=':';out+=v?(*v?"true":"false"):"null";};
#define XAR_REFILL_SOURCE_NUMBER(f) numeric(#f,r.f)
  XAR_REFILL_SOURCE_NUMBER(persistent_full_id);XAR_REFILL_SOURCE_NUMBER(definition_magic_38_raw);
  XAR_REFILL_SOURCE_NUMBER(character_ref_12c_raw);XAR_REFILL_SOURCE_NUMBER(title_ref_130_raw);
  XAR_REFILL_SOURCE_NUMBER(resolved_title_full_id);XAR_REFILL_SOURCE_NUMBER(selected_character_raw_full_id);
  XAR_REFILL_SOURCE_NUMBER(resolved_character_full_id);XAR_REFILL_SOURCE_NUMBER(character_magic_raw);
  XAR_REFILL_SOURCE_NUMBER(raw_byte_4a9);
#undef XAR_REFILL_SOURCE_NUMBER
  boolean("title_used_fallback",r.title_used_fallback);boolean("character_used_fallback",r.character_used_fallback);
  boolean("military_component_present",r.military_component_present);boolean("enabled",r.enabled);
  out+=",\"identity_consistent\":";out+=r.identity_consistent?"true}":"false}";
}
} // namespace xar::game

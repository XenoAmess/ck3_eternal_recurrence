#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
#ifndef XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004
#define XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004 0
#endif
#if XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004 && !XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004
#error static owner switch requires the independent source continuation
#endif
namespace xar::game {
struct GuiRefillStaticOwnerSwitch12004V1 {
  std::string status="unavailable",unavailable_reason="static_owner_source_not_admitted",value_basis;
  std::optional<std::uint32_t> ancestor_depth;
  std::optional<std::int32_t> owner_full_id;
  std::optional<bool> military_component_present,enabled;
  std::optional<std::uint8_t> raw_byte_4a9;
  bool stable_double_read=false;
  bool operator==(const GuiRefillStaticOwnerSwitch12004V1 &) const=default;
};
template<class Text> inline void AppendGuiRefillStaticOwnerSwitch12004(
    std::string &s,const GuiRefillStaticOwnerSwitch12004V1 &v,Text text) {
  s+="{\"source\":\"native_gui_type635_static_direct_owner_switch_12004\",\"scope\":\"static_direct_source_candidate\",\"status\":";text(s,v.status);
  s+=",\"unavailable_reason\":";if(v.unavailable_reason.empty())s+="null";else text(s,v.unavailable_reason);
  s+=",\"current_variable_table_observed\":false,\"native_receiver_selected\":false,\"provider_invoked\":false";
  const auto n=[&](const char *key,const auto &value){s+=",\"";s+=key;s+="\":";s+=value?std::to_string(*value):"null";};
  const auto b=[&](const char *key,const auto &value){s+=",\"";s+=key;s+="\":";s+=value?(*value?"true":"false"):"null";};
  n("ancestor_depth",v.ancestor_depth);n("owner_full_id",v.owner_full_id);
  b("military_component_present",v.military_component_present);n("raw_byte_4a9",v.raw_byte_4a9);b("enabled",v.enabled);
  s+=",\"value_basis\":";if(v.value_basis.empty())s+="null";else text(s,v.value_basis);
  s+=",\"stable_double_read\":";s+=v.stable_double_read?"true":"false";s+='}';
}
}
namespace xar::ck3_12004 {
struct GuiStaticOwnerSwitchCapture12004 {
  game::GuiRefillStaticOwnerSwitch12004V1 value;
  std::vector<std::uintptr_t> identity;
};
// Character has already passed the caller's source owner+218/fullID/Char gate.
// load is the existing budgeted reader, never an independent memory service.
template<class Load> inline GuiStaticOwnerSwitchCapture12004 CaptureGuiStaticOwnerSwitch12004(
    Load load,std::uintptr_t character,std::int32_t owner,std::uint32_t depth) {
  GuiStaticOwnerSwitchCapture12004 capture;
  auto &v=capture.value;std::uintptr_t military=0;std::uint8_t raw=0;
  if(!load("static_owner_military_1c0",character,0x1C0,military)) {
    v.unavailable_reason="static_owner_military_read_failed";return capture;
  }
  if(military&&!load("static_owner_switch_4a9",military,0x4A9,raw)) {
    v.unavailable_reason="static_owner_switch_read_failed";return capture;
  }
  v.status="available";v.unavailable_reason.clear();v.ancestor_depth=depth;v.owner_full_id=owner;
  v.military_component_present=military!=0;v.enabled=military!=0&&raw!=0;
  if(military){v.raw_byte_4a9=raw;v.value_basis="raw_military_byte";}
  else v.value_basis="native_null_military_zero";
  capture.identity={character,military,raw};return capture;
}
inline game::GuiRefillStaticOwnerSwitch12004V1 JoinGuiStaticOwnerSwitch12004(
    const GuiStaticOwnerSwitchCapture12004 &a,const GuiStaticOwnerSwitchCapture12004 &b) {
  if(a.value.status!="available")return a.value;
  if(b.value.status!="available")return b.value;
  game::GuiRefillStaticOwnerSwitch12004V1 value;
  if(a.identity!=b.identity||a.value!=b.value){
    value.unavailable_reason="static_owner_switch_changed_during_capture";return value;
  }
  value=a.value;value.stable_double_read=true;return value;
}
}

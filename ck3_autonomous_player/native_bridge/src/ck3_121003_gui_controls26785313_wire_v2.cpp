#include "xar_bridge/ck3_121003_gui_controls26785313_wire_v2.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <charconv>
#include <utility>
namespace xar::ck3_121003::build26785313 {namespace {
struct Cursor {
  std::string_view text;std::size_t pos=0;
  void Space() noexcept {while(pos<text.size()&&(text[pos]==' '||text[pos]=='\n'||text[pos]=='\r'||text[pos]=='\t'))++pos;}
  bool Take(char ch) noexcept {Space();if(pos==text.size()||text[pos]!=ch)return false;++pos;return true;}
  bool String(std::string_view &out) noexcept {
    if(!Take('"'))return false;const auto start=pos;
    while(pos<text.size()&&text[pos]!='"') {const auto c=static_cast<unsigned char>(text[pos]);if(c<0x20||c>=0x7F||c=='\\'||pos-start>=192)return false;++pos;}
    if(pos==text.size())return false;out=text.substr(start,pos++-start);return true;
  }
  template<class T>bool Number(T &out) noexcept {
    Space();const auto start=pos;if(pos<text.size()&&text[pos]=='-')++pos;const auto digits=pos;
    while(pos<text.size()&&text[pos]>='0'&&text[pos]<='9')++pos;
    if(pos==digits||(pos-digits>1&&text[digits]=='0'))return false;
    T value{};const auto parsed=std::from_chars(text.data()+start,text.data()+pos,value);
    if(parsed.ec!=std::errc{}||parsed.ptr!=text.data()+pos||(text[start]=='-'&&value==0))return false;
    out=value;return true;
  }
  bool Boolean(bool &out) noexcept {
    Space();if(text.substr(pos,4)=="true"){pos+=4;out=true;return true;}
    if(text.substr(pos,5)=="false"){pos+=5;out=false;return true;}return false;
  }
  bool Identity(std::string_view expected,bool hash=false) noexcept {
    std::string_view actual;if(!String(actual)||actual.size()!=expected.size())return false;
    for(std::size_t i=0;i<actual.size();++i) {auto c=actual[i];if(hash&&c>='a'&&c<='f')c=static_cast<char>(c-'a'+'A');if(c!=expected[i])return false;}return true;
  }
};
bool RequestId(std::string_view id) noexcept {
  if(id.empty()||id.size()>96)return false;
  for(const char c:id)if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='-'||c=='_'||c=='.'))return false;
  return true;
}
bool Core(Cursor &c,ck3_1210::CoreSnapshotPrefix &p) noexcept {
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
    std::uint32_t bit=0;bool good=false;
    if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}
    else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}
    else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}
    else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}
    else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}
    else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}
    else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}
    else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  return seen==255&&p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&
      p.map_ready&&p.has_played_character&&p.played_character_id!=0&&p.played_character_id!=-1&&p.played_character_alive;
}

bool CanonicalPositive(Cursor &c,std::uint64_t &out) noexcept {
 std::string_view text;if(!c.String(text)||text.empty()||text[0]<'1'||text[0]>'9')return false;
 for(char ch:text)if(ch<'0'||ch>'9')return false;
 const auto result=std::from_chars(text.data(),text.data()+text.size(),out);
 return result.ec==std::errc{}&&result.ptr==text.data()+text.size()&&out>0;
}
bool Claim(Cursor &c,GuiControlsWireRequest267V2 &r) {
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')) {
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
  std::uint32_t bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kGuiControlsRequestSchema267V2);}
  else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
  else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
  else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
  else if(key=="backend"){bit=16;good=c.Identity(kGuiControlsBackend267V2);}
  else if(key=="deadline_unix_ms"){bit=32;good=c.Number(r.owner_request.deadline_unix_ms)&&r.owner_request.deadline_unix_ms>0;}
  else if(key=="expected_core"){bit=64;good=Core(c,r.owner_request.expected_core);}
  else if(key=="window_name"){bit=128;std::string_view value;good=c.String(value)&&(value=="faith_window"||value=="rite_creation_window"||value=="hud_layer"||value=="bottom"||value=="windows_layer");if(good)r.owner_request.window_name=value;}
  else if(key=="query_generation"){bit=256;good=CanonicalPositive(c,r.control.query_generation);}
  else if(key=="widget_id"){bit=512;good=CanonicalPositive(c,r.control.widget_id);}
  else if(key=="expected_source_rite_id"){bit=1024;good=c.Number(r.expected_source_rite_id)&&r.expected_source_rite_id!=0xFFFFFFFFU;}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }
 return r.owner_request.window_name=="rite_creation_window"?(seen==1279||seen==2047):(seen==255||seen==1023);
}
void String(std::string &out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);
  }out+='"';
}

const char *Status(ck3_1210::GuiControlStatusV1 status) noexcept {
 using S=ck3_1210::GuiControlStatusV1;
 switch(status){case S::available:return "available";case S::submitted:return "submitted";
 case S::expired:return "expired";case S::stale_full_snapshot:return "stale_core";
 case S::stale_gui:return "stale_gui";case S::disabled:return "disabled";case S::indeterminate:return "indeterminate";
 default:return "unavailable";}
}
bool CoreReady(const ck3_1210::CoreSnapshotPrefix &p) noexcept {
 return p.clock.paused&&p.clock.speed>=1&&p.clock.speed<=5&&p.local_player_id>=0&&p.map_ready&&
  p.has_played_character&&p.played_character_id!=0&&p.played_character_id!=-1&&p.played_character_alive;
}
} // namespace
bool ParseGuiControlsRequest267V2(std::string_view text,GuiControlsWireRequest267V2 &out) noexcept {
  try {out={};if(text.size()>16384)return false;Cursor c{text};GuiControlsWireRequest267V2 parsed{};
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
    std::uint32_t bit=0;bool good=false;std::uint64_t number=0;
    if(key=="type"){bit=1;good=c.Identity("execute_step");}
    else if(key=="protocol_version"){bit=2;good=c.Number(number)&&number==1;}
    else if(key=="request_id"){bit=4;good=c.String(parsed.request_id)&&RequestId(parsed.request_id);}
    else if(key=="step"){bit=8;std::string_view step;good=c.String(step)&&(step==kGuiControlsQueryStep267V2||step==kGuiControlsActivateStep267V2);
      if(good){parsed.control.activate=step==kGuiControlsActivateStep267V2;parsed.control.step=parsed.control.activate?kGuiControlsActivateStep267V2:kGuiControlsQueryStep267V2;}}
    else if(key=="expected_revision"){bit=16;good=c.Number(number)&&number==0;}
    else if(key=="gui_control"){bit=32;good=Claim(c,parsed);}
    else if(key=="arguments"){bit=64;good=c.Take('{')&&c.Take('}');}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  c.Space();if(seen!=127||c.pos!=text.size())return false;if(parsed.control.activate!=(parsed.control.query_generation!=0&&parsed.control.widget_id!=0))return false;
  if(parsed.control.activate&&parsed.owner_request.window_name!="rite_creation_window"&&parsed.owner_request.window_name!="bottom"&&parsed.owner_request.window_name!="windows_layer")return false;
  parsed.control.root_name=parsed.owner_request.window_name;parsed.control.deadline_unix_ms=parsed.owner_request.deadline_unix_ms;
  out=std::move(parsed);return true;}catch(...){out={};return false;}
}

bool GuiControlsRouteEnabled267V2([[maybe_unused]]const game::AdapterDescriptor &d,[[maybe_unused]]bool activate) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 const auto has=[&](std::string_view cap){return std::find(d.capabilities.begin(),d.capabilities.end(),cap)!=d.capabilities.end();};
 return game::IsCk3_121003Core26785313Descriptor(d)&&has(ck3_1210::kCoreFrameCapabilityV1)&&
  has(kGuiControlsQueryCapability267V2)&&(!activate||has(kGuiControlsActivateCapability267V2));
#else
 return false;
#endif
}
std::string SerializeGuiControlsCommandResult267V2(std::string_view id,const GuiControlsContext267V2 &q,const game::AdapterDescriptor &d) {
 using S=ck3_1210::GuiControlStatusV1;const auto&r=q.result;
 const bool route=GuiControlsRouteEnabled267V2(d,q.control.activate);
 const bool core_ready=route&&q.core_before_verified&&r.application_main_observed&&CoreReady(q.observed)&&
  q.request.connection_generation&&q.witness_ticket_sequence&&q.witness_pump_epoch&&q.witness_thread_id;
 const bool rite_verified=core_ready&&q.request.window_name=="rite_creation_window"&&q.expected_source_rite_id!=0xFFFFFFFFU&&q.verified_source_rite_id==q.expected_source_rite_id;
 const bool available=(q.request.window_name!="rite_creation_window"||rite_verified)&&core_ready&&!q.control.activate&&r.status==S::available&&r.source_abi_pins_verified&&
  r.query_generation&& !r.widgets.empty()&&r.widgets.size()<=ck3_1210::kGuiControlMaximumRowsV1;
 const bool attempted=r.effect_attempted;
 ck3_1210::CoreFrameObservationV1 core{};core.application_main_observed=route&&r.application_main_observed;
 if(core_ready){core.core_available=true;core.core=q.observed;core.unavailable_reason={};}
 else core.unavailable_reason=route?"current_gui_core_owner_not_verified":"current_gui_controls_profile_unavailable";
 std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(out,id);
 out+=",\"ok\":true,\"result\":{\"step\":";String(out,q.control.activate?kGuiControlsActivateStep267V2:kGuiControlsQueryStep267V2);
 out+=",\"schema\":";String(out,kGuiControlsResultSchema267V2);out+=",\"game_version\":";String(out,kGameVersion);
 out+=",\"executable_sha256\":";String(out,kExecutableSha256);out+=",\"adapter_id\":";String(out,kAdapterId);
 out+=",\"backend\":";String(out,kGuiControlsBackend267V2);out+=",\"status\":";
 String(out,attempted&&!core_ready?"indeterminate":core_ready?Status(r.status):"unavailable");
 const auto boolean=[&](const char*key,bool value){out+=",\"";out+=key;out+="\":";out+=value?"true":"false";};
 boolean("query_available",available);boolean("application_main_observed",core.application_main_observed);
 boolean("core_before_verified",core_ready);boolean("source_abi_pins_verified",core_ready&&r.source_abi_pins_verified);
 boolean("addresses_redacted",true);boolean("complete_snapshot",false);boolean("full_snapshot_before_verified",false);
 boolean("complete_gui_tree",false);boolean("effect_attempted",attempted);boolean("native_handled",attempted&&r.native_handled);
 boolean("verification_pending",attempted||r.verification_pending);boolean("effect_confirmed",false);boolean("physical_save_confirmed",false);
 out+=",\"core_frame\":"+ck3_1210::SerializeCoreFrameV1(core,ck3_1210::CoreFrameReadonlySourceV1::hotfix26785313);
 out+=",\"window_name\":";String(out,q.request.window_name);
 boolean("rite_source_verified",rite_verified);out+=",\"source_rite_id\":";if(rite_verified)out+=std::to_string(q.verified_source_rite_id);else out+="null";
 out+=",\"query_generation\":";if(available||(q.control.activate&&r.query_generation))String(out,std::to_string(r.query_generation));else out+="null";
 out+=",\"owner_witness\":";
 if(core_ready){out+="{\"connection_generation\":";String(out,std::to_string(q.request.connection_generation));
  out+=",\"ticket_sequence\":";String(out,std::to_string(q.witness_ticket_sequence));
  out+=",\"pump_epoch\":";String(out,std::to_string(q.witness_pump_epoch));out+=",\"thread_id\":"+std::to_string(q.witness_thread_id)+'}';
 }else out+="null";
 out+=",\"widgets\":";
 if(available){out+='[';for(std::size_t i=0;i<r.widgets.size();++i){const auto&w=r.widgets[i];if(i)out+=',';
  out+="{\"widget_id\":";String(out,std::to_string(w.widget_id));out+=",\"runtime_name\":";String(out,w.runtime_name);
  out+=",\"child_path\":";String(out,w.child_path);out+=",\"effective_visible\":";out+=w.effective_visible?"true":"false";
  out+=",\"enabled\":";out+=w.enabled?"true":"false";out+=",\"native_callback_admissible\":";out+=w.clickable?"true":"false";out+='}';
 }out+=']';}else out+="null";
 out+=",\"unavailable_reason\":";
 if(available||(core_ready&&(r.status==S::submitted)))out+="null";
 else String(out,!route?"current_gui_controls_profile_unavailable":!r.unavailable_reason.empty()?std::string_view(r.unavailable_reason):"current_gui_controls_source_unavailable");
 out+="}}";return out;
}
} // namespace

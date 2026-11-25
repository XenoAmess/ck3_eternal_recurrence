#include "xar_bridge/ck3_121003_gui_window26785313_wire_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <array>
#include <utility>
#include <charconv>

namespace xar::ck3_121003::build26785313 { namespace {
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
      p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
bool Claim(Cursor &c,GuiWindowRequestV1 &r) {
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
    std::uint32_t bit=0;bool good=false;
    if(key=="schema"){bit=1;good=c.Identity(kGuiWindowRequestSchemaV1);}
    else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
    else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
    else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
    else if(key=="backend"){bit=16;good=c.Identity(kGuiWindowBackendV1);}
    else if(key=="deadline_unix_ms"){bit=32;good=c.Number(r.deadline_unix_ms)&&r.deadline_unix_ms>0;}
    else if(key=="expected_core"){bit=64;good=Core(c,r.expected_core);}
    else if(key=="window_name"){bit=128;std::string_view name;good=c.String(name)&&RequestId(name)&&name.size()<=96;if(good)r.window_name=name;}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  return seen==255;
}
void String(std::string &out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);
  }out+='"';
}
bool AvailableFixedScoreboard(const ReadonlyObservation&in) noexcept {
 const auto&p=in.core;
 if(!in.available||!in.partial||in.offline_fixture||!in.main_owner_observed||in.raw_resources||in.gui_root_index||!in.gui_window||
  !p.clock.paused||p.clock.speed<1||p.clock.speed>5||p.local_player_id<0||!p.map_ready||!p.has_played_character||p.played_character_id==-1||!p.played_character_alive)return false;
 const auto&r=*in.gui_window;
 if(r.requested_name!="zg361_scoreboard_window"||!r.application||!r.context||!r.global_root||!r.connection_generation||!r.ticket_sequence||!r.pump_epoch||!r.owner_thread_id||
  r.top_level.size()>kGuiWindowMaxNodesV1||r.tree.empty()||r.tree.size()>kGuiWindowMaxNodesV1||!r.ancestors.empty()||
  r.root.widget!=r.global_root||r.root.context!=r.context||r.root.parent||r.root.child_count<0||static_cast<std::size_t>(r.root.child_count)!=r.top_level.size())return false;
 const GuiWindowNodeV1*middle=nullptr;
 for(const auto&n:r.top_level){if(!n.widget||n.context!=r.context||n.parent!=r.global_root||n.name.size()>kGuiWindowMaxNameBytesV1)return false;
  if(n.name=="middle"){if(middle)return false;middle=&n;}}
 if(!middle||r.tree[0]!=*middle||r.tree[0].parent_index!=-1||r.tree[0].depth)return false;
 if(!r.window_found)return r.tree.size()==1;
 if(r.tree.size()<2)return false;const auto&root=r.tree[1];
 if(root.name!=r.requested_name||root.parent_index!=0||root.parent!=middle->widget||root.depth!=1||middle->child_count<=0||
  root.sibling_index>=static_cast<std::uint32_t>(middle->child_count)||(root.visible&&!middle->visible)||(root.enabled&&!middle->enabled))return false;
 std::array<std::uint16_t,kGuiWindowMaxNodesV1>children{};
 for(std::size_t i=1;i<r.tree.size();++i){const auto&n=r.tree[i];
  if(!n.widget||n.context!=r.context||n.name.size()>kGuiWindowMaxNameBytesV1||n.depth>kGuiWindowMaxDepthV1||n.child_count<0||(n.flags&1))return false;
  if(i>1){if(n.parent_index<1||static_cast<std::size_t>(n.parent_index)>=i||n.parent!=r.tree[n.parent_index].widget||n.depth!=r.tree[n.parent_index].depth+1)return false;
   const auto&parent=r.tree[n.parent_index];if((n.visible&&!parent.visible)||(n.enabled&&!parent.enabled)||n.sibling_index!=children[n.parent_index])return false;++children[n.parent_index];}
 }
 for(std::size_t i=1;i<r.tree.size();++i)if(children[i]!=static_cast<std::size_t>(r.tree[i].child_count))return false;
 return true;
}
bool Available(const ReadonlyObservation &in) noexcept {
 if(in.gui_window&&in.gui_window->requested_name=="zg361_scoreboard_window")return AvailableFixedScoreboard(in);
 const auto &p=in.core;
 if(!in.available||!in.partial||in.offline_fixture||!in.main_owner_observed||in.raw_resources||in.gui_root_index||!in.gui_window||
    !p.clock.paused||p.clock.speed<1||p.clock.speed>5||p.local_player_id<0||!p.map_ready||!p.has_played_character||p.played_character_id==-1||!p.played_character_alive)return false;
 const auto&r=*in.gui_window;
 if(!r.application||!r.context||!r.global_root||!r.connection_generation||!r.ticket_sequence||!r.pump_epoch||!r.owner_thread_id||
    r.top_level.size()>kGuiWindowMaxNodesV1||r.tree.size()>kGuiWindowMaxNodesV1||r.window_found!=!r.tree.empty()||
    r.root.widget!=r.global_root||r.root.context!=r.context||r.root.parent!=0||r.root.child_count<0||
    static_cast<std::size_t>(r.root.child_count)!=r.top_level.size())return false;
 for(const auto&n:r.top_level)if(!n.widget||n.context!=r.context||n.parent!=r.global_root||n.name.size()>kGuiWindowMaxNameBytesV1)return false;
 std::array<std::uint16_t,kGuiWindowMaxNodesV1> children{};
 const auto found=std::find_if(r.top_level.begin(),r.top_level.end(),[&](const auto&n){return n.name==r.requested_name;});
 const auto matches=std::count_if(r.top_level.begin(),r.top_level.end(),[&](const auto&n){return n.name==r.requested_name;});
 if(matches!=(r.window_found?1:0))return false;
 if(r.window_found&&(found->widget!=r.tree[0].widget||found->name!=r.tree[0].name||found->visible!=r.tree[0].visible||found->enabled!=r.tree[0].enabled||found->sibling_index!=r.tree[0].sibling_index))return false;
 for(std::size_t i=0;i<r.tree.size();++i) {
  const auto&n=r.tree[i];if(!n.widget||n.context!=r.context||n.name.size()>kGuiWindowMaxNameBytesV1||n.depth>kGuiWindowMaxDepthV1||n.child_count<0)return false;
  if(i==0){if(n.parent_index!=-1||n.parent!=r.global_root||n.name!=r.requested_name)return false;}
  else if(n.parent_index<0||static_cast<std::size_t>(n.parent_index)>=i||n.parent!=r.tree[n.parent_index].widget||n.depth!=r.tree[n.parent_index].depth+1)return false;
  if(i){const auto &parent=r.tree[n.parent_index];if((n.visible&&!parent.visible)||(n.enabled&&!parent.enabled)||n.sibling_index!=children[n.parent_index])return false;++children[n.parent_index];}
 }
 for(std::size_t i=0;i<r.tree.size();++i)if(children[i]!=static_cast<std::size_t>(r.tree[i].child_count))return false;
 return true;
}
} // namespace
bool ParseGuiWindowRequestV1(std::string_view text,GuiWindowWireRequestV1 &out) noexcept {
  try {out={};if(text.size()>16384)return false;Cursor c{text};GuiWindowWireRequestV1 parsed{};
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
    std::uint32_t bit=0;bool good=false;std::uint64_t number=0;
    if(key=="type"){bit=1;good=c.Identity("execute_step");}
    else if(key=="protocol_version"){bit=2;good=c.Number(number)&&number==1;}
    else if(key=="request_id"){bit=4;good=c.String(parsed.request_id)&&RequestId(parsed.request_id);}
    else if(key=="step"){bit=8;good=c.Identity(kGuiWindowStepV1);}
    else if(key=="expected_revision"){bit=16;good=c.Number(number)&&number==0;}
    else if(key=="gui_window"){bit=32;good=Claim(c,parsed.owner_request);}
    else if(key=="arguments"){bit=64;good=c.Take('{')&&c.Take('}');}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  c.Space();if(seen!=127||c.pos!=text.size())return false;out=std::move(parsed);return true;}catch(...){out={};return false;}
}
bool GuiWindowRouteEnabledV1([[maybe_unused]]const game::AdapterDescriptor &d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
  return game::IsCk3_121003Core26785313Descriptor(d)&&
      std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kCoreFrameCapabilityV1)!=d.capabilities.end();
#else
  return false;
#endif
}
std::string SerializeGuiWindowCommandResultV1(std::string_view id,const ReadonlyObservation &in,const game::AdapterDescriptor&d) {
 const bool ready=GuiWindowRouteEnabledV1(d)&&Available(in);
 ck3_1210::CoreFrameObservationV1 core{};core.application_main_observed=!in.offline_fixture&&in.main_owner_observed;
 const std::string_view reason=!GuiWindowRouteEnabledV1(d)?"gui_window_profile_unavailable":in.offline_fixture?"offline_fixture_has_no_application_main":
  !in.main_owner_observed?"application_main_not_observed":!in.unavailable_reason.empty()?in.unavailable_reason:"exact_gui_window_source_unavailable";
 if(ready){core.core_available=true;core.core=in.core;core.unavailable_reason={};}else core.unavailable_reason=reason;
 std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(out,id);
 out+=",\"ok\":true,\"result\":{\"step\":";String(out,kGuiWindowStepV1);out+=",\"schema\":";String(out,kGuiWindowSchemaV1);
 out+=",\"game_version\":";String(out,kGameVersion);out+=",\"executable_sha256\":";String(out,kExecutableSha256);
 out+=",\"adapter_id\":";String(out,kAdapterId);out+=",\"backend\":";String(out,kGuiWindowBackendV1);
 out+=",\"status\":";String(out,ready?"partial":"unavailable");
 const auto boolean=[&](const char*key,bool b){out+=",\"";out+=key;out+="\":";out+=b?"true":"false";};
 boolean("tree_source_available",ready);boolean("window_available",ready&&in.gui_window->window_found);
 boolean("application_main_observed",core.application_main_observed);boolean("source_abi_pins_verified",ready);
 boolean("addresses_redacted",true);boolean("complete_snapshot",false);boolean("complete_gui_tree",false);
 boolean("complete_window_tree",ready&&in.gui_window->window_found);boolean("native_findtop_semantics_verified",false);
 boolean("activation_available",false);boolean("control_actions_available",false);
 out+=",\"core_frame\":"+ck3_1210::SerializeCoreFrameV1(core,ck3_1210::CoreFrameReadonlySourceV1::hotfix26785313);
 out+=",\"requested_window\":";if(ready)String(out,in.gui_window->requested_name);else out+="null";
 out+=",\"top_level\":";
 if(ready) {
  const auto &r=*in.gui_window;out+='[';bool first=true;
  const bool focused=r.requested_name=="zg361_scoreboard_window";
  const std::span<const GuiWindowNodeV1>public_top=focused?std::span<const GuiWindowNodeV1>(r.tree).subspan(r.window_found?1:0,r.window_found?1:0):std::span<const GuiWindowNodeV1>(r.top_level);
  for(const auto&n:public_top){if(!first)out+=',';first=false;out+="{\"name\":";String(out,n.name);out+=",\"visible\":";out+=n.visible?"true":"false";out+=",\"enabled\":";out+=n.enabled?"true":"false";out+='}';}out+=']';
  out+=",\"window\":";
  if(r.window_found) {
   out+="{\"nodes\":[";first=true;
   const std::size_t begin=focused?1:0;
   for(std::size_t i=begin;i<r.tree.size();++i) {
    const auto&n=r.tree[i];if(!first)out+=',';first=false;out+="{\"node_id\":";String(out,std::to_string(i-begin));
    out+=",\"parent_id\":";if(i==begin)out+="null";else String(out,std::to_string(n.parent_index-static_cast<std::int32_t>(begin)));
    out+=",\"sibling_index\":"+std::to_string(focused&&i==begin?0:n.sibling_index)+",\"depth\":"+std::to_string(n.depth-(focused?r.tree[begin].depth:0))+",\"name\":";String(out,n.name);
    out+=",\"child_count\":"+std::to_string(n.child_count)+",\"visible\":";out+=n.visible?"true":"false";out+=",\"enabled\":";out+=n.enabled?"true":"false";out+='}';
   }out+="]}";
  }else out+="null";
  out+=",\"owner_witness\":{\"connection_generation\":";String(out,std::to_string(r.connection_generation));
  out+=",\"ticket_sequence\":";String(out,std::to_string(r.ticket_sequence));out+=",\"pump_epoch\":";String(out,std::to_string(r.pump_epoch));out+=",\"thread_id\":"+std::to_string(r.owner_thread_id)+'}';
 } else out+="null,\"window\":null,\"owner_witness\":null";
 out+=",\"unavailable_reason\":";if(ready)out+="null";else String(out,reason);out+="}}";return out;
}
} // namespace

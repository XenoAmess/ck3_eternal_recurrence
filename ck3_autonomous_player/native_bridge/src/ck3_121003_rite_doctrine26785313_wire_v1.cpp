#include "xar_bridge/ck3_121003_rite_doctrine26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <charconv>
namespace xar::ck3_121003::build26785313 { namespace {
struct Cursor {
 std::string_view text;std::size_t pos=0;
 void Space() noexcept {while(pos<text.size()&&(text[pos]==' '||text[pos]=='\r'||text[pos]=='\n'||text[pos]=='\t'))++pos;}
 bool Take(char ch) noexcept {Space();if(pos==text.size()||text[pos]!=ch)return false;++pos;return true;}
 bool String(std::string_view&out) noexcept {
  if(!Take('"'))return false;const auto start=pos;
  while(pos<text.size()&&text[pos]!='"') {const auto c=static_cast<unsigned char>(text[pos]);if(c<0x20||c>=0x7f||c=='\\'||pos-start>=192)return false;++pos;}
  if(pos==text.size())return false;out=text.substr(start,pos++-start);return true;
 }
 template<class T>bool Number(T&out) noexcept {
  Space();const auto start=pos;if(pos<text.size()&&text[pos]=='-')++pos;const auto digits=pos;
  while(pos<text.size()&&text[pos]>='0'&&text[pos]<='9')++pos;
  if(pos==digits||(pos-digits>1&&text[digits]=='0'))return false;T value{};
  const auto parsed=std::from_chars(text.data()+start,text.data()+pos,value);
  if(parsed.ec!=std::errc{}||parsed.ptr!=text.data()+pos||(text[start]=='-'&&value==0))return false;out=value;return true;
 }
 bool UnsignedString(std::uint64_t&out) noexcept {
  std::string_view value;if(!String(value)||value.empty()||value.size()>20||(value.size()>1&&value[0]=='0'))return false;
  for(const char ch:value)if(ch<'0'||ch>'9')return false;
  const auto parsed=std::from_chars(value.data(),value.data()+value.size(),out);
  return parsed.ec==std::errc{}&&parsed.ptr==value.data()+value.size();
 }
 bool Boolean(bool&out) noexcept {
  Space();if(text.substr(pos,4)=="true"){pos+=4;out=true;return true;}
  if(text.substr(pos,5)=="false"){pos+=5;out=false;return true;}return false;
 }
 bool Identity(std::string_view expected,bool hash=false) noexcept {
  std::string_view value;if(!String(value)||value.size()!=expected.size())return false;
  for(std::size_t i=0;i<value.size();++i){auto ch=value[i];if(hash&&ch>='a'&&ch<='f')ch=static_cast<char>(ch-'a'+'A');if(ch!=expected[i])return false;}return true;
 }
};
bool Id(std::string_view id) noexcept {
 if(id.empty()||id.size()>96)return false;
 for(const char ch:id)if(!((ch>='0'&&ch<='9')||(ch>='a'&&ch<='z')||(ch>='A'&&ch<='Z')||ch=='-'||ch=='_'||ch=='.'))return false;
 return true;
}
bool CoreShape(const ck3_1210::CoreSnapshotPrefix&p) noexcept {
 return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&
  p.has_played_character&&p.played_character_id!=0&&p.played_character_id!=-1&&p.played_character_alive;
}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p) noexcept {
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')) {
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
  unsigned bit=0;bool good=false;
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
 return seen==255&&CoreShape(p);
}
bool Action(Cursor&c,RiteDoctrineAction267V1&action) noexcept {
 std::string_view value;if(!c.String(value))return false;
 if(value=="query")action=RiteDoctrineAction267V1::query;
 else if(value=="open_dynastic_category")action=RiteDoctrineAction267V1::open_dynastic_category;
 else if(value=="select_dynastic")action=RiteDoctrineAction267V1::select_dynastic;
 else if(value=="confirm_edit")action=RiteDoctrineAction267V1::confirm_edit;
 else return false;return true;
}
bool Claim(Cursor&c,RiteDoctrineRequest267V1&r) noexcept {
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')) {
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
  unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kRiteDoctrineSchema267V1);}
  else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
  else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
  else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
  else if(key=="backend"){bit=16;good=c.Identity(kGuiWindowBackendV1);}
  else if(key=="action"){bit=32;good=Action(c,r.action);}
  else if(key=="deadline_unix_ms"){bit=64;good=c.Number(r.window.deadline_unix_ms)&&r.window.deadline_unix_ms>0;}
  else if(key=="expected_core"){bit=128;good=Core(c,r.window.expected_core);}
  else if(key=="expected_source_rite_id"){bit=256;good=c.Number(r.expected_source_rite_id)&&r.expected_source_rite_id!=0xFFFFFFFFU;}
  else if(key=="provider_generation"){bit=512;good=c.UnsignedString(r.provider_generation);}
  else if(key=="query_sequence"){bit=1024;good=c.UnsignedString(r.query_sequence);}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }
 return seen==2047;
}
void String(std::string&out,std::string_view value) {
 constexpr char hex[]="0123456789abcdef";out+='"';
 for(const unsigned char ch:value) {
  if(ch=='"')out+="\\\"";else if(ch=='\\')out+="\\\\";
  else if(ch<0x20){out+="\\u00";out+=hex[ch>>4];out+=hex[ch&15];}else out+=static_cast<char>(ch);
 }out+='"';
}
const char*ActionName(RiteDoctrineAction267V1 a) noexcept {
 switch(a){case RiteDoctrineAction267V1::query:return "query";case RiteDoctrineAction267V1::open_dynastic_category:return "open_dynastic_category";
 case RiteDoctrineAction267V1::select_dynastic:return "select_dynastic";case RiteDoctrineAction267V1::confirm_edit:return "confirm_edit";default:return "invalid";}
}
const char*StatusName(RiteDoctrineStatus267V1 s) noexcept {
 switch(s){case RiteDoctrineStatus267V1::available:return "available";case RiteDoctrineStatus267V1::expired:return "expired";
 case RiteDoctrineStatus267V1::stale_core:return "stale_core";case RiteDoctrineStatus267V1::source_changed:return "source_changed";
 case RiteDoctrineStatus267V1::query_consumed:return "query_consumed";case RiteDoctrineStatus267V1::claim_consumed:return "claim_consumed";
 case RiteDoctrineStatus267V1::capacity_exhausted:return "capacity_exhausted";case RiteDoctrineStatus267V1::prerequisite_rejected:return "prerequisite_rejected";
 case RiteDoctrineStatus267V1::category_opened:return "category_opened";case RiteDoctrineStatus267V1::draft_selected:return "draft_selected";
 case RiteDoctrineStatus267V1::confirmation_dispatched:return "confirmation_dispatched";case RiteDoctrineStatus267V1::indeterminate:return "indeterminate";
 default:return "unavailable";}
}
bool FactsAvailable(const RiteDoctrineFacts267V1&f) noexcept {
 return f.core_before_verified&&f.source_rite_verified&&f.source_rite_id!=0xFFFFFFFFU&&CoreShape(f.core)&&
  f.connection_generation&&f.ticket_sequence&&f.pump_epoch&&f.thread_id;
}
} // namespace
bool RiteDoctrineRequestShape267V1(const RiteDoctrineRequest267V1&r) noexcept {
 if(!Id(r.id())||r.expected_source_rite_id==0xFFFFFFFFU||!r.window.deadline_unix_ms||
    r.window.window_name!="rite_creation_window"||!CoreShape(r.window.expected_core))return false;
 if(r.action==RiteDoctrineAction267V1::query)return !r.provider_generation&&!r.query_sequence;
 return r.provider_generation&&r.query_sequence&&
  (r.action==RiteDoctrineAction267V1::open_dynastic_category||r.action==RiteDoctrineAction267V1::select_dynastic||r.action==RiteDoctrineAction267V1::confirm_edit);
}
bool ParseRiteDoctrineRequest267V1(std::string_view text,RiteDoctrineRequest267V1&out) noexcept {
 try {
  out={};if(text.size()>16384)return false;Cursor c{text};RiteDoctrineRequest267V1 parsed;
  if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
  while(!c.Take('}')) {
   if(!first&&!c.Take(','))return false;first=false;std::string_view key,id;
   if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
   if(key=="type"){bit=1;good=c.Identity("execute_step");}
   else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}
   else if(key=="request_id"){bit=4;good=c.String(id)&&Id(id);if(good){std::copy(id.begin(),id.end(),parsed.request_id.begin());parsed.request_id_size=static_cast<std::uint8_t>(id.size());}}
   else if(key=="step"){bit=8;good=c.Identity(kRiteDoctrineStep267V1);}
   else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}
   else if(key=="rite_doctrine"){bit=32;good=Claim(c,parsed);}
   else if(key=="arguments"){bit=64;good=c.Take('{')&&c.Take('}');}
   if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  c.Space();parsed.window.window_name="rite_creation_window";
  if(seen!=127||c.pos!=text.size()||!RiteDoctrineRequestShape267V1(parsed))return false;
  out=std::move(parsed);return true;
 }catch(...){out={};return false;}
}
std::string SerializeRiteDoctrineResult267V1(std::string_view id,const RiteDoctrineResult267V1&r) {
 using S=RiteDoctrineStatus267V1;using A=RiteDoctrineAction267V1;
 const bool facts=FactsAvailable(r.facts),claimed=r.effect_attempted&&r.native_returned&&r.claim_sequence>0&&facts;
 bool coherent=false;
 if(r.status==S::available)coherent=r.action==A::query&&!r.effect_attempted&&!r.claim_sequence&&facts&&r.provider_generation&&r.query_sequence;
 else if(r.status==S::category_opened)coherent=r.action==A::open_dynastic_category&&claimed&&r.facts.category_available;
 else if(r.status==S::draft_selected)coherent=r.action==A::select_dynastic&&claimed&&r.facts.target_available&&
  r.facts.should_display_evaluated&&r.facts.should_display&&r.facts.can_pick_evaluated&&r.facts.can_pick&&
  r.facts.knowledge_evaluated&&r.facts.known_doctrine&&r.post_selected_evaluated&&r.post_selected;
 else if(r.status==S::confirmation_dispatched)coherent=r.action==A::confirm_edit&&claimed&&r.native_handled&&
  r.facts.can_edit_evaluated&&r.facts.can_edit&&r.facts.piety_missing_raw<=0&&r.facts.selected_evaluated&&r.facts.selected;
 const bool success_kind=r.status==S::available||r.status==S::category_opened||r.status==S::draft_selected||r.status==S::confirmation_dispatched;
 const auto status=success_kind&&!coherent?S::indeterminate:r.status;
 std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";String(out,id);
 out+=coherent?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(out,kRiteDoctrineResultSchema267V1);
 const auto field=[&](const char*key,std::string_view value){out+=",\"";out+=key;out+="\":";String(out,value);};
 const auto flag=[&](const char*key,bool value){out+=",\"";out+=key;out+="\":";out+=value?"true":"false";};
 field("game_version",kGameVersion);field("executable_sha256",kExecutableSha256);field("adapter_id",kAdapterId);field("backend",kGuiWindowBackendV1);
 field("step",kRiteDoctrineStep267V1);field("action",ActionName(r.action));field("status",StatusName(status));
 flag("facts_available",facts);flag("effect_attempted",r.effect_attempted);flag("native_returned",r.native_returned);flag("native_handled",r.native_handled);
 flag("post_selected_evaluated",r.post_selected_evaluated);flag("post_selected",r.post_selected);
 flag("addresses_redacted",true);flag("complete_snapshot",false);flag("complete_gui_tree",false);flag("physical_save_confirmed",false);flag("rite_edit_confirmed",false);
 field("group_key",kRiteDoctrineGroup267V1);field("target_key",kRiteDoctrineTarget267V1);
 field("provider_generation",std::to_string(r.provider_generation));field("query_sequence",std::to_string(r.query_sequence));field("claim_sequence",std::to_string(r.claim_sequence));
 ck3_1210::CoreFrameObservationV1 core{};core.application_main_observed=facts;core.core_available=facts;
 if(facts){core.core=r.facts.core;core.unavailable_reason={};}else core.unavailable_reason="current_rite_owner_source_unavailable";
 out+=",\"core_frame\":"+ck3_1210::SerializeCoreFrameV1(core,ck3_1210::CoreFrameReadonlySourceV1::hotfix26785313);
 out+=",\"facts\":";
 if(facts){const auto&f=r.facts;out+="{\"source_rite_id\":"+std::to_string(f.source_rite_id);
  flag("category_available",f.category_available);flag("target_available",f.target_available);
  flag("should_display_evaluated",f.should_display_evaluated);flag("should_display",f.should_display);
  flag("can_pick_evaluated",f.can_pick_evaluated);flag("can_pick",f.can_pick);
  flag("knowledge_evaluated",f.knowledge_evaluated);flag("known_doctrine",f.known_doctrine);
  flag("pam_gate_available",f.knowledge_evaluated&&f.known_doctrine);flag("pam_gate_true",f.knowledge_evaluated&&f.known_doctrine);
  flag("selected_evaluated",f.selected_evaluated);flag("selected",f.selected);
  flag("can_edit_evaluated",f.can_edit_evaluated);flag("can_edit",f.can_edit);
  field("piety_cost_raw",std::to_string(f.piety_cost_raw));field("piety_missing_signed_raw",std::to_string(f.piety_missing_raw));out+=",\"raw_scale\":100000}";
  out+=",\"owner_witness\":{\"connection_generation\":";String(out,std::to_string(f.connection_generation));
  field("ticket_sequence",std::to_string(f.ticket_sequence));field("pump_epoch",std::to_string(f.pump_epoch));out+=",\"thread_id\":"+std::to_string(f.thread_id)+'}';
 }else out+="null,\"owner_witness\":null";
 out+=",\"unavailable_reason\":";if(coherent)out+="null";else String(out,r.reason.empty()?"current_rite_action_not_verified":r.reason);
 out+="}}";return out;
}
} // namespace xar::ck3_121003::build26785313

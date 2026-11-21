#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
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
void String(std::string&out,std::string_view value) {
 constexpr char hex[]="0123456789abcdef";out+='"';
 for(const unsigned char ch:value) {
  if(ch=='"')out+="\\\"";else if(ch=='\\')out+="\\\\";
  else if(ch<0x20){out+="\\u00";out+=hex[ch>>4];out+=hex[ch&15];}else out+=static_cast<char>(ch);
 }out+='"';
}

using Action=FrontendMenuAction267V1;using Status=FrontendMenuStatus267V1;using Route=FrontendMenuRoute267V1;
const char*Name(Action a) noexcept {switch(a){case Action::query_menu:return "query_menu";case Action::quit_menu:return "quit_menu";
case Action::select_robert_1066:return "select_robert_1066";case Action::start_robert_1066:return "start_robert_1066";
case Action::open_bookmarks:return "open_bookmarks";case Action::select_1066_bookmark:return "select_1066_bookmark";}return "invalid";}
const char*Name(Status a) noexcept {switch(a){case Status::unavailable:return "unavailable";case Status::available:return "available";
case Status::expired:return "expired";case Status::source_changed:return "source_changed";case Status::query_consumed:return "query_consumed";
case Status::claim_consumed:return "claim_consumed";case Status::capacity_exhausted:return "capacity_exhausted";
case Status::exit_requested:return "exit_requested";case Status::selection_dispatched:return "selection_dispatched";
case Status::start_dispatched:return "start_dispatched";case Status::indeterminate:return "indeterminate";
case Status::bookmarks_opened:return "bookmarks_opened";case Status::bookmark_selected:return "bookmark_selected";}return "unavailable";}
const char*Name(Route a) noexcept {switch(a){case Route::main_menu:return "main_menu";case Route::bookmarks:return "bookmarks";case Route::lobby:return "lobby";default:return "unavailable";}}
bool ParseAction(Cursor&c,Action&a) noexcept {std::string_view v;if(!c.String(v))return false;
for(auto candidate:{Action::query_menu,Action::quit_menu,Action::select_robert_1066,Action::start_robert_1066,Action::open_bookmarks,Action::select_1066_bookmark})if(v==Name(candidate)){a=candidate;return true;}return false;}
bool Claim(Cursor&c,FrontendMenuRequest267V1&r) noexcept {
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;
 unsigned bit=0;bool good=false;
 if(key=="schema"){bit=1;good=c.Identity(kFrontendMenuRequestSchema267V1);}
 else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
 else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
 else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
 else if(key=="backend"){bit=16;good=c.Identity(kFrontendMenuBackend267V1);}
 else if(key=="action"){bit=32;good=ParseAction(c,r.action);}
 else if(key=="deadline_unix_ms"){bit=64;good=c.Number(r.deadline_unix_ms)&&r.deadline_unix_ms;}
 else if(key=="provider_generation"){bit=128;good=c.UnsignedString(r.provider_generation);}
 else if(key=="query_sequence"){bit=256;good=c.UnsignedString(r.query_sequence);}
 if(!good||!bit||(seen&bit))return false;seen|=bit;}
 return seen==511;
}
bool Facts(const FrontendMenuFacts267V1&f) noexcept {
 const bool robert=f.selected_bookmark_key==kFrontendRobertBookmark267V1&&f.selected_character_key==kFrontendRobertCharacter267V1;
 return (f.route==Route::main_menu||f.route==Route::bookmarks||f.route==Route::lobby)&&f.application_verified&&f.gui_context_verified&&f.global_root_verified&&f.route_root_visible&&f.no_world&&
 f.connection_generation&&f.ticket_sequence&&f.pump_epoch&&f.thread_id&&(!f.robert_source_verified||robert)&&(!f.start_admissible||f.robert_source_verified);
}
} // namespace
bool FrontendMenuRequestShape267V1(const FrontendMenuRequest267V1&r) noexcept {
 if(!Id(r.id())||!r.deadline_unix_ms||FrontendMenuStep267V1(r.action).empty())return false;
 return r.action==Action::query_menu?!r.provider_generation&&!r.query_sequence:r.provider_generation&&r.query_sequence;
}
bool ParseFrontendMenuRequest267V1(std::string_view text,FrontendMenuRequest267V1&out) noexcept {
 try {out={};if(text.size()>16384)return false;Cursor c{text};FrontendMenuRequest267V1 parsed;std::string_view step;
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,id;std::uint64_t n=0;
 if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
 if(key=="type"){bit=1;good=c.Identity("execute_step");}
 else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}
 else if(key=="request_id"){bit=4;good=c.String(id)&&Id(id);if(good){std::copy(id.begin(),id.end(),parsed.request_id.begin());parsed.request_id_size=static_cast<std::uint8_t>(id.size());}}
 else if(key=="step"){bit=8;good=c.String(step);}
 else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}
 else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}
 else if(key=="frontend_menu"){bit=64;good=Claim(c,parsed);}
 if(!good||!bit||(seen&bit))return false;seen|=bit;}
 c.Space();if(seen!=127||c.pos!=text.size()||!FrontendMenuRequestShape267V1(parsed)||step!=FrontendMenuStep267V1(parsed.action))return false;out=std::move(parsed);return true;
 }catch(...){out={};return false;}
}
std::string SerializeFrontendMenuResult267V1(std::string_view id,const FrontendMenuResult267V1&r) {
 const bool facts=Facts(r.facts),lease=r.provider_generation&&r.query_sequence;
 const bool claimed=facts&&lease&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 bool coherent=false,success=false;
 switch(r.status){case Status::available:success=true;coherent=r.action==Action::query_menu&&facts&&lease&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned&&!r.post_selection_verified;break;
 case Status::exit_requested:success=true;coherent=r.action==Action::quit_menu&&claimed&&!r.post_selection_verified;break;
 case Status::bookmarks_opened:success=true;coherent=r.action==Action::open_bookmarks&&claimed&&!r.post_selection_verified&&r.facts.route==Route::bookmarks;break;
 case Status::bookmark_selected:success=true;coherent=r.action==Action::select_1066_bookmark&&claimed&&!r.post_selection_verified&&r.facts.selected_bookmark_key==kFrontendRobertBookmark267V1;break;
 case Status::selection_dispatched:success=true;coherent=r.action==Action::select_robert_1066&&claimed&&r.post_selection_verified&&r.facts.robert_source_verified;break;
 case Status::start_dispatched:success=true;coherent=r.action==Action::start_robert_1066&&claimed&&!r.post_selection_verified&&r.facts.start_admissible;break;
 default:break;}
 const auto status=success&&!coherent?Status::indeterminate:r.status;
 std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";String(out,id);out+=coherent?",\"ok\":true,\"result\":{\"schema\":" : ",\"ok\":false,\"result\":{\"schema\":";String(out,kFrontendMenuResultSchema267V1);
 const auto field=[&](const char*k,std::string_view v){out+=",\"";out+=k;out+="\":";String(out,v);};
 const auto flag=[&](const char*k,bool v){out+=",\"";out+=k;out+="\":";out+=v?"true":"false";};
 const auto optional=[&](const char*k,const std::optional<std::string>&v){out+=",\"";out+=k;out+="\":";if(v)String(out,*v);else out+="null";};
 field("game_version",kGameVersion);field("executable_sha256",kExecutableSha256);field("adapter_id",kAdapterId);field("backend",kFrontendMenuBackend267V1);
 field("step",FrontendMenuStep267V1(r.action));field("action",Name(r.action));field("status",Name(status));
 flag("facts_available",facts);flag("effect_attempted",r.effect_attempted);flag("native_returned",r.native_returned);flag("post_selection_verified",r.post_selection_verified);
 flag("addresses_redacted",true);flag("world_core_fabricated",false);flag("application_exit_confirmed",false);flag("game_started_confirmed",false);flag("physical_save_confirmed",false);
 field("provider_generation",std::to_string(r.provider_generation));field("query_sequence",std::to_string(r.query_sequence));field("claim_sequence",std::to_string(r.claim_sequence));
 out+=",\"source\":";
 if(facts){const auto&f=r.facts;out+="{\"route\":";String(out,Name(f.route));flag("application_verified",f.application_verified);flag("gui_context_verified",f.gui_context_verified);flag("global_root_verified",f.global_root_verified);flag("route_root_visible",f.route_root_visible);flag("no_world",f.no_world);optional("selected_bookmark_key",f.selected_bookmark_key);optional("selected_character_key",f.selected_character_key);flag("robert_source_verified",f.robert_source_verified);flag("start_admissible",f.start_admissible);out+='}';
 out+=",\"owner_witness\":{\"connection_generation\":";String(out,std::to_string(f.connection_generation));field("ticket_sequence",std::to_string(f.ticket_sequence));field("pump_epoch",std::to_string(f.pump_epoch));out+=",\"thread_id\":"+std::to_string(f.thread_id)+'}';}
 else out+="null,\"owner_witness\":null";
 out+=",\"unavailable_reason\":";if(coherent)out+="null";else String(out,r.reason.empty()?"current_frontend_source_not_qualified":r.reason);out+="}}";return out;
}
} // namespace xar::ck3_121003::build26785313

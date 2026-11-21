#include "xar_bridge/ck3_121003_succession_lifecycle26785313_v1.hpp"
#include <algorithm>
#include <charconv>
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
bool Id(std::string_view value) noexcept {
  if(value.empty()||value.size()>96)return false;
  for(const char c:value)if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||
      (c>='A'&&c<='Z')||c=='-'||c=='_'||c=='.'))return false;
  return true;
}
void String(std::string&out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);
  }out+='"';
}

bool UIntText(Cursor&c,std::uint64_t&out)noexcept{std::string_view s;if(!c.String(s)||s.empty()||s.size()>20||(s.size()>1&&s[0]=='0'))return false;for(char v:s)if(v<'0'||v>'9')return false;auto p=std::from_chars(s.data(),s.data()+s.size(),out);return p.ec==std::errc{}&&p.ptr==s.data()+s.size();}
const char*Action(SuccessionAction267V1 a)noexcept{return a==SuccessionAction267V1::query_default?"query_default":"continue_default";}
const char*Step(SuccessionAction267V1 a)noexcept{return a==SuccessionAction267V1::query_default?kSuccessionQueryStep267V1:kSuccessionContinueStep267V1;}
const char*Status(SuccessionStatus267V1 s)noexcept{using S=SuccessionStatus267V1;switch(s){case S::expired:return "expired";case S::stale_source:return "stale_source";case S::claim_consumed:return "claim_consumed";case S::available:return "available";case S::dispatched:return "dispatched";case S::indeterminate:return "indeterminate";default:return "unavailable";}}
const char*Relation(SuccessionPlayerRelation267V1 r)noexcept{using T=SuccessionPlayerRelation267V1;switch(r){case T::pending_predecessor:return "pending_predecessor";case T::heir_already_assigned:return "heir_already_assigned";default:return "unassigned_during_transition";}}
bool WorldShape(const ck3_1210::CoreSnapshotPrefix&w)noexcept{return w.has_played_character?w.played_character_id!=-1:!w.played_character_alive&&w.played_character_id==-1;}
bool SourceShape(const ck3_1210::CoreSnapshotPrefix&w,const SuccessionSource267V1&s)noexcept{
 if(!w.clock.paused||s.dead_character_id==-1||s.continue_character_id==-1||s.dead_character_id==s.continue_character_id||!s.dead_character_dead||!s.continue_character_alive||!s.handler_source_verified||!s.named_root_bound||!s.window_visible||!s.window_enabled||!s.default_button_admissible||!s.default_native_route||!s.stable_two_pass_verified)return false;
 using T=SuccessionPlayerRelation267V1;
 if(s.player_relation==T::pending_predecessor)return w.has_played_character&&w.played_character_id==s.dead_character_id&&!w.played_character_alive;
 if(s.player_relation==T::heir_already_assigned)return w.has_played_character&&w.played_character_id==s.continue_character_id&&w.played_character_alive;
 return !w.has_played_character&&w.played_character_id==-1&&!w.played_character_alive;
}
bool Claim(Cursor&c,SuccessionRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kSuccessionRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kSuccessionBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(value=="query_default")q.action=SuccessionAction267V1::query_default;else if(value=="continue_default")q.action=SuccessionAction267V1::continue_default;else good=false;}
  else if(key=="provider_generation"){bit=64;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=128;good=UIntText(c,q.query_sequence);}else if(key=="expected_dead_character_id"){bit=256;good=c.Number(q.expected_dead_character_id);}else if(key=="expected_continue_character_id"){bit=512;good=c.Number(q.expected_continue_character_id);}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }return seen==1023;
}
}
bool SuccessionRequestShape267V1(const SuccessionRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms)return false;
 if(q.action==SuccessionAction267V1::query_default)return !q.provider_generation&&!q.query_sequence&&q.expected_dead_character_id==-1&&q.expected_continue_character_id==-1;
 return q.provider_generation&&q.query_sequence&&q.expected_dead_character_id!=-1&&q.expected_continue_character_id!=-1&&q.expected_dead_character_id!=q.expected_continue_character_id;
}
bool ParseSuccessionRequest267V1(std::string_view text,SuccessionRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};SuccessionRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t number=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(number)&&number==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}
  else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(number)&&number==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="succession_lifecycle"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||step!=Step(q.action)||!SuccessionRequestShape267V1(q))return false;out=q;return true;
}
std::string SerializeSuccessionResult267V1(std::string_view id,const SuccessionResult267V1&r){
 const bool world=r.world_available&&WorldShape(r.world)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=r.source_available&&world&&r.source.has_value()&&SourceShape(r.world,*r.source);
 const bool query=r.action==SuccessionAction267V1::query_default&&r.status==SuccessionStatus267V1::available&&source&&r.provider_generation&&r.query_sequence&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned;
 const bool dispatched=r.action==SuccessionAction267V1::continue_default&&r.status==SuccessionStatus267V1::dispatched&&source&&r.provider_generation&&r.query_sequence&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool ok=query||dispatched;auto status=r.status;if(!ok&&(status==SuccessionStatus267V1::available||status==SuccessionStatus267V1::dispatched))status=SuccessionStatus267V1::indeterminate;
 std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";String(out,id);out+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(out,kSuccessionResultSchema267V1);
 const auto str=[&](const char*k,std::string_view v){out+=",\"";out+=k;out+="\":";String(out,v);};const auto flag=[&](const char*k,bool v){out+=",\"";out+=k;out+=v?"\":true":"\":false";};
 str("game_version",kGameVersion);str("executable_sha256",kExecutableSha256);str("adapter_id",kAdapterId);str("backend",kSuccessionBackend267V1);str("step",Step(r.action));str("action",Action(r.action));str("status",Status(status));flag("source_available",source);flag("effect_attempted",r.effect_attempted);flag("native_returned",r.native_returned);flag("native_handled",false);str("provider_generation",std::to_string(r.provider_generation));str("query_sequence",std::to_string(r.query_sequence));str("claim_sequence",std::to_string(r.claim_sequence));
 out+=",\"world_before\":";
 if(world){out+="{\"schema\":";String(out,kSuccessionWorldSchema267V1);const auto&w=r.world;out+=",\"date_raw\":"+std::to_string(w.clock.date_raw)+",\"speed\":"+std::to_string(w.clock.speed);flag("paused",w.clock.paused);out+=",\"local_player_id\":"+std::to_string(w.local_player_id);flag("map_ready",w.map_ready);flag("has_played_character",w.has_played_character);out+=",\"played_character_id\":"+std::to_string(w.played_character_id);flag("played_character_alive",w.played_character_alive);out+='}';}else out+="null";
 out+=",\"source\":";
 if(source){const auto&s=*r.source;out+="{\"schema\":";String(out,kSuccessionSourceSchema267V1);out+=",\"dead_character_id\":"+std::to_string(s.dead_character_id)+",\"continue_character_id\":"+std::to_string(s.continue_character_id);str("player_relation",Relation(s.player_relation));flag("dead_character_dead",s.dead_character_dead);flag("continue_character_alive",s.continue_character_alive);flag("handler_source_verified",s.handler_source_verified);flag("named_root_bound",s.named_root_bound);flag("window_visible",s.window_visible);flag("window_enabled",s.window_enabled);flag("default_button_admissible",s.default_button_admissible);flag("default_native_route",s.default_native_route);flag("stable_two_pass_verified",s.stable_two_pass_verified);out+='}';}else out+="null";
 out+=",\"owner_witness\":";
 if(world){out+="{\"connection_generation\":";String(out,std::to_string(r.connection_generation));str("ticket_sequence",std::to_string(r.ticket_sequence));str("pump_epoch",std::to_string(r.pump_epoch));out+=",\"thread_id\":"+std::to_string(r.thread_id)+'}';}else out+="null";
 flag("addresses_redacted",true);flag("continuation_confirmed",false);flag("physical_save_confirmed",false);out+=",\"unavailable_reason\":";if(ok)out+="null";else String(out,r.reason.empty()?"current_succession_original_source_unavailable":r.reason);out+="}}";return out;
}
}

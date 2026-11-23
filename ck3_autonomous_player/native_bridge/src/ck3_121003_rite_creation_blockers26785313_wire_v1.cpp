#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_v1.hpp"
#include <algorithm>
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


bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}

bool Claim(Cursor&c,RiteBlockersRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="schema"){bit=1;good=c.Identity(kRiteBlockersRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kRiteBlockersBackend267V1);}else if(k=="action"){bit=32;good=c.Identity("query_blockers");}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="expected_source_rite_id"){bit=128;good=c.Number(q.expected_source_rite_id)&&q.expected_source_rite_id!=0xFFFFFFFFU;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255;
}
const char*Status(RiteBlockersStatus267V1 s)noexcept{switch(s){case RiteBlockersStatus267V1::available:return "available";case RiteBlockersStatus267V1::expired:return "expired";case RiteBlockersStatus267V1::stale_source:return "stale_source";case RiteBlockersStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}};
bool Utf8(std::string_view text)noexcept{if(text.size()>16384)return false;for(std::size_t i=0;i<text.size();){const auto c=static_cast<unsigned char>(text[i++]);std::uint32_t cp=0;unsigned n=0;if(c<0x80)cp=c;else if(c>=0xC2&&c<=0xDF){cp=c&31;n=1;}else if(c>=0xE0&&c<=0xEF){cp=c&15;n=2;}else if(c>=0xF0&&c<=0xF4){cp=c&7;n=3;}else return false;if(i+n>text.size())return false;for(unsigned j=0;j<n;++j){const auto v=static_cast<unsigned char>(text[i++]);if((v&0xC0)!=0x80)return false;cp=(cp<<6)|(v&63);}if((n==1&&cp<0x80)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF))return false;}return true;}
bool Shape(const RiteBlockersSource267V1&s,const ck3_1210::CoreSnapshotPrefix&f)noexcept{return s.source_rite_id!=0xFFFFFFFFU&&s.actor_id!=-1&&s.actor_id==f.played_character_id&&s.sampled_twice&&Utf8(s.blockers_text);}

}
bool RiteBlockersRequestShape267V1(const RiteBlockersRequest267V1&q)noexcept{return Id(q.id())&&q.deadline_unix_ms&&Prefix(q.expected)&&q.expected_source_rite_id!=0xFFFFFFFFU;}
bool ParseRiteBlockersRequest267V1(std::string_view text,RiteBlockersRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};RiteBlockersRequest267V1 q;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;std::uint64_t n=0;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(k=="request_id"){bit=4;good=c.String(v)&&Id(v);if(good){std::copy(v.begin(),v.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(v.size());}}else if(k=="step"){bit=8;good=c.Identity(kRiteBlockersStep267V1);}else if(k=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(k=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(k=="rite_creation_blockers"){bit=64;good=Claim(c,q);}else if(k=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!RiteBlockersRequestShape267V1(q))return false;out=q;return true;
}
std::string SerializeRiteBlockersResult267V1(std::string_view id,const RiteBlockersResult267V1&r){
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=r.status==RiteBlockersStatus267V1::available&&facts&&r.cleanup_known&&r.source_available&&r.source&&Shape(*r.source,r.facts);
 const bool ok=r.status==RiteBlockersStatus267V1::available&&source&&r.provider_generation&&r.query_sequence;
 auto status=r.status;if(!r.cleanup_known||(!ok&&status==RiteBlockersStatus267V1::available))status=RiteBlockersStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kRiteBlockersResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kRiteBlockersBackend267V1);j.str("action","query_blockers");j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",ok?r.provider_generation:0);j.u64("query_sequence",ok?r.query_sequence:0);j.u64("claim_sequence",0);j.flag("effect_attempted",false);j.flag("native_returned",false);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(ok){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kRiteBlockersSourceSchema267V1);j.num("source_rite_id",s.source_rite_id);j.num("actor_id",s.actor_id);j.flag("is_creating",s.is_creating);j.flag("native_can_create",s.native_can_create);j.str("blockers_text",s.blockers_text);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.flag("sampled_twice",s.sampled_twice);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"rite_creation_blockers_actual_source_unavailable":r.reason);j.data+="}}";return j.data;
}
}

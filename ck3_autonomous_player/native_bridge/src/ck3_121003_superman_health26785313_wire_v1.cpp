#include "xar_bridge/ck3_121003_superman_health26785313_v1.hpp"
#include <algorithm>
#include <charconv>
#include <unordered_set>
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

bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}
bool Claim(Cursor&c,SupermanHealthRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kSupermanHealthRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kSupermanHealthBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(good&&value=="query_health")q.action=SupermanHealthAction267V1::query_health;else if(good&&value=="choose_known")q.action=SupermanHealthAction267V1::choose_known;else good=false;}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=256;good=UIntText(c,q.query_sequence);}
  else if(key=="phase"){bit=512;good=c.String(value);if(value=="baseline")q.phase=SupermanHealthPhase267V1::baseline;else if(value=="completed")q.phase=SupermanHealthPhase267V1::completed;else good=false;}
   if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==1023;
}
const char*Status(SupermanHealthStatus267V1 s)noexcept{switch(s){case SupermanHealthStatus267V1::available:return "available";case SupermanHealthStatus267V1::known_choice_dispatched:return "known_choice_dispatched";case SupermanHealthStatus267V1::expired:return "expired";case SupermanHealthStatus267V1::stale_source:return "stale_source";case SupermanHealthStatus267V1::claim_consumed:return "claim_consumed";case SupermanHealthStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view s){key(k);String(data,s);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t n){key(k);data+=std::to_string(n);}
 void u64(const char*k,std::uint64_t n){str(k,std::to_string(n));}
 void nullable(const char*k,const std::optional<std::string>&s){key(k);if(s)String(data,*s);else data+="null";}
 void nullable(const char*k,const std::optional<std::int32_t>&n){key(k);data+=n?std::to_string(*n):"null";}
};
}

bool SupermanHealthRequestShape267V1(const SupermanHealthRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||static_cast<unsigned>(q.action)>1||static_cast<unsigned>(q.phase)>1)return false;
 return q.action==SupermanHealthAction267V1::query_health?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence);
}
bool ParseSupermanHealthRequest267V1(std::string_view text,SupermanHealthRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};SupermanHealthRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="superman_health"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!SupermanHealthRequestShape267V1(q)||step!=kSupermanHealthSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}

namespace {
const char*Phase(SupermanHealthPhase267V1 p)noexcept{return p==SupermanHealthPhase267V1::completed?"completed":"baseline";}
bool Text(const std::string&s)noexcept{return s.size()<=16384;}
bool SourceShape(const SupermanHealthSource267V1&s,const ck3_1210::CoreSnapshotPrefix&core)noexcept{
 if(static_cast<unsigned>(s.phase)>1||!s.fixture_state_available||s.reference_count!=40||s.characters.size()!=40||!s.event_census_complete||s.named_root_count<0||s.named_root_count>32)return false;
 std::unordered_set<std::int32_t>ids;
 for(std::size_t n=0;n<40;++n){const auto&r=s.characters[n];if(r.case_key!=kSupermanHealthCases267V1[n/2]||r.role!=(n%2?"donor":"receiver")||r.character_id==-1||!ids.insert(r.character_id).second)return false;}
 if(s.characters.front().character_id!=core.played_character_id)return false;
 if(!s.event_found)return !s.named_root_bound&&!s.window_visible&&!s.window_enabled&&!s.instance_id&&!s.recipient_character_id&&!s.definition_key&&!s.opening&&!s.description&&!s.authored_option_count&&s.options.empty()&&!s.native_choice_admissible;
 const bool baseline=s.phase==SupermanHealthPhase267V1::baseline;
 if(!s.named_root_bound||s.named_root_count<1||!s.instance_id||*s.instance_id<=0||!s.recipient_character_id||*s.recipient_character_id!=core.played_character_id||s.definition_key!=(baseline?"sxat.2":"sxat.4")||!s.opening||!Text(*s.opening)||!s.description||!Text(*s.description)||!s.authored_option_count||*s.authored_option_count<0||*s.authored_option_count>64||s.options.size()>64)return false;
 std::unordered_set<std::int32_t>indices;
 for(const auto&o:s.options){if(o.authored_option_index<0||o.authored_option_index>=*s.authored_option_count||!indices.insert(o.authored_option_index).second||!Text(o.text)||!Text(o.disabled_reason))return false;if(o.source_bound_option_key&&(o.source_bound_option_key!=(baseline?"sxat_health_begin":"sxat_health_done_close")||*s.authored_option_count!=1||s.options.size()!=1||o.authored_option_index!=0))return false;}
 return !s.native_choice_admissible||(s.window_visible&&s.window_enabled&&*s.authored_option_count==1&&s.options.size()==1&&s.options[0].authored_option_index==0&&s.options[0].native_can_select&&s.options[0].source_bound_option_key.has_value()&&(baseline?s.baseline_ready_raw:s.matrix_done_raw)==100000);
}
void Raw(Json&j,const char*k,const std::optional<std::int64_t>&v){j.key(k);if(v)String(j.data,std::to_string(*v));else j.data+="null";}
}

std::string SerializeSupermanHealthResult267V1(std::string_view id,const SupermanHealthResult267V1&r){
 const auto index=static_cast<unsigned>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&SourceShape(*r.source,r.facts)&&r.source->phase==r.phase;
 const bool lease=r.provider_generation&&r.query_sequence;
 const bool read=index==0&&r.status==SupermanHealthStatus267V1::available&&source&&lease&&!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const bool dispatched=index==1&&r.status==SupermanHealthStatus267V1::known_choice_dispatched&&source&&lease&&r.source->native_choice_admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool ok=read||dispatched;auto status=r.status;if(!ok&&(status==SupermanHealthStatus267V1::available||status==SupermanHealthStatus267V1::known_choice_dispatched))status=SupermanHealthStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kSupermanHealthResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kSupermanHealthBackend267V1);j.str("action",index==1?"choose_known":"query_health");j.str("phase",Phase(r.phase));j.str("status",Status(status));j.flag("source_available",source);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kSupermanHealthSourceSchema267V1);j.str("phase",Phase(s.phase));j.flag("fixture_state_available",s.fixture_state_available);Raw(j,"baseline_ready_raw",s.baseline_ready_raw);Raw(j,"matrix_done_raw",s.matrix_done_raw);j.num("reference_count",s.reference_count);j.key("characters");j.data+='[';
  for(std::size_t n=0;n<s.characters.size();++n){if(n)j.data+=',';const auto&v=s.characters[n];j.data+="{\"case_key\":";String(j.data,v.case_key);j.str("role",v.role);j.num("character_id",v.character_id);j.key("values");j.data+='{';for(std::size_t m=0;m<14;++m){if(m)j.data+=',';String(j.data,kSupermanHealthValueNames267V1[m]);j.data+=':';String(j.data,std::to_string(v.values[m]));}j.data+="}}";}j.data+=']';
  j.flag("event_census_complete",s.event_census_complete);j.num("named_root_count",s.named_root_count);j.flag("event_found",s.event_found);j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.nullable("instance_id",s.instance_id);j.nullable("recipient_character_id",s.recipient_character_id);j.nullable("definition_key",s.definition_key);j.nullable("opening",s.opening);j.nullable("description",s.description);j.nullable("authored_option_count",s.authored_option_count);j.key("options");j.data+='[';
  for(std::size_t n=0;n<s.options.size();++n){if(n)j.data+=',';const auto&o=s.options[n];j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.flag("native_can_select",o.native_can_select);j.nullable("source_bound_option_key",o.source_bound_option_key);j.data+='}';}j.data+=']';j.flag("native_choice_admissible",s.native_choice_admissible);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("event_closed",false);j.flag("health_changed",false);j.flag("trait_UI_rendered",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_superman_health_source_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace

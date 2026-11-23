#include "xar_bridge/ck3_121003_ccc_event26785313_v1.hpp"
#include <algorithm>
#include <charconv>
#include <unordered_set>
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


bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.date_raw>0&&p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}

bool OptionalId(Cursor&c,std::optional<std::int32_t>&out)noexcept{c.Space();if(c.text.substr(c.pos,4)=="null"){c.pos+=4;out.reset();return true;}std::int32_t v=0;if(!c.Number(v)||v<=0)return false;out=v;return true;}
bool Claim(Cursor&c,CccEventRequest267V1&q)noexcept{if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
 if(k=="schema"){bit=1;good=c.Identity(kCccEventRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kCccEventBackend267V1);}else if(k=="action"){bit=32;good=c.String(v)&&(v=="query"||v=="select_tier_four"||v=="select_temporary_cancel");if(good)q.action=v=="query"?CccEventAction267V1::query:v=="select_tier_four"?CccEventAction267V1::select_tier_four:CccEventAction267V1::select_temporary_cancel;}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="provider_generation"){bit=128;good=c.Number(q.provider_generation);}else if(k=="query_sequence"){bit=256;good=c.Number(q.query_sequence);}else if(k=="instance_id"){bit=512;good=OptionalId(c,q.instance_id);}if(!bit||!good||(seen&bit))return false;seen|=bit;}return seen==1023;}
const char*Action(CccEventAction267V1 a)noexcept{return a==CccEventAction267V1::query?"query":a==CccEventAction267V1::select_tier_four?"select_tier_four":a==CccEventAction267V1::select_temporary_cancel?"select_temporary_cancel":"invalid";}
const char*Status(CccEventStatus267V1 s)noexcept{switch(s){case CccEventStatus267V1::available:return "available";case CccEventStatus267V1::selection_dispatched:return "selection_dispatched";case CccEventStatus267V1::expired:return "expired";case CccEventStatus267V1::stale_source:return "stale_source";case CccEventStatus267V1::claim_consumed:return "claim_consumed";case CccEventStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}void optional(const char*k,const std::optional<std::string>&v){key(k);if(v)String(data,*v);else data+="null";}};
bool Utf8(std::string_view text)noexcept{if(text.size()>16384||text.find('\0')!=std::string_view::npos)return false;for(std::size_t i=0;i<text.size();){const auto c=static_cast<unsigned char>(text[i++]);std::uint32_t cp=0;unsigned n=0;if(c<0x80)cp=c;else if(c>=0xC2&&c<=0xDF){cp=c&31;n=1;}else if(c>=0xE0&&c<=0xEF){cp=c&15;n=2;}else if(c>=0xF0&&c<=0xF4){cp=c&7;n=3;}else return false;if(i+n>text.size())return false;for(unsigned j=0;j<n;++j){const auto v=static_cast<unsigned char>(text[i++]);if((v&0xC0)!=0x80)return false;cp=(cp<<6)|(v&63);}if((n==1&&cp<0x80)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF))return false;}return true;}
bool Key(std::string_view s)noexcept{if(s.empty()||s.size()>256)return false;for(char c:s)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='.'))return false;return true;}
void Census(Json&j,const LydEventSource267V1&e){j.data+="{\"census_complete\":";j.data+=e.census_complete?"true":"false";j.num("named_root_count",e.named_root_count);j.key("events");j.data+='[';bool first=true;for(const auto&r:e.events){if(!first)j.data+=',';first=false;j.data+="{\"instance_id\":"+std::to_string(r.instance_id);j.num("recipient_character_id",r.recipient_character_id);j.num("authored_option_count",r.authored_option_count);j.str("definition_key",r.definition_key);j.str("opening",r.opening);j.str("description",r.description);j.flag("named_root_bound",r.named_root_bound);j.flag("window_visible",r.window_visible);j.flag("window_enabled",r.window_enabled);j.key("options");j.data+='[';bool fo=true;for(const auto&o:r.options){if(!fo)j.data+=',';fo=false;j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.optional("source_bound_option_key",o.source_bound_option_key);j.key("permitted_role");if(o.permitted_role)String(j.data,kLydEventRoleNames267V1[static_cast<std::size_t>(*o.permitted_role)]);else j.data+="null";j.data+='}';}j.data+="]}";}j.data+="]}";}
}
bool CccEventRequestShape267V1(const CccEventRequest267V1&q)noexcept{if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected))return false;if(q.action==CccEventAction267V1::query)return !q.provider_generation&&!q.query_sequence&&!q.instance_id;if(q.action==CccEventAction267V1::select_tier_four||q.action==CccEventAction267V1::select_temporary_cancel)return q.provider_generation&&q.query_sequence&&q.instance_id&&*q.instance_id>0;return false;}
bool CccEventSourceShape267V1(const CccEventSource267V1&s)noexcept{
 LydSource267V1 source;source.kind=LydKind267V1::events;source.events=s.event_census;
 if(!s.sampled_twice||!LydPublicSourceShape267V1(source)||!s.event_census.census_complete)return false;
 for(const auto&row:s.event_census.events){if(!Utf8(row.opening)||!Utf8(row.description))return false;for(const auto&option:row.options)if(!Utf8(option.text)||!Utf8(option.disabled_reason))return false;}
 if(s.fixed_instance_id){if(*s.fixed_instance_id<=0||s.event_census.named_root_count!=1||s.event_census.events.size()!=1)return false;const auto&r=s.event_census.events[0];if(r.instance_id!=*s.fixed_instance_id||r.definition_key!=kCccEventDefinition267V1||r.authored_option_count!=6||!r.named_root_bound||!r.window_visible||!r.window_enabled)return false;}
 if(s.select_d_admissible||s.select_f_admissible){if(!s.case_bound||!s.fixed_instance_id)return false;bool d=false,f=false;for(const auto&o:s.event_census.events[0].options){if(o.authored_option_index==3)d=o.native_can_select&&!o.text.empty();if(o.authored_option_index==4)f=o.native_can_select&&!o.text.empty();}if(s.select_d_admissible&&!d||s.select_f_admissible&&!f)return false;}
 return true;
}

bool ParseCccEventRequest267V1(std::string_view text,CccEventRequest267V1&out)noexcept{out={};if(text.size()>16384)return false;Cursor c{text};CccEventRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;std::uint64_t n=0;if(!c.String(k)||!c.Take(':'))return false;if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(k=="request_id"){bit=4;good=c.String(v)&&Id(v);if(good){std::copy(v.begin(),v.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(v.size());}}else if(k=="step"){bit=8;good=c.String(step);}else if(k=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(k=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(k=="ccc_event"){bit=64;good=Claim(c,q);}else if(k=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}if(!bit||!good||(seen&bit))return false;seen|=bit;}
 c.Space();if(seen!=255||c.pos!=text.size()||!CccEventRequestShape267V1(q)||step!=kCccEventSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;}
std::string SerializeCccEventResult267V1(std::string_view id,const CccEventResult267V1&r){using S=CccEventStatus267V1;using A=CccEventAction267V1;
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&CccEventSourceShape267V1(*r.source);if(source&&r.source->fixed_instance_id&&r.source->event_census.events[0].recipient_character_id!=r.facts.played_character_id)source=false;
 const bool query=r.action==A::query&&!r.instance_id&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned&&!r.native_handled;
 const bool selected=(r.action==A::select_tier_four||r.action==A::select_temporary_cancel)&&r.instance_id&&*r.instance_id>0&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&!r.native_handled&&r.cleanup_known&&source&&(r.action==CccEventAction267V1::select_tier_four?r.source->select_d_admissible:r.source->select_f_admissible)&&r.source->fixed_instance_id==r.instance_id;
 const bool ok=source&&r.provider_generation&&r.query_sequence&&((r.status==S::available&&query)||(r.status==S::selection_dispatched&&selected));auto status=r.status;const bool invalid=(!ok&&(status==S::available||status==S::selection_dispatched))||(r.native_returned&&!r.effect_attempted)||(r.effect_attempted&&!r.claim_sequence)||r.native_handled;
 if(invalid||!r.cleanup_known)status=S::indeterminate;if(status==S::indeterminate)source=false;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kCccEventResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kCccEventBackend267V1);j.str("action",Action(r.action));j.str("status",Status(status));j.flag("source_available",source);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kCccEventSourceSchema267V1);j.key("event_census");Census(j,s.event_census);j.key("fixed_instance_id");if(s.fixed_instance_id)j.data+=std::to_string(*s.fixed_instance_id);else j.data+="null";j.flag("case_bound",s.case_bound);j.flag("select_d_admissible",s.select_d_admissible);j.flag("select_f_admissible",s.select_f_admissible);j.flag("sampled_twice",s.sampled_twice);j.data+='}';}else j.data+="null";
 j.key("instance_id");if(r.instance_id)j.data+=std::to_string(*r.instance_id);else j.data+="null";j.flag("addresses_redacted",true);j.flag("event_closed",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,invalid?"ccc_event_internal_result_coherence_unavailable":r.reason.empty()?"ccc_event_actual_source_unavailable":r.reason);j.data+="}}";return j.data;}
}

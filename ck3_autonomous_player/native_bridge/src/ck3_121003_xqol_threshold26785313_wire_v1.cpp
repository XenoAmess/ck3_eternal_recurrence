#include "xar_bridge/ck3_121003_xqol_threshold26785313_v1.hpp"
#include <algorithm>
#include <bit>
#include <cmath>
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
bool Claim(Cursor&c,XqolThresholdRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kXqolThresholdRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kXqolThresholdBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(good&&value=="query_threshold")q.action=XqolThresholdAction267V1::query_threshold;else if(good&&value=="set_threshold")q.action=XqolThresholdAction267V1::set_threshold;else good=false;}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=256;good=UIntText(c,q.query_sequence);}
  else if(key=="instance_id"){bit=512;c.Space();if(c.text.substr(c.pos,4)=="null"){c.pos+=4;q.instance_id.reset();good=true;}else{std::int32_t v=0;good=c.Number(v)&&v>0;if(good)q.instance_id=v;}}
   else if(key=="target_threshold"){bit=1024;good=c.Number(q.target_threshold)&&q.target_threshold<=100;}
   if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
const char*Status(XqolThresholdStatus267V1 s)noexcept{switch(s){case XqolThresholdStatus267V1::available:return "available";case XqolThresholdStatus267V1::threshold_route_dispatched:return "threshold_route_dispatched";case XqolThresholdStatus267V1::expired:return "expired";case XqolThresholdStatus267V1::stale_source:return "stale_source";case XqolThresholdStatus267V1::claim_consumed:return "claim_consumed";case XqolThresholdStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
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

namespace {
bool PromptCensus(const XqolPromptSource267V1&s,const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!s.census_complete||s.resident_count<0||s.resident_count>32||s.named_root_count<0||s.named_root_count>32)return false;if(!s.event)return !s.authored_option_count&&!s.confirm_admissible&&!s.cancel_admissible;
 const auto&e=*s.event;if(s.named_root_count<1||!e.letter_found||!e.named_root_bound||e.definition_key!="xqol.100"||!e.instance_id||*e.instance_id<=0||e.recipient_character_id!=p.played_character_id||s.authored_option_count!=2||e.options.size()>2||e.resident_count!=s.resident_count||!e.opening||!e.description||e.opening->size()>16384||e.description->size()>16384)return false;bool confirm=false,cancel=false;unsigned seen=0;
 for(const auto&o:e.options){if(o.authored_option_index<0||o.authored_option_index>1||(seen&(1U<<o.authored_option_index))||o.text.size()>16384||o.disabled_reason.size()>16384)return false;seen|=1U<<o.authored_option_index;const char*key=o.authored_option_index==0?"xqol_mass_conversion_event_confirm":"xqol_mass_conversion_event_cancel";if(o.source_bound_option_key!=key)return false;if(o.authored_option_index==0)confirm=e.window_visible&&e.window_enabled&&o.native_can_select;else cancel=e.window_visible&&e.window_enabled&&o.native_can_select;}
 return s.confirm_admissible==confirm&&s.cancel_admissible==cancel;
}
void Row(Json&j,const LetterSource267V1&s){
 j.data+="{\"schema\":";String(j.data,kXqolPromptEventSchema267V1);j.num("resident_count",s.resident_count);j.flag("event_found",s.letter_found);j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.nullable("instance_id",s.instance_id);j.nullable("recipient_character_id",s.recipient_character_id);j.nullable("definition_key",s.definition_key);j.nullable("opening",s.opening);j.nullable("description",s.description);j.key("options");j.data+='[';
 for(std::size_t i=0;i<s.options.size();++i){if(i)j.data+=',';const auto&o=s.options[i];j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.nullable("source_bound_option_key",o.source_bound_option_key);j.data+='}';}j.data+=']';j.flag("known_definition_verified",true);j.data+='}';
}
}
bool XqolThresholdRequestShape267V1(const XqolThresholdRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||static_cast<unsigned>(q.action)>1||q.target_threshold>100)return false;
 return q.action==XqolThresholdAction267V1::query_threshold?(!q.provider_generation&&!q.query_sequence&&!q.instance_id):(q.provider_generation&&q.query_sequence&&q.instance_id&&*q.instance_id>0);
}
bool ParseXqolThresholdRequest267V1(std::string_view text,XqolThresholdRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};XqolThresholdRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="xqol_threshold"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!XqolThresholdRequestShape267V1(q)||step!=kXqolThresholdSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}

namespace {
void PromptSource(Json&j,const XqolPromptSource267V1&x){
 j.data+="{\"schema\":";String(j.data,kXqolPromptSourceSchema267V1);j.num("resident_count",x.resident_count);j.num("named_root_count",x.named_root_count);j.flag("census_complete",x.census_complete);j.nullable("authored_option_count",x.authored_option_count);j.key("event");if(x.event)Row(j,*x.event);else j.data+="null";j.flag("confirm_admissible",x.confirm_admissible);j.flag("cancel_admissible",x.cancel_admissible);j.data+='}';
}
void Bits(Json&j,const char*name,const std::optional<std::uint32_t>&v){j.key(name);if(v)String(j.data,std::to_string(*v));else j.data+="null";}
bool ThresholdCensus(const XqolThresholdSource267V1&s,const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(s.target_threshold>100||!PromptCensus(s.prompt,p))return false;
 if(!s.prompt.event)return !s.scrollbar_found&&!s.handle_found&&!s.native_fixed_route_found&&!s.native_shown&&!s.native_valid&&!s.value_bits_u32&&!s.minimum_bits_u32&&!s.maximum_bits_u32&&!s.step_bits_u32&&!s.set_admissible;
 if(!s.scrollbar_found||!s.handle_found||!s.value_bits_u32||!s.minimum_bits_u32||!s.maximum_bits_u32||!s.step_bits_u32)return false;
 const auto value=std::bit_cast<float>(*s.value_bits_u32);
 if(!std::isfinite(value)||value<0||value>100||*s.minimum_bits_u32!=0||*s.maximum_bits_u32!=0x42C80000U||*s.step_bits_u32!=0x3F800000U)return false;
 if(s.native_fixed_route_found?(!s.native_shown||!s.native_valid):(s.native_shown.has_value()||s.native_valid.has_value()))return false;
 return !s.set_admissible||(s.prompt.event->window_visible&&s.prompt.event->window_enabled&&s.native_fixed_route_found&&s.native_shown==true&&s.native_valid==true);
}
}
std::string SerializeXqolThresholdResult267V1(std::string_view id,const XqolThresholdResult267V1&r){
 const auto index=static_cast<std::size_t>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&ThresholdCensus(*r.source,r.facts);const bool lease=r.provider_generation&&r.query_sequence;
 const bool chosen=source&&r.instance_id&&r.source->prompt.event&&r.source->prompt.event->instance_id==r.instance_id;
 const bool read=index==0&&r.status==XqolThresholdStatus267V1::available&&source&&lease&&!r.instance_id&&!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const bool dispatched=index==1&&r.status==XqolThresholdStatus267V1::threshold_route_dispatched&&source&&lease&&chosen&&r.source->set_admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool ok=read||dispatched;auto status=r.status;if(!ok&&(status==XqolThresholdStatus267V1::available||status==XqolThresholdStatus267V1::threshold_route_dispatched))status=XqolThresholdStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kXqolThresholdResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("backend",kXqolThresholdBackend267V1);j.str("adapter_id",kAdapterId);j.str("action",index==1?"set_threshold":"query_threshold");j.str("status",Status(status));j.flag("source_available",source);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.nullable("instance_id",r.instance_id);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kXqolThresholdSourceSchema267V1);j.key("prompt");PromptSource(j,s.prompt);j.flag("scrollbar_found",s.scrollbar_found);j.flag("handle_found",s.handle_found);j.flag("native_fixed_route_found",s.native_fixed_route_found);j.key("native_shown");j.data+=s.native_shown?(*s.native_shown?"true":"false"):"null";j.key("native_valid");j.data+=s.native_valid?(*s.native_valid?"true":"false"):"null";Bits(j,"value_bits_u32",s.value_bits_u32);Bits(j,"minimum_bits_u32",s.minimum_bits_u32);Bits(j,"maximum_bits_u32",s.maximum_bits_u32);Bits(j,"step_bits_u32",s.step_bits_u32);j.num("target_threshold",s.target_threshold);j.flag("set_admissible",s.set_admissible);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("threshold_applied",false);j.flag("event_closed",false);j.flag("conversion_applied",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_xqol_threshold_source_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace

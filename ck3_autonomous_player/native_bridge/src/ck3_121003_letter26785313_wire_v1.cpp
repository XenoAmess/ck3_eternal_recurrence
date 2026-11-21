#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
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
bool Claim(Cursor&c,LetterRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kLetterRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kLetterBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(good&&value=="query_letter")q.action=LetterAction267V1::query_letter;else if(good&&value=="reply_known")q.action=LetterAction267V1::reply_known;else good=false;}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=256;good=UIntText(c,q.query_sequence);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==511;
}
const char*Status(LetterStatus267V1 s)noexcept{switch(s){case LetterStatus267V1::available:return "available";case LetterStatus267V1::reply_dispatched:return "reply_dispatched";case LetterStatus267V1::expired:return "expired";case LetterStatus267V1::stale_source:return "stale_source";case LetterStatus267V1::claim_consumed:return "claim_consumed";case LetterStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
bool Source(const LetterSource267V1&s,const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(s.resident_count<0||s.resident_count>32||s.options.size()>64)return false;
 if(!s.letter_found)return !s.named_root_bound&&!s.window_visible&&!s.window_enabled&&!s.instance_id&&!s.recipient_character_id&&!s.definition_key&&!s.opening&&!s.description&&s.options.empty()&&!s.known_reply_admissible;
 if(!s.named_root_bound||!s.instance_id||*s.instance_id<=0||!s.recipient_character_id||*s.recipient_character_id==-1||!s.definition_key||s.definition_key->empty()||s.definition_key->size()>256||!s.opening||!s.description||s.opening->size()>16384||s.description->size()>16384)return false;
 for(std::size_t i=0;i<s.options.size();++i){const auto&o=s.options[i];if(o.authored_option_index<0||o.authored_option_index>=64||o.text.size()>16384||o.disabled_reason.size()>16384)return false;for(std::size_t k=0;k<i;++k)if(s.options[k].authored_option_index==o.authored_option_index)return false;
  if(o.source_bound_option_key&&(s.definition_key!=kKnownLetterDefinition267V1||s.options.size()!=1||o.authored_option_index!=0||*o.source_bound_option_key!=kKnownLetterOption267V1))return false;
 }
 if(s.known_reply_admissible&&(s.definition_key!=kKnownLetterDefinition267V1||*s.recipient_character_id!=p.played_character_id||!s.window_visible||!s.window_enabled||s.options.size()!=1||s.options[0].authored_option_index!=0||s.options[0].source_bound_option_key!=kKnownLetterOption267V1||!s.options[0].native_can_select||s.options[0].text.empty()))return false;
 return true;
}
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
bool LetterRequestShape267V1(const LetterRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||static_cast<unsigned>(q.action)>1)return false;
 return q.action==LetterAction267V1::query_letter?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence);
}
bool ParseLetterRequest267V1(std::string_view text,LetterRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};LetterRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="letter"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!LetterRequestShape267V1(q)||step!=kLetterSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}
std::string SerializeLetterResult267V1(std::string_view id,const LetterResult267V1&r){
 const auto index=static_cast<std::size_t>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&Source(*r.source,r.facts);const bool lease=r.provider_generation&&r.query_sequence;
 const bool read=index==0&&r.status==LetterStatus267V1::available&&source&&lease&&!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const bool dispatched=index==1&&r.status==LetterStatus267V1::reply_dispatched&&source&&lease&&r.source->known_reply_admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool ok=read||dispatched;auto status=r.status;if(!ok&&(status==LetterStatus267V1::available||status==LetterStatus267V1::reply_dispatched))status=LetterStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kLetterResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("backend",kLetterBackend267V1);j.str("adapter_id",kAdapterId);j.str("action",index==1?"reply_known":"query_letter");j.str("status",Status(status));j.flag("source_available",source);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kLetterSourceSchema267V1);j.num("resident_count",s.resident_count);j.flag("letter_found",s.letter_found);j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.nullable("instance_id",s.instance_id);j.nullable("recipient_character_id",s.recipient_character_id);j.nullable("definition_key",s.definition_key);j.nullable("opening",s.opening);j.nullable("description",s.description);j.key("options");j.data+='[';
  for(std::size_t i=0;i<s.options.size();++i){if(i)j.data+=',';const auto&o=s.options[i];j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.nullable("source_bound_option_key",o.source_bound_option_key);j.data+='}';}j.data+=']';j.flag("known_reply_admissible",s.known_reply_admissible);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("letter_closed",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_letter_source_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace

#include "xar_bridge/ck3_121003_djc_selected_cost26785313_v1.hpp"
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


bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Cb(std::string_view key)noexcept{return std::find(kDjcUiCbKeys267V1.begin(),kDjcUiCbKeys267V1.end(),key)!=kDjcUiCbKeys267V1.end();}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}

bool Claim(Cursor&c,DjcSelectedCostRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kDjcSelectedCostRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kDjcSelectedCostBackend267V1);}
  else if(key=="action"){bit=32;good=c.Identity("query_selected_cost");}else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="target_character_id"){bit=128;good=c.Number(q.target_character_id);}
  else if(key=="cb_key"){bit=256;good=c.String(value);const auto it=std::find(kDjcUiCbKeys267V1.begin(),kDjcUiCbKeys267V1.end(),value);good=good&&it!=kDjcUiCbKeys267V1.end();if(good)q.cb=static_cast<std::uint8_t>(it-kDjcUiCbKeys267V1.begin());}
  else if(key=="provider_generation"){bit=512;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=1024;good=UIntText(c,q.query_sequence);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
const char*Status(DjcUiStatus267V1 s)noexcept{using S=DjcUiStatus267V1;switch(s){case S::unavailable:return "unavailable";case S::expired:return "expired";case S::stale_source:return "stale_source";case S::claim_consumed:return "claim_consumed";case S::available:return "available";default:return "indeterminate";}}
bool Source(const DjcUiSource267V1&s,const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!s.interaction_definition_verified||s.loaded_interface!=4||!s.native_confirmation.value_or(false)||!s.resident_available||!s.named_root_bound||!s.window_visible||!s.selected||s.actor_id!=p.played_character_id||s.recipient_id!=s.target_character_id||s.target_character_id==-1||s.target_character_id==p.played_character_id||!Cb(s.cb_key))return false;
 const auto&t=*s.selected;return t.cb_key==s.cb_key&&t.target_title_ids.size()<=10000&&t.extra_configuration_ids.size()<=10000&&std::none_of(t.target_title_ids.begin(),t.target_title_ids.end(),[](auto id){return id==-1;});
}
struct Json{
 std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view v){key(k);String(data,v);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}
 void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}
 void ids(const char*k,const std::vector<std::int32_t>&v){key(k);data+='[';for(std::size_t i=0;i<v.size();++i){if(i)data+=',';data+=std::to_string(v[i]);}data+=']';}
 void tuple(const DjcUiTuple267V1&t){data+="{\"cb_key\":";String(data,t.cb_key);num("claimant_character_id",t.claimant_character_id);ids("target_title_ids",t.target_title_ids);ids("extra_configuration_ids",t.extra_configuration_ids);flag("source_row_enabled",t.source_row_enabled);data+='}';}
};
}
bool DjcSelectedCostRequestShape267V1(const DjcSelectedCostRequest267V1&q)noexcept{
 return Id(q.id())&&q.deadline_unix_ms&&Prefix(q.expected)&&q.target_character_id!=-1&&q.target_character_id!=q.expected.played_character_id&&q.cb<3&&q.action==DjcUiAction267V1::query_ui&&q.provider_generation&&q.query_sequence&&!q.choice_token&&!q.origin_claim_sequence;
}
bool ParseDjcSelectedCostRequest267V1(std::string_view text,DjcSelectedCostRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};DjcSelectedCostRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="djc_selected_cost"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||step!=kDjcSelectedCostStep267V1||!DjcSelectedCostRequestShape267V1(q))return false;out=q;return true;
}
std::string SerializeDjcSelectedCostResult267V1(std::string_view id,const DjcSelectedCostResult267V1&r){
 const auto&w=r.witness;const bool facts=w.facts_available&&Prefix(w.facts)&&w.connection_generation&&w.ticket_sequence&&w.pump_epoch&&w.thread_id;
 const bool values=r.values.available&&r.values.cleanup_known&&r.values.native_getter_calls==10&&std::all_of(r.values.raw.begin(),r.values.raw.end(),[](const auto&v){return v.has_value();});
 const bool source=facts&&w.source_available&&w.cleanup_known&&w.source&&Source(*w.source,w.facts)&&values;
 const bool ok=source&&w.provider_generation&&w.query_sequence&&!w.claim_sequence&&!w.effect_attempted&&!w.native_returned&&w.status==DjcUiStatus267V1::available;
 auto status=w.status;if(!ok&&status==DjcUiStatus267V1::available)status=DjcUiStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kDjcSelectedCostResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kDjcSelectedCostBackend267V1);j.str("step",kDjcSelectedCostStep267V1);j.str("action","query_selected_cost");j.str("status",Status(status));j.flag("source_available",ok);j.flag("cleanup_known",w.cleanup_known&&r.values.cleanup_known);j.u64("provider_generation",w.provider_generation);j.u64("query_sequence",w.query_sequence);j.u64("claim_sequence",w.claim_sequence);
 j.key("facts_before");if(facts){const auto&p=w.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner_witness");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(w.connection_generation));j.u64("ticket_sequence",w.ticket_sequence);j.u64("pump_epoch",w.pump_epoch);j.num("thread_id",w.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(ok){const auto&s=*w.source;j.data+="{\"schema\":";String(j.data,kDjcSelectedCostSourceSchema267V1);j.num("target_character_id",s.target_character_id);j.str("cb_key",s.cb_key);j.num("actor_id",s.actor_id);j.num("recipient_id",s.recipient_id);j.num("additional_role_id",s.additional_role_id);j.flag("interaction_definition_verified",s.interaction_definition_verified);j.num("loaded_interface",s.loaded_interface);j.flag("native_confirmation",s.native_confirmation.value_or(false));j.flag("resident_available",s.resident_available);j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.key("selected");j.tuple(*s.selected);j.flag("source_matches_private_query",true);j.data+='}';}else j.data+="null";
 j.key("costs");if(ok){j.data+='[';for(std::size_t i=0;i<kDjcSelectedCostCurrencies267V1.size();++i){if(i)j.data+=',';j.data+="{\"currency\":";String(j.data,kDjcSelectedCostCurrencies267V1[i]);j.str("native_type","CFixedPoint");j.str("raw",std::to_string(*r.values.raw[i]));j.data+='}';}j.data+=']';}else j.data+="null";
 j.num("native_getter_calls",r.values.native_getter_calls);j.flag("effect_attempted",w.effect_attempted);j.flag("native_returned",w.native_returned);j.flag("native_handled",false);j.key("formatted_text");j.data+="null";j.flag("addresses_redacted",true);j.flag("payment_confirmed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,w.reason.empty()?"djc_selected_cost_actual_source_unavailable":w.reason);j.data+="}}";return j.data;
}
} // namespace

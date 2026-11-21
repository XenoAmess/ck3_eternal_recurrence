#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_v1.hpp"
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

constexpr std::array<std::string_view,6> actions{"query_ui","open_ui","select_choice","send_ui","query_warning","accept_warning"};
std::size_t Index(DjcUiAction267V1 a)noexcept{return static_cast<std::size_t>(a);}
bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Cb(std::string_view key)noexcept{return std::find(kDjcUiCbKeys267V1.begin(),kDjcUiCbKeys267V1.end(),key)!=kDjcUiCbKeys267V1.end();}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}
bool Claim(Cursor&c,DjcUiRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kDjcUiRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kDjcUiBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);const auto it=std::find(actions.begin(),actions.end(),value);good=good&&it!=actions.end();if(good)q.action=static_cast<DjcUiAction267V1>(it-actions.begin());}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="target_character_id"){bit=128;good=c.Number(q.target_character_id);}else if(key=="cb_key"){bit=256;good=c.String(value);const auto it=std::find(kDjcUiCbKeys267V1.begin(),kDjcUiCbKeys267V1.end(),value);good=good&&it!=kDjcUiCbKeys267V1.end();if(good)q.cb=static_cast<std::uint8_t>(it-kDjcUiCbKeys267V1.begin());}
  else if(key=="provider_generation"){bit=512;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=1024;good=UIntText(c,q.query_sequence);}else if(key=="choice_token"){bit=2048;good=UIntText(c,q.choice_token);}else if(key=="origin_claim_sequence"){bit=4096;good=UIntText(c,q.origin_claim_sequence);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==8191;
}
const char*Status(DjcUiStatus267V1 a)noexcept{using S=DjcUiStatus267V1;switch(a){case S::expired:return "expired";case S::stale_source:return "stale_source";case S::claim_consumed:return "claim_consumed";case S::available:return "available";case S::open_dispatched:return "open_dispatched";case S::selection_dispatched:return "selection_dispatched";case S::send_dispatched:return "send_dispatched";case S::warning_pending:return "warning_pending";case S::warning_ready:return "warning_ready";case S::warning_dispatched:return "warning_dispatched";case S::indeterminate:return "indeterminate";default:return "unavailable";}}
bool Tuple(const DjcUiTuple267V1&t)noexcept{return Cb(t.cb_key)&&t.target_title_ids.size()<=10000&&t.extra_configuration_ids.size()<=10000&&std::none_of(t.target_title_ids.begin(),t.target_title_ids.end(),[](auto id){return id==-1;});}
bool Source(const DjcUiSource267V1&s,const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(s.target_character_id==-1||s.target_character_id==p.played_character_id||!Cb(s.cb_key)||!s.interaction_definition_verified||!s.native_confirmation.has_value()||!s.native_is_valid.has_value()||s.actor_id!=p.played_character_id||s.recipient_id!=s.target_character_id||s.choices.size()>10000)return false;
 if(s.open_admissible&&(s.loaded_interface!=4||!*s.native_confirmation||!*s.native_is_valid||s.window_visible||s.warning_source_available))return false;
 if((s.named_root_bound&&!s.resident_available)||((s.window_visible||s.window_enabled)&&(!s.resident_available||!s.named_root_bound)))return false;
 if(s.selected&&(!s.resident_available||!Tuple(*s.selected)))return false;
 if(s.native_can_send.has_value()&&(!s.resident_available||!s.named_root_bound||!s.selected))return false;
 if(s.send_admissible&&(!s.native_can_send.value_or(false)||!s.window_visible||!s.window_enabled||!s.selected||s.selected->cb_key!=s.cb_key||!s.selected->source_row_enabled||s.warning_source_available))return false;
 if(s.native_can_accept.has_value()!=s.warning_source_available)return false;
 if(s.accept_admissible&&(!s.warning_source_available||!s.native_can_accept.value_or(false)||!s.selected||s.selected->cb_key!=s.cb_key))return false;
 for(std::size_t i=0;i<s.choices.size();++i){const auto&row=s.choices[i];if(!s.resident_available||!row.choice_token||!Tuple(row.tuple)||row.tuple.cb_key!=s.cb_key)return false;for(std::size_t j=0;j<i;++j)if(s.choices[j].choice_token==row.choice_token)return false;}
 return true;
}
struct Json {
 std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view v){key(k);String(data,v);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}
 void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}
 void optional(const char*k,std::optional<bool>v){key(k);data+=v?(*v?"true":"false"):"null";}
 void ids(const char*k,const std::vector<std::int32_t>&v){key(k);data+='[';for(std::size_t i=0;i<v.size();++i){if(i)data+=',';data+=std::to_string(v[i]);}data+=']';}
 void tuple(const DjcUiTuple267V1&t,bool choice,std::uint64_t token=0){data+='{';if(choice){data+="\"choice_token\":";String(data,std::to_string(token));str("cb_key",t.cb_key);}else{data+="\"cb_key\":";String(data,t.cb_key);}num("claimant_character_id",t.claimant_character_id);ids("target_title_ids",t.target_title_ids);ids("extra_configuration_ids",t.extra_configuration_ids);flag(choice?"native_enabled":"source_row_enabled",t.source_row_enabled);data+='}';}
};
}
bool DjcUiRequestShape267V1(const DjcUiRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||q.target_character_id==-1||q.target_character_id==q.expected.played_character_id||q.cb>=3||Index(q.action)>=6)return false;
 if(q.action==DjcUiAction267V1::query_ui)return !q.provider_generation&&!q.query_sequence&&!q.choice_token&&!q.origin_claim_sequence;
 if(!q.provider_generation||!q.query_sequence)return false;
 if((q.action==DjcUiAction267V1::select_choice)!=static_cast<bool>(q.choice_token))return false;
 return (q.action==DjcUiAction267V1::query_warning||q.action==DjcUiAction267V1::accept_warning)==static_cast<bool>(q.origin_claim_sequence);
}
bool ParseDjcUiRequest267V1(std::string_view text,DjcUiRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};DjcUiRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="djc_ui"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!DjcUiRequestShape267V1(q)||step!=kDjcUiSteps267V1[Index(q.action)])return false;out=q;return true;
}
std::string SerializeDjcUiResult267V1(std::string_view id,const DjcUiResult267V1&r){
 const auto index=Index(r.action);const bool action_valid=index<6;const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=r.source_available&&r.cleanup_known&&facts&&r.source&&Source(*r.source,r.facts);const bool lease=r.provider_generation&&r.query_sequence;
 const bool read=!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const bool observation=action_valid&&source&&lease&&read&&((r.action==DjcUiAction267V1::query_ui&&r.status==DjcUiStatus267V1::available)||(r.action==DjcUiAction267V1::query_warning&&r.status==DjcUiStatus267V1::warning_ready&&r.source->warning_source_available));
 bool dispatched=false;if(source&&lease&&r.claim_sequence&&r.effect_attempted&&r.native_returned){using A=DjcUiAction267V1;using S=DjcUiStatus267V1;dispatched=(r.action==A::open_ui&&r.status==S::open_dispatched&&r.source->open_admissible)||(r.action==A::select_choice&&r.status==S::selection_dispatched&&r.source->resident_available&&r.source->named_root_bound&&r.source->window_visible&&r.source->window_enabled)||(r.action==A::send_ui&&r.status==S::send_dispatched&&r.source->send_admissible)||(r.action==A::accept_warning&&r.status==S::warning_dispatched&&r.source->accept_admissible);}
 const bool ok=observation||dispatched;auto status=r.status;using S=DjcUiStatus267V1;if(!ok&&(status==S::available||status==S::warning_ready||status==S::open_dispatched||status==S::selection_dispatched||status==S::send_dispatched||status==S::warning_dispatched))status=S::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kDjcUiResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kDjcUiBackend267V1);j.str("step",kDjcUiSteps267V1[action_valid?index:0]);j.str("action",actions[action_valid?index:0]);j.str("status",Status(status));j.flag("source_available",source);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner_witness");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kDjcUiSourceSchema267V1);j.num("target_character_id",s.target_character_id);j.str("cb_key",s.cb_key);j.flag("interaction_definition_verified",s.interaction_definition_verified);j.num("loaded_interface",s.loaded_interface);j.optional("native_confirmation",s.native_confirmation);j.optional("native_is_valid",s.native_is_valid);j.flag("open_admissible",s.open_admissible);j.flag("resident_available",s.resident_available);j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.num("actor_id",s.actor_id);j.num("recipient_id",s.recipient_id);j.num("additional_role_id",s.additional_role_id);j.key("selected");if(s.selected)j.tuple(*s.selected,false);else j.data+="null";j.key("choices");j.data+='[';for(std::size_t i=0;i<s.choices.size();++i){if(i)j.data+=',';j.tuple(s.choices[i].tuple,true,s.choices[i].choice_token);}j.data+=']';j.optional("native_can_send",s.native_can_send);j.flag("send_admissible",s.send_admissible);j.flag("warning_source_available",s.warning_source_available);j.optional("native_can_accept",s.native_can_accept);j.flag("accept_admissible",s.accept_admissible);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("submitted",false);j.flag("war_created",false);j.flag("payment_confirmed",false);j.flag("physical_save_confirmed",false);j.data+=",\"war_id\":null,\"total_debit\":null";j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_djc_ui_native_source_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace

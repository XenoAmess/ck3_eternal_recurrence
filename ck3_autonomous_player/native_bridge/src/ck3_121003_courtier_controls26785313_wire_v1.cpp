#include "xar_bridge/ck3_121003_courtier_controls26785313_v1.hpp"
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
bool Claim(Cursor&c,CourtierControlsRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kCourtierControlsRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kCourtierControlsBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(good&&value=="query_control")q.action=CourtierControlsAction267V1::query_control;else if(good&&value=="execute_control")q.action=CourtierControlsAction267V1::execute_control;else good=false;}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=256;good=UIntText(c,q.query_sequence);}
  else if(key=="product"){bit=512;good=c.String(value);if(value=="main")q.product=CourtierProduct267V1::main;else if(value=="vivhite")q.product=CourtierProduct267V1::vivhite;else good=false;}
  else if(key=="control"){bit=1024;good=c.String(value);if(value=="cancel")q.control=CourtierControl267V1::cancel;else if(value=="confirm")q.control=CourtierControl267V1::confirm;else if(value=="age_minus_one")q.control=CourtierControl267V1::age_minus_one;else if(value=="age_plus_one")q.control=CourtierControl267V1::age_plus_one;else good=false;}
   if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
const char*Status(CourtierControlsStatus267V1 s)noexcept{switch(s){case CourtierControlsStatus267V1::available:return "available";case CourtierControlsStatus267V1::control_dispatched:return "control_dispatched";case CourtierControlsStatus267V1::expired:return "expired";case CourtierControlsStatus267V1::stale_source:return "stale_source";case CourtierControlsStatus267V1::claim_consumed:return "claim_consumed";case CourtierControlsStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
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

bool CourtierControlsRequestShape267V1(const CourtierControlsRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||static_cast<unsigned>(q.action)>1||static_cast<unsigned>(q.product)>1||static_cast<unsigned>(q.control)>3)return false;
 return q.action==CourtierControlsAction267V1::query_control?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence);
}
bool ParseCourtierControlsRequest267V1(std::string_view text,CourtierControlsRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};CourtierControlsRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="courtier_controls"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!CourtierControlsRequestShape267V1(q)||step!=kCourtierControlsSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}

namespace {
const char*Product(CourtierProduct267V1 v)noexcept{return v==CourtierProduct267V1::vivhite?"vivhite":"main";}
const char*Control(CourtierControl267V1 v)noexcept{switch(v){case CourtierControl267V1::confirm:return "confirm";case CourtierControl267V1::age_minus_one:return "age_minus_one";case CourtierControl267V1::age_plus_one:return "age_plus_one";default:return "cancel";}}
void NullableBool(Json&j,const char*key,const std::optional<bool>&v){j.key(key);j.data+=v?(*v?"true":"false"):"null";}
bool SourceShape(const CourtierControlsSource267V1&s)noexcept{
 if(static_cast<unsigned>(s.product)>1||static_cast<unsigned>(s.control)>3||!s.confirmation_layer_found||
  (s.modal_found&&!s.creator_window_found)||(s.panel_found&&!s.modal_found))return false;
 if(s.creator_window_found&&!s.panel_found)return false;
 if(!s.panel_found)return !s.window_visible&&!s.window_enabled&&!s.native_definition_found&&!s.native_shown&&!s.native_valid&&!s.execute_admissible;
 if(!s.native_definition_found.has_value())return false;
 if(*s.native_definition_found?(!s.native_shown.has_value()||!s.native_valid.has_value()):(s.native_shown.has_value()||s.native_valid.has_value()))return false;
 return !s.execute_admissible||(s.window_visible&&s.window_enabled&&s.native_definition_found==true&&s.native_shown==true&&s.native_valid==true);
}
}
std::string SerializeCourtierControlsResult267V1(std::string_view id,const CourtierControlsResult267V1&r){
 const auto index=static_cast<unsigned>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&SourceShape(*r.source)&&r.source->product==r.product&&r.source->control==r.control;
 const bool lease=r.provider_generation&&r.query_sequence;
 const bool read=index==0&&r.status==CourtierControlsStatus267V1::available&&source&&lease&&!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const bool dispatched=index==1&&r.status==CourtierControlsStatus267V1::control_dispatched&&source&&lease&&r.source->execute_admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool ok=read||dispatched;auto status=r.status;if(!ok&&(status==CourtierControlsStatus267V1::available||status==CourtierControlsStatus267V1::control_dispatched))status=CourtierControlsStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kCourtierControlsResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kCourtierControlsBackend267V1);j.str("action",index==1?"execute_control":"query_control");j.str("status",Status(status));j.str("product",Product(r.product));j.str("control",Control(r.control));j.flag("source_available",source);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source){const auto&s=*r.source;j.data+="{\"schema\":";String(j.data,kCourtierControlsSourceSchema267V1);j.str("product",Product(s.product));j.str("control",Control(s.control));j.flag("confirmation_layer_found",s.confirmation_layer_found);j.flag("creator_window_found",s.creator_window_found);j.flag("modal_found",s.modal_found);j.flag("panel_found",s.panel_found);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);NullableBool(j,"native_definition_found",s.native_definition_found);NullableBool(j,"native_shown",s.native_shown);NullableBool(j,"native_valid",s.native_valid);j.flag("execute_admissible",s.execute_admissible);j.data+='}';}else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("creator_closed",false);j.flag("courtier_created",false);j.flag("age_changed",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_courtier_controls_source_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace

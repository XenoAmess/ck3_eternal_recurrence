#include "xar_bridge/ck3_121003_ccc_decision26785313_v1.hpp"
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
bool Claim(Cursor&c,CccDecisionRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kCccDecisionRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kCccDecisionBackend267V1);}
  else if(key=="action"){bit=32;good=c.String(value);if(good&&value=="query")q.action=CccDecisionAction267V1::query;else if(good&&value=="open_list")q.action=CccDecisionAction267V1::open_list;else if(good&&value=="open_detail")q.action=CccDecisionAction267V1::open_detail;else if(good&&value=="confirm")q.action=CccDecisionAction267V1::confirm;else good=false;}
  else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=c.Number(q.provider_generation);}else if(key=="query_sequence"){bit=256;good=c.Number(q.query_sequence);}
  else if(key=="decision_key"){bit=512;c.Space();if(c.text.substr(c.pos,4)=="null"){c.pos+=4;q.decision.reset();good=true;}else{good=c.String(value);if(good){q.decision=ParseCccDecisionKey267V1(value);good=q.decision.has_value();}}}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==1023;
}
const char*Action(CccDecisionAction267V1 a)noexcept{switch(a){case CccDecisionAction267V1::open_list:return "open_list";case CccDecisionAction267V1::open_detail:return "open_detail";case CccDecisionAction267V1::confirm:return "confirm";default:return "query";}}
const char*Status(CccDecisionStatus267V1 s)noexcept{switch(s){case CccDecisionStatus267V1::available:return "available";case CccDecisionStatus267V1::navigation_dispatched:return "navigation_dispatched";case CccDecisionStatus267V1::selection_dispatched:return "selection_dispatched";case CccDecisionStatus267V1::confirmation_dispatched:return "confirmation_dispatched";case CccDecisionStatus267V1::expired:return "expired";case CccDecisionStatus267V1::stale_source:return "stale_source";case CccDecisionStatus267V1::claim_consumed:return "claim_consumed";case CccDecisionStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view s){key(k);String(data,s);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t n){key(k);data+=std::to_string(n);}
 void u64(const char*k,std::uint64_t n){str(k,std::to_string(n));}
 void nullable(const char*k,const std::optional<std::string>&s){key(k);if(s)String(data,*s);else data+="null";}
 void nullable(const char*k,const std::optional<std::int32_t>&n){key(k);data+=n?std::to_string(*n):"null";}
};
void Key(Json&j,const char*k,const std::optional<CccDecision267V1>&v){j.key(k);if(v)String(j.data,CccDecisionKey267V1(*v));else j.data+="null";}
bool CccTooltipUtf8Wire267V1(std::string_view text)noexcept{if(text.size()>16384)return false;for(std::size_t i=0;i<text.size();){const auto c=static_cast<unsigned char>(text[i++]);std::uint32_t cp=0;unsigned n=0;if(c<0x80)cp=c;else if(c>=0xC2&&c<=0xDF){cp=c&31;n=1;}else if(c>=0xE0&&c<=0xEF){cp=c&15;n=2;}else if(c>=0xF0&&c<=0xF4){cp=c&7;n=3;}else return false;if(i+n>text.size())return false;for(unsigned j=0;j<n;++j){const auto b=static_cast<unsigned char>(text[i++]);if((b&0xC0)!=0x80)return false;cp=(cp<<6)|(b&63);}if((n==1&&cp<0x80)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF))return false;}return true;}
bool Source(const CccDecisionSource267V1&s)noexcept{
 if(s.confirm_tooltip_observed!=s.confirm_tooltip.has_value()||(s.confirm_tooltip&&!CccTooltipUtf8Wire267V1(*s.confirm_tooltip))||s.cooldown_readback_complete||s.cooldown_expiry_date_raw)return false; // expiry ABI is explicitly unqualified, never0/inferred.
 if(s.case_bound&&(!s.corruption_traits||!s.fixture_tax_variable_present))return false;
 if(s.fixture_tax_variable_present==true&&!s.fixture_tax_exact_half)return false;
 if(s.selected_decision&&s.detail_visible&&!s.confirm_tooltip_observed)return false;
 if(!s.case_bound&&(s.corruption_traits||s.fixture_tax_variable_present||s.fixture_tax_exact_half))return false;
 if(s.fixture_tax_exact_half&&s.fixture_tax_variable_present!=true)return false;
 if((s.confirm_admissible||s.open_list_admissible)&&!s.case_bound)return false;

 if(s.rows.size()>1||(!s.list_found&&(s.list_visible||s.list_enabled||s.complete_model_census||!s.rows.empty()||s.groups_count||s.total_model_rows))||(!s.detail_found&&(s.detail_visible||s.detail_enabled||s.selected_decision||s.other_decision_selected||s.native_can_confirm||s.widget_state)))return false;
 if(s.complete_model_census!=bool(s.groups_count&&s.total_model_rows))return false;
 if(s.groups_count&&(*s.groups_count<0||*s.groups_count>64))return false;if(s.total_model_rows&&(*s.total_model_rows<0||*s.total_model_rows>1024))return false;
 if(s.other_decision_selected&&s.selected_decision)return false;if(s.native_can_confirm&&(!s.selected_decision||!s.detail_visible))return false;
 if(s.confirm_admissible&&(!s.detail_found||!s.detail_visible||!s.detail_enabled||s.blocked_by_visible_modal||!s.selected_decision||s.native_can_confirm!=true))return false;
 if(s.open_list_admissible&&(s.list_visible||s.blocked_by_visible_modal))return false;
 for(std::size_t i=0;i<s.rows.size();++i){const auto&r=s.rows[i];if(CccDecisionKey267V1(r.decision).empty())return false;for(std::size_t n=0;n<i;++n)if(s.rows[n].decision==r.decision)return false;if(r.is_selected!=(s.detail_visible&&s.selected_decision==r.decision))return false;if(r.can_open_detail&&(!s.case_bound||!s.list_visible||!s.list_enabled||r.is_selected||s.blocked_by_visible_modal))return false;}return true;
}
void WriteSource(Json&j,const CccDecisionSource267V1&s){
 j.data+="{\"schema\":";String(j.data,kCccDecisionSourceSchema267V1);
 j.flag("list_found",s.list_found);j.flag("list_visible",s.list_visible);j.flag("list_enabled",s.list_enabled);j.flag("detail_found",s.detail_found);j.flag("detail_visible",s.detail_visible);j.flag("detail_enabled",s.detail_enabled);j.flag("other_decision_selected",s.other_decision_selected);j.flag("open_list_admissible",s.open_list_admissible);j.flag("complete_model_census",s.complete_model_census);j.flag("blocked_by_visible_modal",s.blocked_by_visible_modal);j.flag("confirm_admissible",s.confirm_admissible);j.flag("case_bound",s.case_bound);j.key("corruption_traits");if(s.corruption_traits){j.data+='[';for(std::size_t k=0;k<4;++k){if(k)j.data+=',';j.data+=(*s.corruption_traits)[k]?"true":"false";}j.data+=']';}else j.data+="null";j.key("fixture_tax_variable_present");j.data+=s.fixture_tax_variable_present?(*s.fixture_tax_variable_present?"true":"false"):"null";j.key("fixture_tax_exact_half");j.data+=s.fixture_tax_exact_half?(*s.fixture_tax_exact_half?"true":"false"):"null";j.flag("confirm_tooltip_observed",s.confirm_tooltip_observed);j.key("confirm_tooltip");if(s.confirm_tooltip)String(j.data,*s.confirm_tooltip);else j.data+="null";j.key("cooldown_expiry_date_raw");if(s.cooldown_expiry_date_raw)j.data+=std::to_string(*s.cooldown_expiry_date_raw);else j.data+="null";j.flag("cooldown_readback_complete",s.cooldown_readback_complete);j.nullable("groups_count",s.groups_count);j.nullable("total_model_rows",s.total_model_rows);j.nullable("widget_state",s.widget_state);Key(j,"selected_decision_key",s.selected_decision);j.key("native_can_confirm");j.data+=s.native_can_confirm?(*s.native_can_confirm?"true":"false"):"null";j.key("rows");j.data+='[';
 for(std::size_t i=0;i<s.rows.size();++i){if(i)j.data+=',';const auto&r=s.rows[i];j.data+="{\"decision_key\":";String(j.data,CccDecisionKey267V1(r.decision));j.flag("can_open_detail",r.can_open_detail);j.flag("is_selected",r.is_selected);j.data+='}';}j.data+="]}";
}
}
std::optional<CccDecision267V1>ParseCccDecisionKey267V1(std::string_view text)noexcept{for(std::size_t i=0;i<kCccDecisionKeys267V1.size();++i)if(text==kCccDecisionKeys267V1[i])return static_cast<CccDecision267V1>(i);return {};}
bool CccDecisionRequestShape267V1(const CccDecisionRequest267V1&q)noexcept{
 if(!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||static_cast<unsigned>(q.action)>3||(q.decision&&CccDecisionKey267V1(*q.decision).empty()))return false;
 if(q.action==CccDecisionAction267V1::query)return !q.provider_generation&&!q.query_sequence&&!q.decision;
 return q.provider_generation&&q.query_sequence&&(q.action==CccDecisionAction267V1::open_list?!q.decision:q.decision.has_value());
}
bool ParseCccDecisionRequest267V1(std::string_view text,CccDecisionRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};CccDecisionRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="ccc_decision"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!CccDecisionRequestShape267V1(q)||step!=kCccDecisionSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}

std::string SerializeCccDecisionResult267V1(std::string_view id,const CccDecisionResult267V1&r){
 const auto a=static_cast<std::size_t>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 bool source=r.status!=CccDecisionStatus267V1::indeterminate&&facts&&r.cleanup_known&&r.source_available&&r.source&&Source(*r.source);const bool lease=r.provider_generation&&r.query_sequence;
 bool allowed=false;if(source){if(a==1)allowed=r.source->open_list_admissible;else if(a==2&&r.decision){for(const auto&row:r.source->rows)if(row.decision==r.decision)allowed=row.can_open_detail;}else if(a==3)allowed=r.decision&&r.source->confirm_admissible&&r.source->selected_decision==r.decision;}
 const bool read=a==0&&r.status==CccDecisionStatus267V1::available&&source&&lease&&!r.decision&&!r.effect_attempted&&!r.native_returned&&!r.claim_sequence;
 const auto desired=a==1?CccDecisionStatus267V1::navigation_dispatched:a==2?CccDecisionStatus267V1::selection_dispatched:CccDecisionStatus267V1::confirmation_dispatched;
 const bool dispatched=a>0&&a<4&&r.status==desired&&source&&lease&&allowed&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
 const bool handled_coherent=a==1||!r.native_handled;const bool ok=handled_coherent&&(read||dispatched);auto status=r.status;if(!ok&&(status==CccDecisionStatus267V1::available||status==CccDecisionStatus267V1::navigation_dispatched||status==CccDecisionStatus267V1::selection_dispatched||status==CccDecisionStatus267V1::confirmation_dispatched))status=CccDecisionStatus267V1::indeterminate;
 if(status==CccDecisionStatus267V1::indeterminate)source=false;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kCccDecisionResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("backend",kCccDecisionBackend267V1);j.str("adapter_id",kAdapterId);j.str("action",Action(r.action));j.str("status",Status(status));j.flag("source_available",source);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",r.native_handled);j.flag("cleanup_known",r.cleanup_known);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);Key(j,"decision_key",r.decision);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source)WriteSource(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.flag("decision_applied",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_ccc_decision_source_unavailable":r.reason);j.data+="}}";return j.data;
}
}

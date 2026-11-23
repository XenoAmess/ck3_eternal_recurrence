#include "xar_bridge/ck3_121003_rmtm_observation26785313_v1.hpp"
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


bool Null(Cursor&c)noexcept{c.Space();if(c.text.substr(c.pos,4)!="null")return false;c.pos+=4;return true;}
template<class E,std::size_t N>bool OptionalEnum(Cursor&c,std::optional<E>&out,const std::array<std::string_view,N>&names)noexcept {
 if(Null(c)){out.reset();return true;}std::string_view v;if(!c.String(v))return false;for(std::size_t i=0;i<N;++i)if(names[i]==v){out=static_cast<E>(i);return true;}return false;
}
bool Claim(Cursor&c,RmtmObservationRequest267V1&q)noexcept {
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="schema"){bit=1;good=c.Identity(kRmtmObservationRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kRmtmObservationBackend267V1);}else if(k=="action"){bit=32;good=c.String(v);if(good){good=false;for(std::size_t i=0;i<kRmtmObservationActions267V1.size();++i)if(v==kRmtmObservationActions267V1[i]){q.action=static_cast<RmtmObservationAction267V1>(i);good=true;break;}}}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="provider_generation"){bit=128;good=c.Number(q.provider_generation);}else if(k=="query_sequence"){bit=256;good=c.Number(q.query_sequence);}else if(k=="phase"){bit=512;good=OptionalEnum(c,q.phase,kRmtmPhysicalPhases267V1);}else if(k=="offer_target"){bit=1024;constexpr std::array<std::string_view,2>names{"released_a","released_b"};good=OptionalEnum(c,q.offer_target,names);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
struct Json {std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}template<class T>void nullable(const char*k,const std::optional<T>&v){key(k);if(v)data+=std::to_string(*v);else data+="null";}};
bool Utf8(std::string_view s)noexcept {
 if(s.size()>16384)return false;for(std::size_t i=0;i<s.size();){const auto x=static_cast<unsigned char>(s[i++]);std::uint32_t value=0;unsigned n=0;if(x<0x80)value=x;else if(x>=0xC2&&x<=0xDF){value=x&31;n=1;}else if(x>=0xE0&&x<=0xEF){value=x&15;n=2;}else if(x>=0xF0&&x<=0xF4){value=x&7;n=3;}else return false;if(i+n>s.size())return false;for(unsigned k=0;k<n;++k){const auto c=static_cast<unsigned char>(s[i++]);if((c&0xC0)!=0x80)return false;value=(value<<6)|(c&63);}if((n==1&&value<0x80)||(n==2&&value<0x800)||(n==3&&value<0x10000)||value>0x10FFFF||(value>=0xD800&&value<=0xDFFF))return false;}return true;
}
void Character(std::string&out,const std::optional<RmtmTitleCharacter267V1>&v){if(!v){out+="null";return;}out+="{\"full_id\":"+std::to_string(v->full_id)+",\"alive\":"+(v->alive?"true":"false")+"}";}
void Physical(Json&j,const RmtmTitleQuerySource267V1&s){const auto&t=s.title;j.data+="{\"schema\":";String(j.data,kRmtmTitleQuerySourceSchema267V1);j.num("actor_id",s.actor_id);j.num("full_title_id",t.full_title_id);j.key("holder");Character(j.data,t.holder);j.key("engine_current_heir");Character(j.data,t.engine_current_heir);j.num("native_law_count",t.native_law_count);j.key("physical_own_laws");j.data+='[';for(std::size_t i=0;i<t.physical_own_laws.size();++i){if(i)j.data+=',';const auto&l=t.physical_own_laws[i];j.data+="{\"native_definition_id\":"+std::to_string(l.native_definition_id)+",\"key\":";String(j.data,l.key);j.data+='}';}j.data+=']';j.num("engine_successor_count",t.engine_successor_count);j.flag("sampled_twice",t.sampled_twice);j.data+='}';}
void Source(Json&j,const RmtmObservationSource267V1&s){constexpr std::array<std::string_view,4>kinds{"title_phase","council","budget","offer"};j.data+="{\"schema\":";String(j.data,kRmtmObservationSourceSchema267V1);j.str("kind",kinds[static_cast<std::size_t>(s.kind)]);j.flag("case_bound",s.case_bound);j.flag("sampled_twice",s.sampled_twice);
 j.key("title_phase");if(s.title_phase){const auto&t=*s.title_phase;j.data+="{\"phase\":";String(j.data,kRmtmPhysicalPhases267V1[static_cast<std::size_t>(t.phase)]);j.key("physical");Physical(j,t.physical);j.flag("script_own_single_heir",t.script_own_single_heir);j.flag("holder_realm_single_heir",t.holder_realm_single_heir);j.flag("witness_guard_bound",t.witness_guard_bound);j.flag("witness_sampled_twice",t.witness_sampled_twice);j.data+='}';}else j.data+="null";
 j.key("council");if(s.council){const auto&c=*s.council;j.data+="{\"owner_id\":"+std::to_string(c.owner_id);j.num("native_task_count",c.native_task_count);j.flag("complete_model_census",c.complete_model_census);j.flag("sampled_twice",c.sampled_twice);j.key("seats");j.data+='[';for(std::size_t i=0;i<c.seats.size();++i){if(i)j.data+=',';const auto&r=c.seats[i];j.data+="{\"position_key\":";String(j.data,r.position_key);j.num("full_task_id",r.full_task_id);j.nullable("incumbent_id",r.incumbent_id);j.key("incumbent_alive");j.data+=r.incumbent_alive?(*r.incumbent_alive?"true":"false"):"null";j.data+='}';}j.data+="]}";}else j.data+="null";
 j.key("budget");if(s.budget){const auto&b=*s.budget;j.data+="{\"found\":";j.data+=b.found?"true":"false";j.flag("visible",b.visible);j.flag("enabled",b.enabled);j.flag("blocked_by_visible_modal",b.blocked_by_visible_modal);j.nullable("owner_id",b.owner_id);j.nullable("full_title_id",b.full_title_id);j.nullable("holder_id",b.holder_id);j.flag("open_admissible",b.open_admissible);j.flag("cancel_admissible",b.cancel_admissible);j.str("route",b.route);j.flag("sampled_twice",b.sampled_twice);j.data+='}';}else j.data+="null";
 j.key("offer");if(s.offer){const auto&o=*s.offer;j.data+="{\"target\":";String(j.data,o.target==RmtmOfferTarget267V1::released_a?"released_a":"released_b");j.flag("found",o.found);j.flag("visible",o.visible);j.flag("enabled",o.enabled);j.flag("blocked_by_visible_modal",o.blocked_by_visible_modal);j.num("actor_id",o.actor_id);j.num("recipient_id",o.recipient_id);j.str("interaction_key",o.interaction_key);j.str("description",o.description);j.flag("open_admissible",o.open_admissible);j.flag("cancel_admissible",o.cancel_admissible);j.flag("sampled_twice",o.sampled_twice);j.data+='}';}else j.data+="null";j.data+='}';
}
const char*Status(RmtmObservationStatus267V1 s)noexcept{switch(s){case RmtmObservationStatus267V1::available:return "available";case RmtmObservationStatus267V1::navigation_dispatched:return "navigation_dispatched";case RmtmObservationStatus267V1::expired:return "expired";case RmtmObservationStatus267V1::stale_source:return "stale_source";case RmtmObservationStatus267V1::claim_consumed:return "claim_consumed";case RmtmObservationStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
}
bool RmtmObservationQuery267V1(RmtmObservationAction267V1 a)noexcept {using A=RmtmObservationAction267V1;return a==A::query_title_phase||a==A::query_council||a==A::query_budget||a==A::query_offer;}
RmtmObservationKind267V1 RmtmObservationKindFor267V1(RmtmObservationAction267V1 a)noexcept {const auto n=static_cast<unsigned>(a);return n==0?RmtmObservationKind267V1::title_phase:n==1?RmtmObservationKind267V1::council:n<5?RmtmObservationKind267V1::budget:RmtmObservationKind267V1::offer;}
bool RmtmObservationRequestShape267V1(const RmtmObservationRequest267V1&q)noexcept {
 const auto a=static_cast<unsigned>(q.action);if(a>=8||!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected))return false;
 if((a==0)!=q.phase.has_value()||(q.phase&&static_cast<unsigned>(*q.phase)>=3)||(a>=5)!=q.offer_target.has_value()||(q.offer_target&&static_cast<unsigned>(*q.offer_target)>=2))return false;
 return RmtmObservationQuery267V1(q.action)?!q.provider_generation&&!q.query_sequence:q.provider_generation&&q.query_sequence;
}
bool RmtmObservationSourceShape267V1(const RmtmObservationSource267V1&s,const ck3_1210::CoreSnapshotPrefix&f)noexcept {
 if(static_cast<unsigned>(s.kind)>3||!s.sampled_twice||int(bool(s.title_phase))+int(bool(s.council))+int(bool(s.budget))+int(bool(s.offer))!=1)return false;
 if(s.kind==RmtmObservationKind267V1::title_phase){if(!s.title_phase)return false;const auto&t=*s.title_phase;return static_cast<unsigned>(t.phase)<3&&t.witness_guard_bound&&t.witness_sampled_twice&&RmtmTitleQuerySourceShape267V1(t.physical,f);}
 if(s.kind==RmtmObservationKind267V1::council){if(!s.council)return false;const auto&c=*s.council;if(c.owner_id!=f.played_character_id||!c.complete_model_census||!c.sampled_twice||c.native_task_count<0||c.native_task_count>4096)return false;for(std::size_t i=0;i<9;++i){const auto&r=c.seats[i];if(r.position_key!=kRmtmCouncilKeys267V1[i]||r.full_task_id==0xFFFFFFFFU||r.incumbent_id.has_value()!=r.incumbent_alive.has_value()||(r.incumbent_id&&*r.incumbent_id==0xFFFFFFFFU))return false;for(std::size_t j=0;j<i;++j)if(c.seats[j].full_task_id==r.full_task_id)return false;}return true;}
 if(s.kind==RmtmObservationKind267V1::budget){if(!s.budget)return false;const auto&b=*s.budget;if(!b.sampled_twice||b.route!="my_realm_player"||(b.owner_id&&*b.owner_id==-1)||(b.full_title_id&&*b.full_title_id==0xFFFFFFFFU)||(b.holder_id&&*b.holder_id==0xFFFFFFFFU)||b.full_title_id.has_value()!=b.holder_id.has_value())return false;if(!b.found&&(b.visible||b.enabled||b.owner_id||b.full_title_id||b.cancel_admissible))return false;if(b.cancel_admissible&&(!s.case_bound||!b.found||!b.visible||!b.enabled||b.blocked_by_visible_modal||b.owner_id!=f.played_character_id))return false;if(b.open_admissible&&(!s.case_bound||b.visible||b.blocked_by_visible_modal))return false;return true;}
 if(!s.offer)return false;const auto&o=*s.offer;if(static_cast<unsigned>(o.target)>1||!o.sampled_twice||o.actor_id!=f.played_character_id||o.recipient_id==-1||o.interaction_key!="offer_vassalization_interaction"||!Utf8(o.description))return false;if(!o.found&&(o.visible||o.enabled||o.cancel_admissible))return false;if((o.open_admissible||o.cancel_admissible)&&(!s.case_bound||o.blocked_by_visible_modal))return false;if(o.open_admissible&&o.visible)return false;if(o.cancel_admissible&&(!o.found||!o.visible||!o.enabled))return false;return true;
}
bool ParseRmtmObservationRequest267V1(std::string_view text,RmtmObservationRequest267V1&out)noexcept {
 out={};if(text.size()>16384)return false;Cursor c{text};RmtmObservationRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;std::uint64_t n=0;if(!c.String(k)||!c.Take(':'))return false;
 if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(k=="request_id"){bit=4;good=c.String(v)&&Id(v);if(good){std::copy(v.begin(),v.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(v.size());}}else if(k=="step"){bit=8;good=c.String(step);}else if(k=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(k=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(k=="rmtm_observation"){bit=64;good=Claim(c,q);}else if(k=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
 if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!RmtmObservationRequestShape267V1(q)||step!=kRmtmObservationSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}
std::string SerializeRmtmObservationResult267V1(std::string_view id,const RmtmObservationResult267V1&r) {
 using A=RmtmObservationAction267V1;using S=RmtmObservationStatus267V1;
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&RmtmObservationSourceShape267V1(*r.source,r.facts)&&r.source->kind==RmtmObservationKindFor267V1(r.action);
 const bool query=RmtmObservationQuery267V1(r.action)&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned&&!r.native_handled;
 bool admissible=false;if(source&&!RmtmObservationQuery267V1(r.action)){if(r.action==A::open_budget)admissible=r.source->budget&&r.source->budget->open_admissible;else if(r.action==A::cancel_budget)admissible=r.source->budget&&r.source->budget->cancel_admissible;else if(r.action==A::open_offer)admissible=r.source->offer&&r.source->offer->open_admissible;else if(r.action==A::cancel_offer)admissible=r.source->offer&&r.source->offer->cancel_admissible;}
 const bool dispatched=admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&(r.action==A::open_budget||!r.native_handled);
 const bool ok=source&&r.provider_generation&&r.query_sequence&&((r.status==S::available&&query)||(r.status==S::navigation_dispatched&&dispatched));auto status=r.status;
 if(!r.cleanup_known||(!ok&&(status==S::available||status==S::navigation_dispatched))||(r.native_returned&&!r.effect_attempted)||(r.effect_attempted&&!r.claim_sequence)||(r.native_handled&&r.action!=A::open_budget))status=S::indeterminate;
 Json j;j.data="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(j.data,id);j.flag("ok",ok);j.key("result");j.data+="{\"schema\":";String(j.data,kRmtmObservationResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kRmtmObservationBackend267V1);j.str("action",static_cast<unsigned>(r.action)<8?kRmtmObservationActions267V1[static_cast<std::size_t>(r.action)]:"invalid");j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",r.native_handled);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(ok)Source(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"rmtm_actual_observation_primitive_unavailable":r.reason);j.data+="}}";return j.data;
}
}

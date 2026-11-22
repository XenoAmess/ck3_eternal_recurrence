#include "xar_bridge/ck3_121003_ted_actor_transition26785313_wire_v1.hpp"
#include <algorithm>
#include <charconv>
#include <limits>
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
template<class T,std::size_t N>bool EnumText(Cursor&c,const std::array<std::string_view,N>&names,T&out)noexcept{std::string_view text;if(!c.String(text))return false;for(std::size_t n=0;n<N;++n)if(names[n]==text){out=static_cast<T>(n);return true;}return false;}
struct Json{std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view s){key(k);String(data,s);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t n){key(k);data+=std::to_string(n);}
 void u64(const char*k,std::uint64_t n){str(k,std::to_string(n));}
 void nullable(const char*k,const std::optional<std::string>&s){key(k);if(s)String(data,*s);else data+="null";}
 void nullable(const char*k,const std::optional<std::int32_t>&n){key(k);data+=n?std::to_string(*n):"null";}
 void raw(const char*k,const std::optional<std::int64_t>&n){key(k);if(n)String(data,std::to_string(*n));else data+="null";}
 void nullable(const char*k,const std::optional<bool>&b){key(k);data+=b?(*b?"true":"false"):"null";}
};

constexpr std::array<std::string_view,4>Actions{"query_role","advance_day","query_operation","confirm_epoch"};
constexpr std::array<std::string_view,12>Statuses{"unavailable","expired","stale_source","claim_consumed","capacity_exhausted","available","submitted","running","completed_day","transition_pending","epoch_confirmed","indeterminate"};
std::string_view IdOf(const std::array<char,97>&s,std::uint8_t n)noexcept{return {s.data(),n};}
bool Claim(Cursor&c,TedTransitionRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kTedTransitionRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kTedTransitionBackend267V1);}
  else if(key=="action"){bit=32;good=EnumText(c,Actions,q.action);}else if(key=="operation_id"){bit=64;good=c.String(value)&&(value.empty()||Id(value));if(good){std::copy(value.begin(),value.end(),q.operation_id.begin());q.operation_id_size=static_cast<std::uint8_t>(value.size());}}
  else if(key=="expected_core"){bit=128;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=256;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=512;good=UIntText(c,q.query_sequence);}else if(key=="actor_epoch"){bit=1024;good=UIntText(c,q.actor_epoch);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
bool Actor(std::int32_t id)noexcept{return id!=-1;}
bool Day(std::int32_t start,std::int32_t target)noexcept{return static_cast<std::int64_t>(start)+24==target;}
bool PendingShape(const TedPendingTransition267V1&p)noexcept{return Id(p.operation_id)&&p.claim_sequence&&p.generation&&p.original_deadline_unix_ms&&Actor(p.before_actor_id)&&Actor(p.after_actor_id)&&p.before_actor_id!=p.after_actor_id&&Day(p.starting_date_raw,p.target_date_raw)&&p.completed_daily_ticks==1&&p.exact_day_confirmed&&p.shutdown_safe&&p.cleanup_known;}
void EmitCore(Json&j,const ck3_1210::CoreSnapshotPrefix&p){j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}
void EmitPending(Json&j,const TedPendingTransition267V1&p){j.data+="{\"operation_id\":";String(j.data,p.operation_id);j.u64("claim_sequence",p.claim_sequence);j.u64("generation",p.generation);j.num("original_deadline_unix_ms",static_cast<std::int64_t>(p.original_deadline_unix_ms));j.num("before_actor_id",p.before_actor_id);j.num("after_actor_id",p.after_actor_id);j.num("starting_date_raw",p.starting_date_raw);j.num("target_date_raw",p.target_date_raw);j.num("completed_daily_ticks",p.completed_daily_ticks);j.flag("exact_day_confirmed",p.exact_day_confirmed);j.flag("shutdown_safe",p.shutdown_safe);j.flag("cleanup_known",p.cleanup_known);j.data+='}';}
void EmitSource(Json&j,const TedTransitionSource267V1&s){j.data+="{\"schema\":";String(j.data,kTedTransitionSourceSchema267V1);j.str("role",s.role==TedActorRole267V1::song?"song":"recipient");j.flag("definition_found",s.definition_found);j.nullable("native_shown",s.native_shown);j.u64("actor_epoch",s.actor_epoch);j.nullable("song_actor_id",s.song_actor_id);j.nullable("recipient_actor_id",s.recipient_actor_id);j.key("pending");if(s.pending)EmitPending(j,*s.pending);else j.data+="null";j.flag("runtime_ready",s.runtime_ready);j.flag("predecessor_resolved",s.predecessor_resolved);j.flag("advance_admissible",s.advance_admissible);j.flag("confirm_admissible",s.confirm_admissible);j.data+='}';}
void EmitProgress(Json&j,const TedTransitionProgress267V1&p){j.data+="{\"generation\":\""+std::to_string(p.generation)+'"';j.num("starting_date_raw",p.starting_date_raw);j.num("target_date_raw",p.target_date_raw);j.num("last_observed_date_raw",p.last_observed_date_raw);j.num("before_actor_id",p.before_actor_id);j.num("after_actor_id",p.after_actor_id);j.num("completed_daily_ticks",p.completed_daily_ticks);j.num("failure_flags",p.failure_flags);j.num("overshoot_days",p.overshoot_days);j.flag("arm_attempted",p.arm_attempted);j.flag("resume_attempted",p.resume_attempted);j.flag("resume_submitted",p.resume_submitted);j.flag("exact_day_confirmed",p.exact_day_confirmed);j.flag("transition_pending",p.transition_pending);j.flag("shutdown_safe",p.shutdown_safe);j.flag("armed",p.armed);j.flag("access_cleanup_unknown",p.access_cleanup_unknown);j.data+='}';}
bool IsOkay(TedTransitionStatus267V1 s)noexcept{return s==TedTransitionStatus267V1::available||s==TedTransitionStatus267V1::submitted||s==TedTransitionStatus267V1::running||s==TedTransitionStatus267V1::completed_day||s==TedTransitionStatus267V1::transition_pending||s==TedTransitionStatus267V1::epoch_confirmed;}
bool ResultShape(const TedTransitionResult267V1&r)noexcept{
 using A=TedTransitionAction267V1;using S=TedTransitionStatus267V1;
 if(static_cast<unsigned>(r.action)>3||static_cast<unsigned>(r.status)>11||!Id(r.request_id)||!r.deadline_unix_ms||r.actor_epoch>2||r.source_available!=bool(r.source))return false;
 if(r.action==A::query_role){if(!r.operation_id.empty())return false;}else if(!Id(r.operation_id))return false;
 if(r.facts_available){if(!Prefix(r.facts)||!r.connection_generation||!r.ticket_sequence||!r.pump_epoch||!r.thread_id)return false;}else if(r.connection_generation||r.ticket_sequence||r.pump_epoch||r.thread_id)return false;
 if(r.source&&(!r.facts_available||!TedTransitionSourceShape267V1(*r.source)||!r.cleanup_known))return false;
 if(r.progress&&!TedTransitionProgressShape267V1(*r.progress))return false;
 if(r.action==A::query_operation&&r.source)return false;
 if(!r.cleanup_known&&r.status!=S::indeterminate)return false;
 if(r.status==S::available)return r.action==A::query_role&&r.source&&r.facts_available&&r.provider_generation&&r.query_sequence&&!r.accepted&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned&&!r.progress&&r.source->actor_epoch==r.actor_epoch;
 if(r.status==S::epoch_confirmed)return r.action==A::confirm_epoch&&r.source&&r.source->confirm_admissible&&r.source->actor_epoch==0&&r.actor_epoch==1&&r.accepted&&r.claim_sequence&&r.provider_generation&&r.query_sequence&&!r.effect_attempted&&!r.native_returned&&!r.progress;
 if(r.status==S::submitted||r.status==S::running||r.status==S::completed_day||r.status==S::transition_pending){
  if((r.action!=A::advance_day&&r.action!=A::query_operation)||!r.accepted||!r.claim_sequence||!r.provider_generation||!r.query_sequence||!r.facts_available||!r.progress||!r.progress->arm_attempted||!r.progress->resume_attempted||!r.progress->resume_submitted||!r.effect_attempted||!r.native_returned||!r.cleanup_known)return false;
  if(r.action==A::advance_day&&(!r.source||!r.source->advance_admissible))return false;
  if(r.status==S::submitted||r.status==S::running)return !r.progress->exact_day_confirmed&&!r.progress->transition_pending&&!r.progress->failure_flags&&!r.progress->access_cleanup_unknown;
  if(!r.progress->exact_day_confirmed||r.progress->armed||!r.progress->shutdown_safe||r.progress->access_cleanup_unknown||r.progress->failure_flags||r.progress->completed_daily_ticks!=1||r.progress->overshoot_days||!Actor(r.progress->after_actor_id))return false;
  return r.status==S::transition_pending?(r.progress->transition_pending&&r.actor_epoch==0&&r.progress->before_actor_id!=r.progress->after_actor_id):(!r.progress->transition_pending&&r.progress->before_actor_id==r.progress->after_actor_id);
 }
 if(r.status==S::indeterminate)return true;
 return !r.accepted&&!r.effect_attempted&&!r.native_returned&&r.cleanup_known;
}
} // namespace
bool TedTransitionRequestShape267V1(const TedTransitionRequest267V1&q)noexcept{
 const auto a=static_cast<unsigned>(q.action);if(a>3||!Id(IdOf(q.request_id,q.request_id_size))||!q.deadline_unix_ms||!Prefix(q.expected)||q.actor_epoch>1)return false;
 if(a==0)return q.operation_id_size==0&&!q.provider_generation&&!q.query_sequence&&!q.actor_epoch;
 return Id(IdOf(q.operation_id,q.operation_id_size))&&q.provider_generation&&q.query_sequence&&(a!=3||q.actor_epoch==0);
}
bool ParseTedTransitionRequest267V1(std::string_view text,TedTransitionRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};TedTransitionRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="ted_actor_transition"){bit=64;good=Claim(c,q);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!TedTransitionRequestShape267V1(q)||step!=kTedTransitionSteps267V1[static_cast<std::size_t>(q.action)])return false;out=q;return true;
}
bool TedTransitionSourceShape267V1(const TedTransitionSource267V1&s)noexcept{
 if(static_cast<unsigned>(s.role)>1||s.actor_epoch>2||s.definition_found!=s.native_shown.has_value()||(s.song_actor_id&&!Actor(*s.song_actor_id))||(s.recipient_actor_id&&!Actor(*s.recipient_actor_id)))return false;
 if(s.pending&&(!PendingShape(*s.pending)||s.actor_epoch!=0||s.role!=TedActorRole267V1::recipient||!s.song_actor_id||*s.song_actor_id!=s.pending->before_actor_id||(s.recipient_actor_id&&*s.recipient_actor_id!=s.pending->after_actor_id)))return false;
 if(s.actor_epoch&&(!s.song_actor_id||!s.recipient_actor_id||*s.song_actor_id==*s.recipient_actor_id||s.role!=TedActorRole267V1::recipient||s.pending))return false;
 if(s.advance_admissible&&(!s.definition_found||s.native_shown!=true||!s.runtime_ready||!s.predecessor_resolved||s.pending||s.actor_epoch>=2||s.confirm_admissible||(s.actor_epoch==0&&(s.role!=TedActorRole267V1::song||!s.song_actor_id||s.recipient_actor_id))))return false;
 if(s.confirm_admissible&&(!s.definition_found||s.native_shown!=true||!s.runtime_ready||!s.predecessor_resolved||!s.pending||s.actor_epoch||s.role!=TedActorRole267V1::recipient||!s.song_actor_id||!s.recipient_actor_id||s.advance_admissible))return false;
 return true;
}
bool TedTransitionProgressShape267V1(const TedTransitionProgress267V1&p)noexcept{
 if(!Day(p.starting_date_raw,p.target_date_raw)||!Actor(p.before_actor_id)||p.completed_daily_ticks>1||p.overshoot_days<0||p.resume_submitted&&!p.resume_attempted||p.resume_attempted&&!p.arm_attempted||p.armed&&!p.generation)return false;
 if(p.exact_day_confirmed&&(!p.generation||p.failure_flags||p.overshoot_days||p.completed_daily_ticks!=1||p.last_observed_date_raw!=p.target_date_raw||!Actor(p.after_actor_id)||p.armed||!p.shutdown_safe||p.access_cleanup_unknown||!p.resume_submitted))return false;
 if(p.transition_pending&&(!p.exact_day_confirmed||p.before_actor_id==p.after_actor_id))return false;return true;
}
std::string SerializeTedTransitionResult267V1(std::string_view id,const TedTransitionResult267V1&input){
 TedTransitionResult267V1 r=input;if(!ResultShape(r)){r.status=TedTransitionStatus267V1::indeterminate;r.accepted=false;r.source_available=false;r.source.reset();r.cleanup_known=false;r.reason="ted_internal_result_coherence_unavailable_no_permission";}
 const bool okay=ResultShape(r)&&IsOkay(r.status);Json j;j.data="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(j.data,id);j.flag("ok",okay);j.key("result");j.data+="{\"schema\":";String(j.data,kTedTransitionResultSchema267V1);j.str("backend",kTedTransitionBackend267V1);j.str("action",Actions[static_cast<unsigned>(r.action)<4?static_cast<unsigned>(r.action):0]);j.str("request_id",r.request_id);j.str("operation_id",r.operation_id);j.str("status",Statuses[static_cast<unsigned>(r.status)<12?static_cast<unsigned>(r.status):0]);j.flag("ok",okay);j.flag("accepted",r.accepted);j.flag("source_available",r.source_available);j.str("unavailable_reason",r.reason);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.u64("actor_epoch",r.actor_epoch);j.num("deadline_unix_ms",static_cast<std::int64_t>(r.deadline_unix_ms));j.u64("connection_generation",r.connection_generation);j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.key("facts_before");if(r.facts_available)EmitCore(j,r.facts);else j.data+="null";j.key("source");if(r.source)EmitSource(j,*r.source);else j.data+="null";j.key("progress");if(r.progress)EmitProgress(j,*r.progress);else j.data+="null";j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("cleanup_known",r.cleanup_known);j.key("core_after");j.data+="null}}";return j.data;
}
} // namespace

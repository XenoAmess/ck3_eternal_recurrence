#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
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

bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p) noexcept {
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;
  if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}
  else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}
  else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}
  else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}
  else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}
  else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}
  else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}
  else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }
 return seen==255;
}
bool Claim(Cursor&c,DateAdvanceRequest267V1&r) noexcept {
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;
  if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kDateAdvanceSchema267V1);}
  else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
  else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
  else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
  else if(key=="backend"){bit=16;good=c.Identity(kGuiWindowBackendV1);}
  else if(key=="deadline_unix_ms"){bit=32;good=c.Number(r.deadline_unix_ms)&&r.deadline_unix_ms>0;}
  else if(key=="expected_core"){bit=64;good=Core(c,r.expected_core);}
  else if(key=="operation_id"){
   bit=128;good=c.String(value)&&Id(value);
   if(good){std::copy(value.begin(),value.end(),r.operation_id.begin());r.operation_id_size=static_cast<std::uint8_t>(value.size());}
  }
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }
 return seen==255;
}
bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
  a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
  a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
const char*Status(DateAdvanceStatus267V1 s) noexcept {
 using S=DateAdvanceStatus267V1;switch(s){case S::expired:return "expired";case S::stale_core:return "stale_core_prefix";
 case S::source_changed:return "source_changed";case S::claim_consumed:return "claim_consumed";
 case S::capacity_exhausted:return "capacity_exhausted";case S::submitted:return "submitted";case S::running:return "running";
 case S::completed:return "completed";case S::rejected:return "rejected";case S::indeterminate:return "indeterminate";
 default:return "unavailable";}
}
const char*State(ck3_11906::TacticalDailySentinelStateV1 s) noexcept {
 using S=ck3_11906::TacticalDailySentinelStateV1;switch(s){case S::idle:return "idle";case S::armed:return "armed";
 case S::triggered:return "triggered";case S::failed:return "failed";default:return "unavailable";}
}
bool Before(const DateAdvanceRequest267V1&q,const DateAdvanceResult267V1&r) noexcept {
 return r.owner_before_verified&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id&&Same(q.expected_core,r.core_before);
}
bool Completed(const DateAdvanceRequest267V1&q,const DateAdvanceResult267V1&r) noexcept {
 const auto&s=r.sentinel;const auto start=q.expected_core.clock.date_raw;
 return DateAdvanceRequestShape267V1(q)&&r.claim_found&&r.claim_sequence&&r.generation&&Before(q,r)&&
  r.arm_attempted&&r.resume_attempted&&r.resume_submitted&&r.exact_day_confirmed&&r.shutdown_safe&&!r.armed&&
  !r.access_cleanup_unknown&&!r.failure_flags&&s.generation==r.generation&&s.state==ck3_11906::TacticalDailySentinelStateV1::triggered&&
  s.mode==ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel&&s.army_count==0&&s.combat_count==0&&
  s.starting_date_raw==start&&s.target_date_raw==start+24&&s.last_observed_date_raw==start+24&&s.trigger_date_raw==start+24&&
  s.speed==q.expected_core.clock.speed&&s.completed_daily_ticks==1&&s.signed_date_delta_from_target_raw==0&&s.overshoot_days==0&&
  s.trigger_flags==ck3_11906::tactical_daily_trigger_date_deadline&&s.pause_observed&&s.pause_wrapper_called&&!s.terminal_observed&&!s.abnormal;
}
void CoreJson(std::string&out,const ck3_1210::CoreSnapshotPrefix&p){
 out+="{\"date_raw\":"+std::to_string(p.clock.date_raw)+",\"speed\":"+std::to_string(p.clock.speed)+",\"paused\":"+(p.clock.paused?"true":"false");
 out+=",\"local_player_id\":"+std::to_string(p.local_player_id)+",\"map_ready\":"+(p.map_ready?"true":"false");
 out+=",\"has_played_character\":";out+=p.has_played_character?"true":"false";
 out+=",\"played_character_id\":"+std::to_string(p.played_character_id)+",\"played_character_alive\":"+(p.played_character_alive?"true":"false")+'}';
}
} // namespace
bool ParseDateAdvanceRequest267V1(std::string_view text,DateAdvanceRequest267V1&out) noexcept {
 out={};if(text.size()>16384)return false;Cursor c{text};DateAdvanceRequest267V1 r;
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;
  if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}
  else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}
  else if(key=="request_id"){
   bit=4;good=c.String(value)&&Id(value);
   if(good){std::copy(value.begin(),value.end(),r.request_id.begin());r.request_id_size=static_cast<std::uint8_t>(value.size());}
  }
  else if(key=="step"){
   bit=8;good=c.String(value)&&(value==kDateAdvanceStep267V1||value==kDateAdvanceStatusStep267V1);
   if(good)r.status_query=value==kDateAdvanceStatusStep267V1;
  }
  else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}
  else if(key=="date_advance"){bit=32;good=Claim(c,r);}
  else if(key=="arguments"){bit=64;good=c.Take('{')&&c.Take('}');}
  if(!good||!bit||(seen&bit))return false;seen|=bit;
 }
 c.Space();if(seen!=127||c.pos!=text.size()||!DateAdvanceRequestShape267V1(r))return false;out=r;return true;
}
std::string SerializeDateAdvanceResult267V1(std::string_view id,const DateAdvanceRequest267V1&q,const DateAdvanceResult267V1&r){
 const bool before=Before(q,r),complete=Completed(q,r);
 const bool accepted=!q.status_query&&r.status==DateAdvanceStatus267V1::submitted&&DateAdvanceRequestShape267V1(q)&&
  r.claim_found&&r.claim_sequence&&r.generation&&before&&r.arm_attempted&&r.resume_attempted&&r.resume_submitted&&
  r.sentinel.generation==r.generation&&r.sentinel.state==ck3_11906::TacticalDailySentinelStateV1::armed&&
  r.sentinel.mode==ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel&&r.sentinel.army_count==0&&r.sentinel.combat_count==0&&
  r.sentinel.starting_date_raw==q.expected_core.clock.date_raw&&r.sentinel.target_date_raw==q.expected_core.clock.date_raw+24&&
  r.sentinel.speed==q.expected_core.clock.speed;
 const auto status=(r.status==DateAdvanceStatus267V1::completed&&!complete)||
  (r.status==DateAdvanceStatus267V1::submitted&&!q.status_query&&!accepted)?DateAdvanceStatus267V1::indeterminate:r.status;
 const bool ok=q.status_query?r.claim_found:accepted;
 std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(out,id);
 out+=ok?",\"ok\":true,\"result\":{\"schema\":":",\"ok\":false,\"result\":{\"schema\":";String(out,kDateAdvanceResultSchema267V1);
 out+=",\"game_version\":";String(out,kGameVersion);out+=",\"executable_sha256\":";String(out,kExecutableSha256);
 out+=",\"adapter_id\":";String(out,kAdapterId);out+=",\"backend\":";String(out,kGuiWindowBackendV1);
 out+=",\"step\":";String(out,q.step());out+=",\"status\":";String(out,Status(status));
 out+=",\"operation_id\":";String(out,q.operation());
 const auto boolean=[&](const char*name,bool v){out+=",\"";out+=name;out+="\":";out+=v?"true":"false";};
 boolean("accepted",accepted);boolean("claim_found",r.claim_found);boolean("owner_before_verified",before);
 boolean("arm_attempted",r.arm_attempted);boolean("resume_attempted",r.resume_attempted);boolean("resume_submitted",r.resume_submitted);
 boolean("exact_day_confirmed",complete);boolean("shutdown_safe",r.shutdown_safe);boolean("armed",r.armed);
 boolean("access_cleanup_unknown",r.access_cleanup_unknown);boolean("complete_snapshot",false);boolean("physical_save_confirmed",false);
 out+=",\"failure_flags\":"+std::to_string(r.failure_flags);
 const auto u64=[&](const char*name,std::uint64_t n){out+=",\"";out+=name;out+="\":";if(n)String(out,std::to_string(n));else out+="null";};
 u64("claim_sequence",r.claim_sequence);u64("generation",r.generation);
 out+=",\"core_before\":";if(before)CoreJson(out,r.core_before);else out+="null";
 // No fresh after-Core is manufactured from the terminal date/paused fields.
 out+=",\"core_after\":null,\"owner_witness\":";
 if(before){out+="{\"connection_generation\":";String(out,std::to_string(r.connection_generation));
  out+=",\"ticket_sequence\":";String(out,std::to_string(r.ticket_sequence));out+=",\"pump_epoch\":";String(out,std::to_string(r.pump_epoch));
  out+=",\"thread_id\":"+std::to_string(r.thread_id)+'}';}else out+="null";
 out+=",\"sentinel\":";
  if(r.claim_found&&r.generation){const auto&s=r.sentinel;out+="{\"state\":";String(out,State(s.state));
  out+=",\"generation\":";if(s.generation)String(out,std::to_string(s.generation));else out+="null";
  out+=",\"mode\":";String(out,s.mode==ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel?"terminal_or_sentinel":"unavailable");
  out+=",\"army_count\":"+std::to_string(s.army_count)+",\"combat_count\":"+std::to_string(s.combat_count);
  out+=",\"starting_date_raw\":"+std::to_string(s.starting_date_raw)+",\"target_date_raw\":"+std::to_string(s.target_date_raw);
  out+=",\"last_observed_date_raw\":"+std::to_string(s.last_observed_date_raw)+",\"trigger_date_raw\":"+std::to_string(s.trigger_date_raw);
  out+=",\"speed\":"+std::to_string(s.speed)+",\"completed_daily_ticks\":"+std::to_string(s.completed_daily_ticks);
  out+=",\"trigger_flags\":"+std::to_string(s.trigger_flags)+",\"signed_date_delta_from_target_raw\":"+std::to_string(s.signed_date_delta_from_target_raw);
  out+=",\"overshoot_days\":"+std::to_string(s.overshoot_days);
  out+=",\"pause_wrapper_called\":";out+=s.pause_wrapper_called?"true":"false";
  out+=",\"pause_observed\":";out+=s.pause_observed?"true":"false";
  out+=",\"combat_terminal_observed\":";out+=s.terminal_observed?"true":"false";
  out+=",\"abnormal\":";out+=s.abnormal?"true":"false";out+='}';
 }else out+="null";
 out+="}}";return out;
}
} // namespace

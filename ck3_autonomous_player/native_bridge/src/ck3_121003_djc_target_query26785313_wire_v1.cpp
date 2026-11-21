#include "xar_bridge/ck3_121003_djc_target_query26785313_v1.hpp"
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
bool Claim(Cursor&c,DjcTargetQueryRequest267V1&q) noexcept {
  auto&p=q.expected;if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;
    if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
    if(key=="schema"){bit=1;good=c.Identity(kDjcTargetQuerySchema267V1);}
    else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
    else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
    else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
    else if(key=="backend"){bit=16;good=c.Identity(kDjcTargetQueryBackend267V1);}
    else if(key=="date_raw"){bit=32;good=c.Number(p.clock.date_raw);}
    else if(key=="speed"){bit=64;good=c.Number(p.clock.speed);}
    else if(key=="paused"){bit=128;good=c.Boolean(p.clock.paused);}
    else if(key=="local_player_id"){bit=256;good=c.Number(p.local_player_id);}
    else if(key=="map_ready"){bit=512;good=c.Boolean(p.map_ready);}
    else if(key=="has_played_character"){bit=1024;good=c.Boolean(p.has_played_character);}
    else if(key=="played_character_id"){bit=2048;good=c.Number(p.played_character_id);}
    else if(key=="played_character_alive"){bit=4096;good=c.Boolean(p.played_character_alive);}
    else if(key=="target_character_id"){bit=8192;good=c.Number(q.target_character_id);}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  return seen==16383&&p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&
      p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
void String(std::string&out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);
  }out+='"';
}
bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
const char*Name(DjcTargetQueryStatus267V1 v)noexcept{using S=DjcTargetQueryStatus267V1;switch(v){case S::available:return "available";case S::expired:return "expired";case S::stale_core:return "stale_core";case S::indeterminate:return "indeterminate";default:return "unavailable";}}
bool Choices(const DjcRawTarget267V1&r)noexcept{
 if(!r.available||!r.cleanup_known||r.target_character_id==-1)return false;
 for(std::size_t i=0;i<3;++i){const auto&cb=r.casus_belli[i];if(cb.key!=kDjcCbKeys267V1[i]||!cb.definition_present)return false;
  if(cb.enabled){if(!cb.evaluation_returned||!cb.native_available.has_value())return false;}
  else if(cb.evaluation_returned||cb.native_available.has_value()||!cb.choices.empty())return false;
  if(!cb.native_available.value_or(false)&&!cb.choices.empty())return false;
  for(const auto&choice:cb.choices){if(choice.casus_belli_index<0||choice.configuration_index< -1||choice.target_title_ids.size()>10000||choice.extra_configuration_ids.size()>10000)return false;for(auto id:choice.target_title_ids)if(id==-1)return false;}
 }return true;
}
}
bool DjcTargetQueryRequestShape267V1(const DjcTargetQueryRequest267V1&q)noexcept{return Id(q.id())&&q.deadline_unix_ms&&Prefix(q.expected)&&q.target_character_id!=-1&&q.target_character_id!=q.expected.played_character_id;}
bool ParseDjcTargetQueryRequest267V1(std::string_view text,DjcTargetQueryRequest267V1&out) noexcept {
  out={};if(text.size()>16384)return false;Cursor c{text};DjcTargetQueryRequest267V1 parsed;
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key,id;
    if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;std::uint64_t number=0;
    if(key=="type"){bit=1;good=c.Identity("execute_step");}
    else if(key=="protocol_version"){bit=2;good=c.Number(number)&&number==1;}
    else if(key=="request_id") {
      bit=4;good=c.String(id)&&Id(id);
      if(good){std::copy(id.begin(),id.end(),parsed.request_id.begin());parsed.request_id_size=static_cast<std::uint8_t>(id.size());}
    }
    else if(key=="step"){bit=8;good=c.Identity(kDjcTargetQueryStep267V1);}
    else if(key=="expected_revision"){bit=16;good=c.Number(number)&&number==0;}
    else if(key=="djc_war_query"){bit=32;good=Claim(c,parsed);}
    else if(key=="core_control_deadline_unix_ms") {
      bit=64;good=c.Number(parsed.deadline_unix_ms)&&parsed.deadline_unix_ms>0;
    }
    else if(key=="arguments"){bit=128;good=c.Take('{')&&c.Take('}');}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  c.Space();if(seen!=255||c.pos!=text.size())return false;
  if(!DjcTargetQueryRequestShape267V1(parsed))return false;out=parsed;return true;
}

std::string SerializeDjcTargetQueryResult267V1(std::string_view id,const DjcTargetQueryResult267V1&r){
 const bool facts=r.core_available&&Prefix(r.observed)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool available=r.status==DjcTargetQueryStatus267V1::available&&facts&&Choices(r.raw)&&r.provider_generation&&r.query_sequence;
 const auto status=r.status==DjcTargetQueryStatus267V1::available&&!available?DjcTargetQueryStatus267V1::indeterminate:r.status;
 std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";String(out,id);out+=available?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(out,kDjcTargetQueryResultSchema267V1);
 const auto text=[&](const char*k,std::string_view v){out+=",\"";out+=k;out+="\":";String(out,v);};
 const auto flag=[&](const char*k,bool v){out+=",\"";out+=k;out+=v?"\":true":"\":false";};
 text("game_version",kGameVersion);text("executable_sha256",kExecutableSha256);text("adapter_id",kAdapterId);text("backend",kDjcTargetQueryBackend267V1);text("step",kDjcTargetQueryStep267V1);text("status",Name(status));flag("available",available);flag("scratch_cleanup_known",r.raw.cleanup_known);
 out+=",\"target_character_id\":"+std::to_string(r.raw.target_character_id);text("provider_generation",std::to_string(r.provider_generation));text("query_sequence",std::to_string(r.query_sequence));
 out+=",\"core_before\":";
 if(facts){const auto&p=r.observed;out+="{\"date_raw\":"+std::to_string(p.clock.date_raw)+",\"speed\":"+std::to_string(p.clock.speed);flag("paused",p.clock.paused);out+=",\"local_player_id\":"+std::to_string(p.local_player_id);flag("map_ready",p.map_ready);flag("has_played_character",p.has_played_character);out+=",\"played_character_id\":"+std::to_string(p.played_character_id);flag("played_character_alive",p.played_character_alive);out+='}';out+=",\"owner_witness\":{\"connection_generation\":";String(out,std::to_string(r.connection_generation));text("ticket_sequence",std::to_string(r.ticket_sequence));text("pump_epoch",std::to_string(r.pump_epoch));out+=",\"thread_id\":"+std::to_string(r.thread_id)+'}';}else out+="null,\"owner_witness\":null";
 out+=",\"casus_belli\":";
 if(available){out+='[';for(std::size_t i=0;i<3;++i){if(i)out+=',';const auto&cb=r.raw.casus_belli[i];out+="{\"key\":";String(out,cb.key);flag("definition_present",cb.definition_present);flag("enabled",cb.enabled);flag("native_evaluation_returned",cb.evaluation_returned);flag("selection_materialization_available",cb.selection_materialization_available);out+=",\"native_available\":";if(cb.native_available.has_value())out+=*cb.native_available?"true":"false";else out+="null";out+=",\"choices\":[";
  for(std::size_t j=0;j<cb.choices.size();++j){if(j)out+=',';const auto&c=cb.choices[j];out+="{\"casus_belli_index\":"+std::to_string(c.casus_belli_index)+",\"configuration_index\":"+std::to_string(c.configuration_index)+",\"claimant_character_id\":"+std::to_string(c.claimant_character_id)+",\"target_title_ids\":[";for(std::size_t n=0;n<c.target_title_ids.size();++n){if(n)out+=',';out+=std::to_string(c.target_title_ids[n]);}out+="],\"extra_configuration_ids\":[";for(std::size_t n=0;n<c.extra_configuration_ids.size();++n){if(n)out+=',';out+=std::to_string(c.extra_configuration_ids[n]);}out+="]}";}out+="]}";}out+=']';}else out+="null";
 flag("addresses_redacted",true);flag("read_only",true);out+=",\"ordinary_can_declare_war\":null,\"total_debit\":null";flag("submission_available",false);flag("war_submission_attempted",false);flag("war_submitted",false);out+=",\"war_id\":null,\"unavailable_reason\":";if(available)out+="null";else String(out,r.reason.empty()?(r.raw.reason.empty()?"current_djc_target_query_unavailable":r.raw.reason):r.reason);out+="}}";return out;
}
}

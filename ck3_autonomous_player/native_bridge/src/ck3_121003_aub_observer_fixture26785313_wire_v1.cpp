#include "xar_bridge/ck3_121003_aub_observer_fixture26785313_v1.hpp"
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
bool Claim(Cursor&c,ck3_1210::CoreSnapshotPrefix&p) noexcept {
  if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
  while(!c.Take('}')) {
    if(!first&&!c.Take(','))return false;first=false;std::string_view key;
    if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
    if(key=="schema"){bit=1;good=c.Identity(kAubObserverFixtureSchema267V1);}
    else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}
    else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}
    else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}
    else if(key=="backend"){bit=16;good=c.Identity(kAubObserverFixtureBackend267V1);}
    else if(key=="date_raw"){bit=32;good=c.Number(p.clock.date_raw);}
    else if(key=="speed"){bit=64;good=c.Number(p.clock.speed);}
    else if(key=="paused"){bit=128;good=c.Boolean(p.clock.paused);}
    else if(key=="local_player_id"){bit=256;good=c.Number(p.local_player_id);}
    else if(key=="map_ready"){bit=512;good=c.Boolean(p.map_ready);}
    else if(key=="has_played_character"){bit=1024;good=c.Boolean(p.has_played_character);}
    else if(key=="played_character_id"){bit=2048;good=c.Number(p.played_character_id);}
    else if(key=="played_character_alive"){bit=4096;good=c.Boolean(p.played_character_alive);}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  return seen==8191&&p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&
      p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
void String(std::string&out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);
  }out+='"';
}
const char*Name(AubObserverFixtureStatus267V1 v)noexcept{using S=AubObserverFixtureStatus267V1;switch(v){case S::expired:return "expired";case S::stale_core:return "stale_core";case S::claim_consumed:return "claim_consumed";case S::source_changed:return "source_changed";case S::dispatched:return "dispatched";case S::indeterminate:return "indeterminate";default:return "unavailable";}}
bool Hash(std::string_view h)noexcept{if(h.size()!=64)return false;for(char c:h)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;}
bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
}
bool AubObserverFixtureRequestShape267V1(const AubObserverFixtureRequest267V1&q)noexcept{return Id(q.id())&&q.deadline_unix_ms>0&&Prefix(q.expected);}
bool ParseAubObserverFixtureRequest267V1(std::string_view text,AubObserverFixtureRequest267V1&out) noexcept {
  out={};if(text.size()>16384)return false;Cursor c{text};AubObserverFixtureRequest267V1 parsed;
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
    else if(key=="step"){bit=8;good=c.Identity(kAubObserverFixtureStep267V1);}
    else if(key=="expected_revision"){bit=16;good=c.Number(number)&&number==0;}
    else if(key=="aub_observer_fixture"){bit=32;good=Claim(c,parsed.expected);}
    else if(key=="core_control_deadline_unix_ms") {
      bit=64;good=c.Number(parsed.deadline_unix_ms)&&parsed.deadline_unix_ms>0;
    }
    else if(key=="arguments"){bit=128;good=c.Take('{')&&c.Take('}');}
    if(!good||!bit||(seen&bit))return false;seen|=bit;
  }
  c.Space();if(seen!=255||c.pos!=text.size())return false;
  if(!AubObserverFixtureRequestShape267V1(parsed))return false;out=parsed;return true;
}
std::string SerializeAubObserverFixtureResult267V1(std::string_view id,const AubObserverFixtureResult267V1&r){
 const bool facts=r.core_available&&Prefix(r.observed)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool accepted=r.status==AubObserverFixtureStatus267V1::dispatched&&facts&&r.effect_attempted&&r.native_returned&&r.native_accepted&&r.cleanup_known&&r.claim_sequence&&r.file_verified&&r.file_verified_after&&Hash(r.inbox_sha256);
 const auto status=r.status==AubObserverFixtureStatus267V1::dispatched&&!accepted?AubObserverFixtureStatus267V1::indeterminate:r.status;
 std::string out=R"({"type":"command_result","protocol_version":1,"request_id":)";String(out,id);out+=accepted?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(out,kAubObserverFixtureResultSchema267V1);
 const auto field=[&](const char*k,std::string_view v){out+=",\"";out+=k;out+="\":";String(out,v);};
 const auto flag=[&](const char*k,bool v){out+=",\"";out+=k;out+=v?"\":true":"\":false";};
 field("game_version",kGameVersion);field("executable_sha256",kExecutableSha256);field("adapter_id",kAdapterId);field("backend",kAubObserverFixtureBackend267V1);field("step",kAubObserverFixtureStep267V1);field("status",Name(status));
 flag("effect_attempted",r.effect_attempted);flag("native_returned",r.native_returned);flag("native_accepted",r.native_accepted);flag("cleanup_known",r.cleanup_known);field("claim_sequence",std::to_string(r.claim_sequence));field("inbox_filename",kAubObserverFixtureFilename267V1);
 out+=",\"inbox_sha256\":";if(Hash(r.inbox_sha256))String(out,r.inbox_sha256);else out+="null";flag("file_verified",r.file_verified);flag("file_verified_after",r.file_verified_after);
 out+=",\"core_before\":";if(facts){const auto&p=r.observed;out+="{\"date_raw\":"+std::to_string(p.clock.date_raw)+",\"speed\":"+std::to_string(p.clock.speed);flag("paused",p.clock.paused);out+=",\"local_player_id\":"+std::to_string(p.local_player_id);flag("map_ready",p.map_ready);flag("has_played_character",p.has_played_character);out+=",\"played_character_id\":"+std::to_string(p.played_character_id);flag("played_character_alive",p.played_character_alive);out+='}';out+=",\"owner_witness\":{\"connection_generation\":";String(out,std::to_string(r.connection_generation));field("ticket_sequence",std::to_string(r.ticket_sequence));field("pump_epoch",std::to_string(r.pump_epoch));out+=",\"thread_id\":"+std::to_string(r.thread_id)+'}';}else out+="null,\"owner_witness\":null";
 flag("addresses_redacted",true);flag("observer_markers_confirmed",false);flag("business_pass_confirmed",false);flag("production_actions_confirmed",false);flag("physical_save_confirmed",false);out+=",\"unavailable_reason\":";if(accepted)out+="null";else String(out,r.reason.empty()?"current_fixed_fixture_not_qualified":r.reason);out+="}}";return out;
}
}

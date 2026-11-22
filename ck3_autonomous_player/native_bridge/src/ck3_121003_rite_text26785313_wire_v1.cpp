#include "xar_bridge/ck3_121003_rite_text26785313_v1.hpp"
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
  bool Utf8String(std::string&out)noexcept{out.clear();try{
    if(!Take('"'))return false;
    const auto hex=[&](std::uint32_t&v){v=0;for(int i=0;i<4;++i){if(pos==text.size())return false;const auto c=text[pos++];unsigned digit=0;if(c>='0'&&c<='9')digit=static_cast<unsigned>(c-'0');else if(c>='a'&&c<='f')digit=static_cast<unsigned>(c-'a'+10);else if(c>='A'&&c<='F')digit=static_cast<unsigned>(c-'A'+10);else return false;v=(v<<4)|digit;}return true;};
    const auto scalar=[&](std::uint32_t cp){if(cp<0x80)out+=static_cast<char>(cp);else if(cp<0x800){out+=static_cast<char>(0xC0|(cp>>6));out+=static_cast<char>(0x80|(cp&63));}else if(cp<0x10000){out+=static_cast<char>(0xE0|(cp>>12));out+=static_cast<char>(0x80|((cp>>6)&63));out+=static_cast<char>(0x80|(cp&63));}else{out+=static_cast<char>(0xF0|(cp>>18));out+=static_cast<char>(0x80|((cp>>12)&63));out+=static_cast<char>(0x80|((cp>>6)&63));out+=static_cast<char>(0x80|(cp&63));}};
    while(pos<text.size()){const auto c=static_cast<unsigned char>(text[pos++]);if(c=='"')return true;if(c<0x20)return false;if(c!='\\')out+=static_cast<char>(c);else{if(pos==text.size())return false;const auto e=text[pos++];switch(e){case '"':out+='"';break;case '\\':out+='\\';break;case '/':out+='/';break;case 'b':out+='\b';break;case 'f':out+='\f';break;case 'n':out+='\n';break;case 'r':out+='\r';break;case 't':out+='\t';break;case 'u':{std::uint32_t cp=0;if(!hex(cp))return false;if(cp>=0xD800&&cp<=0xDBFF){if(pos+2>text.size()||text[pos++]!='\\'||text[pos++]!='u')return false;std::uint32_t low=0;if(!hex(low)||low<0xDC00||low>0xDFFF)return false;cp=0x10000+((cp-0xD800)<<10)+(low-0xDC00);}else if(cp>=0xDC00&&cp<=0xDFFF)return false;scalar(cp);break;}default:return false;}}if(out.size()>4096)return false;}return false;
   }catch(...){out.clear();return false;}}
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

bool U64(Cursor&c,std::uint64_t&v)noexcept{std::string_view s;if(!c.String(s)||s.empty()||(s.size()>1&&s.front()=='0'))return false;for(char x:s)if(x<'0'||x>'9')return false;const auto r=std::from_chars(s.data(),s.data()+s.size(),v);return r.ec==std::errc{}&&r.ptr==s.data()+s.size();}

bool Utf8(std::string_view text,std::size_t maxbytes,std::size_t maxscalars,bool write,bool description)noexcept{
 if(text.size()>maxbytes)return false;std::size_t count=0;
 for(std::size_t i=0;i<text.size();){auto c=static_cast<unsigned char>(text[i++]);std::uint32_t cp=0;unsigned n=0;if(c<0x80)cp=c;else if(c>=0xC2&&c<=0xDF){cp=c&31;n=1;}else if(c>=0xE0&&c<=0xEF){cp=c&15;n=2;}else if(c>=0xF0&&c<=0xF4){cp=c&7;n=3;}else return false;
  if(i+n>text.size())return false;for(unsigned j=0;j<n;++j){const auto b=static_cast<unsigned char>(text[i++]);if((b&0xC0)!=0x80)return false;cp=(cp<<6)|(b&63);}if((n==1&&cp<0x80)||(n==2&&cp<0x800)||(n==3&&cp<0x10000)||cp>0x10FFFF||(cp>=0xD800&&cp<=0xDFFF)||++count>maxscalars)return false;
  if(write&&(cp<0x20||cp==0x7F)&&!(description&&(cp==9||cp==10)))return false;
 }return true;
}
bool Action(Cursor&c,RiteTextAction267V1&a)noexcept{std::string_view s;if(!c.String(s))return false;if(s=="query")a=RiteTextAction267V1::query;else if(s=="set_name")a=RiteTextAction267V1::set_name;else if(s=="set_description")a=RiteTextAction267V1::set_description;else return false;return true;}
bool Claim(Cursor&c,RiteTextRequest267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="schema"){bit=1;good=c.Identity(kRiteTextRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kRiteTextBackend267V1);}else if(k=="action"){bit=32;good=Action(c,q.action);}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="expected_source_rite_id"){bit=128;good=c.Number(q.expected_source_rite_id)&&q.expected_source_rite_id!=0xFFFFFFFFU;}else if(k=="provider_generation"){bit=256;good=U64(c,q.provider_generation);}else if(k=="query_sequence"){bit=512;good=U64(c,q.query_sequence);}else if(k=="text"){bit=1024;good=c.Utf8String(q.text);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==2047;
}
const char*ActionName(RiteTextAction267V1 a)noexcept{switch(a){case RiteTextAction267V1::set_name:return"set_name";case RiteTextAction267V1::set_description:return"set_description";default:return"query";}}
const char*Status(RiteTextStatus267V1 s)noexcept{switch(s){case RiteTextStatus267V1::available:return"available";case RiteTextStatus267V1::expired:return"expired";case RiteTextStatus267V1::stale_source:return"stale_source";case RiteTextStatus267V1::claim_consumed:return"claim_consumed";case RiteTextStatus267V1::prerequisite_rejected:return"prerequisite_rejected";case RiteTextStatus267V1::text_dispatched:return"text_dispatched";case RiteTextStatus267V1::indeterminate:return"indeterminate";default:return"unavailable";}}
struct Json{std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}};
bool SourceShape(const RiteTextSource267V1&s,const ck3_1210::CoreSnapshotPrefix&c)noexcept{return s.source_rite_id!=0xFFFFFFFFU&&s.actor_id!=-1&&s.actor_id==c.played_character_id&&Utf8(s.name,4096,4096,false,false)&&Utf8(s.description,4096,4096,false,true)&&(!s.write_admissible||(s.is_creating&&s.window_visible&&s.window_enabled&&!s.blocked_by_unrelated_modal));}
bool PositiveShape(const RiteTextResult267V1&r)noexcept{if(!r.cleanup_known||!r.facts_available||!Prefix(r.facts)||!r.connection_generation||!r.ticket_sequence||!r.pump_epoch||!r.thread_id||!r.source_available||!r.source||!SourceShape(*r.source,r.facts)||!r.provider_generation||!r.query_sequence||r.native_handled)return false;
 if(r.status==RiteTextStatus267V1::available)return r.action==RiteTextAction267V1::query&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned;
 return r.status==RiteTextStatus267V1::text_dispatched&&(r.action==RiteTextAction267V1::set_name||r.action==RiteTextAction267V1::set_description)&&r.source->write_admissible&&r.claim_sequence&&r.effect_attempted&&r.native_returned;
}
void Source(Json&j,const RiteTextSource267V1&s){j.data+="{\"schema\":";String(j.data,kRiteTextSourceSchema267V1);j.num("source_rite_id",s.source_rite_id);j.num("actor_id",s.actor_id);j.flag("is_creating",s.is_creating);j.str("name",s.name);j.str("description",s.description);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.flag("blocked_by_unrelated_modal",s.blocked_by_unrelated_modal);j.flag("write_admissible",s.write_admissible);j.data+='}';}
}
bool RiteTextRequestShape267V1(const RiteTextRequest267V1&q)noexcept{return Id(q.id())&&q.deadline_unix_ms&&Prefix(q.expected)&&q.expected_source_rite_id!=0xFFFFFFFFU&&(q.action==RiteTextAction267V1::query?(!q.provider_generation&&!q.query_sequence&&q.text.empty()):((q.action==RiteTextAction267V1::set_name||q.action==RiteTextAction267V1::set_description)&&q.provider_generation&&q.query_sequence&&Utf8(q.text,q.action==RiteTextAction267V1::set_name?120:1600,q.action==RiteTextAction267V1::set_name?30:400,true,q.action==RiteTextAction267V1::set_description)));}
bool ParseRiteTextRequest267V1(std::string_view text,RiteTextRequest267V1&out)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};RiteTextRequest267V1 q;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k,v;unsigned bit=0;bool good=false;std::uint64_t n=0;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(k=="request_id"){bit=4;good=c.String(v)&&Id(v);if(good){std::copy(v.begin(),v.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(v.size());}}else if(k=="step"){bit=8;good=c.Identity(kRiteTextStep267V1);}else if(k=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(k=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(k=="rite_text"){bit=64;good=Claim(c,q);}else if(k=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!RiteTextRequestShape267V1(q))return false;try{out=std::move(q);return true;}catch(...){out={};return false;}
}
std::string SerializeRiteTextResult267V1(std::string_view id,const RiteTextResult267V1&r){
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool positive=r.status==RiteTextStatus267V1::available||r.status==RiteTextStatus267V1::text_dispatched;
 const bool ok=positive&&PositiveShape(r);auto status=r.status;if(!r.cleanup_known||(positive&&!ok))status=RiteTextStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kRiteTextResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kRiteTextBackend267V1);j.str("action",ActionName(r.action));j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(ok)Source(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.flag("text_applied",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"rite_text_actual_source_or_internal_coherence_unavailable":r.reason);j.data+="}}";return j.data;
}
}

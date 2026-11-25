#include "xar_bridge/ck3_121003_zg361_ae226785313_v1.hpp"
#include <algorithm>
#include <bit>
#include <charconv>

namespace xar::ck3_121003::build26785313 { namespace {
// Fixed request strings are ASCII identifiers. Runtime text is serialized by
// explicit length below; the request has no caller text/key/index parameter.
struct Cursor {
 std::string_view text;std::size_t pos=0;
 void Space()noexcept{while(pos<text.size()&&(text[pos]==' '||text[pos]=='\n'||text[pos]=='\r'||text[pos]=='\t'))++pos;}
 bool Take(char ch)noexcept{Space();if(pos==text.size()||text[pos]!=ch)return false;++pos;return true;}
 bool String(std::string_view&out)noexcept{
  if(!Take('"'))return false;const auto start=pos;
  while(pos<text.size()&&text[pos]!='"'){const auto c=static_cast<unsigned char>(text[pos]);if(c<0x20||c>=0x7F||c=='\\'||pos-start>=192)return false;++pos;}
  if(pos==text.size())return false;out=text.substr(start,pos++-start);return true;
 }
 template<class T>bool Number(T&out)noexcept{
  Space();const auto start=pos;if(pos<text.size()&&text[pos]=='-')++pos;const auto digits=pos;
  while(pos<text.size()&&text[pos]>='0'&&text[pos]<='9')++pos;
  if(pos==digits||(pos-digits>1&&text[digits]=='0'))return false;
  T value{};const auto parsed=std::from_chars(text.data()+start,text.data()+pos,value);
  if(parsed.ec!=std::errc{}||parsed.ptr!=text.data()+pos||(text[start]=='-'&&value==0))return false;out=value;return true;
 }
 bool U64(std::uint64_t&out)noexcept{
  std::string_view value;if(!String(value)||value.empty()||(value.size()>1&&value.front()=='0'))return false;
  for(const char c:value)if(c<'0'||c>'9')return false;
  std::uint64_t parsed=0;const auto r=std::from_chars(value.data(),value.data()+value.size(),parsed);
  if(r.ec!=std::errc{}||r.ptr!=value.data()+value.size())return false;out=parsed;return true;
 }
 bool Boolean(bool&out)noexcept{
  Space();if(text.substr(pos,4)=="true"){pos+=4;out=true;return true;}
  if(text.substr(pos,5)=="false"){pos+=5;out=false;return true;}return false;
 }
 bool Identity(std::string_view expected,bool hash=false)noexcept{
  std::string_view actual;if(!String(actual)||actual.size()!=expected.size())return false;
  for(std::size_t i=0;i<actual.size();++i){auto c=actual[i];if(hash&&c>='a'&&c<='f')c=static_cast<char>(c-'a'+'A');if(c!=expected[i])return false;}return true;
 }
};
bool Id(std::string_view value)noexcept{
 if(value.empty()||value.size()>96)return false;
 for(const char c:value)if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='-'||c=='_'||c=='.'))return false;
 return true;
}
bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{
 return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
}
bool Action(Cursor&c,Zg361Ae2Action267V1&out)noexcept{
 std::string_view name;if(!c.String(name))return false;
 for(std::size_t n=0;n<kZg361Ae2Actions267V1.size();++n)if(name==kZg361Ae2Actions267V1[n]){out=static_cast<Zg361Ae2Action267V1>(n);return true;}
 return false;
}
bool Claim(Cursor&c,Zg361Ae2Request267V1&q)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kZg361Ae2RequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(key=="backend"){bit=16;good=c.Identity(kZg361Ae2Backend267V1);}else if(key=="action"){bit=32;good=Action(c,q.action);}else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=c.U64(q.provider_generation);}else if(key=="query_sequence"){bit=256;good=c.U64(q.query_sequence);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==511;
}
bool Utf8(std::string_view text)noexcept{
 if(text.size()>16384)return false;
 for(std::size_t i=0;i<text.size();){const auto c=static_cast<unsigned char>(text[i++]);if(c<0x80)continue;
  unsigned n=0;std::uint32_t value=0,min=0;
  if((c&0xE0)==0xC0){n=1;value=c&31;min=0x80;}else if((c&0xF0)==0xE0){n=2;value=c&15;min=0x800;}else if((c&0xF8)==0xF0){n=3;value=c&7;min=0x10000;}else return false;
  if(n>text.size()-i)return false;while(n--){const auto z=static_cast<unsigned char>(text[i++]);if((z&0xC0)!=0x80)return false;value=(value<<6)|(z&63);}
  if(value<min||value>0x10FFFF||(value>=0xD800&&value<=0xDFFF))return false;
 }return true;
}
bool Cached(std::string_view text)noexcept{return Utf8(text)&&text.find('\0')==std::string_view::npos;}
bool Key(std::string_view text)noexcept{
 if(text.empty()||text.size()>256)return false;
 for(const char c:text)if(!((c>='0'&&c<='9')||(c>='A'&&c<='Z')||(c>='a'&&c<='z')||c=='_'||c=='.'||c=='-'))return false;
 return true;
}
bool ControlValid(Zg361Ae2Control267V1 c)noexcept{return static_cast<unsigned>(c)<kZg361Ae2ControlKeys267V1.size();}
const char*ControlName(Zg361Ae2Control267V1 c)noexcept{return c==Zg361Ae2Control267V1::present?"present":"verify";}
const Zg361Ae2ControlRow267V1*Find(const Zg361Ae2Controls267V1&s,Zg361Ae2Control267V1 c)noexcept{
 for(const auto&r:s.rows)if(r.control==c)return &r;return nullptr;
}
bool Controls(const Zg361Ae2Controls267V1&s)noexcept{
 if(s.rows.size()>2||(s.selected_control&&!ControlValid(*s.selected_control)))return false;
 if(s.open_list_admissible&&(!s.resident_available||!s.actor_bound||s.list_visible||s.detail_visible||s.blocked_by_visible_modal))return false;
 unsigned seen=0;
 for(const auto&r:s.rows){
  if(!ControlValid(r.control))return false;const auto n=static_cast<unsigned>(r.control),bit=1U<<n;
  if((seen&bit)||r.definition_key!=kZg361Ae2ControlKeys267V1[n])return false;seen|=bit;
  if(r.native_can_confirm&&(!s.detail_visible||s.selected_control!=r.control))return false;
  if(r.open_detail_admissible&&(!r.native_can_open_detail||!s.actor_bound||!s.model_complete||!s.list_visible||s.blocked_by_visible_modal))return false;
  if(r.confirm_admissible&&(!s.actor_bound||!s.model_complete||!s.detail_visible||s.selected_control!=r.control||r.native_can_confirm!=true||s.blocked_by_visible_modal))return false;
 }return true;
}
bool Review(const Zg361Review267V1&s)noexcept{
 if(s.selected_definition_key&&!Key(*s.selected_definition_key))return false;
 if(s.selected_review&&(!s.detail_visible||s.selected_definition_key!=kZg361ReviewKey267V1))return false;
 if(s.requirements_complete){
  if(!s.selected_review||!s.actor_bound||!s.model_complete||!s.row_present||!s.has_requirements||!s.requirements_description||!Utf8(*s.requirements_description))return false;
 }else if(s.has_requirements||s.requirements_description)return false;
 return !s.open_detail_admissible||(s.resident_available&&s.actor_bound&&s.model_complete&&s.row_present&&s.list_visible&&!s.selected_review&&!s.blocked_by_visible_modal);
}
const Zg361Ae2Option267V1*Pay(const Zg361Ae2Snapshot267V1&s)noexcept{
 for(const auto&o:s.options)if(o.authored_option_index==15)return &o;return nullptr;
}
bool Events(const Zg361Ae2Events267V1&s)noexcept{
 if(!s.census_complete||s.census.size()>32)return false;
 for(std::size_t i=0;i<s.census.size();++i){const auto&r=s.census[i];
  if(r.instance_id<=0||r.recipient_character_id==0xFFFFFFFFU||!Key(r.definition_key))return false;
  for(std::size_t n=0;n<i;++n)if(s.census[n].instance_id==r.instance_id)return false;
 }
 if(!s.ae2)return true;const auto&a=*s.ae2;
 if(a.instance_id<=0||a.recipient_character_id==0xFFFFFFFFU||a.definition_key!=kZg361Ae2Definition267V1||a.authored_option_count!=kZg361Ae2AuthoredCount267V1)return false;
 bool identity=false;for(const auto&r:s.census)if(r.instance_id==a.instance_id&&r.recipient_character_id==a.recipient_character_id&&r.definition_key==a.definition_key)identity=true;
 if(!identity)return false;unsigned seen=0;
 for(const auto&o:a.options){
  const auto it=std::find(kZg361Ae2AuthoredIndices267V1.begin(),kZg361Ae2AuthoredIndices267V1.end(),o.authored_option_index);
  if(it==kZg361Ae2AuthoredIndices267V1.end())return false;const auto n=static_cast<std::size_t>(it-kZg361Ae2AuthoredIndices267V1.begin());const auto bit=1U<<n;
  if((seen&bit)||o.option_key!=kZg361Ae2OptionKeys267V1[n]||!Cached(o.text)||!Cached(o.disabled_reason)||!Utf8(o.tooltip))return false;seen|=bit;
 }
 const auto*pay=Pay(a);
 return seen==7&&(!a.pay_now_admissible||(a.phase_bound&&a.named_root_bound&&a.window_visible&&a.window_enabled&&a.tooltips_complete&&pay&&pay->native_can_select));
}
void String(std::string&out,std::string_view value){
 constexpr char hex[]="0123456789abcdef";out+='"';
 for(const unsigned char c:value){if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=static_cast<char>(c);}out+='"';
}
struct Json{
 std::string data;
 void key(const char*k){data+=",\"";data+=k;data+="\":";}
 void str(const char*k,std::string_view v){key(k);String(data,v);}
 void flag(const char*k,bool v){key(k);data+=v?"true":"false";}
 void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}
 void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}
};
const char*Status(Zg361Ae2Status267V1 s)noexcept{
 switch(s){case Zg361Ae2Status267V1::unavailable:return "unavailable";case Zg361Ae2Status267V1::expired:return "expired";case Zg361Ae2Status267V1::stale_source:return "stale_source";case Zg361Ae2Status267V1::claim_consumed:return "claim_consumed";case Zg361Ae2Status267V1::available:return "available";case Zg361Ae2Status267V1::navigation_dispatched:return "navigation_dispatched";case Zg361Ae2Status267V1::selection_dispatched:return "selection_dispatched";case Zg361Ae2Status267V1::confirmation_dispatched:return "confirmation_dispatched";case Zg361Ae2Status267V1::indeterminate:return "indeterminate";}return "invalid";
}
Zg361Ae2Status267V1 Dispatched(Zg361Ae2Action267V1 a)noexcept{
 using A=Zg361Ae2Action267V1;using T=Zg361Ae2Status267V1;
 if(a==A::choose_pay_now)return T::selection_dispatched;
 if(a==A::confirm_present||a==A::confirm_verify)return T::confirmation_dispatched;
 return T::navigation_dispatched;
}
bool Scoreboard(const Zg361Scoreboard267V1&s)noexcept{
 if(!s.complete||s.window_nodes>4096||s.modal_children>4096)return false;
 if(s.window_found!=(s.window_nodes>0)||(!s.window_found&&(s.window_visible||s.window_enabled||s.modal_found)))return false;
 if(!s.modal_found&&(s.modal_visible||s.modal_enabled||s.modal_children))return false;
 if(s.open_entry&&std::find(kZg361ScoreboardEntries267V1.begin(),kZg361ScoreboardEntries267V1.end(),*s.open_entry)==kZg361ScoreboardEntries267V1.end())return false;
 return (!s.open_admissible||(s.window_found&&s.window_visible&&s.window_enabled&&!s.modal_visible&&s.open_entry))&&
  (!s.close_admissible||(s.window_found&&s.window_visible&&s.window_enabled&&s.modal_found&&s.modal_visible&&s.modal_enabled));
}
void Source(Json&j,const Zg361Ae2Source267V1&s){
 j.data+="{\"schema\":";String(j.data,kZg361Ae2SourceSchema267V1);
 if(s.kind==Zg361Ae2Kind267V1::scoreboard){
  j.str("kind","scoreboard");j.key("scoreboard");const auto&r=*s.scoreboard;
  j.data+="{\"complete\":";j.data+=r.complete?"true":"false";
  j.flag("window_found",r.window_found);j.flag("window_visible",r.window_visible);j.flag("window_enabled",r.window_enabled);
  j.flag("modal_found",r.modal_found);j.flag("modal_visible",r.modal_visible);j.flag("modal_enabled",r.modal_enabled);
  j.num("window_nodes",r.window_nodes);j.num("modal_children",r.modal_children);
  j.key("open_entry");if(r.open_entry)String(j.data,*r.open_entry);else j.data+="null";
  j.flag("open_admissible",r.open_admissible);j.flag("close_admissible",r.close_admissible);j.data+="}}";return;
 }
 if(s.kind==Zg361Ae2Kind267V1::review){
  j.str("kind","review");j.key("review");const auto&r=*s.review;
  j.data+="{\"definition_key\":";String(j.data,kZg361ReviewKey267V1);
  j.flag("resident_available",r.resident_available);j.flag("list_visible",r.list_visible);j.flag("detail_visible",r.detail_visible);j.flag("detail_enabled",r.detail_enabled);
  j.flag("actor_bound",r.actor_bound);j.flag("model_complete",r.model_complete);j.flag("blocked_by_visible_modal",r.blocked_by_visible_modal);j.flag("row_present",r.row_present);
  j.flag("selected_review",r.selected_review);j.flag("open_detail_admissible",r.open_detail_admissible);j.flag("requirements_complete",r.requirements_complete);
  j.key("selected_definition_key");if(r.selected_definition_key)String(j.data,*r.selected_definition_key);else j.data+="null";
  j.key("has_requirements");if(r.has_requirements)j.data+=*r.has_requirements?"true":"false";else j.data+="null";
  j.key("requirements_description");if(r.requirements_description)String(j.data,*r.requirements_description);else j.data+="null";
  j.data+="}}";return;
 }
 j.str("kind",s.kind==Zg361Ae2Kind267V1::controls?"controls":"events");
 j.key("controls");
 if(s.controls){const auto&c=*s.controls;j.data+="{\"resident_available\":";j.data+=c.resident_available?"true":"false";
  j.flag("list_visible",c.list_visible);j.flag("detail_visible",c.detail_visible);j.flag("actor_bound",c.actor_bound);j.flag("model_complete",c.model_complete);j.flag("blocked_by_visible_modal",c.blocked_by_visible_modal);j.flag("open_list_admissible",c.open_list_admissible);
  j.key("selected_control");if(c.selected_control)String(j.data,ControlName(*c.selected_control));else j.data+="null";
  j.key("rows");j.data+='[';bool first=true;for(const auto&r:c.rows){if(!first)j.data+=',';first=false;j.data+="{\"control\":";String(j.data,ControlName(r.control));j.str("definition_key",r.definition_key);j.flag("native_can_open_detail",r.native_can_open_detail);j.flag("open_detail_admissible",r.open_detail_admissible);j.key("native_can_confirm");j.data+=r.native_can_confirm?(*r.native_can_confirm?"true":"false"):"null";j.flag("confirm_admissible",r.confirm_admissible);j.data+='}';}j.data+="]}";
 }else j.data+="null";
 j.key("events");
 if(s.events){const auto&e=*s.events;j.data+="{\"census_complete\":";j.data+=e.census_complete?"true":"false";j.key("census");j.data+='[';
  bool first=true;for(const auto&r:e.census){if(!first)j.data+=',';first=false;j.data+="{\"instance_id\":"+std::to_string(r.instance_id);j.num("recipient_character_id",r.recipient_character_id);j.str("definition_key",r.definition_key);j.data+='}';}j.data+=']';j.key("ae2");
  if(e.ae2){const auto&a=*e.ae2;j.data+="{\"instance_id\":"+std::to_string(a.instance_id);j.num("recipient_character_id",a.recipient_character_id);j.str("definition_key",a.definition_key);j.num("authored_option_count",a.authored_option_count);j.flag("phase_bound",a.phase_bound);j.flag("named_root_bound",a.named_root_bound);j.flag("window_visible",a.window_visible);j.flag("window_enabled",a.window_enabled);j.flag("tooltips_complete",a.tooltips_complete);j.key("options");j.data+='[';
   bool option_first=true;for(const auto&o:a.options){if(!option_first)j.data+=',';option_first=false;j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.str("option_key",o.option_key);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.str("tooltip",o.tooltip);j.data+='}';}j.data+=']';j.flag("pay_now_admissible",a.pay_now_admissible);j.data+='}';
  }else j.data+="null";j.data+='}';
 }else j.data+="null";j.data+='}';
}
} // namespace

const char*Zg361Ae2ActionName267V1(Zg361Ae2Action267V1 a)noexcept{
 constexpr const char*names[]{"query_controls","open_controls_list","open_present_detail","confirm_present","query_ae2","choose_pay_now","open_verify_detail","confirm_verify","query_review_requirements","open_review_detail","query_scoreboard","open_scoreboard","close_scoreboard"};
 const auto n=static_cast<unsigned>(a);return n<std::size(names)?names[n]:"invalid";
}
bool Zg361Ae2Query267V1(Zg361Ae2Action267V1 a)noexcept{return a==Zg361Ae2Action267V1::query_controls||a==Zg361Ae2Action267V1::query_ae2||a==Zg361Ae2Action267V1::query_review_requirements||a==Zg361Ae2Action267V1::query_scoreboard;}
Zg361Ae2Kind267V1 Zg361Ae2KindFor267V1(Zg361Ae2Action267V1 a)noexcept{if(a==Zg361Ae2Action267V1::query_scoreboard||a==Zg361Ae2Action267V1::open_scoreboard||a==Zg361Ae2Action267V1::close_scoreboard)return Zg361Ae2Kind267V1::scoreboard;if(a==Zg361Ae2Action267V1::query_review_requirements||a==Zg361Ae2Action267V1::open_review_detail)return Zg361Ae2Kind267V1::review;return a==Zg361Ae2Action267V1::query_ae2||a==Zg361Ae2Action267V1::choose_pay_now?Zg361Ae2Kind267V1::events:Zg361Ae2Kind267V1::controls;}
bool Zg361Ae2RequestShape267V1(const Zg361Ae2Request267V1&q)noexcept{
 return q.request_id_size<=96&&Id(q.id())&&q.deadline_unix_ms&&Prefix(q.expected)&&std::string_view(Zg361Ae2ActionName267V1(q.action))!="invalid"&&(Zg361Ae2Query267V1(q.action)?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence));
}
bool ParseZg361Ae2Request267V1(std::string_view packet,Zg361Ae2Request267V1&out)noexcept{
 out={};if(packet.empty()||packet.size()>16384)return false;Cursor c{packet};if(!c.Take('{'))return false;Zg361Ae2Request267V1 q;unsigned seen=0;bool first=true;
 while(!c.Take('}')){
  if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;unsigned v=0;good=c.Number(v)&&v==1;}else if(k=="request_id"){bit=4;std::string_view id;good=c.String(id)&&Id(id);if(good){std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());}}else if(k=="step"){bit=8;good=c.Identity(kZg361Ae2Step267V1);}else if(k=="actor"){bit=16;good=c.Identity("local_player");}else if(k=="target"){bit=32;good=c.Take('{')&&c.Identity("kind")&&c.Take(':')&&c.Identity("none")&&c.Take('}');}else if(k=="arguments"){bit=64;good=c.Take('{')&&c.Identity("zg361_ae2")&&c.Take(':')&&Claim(c,q)&&c.Take('}');}else if(k=="deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=packet.size()||!Zg361Ae2RequestShape267V1(q))return false;out=q;return true;
}
bool Zg361Ae2SourceShape267V1(const Zg361Ae2Source267V1&s)noexcept{
 if(static_cast<unsigned>(s.controls.has_value())+static_cast<unsigned>(s.events.has_value())+static_cast<unsigned>(s.review.has_value())+static_cast<unsigned>(s.scoreboard.has_value())!=1)return false;
 if(s.kind==Zg361Ae2Kind267V1::scoreboard)return s.scoreboard&&Scoreboard(*s.scoreboard);
 if(s.kind==Zg361Ae2Kind267V1::controls)return s.controls&&Controls(*s.controls);
 if(s.kind==Zg361Ae2Kind267V1::events)return s.events&&Events(*s.events);
 if(s.kind==Zg361Ae2Kind267V1::review)return s.review&&Review(*s.review);
 return false;
}
bool Zg361Ae2PublicAdmissible267V1(const Zg361Ae2Source267V1&s,Zg361Ae2Action267V1 a)noexcept{
 using A=Zg361Ae2Action267V1;
 if(std::string_view(Zg361Ae2ActionName267V1(a))=="invalid"||s.kind!=Zg361Ae2KindFor267V1(a)||!Zg361Ae2SourceShape267V1(s))return false;
 if(Zg361Ae2Query267V1(a))return true;
 if(a==A::open_scoreboard)return s.scoreboard->open_admissible;
 if(a==A::close_scoreboard)return s.scoreboard->close_admissible;
 if(a==A::open_review_detail)return s.review->open_detail_admissible;
 if(a==A::choose_pay_now)return s.events->ae2&&s.events->ae2->pay_now_admissible;
 const auto&c=*s.controls;if(a==A::open_controls_list)return c.open_list_admissible;
 const auto which=a==A::open_present_detail||a==A::confirm_present?Zg361Ae2Control267V1::present:Zg361Ae2Control267V1::verify;
 const auto*r=Find(c,which);if(!r)return false;
 return a==A::open_present_detail||a==A::open_verify_detail?r->open_detail_admissible:r->confirm_admissible;
}
std::string SerializeZg361Ae2Result267V1(std::string_view id,const Zg361Ae2Result267V1&r){
 const bool action=std::string_view(Zg361Ae2ActionName267V1(r.action))!="invalid";
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool query=Zg361Ae2Query267V1(r.action);
 const bool source=r.source_available&&facts&&r.cleanup_known&&r.source&&r.source->kind==Zg361Ae2KindFor267V1(r.action)&&Zg361Ae2SourceShape267V1(*r.source);
 const bool actor=source&&r.action==Zg361Ae2Action267V1::choose_pay_now?r.source->events->ae2&&r.source->events->ae2->recipient_character_id==std::bit_cast<std::uint32_t>(r.facts.played_character_id):true;
 bool ok=action&&source&&r.provider_generation&&r.query_sequence&&actor&&(query?(r.status==Zg361Ae2Status267V1::available&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned):(r.status==Dispatched(r.action)&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&Zg361Ae2PublicAdmissible267V1(*r.source,r.action)));
 const bool invalid=!action||std::string_view(Status(r.status))=="invalid"||(r.native_returned&&!r.effect_attempted)||(r.effect_attempted&&!r.claim_sequence)||(query&&(r.claim_sequence||r.effect_attempted||r.native_returned));
 const bool success_status=r.status==Zg361Ae2Status267V1::available||r.status==Zg361Ae2Status267V1::navigation_dispatched||r.status==Zg361Ae2Status267V1::selection_dispatched||r.status==Zg361Ae2Status267V1::confirmation_dispatched;
 auto status=r.status;if(invalid||!r.cleanup_known||(success_status&&!ok)){status=Zg361Ae2Status267V1::indeterminate;ok=false;}
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";
 String(j.data,kZg361Ae2ResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kZg361Ae2Backend267V1);j.str("action",Zg361Ae2ActionName267V1(r.action));j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(ok)Source(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"zg361_ae2_current_source_or_owner_unavailable":r.reason);j.data+="}}";return j.data;
}
} // namespace xar::ck3_121003::build26785313

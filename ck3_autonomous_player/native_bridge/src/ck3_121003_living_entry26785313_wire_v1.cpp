#include "xar_bridge/ck3_121003_living_entry26785313_v1.hpp"
#include <algorithm>
#include <bit>
#include <charconv>
#include <utility>
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


bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
bool Core(Cursor&c,ck3_1210::CoreSnapshotPrefix&p)noexcept{
 if(!c.Take('{'))return false;std::uint32_t seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key;if(!c.String(key)||!c.Take(':'))return false;std::uint32_t bit=0;bool good=false;
  if(key=="date_raw"){bit=1;good=c.Number(p.clock.date_raw);}else if(key=="speed"){bit=2;good=c.Number(p.clock.speed);}else if(key=="paused"){bit=4;good=c.Boolean(p.clock.paused);}else if(key=="local_player_id"){bit=8;good=c.Number(p.local_player_id);}else if(key=="map_ready"){bit=16;good=c.Boolean(p.map_ready);}else if(key=="has_played_character"){bit=32;good=c.Boolean(p.has_played_character);}else if(key=="played_character_id"){bit=64;good=c.Number(p.played_character_id);}else if(key=="played_character_alive"){bit=128;good=c.Boolean(p.played_character_alive);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==255&&Prefix(p);
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

const char*Status(LivingEntryStatus267V1 s){switch(s){case LivingEntryStatus267V1::available:return "available";case LivingEntryStatus267V1::dispatched:return "dispatched";case LivingEntryStatus267V1::rejected:return "rejected";case LivingEntryStatus267V1::expired:return "expired";case LivingEntryStatus267V1::stale_source:return "stale_source";case LivingEntryStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}void opt(const char*k,const std::optional<bool>&v){key(k);data+=v?(*v?"true":"false"):"null";}};
bool Action(Cursor&c,LivingEntryAction267V1&out){std::string_view name;if(!c.String(name))return false;for(unsigned i=0;i<=static_cast<unsigned>(LivingEntryAction267V1::open_detail);++i){const auto a=static_cast<LivingEntryAction267V1>(i);if(name==LivingEntryActionName267V1(a)){out=a;return true;}}return false;}
bool Claim(Cursor&c,LivingEntryRequest267V1&q){
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="schema"){bit=1;good=c.Identity(kLivingEntryRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kLivingEntryBackend267V1);}else if(k=="action"){bit=32;good=Action(c,q.action);}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="provider_generation"){bit=128;good=c.Number(q.provider_generation);}else if(k=="query_sequence"){bit=256;good=c.Number(q.query_sequence);}if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==511;
}

bool ActionAdmissible(const LivingEntrySource267V1&s,LivingEntryAction267V1 a){
 using A=LivingEntryAction267V1;
 if(LivingEntryQuery267V1(a))return true;
 if(a==A::open_inventory)return s.inventory&&s.inventory->open_admissible;
 if(a==A::open_detail)return s.detail&&s.detail->open_admissible;
 if(!s.manage||!s.manage->owner_bound)return false;
 const auto&m=*s.manage;
 if(a==A::open_manage_list)return m.open_list_admissible;
 if(a==A::open_manage_detail)return m.rows.size()==1&&m.rows[0].can_open_detail;
 return a==A::confirm_manage&&m.confirm_admissible&&m.native_can_confirm==true;
}
bool Manage(const LivingManageSource267V1&m){
 if(!m.owner_bound||m.rows.size()>1||
  (m.list_visible&&!m.list_found)||(m.detail_visible&&!m.detail_found)||
  (m.complete_model_census&&(!m.list_found||!m.groups_count||!m.total_model_rows))||
  (m.groups_count&&(*m.groups_count<0||*m.groups_count>64))||
  (m.total_model_rows&&(*m.total_model_rows<0||*m.total_model_rows>1024))||
  (m.selected_decision&&*m.selected_decision!=LivingManage267V1::manage)||
  (m.widget_state&&(*m.widget_state<0||*m.widget_state>1))||
  (m.native_can_confirm&&(!m.detail_visible||!m.selected_decision))||
  (m.confirm_tooltip_observed!=m.confirm_tooltip.has_value())||
  (m.confirm_tooltip&&(!m.detail_visible||!m.selected_decision||!Utf8(*m.confirm_tooltip)))||
  (m.open_list_admissible&&(m.list_visible||m.detail_visible||m.blocked_by_visible_modal))||
  (m.confirm_admissible&&(!m.detail_visible||!m.detail_enabled||!m.selected_decision||
   !m.complete_model_census||m.native_can_confirm!=true||m.blocked_by_visible_modal)))return false;
 for(const auto&r:m.rows)if(r.decision!=LivingManage267V1::manage||
  (r.can_open_detail&&(!m.complete_model_census||!m.list_visible||!m.list_enabled||r.is_selected||m.blocked_by_visible_modal))||
  (r.is_selected&&(!m.detail_visible||!m.selected_decision)))return false;
 return true;
}
void Source(Json&j,const LivingEntrySource267V1&s){
 j.data+="{\"schema\":";String(j.data,kLivingEntrySourceSchema267V1);
 j.str("kind",s.kind==LivingEntryKind267V1::manage?"manage":s.kind==LivingEntryKind267V1::inventory?"inventory":"detail");
 j.num("actor_full_id",s.actor_full_id);j.key("manage");
 if(s.manage){const auto&m=*s.manage;j.data+="{\"list_found\":";j.data+=m.list_found?"true":"false";
  j.flag("list_visible",m.list_visible);j.flag("list_enabled",m.list_enabled);
  j.flag("detail_found",m.detail_found);j.flag("detail_visible",m.detail_visible);j.flag("detail_enabled",m.detail_enabled);
  const auto number=[&](const char*k,const std::optional<std::int32_t>&v){j.key(k);j.data+=v?std::to_string(*v):"null";};
  number("groups_count",m.groups_count);number("total_model_rows",m.total_model_rows);
  j.flag("complete_model_census",m.complete_model_census);j.flag("blocked_by_visible_modal",m.blocked_by_visible_modal);
  j.flag("other_decision_selected",m.other_decision_selected);j.key("selected_decision_key");
  if(m.selected_decision)String(j.data,"xalw_manage_decision");else j.data+="null";
  number("widget_state",m.widget_state);j.opt("native_can_confirm",m.native_can_confirm);
  j.flag("confirm_admissible",m.confirm_admissible);j.flag("open_list_admissible",m.open_list_admissible);
  j.key("rows");j.data+='[';bool first=true;for(const auto&r:m.rows){if(!first)j.data+=',';first=false;
   j.data+="{\"decision_key\":\"xalw_manage_decision\"";j.flag("can_open_detail",r.can_open_detail);j.flag("is_selected",r.is_selected);j.data+='}';}
  j.data+=']';j.flag("owner_bound",m.owner_bound);j.key("confirm_tooltip");
  if(m.confirm_tooltip)String(j.data,*m.confirm_tooltip);else j.data+="null";
  j.flag("confirm_tooltip_observed",m.confirm_tooltip_observed);j.data+='}';
 }else j.data+="null";
 const auto view=[&](const char*k,const std::optional<LivingEntryViewData267V1>&v){j.key(k);if(!v){j.data+="null";return;}
  j.data+="{\"expected_payload_full_id\":"+std::to_string(v->expected_payload_full_id);
  j.flag("window_found",v->window_found);j.flag("visible",v->visible);j.flag("enabled",v->enabled);
  j.flag("payload_bound",v->payload_bound);j.flag("blocked_by_visible_modal",v->blocked_by_visible_modal);
  j.flag("open_admissible",v->open_admissible);j.data+='}';};
 view("inventory",s.inventory);view("detail",s.detail);j.flag("sampled_twice",s.sampled_twice);j.data+='}';
}
}
const char*LivingEntryActionName267V1(LivingEntryAction267V1 a)noexcept {
 constexpr const char*names[]{"query_manage","open_manage_list","open_manage_detail","confirm_manage",
  "query_inventory_entry","open_inventory","query_detail_entry","open_detail"};
 const auto i=static_cast<unsigned>(a);return i<std::size(names)?names[i]:"invalid";
}
LivingEntryKind267V1 LivingEntryKindFor267V1(LivingEntryAction267V1 a)noexcept {
 return a<=LivingEntryAction267V1::confirm_manage?LivingEntryKind267V1::manage:
  a<=LivingEntryAction267V1::open_inventory?LivingEntryKind267V1::inventory:LivingEntryKind267V1::detail;
}
bool LivingEntryQuery267V1(LivingEntryAction267V1 a)noexcept {
 return a==LivingEntryAction267V1::query_manage||a==LivingEntryAction267V1::query_inventory_entry||a==LivingEntryAction267V1::query_detail_entry;
}
bool LivingEntryRequestShape267V1(const LivingEntryRequest267V1&q)noexcept {
 return LivingInventoryQueryRequestShape267V1(q)&&std::string_view(LivingEntryActionName267V1(q.action))!="invalid"&&
  (LivingEntryQuery267V1(q.action)?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence));
}
bool LivingEntrySourceShape267V1(const LivingEntrySource267V1&s,const ck3_1210::CoreSnapshotPrefix&f)noexcept {
 try{
  if(!Prefix(f)||!s.sampled_twice||s.actor_full_id!=std::bit_cast<std::uint32_t>(f.played_character_id)||
   static_cast<unsigned>(s.manage.has_value())+static_cast<unsigned>(s.inventory.has_value())+static_cast<unsigned>(s.detail.has_value())!=1)return false;
  if(s.kind==LivingEntryKind267V1::manage)return s.manage&&Manage(*s.manage);
  const auto*v=s.kind==LivingEntryKind267V1::inventory?(s.inventory?&*s.inventory:nullptr):
   s.kind==LivingEntryKind267V1::detail?(s.detail?&*s.detail:nullptr):nullptr;
  return v&&v->expected_payload_full_id!=0xFFFFFFFFU&&(!v->visible||v->window_found)&&
   (!v->payload_bound||v->window_found)&&
   (s.kind!=LivingEntryKind267V1::inventory||v->expected_payload_full_id==s.actor_full_id)&&
   (!v->open_admissible||(!v->visible&&!v->blocked_by_visible_modal));
 }catch(...){return false;}
}
bool ParseLivingEntryRequest267V1(std::string_view packet,LivingEntryRequest267V1&out)noexcept{
 out={};if(packet.empty()||packet.size()>16384)return false;Cursor c{packet};if(!c.Take('{'))return false;LivingEntryRequest267V1 q;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;unsigned v=0;good=c.Number(v)&&v==1;}else if(k=="request_id"){bit=4;std::string_view id;good=c.String(id)&&Id(id);if(good){std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());}}else if(k=="step"){bit=8;std::string_view step;good=c.String(step)&&step=="ck3_121003_living_entry.execute";}else if(k=="actor"){bit=16;good=c.Identity("local_player");}else if(k=="target"){bit=32;good=c.Take('{')&&c.Identity("kind")&&c.Take(':')&&c.Identity("none")&&c.Take('}');}else if(k=="arguments"){bit=64;good=c.Take('{')&&c.Identity("living_entry")&&c.Take(':')&&Claim(c,q)&&c.Take('}');}else if(k=="deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms);}if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=packet.size()||!LivingEntryRequestShape267V1(q))return false;out=q;return true;
}
std::string SerializeLivingEntryResult267V1(std::string_view id,const LivingEntryResult267V1&r){
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool query=LivingEntryQuery267V1(r.action),source=r.source_available&&facts&&r.cleanup_known&&r.source&&r.source->kind==LivingEntryKindFor267V1(r.action)&&LivingEntrySourceShape267V1(*r.source,r.facts);
 bool ok=source&&r.provider_generation&&r.query_sequence&&(query?(r.status==LivingEntryStatus267V1::available&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned):(r.status==LivingEntryStatus267V1::dispatched&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&ActionAdmissible(*r.source,r.action)));
 const bool invalid=(r.native_returned&&!r.effect_attempted)||(r.effect_attempted&&!r.claim_sequence)||(query&&(r.claim_sequence||r.effect_attempted||r.native_returned));
 auto status=r.status;if(invalid||!r.cleanup_known||((status==LivingEntryStatus267V1::available||status==LivingEntryStatus267V1::dispatched)&&!ok)){status=LivingEntryStatus267V1::indeterminate;ok=false;}
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kLivingEntryResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kLivingEntryBackend267V1);j.str("action",LivingEntryActionName267V1(r.action));j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";j.key("source");if(ok)Source(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"living_entry_current_source_or_owner_unavailable":r.reason);j.data+="}}";return j.data;
}
}

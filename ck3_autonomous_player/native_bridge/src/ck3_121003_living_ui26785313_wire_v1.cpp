#include "xar_bridge/ck3_121003_living_ui26785313_v1.hpp"
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

const char*Status(LivingUiStatus267V1 s){switch(s){case LivingUiStatus267V1::available:return "available";case LivingUiStatus267V1::dispatched:return "dispatched";case LivingUiStatus267V1::rejected:return "rejected";case LivingUiStatus267V1::expired:return "expired";case LivingUiStatus267V1::stale_source:return "stale_source";case LivingUiStatus267V1::indeterminate:return "indeterminate";default:return "unavailable";}}
struct Json{std::string data;void key(const char*k){data+=",\"";data+=k;data+="\":";}void str(const char*k,std::string_view v){key(k);String(data,v);}void flag(const char*k,bool v){key(k);data+=v?"true":"false";}void num(const char*k,std::int64_t v){key(k);data+=std::to_string(v);}void u64(const char*k,std::uint64_t v){str(k,std::to_string(v));}void opt(const char*k,const std::optional<bool>&v){key(k);data+=v?(*v?"true":"false"):"null";}};
bool Action(Cursor&c,LivingUiAction267V1&out){std::string_view name;if(!c.String(name))return false;for(unsigned i=0;i<=static_cast<unsigned>(LivingUiAction267V1::close_management);++i){const auto a=static_cast<LivingUiAction267V1>(i);if(name==LivingUiActionName267V1(a)){out=a;return true;}}return false;}
bool Claim(Cursor&c,LivingUiRequest267V1&q){
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;
  if(k=="schema"){bit=1;good=c.Identity(kLivingUiRequestSchema267V1);}else if(k=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(k=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(k=="adapter_id"){bit=8;good=c.Identity(kAdapterId);}else if(k=="backend"){bit=16;good=c.Identity(kLivingUiBackend267V1);}else if(k=="action"){bit=32;good=Action(c,q.action);}else if(k=="expected_core"){bit=64;good=Core(c,q.expected);}else if(k=="provider_generation"){bit=128;good=c.Number(q.provider_generation);}else if(k=="query_sequence"){bit=256;good=c.Number(q.query_sequence);}if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==511;
}
bool Ref(const LivingArtifactReference267V1&r){switch(r.state){case LivingReferenceState267V1::absent:case LivingReferenceState267V1::present_empty:return r.scope_kind==0&&!r.full_id;case LivingReferenceState267V1::wrong_kind:return r.scope_kind!=0&&r.scope_kind!=36&&!r.full_id;case LivingReferenceState267V1::artifact:return r.scope_kind==36&&r.full_id&&*r.full_id!=0xFFFFFFFFU;}return false;}
void EmitRef(Json&j,const LivingArtifactReference267V1&r){j.data+="{\"state\":";const char*s=r.state==LivingReferenceState267V1::absent?"absent":r.state==LivingReferenceState267V1::present_empty?"present_empty":r.state==LivingReferenceState267V1::wrong_kind?"wrong_kind":"artifact";String(j.data,s);j.num("scope_kind",r.scope_kind);j.key("artifact_full_id");j.data+=r.full_id?std::to_string(*r.full_id):"null";j.data+='}';}
int FixedIndex(LivingUiAction267V1 action,std::string_view definition){using A=LivingUiAction267V1;if(definition=="xalw.12"&&action==A::open_tutorial)return 0;if(definition=="xalw.10"){if(action==A::feed_common)return 1;if(action==A::feed_masterwork)return 2;if(action==A::feed_famed)return 3;if(action==A::feed_illustrious)return 4;if(action==A::close_management)return 9;}if(definition=="xalw.11"){if(action==A::confirm_review)return 0;if(action==A::cancel_review)return 1;}return -1;}
bool Key(std::string_view key){if(key.empty()||key.size()>256)return false;for(const auto c:key)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))return false;return true;}
bool Events(const LivingEventData267V1&d,const ck3_1210::CoreSnapshotPrefix&f){
 if(!d.complete_bindings||!d.census.census_complete||d.census.named_root_count<0||d.census.named_root_count>64||static_cast<std::size_t>(d.census.named_root_count)!=d.census.events.size()||d.bindings.size()>64||d.fixed_actions.size()>128)return false;
 std::vector<std::int32_t>instances,bound;
 for(const auto&e:d.census.events){if(e.instance_id<=0||e.recipient_character_id==-1||!e.named_root_bound||e.authored_option_count<0||e.authored_option_count>64||e.options.size()>64||!Key(e.definition_key)||!Utf8(e.opening)||!Utf8(e.description)||std::find(instances.begin(),instances.end(),e.instance_id)!=instances.end())return false;instances.push_back(e.instance_id);std::vector<int>indices;for(const auto&o:e.options){if(o.authored_option_index<0||o.authored_option_index>=e.authored_option_count||std::find(indices.begin(),indices.end(),o.authored_option_index)!=indices.end()||o.permitted_role||o.source_bound_option_key||!Utf8(o.text)||!Utf8(o.disabled_reason))return false;indices.push_back(o.authored_option_index);}}
 for(const auto&b:d.bindings){if(std::find(bound.begin(),bound.end(),b.instance_id)!=bound.end()||!b.complete_named_scopes||!b.sampled_twice||b.recipient_id!=f.played_character_id||!Ref(b.target)||!Ref(b.material)||!b.target_owned||!b.target.full_id)return false;bound.push_back(b.instance_id);const auto e=std::find_if(d.census.events.begin(),d.census.events.end(),[&](const auto&e){return e.instance_id==b.instance_id&&e.recipient_character_id==b.recipient_id&&e.definition_key==b.definition_key;});if(e==d.census.events.end()||e->authored_option_count!=(b.definition_key=="xalw.10"?10:2)||(b.definition_key!="xalw.12"&&b.definition_key!="xalw.10"&&b.definition_key!="xalw.11")||b.material_required!=(b.definition_key=="xalw.11")||(b.material_owned&&(!b.material.full_id||*b.material.full_id==0xFFFFFFFFU))||(b.material_required&&(!b.material_owned||b.target.full_id==b.material.full_id)))return false;}
 for(const auto&e:d.census.events)if(e.recipient_character_id==f.played_character_id&&(e.definition_key=="xalw.12"||e.definition_key=="xalw.10"||e.definition_key=="xalw.11")&&std::find(bound.begin(),bound.end(),e.instance_id)==bound.end())return false;
 std::vector<std::pair<int,int>>seen;for(const auto&a:d.fixed_actions){const auto b=std::find_if(d.bindings.begin(),d.bindings.end(),[&](const auto&b){return b.instance_id==a.instance_id;});const auto pair=std::pair{a.instance_id,static_cast<int>(a.action)};if(b==d.bindings.end()||FixedIndex(a.action,b->definition_key)!=a.authored_option_index||std::find(seen.begin(),seen.end(),pair)!=seen.end())return false;seen.push_back(pair);const auto e=std::find_if(d.census.events.begin(),d.census.events.end(),[&](const auto&e){return e.instance_id==a.instance_id;});const auto o=std::find_if(e->options.begin(),e->options.end(),[&](const auto&o){return o.authored_option_index==a.authored_option_index;});if(o==e->options.end()||(a.admissible&&(!e->window_visible||!e->window_enabled||!o->native_can_select)))return false;}
 return true;
}
bool ActionAdmissible(const LivingUiSource267V1&s,LivingUiAction267V1 action){
 if(LivingUiQuery267V1(action))return true;
 if(s.weapon){switch(action){case LivingUiAction267V1::select_weapon:return s.weapon->select_admissible;case LivingUiAction267V1::equip_target:return s.weapon->equip_admissible;case LivingUiAction267V1::unequip_target:return s.weapon->unequip_admissible;default:return false;}}
 return s.events&&std::count_if(s.events->fixed_actions.begin(),s.events->fixed_actions.end(),[&](const auto&a){return a.action==action&&a.admissible;})==1;
}
void Source(Json&j,const LivingUiSource267V1&s){
 j.data+="{\"schema\":";String(j.data,kLivingUiSourceSchema267V1);j.str("kind",s.kind==LivingUiKind267V1::weapon?"weapon":s.kind==LivingUiKind267V1::events?"events":"detail");j.num("actor_full_id",s.actor_full_id);
 j.key("weapon");if(s.weapon){const auto&w=*s.weapon;j.data+="{\"target_full_id\":"+std::to_string(w.target_full_id);j.key("weapon_artifact_full_id");j.data+=w.weapon_artifact_full_id?std::to_string(*w.weapon_artifact_full_id):"null";j.flag("window_found",w.window_found);j.flag("visible",w.visible);j.flag("enabled",w.enabled);j.flag("target_equipped",w.target_equipped);j.flag("weapon_selected",w.weapon_selected);j.opt("native_slot_available",w.native_slot_available);j.opt("native_can_hold",w.native_can_hold);j.flag("select_admissible",w.select_admissible);j.flag("equip_admissible",w.equip_admissible);j.flag("unequip_admissible",w.unequip_admissible);j.data+='}';}else j.data+="null";
 j.key("events");if(s.events){const auto&d=*s.events;j.data+="{\"census_complete\":";j.data+=d.census.census_complete?"true":"false";j.num("named_root_count",d.census.named_root_count);j.key("events");j.data+='[';bool first=true;for(const auto&e:d.census.events){if(!first)j.data+=',';first=false;j.data+="{\"instance_id\":"+std::to_string(e.instance_id);j.num("recipient_character_id",e.recipient_character_id);j.str("definition_key",e.definition_key);j.num("authored_option_count",e.authored_option_count);j.flag("named_root_bound",e.named_root_bound);j.flag("window_visible",e.window_visible);j.flag("window_enabled",e.window_enabled);j.str("opening",e.opening);j.str("description",e.description);j.key("options");j.data+='[';bool of=true;for(const auto&o:e.options){if(!of)j.data+=',';of=false;j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.key("permitted_role");j.data+="null";j.key("source_bound_option_key");j.data+="null}";}j.data+="]}";}j.data+=']';j.key("bindings");j.data+='[';first=true;for(const auto&b:d.bindings){if(!first)j.data+=',';first=false;j.data+="{\"instance_id\":"+std::to_string(b.instance_id);j.num("recipient_id",b.recipient_id);j.str("definition_key",b.definition_key);j.key("target");EmitRef(j,b.target);j.key("material");EmitRef(j,b.material);j.flag("target_owned",b.target_owned);j.flag("material_owned",b.material_owned);j.flag("material_required",b.material_required);j.flag("complete_named_scopes",b.complete_named_scopes);j.flag("sampled_twice",b.sampled_twice);j.data+='}';}j.data+=']';j.key("fixed_actions");j.data+='[';first=true;for(const auto&a:d.fixed_actions){if(!first)j.data+=',';first=false;j.data+="{\"action\":";String(j.data,LivingUiActionName267V1(a.action));j.num("instance_id",a.instance_id);j.num("authored_option_index",a.authored_option_index);j.flag("admissible",a.admissible);j.data+='}';}j.data+=']';j.flag("complete_bindings",d.complete_bindings);j.data+='}';}else j.data+="null";
 j.key("detail");if(s.detail){const auto&d=*s.detail;j.data+="{\"target_full_id\":"+std::to_string(d.target_full_id);j.flag("window_found",d.window_found);j.flag("visible",d.visible);j.flag("enabled",d.enabled);j.flag("target_bound",d.target_bound);const auto text=[&](const char*k,const std::optional<std::string>&v){j.key(k);if(v)String(j.data,*v);else j.data+="null";};text("modifier_effects_text",d.modifier_effects_text);text("custom_effects_text",d.custom_effects_text);text("description_text",d.description_text);j.data+='}';}else j.data+="null";j.flag("sampled_twice",s.sampled_twice);j.data+='}';
}
}
const char*LivingUiActionName267V1(LivingUiAction267V1 a)noexcept{constexpr const char*names[]{"query_weapon","select_weapon","equip_target","unequip_target","query_events","open_tutorial","feed_common","feed_masterwork","feed_famed","feed_illustrious","cancel_review","confirm_review","query_detail","close_management"};const auto i=static_cast<unsigned>(a);return i<std::size(names)?names[i]:"invalid";}
LivingUiKind267V1 LivingUiKindFor267V1(LivingUiAction267V1 a)noexcept{return a<=LivingUiAction267V1::unequip_target?LivingUiKind267V1::weapon:a==LivingUiAction267V1::query_detail?LivingUiKind267V1::detail:LivingUiKind267V1::events;}
bool LivingUiQuery267V1(LivingUiAction267V1 a)noexcept{return a==LivingUiAction267V1::query_weapon||a==LivingUiAction267V1::query_events||a==LivingUiAction267V1::query_detail;}
bool LivingUiRequestShape267V1(const LivingUiRequest267V1&q)noexcept{return LivingInventoryQueryRequestShape267V1(q)&&std::string_view(LivingUiActionName267V1(q.action))!="invalid"&&(LivingUiQuery267V1(q.action)?(!q.provider_generation&&!q.query_sequence):(q.provider_generation&&q.query_sequence));}
bool LivingUiSourceShape267V1(const LivingUiSource267V1&s,const ck3_1210::CoreSnapshotPrefix&f)noexcept{
 try{if(!Prefix(f)||!s.sampled_twice||s.actor_full_id!=std::bit_cast<std::uint32_t>(f.played_character_id)||static_cast<unsigned>(s.weapon.has_value())+static_cast<unsigned>(s.events.has_value())+static_cast<unsigned>(s.detail.has_value())!=1)return false;
 if(s.kind==LivingUiKind267V1::events)return s.events&&Events(*s.events,f);
 if(s.kind==LivingUiKind267V1::weapon){if(!s.weapon)return false;const auto&w=*s.weapon;const bool native=w.native_slot_available==true&&w.native_can_hold==true;return w.target_full_id!=0xFFFFFFFFU&&(!w.weapon_artifact_full_id||*w.weapon_artifact_full_id!=0xFFFFFFFFU)&&(!w.visible||w.window_found)&&(!w.select_admissible||(w.window_found&&w.visible&&w.enabled&&native&&!w.weapon_selected&&!w.target_equipped))&&(!w.equip_admissible||(w.window_found&&w.visible&&w.enabled&&native&&w.weapon_selected&&!w.target_equipped))&&(!w.unequip_admissible||(w.window_found&&w.visible&&w.enabled&&w.target_equipped&&w.weapon_artifact_full_id==w.target_full_id));}
 if(!s.detail)return false;const auto&d=*s.detail;return d.target_full_id!=0xFFFFFFFFU&&(!d.visible||d.window_found)&&(!d.target_bound||d.window_found)&&(!d.modifier_effects_text||(d.target_bound&&Utf8(*d.modifier_effects_text)))&&(!d.custom_effects_text||(d.target_bound&&Utf8(*d.custom_effects_text)))&&(!d.description_text||(d.target_bound&&Utf8(*d.description_text)));}catch(...){return false;}
}
bool ParseLivingUiRequest267V1(std::string_view packet,LivingUiRequest267V1&out)noexcept{
 out={};if(packet.empty()||packet.size()>16384)return false;Cursor c{packet};if(!c.Take('{'))return false;LivingUiRequest267V1 q;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view k;unsigned bit=0;bool good=false;if(!c.String(k)||!c.Take(':'))return false;if(k=="type"){bit=1;good=c.Identity("execute_step");}else if(k=="protocol_version"){bit=2;unsigned v=0;good=c.Number(v)&&v==1;}else if(k=="request_id"){bit=4;std::string_view id;good=c.String(id)&&Id(id);if(good){std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());}}else if(k=="step"){bit=8;std::string_view step;good=c.String(step)&&step=="ck3_121003_living_ui.execute";}else if(k=="actor"){bit=16;good=c.Identity("local_player");}else if(k=="target"){bit=32;good=c.Take('{')&&c.Identity("kind")&&c.Take(':')&&c.Identity("none")&&c.Take('}');}else if(k=="arguments"){bit=64;good=c.Take('{')&&c.Identity("living_ui")&&c.Take(':')&&Claim(c,q)&&c.Take('}');}else if(k=="deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms);}if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=packet.size()||!LivingUiRequestShape267V1(q))return false;out=q;return true;
}
std::string SerializeLivingUiResult267V1(std::string_view id,const LivingUiResult267V1&r){
 const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool query=LivingUiQuery267V1(r.action),source=r.source_available&&facts&&r.cleanup_known&&r.source&&r.source->kind==LivingUiKindFor267V1(r.action)&&LivingUiSourceShape267V1(*r.source,r.facts);
 bool ok=source&&r.provider_generation&&r.query_sequence&&(query?(r.status==LivingUiStatus267V1::available&&!r.claim_sequence&&!r.effect_attempted&&!r.native_returned):(r.status==LivingUiStatus267V1::dispatched&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&ActionAdmissible(*r.source,r.action)));
 const bool invalid=(r.native_returned&&!r.effect_attempted)||(r.effect_attempted&&!r.claim_sequence)||(query&&(r.claim_sequence||r.effect_attempted||r.native_returned));
 auto status=r.status;if(invalid||!r.cleanup_known||((status==LivingUiStatus267V1::available||status==LivingUiStatus267V1::dispatched)&&!ok)){status=LivingUiStatus267V1::indeterminate;ok=false;}
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kLivingUiResultSchema267V1);j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("adapter_id",kAdapterId);j.str("backend",kLivingUiBackend267V1);j.str("action",LivingUiActionName267V1(r.action));j.str("status",Status(status));j.flag("source_available",ok);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",false);j.flag("cleanup_known",r.cleanup_known);
 j.key("facts_before");if(facts){const auto&f=r.facts;j.data+="{\"date_raw\":"+std::to_string(f.clock.date_raw);j.num("speed",f.clock.speed);j.flag("paused",f.clock.paused);j.num("local_player_id",f.local_player_id);j.flag("map_ready",f.map_ready);j.flag("has_played_character",f.has_played_character);j.num("played_character_id",f.played_character_id);j.flag("played_character_alive",f.played_character_alive);j.data+='}';}else j.data+="null";j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";j.key("source");if(ok)Source(j,*r.source);else j.data+="null";j.flag("addresses_redacted",true);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"living_ui_current_source_or_owner_unavailable":r.reason);j.data+="}}";return j.data;
}
}

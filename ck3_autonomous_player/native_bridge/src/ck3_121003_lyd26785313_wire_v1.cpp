#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"
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
template<class T,std::size_t N>bool EnumText(Cursor&c,const std::array<std::string_view,N>&names,T&out)noexcept{std::string_view text;if(!c.String(text))return false;for(std::size_t n=0;n<N;++n)if(names[n]==text){out=static_cast<T>(n);return true;}return false;}
template<class T,std::size_t N>bool NullableEnum(Cursor&c,const std::array<std::string_view,N>&names,std::optional<T>&out)noexcept{c.Space();if(c.text.substr(c.pos,4)=="null"){c.pos+=4;out.reset();return true;}T value{};if(!EnumText(c,names,value))return false;out=value;return true;}
bool Claim(Cursor&c,LydRequest267V1&q,std::string_view adapter)noexcept{
 if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;
  if(key=="schema"){bit=1;good=c.Identity(kLydRequestSchema267V1);}else if(key=="game_version"){bit=2;good=c.Identity(kGameVersion);}else if(key=="executable_sha256"){bit=4;good=c.Identity(kExecutableSha256,true);}else if(key=="adapter_id"){bit=8;good=c.Identity(adapter);}else if(key=="backend"){bit=16;good=c.Identity(kLydBackend267V1);}
  else if(key=="action"){bit=32;good=EnumText(c,kLydActionNames267V1,q.action);}else if(key=="expected_core"){bit=64;good=Core(c,q.expected);}else if(key=="provider_generation"){bit=128;good=UIntText(c,q.provider_generation);}else if(key=="query_sequence"){bit=256;good=UIntText(c,q.query_sequence);}
  else if(key=="decision_key"){bit=512;good=NullableEnum(c,kLydDecisionKeys267V1,q.decision);}else if(key=="personal_key"){bit=1024;good=NullableEnum(c,kLydPersonalKeys267V1,q.personal);}else if(key=="event_role"){bit=2048;good=NullableEnum(c,kLydEventRoleNames267V1,q.event_role);}
  else if(key=="instance_id"){bit=4096;c.Space();if(c.text.substr(c.pos,4)=="null"){c.pos+=4;q.instance_id.reset();good=true;}else{std::int32_t n=0;good=c.Number(n);if(good)q.instance_id=n;}}
  else if(key=="choice_token"){bit=8192;good=c.String(value)&&value.size()<=96;if(good)q.choice_token.assign(value);}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }return seen==16383;
}
const char*Status(LydStatus267V1 s)noexcept{switch(s){case LydStatus267V1::available:return"available";case LydStatus267V1::navigation_dispatched:return"navigation_dispatched";case LydStatus267V1::selection_dispatched:return"selection_dispatched";case LydStatus267V1::confirmation_dispatched:return"confirmation_dispatched";case LydStatus267V1::expired:return"expired";case LydStatus267V1::stale_source:return"stale_source";case LydStatus267V1::claim_consumed:return"claim_consumed";case LydStatus267V1::indeterminate:return"indeterminate";default:return"unavailable";}}
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
template<class T,std::size_t N>void Enum(Json&j,const char*k,const std::array<std::string_view,N>&names,const std::optional<T>&v){j.key(k);if(v&&static_cast<std::size_t>(*v)<N)String(j.data,names[static_cast<std::size_t>(*v)]);else j.data+="null";}
[[maybe_unused]]bool KeyText(std::string_view text,std::size_t bound=192)noexcept{if(text.empty()||text.size()>bound)return false;for(char c:text)if(!((c>='0'&&c<='9')||(c>='A'&&c<='Z')||(c>='a'&&c<='z')||c=='_'||c=='.'||c=='-'))return false;return true;}
struct EventRule{std::string_view definition,option;std::int32_t count,index;LydEventRole267V1 role;};
constexpr std::array<EventRule,7>kEventRules{{
 {"lyd.1","lyd_welcome_continue",1,0,LydEventRole267V1::welcome_continue},
 {"lyd.1002","lyd_play_ritual_music_option_0",2,0,LydEventRole267V1::ritual_music_pay},
 {"lyd.1002","lyd_play_cancel",2,1,LydEventRole267V1::ritual_music_cancel},
 {"lyd.1000","lyd_play_reverent_heaven_option_0",2,0,LydEventRole267V1::reverent_heaven_pay},
 {"lyd.1000","lyd_play_cancel",2,1,LydEventRole267V1::reverent_heaven_cancel},
 {"lyd.1032","lyd_play_knowing_acting_support_option_0",3,0,LydEventRole267V1::knowing_acting_inquiry},
 {"lyd.1032","lyd_play_cancel",3,2,LydEventRole267V1::knowing_acting_cancel}}};
bool RoleMatches(const LydEventRow267V1&row,const LydEventOption267V1&option)noexcept{if(!option.permitted_role||!option.source_bound_option_key)return false;for(const auto&r:kEventRules)if(r.role==option.permitted_role&&r.definition==row.definition_key&&r.count==row.authored_option_count&&r.index==option.authored_option_index&&r.option==option.source_bound_option_key)return true;return false;}
} // namespace
std::optional<LydDecision267V1>ParseLydDecisionKey267V1(std::string_view text)noexcept{for(std::size_t n=0;n<kLydDecisionKeys267V1.size();++n)if(kLydDecisionKeys267V1[n]==text)return static_cast<LydDecision267V1>(n);return{};}
LydKind267V1 LydKindForAction267V1(LydAction267V1 action)noexcept{const auto n=static_cast<unsigned>(action);return n<=3?LydKind267V1::decisions:n<=5?LydKind267V1::events:n<=11?LydKind267V1::personal:LydKind267V1::readback;}
bool LydQueryAction267V1(LydAction267V1 action)noexcept{return action==LydAction267V1::query_decisions||action==LydAction267V1::query_events||action==LydAction267V1::query_personal||action==LydAction267V1::query_add_confirmation||action==LydAction267V1::query_readback;}
bool LydRequestShape267V1(const LydRequest267V1&q)noexcept{
 const auto a=static_cast<unsigned>(q.action);if(a>=13||!Id(q.id())||!q.deadline_unix_ms||!Prefix(q.expected)||(q.decision&&static_cast<unsigned>(*q.decision)>=5)||(q.personal&&static_cast<unsigned>(*q.personal)>=2)||(q.event_role&&static_cast<unsigned>(*q.event_role)>=7))return false;
 if(LydQueryAction267V1(q.action)){if(q.provider_generation||q.query_sequence)return false;}else if(!q.provider_generation||!q.query_sequence)return false;
 if(a<=3)return !q.personal&&!q.event_role&&!q.instance_id&&q.choice_token.empty()&&((a<=1)?!q.decision:q.decision.has_value())&&!(a==3&&q.decision==LydDecision267V1::begin_readonly);
 if(a<=5)return !q.decision&&!q.personal&&q.choice_token.empty()&&(a==4?(!q.event_role&&!q.instance_id):(q.event_role&&q.instance_id&&*q.instance_id>0));
 if(a<=11)return !q.decision&&!q.event_role&&!q.instance_id&&q.personal&&(a==9?KeyText(q.choice_token,96):q.choice_token.empty());
 return !q.decision&&!q.personal&&!q.event_role&&!q.instance_id&&q.choice_token.empty();
}
namespace {
bool ParseRequest(std::string_view text,LydRequest267V1&out,std::string_view adapter)noexcept{
 out={};if(text.size()>16384)return false;Cursor c{text};LydRequest267V1 q;std::string_view step;if(!c.Take('{'))return false;unsigned seen=0;bool first=true;
 while(!c.Take('}')){if(!first&&!c.Take(','))return false;first=false;std::string_view key,value;if(!c.String(key)||!c.Take(':'))return false;unsigned bit=0;bool good=false;std::uint64_t n=0;
  if(key=="type"){bit=1;good=c.Identity("execute_step");}else if(key=="protocol_version"){bit=2;good=c.Number(n)&&n==1;}else if(key=="request_id"){bit=4;good=c.String(value)&&Id(value);if(good){std::copy(value.begin(),value.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(value.size());}}else if(key=="step"){bit=8;good=c.String(step);}else if(key=="expected_revision"){bit=16;good=c.Number(n)&&n==0;}else if(key=="arguments"){bit=32;good=c.Take('{')&&c.Take('}');}else if(key=="lyd"){bit=64;good=Claim(c,q,adapter);}else if(key=="core_control_deadline_unix_ms"){bit=128;good=c.Number(q.deadline_unix_ms)&&q.deadline_unix_ms;}
  if(!bit||!good||(seen&bit))return false;seen|=bit;
 }c.Space();if(seen!=255||c.pos!=text.size()||!LydRequestShape267V1(q)||step!=kLydSteps267V1[static_cast<std::size_t>(q.action)])return false;out=std::move(q);return true;
}
}
bool ParseLydRequest267V1(std::string_view text,LydRequest267V1&out)noexcept{
 return ParseRequest(text,out,kAdapterId);
}
bool ParseFull111LydEventRequest267V1(std::string_view text,LydRequest267V1&out)noexcept{
 LydRequest267V1 request;
 if(!ParseRequest(text,request,full111::kAdapterId)||request.action!=LydAction267V1::query_events){
  out={};return false;
 }
 out=std::move(request);return true;
}
bool LydPublicSourceShape267V1(const LydSource267V1&v)noexcept{
 if(static_cast<unsigned>(v.kind)>3||static_cast<unsigned>(bool(v.decisions))+static_cast<unsigned>(bool(v.events))+static_cast<unsigned>(bool(v.personal))+static_cast<unsigned>(bool(v.readback))!=1)return false;
 if(v.kind==LydKind267V1::decisions){
  if(!v.decisions)return false;const auto&s=*v.decisions;
  if(s.rows.size()>5||(!s.list_found&&(s.list_visible||s.list_enabled||s.complete_model_census||!s.rows.empty()||s.groups_count||s.total_model_rows))||(!s.detail_found&&(s.detail_visible||s.detail_enabled||s.selected_decision||s.other_decision_selected||s.native_can_confirm||s.widget_state)))return false;
  if(s.complete_model_census!=bool(s.groups_count&&s.total_model_rows)||(!s.complete_model_census&&(!s.rows.empty()||s.groups_count||s.total_model_rows)))return false;
  if(s.groups_count&&(*s.groups_count<0||*s.groups_count>64))return false;if(s.total_model_rows&&(*s.total_model_rows<0||*s.total_model_rows>1024))return false;
  if(s.other_decision_selected&&s.selected_decision)return false;if(s.native_can_confirm&&(!s.selected_decision||!s.detail_visible))return false;
  if(s.confirm_admissible&&(!s.detail_found||!s.detail_visible||!s.detail_enabled||s.blocked_by_visible_modal||!s.selected_decision||s.selected_decision==LydDecision267V1::begin_readonly||s.native_can_confirm!=true))return false;
  if(s.open_list_admissible&&(s.list_visible||s.blocked_by_visible_modal))return false;
  for(std::size_t i=0;i<s.rows.size();++i){const auto&r=s.rows[i];if(LydDecisionKey267V1(r.decision).empty())return false;for(std::size_t n=0;n<i;++n)if(s.rows[n].decision==r.decision)return false;if(r.is_selected!=(s.detail_visible&&s.selected_decision==r.decision))return false;if(r.can_open_detail&&(!s.list_visible||!s.list_enabled||r.is_selected||s.blocked_by_visible_modal))return false;}return !s.conditions_text||s.conditions_text->size()<=16384;
 }
 if(v.kind==LydKind267V1::events){
  if(!v.events)return false;const auto&s=*v.events;if(!s.census_complete||s.named_root_count<0||s.named_root_count>32||static_cast<std::size_t>(s.named_root_count)!=s.events.size())return false;
  for(std::size_t n=0;n<s.events.size();++n){const auto&r=s.events[n];if(r.instance_id<=0||r.recipient_character_id==-1||r.authored_option_count<0||r.authored_option_count>64||!KeyText(r.definition_key,256)||r.opening.size()>16384||r.description.size()>16384||!r.named_root_bound||r.options.size()>64)return false;for(std::size_t k=0;k<n;++k)if(s.events[k].instance_id==r.instance_id)return false;
   for(std::size_t i=0;i<r.options.size();++i){const auto&o=r.options[i];if(o.authored_option_index<0||o.authored_option_index>=r.authored_option_count||o.text.size()>16384||o.disabled_reason.size()>16384||(o.source_bound_option_key&&!KeyText(*o.source_bound_option_key,256))||(o.permitted_role&&(static_cast<unsigned>(*o.permitted_role)>=7||!RoleMatches(r,o))))return false;for(std::size_t k=0;k<i;++k)if(r.options[k].authored_option_index==o.authored_option_index)return false;}
  }return true;
 }
 if(v.kind==LydKind267V1::personal){
  if(!v.personal)return false;const auto&s=*v.personal;if(!s.resident_available||s.quoted_currency_costs||s.rows.size()>2048||s.slots.size()>64||s.actual_personal_keys.size()>64)return false;
  if(s.window_visible&&(!s.named_root_bound||!s.actor_bound||s.native_window_visible!=true||!s.model_materialized))return false;
  if(s.model_materialized){if(!s.slots_complete||!s.groups_complete||!s.slot_count||!s.group_count||*s.slot_count<0||*s.slot_count>64||*s.group_count<0||*s.group_count>7||static_cast<std::size_t>(*s.slot_count)!=s.slots.size())return false;}
  else if(s.slots_complete||s.groups_complete||s.slot_count||s.group_count||!s.slots.empty()||!s.rows.empty()||s.empty_slot_found)return false;
  bool empty=false;for(const auto&slot:s.slots){if(slot.is_empty){empty=true;if(slot.definition_key||slot.is_personal)return false;}else if(!slot.definition_key||!KeyText(*slot.definition_key))return false;}if(empty!=s.empty_slot_found)return false;
  for(std::size_t n=0;n<s.actual_personal_keys.size();++n){if(!KeyText(s.actual_personal_keys[n]))return false;for(std::size_t k=0;k<n;++k)if(s.actual_personal_keys[k]==s.actual_personal_keys[n])return false;}
  if(!s.actual_personal_complete&&!s.actual_personal_keys.empty())return false;
  for(std::size_t n=0;n<s.rows.size();++n){const auto&r=s.rows[n];if(r.group_category>6||!KeyText(r.definition_key)||(!r.choice_token.empty()&&!KeyText(r.choice_token,96)))return false;if(r.native_can_pick&&std::find(kLydPersonalKeys267V1.begin(),kLydPersonalKeys267V1.end(),r.definition_key)==kLydPersonalKeys267V1.end())return false;for(std::size_t k=0;k<n;++k)if(s.rows[k].definition_key==r.definition_key||(!r.choice_token.empty()&&s.rows[k].choice_token==r.choice_token))return false;
   if(r.select_admissible&&(!s.window_visible||!s.window_enabled||!s.actor_bound||!s.is_adding||!s.model_materialized||s.blocked_by_visible_modal||!s.empty_slot_found||!s.actual_personal_complete||!r.group_can_pick||r.is_personal||r.native_can_pick!=true||r.choice_token.empty()||std::find(kLydPersonalKeys267V1.begin(),kLydPersonalKeys267V1.end(),r.definition_key)==kLydPersonalKeys267V1.end()||std::find(s.actual_personal_keys.begin(),s.actual_personal_keys.end(),r.definition_key)!=s.actual_personal_keys.end()))return false;
  }
  if(s.open_admissible&&(s.window_visible||s.native_window_visible!=false||s.blocked_by_visible_modal))return false;
  if(s.start_add_admissible&&(!s.window_visible||!s.window_enabled||!s.actor_bound||!s.empty_slot_found||!s.model_materialized||s.is_adding||s.blocked_by_visible_modal))return false;
  const auto&m=s.add_modal;if(!m.found&&(m.named_root_bound||m.visible||m.closed||m.personal||m.native_can_accept||m.accept_admissible))return false;
  if(m.found&&(!m.personal||static_cast<unsigned>(*m.personal)>1||!m.named_root_bound))return false;
  if(m.accept_admissible&&(!m.found||!m.visible||m.closed||m.native_can_accept!=true||!s.actor_bound||!s.actual_personal_complete||!s.empty_slot_found))return false;return true;
 }
 return v.readback&&v.readback->resources.has_value()&&!v.readback->original_case_readback_complete&&!v.readback->legitimacy_raw&&!v.readback->diplomacy_xp_raw&&!v.readback->learning_xp_raw&&!v.readback->capital_control_raw;
}
bool LydPublicAdmissible267V1(const LydSource267V1&s,const LydRequest267V1&q)noexcept{
 if(static_cast<unsigned>(q.action)>=13||(q.personal&&static_cast<unsigned>(*q.personal)>=2)||(q.decision&&static_cast<unsigned>(*q.decision)>=5)||(q.event_role&&static_cast<unsigned>(*q.event_role)>=7)||s.kind!=LydKindForAction267V1(q.action)||!LydPublicSourceShape267V1(s))return false;
 if(q.action==LydAction267V1::open_list)return s.decisions->open_list_admissible;
 if(q.action==LydAction267V1::open_detail&&q.decision){for(const auto&r:s.decisions->rows)if(r.decision==q.decision)return r.can_open_detail;return false;}
 if(q.action==LydAction267V1::confirm_decision)return q.decision&&q.decision!=LydDecision267V1::begin_readonly&&s.decisions->selected_decision==q.decision&&s.decisions->confirm_admissible;
 if(q.action==LydAction267V1::choose_known_event_option&&q.instance_id&&q.event_role){for(const auto&r:s.events->events)if(r.instance_id==q.instance_id&&r.recipient_character_id==q.expected.played_character_id&&r.named_root_bound&&r.window_visible&&r.window_enabled){for(const auto&o:r.options)if(o.permitted_role==q.event_role&&o.native_can_select)return true;}return false;}
 if(q.action==LydAction267V1::open_personal)return s.personal->open_admissible;
 if(q.action==LydAction267V1::start_add_personal)return s.personal->start_add_admissible;
 if(q.action==LydAction267V1::select_personal_candidate&&q.personal){for(const auto&r:s.personal->rows)if(r.definition_key==kLydPersonalKeys267V1[static_cast<std::size_t>(*q.personal)]&&r.choice_token==q.choice_token)return r.select_admissible;return false;}
 if(q.action==LydAction267V1::confirm_personal_add)return q.personal&&s.personal->add_modal.personal==q.personal&&s.personal->add_modal.accept_admissible;
 return false;
}
namespace {
void Resources(Json&j,const RawResources&r){j.data+="{\"personal_gold_raw\":";String(j.data,std::to_string(r.personal_gold_raw));j.str("prestige_raw",std::to_string(r.prestige_raw));j.str("piety_raw",std::to_string(r.piety_raw));j.num("stress_points",r.stress_points);j.data+='}';}
void DecisionSource(Json&j,const LydDecisionSource267V1&s){
 j.data+="{\"list_found\":";j.data+=s.list_found?"true":"false";j.flag("list_visible",s.list_visible);j.flag("list_enabled",s.list_enabled);j.flag("detail_found",s.detail_found);j.flag("detail_visible",s.detail_visible);j.flag("detail_enabled",s.detail_enabled);j.flag("other_decision_selected",s.other_decision_selected);j.flag("open_list_admissible",s.open_list_admissible);j.flag("complete_model_census",s.complete_model_census);j.flag("blocked_by_visible_modal",s.blocked_by_visible_modal);j.flag("confirm_admissible",s.confirm_admissible);j.nullable("groups_count",s.groups_count);j.nullable("total_model_rows",s.total_model_rows);j.nullable("widget_state",s.widget_state);Enum(j,"selected_decision_key",kLydDecisionKeys267V1,s.selected_decision);j.nullable("native_can_confirm",s.native_can_confirm);j.key("rows");j.data+='[';
 for(std::size_t n=0;n<s.rows.size();++n){if(n)j.data+=',';const auto&r=s.rows[n];j.data+="{\"decision_key\":";String(j.data,LydDecisionKey267V1(r.decision));j.flag("can_open_detail",r.can_open_detail);j.flag("is_selected",r.is_selected);j.data+='}';}j.data+=']';j.nullable("conditions_text",s.conditions_text);j.data+='}';
}
void EventSource(Json&j,const LydEventSource267V1&s,bool include_permissions){
 j.data+="{\"census_complete\":";j.data+=s.census_complete?"true":"false";j.num("named_root_count",s.named_root_count);j.key("events");j.data+='[';
 for(std::size_t n=0;n<s.events.size();++n){if(n)j.data+=',';const auto&r=s.events[n];j.data+="{\"instance_id\":"+std::to_string(r.instance_id);j.num("recipient_character_id",r.recipient_character_id);j.num("authored_option_count",r.authored_option_count);j.str("definition_key",r.definition_key);j.str("opening",r.opening);j.str("description",r.description);j.flag("named_root_bound",r.named_root_bound);j.flag("window_visible",r.window_visible);j.flag("window_enabled",r.window_enabled);j.key("options");j.data+='[';
  for(std::size_t k=0;k<r.options.size();++k){if(k)j.data+=',';const auto&o=r.options[k];j.data+="{\"authored_option_index\":"+std::to_string(o.authored_option_index);j.flag("native_can_select",o.native_can_select);j.str("text",o.text);j.str("disabled_reason",o.disabled_reason);j.nullable("source_bound_option_key",include_permissions?o.source_bound_option_key:std::nullopt);Enum(j,"permitted_role",kLydEventRoleNames267V1,include_permissions?o.permitted_role:std::nullopt);j.data+='}';}j.data+="]}";
 }j.data+="]}";
}
void PersonalSource(Json&j,const LydPersonalSource267V1&s){
 j.data+="{\"resident_available\":";j.data+=s.resident_available?"true":"false";j.flag("named_root_bound",s.named_root_bound);j.flag("window_visible",s.window_visible);j.flag("window_enabled",s.window_enabled);j.flag("actor_bound",s.actor_bound);j.flag("is_adding",s.is_adding);j.flag("model_materialized",s.model_materialized);j.flag("slots_complete",s.slots_complete);j.flag("groups_complete",s.groups_complete);j.flag("empty_slot_found",s.empty_slot_found);j.flag("actual_personal_complete",s.actual_personal_complete);j.flag("blocked_by_visible_modal",s.blocked_by_visible_modal);j.flag("open_admissible",s.open_admissible);j.flag("start_add_admissible",s.start_add_admissible);j.nullable("slot_count",s.slot_count);j.nullable("group_count",s.group_count);j.nullable("native_window_visible",s.native_window_visible);j.key("slots");j.data+='[';
 for(std::size_t n=0;n<s.slots.size();++n){if(n)j.data+=',';const auto&r=s.slots[n];j.data+="{\"is_empty\":";j.data+=r.is_empty?"true":"false";j.flag("is_personal",r.is_personal);j.nullable("definition_key",r.definition_key);j.data+='}';}j.data+=']';j.key("rows");j.data+='[';
 for(std::size_t n=0;n<s.rows.size();++n){if(n)j.data+=',';const auto&r=s.rows[n];j.data+="{\"group_category\":"+std::to_string(r.group_category);j.str("definition_key",r.definition_key);j.str("choice_token",r.choice_token);j.flag("group_can_pick",r.group_can_pick);j.flag("is_personal",r.is_personal);j.nullable("native_can_pick",r.native_can_pick);j.flag("select_admissible",r.select_admissible);j.data+='}';}j.data+=']';j.key("actual_personal_keys");j.data+='[';for(std::size_t n=0;n<s.actual_personal_keys.size();++n){if(n)j.data+=',';String(j.data,s.actual_personal_keys[n]);}j.data+=']';
 const auto&m=s.add_modal;j.key("add_modal");j.data+="{\"found\":";j.data+=m.found?"true":"false";j.flag("named_root_bound",m.named_root_bound);j.flag("visible",m.visible);j.flag("closed",m.closed);Enum(j,"personal_key",kLydPersonalKeys267V1,m.personal);j.nullable("native_can_accept",m.native_can_accept);j.flag("accept_admissible",m.accept_admissible);j.data+='}';j.raw("spiritual_fulfillment_raw",s.spiritual_fulfillment_raw);j.key("quoted_currency_costs");if(s.quoted_currency_costs)Resources(j,*s.quoted_currency_costs);else j.data+="null";j.data+='}';
}
void ReadbackSource(Json&j,const LydReadbackSource267V1&s){j.data+="{\"resources\":";if(s.resources)Resources(j,*s.resources);else j.data+="null";j.raw("legitimacy_raw",s.legitimacy_raw);j.raw("diplomacy_xp_raw",s.diplomacy_xp_raw);j.raw("learning_xp_raw",s.learning_xp_raw);j.raw("capital_control_raw",s.capital_control_raw);j.flag("original_case_readback_complete",s.original_case_readback_complete);j.data+='}';}
void WriteSource(Json&j,const LydSource267V1&s,bool include_event_permissions){
 constexpr std::array<std::string_view,4>kinds{"decisions","events","personal","readback"};j.data+="{\"schema\":";String(j.data,kLydSourceSchema267V1);j.str("kind",kinds[static_cast<std::size_t>(s.kind)]);j.key("decisions");if(s.decisions)DecisionSource(j,*s.decisions);else j.data+="null";j.key("events");if(s.events)EventSource(j,*s.events,include_event_permissions);else j.data+="null";j.key("personal");if(s.personal)PersonalSource(j,*s.personal);else j.data+="null";j.key("readback");if(s.readback)ReadbackSource(j,*s.readback);else j.data+="null";j.data+='}';
}
}
namespace {
std::string SerializeResult(std::string_view id,const LydResult267V1&r,std::string_view adapter){
 const bool full111_events_only=adapter==full111::kAdapterId;
 const auto a=static_cast<std::size_t>(r.action);const bool facts=r.facts_available&&Prefix(r.facts)&&r.connection_generation&&r.ticket_sequence&&r.pump_epoch&&r.thread_id;
 const bool source=facts&&r.cleanup_known&&r.source_available&&r.source&&LydPublicSourceShape267V1(*r.source)&&
  r.source->kind==LydKindForAction267V1(r.action)&&(!full111_events_only||
   (r.action==LydAction267V1::query_events&&r.status==LydStatus267V1::available&&
    r.provider_generation&&r.query_sequence&&!r.claim_sequence&&!r.effect_attempted&&
    !r.native_returned&&!r.native_handled&&!r.source->events->events.empty()));
 const bool lease=r.provider_generation&&r.query_sequence;LydRequest267V1 q;q.action=r.action;q.expected=r.facts;q.decision=r.decision;q.personal=r.personal;q.event_role=r.event_role;q.instance_id=r.instance_id;
 // The opaque selected token is preserved only in the private request. Public selection dispatch is independently authorized by the matching reviewed key/row.
 if(source&&q.personal&&static_cast<std::size_t>(*q.personal)<kLydPersonalKeys267V1.size()&&a==9){for(const auto&row:r.source->personal->rows)if(row.definition_key==kLydPersonalKeys267V1[static_cast<std::size_t>(*q.personal)]&&row.select_admissible){q.choice_token=row.choice_token;break;}}
 const bool read=a<13&&LydQueryAction267V1(r.action)&&r.status==LydStatus267V1::available&&source&&lease&&!r.effect_attempted&&!r.native_returned&&!r.native_handled&&!r.claim_sequence;
 const auto desired=a==3||a==5||a==11?LydStatus267V1::confirmation_dispatched:a==2||a==9?LydStatus267V1::selection_dispatched:LydStatus267V1::navigation_dispatched;
 const bool dispatched=!full111_events_only&&a<13&&!LydQueryAction267V1(r.action)&&r.status==desired&&source&&lease&&r.claim_sequence&&r.effect_attempted&&r.native_returned&&(!r.native_handled||a==1||a==7)&&LydPublicAdmissible267V1(*r.source,q);
 const bool ok=read||dispatched;auto status=r.status;if(!ok&&(status==LydStatus267V1::available||status==LydStatus267V1::navigation_dispatched||status==LydStatus267V1::selection_dispatched||status==LydStatus267V1::confirmation_dispatched))status=LydStatus267V1::indeterminate;
 Json j;j.data=R"({"type":"command_result","protocol_version":1,"request_id":)";String(j.data,id);j.data+=ok?R"(,"ok":true,"result":{"schema":)":R"(,"ok":false,"result":{"schema":)";String(j.data,kLydResultSchema267V1);
 j.str("game_version",kGameVersion);j.str("executable_sha256",kExecutableSha256);j.str("backend",kLydBackend267V1);j.str("adapter_id",adapter);j.str("action",a<13?kLydActionNames267V1[a]:"invalid");j.str("status",Status(status));j.flag("source_available",source);j.flag("effect_attempted",r.effect_attempted);j.flag("native_returned",r.native_returned);j.flag("native_handled",r.native_handled);j.flag("cleanup_known",r.cleanup_known);j.u64("provider_generation",r.provider_generation);j.u64("query_sequence",r.query_sequence);j.u64("claim_sequence",r.claim_sequence);
 Enum(j,"decision_key",kLydDecisionKeys267V1,r.decision);Enum(j,"personal_key",kLydPersonalKeys267V1,r.personal);Enum(j,"event_role",kLydEventRoleNames267V1,r.event_role);j.nullable("instance_id",r.instance_id);
 j.key("facts_before");if(facts){const auto&p=r.facts;j.data+="{\"date_raw\":"+std::to_string(p.clock.date_raw);j.num("speed",p.clock.speed);j.flag("paused",p.clock.paused);j.num("local_player_id",p.local_player_id);j.flag("map_ready",p.map_ready);j.flag("has_played_character",p.has_played_character);j.num("played_character_id",p.played_character_id);j.flag("played_character_alive",p.played_character_alive);j.data+='}';}else j.data+="null";
 j.key("owner");if(facts){j.data+="{\"connection_generation\":";String(j.data,std::to_string(r.connection_generation));j.u64("ticket_sequence",r.ticket_sequence);j.u64("pump_epoch",r.pump_epoch);j.num("thread_id",r.thread_id);j.data+='}';}else j.data+="null";
 j.key("source");if(source)WriteSource(j,*r.source,!full111_events_only);else j.data+="null";
 j.flag("addresses_redacted",true);j.flag("event_closed",false);j.flag("personal_applied",false);j.flag("gold_paid",false);j.flag("piety_paid",false);j.flag("modifiers_applied",false);j.flag("new_date_observed",false);j.flag("physical_save_confirmed",false);j.key("unavailable_reason");if(ok)j.data+="null";else String(j.data,r.reason.empty()?"current_lyd_source_unavailable":r.reason);j.data+="}}";return j.data;
}
}
std::string SerializeLydResult267V1(std::string_view id,const LydResult267V1&r){
 return SerializeResult(id,r,kAdapterId);
}
std::string SerializeFull111LydEventResult267V1(std::string_view id,const LydResult267V1&r){
 return SerializeResult(id,r,full111::kAdapterId);
}
}

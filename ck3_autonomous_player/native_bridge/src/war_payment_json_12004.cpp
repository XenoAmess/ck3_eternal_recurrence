#include "xar_bridge/war_payment_runtime_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <limits>
#include <type_traits>

namespace xar::ck3_12004 {
namespace {
using Event=ArmyNaturalPhaseEvent12004;
std::string Quoted(std::string_view value) {
  std::string out="\"";constexpr char hex[]="0123456789abcdef";
  for(const unsigned char c:value) {
    if(c=='"'||c=='\\') {out+='\\';out+=static_cast<char>(c);}
    else if(c<32) {out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }
  out+='"';return out;
}
struct Object {
  std::string text="{";bool first=true;
  void Raw(std::string_view key,std::string value) {if(!first)text+=',';first=false;text+=Quoted(key);text+=':';text+=value;}
  void Str(std::string_view key,std::string_view value) {Raw(key,Quoted(value));}
  void Num(std::string_view key,auto value) {Raw(key,std::to_string(value));}
  void Bool(std::string_view key,bool value) {Raw(key,value?"true":"false");}
  template<class T>void Opt(std::string_view key,const std::optional<T> &v) {if(v)Num(key,*v);else Raw(key,"null");}
  std::string Done(){return text+'}';}
};
std::string EventJson(const Event &e) {Object o;o.Num("clock_identity",e.clock_identity);o.Num("sequence",e.sequence);o.Opt("thread_id",e.thread_id);return o.Done();}
bool ValidEvent(const Event &e) noexcept {return e.clock_identity && e.sequence && e.thread_id;}
bool ExactSha(std::string_view value) noexcept {
  if(value.size()!=64)return false;
  const auto lower=[](unsigned char c) {return static_cast<unsigned char>(c>='A'&&c<='F'?c+('a'-'A'):c);};
  for(std::size_t i=0;i<64;++i)if(lower(static_cast<unsigned char>(value[i]))!=lower(static_cast<unsigned char>(kExecutableSha256[i])))return false;
  return true;
}
bool SameEvent(const Event &a,const Event &b) noexcept {
  return ValidEvent(a)&&ValidEvent(b)&&a.clock_identity==b.clock_identity&&a.sequence==b.sequence&&a.thread_id==b.thread_id;
}
bool Before(const Event &a,const Event &b) noexcept {
  return ValidEvent(a)&&ValidEvent(b)&&a.clock_identity==b.clock_identity&&a.thread_id==b.thread_id&&a.sequence<b.sequence;
}
bool Session(const WarPaymentSession12004 &a,const WarPaymentSession12004 &b) noexcept {
  if(!a.pid||!a.process_create_time_100ns||!a.connection_generation||!a.player_character_full_id||
     a.pid!=b.pid||a.process_create_time_100ns!=b.process_create_time_100ns||
     a.connection_generation!=b.connection_generation||a.player_character_full_id!=b.player_character_full_id||
     a.loaded_game_epoch!=b.loaded_game_epoch)return false;
  if(a.loaded_game_epoch&&*a.loaded_game_epoch)return true;
  return a.same_owned_process_no_load_window&&b.same_owned_process_no_load_window&&
    a.controlled_window_id&&a.controlled_window_id==b.controlled_window_id&&
    a.game_state_identity_witness&&a.game_state_identity_witness==b.game_state_identity_witness;
}
std::string SessionJson(const WarPaymentSession12004 &s) {
  Object o;o.Num("pid",s.pid);o.Num("process_create_time_100ns",s.process_create_time_100ns);
  o.Num("connection_generation",s.connection_generation);o.Opt("loaded_game_epoch",s.loaded_game_epoch);
  o.Num("controlled_window_id",s.controlled_window_id);o.Bool("same_owned_process_no_load_window",s.same_owned_process_no_load_window);
  o.Num("game_state_identity_witness",s.game_state_identity_witness);o.Opt("player_character_full_id",s.player_character_full_id);
  o.Opt("snapshot_revision",s.snapshot_revision);o.Opt("native_date_raw",s.native_date_raw);o.Opt("absolute_day_raw",s.absolute_day_raw);return o.Done();
}
std::string SamplingJson(const ArmyObserverResearchSamplingState12004 &s) {
  Object o;o.Bool("available",s.available);o.Bool("capture_enabled",s.enabled);o.Bool("busy",s.busy);o.Bool("clear_completed",s.clear_completed);
  o.Num("epoch",s.epoch);o.Num("active_captures",s.active_captures);o.Num("retained_records",s.retained_records);o.Num("qualified_records",s.qualified_records);return o.Done();
}
std::string FrameJson(const WarPaymentFrame12004 &f) {
  Object o;o.Num("character",f.character);o.Num("wrapper",f.wrapper);
#define OPT(name) o.Opt(#name,f.name)
  OPT(character_id);OPT(character_magic);OPT(character_extension);OPT(personal_gold_bits);OPT(wrapper_balance_bits);
  OPT(land_id);OPT(land_magic);OPT(army_id);OPT(army_magic);OPT(requested_unit_id);OPT(province_magic);OPT(province_id);OPT(army_1d4);
#undef OPT
  o.Bool("capture_complete",f.capture_complete);o.Num("failed_reads",f.failed_reads);return o.Done();
}
std::string NaturalJson(const WarPaymentNaturalParent12004 &p) {
  Object o;o.Bool("observed",p.observed);o.Num("phase",static_cast<unsigned>(p.phase));o.Num("actual_entry_rva",p.actual_entry_rva);
  o.Num("primary_manager",p.primary_manager);o.Num("game_state",p.game_state);o.Opt("session_identity",p.session_identity);
  o.Raw("entry_event",EventJson(p.entry_event));o.Opt("date_raw",p.date_raw);o.Opt("absolute_day_raw",p.absolute_day_raw);return o.Done();
}
bool Complete(const WarPaymentRecord12004 &r,const WarPaymentSession12004 &current) noexcept {
  return r.original_called&&r.original_returned&&!r.tls_depth_exceeded&&r.before.capture_complete&&r.after.capture_complete&&
    !r.before.failed_reads&&!r.after.failed_reads&&Before(r.entry_event,r.returned_event)&&
    Session(r.session_entry,r.session_return)&&Session(r.session_entry,current);
}
bool SameCharacter(const WarPaymentFrame12004 &a,const WarPaymentFrame12004 &b) noexcept {
  return a.character&&a.character==b.character&&a.character_id&&a.character_id==b.character_id&&
    *a.character_id!=0xFFFFFFFFU&&a.character_magic==0x43686172U&&b.character_magic==0x43686172U&&
    a.character_extension&&*a.character_extension&&a.character_extension==b.character_extension;
}
const WarPaymentRecord12004 *Find(const WarPaymentJournalSnapshot12004 &j,WarPaymentKind12004 kind,const Event &e) noexcept {
  const WarPaymentRecord12004 *found=nullptr;
  for(const auto &r:j.records)if(r.kind==kind&&SameEvent(r.entry_event,e)) {if(found)return nullptr;found=&r;}
  return found;
}
bool NaturalMatches(const WarPaymentRecord12004 &r,const ArmyNaturalPhaseRecord12004 &n,const WarPaymentSession12004 &current) noexcept {
  const auto &p=r.natural_parent_metadata;const auto &q=r.natural_return_metadata;const auto &s=n.scope;
  if(!p.observed||!q.observed||!s.observed||p.phase!=ArmyNaturalPhaseKind12004::post_date||q.phase!=p.phase||s.phase!=p.phase||
     p.actual_entry_rva!=0x2A9A570||q.actual_entry_rva!=p.actual_entry_rva||s.actual_entry_rva!=p.actual_entry_rva||
     !p.primary_manager||p.primary_manager!=q.primary_manager||p.primary_manager!=s.primary_manager_identity||
     !p.game_state||p.game_state!=q.game_state||p.game_state!=s.game_state_identity||
     !SameEvent(p.entry_event,q.entry_event)||!SameEvent(p.entry_event,s.entry_event)||
     !Before(s.entry_event,r.entry_event)||!Before(r.returned_event,n.returned_event)||
     !n.original_called||!n.original_returned||!p.date_raw||p.date_raw!=q.date_raw||p.date_raw!=s.date_raw||
     !p.absolute_day_raw||p.absolute_day_raw!=q.absolute_day_raw||p.absolute_day_raw!=s.absolute_day_raw||
     !n.returned_date_raw||n.returned_date_raw!=s.date_raw||
     !n.returned_absolute_day_raw||n.returned_absolute_day_raw!=s.absolute_day_raw)return false;
  if(current.loaded_game_epoch&&*current.loaded_game_epoch)
    return p.session_identity==current.loaded_game_epoch&&q.session_identity==current.loaded_game_epoch&&s.session_identity==current.loaded_game_epoch;
  return current.same_owned_process_no_load_window&&current.game_state_identity_witness==p.game_state&&
    !p.session_identity&&!q.session_identity&&!s.session_identity;
}
std::string GenericValuesJson(const WarPaymentGenericValues12004 &v) {
  Object o;
  o.Opt("context_identity_before",v.context_identity_before);o.Opt("context_identity_after",v.context_identity_after);
  o.Opt("value_2c0",v.value_2c0);o.Opt("value_2c8",v.value_2c8);o.Opt("value_28",v.value_28);o.Opt("value_30",v.value_30);
  o.Bool("capture_complete",v.capture_complete);o.Bool("context_stable",v.context_stable);o.Num("failed_reads",v.failed_reads);return o.Done();
}
std::string GenericParentJson(const WarPaymentGenericParentTrace12004 &p) {
  Object o;o.Num("module_base",p.module_base);o.Num("module_image_size",p.module_image_size);
  o.Num("reported_frame_count",p.reported_frame_count);o.Bool("capture_succeeded",p.capture_succeeded);
  o.Bool("truncated",p.truncated);o.Num("caller_match_count",p.caller_match_count);
  std::string frames="[";
  if(p.capture_succeeded)for(std::size_t i=0;i<p.reported_frame_count;++i) {if(i)frames+=',';frames+=std::to_string(p.frames_absolute[i]);}
  frames+=']';o.Raw("frames_absolute",std::move(frames));
  o.Opt("parent_return_absolute",p.parent_return_absolute);o.Opt("parent_return_rva",p.parent_return_rva);
  o.Bool("parent_in_same_image",p.parent_in_same_image);return o.Done();
}
std::string GenericContextJson(const WarPaymentGenericContext12004 &g) {
  Object o;o.Num("schema_version",1);o.Num("source_entry_rva",kWarPaymentGenericSource12004);
  o.Num("source_wallet_return_rva",kWarPaymentGenericReturn12004);
  o.Str("attribution_scope","raw_source_context_and_unwind_parent_only");o.Str("maintenance_attribution","unclosed");
  o.Raw("before",GenericValuesJson(g.before));o.Raw("after",GenericValuesJson(g.after));
  o.Raw("parent_trace",GenericParentJson(g.parent_trace));
  o.Opt("before_computed_add_raw",g.before_computed_add_raw);
  if(g.before_formula_matches_amount)o.Bool("before_formula_matches_amount",*g.before_formula_matches_amount);
  else o.Raw("before_formula_matches_amount","null");
  o.Bool("context_values_stable",g.context_values_stable);return o.Done();
}


std::string Raw4FrameJson(const WarPaymentRaw4Frame12004 &f) {
  Object o;o.Opt("character_full_id",f.character_full_id);o.Opt("character_magic",f.character_magic);
  o.Opt("extension",f.extension);o.Opt("context",f.context);o.Opt("physical_4a0_bits",f.physical_4a0_bits);
  o.Num("failed_reads",f.failed_reads);return o.Done();
}
std::string Raw4Json(const WarPaymentRaw4Snapshot12004 &s) {
  Object o;o.Num("schema_version",1);o.Num("source_entry_rva",0x28B9490);
  o.Str("capture_origin","native_entry_detour");o.Str("resource_name","unknown");
  o.Str("payment_attribution","unclosed");o.Bool("read_complete",s.read_complete);
  o.Num("latest_sequence",s.latest_sequence);o.Num("oldest_sequence",s.oldest_sequence);
  o.Num("overwritten",s.overwritten);o.Num("publication_failures",s.publication_failures);
  std::string rows="[";bool first=true;
  for(const auto &r:s.records) {
    if(!first)rows+=',';first=false;Object v;
    v.Num("journal_sequence",r.journal_sequence);v.Num("raw_selector",r.raw_selector);
    v.Num("character",r.character);v.Num("out_pointer",r.out_pointer);
    v.Num("caller_return_absolute",r.caller_return_absolute);v.Num("module_base",r.module_base);
    v.Opt("caller_return_rva",r.caller_return_rva);v.Raw("entry_event",EventJson(r.entry_event));
    v.Raw("returned_event",EventJson(r.returned_event));v.Raw("session_entry",SessionJson(r.session_entry));
    v.Raw("session_return",SessionJson(r.session_return));
    v.Raw("natural_parent_metadata",NaturalJson(r.natural_parent_metadata));
    v.Raw("natural_return_metadata",NaturalJson(r.natural_return_metadata));
    v.Raw("before",Raw4FrameJson(r.before));v.Raw("after",Raw4FrameJson(r.after));
    v.Opt("out64_bits",r.out64_bits);v.Num("output_failed_reads",r.output_failed_reads);
    v.Bool("original_called",r.original_called);v.Bool("original_returned",r.original_returned);
    v.Num("raw_return_bits",r.raw_return_bits);rows+=v.Done();
  }
  rows+=']';o.Raw("records",std::move(rows));return o.Done();
}

std::string RecordJson(const WarPaymentRecord12004 &r) {
  Object o;
#define NUM(name) o.Num(#name,r.name)
#define BOOL(name) o.Bool(#name,r.name)
  NUM(journal_sequence);o.Num("kind",static_cast<unsigned>(r.kind));NUM(receiver);NUM(second_pointer);NUM(caller_return_rva);NUM(amount_raw);NUM(resource_kind_raw);NUM(component_raw);
  o.Raw("entry_event",EventJson(r.entry_event));o.Raw("returned_event",EventJson(r.returned_event));
  o.Raw("parent_transition_entry",EventJson(r.parent_transition_entry));o.Raw("parent_gateway_entry",EventJson(r.parent_gateway_entry));
  NUM(parent_transition_army);NUM(parent_gateway_character);NUM(parent_transition_caller);NUM(parent_gateway_caller);NUM(parent_gateway_resource);NUM(parent_gateway_component);NUM(parent_gateway_amount);
  o.Raw("natural_parent_metadata",NaturalJson(r.natural_parent_metadata));o.Raw("natural_return_metadata",NaturalJson(r.natural_return_metadata));
  o.Raw("session_entry",SessionJson(r.session_entry));o.Raw("session_return",SessionJson(r.session_return));o.Raw("before",FrameJson(r.before));o.Raw("after",FrameJson(r.after));
  BOOL(original_called);BOOL(original_returned);NUM(raw_return_bits);BOOL(clock_thread_order_matches);BOOL(session_matches);BOOL(natural_parent_matches);BOOL(same_character_after);BOOL(same_wrapper_after);BOOL(personal_wrapper_matches_character);BOOL(source_boarding_call_chain_matches);BOOL(tls_depth_exceeded);
#undef NUM
#undef BOOL
  if(r.generic_wallet_context)o.Raw("generic_wallet_context_v1",GenericContextJson(*r.generic_wallet_context));
  return o.Done();
}
} // namespace

std::vector<WarPaymentQualifiedDebit12004> QualifyWarPaymentDebits12004(const WarPaymentJournalSnapshot12004 &j,
    const WarPaymentEnvelope12004 &e,const std::vector<ArmyNaturalPhaseRecord12004> &natural,const ArmyNaturalPhaseJournalStatus12004 &ns) {
  std::vector<WarPaymentQualifiedDebit12004> out;
  if(!e.installed||e.install_failure_flags||e.machine_id.empty()||!ExactSha(e.executable_sha256)||
     (!e.current_session.loaded_game_epoch&&!e.controlled_window_admitted)||
     !Session(e.current_session,e.current_session)||!j.read_complete||!j.sampling.available||!j.sampling.enabled||j.sampling.busy||
     j.sampling.active_captures||j.overwritten||j.publication_failures||!ns.read_complete||ns.overwritten_records||ns.failed_appends)return out;
  for(const auto &w:j.records) {
    const bool personal=w.kind==WarPaymentKind12004::personal_sub;
    const bool land=w.kind==WarPaymentKind12004::land_sub;
    if((!personal&&!land)||w.amount_raw<=0||!Complete(w,e.current_session)||!SameCharacter(w.before,w.after)||
       w.before.character_id!=e.current_session.player_character_full_id||
       !w.before.wrapper||w.before.wrapper!=w.after.wrapper||w.receiver!=w.before.wrapper||
       w.second_pointer!=w.before.character||!w.before.wrapper_balance_bits||!w.after.wrapper_balance_bits||
       (personal&&w.caller_return_rva!=0x28B99B2)||(land&&w.caller_return_rva!=0x28B9A6D))continue;
    if(personal&&(*w.before.character_extension>(std::numeric_limits<std::uintptr_t>::max)()-0xF8||
       w.before.wrapper!=*w.before.character_extension+0xF8))continue;
    if(land&&(!w.before.land_id||w.before.land_id!=w.after.land_id||*w.before.land_id==0xFFFFFFFFU||
       w.before.land_magic!=0x4C616E64U||w.after.land_magic!=0x4C616E64U))continue;
    const auto *g=Find(j,WarPaymentKind12004::gateway,w.parent_gateway_entry);
    const auto *t=Find(j,WarPaymentKind12004::transition,w.parent_transition_entry);
    if(!g||!t||!Complete(*g,e.current_session)||!Complete(*t,e.current_session)||
       g->caller_return_rva!=0x24E8F40||t->caller_return_rva!=0x2A9A8C5||
       !SameCharacter(g->before,g->after)||g->before.character!=w.before.character||
       g->before.character_id!=w.before.character_id||g->before.character_extension!=w.before.character_extension||
       g->receiver!=w.before.character||g->resource_kind_raw!=(personal?0:3)||g->component_raw!=3||g->amount_raw!=w.amount_raw||
       w.parent_gateway_character!=g->receiver||w.parent_gateway_caller!=g->caller_return_rva||
       w.parent_gateway_resource!=g->resource_kind_raw||w.parent_gateway_component!=g->component_raw||w.parent_gateway_amount!=g->amount_raw||
       w.parent_transition_army!=t->receiver||w.parent_transition_caller!=t->caller_return_rva||
       g->parent_transition_army!=t->receiver||g->parent_transition_caller!=t->caller_return_rva||
       !SameEvent(g->parent_transition_entry,t->entry_event)||
       !Before(t->entry_event,g->entry_event)||!Before(g->entry_event,w.entry_event)||
       !Before(w.returned_event,g->returned_event)||!Before(g->returned_event,t->returned_event)||
       !t->before.army_id||t->before.army_id!=t->after.army_id||*t->before.army_id==0xFFFFFFFFU||
       !t->before.army_magic||t->before.army_magic!=t->after.army_magic||
       !t->before.requested_unit_id||t->before.requested_unit_id!=t->after.requested_unit_id||
       !t->before.province_id||t->before.province_id!=t->after.province_id||
       t->before.province_magic!=0x50726F76U||t->after.province_magic!=0x50726F76U||t->before.army_1d4!=0)continue;
    bool parent_return=false;
    for(const auto &n:natural)if(NaturalMatches(w,n,e.current_session)&&NaturalMatches(*g,n,e.current_session)&&NaturalMatches(*t,n,e.current_session)) {parent_return=true;break;}
    if(!parent_return)continue;
    // These are full callback entry/return balances, not instruction-local store
    // values. Keep mismatches raw and do not promote them as an exact debit.
    const auto expected=*w.before.wrapper_balance_bits-static_cast<std::uint64_t>(w.amount_raw);
    if(expected!=*w.after.wrapper_balance_bits)continue;
    out.push_back({w.journal_sequence,t->journal_sequence,g->journal_sequence,personal?0:3,
      *w.before.character_id,land?w.before.land_id:std::nullopt,w.amount_raw,*w.before.wrapper_balance_bits,*w.after.wrapper_balance_bits,true});
  }
  return out;
}
std::string SerializeWarPaymentJournal12004(const WarPaymentJournalSnapshot12004 &j,const WarPaymentEnvelope12004 &e,
    const std::vector<ArmyNaturalPhaseRecord12004> &natural,const ArmyNaturalPhaseJournalStatus12004 &ns) {
  Object o;o.Num("schema_version",1);o.Str("machine_id",e.machine_id);o.Str("executable_sha256",e.executable_sha256);
  o.Str("game_version","1.20.0.4");o.Num("steam_build_id",25734779);o.Bool("installed",e.installed);o.Num("install_failure_flags",e.install_failure_flags);
  o.Bool("controlled_window_admitted",e.controlled_window_admitted);o.Str("session_basis",e.current_session.loaded_game_epoch?"source_proved_epoch":e.controlled_window_admitted?"same_owned_process_no_load_window":"unqualified");
  o.Str("balance_boundary","whole_original_callback_entry_return");o.Str("maintenance_attribution","unclosed");
  o.Raw("current_session",SessionJson(e.current_session));o.Raw("sampling",SamplingJson(j.sampling));o.Bool("read_complete",j.read_complete);
  o.Num("latest_sequence",j.latest_sequence);o.Num("oldest_sequence",j.oldest_sequence);o.Num("overwritten",j.overwritten);o.Num("publication_failures",j.publication_failures);
  Object n;n.Bool("read_complete",ns.read_complete);n.Num("retained_records",ns.retained_records);n.Num("overwritten_records",ns.overwritten_records);n.Num("failed_appends",ns.failed_appends);o.Raw("natural_journal_status",n.Done());
  std::string records="[";bool first=true;for(const auto &r:j.records) {if(!first)records+=',';first=false;records+=RecordJson(r);}records+=']';o.Raw("records",std::move(records));
  std::string parents="[";first=true;for(const auto &p:natural) {if(!first)parents+=',';first=false;Object v;const auto &s=p.scope;
    v.Raw("metadata",NaturalJson({s.observed,s.phase,s.actual_entry_rva,s.primary_manager_identity,s.game_state_identity,s.session_identity,s.entry_event,s.date_raw,s.absolute_day_raw}));
    v.Bool("original_called",p.original_called);v.Bool("original_returned",p.original_returned);v.Num("raw_return_bits",p.raw_return_bits);v.Raw("returned_event",EventJson(p.returned_event));
    v.Opt("returned_date_raw",p.returned_date_raw);v.Opt("returned_absolute_day_raw",p.returned_absolute_day_raw);parents+=v.Done();}parents+=']';o.Raw("natural_parent_returns",std::move(parents));
  const auto qualified=QualifyWarPaymentDebits12004(j,e,natural,ns);std::string debits="[";first=true;
  for(const auto &q:qualified) {if(!first)debits+=',';first=false;Object v;v.Num("writer_sequence",q.writer_sequence);v.Num("transition_sequence",q.transition_sequence);v.Num("gateway_sequence",q.gateway_sequence);v.Num("account_kind",q.account_kind);v.Num("payer_character_id",q.payer_character_id);v.Opt("land_id",q.land_id);v.Num("requested_amount_raw",q.requested_amount_raw);v.Num("entry_balance_bits",q.entry_balance_bits);v.Num("returned_balance_bits",q.returned_balance_bits);v.Bool("returned_balance_matches_requested_sub",q.returned_balance_matches_requested_sub);debits+=v.Done();}debits+=']';o.Raw("qualified_boarding_debits",std::move(debits));
  if(j.raw4.compiled)o.Raw("raw_resource4_getter_v1",Raw4Json(j.raw4));
  return o.Done();
}
std::string AppendWarPaymentJournal12004(std::string json,const WarPaymentJournalSnapshot12004 &j,const WarPaymentEnvelope12004 &e,
    const std::vector<ArmyNaturalPhaseRecord12004> &natural,const ArmyNaturalPhaseJournalStatus12004 &ns) {
  if(json.empty()||json.back()!='}')return json;
  json.pop_back();json+=",\"war_payment_observations_v1\":";json+=SerializeWarPaymentJournal12004(j,e,natural,ns);json+='}';return json;
}
} // namespace xar::ck3_12004

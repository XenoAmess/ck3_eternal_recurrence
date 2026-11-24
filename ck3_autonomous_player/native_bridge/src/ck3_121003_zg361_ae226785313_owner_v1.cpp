#include "xar_bridge/ck3_121003_zg361_ae226785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#ifndef XAR_ZG361_AE2_READ_CURRENT_RAW
#define XAR_ZG361_AE2_READ_CURRENT_RAW ReadZg361Ae2Raw267V1
#endif
#ifndef XAR_ZG361_AE2_READ_FRAME
#define XAR_ZG361_AE2_READ_FRAME ReadZg361Ae2FrameOnOwner267V1
#endif
namespace {
using A=Zg361Ae2Action267V1;using Status=Zg361Ae2Status267V1;
[[maybe_unused]]std::uint64_t Wall(){const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const Zg361Ae2Context267V1&q){const auto wall=Wall();return wall&&wall<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z){
 return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&
  a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&
  a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;
}
[[maybe_unused]]bool World(const Zg361Ae2Frame267V1&a,const Zg361Ae2Frame267V1&z){return a.facts_verified&&z.facts_verified&&Core(a.core,z.core)&&a.game&&a.game==z.game&&a.jomini&&a.jomini==z.jomini&&a.character_storage&&a.character_storage==z.character_storage;}
[[maybe_unused]]bool Frame(const Zg361Ae2Frame267V1&a,const Zg361Ae2Frame267V1&z){
 if(!World(a,z)||a.controls.has_value()!=z.controls.has_value()||a.events.has_value()!=z.events.has_value())return false;
 if(a.controls)return a.controls->facts_verified&&z.controls->facts_verified&&Core(a.controls->core,z.controls->core)&&a.controls->scene==z.controls->scene&&a.controls->witness==z.controls->witness;
 return a.events&&a.events->facts_verified&&z.events->facts_verified&&Core(a.events->core,z.events->core)&&a.events->scene==z.events->scene&&a.events->witness==z.events->witness;
}
// Stable action-owned leaves, evaluated only from complete captured copies.
[[maybe_unused]]const GuiWindowNodeV1* EntryUniqueNode(const std::vector<GuiWindowNodeV1>&v,std::uintptr_t id){
 const GuiWindowNodeV1*out=nullptr;for(const auto&n:v)if(n.widget==id){if(out)return nullptr;out=&n;}return out;
}
[[maybe_unused]]const GuiWindowNodeV1* EntryUniqueNamed(const std::vector<GuiWindowNodeV1>&v,std::string_view name,std::uintptr_t parent,bool restrict_parent){
 const GuiWindowNodeV1*out=nullptr;for(const auto&n:v)if(n.name==name&&(!restrict_parent||n.parent==parent)){if(out)return nullptr;out=&n;}return out;
}
[[maybe_unused]]bool EntryStableNode(const GuiWindowNodeV1&a,const GuiWindowNodeV1&z){
 return a.widget&&a.widget==z.widget&&a.vtable==z.vtable&&a.parent==z.parent&&a.context==z.context&&
  a.name==z.name&&a.flags==z.flags&&a.visible==z.visible&&a.enabled==z.enabled;
}
[[maybe_unused]]bool EntrySceneScalars(const zg361_ae2_control::Zg361Ae2ManageScene267V1&a,const zg361_ae2_control::Zg361Ae2ManageScene267V1&z){
 return a.connection_generation==z.connection_generation&&a.wall_deadline==z.wall_deadline&&
  a.jomini==z.jomini&&a.gfx==z.gfx&&a.handler==z.handler&&a.context==z.context&&a.global==z.global&&
  a.list_root==z.list_root&&a.detail_root==z.detail_root&&a.list_visible==z.list_visible&&
  a.list_enabled==z.list_enabled&&a.detail_visible==z.detail_visible&&a.detail_enabled==z.detail_enabled&&a.owner_bound==z.owner_bound;
}
[[maybe_unused]]bool EntryNavigationProjection(const zg361_ae2_control::Zg361Ae2ManageFrame267V1&a,const zg361_ae2_control::Zg361Ae2ManageFrame267V1&z,std::uintptr_t nav){
 if(!nav||!a.facts_verified||!z.facts_verified||!Core(a.core,z.core)||!EntrySceneScalars(a.scene,z.scene)||
  a.witness.empty()||z.witness.empty()||a.witness.size()>4096||z.witness.size()>4096||
  a.scene.hud.empty()||z.scene.hud.empty()||a.scene.hud.size()>4096||z.scene.hud.size()>4096)return false;
 const auto&b=a.scene;const auto&c=z.scene;
 const auto global_b=EntryUniqueNode(a.witness,b.global),global_a=EntryUniqueNode(z.witness,c.global);
 if(!global_b||!global_a||global_b->parent||global_a->parent||global_b->context!=b.context||global_a->context!=c.context||!EntryStableNode(*global_b,*global_a))return false;
 const GuiWindowNodeV1*layers_b[3]{},*layers_a[3]{};
 constexpr const char*names[]{"windows_layer","middle","hud_layer"};
 for(std::size_t n=0;n<3;++n){layers_b[n]=EntryUniqueNamed(a.witness,names[n],b.global,true);layers_a[n]=EntryUniqueNamed(z.witness,names[n],c.global,true);
  if(!layers_b[n]||!layers_a[n]||layers_b[n]->context!=b.context||layers_a[n]->context!=c.context||!EntryStableNode(*layers_b[n],*layers_a[n]))return false;}
 const std::uintptr_t roots_b[]{b.list_root,b.detail_root},roots_a[]{c.list_root,c.detail_root};
 constexpr const char*root_names[]{"decisions_view","decisiondetail_view"};
 for(std::size_t n=0;n<2;++n){const auto x=EntryUniqueNamed(a.witness,root_names[n],layers_b[n]->widget,true),y=EntryUniqueNamed(z.witness,root_names[n],layers_a[n]->widget,true);
  if(roots_b[n]!=roots_a[n]||bool(x)!=bool(roots_b[n])||bool(y)!=bool(roots_a[n]))return false;
  if(x&&(!y||x->widget!=roots_b[n]||y->widget!=roots_a[n]||x->context!=b.context||y->context!=c.context||!EntryStableNode(*x,*y)))return false;}
 const auto tab_b=EntryUniqueNamed(b.hud,"tab_decisions",0,false),tab_a=EntryUniqueNamed(c.hud,"tab_decisions",0,false);
 if(!tab_b||!tab_a||!EntryStableNode(*tab_b,*tab_a)||nav==tab_b->widget)return false;
 std::unordered_set<std::uintptr_t>seen;bool tab=false;std::uintptr_t current=nav;
 for(std::size_t depth=0;depth<=32;++depth){
  if(!seen.insert(current).second)return false;
  const auto x=EntryUniqueNode(b.hud,current),y=EntryUniqueNode(c.hud,current);
  if(!x||!y||x->context!=b.context||y->context!=c.context||!EntryStableNode(*x,*y))return false;
  const auto wx=EntryUniqueNode(a.witness,current),wy=EntryUniqueNode(z.witness,current);
  if(!wx||!wy||!EntryStableNode(*x,*wx)||!EntryStableNode(*y,*wy))return false;
  tab|=current==tab_b->widget;
  if(current==layers_b[2]->widget)return tab&&x->parent==b.global&&y->parent==c.global;
  if(!x->parent)return false;current=x->parent;
 }return false;
}

[[maybe_unused]]bool CaptureFrame(Zg361Ae2Context267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,Zg361Ae2Frame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||
  q.mailbox->permitted_executor_sextrigintary!=&ExecuteZg361Ae2OnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 std::string why;const bool good=XAR_ZG361_AE2_READ_FRAME(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,out,why);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;
  q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}return Core(q.request.expected,out.core)&&Time(q);
}
}
bool Zg361Ae2NavigationProjection267V1(const zg361_ae2_control::Zg361Ae2ManageFrame267V1&a,
 const zg361_ae2_control::Zg361Ae2ManageFrame267V1&b,std::uintptr_t nav){return EntryNavigationProjection(a,b,nav);}
struct Zg361Ae2Session267V1::State {
 struct Lease{Zg361Ae2Frame267V1 frame;Zg361Ae2Raw267V1 raw;Zg361Ae2Source267V1 published;
  Zg361Ae2Request267V1 request;std::uint64_t query=0,connection=0,mono=0;bool spent=false;};
 std::atomic_bool unknown{false};std::mutex mutex;
 std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0,connection=0;
 std::uint32_t thread=0;std::optional<Zg361Ae2Frame267V1>initial;std::optional<Lease>latest;
 std::array<bool,8>once{};std::array<bool,2>list_once{};
 bool present_sent=false,pay_sent=false,original_instance_absent=false,verify_sent=false;
 std::optional<Zg361Ae2EventIdentity267V1>event;
 std::vector<std::pair<std::string,std::uint64_t>>claims;
};
Zg361Ae2Session267V1::Zg361Ae2Session267V1():state_(std::make_unique<State>()){}
Zg361Ae2Session267V1::~Zg361Ae2Session267V1()=default;
Zg361Ae2Session267V1&RetainedZg361Ae2Session267V1(){static Zg361Ae2Session267V1 state;return state;}
void BlockZg361Ae2Unknown267V1(Zg361Ae2Session267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmZg361Ae2Deadline267V1(Zg361Ae2Context267V1&q)noexcept{
 q.monotonic_deadline_ms=0;const auto wall=Wall();
 if(wall&&q.request.deadline_unix_ms>wall)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-wall,std::uint64_t{8000});
}
bool ExecuteZg361Ae2Inner267V1(Zg361Ae2Context267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;
 q.result.query_sequence=q.request.query_sequence;q.result.reason="zg361_ae2_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 try{
  const auto reject=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;q.result.source_available=false;q.result.source.reset();return true;};
  if(!q.session||!Zg361Ae2RequestShape267V1(q.request))return reject(Status::unavailable,"zg361_ae2_actual_request_or_session_unavailable");
  auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&old:state.claims)if(old.first==q.request.id()){q.result.claim_sequence=old.second;return reject(Status::claim_consumed,"zg361_ae2_original_effect_id_retained");}
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(Status::indeterminate,"zg361_ae2_prior_family_UNKNOWN_no_retry");}
  if(!Time(q))return reject(Status::expired,"zg361_ae2_original_deadline_expired");
  const auto capture=[&](Zg361Ae2Frame267V1&frame,Zg361Ae2Raw267V1&raw){
   if(!CaptureFrame(q,s,frame))return false;std::string why;
   const bool good=XAR_ZG361_AE2_READ_CURRENT_RAW(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw,why);
   q.observation_entered|=raw.entered;q.result.cleanup_known&=raw.cleanup_known;
   if(!good||!q.result.cleanup_known){q.result.reason=why;return false;}
   Zg361Ae2Frame267V1 after;
   if(!CaptureFrame(q,s,after)||!Frame(frame,after)||!Time(q)){q.result.reason="zg361_ae2_actual_frame_changed_after_read";return false;}
   if(state.initial&&(!World(*state.initial,frame)||state.connection!=q.connection_generation||state.thread!=s.thread_id)){
    q.result.reason="zg361_ae2_original_world_actor_receiver_or_thread_changed";return false;}
   return true;
  };
  const auto failed=[&]{
   if(!q.result.cleanup_known){state.unknown.store(true);return reject(Status::indeterminate,"zg361_ae2_owned_read_cleanup_UNKNOWN");}
   const auto why=q.result.reason;return reject(Time(q)?Status::unavailable:Status::expired,why.empty()?"zg361_ae2_complete_source_unavailable":why.c_str());
  };
  const auto phase_admits=[&](A a){
   const auto index=static_cast<unsigned>(a);
   if(!Zg361Ae2Query267V1(a)&&a!=A::open_controls_list&&
    (index>=state.once.size()||state.once[index]))return false;
   if(a==A::open_controls_list){const auto phase=state.pay_sent&&state.original_instance_absent?1U:0U;
    return !state.verify_sent&&!state.list_once[phase]&&(phase==1||!state.present_sent);}
   if(a==A::open_present_detail)return !state.present_sent&&!state.once[static_cast<unsigned>(a)];
   if(a==A::confirm_present)return !state.present_sent&&state.once[static_cast<unsigned>(A::open_present_detail)];
   if(a==A::choose_pay_now)return state.present_sent&&!state.pay_sent&&state.event.has_value();
   if(a==A::open_verify_detail)return state.pay_sent&&state.original_instance_absent&&!state.verify_sent&&!state.once[static_cast<unsigned>(a)];
   if(a==A::confirm_verify)return state.pay_sent&&state.original_instance_absent&&!state.verify_sent&&state.once[static_cast<unsigned>(A::open_verify_detail)];
   return Zg361Ae2Query267V1(a);
  };
  const auto publish=[&](const Zg361Ae2Raw267V1&raw){
   auto source=raw.source;
   if(source.controls){auto&c=*source.controls;c.open_list_admissible&=phase_admits(A::open_controls_list);
    for(auto&r:c.rows){const bool present=r.control==Zg361Ae2Control267V1::present;
     r.open_detail_admissible&=phase_admits(present?A::open_present_detail:A::open_verify_detail);
     r.confirm_admissible&=phase_admits(present?A::confirm_present:A::confirm_verify);}}
   if(source.events&&source.events->ae2){auto&a=*source.events->ae2;
    const bool same=state.event&&state.event->instance_id==a.instance_id&&state.event->recipient_character_id==a.recipient_character_id&&state.event->definition_key==a.definition_key;
    a.pay_now_admissible&=phase_admits(A::choose_pay_now)&&same;}
   return source;
  };
  if(Zg361Ae2Query267V1(q.request.action)){
   state.latest.reset();Zg361Ae2Frame267V1 frame;Zg361Ae2Raw267V1 raw;
   if(!capture(frame,raw))return failed();
   if(state.query>=32)return reject(Status::claim_consumed,"zg361_ae2_finite_query_capacity");
   if(!state.initial){state.initial=frame;state.connection=q.connection_generation;state.thread=s.thread_id;}
   if(raw.source.events&&raw.source.events->census_complete){
    const auto&e=*raw.source.events;
    if(state.present_sent&&!state.pay_sent&&e.ae2){const auto&a=*e.ae2;
     const Zg361Ae2EventIdentity267V1 actual{a.instance_id,a.recipient_character_id,a.definition_key};
     if(state.event&&*state.event!=actual)return reject(Status::stale_source,"zg361_ae2_original_present_instance_replaced");
     state.event=actual;
    }
    if(state.pay_sent&&state.event){bool id_still_present=false;
     for(const auto&row:e.census)if(row.instance_id==state.event->instance_id)id_still_present=true;
     // A reused instance with another definition/recipient is not absence.
     state.original_instance_absent=!id_still_present;
    }
   }
   auto source=publish(raw);const auto query=++state.query;
   state.latest=Zg361Ae2Session267V1::State::Lease{frame,raw,source,q.request,query,q.connection_generation,q.monotonic_deadline_ms,false};
   q.result.source=std::move(source);q.result.source_available=true;q.result.status=Status::available;
   q.result.provider_generation=state.generation;q.result.query_sequence=query;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(Status::stale_source,"zg361_ae2_original_private_query_missing");auto&lease=*state.latest;
  q.result.provider_generation=state.generation;q.result.query_sequence=lease.query;
  const auto action=static_cast<unsigned>(q.request.action);
  if(action>=state.once.size()||lease.spent||q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||
   q.connection_generation!=lease.connection||q.request.id()==lease.request.id()||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||
   !Core(q.request.expected,lease.request.expected)||Zg361Ae2KindFor267V1(q.request.action)!=Zg361Ae2KindFor267V1(lease.request.action)||
   (q.request.action!=A::open_controls_list&&state.once[action])||!phase_admits(q.request.action))
   return reject(Status::stale_source,"zg361_ae2_original_source_body_receiver_phase_or_once_mismatch");
  if(GetTickCount64()>=lease.mono)return reject(Status::expired,"zg361_ae2_original_query_deadline_expired");
  q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  Zg361Ae2Frame267V1 frame;Zg361Ae2Raw267V1 actual;
  if(!capture(frame,actual))return failed();
  if(!SameZg361Ae2LeaseFrame267V1(q.request.action,lease.frame,lease.raw,frame,actual)||!SameZg361Ae2Raw267V1(actual,lease.raw)||
   !Zg361Ae2PublicAdmissible267V1(publish(actual),q.request.action))
   return reject(Status::stale_source,"zg361_ae2_complete_action_source_changed_or_refused");
  if(state.claims.size()>=16||state.claim==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::claim_consumed,"zg361_ae2_finite_claim_capacity");
  const auto claim=++state.claim;state.claims.emplace_back(std::string(q.request.id()),claim);lease.spent=true;
  if(q.request.action==A::open_controls_list)state.list_once[state.pay_sent&&state.original_instance_absent?1U:0U]=true;
  else state.once[action]=true;
  q.result.claim_sequence=claim;
  const auto call=CallZg361Ae2Raw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,actual);
  q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known){state.unknown.store(true);return reject(Status::indeterminate,"zg361_ae2_native_completion_UNKNOWN_claim_retained");}
  if(!call.entered||!call.native_returned)return reject(Status::stale_source,"zg361_ae2_preeffect_refused_original_claim_retained");
  if(q.request.action==A::confirm_present)state.present_sent=true;
  if(q.request.action==A::choose_pay_now){state.pay_sent=true;state.original_instance_absent=false;}
  if(q.request.action==A::confirm_verify)state.verify_sent=true;
  q.result.source=lease.published;q.result.source_available=true;
  q.result.status=q.request.action==A::choose_pay_now?Status::selection_dispatched:
   q.request.action==A::confirm_present||q.request.action==A::confirm_verify?Status::confirmation_dispatched:Status::navigation_dispatched;
  q.result.reason.clear();return true;
 }catch(...){if(q.session)BlockZg361Ae2Unknown267V1(*q.session);q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();
  q.result.status=Status::indeterminate;q.result.reason="zg361_ae2_owner_local_UNKNOWN";}
#endif
 return true;
}
bool ExecuteZg361Ae2OnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 if(!p)return false;auto&q=*static_cast<Zg361Ae2Context267V1*>(p);
 __try{return ExecuteZg361Ae2Inner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockZg361Ae2Unknown267V1(*q.session);
  q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.status=Status::indeterminate;
  q.result.reason="zg361_ae2_original_native_exception_UNKNOWN";return true;}
}
}

#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <stdexcept>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const DjcUiContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const DjcUiFrame267V1&a,const DjcUiFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool Frame(DjcUiContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,DjcUiFrame267V1&frame){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_undenary!=&ExecuteDjcUiOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;
 const bool good=ReadDjcUiFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,frame,reason);
 if(frame.facts_verified){q.result.facts_available=true;q.result.facts=frame.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(frame.core,q.request.expected)){q.result.reason="djc_ui_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(DjcUiContext267V1&q,const DjcUiFrame267V1&frame,bool initial_query,DjcUiRawObservation267V1&raw){
 const auto b=BindDjcUiImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified){q.result.reason="djc_ui_actual_image_unavailable";return false;}
 q.native_observation_entered=true;std::string reason;
 const bool good=initial_query?ReadDjcUiRaw267V1(q.bindings,b,q.request.expected,q.request.target_character_id,q.request.cb,frame.scene,q.monotonic_deadline_ms,raw,reason):ReadDjcUiRawForClaim267V1(q.bindings,b,q.request.expected,q.request.target_character_id,q.request.cb,frame.scene,q.monotonic_deadline_ms,raw,reason);
 q.result.cleanup_known=raw.cleanup_known;if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return Time(q);
}
[[maybe_unused]]bool PendingIdentity(const DjcUiFrame267V1&a,const DjcUiRawObservation267V1&x,const DjcUiFrame267V1&b,const DjcUiRawObservation267V1&y)noexcept{
 // Native Send itself refreshes/applies the special payload and can hide its source view.
 // Match exact persistent receiver/roles/full selection, then independently validate the
 // newly owned modal's copied context. Never replay pre-Send raw context bytes.
 return SameCore(a.core,b.core)&&a.scene.jomini==b.scene.jomini&&a.scene.gfx==b.scene.gfx&&a.scene.handler==b.scene.handler&&a.scene.gui_context==b.scene.gui_context&&a.scene.global_root==b.scene.global_root&&a.scene.middle==b.scene.middle&&a.scene.view_root==b.scene.view_root&&x.view==y.view&&x.outer==y.outer&&x.definition==y.definition&&x.actor==y.actor&&x.target==y.target&&x.additional==y.additional&&x.source.actor_id==y.source.actor_id&&x.source.recipient_id==y.source.recipient_id&&x.source.additional_role_id==y.source.additional_role_id&&x.selected&&y.selected&&x.selected->definition==y.selected->definition&&x.selected->tuple==y.selected->tuple;
}
}
struct DjcUiSession267V1::State{
 struct Lease{DjcUiFrame267V1 frame;DjcUiRawObservation267V1 raw;DjcUiRequest267V1 request;std::uint64_t sequence=0,connection=0,mono=0;bool consumed=false;std::vector<std::pair<std::uint64_t,std::uintptr_t>>tokens;};
 struct Claim{DjcUiAction267V1 action;std::uint64_t sequence=0,lease=0,deadline=0;std::string id;};
 struct SendKey{std::int32_t actor=-1,target=-1;DjcUiTuple267V1 tuple;friend bool operator==(const SendKey&,const SendKey&)=default;};
 struct Pending{Lease origin;std::uint64_t send_claim=0,final_claim=0;bool final_returned=false;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0,token_sequence=(GetTickCount64()^0x9E3779B97F4A7C15ULL);
 std::optional<Lease>latest,warning;std::optional<Pending>pending;std::vector<Claim>claims;std::vector<SendKey>sent;
};
DjcUiSession267V1::DjcUiSession267V1():state_(std::make_unique<State>()){}
DjcUiSession267V1::~DjcUiSession267V1()=default;
void BlockDjcUiUnknown267V1(DjcUiSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmDjcUiDeadline267V1(DjcUiContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteDjcUiInner267V1(DjcUiContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.selected_cost_values={};q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="current_djc_ui_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
 try{using A=DjcUiAction267V1;using S=DjcUiStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};
   if(q.selected_cost_query){
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1
    if(!q.session||!DjcSelectedCostRequestShape267V1(q.request))return reject(S::unavailable,"djc_cost_request_or_process_session_unavailable");
    auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
    if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;q.selected_cost_values.cleanup_known=false;return reject(S::indeterminate,"djc_cost_prior_unknown_blocks_observation");}
    if(!Time(q))return reject(S::expired,"djc_cost_original_deadline_expired");
    for(const auto&claim:state.claims)if(claim.id==q.request.id())return reject(S::claim_consumed,"djc_cost_original_effect_id_cannot_be_reused_for_read");
    if(state.pending&&!state.pending->final_returned)return reject(S::claim_consumed,"djc_cost_pending_send_only_allows_original_warning_path");
    if(!state.latest)return reject(S::stale_source,"djc_cost_original_private_ui_query_absent");
    const auto&lease=*state.latest;
    if(lease.consumed)return reject(S::claim_consumed,"djc_cost_original_private_ui_query_consumed");
    if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||q.request.target_character_id!=lease.request.target_character_id||q.request.cb!=lease.request.cb||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"djc_cost_original_private_ui_query_identity_mismatch");
    if(GetTickCount64()>=lease.mono)return reject(S::expired,"djc_cost_original_private_query_deadline_expired");
    q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
    DjcUiFrame267V1 frame;if(!Frame(q,s,frame))return true;
    if(!SameFrame(lease.frame,frame))return reject(S::stale_source,"djc_cost_original_private_owner_frame_changed");
    DjcUiRawObservation267V1 raw;
    if(!Observe(q,frame,false,raw)){if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}return true;}
    if(!SameDjcUiRaw267V1(lease.raw,raw))return reject(S::stale_source,"djc_cost_original_private_full_native_source_changed");
    const auto binding=BindDjcUiImage267V1(q.bindings.module_base,kExecutableSha256);std::string reason;
    const bool good=ReadDjcSelectedCostRaw267V1(q.bindings,binding,q.request.expected,q.request.target_character_id,q.request.cb,frame.scene,q.monotonic_deadline_ms,raw,q.selected_cost_values,reason);
    q.result.cleanup_known=q.result.cleanup_known&&q.selected_cost_values.cleanup_known;
    if(!good){if(!q.result.cleanup_known){state.unknown.store(true);return reject(S::indeterminate,reason.empty()?"djc_cost_native_cleanup_unknown":reason.c_str());}return reject(Time(q)?S::unavailable:S::expired,reason.empty()?"djc_cost_native_values_unavailable":reason.c_str());}
    const auto before=frame;
    if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame))return reject(S::stale_source,"djc_cost_post_getter_owner_or_private_source_changed");
    if(!Time(q))return reject(S::expired,"djc_cost_original_post_observation_deadline_expired");
    if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;q.selected_cost_values.cleanup_known=false;return reject(S::indeterminate,"djc_cost_concurrent_prior_unknown");}
    q.result.source_available=true;q.result.source=raw.source;q.result.provider_generation=state.generation;q.result.query_sequence=lease.sequence;q.result.status=S::available;q.result.reason.clear();return true;
#else
    return reject(S::unavailable,"current_djc_selected_cost_default_off");
#endif
   }

  if(!q.session||!DjcUiRequestShape267V1(q.request))return reject(S::unavailable,"djc_ui_request_or_process_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"djc_ui_original_effect_id_retained_no_replay");}
  if(!Time(q))return reject(S::expired,"djc_ui_original_deadline_expired");
  DjcUiFrame267V1 frame;if(!Frame(q,s,frame))return true;
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"djc_ui_prior_unknown_blocks_native_observation_and_effect");}
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"djc_ui_retained_capacity_exhausted");
  const auto source_failure=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  const auto lease_request=[&](const DjcUiSession267V1::State::Lease&lease){return q.request.provider_generation==state.generation&&q.request.query_sequence==lease.sequence&&q.connection_generation==lease.connection&&q.request.deadline_unix_ms==lease.request.deadline_unix_ms&&q.request.target_character_id==lease.request.target_character_id&&q.request.cb==lease.request.cb&&SameCore(q.request.expected,lease.request.expected)&&q.request.id()!=lease.request.id();};
  const auto make_lease=[&](DjcUiRawObservation267V1 raw){DjcUiSession267V1::State::Lease lease;lease.frame=frame;lease.raw=std::move(raw);lease.request=q.request;lease.sequence=++state.query_sequence;lease.connection=q.connection_generation;lease.mono=q.monotonic_deadline_ms;
   q.result.source=lease.raw.source;for(std::size_t i=0;i<lease.raw.choices.size();++i){if(state.token_sequence==(std::numeric_limits<std::uint64_t>::max)())throw std::overflow_error("DJC token exhausted");const auto token=++state.token_sequence;lease.tokens.push_back({token,lease.raw.choices[i].row});q.result.source->choices[i].choice_token=token;}
   q.result.provider_generation=state.generation;q.result.query_sequence=lease.sequence;return lease;};
  if(q.request.action==A::query_ui){
   state.latest.reset();const auto source_frame=frame;DjcUiRawObservation267V1 raw;if(!Observe(q,frame,true,raw))return source_failure();
   if(!Frame(q,s,frame)||!SameFrame(source_frame,frame))return reject(S::stale_source,"djc_ui_post_observation_core_or_scene_changed");
   state.latest=make_lease(std::move(raw));q.result.source->accept_admissible=false;
   if(state.pending&&!state.pending->final_returned){q.result.source->open_admissible=false;q.result.source->send_admissible=false;}
   q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(q.request.action==A::query_warning){
   if(!state.pending||state.pending->send_claim!=q.request.origin_claim_sequence||!lease_request(state.pending->origin)||state.pending->final_claim)return reject(S::stale_source,"djc_ui_original_private_pending_send_mismatch");
   auto&pending=*state.pending;if(GetTickCount64()>=pending.origin.mono)return reject(S::expired,"djc_ui_original_send_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,pending.origin.mono);
   DjcUiRawObservation267V1 raw;if(!Observe(q,frame,false,raw))return source_failure();
   if(!PendingIdentity(pending.origin.frame,pending.origin.raw,frame,raw))return reject(S::stale_source,"djc_ui_actual_pending_window_roles_or_selected_tuple_changed");
   if(!raw.source.warning_source_available&&!raw.no_active_dialog)return reject(S::unavailable,"djc_ui_active_dialog_is_not_exact_pending_war_warning");
   state.warning=make_lease(raw);
   q.result.source->open_admissible=false;q.result.source->send_admissible=false;
   if(!raw.source.warning_source_available)return reject(S::warning_pending,"djc_ui_original_send_valid_warning_not_materialized");
   q.result.status=S::warning_ready;q.result.reason.clear();return true;
  }
  auto*lease=q.request.action==A::accept_warning?(state.warning?&*state.warning:nullptr):(state.latest?&*state.latest:nullptr);
  if(!lease||!lease_request(*lease))return reject(S::stale_source,"djc_ui_original_private_query_lease_mismatch");
  if(lease->consumed)return reject(S::claim_consumed,"djc_ui_private_query_action_already_claimed");
  if(GetTickCount64()>=lease->mono)return reject(S::expired,"djc_ui_original_query_monotonic_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease->mono);
  if(q.request.action==A::accept_warning){if(!state.pending||q.request.origin_claim_sequence!=state.pending->send_claim||state.pending->final_claim)return reject(S::claim_consumed,"djc_ui_original_send_or_warning_claim_retained");}
  else if(state.pending&&!state.pending->final_returned)return reject(S::claim_consumed,"djc_ui_prior_send_may_only_query_or_accept_its_original_warning");
  DjcUiRawObservation267V1 raw;if(!Observe(q,frame,false,raw))return source_failure();
  if(!SameFrame(lease->frame,frame)||!SameDjcUiRaw267V1(lease->raw,raw))return reject(S::stale_source,"djc_ui_actual_frame_or_full_native_material_changed");
  // Echo only tokens genuinely minted for this private query, never raw row positions.
  q.result.source->choices.clear();for(const auto&token:lease->tokens){const auto it=std::find_if(raw.choices.begin(),raw.choices.end(),[&](const auto&item){return item.row==token.second;});if(it==raw.choices.end())return reject(S::stale_source,"djc_ui_actual_token_row_disappeared");q.result.source->choices.push_back({token.first,it->tuple});}
  std::uintptr_t row=0;DjcUiSession267V1::State::SendKey send;
  if(q.request.action==A::open_ui){if(!raw.source.open_admissible)return reject(S::unavailable,"djc_ui_fixed_native_confirmation_interface_or_validity_refused");}
  else if(q.request.action==A::select_choice){const auto it=std::find_if(lease->tokens.begin(),lease->tokens.end(),[&](const auto&t){return t.first==q.request.choice_token;});if(it==lease->tokens.end())return reject(S::stale_source,"djc_ui_choice_not_minted_by_original_query");row=it->second;const auto native=std::find_if(raw.choices.begin(),raw.choices.end(),[&](const auto&v){return v.row==row;});if(native==raw.choices.end()||!native->tuple.source_row_enabled||!raw.source.named_root_bound||!raw.source.window_visible||!raw.source.window_enabled||!raw.no_active_dialog)return reject(S::unavailable,"djc_ui_actual_native_choice_not_enabled");}
  else if(q.request.action==A::send_ui){if(!raw.source.send_admissible||!raw.selected)return reject(S::unavailable,"djc_ui_actual_selected_or_native_can_send_refused");send={q.request.expected.played_character_id,q.request.target_character_id,raw.selected->tuple};if(std::find(state.sent.begin(),state.sent.end(),send)!=state.sent.end())return reject(S::claim_consumed,"djc_ui_same_actual_war_tuple_send_retained_no_replay");}
  else if(q.request.action==A::accept_warning){if(!raw.source.accept_admissible||!state.pending||!PendingIdentity(state.pending->origin.frame,state.pending->origin.raw,frame,raw))return reject(S::unavailable,"djc_ui_actual_pending_modal_can_refused");}
  else return reject(S::unavailable,"djc_ui_fixed_action_unavailable");
  if(!Time(q))return reject(S::expired,"djc_ui_original_preclaim_deadline_expired");
  const auto sequence=state.claim_sequence+1;state.claims.push_back({q.request.action,sequence,lease->sequence,q.request.deadline_unix_ms,std::string(q.request.id())});state.claim_sequence=sequence;lease->consumed=true;q.result.claim_sequence=sequence;
  if(q.request.action==A::send_ui)state.sent.push_back(send);
  if(q.request.action==A::accept_warning)state.pending->final_claim=sequence;
  const auto bindings=BindDjcUiImage267V1(q.bindings.module_base,kExecutableSha256);const auto call=CallDjcUiRaw267V1(q.request.action,q.bindings,bindings,q.request.expected,q.request.target_character_id,q.request.cb,frame.scene,q.monotonic_deadline_ms,raw,row);
  q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==DjcUiRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==DjcUiRawCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"djc_ui_native_effect_or_resource_cleanup_unknown_no_replay");}
  if(call.status!=DjcUiRawCallStatus267V1::returned)return reject(S::stale_source,"djc_ui_pre_effect_refusal_claim_retained");
  q.result.reason.clear();
  if(q.request.action==A::open_ui)q.result.status=S::open_dispatched;
  else if(q.request.action==A::select_choice)q.result.status=S::selection_dispatched;
  else if(q.request.action==A::send_ui){state.pending=DjcUiSession267V1::State::Pending{*lease,sequence,0,false};state.warning.reset();q.result.status=S::send_dispatched;}
  else{state.pending->final_returned=true;q.result.status=S::warning_dispatched;}
  return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockDjcUiUnknown267V1(*q.session);q.result.status=(q.native_observation_entered||q.result.effect_attempted)?DjcUiStatus267V1::indeterminate:DjcUiStatus267V1::unavailable;q.result.reason="djc_ui_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteDjcUiOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<DjcUiContext267V1*>(p);__try{return ExecuteDjcUiInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockDjcUiUnknown267V1(*q.session);q.result.status=DjcUiStatus267V1::indeterminate;if(q.selected_cost_query){q.selected_cost_values.cleanup_known=false;q.result.cleanup_known=false;}return true;}}
} // namespace

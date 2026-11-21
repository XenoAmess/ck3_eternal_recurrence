#include "xar_bridge/ck3_121003_succession_lifecycle26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <optional>
#include <vector>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const SuccessionContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameWorld(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameWindow(GuiWindowV1 a,GuiWindowV1 b){a.ticket_sequence=b.ticket_sequence=0;a.pump_epoch=b.pump_epoch=0;return a==b;}
[[maybe_unused]]bool SameFrame(const SuccessionLifecycleFrame267V1&a,const SuccessionLifecycleFrame267V1&b){return a.world_verified&&b.world_verified&&SameWorld(a.world,b.world)&&SameWindow(a.window,b.window)&&a.game_state==b.game_state&&a.jomini==b.jomini&&a.storage==b.storage&&a.game_data==b.game_data&&a.player_entries==b.player_entries&&a.player_count==b.player_count&&a.gfx==b.gfx&&a.handler==b.handler&&a.default_button_index==b.default_button_index;}
[[maybe_unused]]bool Capture(SuccessionContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,
 SuccessionLifecycleFrame267V1&frame,SuccessionRawSample267V1&raw,SuccessionSource267V1&source){
 if(!Time(q)||!q.connection_generation||!q.mailbox||q.mailbox->offline_fixture||q.mailbox->permitted_executor_denary!=&ExecuteSuccessionLifecycleOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 std::string reason;const bool read=ReadSuccessionLifecycleFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.connection_generation,q.request.deadline_unix_ms,q.monotonic_deadline_ms,frame,reason);
 if(frame.world_verified){q.result.world_available=true;q.result.world=frame.world;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!read){q.result.reason=reason;return false;}
 if(!frame.world.clock.paused||frame.default_button_index>=frame.window.tree.size()||frame.window.tree.empty()){q.result.reason="succession_actual_paused_default_button_unavailable";return false;}
 const auto b=BindSuccessionContinueImage267V1(q.bindings.module_base,kExecutableSha256);const SuccessionExpectedWindow267V1 e{frame.jomini,frame.gfx,frame.handler,frame.window.tree[0].widget,frame.window.context};
 if(!b.verified||!ReadSuccessionContinueRaw267V1(q.bindings,b,e,raw,reason)){q.result.reason=reason;return false;}
 source.dead_character_id=raw.dead_character_id;source.continue_character_id=raw.continue_character_id;
 const auto&w=frame.world;
 if(w.has_played_character&&w.played_character_id==raw.dead_character_id&&!w.played_character_alive)source.player_relation=SuccessionPlayerRelation267V1::pending_predecessor;
 else if(w.has_played_character&&w.played_character_id==raw.continue_character_id&&w.played_character_alive)source.player_relation=SuccessionPlayerRelation267V1::heir_already_assigned;
 else if(!w.has_played_character&&w.played_character_id==-1&&!w.played_character_alive)source.player_relation=SuccessionPlayerRelation267V1::unassigned_during_transition;
 else{q.result.reason="succession_actual_player_not_native_predecessor_or_continue_role";return false;}
 source.dead_character_dead=source.continue_character_alive=source.handler_source_verified=source.named_root_bound=source.window_visible=source.window_enabled=source.default_button_admissible=source.default_native_route=source.stable_two_pass_verified=true;
 q.result.source=source;q.result.source_available=true;return Time(q);
}
}
struct SuccessionSession267V1::State {
 struct Lease {SuccessionLifecycleFrame267V1 frame;SuccessionRawSample267V1 raw;SuccessionSource267V1 source;std::uint64_t sequence=0,connection=0,wall=0,mono=0;std::string query_id;};
 struct Claim {std::int32_t dead=-1,heir=-1;std::uint64_t sequence=0,wall=0;std::string id;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;
 std::optional<Lease>latest;std::vector<Claim>claims;
};
SuccessionSession267V1::SuccessionSession267V1():state_(std::make_unique<State>()){}
SuccessionSession267V1::~SuccessionSession267V1()=default;
void BlockSuccessionUnknown267V1(SuccessionSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmSuccessionDeadline267V1(SuccessionContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteSuccessionLifecycleInner267V1(SuccessionContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="current_succession_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
 try{
  using Status=SuccessionStatus267V1;const auto reject=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;return true;};
  if(!q.session||!SuccessionRequestShape267V1(q.request))return reject(Status::unavailable,"succession_request_or_process_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  if(state.unknown.load(std::memory_order_acquire))return reject(Status::indeterminate,"succession_prior_unknown_no_replay");
  if(!Time(q))return reject(Status::expired,"succession_original_deadline_expired");
  if(q.request.action==SuccessionAction267V1::query_default){
   state.latest.reset();SuccessionLifecycleFrame267V1 f;SuccessionRawSample267V1 raw;SuccessionSource267V1 source;
   if(!Capture(q,s,f,raw,source))return true;
   for(const auto&claim:state.claims)if(claim.dead==source.dead_character_id){q.result.claim_sequence=claim.sequence;return reject(Status::claim_consumed,"succession_predecessor_claim_already_retained");}
   if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)()||state.claims.size()>=64)return reject(Status::claim_consumed,"succession_retained_capacity_exhausted");
   typename SuccessionSession267V1::State::Lease lease;lease.frame=std::move(f);lease.raw=raw;lease.source=source;lease.sequence=++state.query_sequence;lease.connection=q.connection_generation;lease.wall=q.request.deadline_unix_ms;lease.mono=q.monotonic_deadline_ms;lease.query_id=q.request.id();state.latest=std::move(lease);
   q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=Status::available;q.result.reason.clear();return true;
  }
  if(!state.latest||q.request.provider_generation!=state.generation||q.request.query_sequence!=state.latest->sequence||q.connection_generation!=state.latest->connection||q.request.deadline_unix_ms!=state.latest->wall||q.request.id()==state.latest->query_id||q.request.expected_dead_character_id!=state.latest->source.dead_character_id||q.request.expected_continue_character_id!=state.latest->source.continue_character_id)return reject(Status::stale_source,"succession_original_private_query_lease_mismatch");
  const auto&lease=*state.latest;for(const auto&claim:state.claims)if(claim.dead==lease.source.dead_character_id){q.result.claim_sequence=claim.sequence;return reject(Status::claim_consumed,"succession_original_claim_no_replay");}
  if(GetTickCount64()>=lease.mono)return reject(Status::expired,"succession_original_query_monotonic_deadline_expired");
  q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  SuccessionLifecycleFrame267V1 fresh;SuccessionRawSample267V1 raw;SuccessionSource267V1 source;
  if(!Capture(q,s,fresh,raw,source))return true;
  if(!SameFrame(lease.frame,fresh)||lease.raw!=raw)return reject(Status::stale_source,"succession_native_world_window_or_material_changed");
  if(!Time(q))return reject(Status::expired,"succession_original_preclaim_deadline_expired");
  const auto b=BindSuccessionContinueImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified)return reject(Status::stale_source,"succession_image_changed_before_claim");
  const auto sequence=state.claim_sequence+1;state.claims.push_back({source.dead_character_id,source.continue_character_id,sequence,q.request.deadline_unix_ms,std::string(q.request.id())});state.claim_sequence=sequence;q.result.claim_sequence=sequence;
  const SuccessionExpectedWindow267V1 e{fresh.jomini,fresh.gfx,fresh.handler,fresh.window.tree[0].widget,fresh.window.context};
  const auto call=CallSuccessionContinueRaw267V1(q.bindings,b,e,raw);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==SuccessionRawCallStatus267V1::returned;
  if(call.status==SuccessionRawCallStatus267V1::returned){q.result.status=Status::dispatched;q.result.reason.clear();return true;}
  if(call.effect_entered){state.unknown.store(true);return reject(Status::indeterminate,"succession_native_close_unknown_no_replay");}
  return reject(Status::stale_source,"succession_preclose_refusal_claim_retained");
 }catch(...){if(q.session&&q.result.effect_attempted)BlockSuccessionUnknown267V1(*q.session);q.result.status=q.result.effect_attempted?SuccessionStatus267V1::indeterminate:SuccessionStatus267V1::unavailable;q.result.reason="succession_owner_exception_claim_retained";}
#endif
 return true;
}
bool ExecuteSuccessionLifecycleOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<SuccessionContext267V1*>(p);__try{return ExecuteSuccessionLifecycleInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockSuccessionUnknown267V1(*q.session);q.result.status=SuccessionStatus267V1::indeterminate;return true;}}
}

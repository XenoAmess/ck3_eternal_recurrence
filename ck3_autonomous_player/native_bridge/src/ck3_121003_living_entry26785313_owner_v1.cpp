#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_gui_identity26785313_private_v1.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
using A=LivingEntryAction267V1;using Status=LivingEntryStatus267V1;
[[maybe_unused]]std::uint64_t Wall(){const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const LivingEntryContext267V1&q){const auto wall=Wall();return wall&&wall<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z){
 return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&
  a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&
  a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;
}
[[maybe_unused]]bool World(const LivingInventoryFrame267V1&a,const LivingInventoryFrame267V1&z){
 return a.facts_verified&&z.facts_verified&&Core(a.core,z.core)&&a.game==z.game&&a.jomini==z.jomini&&
  a.actor==z.actor&&a.character_storage==z.character_storage&&a.data==z.data&&a.players==z.players&&
  a.player==z.player&&a.connection_generation==z.connection_generation;
}
[[maybe_unused]]bool Frame(const LivingEntryFrame267V1&a,const LivingEntryFrame267V1&z){
 if(!World(a.inventory,z.inventory)||a.manage.has_value()!=z.manage.has_value()||a.view.has_value()!=z.view.has_value())return false;
 if(a.manage&&(!a.manage->facts_verified||!z.manage->facts_verified||!Core(a.manage->core,z.manage->core)||
  a.manage->scene!=z.manage->scene||a.manage->witness!=z.manage->witness))return false;
 if(a.view){const auto&x=*a.view;const auto&y=*z.view;
  if(!x.owner_observed||!y.owner_observed||x.gfx!=y.gfx||x.manager!=y.manager||
   !SameLivingGuiIdentity267V1(x.gui,y.gui))return false;
 }

 return true;
}
[[maybe_unused]]bool CaptureFrame(LivingEntryContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LivingEntryFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||
  q.mailbox->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 std::string why;const bool good=ReadLivingEntryFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,
  &q.invocation,q.request,q.monotonic_deadline_ms,out,why);
 if(out.inventory.facts_verified){q.result.facts_available=true;q.result.facts=out.inventory.core;
  q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;
  q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}
 return World(out.inventory,out.inventory)&&Core(q.request.expected,out.inventory.core)&&
  out.inventory.connection_generation==q.connection_generation&&Time(q);
}
}
struct LivingEntrySession267V1::State {
 struct Lease {LivingEntryFrame267V1 frame;LivingEntryRaw267V1 raw;LivingEntryRequest267V1 request;
  std::uint64_t sequence=0,connection=0,mono=0;bool spent=false;};
 std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0;
 std::optional<Lease>latest;std::optional<LivingInventoryFrame267V1>initial;
 std::uint32_t target=0xFFFFFFFFU;std::array<bool,8>once{};
 std::vector<std::pair<std::string,std::uint64_t>>claims;
};
LivingEntrySession267V1::LivingEntrySession267V1():state_(std::make_unique<State>()){}
LivingEntrySession267V1::~LivingEntrySession267V1()=default;
LivingEntrySession267V1&RetainedLivingEntrySession267V1(){static LivingEntrySession267V1 state;return state;}
void ArmLivingEntryDeadline267V1(LivingEntryContext267V1&q)noexcept{
 q.monotonic_deadline_ms=0;const auto wall=Wall();
 if(wall&&q.request.deadline_unix_ms>wall)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-wall,std::uint64_t{8000});
}
bool ExecuteLivingEntryInner267V1(LivingEntryContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.reason="living_entry_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
 try{
  const auto reject=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;q.result.source_available=false;q.result.source.reset();return true;};
  if(!q.session||!LivingEntryRequestShape267V1(q.request))return reject(Status::unavailable,"living_entry_actual_request_or_session_unavailable");
  auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&old:state.claims)if(old.first==q.request.id()){q.result.claim_sequence=old.second;return reject(Status::rejected,"living_entry_original_effect_id_retained");}
  if(LivingFamilyUnknown267V1()){q.result.cleanup_known=false;return reject(Status::indeterminate,"living_entry_prior_family_UNKNOWN");}
  if(!Time(q))return reject(Status::expired,"living_entry_original_deadline_expired");
  const auto capture=[&](LivingEntryFrame267V1&frame,LivingEntryRaw267V1&raw){
   if(!CaptureFrame(q,s,frame))return false;std::string why;
   const bool good=ReadLivingEntryRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw,why);
   q.observation_entered|=raw.entered;q.result.cleanup_known&=raw.cleanup_known;
   if(!good){q.result.reason=why;return false;}
   LivingEntryFrame267V1 after;
   if(!CaptureFrame(q,s,after)||!Frame(frame,after)||!Time(q))return false;
   const auto&r=raw.inventory.fixed_references[0];
   if(r.state!=LivingReferenceState267V1::artifact||!r.full_id)return false;
   if(state.initial&&(!World(*state.initial,frame.inventory)||state.target!=*r.full_id))return false;
   return true;
  };
  const auto failed=[&]{
   if(!q.result.cleanup_known){BlockLivingFamilyUnknown267V1();return reject(Status::indeterminate,"living_entry_owned_read_cleanup_UNKNOWN");}
   const auto why=q.result.reason;
   return reject(Time(q)?Status::unavailable:Status::expired,why.empty()?"living_entry_complete_source_unavailable":why.c_str());
  };
  if(LivingEntryQuery267V1(q.request.action)){
   state.latest.reset();LivingEntryFrame267V1 frame;LivingEntryRaw267V1 raw;
   if(!capture(frame,raw))return failed();
   if(state.query==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::unavailable,"living_entry_query_sequence_exhausted");
   if(!state.initial){state.initial=frame.inventory;state.target=*raw.inventory.fixed_references[0].full_id;}
   state.latest=LivingEntrySession267V1::State::Lease{frame,raw,q.request,++state.query,q.connection_generation,q.monotonic_deadline_ms,false};
   q.result.source=raw.source;q.result.source_available=true;q.result.status=Status::available;
   q.result.provider_generation=state.generation;q.result.query_sequence=state.query;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(Status::stale_source,"living_entry_private_query_missing");auto&lease=*state.latest;
  q.result.provider_generation=state.generation;q.result.query_sequence=lease.sequence;
  const auto action=static_cast<std::size_t>(q.request.action);
  if(action>=state.once.size()||state.once[action]||lease.spent||q.request.provider_generation!=state.generation||
   q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.id()==lease.request.id()||
   q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!Core(q.request.expected,lease.request.expected)||
   LivingEntryKindFor267V1(q.request.action)!=LivingEntryKindFor267V1(lease.request.action))
   return reject(Status::stale_source,"living_entry_original_owner_Core_body_or_once_mismatch");
  if(GetTickCount64()>=lease.mono)return reject(Status::expired,"living_entry_original_query_deadline_expired");
  q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LivingEntryFrame267V1 frame;LivingEntryRaw267V1 actual;
  if(!capture(frame,actual))return failed();
  if(!Frame(frame,lease.frame)||!SameLivingEntryRaw267V1(actual,lease.raw))return reject(Status::stale_source,"living_entry_complete_physical_source_changed");
  if(state.claims.size()>=16||state.claim==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::rejected,"living_entry_finite_claim_capacity");
  const auto claim=++state.claim;state.claims.emplace_back(std::string(q.request.id()),claim);
  lease.spent=true;state.once[action]=true;q.result.claim_sequence=claim;
  const auto call=CallLivingEntryRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,actual);
  q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known){BlockLivingFamilyUnknown267V1();return reject(Status::indeterminate,"living_entry_native_completion_UNKNOWN_claim_retained");}
  if(!call.entered||!call.native_returned)return reject(Status::stale_source,"living_entry_preeffect_refused_claim_retained");
  q.result.source=lease.raw.source;q.result.source_available=true;q.result.status=Status::dispatched;q.result.reason.clear();return true;
 }catch(...){BlockLivingFamilyUnknown267V1();q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();
  q.result.status=Status::indeterminate;q.result.reason="living_entry_owner_local_UNKNOWN";}
#endif
 return true;
}
bool ExecuteLivingEntryOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 if(!p)return false;auto&q=*static_cast<LivingEntryContext267V1*>(p);
 __try{return ExecuteLivingEntryInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){BlockLivingFamilyUnknown267V1();
  q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.status=Status::indeterminate;
  q.result.reason="living_entry_original_native_exception_UNKNOWN";return true;}
}
}

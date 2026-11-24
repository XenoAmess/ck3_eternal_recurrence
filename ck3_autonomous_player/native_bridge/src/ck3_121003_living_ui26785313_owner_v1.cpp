#include "xar_bridge/ck3_121003_living_ui26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_finite_case26785313_private_v1.hpp"
#include "xar_bridge/ck3_121003_living_gui_identity26785313_private_v1.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
using A=LivingUiAction267V1;using S=LivingUiStatus267V1;
std::uint64_t Wall(){const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const LivingUiContext267V1&q){return Wall()&&Wall()<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b){return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool InventoryFrame(const LivingInventoryFrame267V1&a,const LivingInventoryFrame267V1&b){return a.facts_verified&&b.facts_verified&&Core(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.actor==b.actor&&a.data==b.data&&a.character_storage==b.character_storage&&a.players==b.players&&a.player==b.player&&a.connection_generation==b.connection_generation;}
[[maybe_unused]]bool Frame(const LivingUiFrame267V1&a,const LivingUiFrame267V1&b){
 if(!InventoryFrame(a.inventory,b.inventory)||a.weapon.has_value()!=b.weapon.has_value()||a.events.has_value()!=b.events.has_value()||a.detail.has_value()!=b.detail.has_value())return false;
 const auto gui=[](const LivingWeaponFrame267V1&x,const LivingWeaponFrame267V1&y){return x.owner_observed&&y.owner_observed&&x.gfx==y.gfx&&x.manager==y.manager&&SameLivingGuiIdentity267V1(x.gui,y.gui);};
 if(a.weapon&&!gui(*a.weapon,*b.weapon))return false;
 if(a.detail&&!gui(*a.detail,*b.detail))return false;
 return !a.events||(a.events->facts_verified&&b.events->facts_verified&&Core(a.events->core,b.events->core)&&a.events->scene==b.events->scene&&a.events->witness==b.events->witness&&a.events->name_witness==b.events->name_witness);
}
[[maybe_unused]]bool CaptureFrame(LivingUiContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LivingUiFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||
    q.mailbox->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
 std::string why;const bool good=ReadLivingUiFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q.invocation,q.request,q.monotonic_deadline_ms,out,why);
 if(out.inventory.facts_verified){q.result.facts_available=true;q.result.facts=out.inventory.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}return Core(q.request.expected,out.inventory.core)&&out.inventory.connection_generation==q.connection_generation&&Time(q);
}
}
struct LivingUiSession267V1::State {
 struct Lease {LivingUiFrame267V1 frame;LivingUiRaw267V1 raw;LivingUiRequest267V1 request;std::uint64_t sequence=0,connection=0,mono=0;bool spent=false;};
 std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0;
 std::optional<Lease>latest;std::vector<std::pair<std::string,std::uint64_t>>claims;
 living_inventory_private::LivingFiniteCase267V1 finite;
 LivingWeaponPrivateSession267V1 weapon;
};
LivingUiSession267V1::LivingUiSession267V1():state_(std::make_unique<State>()){}
LivingUiSession267V1::~LivingUiSession267V1()=default;
LivingUiSession267V1&RetainedLivingUiSession267V1(){static LivingUiSession267V1 session;return session;}
void ArmLivingUiDeadline267V1(LivingUiContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto wall=Wall();if(wall&&q.request.deadline_unix_ms>wall)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-wall,std::uint64_t{8000});}
bool ExecuteLivingUiInner267V1(LivingUiContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 q.result={};q.result.action=q.request.action;q.result.reason="living_UI_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 try{
  const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;q.result.source_available=false;q.result.source.reset();return true;};
  if(!q.session||!LivingUiRequestShape267V1(q.request))return reject(S::unavailable,"living_UI_actual_request_or_session_unavailable");
  auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&old:state.claims)if(old.first==q.request.id()){q.result.claim_sequence=old.second;return reject(S::rejected,"living_UI_original_effect_id_retained");}
  if(LivingFamilyUnknown267V1()){q.result.cleanup_known=false;return reject(S::indeterminate,"living_UI_prior_family_UNKNOWN");}
  if(!Time(q))return reject(S::expired,"living_UI_original_deadline_expired");
  const auto capture=[&](LivingUiFrame267V1&frame,LivingUiRaw267V1&raw,living_inventory_private::LivingFiniteCase267V1&finite){
   if(!CaptureFrame(q,s,frame))return false;std::string why;
   const bool good=ReadLivingUiRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,finite,raw,why);
   q.observation_entered|=raw.entered;q.result.cleanup_known&=raw.cleanup_known;
   if(!good){q.result.reason=why;return false;}
   LivingUiFrame267V1 after;return CaptureFrame(q,s,after)&&Frame(frame,after)&&Time(q);
  };
  const auto failed=[&]{if(!q.result.cleanup_known){BlockLivingFamilyUnknown267V1();return reject(S::indeterminate,"living_UI_owned_read_cleanup_UNKNOWN");}const auto why=q.result.reason;return reject(Time(q)?S::unavailable:S::expired,why.empty()?"living_UI_complete_source_unavailable":why.c_str());};
  if(LivingUiQuery267V1(q.request.action)){
   state.latest.reset();LivingUiFrame267V1 frame;LivingUiRaw267V1 raw;auto finite=state.finite;
   if(!capture(frame,raw,finite))return failed();
   if(state.query==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"living_UI_query_sequence_exhausted");
   state.finite=std::move(finite);state.latest=LivingUiSession267V1::State::Lease{frame,raw,q.request,++state.query,q.connection_generation,q.monotonic_deadline_ms,false};
   q.result.source=raw.source;q.result.source_available=true;q.result.status=S::available;q.result.provider_generation=state.generation;q.result.query_sequence=state.query;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"living_UI_original_private_query_missing");auto&lease=*state.latest;
  q.result.provider_generation=state.generation;q.result.query_sequence=lease.sequence;
  if(lease.spent||q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.id()==lease.request.id()||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!Core(q.request.expected,lease.request.expected)||LivingUiKindFor267V1(q.request.action)!=LivingUiKindFor267V1(lease.request.action))return reject(S::stale_source,"living_UI_original_connection_Core_body_or_lease_mismatch");
  if(GetTickCount64()>=lease.mono)return reject(S::expired,"living_UI_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LivingUiFrame267V1 frame;LivingUiRaw267V1 actual;auto finite=state.finite;
  if(!capture(frame,actual,finite))return failed();
  if(!Frame(frame,lease.frame)||!SameLivingUiRaw267V1(actual,lease.raw))return reject(S::stale_source,"living_UI_complete_physical_draft_changed");
  if(state.claims.size()>=32||state.claim==(std::numeric_limits<std::uint64_t>::max)())return reject(S::rejected,"living_UI_finite_claim_capacity");
  const auto claim=++state.claim;state.claims.emplace_back(std::string(q.request.id()),claim);lease.spent=true;q.result.claim_sequence=claim;
  // The Raw layer independently re-acquires, checks fixed-instance/phase or
  // weapon guard, and retains its own once marker BEFORE the official callback.
  const auto call=CallLivingUiRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,actual,state.finite,state.weapon);
  q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known){BlockLivingFamilyUnknown267V1();living_inventory_private::LivingFiniteUnknown267V1(state.finite);return reject(S::indeterminate,"living_UI_native_completion_UNKNOWN_claim_retained");}
  if(!call.entered||!call.native_returned)return reject(S::stale_source,"living_UI_preeffect_refused_claim_retained");
  q.result.source=lease.raw.source;q.result.source_available=true;q.result.status=S::dispatched;q.result.reason.clear();return true;
 }catch(...){BlockLivingFamilyUnknown267V1();q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.status=S::indeterminate;q.result.reason="living_UI_owner_local_UNKNOWN";}
#endif
 return true;
}
bool ExecuteLivingUiOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 if(!p)return false;auto&q=*static_cast<LivingUiContext267V1*>(p);
 __try{return ExecuteLivingUiInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){BlockLivingFamilyUnknown267V1();q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.status=S::indeterminate;q.result.reason="living_UI_original_native_exception_UNKNOWN";return true;}
}
}

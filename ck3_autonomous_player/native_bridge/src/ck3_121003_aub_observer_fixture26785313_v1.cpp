#include "xar_bridge/ck3_121003_aub_observer_fixture26785313_v1.hpp"
#include "xar_bridge/ck3_121003_aub_private_console26785313_v1.hpp"
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
#include "xar_bridge/ck3_121003_aub_observer_fixture_body26785313_v1.hpp"
#endif
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <limits>
#include <vector>
#include <windows.h>
#include <shellapi.h>
namespace xar::ck3_121003::build26785313 { namespace {
using Status=AubObserverFixtureStatus267V1;
bool Copy(const void*p,void*out,std::size_t n) noexcept {if(!p||!out||!n)return false;__try{std::memcpy(out,p,n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(reinterpret_cast<const void*>(p+off),&v,sizeof(v));}
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const AubObserverFixtureContext267V1&q)noexcept{const auto t=Wall();return t&&q.monotonic_deadline_ms&&t<q.request.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Equal(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
struct Resource {
 ck3_12002::ConsoleFixtureRandomScope scope{};ck3_12002::ConsoleFixtureNativeString command{};
 void*prior_wrapper=nullptr;std::uint32_t prior_owner_tid=0;
 bool enter_attempted=false,enter_completed=false,wrapper_installed=false;
 bool string_attempted=false,string_release_attempted=false,string_released=false;
 bool scope_release_attempted=false,scope_released=false,console_entered=false;
};
[[maybe_unused]]bool Enter(const ck3_12002::ConsoleFixtureBindings&b,Resource&r,const ck3_12002::ConsoleFixtureSourceLocation&where)noexcept{r.enter_attempted=true;__try{r.enter_completed=b.enter_random_scope(&r.scope,nullptr,&where)==&r.scope;return r.enter_completed;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Assign(const ck3_12002::ConsoleFixtureBindings&b,Resource&r)noexcept{r.string_attempted=true;__try{return b.assign_string(&r.command,ck3_12002::kPrivateFixtureInboxCommand,21)==&r.command;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Execute(const ck3_12002::ConsoleFixtureBindings&b,Resource&r,void*console,bool&accepted)noexcept{r.console_entered=true;__try{accepted=b.execute(console,&r.command);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool ReleaseString(const ck3_12002::ConsoleFixtureBindings&b,Resource&r)noexcept{
 if(!r.string_attempted)return true;if(r.string_release_attempted)return r.string_released;r.string_release_attempted=true;
 __try{b.destroy_string(&r.command);r.string_released=r.command.size==0&&r.command.capacity==15&&r.command.storage[0]==0;return r.string_released;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool ReleaseScope(const ck3_12002::ConsoleFixtureBindings&b,Resource&r,std::uintptr_t base)noexcept{
 if(!r.enter_attempted)return true;if(r.scope_release_attempted)return r.scope_released;
 if(!r.enter_completed||r.scope.owner_state!=reinterpret_cast<void*>(base+0x5D55998)||r.scope.owns_owner>1)return false;
 r.scope_release_attempted=true;
 __try{b.exit_random_scope(&r.scope);void*current=nullptr;std::uint32_t owner=0;
  r.scope_released=Copy(b.random_wrapper_slot,&current,8)&&current==r.prior_wrapper&&At(base,0x5D559A8,owner)&&owner==r.prior_owner_tid;
  return r.scope_released;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Cleanup(const ck3_12002::ConsoleFixtureBindings&b,Resource&r,std::uintptr_t base)noexcept{
 const bool text=ReleaseString(b,r);const bool scope=ReleaseScope(b,r,base);return text&&scope;
}
#include "ck3_121003_aub_observer_fixture26785313_file.inc"
[[maybe_unused]]bool Core(AubObserverFixtureContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s){
 if(!Time(q)||!q.connection_generation||!q.session||!q.mailbox||q.mailbox->offline_fixture||q.mailbox->permitted_executor_septenary!=&ExecuteAubObserverFixtureOnOwner267V1)return false;
 ReadonlyObservation actual;if(!ReadAubObserverFixtureCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,actual)||!actual.available||actual.offline_fixture||!actual.main_owner_observed||!Equal(actual.core,q.request.expected))return false;
 q.result.observed=actual.core;q.result.core_available=true;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;return true;
}
}
struct AubObserverFixtureSession267V1::State {std::atomic_bool unknown{false};bool claimed=false;Resource resource;ck3_12002::ConsoleFixtureBindings bound{};std::uintptr_t base=0;};
AubObserverFixtureSession267V1::AubObserverFixtureSession267V1():state_(std::make_unique<State>()){}
AubObserverFixtureSession267V1::~AubObserverFixtureSession267V1(){if(state_&&(state_->unknown.load()||(state_->resource.wrapper_installed&&!state_->resource.scope_released)))(void)state_.release();}
void BlockAubObserverFixtureUnknown267V1(AubObserverFixtureSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmAubObserverFixtureDeadline267V1(AubObserverFixtureContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteAubObserverFixtureInner267V1(AubObserverFixtureContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.reason="current_fixed_fixture_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
 try{
  const auto refuse=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;return true;};
  if(!q.session||!AubObserverFixtureRequestShape267V1(q.request))return refuse(Status::unavailable,"fixed_fixture_profile_or_request_unavailable");auto&state=*q.session->state_;
  if(state.unknown.load(std::memory_order_acquire))return refuse(Status::indeterminate,"fixed_fixture_prior_unknown_no_replay");if(state.claimed){q.result.claim_sequence=1;return refuse(Status::claim_consumed,"fixed_fixture_original_claim_retained");}
  if(!Time(q))return refuse(Status::expired,"fixed_fixture_original_deadline_expired");
  q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);const auto base=q.bindings.module_base;
  const auto bound=BindAubPrivateInboxFixture267V1(base,kExecutableSha256);std::uintptr_t console=0;
  InputWitness before,again;
  if(!Core(q,s)||!ReadBoundAubPrivateInboxConsole267V1(q.bindings,bound,console)||!ReadFixedInput(before)||!ReadFixedInput(again)||before!=again)return refuse(Status::unavailable,"fixed_fixture_exact_owner_console_or_body_unavailable");
  q.result.file_verified=true;q.result.inbox_sha256=kAubObserverFixtureBodySha256267V1;
  std::uint32_t owner=0;if(!At(base,0x5D559A8,owner)||(owner&&owner!=s.thread_id))return refuse(Status::unavailable,"fixed_fixture_rng_owned_by_other_thread");
  if(!Core(q,s)||!Time(q))return refuse(Status::source_changed,"fixed_fixture_preclaim_core_changed");state.claimed=true;q.result.claim_sequence=1;
  state.bound=bound;state.base=base;auto&r=state.resource;r.prior_owner_tid=owner;if(!Copy(bound.random_wrapper_slot,&r.prior_wrapper,8)){state.unknown.store(true);return refuse(Status::indeterminate,"fixed_fixture_wrapper_read_unknown");}
  const ck3_12002::ConsoleFixtureSourceLocation where{__LINE__,0,"ck3_121003_aub_observer_fixture26785313_v1.cpp","fixed_aub_observer",0};
  q.resource_ownership_entered=true;
  if(!Enter(bound,r,where)||r.scope.owner_state!=reinterpret_cast<void*>(base+0x5D55998)||r.scope.owns_owner>1){state.unknown.store(true);return refuse(Status::indeterminate,"fixed_fixture_rng_enter_unknown_retained");}
  r.scope.previous_slot_target=bound.random_wrapper_slot;r.scope.previous_value=std::atomic_ref<void*>(*bound.random_wrapper_slot).exchange(&r.scope,std::memory_order_seq_cst);r.scope.restore_slot=1;r.wrapper_installed=true;
  if(r.scope.previous_value!=r.prior_wrapper){const bool cleaned=Cleanup(bound,r,base);q.result.cleanup_known=cleaned;state.unknown.store(true);return refuse(Status::indeterminate,"fixed_fixture_wrapper_source_changed");}
  bool accepted=false;bool returned=false;
  if(Assign(bound,r)&&Core(q,s)&&ReadFixedInput(again)&&again==before&&Time(q)){
   std::uintptr_t fresh_console=0;if(ReadBoundAubPrivateInboxConsole267V1(q.bindings,bound,fresh_console)&&fresh_console==console){q.result.effect_attempted=true;returned=Execute(bound,r,reinterpret_cast<void*>(console),accepted);}
  }
  q.result.native_returned=returned;q.result.native_accepted=accepted;q.result.cleanup_known=Cleanup(bound,r,base);
  q.result.file_verified_after=ReadFixedInput(again)&&again==before;
  if(q.result.effect_attempted){
   if(returned&&accepted&&q.result.cleanup_known&&q.result.file_verified_after&&VerifyAubPrivateInboxImage267V1(base)){q.result.status=Status::dispatched;q.result.reason.clear();return true;}
   state.unknown.store(true);return refuse(Status::indeterminate,"fixed_fixture_native_or_cleanup_unknown_no_replay");
  }
  if(!q.result.cleanup_known){state.unknown.store(true);return refuse(Status::indeterminate,"fixed_fixture_cleanup_unknown_before_console");}
  return refuse(Status::source_changed,"fixed_fixture_preconsole_source_changed_claim_retained");
 }catch(...){bool uncertain=q.resource_ownership_entered||q.result.effect_attempted;
  if(q.session&&uncertain){auto&state=*q.session->state_;q.result.cleanup_known=Cleanup(state.bound,state.resource,state.base);BlockAubObserverFixtureUnknown267V1(*q.session);}
  q.result.status=uncertain?Status::indeterminate:Status::unavailable;q.result.reason="fixed_fixture_exception_source_or_resource_retained";}
#else
 (void)s;
#endif
 return true;
}
bool ExecuteAubObserverFixtureOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<AubObserverFixtureContext267V1*>(p);__try{return ExecuteAubObserverFixtureInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){
 if(q.session){auto&state=*q.session->state_;
  if(q.resource_ownership_entered&&q.result.thread_id&&GetCurrentThreadId()==q.result.thread_id)
   q.result.cleanup_known=Cleanup(state.bound,state.resource,state.base);
  BlockAubObserverFixtureUnknown267V1(*q.session);}
 q.result.status=Status::indeterminate;return true;}}
}

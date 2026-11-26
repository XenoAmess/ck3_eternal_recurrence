#include "xar_bridge/ck3_1210_opening_frame56.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include <intrin.h>
#include <windows.h>
namespace xar::ck3_1210 {namespace {
bool SameCoreBindings(const CoreBindings&a,const CoreBindings&b) noexcept {
 return a.enabled && b.enabled && a.image_build==b.image_build && a.game_state_slot==b.game_state_slot &&
 a.jomini_state_slot==b.jomini_state_slot && a.character_storage_slot==b.character_storage_slot && a.get_local_player==b.get_local_player;
}
bool Cap(const game::GameAdapter *a,ImageBuildV1 build,OpeningReadKind56 k) noexcept {
 const auto *profile=FindOpeningReadWireProfile56(build,k);
 return a && profile && a->enabled() && game::Ck3_1210BasicBuild(a->descriptor())==build &&
 a->supports(profile->capability) && a->supports_snapshot() && a->supports("game.query.fresh-full-state.v1");
}
bool Targets(const PersonalGoldMailboxContextV1&p,const OpeningMailboxContext56&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 const auto &m=*p.mailbox;
#if defined(XAR_CK3_OPENING56_OFFLINE_FIXTURE)
 if(m.offline_fixture)return true;
#else
 if(m.offline_fixture)return false;
#endif
 const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
 const auto exact=BindOpeningReadImage56(base,p.game->descriptor().executable_sha256);const auto &b=q.bindings;
 const bool current=exact.core.image_build==ImageBuildV1::full11126785313;
 const auto tls_flag=current?ck3_121003::build26785313::kTlsFlagRva:hotfix26757580::kTlsFlag;
 const auto tls_getter=current?ck3_121003::build26785313::kTlsGetterRva:hotfix26757580::kTlsGetter;
 if(q.read_access.copy || q.read_access.context || !base || p.image_base!=base || m.module_base!=base || !exact.exact_build_admitted ||
 !SameCoreBindings(b.core,exact.core) || !SameCoreBindings(p.bindings.core,exact.core) ||
 b.government!=exact.government || b.identifier_name!=exact.identifier_name || b.focus!=exact.focus ||
 b.lifestyle!=exact.lifestyle || b.xp!=exact.xp || b.points!=exact.points || b.used!=exact.used ||
 b.government_fallback_slot!=exact.government_fallback_slot || b.identifier_manager_slot!=exact.identifier_manager_slot ||
 b.focus_fallback_slot!=exact.focus_fallback_slot || b.identifier_missing_string!=exact.identifier_missing_string ||
 b.government_vtable!=exact.government_vtable || b.focus_vtable!=exact.focus_vtable || b.lifestyle_vtable!=exact.lifestyle_vtable ||
 m.game_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.game_state_slot) ||
 m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.jomini_state_slot) ||
 m.tls_initialized_flag!=base+tls_flag || s.tls_initialized_flag_address!=m.tls_initialized_flag ||
 reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+tls_getter)return false;
 // Read only the already-warm embedded TLS context; never invoke its lazy getter.
 if(*reinterpret_cast<const std::uint8_t*>(m.tls_initialized_flag)!=1)return false;
 const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));if(!slots || !slots[0])return false;
 const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
 return (*reinterpret_cast<const std::uint32_t*>(block+0x3620)&1U)!=0 && block+0x3628==s.tls_context &&
 *reinterpret_cast<const std::uint8_t*>(s.tls_context+0x20)==1;
}
bool OwnerInner(const PersonalGoldMailboxContextV1&p,const OpeningMailboxContext56&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 const auto build=q.bindings.core.image_build;
 if(p.kind!=ActorObservationKindV1::opening_readonly56 || p.opening56!=&q || !Cap(p.game,build,q.kind) ||
 !Cap(q.native_full_adapter,build,q.kind) ||
 !p.mailbox || !p.ticket.sequence || !p.bindings.exact_build_admitted || !q.bindings.exact_build_admitted ||
 !SameCoreBindings(p.bindings.core,q.bindings.core) || q.bindings.integration_native_calls_permitted ||
 q.bindings.native_call_admission || q.bindings.native_call_admission_context || q.expected_native_revision==0 || !q.current_published_revision)return false;
 const auto &m=*p.mailbox;
 if(!s.thread_id || s.thread_id!=GetCurrentThreadId() || !s.pump_epoch || s.tls_initialized!=1 || s.tls_main_thread_marker!=1 ||
 !s.tls_context || !s.paused || !s.game_state || !s.jomini_state || !m.iat_hook_installed.load() || !m.active_hook_calls.load() ||
 m.owner_thread_id.load()!=s.thread_id || m.pump_epochs.load()!=s.pump_epoch || m.failure_flags.load()!=0 ||
 m.stop_requested.load() || m.proof_reset_requested.load() ||
 m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
 m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing || m.published_sequence.load()!=p.ticket.sequence ||
 m.executor_started_sequence.load()!=p.ticket.sequence || m.executor_started_pump_epoch.load()!=s.pump_epoch ||
 m.executor_context!=&p || m.executor.load()!=&ExecutePersonalGoldMailboxV1 || !Targets(p,q,s))return false;
 return q.bindings.core.game_state_slot && q.bindings.core.jomini_state_slot &&
 reinterpret_cast<std::uintptr_t>(*q.bindings.core.game_state_slot)==s.game_state &&
 reinterpret_cast<std::uintptr_t>(*q.bindings.core.jomini_state_slot)==s.jomini_state &&
 *q.current_published_revision==q.expected_native_revision;
}
bool Owner(const PersonalGoldMailboxContextV1&p,const OpeningMailboxContext56&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
#if defined(_MSC_VER)
 __try {
#endif
 return OwnerInner(p,q,s);
#if defined(_MSC_VER)
 } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
CoreSnapshotPrefix Prefix(const game::Snapshot&s) noexcept {
 CoreSnapshotPrefix p{};p.clock={s.date_raw,s.speed,s.paused};p.local_player_id=s.player_id;p.map_ready=s.map_ready;
 p.has_played_character=s.has_played_character;p.played_character_id=s.played_character_id;p.played_character_alive=s.played_character_alive;return p;
}
struct Scope {
 PersonalGoldMailboxContextV1 &parent;OpeningMailboxContext56 &q;
 ck3_11906::MainThreadExecutionStampV1 stamp;
 const game::GameAdapter *parent_adapter,*raw_adapter;
 const std::uint64_t *revision_source;const ck3_11906::MainThreadQueryMailboxV1 *mailbox;
 std::uint64_t revision,ticket;CoreBindings core;
 OpeningReadKind56 kind;OpeningReadBindings56 bindings;OpeningReadAccess56 read_access;
 bool Sources() const noexcept {
  return parent.game==parent_adapter && parent.mailbox==mailbox && parent.opening56==&q && parent.ticket.sequence==ticket &&
  q.native_full_adapter==raw_adapter && q.current_published_revision==revision_source && q.expected_native_revision==revision &&
  SameCoreBindings(parent.bindings.core,core) && SameCoreBindings(q.bindings.core,core) && q.kind==kind &&
  q.bindings.government==bindings.government && q.bindings.identifier_name==bindings.identifier_name &&
  q.bindings.focus==bindings.focus && q.bindings.lifestyle==bindings.lifestyle && q.bindings.xp==bindings.xp &&
  q.bindings.points==bindings.points && q.bindings.used==bindings.used &&
  q.bindings.government_fallback_slot==bindings.government_fallback_slot && q.bindings.identifier_manager_slot==bindings.identifier_manager_slot &&
  q.bindings.focus_fallback_slot==bindings.focus_fallback_slot && q.bindings.identifier_missing_string==bindings.identifier_missing_string &&
  q.bindings.government_vtable==bindings.government_vtable && q.bindings.focus_vtable==bindings.focus_vtable &&
  q.bindings.lifestyle_vtable==bindings.lifestyle_vtable && q.read_access.copy==read_access.copy && q.read_access.context==read_access.context;
 }
};
bool Admission(void *context) noexcept {
 const auto &scope=*static_cast<const Scope*>(context);
 return scope.Sources() && Owner(scope.parent,scope.q,scope.stamp);
}
bool FullCall(const game::GameAdapter&a,game::Snapshot&s) noexcept {
#if defined(_MSC_VER)
 __try {
#endif
 return a.read_snapshot(s);
#if defined(_MSC_VER)
 } __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
void Clear(OpeningMailboxContext56&q,std::string_view reason) noexcept {
 const auto calls=q.observation.native_call_attempts;q.observation={};q.observation.kind=q.kind;
 q.observation.native_call_attempts=calls;q.observation.unavailable_reason=reason;q.completed=false;
}
}
bool ExecuteOpeningOnActorOwner56(PersonalGoldMailboxContextV1&p,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 p.application_main_observed=false;if(!p.opening56)return true;auto &q=*p.opening56;
 q.observation={};q.observation.kind=q.kind;q.completed=false;q.application_main_observed=false;q.offline_fixture=false;
 q.ticket_sequence=q.pump_epoch=0;q.thread_id=0;q.current_full_attempts=0;
 try {
  if(!Owner(p,q,s)){Clear(q,"opening_actor_owner_unqualified");return true;}
  const game::Snapshot basis=q.expected_full;
  if(!basis.paused || !basis.map_ready || !basis.has_played_character || !basis.played_character_alive ||
  basis.played_character_id==-1 || basis.date_raw!=s.date_raw){Clear(q,"opening_full_basis_unavailable");return true;}
  q.offline_fixture=p.mailbox->offline_fixture;q.application_main_observed=!q.offline_fixture;p.application_main_observed=q.application_main_observed;
  q.ticket_sequence=p.ticket.sequence;q.pump_epoch=s.pump_epoch;q.thread_id=s.thread_id;
  Scope scope{p,q,s,p.game,q.native_full_adapter,q.current_published_revision,p.mailbox,q.expected_native_revision,p.ticket.sequence,p.bindings.core,q.kind,q.bindings,q.read_access};
  game::Snapshot before{},after{};
  ++q.current_full_attempts;
  if(!Admission(&scope) || !FullCall(*scope.raw_adapter,before) || !Admission(&scope) || before!=basis || q.expected_full!=basis){Clear(q,"opening_current_full_before_changed");return true;}
  auto local=q.bindings;local.integration_native_calls_permitted=true;local.native_call_admission=&Admission;local.native_call_admission_context=&scope;
  const bool read=ReadOpeningReadonly56(local,Prefix(basis),q.kind,q.observation,q.read_access);
  ++q.current_full_attempts;
  if(!Admission(&scope) || !FullCall(*scope.raw_adapter,after) || !Admission(&scope) || after!=basis || q.expected_full!=basis){Clear(q,"opening_current_full_after_changed");return true;}
  if(!read)return true;
  q.completed=true;return true;
 }catch(...){Clear(q,"opening_actor_cpp_exception");return true;}
}
}

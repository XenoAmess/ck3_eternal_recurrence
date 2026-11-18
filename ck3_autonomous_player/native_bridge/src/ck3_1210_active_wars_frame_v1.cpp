#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <windows.h>
namespace xar::ck3_1210 {
namespace {
bool SameCoreBindings(const CoreBindings &a,const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot==b.game_state_slot &&
      a.jomini_state_slot==b.jomini_state_slot && a.character_storage_slot==b.character_storage_slot &&
      a.get_local_player==b.get_local_player;
}
void Clear(ActiveWarsMailboxContextV1 &q,std::string_view reason) noexcept {
  const auto calls=q.observation.native_score_calls_attempted;
  q.observation={};q.observation.native_score_calls_attempted=calls;
  q.observation.unavailable_reason=reason;q.application_main_observed=false;
}
bool Targets(const PersonalGoldMailboxContextV1 &p,const ActiveWarsMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  const auto &m=*p.mailbox;
  if(m.offline_fixture)return true; // Explicit NoGame RAM, never mapped-image proof.
  if(q.fixture_access.context || q.fixture_access.copy)return false;
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  const auto exact=BindActiveWarsImageV1(base,kExecutableSha256);
  if(!base || !exact.exact_build_admitted || m.module_base!=base ||
      m.tls_initialized_flag!=base+0x695910C ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+0x44FEA30 ||
      !SameCoreBindings(q.bindings.core,exact.core) ||
      q.bindings.war_registry_slot!=exact.war_registry_slot ||
      q.bindings.war_registry_vtable!=exact.war_registry_vtable ||
      q.bindings.war_manager_vtable!=exact.war_manager_vtable ||
      q.bindings.war_vtable!=exact.war_vtable ||
      q.bindings.get_attacker_war_score!=exact.get_attacker_war_score)return false;
  return *reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)==1 &&
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter())==s.tls_context &&
      *reinterpret_cast<const std::uint8_t *>(s.tls_context+0x20)==1;
}
bool Owner(const PersonalGoldMailboxContextV1 &p,const ActiveWarsMailboxContextV1 &q,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(p.kind!=ActorObservationKindV1::active_wars || p.wars!=&q || !p.game ||
      !p.game->enabled() || !game::IsCk3_1210Descriptor(p.game->descriptor()) ||
      !p.game->supports(kActiveWarsIdentityCapabilityV1) || !p.mailbox ||
      p.ticket.sequence==0 || !p.bindings.exact_build_admitted || !q.bindings.exact_build_admitted ||
      !SameCoreBindings(p.bindings.core,q.bindings.core))return false;
  const auto &m=*p.mailbox;const auto &b=q.bindings.core;
  if(s.thread_id==0 || s.thread_id!=GetCurrentThreadId() || s.pump_epoch==0 ||
      s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || s.tls_context==0 ||
      !s.paused || s.game_state==0 || s.jomini_state==0 ||
      !m.iat_hook_installed.load() || m.owner_thread_id.load()!=s.thread_id ||
      m.failure_flags.load()!=0 || m.stop_requested.load() ||
      m.paused_owner_verified_pump_epochs.load()<
          ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      m.published_sequence.load()!=p.ticket.sequence ||
      m.executor_started_sequence.load()!=p.ticket.sequence ||
      m.executor_started_pump_epoch.load()!=s.pump_epoch ||
      m.executor_context!=&p || m.executor.load()!=&ExecutePersonalGoldMailboxV1 ||
      !b.game_state_slot || !b.jomini_state_slot ||
      reinterpret_cast<std::uintptr_t>(*b.game_state_slot)!=s.game_state ||
      reinterpret_cast<std::uintptr_t>(*b.jomini_state_slot)!=s.jomini_state)return false;
  return Targets(p,q,s);
}
struct Admission { PersonalGoldMailboxContextV1 *parent; ActiveWarsMailboxContextV1 *query; const ck3_11906::MainThreadExecutionStampV1 *stamp; };
bool Admit(void *opaque) noexcept {
  const auto &a=*static_cast<Admission *>(opaque);return Owner(*a.parent,*a.query,*a.stamp);
}
bool Read(PersonalGoldMailboxContextV1 &p,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  p.observation={};p.foundation={};p.application_main_observed=false;
  if(!p.wars)return true;
  auto &q=*p.wars;q.observation={};q.application_main_observed=false;
  if(!Owner(p,q,s)){Clear(q,"active_wars_actor_owner_unqualified");return true;}
  CoreSnapshotPrefix expected{};
  if(!ReadCoreSnapshot(q.bindings.core,expected) || expected.clock.date_raw!=s.date_raw ||
      expected.clock.paused!=s.paused){Clear(q,"active_wars_actor_core_changed");return true;}
  Admission admission{&p,&q,&s};
  auto local=q.bindings;local.native_call_admission=&Admit;local.native_call_admission_context=&admission;
  local.integration_native_calls_permitted=true; // Only this actual owner-local copy.
  (void)ReadActiveWarsV1(local,expected,q.observation,q.fixture_access);
  if(!Owner(p,q,s)){Clear(q,"active_wars_actor_owner_changed");return true;}
  q.application_main_observed=p.application_main_observed=true;
  return true;
}
void Fault(PersonalGoldMailboxContextV1 &p) noexcept {
  if(p.wars)Clear(*p.wars,"active_wars_actor_memory_read_failed");
  p.application_main_observed=false;
}
}
bool ExecuteActiveWarsOnActorOwnerV1(PersonalGoldMailboxContextV1 &p,
    const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
#if defined(_MSC_VER)
  __try {return Read(p,s);}
  __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER) {
    Fault(p);return true;
  }
#else
  return Read(p,s);
#endif
}
}

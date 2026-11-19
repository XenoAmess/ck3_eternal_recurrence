#include "xar_bridge/ck3_1210_active_wars_frame_v1.hpp"
#include "xar_bridge/ck3_1210_military_production58.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_nonempty_military_hotfix26757580_v1.hpp"
#include <intrin.h>
#include <windows.h>
#include <cstring>
namespace xar::ck3_1210 {namespace {
bool SameCoreBinding58(const CoreBindings&a,const CoreBindings&b) noexcept {
 return a.enabled && b.enabled && a.image_build==b.image_build && a.game_state_slot==b.game_state_slot &&
 a.jomini_state_slot==b.jomini_state_slot && a.character_storage_slot==b.character_storage_slot && a.get_local_player==b.get_local_player;
}
bool SameWarsBinding58(const ActiveWarsBindingsV1&a,const ActiveWarsBindingsV1&b) noexcept {
 return a.exact_build_admitted && b.exact_build_admitted && SameCoreBinding58(a.core,b.core) &&
 a.war_registry_slot==b.war_registry_slot && a.war_registry_vtable==b.war_registry_vtable &&
 a.war_manager_vtable==b.war_manager_vtable && a.war_vtable==b.war_vtable && a.get_attacker_war_score==b.get_attacker_war_score;
}
bool SamePrefix58(const CoreSnapshotPrefix&a,const CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed && a.clock.paused==b.clock.paused &&
 a.local_player_id==b.local_player_id && a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
 a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
bool Targets58(const PersonalGoldMailboxContextV1&p,const ActiveWarsMailboxContextV1&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 const auto &m=*p.mailbox;
#if defined(XAR_CK3_MILITARY58_OFFLINE_FIXTURE)
 if(m.offline_fixture)return true;
#else
 if(m.offline_fixture)return false;
#endif
 if(q.fixture_access.context || q.fixture_access.copy)return false;
 const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
 const auto exact=BindActiveWarsImageV1(base,hotfix26757580::kExecutableSha256);
 if(!base || p.image_base!=base || m.module_base!=base || !SameWarsBinding58(q.bindings,exact) ||
 !SameCoreBinding58(p.bindings.core,exact.core) || m.game_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.game_state_slot) ||
 m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.jomini_state_slot) ||
 m.tls_initialized_flag!=base+hotfix26757580::kTlsFlag || s.tls_initialized_flag_address!=m.tls_initialized_flag ||
 reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+hotfix26757580::kTlsGetter ||
 *reinterpret_cast<const std::uint8_t*>(m.tls_initialized_flag)!=1)return false;
 const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));if(!slots || !slots[0])return false;
 const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
 return (*reinterpret_cast<const std::uint32_t*>(block+0x3620)&1U)!=0 && block+0x3628==s.tls_context &&
 *reinterpret_cast<const std::uint8_t*>(s.tls_context+0x20)==1 &&
 std::memcmp(reinterpret_cast<const void*>(q.bindings.get_attacker_war_score),military_hotfix26757580::kScoreEntry32.data(),32)==0;
}
bool OwnerInner58(const PersonalGoldMailboxContextV1&p,const ActiveWarsMailboxContextV1&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 if(p.kind!=ActorObservationKindV1::active_wars || p.wars!=&q || q.output_build!=ImageBuildV1::hotfix26757580 ||
 !p.game || !p.game->enabled() || !game::IsCk3_1210Hotfix26757580Descriptor(p.game->descriptor()) ||
 !p.game->supports(kActiveWarsHotfixCapability58) || !p.mailbox || !p.ticket.sequence || !p.bindings.exact_build_admitted ||
 !q.bindings.exact_build_admitted || !SameCoreBinding58(p.bindings.core,q.bindings.core) ||
 q.bindings.integration_native_calls_permitted || q.bindings.native_call_admission || q.bindings.native_call_admission_context)return false;
 const auto &m=*p.mailbox;
 if(!s.thread_id || s.thread_id!=GetCurrentThreadId() || !s.pump_epoch || s.tls_initialized!=1 || s.tls_main_thread_marker!=1 ||
 !s.tls_context || !s.paused || !s.game_state || !s.jomini_state || !m.iat_hook_installed.load() || !m.active_hook_calls.load() ||
 m.pump_epochs.load()!=s.pump_epoch || m.owner_thread_id.load()!=s.thread_id || m.failure_flags.load()!=0 ||
 m.stop_requested.load() || m.proof_reset_requested.load() ||
 m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
 m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing || m.published_sequence.load()!=p.ticket.sequence ||
 m.executor_started_sequence.load()!=p.ticket.sequence || m.executor_started_pump_epoch.load()!=s.pump_epoch ||
 m.executor_context!=&p || m.executor.load()!=&ExecutePersonalGoldMailboxV1 || !Targets58(p,q,s))return false;
 return *q.bindings.core.game_state_slot==reinterpret_cast<void*>(s.game_state) &&
 *q.bindings.core.jomini_state_slot==reinterpret_cast<void*>(s.jomini_state);
}
bool Owner58(const PersonalGoldMailboxContextV1&p,const ActiveWarsMailboxContextV1&q,
 const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 __try {return OwnerInner58(p,q,s);} __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool Core58(const CoreBindings&b,CoreSnapshotPrefix&p) noexcept {
 __try{return ReadCoreSnapshot(b,p);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
struct Admission58 {
 PersonalGoldMailboxContextV1 &p;ActiveWarsMailboxContextV1 &q;ck3_11906::MainThreadExecutionStampV1 stamp;
 const game::GameAdapter *game;const ck3_11906::MainThreadQueryMailboxV1 *mailbox;
 std::uint64_t ticket;ActiveWarsBindingsV1 bindings;ActiveWarsReadAccessV1 access;CoreSnapshotPrefix expected;
};
bool Admit58(void *context) noexcept {
 if(!context)return false;const auto &a=*static_cast<const Admission58*>(context);
 if(a.p.game!=a.game || a.p.mailbox!=a.mailbox || a.p.ticket.sequence!=a.ticket ||
 !SameWarsBinding58(a.q.bindings,a.bindings) || a.q.fixture_access.context!=a.access.context || a.q.fixture_access.copy!=a.access.copy ||
 !Owner58(a.p,a.q,a.stamp))return false;
 CoreSnapshotPrefix current{};return Core58(a.bindings.core,current) && SamePrefix58(current,a.expected) && Owner58(a.p,a.q,a.stamp);
}
void Clear58(ActiveWarsMailboxContextV1&q,std::string_view reason) noexcept {
 const auto calls=q.observation.native_score_calls_attempted;q.observation={};q.observation.native_score_calls_attempted=calls;
 q.observation.unavailable_reason=reason;q.application_main_observed=false;
}
}
bool ExecuteActiveWarsHotfixOnActor58(PersonalGoldMailboxContextV1&p,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 p.application_main_observed=false;if(!p.wars)return true;auto&q=*p.wars;
 q.observation={};q.application_main_observed=false;q.offline_fixture=false;q.ticket_sequence=q.pump_epoch=0;q.thread_id=0;
 if(!Owner58(p,q,s)){Clear58(q,"active_wars_hotfix_owner_unqualified");return true;}
 CoreSnapshotPrefix expected{};
 if(!Core58(q.bindings.core,expected) || expected.clock.date_raw!=s.date_raw || expected.clock.paused!=s.paused){Clear58(q,"active_wars_hotfix_core_unavailable");return true;}
 q.offline_fixture=p.mailbox->offline_fixture;q.ticket_sequence=p.ticket.sequence;q.pump_epoch=s.pump_epoch;q.thread_id=s.thread_id;
 Admission58 admission{p,q,s,p.game,p.mailbox,p.ticket.sequence,q.bindings,q.fixture_access,expected};
 auto local=q.bindings;local.integration_native_calls_permitted=true;local.native_call_admission=&Admit58;local.native_call_admission_context=&admission;
 (void)ReadActiveWarsV1(local,expected,q.observation,q.fixture_access);
 if(!Admit58(&admission)){Clear58(q,"active_wars_hotfix_owner_changed");return true;}
 q.application_main_observed=!q.offline_fixture;p.application_main_observed=q.application_main_observed;return true;
}
}

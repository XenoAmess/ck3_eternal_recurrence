#include "xar_bridge/ck3_26757580_council_frame67.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <cstring>
#include <limits>
#include <intrin.h>
#include <windows.h>
namespace xar::ck3_1210::council67 {namespace {
bool SameCore(const CoreBindings&a,const CoreBindings&b)noexcept {
 return a.enabled && b.enabled && a.image_build==b.image_build &&
 a.game_state_slot==b.game_state_slot && a.jomini_state_slot==b.jomini_state_slot &&
 a.character_storage_slot==b.character_storage_slot && a.get_local_player==b.get_local_player;
}
bool SameBindings(const Bindings&a,const Bindings&b)noexcept {
 return a.exact_build_admitted && b.exact_build_admitted &&
 SameCore(a.core,b.core) && a.memory.image_base==b.memory.image_base;
}
bool Profile(const game::GameAdapter*a)noexcept {
 return a && a->enabled() && game::IsCk3_1210Hotfix26757580Descriptor(a->descriptor()) &&
 a->supports_snapshot() && a->supports("game.query.fresh-full-state.v1");
}
bool Targets(const PersonalGoldMailboxContextV1&p,const MailboxContext&q,
 const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 const auto&m=*p.mailbox;
#if defined(XAR_CK3_COUNCIL67_OFFLINE_FIXTURE)
 if(m.offline_fixture)return true;
#else
 if(m.offline_fixture)return false;
#endif
 const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
 const auto exact=BindImage(base,p.game->descriptor().executable_sha256);
 if(!base || p.image_base!=base || m.module_base!=base ||
 q.read_access.context || q.read_access.copy || !SameBindings(q.bindings,exact) ||
 !SameCore(p.bindings.core,exact.core) ||
 m.game_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.game_state_slot) ||
 m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(exact.core.jomini_state_slot) ||
 m.tls_initialized_flag!=base+hotfix26757580::kTlsFlag ||
 s.tls_initialized_flag_address!=m.tls_initialized_flag ||
 reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+hotfix26757580::kTlsGetter ||
 *reinterpret_cast<const std::uint8_t*>(m.tls_initialized_flag)!=1)return false;
 // Require the already-warm embedded context; never call its lazy getter.
 const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));
 if(!slots || !slots[0])return false;
 const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
 return (*reinterpret_cast<const std::uint32_t*>(block+0x3620)&1U)!=0 &&
 block+0x3628==s.tls_context && *reinterpret_cast<const std::uint8_t*>(s.tls_context+0x20)==1;
}
bool OwnerInner(const PersonalGoldMailboxContextV1&p,const MailboxContext&q,
 const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 if(p.kind!=ActorObservationKindV1::council_observation67 || p.council67!=&q ||
 !Profile(p.game) || !Profile(q.native_full_adapter) || !p.mailbox || !p.ticket.sequence ||
 !p.bindings.exact_build_admitted || !q.bindings.exact_build_admitted ||
 !IsHotfix(q.bindings.core.image_build) || !SameCore(p.bindings.core,q.bindings.core) ||
 !q.expected_native_revision || !q.current_published_revision)return false;
 const auto&m=*p.mailbox;
 if(!s.thread_id || s.thread_id!=GetCurrentThreadId() || !s.pump_epoch ||
 s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || !s.tls_context ||
 !s.paused || !s.game_state || !s.jomini_state ||
 !m.iat_hook_installed.load() || !m.active_hook_calls.load() ||
 m.owner_thread_id.load()!=s.thread_id || m.pump_epochs.load()!=s.pump_epoch ||
 m.failure_flags.load() || m.stop_requested.load() || m.proof_reset_requested.load() ||
 m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
 m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing ||
 m.published_sequence.load()!=p.ticket.sequence || m.executor_started_sequence.load()!=p.ticket.sequence ||
 m.executor_started_pump_epoch.load()!=s.pump_epoch || m.executor_context!=&p ||
 m.executor.load()!=&ExecutePersonalGoldMailboxV1 || !Targets(p,q,s))return false;
 return *q.bindings.core.game_state_slot==reinterpret_cast<void*>(s.game_state) &&
 *q.bindings.core.jomini_state_slot==reinterpret_cast<void*>(s.jomini_state) &&
 *q.current_published_revision==q.expected_native_revision;
}
bool Owner(const PersonalGoldMailboxContextV1&p,const MailboxContext&q,
 const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 __try{return OwnerInner(p,q,s);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool SafeCopy(std::uintptr_t from,void*to,std::size_t size)noexcept {
 __try{std::memcpy(to,reinterpret_cast<const void*>(from),size);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool CoreRead(const CoreBindings&b,CoreSnapshotPrefix&p)noexcept {
 __try{return ReadCoreSnapshot(b,p);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool FullRead(const game::GameAdapter&a,game::Snapshot&s)noexcept {
 __try{return a.read_snapshot(s);}
 __except(GetExceptionCode()==0xE06D7363UL?EXCEPTION_CONTINUE_SEARCH:EXCEPTION_EXECUTE_HANDLER){return false;}
}
CoreSnapshotPrefix Prefix(const game::Snapshot&s)noexcept {
 CoreSnapshotPrefix p{};p.clock={s.date_raw,s.speed,s.paused};p.local_player_id=s.player_id;
 p.map_ready=s.map_ready;p.has_played_character=s.has_played_character;
 p.played_character_id=s.played_character_id;p.played_character_alive=s.played_character_alive;return p;
}
bool SamePrefix(const CoreSnapshotPrefix&a,const CoreSnapshotPrefix&b)noexcept {
 return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed &&
 a.clock.paused==b.clock.paused && a.local_player_id==b.local_player_id &&
 a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
 a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
struct Record {
 std::uintptr_t address=0;std::vector<std::byte> bytes;
 friend bool operator==(const Record&,const Record&)=default;
};
struct Scope {
 PersonalGoldMailboxContextV1&p;MailboxContext&q;ck3_11906::MainThreadExecutionStampV1 stamp;
 const game::GameAdapter*parent_adapter;const game::GameAdapter*raw_adapter;
 const std::uint64_t*revision_source;const ck3_11906::MainThreadQueryMailboxV1*mailbox;
 std::uint64_t revision,ticket;Bindings bindings;ReadAccess access;
 bool owner_failed=false;std::size_t bytes=0;std::vector<Record> ledger;
 bool Admit()noexcept {
  const bool okay=p.game==parent_adapter && p.mailbox==mailbox && p.council67==&q &&
   p.ticket.sequence==ticket && q.native_full_adapter==raw_adapter &&
   q.current_published_revision==revision_source && q.expected_native_revision==revision &&
   SameBindings(q.bindings,bindings) && SameCore(p.bindings.core,bindings.core) &&
   q.read_access.context==access.context && q.read_access.copy==access.copy && Owner(p,q,stamp);
  if(!okay)owner_failed=true;return okay;
 }
 static bool Consistent(void*c)noexcept{return static_cast<Scope*>(c)->Admit();}
 static bool Copy(void*c,std::uintptr_t from,void*to,std::size_t size)noexcept {
  auto&s=*static_cast<Scope*>(c);
  if(!s.Admit() || size>262144-s.bytes || s.ledger.size()>=8192)return false;
  try {
   Record r;r.address=from;r.bytes.resize(size);
   const bool read=s.access.copy?s.access.copy(s.access.context,from,r.bytes.data(),size):SafeCopy(from,r.bytes.data(),size);
   if(!s.Admit() || !read)return false;
   std::memcpy(to,r.bytes.data(),size);s.bytes+=size;s.ledger.push_back(std::move(r));return true;
  }catch(...){return false;}
 }
 template<class T>bool Get(std::uintptr_t address,T&out)noexcept {
  return Copy(this,address,&out,sizeof(out));
 }
 bool Read(xar::council_observation65::Observation&out,const game::Snapshot&basis) {
  out.rows.clear();out.reason="council67_core_source_unavailable";
  CoreSnapshotPrefix current{};
  if(!Admit() || !CoreRead(bindings.core,current) || !Admit() || !SamePrefix(current,Prefix(basis)))return false;
  xar::council_observation65::FrameSource f{};
  f.native_revision=revision;f.date_raw=basis.date_raw;f.actor_id=basis.played_character_id;
  std::uintptr_t slots=0;
  if(!Get(reinterpret_cast<std::uintptr_t>(bindings.core.game_state_slot),f.game_state) ||
   f.game_state>std::numeric_limits<std::uintptr_t>::max()-0xA0 ||
   !Get(f.game_state+0xA0,f.game_data) ||
   !Get(reinterpret_cast<std::uintptr_t>(bindings.core.character_storage_slot),f.character_store) ||
   f.character_store>std::numeric_limits<std::uintptr_t>::max()-0x20 ||
   !Get(f.character_store+0x20,slots) ||
   slots>std::numeric_limits<std::uintptr_t>::max()-0x10000000 ||
   !Get(slots+(static_cast<std::uint32_t>(f.actor_id)&0xFFFFFFU)*16ULL+8,f.actor))return false;
  return xar::council_observation65::Read(bindings.memory,{this,&Copy,&Consistent},f,out);
 }
};
void Clear(MailboxContext&q,std::string_view reason)noexcept {
 q.observation.rows.clear();q.observation.reason=reason;q.completed=q.data_ready=false;
 q.application_main_observed=false;
}
}
Bindings BindImage(std::uintptr_t base,std::string_view sha)noexcept {
 Bindings b{};b.memory=xar::council_observation65::BindImage(base,sha);
 if(b.memory.image_base){b.core=BindCoreImage(base,sha);b.exact_build_admitted=b.core.enabled && IsHotfix(b.core.image_build);}
 return b.exact_build_admitted?b:Bindings{};
}
bool ExecuteOnActor(PersonalGoldMailboxContextV1&p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept {
 p.application_main_observed=false;if(!p.council67)return true;auto&q=*p.council67;
 q.observation={};q.completed=q.data_ready=q.application_main_observed=q.offline_fixture=false;
 q.ticket_sequence=q.pump_epoch=0;q.thread_id=0;q.current_full_attempts=0;
 try {
  if(!Owner(p,q,s)){Clear(q,"council67_actor_owner_unqualified");return true;}
  const game::Snapshot basis=q.expected_full;
  if(!basis.paused || !basis.map_ready || !basis.has_played_character || !basis.played_character_alive ||
   basis.played_character_id==-1 || basis.date_raw!=s.date_raw){Clear(q,"council67_full_basis_unavailable");return true;}
  q.offline_fixture=p.mailbox->offline_fixture;q.application_main_observed=!q.offline_fixture;
  p.application_main_observed=q.application_main_observed;q.ticket_sequence=p.ticket.sequence;
  q.pump_epoch=s.pump_epoch;q.thread_id=s.thread_id;
  Scope scope{p,q,s,p.game,q.native_full_adapter,q.current_published_revision,p.mailbox,
   q.expected_native_revision,p.ticket.sequence,q.bindings,q.read_access};
  game::Snapshot before{},after{};++q.current_full_attempts;
  if(!scope.Admit() || !FullRead(*scope.raw_adapter,before) || !scope.Admit() ||
   before!=basis || q.expected_full!=basis){Clear(q,"council67_full_before_changed");return true;}
  const bool read=scope.Read(q.observation,basis);
  if(scope.owner_failed){Clear(q,"council67_owner_during_read");return true;}
  auto source=std::move(scope.ledger);scope.ledger.clear();scope.bytes=0;
  ++q.current_full_attempts;
  if(!scope.Admit() || !FullRead(*scope.raw_adapter,after) || !scope.Admit() ||
   after!=basis || q.expected_full!=basis){Clear(q,"council67_full_after_changed");return true;}
  if(read){
   xar::council_observation65::Observation confirm{};
   if(!scope.Read(confirm,basis) || !scope.Admit() || source!=scope.ledger ||
    confirm.rows!=q.observation.rows || q.expected_full!=basis){
    Clear(q,"council67_sources_after_full_changed");return true;
   }
  }
  if(scope.owner_failed || !scope.Admit()){Clear(q,"council67_owner_final");return true;}
  if(!read && q.observation.reason.empty())q.observation.reason="council67_core_source_unavailable";
  q.data_ready=read;q.completed=true;return true;
 }catch(...){Clear(q,"council67_cpp_exception");return true;}
}
} // namespace xar::ck3_1210::council67

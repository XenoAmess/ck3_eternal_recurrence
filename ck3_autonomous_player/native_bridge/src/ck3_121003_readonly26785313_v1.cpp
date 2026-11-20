#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_gui_root_index26785313_pins_v1.hpp"
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
#include "xar_bridge/ck3_121003_application_exit26785313_v1.hpp"
#endif
#include <array>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <utility>
#include <windows.h>
#include <intrin.h>

namespace xar::ck3_121003::build26785313 { namespace {
bool Copy(const void *from,void *to,std::size_t size) noexcept {
  if(!from||!to)return false;
  __try {std::memcpy(to,from,size);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T> bool At(std::uintptr_t base,std::size_t offset,T &out) noexcept {
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  return base&&offset<=max-base&&sizeof(T)-1<=max-base-offset&&
      Copy(reinterpret_cast<const void*>(base+offset),&out,sizeof(out));
}
bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
  return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
    a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
    a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
bool Sha(std::string_view input) noexcept {
  if(input.size()!=64)return false;
  for(std::size_t i=0;i<64;++i) {
    char v=input[i];if(v>='a'&&v<='f')v=static_cast<char>(v-'a'+'A');
    if(v!=kExecutableSha256[i])return false;
  }
  return true;
}
bool ExactTargets(const ReadonlyBindings&b) noexcept {
  const auto base=b.module_base;
  return b.exact_image_admitted&&b.core.enabled&&base&&
    b.core.image_build==ck3_1210::ImageBuildV1::unknown&&
    reinterpret_cast<std::uintptr_t>(b.core.game_state_slot)==base+kGameStateSlotRva&&
    reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot)==base+kJominiStateSlotRva&&
    reinterpret_cast<std::uintptr_t>(b.core.character_storage_slot)==base+kCharacterStorageSlotRva&&
    reinterpret_cast<std::uintptr_t>(b.core.get_local_player)==base+kGetLocalPlayerRva;
}
struct OwnerInvocationV1 {
  ck3_11906::MainThreadQueryExecutorV1 executor=&ExecuteReadonlyOnOwner;
  void *context=nullptr;
};
bool OwnerInner(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
    const OwnerInvocationV1 &invocation) noexcept {
  if(invocation.executor!=&ExecuteReadonlyOnOwner) {
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
    if(invocation.executor!=&ExecuteApplicationExitOnOwner267V1 || !invocation.context)return false;
#else
    return false;
#endif
  }
  const void *const actual_context=invocation.context?invocation.context:&q;
  if(!q.mailbox||!q.ticket.sequence||!q.bindings.exact_image_admitted)return false;
  auto&m=*q.mailbox;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  if(m.offline_fixture)return q.bindings.offline_fixture&&q.bindings.core.enabled;
  if(q.bindings.offline_fixture)return false;
#else
  if(m.offline_fixture)return false;
#endif
  const auto base=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if(!base||q.bindings.module_base!=base||m.module_base!=base||!ExactTargets(q.bindings)||
    !VerifyReadonlyImage(base)||!s.thread_id||s.thread_id!=GetCurrentThreadId()||!s.pump_epoch||
    !s.paused||s.tls_initialized!=1||s.tls_main_thread_marker!=1||!s.tls_context||!s.game_state||!s.jomini_state||
    !m.iat_hook_installed.load()||!m.active_hook_calls.load()||
    m.owner_thread_id.load()!=s.thread_id||m.pump_epochs.load()!=s.pump_epoch||
    m.failure_flags.load()!=0||m.stop_requested.load()||m.proof_reset_requested.load()||
    m.paused_owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs||
    m.owner_verified_pump_epochs.load()<ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs||
    m.state.load()!=ck3_11906::MainThreadQueryMailboxStateV1::executing||
    m.published_sequence.load()!=q.ticket.sequence||m.executor_started_sequence.load()!=q.ticket.sequence||
    m.executor_started_pump_epoch.load()!=s.pump_epoch||m.executor_context!=actual_context||
    m.executor.load()!=invocation.executor||
    m.game_state_slot!=base+kGameStateSlotRva||m.jomini_state_slot!=base+kJominiStateSlotRva||
    m.tls_initialized_flag!=base+kTlsFlagRva||s.tls_initialized_flag_address!=m.tls_initialized_flag||
    reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=base+kTlsGetterRva)return false;
  // Reuse Opening56's already-warm TLS check. Do not invoke a lazy TLS getter.
  std::uint8_t initialized=0,marker=0;
  std::uint32_t flags=0;
  if(!At(base,kTlsFlagRva,initialized)||initialized!=1)return false;
  const auto slots=reinterpret_cast<void**>(__readgsqword(0x58));
  if(!slots||!slots[0])return false;
  const auto block=reinterpret_cast<std::uintptr_t>(slots[0]);
  if(!At(block,0x3620,flags)||(flags&1U)==0||block+0x3628!=s.tls_context||
    !At(s.tls_context,0x20,marker)||marker!=1)return false;
  std::uintptr_t state=0,jomini=0;
  return At(base,kGameStateSlotRva,state)&&At(base,kJominiStateSlotRva,jomini)&&
    state==s.game_state&&jomini==s.jomini_state;
}
bool Owner(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
    const OwnerInvocationV1 &invocation={}) noexcept {
  __try {return OwnerInner(q,s,invocation);}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
#include "ck3_121003_gui_root_index26785313_v1.inc"
struct Sample {
  ck3_1210::CoreSnapshotPrefix core{};
  std::uintptr_t state=0,jomini=0,storage=0,data=0,players=0,actor=0,living=0;
  std::int32_t id=-1;
  std::uint32_t type=0;
  std::uintptr_t death=0;
  RawResources resources{};
  std::optional<GuiRootIndexV1> gui_root_index;
};
bool Same(const Sample&a,const Sample&b) noexcept {
  return Same(a.core,b.core)&&a.state==b.state&&a.jomini==b.jomini&&a.storage==b.storage&&
    a.data==b.data&&a.players==b.players&&a.actor==b.actor&&a.living==b.living&&
    a.id==b.id&&a.type==b.type&&a.death==b.death&&a.resources==b.resources&&
    a.gui_root_index==b.gui_root_index;
}
bool NativeCore(const ck3_1210::CoreBindings&b,ck3_1210::CoreSnapshotPrefix&out) noexcept {
  __try {return ck3_1210::ReadCoreSnapshot(b,out);}
  __except(EXCEPTION_EXECUTE_HANDLER){out={};return false;}
}
std::uintptr_t Resolve(const ck3_1210::CoreBindings&b,std::int32_t id) noexcept {
  __try {return reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b,id));}
  __except(EXCEPTION_EXECUTE_HANDLER){return 0;}
}
bool Take(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,Sample&out,
    const OwnerInvocationV1 &invocation) noexcept {
  if(!Owner(q,s,invocation))return false;
  ++q.observation.core_read_attempts;
  if(!NativeCore(q.bindings.core,out.core)||!Owner(q,s,invocation)||!out.core.clock.paused||
    !out.core.map_ready||!out.core.has_played_character||!out.core.played_character_alive||
    out.core.played_character_id==-1)return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  const bool offline=q.bindings.offline_fixture;
#else
  constexpr bool offline=false;
#endif
  if(!offline&&out.core.clock.date_raw!=s.date_raw)return false;
  if(!At(reinterpret_cast<std::uintptr_t>(q.bindings.core.game_state_slot),0,out.state)||
    !At(reinterpret_cast<std::uintptr_t>(q.bindings.core.jomini_state_slot),0,out.jomini)||
    !At(reinterpret_cast<std::uintptr_t>(q.bindings.core.character_storage_slot),0,out.storage)||
    !At(out.state,0xA0,out.data)||!At(out.jomini,0x18,out.players))return false;
  out.actor=Resolve(q.bindings.core,out.core.played_character_id);
  if(!At(out.actor,0x18,out.id)||!At(out.actor,0x1C,out.type)||!At(out.actor,0x1D0,out.death)||
    out.id!=out.core.played_character_id||out.type!=0x43686172U||out.death!=0)return false;
  if(q.mode==ReadonlyModeV1::core_only)return Owner(q,s,invocation);
  if(q.mode==ReadonlyModeV1::core_and_gui_root_index) {
    GuiRootIndexV1 roots{};
    if(!ReadGuiRootIndexV1(q,s,out.core,roots))return false;
    out.gui_root_index=std::move(roots);return Owner(q,s,invocation);
  }
  if(q.mode!=ReadonlyModeV1::core_and_raw_resources||!At(out.actor,0x1B0,out.living))return false;
  // Named current-image GetGold/GetPrestige/GetPiety/GetStress callers prove these widths.
  // Null living is the native getters' observed zero branch, not a failed copy.
  if(out.living&&(!At(out.living,0x100,out.resources.personal_gold_raw)||
    !At(out.living,0x130,out.resources.prestige_raw)||!At(out.living,0x110,out.resources.piety_raw)||
    !At(out.living,0x2F8,out.resources.stress_points)))return false;
  return Owner(q,s,invocation);
}
bool Read(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
    const OwnerInvocationV1 &invocation={}) noexcept {
  Sample a{},b{};
  if(!Take(q,s,a,invocation)||!Take(q,s,b,invocation)||!Same(a,b)||!Owner(q,s,invocation))return false;
  q.observation.available=true;q.observation.core=b.core;
  if(q.mode==ReadonlyModeV1::core_and_raw_resources)q.observation.raw_resources=b.resources;
  if(q.mode==ReadonlyModeV1::core_and_gui_root_index)q.observation.gui_root_index=std::move(b.gui_root_index);
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  q.observation.offline_fixture=q.bindings.offline_fixture;
#endif
  q.observation.main_owner_observed=!q.observation.offline_fixture;
  q.observation.unavailable_reason={};return true;
}
} // namespace
std::span<const ImagePin> ReadonlyImagePins() noexcept {return pins::kPins;}
std::span<const ImagePin> GuiRootIndexImagePinsV1() noexcept {return gui_root_pins::kPins;}
bool VerifyGuiRootIndexImageV1([[maybe_unused]]std::uintptr_t base) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_ROOT_INDEX_V1)
  return false;
#else
  if(!VerifyReadonlyImage(base))return false;
  std::array<unsigned char,64> observed{};
  for(const auto &pin:gui_root_pins::kPins) {
    if(pin.bytes.empty() || pin.bytes.size()>observed.size() || pin.rva>kImageSize-pin.bytes.size() ||
        !Copy(reinterpret_cast<const void*>(base+pin.rva),observed.data(),pin.bytes.size()) ||
        std::memcmp(observed.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
  }
  for(const auto &type:gui_root_pins::kTypes) {
    std::uintptr_t col=0;
    if(!At(base,type.vtable_rva-sizeof(std::uintptr_t),col) || col!=base+type.col_rva)return false;
  }
  return true;
#endif
}
bool VerifyReadonlyImage(std::uintptr_t base) noexcept {
  if(!base||base>(std::numeric_limits<std::uintptr_t>::max)()-kImageSize)return false;
  std::uint16_t mz=0,machine=0,magic=0;std::uint32_t pe=0,sig=0,stamp=0,size=0;
  std::uint64_t preferred_base=0;
  if(!At(base,0,mz)||mz!=0x5A4D||!At(base,0x3C,pe)||pe>0x800||
    !At(base,pe,sig)||sig!=0x4550||!At(base,pe+4,machine)||machine!=0x8664||
    !At(base,pe+8,stamp)||stamp!=kPeTimestamp||!At(base,pe+24,magic)||magic!=0x20B||
    !At(base,pe+24+24,preferred_base)||preferred_base!=0x140000000ULL||
    !At(base,pe+24+56,size)||size!=kImageSize)return false;
  std::array<unsigned char,64> observed{};
  for(const auto &pin:pins::kPins) {
    if(pin.bytes.empty()||pin.bytes.size()>observed.size()||pin.rva>kImageSize-pin.bytes.size()||
      !Copy(reinterpret_cast<const void*>(base+pin.rva),observed.data(),pin.bytes.size())||
      std::memcmp(observed.data(),pin.bytes.data(),pin.bytes.size())!=0)return false;
  }
  return true;
}
ReadonlyBindings BindReadonlyImage(std::uintptr_t base,std::string_view sha) noexcept {
  ReadonlyBindings out{};
  if(!Sha(sha)||!VerifyReadonlyImage(base))return out;
  out.exact_image_admitted=true;out.module_base=base;
  out.core.enabled=true;out.core.image_build=ck3_1210::ImageBuildV1::unknown;
  out.core.game_state_slot=reinterpret_cast<void**>(base+kGameStateSlotRva);
  out.core.jomini_state_slot=reinterpret_cast<void**>(base+kJominiStateSlotRva);
  out.core.character_storage_slot=reinterpret_cast<void**>(base+kCharacterStorageSlotRva);
  out.core.get_local_player=reinterpret_cast<ck3_1210::GetLocalPlayer>(base+kGetLocalPlayerRva);
  return out;
}
const ck3_11906::MainThreadQueryBuildProfileV1 &ReadonlyThreadProfile() noexcept {
  static const ck3_11906::MainThreadQueryBuildProfileV1 p{kPeekReturnRva,kPeekMessageWIatRva,kRngWrapperSlotRva,
    kJominiStateSlotRva,kGameStateSlotRva,kTlsFlagRva,kTlsGetterRva,&VerifyReadonlyImage};
  return p;
}
bool ExecuteReadonlyOnOwner(void *ptr,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  if(!ptr)return false;auto&q=*static_cast<ReadonlyContext*>(ptr);q.observation={};
  if(!Read(q,s)) {
    const auto attempts=q.observation.core_read_attempts;
    q.observation={};q.observation.core_read_attempts=attempts;
    q.observation.unavailable_reason=q.mode==ReadonlyModeV1::core_and_gui_root_index
        ?"exact_gui_root_index_source_unavailable":"exact_paused_readonly_source_unavailable";
  }
  return true; // typed unavailable is separate from executor infrastructure ACK
}
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
bool ReadApplicationExitCoreOnOwner267V1(const ReadonlyBindings &bindings,
    ck3_11906::MainThreadQueryMailboxV1 *mailbox,const ck3_11906::MainThreadQueryTicketV1 &ticket,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,void *actual_context,ReadonlyObservation &out) noexcept {
  out={};if(!actual_context)return false;
  ReadonlyContext q;q.bindings=bindings;q.mailbox=mailbox;q.ticket=ticket;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteApplicationExitOnOwner267V1,actual_context};
  const bool good=Read(q,stamp,invocation);out=std::move(q.observation);return good;
}
#endif
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
ReadonlyBindings NoGameBindings(std::uintptr_t image,ck3_1210::CoreBindings core) noexcept {
  auto out=BindReadonlyImage(image,kExecutableSha256);
  if(out.exact_image_admitted){out.core=core;out.offline_fixture=true;}return out;
}
#endif
} // namespace xar::ck3_121003::build26785313

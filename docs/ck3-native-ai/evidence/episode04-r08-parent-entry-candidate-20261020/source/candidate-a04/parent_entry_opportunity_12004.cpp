#include "parent_entry_opportunity_12004.hpp"
#include <cstring>
#include <mutex>
#if !defined(XAR_ENABLE_PARENT_ENTRY_OPPORTUNITY_12004)
#error Parent entry source candidate requires explicit default-OFF build opt-in
#endif

extern "C" {
xar::ck3_12004::parent_entry::WireState XarParentEntryState12004{};
std::uintptr_t XarParentEntryContinuation12004=0;
extern void (*const XarParentEntryOriginalPrefixTarget12004)()=&XarParentEntryOriginalPrefix12004;
}
namespace xar::ck3_12004::parent_entry {
namespace {
std::mutex mutex;
Admission owner{};
Environment environment{};
std::array<std::uint8_t,16> patch{};
bool owned=false,patch_may_be_present=false,armed_once=false,identity_before=false;
DWORD original_protection=0;
constexpr std::uint64_t kMaximumPointer=0x00007fffffffffffULL;
bool Pointer(std::uint64_t p,std::size_t n=1) noexcept {
  return p>=0x10000 && n && p<=kMaximumPointer-(n-1);
}
template<class T> bool ReadAt(std::uintptr_t p,T&v) noexcept {
  return Pointer(p,sizeof v)&&environment.read&&
    environment.read(environment.context,p,&v,sizeof v);
}
LONG64 Atomic(volatile LONG64&v) noexcept {return InterlockedCompareExchange64(&v,0,0);}
bool Identity() noexcept {
  std::uint32_t id=0,magic=0,day=0;
  std::uint64_t death=0,a=0,b=0,state=0,recheck=0,date=0;
  FILETIME created{},exited{},kernel{},user{};
  if(GetCurrentProcessId()!=owner.pid||
     reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))!=owner.module_base||
     !GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user))return false;
  const auto actual_created=(std::uint64_t(created.dwHighDateTime)<<32)|created.dwLowDateTime;
  return actual_created==owner.process_create_time_100ns&&
    ReadAt(owner.character+0x18,id)&&id==owner.full_id&&
    ReadAt(owner.character+0x1c,magic)&&magic==0x43686172&&
    ReadAt(owner.character+0x1d0,death)&&death==0&&
    ReadAt(owner.character+0x1c0,a)&&ReadAt(owner.character+0x1c0,b)&&
    a==b&&a==owner.context&&
    ReadAt(owner.module_base+0x5C68C50,state)&&state==owner.game_state&&
    ReadAt(state+8,date)&&ReadAt(state+0x9c,day)&&
    ReadAt(owner.module_base+0x5C68C50,recheck)&&recheck==state&&
    static_cast<std::uint32_t>(date)>=owner.date_raw&&
    static_cast<std::uint32_t>(date)<=owner.date_raw+24&&
    day>=owner.absolute_day&&day<=owner.absolute_day+1;
}
bool ReadPrefix(std::array<std::uint8_t,16>&v) noexcept {
  return ReadAt(owner.module_base+kEntryRva,v);
}
bool CopyPrefix(const std::array<std::uint8_t,16>&v) noexcept {
  __try {std::memcpy(reinterpret_cast<void*>(owner.module_base+kEntryRva),v.data(),v.size());return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool Restore() noexcept {
  if(!patch_may_be_present)return true;
  std::array<std::uint8_t,16> current{};
  if(!ReadPrefix(current)||(current!=patch&&current!=kPrefix))return false;
  auto*target=reinterpret_cast<void*>(owner.module_base+kEntryRva);
  DWORD temporary=0,ignored=0;
  if(!VirtualProtect(target,16,PAGE_EXECUTE_READWRITE,&temporary))return false;
  const bool copied=CopyPrefix(kPrefix);
  const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,16)!=FALSE;
  const bool protected_again=VirtualProtect(target,16,original_protection,&ignored)!=FALSE;
  std::array<std::uint8_t,16> actual{};
  if(!copied||!flushed||!protected_again||!ReadPrefix(actual)||actual!=kPrefix)return false;
  patch_may_be_present=false;
  return true;
}
}
bool Install(const Admission&a,const Environment&e) noexcept {
  try {
    const std::lock_guard lock(mutex);
    if(owned||!e.all_reachable_threads_quiescent||!e.read||
       !a.ordinary_null_owner||!a.explicit_entry_hook_admission||
       a.machine_id.empty()||a.executable_sha256!=kExeSha||!a.pid||
       !a.process_create_time_100ns||!a.generation||!a.window||!a.payment_epoch||
       !a.full_id||!a.local_player_id||!Pointer(a.character,0x1d8)||!Pointer(a.context)||
       !Pointer(a.game_state,0xa0)||!Pointer(a.module_base,102518784)||
       a.date_raw>UINT32_MAX-24||a.absolute_day>UINT32_MAX-1)return false;
    owner=a;environment=e;
    std::array<std::uint8_t,16> current{};
    if(!Identity()||!ReadPrefix(current)||current!=kPrefix)return false;
    // Static ASM copied prefix has its own compiler-generated pdata/xdata.
    // Reject any actual emitted bytes differing from the held16B anchor.
    std::array<std::uint8_t,16> emitted{};
    if(!ReadAt(reinterpret_cast<std::uintptr_t>(&XarParentEntryOriginalPrefix12004),emitted)||
       emitted!=kPrefix)return false;
    HMODULE pinned=nullptr;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&XarParentEntryThunk12004),&pinned))return false;
    XarParentEntryContinuation12004=a.module_base+kEntryRva+16;
    patch.fill(0x90);patch[0]=0xff;patch[1]=0x25;
    std::memset(patch.data()+2,0,4);
    const auto destination=reinterpret_cast<std::uintptr_t>(&XarParentEntryThunk12004);
    std::memcpy(patch.data()+6,&destination,sizeof destination);
    auto&wire=XarParentEntryState12004;
    wire.target_character=a.character;wire.admitted_full_id=a.full_id;
    wire.epoch=a.payment_epoch;wire.generation=a.generation;wire.window=a.window;
    wire.admission_date=a.date_raw;wire.admission_absolute_day=a.absolute_day;
    auto*target=reinterpret_cast<void*>(a.module_base+kEntryRva);
    if(!VirtualProtect(target,16,PAGE_EXECUTE_READWRITE,&original_protection))return false;
    // Ownership is retained before the first byte can possibly be changed.
    owned=true;patch_may_be_present=true;
    const bool copied=CopyPrefix(patch);
    const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,16)!=FALSE;
    DWORD ignored=0;
    const bool protected_again=VirtualProtect(target,16,original_protection,&ignored)!=FALSE;
    if(!copied||!flushed||!protected_again||!ReadPrefix(current)||current!=patch){
      if(Restore())owned=false;
      return false;
    }
    return true; // installed but runtime OFF
  }catch(...){return false;}
}
bool ArmOnce() noexcept {
  try {
    const std::lock_guard lock(mutex);
    if(!owned||!patch_may_be_present||armed_once||!Identity())return false;
    std::array<std::uint8_t,16> current{};
    if(!ReadPrefix(current)||current!=patch)return false;
    auto&wire=XarParentEntryState12004;
    if(Atomic(wire.enabled)||Atomic(wire.active_thunks)||Atomic(wire.frame_state))return false;
    // No reset/rearm route. All immutable configuration was set before publish.
    identity_before=true;armed_once=true;
    InterlockedExchange64(&wire.enabled,1);
    return true;
  }catch(...){return false;}
}
bool StopAndSnapshot(Snapshot&out) noexcept {
  try {
    const std::lock_guard lock(mutex);
    auto&wire=XarParentEntryState12004;
    InterlockedExchange64(&wire.enabled,0); // unconditional safe OFF first
    out={};
    if(!owned)return false;
    out.owner=owner;
    if(!armed_once){out.status=Snapshot::Status::not_armed;return false;}
    out.identity_before_verified=identity_before;
    if(Atomic(wire.active_thunks)){
      out.status=Snapshot::Status::busy;out.producer_busy=true;return false;
    }
    std::array<std::uint8_t,16> current{};
    if(!ReadPrefix(current)||current!=patch){
      out.status=Snapshot::Status::invalid_wire_state;return false;
    }
    const auto state=Atomic(wire.frame_state);
    const auto overflow=Atomic(wire.counter_overflow);
    if((state!=0&&state!=2)||(overflow!=0&&overflow!=1)){
      out.status=Snapshot::Status::invalid_wire_state;return false;
    }
    out.raw_foreign_counter_bits=static_cast<std::uint64_t>(Atomic(wire.foreign_count));
    out.raw_matching_counter_bits=static_cast<std::uint64_t>(Atomic(wire.matching_pointer_count));
    out.raw_dropped_counter_bits=static_cast<std::uint64_t>(Atomic(wire.dropped_matching_count));
    if(state==2)out.frame=wire.frame;
    const bool frame_consistent=state==0||
      (out.frame->rdx==owner.character&&Pointer(out.frame->rsp,sizeof(std::uint64_t)));
    const bool counts_consistent=overflow||
      (state==0?(*out.raw_matching_counter_bits==0&&*out.raw_dropped_counter_bits==0):
       (*out.raw_matching_counter_bits>0&&
        *out.raw_dropped_counter_bits==*out.raw_matching_counter_bits-1));
    if(!frame_consistent||!counts_consistent){
      out.status=Snapshot::Status::invalid_wire_state;return false;
    }
    if(!overflow){
      out.foreign_count=out.raw_foreign_counter_bits;
      out.matching_pointer_count=out.raw_matching_counter_bits;
      out.dropped_matching_count=out.raw_dropped_counter_bits;
    }
    out.counter_overflow=overflow!=0;
    out.frame_state=static_cast<std::uint64_t>(state);
    out.identity_after_verified=Identity();out.stopped=true;out.producer_busy=false;
    out.status=Snapshot::Status::stopped;
    return true; // capture closed, NOT a target-ID-at-entry/business PASS
  }catch(...){return false;}
}
bool Uninstall(bool quiescent) noexcept {
  try {
    const std::lock_guard lock(mutex);
    InterlockedExchange64(&XarParentEntryState12004.enabled,0);
    if(!quiescent||Atomic(XarParentEntryState12004.active_thunks))return false;
    if(!owned)return true;
    if(!Restore())return false;
    owned=false;
    // Static code remains pinned even after success; do not unload on a guess.
    return true;
  }catch(...){return false;}
}
}

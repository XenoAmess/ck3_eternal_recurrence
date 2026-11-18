#include "xar_bridge/ck3_1210_daily_final_hook_v1.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <exception>
#include <limits>
#include <windows.h>

namespace xar::ck3_1210 {
namespace {
static_assert(sizeof(DailyFinalOriginalV1)==8 && sizeof(void *)==8);
SRWLOCK g_life=SRWLOCK_INIT;
SRWLOCK g_entry=SRWLOCK_INIT;
DailyFinalHookStateV1 *g_active=nullptr; // Both locks for writes; entry for readers.
std::atomic<DailyFinalOriginalV1> g_fallback{nullptr};
bool g_used=false; // One successful installation per DLL/process lifetime.
struct Exclusive {
  SRWLOCK *lock;
  explicit Exclusive(SRWLOCK &v) noexcept:lock(&v){AcquireSRWLockExclusive(lock);}
  ~Exclusive(){ReleaseSRWLockExclusive(lock);}
};
std::uintptr_t Bits(DailyFinalOriginalV1 fn) noexcept {return std::bit_cast<std::uintptr_t>(fn);}
DailyFinalOriginalV1 Function(std::uintptr_t p) noexcept {return std::bit_cast<DailyFinalOriginalV1>(p);}
bool DefaultCopy(void *,const void *from,void *to,std::size_t n) noexcept {
  if(!from||!to)return false;
#if defined(_MSC_VER)
  __try {std::memcpy(to,from,n);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  std::memcpy(to,from,n);return true;
#endif
}
bool DefaultProtect(void *,void *at,std::size_t n,std::uint32_t protection,std::uint32_t &old) noexcept {
  DWORD actual=0;
  if(!VirtualProtect(at,n,static_cast<DWORD>(protection),&actual))return false;
  old=actual;return true;
}
bool DefaultExchange(void *,DailyFinalOriginalV1 *slot,DailyFinalOriginalV1 desired,
    DailyFinalOriginalV1 expected,DailyFinalOriginalV1 &observed) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    auto *raw=reinterpret_cast<void *volatile *>(slot);
    auto previous=InterlockedCompareExchangePointer(raw,std::bit_cast<void *>(desired),std::bit_cast<void *>(expected));
    observed=std::bit_cast<DailyFinalOriginalV1>(previous);return true;
#if defined(_MSC_VER)
  } __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
DailyFinalHookMemoryV1 Memory(DailyFinalHookMemoryV1 m) noexcept {
  if(!m.copy)m.copy=DefaultCopy;if(!m.protect)m.protect=DefaultProtect;if(!m.exchange)m.exchange=DefaultExchange;return m;
}
template<class T> bool Read(const DailyFinalHookMemoryV1 &m,std::uintptr_t at,T &out) noexcept {
  return m.copy(m.context,reinterpret_cast<const void *>(at),&out,sizeof(out));
}
constexpr std::array<unsigned char,32> kEntry{
  0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8d,0x4c,0x24,0x38,0xe8,0x00,0xc1,0xd0,0xfd,
  0x48,0x8b,0x05,0xa1,0xaa,0xa3,0x03,0x48,0x8b,0x88,0xa0,0x00,0x00,0x00,0x48,0x81};
struct Col {std::uint32_t signature,offset,cd,type,hierarchy,self;};
bool ImageGuard(const DailyFinalHookBindingsV1 &b,const DailyFinalHookMemoryV1 &m) noexcept {
  constexpr char type_name[]=".?AVCDailyTickCommand@@";
  constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
  const auto base=b.module_base;
  if(!base || base>max-0x6FE5000 ||
      b.slot!=reinterpret_cast<DailyFinalOriginalV1 *>(base+kDailyFinalSlotRvaV1) ||
      Bits(b.expected_original)!=base+kDailyFinalFunctionRvaV1)return false;
  std::array<unsigned char,32> entry{};char name[sizeof(type_name)]{};
  Col primary{},secondary{};std::uintptr_t pc=0,sc=0,pre=0,execute=0,post=0,bridge=0;
  if(!m.copy(m.context,reinterpret_cast<void *>(base+kDailyFinalFunctionRvaV1),entry.data(),entry.size()) || entry!=kEntry ||
      !m.copy(m.context,reinterpret_cast<void *>(base+kDailyFinalTypeDescriptorRvaV1+16),name,sizeof(name)) ||
      std::memcmp(name,type_name,sizeof(name))!=0)return false;
  if(!Read(m,base+kDailyFinalPrimaryColRvaV1,primary) || !Read(m,base+kDailyFinalSecondaryColRvaV1,secondary) ||
      primary.signature!=1 || primary.offset!=0 || primary.type!=kDailyFinalTypeDescriptorRvaV1 ||
      primary.self!=kDailyFinalPrimaryColRvaV1 || primary.cd!=0 || secondary.cd!=0 ||
      primary.hierarchy!=0x51BE070 || secondary.signature!=1 || secondary.offset!=0x18 ||
      secondary.type!=kDailyFinalTypeDescriptorRvaV1 || secondary.self!=kDailyFinalSecondaryColRvaV1 ||
      primary.hierarchy!=secondary.hierarchy)return false;
  std::array<std::uint32_t,4> hierarchy{};
  if(!Read(m,base+0x51BE070,hierarchy) || hierarchy!=std::array<std::uint32_t,4>{0,1,7,0x51B8AC8})return false;
  return Read(m,base+kDailyFinalPrimaryVtableRvaV1-8,pc) && pc==base+kDailyFinalPrimaryColRvaV1 &&
      Read(m,base+kDailyFinalSecondaryVtableRvaV1-8,sc) && sc==base+kDailyFinalSecondaryColRvaV1 &&
      Read(m,base+kDailyFinalPrimaryVtableRvaV1+0x38,bridge) && bridge==base+0x8B27B0 &&
      Read(m,base+kDailyFinalSecondaryVtableRvaV1+8,execute) && execute==base+0x2E765F0 &&
      Read(m,base+kDailyFinalSecondaryVtableRvaV1+0x10,pre) && pre==base+0x2E766C0 &&
      Read(m,base+kDailyFinalSlotRvaV1,post) && post==base+kDailyFinalFunctionRvaV1;
}
DailyFinalHookResultV1 Result(DailyFinalHookStateV1 &s,DailyFinalHookResultV1 r) noexcept {
  s.last_result.store(r,std::memory_order_release);return r;
}
void Publish(DailyFinalHookStateV1 &s) noexcept {
  Exclusive gate(g_entry);g_fallback.store(s.bindings.expected_original,std::memory_order_release);g_active=&s;
}
bool DetachIfDrained(DailyFinalHookStateV1 &s,DailyFinalHookPhaseV1 phase) noexcept {
  Exclusive gate(g_entry);
  if(s.inflight.load(std::memory_order_acquire)!=0)return false;
  if(g_active==&s)g_active=nullptr;s.phase.store(phase,std::memory_order_release);return true;
}
bool Protect(DailyFinalHookStateV1 &s,std::uint32_t protection,std::uint32_t &old) noexcept {
  return s.memory.protect(s.memory.context,s.bindings.slot,sizeof(DailyFinalOriginalV1),protection,old);
}
bool RestoreProtection(DailyFinalHookStateV1 &s) noexcept {
  if(s.protection_restored)return true;
  std::uint32_t ignored=0;
  if(!Protect(s,s.original_protection,ignored))return false;
  s.protection_restored=true;return true;
}
DailyFinalHookResultV1 RestoreOwned(DailyFinalHookStateV1 &s) noexcept {
  if(!s.slot_published)
    return RestoreProtection(s)?DailyFinalHookResultV1::uninstalled:DailyFinalHookResultV1::protection_restore_failed;
  DailyFinalOriginalV1 current=nullptr;
  if(!s.memory.copy(s.memory.context,s.bindings.slot,&current,sizeof(current))) {
    // Restore our page protection even when the pointer cannot be inspected.
    return RestoreProtection(s)?DailyFinalHookResultV1::exchange_failed:DailyFinalHookResultV1::protection_restore_failed;
  }
  if(s.slot_restored || current!=&XarDailyFinalHook1210V1) {
    const bool original=s.slot_restored && current==s.bindings.expected_original;
    // A foreign pointer is never changed; our pending protection is still owed.
    if(!RestoreProtection(s))return DailyFinalHookResultV1::protection_restore_failed;
    return original?DailyFinalHookResultV1::uninstalled:DailyFinalHookResultV1::foreign_slot;
  }
  std::uint32_t ignored=0;
  if(!Protect(s,PAGE_READWRITE,ignored))return DailyFinalHookResultV1::protection_failed;
  s.protection_restored=false;
  DailyFinalOriginalV1 observed=nullptr;
  const bool exchanged=s.memory.exchange(s.memory.context,s.bindings.slot,
      s.bindings.expected_original,&XarDailyFinalHook1210V1,observed);
  if(exchanged && observed==&XarDailyFinalHook1210V1)s.slot_restored=true;
  const bool protected_back=Protect(s,s.original_protection,ignored);
  s.protection_restored=protected_back;
  if(!protected_back)return DailyFinalHookResultV1::protection_restore_failed;
  if(!exchanged)return DailyFinalHookResultV1::exchange_failed;
  return s.slot_restored?DailyFinalHookResultV1::uninstalled:DailyFinalHookResultV1::foreign_slot;
}
struct Entry {DailyFinalHookStateV1 *state=nullptr;DailyFinalOriginalV1 original=nullptr;};
Entry Enter() noexcept {
  AcquireSRWLockShared(&g_entry);
  Entry entry{g_active,g_fallback.load(std::memory_order_acquire)};
  if(entry.state) {
    entry.state->inflight.fetch_add(1,std::memory_order_acq_rel);
    entry.original=entry.state->bindings.expected_original;
  }
  ReleaseSRWLockShared(&g_entry);return entry;
}
void Leave(const Entry &entry) noexcept {
  if(entry.state)entry.state->inflight.fetch_sub(1,std::memory_order_acq_rel);
}
void Invoke(const Entry &entry) {
  if(!entry.original)std::terminate(); // Unpublished thunk is not a substitute final.
  entry.original(); // Never caught, swallowed, skipped or replaced.
  if(entry.state && entry.state->phase.load(std::memory_order_acquire)==DailyFinalHookPhaseV1::installed) {
    const auto callback=entry.state->callback.load(std::memory_order_acquire);
    if(callback)callback(entry.state->callback_context);
  }
}
} // namespace

DailyFinalHookBindingsV1 BindDailyFinalHookImageV1(std::uintptr_t base,std::string_view sha) noexcept {
  if(!base || sha!=kExecutableSha256 ||
      base>(std::numeric_limits<std::uintptr_t>::max)()-0x6FE5000)return {};
  return {DailyFinalBindingKindV1::exact_image,base,
      reinterpret_cast<DailyFinalOriginalV1 *>(base+kDailyFinalSlotRvaV1),
      Function(base+kDailyFinalFunctionRvaV1)};
}
DailyFinalHookBindingsV1 DailyFinalHookFixtureBindingsV1(DailyFinalOriginalV1 *slot,
    DailyFinalOriginalV1 original) noexcept {
  if(!slot || !original)return {};
  return {DailyFinalBindingKindV1::offline_fixture,0,slot,original};
}
DailyFinalHookResultV1 InstallDailyFinalHookV1(DailyFinalHookStateV1 &s,
    const DailyFinalHookBindingsV1 &b,const DailyFinalHookEnvironmentV1 &env,
    DailyFinalPostCallbackV1 callback,void *context) noexcept {
  Exclusive life(g_life);
  if(g_used || g_active || s.phase.load(std::memory_order_acquire)!=DailyFinalHookPhaseV1::idle)
    return Result(s,DailyFinalHookResultV1::already_installed);
  if(!b.slot || !b.expected_original || !callback || b.expected_original==&XarDailyFinalHook1210V1 ||
      reinterpret_cast<std::uintptr_t>(b.slot)%alignof(DailyFinalOriginalV1)!=0 ||
      (b.kind!=DailyFinalBindingKindV1::exact_image && b.kind!=DailyFinalBindingKindV1::offline_fixture))
    return Result(s,DailyFinalHookResultV1::invalid_request);
  if(!env.cold_quiescence_proven)return Result(s,DailyFinalHookResultV1::quiescence_required);
  const bool fixture=b.kind==DailyFinalBindingKindV1::offline_fixture;
  if(fixture && !env.allow_offline_fixture)return Result(s,DailyFinalHookResultV1::guard_failed);
  const auto memory=Memory(env.memory);
  if(!fixture && !ImageGuard(b,memory))return Result(s,DailyFinalHookResultV1::guard_failed);
  const auto fallback=g_fallback.load(std::memory_order_acquire);
  if(fallback && fallback!=b.expected_original)return Result(s,DailyFinalHookResultV1::invalid_state);
  DailyFinalOriginalV1 observed=nullptr;
  if(!memory.copy(memory.context,b.slot,&observed,sizeof(observed)))return Result(s,DailyFinalHookResultV1::guard_failed);
  if(observed!=b.expected_original)return Result(s,DailyFinalHookResultV1::foreign_slot);
  s.bindings=b;s.memory=memory;s.callback_context=context;s.fixture_only=fixture;s.image_guarded=!fixture;
  s.slot_restored=false;s.slot_published=false;s.protection_restored=true;s.callback.store(nullptr,std::memory_order_release);
  if(!Protect(s,PAGE_READWRITE,s.original_protection))return Result(s,DailyFinalHookResultV1::protection_failed);
  s.protection_restored=false;s.phase.store(DailyFinalHookPhaseV1::installing,std::memory_order_release);
  Publish(s);
  const bool exchanged=s.memory.exchange(s.memory.context,b.slot,&XarDailyFinalHook1210V1,b.expected_original,observed);
  s.slot_published=exchanged && observed==b.expected_original;
  std::uint32_t ignored=0;
  const bool protected_back=Protect(s,s.original_protection,ignored);s.protection_restored=protected_back;
  if(!exchanged || observed!=b.expected_original) {
    s.phase.store(DailyFinalHookPhaseV1::stopping,std::memory_order_release);
    // CAS failure has no write effect by the memory-seam contract.
    if(RestoreOwned(s)==DailyFinalHookResultV1::uninstalled && DetachIfDrained(s,DailyFinalHookPhaseV1::idle))
      return Result(s,exchanged?DailyFinalHookResultV1::foreign_slot:DailyFinalHookResultV1::exchange_failed);
    return Result(s,DailyFinalHookResultV1::rollback_failed);
  }
  if(!protected_back) {
    s.phase.store(DailyFinalHookPhaseV1::stopping,std::memory_order_release);
    const auto restored=RestoreOwned(s);
    if(restored==DailyFinalHookResultV1::uninstalled && DetachIfDrained(s,DailyFinalHookPhaseV1::idle))
      return Result(s,DailyFinalHookResultV1::protection_restore_failed);
    return Result(s,DailyFinalHookResultV1::rollback_failed);
  }
  s.callback.store(callback,std::memory_order_release);
  s.phase.store(DailyFinalHookPhaseV1::installed,std::memory_order_release);g_used=true;
  return Result(s,DailyFinalHookResultV1::installed);
}
DailyFinalHookResultV1 UninstallDailyFinalHookV1(DailyFinalHookStateV1 &s) noexcept {
  Exclusive life(g_life);
  const auto phase=s.phase.load(std::memory_order_acquire);
  if(g_active!=&s || (phase!=DailyFinalHookPhaseV1::installed && phase!=DailyFinalHookPhaseV1::stopping))
    return Result(s,DailyFinalHookResultV1::invalid_state);
  s.callback.store(nullptr,std::memory_order_release);
  s.phase.store(DailyFinalHookPhaseV1::stopping,std::memory_order_release);
  const auto restored=RestoreOwned(s);
  if(restored!=DailyFinalHookResultV1::uninstalled)return Result(s,restored);
  if(!DetachIfDrained(s,DailyFinalHookPhaseV1::uninstalled))return Result(s,DailyFinalHookResultV1::draining);
  return Result(s,DailyFinalHookResultV1::uninstalled);
}
DailyFinalHookStatusV1 ReadDailyFinalHookStatusV1(const DailyFinalHookStateV1 &s) noexcept {
  Exclusive life(g_life);DailyFinalHookStatusV1 out{};
  out.phase=s.phase.load(std::memory_order_acquire);out.last_result=s.last_result.load(std::memory_order_acquire);
  out.inflight=s.inflight.load(std::memory_order_acquire);out.callback_enabled=s.callback.load(std::memory_order_acquire)!=nullptr;
  out.slot_restored=s.slot_restored;out.protection_restored=s.protection_restored;
  out.image_guarded=s.image_guarded;out.fixture_only=s.fixture_only;
  return out;
}
extern "C" void __fastcall XarDailyFinalHook1210V1() {
  const auto entry=Enter();
#if defined(_MSC_VER)
  // __finally runs on native SEH and C++ unwinding without swallowing either.
  __try {Invoke(entry);} __finally {Leave(entry);}
#else
  try {Invoke(entry);} catch(...) {Leave(entry);throw;}
  Leave(entry);
#endif
}
} // namespace xar::ck3_1210

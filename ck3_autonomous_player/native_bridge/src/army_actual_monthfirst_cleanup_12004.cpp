#include "xar_bridge/army_actual_monthfirst_cleanup_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <mutex>
#include <unordered_map>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t,19> kDisplaced{
  0x48,0x89,0x5C,0x24,0x18,0x55,0x56,0x57,0x48,0x83,0xEC,0x20,
  0x48,0x8D,0xB9,0x68,0x04,0x00,0x00};
std::mutex g_mutex;
std::array<ArmyActualMonthfirstCleanupRecord12004,
           kArmyActualMonthfirstCleanupJournalCapacity12004> g_records{};
std::uint64_t g_latest = 0, g_unattributed = 0;
std::atomic<std::uint64_t> g_dropped{0};
std::atomic<ArmyActualMonthfirstCleanupDetourState12004 *> g_state{nullptr};
std::atomic<ArmyActualMonthfirstCleanupOriginal12004> g_original{nullptr};
ArmyActualMonthfirstCleanupBindings12004 g_binding;

template<class Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool DefaultRead(void *, std::uintptr_t address, void *output, std::size_t count) noexcept {
  if (!address) return false;
  return FaultBoundary([&]() noexcept {
    std::memcpy(output,reinterpret_cast<const void *>(address),count); return true;
  });
}
template<class T> std::optional<T> Read(const ArmyActualMonthfirstCleanupBindings12004 &b,
                                      std::uintptr_t address) {
  T value{};
  if (!address || !b.read || !FaultBoundary([&]() noexcept {
        return b.read(b.read_context,address,&value,sizeof(value));
      })) return std::nullopt;
  return value;
}
ArmyNaturalPhaseEvent12004 Stamp(const ArmyActualMonthfirstCleanupBindings12004 &b) noexcept {
  return b.next_event ? b.next_event(b.event_context) : NextArmyNaturalPhaseEvent12004();
}

struct Selection {
  ArmyActualMonthfirstCleanupSelection12004 kind = ArmyActualMonthfirstCleanupSelection12004::unavailable;
  std::optional<std::uintptr_t> object;
  std::optional<std::uint32_t> indexed_full, selected_full, magic;
  std::optional<bool> valid;
  bool complete = false;
};
Selection Resolve(const ArmyActualMonthfirstCleanupBindings12004 &b, std::uint32_t requested) {
  Selection out;
  const auto registry = Read<std::uintptr_t>(b,b.image_base+0x5D1EB68U);
  if (!registry) return out;
  if (*registry) {
    const auto count = Read<std::uint32_t>(b,*registry+0x2C);
    if (!count) return out;
    const auto index = requested & 0xFFFFFFU;
    if (index < *count) {
      const auto data = Read<std::uintptr_t>(b,*registry+0x20);
      if (!data || !*data) return out;
      const auto object = Read<std::uintptr_t>(b,*data+std::uintptr_t{16}*index+8);
      if (!object) return out;
      if (*object) {
        out.indexed_full = Read<std::uint32_t>(b,*object+0x10);
        if (!out.indexed_full) return out;
        if (*out.indexed_full == requested) {
          out.object = *object;
          out.kind = ArmyActualMonthfirstCleanupSelection12004::registry_full_generation;
        }
      }
    }
  }
  if (!out.object) {
    out.object = Read<std::uintptr_t>(b,b.image_base+0x5D1EB58U);
    out.kind = ArmyActualMonthfirstCleanupSelection12004::native_fallback;
    if (!out.object || !*out.object) return out;
  }
  out.magic = Read<std::uint32_t>(b,*out.object+0x14);
  if (!out.magic) return out;
  if (*out.magic != 0x52656769U) {
    out.valid = false; out.complete = true; return out;
  }
  out.selected_full = Read<std::uint32_t>(b,*out.object+0x10);
  if (!out.selected_full) return out;
  out.valid = *out.selected_full != 0xFFFFFFFFU;
  out.complete = true;
  return out;
}

ArmyActualMonthfirstCleanupFrame12004 Capture(const ArmyActualMonthfirstCleanupBindings12004 &b,
    std::uintptr_t primary, std::uintptr_t date,
    const ArmyActualMonthfirstCleanupFrame12004 *before) {
  ArmyActualMonthfirstCleanupFrame12004 out;
  out.primary_manager_identity = primary;
  out.header_identity = primary+0x468;
  out.passed_date_pointer_identity = date;
  out.passed_date_raw64 = Read<std::uint64_t>(b,date);
  out.buffer_identity = Read<std::uintptr_t>(b,out.header_identity);
  out.live_count_raw_i32 = Read<std::int32_t>(b,out.header_identity+0xC);
  out.header_complete = out.buffer_identity.has_value() && out.live_count_raw_i32.has_value();
  if (!out.header_complete) { out.unavailable_reason="cleanup_header_partial"; return out; }
  if (*out.live_count_raw_i32 < 0) { out.unavailable_reason="cleanup_negative_count_not_materialized"; return out; }
  auto extent = static_cast<std::size_t>(*out.live_count_raw_i32);
  if (before && before->buffer_identity) {
    out.original_backing_address_preserved = *out.buffer_identity == *before->buffer_identity;
    if (*out.original_backing_address_preserved && before->physical_copy_complete)
      extent=std::max(extent,before->copied_physical_extent);
  }
  if (extent > kArmyActualMonthfirstCleanupMaximumRecords12004) {
    out.truncated=true; out.unavailable_reason="cleanup_physical_extent_exceeds_bound"; return out;
  }
  if (extent && *out.buffer_identity==0) { out.unavailable_reason="cleanup_nonempty_buffer_null"; return out; }
  out.copied_physical_extent=extent;
  std::unordered_map<std::uint32_t,Selection> selections;
  std::unordered_map<std::uintptr_t,std::optional<std::uint64_t>> dates;
  bool complete=out.passed_date_raw64.has_value();
  for (std::size_t i=0;i<extent;++i) {
    ArmyActualMonthfirstCleanupSlot12004 slot;
    slot.physical_index=static_cast<std::int32_t>(i);
    slot.record_identity=*out.buffer_identity+i*16;
    slot.vtable_identity=Read<std::uintptr_t>(b,slot.record_identity);
    if (slot.vtable_identity && *slot.vtable_identity)
      slot.slot0_target_identity=Read<std::uintptr_t>(b,*slot.vtable_identity);
    if (slot.slot0_target_identity)
      slot.slot0_matches_known_mode0_source=*slot.slot0_target_identity==b.image_base+0x8863D0U;
    slot.requested_regi_full_id=Read<std::uint32_t>(b,slot.record_identity+8);
    slot.ordinal=Read<std::int32_t>(b,slot.record_identity+0xC);
    bool ready=slot.vtable_identity.has_value() && slot.slot0_target_identity.has_value() &&
        slot.requested_regi_full_id.has_value() && slot.ordinal.has_value();
    if (slot.requested_regi_full_id && slot.ordinal) {
      const auto requested=*slot.requested_regi_full_id;
      auto selected=selections.find(requested);
      if (selected==selections.end()) selected=selections.emplace(requested,Resolve(b,requested)).first;
      const auto &s=selected->second;
      slot.selection=s.kind; slot.selected_regi_identity=s.object;
      slot.indexed_regi_full_id=s.indexed_full; slot.selected_regi_full_id=s.selected_full;
      slot.selected_magic_14=s.magic; slot.selected_regi_valid=s.valid;
      ready=ready && s.complete;
      if (s.complete && s.valid && *s.valid && s.object) {
        const auto chunk=*s.object+std::uintptr_t{0x18}+
            static_cast<std::uintptr_t>(static_cast<std::int64_t>(*slot.ordinal)*36);
        slot.computed_chunk_identity=chunk;
        if (chunk) {
          auto found=dates.find(chunk);
          if (found==dates.end()) found=dates.emplace(chunk,Read<std::uint64_t>(b,chunk+0x1C)).first;
          slot.date_1c_raw64=found->second;
          ready=ready && slot.date_1c_raw64.has_value();
        }
      }
    }
    slot.complete=ready;
    if (!ready) slot.unavailable_reason="cleanup_physical_slot_or_source_materialization_partial";
    complete=complete && ready;
    out.physical_slots.push_back(std::move(slot));
  }
  out.physical_copy_complete=out.physical_slots.size()==extent;
  out.complete=complete && out.physical_copy_complete;
  if (!out.complete) out.unavailable_reason="cleanup_raw_frame_partial";
  return out;
}

bool EventPresent(const ArmyNaturalPhaseEvent12004 &e) {
  return e.clock_identity!=0 && e.sequence!=0 && e.thread_id && *e.thread_id!=0;
}
void CheckLineage(ArmyActualMonthfirstCleanupRecord12004 &r) {
  const auto &parent=r.phase.entry_event;
  if (!EventPresent(parent) || !EventPresent(r.before_event) ||
      !EventPresent(r.before_copied_event) || !EventPresent(r.returned_event) ||
      !EventPresent(r.after_copied_event)) return;
  bool same=true;
  auto last=parent.sequence;
  for (const auto *event : {&r.before_event,&r.before_copied_event,&r.returned_event,&r.after_copied_event}) {
    same=same && event->clock_identity==parent.clock_identity && event->thread_id==parent.thread_id &&
         event->sequence>last;
    last=event->sequence;
  }
  r.same_clock_thread_order=same;
}
void Publish(ArmyActualMonthfirstCleanupRecord12004 &r) noexcept {
  try {
    const std::lock_guard lock(g_mutex);
    if (!r.source_call_admitted) { ++g_unattributed; return; }
    const auto next=g_latest+1;
    r.journal_ordinal=next;
    g_records[(next-1)%g_records.size()]=r;
    g_latest=next;
  } catch (...) { r.capture_failure_flags|=1U<<4;g_dropped.fetch_add(1,std::memory_order_relaxed); }
}

void AbsoluteJump(std::uint8_t *destination,std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t,6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(destination,prefix.data(),prefix.size());
  std::memcpy(destination+prefix.size(),&target,sizeof(target));
}
void *DefaultAlloc(void *,std::size_t size,DWORD type,DWORD protection) noexcept {
  return VirtualAlloc(nullptr,size,type,protection);
}
bool DefaultFree(void *,void *address,std::size_t size,DWORD type) noexcept {
  return VirtualFree(address,size,type)!=FALSE;
}
bool DefaultProtect(void *,void *address,std::size_t size,DWORD protection,DWORD &old) noexcept {
  return VirtualProtect(address,size,protection,&old)!=FALSE;
}
bool DefaultFlush(void *,const void *address,std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(),address,size)!=FALSE;
}
void Fail(ArmyActualMonthfirstCleanupDetourState12004 &s,std::uint32_t flag) noexcept {
  s.failure_flags.fetch_or(flag,std::memory_order_acq_rel);
}
std::array<std::uint8_t,19> HookBytes() noexcept {
  std::array<std::uint8_t,19> bytes;
  bytes.fill(0x90);
  AbsoluteJump(bytes.data(),reinterpret_cast<std::uintptr_t>(&XarArmyActualMonthfirstCleanupHook12004));
  return bytes;
}
bool WritePatch(ArmyActualMonthfirstCleanupDetourState12004 &s,
    const std::array<std::uint8_t,19> &expected,const std::array<std::uint8_t,19> &desired) noexcept {
  auto *target=reinterpret_cast<void *>(s.callback_target);
  if (!FaultBoundary([&]() noexcept {return std::memcmp(target,expected.data(),expected.size())==0;})) {
    Fail(s,cleanup_install_anchor); return false;
  }
  DWORD old=0;
  if (!s.protect(s.memory_context,target,desired.size(),PAGE_EXECUTE_READWRITE,old)) {
    Fail(s,cleanup_install_protection); return false;
  }
  std::memcpy(target,desired.data(),desired.size());
  const bool flushed=s.flush(s.memory_context,target,desired.size());
  DWORD ignored=0;
  const bool restored=s.protect(s.memory_context,target,desired.size(),old,ignored);
  if (flushed && restored) return true;
  Fail(s,flushed ? cleanup_install_protection : cleanup_install_flush);
  DWORD rollback_old=0;
  const bool writable=s.protect(s.memory_context,target,expected.size(),PAGE_EXECUTE_READWRITE,rollback_old);
  if (writable) std::memcpy(target,expected.data(),expected.size());
  const bool rollback_flush=writable && s.flush(s.memory_context,target,expected.size());
  const bool rollback_restore=writable && s.protect(s.memory_context,target,expected.size(),old,ignored);
  if (!rollback_flush || !rollback_restore) Fail(s,cleanup_install_rollback);
  return false;
}
} // namespace

ArmyActualMonthfirstCleanupBindings12004 BindArmyActualMonthfirstCleanup12004(
    std::uintptr_t base,std::string_view sha) noexcept {
  ArmyActualMonthfirstCleanupBindings12004 out;
  if (!base || sha!=kExecutableSha256 ||
      base>std::numeric_limits<std::uintptr_t>::max()-0x5D1EB68U) return out;
  out.enabled=true; out.image_base=base; out.read=&DefaultRead;
  out.next_event=&NextArmyNaturalPhaseEvent12004;
  return out;
}

ArmyActualMonthfirstCleanupRecord12004 InvokeArmyActualMonthfirstCleanup12004(
    const ArmyActualMonthfirstCleanupBindings12004 &b,ArmyActualMonthfirstCleanupOriginal12004 original,
    void *primary,const void *date,std::uintptr_t caller_return_rva) noexcept {
  ArmyActualMonthfirstCleanupRecord12004 out;
  out.caller_return_rva=caller_return_rva;
  const auto identity=reinterpret_cast<std::uintptr_t>(primary);
  try {
    out.phase=CopyActiveArmyNaturalPhaseScope12004();
    out.source_call_admitted=b.enabled && out.phase.observed &&
        out.phase.phase==ArmyNaturalPhaseKind12004::post_date &&
        out.phase.actual_entry_rva==kArmyNaturalPostDateRva12004 &&
        caller_return_rva==kArmyActualMonthfirstCleanupReturnRva12004 && identity!=0 &&
        out.phase.primary_manager_identity==identity &&
        out.phase.secondary_manager_identity==identity+8;
    if (out.source_call_admitted) {
      out.saved_mask02_admitted_by_literal_call=true;
      (void)ObserveArmyNaturalPhaseSavedMask12004(identity+8,caller_return_rva,std::uint8_t{2});
      out.phase=CopyActiveArmyNaturalPhaseScope12004();
      out.before_event=Stamp(b);
      out.before=Capture(b,identity,reinterpret_cast<std::uintptr_t>(date),nullptr);
      out.before_copied_event=Stamp(b);
      if (out.phase.date_raw && out.before.passed_date_raw64)
        out.phase_date_matches_passed_date=*out.phase.date_raw==*out.before.passed_date_raw64;
      if (!out.before.complete) out.capture_failure_flags|=1U;
    } else out.capture_failure_flags|=1U<<2;
  } catch (...) { out.capture_failure_flags|=1U; }
  if (original) {
    out.original_called=true;
    out.raw_return_bits=original(primary,date);
    out.original_returned=true;
  } else out.capture_failure_flags|=1U<<3;
  try {
    if (out.source_call_admitted && out.original_returned) {
      out.returned_event=Stamp(b);
      out.after=Capture(b,identity,reinterpret_cast<std::uintptr_t>(date),&out.before);
      out.after_copied_event=Stamp(b);
      if (!out.after.complete) out.capture_failure_flags|=1U<<1;
      CheckLineage(out);
    }
    Publish(out);
  } catch (...) { out.capture_failure_flags|=1U<<1; }
  return out;
}

ArmyActualMonthfirstCleanupJournal12004 ReadArmyActualMonthfirstCleanupJournal12004() noexcept {
  ArmyActualMonthfirstCleanupJournal12004 out;
  out.dropped_record_copies=g_dropped.load(std::memory_order_relaxed);
  out.owned_copy_complete=out.dropped_record_copies==0;
  const auto *state=g_state.load(std::memory_order_acquire);
  out.observer_installed=state && state->installed.load(std::memory_order_acquire)!=0;
  try {
    const std::lock_guard lock(g_mutex);
    out.latest_ordinal=g_latest;
    out.oldest_available_ordinal=g_latest==0 ? 0 : g_latest<=g_records.size() ? 1 : g_latest-g_records.size()+1;
    out.overwritten_records=g_latest>g_records.size() ? g_latest-g_records.size() : 0;
    out.unattributed_invocations=g_unattributed;
    for (auto n=out.oldest_available_ordinal;n!=0 && n<=g_latest;++n) {
      const auto &record=g_records[(n-1)%g_records.size()];
      if (record.journal_ordinal==n) out.events.push_back(record);
    }
  } catch (...) {out.owned_copy_complete=false;}
  return out;
}
void ClearArmyActualMonthfirstCleanupJournalFixture12004() noexcept {
  if (g_state.load(std::memory_order_acquire)) return;
  try {const std::lock_guard lock(g_mutex);g_latest=0;g_unattributed=0;g_dropped.store(0);for(auto &r:g_records)r={};}
  catch (...) {}
}

bool InstallArmyActualMonthfirstCleanup12004(ArmyActualMonthfirstCleanupDetourState12004 &s,
    const ArmyActualMonthfirstCleanupInstallEnvironment12004 &e,std::string_view sha) noexcept {
  s.failure_flags.store(0,std::memory_order_relaxed);
  if (sha!=kExecutableSha256 || !e.bindings.enabled || !e.bindings.image_base) {
    Fail(s,cleanup_install_exact_build);return false;
  }
  if (!e.primary_thread_suspended_proven) {Fail(s,cleanup_install_quiescence);return false;}
  if (s.installed.load(std::memory_order_acquire)!=0) return true;
  ArmyActualMonthfirstCleanupDetourState12004 *empty=nullptr;
  if (!g_state.compare_exchange_strong(empty,&s,std::memory_order_acq_rel)) {
    Fail(s,cleanup_install_already_active);return false;
  }
  s.callback_target=e.callback_target_override ? e.callback_target_override :
      e.bindings.image_base+kArmyActualMonthfirstCleanupRva12004;
  s.memory_context=e.memory_context;s.free=e.free ? e.free : &DefaultFree;
  s.protect=e.protect ? e.protect : &DefaultProtect;s.flush=e.flush ? e.flush : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {return std::memcmp(reinterpret_cast<const void *>(s.callback_target),
      kDisplaced.data(),kDisplaced.size())==0;})) {
    Fail(s,cleanup_install_anchor);g_state.store(nullptr,std::memory_order_release);return false;
  }
  const auto allocate=e.allocate ? e.allocate : &DefaultAlloc;
  constexpr auto size=kArmyActualMonthfirstCleanupDisplacedBytes12004+std::size_t{14};
  s.trampoline=allocate(e.memory_context,size,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  if (!s.trampoline) {Fail(s,cleanup_install_allocation);g_state.store(nullptr,std::memory_order_release);return false;}
  auto *bytes=static_cast<std::uint8_t *>(s.trampoline);
  std::memcpy(bytes,kDisplaced.data(),kDisplaced.size());
  AbsoluteJump(bytes+kDisplaced.size(),s.callback_target+kDisplaced.size());
  DWORD old=0;
  const bool executable=s.protect(e.memory_context,s.trampoline,size,PAGE_EXECUTE_READ,old);
  const bool flushed=executable && s.flush(e.memory_context,s.trampoline,size);
  if (flushed) {
    g_binding=e.bindings;
    g_original.store(reinterpret_cast<ArmyActualMonthfirstCleanupOriginal12004>(s.trampoline),std::memory_order_release);
  }
  if (!executable || !flushed || !WritePatch(s,kDisplaced,HookBytes())) {
    if (!executable) Fail(s,cleanup_install_protection);else if(!flushed)Fail(s,cleanup_install_flush);
    // If rollback did not restore the target, retain executable backing and
    // original for process safety; Root sees failed install and aborts startup.
    if ((s.failure_flags.load(std::memory_order_acquire)&cleanup_install_rollback)==0) {
      g_original.store(nullptr,std::memory_order_release);
      (void)s.free(e.memory_context,s.trampoline,0,MEM_RELEASE);s.trampoline=nullptr;
      g_state.store(nullptr,std::memory_order_release);
    }
    return false;
  }
  s.original=kDisplaced;s.installed.store(1,std::memory_order_release);return true;
}

extern "C" std::uintptr_t __fastcall XarArmyActualMonthfirstCleanupHook12004(
    void *primary,const void *date) noexcept {
  const auto original=g_original.load(std::memory_order_acquire);
  if (!original) return 0;
#if defined(_MSC_VER)
  const auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller=reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva=caller>=g_binding.image_base ? caller-g_binding.image_base : 0;
  const auto record=InvokeArmyActualMonthfirstCleanup12004(g_binding,original,primary,date,rva);
  return record.raw_return_bits.value_or(0);
}
} // namespace xar::ck3_12004

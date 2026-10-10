#include "xar_bridge/conception_pair_provider_passive_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"
#include <algorithm>
#include <cstring>
#include <intrin.h>

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, 16> anchor{
    0x48,0x89,0x5C,0x24,0x08,0x55,0x56,0x57,
    0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
constexpr std::size_t jump_size = 14, trampoline_size = anchor.size() + jump_size;
ConceptionPairProviderBindings12004 binding;
std::atomic<ConceptionPairProviderOriginal12004> original{nullptr};
std::atomic<bool> installed{false};
SRWLOCK journal_lock = SRWLOCK_INIT;
std::array<ConceptionPairProviderObservation12004,
           kConceptionPairProviderJournalCapacity12004> journal{};
std::uint64_t next_sequence = 0, latest_sequence = 0;

bool NativeRead(void *, const void *source, void *output, std::size_t size) noexcept {
  if (source == nullptr || output == nullptr) return false;
  __try { std::memcpy(output, source, size); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
}
void *NativeAlloc(void *, std::size_t size, DWORD kind, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, kind, protection);
}
bool NativeFree(void *, void *address, std::size_t size, DWORD kind) noexcept {
  return VirtualFree(address, size, kind) != FALSE;
}
bool NativeProtect(void *, void *address, std::size_t size, DWORD protection,
                   DWORD &previous) noexcept {
  return VirtualProtect(address, size, protection, &previous) != FALSE;
}
bool NativeFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
PersonInstalledTransferEvent12004 NativeEvent(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
void Jump(std::uint8_t *bytes, std::uintptr_t target) noexcept {
  bytes[0]=0xFF; bytes[1]=0x25;
  std::memset(bytes+2,0,4);
  std::memcpy(bytes+6,&target,sizeof(target));
}
template<typename T> std::optional<T> Copy(std::uintptr_t address) noexcept {
  T value{};
  if (address == 0 || binding.read_memory == nullptr ||
      !binding.read_memory(binding.read_context,
          reinterpret_cast<const void *>(address), &value, sizeof(value))) return std::nullopt;
  return value;
}
bool SameParent(const ConceptionPairProviderParentScope12004 &a,
                const ConceptionPairProviderParentScope12004 &b) noexcept {
  return a.active && b.active && a.parent_scope_id==b.parent_scope_id &&
      a.thread_id==b.thread_id && a.process_clock==b.process_clock &&
      a.clock_identity==b.clock_identity && a.first_character==b.first_character &&
      a.second_character==b.second_character && a.first_full_id==b.first_full_id &&
      a.second_full_id==b.second_full_id && a.sample_receiver==b.sample_receiver;
}
void Publish(ConceptionPairProviderObservation12004 &record) noexcept {
  AcquireSRWLockExclusive(&journal_lock);
  record.journal_sequence=++next_sequence;
  ReleaseSRWLockExclusive(&journal_lock);
  if (binding.child_return != nullptr &&
      !binding.child_return(binding.child_return_context,record))
    record.capture_failure_flags|=conception_provider_capture_attach;
  AcquireSRWLockExclusive(&journal_lock);
  journal[static_cast<std::size_t>((record.journal_sequence-1)%journal.size())]=record;
  latest_sequence=std::max(latest_sequence,record.journal_sequence);
  ReleaseSRWLockExclusive(&journal_lock);
}
void *Invoke(std::uintptr_t caller_pc, std::uintptr_t caller_rva,
             void *output, void *first, void *second,
             std::uint32_t mode, void *fifth) noexcept {
  const auto native=original.load(std::memory_order_acquire);
  if (native==nullptr) return nullptr; // No installed hook can admit this state.
  ConceptionPairProviderParentScope12004 parent;
  const auto thread=GetCurrentThreadId();
  const bool eligible=binding.enabled &&
      caller_rva==kConceptionPairProviderReturnRva12004 && mode==3 && fifth==nullptr &&
      binding.read_parent!=nullptr &&
      binding.read_parent(binding.parent_context,parent) && parent.active &&
      parent.parent_scope_id!=0 && parent.clock_identity!=0 && parent.thread_id==thread &&
      parent.first_character==reinterpret_cast<std::uintptr_t>(first) &&
      parent.second_character==reinterpret_cast<std::uintptr_t>(second);
  if (!eligible) return native(output,first,second,mode,fifth);
  ConceptionPairProviderObservation12004 record;
  record.parent=parent;
  record.process_id=GetCurrentProcessId(); record.thread_id=thread;
  record.caller_return_pc=caller_pc; record.caller_return_rva=caller_rva;
  record.output_pointer=reinterpret_cast<std::uintptr_t>(output);
  record.first_character=reinterpret_cast<std::uintptr_t>(first);
  record.second_character=reinterpret_cast<std::uintptr_t>(second);
  record.mode=mode; record.fifth_argument=reinterpret_cast<std::uintptr_t>(fifth);
  if (binding.next_event!=nullptr) record.before_event=binding.next_event(binding.event_context);
  record.output_before=Copy<std::int64_t>(record.output_pointer);
  record.first_full_id_before=Copy<std::uint32_t>(record.first_character+0x18);
  record.second_full_id_before=Copy<std::uint32_t>(record.second_character+0x18);
  if (!record.output_before) record.capture_failure_flags|=conception_provider_capture_output_before;
  if (!record.first_full_id_before || !record.second_full_id_before)
    record.capture_failure_flags|=conception_provider_capture_identity_before;
  void *returned=native(output,first,second,mode,fifth);
  record.native_return_bits=reinterpret_cast<std::uintptr_t>(returned);
  record.original_returned=true;
  record.native_return_matches_output=returned==output;
  record.output_after=Copy<std::int64_t>(record.output_pointer);
  record.first_full_id_after=Copy<std::uint32_t>(record.first_character+0x18);
  record.second_full_id_after=Copy<std::uint32_t>(record.second_character+0x18);
  if (binding.next_event!=nullptr) record.returned_event=binding.next_event(binding.event_context);
  if (!record.output_after) record.capture_failure_flags|=conception_provider_capture_output_after;
  if (!record.first_full_id_after || !record.second_full_id_after)
    record.capture_failure_flags|=conception_provider_capture_identity_after;
  ConceptionPairProviderParentScope12004 after;
  record.parent_extent_unchanged=binding.read_parent(binding.parent_context,after) && SameParent(parent,after);
  if (!record.parent_extent_unchanged)
    record.capture_failure_flags|=conception_provider_capture_parent_changed;
  record.event_clock_and_thread_match=record.before_event.clock_identity==parent.clock_identity &&
      record.returned_event.clock_identity==parent.clock_identity &&
      record.before_event.thread_id==parent.thread_id &&
      record.returned_event.thread_id==parent.thread_id &&
      record.before_event.sequence>parent.process_clock &&
      record.returned_event.sequence>record.before_event.sequence;
  if (!record.event_clock_and_thread_match)
    record.capture_failure_flags|=conception_provider_capture_event_coordinate;
  record.actual_caller_input_ready=record.original_returned && record.output_after.has_value() &&
      record.parent_extent_unchanged && record.event_clock_and_thread_match;
  Publish(record);
  return returned;
}
bool ValidBinding(const ConceptionPairProviderBindings12004 &b) noexcept {
  return b.enabled && b.image_base!=0 && b.read_memory!=nullptr &&
      b.read_parent!=nullptr && b.next_event!=nullptr && b.child_return!=nullptr;
}
void ResetJournal() noexcept {
  AcquireSRWLockExclusive(&journal_lock);
  journal={}; next_sequence=latest_sequence=0;
  ReleaseSRWLockExclusive(&journal_lock);
}
} // namespace

ConceptionPairProviderBindings12004 BindConceptionPairProviderImage12004(
    std::uintptr_t image_base, std::string_view sha) noexcept {
  if (image_base==0 || sha!=kConceptionPairProviderSourcePin12004) return {};
  ConceptionPairProviderBindings12004 b;
  b.enabled=true; b.image_base=image_base; b.read_memory=NativeRead; b.next_event=NativeEvent;
  return b;
}

bool InstallConceptionPairProviderPassive12004(
    ConceptionPairProviderDetourState12004 &state,
    const ConceptionPairProviderInstallEnvironment12004 &env,
    std::string_view sha) noexcept {
  auto Fail=[&](std::uint32_t flag) noexcept {
    state.failure_flags.fetch_or(flag,std::memory_order_relaxed); return false;
  };
  if (sha!=kConceptionPairProviderSourcePin12004 || !env.bindings.enabled)
    return Fail(conception_provider_install_exact_build);
  if (!env.primary_thread_suspended_proven) return Fail(conception_provider_install_quiescence);
  if (!ValidBinding(env.bindings)) return Fail(conception_provider_install_binding);
  if (state.installed.load()!=0 || installed.load())
    return Fail(conception_provider_install_already_installed);
  auto *target=reinterpret_cast<std::uint8_t *>(env.bindings.image_base+kConceptionPairProviderRva12004);
  std::array<std::uint8_t,anchor.size()> actual{};
  if (!env.bindings.read_memory(env.bindings.read_context,target,actual.data(),actual.size()) || actual!=anchor)
    return Fail(conception_provider_install_anchor);
  const auto allocate=env.virtual_alloc_override ? env.virtual_alloc_override : NativeAlloc;
  const auto release=env.virtual_free_override ? env.virtual_free_override : NativeFree;
  const auto protect=env.virtual_protect_override ? env.virtual_protect_override : NativeProtect;
  const auto flush=env.flush_instruction_cache_override ? env.flush_instruction_cache_override : NativeFlush;
  auto *trampoline=static_cast<std::uint8_t *>(allocate(env.memory_context,trampoline_size,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if (trampoline==nullptr) return Fail(conception_provider_install_allocation);
  std::memcpy(trampoline,actual.data(),actual.size());
  Jump(trampoline+actual.size(),reinterpret_cast<std::uintptr_t>(target)+actual.size());
  DWORD old_trampoline=0;
  if (!protect(env.memory_context,trampoline,trampoline_size,PAGE_EXECUTE_READ,old_trampoline)) {
    release(env.memory_context,trampoline,0,MEM_RELEASE);
    return Fail(conception_provider_install_protection);
  }
  if (!flush(env.memory_context,trampoline,trampoline_size)) {
    release(env.memory_context,trampoline,0,MEM_RELEASE);
    return Fail(conception_provider_install_flush);
  }
  DWORD old_target=0;
  if (!protect(env.memory_context,target,actual.size(),PAGE_EXECUTE_READWRITE,old_target)) {
    release(env.memory_context,trampoline,0,MEM_RELEASE);
    return Fail(conception_provider_install_protection);
  }
  binding=env.bindings;
  original.store(reinterpret_cast<ConceptionPairProviderOriginal12004>(trampoline),std::memory_order_release);
  std::array<std::uint8_t,anchor.size()> patch{};
  patch.fill(0x90);
  const auto callback=env.callback_target_override ? env.callback_target_override :
      reinterpret_cast<std::uintptr_t>(&XarConceptionPairProviderHook12004);
  Jump(patch.data(),callback); std::memcpy(target,patch.data(),patch.size());
  DWORD ignored=0;
  const bool restored=protect(env.memory_context,target,patch.size(),old_target,ignored);
  const bool flushed=flush(env.memory_context,target,patch.size());
  if (!restored || !flushed) {
    state.failure_flags.fetch_or(!restored ? conception_provider_install_protection :
        conception_provider_install_flush,std::memory_order_relaxed);
    DWORD rollback_old=0;
    const bool writable=protect(env.memory_context,target,actual.size(),PAGE_EXECUTE_READWRITE,rollback_old);
    bool rollback_ok=false;
    if (writable) {
      std::memcpy(target,actual.data(),actual.size());
      DWORD rollback_ignored=0;
      const bool protection_ok=protect(env.memory_context,target,actual.size(),old_target,rollback_ignored);
      const bool cache_ok=flush(env.memory_context,target,actual.size());
      rollback_ok=protection_ok && cache_ok;
    }
    if (!rollback_ok) {
      state.failure_flags.fetch_or(conception_provider_install_rollback,std::memory_order_relaxed);
      state.trampoline=trampoline; state.original=actual; state.callback_target=callback;
      state.memory_context=env.memory_context; state.virtual_free=release;
      state.virtual_protect=protect; state.flush_instruction_cache=flush;
      state.installed.store(1); installed.store(true);
      return false; // Retain any potentially reachable trampoline.
    }
    original.store(nullptr); binding={};
    release(env.memory_context,trampoline,0,MEM_RELEASE);
    return false;
  }
  state.trampoline=trampoline; state.original=actual; state.callback_target=callback;
  state.memory_context=env.memory_context; state.virtual_free=release;
  state.virtual_protect=protect; state.flush_instruction_cache=flush;
  state.failure_flags.store(0); state.installed.store(1); installed.store(true);
  return true;
}

bool UninstallConceptionPairProviderPassive12004(
    ConceptionPairProviderDetourState12004 &state, bool suspended) noexcept {
  if (!suspended || state.installed.load()==0 || state.virtual_protect==nullptr ||
      state.flush_instruction_cache==nullptr || state.virtual_free==nullptr) return false;
  auto *target=reinterpret_cast<void *>(binding.image_base+kConceptionPairProviderRva12004);
  DWORD previous=0;
  if (!state.virtual_protect(state.memory_context,target,state.original.size(),PAGE_EXECUTE_READWRITE,previous)) return false;
  std::memcpy(target,state.original.data(),state.original.size());
  DWORD ignored=0;
  const bool protection_ok=state.virtual_protect(state.memory_context,target,state.original.size(),previous,ignored);
  const bool cache_ok=state.flush_instruction_cache(state.memory_context,target,state.original.size());
  if (!protection_ok || !cache_ok) return false;
  original.store(nullptr); binding={}; installed.store(false); state.installed.store(0);
  const bool released=state.virtual_free(state.memory_context,state.trampoline,0,MEM_RELEASE);
  if (released) state.trampoline=nullptr;
  return released;
}

std::optional<ConceptionPairProviderObservations12004> ReadConceptionPairProviderObservations12004(
    std::uintptr_t clock, std::uint64_t scope) noexcept {
  if ((clock==0)!=(scope==0)) return std::nullopt;
  try {
    ConceptionPairProviderObservations12004 result;
    result.observer_installed=installed.load();
    result.events.reserve(journal.size());
    AcquireSRWLockShared(&journal_lock);
    result.latest_sequence=latest_sequence;
    result.oldest_available_sequence=latest_sequence==0 ? 0 :
        (latest_sequence>journal.size() ? latest_sequence-journal.size()+1 : 1);
    result.overwritten_events=latest_sequence>journal.size() ? latest_sequence-journal.size() : 0;
    for (std::uint64_t sequence=result.oldest_available_sequence;
         sequence!=0 && sequence<=latest_sequence; ++sequence) {
      const auto &record=journal[static_cast<std::size_t>((sequence-1)%journal.size())];
      if (record.journal_sequence==sequence &&
          (clock==0 || (record.parent.clock_identity==clock && record.parent.parent_scope_id==scope)))
        result.events.push_back(record);
    }
    ReleaseSRWLockShared(&journal_lock);
    return result;
  } catch (...) { return std::nullopt; }
}

extern "C" __declspec(noinline) void *__fastcall XarConceptionPairProviderHook12004(
    void *output, void *first, void *second, std::uint32_t mode, void *fifth) noexcept {
  const auto pc=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto rva=pc>=binding.image_base ? pc-binding.image_base : 0;
  return Invoke(pc,rva,output,first,second,mode,fifth);
}
bool InitializeConceptionPairProviderFixture12004(
    const ConceptionPairProviderBindings12004 &b, ConceptionPairProviderOriginal12004 native) noexcept {
  if (installed.load() || !ValidBinding(b) || native==nullptr) return false;
  binding=b; original.store(native); ResetJournal(); return true;
}
void *InvokeConceptionPairProviderFixture12004(
    std::uintptr_t rva, void *output, void *first, void *second,
    std::uint32_t mode, void *fifth) noexcept {
  return Invoke(binding.image_base+rva,rva,output,first,second,mode,fifth);
}
} // namespace xar::ck3_12004

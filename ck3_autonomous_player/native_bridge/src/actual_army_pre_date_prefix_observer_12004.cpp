#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include <cstring>
#include <limits>
#include <mutex>
#include <utility>
#if defined(_MSC_VER)
#include <intrin.h>
#endif
namespace xar::ck3_12004 {
namespace {
bool MatchesStartupExecutableSha(std::string_view actual) noexcept {
  // Digest identity is independent of hexadecimal letter case.
  // Keep the source/wire constant spelling unchanged.
  const std::string_view expected = kActualArmyPreDatePrefixSha12004;
  if (actual.size() != expected.size()) return false;
  for (std::size_t i = 0; i < actual.size(); ++i) {
    char digit = actual[i];
    if (digit >= 'A' && digit <= 'F') digit = static_cast<char>(digit - 'A' + 'a');
    if (digit != expected[i]) return false;
  }
  return true;
}
// Five whole instructions, 17B; no relative or RIP operand. Resume 2A9A351.
constexpr std::array<std::uint8_t,17> kCallbackPrologue{
  0x40,0x53,0x41,0x54,0x41,0x55,0x48,0x83,0xEC,0x40,0x4C,0x63,0xA1,0xD4,0,0,0};
using Event=ActualArmyPreDatePrefixObservation12004;
ActualArmyPreDatePrefixBindings12004 g_bindings{};
std::atomic<ActualArmyPreDatePrefixOriginal12004> g_original{nullptr};
std::atomic<ActualArmyPreDatePrefixDetourState12004 *> g_active_state{nullptr};
std::atomic<bool> g_available{false},g_fixture_mode{false};
std::array<Event,kActualArmyPreDatePrefixJournalCapacity12004> g_slots{};
std::mutex g_mutex;
std::uint64_t g_latest=0;
std::atomic<std::uint64_t> g_failures{0};
template<class Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool ReadMemory(std::uintptr_t address,void *out,std::size_t bytes) noexcept {
  if(!address || address>(std::numeric_limits<std::uintptr_t>::max)()-bytes)return false;
  return FaultBoundary([&]() noexcept {
    if(g_bindings.read_memory)return g_bindings.read_memory(g_bindings.read_context,reinterpret_cast<const void *>(address),out,bytes);
    std::memcpy(out,reinterpret_cast<const void *>(address),bytes);return true;
  });
}
template<class T> std::optional<T> Read(std::uintptr_t base,std::size_t offset=0) noexcept {
  if(!base || base>(std::numeric_limits<std::uintptr_t>::max)()-offset)return std::nullopt;
  T value{};if(!ReadMemory(base+offset,&value,sizeof value))return std::nullopt;return value;
}
ActualArmyPreDatePrefixQueue12004 Queue(std::uintptr_t primary,std::size_t offset) {
  ActualArmyPreDatePrefixQueue12004 out{};
  out.data_identity=Read<std::uintptr_t>(primary,offset);
  out.capacity=Read<std::int32_t>(primary,offset+8);
  out.count=Read<std::int32_t>(primary,offset+12);
  if(!out.data_identity || !out.capacity || !out.count)return out;
  const bool valid=*out.count>=0 && *out.capacity>=0 && *out.count<=*out.capacity &&
    static_cast<std::size_t>(*out.capacity)<=(std::numeric_limits<std::uintptr_t>::max)()/4 &&
    *out.data_identity<=(std::numeric_limits<std::uintptr_t>::max)()-static_cast<std::uintptr_t>(*out.count>=0?*out.count:0)*4 &&
    (!*out.count || *out.data_identity);
  out.bounds_valid=valid;if(!valid)return out;
  out.copy_bound_admitted=static_cast<std::size_t>(*out.count)<=g_bindings.maximum_copied_occurrences;
  if(!*out.copy_bound_admitted)return out;
  const auto bytes=static_cast<std::size_t>(*out.count)*4;
  out.end_identity=*out.data_identity+bytes;
  out.ordered_full_ids.resize(static_cast<std::size_t>(*out.count));
  out.copied_complete=!bytes || ReadMemory(*out.data_identity,out.ordered_full_ids.data(),bytes);
  if(!out.copied_complete)out.ordered_full_ids.clear();
  return out;
}
ActualArmyPreDatePrefixSnapshot12004 Capture(std::uintptr_t primary,std::uintptr_t date,std::uintptr_t state) {
  ActualArmyPreDatePrefixSnapshot12004 out{};
  out.source_c8=Queue(primary,0xC8);out.destination_158=Queue(primary,0x158);
  out.supplied_date_raw_u64=Read<std::uint64_t>(date);
  out.game_date_raw_u64=Read<std::uint64_t>(state,8);
  out.absolute_day_raw_u32=Read<std::uint32_t>(state,0x9C);
  out.calendar_c0_raw_u8=Read<std::uint8_t>(state,0xC0);
  if(out.source_c8.count)out.conditional_no_work_arm=*out.source_c8.count<=0;
  return out;
}
bool SameThreadOrder(const ArmyNaturalPhaseEvent12004 &parent,const ArmyNaturalPhaseEvent12004 &child) noexcept {
  return parent.clock_identity && parent.clock_identity==child.clock_identity && parent.thread_id &&
    parent.thread_id==child.thread_id && parent.sequence<child.sequence;
}
bool InitializeRuntime(const ActualArmyPreDatePrefixBindings12004 &b,ActualArmyPreDatePrefixOriginal12004 original) noexcept {
  if(!b.enabled || !b.image_base || !original)return false;
  g_bindings=b;g_original.store(original,std::memory_order_release);g_available.store(true,std::memory_order_release);return true;
}
void Publish(Event &event) noexcept {
  try {std::lock_guard<std::mutex> lock(g_mutex);event.sequence=++g_latest;g_slots[(event.sequence-1)%g_slots.size()]=event;}
  catch(...) {++g_failures;}
}
std::uint64_t Observe(std::uintptr_t return_rva,const void *manager,const void *date,std::uint64_t incoming_rax) noexcept {
  const auto original=g_original.load(std::memory_order_acquire);if(!original)return incoming_rax;
  if(return_rva!=kActualArmyPreDatePrefixReturnRva12004)return original(manager,date,incoming_rax);
  Event event{};event.primary_manager_identity=reinterpret_cast<std::uintptr_t>(manager);
  event.date_argument_identity=reinterpret_cast<std::uintptr_t>(date);event.caller_return_rva=return_rva;event.incoming_rax_raw_u64=incoming_rax;
  try {
    event.parent=CopyActiveArmyNaturalPhaseScope12004();event.entry_event=NextArmyNaturalPhaseEvent12004();
    event.parent_bound=event.parent.observed && event.parent.phase==ArmyNaturalPhaseKind12004::pre_date &&
      event.parent.actual_entry_rva==kArmyNaturalPreDateRva12004 && event.parent.primary_manager_identity==event.primary_manager_identity &&
      SameThreadOrder(event.parent.entry_event,event.entry_event);
    if(!event.parent_bound)event.capture_failure_flags|=1U;
    event.before=Capture(event.primary_manager_identity,event.date_argument_identity,event.parent.game_state_identity);
    if(!event.before.source_c8.count || !event.before.destination_158.count)event.capture_failure_flags|=2U;
  }catch(...){event.capture_failure_flags|=8U;}
  // The observation exception boundary never catches, retries, or synthesizes
  // the naturally executing original. Its opaque return always wins.
  event.original_called=true;
  const auto returned=original(manager,date,incoming_rax);
  event.original_returned=true;event.original_rax_raw_u64=returned;
  // This literal edge occurs before parent caller resumes at its roster loads.
  event.original_roster_capture_complete=ObserveArmyNaturalPhaseOriginalRoster12004(
    event.primary_manager_identity,return_rva,event.before.supplied_date_raw_u64);
  try {
    event.returned_event=NextArmyNaturalPhaseEvent12004();
    const auto after_parent=CopyActiveArmyNaturalPhaseScope12004();
    if(after_parent.primary_manager_identity==event.primary_manager_identity &&
       after_parent.original_army_roster.boundary==ArmyNaturalRosterBoundary12004::pre_date_prefix_return &&
       after_parent.original_army_roster.capture_rva==return_rva)
      event.captured_original_roster=after_parent.original_army_roster;
    event.after=Capture(event.primary_manager_identity,event.date_argument_identity,event.parent.game_state_identity);
    if(!event.after.source_c8.count || !event.after.destination_158.count)event.capture_failure_flags|=4U;
    if(!event.original_roster_capture_complete)event.capture_failure_flags|=16U;
    Publish(event);
  }catch(...){/* Copy failure does not alter original RAX. */}
  return returned;
}
void WriteAbsoluteJump(std::uint8_t *output,std::uintptr_t destination) noexcept {
  output[0]=0xFF;output[1]=0x25;std::memset(output+2,0,4);std::memcpy(output+6,&destination,sizeof destination);
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
void *DefaultAlloc(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
void Fail(ActualArmyPreDatePrefixDetourState12004 &state,
          ActualArmyPreDatePrefixInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualArmyPreDatePrefixDetourState12004 &state,
                const std::array<std::uint8_t, kActualArmyPreDatePrefixPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualArmyPreDatePrefixPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_army_prefix_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_army_prefix_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_army_prefix_install_protection
                     : actual_army_prefix_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_army_prefix_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualArmyPreDatePrefixPatchBytes12004>
HookPatch(const ActualArmyPreDatePrefixDetourState12004 &state) noexcept {
  std::array<std::uint8_t, kActualArmyPreDatePrefixPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(state.trampoline) +
      kActualArmyPreDatePrefixPatchBytes12004 + 14 + 17);
  return patch;
}

} // namespace
bool InstallActualArmyPreDatePrefixObserver12004(
    ActualArmyPreDatePrefixDetourState12004 &state,
    const ActualArmyPreDatePrefixInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0) {
    // A retained failed rollback cannot become a successful installation by
    // resetting flags on a second call. Startup installation owns this state.
    return state.failure_flags.load(std::memory_order_acquire) == 0 &&
        g_active_state.load(std::memory_order_acquire) == &state &&
        environment.primary_thread_suspended_proven && environment.bindings.enabled &&
        environment.bindings.image_base == g_bindings.image_base &&
        MatchesStartupExecutableSha(executable_sha256);
  }
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (!MatchesStartupExecutableSha(executable_sha256) || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_army_prefix_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_army_prefix_install_quiescence);
    return false;
  }
  ActualArmyPreDatePrefixDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_army_prefix_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualArmyPreDatePrefixRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.callback_target),
                            kCallbackPrologue.data(), kCallbackPrologue.size()) == 0;
      })) {
    Fail(state, actual_army_prefix_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualArmyPreDatePrefixPatchBytes12004 +
      14 +
      34;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_army_prefix_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kCallbackPrologue.data(), kCallbackPrologue.size());
  WriteAbsoluteJump(bytes + kCallbackPrologue.size(),
                    state.callback_target + kCallbackPrologue.size());
  // Original-call thunk restores source-visible entry RAX before JMP.
  // Entry thunk saves RAX before C++ runs, retaining the real return address.
  auto *entry = bytes + kActualArmyPreDatePrefixPatchBytes12004 +
      14;
  constexpr std::array<std::uint8_t, 3> capture{0x4C,0x89,0xC0};
  std::memcpy(entry, capture.data(), capture.size()); // RAX=R8 before original
  WriteAbsoluteJump(entry + capture.size(), reinterpret_cast<std::uintptr_t>(state.trampoline));
  entry += 17;
  constexpr std::array<std::uint8_t,3> save_rax{0x49,0x89,0xC0};
  std::memcpy(entry,save_rax.data(),save_rax.size());
  WriteAbsoluteJump(entry + capture.size(), reinterpret_cast<std::uintptr_t>(
      &XarActualArmyPreDatePrefixHook12004));
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  g_fixture_mode.store(false,std::memory_order_release);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualArmyPreDatePrefixOriginal12004>(bytes + kActualArmyPreDatePrefixPatchBytes12004 + 14));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch(state))) {
    if (!executable) Fail(state, actual_army_prefix_install_protection);
    else if (!flushed) Fail(state, actual_army_prefix_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         actual_army_prefix_install_rollback) != 0) {
      state.original = kCallbackPrologue;
      state.installed.store(1, std::memory_order_release);
      return false; // Keep trampoline/forwarding intact for explicit recovery.
    }
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kCallbackPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}


std::optional<ActualArmyPreDatePrefixObservations12004> ReadActualArmyPreDatePrefixObservations12004(std::uintptr_t primary) noexcept {
  try {
    std::lock_guard<std::mutex> lock(g_mutex);ActualArmyPreDatePrefixObservations12004 out{};
    const auto *state=g_active_state.load(std::memory_order_acquire);
    out.observer_installed=g_available.load(std::memory_order_acquire) && (g_fixture_mode.load() || (state && state->installed.load()!=0 && state->failure_flags.load()==0));
    out.current_session_guard=g_bindings.enabled && g_bindings.image_base!=0;
    out.latest_sequence=g_latest;out.oldest_available_sequence=g_latest?g_latest<=g_slots.size()?1:g_latest-g_slots.size()+1:0;
    out.overwritten_events=g_latest>g_slots.size()?g_latest-g_slots.size():0;out.unattributed_capture_failures=g_failures.load();
    for(auto n=out.oldest_available_sequence;n && n<=g_latest;++n){const auto &e=g_slots[(n-1)%g_slots.size()];if(e.sequence==n && primary && e.primary_manager_identity==primary)out.events.push_back(e);}
    return out;
  }catch(...){return std::nullopt;}
}
ActualArmyPreDatePrefixBindings12004 BindActualArmyPreDatePrefixImage12004(std::uintptr_t image,std::string_view sha) noexcept {
  ActualArmyPreDatePrefixBindings12004 out{};out.enabled=image && MatchesStartupExecutableSha(sha);out.image_base=out.enabled?image:0;return out;
}
bool InitializeActualArmyPreDatePrefixFixture12004(const ActualArmyPreDatePrefixBindings12004 &b,ActualArmyPreDatePrefixOriginal12004 original) noexcept {
  if(g_active_state.load()!=nullptr)return false;
  if(!InitializeRuntime(b,original))return false;
  try {std::lock_guard<std::mutex> lock(g_mutex);g_latest=0;g_failures=0;for(auto &e:g_slots)e={};}
  catch(...){return false;}
  g_fixture_mode.store(true);return true;
}
std::uint64_t InvokeActualArmyPreDatePrefixFixture12004(std::uintptr_t rva,const void *manager,const void *date,std::uint64_t incoming_rax) noexcept {
  return Observe(rva,manager,date,incoming_rax);
}
extern "C" std::uint64_t __fastcall XarActualArmyPreDatePrefixHook12004(const void *manager,const void *date,std::uint64_t incoming_rax) noexcept {
#if defined(_MSC_VER)
  const auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller=reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva=g_bindings.image_base && caller>=g_bindings.image_base?caller-g_bindings.image_base:0;
  return Observe(rva,manager,date,incoming_rax);
}
} // namespace xar::ck3_12004

#include "xar_bridge/actual_army_assault_placement_observer_12004.hpp"
#include "xar_bridge/army_daily_assault_active_table_collector_v1.inc.hpp"
#include <cstring>
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
  const std::string_view expected = kDailyAssaultPreparationExecutableSha256;
  if (actual.size() != expected.size()) return false;
  for (std::size_t i = 0; i < actual.size(); ++i) {
    char digit = actual[i];
    if (digit >= 'A' && digit <= 'F') digit = static_cast<char>(digit - 'A' + 'a');
    if (digit != expected[i]) return false;
  }
  return true;
}
constexpr std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004>
    kCallbackPrologue{0x48,0x89,0x5C,0x24,0x10,0x55,0x56,0x57,0x41,0x56,
                      0x41,0x57,0x48,0x81,0xEC,0x80,0x00,0x00,0x00};
using Event = ActualArmyAssaultPlacementObservation12004;
using TableBindings = ck3_12003::CurrentDailyAssaultTableBindings12003;
struct JournalSlot { std::uint64_t sequence = 0; Event event{}; };
std::array<JournalSlot, kActualArmyAssaultPlacementJournalCapacity12004> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0, g_unattributed_failures = 0;
std::atomic<bool> g_fixture_mode{false}, g_available{false};
ActualArmyAssaultPlacementBindings12004 g_bindings{};
std::atomic<ActualArmyAssaultPlacementOriginal12004> g_original{nullptr};
std::atomic<ActualArmyAssaultPlacementDetourState12004 *> g_active_state{nullptr};

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool ReadMemory(const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output) return false;
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory) return g_bindings.read_memory(g_bindings.read_context,address,output,size);
    std::memcpy(output,address,size); return true;
  });
}
template <typename T> std::optional<T> ReadAt(std::uintptr_t base, std::size_t offset=0) noexcept {
  if (!base || offset>UINTPTR_MAX-base) return std::nullopt;
  T value{};
  return ReadMemory(reinterpret_cast<const void *>(base+offset),&value,sizeof(value)) ? std::optional<T>{value} : std::nullopt;
}
struct CaptureBudget {
  ActualArmyAssaultPlacementSnapshot12004 *out = nullptr;
  std::uintptr_t entries = 0;
};
bool CollectorRead(void *context,const void *address,void *output,std::size_t size) noexcept {
  auto &budget=*static_cast<CaptureBudget *>(context); auto &out=*budget.out;
  if (out.read_calls>=16384 || size>262144-out.read_bytes) { out.budget_exhausted=true; return false; }
  ++out.read_calls; out.read_bytes+=size;
  const auto pointer=reinterpret_cast<std::uintptr_t>(address);
  if (budget.entries && pointer>=budget.entries) {
    const auto distance=pointer-budget.entries;
    // Limit only reads whose address is an actual table control/count field.
    // Registry/object reads can be above this storage; require the raw extent.
    std::uint64_t extent=0;
    if(out.mask_raw_i32 && out.tail_distance_raw_u8) {
      const auto bits=static_cast<std::uint32_t>(*out.mask_raw_i32)+*out.tail_distance_raw_u8+1U;
      std::int32_t signed_extent{}; std::memcpy(&signed_extent,&bits,4);
      if(signed_extent>=0)extent=static_cast<std::uint32_t>(signed_extent);
    }
    const auto slot=distance/0x40, field=distance%0x40;
    if(slot<extent && size==1 && field==4 && slot>=256) { out.budget_exhausted=true; return false; }
    if(slot<extent && size==4 && (field==0x1C || field==0x34)) {
      std::int32_t count{};
      if(!ReadMemory(address,&count,4))return false;
      if(count>0 && static_cast<std::uint64_t>(count)>1024-out.admitted_reference_count) {
        out.budget_exhausted=true;
        try { out.denied_vector_counts.push_back({static_cast<std::int64_t>(slot),field==0x34,count}); } catch (...) {}
        return false; // Existing collector stops this vector before its loop.
      }
      if(count>0)out.admitted_reference_count+=static_cast<std::size_t>(count);
      std::memcpy(output,&count,4); return true;
    }
  }
  return ReadMemory(address,output,size);
}
TableBindings InputBindings(CaptureBudget &budget) noexcept {
  TableBindings out{};
  const auto at=[](std::uintptr_t rva){return reinterpret_cast<const void *>(g_bindings.image_base+rva);};
  out.enabled=g_bindings.enabled;out.game_state_slot=at(0x5C68C50);
  out.siege_registry_slot=at(0x5D1EC88);out.siege_fallback_slot=at(0x5D1EC60);
  out.army_registry_slot=at(0x5D1DE48);out.army_fallback_slot=at(0x5D1DE50);
  out.arrg_registry_slot=at(0x5D1F340);out.arrg_fallback_slot=at(0x5D1F338);
  out.expected_army_allocator=at(0x54E0570);out.expected_arrg_allocator=at(0x54DEB68);
  out.read_context=&budget;out.read_memory=&CollectorRead;return out;
}
ActualArmyAssaultPlacementSnapshot12004 Capture(std::uintptr_t table,const char *stage) {
  ActualArmyAssaultPlacementSnapshot12004 out{};out.stage=stage;
  out.capture_event=NextArmyNaturalPhaseEvent12004();out.receiver_table_identity=table;
  out.entries_identity=ReadAt<std::uintptr_t>(table,8);
  if(out.entries_identity)out.native_empty_storage_matches=*out.entries_identity==g_bindings.image_base+kActualArmyAssaultEmptyStorageRva12004;
  out.occupied_count_raw_i32=ReadAt<std::int32_t>(table,0x10);out.mask_raw_i32=ReadAt<std::int32_t>(table,0x14);
  out.tail_distance_raw_u8=ReadAt<std::uint8_t>(table,0x18);out.load_factor_f32_bits_u32=ReadAt<std::uint32_t>(table,0x1C);
  out.table_allocator_identity=ReadAt<std::uintptr_t>(table,0x20);
  const auto state=ReadAt<std::uintptr_t>(g_bindings.image_base+0x5C68C50);
  const auto data=state ? ReadAt<std::uintptr_t>(*state,0xA0) : std::nullopt;
  if(data && *data && *data<=UINTPTR_MAX-0x2A6B0)out.current_primary_table_matches_receiver=*data+0x2A540+0x170==table;
  if(out.current_primary_table_matches_receiver==true) {
    CaptureBudget budget{&out,out.entries_identity.value_or(0)};
    out.physical_table=ck3_12003::ReadCurrentDailyAssaultTable12003(InputBindings(budget));
    // Keep the existing collector DTO vocabulary. The owned snapshot stage
    // above identifies this historical native boundary, never a later query.
    // An incomplete bounded scan must never become an available empty table.
    if(out.budget_exhausted) {
      out.physical_table.ready=false;out.physical_table.raw_groups_ready=false;
      out.physical_table.status="partial";out.physical_table.unavailable_reason="actual_placement_capture_budget_exhausted";
    }
    const auto &header=out.physical_table.header;
    const bool same_header=out.entries_identity && header.entries_present &&
        *header.entries_present==(*out.entries_identity!=0) &&
        (*out.entries_identity==0 || header.entries_identity=="native:"+std::to_string(*out.entries_identity)) &&
        header.occupied_count_raw_i32==out.occupied_count_raw_i32 && header.mask_raw_i32==out.mask_raw_i32 &&
        header.tail_distance_raw_u8==out.tail_distance_raw_u8 && header.load_factor_f32_bits_u32==out.load_factor_f32_bits_u32 &&
        out.physical_table.manager_identity=="native:"+std::to_string(table-0x170);
    const bool count_matches=out.occupied_count_raw_i32 && *out.occupied_count_raw_i32>=0 &&
        out.physical_table.physical_scan_ready && out.physical_table.observed_occupied_group_count==*out.occupied_count_raw_i32;
    if(!same_header || (out.physical_table.physical_scan_ready && !count_matches)) {
      out.physical_table.ready=false;out.physical_table.raw_groups_ready=false;out.physical_table.status="partial";
      out.physical_table.unavailable_reason=same_header ? "actual_placement_occupied_count_control_mismatch" : "actual_placement_receiver_header_changed_during_copy";
    }
    if(header.end_marker_control_raw_u8!=std::uint8_t{0xFF}) {
      out.physical_table.ready=false;out.physical_table.raw_groups_ready=false;
      out.physical_table.physical_scan_ready=false;out.physical_table.status="partial";
      out.physical_table.unavailable_reason="actual_placement_native_end_marker_unavailable";
    }
  } else {
    out.physical_table.unavailable_reason=out.current_primary_table_matches_receiver==false
        ? "actual_placement_receiver_not_current_primary_table"
        : "actual_placement_primary_table_read_binding_unavailable";
    out.physical_table.header.unavailable_reason=out.physical_table.unavailable_reason;
  }
  out.capture_complete=out.current_primary_table_matches_receiver==true && !out.budget_exhausted &&
      out.physical_table.header.ready && out.physical_table.physical_scan_ready && out.physical_table.raw_groups_ready;
  return out;
}
bool InitializeRuntime(const ActualArmyAssaultPlacementBindings12004 &bindings,ActualArmyAssaultPlacementOriginal12004 original) noexcept {
  if(!bindings.enabled || !bindings.image_base || !original)return false;
  g_available.store(false,std::memory_order_release);
  {const std::lock_guard lock(g_journal_mutex);g_bindings=bindings;g_latest_sequence=0;g_unattributed_failures=0;g_fixture_mode.store(false,std::memory_order_release);for(auto &slot:g_slots)slot={};}
  g_original.store(original,std::memory_order_release);g_available.store(true,std::memory_order_release);return true;
}
void Publish(Event &event) {
  const std::lock_guard lock(g_journal_mutex);
  if(!event.preparation.selected_army_full_id_raw_u32){++g_unattributed_failures;return;}
  event.sequence=++g_latest_sequence;auto &slot=g_slots[(event.sequence-1)%g_slots.size()];slot.event=event;slot.sequence=event.sequence;
}
void WriteAbsoluteJump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
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
void Fail(ActualArmyAssaultPlacementDetourState12004 &state,
          ActualArmyAssaultPlacementInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualArmyAssaultPlacementDetourState12004 &state,
                const std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_army_placement_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_army_placement_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_army_placement_install_protection
                     : actual_army_placement_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_army_placement_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualArmyAssaultPlacementHook12004));
  return patch;
}

} // namespace
bool InstallActualArmyAssaultPlacementObserver12004(
    ActualArmyAssaultPlacementDetourState12004 &state,
    const ActualArmyAssaultPlacementInstallEnvironment12004 &environment,
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
  state.failure_flags.store(actual_army_placement_install_none, std::memory_order_relaxed);
  if (!MatchesStartupExecutableSha(executable_sha256) || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_army_placement_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_army_placement_install_quiescence);
    return false;
  }
  ActualArmyAssaultPlacementDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_army_placement_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualArmyAssaultPlacementRva12004;
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
    Fail(state, actual_army_placement_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualArmyAssaultPlacementPatchBytes12004 +
      kActualArmyAssaultPlacementAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_army_placement_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kCallbackPrologue.data(), kCallbackPrologue.size());
  WriteAbsoluteJump(bytes + kCallbackPrologue.size(),
                    state.callback_target + kCallbackPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualArmyAssaultPlacementOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_army_placement_install_protection);
    else if (!flushed) Fail(state, actual_army_placement_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         actual_army_placement_install_rollback) != 0) {
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


ActualArmyAssaultPlacementBindings12004 BindActualArmyAssaultPlacementImage12004(std::uintptr_t base,std::string_view sha) noexcept {
  ActualArmyAssaultPlacementBindings12004 out{};if(!base || !MatchesStartupExecutableSha(sha))return out;
  out.enabled=true;out.image_base=base;return out;
}
bool InitializeActualArmyAssaultPlacementFixture12004(const ActualArmyAssaultPlacementBindings12004 &bindings,ActualArmyAssaultPlacementOriginal12004 original) noexcept {
  if(g_active_state.load(std::memory_order_acquire))return false;
  const bool ready=InitializeRuntime(bindings,original);if(ready)g_fixture_mode.store(true,std::memory_order_release);return ready;
}
std::optional<ActualArmyAssaultPlacementObservations12004> ReadActualArmyAssaultPlacementObservations12004(std::uint32_t full_id) noexcept {
  if(!g_available.load(std::memory_order_acquire))return std::nullopt;
  const auto *state=g_active_state.load(std::memory_order_acquire);
  const bool guarded=state && g_bindings.enabled && state->installed.load(std::memory_order_acquire)!=0 && state->failure_flags.load(std::memory_order_acquire)==0;
  if(!guarded && !g_fixture_mode.load(std::memory_order_acquire))return std::nullopt;
  try {
    ActualArmyAssaultPlacementObservations12004 out{};out.observer_installed=guarded;out.current_session_guard=guarded;
    const std::lock_guard lock(g_journal_mutex);out.latest_sequence=g_latest_sequence;
    out.oldest_available_sequence=g_latest_sequence==0 ? 0 : g_latest_sequence<=g_slots.size() ? 1 : g_latest_sequence-g_slots.size()+1;
    out.overwritten_events=g_latest_sequence>g_slots.size() ? g_latest_sequence-g_slots.size() : 0;out.unattributed_capture_failures=g_unattributed_failures;
    for(auto sequence=out.oldest_available_sequence;sequence!=0 && sequence<=g_latest_sequence;++sequence){const auto &slot=g_slots[(sequence-1)%g_slots.size()];if(slot.sequence==sequence && slot.event.preparation.selected_army_full_id_raw_u32==full_id)out.events.push_back(slot.event);}
    return out;
  } catch (...) {return std::nullopt;}
}
namespace {
std::uint64_t Observe(std::uintptr_t return_rva,const void *table,void *output,std::uint32_t hash,const std::uint32_t *key) noexcept {
  const auto original=g_original.load(std::memory_order_acquire);if(!original)return 0;
  if(return_rva!=kActualArmyAssaultPlacementDirectReturnRva12004 && return_rva!=kActualArmyAssaultPlacementRecursiveReturnRva12004)return original(table,output,hash,key);
  Event event{};
  try {
    event.preparation=CopyActiveActualArmyDailyAssaultPreparation12004();event.entry_event=NextArmyNaturalPhaseEvent12004();
    event.caller_return_rva=return_rva;event.recursive=return_rva==kActualArmyAssaultPlacementRecursiveReturnRva12004;
    event.incoming_table_identity=reinterpret_cast<std::uintptr_t>(table);event.incoming_output_identity=reinterpret_cast<std::uintptr_t>(output);
    event.incoming_key_identity=reinterpret_cast<std::uintptr_t>(key);event.incoming_hash_raw_u32=hash;event.incoming_key_raw_u32=ReadAt<std::uint32_t>(event.incoming_key_identity);
    const auto &active=event.preparation;
    event.selected_army_full_id_at_placement_u32=ReadAt<std::uint32_t>(active.incoming_selected_army,0x10);
    event.parent_bound=active.observed && active.parent_bound && active.original_occurrence_bound && active.selected_army_full_id_raw_u32 &&
        event.selected_army_full_id_at_placement_u32==active.selected_army_full_id_raw_u32 &&
        active.incoming_primary_manager<=UINTPTR_MAX-0x170 && active.incoming_primary_manager+0x170==event.incoming_table_identity &&
        active.entry_event.clock_identity==event.entry_event.clock_identity && active.entry_event.sequence<event.entry_event.sequence &&
        active.entry_event.thread_id && event.entry_event.thread_id && active.entry_event.thread_id==event.entry_event.thread_id;
    if(!event.parent_bound)event.capture_failure_flags|=actual_army_placement_capture_parent;
    if(!event.incoming_key_raw_u32)event.capture_failure_flags|=actual_army_placement_capture_request;
    event.before=Capture(event.incoming_table_identity,"actual_2AA2010_before_original");
    if(!event.before.capture_complete)event.capture_failure_flags|=actual_army_placement_capture_before;
    if(event.before.current_primary_table_matches_receiver!=true)event.capture_failure_flags|=actual_army_placement_capture_receiver;
  } catch (...) {event.capture_failure_flags|=actual_army_placement_capture_exception;}
  event.original_called=true;
  // Native effects are outside every observation catch/fault boundary.
  const std::uint64_t returned=original(table,output,hash,key);
  event.original_returned=true;event.original_rax_raw_u64=returned;
  try {
    event.returned_event=NextArmyNaturalPhaseEvent12004();event.after=Capture(reinterpret_cast<std::uintptr_t>(table),"actual_2AA2010_after_original_before_preparation_append");
    if(!event.after.capture_complete)event.capture_failure_flags|=actual_army_placement_capture_after;
    if(event.before.entries_identity && event.after.entries_identity)event.entries_identity_changed=event.before.entries_identity!=event.after.entries_identity;
    event.returned_entry_identity=ReadAt<std::uintptr_t>(reinterpret_cast<std::uintptr_t>(output));event.returned_inserted_raw_u8=ReadAt<std::uint8_t>(reinterpret_cast<std::uintptr_t>(output),8);
    if(!event.returned_entry_identity || !event.returned_inserted_raw_u8)event.capture_failure_flags|=actual_army_placement_capture_output;
    if(event.returned_entry_identity && event.after.entries_identity && *event.returned_entry_identity>=*event.after.entries_identity && event.after.physical_table.header.end_slot_raw_i32) {
      const auto distance=*event.returned_entry_identity-*event.after.entries_identity;
      const auto end=*event.after.physical_table.header.end_slot_raw_i32;
      if(distance%0x40==0 && end>=0 && distance/0x40<static_cast<std::uint32_t>(end))event.returned_physical_slot_i64=static_cast<std::int64_t>(distance/0x40);
    }
    Publish(event);
  } catch (...) { /* Owned-copy failure preserves every original return bit. */ }
  return returned;
}
} // namespace
std::uint64_t InvokeActualArmyAssaultPlacementFixture12004(std::uintptr_t return_rva,const void *table,void *output,std::uint32_t hash,const std::uint32_t *key) noexcept {return Observe(return_rva,table,output,hash,key);}
extern "C" std::uint64_t __fastcall XarActualArmyAssaultPlacementHook12004(const void *table,void *output,std::uint32_t hash,const std::uint32_t *key) noexcept {
#if defined(_MSC_VER)
  const auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller=reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva=g_bindings.image_base && caller>=g_bindings.image_base ? caller-g_bindings.image_base : 0;
  return Observe(rva,table,output,hash,key);
}
ActualArmyAssaultPlacementProjection12004 ProjectActualArmyAssaultPlacementObservation12004(
    const ActualArmyAssaultPlacementObservation12004 &placement,const ActualArmyDailyAssaultPreparationObservation12004 &preparation) {
  ActualArmyAssaultPlacementProjection12004 out{};
  const auto fail=[&](const char *reason){out.unavailable_reason=reason;return out;};
  const auto &active=placement.preparation;
  if(!placement.parent_bound || placement.recursive || placement.caller_return_rva!=kActualArmyAssaultPlacementDirectReturnRva12004 || !placement.original_returned)
    return fail("actual_placement_direct_parent_unbound");
  if(!preparation.active.parent_bound || !preparation.active.original_occurrence_bound || !preparation.original_returned ||
      active.entry_event.clock_identity!=preparation.active.entry_event.clock_identity || active.entry_event.sequence!=preparation.active.entry_event.sequence ||
      active.entry_event.thread_id!=preparation.active.entry_event.thread_id || active.incoming_primary_manager!=preparation.active.incoming_primary_manager ||
      active.incoming_selected_army!=preparation.active.incoming_selected_army || active.local_start_index!=preparation.active.local_start_index ||
      active.selected_army_full_id_raw_u32!=preparation.active.selected_army_full_id_raw_u32 || active.native_occurrence_index!=preparation.active.native_occurrence_index ||
      !placement.returned_event.sequence || preparation.returned_event.sequence<=placement.returned_event.sequence)
    return fail("actual_placement_preparation_event_join_unbound");
  const auto same_clock_thread=[&](const ArmyNaturalPhaseEvent12004 &stamp) {
    return stamp.clock_identity==active.entry_event.clock_identity && stamp.sequence!=0 &&
        stamp.thread_id && stamp.thread_id==active.entry_event.thread_id;
  };
  if(!same_clock_thread(placement.before.capture_event) || !same_clock_thread(placement.returned_event) ||
      !same_clock_thread(placement.after.capture_event) || !same_clock_thread(preparation.returned_event) ||
      active.parent.entry_event.clock_identity!=preparation.active.parent.entry_event.clock_identity ||
      active.parent.entry_event.sequence!=preparation.active.parent.entry_event.sequence ||
      active.parent.entry_event.thread_id!=preparation.active.parent.entry_event.thread_id ||
      placement.before.capture_event.sequence<=placement.entry_event.sequence ||
      placement.returned_event.sequence<=placement.before.capture_event.sequence ||
      placement.after.capture_event.sequence<=placement.returned_event.sequence ||
      preparation.returned_event.sequence<=placement.after.capture_event.sequence ||
      preparation.same_selected_army_generation_after!=true)
    return fail("actual_placement_capture_clock_or_generation_unbound");
  if(!preparation.before.copied_stage_input || !placement.before.capture_complete || !placement.incoming_key_raw_u32 || !placement.before.native_empty_storage_matches)
    return fail("actual_placement_owned_source_inputs_partial");
  auto stage=*preparation.before.copied_stage_input;
  if(!stage.boundary_binding_ready || !stage.ordered_append_inputs_ready || stage.ordered_append_inputs.size()!=1 ||
      stage.boundary.native_occurrence_index!=active.native_occurrence_index ||
      stage.boundary.frame_identity!="actual-army:"+std::to_string(active.entry_event.clock_identity)+":"+std::to_string(active.entry_event.sequence) ||
      stage.ordered_append_inputs.front().native_occurrence_index!=active.native_occurrence_index ||
      stage.ordered_append_inputs.front().selected_army_full_id_u32!=active.selected_army_full_id_raw_u32 ||
      stage.ordered_append_inputs.front().selected_siege_full_id_u32!=placement.incoming_key_raw_u32 ||
      stage.ordered_append_inputs.front().selected_siege_fnv1a_u32!=placement.incoming_hash_raw_u32 ||
      stage.ordered_append_inputs.front().army_append!=true)
    return fail("actual_placement_exact_append_request_unbound");
  stage.current_group_records=placement.before.physical_table;stage.current_group_frame_matches=true;stage.current_group_records_ready=placement.before.physical_table.ready;
  AssaultPlacementBaseline12004 baseline{};baseline.stage=AssaultPlacementBaselineStage12004::pre_date_copied_table;
  baseline.frame_identity=stage.boundary.frame_identity;
  baseline.source_provenance="owned_actual_2AA2010_entry_joined_to_actual_2A99B20_single_occurrence";
  baseline.native_empty_storage_matches=placement.before.native_empty_storage_matches;baseline.operation_limit=16384;
  out.projection=ProjectAssaultGroupPlacement12004(stage,baseline);out.mapping_ready=true;
  if(!out.projection->ready)out.unavailable_reason=out.projection->unavailable_reason;
  return out;
}
} // namespace xar::ck3_12004

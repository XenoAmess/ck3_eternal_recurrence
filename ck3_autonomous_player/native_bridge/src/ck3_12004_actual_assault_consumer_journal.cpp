#include "xar_bridge/ck3_12004_actual_assault_consumer_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <bit>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
using Event = ArmyActualAssaultConsumerObservationV1;
constexpr std::array<std::uint8_t, 19> kConsumerPrologue{
  0x48,0x89,0x4C,0x24,0x08,0x53,0x41,0x54,0x48,0x83,0xEC,0x48,
  0x48,0x8B,0x91,0x78,0x01,0x00,0x00};
struct JournalSlot { std::uint64_t sequence = 0; Event event; };
std::array<JournalSlot, kAssaultConsumerJournalEvents12004> g_slots;
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
ActualAssaultConsumerBindings12004 g_bindings;
std::atomic<bool> g_available{false};
std::atomic<ActualAssaultConsumerOriginal12004> g_original{nullptr};
std::atomic<ActualAssaultConsumerDetourState12004 *> g_active_state{nullptr};
thread_local ArmyAssaultConsumerParent12004 g_parent;
thread_local Event *g_event = nullptr;
thread_local std::size_t g_budget_cursor = 0;

template<class F> bool FaultBoundary(F callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool ReadMemory(const void *address, void *output, std::size_t size) noexcept {
  if (!address) return false;
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory) return g_bindings.read_memory(g_bindings.read_context,address,output,size);
    std::memcpy(output,address,size); return true;
  });
}
template<class T> std::optional<T> Read(std::uintptr_t object, std::size_t offset=0) noexcept {
  T out{};
  if (!object || object > UINTPTR_MAX-offset ||
      !ReadMemory(reinterpret_cast<const void *>(object+offset), &out, sizeof(out))) return {};
  return out;
}
AssaultConsumerResolved12004 Resolve(std::optional<std::uint32_t> raw,
    std::uintptr_t registry_rva, std::uintptr_t fallback_rva, std::size_t full_offset) noexcept {
  AssaultConsumerResolved12004 out; out.requested_full_id=raw;
  if (!raw) return out;
  auto store=Read<std::uintptr_t>(g_bindings.image_base+registry_rva);
  if (!store) return out;
  if (*store) {
    auto bound=Read<std::uint32_t>(*store,0x2C);
    if (!bound) return out;
    auto index=*raw&0xFFFFFFU;
    if (index<*bound) {
      auto table=Read<std::uintptr_t>(*store,0x20);
      if (!table || !*table) return out;
      auto selected=Read<std::uintptr_t>(*table,std::size_t(index)*16+8);
      if (!selected) return out;
      if (*selected) {
        auto full=Read<std::uint32_t>(*selected,full_offset);
        if (!full) return out;
        if (*full==*raw) {
          out.object_identity=*selected; out.selected_full_id=*full; out.used_fallback=false; return out;
        }
      }
    }
  }
  auto fallback=Read<std::uintptr_t>(g_bindings.image_base+fallback_rva);
  if (!fallback || !*fallback) return out;
  out.object_identity=*fallback; out.selected_full_id=Read<std::uint32_t>(*fallback,full_offset);
  out.used_fallback=true; return out;
}
AssaultConsumerVector12004 Vector(std::uintptr_t header, bool payload=true) {
  AssaultConsumerVector12004 out;
  out.data_identity=Read<std::uintptr_t>(header);
  out.capacity=Read<std::int32_t>(header,8); out.count=Read<std::int32_t>(header,12);
  out.allocator_identity=Read<std::uintptr_t>(header,16);
  if (!payload || !out.count || !out.capacity || *out.count<0 || *out.capacity<*out.count) return out;
  if (*out.count==0) { out.references_complete=true; return out; }
  if (!out.data_identity || !*out.data_identity) return out;
  auto count=std::min<std::size_t>(*out.count,kAssaultConsumerMaximumOccurrences12004);
  out.references_complete=count==std::size_t(*out.count);
  for (std::size_t i=0;i<count;++i) {
    auto raw=Read<std::uint32_t>(*out.data_identity,i*4);
    out.references_complete=out.references_complete&&raw.has_value(); out.ordered_full_ids.push_back(raw);
  }
  return out;
}
std::optional<bool> WriterSkipped(std::uintptr_t arrg) noexcept {
  auto character=Read<std::uint32_t>(arrg,0x148);
  if (!character) return {};
  if (*character==UINT32_MAX) return false;
  auto selected=Resolve(character,0x5C67568,0x5C67570,0x18);
  if (!selected.object_identity || !selected.selected_full_id) return {};
  auto magic=Read<std::uint32_t>(*selected.object_identity,0x1C);
  if (!magic) return {};
  return *magic==0x43686172 && *selected.selected_full_id!=UINT32_MAX;
}
AssaultConsumerPhysical12004 Physical(std::uintptr_t object) noexcept {
  AssaultConsumerPhysical12004 out; out.object_identity=object;
  out.maximum=Read<std::int32_t>(object,0); out.current=Read<std::int32_t>(object,4);
  out.persistent_full_id=Read<std::int32_t>(object,8); out.own_ordinal=Read<std::int32_t>(object,12);
  out.army_regiment_full_id=Read<std::int32_t>(object,16); out.state=Read<std::int32_t>(object,24); return out;
}
AssaultConsumerRegiment12004 Regiment(AssaultConsumerResolved12004 resolved,
    std::size_t &remaining_data) {
  AssaultConsumerRegiment12004 out; out.resolution=resolved;
  if (!resolved.object_identity || !resolved.selected_full_id) return out;
  auto object=*resolved.object_identity;
  out.magic=Read<std::uint32_t>(object,0x14);
  if (!out.magic) return out;
  out.identity_valid=*out.magic==0x41725267 && *resolved.selected_full_id!=UINT32_MAX;
  if (!*out.identity_valid) { out.data_complete=true; return out; }
  out.current=Read<std::int32_t>(object,0x38); out.maximum=Read<std::int32_t>(object,0x3C);
  auto definition=Read<std::uintptr_t>(object,0x18);
  if (definition && *definition) out.definition_type=Read<std::int32_t>(*definition,0x2A0);
  out.native_loss_writer_skipped=WriterSkipped(object);
  if (out.native_loss_writer_skipped==true) { out.data_complete=true; return out; }
  out.data_identity=Read<std::uintptr_t>(object,0x20);
  out.data_capacity=Read<std::int32_t>(object,0x28); out.data_count=Read<std::int32_t>(object,0x2C);
  if (!out.data_count || !out.data_capacity || *out.data_count<0 || *out.data_capacity<*out.data_count) return out;
  if (*out.data_count==0) { out.data_complete=true; return out; }
  if (!out.data_identity || !*out.data_identity) return out;
  auto count=std::min<std::size_t>(*out.data_count,remaining_data);
  remaining_data-=count; out.data_complete=count==std::size_t(*out.data_count);
  for (std::size_t i=0;i<count;++i) {
    AssaultConsumerData12004 row; row.native_index=static_cast<std::int32_t>(i);
    row.persistent_full_id=Read<std::uint32_t>(*out.data_identity,i*16+8);
    row.data_ordinal=Read<std::int32_t>(*out.data_identity,i*16+12);
    row.persistent_resolution=Resolve(row.persistent_full_id,0x5D1EB68,0x5D1EB58,0x10);
    if (row.persistent_resolution.object_identity && row.persistent_resolution.selected_full_id) {
      auto reg=*row.persistent_resolution.object_identity;
      auto magic=Read<std::uint32_t>(reg,0x14);
      if (magic) row.persistent_identity_valid=*magic==0x52656769 && *row.persistent_resolution.selected_full_id!=UINT32_MAX;
      // Native ordinal addressing has no safety bound. Excluded malformed
      // ordinals are explicitly partial instead of guessing lifecycle effects.
      if (row.persistent_identity_valid==true && row.data_ordinal && *row.data_ordinal>=0 && *row.data_ordinal<7) {
        row.physical=Physical(reg+0x18+std::size_t(*row.data_ordinal)*0x24);
        row.ready=row.physical->maximum && row.physical->current && row.physical->state &&
            row.physical->persistent_full_id && row.physical->own_ordinal && row.physical->army_regiment_full_id;
      }
    }
    out.data_complete=out.data_complete&&row.ready; out.data_records.push_back(std::move(row));
  }
  return out;
}
bool RegimentsComplete(const std::vector<AssaultConsumerRegiment12004> &rows) noexcept {
  return std::all_of(rows.begin(),rows.end(),[](const auto &r) {
    return r.identity_valid && (!*r.identity_valid ||
      (r.current && r.maximum && r.native_loss_writer_skipped && r.data_complete));
  });
}
void AddRegiment(Event &event, std::optional<std::uint32_t> raw, std::size_t &remaining_data) {
  auto resolved=Resolve(raw,0x5D1F340,0x5D1F338,0x10);
  if (resolved.object_identity && std::any_of(event.entry_regiments.begin(),event.entry_regiments.end(),
      [&](const auto &r){return r.resolution.object_identity==resolved.object_identity;})) return;
  if (event.entry_regiments.size()>=kAssaultConsumerMaximumRegiments12004) { event.capture_failure_flags|=2; return; }
  event.entry_regiments.push_back(Regiment(resolved,remaining_data));
}
AssaultConsumerTable12004 Table(std::uintptr_t manager, bool payload, Event *event=nullptr) {
  AssaultConsumerTable12004 out;
  out.entries_identity=Read<std::uintptr_t>(manager,0x178);
  out.occupied_count=Read<std::int32_t>(manager,0x180); out.mask=Read<std::int32_t>(manager,0x184);
  out.tail_distance=Read<std::uint8_t>(manager,0x188); out.load_factor_bits=Read<std::uint32_t>(manager,0x18C);
  if (out.mask && out.tail_distance) out.end_slot=std::bit_cast<std::int32_t>(std::uint32_t(*out.mask)+*out.tail_distance+1U);
  if (!out.entries_identity || !*out.entries_identity || !out.end_slot || *out.end_slot<0) return out;
  auto slots=std::min<std::size_t>(*out.end_slot,kAssaultConsumerMaximumSlots12004);
  out.controls_complete=slots==std::size_t(*out.end_slot);
  if (out.controls_complete) out.end_marker_control=Read<std::uint8_t>(*out.entries_identity,slots*0x40+4);
  out.controls_complete=out.controls_complete && out.end_marker_control && *out.end_marker_control!=0;
  out.raw_references_complete=payload;
  std::size_t remaining_data=kAssaultConsumerMaximumDataRecords12004;
  for (std::size_t slot=0;slot<slots;++slot) {
    auto record=*out.entries_identity+slot*0x40;
    auto control=Read<std::uint8_t>(record,4); out.physical_controls.push_back(control);
    out.controls_complete=out.controls_complete&&control.has_value();
    if (!control || !*control) continue;
    if (out.groups.size()>=kAssaultConsumerMaximumGroups12004) { out.raw_references_complete=false; continue; }
    AssaultConsumerGroup12004 group; group.native_index=static_cast<std::int32_t>(out.groups.size());
    group.physical_slot=static_cast<std::int64_t>(slot); group.control=control;
    group.hash=Read<std::uint32_t>(record); group.siege_full_id=Read<std::uint32_t>(record,8);
    group.armies=Vector(record+0x10,payload); group.arrgs=Vector(record+0x28,payload);
    if (payload) {
      group.siege_resolution=Resolve(group.siege_full_id,0x5D1EC88,0x5D1EC60,8);
      if (group.siege_resolution.object_identity) {
        group.province_identity=Read<std::uintptr_t>(*group.siege_resolution.object_identity,0x200);
        group.breach_level=Read<std::int32_t>(*group.siege_resolution.object_identity,0x3D8);
        if (group.province_identity && *group.province_identity) {
          group.province_magic=Read<std::uint32_t>(*group.province_identity,0x85C);
          group.province_full_id=Read<std::uint32_t>(*group.province_identity,0x10);
        }
      }
      std::int32_t index=0;
      for (auto raw:group.armies.ordered_full_ids) {
        AssaultConsumerArmy12004 army; army.native_index=index++;
        army.resolution=Resolve(raw,0x5D1DE48,0x5D1DE50,0x10);
        if (army.resolution.object_identity) army.regiment_roster=Vector(*army.resolution.object_identity+0x38);
        if (event) for (auto id:army.regiment_roster.ordered_full_ids) AddRegiment(*event,id,remaining_data);
        group.army_occurrences.push_back(std::move(army));
      }
      if (event) for (auto raw:group.arrgs.ordered_full_ids) AddRegiment(*event,raw,remaining_data);
      out.raw_references_complete=out.raw_references_complete&&group.armies.references_complete&&group.arrgs.references_complete;
    }
    out.groups.push_back(std::move(group));
  }
  out.raw_references_complete=out.raw_references_complete&&out.controls_complete;
  return out;
}
ArmyNaturalPhaseEvent12004 NextEvent() noexcept {
  return g_bindings.next_event ? g_bindings.next_event(g_bindings.event_context) : ArmyNaturalPhaseEvent12004{};
}
bool SameThreadClock(const ArmyNaturalPhaseEvent12004 &a,const ArmyNaturalPhaseEvent12004 &b) noexcept {
  return a.clock_identity && a.clock_identity==b.clock_identity && a.sequence && b.sequence &&
    a.thread_id && b.thread_id && a.thread_id==b.thread_id;
}
bool InitializeRuntime(const ActualAssaultConsumerBindings12004 &bindings,
    ActualAssaultConsumerOriginal12004 original) noexcept {
  if (!bindings.enabled || !original) return false;
  g_available.store(false,std::memory_order_release);
  { const std::lock_guard lock(g_journal_mutex); g_bindings=bindings; g_latest_sequence=0; for(auto &slot:g_slots) slot={}; }
  g_original.store(original,std::memory_order_release); g_available.store(true,std::memory_order_release); return true;
}
void Publish(Event &&event) noexcept {
  try { const std::lock_guard lock(g_journal_mutex); event.journal_sequence=++g_latest_sequence;
    auto &slot=g_slots[(event.journal_sequence-1)%g_slots.size()]; slot.sequence=event.journal_sequence; slot.event=std::move(event);
  } catch (...) { }
}
// Source-owned detour helpers and installation follow below.
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
void Fail(ActualAssaultConsumerDetourState12004 &state,
          ActualAssaultConsumerInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualAssaultConsumerDetourState12004 &state,
                const std::array<std::uint8_t, kActualAssaultConsumerPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualAssaultConsumerPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.consumer_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, assault_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, assault_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? assault_install_protection : assault_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored) Fail(state, assault_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualAssaultConsumerPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualAssaultConsumerPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualAssaultConsumerHook12004));
  return patch;
}

} // namespace


ActualAssaultConsumerBindings12004 BindActualAssaultConsumerJournalImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ActualAssaultConsumerBindings12004 out;
  if (!base || sha != kExecutableSha256) return out;
  out.enabled=true; out.image_base=base;
  out.read_parent_scope=&CopyActiveArmyNaturalPhaseScope12004;
  out.next_event=&NextArmyNaturalPhaseEvent12004;
  return out;
}
bool InitializeActualAssaultConsumerJournalFixture12004(
    const ActualAssaultConsumerBindings12004 &bindings,
    ActualAssaultConsumerOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire)) return false;
  return InitializeRuntime(bindings,original);
}
bool InstallActualAssaultConsumerJournal12004(
    ActualAssaultConsumerDetourState12004 &state,
    const ActualAssaultConsumerInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(assault_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, assault_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, assault_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  ActualAssaultConsumerDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, assault_install_already_installed);
    return false;
  }
  state.consumer_target = environment.consumer_target_override != 0
      ? environment.consumer_target_override
      : environment.bindings.image_base + kActualAssaultConsumerRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.consumer_target),
                            kConsumerPrologue.data(), kConsumerPrologue.size()) == 0;
      })) {
    Fail(state, assault_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualAssaultConsumerPatchBytes12004 +
      14;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, assault_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kConsumerPrologue.data(), kConsumerPrologue.size());
  WriteAbsoluteJump(bytes + kConsumerPrologue.size(),
                    state.consumer_target + kConsumerPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualAssaultConsumerOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kConsumerPrologue, HookPatch())) {
    if (!executable) Fail(state, assault_install_protection);
    else if (!flushed) Fail(state, assault_install_flush);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kConsumerPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallActualAssaultConsumerJournal12004(
    ActualAssaultConsumerDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, assault_install_quiescence);
    return false;
  }
  if (!WritePatch(state, HookPatch(), state.original)) return false;
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline,
                                         0, MEM_RELEASE);
  if (freed) state.trampoline = nullptr;
  else Fail(state, assault_install_allocation);
  return freed;
}

bool CopyActiveArmyAssaultConsumerParent12004(ArmyAssaultConsumerParent12004 &output) noexcept {
  output=g_parent; return output.active;
}
bool RecordActualAssaultConsumerBudget12004(std::uintptr_t receiver, std::uintptr_t caller,
    const ArmyNaturalPhaseEvent12004 &entry, const ArmyNaturalPhaseEvent12004 &returned,
    std::int32_t scalar, std::optional<std::uint32_t> siege_id,
    std::optional<std::uintptr_t> province, std::optional<std::uint32_t> province_id) noexcept {
  if (!g_event || !g_parent.active || !g_parent.exact_post_date_parent || caller!=0x2A97F64 ||
      !SameThreadClock(g_parent.entry_event,entry) || !SameThreadClock(entry,returned) ||
      entry.sequence<=g_parent.entry_event.sequence || returned.sequence<=entry.sequence ||
      g_budget_cursor>=g_event->entry_table.groups.size()) return false;
  auto &group=g_event->entry_table.groups[g_budget_cursor++];
  if (!group.siege_resolution.object_identity || *group.siege_resolution.object_identity!=receiver ||
      !siege_id || group.siege_resolution.selected_full_id!=siege_id ||
      !province || group.province_identity!=province || !province_id || group.province_full_id!=province_id) {
    g_event->capture_failure_flags|=128; return false;
  }
  group.native_current_expected_loss=scalar; group.natural_budget_observed=true;
  group.budget_entry_event=entry; group.budget_returned_event=returned; return true;
}
std::uintptr_t InvokeActualAssaultConsumerObserver12004(void *manager,
    std::optional<std::uintptr_t> caller) noexcept {
  auto original=g_original.load(std::memory_order_acquire);
  if (!original) return 0;
  // Other actual callers are forwarded unchanged, without being relabelled as
  // the closed post-date stage.
  if (caller!=0x2A9A8EA) return original(manager);
  Event event;
  auto installed=g_active_state.load(std::memory_order_acquire);
  event.current_session_guard=installed && installed->installed.load(std::memory_order_acquire)!=0;
  auto &parent=event.parent;
  parent.actual_entry_rva=kActualAssaultConsumerRva12004;
  parent.caller_return_rva=caller; parent.manager_identity=reinterpret_cast<std::uintptr_t>(manager);
  parent.entry_event=NextEvent();
  if (g_bindings.read_parent_scope) {
    auto scope=g_bindings.read_parent_scope();
    parent.phase_entry_event=scope.entry_event; parent.date_raw=scope.date_raw;
    parent.absolute_day_raw=scope.absolute_day_raw;
    parent.exact_post_date_parent=scope.observed && scope.phase==ArmyNaturalPhaseKind12004::post_date &&
      scope.actual_entry_rva==0x2A9A570 && scope.primary_manager_identity==parent.manager_identity &&
      SameThreadClock(scope.entry_event,parent.entry_event) && scope.entry_event.sequence<parent.entry_event.sequence;
  }
  if (!parent.exact_post_date_parent) event.capture_failure_flags|=64;
  try {
    event.entry_table=Table(parent.manager_identity,true,&event);
    event.entry_pending_queue=Vector(parent.manager_identity+0x68);
    event.entry_dependencies_complete=event.entry_table.raw_references_complete &&
      event.entry_pending_queue.references_complete && event.entry_table.occupied_count &&
      *event.entry_table.occupied_count>=0 && std::size_t(*event.entry_table.occupied_count)==event.entry_table.groups.size() &&
      RegimentsComplete(event.entry_regiments) && !(event.capture_failure_flags&2);
    for (const auto &group:event.entry_table.groups) for (const auto &army:group.army_occurrences)
      event.entry_dependencies_complete=event.entry_dependencies_complete && army.resolution.selected_full_id &&
        army.regiment_roster.references_complete;
  } catch (...) { event.capture_failure_flags|=256; }
  auto previous_parent=g_parent; auto *previous_event=g_event; auto previous_cursor=g_budget_cursor;
  parent.active=true; g_parent=parent; g_event=&event; g_budget_cursor=0;
  event.original_called=true;
  // Exactly one natural invocation, outside all observation fault boundaries.
  const auto bits=original(manager);
  event.original_returned=true; event.raw_return_bits=bits;
  g_parent=previous_parent; g_event=previous_event; g_budget_cursor=previous_cursor;
  parent.active=false; event.returned_event=NextEvent();
  try {
    event.returned_table=Table(parent.manager_identity,false);
    event.returned_pending_queue=Vector(parent.manager_identity+0x68);
    std::size_t remaining_data=kAssaultConsumerMaximumDataRecords12004;
    event.returned_dependencies_complete=event.entry_dependencies_complete &&
      SameThreadClock(parent.entry_event,event.returned_event) && event.returned_event.sequence>parent.entry_event.sequence &&
      event.returned_table.controls_complete && event.returned_pending_queue.references_complete;
    for (const auto &before:event.entry_regiments) {
      auto selected=before.resolution;
      if (selected.object_identity) selected.selected_full_id=Read<std::uint32_t>(*selected.object_identity,0x10);
      auto after=Regiment(selected,remaining_data);
      after.same_instance_after=selected.selected_full_id && selected.selected_full_id==before.resolution.selected_full_id;
      after.same_data_header_after=after.data_identity==before.data_identity && after.data_count==before.data_count && after.data_capacity==before.data_capacity;
      bool same_records=after.data_records.size()==before.data_records.size();
      for (std::size_t i=0;same_records && i<before.data_records.size();++i) {
        const auto &a=after.data_records[i]; const auto &b=before.data_records[i];
        same_records=a.persistent_full_id==b.persistent_full_id && a.data_ordinal==b.data_ordinal &&
          a.physical && b.physical && a.physical->object_identity==b.physical->object_identity &&
          a.physical->persistent_full_id==b.physical->persistent_full_id && a.physical->own_ordinal==b.physical->own_ordinal &&
          a.physical->army_regiment_full_id==b.physical->army_regiment_full_id;
      }
      event.returned_dependencies_complete=event.returned_dependencies_complete && after.same_instance_after==true &&
        after.same_data_header_after==true && same_records;
      event.returned_regiments.push_back(std::move(after));
    }
    event.returned_dependencies_complete=event.returned_dependencies_complete&&RegimentsComplete(event.returned_regiments);
  } catch (...) { event.capture_failure_flags|=256; event.returned_dependencies_complete=false; }
  // Entry is a real natural frame. Full B/prior-write binding is independent
  // and remains false until another actual captured family proves it.
  Publish(std::move(event));
  return bits;
}
std::optional<ArmyActualAssaultConsumerObservationsV1>
ReadActualAssaultConsumerObservations12004(std::uint32_t owned_army_full_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return {};
  try {
    ArmyActualAssaultConsumerObservationsV1 out;
    auto active=g_active_state.load(std::memory_order_acquire);
    out.observer_installed=active && active->installed.load(std::memory_order_acquire)!=0;
    out.current_session_guard=out.observer_installed;
    const std::lock_guard lock(g_journal_mutex);
    out.latest_journal_sequence=g_latest_sequence;
    out.overwritten_events=g_latest_sequence>g_slots.size()?g_latest_sequence-g_slots.size():0;
    auto first=g_latest_sequence>g_slots.size()?g_latest_sequence-g_slots.size()+1:1;
    for (auto sequence=first;sequence<=g_latest_sequence;++sequence) {
      const auto &slot=g_slots[(sequence-1)%g_slots.size()]; if(slot.sequence!=sequence) continue;
      bool member=false;
      for (const auto &group:slot.event.entry_table.groups)
        member=member || std::find(group.armies.ordered_full_ids.begin(),group.armies.ordered_full_ids.end(),
          std::optional<std::uint32_t>{owned_army_full_id})!=group.armies.ordered_full_ids.end();
      if(member) out.events.push_back(slot.event);
    }
    return out;
  } catch (...) { return {}; }
}
extern "C" std::uintptr_t __fastcall XarActualAssaultConsumerHook12004(void *manager) noexcept {
#if defined(_MSC_VER)
  auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  auto caller=reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  std::optional<std::uintptr_t> rva;
  if (g_bindings.image_base && caller>=g_bindings.image_base) rva=caller-g_bindings.image_base;
  return InvokeActualAssaultConsumerObserver12004(manager,rva);
}
} // namespace xar::ck3_12004


#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"
#include <cstring>
#include <mutex>
#include <string>
#include <utility>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
// Six whole instructions: 2+1+4+3+3+3=16 bytes, no RIP/relative operands.
constexpr std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004>
    kCallbackPrologue{0x40,0x56,0x57,0x48,0x83,0xEC,0x48,0x48,
                      0x8B,0xF9,0x48,0x8B,0xF2,0x48,0x8B,0xCA};
using Event = ActualArmyDailyAssaultPreparationObservation12004;
using Bindings = ck3_12003::CurrentDailyAssaultRosterAdmissionBindings12003;
namespace detail = ck3_12003::daily_assault_roster_detail;
struct JournalSlot { std::uint64_t sequence = 0; Event event{}; };
std::array<JournalSlot, kActualArmyDailyAssaultPreparationJournalCapacity12004> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0, g_unattributed_failures = 0;
std::uint64_t g_dropped_owned_copy_events = 0;
std::atomic<bool> g_fixture_mode{false}, g_available{false};
ActualArmyDailyAssaultPreparationBindings12004 g_bindings{};
std::atomic<ActualArmyDailyAssaultPreparationOriginal12004> g_original{nullptr};
std::atomic<ActualArmyDailyAssaultPreparationDetourState12004 *> g_active_state{nullptr};
thread_local const ActualArmyDailyAssaultPreparationActive12004 *g_active_preparation = nullptr;
thread_local bool g_capture_budget_active = false;
thread_local std::size_t g_capture_reads_remaining = 0;
constexpr std::size_t kMaximumCopiedReferences = 4096;

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool ReadMemory(void *, const void *address, void *output, std::size_t size) noexcept {
  if (!address) return false;
  if (g_capture_budget_active) {
    if (!g_capture_reads_remaining) return false;
    --g_capture_reads_remaining;
  }
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory)
      return g_bindings.read_memory(g_bindings.read_context, address, output, size);
    std::memcpy(output, address, size); return true;
  });
}
Bindings InputBindings() noexcept {
  Bindings b{};
  const auto at = [](std::uintptr_t rva) { return reinterpret_cast<const void *>(g_bindings.image_base + rva); };
  b.enabled = g_bindings.enabled; b.read_memory = &ReadMemory;
  b.game_state_slot=at(0x5C68C50); b.army_registry_slot=at(0x5D1DE48); b.army_fallback_slot=at(0x5D1DE50);
  b.unit_registry_slot=at(0x5D1E380); b.unit_fallback_slot=at(0x5D1E378);
  b.character_registry_slot=at(0x5C67568); b.character_fallback_slot=at(0x5C67570);
  b.war_registry_slot=at(0x5D1DE58); b.war_fallback_slot=at(0x5D1DE40);
  b.siege_registry_slot=at(0x5D1EC88); b.siege_fallback_slot=at(0x5D1EC60);
  b.province_fallback_slot=at(0x5D1E390); b.relationship_fallback_slot=at(0x5D27B70);
  // A passive input observer never calls the province-classification getter.
  // Its dependent gate branch stays partial; the genuine callback still runs.
  b.get_current_province73c_classification = nullptr;
  return b;
}
bool BoundedVector(const Bindings &b, const void *header) {
  const auto count = detail::Read<std::int32_t>(b, header, 0xC);
  return count && *count >= 0 && static_cast<std::size_t>(*count) <= kMaximumCopiedReferences;
}
game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 SelectedOccurrence(
    const Bindings &b, const void *manager, const void *army,
    const ActualArmyDailyAssaultPreparationActive12004 &active,
    const game::ArmyDailyAssaultRawReferencesV1 &removal) {
  game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 out{};
  out.native_index = active.native_occurrence_index.value_or(-1);
  out.raw_full_id_u32 = active.requested_army_full_id_u32;
  // Direct observed argument; do not re-resolve an ID to replace RDX.
  auto &selection = out.original_army_resolution;
  selection.selection = "actual_original_rdx";
  selection.object_identity = detail::Identity(army);
  selection.requested_full_id_u32 = active.requested_army_full_id_u32;
  selection.selected_full_id_u32 = detail::Read<std::uint32_t>(b, army, 0x10);
  selection.selected_object_ready = army != nullptr;
  selection.selected_full_id_read_ready = selection.selected_full_id_u32.has_value();
  detail::Finish(selection, selection.selected_object_ready && selection.selected_full_id_read_ready);
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; detail::Finish(out, false); return out; };
  const auto skip = [&]() {
    out.army_append_ready=true; out.army_append=false; out.arrg_append_ready=true;
    out.arrg_append_full_ids_u32=std::vector<std::uint32_t>{}; detail::Finish(out,true); return out;
  };
  if (!selection.ready) return fail("actual_preparation_selected_argument_unavailable");
  out.gate=detail::Gate(b,army);
  if (!out.gate.ready) return fail(out.gate.unavailable_reason.c_str());
  if (out.gate.verdict==false) return skip();
  out.caller_army_unit_id_raw_u32=detail::Read<std::uint32_t>(b,army,0x124);
  auto unit=detail::Resolve(b,b.unit_registry_slot,b.unit_fallback_slot,out.caller_army_unit_id_raw_u32,0x10);
  out.caller_unit_resolution=unit.observation;
  if (!unit.observation.selected_object_ready) return fail("actual_preparation_unit_operand_unavailable");
  const auto raw_province=detail::Read<const void *>(b,unit.object,0x20);
  if (!raw_province) return fail("actual_preparation_province_pointer_unavailable");
  const void *province=*raw_province; out.caller_used_province_fallback=province==nullptr;
  if (!province) { const auto fallback=detail::Read<const void *>(b,b.province_fallback_slot); if (!fallback) return fail("actual_preparation_province_fallback_unavailable"); province=*fallback; }
  out.caller_province_identity=detail::Identity(province); out.caller_province_present=province!=nullptr;
  if (!province) return fail("actual_preparation_province_null");
  out.caller_province_siege_id_raw_u32=detail::Read<std::uint32_t>(b,province,0x788);
  auto siege=detail::Resolve(b,b.siege_registry_slot,b.siege_fallback_slot,out.caller_province_siege_id_raw_u32,8);
  out.siege_resolution=siege.observation;
  if (!siege.observation.selected_object_ready) return fail("actual_preparation_siege_operand_unavailable");
  out.siege_flag_44c_raw_u8=detail::Read<std::uint8_t>(b,siege.object,0x44C);
  if (!out.siege_flag_44c_raw_u8) return fail("actual_preparation_siege_flag_unavailable");
  if (*out.siege_flag_44c_raw_u8==0) return skip();
  out.selected_army_full_id_raw_u32=selection.selected_full_id_u32;
  out.removal_contains_selected_army=detail::Contains(removal,*selection.selected_full_id_u32);
  if (!out.removal_contains_selected_army) return fail("actual_preparation_removal_membership_unavailable");
  if (*out.removal_contains_selected_army) return skip();
  out.army_append_siege_full_id_u32=detail::Read<std::uint32_t>(b,siege.object,8);
  if (!out.army_append_siege_full_id_u32) return fail("actual_preparation_siege_key_unavailable");
  out.army_append_ready=true; out.army_append=true; out.army_append_full_id_u32=selection.selected_full_id_u32;
  const auto mask=detail::Read<std::int32_t>(b,manager,0x144);
  const auto tail=detail::Read<std::uint8_t>(b,manager,0x148);
  if (!mask || !tail || *mask<0 || static_cast<std::uint64_t>(*mask)+*tail+1U>kMaximumCopiedReferences)
    return fail("actual_preparation_pending_bound_unavailable");
  auto pending=detail::Pending(b,manager,*selection.selected_full_id_u32);
  out.pending_selection=pending.observation;
  if (!out.pending_selection.ready) return fail("actual_preparation_pending_selection_incomplete");
  if (*out.pending_selection.selected_control_raw_u8==0xFF) { out.arrg_append_ready=true; out.arrg_append_full_ids_u32=std::vector<std::uint32_t>{}; detail::Finish(out,true); return out; }
  if (!BoundedVector(b,detail::At(army,0x38))) return fail("actual_preparation_arrg_bound_unavailable");
  out.original_arrg_references=detail::References(b,detail::At(army,0x38));
  if (out.original_arrg_references.count_raw_i32 && *out.original_arrg_references.count_raw_i32>0) {
    if (!BoundedVector(b,detail::At(pending.record,0x10))) return fail("actual_preparation_suppression_bound_unavailable");
    out.pending_selection.suppression_references=detail::References(b,detail::At(pending.record,0x10));
  }
  bool complete=out.original_arrg_references.references_ready; std::vector<std::uint32_t> appended;
  for (const auto &raw:out.original_arrg_references.occurrences) {
    game::ArmyDailyAssaultArRgAdmissionOccurrenceV1 row{}; row.native_index=raw.native_index; row.raw_full_id_u32=raw.raw_full_id_u32;
    if (row.raw_full_id_u32) row.pending_contains=detail::Contains(out.pending_selection.suppression_references,*row.raw_full_id_u32);
    if (row.pending_contains) { row.append=!*row.pending_contains; if (*row.append) appended.push_back(*row.raw_full_id_u32); detail::Finish(row,true); }
    else { row.unavailable_reason="actual_preparation_arrg_membership_unavailable"; detail::Finish(row,false); complete=false; }
    out.arrg_occurrences.push_back(std::move(row));
  }
  out.arrg_append_ready=complete; if (complete) out.arrg_append_full_ids_u32=std::move(appended);
  detail::Finish(out,complete); return out;
}

void BindOriginalOccurrence(const Bindings &b, ActualArmyDailyAssaultPreparationActive12004 &active) {
  active.iterator_entry_full_id_u32=detail::Read<std::uint32_t>(b,reinterpret_cast<const void *>(active.actual_caller_iterator));
  const auto &roster=active.parent.original_army_roster;
  if (!active.parent_bound || roster.boundary!=ArmyNaturalRosterBoundary12004::pre_date_prefix_return ||
      roster.capture_rva!=kArmyNaturalOriginalRosterCaptureRva12004 || !roster.complete ||
      roster.capture_event.clock_identity!=active.entry_event.clock_identity ||
      roster.capture_event.thread_id!=active.entry_event.thread_id ||
      roster.capture_event.sequence<=active.parent.entry_event.sequence || roster.capture_event.sequence>=active.entry_event.sequence ||
      !roster.begin_identity || !roster.end_identity || !roster.count || *roster.count<0 ||
      roster.ordered_full_ids.size()>kMaximumCopiedReferences ||
      static_cast<std::size_t>(*roster.count)!=roster.ordered_full_ids.size() ||
      active.actual_caller_end!=*roster.end_identity || active.actual_caller_iterator<*roster.begin_identity ||
      active.actual_caller_iterator>=*roster.end_identity ||
      (active.actual_caller_iterator-*roster.begin_identity)%4!=0 ||
      *roster.end_identity-*roster.begin_identity!=static_cast<std::uintptr_t>(*roster.count)*4U) return;
  const auto index=(active.actual_caller_iterator-*roster.begin_identity)/4U;
  if (index>=roster.ordered_full_ids.size() || active.iterator_entry_full_id_u32!=roster.ordered_full_ids[index]) return;
  active.native_occurrence_index=static_cast<std::int32_t>(index); active.local_start_index=active.native_occurrence_index;
  active.requested_army_full_id_u32=roster.ordered_full_ids[index]; active.original_occurrence_bound=true;
}

ActualArmyDailyAssaultPreparationSnapshot12004 Capture(
    const ActualArmyDailyAssaultPreparationActive12004 &active, bool bind_before) {
  struct RestoreBudget { bool active; std::size_t remaining; ~RestoreBudget() { g_capture_budget_active=active; g_capture_reads_remaining=remaining; } } restore{g_capture_budget_active,g_capture_reads_remaining};
  g_capture_budget_active=true; g_capture_reads_remaining=65536;
  ActualArmyDailyAssaultPreparationSnapshot12004 out{}; const auto b=InputBindings();
  const auto manager=reinterpret_cast<const void *>(active.incoming_primary_manager);
  const auto army=reinterpret_cast<const void *>(active.incoming_selected_army);
  out.selected_army_full_id_raw_u32=detail::Read<std::uint32_t>(b,army,0x10);
  const auto state=detail::Read<const void *>(b,b.game_state_slot);
  if (state && *state) {
    out.game_state_identity_raw=reinterpret_cast<std::uintptr_t>(*state);
    if (active.parent.game_state_identity) out.game_state_matches_parent=*out.game_state_identity_raw==active.parent.game_state_identity;
    out.game_date_raw_u64=detail::Read<std::uint64_t>(b,*state,8);
    out.absolute_day_raw_u32=detail::Read<std::uint32_t>(b,*state,0x9C);
    out.calendar_flags_raw_u8=detail::Read<std::uint8_t>(b,*state,0xC0);
  }
  if (BoundedVector(b,detail::At(manager,0x68))) out.removal_queue=detail::RemovalReferences(b,manager,nullptr);
  else out.removal_queue.unavailable_reason="actual_preparation_removal_bound_unavailable";
  out.selected_occurrence=SelectedOccurrence(b,manager,army,active,out.removal_queue);
  out.source_inputs_ready=out.selected_occurrence.ready;
  if (!bind_before || !active.original_occurrence_bound || out.game_state_matches_parent!=true) return out;
  // Earlier/later occurrences stay raw references only. Their admissions are not
  // replayed at this call. Old35 selects only the exact bound native occurrence.
  game::ArmyCurrentDailyAssaultRosterAdmissionV1 admission{};
  admission.manager_identity=detail::Identity(manager);
  auto &raw=admission.original_roster; const auto &parent_roster=active.parent.original_army_roster;
  raw.count_raw_i32=parent_roster.count; raw.data_present=true; raw.data_identity=detail::Identity(reinterpret_cast<const void *>(*parent_roster.begin_identity));
  raw.references_ready=true; raw.observed_occurrence_count=*parent_roster.count; detail::Finish(raw,true);
  for (std::size_t i=0;i<parent_roster.ordered_full_ids.size();++i) {
    game::ArmyDailyAssaultRawReferenceOccurrenceV1 reference{}; reference.native_index=static_cast<std::int32_t>(i); reference.raw_full_id_u32=parent_roster.ordered_full_ids[i]; detail::Finish(reference,true); raw.occurrences.push_back(reference);
    game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 row{}; row.native_index=reference.native_index; row.raw_full_id_u32=reference.raw_full_id_u32;
    if (row.native_index==active.native_occurrence_index) row=out.selected_occurrence;
    admission.occurrences.push_back(std::move(row));
  }
  admission.removal_queue=out.removal_queue;
  DailyAssaultPreparationBoundary12004 boundary{};
  boundary.executable_sha256=kDailyAssaultPreparationExecutableSha256; boundary.stage=DailyAssaultPreparationStage12004::pre_date_assault_call;
  boundary.frame_identity="actual-army:"+std::to_string(active.entry_event.clock_identity)+":"+std::to_string(active.entry_event.sequence);
  boundary.query_sequence=active.entry_event.sequence;
  if (out.game_date_raw_u64) boundary.game_date_raw_i32=detail::Signed(static_cast<std::uint32_t>(*out.game_date_raw_u64));
  if (out.absolute_day_raw_u32) boundary.absolute_day_raw_i32=detail::Signed(*out.absolute_day_raw_u32);
  boundary.calendar_flags_raw_u8=out.calendar_flags_raw_u8; boundary.primary_manager_identity=admission.manager_identity.value_or("");
  boundary.callsite_rva=kDailyAssaultPreparationCallsiteRva; boundary.native_occurrence_index=active.native_occurrence_index;
  boundary.original_roster_capture_identity=raw.data_identity.value_or(""); boundary.selected_army_identity=detail::Identity(army);
  out.copied_stage_input=BindDailyAssaultPreparationInputs12004(boundary,admission,nullptr,{});
  return out;
}
bool InitializeRuntime(const ActualArmyDailyAssaultPreparationBindings12004 &bindings,
                       ActualArmyDailyAssaultPreparationOriginal12004 original) noexcept {
  if (!bindings.enabled || !bindings.image_base || !original) return false;
  g_available.store(false,std::memory_order_release);
  { const std::lock_guard lock(g_journal_mutex); g_bindings=bindings; g_latest_sequence=0; g_unattributed_failures=0; g_dropped_owned_copy_events=0; g_fixture_mode.store(false,std::memory_order_release); for(auto &slot:g_slots)slot={}; }
  g_original.store(original,std::memory_order_release); g_available.store(true,std::memory_order_release); return true;
}
void Publish(Event &event) {
  const std::lock_guard lock(g_journal_mutex);
  if (!event.before.selected_army_full_id_raw_u32) { ++g_unattributed_failures; return; }
  event.sequence=++g_latest_sequence; auto &slot=g_slots[(event.sequence-1)%g_slots.size()]; slot.event=event; slot.sequence=event.sequence;
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
void Fail(ActualArmyDailyAssaultPreparationDetourState12004 &state,
          ActualArmyDailyAssaultPreparationInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualArmyDailyAssaultPreparationDetourState12004 &state,
                const std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_army_preparation_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_army_preparation_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_army_preparation_install_protection
                     : actual_army_preparation_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_army_preparation_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004>
HookPatch(const ActualArmyDailyAssaultPreparationDetourState12004 &state) noexcept {
  std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(state.trampoline) +
      kActualArmyDailyAssaultPreparationPatchBytes12004 + kActualArmyDailyAssaultPreparationAbsoluteJumpBytes12004);
  return patch;
}

} // namespace
bool InstallActualArmyDailyAssaultPreparationObserver12004(
    ActualArmyDailyAssaultPreparationDetourState12004 &state,
    const ActualArmyDailyAssaultPreparationInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0) {
    // A retained failed rollback cannot become a successful installation by
    // resetting flags on a second call. Startup installation owns this state.
    return state.failure_flags.load(std::memory_order_acquire) == 0 &&
        g_active_state.load(std::memory_order_acquire) == &state &&
        environment.primary_thread_suspended_proven && environment.bindings.enabled &&
        environment.bindings.image_base == g_bindings.image_base &&
        executable_sha256 == kDailyAssaultPreparationExecutableSha256;
  }
  state.failure_flags.store(actual_army_preparation_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kDailyAssaultPreparationExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_army_preparation_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_army_preparation_install_quiescence);
    return false;
  }
  ActualArmyDailyAssaultPreparationDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_army_preparation_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualArmyDailyAssaultPreparationRva12004;
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
    Fail(state, actual_army_preparation_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualArmyDailyAssaultPreparationPatchBytes12004 +
      kActualArmyDailyAssaultPreparationAbsoluteJumpBytes12004 +
      kActualArmyDailyAssaultPreparationEntryThunkBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_army_preparation_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kCallbackPrologue.data(), kCallbackPrologue.size());
  WriteAbsoluteJump(bytes + kCallbackPrologue.size(),
                    state.callback_target + kCallbackPrologue.size());
  // Actual caller nonvolatile cursor registers are captured before any C++
  // prologue can reuse them. JMP retains the real native return address.
  auto *entry = bytes + kActualArmyDailyAssaultPreparationPatchBytes12004 +
      kActualArmyDailyAssaultPreparationAbsoluteJumpBytes12004;
  constexpr std::array<std::uint8_t, 6> capture{0x4D,0x8B,0xC7,0x4D,0x8B,0xCC};
  std::memcpy(entry, capture.data(), capture.size()); // R8=R15; R9=R12
  WriteAbsoluteJump(entry + capture.size(), reinterpret_cast<std::uintptr_t>(
      &XarActualArmyDailyAssaultPreparationHook12004));
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualArmyDailyAssaultPreparationOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch(state))) {
    if (!executable) Fail(state, actual_army_preparation_install_protection);
    else if (!flushed) Fail(state, actual_army_preparation_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         actual_army_preparation_install_rollback) != 0) {
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

namespace {

} // namespace
ActualArmyDailyAssaultPreparationBindings12004 BindActualArmyDailyAssaultPreparationImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ActualArmyDailyAssaultPreparationBindings12004 result{};
  if (!base || sha!=kDailyAssaultPreparationExecutableSha256) return result;
  result.enabled=true; result.image_base=base; return result;
}
bool InitializeActualArmyDailyAssaultPreparationFixture12004(
    const ActualArmyDailyAssaultPreparationBindings12004 &bindings,
    ActualArmyDailyAssaultPreparationOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire)) return false;
  const bool ready=InitializeRuntime(bindings,original); if(ready)g_fixture_mode.store(true,std::memory_order_release); return ready;
}
ActualArmyDailyAssaultPreparationActive12004 CopyActiveActualArmyDailyAssaultPreparation12004() noexcept {
  try { return g_active_preparation ? *g_active_preparation : ActualArmyDailyAssaultPreparationActive12004{}; }
  catch (...) { return {}; }
}
std::optional<ActualArmyDailyAssaultPreparationObservations12004>
ReadActualArmyDailyAssaultPreparationObservations12004(std::uint32_t full_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  const auto *state=g_active_state.load(std::memory_order_acquire);
  const bool guarded=state && g_bindings.enabled && g_bindings.image_base && state->installed.load(std::memory_order_acquire)!=0 && state->failure_flags.load(std::memory_order_acquire)==0;
  if (!guarded && !g_fixture_mode.load(std::memory_order_acquire)) return std::nullopt;
  try {
    ActualArmyDailyAssaultPreparationObservations12004 out{}; out.observer_installed=guarded; out.current_session_guard=guarded;
    const std::lock_guard lock(g_journal_mutex); out.latest_sequence=g_latest_sequence;
    out.oldest_available_sequence=g_latest_sequence==0 ? 0 : g_latest_sequence<=g_slots.size() ? 1 : g_latest_sequence-g_slots.size()+1;
    out.overwritten_events=g_latest_sequence>g_slots.size() ? g_latest_sequence-g_slots.size() : 0;
    out.unattributed_capture_failures=g_unattributed_failures;
    out.dropped_owned_copy_events=g_dropped_owned_copy_events;
    for(auto sequence=out.oldest_available_sequence;sequence!=0 && sequence<=g_latest_sequence;++sequence) { const auto &slot=g_slots[(sequence-1)%g_slots.size()]; if(slot.sequence==sequence && slot.event.before.selected_army_full_id_raw_u32==full_id)out.events.push_back(slot.event); }
    return out;
  } catch (...) { return std::nullopt; }
}
namespace {
std::uint64_t Observe(std::uintptr_t return_rva, const void *manager, const void *army,
                      std::uintptr_t iterator, std::uintptr_t end) noexcept {
  const auto original=g_original.load(std::memory_order_acquire); if(!original)return 0;
  if(return_rva!=kActualArmyDailyAssaultPreparationReturnRva12004)return original(manager,army);
  Event event{};
  auto &active=event.active;
  const auto *previous=g_active_preparation;
  try {
    active.observed=true; active.parent=CopyActiveArmyNaturalPhaseScope12004(); active.entry_event=NextArmyNaturalPhaseEvent12004();
    active.incoming_primary_manager=reinterpret_cast<std::uintptr_t>(manager); active.incoming_selected_army=reinterpret_cast<std::uintptr_t>(army);
    active.caller_return_rva=return_rva; active.callsite_rva=return_rva-5; active.actual_caller_iterator=iterator; active.actual_caller_end=end;
    active.parent_bound=active.parent.observed && active.parent.phase==ArmyNaturalPhaseKind12004::pre_date && active.parent.actual_entry_rva==kArmyNaturalPreDateRva12004 &&
      active.parent.primary_manager_identity==active.incoming_primary_manager && active.entry_event.clock_identity && active.parent.entry_event.clock_identity==active.entry_event.clock_identity &&
      active.parent.entry_event.sequence<active.entry_event.sequence && active.parent.entry_event.thread_id && active.entry_event.thread_id && active.parent.entry_event.thread_id==active.entry_event.thread_id;
    if(!active.parent_bound)event.capture_failure_flags|=actual_army_preparation_capture_parent;
    BindOriginalOccurrence(InputBindings(),active);
    if(!active.original_occurrence_bound)event.capture_failure_flags|=actual_army_preparation_capture_roster;
    event.before=Capture(active,true); active.selected_army_full_id_raw_u32=event.before.selected_army_full_id_raw_u32;
    if(!event.before.source_inputs_ready)event.capture_failure_flags|=actual_army_preparation_capture_before;
  } catch (...) { event.capture_failure_flags|=actual_army_preparation_capture_exception; }
  // No observation fault boundary catches or repeats the genuine native call.
  // The TLS parent covers its actual children, then restores any outer instance.
  g_active_preparation=&active; event.original_called=true;
  const std::uint64_t returned=original(manager,army);
  g_active_preparation=previous; event.original_returned=true; event.original_rax_raw_u64=returned;
  try {
    event.returned_event=NextArmyNaturalPhaseEvent12004(); event.after=Capture(active,false);
    if(!event.after.source_inputs_ready)event.capture_failure_flags|=actual_army_preparation_capture_after;
    if(event.before.selected_army_full_id_raw_u32 && event.after.selected_army_full_id_raw_u32) {
      event.same_selected_army_generation_after=event.before.selected_army_full_id_raw_u32==event.after.selected_army_full_id_raw_u32;
      if(event.same_selected_army_generation_after==false)event.capture_failure_flags|=actual_army_preparation_capture_identity_changed;
    }
  } catch (...) { event.capture_failure_flags|=actual_army_preparation_capture_exception; }
  try { Publish(event); }
  catch (...) { const std::lock_guard lock(g_journal_mutex); ++g_dropped_owned_copy_events; }
  return returned;
}
} // namespace
std::uint64_t InvokeActualArmyDailyAssaultPreparationFixture12004(
    std::uintptr_t return_rva,const void *manager,const void *army,std::uintptr_t iterator,std::uintptr_t end) noexcept {
  if (!g_fixture_mode.load(std::memory_order_acquire)) return 0;
  return Observe(return_rva,manager,army,iterator,end);
}
extern "C" std::uint64_t __fastcall XarActualArmyDailyAssaultPreparationHook12004(
    const void *manager,const void *army,std::uintptr_t iterator,std::uintptr_t end) noexcept {
#if defined(_MSC_VER)
  const auto caller=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller=reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva=g_bindings.image_base && caller>=g_bindings.image_base ? caller-g_bindings.image_base : 0;
  return Observe(rva,manager,army,iterator,end);
}
} // namespace xar::ck3_12004

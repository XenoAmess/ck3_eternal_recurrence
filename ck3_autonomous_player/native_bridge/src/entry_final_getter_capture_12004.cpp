#include "xar_bridge/entry_final_getter_capture_12004.hpp"
#include "xar_bridge/entry_final_writer_capture_12004.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <cstring>
#include <intrin.h>
#include <limits>
#include <optional>
#include <type_traits>

namespace xar::ck3_12004 {

static_assert(sizeof(std::uintptr_t) == sizeof(std::uint64_t));
static_assert(std::is_same_v<EntryFinalGetterOriginal12004,
    ck3_12002::EvaluateRegimentStatsAtProvince>);

namespace {
bool Ordered(const PersonInstalledTransferEvent12004 &before,
             const PersonInstalledTransferEvent12004 &after) noexcept {
  return before.clock_identity != 0 &&
      before.clock_identity == after.clock_identity &&
      before.sequence != 0 && after.sequence > before.sequence &&
      before.thread_id && after.thread_id &&
      before.thread_id == after.thread_id;
}
bool SameToken(const PersonInstalledTransferEvent12004 &a,
               const PersonInstalledTransferEvent12004 &b) noexcept {
  return a.clock_identity != 0 && a.clock_identity == b.clock_identity &&
      a.sequence != 0 && a.sequence == b.sequence &&
      a.thread_id && b.thread_id && a.thread_id == b.thread_id;
}
template <typename T>
std::optional<T> Field(const EntryFinalGetterCaptureBindings12004 &b,
                      std::uintptr_t object, std::size_t offset) noexcept {
  constexpr auto maximum = std::numeric_limits<std::uintptr_t>::max();
  if (object == 0 || b.read == nullptr ||
      offset > maximum - (sizeof(T) - 1) ||
      object > maximum - offset - (sizeof(T) - 1))
    return std::nullopt;
  T value{};
  if (!b.read(b.read_context, object + offset, &value, sizeof(value)))
    return std::nullopt;
  return value;
}
void EventJson(std::string &json,
               const PersonInstalledTransferEvent12004 &event) {
  json += "{\"clock_identity\":" + std::to_string(event.clock_identity);
  json += ",\"sequence\":" + std::to_string(event.sequence);
  json += ",\"thread_id\":";
  json += event.thread_id ? std::to_string(*event.thread_id) : "null";
  json += '}';
}
template <typename T>
void OptionalNumber(std::string &json, std::string_view key,
                    const std::optional<T> &value) {
  json += "\"";
  json += key;
  json += "\":";
  json += value ? std::to_string(*value) : "null";
}
} // namespace

EntryFinalGetterCaptureBindings12004 BindEntryFinalGetterCapture12004(
    std::string_view build, std::string_view executable_sha256,
    std::uintptr_t module_base, PersonInstalledTransferRead12004 read,
    void *read_context, PersonInstalledTransferEventReader12004 next_event,
    void *event_context) noexcept {
  constexpr std::string_view pin =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  EntryFinalGetterCaptureBindings12004 result{};
  result.exact_build_admitted = build == "1.20.0.4" &&
      executable_sha256 == pin && module_base != 0 &&
      module_base <= std::numeric_limits<std::uintptr_t>::max() -
          kEntryFinalGetterWriterReturn12004 &&
      next_event != nullptr;
  result.module_base = module_base;
  result.read_context = read_context;
  result.read = read;
  result.event_context = event_context;
  result.next_event = next_event;
  return result;
}

void *CaptureNaturalEntryFinalGetterReturn12004(
    const EntryFinalGetterCaptureBindings12004 &b,
    EntryFinalGetterOriginal12004 original,
    void *actual_resolved_regiment, void *actual_output, void *actual_province,
    std::uintptr_t actual_caller_return_address) {
  // A hook may be installed only after its original trampoline is established.
  if (original == nullptr) return nullptr;
  const auto *active = PeekActiveEntryFinalWriterScope12004();
  const auto province = reinterpret_cast<std::uintptr_t>(actual_province);
  const bool admitted = b.exact_build_admitted &&
      b.next_event != nullptr && active != nullptr &&
      active->image_base == b.module_base && active->entry_identity != 0 &&
      active->province_identity == province &&
      actual_caller_return_address >= b.module_base &&
      actual_caller_return_address - b.module_base ==
          kEntryFinalGetterWriterReturn12004;
  if (!admitted)
    return original(actual_resolved_regiment, actual_output, actual_province);

  EntryFinalGetterReturnedRecord12004 record{};
  record.writer_scope = *active;
  record.begin_event = b.next_event(b.event_context);
  if (!Ordered(record.writer_scope.begin_event, record.begin_event))
    return original(actual_resolved_regiment, actual_output, actual_province);

  record.actual_resolved_regiment_identity =
      reinterpret_cast<std::uintptr_t>(actual_resolved_regiment);
  record.actual_output_identity = reinterpret_cast<std::uintptr_t>(actual_output);
  record.actual_province_identity = province;
  record.caller_return_rva = actual_caller_return_address - b.module_base;
  record.original_called = true;
  auto *returned = original(
      actual_resolved_regiment, actual_output, actual_province);
  record.original_returned = true;
  record.raw_return_bits = reinterpret_cast<std::uintptr_t>(returned);
  record.completed_event = b.next_event(b.event_context);

  const auto *after = PeekActiveEntryFinalWriterScope12004();
  if (after != active || after == nullptr ||
      !SameToken(record.writer_scope.begin_event, after->begin_event) ||
      after->image_base != record.writer_scope.image_base ||
      after->entry_identity != record.writer_scope.entry_identity ||
      after->province_identity != record.writer_scope.province_identity ||
      after->writer_return_rva != record.writer_scope.writer_return_rva ||
      !Ordered(record.begin_event, record.completed_event))
    return returned;

  // The source writer dereferences returned RAX, so copy this record now while
  // its enclosing writer's stack output remains live. Every field is independent.
  const auto address = reinterpret_cast<std::uintptr_t>(returned);
  record.returned_fields.max_size_bits = Field<std::uint32_t>(b, address, 0x08);
  record.returned_fields.siege_bits = Field<std::uint64_t>(b, address, 0x10);
  record.returned_fields.damage_bits = Field<std::uint64_t>(b, address, 0x18);
  record.returned_fields.toughness_bits = Field<std::uint64_t>(b, address, 0x20);
  record.returned_fields.pursuit_bits = Field<std::uint64_t>(b, address, 0x28);
  record.returned_fields.screen_bits = Field<std::uint64_t>(b, address, 0x30);
  // The writer validates the exact active phase, optional typed Side/slot,
  // genuine caller, actual province, shared event order and one-child ownership.
  (void)NotifyEntryFinalWriterReturnedRecord12004(record);
  return returned;
}

std::string EntryFinalGetterReturnedRecordJson12004(
    const EntryFinalGetterReturnedRecord12004 &record) {
  std::string json = "{\"source\":\"native_natural_entry_final_getter_return\"";
  json += ",\"actual_callee_rva\":" + std::to_string(kEntryFinalGetterRva12004);
  json += ",\"caller_return_rva\":" + std::to_string(record.caller_return_rva);
  json += ",\"actual_resolved_regiment_identity\":" +
      std::to_string(record.actual_resolved_regiment_identity);
  json += ",\"actual_output_identity\":" +
      std::to_string(record.actual_output_identity);
  json += ",\"actual_province_identity\":" +
      std::to_string(record.actual_province_identity);
  json += ",\"begin_event\":";
  EventJson(json, record.begin_event);
  json += ",\"completed_event\":";
  EventJson(json, record.completed_event);
  json += ",\"original_called\":";
  json += record.original_called ? "true" : "false";
  json += ",\"original_returned\":";
  json += record.original_returned ? "true" : "false";
  json += ",\"raw_return_bits\":" + std::to_string(record.raw_return_bits);
  json += ",\"returned_fields\":{";
  const auto &fields = record.returned_fields;
  OptionalNumber(json, "max_size_bits", fields.max_size_bits);
  json += ',';
  OptionalNumber(json, "siege_bits", fields.siege_bits);
  json += ',';
  OptionalNumber(json, "damage_bits", fields.damage_bits);
  json += ',';
  OptionalNumber(json, "toughness_bits", fields.toughness_bits);
  json += ',';
  OptionalNumber(json, "pursuit_bits", fields.pursuit_bits);
  json += ',';
  OptionalNumber(json, "screen_bits", fields.screen_bits);
  json += "}}";
  return json;
}

} // namespace xar::ck3_12004


namespace xar::ck3_12004 {
namespace {
std::atomic<EntryFinalGetterCaptureState12004 *> g_getter_state{nullptr};
std::atomic<EntryFinalGetterOriginal12004> g_getter_original{nullptr};
std::atomic<std::uint32_t> g_getter_in_flight{0};
EntryFinalGetterCaptureBindings12004 g_getter_bindings;
EntryFinalGetterCaptureBindings12004 g_getter_anchor_bindings;
bool GetterNativeRead(void *, std::uintptr_t address, void *output,
                      std::size_t bytes) noexcept {
  if (!address || !output || !bytes ||
      address > std::numeric_limits<std::uintptr_t>::max() - (bytes - 1))
    return false;
  SIZE_T copied = 0;
  return ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
      output, bytes, &copied) && copied == bytes;
}
PersonInstalledTransferEvent12004 GetterSharedEvent(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
void GetterFail(EntryFinalGetterCaptureState12004 &state,
                EntryFinalGetterCaptureFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_relaxed);
}
void *GetterAllocate(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool GetterFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool GetterProtect(void *, void *address, std::size_t size, DWORD protection,
                   DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool GetterFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
void GetterJump(std::uint8_t *output, std::uintptr_t destination) noexcept {
  constexpr std::array<std::uint8_t, 6> instruction{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(output, instruction.data(), instruction.size());
  std::memcpy(output + instruction.size(), &destination, sizeof(destination));
}
std::array<std::uint8_t, 15> GetterPatch() noexcept {
  std::array<std::uint8_t, 15> patch{};
  patch.fill(0x90);
  GetterJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarEntryFinalGetterCaptureHook12004V1));
  return patch;
}
bool GetterTargetEquals(std::uintptr_t target,
                         const std::array<std::uint8_t, 15> &expected) noexcept {
  std::array<std::uint8_t, 15> actual{};
  return g_getter_anchor_bindings.read &&
      g_getter_anchor_bindings.read(g_getter_anchor_bindings.read_context,
          target, actual.data(), actual.size()) && actual == expected;
}
bool GetterWritePatch(EntryFinalGetterCaptureState12004 &state,
    const std::array<std::uint8_t, 15> &expected,
    const std::array<std::uint8_t, 15> &desired, bool &written) noexcept {
  written = false;
  if (!GetterTargetEquals(state.target, expected)) {
    GetterFail(state, getter_capture_anchor);
    return false;
  }
  DWORD previous = 0;
  if (!state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      PAGE_EXECUTE_READWRITE, previous)) {
    GetterFail(state, getter_capture_protection);
    return false;
  }
  if (!state.target_protection_known) {
    state.target_protection_known = true;
    state.original_target_protection = previous;
  }
  std::memcpy(reinterpret_cast<void *>(state.target), desired.data(), desired.size());
  written = true;
  const bool flushed = state.flush(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      state.original_target_protection, ignored);
  if (!flushed) GetterFail(state, getter_capture_flush);
  if (!restored) GetterFail(state, getter_capture_protection);
  return flushed && restored;
}
struct GetterFlight {
  GetterFlight() noexcept { g_getter_in_flight.fetch_add(1, std::memory_order_acq_rel); }
  ~GetterFlight() { g_getter_in_flight.fetch_sub(1, std::memory_order_acq_rel); }
};
void GetterDrop(EntryFinalGetterCaptureState12004 &state) noexcept {
  g_getter_original.store(nullptr, std::memory_order_release);
  g_getter_state.store(nullptr, std::memory_order_release);
  state.installed.store(0, std::memory_order_release);
}
} // namespace

EntryFinalGetterCaptureBindings12004 BindEntryFinalGetterCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  return BindEntryFinalGetterCapture12004("1.20.0.4", executable_sha256,
      module_base, GetterNativeRead, nullptr, GetterSharedEvent, nullptr);
}

bool InstallEntryFinalGetterCapture12004(EntryFinalGetterCaptureState12004 &state,
    const EntryFinalGetterCaptureInstall12004 &environment,
    std::string_view executable_sha256) noexcept {
  constexpr std::string_view pin =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  if (executable_sha256 != pin || !environment.bindings.exact_build_admitted ||
      environment.module_base == 0 ||
      environment.bindings.module_base != environment.module_base ||
      environment.module_base > std::numeric_limits<std::uintptr_t>::max() -
          kEntryFinalGetterWriterReturn12004 ||
      (environment.target_override && !environment.offline_fixture)) {
    GetterFail(state, getter_capture_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    GetterFail(state, getter_capture_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.trampoline != nullptr) {
    GetterFail(state, getter_capture_already_installed);
    return false;
  }
  if (g_getter_in_flight.load(std::memory_order_acquire) != 0) {
    GetterFail(state, getter_capture_callback_active);
    return false;
  }
  EntryFinalGetterCaptureState12004 *expected = nullptr;
  if (!g_getter_state.compare_exchange_strong(expected, &state,
                                             std::memory_order_acq_rel)) {
    GetterFail(state, getter_capture_already_installed);
    return false;
  }
  state.target = environment.target_override ? environment.target_override :
      environment.module_base + kEntryFinalGetterRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ?
      environment.virtual_free_override : GetterFree;
  state.virtual_protect = environment.virtual_protect_override ?
      environment.virtual_protect_override : GetterProtect;
  state.flush = environment.flush_override ? environment.flush_override : GetterFlush;
  const auto allocate = environment.virtual_alloc_override ?
      environment.virtual_alloc_override : GetterAllocate;
  g_getter_bindings = environment.bindings;
  // Only fixture installs may provide a clock override. Production uses 13's
  // existing shared process clock, rather than a private or caller-owned clock.
  if (!environment.offline_fixture) {
    g_getter_bindings.next_event = GetterSharedEvent;
    g_getter_bindings.event_context = nullptr;
  }
  g_getter_anchor_bindings = g_getter_bindings;
  if (!g_getter_anchor_bindings.read) {
    g_getter_anchor_bindings.read = GetterNativeRead;
    g_getter_anchor_bindings.read_context = nullptr;
  }
  state.target_protection_known = false;
  state.original_target_protection = 0;
  if (!GetterTargetEquals(state.target, kEntryFinalGetterPrologue12004)) {
    GetterFail(state, getter_capture_anchor);
    GetterDrop(state);
    return false;
  }
  state.trampoline = allocate(state.memory_context,
      kEntryFinalGetterTrampolineBytes12004, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (!state.trampoline) {
    GetterFail(state, getter_capture_allocation);
    GetterDrop(state);
    return false;
  }
  auto *code = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(code, kEntryFinalGetterPrologue12004.data(),
      kEntryFinalGetterPrologue12004.size());
  GetterJump(code + kEntryFinalGetterPrologue12004.size(),
      state.target + kEntryFinalGetterPrologue12004.size());
  DWORD previous = 0;
  const bool protected_code = state.virtual_protect(state.memory_context, code,
      kEntryFinalGetterTrampolineBytes12004, PAGE_EXECUTE_READ, previous);
  const bool flushed_code = protected_code && state.flush(state.memory_context,
      code, kEntryFinalGetterTrampolineBytes12004);
  if (flushed_code)
    g_getter_original.store(reinterpret_cast<EntryFinalGetterOriginal12004>(code),
                            std::memory_order_release);
  else
    GetterFail(state, protected_code ? getter_capture_flush : getter_capture_protection);
  bool written = false;
  const bool patched = flushed_code && GetterWritePatch(state,
      kEntryFinalGetterPrologue12004, GetterPatch(), written);
  if (!patched) {
    if (written) {
      bool restored = false;
      if (!GetterWritePatch(state, GetterPatch(), kEntryFinalGetterPrologue12004,
                            restored)) {
        // The target may still reference this trampoline, or its restored bytes
        // may have an unproven cache/protection transaction. Retain everything.
        GetterFail(state, getter_capture_rollback);
        state.original = kEntryFinalGetterPrologue12004;
        state.installed.store(1, std::memory_order_release);
        return false;
      }
    }
    GetterDrop(state);
    if (state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE))
      state.trampoline = nullptr;
    else
      GetterFail(state, getter_capture_allocation);
    return false;
  }
  state.original = kEntryFinalGetterPrologue12004;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallEntryFinalGetterCapture12004(EntryFinalGetterCaptureState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 &&
      state.trampoline == nullptr) return true;
  if (!primary_thread_suspended_proven) {
    GetterFail(state, getter_capture_quiescence);
    return false;
  }
  const bool installed = state.installed.load(std::memory_order_acquire) != 0;
  if ((installed && g_getter_state.load(std::memory_order_acquire) != &state) ||
      g_getter_in_flight.load(std::memory_order_acquire) != 0) {
    GetterFail(state, getter_capture_callback_active);
    return false;
  }
  if (installed) {
    const auto expected = GetterTargetEquals(state.target, GetterPatch()) ?
        GetterPatch() : state.original;
    bool written = false;
    if (!GetterWritePatch(state, expected, state.original, written)) {
      if (written && expected == GetterPatch()) {
        bool put_back = false;
        if (!GetterWritePatch(state, state.original, GetterPatch(), put_back))
          GetterFail(state, getter_capture_rollback);
      }
      return false;
    }
  }
  GetterDrop(state);
  if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
    GetterFail(state, getter_capture_allocation);
    return false;
  }
  state.trampoline = nullptr;
  return true;
}

extern "C" __declspec(noinline) void *
XarEntryFinalGetterCaptureHook12004V1(void *regiment, void *output, void *province) {
  GetterFlight flight;
  const auto original = g_getter_original.load(std::memory_order_acquire);
  return CaptureNaturalEntryFinalGetterReturn12004(g_getter_bindings, original,
      regiment, output, province,
      reinterpret_cast<std::uintptr_t>(_ReturnAddress()));
}
} // namespace xar::ck3_12004

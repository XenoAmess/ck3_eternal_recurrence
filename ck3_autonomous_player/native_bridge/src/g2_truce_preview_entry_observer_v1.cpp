#include "xar_bridge/g2_truce_preview_entry_observer_v1.hpp"

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "G2 truce preview-entry observer is x64-only");

constexpr std::size_t kStubBytes = 224;
constexpr std::array<std::uint8_t, kG2TrucePreviewEntryPatchBytesV1> kAnchor{
    0x48, 0x8B, 0x02, 0x4D, 0x8B, 0xF0, 0x4C, 0x8B,
    0xD2, 0x48, 0x8B, 0xF9, 0x66, 0x83, 0x38, 0x04};

std::atomic<G2TrucePreviewEntryObserverV1State *> g_active{nullptr};

void AddFailure(G2TrucePreviewEntryObserverV1State &state,
                G2TrucePreviewEntryObserverFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

void *DefaultAlloc(void *, std::size_t size, DWORD type,
                   DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old_protection) noexcept {
  old_protection = 0;
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  if (module_base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - module_base) {
    return 0;
  }
  return module_base + rva;
}

bool SafeCopyFrom(std::uintptr_t address, void *output,
                  std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
bool SafeCopyTo(std::uintptr_t address, const void *input,
                std::size_t size) noexcept {
  if (address == 0 || input == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), input, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
bool SafeEqual(std::uintptr_t address, const void *expected,
               std::size_t size) noexcept {
  std::array<std::uint8_t, kG2TrucePreviewEntryPatchBytesV1> actual{};
  return size <= actual.size() &&
      SafeCopyFrom(address, actual.data(), size) &&
      std::memcmp(actual.data(), expected, size) == 0;
}
std::uintptr_t SafeLoadPointer(std::uintptr_t address) noexcept {
  std::uintptr_t output = 0;
  (void)SafeCopyFrom(address, &output, sizeof(output));
  return output;
}
bool IsExecutable(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ ||
      protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}

template <std::size_t N>
void Emit(std::array<std::uint8_t, N> &bytes, std::size_t &cursor,
          std::initializer_list<std::uint8_t> source) noexcept {
  for (const auto byte : source) bytes[cursor++] = byte;
}
template <std::size_t N>
void EmitU64(std::array<std::uint8_t, N> &bytes, std::size_t &cursor,
             std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(bytes.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}
template <std::size_t N>
void EmitJump(std::array<std::uint8_t, N> &bytes, std::size_t &cursor,
              std::uintptr_t target) noexcept {
  Emit(bytes, cursor, {0xFF, 0x25, 0, 0, 0, 0});
  EmitU64(bytes, cursor, target);
}

void EmitPreserve(std::array<std::uint8_t, kStubBytes> &bytes,
                  std::size_t &cursor) noexcept {
  // The hook is after a completed prolog and RSP is 16-byte aligned.  Eight
  // pushes retain alignment; 0x20 bytes are call shadow space and the next
  // 0x60 bytes preserve volatile XMM0-XMM5.
  Emit(bytes, cursor, {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
                       0x41, 0x51, 0x41, 0x52, 0x41, 0x53,
                       0x48, 0x81, 0xEC, 0x80, 0x00, 0x00, 0x00});
  Emit(bytes, cursor, {0xF3, 0x0F, 0x7F, 0x44, 0x24, 0x20,
                       0xF3, 0x0F, 0x7F, 0x4C, 0x24, 0x30,
                       0xF3, 0x0F, 0x7F, 0x54, 0x24, 0x40,
                       0xF3, 0x0F, 0x7F, 0x5C, 0x24, 0x50,
                       0xF3, 0x0F, 0x7F, 0x64, 0x24, 0x60,
                       0xF3, 0x0F, 0x7F, 0x6C, 0x24, 0x70});
}
void EmitRestore(std::array<std::uint8_t, kStubBytes> &bytes,
                 std::size_t &cursor) noexcept {
  Emit(bytes, cursor, {0xF3, 0x0F, 0x6F, 0x44, 0x24, 0x20,
                       0xF3, 0x0F, 0x6F, 0x4C, 0x24, 0x30,
                       0xF3, 0x0F, 0x6F, 0x54, 0x24, 0x40,
                       0xF3, 0x0F, 0x6F, 0x5C, 0x24, 0x50,
                       0xF3, 0x0F, 0x6F, 0x64, 0x24, 0x60,
                       0xF3, 0x0F, 0x6F, 0x6C, 0x24, 0x70,
                       0x48, 0x81, 0xC4, 0x80, 0x00, 0x00, 0x00,
                       0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
                       0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void G2TrucePreviewEntryThunkV1(
    std::uintptr_t effect_this, std::uintptr_t preview_context,
    std::uintptr_t preview_collector) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordG2TrucePreviewEntryV1(*state, effect_this, preview_context,
                                preview_collector);
  }
}

std::size_t BuildStub(G2TrucePreviewEntryObserverV1State &state,
                      std::array<std::uint8_t, kStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  EmitPreserve(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8B, 0x8C, 0x24, 0xA8, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x8B, 0x94, 0x24, 0xA0, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x4C, 0x8B, 0x84, 0x24, 0x98, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&G2TrucePreviewEntryThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestore(stub, cursor);
  for (const auto byte : kAnchor) stub[cursor++] = byte;
  EmitJump(stub, cursor, state.continue_target);
  return cursor;
}

void BuildPatch(G2TrucePreviewEntryObserverV1State &state) noexcept {
  state.installed_patch.fill(0x90);
  std::size_t cursor = 0;
  EmitJump(state.installed_patch, cursor,
           reinterpret_cast<std::uintptr_t>(state.stub));
}

bool Flush(G2TrucePreviewEntryObserverV1State &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult {
  success,
  original_preserved,
  rollback_unproven,
};

TargetWriteResult WriteTarget(G2TrucePreviewEntryObserverV1State &state,
                              const std::uint8_t *expected,
                              const std::uint8_t *desired) noexcept {
  if (!SafeEqual(state.patch_target, expected, state.original.size())) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD old_protection = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(state.patch_target),
                             state.original.size(), PAGE_EXECUTE_READWRITE,
                             old_protection)) {
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  if (!IsExecutable(old_protection)) {
    DWORD ignored = 0;
    (void)state.virtual_protect(state.memory_context,
                                reinterpret_cast<void *>(state.patch_target),
                                state.original.size(), old_protection, ignored);
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool copied = SafeCopyTo(state.patch_target, desired,
                                 state.original.size());
  const bool identical = copied && SafeEqual(
      state.patch_target, desired, state.original.size());
  const bool flushed = identical && Flush(
      state, reinterpret_cast<void *>(state.patch_target),
      state.original.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      state.original.size(), old_protection, ignored);
  if (identical && flushed && restored) return TargetWriteResult::success;

  AddFailure(state, g2_truce_preview_entry_observer_failure_rollback);
  DWORD rollback_old = 0;
  bool rollback_proven = false;
  if (state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            state.original.size(), PAGE_EXECUTE_READWRITE,
                            rollback_old)) {
    const bool rollback_copied = SafeCopyTo(
        state.patch_target, expected, state.original.size());
    const bool rollback_identical = rollback_copied && SafeEqual(
        state.patch_target, expected, state.original.size());
    const bool rollback_flushed = rollback_identical && Flush(
        state, reinterpret_cast<void *>(state.patch_target),
        state.original.size());
    const bool rollback_protected = state.virtual_protect(
        state.memory_context, reinterpret_cast<void *>(state.patch_target),
        state.original.size(), old_protection, ignored);
    rollback_proven = rollback_identical && rollback_flushed &&
        rollback_protected;
  }
  return rollback_proven ? TargetWriteResult::original_preserved
                         : TargetWriteResult::rollback_unproven;
}

bool HasOverrides(
    const G2TrucePreviewEntryObserverEnvironmentV1 &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(G2TrucePreviewEntryObserverV1State &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.stub = nullptr;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

void RecordG2TrucePreviewEntryV1(G2TrucePreviewEntryObserverV1State &state,
                                 std::uintptr_t effect_this,
                                 std::uintptr_t preview_context,
                                 std::uintptr_t preview_collector) noexcept {
  const auto vtable = SafeLoadPointer(effect_this);
  const auto normal = Resolve(0, state.module_base,
                              kG2AddTruceEffectNormalVtableRvaV1);
  const auto forced = Resolve(0, state.module_base,
                              kG2AddTruceEffectForcedVtableRvaV1);
  if (vtable != normal && vtable != forced) return;

  state.last_effect_this.store(effect_this, std::memory_order_relaxed);
  state.last_effect_vtable.store(vtable, std::memory_order_relaxed);
  state.last_preview_context.store(preview_context,
                                   std::memory_order_relaxed);
  state.last_preview_collector.store(preview_collector,
                                     std::memory_order_relaxed);
  if (vtable == normal) {
    state.normal_effect_count.fetch_add(1, std::memory_order_relaxed);
  } else {
    state.forced_effect_count.fetch_add(1, std::memory_order_relaxed);
  }
  state.accepted_count.fetch_add(1, std::memory_order_release);
  const auto callback_address =
      state.armed_capture_callback.load(std::memory_order_acquire);
  if (callback_address != 0) {
    const auto context_address =
        state.armed_capture_context.load(std::memory_order_relaxed);
    reinterpret_cast<G2TrucePreviewEntryCaptureV1>(callback_address)(
        reinterpret_cast<void *>(context_address), effect_this,
        preview_context, preview_collector);
  }
}

bool ArmG2TrucePreviewEntryCaptureV1(
    G2TrucePreviewEntryCaptureV1 callback, void *context) noexcept {
  auto *const state = g_active.load(std::memory_order_acquire);
  if (state == nullptr || callback == nullptr || context == nullptr ||
      state->installed.load(std::memory_order_acquire) == 0) {
    return false;
  }
  if (state->armed_capture_callback.load(std::memory_order_acquire) != 0) {
    return false;
  }
  state->armed_capture_context.store(
      reinterpret_cast<std::uintptr_t>(context), std::memory_order_relaxed);
  state->armed_capture_callback.store(
      reinterpret_cast<std::uintptr_t>(callback), std::memory_order_release);
  return true;
}

void DisarmG2TrucePreviewEntryCaptureV1() noexcept {
  auto *const state = g_active.load(std::memory_order_acquire);
  if (state == nullptr) return;
  state->armed_capture_callback.store(0, std::memory_order_release);
  state->armed_capture_context.store(0, std::memory_order_relaxed);
}

bool InstallG2TrucePreviewEntryObserverV1(
    G2TrucePreviewEntryObserverV1State &state,
    const G2TrucePreviewEntryObserverEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(g2_truce_preview_entry_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        g2_truce_preview_entry_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasOverrides(environment)) {
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      g_active.load(std::memory_order_acquire) != nullptr) {
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               state.module_base,
                               kG2TrucePreviewEntryPatchRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  state.module_base,
                                  kG2TrucePreviewEntryContinueRvaV1);
  if (state.patch_target == 0 ||
      state.continue_target !=
          state.patch_target + kG2TrucePreviewEntryPatchBytesV1 ||
      !SafeEqual(state.patch_target, kAnchor.data(), kAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original.data(),
                    state.original.size())) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_anchor);
    ClearRuntime(state);
    return false;
  }

  state.memory_context = environment.memory_context;
  const auto alloc = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;

  state.stub = alloc(state.memory_context, kStubBytes,
                     MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_allocation);
    ClearRuntime(state);
    return false;
  }
  std::array<std::uint8_t, kStubBytes> stub{};
  const auto used = BuildStub(state, stub);
  if (used == 0 || used > stub.size() ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  used)) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_allocation);
    (void)state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE);
    ClearRuntime(state);
    return false;
  }
  DWORD old_protection = 0;
  if (!state.virtual_protect(state.memory_context, state.stub, kStubBytes,
                             PAGE_EXECUTE_READ, old_protection) ||
      old_protection != PAGE_READWRITE ||
      !Flush(state, state.stub, used)) {
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_stub_protection);
    (void)state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE);
    ClearRuntime(state);
    return false;
  }
  BuildPatch(state);
  g_active.store(&state, std::memory_order_release);
  const auto installed = WriteTarget(state, state.original.data(),
                                     state.installed_patch.data());
  if (installed != TargetWriteResult::success) {
    if (installed == TargetWriteResult::rollback_unproven) {
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    g_active.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE);
    ClearRuntime(state);
    return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallG2TrucePreviewEntryObserverV1(
    G2TrucePreviewEntryObserverV1State &state) noexcept {
  state.armed_capture_callback.store(0, std::memory_order_release);
  state.armed_capture_context.store(0, std::memory_order_relaxed);
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active.load(std::memory_order_acquire) != &state) {
    AddFailure(state,
               g2_truce_preview_entry_observer_failure_already_installed);
    return false;
  }
  if (WriteTarget(state, state.installed_patch.data(),
                  state.original.data()) != TargetWriteResult::success) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active.store(nullptr, std::memory_order_release);
  const bool released = state.virtual_free != nullptr &&
      state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE);
  if (!released) {
    AddFailure(state, g2_truce_preview_entry_observer_failure_rollback);
    return false;
  }
  ClearRuntime(state);
  return true;
}

G2TrucePreviewEntryObserverV1Diagnostics
ReadG2TrucePreviewEntryObserverV1Diagnostics(
    const G2TrucePreviewEntryObserverV1State &state) noexcept {
  G2TrucePreviewEntryObserverV1Diagnostics output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.accepted_count = state.accepted_count.load(std::memory_order_acquire);
  output.normal_effect_count =
      state.normal_effect_count.load(std::memory_order_relaxed);
  output.forced_effect_count =
      state.forced_effect_count.load(std::memory_order_relaxed);
  output.last_effect_this =
      state.last_effect_this.load(std::memory_order_relaxed);
  output.last_effect_vtable =
      state.last_effect_vtable.load(std::memory_order_relaxed);
  output.last_preview_context =
      state.last_preview_context.load(std::memory_order_relaxed);
  output.last_preview_collector =
      state.last_preview_collector.load(std::memory_order_relaxed);
  return output;
}

} // namespace xar::bridge

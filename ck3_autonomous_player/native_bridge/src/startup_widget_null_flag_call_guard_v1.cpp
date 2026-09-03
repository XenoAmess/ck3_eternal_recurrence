#include "xar_bridge/startup_widget_null_flag_call_guard_v1.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "the startup widget null flag-call guard is x64-only");
static_assert(sizeof(std::atomic<std::uint64_t>) == sizeof(std::uint64_t));
static_assert(kStartupWidgetNullFlagCallPatchRvaV1 == 0xAF4EE0);
static_assert(kStartupWidgetNullFlagCallTargetRvaV1 == 0x369CB30);

std::atomic<StartupWidgetNullFlagCallGuardV1State *> g_active_guard{
    nullptr};

constexpr std::array<std::uint8_t,
                     kStartupWidgetNullFlagCallPatchBytesV1>
    kPatchAnchor{
        0x45, 0x33, 0xC0,             // xor r8d, r8d
        0xB2, 0x01,                   // mov dl, 1
        0x48, 0x8B, 0xCF,             // mov rcx, rdi
        0xE8, 0x43, 0x7C, 0xBA, 0x02 // call 0x369CB30
    };

// Freeze the complete overwritten call plus the next two complete calls. The
// owner PDATA row and the preceding null producer/failure-helper edge are
// independently bound by the source contract and native executable test.
constexpr std::array<std::uint8_t,
                     kStartupWidgetNullFlagCallProductionAnchorBytesV1>
    kProductionAnchor{
        0x45, 0x33, 0xC0, 0xB2, 0x01, 0x48, 0x8B, 0xCF,
        0xE8, 0x43, 0x7C, 0xBA, 0x02,
        0x49, 0x8B, 0xCF, 0xE8, 0x5B, 0x06, 0x97, 0x02,
        0x48, 0x8B, 0xCE, 0xE8, 0x33, 0x00, 0x00, 0x00};

void AddFailure(StartupWidgetNullFlagCallGuardV1State &state,
                StartupWidgetNullFlagCallGuardFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

void *DefaultVirtualAlloc(void *, std::size_t size, DWORD allocation_type,
                          DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool DefaultVirtualFree(void *, void *address, std::size_t size,
                        DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultVirtualProtect(void *, void *address, std::size_t size,
                           DWORD new_protection,
                           DWORD &old_protection) noexcept {
  old_protection = 0;
  return VirtualProtect(address, size, new_protection, &old_protection) !=
         FALSE;
}

bool DefaultFlushInstructionCache(void *, const void *address,
                                  std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool AddRva(std::uintptr_t module_base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (module_base == 0 ||
      rva > std::numeric_limits<std::uintptr_t>::max() - module_base) {
    output = 0;
    return false;
  }
  output = module_base + rva;
  return true;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) {
    return override_address;
  }
  std::uintptr_t resolved = 0;
  (void)AddRva(module_base, rva, resolved);
  return resolved;
}

bool SafeBytesEqual(std::uintptr_t address, const std::uint8_t *expected,
                    std::size_t size) noexcept {
  if (address == 0 || expected == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), expected,
                       size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool SafeCopyFrom(std::uintptr_t address, std::uint8_t *destination,
                  std::size_t size) noexcept {
  if (address == 0 || destination == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool SafeCopyTo(std::uintptr_t address, const std::uint8_t *source,
                std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool IsExecutableProtection(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ ||
         protection == PAGE_EXECUTE_READWRITE ||
         protection == PAGE_EXECUTE_WRITECOPY;
}

bool HasUnsupportedProductionOverride(
    const StartupWidgetNullFlagCallGuardV1Environment &environment) noexcept {
  return environment.patch_target_override != 0 ||
         environment.continue_target_override != 0 ||
         environment.call_target_override != 0 ||
         environment.memory_context != nullptr ||
         environment.virtual_alloc_override != nullptr ||
         environment.virtual_free_override != nullptr ||
         environment.virtual_protect_override != nullptr ||
         environment.flush_instruction_cache_override != nullptr;
}

bool ExactAnchorsMatch(std::uintptr_t patch_target,
                       bool offline_fixture) noexcept {
  if (!SafeBytesEqual(patch_target, kPatchAnchor.data(),
                      kPatchAnchor.size())) {
    return false;
  }
  return offline_fixture ||
      SafeBytesEqual(patch_target, kProductionAnchor.data(),
                     kProductionAnchor.size());
}

void EmitBytes(
    std::array<std::uint8_t, kStartupWidgetNullFlagCallStubBytesV1> &stub,
    std::size_t &cursor,
    std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto byte : bytes) {
    stub[cursor++] = byte;
  }
}

void EmitU64(
    std::array<std::uint8_t, kStartupWidgetNullFlagCallStubBytesV1> &stub,
    std::size_t &cursor, std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(stub.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

bool BuildStub(
    StartupWidgetNullFlagCallGuardV1State &state,
    std::array<std::uint8_t, kStartupWidgetNullFlagCallStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;

  // Replay the three argument instructions exactly, then suppress only the
  // confirmed null-RDI callsite. Both paths preserve the owner's stack frame.
  EmitBytes(stub, cursor,
            {0x45, 0x33, 0xC0, 0xB2, 0x01, 0x48, 0x8B, 0xCF,
             0x48, 0x85, 0xFF, 0x74, 0x0F}); // test rdi,rdi; jz null
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, call_target
  EmitU64(stub, cursor, state.call_target);
  EmitBytes(stub, cursor, {0x41, 0xFF, 0xD3}); // call r11
  EmitBytes(stub, cursor, {0xEB, 0x0E});       // jmp common continuation

  EmitBytes(stub, cursor, {0x49, 0xBB}); // null: mov r11, counter
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&state.suppressed_count));
  EmitBytes(stub, cursor, {0xF0, 0x49, 0xFF, 0x03}); // lock inc qword [r11]

  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, continue_target
  EmitU64(stub, cursor, state.continue_target);
  EmitBytes(stub, cursor, {0x41, 0xFF, 0xE3}); // jmp r11

  return cursor == stub.size();
}

void BuildPatch(
    std::uintptr_t stub_address,
    std::array<std::uint8_t, kStartupWidgetNullFlagCallPatchBytesV1>
        &patch) noexcept {
  // mov r11, imm64; jmp r11. The 13-byte window comprises four complete body
  // instructions and begins after the owning function's unwind prologue.
  patch[0] = 0x49;
  patch[1] = 0xBB;
  const auto encoded = static_cast<std::uint64_t>(stub_address);
  std::memcpy(patch.data() + 2, &encoded, sizeof(encoded));
  patch[10] = 0x41;
  patch[11] = 0xFF;
  patch[12] = 0xE3;
}

bool Flush(StartupWidgetNullFlagCallGuardV1State &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult {
  success,
  original_preserved,
  rollback_unproven,
};

TargetWriteResult WriteTargetTransaction(
    StartupWidgetNullFlagCallGuardV1State &state,
    const std::uint8_t *expected, const std::uint8_t *desired) noexcept {
  const auto target = state.patch_target;
  constexpr auto size = kStartupWidgetNullFlagCallPatchBytesV1;
  if (!SafeBytesEqual(target, expected, size)) {
    AddFailure(state,
               startup_widget_null_flag_call_guard_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }

  DWORD previous = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), size,
                             PAGE_EXECUTE_READWRITE, previous)) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  if (!IsExecutableProtection(previous)) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_target_protection);
    DWORD ignored = 0;
    (void)state.virtual_protect(state.memory_context,
                                reinterpret_cast<void *>(target), size,
                                previous, ignored);
    return TargetWriteResult::original_preserved;
  }

  const bool wrote = SafeCopyTo(target, desired, size);
  const bool desired_identity = wrote && SafeBytesEqual(target, desired, size);
  const bool desired_flushed = desired_identity &&
      Flush(state, reinterpret_cast<const void *>(target), size);
  DWORD ignored = 0;
  const bool protection_restored = desired_flushed &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            previous, ignored);
  if (!wrote || !desired_identity) {
    AddFailure(state,
               startup_widget_null_flag_call_guard_failure_target_identity);
  }
  if (desired_flushed && !protection_restored) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_target_protection);
  }
  if (desired_identity && desired_flushed && protection_restored) {
    return TargetWriteResult::success;
  }

  // Roll back while the page is still writable. Failed rollback retains both
  // global ownership and the RX stub because the target may still reach it.
  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable &&
      SafeCopyTo(target, expected, size);
  const bool rollback_identity = rollback_written &&
      SafeBytesEqual(target, expected, size);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(state.memory_context,
                                    reinterpret_cast<const void *>(target),
                                    size);
  DWORD rollback_ignored = 0;
  const bool rollback_protection = rollback_writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            previous, rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protection) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(StartupWidgetNullFlagCallGuardV1State &state) noexcept {
  if (state.stub == nullptr) {
    return true;
  }
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolvedState(
    StartupWidgetNullFlagCallGuardV1State &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.call_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

bool InstallStartupWidgetNullFlagCallGuardV1(
    StartupWidgetNullFlagCallGuardV1State &state,
    const StartupWidgetNullFlagCallGuardV1Environment &environment) noexcept {
  state.failure_flags.store(
      startup_widget_null_flag_call_guard_failure_none,
      std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state,
               startup_widget_null_flag_call_guard_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_already_installed);
    return false;
  }

  StartupWidgetNullFlagCallGuardV1State *expected_active = nullptr;
  if (!g_active_guard.compare_exchange_strong(
          expected_active, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               environment.module_base,
                               kStartupWidgetNullFlagCallPatchRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  environment.module_base,
                                  kStartupWidgetNullFlagCallContinueRvaV1);
  state.call_target = Resolve(environment.call_target_override,
                             environment.module_base,
                             kStartupWidgetNullFlagCallTargetRvaV1);
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
                           ? environment.virtual_free_override
                           : &DefaultVirtualFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
                              ? environment.virtual_protect_override
                              : &DefaultVirtualProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
          ? environment.flush_instruction_cache_override
          : &DefaultFlushInstructionCache;
  const auto virtual_alloc = environment.virtual_alloc_override != nullptr
                                 ? environment.virtual_alloc_override
                                 : &DefaultVirtualAlloc;

  const bool resolved = state.patch_target != 0 &&
      state.continue_target != 0 && state.call_target != 0;
  if (!resolved ||
      state.continue_target !=
          state.patch_target + kStartupWidgetNullFlagCallPatchBytesV1 ||
      !ExactAnchorsMatch(state.patch_target, environment.offline_fixture)) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_anchor);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  if (!SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_anchor);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  state.suppressed_count.store(0, std::memory_order_relaxed);
  state.stub = virtual_alloc(state.memory_context,
                             kStartupWidgetNullFlagCallStubBytesV1,
                             MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state,
               startup_widget_null_flag_call_guard_failure_allocation);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  std::array<std::uint8_t, kStartupWidgetNullFlagCallStubBytesV1> stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state,
               startup_widget_null_flag_call_guard_failure_allocation);
    (void)ReleaseStub(state);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  DWORD previous = 0;
  const bool stub_protected = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context, state.stub, stub.size(),
                            PAGE_EXECUTE_READ, previous) &&
      previous == PAGE_READWRITE;
  const bool stub_flushed = stub_protected &&
      Flush(state, state.stub, stub.size());
  if (!stub_protected || !stub_flushed) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_stub_protection);
    (void)ReleaseStub(state);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  BuildPatch(reinterpret_cast<std::uintptr_t>(state.stub),
             state.installed_patch_bytes);
  const auto write_result = WriteTargetTransaction(
      state, state.original_patch_bytes.data(),
      state.installed_patch_bytes.data());
  if (write_result != TargetWriteResult::success) {
    if (write_result == TargetWriteResult::original_preserved) {
      (void)ReleaseStub(state);
      ClearResolvedState(state);
      g_active_guard.store(nullptr, std::memory_order_release);
    } else {
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }

  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallStartupWidgetNullFlagCallGuardV1(
    StartupWidgetNullFlagCallGuardV1State &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_guard.load(std::memory_order_acquire) != &state ||
      state.stub == nullptr) {
    AddFailure(
        state,
        startup_widget_null_flag_call_guard_failure_already_installed);
    return false;
  }

  const auto result = WriteTargetTransaction(
      state, state.installed_patch_bytes.data(),
      state.original_patch_bytes.data());
  if (result != TargetWriteResult::success) {
    AddFailure(state, startup_widget_null_flag_call_guard_failure_rollback);
    return false;
  }

  state.installed.store(0, std::memory_order_release);
  g_active_guard.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) {
    ClearResolvedState(state);
  }
  return released;
}

StartupWidgetNullFlagCallGuardV1Diagnostics
ReadStartupWidgetNullFlagCallGuardV1Diagnostics(
    const StartupWidgetNullFlagCallGuardV1State &state) noexcept {
  StartupWidgetNullFlagCallGuardV1Diagnostics output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.suppressed_count =
      state.suppressed_count.load(std::memory_order_acquire);
  return output;
}

} // namespace xar::bridge

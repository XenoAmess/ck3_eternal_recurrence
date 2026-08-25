#include "xar_bridge/startup_particle2_null_guard_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8, "the startup guard is x64-only");
static_assert(sizeof(std::atomic<std::uint64_t>) == sizeof(std::uint64_t));
static_assert(sizeof(std::atomic<std::uint32_t>) == sizeof(std::uint32_t));

std::atomic<StartupParticle2NullGuardV1State *> g_active_guard{nullptr};

constexpr std::array<std::uint8_t, 29> kRegistrationPrologueAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10,
    0x48, 0x89, 0x74, 0x24, 0x18, 0x48, 0x89, 0x7C, 0x24, 0x20,
    0x41, 0x56, 0x48, 0x81, 0xEC, 0x80, 0x08, 0x00, 0x00};

// The first 13 bytes are replaced. The trailing eight-byte slot load is also
// frozen so the continuation at 0x1DABD82 cannot drift independently.
constexpr std::array<std::uint8_t,
                     kStartupParticle2NullGuardPatchAnchorBytesV1>
    kPatchAnchor{
        0x0F, 0xB6, 0xEA, 0x48, 0x8B, 0xD9, 0x48,
        0x8B, 0x05, 0x8E, 0x3B, 0x96, 0x03, 0x4C,
        0x8B, 0xB4, 0xE8, 0xA8, 0x00, 0x00, 0x00};

constexpr std::array<std::uint8_t, 30> kRegistrationEpilogueAnchor{
    0x4C, 0x8D, 0x9C, 0x24, 0x80, 0x08, 0x00, 0x00,
    0x49, 0x8B, 0x5B, 0x10, 0x49, 0x8B, 0x6B, 0x18,
    0x49, 0x8B, 0x73, 0x20, 0x49, 0x8B, 0x7B, 0x28,
    0x49, 0x8B, 0xE3, 0x41, 0x5E, 0xC3};

void AddFailure(StartupParticle2NullGuardV1State &state,
                StartupParticle2NullGuardFailureV1 failure) noexcept {
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
    const StartupParticle2NullGuardV1Environment &environment) noexcept {
  return environment.patch_target_override != 0 ||
         environment.root_slot_address_override != 0 ||
         environment.continue_target_override != 0 ||
         environment.skip_target_override != 0 ||
         environment.memory_context != nullptr ||
         environment.virtual_alloc_override != nullptr ||
         environment.virtual_free_override != nullptr ||
         environment.virtual_protect_override != nullptr ||
         environment.flush_instruction_cache_override != nullptr;
}

bool ExactAnchorsMatch(std::uintptr_t patch_target,
                       std::uintptr_t skip_target) noexcept {
  if (patch_target < kStartupParticle2RegistrationPrologueBytesV1) {
    return false;
  }
  const auto function_entry =
      patch_target - kStartupParticle2RegistrationPrologueBytesV1;
  return SafeBytesEqual(function_entry, kRegistrationPrologueAnchor.data(),
                        kRegistrationPrologueAnchor.size()) &&
         SafeBytesEqual(patch_target, kPatchAnchor.data(),
                        kPatchAnchor.size()) &&
         SafeBytesEqual(skip_target, kRegistrationEpilogueAnchor.data(),
                        kRegistrationEpilogueAnchor.size());
}

void EmitBytes(std::array<std::uint8_t,
                          kStartupParticle2NullGuardStubBytesV1> &stub,
               std::size_t &cursor,
               std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto byte : bytes) {
    stub[cursor++] = byte;
  }
}

void EmitU64(std::array<std::uint8_t,
                        kStartupParticle2NullGuardStubBytesV1> &stub,
             std::size_t &cursor, std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(stub.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

void EmitI32(std::array<std::uint8_t,
                        kStartupParticle2NullGuardStubBytesV1> &stub,
             std::size_t &cursor, std::int32_t value) noexcept {
  std::memcpy(stub.data() + cursor, &value, sizeof(value));
  cursor += sizeof(value);
}

bool PatchRelative32(
    std::array<std::uint8_t, kStartupParticle2NullGuardStubBytesV1> &stub,
    std::size_t displacement_offset, std::size_t target_offset) noexcept {
  const auto instruction_end = displacement_offset + sizeof(std::int32_t);
  if (displacement_offset > stub.size() - sizeof(std::int32_t) ||
      target_offset > stub.size() ||
      target_offset > static_cast<std::size_t>(
                          std::numeric_limits<std::int32_t>::max()) +
                          instruction_end) {
    return false;
  }
  const auto relative = static_cast<std::int64_t>(target_offset) -
                        static_cast<std::int64_t>(instruction_end);
  if (relative < std::numeric_limits<std::int32_t>::min() ||
      relative > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  const auto encoded = static_cast<std::int32_t>(relative);
  std::memcpy(stub.data() + displacement_offset, &encoded, sizeof(encoded));
  return true;
}

bool BuildStub(
    StartupParticle2NullGuardV1State &state,
    std::array<std::uint8_t, kStartupParticle2NullGuardStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;

  // Replay the two overwritten argument-preservation instructions.
  EmitBytes(stub, cursor, {0x0F, 0xB6, 0xEA}); // movzx ebp, dl
  EmitBytes(stub, cursor, {0x48, 0x8B, 0xD9}); // mov rbx, rcx
  EmitBytes(stub, cursor, {0x83, 0xFD, 0x07}); // cmp ebp, 7
  EmitBytes(stub, cursor, {0x0F, 0x87});       // ja suppress_no_mask
  const auto invalid_index_displacement = cursor;
  EmitI32(stub, cursor, 0);

  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, root_slot_address
  EmitU64(stub, cursor, state.root_slot_address);
  EmitBytes(stub, cursor, {0x4D, 0x8B, 0x1B}); // mov r11, [r11]
  EmitBytes(stub, cursor, {0x4D, 0x85, 0xDB}); // test r11, r11
  EmitBytes(stub, cursor, {0x0F, 0x84});       // je suppress_with_mask
  const auto null_root_displacement = cursor;
  EmitI32(stub, cursor, 0);

  // mov r14, [r11 + rbp*8 + 0xa8]
  EmitBytes(stub, cursor,
            {0x4D, 0x8B, 0xB4, 0xEB, 0xA8, 0x00, 0x00, 0x00});
  EmitBytes(stub, cursor, {0x4D, 0x85, 0xF6}); // test r14, r14
  EmitBytes(stub, cursor, {0x0F, 0x84});       // je suppress_with_mask
  const auto null_slot_displacement = cursor;
  EmitI32(stub, cursor, 0);

  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, continue_target
  EmitU64(stub, cursor, state.continue_target);
  EmitBytes(stub, cursor, {0x41, 0xFF, 0xE3}); // jmp r11

  const auto suppress_with_mask = cursor;
  EmitBytes(stub, cursor, {0xB8, 0x01, 0x00, 0x00, 0x00}); // mov eax, 1
  EmitBytes(stub, cursor, {0x89, 0xE9});                   // mov ecx, ebp
  EmitBytes(stub, cursor, {0xD3, 0xE0});                   // shl eax, cl
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, &mask
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&state.suppressed_index_mask));
  EmitBytes(stub, cursor, {0xF0, 0x41, 0x09, 0x03}); // lock or [r11], eax

  const auto suppress_no_mask = cursor;
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, &count
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&state.suppressed_count));
  EmitBytes(stub, cursor, {0xF0, 0x49, 0xFF, 0x03}); // lock inc qword [r11]
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, &last_index
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&state.last_suppressed_index));
  // xchg with memory is implicitly locked. EBP is dead on the suppress path
  // and the original epilogue restores it from the unwind-described frame.
  EmitBytes(stub, cursor, {0x41, 0x87, 0x2B}); // xchg [r11], ebp
  EmitBytes(stub, cursor, {0x49, 0xBB});       // mov r11, skip_target
  EmitU64(stub, cursor, state.skip_target);
  EmitBytes(stub, cursor, {0x41, 0xFF, 0xE3}); // jmp r11

  return cursor == stub.size() &&
         PatchRelative32(stub, invalid_index_displacement,
                         suppress_no_mask) &&
         PatchRelative32(stub, null_root_displacement,
                         suppress_with_mask) &&
         PatchRelative32(stub, null_slot_displacement,
                         suppress_with_mask);
}

void BuildPatch(std::uintptr_t stub_address,
                std::array<std::uint8_t,
                           kStartupParticle2NullGuardPatchBytesV1>
                    &patch) noexcept {
  // mov r11, imm64; jmp r11. This is exactly 13 bytes and does not split an
  // instruction or overlap the following original slot load.
  patch[0] = 0x49;
  patch[1] = 0xBB;
  const auto encoded = static_cast<std::uint64_t>(stub_address);
  std::memcpy(patch.data() + 2, &encoded, sizeof(encoded));
  patch[10] = 0x41;
  patch[11] = 0xFF;
  patch[12] = 0xE3;
}

bool Flush(StartupParticle2NullGuardV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, startup_particle2_null_guard_failure_flush);
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
    StartupParticle2NullGuardV1State &state, const std::uint8_t *expected,
    const std::uint8_t *desired) noexcept {
  const auto target = state.patch_target;
  constexpr auto size = kStartupParticle2NullGuardPatchBytesV1;
  if (!SafeBytesEqual(target, expected, size)) {
    AddFailure(state, startup_particle2_null_guard_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }

  DWORD previous = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), size,
                             PAGE_EXECUTE_READWRITE, previous)) {
    AddFailure(state, startup_particle2_null_guard_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  if (!IsExecutableProtection(previous)) {
    AddFailure(state, startup_particle2_null_guard_failure_target_protection);
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
                            reinterpret_cast<void *>(target), size, previous,
                            ignored);
  if (!wrote || !desired_identity) {
    AddFailure(state, startup_particle2_null_guard_failure_target_identity);
  }
  if (desired_flushed && !protection_restored) {
    AddFailure(state, startup_particle2_null_guard_failure_target_protection);
  }
  if (desired_identity && desired_flushed && protection_restored) {
    return TargetWriteResult::success;
  }

  // Roll back while the page is still writable. If restoring the original
  // protection failed above, VirtualProtect left the page protection unchanged
  // on Windows; reacquire RWX anyway so a custom fixture must prove the state.
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
                            reinterpret_cast<void *>(target), size, previous,
                            rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protection) {
    AddFailure(state, startup_particle2_null_guard_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(StartupParticle2NullGuardV1State &state) noexcept {
  if (state.stub == nullptr) {
    return true;
  }
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state, startup_particle2_null_guard_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolvedState(StartupParticle2NullGuardV1State &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.root_slot_address = 0;
  state.continue_target = 0;
  state.skip_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

bool InstallStartupParticle2NullGuardV1(
    StartupParticle2NullGuardV1State &state,
    const StartupParticle2NullGuardV1Environment &environment) noexcept {
  state.failure_flags.store(startup_particle2_null_guard_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, startup_particle2_null_guard_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        startup_particle2_null_guard_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(state,
               startup_particle2_null_guard_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(state, startup_particle2_null_guard_failure_already_installed);
    return false;
  }

  StartupParticle2NullGuardV1State *expected_active = nullptr;
  if (!g_active_guard.compare_exchange_strong(
          expected_active, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state, startup_particle2_null_guard_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               environment.module_base,
                               kStartupParticle2NullGuardPatchRvaV1);
  state.root_slot_address = Resolve(
      environment.root_slot_address_override, environment.module_base,
      kStartupParticle2RootSlotRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  environment.module_base,
                                  kStartupParticle2NullGuardContinueRvaV1);
  state.skip_target = Resolve(environment.skip_target_override,
                              environment.module_base,
                              kStartupParticle2NullGuardSkipRvaV1);
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
      state.root_slot_address != 0 && state.continue_target != 0 &&
      state.skip_target != 0;
  if (!resolved ||
      !ExactAnchorsMatch(state.patch_target, state.skip_target) ||
      state.continue_target !=
          state.patch_target + kStartupParticle2NullGuardPatchAnchorBytesV1) {
    AddFailure(state, startup_particle2_null_guard_failure_anchor);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  if (!SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state, startup_particle2_null_guard_failure_anchor);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  state.suppressed_count.store(0, std::memory_order_relaxed);
  state.suppressed_index_mask.store(0, std::memory_order_relaxed);
  state.last_suppressed_index.store(kStartupParticle2NoSuppressedIndexV1,
                                    std::memory_order_relaxed);

  state.stub = virtual_alloc(state.memory_context,
                             kStartupParticle2NullGuardStubBytesV1,
                             MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state, startup_particle2_null_guard_failure_allocation);
    ClearResolvedState(state);
    g_active_guard.store(nullptr, std::memory_order_release);
    return false;
  }

  std::array<std::uint8_t, kStartupParticle2NullGuardStubBytesV1> stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state, startup_particle2_null_guard_failure_allocation);
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
  const bool stub_flushed = stub_protected && Flush(state, state.stub,
                                                    stub.size());
  if (!stub_protected || !stub_flushed) {
    AddFailure(state,
               startup_particle2_null_guard_failure_stub_protection);
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
      // Never release code that the target may still reach. The failed
      // pre-resume install remains visible as installed+rollback-failed.
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }

  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallStartupParticle2NullGuardV1(
    StartupParticle2NullGuardV1State &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_guard.load(std::memory_order_acquire) != &state ||
      state.stub == nullptr) {
    AddFailure(state, startup_particle2_null_guard_failure_already_installed);
    return false;
  }

  const auto result = WriteTargetTransaction(
      state, state.installed_patch_bytes.data(),
      state.original_patch_bytes.data());
  if (result != TargetWriteResult::success) {
    AddFailure(state, startup_particle2_null_guard_failure_rollback);
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

StartupParticle2NullGuardV1Diagnostics
ReadStartupParticle2NullGuardV1Diagnostics(
    const StartupParticle2NullGuardV1State &state) noexcept {
  StartupParticle2NullGuardV1Diagnostics output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags =
      state.failure_flags.load(std::memory_order_acquire);
  output.suppressed_count =
      state.suppressed_count.load(std::memory_order_acquire);
  output.suppressed_index_mask =
      state.suppressed_index_mask.load(std::memory_order_acquire);
  output.last_suppressed_index =
      state.last_suppressed_index.load(std::memory_order_acquire);
  return output;
}

} // namespace xar::bridge

#include "xar_bridge/startup_particle2_stage_recorder_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "the startup particle2 stage recorder is x64-only");
static_assert(sizeof(std::atomic<std::uint64_t>) == sizeof(std::uint64_t));
static_assert(sizeof(std::atomic<std::uint32_t>) == sizeof(std::uint32_t));

std::atomic<StartupParticle2StageRecorderV1State *> g_active_recorder{
    nullptr};

constexpr std::array<std::uint8_t, 27> kFactoryPrologueAnchor{
    0x48, 0x89, 0x4C, 0x24, 0x08, 0x55, 0x53, 0x56, 0x57,
    0x41, 0x54, 0x41, 0x56, 0x41, 0x57, 0x48, 0x8D, 0x6C,
    0x24, 0xD9, 0x48, 0x81, 0xEC, 0xF0, 0x00, 0x00, 0x00};

constexpr std::array<std::uint8_t, kStartupParticle2SourcePatchBytesV1>
    kSourcePatchAnchor{
        0x48, 0x8B, 0x4D, 0x77, 0x48, 0x85, 0xC9, 0x75, 0x08,
        0x4C, 0x89, 0x37, 0xE9, 0x92, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t, 7> kSourceHealthyAnchor{
    0x48, 0x8D, 0x46, 0x20, 0x8B, 0x50, 0x10};
constexpr std::array<std::uint8_t, 21> kSourceNullAnchor{
    0x48, 0x8B, 0xC7, 0x48, 0x81, 0xC4, 0xF0, 0x00, 0x00, 0x00,
    0x41, 0x5F, 0x41, 0x5E, 0x41, 0x5C, 0x5F, 0x5E, 0x5B, 0x5D,
    0xC3};

constexpr std::array<std::uint8_t, 5> kVariantPredicateAnchor{
    0x48, 0x85, 0xC0, 0x75, 0x10};
constexpr std::array<std::uint8_t, kStartupParticle2VariantPatchBytesV1>
    kVariantPatchAnchor{
        0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
        0x00, 0x00, 0x00, 0xE9, 0x1D, 0x01, 0x00, 0x00};
constexpr std::array<std::uint8_t, 9> kVariantNullAnchor{
    0x48, 0x8B, 0x75, 0x77, 0x48, 0x85, 0xF6, 0x74, 0x26};

constexpr std::array<std::uint8_t, 7> kBackendPredicateAnchor{
    0x48, 0x83, 0x7D, 0x7F, 0x00, 0x75, 0x1A};
constexpr std::array<std::uint8_t, kStartupParticle2BackendPatchBytesV1>
    kBackendPatchAnchor{
        0x4C, 0x89, 0x37, 0xC7, 0x44, 0x24, 0x30, 0x03,
        0x00, 0x00, 0x00, 0x48, 0x8D, 0x4D, 0xB7};
constexpr std::array<std::uint8_t, 11> kBackendNullAnchor{
    0xE8, 0x30, 0x01, 0x00, 0x00, 0x90,
    0xE9, 0xD7, 0x00, 0x00, 0x00};

void AddFailure(StartupParticle2StageRecorderV1State &state,
                StartupParticle2StageRecorderFailureV1 failure) noexcept {
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
    const StartupParticle2StageRecorderV1Environment &environment) noexcept {
  return environment.source_patch_target_override != 0 ||
      environment.source_healthy_target_override != 0 ||
      environment.source_null_target_override != 0 ||
      environment.variant_patch_target_override != 0 ||
      environment.variant_null_target_override != 0 ||
      environment.backend_patch_target_override != 0 ||
      environment.backend_null_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool ExactAnchorsMatch(
    const StartupParticle2StageRecorderV1State &state,
    bool offline_fixture) noexcept {
  if (!SafeBytesEqual(state.source_patch_target, kSourcePatchAnchor.data(),
                      kSourcePatchAnchor.size()) ||
      !SafeBytesEqual(state.variant_patch_target, kVariantPatchAnchor.data(),
                      kVariantPatchAnchor.size()) ||
      !SafeBytesEqual(state.backend_patch_target, kBackendPatchAnchor.data(),
                      kBackendPatchAnchor.size())) {
    return false;
  }
  if (offline_fixture) {
    return true;
  }
  std::uintptr_t function_entry = 0;
  return AddRva(state.module_base, kStartupParticle2FactoryFunctionRvaV1,
                function_entry) &&
      SafeBytesEqual(function_entry, kFactoryPrologueAnchor.data(),
                     kFactoryPrologueAnchor.size()) &&
      SafeBytesEqual(state.source_healthy_target, kSourceHealthyAnchor.data(),
                     kSourceHealthyAnchor.size()) &&
      SafeBytesEqual(state.source_null_target, kSourceNullAnchor.data(),
                     kSourceNullAnchor.size()) &&
      state.variant_patch_target >= kVariantPredicateAnchor.size() &&
      SafeBytesEqual(state.variant_patch_target -
                         kVariantPredicateAnchor.size(),
                     kVariantPredicateAnchor.data(),
                     kVariantPredicateAnchor.size()) &&
      SafeBytesEqual(state.variant_null_target, kVariantNullAnchor.data(),
                     kVariantNullAnchor.size()) &&
      state.backend_patch_target >= kBackendPredicateAnchor.size() &&
      SafeBytesEqual(state.backend_patch_target -
                         kBackendPredicateAnchor.size(),
                     kBackendPredicateAnchor.data(),
                     kBackendPredicateAnchor.size()) &&
      SafeBytesEqual(state.backend_null_target, kBackendNullAnchor.data(),
                     kBackendNullAnchor.size());
}

template <std::size_t Size>
void EmitBytes(std::array<std::uint8_t, Size> &stub, std::size_t &cursor,
               std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto byte : bytes) {
    stub[cursor++] = byte;
  }
}

template <std::size_t Size>
void EmitU64(std::array<std::uint8_t, Size> &stub, std::size_t &cursor,
             std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(stub.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

template <std::size_t Size>
void EmitI32(std::array<std::uint8_t, Size> &stub, std::size_t &cursor,
             std::int32_t value) noexcept {
  std::memcpy(stub.data() + cursor, &value, sizeof(value));
  cursor += sizeof(value);
}

template <std::size_t Size>
bool PatchRelative32(std::array<std::uint8_t, Size> &stub,
                     std::size_t displacement_offset,
                     std::size_t target_offset) noexcept {
  const auto instruction_end = displacement_offset + sizeof(std::int32_t);
  if (displacement_offset > stub.size() - sizeof(std::int32_t) ||
      target_offset > stub.size()) {
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

template <std::size_t Size>
void EmitCounterIncrement(std::array<std::uint8_t, Size> &stub,
                          std::size_t &cursor,
                          const std::atomic<std::uint64_t> &counter) noexcept {
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, &counter
  EmitU64(stub, cursor, reinterpret_cast<std::uintptr_t>(&counter));
  EmitBytes(stub, cursor,
            {0xF0, 0x49, 0xFF, 0x03}); // lock inc qword ptr [r11]
}

template <std::size_t Size>
void EmitAbsoluteJump(std::array<std::uint8_t, Size> &stub,
                      std::size_t &cursor,
                      std::uintptr_t target) noexcept {
  EmitBytes(stub, cursor, {0x49, 0xBB}); // mov r11, target
  EmitU64(stub, cursor, target);
  EmitBytes(stub, cursor, {0x41, 0xFF, 0xE3}); // jmp r11
}

bool BuildSourceStub(
    StartupParticle2StageRecorderV1State &state,
    std::array<std::uint8_t, kStartupParticle2SourceStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;
  EmitBytes(stub, cursor, {0x48, 0x8B, 0x4D, 0x77}); // mov rcx,[rbp+77]
  EmitBytes(stub, cursor, {0x48, 0x85, 0xC9});       // test rcx,rcx
  EmitBytes(stub, cursor, {0x0F, 0x85});             // jne healthy
  const auto healthy_displacement = cursor;
  EmitI32(stub, cursor, 0);

  EmitCounterIncrement(stub, cursor, state.source_lookup_null_count);
  EmitBytes(stub, cursor, {0x4C, 0x89, 0x37}); // mov [rdi],r14
  EmitAbsoluteJump(stub, cursor, state.source_null_target);

  const auto healthy_offset = cursor;
  EmitAbsoluteJump(stub, cursor, state.source_healthy_target);
  return cursor == stub.size() &&
      PatchRelative32(stub, healthy_displacement, healthy_offset);
}

bool BuildVariantStub(
    StartupParticle2StageRecorderV1State &state,
    std::array<std::uint8_t, kStartupParticle2VariantStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;
  EmitCounterIncrement(stub, cursor, state.variant_lookup_null_count);
  EmitBytes(stub, cursor, {0x4C, 0x89, 0x37}); // mov [rdi],r14
  EmitBytes(stub, cursor,
            {0xC7, 0x44, 0x24, 0x30, 0x03, 0x00, 0x00, 0x00});
  EmitAbsoluteJump(stub, cursor, state.variant_null_target);
  return cursor == stub.size();
}

bool BuildBackendStub(
    StartupParticle2StageRecorderV1State &state,
    std::array<std::uint8_t, kStartupParticle2BackendStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;
  EmitCounterIncrement(stub, cursor, state.backend_creation_null_count);
  EmitBytes(stub, cursor, {0x4C, 0x89, 0x37}); // mov [rdi],r14
  EmitBytes(stub, cursor,
            {0xC7, 0x44, 0x24, 0x30, 0x03, 0x00, 0x00, 0x00});
  EmitBytes(stub, cursor, {0x48, 0x8D, 0x4D, 0xB7}); // lea rcx,[rbp-49]
  EmitAbsoluteJump(stub, cursor, state.backend_null_target);
  return cursor == stub.size();
}

template <std::size_t Size>
void BuildPatch(std::uintptr_t stub_address,
                std::array<std::uint8_t, Size> &patch) noexcept {
  static_assert(Size >= 13);
  patch.fill(0x90);
  patch[0] = 0x49;
  patch[1] = 0xBB; // mov r11, imm64
  const auto encoded = static_cast<std::uint64_t>(stub_address);
  std::memcpy(patch.data() + 2, &encoded, sizeof(encoded));
  patch[10] = 0x41;
  patch[11] = 0xFF;
  patch[12] = 0xE3; // jmp r11
}

bool Flush(StartupParticle2StageRecorderV1State &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, startup_particle2_stage_recorder_failure_flush);
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
    StartupParticle2StageRecorderV1State &state, std::uintptr_t target,
    std::size_t size, const std::uint8_t *expected,
    const std::uint8_t *desired,
    DWORD *original_protection = nullptr) noexcept {
  if (!SafeBytesEqual(target, expected, size)) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }

  DWORD previous = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context,
                             reinterpret_cast<void *>(target), size,
                             PAGE_EXECUTE_READWRITE, previous)) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  if (!IsExecutableProtection(previous)) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_protection);
    DWORD ignored = 0;
    (void)state.virtual_protect(state.memory_context,
                                reinterpret_cast<void *>(target), size,
                                previous, ignored);
    return TargetWriteResult::original_preserved;
  }
  if (original_protection != nullptr) {
    *original_protection = previous;
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
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_identity);
  }
  if (desired_flushed && !protection_restored) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_protection);
  }
  if (desired_identity && desired_flushed && protection_restored) {
    return TargetWriteResult::success;
  }

  // Re-establish the exact expected bytes before returning any install error.
  // If this cannot be proven, the owner and RX stubs remain alive.
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
    AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ProveOriginalTarget(
    StartupParticle2StageRecorderV1State &state, std::uintptr_t target,
    std::size_t size, const std::uint8_t *original,
    DWORD original_protection) noexcept {
  if (original_protection == 0 ||
      !IsExecutableProtection(original_protection) ||
      !SafeBytesEqual(target, original, size)) {
    AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
    return false;
  }

  // Byte identity alone is insufficient after an unproven rollback: the
  // processor may still execute a stale jump, or a failed protection restore
  // may have left the target writable.  Re-enter a writable transaction,
  // flush the original bytes, and explicitly restore the protection captured
  // before the first patch before ownership can be released.
  DWORD current = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            PAGE_EXECUTE_READWRITE, current);
  const bool identity = writable && SafeBytesEqual(target, original, size);
  const bool flushed = identity &&
      Flush(state, reinterpret_cast<const void *>(target), size);
  DWORD ignored = 0;
  const bool protection_restored = writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            original_protection, ignored);
  if (!writable || !protection_restored) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_target_protection);
  }
  if (!identity || !flushed || !protection_restored) {
    AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
    return false;
  }
  return true;
}

template <std::size_t Size>
bool RestorePatch(
    StartupParticle2StageRecorderV1State &state, std::uint32_t mask,
    std::uintptr_t target, const std::array<std::uint8_t, Size> &installed,
    const std::array<std::uint8_t, Size> &original,
    DWORD original_protection) noexcept {
  if ((state.patch_mask.load(std::memory_order_acquire) & mask) == 0) {
    return true;
  }
  if (SafeBytesEqual(target, original.data(), original.size())) {
    if (ProveOriginalTarget(state, target, original.size(), original.data(),
                            original_protection)) {
      state.patch_mask.fetch_and(~mask, std::memory_order_acq_rel);
      return true;
    }
    return false;
  }
  const auto result = WriteTargetTransaction(
      state, target, original.size(), installed.data(), original.data());
  if (result == TargetWriteResult::success ||
      SafeBytesEqual(target, original.data(), original.size())) {
    state.patch_mask.fetch_and(~mask, std::memory_order_acq_rel);
    return true;
  }
  AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
  return false;
}

bool RestoreAllPatches(
    StartupParticle2StageRecorderV1State &state) noexcept {
  bool restored = RestorePatch(
      state, kStartupParticle2BackendPatchMaskV1,
      state.backend_patch_target, state.installed_backend_bytes,
      state.original_backend_bytes, state.backend_original_protection);
  restored = RestorePatch(
                 state, kStartupParticle2VariantPatchMaskV1,
                 state.variant_patch_target, state.installed_variant_bytes,
                 state.original_variant_bytes,
                 state.variant_original_protection) &&
      restored;
  restored = RestorePatch(
                 state, kStartupParticle2SourcePatchMaskV1,
                 state.source_patch_target, state.installed_source_bytes,
                 state.original_source_bytes,
                 state.source_original_protection) &&
      restored;
  return restored &&
      state.patch_mask.load(std::memory_order_acquire) == 0;
}

bool ReleaseStubs(StartupParticle2StageRecorderV1State &state) noexcept {
  if (state.stub_allocation == nullptr) {
    return true;
  }
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub_allocation, 0,
                          MEM_RELEASE)) {
    AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
    return false;
  }
  state.stub_allocation = nullptr;
  return true;
}

void ClearResolvedState(
    StartupParticle2StageRecorderV1State &state) noexcept {
  state.module_base = 0;
  state.source_patch_target = 0;
  state.source_healthy_target = 0;
  state.source_null_target = 0;
  state.variant_patch_target = 0;
  state.variant_null_target = 0;
  state.backend_patch_target = 0;
  state.backend_null_target = 0;
  state.source_original_protection = 0;
  state.variant_original_protection = 0;
  state.backend_original_protection = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

void ReleaseCleanOwnership(
    StartupParticle2StageRecorderV1State &state) noexcept {
  const bool released = ReleaseStubs(state);
  if (released) {
    ClearResolvedState(state);
    g_active_recorder.store(nullptr, std::memory_order_release);
  } else {
    state.installed.store(1, std::memory_order_release);
  }
}

} // namespace

bool InstallStartupParticle2StageRecorderV1(
    StartupParticle2StageRecorderV1State &state,
    const StartupParticle2StageRecorderV1Environment &environment) noexcept {
  state.failure_flags.store(startup_particle2_stage_recorder_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        startup_particle2_stage_recorder_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.patch_mask.load(std::memory_order_acquire) != 0 ||
      state.stub_allocation != nullptr) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_already_installed);
    return false;
  }

  StartupParticle2StageRecorderV1State *expected_active = nullptr;
  if (!g_active_recorder.compare_exchange_strong(
          expected_active, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.source_patch_target = Resolve(
      environment.source_patch_target_override, environment.module_base,
      kStartupParticle2SourcePatchRvaV1);
  state.source_healthy_target = Resolve(
      environment.source_healthy_target_override, environment.module_base,
      kStartupParticle2SourceHealthyRvaV1);
  state.source_null_target = Resolve(
      environment.source_null_target_override, environment.module_base,
      kStartupParticle2SourceNullRvaV1);
  state.variant_patch_target = Resolve(
      environment.variant_patch_target_override, environment.module_base,
      kStartupParticle2VariantPatchRvaV1);
  state.variant_null_target = Resolve(
      environment.variant_null_target_override, environment.module_base,
      kStartupParticle2VariantNullRvaV1);
  state.backend_patch_target = Resolve(
      environment.backend_patch_target_override, environment.module_base,
      kStartupParticle2BackendPatchRvaV1);
  state.backend_null_target = Resolve(
      environment.backend_null_target_override, environment.module_base,
      kStartupParticle2BackendNullRvaV1);

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

  const bool resolved = state.source_patch_target != 0 &&
      state.source_healthy_target != 0 && state.source_null_target != 0 &&
      state.variant_patch_target != 0 && state.variant_null_target != 0 &&
      state.backend_patch_target != 0 && state.backend_null_target != 0;
  if (!resolved || !ExactAnchorsMatch(state, environment.offline_fixture) ||
      !SafeCopyFrom(state.source_patch_target,
                    state.original_source_bytes.data(),
                    state.original_source_bytes.size()) ||
      !SafeCopyFrom(state.variant_patch_target,
                    state.original_variant_bytes.data(),
                    state.original_variant_bytes.size()) ||
      !SafeCopyFrom(state.backend_patch_target,
                    state.original_backend_bytes.data(),
                    state.original_backend_bytes.size())) {
    AddFailure(state, startup_particle2_stage_recorder_failure_anchor);
    ClearResolvedState(state);
    g_active_recorder.store(nullptr, std::memory_order_release);
    return false;
  }

  state.patch_mask.store(0, std::memory_order_relaxed);
  state.source_lookup_null_count.store(0, std::memory_order_relaxed);
  state.variant_lookup_null_count.store(0, std::memory_order_relaxed);
  state.backend_creation_null_count.store(0, std::memory_order_relaxed);
  state.source_original_protection = 0;
  state.variant_original_protection = 0;
  state.backend_original_protection = 0;

  state.stub_allocation = virtual_alloc(
      state.memory_context, kStartupParticle2StageRecorderStubBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub_allocation == nullptr) {
    AddFailure(state, startup_particle2_stage_recorder_failure_allocation);
    ClearResolvedState(state);
    g_active_recorder.store(nullptr, std::memory_order_release);
    return false;
  }

  std::array<std::uint8_t, kStartupParticle2SourceStubBytesV1> source_stub{};
  std::array<std::uint8_t, kStartupParticle2VariantStubBytesV1> variant_stub{};
  std::array<std::uint8_t, kStartupParticle2BackendStubBytesV1> backend_stub{};
  std::array<std::uint8_t, kStartupParticle2StageRecorderStubBytesV1>
      combined_stubs{};
  if (!BuildSourceStub(state, source_stub) ||
      !BuildVariantStub(state, variant_stub) ||
      !BuildBackendStub(state, backend_stub)) {
    AddFailure(state, startup_particle2_stage_recorder_failure_allocation);
    ReleaseCleanOwnership(state);
    return false;
  }
  auto output = combined_stubs.begin();
  output = std::copy(source_stub.begin(), source_stub.end(), output);
  output = std::copy(variant_stub.begin(), variant_stub.end(), output);
  (void)std::copy(backend_stub.begin(), backend_stub.end(), output);
  if (!SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub_allocation),
                  combined_stubs.data(), combined_stubs.size())) {
    AddFailure(state, startup_particle2_stage_recorder_failure_allocation);
    ReleaseCleanOwnership(state);
    return false;
  }

  DWORD previous = 0;
  const bool stub_protected = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context, state.stub_allocation,
                            combined_stubs.size(), PAGE_EXECUTE_READ,
                            previous) &&
      previous == PAGE_READWRITE;
  const bool stub_flushed = stub_protected &&
      Flush(state, state.stub_allocation, combined_stubs.size());
  if (!stub_protected || !stub_flushed) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_stub_protection);
    ReleaseCleanOwnership(state);
    return false;
  }

  const auto stub_base =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  BuildPatch(stub_base, state.installed_source_bytes);
  BuildPatch(stub_base + kStartupParticle2SourceStubBytesV1,
             state.installed_variant_bytes);
  BuildPatch(stub_base + kStartupParticle2SourceStubBytesV1 +
                 kStartupParticle2VariantStubBytesV1,
             state.installed_backend_bytes);

  auto write_result = WriteTargetTransaction(
      state, state.source_patch_target, state.original_source_bytes.size(),
      state.original_source_bytes.data(), state.installed_source_bytes.data(),
      &state.source_original_protection);
  if (write_result == TargetWriteResult::success) {
    state.patch_mask.fetch_or(kStartupParticle2SourcePatchMaskV1,
                              std::memory_order_acq_rel);
  } else {
    if (write_result == TargetWriteResult::rollback_unproven) {
      state.patch_mask.fetch_or(kStartupParticle2SourcePatchMaskV1,
                                std::memory_order_acq_rel);
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    const bool restored = RestoreAllPatches(state);
    if (restored) {
      ReleaseCleanOwnership(state);
    } else {
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }

  write_result = WriteTargetTransaction(
      state, state.variant_patch_target, state.original_variant_bytes.size(),
      state.original_variant_bytes.data(),
      state.installed_variant_bytes.data(),
      &state.variant_original_protection);
  if (write_result == TargetWriteResult::success) {
    state.patch_mask.fetch_or(kStartupParticle2VariantPatchMaskV1,
                              std::memory_order_acq_rel);
  } else {
    if (write_result == TargetWriteResult::rollback_unproven) {
      state.patch_mask.fetch_or(kStartupParticle2VariantPatchMaskV1,
                                std::memory_order_acq_rel);
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    const bool restored = RestoreAllPatches(state);
    if (restored) {
      ReleaseCleanOwnership(state);
    } else {
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }

  write_result = WriteTargetTransaction(
      state, state.backend_patch_target, state.original_backend_bytes.size(),
      state.original_backend_bytes.data(),
      state.installed_backend_bytes.data(),
      &state.backend_original_protection);
  if (write_result == TargetWriteResult::success) {
    state.patch_mask.fetch_or(kStartupParticle2BackendPatchMaskV1,
                              std::memory_order_acq_rel);
  } else {
    if (write_result == TargetWriteResult::rollback_unproven) {
      state.patch_mask.fetch_or(kStartupParticle2BackendPatchMaskV1,
                                std::memory_order_acq_rel);
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    const bool restored = RestoreAllPatches(state);
    if (restored) {
      ReleaseCleanOwnership(state);
    } else {
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }

  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallStartupParticle2StageRecorderV1(
    StartupParticle2StageRecorderV1State &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_recorder.load(std::memory_order_acquire) != &state ||
      state.stub_allocation == nullptr) {
    AddFailure(state,
               startup_particle2_stage_recorder_failure_already_installed);
    return false;
  }
  if (!RestoreAllPatches(state)) {
    AddFailure(state, startup_particle2_stage_recorder_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  const bool released = ReleaseStubs(state);
  if (!released) {
    state.installed.store(1, std::memory_order_release);
    return false;
  }
  ClearResolvedState(state);
  g_active_recorder.store(nullptr, std::memory_order_release);
  return true;
}

StartupParticle2StageRecorderV1Diagnostics
ReadStartupParticle2StageRecorderV1Diagnostics(
    const StartupParticle2StageRecorderV1State &state) noexcept {
  StartupParticle2StageRecorderV1Diagnostics output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.patch_mask = state.patch_mask.load(std::memory_order_acquire);
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.source_lookup_null_count =
      state.source_lookup_null_count.load(std::memory_order_acquire);
  output.variant_lookup_null_count =
      state.variant_lookup_null_count.load(std::memory_order_acquire);
  output.backend_creation_null_count =
      state.backend_creation_null_count.load(std::memory_order_acquire);
  return output;
}

} // namespace xar::bridge

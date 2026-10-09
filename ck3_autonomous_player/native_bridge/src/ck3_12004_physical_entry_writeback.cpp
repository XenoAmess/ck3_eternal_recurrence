#include "xar_bridge/ck3_12004_physical_entry_writeback.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, kPhysicalEntryWriterPatchBytes12004> kAnchor{
    0x40, 0x53, 0x48, 0x83, 0xEC, 0x60, 0x4C, 0x8B,
    0x05, 0x93, 0x78, 0x6C, 0x03, 0x4C, 0x8B, 0xCA};
std::atomic<PhysicalEntryWriterOriginal12004> g_original{nullptr};
std::atomic<PhysicalEntryWritebackDetourState12004 *> g_active{nullptr};

template <class Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
void Jump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}
auto HookPatch() noexcept {
  std::array<std::uint8_t, kPhysicalEntryWriterPatchBytes12004> patch;
  patch.fill(0x90);
  Jump(patch.data(), reinterpret_cast<std::uintptr_t>(&XarPhysicalEntryWriterHook12004));
  return patch;
}
void Fail(PhysicalEntryWritebackDetourState12004 &state, std::uint32_t flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}
bool DefaultFree(void *, void *address, std::size_t bytes, DWORD kind) noexcept {
  return VirtualFree(address, bytes, kind) != FALSE;
}
void *DefaultAlloc(void *, std::size_t bytes, DWORD kind, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, bytes, kind, protection);
}
bool DefaultProtect(void *, void *address, std::size_t bytes, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, bytes, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t bytes) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, bytes) != FALSE;
}
bool WritePatch(PhysicalEntryWritebackDetourState12004 &state,
    const std::array<std::uint8_t, kPhysicalEntryWriterPatchBytes12004> &expected,
    const std::array<std::uint8_t, kPhysicalEntryWriterPatchBytes12004> &desired) noexcept {
  auto *address = reinterpret_cast<void *>(state.writer_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(address, expected.data(), expected.size()) == 0;
      })) { Fail(state, actual_loss_install_anchor); return false; }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, address, expected.size(),
                            PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_loss_install_protection); return false;
  }
  std::memcpy(address, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(state.memory_context, address, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, address, desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_loss_install_protection : actual_loss_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, address, expected.size(),
                                             PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(address, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, address, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, address, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored) Fail(state, actual_loss_install_rollback);
  return false;
}
} // namespace

std::array<std::uint8_t, kPhysicalEntryWriterTrampolineBytes12004>
BuildPhysicalEntryWriterTrampoline12004(std::uintptr_t image_base) noexcept {
  std::array<std::uint8_t, kPhysicalEntryWriterTrampolineBytes12004> result{};
  // Preserve push RBX / sub RSP,60. MOV's absolute expansion changes neither
  // flags nor any register the original RIP-relative load did not overwrite.
  std::memcpy(result.data(), kAnchor.data(), 6);
  result[6] = 0x49; result[7] = 0xB8; // mov r8, imm64
  const std::uintptr_t slot = image_base + kPhysicalEntryWriterRegimentSlotRva12004;
  std::memcpy(result.data() + 8, &slot, sizeof(slot));
  constexpr std::array<std::uint8_t, 6> tail{0x4D, 0x8B, 0x00, 0x4C, 0x8B, 0xCA};
  std::memcpy(result.data() + 16, tail.data(), tail.size());
  Jump(result.data() + 22, image_base + kPhysicalEntryWriterRva12004 + kAnchor.size());
  return result;
}

bool InitializePhysicalEntryWritebackFixture12004(PhysicalEntryWriterOriginal12004 original) noexcept {
  if (original == nullptr || g_active.load(std::memory_order_acquire) != nullptr) return false;
  g_original.store(original, std::memory_order_release);
  return true;
}

std::uint64_t InvokePhysicalEntryWriter12004(void *entry, void *province) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0;
  KnightStatPhysicalEntryScope12004 scope(entry, province);
  const std::uint64_t result = original(entry, province);
  scope.Complete(result);
  return result;
}

bool InstallPhysicalEntryWriteback12004(PhysicalEntryWritebackDetourState12004 &state,
    const PhysicalEntryWritebackInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_loss_install_exact_build); return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence); return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  PhysicalEntryWritebackDetourState12004 *expected = nullptr;
  if (!g_active.compare_exchange_strong(expected, &state)) {
    Fail(state, actual_loss_install_already_installed); return false;
  }
  state.writer_target = environment.writer_target_override != 0
      ? environment.writer_target_override
      : environment.bindings.image_base + kPhysicalEntryWriterRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ? environment.virtual_free_override : DefaultFree;
  state.virtual_protect = environment.virtual_protect_override ? environment.virtual_protect_override : DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override
      ? environment.flush_instruction_cache_override : DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.writer_target),
                           kAnchor.data(), kAnchor.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor); g_active.store(nullptr); return false;
  }
  const auto allocate = environment.virtual_alloc_override ? environment.virtual_alloc_override : DefaultAlloc;
  const auto trampoline = BuildPhysicalEntryWriterTrampoline12004(environment.bindings.image_base);
  state.writer_trampoline = allocate(state.memory_context, trampoline.size(),
                                    MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.writer_trampoline == nullptr) {
    Fail(state, actual_loss_install_allocation); g_active.store(nullptr); return false;
  }
  std::memcpy(state.writer_trampoline, trampoline.data(), trampoline.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context, state.writer_trampoline,
      trampoline.size(), PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.writer_trampoline, trampoline.size());
  if (!flushed) {
    Fail(state, executable ? actual_loss_install_flush : actual_loss_install_protection);
    (void)state.virtual_free(state.memory_context, state.writer_trampoline, 0, MEM_RELEASE);
    state.writer_trampoline = nullptr; g_active.store(nullptr); return false;
  }
  g_original.store(reinterpret_cast<PhysicalEntryWriterOriginal12004>(state.writer_trampoline),
                   std::memory_order_release);
  if (!WritePatch(state, kAnchor, HookPatch())) {
    g_original.store(nullptr);
    (void)state.virtual_free(state.memory_context, state.writer_trampoline, 0, MEM_RELEASE);
    state.writer_trampoline = nullptr; g_active.store(nullptr); return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPhysicalEntryWriteback12004(PhysicalEntryWritebackDetourState12004 &state,
                                       bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence); return false;
  }
  if (!WritePatch(state, HookPatch(), kAnchor)) return false;
  state.installed.store(0, std::memory_order_release);
  g_original.store(nullptr); g_active.store(nullptr);
  const bool freed = state.virtual_free(state.memory_context, state.writer_trampoline, 0, MEM_RELEASE);
  if (freed) state.writer_trampoline = nullptr;
  return freed;
}

extern "C" __declspec(noinline) std::uint64_t __fastcall
XarPhysicalEntryWriterHook12004(void *entry, void *province) noexcept {
  return InvokePhysicalEntryWriter12004(entry, province);
}
} // namespace xar::ck3_12004

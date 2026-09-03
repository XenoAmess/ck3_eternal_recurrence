#include "xar_bridge/cold_map_vfs_observer_v1.hpp"

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8, "cold-map VFS observer is x64-only");

constexpr std::size_t kStubBytes = 128;
constexpr std::array<std::size_t, 3> kPatchSizes{
    kColdMapVfsCtorPatchBytesV1, kColdMapVfsVariantPatchBytesV1,
    kColdMapVfsPollPatchBytesV1};
constexpr std::array<std::uintptr_t, 3> kPatchRvas{
    kColdMapVfsCtorPatchRvaV1, kColdMapVfsVariantPatchRvaV1,
    kColdMapVfsPollPatchRvaV1};
constexpr std::array<std::uintptr_t, 3> kContinueRvas{
    kColdMapVfsCtorContinueRvaV1, kColdMapVfsVariantContinueRvaV1,
    kColdMapVfsPollContinueRvaV1};
constexpr std::array<std::uint8_t, 15> kCtorAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
    0x24, 0x18, 0x48, 0x89, 0x7C, 0x24, 0x20};
constexpr std::array<std::uint8_t, 15> kVariantAnchor{
    0x49, 0x8D, 0x4E, 0x38, 0xE8, 0x49, 0x0D,
    0x00, 0x00, 0x80, 0x7C, 0x24, 0x40, 0x01, 0x00};
constexpr std::array<std::uint8_t, 15> kPollAnchor{
    0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x0F, 0xB6,
    0x41, 0x0C, 0x48, 0x8B, 0xD9, 0x3C, 0x0A};

std::atomic<ColdMapVfsObserverV1State *> g_active{nullptr};

void AddFailure(ColdMapVfsObserverV1State &state,
                ColdMapVfsObserverFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

void *DefaultAlloc(void *, std::size_t n, DWORD t, DWORD p) noexcept {
  return VirtualAlloc(nullptr, n, t, p);
}
bool DefaultFree(void *, void *p, std::size_t n, DWORD t) noexcept {
  return VirtualFree(p, n, t) != FALSE;
}
bool DefaultProtect(void *, void *p, std::size_t n, DWORD next,
                    DWORD &old) noexcept {
  old = 0;
  return VirtualProtect(p, n, next, &old) != FALSE;
}
bool DefaultFlush(void *, const void *p, std::size_t n) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), p, n) != FALSE;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t base, std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  if (base == 0 || rva > std::numeric_limits<std::uintptr_t>::max() - base)
    return 0;
  return base + rva;
}

bool SafeCopyFrom(std::uintptr_t p, void *out, std::size_t n) noexcept {
  if (p == 0 || out == nullptr || n == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, reinterpret_cast<const void *>(p), n);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
bool SafeCopyTo(std::uintptr_t p, const void *in, std::size_t n) noexcept {
  if (p == 0 || in == nullptr || n == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(p), in, n);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}
bool SafeEqual(std::uintptr_t p, const void *expected, std::size_t n) noexcept {
  std::array<std::uint8_t, 15> actual{};
  return n <= actual.size() && SafeCopyFrom(p, actual.data(), n) &&
      std::memcmp(actual.data(), expected, n) == 0;
}
template <typename T> T SafeLoad(std::uintptr_t p) noexcept {
  T value{};
  (void)SafeCopyFrom(p, &value, sizeof(value));
  return value;
}
bool Executable(DWORD p) noexcept {
  return p == PAGE_EXECUTE_READ || p == PAGE_EXECUTE_READWRITE ||
      p == PAGE_EXECUTE_WRITECOPY;
}

template <std::size_t N>
void Emit(std::array<std::uint8_t, N> &b, std::size_t &c,
          std::initializer_list<std::uint8_t> bytes) noexcept {
  for (auto x : bytes) b[c++] = x;
}
template <std::size_t N>
void EmitU64(std::array<std::uint8_t, N> &b, std::size_t &c,
             std::uintptr_t x) noexcept {
  const auto value = static_cast<std::uint64_t>(x);
  std::memcpy(b.data() + c, &value, 8);
  c += 8;
}
template <std::size_t N>
void EmitJump(std::array<std::uint8_t, N> &b, std::size_t &c,
              std::uintptr_t x) noexcept {
  Emit(b, c, {0xFF, 0x25, 0, 0, 0, 0});
  EmitU64(b, c, x);
}
template <std::size_t N>
void EmitCallRax(std::array<std::uint8_t, N> &b, std::size_t &c,
                 std::uintptr_t x) noexcept {
  Emit(b, c, {0x48, 0xB8});
  EmitU64(b, c, x);
  Emit(b, c, {0xFF, 0xD0});
}
template <std::size_t N>
void EmitPreserve(std::array<std::uint8_t, N> &b, std::size_t &c) noexcept {
  Emit(b, c, {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
              0x41, 0x51, 0x41, 0x52, 0x41, 0x53,
              0x48, 0x83, 0xEC, 0x28});
}
template <std::size_t N>
void EmitRestore(std::array<std::uint8_t, N> &b, std::size_t &c) noexcept {
  Emit(b, c, {0x48, 0x83, 0xC4, 0x28,
              0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
              0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

template <std::size_t N>
void EmitPreserveAtAlignedSite(std::array<std::uint8_t, N> &b,
                               std::size_t &c) noexcept {
  Emit(b, c, {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
              0x41, 0x51, 0x41, 0x52, 0x41, 0x53,
              0x48, 0x83, 0xEC, 0x20});
}

template <std::size_t N>
void EmitRestoreAtAlignedSite(std::array<std::uint8_t, N> &b,
                              std::size_t &c) noexcept {
  Emit(b, c, {0x48, 0x83, 0xC4, 0x20,
              0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
              0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void ColdMapVfsCtorThunkV1(std::uintptr_t descriptor) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) RecordColdMapVfsCtorV1(*state, descriptor);
}
extern "C" void ColdMapVfsVariantThunkV1(std::uintptr_t variant) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) RecordColdMapVfsVariantV1(*state, variant);
}
extern "C" void ColdMapVfsPollThunkV1(std::uintptr_t object) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) RecordColdMapVfsPollV1(*state, object);
}

std::size_t BuildStub(ColdMapVfsObserverV1State &state, std::size_t index,
                      std::array<std::uint8_t, kStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t c = 0;
  if (index == 1) {
    Emit(stub, c, {0x49, 0x8D, 0x4E, 0x38});
    Emit(stub, c, {0x49, 0xBB});
    EmitU64(stub, c, state.variant_move_target);
    Emit(stub, c, {0x41, 0xFF, 0xD3});
  }
  if (index == 1)
    EmitPreserveAtAlignedSite(stub, c);
  else
    EmitPreserve(stub, c);
  if (index == 0)
    Emit(stub, c, {0x48, 0x8B, 0x4C, 0x24, 0x48}); // original RDX
  else if (index == 1)
    Emit(stub, c, {0x49, 0x8D, 0x4E, 0x38});
  else
    Emit(stub, c, {0x48, 0x8B, 0x4C, 0x24, 0x50}); // original RCX
  EmitCallRax(stub, c, index == 0
      ? reinterpret_cast<std::uintptr_t>(&ColdMapVfsCtorThunkV1)
      : index == 1
          ? reinterpret_cast<std::uintptr_t>(&ColdMapVfsVariantThunkV1)
          : reinterpret_cast<std::uintptr_t>(&ColdMapVfsPollThunkV1));
  if (index == 1)
    EmitRestoreAtAlignedSite(stub, c);
  else
    EmitRestore(stub, c);
  if (index == 0) {
    for (std::size_t i = 0; i < kPatchSizes[0]; ++i) stub[c++] = kCtorAnchor[i];
  } else if (index == 1) {
    Emit(stub, c, {0x80, 0x7C, 0x24, 0x40, 0x01});
  } else {
    for (std::size_t i = 0; i < kPatchSizes[2]; ++i) stub[c++] = kPollAnchor[i];
  }
  EmitJump(stub, c, state.hooks[index].continue_target);
  return c;
}

void BuildPatch(ColdMapVfsHookStateV1 &hook) noexcept {
  hook.installed_patch.fill(0x90);
  std::size_t c = 0;
  EmitJump(hook.installed_patch, c,
           reinterpret_cast<std::uintptr_t>(hook.stub));
}

const std::uint8_t *Anchor(std::size_t index) noexcept {
  if (index == 0) return kCtorAnchor.data();
  if (index == 1) return kVariantAnchor.data();
  return kPollAnchor.data();
}

bool Flush(ColdMapVfsObserverV1State &s, const void *p, std::size_t n) noexcept {
  if (s.flush_instruction_cache == nullptr ||
      !s.flush_instruction_cache(s.memory_context, p, n)) {
    AddFailure(s, cold_map_vfs_observer_failure_flush);
    return false;
  }
  return true;
}

bool WriteHook(ColdMapVfsObserverV1State &s, ColdMapVfsHookStateV1 &h,
               const std::uint8_t *expected, const std::uint8_t *next) noexcept {
  if (!SafeEqual(h.patch_target, expected, h.patch_size)) {
    AddFailure(s, cold_map_vfs_observer_failure_target_identity);
    return false;
  }
  DWORD old = 0;
  if (s.virtual_protect == nullptr ||
      !s.virtual_protect(s.memory_context,
                         reinterpret_cast<void *>(h.patch_target), h.patch_size,
                         PAGE_EXECUTE_READWRITE, old)) {
    AddFailure(s, cold_map_vfs_observer_failure_target_protection);
    return false;
  }
  if (!Executable(old)) {
    DWORD ignored = 0;
    (void)s.virtual_protect(s.memory_context,
                            reinterpret_cast<void *>(h.patch_target), h.patch_size,
                            old, ignored);
    AddFailure(s, cold_map_vfs_observer_failure_target_protection);
    return false;
  }
  const bool copied = SafeCopyTo(h.patch_target, next, h.patch_size);
  const bool identical = copied && SafeEqual(h.patch_target, next, h.patch_size);
  const bool flushed = identical && Flush(
      s, reinterpret_cast<void *>(h.patch_target), h.patch_size);
  DWORD ignored = 0;
  const bool restored = s.virtual_protect(
      s.memory_context, reinterpret_cast<void *>(h.patch_target), h.patch_size,
      old, ignored);
  if (identical && flushed && restored) return true;
  AddFailure(s, cold_map_vfs_observer_failure_rollback);
  DWORD rollback_old = 0;
  if (s.virtual_protect(s.memory_context,
                        reinterpret_cast<void *>(h.patch_target), h.patch_size,
                        PAGE_EXECUTE_READWRITE, rollback_old)) {
    (void)SafeCopyTo(h.patch_target, expected, h.patch_size);
    (void)Flush(s, reinterpret_cast<void *>(h.patch_target), h.patch_size);
    (void)s.virtual_protect(s.memory_context,
                            reinterpret_cast<void *>(h.patch_target), h.patch_size,
                            old, ignored);
  }
  return false;
}

bool HasOverrides(const ColdMapVfsObserverEnvironmentV1 &e) noexcept {
  return e.patch_target_overrides != std::array<std::uintptr_t, 3>{} ||
      e.continue_target_overrides != std::array<std::uintptr_t, 3>{} ||
      e.variant_move_target_override != 0 || e.memory_context != nullptr ||
      e.virtual_alloc_override != nullptr || e.virtual_free_override != nullptr ||
      e.virtual_protect_override != nullptr ||
      e.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(ColdMapVfsObserverV1State &s) noexcept {
  s.module_base = 0;
  s.variant_move_target = 0;
  s.memory_context = nullptr;
  s.virtual_free = nullptr;
  s.virtual_protect = nullptr;
  s.flush_instruction_cache = nullptr;
  for (auto &h : s.hooks) {
    h.patch_target = h.continue_target = 0;
    h.patch_size = 0;
    h.stub = nullptr;
  }
}

} // namespace

void RecordColdMapVfsCtorV1(ColdMapVfsObserverV1State &s,
                            std::uintptr_t d) noexcept {
  const auto data = SafeLoad<std::uintptr_t>(d);
  s.ctor_descriptor.store(d, std::memory_order_relaxed);
  s.ctor_data.store(data, std::memory_order_relaxed);
  s.ctor_length.store(SafeLoad<std::uint32_t>(d + 8), std::memory_order_relaxed);
  s.ctor_flag.store(SafeLoad<std::uint8_t>(d + 12), std::memory_order_relaxed);
  s.ctor_word0.store(SafeLoad<std::uint64_t>(data), std::memory_order_relaxed);
  s.ctor_word1.store(SafeLoad<std::uint64_t>(data + 8), std::memory_order_relaxed);
  s.ctor_count.fetch_add(1, std::memory_order_release);
}

void RecordColdMapVfsVariantV1(ColdMapVfsObserverV1State &s,
                               std::uintptr_t v) noexcept {
  const auto payload = SafeLoad<std::uintptr_t>(v);
  s.variant_address.store(v, std::memory_order_relaxed);
  s.variant_tag.store(SafeLoad<std::uint8_t>(v + 0x20), std::memory_order_relaxed);
  s.variant_payload.store(payload, std::memory_order_relaxed);
  s.variant_length.store(SafeLoad<std::uint32_t>(v + 0x10), std::memory_order_relaxed);
  s.variant_capacity.store(SafeLoad<std::uint32_t>(v + 0x18), std::memory_order_relaxed);
  s.variant_word0.store(SafeLoad<std::uint64_t>(payload), std::memory_order_relaxed);
  s.variant_word1.store(SafeLoad<std::uint64_t>(payload + 8), std::memory_order_relaxed);
  s.variant_count.fetch_add(1, std::memory_order_release);
}

void RecordColdMapVfsPollV1(ColdMapVfsObserverV1State &s,
                            std::uintptr_t o) noexcept {
  const auto v = o + 0x38;
  const auto payload = SafeLoad<std::uintptr_t>(v);
  s.poll_object.store(o, std::memory_order_relaxed);
  s.poll_state.store(SafeLoad<std::uint8_t>(o + 0x0C), std::memory_order_relaxed);
  s.poll_aux_state.store(SafeLoad<std::uint8_t>(o + 0x0D), std::memory_order_relaxed);
  s.poll_variant_tag.store(SafeLoad<std::uint8_t>(v + 0x20), std::memory_order_relaxed);
  s.poll_payload.store(payload, std::memory_order_relaxed);
  s.poll_length.store(SafeLoad<std::uint32_t>(v + 0x10), std::memory_order_relaxed);
  s.poll_capacity.store(SafeLoad<std::uint32_t>(v + 0x18), std::memory_order_relaxed);
  s.poll_word0.store(SafeLoad<std::uint64_t>(payload), std::memory_order_relaxed);
  s.poll_word1.store(SafeLoad<std::uint64_t>(payload + 8), std::memory_order_relaxed);
  s.poll_count.fetch_add(1, std::memory_order_release);
}

bool InstallColdMapVfsObserverV1(
    ColdMapVfsObserverV1State &s,
    const ColdMapVfsObserverEnvironmentV1 &e) noexcept {
  if (!e.exact_build_admitted) {
    AddFailure(s, cold_map_vfs_observer_failure_exact_build);
    return false;
  }
  if (!e.primary_thread_suspended_proven) {
    AddFailure(s, cold_map_vfs_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!e.offline_fixture && HasOverrides(e)) {
    AddFailure(s, cold_map_vfs_observer_failure_unsupported_override);
    return false;
  }
  if (s.installed.load(std::memory_order_acquire) != 0 ||
      g_active.load(std::memory_order_acquire) != nullptr) {
    AddFailure(s, cold_map_vfs_observer_failure_already_installed);
    return false;
  }
  s.module_base = e.module_base;
  s.variant_move_target = Resolve(e.variant_move_target_override, e.module_base,
                                  kColdMapVfsVariantMoveRvaV1);
  for (std::size_t i = 0; i < 3; ++i) {
    auto &h = s.hooks[i];
    h.patch_size = kPatchSizes[i];
    h.patch_target = Resolve(e.patch_target_overrides[i], e.module_base,
                             kPatchRvas[i]);
    h.continue_target = Resolve(e.continue_target_overrides[i], e.module_base,
                                kContinueRvas[i]);
    if (h.patch_target == 0 || h.continue_target == 0 ||
        !SafeEqual(h.patch_target, Anchor(i), h.patch_size) ||
        !SafeCopyFrom(h.patch_target, h.original.data(), h.patch_size)) {
      AddFailure(s, cold_map_vfs_observer_failure_anchor);
      ClearRuntime(s);
      return false;
    }
  }
  if (s.variant_move_target == 0) {
    AddFailure(s, cold_map_vfs_observer_failure_anchor);
    ClearRuntime(s);
    return false;
  }
  auto alloc = e.virtual_alloc_override != nullptr
      ? e.virtual_alloc_override : &DefaultAlloc;
  s.virtual_free = e.virtual_free_override != nullptr
      ? e.virtual_free_override : &DefaultFree;
  s.virtual_protect = e.virtual_protect_override != nullptr
      ? e.virtual_protect_override : &DefaultProtect;
  s.flush_instruction_cache = e.flush_instruction_cache_override != nullptr
      ? e.flush_instruction_cache_override : &DefaultFlush;
  s.memory_context = e.memory_context;
  for (std::size_t i = 0; i < 3; ++i) {
    auto &h = s.hooks[i];
    h.stub = alloc(s.memory_context, kStubBytes, MEM_RESERVE | MEM_COMMIT,
                   PAGE_READWRITE);
    if (h.stub == nullptr) {
      AddFailure(s, cold_map_vfs_observer_failure_allocation);
      (void)UninstallColdMapVfsObserverV1(s);
      return false;
    }
    std::array<std::uint8_t, kStubBytes> stub{};
    const auto used = BuildStub(s, i, stub);
    if (used == 0 || used > stub.size() ||
        !SafeCopyTo(reinterpret_cast<std::uintptr_t>(h.stub), stub.data(), used)) {
      AddFailure(s, cold_map_vfs_observer_failure_allocation);
      (void)UninstallColdMapVfsObserverV1(s);
      return false;
    }
    DWORD old = 0;
    if (!s.virtual_protect(s.memory_context, h.stub, kStubBytes,
                           PAGE_EXECUTE_READ, old) ||
        !Flush(s, h.stub, used)) {
      AddFailure(s, cold_map_vfs_observer_failure_stub_protection);
      (void)UninstallColdMapVfsObserverV1(s);
      return false;
    }
    BuildPatch(h);
  }
  g_active.store(&s, std::memory_order_release);
  for (std::size_t i = 0; i < 3; ++i) {
    auto &h = s.hooks[i];
    if (!WriteHook(s, h, h.original.data(), h.installed_patch.data())) {
      for (std::size_t j = i; j-- > 0;) {
        auto &old = s.hooks[j];
        if (WriteHook(s, old, old.installed_patch.data(), old.original.data()))
          s.installed_mask.fetch_and(~(1U << j), std::memory_order_release);
      }
      (void)UninstallColdMapVfsObserverV1(s);
      return false;
    }
    s.installed_mask.fetch_or(1U << i, std::memory_order_release);
  }
  s.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallColdMapVfsObserverV1(ColdMapVfsObserverV1State &s) noexcept {
  bool ok = true;
  for (std::size_t i = 3; i-- > 0;) {
    auto &h = s.hooks[i];
    if ((s.installed_mask.load(std::memory_order_acquire) & (1U << i)) != 0) {
      if (WriteHook(s, h, h.installed_patch.data(), h.original.data()))
        s.installed_mask.fetch_and(~(1U << i), std::memory_order_release);
      else
        ok = false;
    }
  }
  if (s.installed_mask.load(std::memory_order_acquire) != 0) return false;
  g_active.store(nullptr, std::memory_order_release);
  for (auto &h : s.hooks) {
    if (h.stub != nullptr && (s.virtual_free == nullptr ||
        !s.virtual_free(s.memory_context, h.stub, 0, MEM_RELEASE))) {
      AddFailure(s, cold_map_vfs_observer_failure_rollback);
      ok = false;
    } else {
      h.stub = nullptr;
    }
  }
  s.installed.store(0, std::memory_order_release);
  if (ok) ClearRuntime(s);
  return ok;
}

ColdMapVfsObserverV1Diagnostics ReadColdMapVfsObserverV1Diagnostics(
    const ColdMapVfsObserverV1State &s) noexcept {
  ColdMapVfsObserverV1Diagnostics d{};
  d.installed = s.installed.load(std::memory_order_acquire) != 0;
  d.installed_mask = s.installed_mask.load(std::memory_order_acquire);
  d.failure_flags = s.failure_flags.load(std::memory_order_acquire);
#define XAR_LOAD(name) d.name = s.name.load(std::memory_order_acquire)
  XAR_LOAD(ctor_count); XAR_LOAD(ctor_descriptor); XAR_LOAD(ctor_data);
  XAR_LOAD(ctor_length); XAR_LOAD(ctor_flag); XAR_LOAD(ctor_word0); XAR_LOAD(ctor_word1);
  XAR_LOAD(variant_count); XAR_LOAD(variant_address); XAR_LOAD(variant_tag);
  XAR_LOAD(variant_payload); XAR_LOAD(variant_length); XAR_LOAD(variant_capacity);
  XAR_LOAD(variant_word0); XAR_LOAD(variant_word1);
  XAR_LOAD(poll_count); XAR_LOAD(poll_object); XAR_LOAD(poll_state);
  XAR_LOAD(poll_aux_state); XAR_LOAD(poll_variant_tag); XAR_LOAD(poll_payload);
  XAR_LOAD(poll_length); XAR_LOAD(poll_capacity); XAR_LOAD(poll_word0); XAR_LOAD(poll_word1);
#undef XAR_LOAD
  return d;
}

} // namespace xar::bridge

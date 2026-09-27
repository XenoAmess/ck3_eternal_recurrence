#include "xar_bridge/combat_advantage_components_observer_v1.hpp"

#include <intrin.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::uintptr_t, 4> kRvas{
    0x2308D50, 0x2307CB0, 0x2307680, 0x2307230};
constexpr std::array<std::uint8_t, 15> kCacheBytes{
    0x48,0x89,0x5C,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57,0x48,0x83,0xEC,0x20};
constexpr std::array<std::uint8_t, 16> kSideBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,0x56,0x57,0x41,0x54,0x41,0x56};
constexpr std::array<std::uint8_t, 15> kCommanderBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7C,0x24,0x20};
constexpr std::array<std::uint8_t, 15> kAggregatorBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
constexpr std::size_t kTrampolineBytes = 64;

using CacheFn = void(__fastcall *)(void *);
using SideFn = std::int64_t *(__fastcall *)(void *, std::int64_t *,
                                             std::int32_t, void *);
using HelperFn = std::int64_t *(__fastcall *)(void *, void *, void *,
                                               std::int32_t, std::int32_t,
                                               void *);
std::atomic<AdvantageComponentObserverV1 *> g_observer{nullptr};
CacheFn g_cache_original = nullptr;
SideFn g_side_original = nullptr;
HelperFn g_commander_original = nullptr;
HelperFn g_aggregator_original = nullptr;

struct CacheContext {
  AdvantageComponentObserverV1 *observer = nullptr;
  AdvantageMaterializationV1 *record = nullptr;
  std::uint32_t next_side = 0;
  CacheContext *prior = nullptr;
};
struct SideContext {
  CacheContext *cache = nullptr;
  AdvantageSideComponentsV1 *record = nullptr;
  SideContext *prior = nullptr;
};
thread_local CacheContext *g_cache_context = nullptr;
thread_local SideContext *g_side_context = nullptr;

template <typename T> T Read(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::uint8_t *>(base) + offset,
              sizeof(value));
  return value;
}

bool SumExact(std::int64_t a, std::int64_t b, std::int64_t c,
              std::int64_t expected) noexcept {
  const auto can_add = [](std::int64_t x, std::int64_t y) {
    return (y <= 0 || x <= std::numeric_limits<std::int64_t>::max() - y) &&
           (y >= 0 || x >= std::numeric_limits<std::int64_t>::min() - y);
  };
  if (!can_add(a, b)) return false;
  const auto partial = a + b;
  return can_add(partial, c) && partial + c == expected;
}

void Fail(AdvantageComponentObserverV1 *observer,
          std::uint32_t bit) noexcept {
  if (observer != nullptr)
    observer->failure_flags.fetch_or(bit, std::memory_order_relaxed);
}

void __fastcall CacheHook(void *combat) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const observer = g_observer.load(std::memory_order_acquire);
  if (observer == nullptr || !observer->armed.load(std::memory_order_acquire) ||
      observer->combat != reinterpret_cast<std::uintptr_t>(combat)) {
    g_cache_original(combat);
    return;
  }
  if (Read<std::uintptr_t>(
          reinterpret_cast<const void *>(observer->current_date_slot), 0) !=
      observer->current_date_object) {
    Fail(observer, 128);
    g_cache_original(combat);
    return;
  }
  const auto ordinal = observer->count.fetch_add(1, std::memory_order_acq_rel);
  if (ordinal >= observer->records.size()) {
    Fail(observer, 1);
    g_cache_original(combat);
    return;
  }
  auto &record = observer->records[ordinal];
  record.ordinal = ordinal;
  record.thread_id = GetCurrentThreadId();
  if (caller < observer->module_base ||
      caller - observer->module_base >
          std::numeric_limits<std::uint32_t>::max()) {
    Fail(observer, 256);
  } else {
    record.caller_rva = static_cast<std::uint32_t>(
        caller - observer->module_base);
  }
  record.combat_id = Read<std::int32_t>(combat, 0x08);
  record.date_raw = Read<std::int32_t>(
      reinterpret_cast<const void *>(observer->current_date_object), 0x08);
  record.base_raw = Read<std::int64_t>(combat, 0x6C8);
  if (record.combat_id != observer->combat_id) Fail(observer, 2);
  CacheContext context{observer, &record, 0, g_cache_context};
  g_cache_context = &context;
  g_cache_original(combat);
  g_cache_context = context.prior;
  record.resolved_raw = Read<std::int64_t>(combat, 0x710);
  const auto &left = record.sides[0];
  const auto &right = record.sides[1];
  record.complete = context.next_side == 2 && left.complete && right.complete &&
      right.total_raw != std::numeric_limits<std::int64_t>::min() &&
      SumExact(record.base_raw, left.total_raw, -right.total_raw,
               record.resolved_raw);
  if (!record.complete) Fail(observer, 4);
}

std::int64_t *__fastcall SideHook(void *combat, std::int64_t *output,
                                   std::int32_t side_index,
                                   void *target_context) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const context = g_cache_context;
  if (context == nullptr || context->observer == nullptr ||
      context->observer->combat != reinterpret_cast<std::uintptr_t>(combat))
    return g_side_original(combat, output, side_index, target_context);
  auto *const observer = context->observer;
  if (target_context != nullptr || side_index < 0 || side_index > 1 ||
      caller != observer->module_base +
          (side_index == 0 ? 0x2308DB4 : 0x2308DCB) ||
      context->next_side != static_cast<std::uint32_t>(side_index)) {
    Fail(observer, 8);
    return g_side_original(combat, output, side_index, target_context);
  }
  auto &record = context->record->sides[side_index];
  record.side_index = side_index;
  record.roll = Read<std::int32_t>(combat, 0x6D0 + 4U * side_index);
  record.roll_raw = static_cast<std::int64_t>(record.roll) * 100000;
  record.commander_character_id = Read<std::int32_t>(
      combat, 0x94 + 0x348U * side_index);
  SideContext side{context, &record, g_side_context};
  g_side_context = &side;
  auto *const result = g_side_original(combat, output, side_index,
                                        target_context);
  g_side_context = side.prior;
  record.total_raw = output != nullptr ? *output : 0;
  record.complete = result == output && record.helper_calls == 2 &&
      SumExact(record.roll_raw, record.commander_raw,
               record.aggregator_raw, record.total_raw);
  if (!record.complete) Fail(observer, 16);
  ++context->next_side;
  return result;
}

std::int64_t *__fastcall CommanderHook(
    void *combat, void *arg2, void *arg3, std::int32_t side_index,
    std::int32_t arg5, void *arg6) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const value = g_commander_original(combat, arg2, arg3,
                                           side_index, arg5, arg6);
  auto *const side = g_side_context;
  if (side != nullptr && side->record != nullptr) {
    if (value != nullptr &&
        caller == side->cache->observer->module_base + 0x2307E8D &&
        side->record->side_index == side_index &&
        side->record->helper_calls == 0) {
      side->record->commander_raw = *value;
      side->record->helper_calls = 1;
    } else Fail(side->cache->observer, 32);
  }
  return value;
}

std::int64_t *__fastcall AggregatorHook(
    void *combat, void *arg2, void *arg3, std::int32_t side_index,
    std::int32_t arg5, void *arg6) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const value = g_aggregator_original(combat, arg2, arg3,
                                            side_index, arg5, arg6);
  auto *const side = g_side_context;
  if (side != nullptr && side->record != nullptr) {
    if (value != nullptr &&
        caller == side->cache->observer->module_base + 0x2307EBA &&
        side->record->side_index == side_index &&
        side->record->helper_calls == 1) {
      side->record->aggregator_raw = *value;
      side->record->helper_calls = 2;
    } else Fail(side->cache->observer, 64);
  }
  return value;
}

void AbsoluteJump(std::uint8_t *dst, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(dst, prefix.data(), prefix.size());
  std::memcpy(dst + 6, &target, 8);
}

bool Matches(std::uintptr_t target, const std::uint8_t *bytes,
             std::size_t size) noexcept {
  if (target == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(target), bytes, size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool WriteSite(std::uintptr_t target, const std::uint8_t *expected,
               const std::uint8_t *desired, std::size_t size,
               bool &possibly_written) noexcept {
  possibly_written = false;
  if (!Matches(target, expected, size)) return false;
  DWORD old = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(target), size,
                      PAGE_EXECUTE_READWRITE, &old)) return false;
  if (!Matches(target, expected, size)) {
    DWORD ignored = 0;
    (void)VirtualProtect(reinterpret_cast<void *>(target), size, old, &ignored);
    return false;
  }
  possibly_written = true;
  std::memcpy(reinterpret_cast<void *>(target), desired, size);
  const bool flushed = FlushInstructionCache(
      GetCurrentProcess(), reinterpret_cast<void *>(target), size) != FALSE;
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(
      reinterpret_cast<void *>(target), size, old, &ignored) != FALSE;
  if (flushed && protected_again && Matches(target, desired, size)) return true;
  // Preserve safety on a post-write failure; caller retains trampoline if
  // restoring bytes or instruction-cache visibility cannot be proven.
  DWORD writable = 0;
  if (VirtualProtect(reinterpret_cast<void *>(target), size,
                     PAGE_EXECUTE_READWRITE, &writable)) {
    std::memcpy(reinterpret_cast<void *>(target), expected, size);
    (void)FlushInstructionCache(
        GetCurrentProcess(), reinterpret_cast<void *>(target), size);
    DWORD restored = 0;
    (void)VirtualProtect(reinterpret_cast<void *>(target), size, old, &restored);
  }
  return false;
}

bool PatchOne(AdvantageComponentDetoursV1::Site &site,
              std::uintptr_t target, const std::uint8_t *expected,
              std::uint8_t size, std::uintptr_t hook) noexcept {
  site.target = target;
  site.size = size;
  std::memcpy(site.original.data(), expected, size);
  if (!Matches(target, expected, size)) return false;
  site.trampoline = VirtualAlloc(nullptr, kTrampolineBytes,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (site.trampoline == nullptr) return false;
  auto *const bytes = static_cast<std::uint8_t *>(site.trampoline);
  std::memcpy(bytes, expected, size);
  AbsoluteJump(bytes + size, target + size);
  DWORD previous = 0;
  if (!VirtualProtect(bytes, kTrampolineBytes, PAGE_EXECUTE_READ, &previous) ||
      previous != PAGE_READWRITE ||
      !FlushInstructionCache(GetCurrentProcess(), bytes, kTrampolineBytes))
    return false;
  std::array<std::uint8_t, 16> patch{};
  patch.fill(0x90);
  AbsoluteJump(patch.data(), hook);
  bool possibly_written = false;
  if (!WriteSite(target, expected, patch.data(), size, possibly_written)) {
    // Even if a best-effort rollback restored bytes, an instruction-cache
    // failure after the write cannot be certified safe for game resumption.
    site.installed = possibly_written;
    return false;
  }
  site.installed = true;
  return true;
}

bool RestoreOne(AdvantageComponentDetoursV1::Site &site,
                std::uintptr_t hook) noexcept {
  if (!site.installed) return true;
  std::array<std::uint8_t, 16> patch{};
  patch.fill(0x90);
  AbsoluteJump(patch.data(), hook);
  bool possibly_written = false;
  if (!WriteSite(site.target, patch.data(), site.original.data(), site.size,
                 possibly_written))
    return false;
  site.installed = false;
  return true;
}

void FreeUnpatched(AdvantageComponentDetoursV1 &detours) noexcept {
  for (auto &site : detours.sites) {
    if (!site.installed && site.trampoline != nullptr) {
      (void)VirtualFree(site.trampoline, 0, MEM_RELEASE);
      site.trampoline = nullptr;
    }
  }
}

const std::array<std::uintptr_t, 4> kHooks{
    reinterpret_cast<std::uintptr_t>(&CacheHook),
    reinterpret_cast<std::uintptr_t>(&SideHook),
    reinterpret_cast<std::uintptr_t>(&CommanderHook),
    reinterpret_cast<std::uintptr_t>(&AggregatorHook)};

} // namespace

bool InstallAdvantageComponentObserverV1(
    AdvantageComponentDetoursV1 &detours, AdvantageComponentObserverV1 &observer,
    std::uintptr_t module_base, bool exact_build_admitted,
    bool paused_quiescence_proven) noexcept {
  if (!exact_build_admitted || !paused_quiescence_proven || module_base == 0 ||
      observer.combat == 0 || observer.combat_id <= 0 ||
      observer.current_date_slot == 0 || observer.current_date_object == 0 ||
      g_observer.load(std::memory_order_acquire) != nullptr) return false;
  for (const auto &site : detours.sites)
    if (site.trampoline != nullptr || site.installed) return false;
  detours = {};
  observer.module_base = module_base;
  const std::array<const std::uint8_t *, 4> expected{
      kCacheBytes.data(), kSideBytes.data(), kCommanderBytes.data(),
      kAggregatorBytes.data()};
  const std::array<std::uint8_t, 4> sizes{15, 16, 15, 15};
  for (std::size_t i = 0; i < 4; ++i) {
    if (!Matches(module_base + kRvas[i], expected[i], sizes[i])) {
      detours.failure_flags |= 1;
      return false;
    }
  }
  for (std::size_t i = 0; i < 4; ++i) {
    if (!PatchOne(detours.sites[i], module_base + kRvas[i], expected[i],
                  sizes[i], kHooks[i])) {
      detours.failure_flags |= 2;
      bool restored = true;
      for (std::size_t j = i + 1; j-- > 0;)
        restored = RestoreOne(detours.sites[j], kHooks[j]) && restored;
      if (!restored) detours.failure_flags |= 4;
      FreeUnpatched(detours);
      return false;
    }
    switch (i) {
      case 0: g_cache_original = reinterpret_cast<CacheFn>(detours.sites[i].trampoline); break;
      case 1: g_side_original = reinterpret_cast<SideFn>(detours.sites[i].trampoline); break;
      case 2: g_commander_original = reinterpret_cast<HelperFn>(detours.sites[i].trampoline); break;
      case 3: g_aggregator_original = reinterpret_cast<HelperFn>(detours.sites[i].trampoline); break;
    }
  }
  g_observer.store(&observer, std::memory_order_release);
  observer.armed.store(true, std::memory_order_release);
  return true;
}

bool UninstallAdvantageComponentObserverV1(
    AdvantageComponentDetoursV1 &detours,
    AdvantageComponentObserverV1 &observer) noexcept {
  observer.armed.store(false, std::memory_order_release);
  bool restored = true;
  for (std::size_t i = 4; i-- > 0;)
    restored = RestoreOne(detours.sites[i], kHooks[i]) && restored;
  if (!restored) { detours.failure_flags |= 4; return false; }
  g_observer.store(nullptr, std::memory_order_release);
  FreeUnpatched(detours);
  g_cache_original = nullptr;
  g_side_original = nullptr;
  g_commander_original = nullptr;
  g_aggregator_original = nullptr;
  return true;
}

bool AdvantageComponentObserverCompleteV1(
    const AdvantageComponentObserverV1 &observer) noexcept {
  const auto count = observer.count.load(std::memory_order_acquire);
  if (count == 0 || count > observer.records.size() ||
      observer.failure_flags.load(std::memory_order_acquire) != 0) return false;
  for (std::uint32_t i = 0; i < count; ++i) {
    const auto &r = observer.records[i];
    if (!r.complete || r.ordinal != i || r.combat_id != observer.combat_id ||
        r.thread_id == 0 || r.caller_rva == 0 ||
        r.sides[1].total_raw == std::numeric_limits<std::int64_t>::min() ||
        !SumExact(r.base_raw, r.sides[0].total_raw,
                  -r.sides[1].total_raw, r.resolved_raw)) return false;
    for (std::size_t side = 0; side < 2; ++side) {
      const auto &s = r.sides[side];
      if (!s.complete || s.side_index != static_cast<std::int32_t>(side) ||
          s.helper_calls != 2 ||
          s.roll_raw != static_cast<std::int64_t>(s.roll) * 100000 ||
          !SumExact(s.roll_raw, s.commander_raw, s.aggregator_raw,
                    s.total_raw)) return false;
    }
  }
  return true;
}

std::string SerializeAdvantageComponentObserverV1(
    const AdvantageComponentObserverV1 &observer) {
  std::string out = "{\"schema_version\":1,"
                    "\"source\":\"native_cache_0x2308d50_original_calls\","
                    "\"requested\":true,\"available\":";
  out += AdvantageComponentObserverCompleteV1(observer) ? "true" : "false";
  out += ",\"failure_flags\":" + std::to_string(
      observer.failure_flags.load(std::memory_order_acquire));
  const auto count = std::min<std::uint32_t>(
      observer.count.load(std::memory_order_acquire),
      static_cast<std::uint32_t>(observer.records.size()));
  out += ",\"materializations\":[";
  for (std::uint32_t i = 0; i < count; ++i) {
    if (i != 0) out += ',';
    const auto &r = observer.records[i];
    out += "{\"ordinal\":" + std::to_string(r.ordinal) +
           ",\"thread_id\":" + std::to_string(r.thread_id) +
           ",\"caller_rva\":" + std::to_string(r.caller_rva) +
           ",\"combat_id\":" + std::to_string(r.combat_id) +
           ",\"date_raw\":" + std::to_string(r.date_raw) +
           ",\"base_raw\":" + std::to_string(r.base_raw) +
           ",\"resolved_raw\":" + std::to_string(r.resolved_raw) +
           ",\"complete\":" + (r.complete ? "true" : "false") +
           ",\"sides\":[";
    for (std::size_t j = 0; j < 2; ++j) {
      if (j != 0) out += ',';
      const auto &s = r.sides[j];
      out += "{\"side_index\":" + std::to_string(s.side_index) +
             ",\"roll\":" + std::to_string(s.roll) +
             ",\"commander_character_id\":" + std::to_string(s.commander_character_id) +
             ",\"roll_raw\":" + std::to_string(s.roll_raw) +
             ",\"commander_raw\":" + std::to_string(s.commander_raw) +
             ",\"aggregator_raw\":" + std::to_string(s.aggregator_raw) +
             ",\"total_raw\":" + std::to_string(s.total_raw) +
             ",\"helper_calls\":" + std::to_string(s.helper_calls) +
             ",\"complete\":" + (s.complete ? "true}" : "false}");
    }
    out += "]}";
  }
  out += "]}";
  return out;
}

} // namespace xar::ck3_11906

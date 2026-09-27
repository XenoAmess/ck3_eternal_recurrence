#include "xar_bridge/combat_advantage_components_observer_v1.hpp"

#include <intrin.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::uintptr_t, 7> kRvas{
    0x2308D50, 0x2307CB0, 0x2307680, 0x2307230,
    0x23CBCE0, 0x251B8F0, 0x251C200};
constexpr std::array<std::uint8_t, 15> kCacheBytes{
    0x48,0x89,0x5C,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57,0x48,0x83,0xEC,0x20};
constexpr std::array<std::uint8_t, 16> kSideBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,0x56,0x57,0x41,0x54,0x41,0x56};
constexpr std::array<std::uint8_t, 15> kCommanderBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7C,0x24,0x20};
constexpr std::array<std::uint8_t, 15> kAggregatorBytes{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,0x48,0x89,0x74,0x24,0x20};
constexpr std::array<std::uint8_t, 15> kRefreshBytes{
    0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xEC,0x20};
constexpr std::array<std::uint8_t, 16> kAppendBytes{
    0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xEC,0x20,
    0x48,0x8B,0xF2,0x48,0x8B,0xF9};
constexpr std::array<std::uint8_t, 15> kGateBytes{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x10,
    0x57,0x48,0x83,0xEC,0x20};
constexpr std::size_t kTrampolineBytes = 64;

using CacheFn = void(__fastcall *)(void *);
using SideFn = std::int64_t *(__fastcall *)(void *, std::int64_t *,
                                             std::int32_t, void *);
using HelperFn = std::int64_t *(__fastcall *)(void *, void *, void *,
                                               std::int32_t, std::int32_t,
                                               void *);
using RefreshFn = void(__fastcall *)(void *);
using AppendFn = void(__fastcall *)(void *, void *);
using GateFn = bool(__fastcall *)(void *);
std::atomic<AdvantageComponentObserverV1 *> g_observer{nullptr};
CacheFn g_cache_original = nullptr;
SideFn g_side_original = nullptr;
HelperFn g_commander_original = nullptr;
HelperFn g_aggregator_original = nullptr;
RefreshFn g_refresh_original = nullptr;
AppendFn g_append_original = nullptr;
GateFn g_gate_original = nullptr;

struct CacheContext {
  AdvantageComponentObserverV1 *observer = nullptr;
  AdvantageMaterializationV1 *record = nullptr;
  std::uint32_t next_side = 0;
  std::uint32_t next_refresh_side = 0;
  CacheContext *prior = nullptr;
};
struct SideContext {
  CacheContext *cache = nullptr;
  AdvantageSideComponentsV1 *record = nullptr;
  SideContext *prior = nullptr;
};
struct RefreshContext {
  CacheContext *cache = nullptr;
  std::uintptr_t side = 0;
  std::int32_t side_index = -1;
  RefreshContext *prior = nullptr;
};
struct AppendContext {
  RefreshContext *refresh = nullptr;
  std::uintptr_t accolade = 0;
  std::uint32_t gate_calls = 0;
  AppendContext *prior = nullptr;
};
thread_local CacheContext *g_cache_context = nullptr;
thread_local SideContext *g_side_context = nullptr;
thread_local RefreshContext *g_refresh_context = nullptr;
thread_local AppendContext *g_append_context = nullptr;

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

void RecordAggregatorFailure(AdvantageComponentObserverV1 *observer,
                             const AdvantageSideComponentsV1 &record,
                             std::uintptr_t caller, std::int32_t side_index,
                             bool value_present,
                             std::uint32_t gate) noexcept {
  std::uint32_t unclaimed = 0;
  if (observer->first_aggregator_failure_gate.compare_exchange_strong(
          unclaimed, std::numeric_limits<std::uint32_t>::max(),
          std::memory_order_acq_rel)) {
    observer->first_aggregator_failure_thread_id = GetCurrentThreadId();
    observer->first_aggregator_failure_caller_address = caller;
    if (caller >= observer->module_base &&
        caller - observer->module_base <=
            std::numeric_limits<std::uint32_t>::max()) {
      observer->first_aggregator_failure_caller_rva =
          static_cast<std::uint32_t>(caller - observer->module_base);
    }
    observer->first_aggregator_failure_side_index = side_index;
    observer->first_aggregator_failure_expected_side_index =
        record.side_index;
    observer->first_aggregator_failure_helper_calls = record.helper_calls;
    observer->first_aggregator_failure_value_present = value_present;
    observer->first_aggregator_failure_gate.store(gate,
                                                   std::memory_order_release);
  }
  Fail(observer, 64);
}

void __fastcall RefreshHook(void *side) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const cache = g_cache_context;
  if (cache == nullptr || cache->observer == nullptr ||
      cache->observer->combat == 0) {
    g_refresh_original(side);
    return;
  }
  auto *const observer = cache->observer;
  const auto index = cache->next_refresh_side;
  if (index > 1 || GetCurrentThreadId() != cache->record->thread_id ||
      caller != observer->module_base +
                    (index == 0 ? 0x2308D6B : 0x2308D77) ||
      reinterpret_cast<std::uintptr_t>(side) !=
          observer->combat + 0x20 + 0x348U * index) {
    Fail(observer, 512);
    g_refresh_original(side);
    return;
  }
  RefreshContext refresh{cache, reinterpret_cast<std::uintptr_t>(side),
                         static_cast<std::int32_t>(index), g_refresh_context};
  g_refresh_context = &refresh;
  g_refresh_original(side);
  g_refresh_context = refresh.prior;
  ++cache->next_refresh_side;
  cache->record->refresh_side_count = cache->next_refresh_side;
}

void __fastcall AppendHook(void *accolade, void *aggregator) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const refresh = g_refresh_context;
  if (refresh == nullptr || refresh->cache == nullptr) {
    g_append_original(accolade, aggregator);
    return;
  }
  auto *const observer = refresh->cache->observer;
  if (accolade == nullptr ||
      caller != observer->module_base + 0x23CBEA8 ||
      reinterpret_cast<std::uintptr_t>(aggregator) !=
          refresh->side + 0x110 ||
      GetCurrentThreadId() != refresh->cache->record->thread_id) {
    Fail(observer, 1024);
    g_append_original(accolade, aggregator);
    return;
  }
  AppendContext append{refresh, reinterpret_cast<std::uintptr_t>(accolade),
                       0, g_append_context};
  g_append_context = &append;
  g_append_original(accolade, aggregator);
  g_append_context = append.prior;
  if (append.gate_calls != 1) Fail(observer, 1024);
}

bool __fastcall GateHook(void *accolade) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  auto *const append = g_append_context;
  if (append == nullptr || append->refresh == nullptr) {
    return g_gate_original(accolade);
  }
  auto *const refresh = append->refresh;
  auto *const observer = refresh->cache->observer;
  if (accolade == nullptr ||
      reinterpret_cast<std::uintptr_t>(accolade) != append->accolade ||
      caller != observer->module_base + 0x251B905 ||
      GetCurrentThreadId() != refresh->cache->record->thread_id ||
      append->gate_calls != 0) {
    Fail(observer, 2048);
    return g_gate_original(accolade);
  }
  ++append->gate_calls;
  auto &materialization = *refresh->cache->record;
  const auto accolade_id = Read<std::int32_t>(accolade, 0x08);
  const auto source_rows = Read<std::uintptr_t>(accolade, 0x58);
  const auto source_row_count = Read<std::int32_t>(accolade, 0x64);
  const bool passed = g_gate_original(accolade);
  const bool stable =
      accolade_id != -1 && source_row_count >= 0 &&
      source_row_count <= 4096 &&
      (source_row_count == 0 || source_rows != 0) &&
      Read<std::int32_t>(accolade, 0x08) == accolade_id &&
      Read<std::uintptr_t>(accolade, 0x58) == source_rows &&
      Read<std::int32_t>(accolade, 0x64) == source_row_count;
  if (!stable) Fail(observer, 2048);
  const auto ordinal = materialization.accolade_gate_count++;
  if (ordinal >= materialization.accolade_gates.size()) {
    Fail(observer, 4096);
  } else {
    materialization.accolade_gates[ordinal] = {
        ordinal, refresh->side_index, accolade_id, source_row_count,
        passed, stable};
  }
  return passed;
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
  CacheContext context{observer, &record, 0, 0, g_cache_context};
  g_cache_context = &context;
  g_cache_original(combat);
  g_cache_context = context.prior;
  record.resolved_raw = Read<std::int64_t>(combat, 0x710);
  const auto &left = record.sides[0];
  const auto &right = record.sides[1];
  record.complete = context.next_refresh_side == 2 &&
      context.next_side == 2 && left.complete && right.complete &&
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
      record.primary_aggregator_calls == 1 &&
      record.nested_aggregator_calls <= 1 &&
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
    auto *const observer = side->cache->observer;
    const auto caller_rva = caller >= observer->module_base &&
        caller - observer->module_base <=
            std::numeric_limits<std::uint32_t>::max()
        ? static_cast<std::uint32_t>(caller - observer->module_base) : 0;
    const auto decision = ClassifyAdvantageAggregatorCallV1(
        value != nullptr,
        combat == reinterpret_cast<void *>(observer->combat), caller_rva,
        side_index, side->record->side_index, side->record->helper_calls,
        side->record->nested_aggregator_calls,
        side->record->primary_aggregator_calls);
    if (decision.failure_gate != 0) {
      RecordAggregatorFailure(observer, *side->record, caller, side_index,
                              value != nullptr, decision.failure_gate);
    } else if (decision.kind ==
               AdvantageAggregatorCallKindV1::nested_commander) {
      // 0x23079FE is the original commander helper's own aggregator call.
      // Its return is already part of commander_raw at 0x2307A06.
      ++side->record->nested_aggregator_calls;
    } else {
      side->record->aggregator_raw = *value;
      side->record->helper_calls = 2;
      ++side->record->primary_aggregator_calls;
    }
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

const std::array<std::uintptr_t, 7> kHooks{
    reinterpret_cast<std::uintptr_t>(&CacheHook),
    reinterpret_cast<std::uintptr_t>(&SideHook),
    reinterpret_cast<std::uintptr_t>(&CommanderHook),
    reinterpret_cast<std::uintptr_t>(&AggregatorHook),
    reinterpret_cast<std::uintptr_t>(&RefreshHook),
    reinterpret_cast<std::uintptr_t>(&AppendHook),
    reinterpret_cast<std::uintptr_t>(&GateHook)};

} // namespace

AdvantageAggregatorCallDecisionV1 ClassifyAdvantageAggregatorCallV1(
    bool value_present, bool combat_matches, std::uint32_t caller_rva,
    std::int32_t side_index, std::int32_t expected_side_index,
    std::uint32_t helper_calls, std::uint32_t nested_calls,
    std::uint32_t primary_calls) noexcept {
  if (!value_present) return {{}, 1};
  if (!combat_matches) return {{}, 3};
  const bool nested = caller_rva == 0x2307A03;
  const bool primary = caller_rva == 0x2307EBA;
  if (!nested && !primary) return {{}, 2};
  if (side_index != expected_side_index) return {{}, 4};
  if (nested) {
    if (helper_calls != 0 || nested_calls != 0) return {{}, 5};
    return {AdvantageAggregatorCallKindV1::nested_commander, 0};
  }
  if (helper_calls != 1 || primary_calls != 0) return {{}, 5};
  return {AdvantageAggregatorCallKindV1::primary_side, 0};
}

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
  const std::array<const std::uint8_t *, 7> expected{
      kCacheBytes.data(), kSideBytes.data(), kCommanderBytes.data(),
      kAggregatorBytes.data(), kRefreshBytes.data(), kAppendBytes.data(),
      kGateBytes.data()};
  const std::array<std::uint8_t, 7> sizes{15, 16, 15, 15, 15, 16, 15};
  for (std::size_t i = 0; i < 7; ++i) {
    if (!Matches(module_base + kRvas[i], expected[i], sizes[i])) {
      detours.failure_flags |= 1;
      return false;
    }
  }
  for (std::size_t i = 0; i < 7; ++i) {
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
      case 4: g_refresh_original = reinterpret_cast<RefreshFn>(detours.sites[i].trampoline); break;
      case 5: g_append_original = reinterpret_cast<AppendFn>(detours.sites[i].trampoline); break;
      case 6: g_gate_original = reinterpret_cast<GateFn>(detours.sites[i].trampoline); break;
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
  for (std::size_t i = 7; i-- > 0;)
    restored = RestoreOne(detours.sites[i], kHooks[i]) && restored;
  if (!restored) { detours.failure_flags |= 4; return false; }
  g_observer.store(nullptr, std::memory_order_release);
  FreeUnpatched(detours);
  g_cache_original = nullptr;
  g_side_original = nullptr;
  g_commander_original = nullptr;
  g_aggregator_original = nullptr;
  g_refresh_original = nullptr;
  g_append_original = nullptr;
  g_gate_original = nullptr;
  return true;
}

bool AdvantageComponentObserverCompleteV1(
    const AdvantageComponentObserverV1 &observer) noexcept {
  const auto count = observer.count.load(std::memory_order_acquire);
  if (count == 0 || count > observer.records.size() ||
      observer.failure_flags.load(std::memory_order_acquire) != 0 ||
      observer.first_aggregator_failure_gate.load(
          std::memory_order_acquire) != 0) return false;
  for (std::uint32_t i = 0; i < count; ++i) {
    const auto &r = observer.records[i];
    if (!r.complete || r.ordinal != i || r.combat_id != observer.combat_id ||
        r.thread_id == 0 || r.caller_rva == 0 ||
        r.refresh_side_count != 2 ||
        r.accolade_gate_count > r.accolade_gates.size() ||
        r.sides[1].total_raw == std::numeric_limits<std::int64_t>::min() ||
        !SumExact(r.base_raw, r.sides[0].total_raw,
                  -r.sides[1].total_raw, r.resolved_raw)) return false;
    for (std::uint32_t gate_index = 0;
         gate_index < r.accolade_gate_count; ++gate_index) {
      const auto &gate = r.accolade_gates[gate_index];
      if (gate.ordinal != gate_index || gate.side_index < 0 ||
          gate.side_index > 1 || gate.accolade_id == -1 ||
          gate.source_row_count < 0 || gate.source_row_count > 4096 ||
          !gate.stable ||
          (gate.source_row_count == 0 && !gate.all_rows_passed)) return false;
    }
    for (std::size_t side = 0; side < 2; ++side) {
      const auto &s = r.sides[side];
      if (!s.complete || s.side_index != static_cast<std::int32_t>(side) ||
          s.helper_calls != 2 || s.primary_aggregator_calls != 1 ||
          s.nested_aggregator_calls > 1 ||
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
  out += ",\"first_aggregator_failure\":{\"gate\":" +
         std::to_string(observer.first_aggregator_failure_gate.load(
             std::memory_order_acquire));
  out += ",\"thread_id\":" +
         std::to_string(observer.first_aggregator_failure_thread_id);
  out += ",\"caller_rva\":" +
         std::to_string(observer.first_aggregator_failure_caller_rva);
  out += ",\"caller_address\":" +
         std::to_string(observer.first_aggregator_failure_caller_address);
  out += ",\"side_index\":" +
         std::to_string(observer.first_aggregator_failure_side_index);
  out += ",\"expected_side_index\":" +
         std::to_string(observer.first_aggregator_failure_expected_side_index);
  out += ",\"helper_calls\":" +
         std::to_string(observer.first_aggregator_failure_helper_calls);
  out += ",\"value_present\":" +
         std::string(observer.first_aggregator_failure_value_present ?
                         "true}" : "false}");
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
           ",\"refresh_side_count\":" +
           std::to_string(r.refresh_side_count) +
           ",\"accolade_gates\":[";
    const auto gate_count = std::min<std::uint32_t>(
        r.accolade_gate_count,
        static_cast<std::uint32_t>(r.accolade_gates.size()));
    for (std::uint32_t gate_index = 0; gate_index < gate_count;
         ++gate_index) {
      if (gate_index != 0) out += ',';
      const auto &gate = r.accolade_gates[gate_index];
      out += "{\"ordinal\":" + std::to_string(gate.ordinal) +
             ",\"side_index\":" + std::to_string(gate.side_index) +
             ",\"accolade_id\":" + std::to_string(gate.accolade_id) +
             ",\"source_row_count\":" +
             std::to_string(gate.source_row_count) +
             ",\"all_rows_passed\":" +
             (gate.all_rows_passed ? "true" : "false") +
             ",\"stable\":" + (gate.stable ? "true" : "false") +
             ",\"failure_kind\":\"" +
             (gate.all_rows_passed ? "none" : "unknown_null_or_virtual") +
             "\",\"slot_binding_status\":"
             "\"unbound_original_entry_pointer\"}";
    }
    out += "],\"sides\":[";
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
             ",\"nested_aggregator_calls\":" + std::to_string(s.nested_aggregator_calls) +
             ",\"primary_aggregator_calls\":" + std::to_string(s.primary_aggregator_calls) +
             ",\"complete\":" + (s.complete ? "true}" : "false}");
    }
    out += "]}";
  }
  out += "]}";
  return out;
}

} // namespace xar::ck3_11906

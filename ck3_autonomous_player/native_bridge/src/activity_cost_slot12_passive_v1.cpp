#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"

#include <windows.h>
#include <intrin.h>

#include <algorithm>
#include <atomic>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::array<std::uint8_t, kActivityCostPatchBytesV1> kRefreshPrologue{
    0x48, 0x89, 0x5C, 0x24, 0x20, 0x55, 0x56, 0x57,
    0x41, 0x54, 0x41, 0x55, 0x41, 0x56};
constexpr std::array<std::uint8_t, 5> kSlot12Call{
    0xE8, 0x81, 0x49, 0x00, 0x00};
constexpr std::size_t kJumpBytes = 14;
constexpr std::size_t kConfigurationCapacity = 0x1B10 - 0x1500;
std::atomic<ActivityCostSlot12ObserverV1 *> g_active_observer{nullptr};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset >
                       (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  output = base + offset;
  return true;
}

bool Read(const ActivityCostSlot12EnvironmentV1 &environment,
          std::uintptr_t base, std::size_t offset, void *output,
          std::size_t bytes) noexcept {
  std::uintptr_t address = 0;
  return environment.read_memory != nullptr &&
         Add(base, offset, address) &&
         environment.read_memory(environment.context, address, output, bytes);
}

template <typename T>
bool ReadAt(const ActivityCostSlot12EnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &output) noexcept {
  return Read(environment, base, offset, &output, sizeof(output));
}

bool IsFeastType(const ActivityCostSlot12EnvironmentV1 &environment,
                 std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      environment.executable_sha256);
  if (layout == nullptr) return false;
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t length = 0, capacity = 0;
  if (!ReadAt(environment, type, 0, vtable) ||
      vtable != environment.module_base + layout->type_vtable_rva ||
      !ReadAt(environment, type, 0x28, length) ||
      !ReadAt(environment, type, 0x30, capacity) ||
      length != key.size() || length > capacity)
    return false;
  if (capacity > 15 && !ReadAt(environment, type, 0x18, data)) return false;
  std::array<char, 16> copied{};
  return Read(environment, data, 0, copied.data(), key.size()) &&
         std::memcmp(copied.data(), key.data(), key.size()) == 0;
}

bool FingerprintConfiguration(
    const ActivityCostSlot12EnvironmentV1 &environment,
    std::uintptr_t planner, std::uint64_t &output) noexcept {
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      environment.executable_sha256);
  if (layout == nullptr) return false;
  std::array<std::uint8_t, kConfigurationCapacity> bytes{};
  const auto configuration_size = layout->breakdown_offset - layout->type_offset;
  if (!Read(environment, planner, layout->type_offset, bytes.data(),
            configuration_size))
    return false;
  std::uint64_t hash = 14695981039346656037ULL;
  for (std::size_t i = 0; i < configuration_size; ++i) {
    const auto byte = bytes[i];
    hash ^= byte;
    hash *= 1099511628211ULL;
  }
  // The selected category and cost-driving option vectors are outside the
  // planner object. Their pointer/count fields above alone would miss an
  // in-place selection change in an existing row.
  struct Rows {
    std::size_t pointer_offset;
    std::size_t count_offset;
    std::size_t stride;
  };
  const std::array<Rows, 2> row_sets{{
      {layout->category_rows_offset, layout->category_count_offset, 0x10},
      {layout->option_rows_offset, layout->option_count_offset, 0x38},
  }};
  std::array<std::uint8_t, 128 * 0x38> rows{};
  for (const auto &set : row_sets) {
    std::uintptr_t pointer = 0;
    std::int32_t count = -1;
    if (!ReadAt(environment, planner, set.pointer_offset, pointer) ||
        !ReadAt(environment, planner, set.count_offset, count) ||
        count < 0 || count > 128 || (count != 0 && pointer == 0))
      return false;
    const auto size = static_cast<std::size_t>(count) * set.stride;
    if (size != 0 &&
        !Read(environment, pointer, 0, rows.data(), size))
      return false;
    for (std::size_t i = 0; i < size; ++i) {
      hash ^= rows[i];
      hash *= 1099511628211ULL;
    }
  }
  output = hash;
  return true;
}

void WriteAbsoluteJump(std::uint8_t *target, const void *destination) noexcept {
  target[0] = 0xFF;
  target[1] = 0x25;
  std::memset(target + 2, 0, 4);
  const auto address = reinterpret_cast<std::uintptr_t>(destination);
  std::memcpy(target + 6, &address, sizeof(address));
}

void __fastcall RefreshHook(void *planner) noexcept {
  auto *observer = g_active_observer.load(std::memory_order_acquire);
  if (observer == nullptr || observer->trampoline == nullptr) return;
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto original =
      reinterpret_cast<void(__fastcall *)(void *)>(observer->trampoline);
  original(planner);
  (void)RecordActivityCostSlot12NormalReturnV1(
      *observer, caller, reinterpret_cast<std::uintptr_t>(planner));
}

} // namespace

bool VerifyActivityCostSlot12ExactAbiV1(
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept {
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      environment.executable_sha256);
  if (!environment.enabled || !environment.primary_thread_suspended ||
      layout == nullptr ||
      environment.module_base == 0 || environment.read_memory == nullptr ||
      environment.read_frame == nullptr)
    return false;
  std::array<std::uint8_t, kActivityCostPatchBytesV1> prologue{};
  std::array<std::uint8_t, 5> call{};
  const std::array<std::uint8_t, 5> expected_call =
      IsActivityFeastCostsModernBuildV1(environment.executable_sha256)
          ? std::array<std::uint8_t, 5>{0xE8, 0x71, 0x4B, 0x00, 0x00}
          : kSlot12Call;
  return ReadAt(environment, environment.module_base,
                layout->refresh_rva, prologue) &&
         prologue == kRefreshPrologue &&
         ReadAt(environment, environment.module_base,
                layout->slot12_return_rva - 5, call) &&
         call == expected_call;
}

bool RecordActivityCostSlot12NormalReturnV1(
    ActivityCostSlot12ObserverV1 &observer, std::uintptr_t caller_return,
    std::uintptr_t planner) noexcept {
  const auto &environment = observer.environment;
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      environment.executable_sha256);
  if (layout == nullptr) return false;
  if (caller_return !=
          environment.module_base + layout->slot12_return_rva ||
      planner == 0 || environment.read_memory == nullptr ||
      environment.read_frame == nullptr)
    return false;
  ActivityCostSlot12CaptureV1 candidate{};
  if (!environment.read_frame(environment.context, candidate.frame) ||
      !candidate.frame.paused || candidate.frame.actor_character_id <= 0 ||
      candidate.frame.thread_id == 0 ||
      candidate.frame.thread_id != GetCurrentThreadId())
    return false;
  candidate.planner = planner;
  std::uintptr_t vtable = 0;
  if (!ReadAt(environment, planner, 0, vtable) ||
      vtable != environment.module_base + layout->planner_vtable_rva ||
      !ReadAt(environment, planner, layout->owner_offset, candidate.owner) ||
      candidate.owner == 0 ||
      !ReadAt(environment, planner, layout->type_offset, candidate.activity_type) ||
      candidate.activity_type == 0 ||
      !IsFeastType(environment, candidate.activity_type) ||
      !ReadAt(environment, planner, layout->stage_offset, candidate.planning_stage) ||
      candidate.planning_stage < 0 || candidate.planning_stage > 5 ||
      !FingerprintConfiguration(environment, planner,
                                candidate.configuration_fingerprint))
    return false;
  for (std::size_t index = 0; index < candidate.raw_aggregate.size(); ++index) {
    const std::size_t offset = layout->breakdown_offset + 0x50 + index * 0x90 + 0x78;
    if (!ReadAt(environment, planner, offset,
                candidate.raw_aggregate[index]))
      return false;
  }
  ActivityCostSlot12FrameV1 after{};
  std::uint64_t fingerprint_after = 0;
  if (!environment.read_frame(environment.context, after) ||
      after.date_raw != candidate.frame.date_raw ||
      after.actor_character_id != candidate.frame.actor_character_id ||
      after.thread_id != candidate.frame.thread_id || !after.paused ||
      !FingerprintConfiguration(environment, planner, fingerprint_after) ||
      fingerprint_after != candidate.configuration_fingerprint)
    return false;
  std::lock_guard lock(observer.capture_mutex);
  candidate.sequence = observer.latest.sequence + 1;
  observer.latest = candidate;
  return true;
}

ActivityCostSlot12ReadStatusV1 ReadActivityCostSlot12PassiveV1(
    ActivityCostSlot12ObserverV1 &observer,
    const ActivityCostSlot12FrameV1 &expected,
    ActivityCostSlot12CaptureV1 &output) noexcept {
  const auto *layout = ActivityFeastCostLayoutForBuildV1(
      observer.environment.executable_sha256);
  if (!observer.environment.enabled || layout == nullptr)
    return ActivityCostSlot12ReadStatusV1::exact_build_rejected;
  {
    std::lock_guard lock(observer.capture_mutex);
    output = observer.latest;
  }
  if (output.sequence == 0)
    return ActivityCostSlot12ReadStatusV1::no_normal_refresh;
  if (output.frame.date_raw != expected.date_raw ||
      output.frame.actor_character_id != expected.actor_character_id ||
      output.frame.thread_id != expected.thread_id || !output.frame.paused ||
      !expected.paused)
    return ActivityCostSlot12ReadStatusV1::frame_changed;
  std::uintptr_t owner = 0, type = 0, vtable = 0;
  std::int32_t stage = -1;
  std::uint64_t fingerprint = 0;
  const auto &environment = observer.environment;
  if (!ReadAt(environment, output.planner, 0, vtable) ||
      vtable != environment.module_base + layout->planner_vtable_rva ||
      !ReadAt(environment, output.planner, layout->owner_offset, owner) ||
      owner != output.owner ||
      !ReadAt(environment, output.planner, layout->type_offset, type) ||
      type != output.activity_type || !IsFeastType(environment, type) ||
      !ReadAt(environment, output.planner, layout->stage_offset, stage) ||
      stage != output.planning_stage ||
      !FingerprintConfiguration(environment, output.planner, fingerprint) ||
      fingerprint != output.configuration_fingerprint)
    return ActivityCostSlot12ReadStatusV1::configuration_changed;
  ActivityCostSlot12FrameV1 after{};
  if (!environment.read_frame(environment.context, after) ||
      after.date_raw != expected.date_raw ||
      after.actor_character_id != expected.actor_character_id ||
      after.thread_id != expected.thread_id || !after.paused)
    return ActivityCostSlot12ReadStatusV1::frame_changed;
  return ActivityCostSlot12ReadStatusV1::observed;
}

bool InstallActivityCostSlot12PassiveV1(
    ActivityCostSlot12ObserverV1 &observer,
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept {
  if (observer.installed || !VerifyActivityCostSlot12ExactAbiV1(environment))
    return false;
  auto *target = reinterpret_cast<std::uint8_t *>(
      environment.module_base + ActivityFeastCostLayoutForBuildV1(
          environment.executable_sha256)->refresh_rva);
  auto *trampoline = static_cast<std::uint8_t *>(VirtualAlloc(
      nullptr, kActivityCostPatchBytesV1 + kJumpBytes,
      MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
  if (trampoline == nullptr) return false;
  std::memcpy(observer.original_bytes.data(), target,
              observer.original_bytes.size());
  std::memcpy(trampoline, observer.original_bytes.data(),
              observer.original_bytes.size());
  WriteAbsoluteJump(trampoline + kActivityCostPatchBytesV1,
                    target + kActivityCostPatchBytesV1);
  if (!FlushInstructionCache(GetCurrentProcess(), trampoline,
                             kActivityCostPatchBytesV1 + kJumpBytes)) {
    VirtualFree(trampoline, 0, MEM_RELEASE);
    return false;
  }
  observer.environment = environment;
  observer.trampoline = trampoline;
  ActivityCostSlot12ObserverV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(expected, &observer)) {
    observer.trampoline = nullptr;
    VirtualFree(trampoline, 0, MEM_RELEASE);
    return false;
  }
  std::array<std::uint8_t, kActivityCostPatchBytesV1> patch{};
  WriteAbsoluteJump(patch.data(), reinterpret_cast<const void *>(&RefreshHook));
  DWORD previous = 0;
  if (!VirtualProtect(target, patch.size(), PAGE_EXECUTE_READWRITE, &previous)) {
    g_active_observer.store(nullptr);
    observer.trampoline = nullptr;
    VirtualFree(trampoline, 0, MEM_RELEASE);
    return false;
  }
  std::memcpy(target, patch.data(), patch.size());
  const bool flushed = FlushInstructionCache(GetCurrentProcess(), target,
                                              patch.size()) != FALSE;
  DWORD ignored = 0;
  const bool restored =
      VirtualProtect(target, patch.size(), previous, &ignored) != FALSE;
  if (!flushed || !restored) {
    DWORD writable = 0;
    if (VirtualProtect(target, patch.size(), PAGE_EXECUTE_READWRITE,
                       &writable)) {
      std::memcpy(target, observer.original_bytes.data(), patch.size());
      FlushInstructionCache(GetCurrentProcess(), target, patch.size());
      VirtualProtect(target, patch.size(), previous, &ignored);
    }
    g_active_observer.store(nullptr);
    observer.trampoline = nullptr;
    VirtualFree(trampoline, 0, MEM_RELEASE);
    return false;
  }
  observer.installed = true;
  return true;
}

} // namespace xar::bridge

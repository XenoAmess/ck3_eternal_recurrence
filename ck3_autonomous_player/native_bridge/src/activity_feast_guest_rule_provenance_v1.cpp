#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"

#include <windows.h>
#include <intrin.h>

#include <algorithm>
#include <atomic>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::array<std::uint8_t, kActivityGuestRuleRefreshPatchBytesV1>
    kRefreshPrologue{0x4C, 0x89, 0x44, 0x24, 0x18,
                     0x48, 0x89, 0x54, 0x24, 0x10,
                     0x48, 0x89, 0x4C, 0x24, 0x08};
constexpr std::array<std::uint8_t, kActivityGuestRuleEffectPatchBytesV1>
    kEffectPrologue{0x48, 0x89, 0x5C, 0x24, 0x10,
                    0x48, 0x89, 0x74, 0x24, 0x18,
                    0x57, 0x48, 0x81, 0xEC, 0x30, 0x04, 0x00, 0x00};
constexpr std::array<std::uint8_t, 5> kRefreshCall{
    0xE8, 0x3F, 0xE9, 0x81, 0x01};
constexpr std::array<std::uint8_t, 5> kEffectCall{
    0xE8, 0xF6, 0x0E, 0xAB, 0x00};
constexpr std::size_t kAbsoluteJumpBytes = 14;
constexpr std::uintptr_t kFeastTypeVtableRva = 0x440E308;
std::atomic<ActivityGuestRuleProvenanceObserverV1 *> g_observer{nullptr};
thread_local ActivityGuestRuleProvenanceObserverV1 *g_current_refresh = nullptr;

void CountRefresh(ActivityGuestRuleProvenanceObserverV1 &observer,
                  ActivityGuestRuleRefreshDiagnosticV1 reason) noexcept {
  observer.refresh_diagnostics[static_cast<std::size_t>(reason)].fetch_add(
      1, std::memory_order_relaxed);
}

bool Address(std::uintptr_t base, std::size_t offset,
             std::uintptr_t &address) noexcept {
  if (base == 0 || offset >
                       (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

bool ReadBytes(const ActivityCostSlot12EnvironmentV1 &env,
               std::uintptr_t base, std::size_t offset, void *output,
               std::size_t bytes) noexcept {
  std::uintptr_t address = 0;
  return env.read_memory != nullptr && Address(base, offset, address) &&
         env.read_memory(env.context, address, output, bytes);
}

template <typename T>
bool Read(const ActivityCostSlot12EnvironmentV1 &env,
          std::uintptr_t base, std::size_t offset, T &output) noexcept {
  return ReadBytes(env, base, offset, &output, sizeof(output));
}

bool FeastType(const ActivityCostSlot12EnvironmentV1 &env,
               std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t length = 0, capacity = 0;
  if (!Read(env, type, 0, vtable) ||
      vtable != env.module_base + kFeastTypeVtableRva ||
      !Read(env, type, 0x28, length) ||
      !Read(env, type, 0x30, capacity) ||
      length != key.size() || length > capacity ||
      (capacity > 15 && !Read(env, type, 0x18, data)))
    return false;
  std::array<char, 16> copied{};
  return ReadBytes(env, data, 0, copied.data(), key.size()) &&
         std::memcmp(copied.data(), key.data(), key.size()) == 0;
}

void HashBytes(std::uint64_t &hash, const void *data,
               std::size_t size) noexcept {
  const auto *bytes = static_cast<const std::uint8_t *>(data);
  for (std::size_t i = 0; i < size; ++i) {
    hash ^= bytes[i];
    hash *= 1099511628211ULL;
  }
}

bool GroupFingerprint(const ActivityCostSlot12EnvironmentV1 &env,
                      std::uintptr_t filtered_groups,
                      std::uint64_t &fingerprint) noexcept {
  std::uintptr_t groups = 0;
  std::int32_t count = -1;
  if (!Read(env, filtered_groups, 0, groups) ||
      !Read(env, filtered_groups, 0xC, count) || count < 0 || count > 64 ||
      (count != 0 && groups == 0))
    return false;
  std::uint64_t hash = 14695981039346656037ULL;
  HashBytes(hash, &count, sizeof(count));
  for (std::int32_t i = 0; i < count; ++i) {
    const auto row = groups + static_cast<std::size_t>(i) * 0x18;
    std::uintptr_t ids = 0;
    std::int32_t length = -1;
    if (!Read(env, row, 0, ids) || !Read(env, row, 0xC, length) ||
        length < 0 || length > static_cast<std::int32_t>(kActivityGuestRuleMaxIdsV1) ||
        (length != 0 && ids == 0))
      return false;
    HashBytes(hash, &length, sizeof(length));
    std::array<std::uint32_t, kActivityGuestRuleMaxIdsV1> values{};
    if (length != 0 &&
        !ReadBytes(env, ids, 0, values.data(),
                   static_cast<std::size_t>(length) * sizeof(values[0])))
      return false;
    HashBytes(hash, values.data(),
              static_cast<std::size_t>(length) * sizeof(values[0]));
  }
  fingerprint = hash;
  return true;
}

bool ActiveRuleFingerprint(const ActivityCostSlot12EnvironmentV1 &env,
                           std::uintptr_t active_rules,
                           std::uint64_t &fingerprint) noexcept {
  std::uintptr_t rows = 0;
  std::int32_t count = -1;
  if (!Read(env, active_rules, 0, rows) ||
      !Read(env, active_rules, 0xC, count) || count < 0 ||
      count > static_cast<std::int32_t>(kActivityGuestRuleMaxRulesV1) ||
      (count != 0 && rows == 0))
    return false;
  std::array<std::uint8_t, kActivityGuestRuleMaxRulesV1 * 16> bytes{};
  if (count != 0 &&
      !ReadBytes(env, rows, 0, bytes.data(),
                 static_cast<std::size_t>(count) * 16))
    return false;
  std::uint64_t hash = 14695981039346656037ULL;
  HashBytes(hash, &count, sizeof(count));
  HashBytes(hash, bytes.data(), static_cast<std::size_t>(count) * 16);
  fingerprint = hash;
  return true;
}

void MarkReadFailed(ActivityGuestRuleProvenanceCaptureV1 &capture) noexcept {
  capture.native_read_failed = true;
}

void WriteAbsoluteJump(std::uint8_t *target,
                       const void *destination) noexcept {
  target[0] = 0xFF;
  target[1] = 0x25;
  std::memset(target + 2, 0, 4);
  const auto address = reinterpret_cast<std::uintptr_t>(destination);
  std::memcpy(target + 6, &address, sizeof(address));
}

bool Restore(std::uint8_t *target, const std::uint8_t *original,
             std::size_t count) noexcept {
  DWORD previous = 0;
  if (!VirtualProtect(target, count, PAGE_EXECUTE_READWRITE, &previous))
    return false;
  std::memcpy(target, original, count);
  const bool flushed =
      FlushInstructionCache(GetCurrentProcess(), target, count) != FALSE;
  DWORD ignored = 0;
  return VirtualProtect(target, count, previous, &ignored) != FALSE && flushed;
}

bool Patch(std::uint8_t *target, const void *hook,
           const std::uint8_t *original, std::size_t count,
           void *&trampoline) noexcept {
  auto *allocated = static_cast<std::uint8_t *>(VirtualAlloc(
      nullptr, count + kAbsoluteJumpBytes, MEM_COMMIT | MEM_RESERVE,
      PAGE_EXECUTE_READWRITE));
  if (allocated == nullptr) return false;
  std::memcpy(allocated, original, count);
  WriteAbsoluteJump(allocated + count, target + count);
  if (!FlushInstructionCache(GetCurrentProcess(), allocated,
                             count + kAbsoluteJumpBytes)) {
    VirtualFree(allocated, 0, MEM_RELEASE);
    return false;
  }
  std::array<std::uint8_t, kActivityGuestRuleEffectPatchBytesV1> bytes{};
  WriteAbsoluteJump(bytes.data(), hook);
  // The remaining complete prologue bytes are unreachable after the jump.
  std::fill(bytes.begin() + kAbsoluteJumpBytes, bytes.begin() + count,
            std::uint8_t{0x90});
  DWORD previous = 0;
  if (!VirtualProtect(target, count, PAGE_EXECUTE_READWRITE, &previous)) {
    VirtualFree(allocated, 0, MEM_RELEASE);
    return false;
  }
  std::memcpy(target, bytes.data(), count);
  const bool flushed =
      FlushInstructionCache(GetCurrentProcess(), target, count) != FALSE;
  DWORD ignored = 0;
  const bool restored =
      VirtualProtect(target, count, previous, &ignored) != FALSE;
  if (!flushed || !restored) {
    (void)Restore(target, original, count);
    VirtualFree(allocated, 0, MEM_RELEASE);
    return false;
  }
  trampoline = allocated;
  return true;
}

std::uintptr_t __fastcall EffectHook(void *effect,
                                     void *temporary_output) noexcept {
  auto *observer = g_observer.load(std::memory_order_acquire);
  if (observer == nullptr || observer->effect_trampoline == nullptr) return 0;
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  using Native = std::uintptr_t(__fastcall *)(void *, void *);
  const auto value = reinterpret_cast<Native>(observer->effect_trampoline)(
      effect, temporary_output);
  if (g_current_refresh == observer)
    RecordActivityGuestRuleEffectReturnV1(
        *observer, return_address,
        reinterpret_cast<std::uintptr_t>(effect),
        reinterpret_cast<std::uintptr_t>(temporary_output));
  return value;
}

std::uintptr_t __fastcall RefreshHook(void *activity_type, void *context,
                                      void *selected, void *active_rules,
                                      void *configuration,
                                      void *filtered_groups) noexcept {
  auto *observer = g_observer.load(std::memory_order_acquire);
  if (observer == nullptr || observer->refresh_trampoline == nullptr) return 0;
  CountRefresh(*observer, ActivityGuestRuleRefreshDiagnosticV1::hook_entered);
  const auto return_address =
      reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto groups = reinterpret_cast<std::uintptr_t>(filtered_groups);
  auto *previous = g_current_refresh;
  bool capture = false;
  if (previous != nullptr)
    CountRefresh(*observer, ActivityGuestRuleRefreshDiagnosticV1::nested_refresh);
  else if (groups < 0x1590)
    CountRefresh(*observer,
                 ActivityGuestRuleRefreshDiagnosticV1::invalid_group_argument);
  else {
    capture = BeginActivityGuestRuleRefreshV1(
        *observer, return_address, groups - 0x1590,
        reinterpret_cast<std::uintptr_t>(active_rules), groups);
  }
  g_current_refresh = capture ? observer : nullptr;
  using Native = std::uintptr_t(__fastcall *)(void *, void *, void *, void *,
                                               void *, void *);
  const auto value = reinterpret_cast<Native>(observer->refresh_trampoline)(
      activity_type, context, selected, active_rules, configuration,
      filtered_groups);
  g_current_refresh = previous;
  if (capture) {
    FinishActivityGuestRuleRefreshV1(*observer);
  }
  return value;
}

} // namespace

bool BeginActivityGuestRuleRefreshV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    std::uintptr_t caller_return, std::uintptr_t planner,
    std::uintptr_t active_rules, std::uintptr_t filtered_groups) noexcept {
  const auto &env = observer.environment;
  if (caller_return !=
      env.module_base + kActivityGuestRuleRefreshReturnRvaV1) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::wrong_caller);
    return false;
  }
  if (planner == 0 || active_rules != planner + 0x1A18 ||
      filtered_groups != planner + 0x1590 || env.read_frame == nullptr) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::invalid_arguments);
    return false;
  }
  ActivityCostSlot12FrameV1 frame{};
  std::uintptr_t vtable = 0, type = 0;
  std::int32_t stage = -1;
  if (!env.read_frame(env.context, frame)) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::frame_unavailable);
    return false;
  }
  if (!frame.paused) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::frame_unpaused);
    return false;
  }
  if (frame.actor_character_id <= 0 ||
      frame.thread_id != GetCurrentThreadId()) {
    CountRefresh(observer,
                 ActivityGuestRuleRefreshDiagnosticV1::actor_or_thread_unavailable);
    return false;
  }
  if (!Read(env, planner, 0, vtable) ||
      vtable != env.module_base + 0x41205F0) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::planner_unavailable);
    return false;
  }
  if (!Read(env, planner, 0x1530, type) || !FeastType(env, type)) {
    CountRefresh(observer,
                 ActivityGuestRuleRefreshDiagnosticV1::feast_type_unavailable);
    return false;
  }
  if (!Read(env, planner, 0x1AB0, stage)) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::stage_unavailable);
    return false;
  }
  observer.last_seen_stage.store(stage, std::memory_order_relaxed);
  if (stage != 5) {
    CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::stage_not_five);
    return false;
  }
  CountRefresh(observer, ActivityGuestRuleRefreshDiagnosticV1::accepted);
  auto &capture = observer.working;
  capture = {};
  capture.frame = frame;
  capture.planner = planner;
  capture.activity_type = type;
  capture.active_rules = active_rules;
  capture.filtered_groups = filtered_groups;
  capture.planning_stage = stage;
  return true;
}

void RecordActivityGuestRuleEffectReturnV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    std::uintptr_t caller_return, std::uintptr_t effect,
    std::uintptr_t temporary_output) noexcept {
  auto &capture = observer.working;
  const auto &env = observer.environment;
  if (caller_return != env.module_base + kActivityGuestRuleEffectReturnRvaV1 ||
      capture.planner == 0 || capture.native_read_failed || capture.overflow ||
      effect < 0x38 || temporary_output == 0)
    return;
  if (capture.rule_count == kActivityGuestRuleMaxRulesV1) {
    capture.overflow = true;
    return;
  }
  const auto definition = effect - 0x38;
  std::uintptr_t active_rows = 0;
  std::int32_t active_count = -1;
  std::uint32_t hash = 0, list_key = 0;
  if (!Read(env, capture.active_rules, 0, active_rows) ||
      !Read(env, capture.active_rules, 0xC, active_count) ||
      active_count < 0 || active_count >
          static_cast<std::int32_t>(kActivityGuestRuleMaxRulesV1) ||
      (active_count != 0 && active_rows == 0) ||
      !Read(env, definition, 0x14, hash) ||
      !Read(env, definition, 0x9C, list_key)) {
    MarkReadFailed(capture);
    return;
  }
  std::int32_t priority = -1;
  for (std::int32_t i = 0; i < active_count; ++i) {
    const auto row = active_rows + static_cast<std::size_t>(i) * 16;
    std::uintptr_t pointer = 0;
    if (!Read(env, row, 0, pointer)) {
      MarkReadFailed(capture);
      return;
    }
    if (pointer != definition) continue;
    if (priority != -1 || !Read(env, row, 8, priority)) {
      MarkReadFailed(capture);
      return;
    }
  }
  if (priority < 0 || priority > 63) {
    MarkReadFailed(capture);
    return;
  }
  auto &rule = capture.rules[capture.rule_count];
  rule.definition = definition;
  rule.native_key_hash = hash;
  rule.priority = priority;
  rule.raw_begin = capture.raw_id_count;
  std::uintptr_t output_rows = 0;
  std::int32_t output_count = -1;
  if (!Read(env, temporary_output, 0x100, output_rows) ||
      !Read(env, temporary_output, 0x10C, output_count) ||
      output_count < 0 || output_count > 256 ||
      (output_count != 0 && output_rows == 0)) {
    MarkReadFailed(capture);
    return;
  }
  for (std::int32_t i = 0; i < output_count; ++i) {
    const auto row = output_rows + static_cast<std::size_t>(i) * 0x48;
    std::uint32_t key = 0;
    if (!Read(env, row, 8, key)) {
      MarkReadFailed(capture);
      return;
    }
    if (key != list_key) continue;
    std::uintptr_t values = 0;
    std::int32_t length = -1;
    if (!Read(env, row, 0x10, values) ||
        !Read(env, row, 0x1C, length) || length < 0 ||
        length > static_cast<std::int32_t>(kActivityGuestRuleMaxIdsV1) ||
        (length != 0 && values == 0)) {
      MarkReadFailed(capture);
      return;
    }
    for (std::int32_t j = 0; j < length; ++j) {
      const auto item = values + static_cast<std::size_t>(j) * 16;
      std::uint16_t type = 0;
      std::uint32_t id = 0;
      if (!Read(env, item, 0, type) || !Read(env, item, 8, id)) {
        MarkReadFailed(capture);
        return;
      }
      if (type != 4 || id == 0xFFFFFFFFU) continue;
      if (capture.raw_id_count == kActivityGuestRuleMaxIdsV1) {
        capture.overflow = true;
        return;
      }
      capture.raw_ids[capture.raw_id_count++] = id;
      ++rule.raw_count;
    }
  }
  ++capture.rule_count;
}

void FinishActivityGuestRuleRefreshV1(
    ActivityGuestRuleProvenanceObserverV1 &observer) noexcept {
  auto &capture = observer.working;
  const auto &env = observer.environment;
  if (capture.planner == 0) return;
  ActivityCostSlot12FrameV1 after{};
  std::uintptr_t type = 0;
  std::int32_t stage = -1;
  if (env.read_frame == nullptr ||
      !env.read_frame(env.context, after) || !after.paused ||
      after.date_raw != capture.frame.date_raw ||
      after.actor_character_id != capture.frame.actor_character_id ||
      after.thread_id != capture.frame.thread_id ||
      !Read(env, capture.planner, 0x1530, type) ||
      type != capture.activity_type ||
      !Read(env, capture.planner, 0x1AB0, stage) || stage != 5) {
    capture.native_read_failed = true;
  }
  std::uintptr_t group_rows = 0;
  std::int32_t group_count = -1;
  if (!Read(env, capture.filtered_groups, 0, group_rows) ||
      !Read(env, capture.filtered_groups, 0xC, group_count) ||
      group_count < 0 || group_count > 64 ||
      (group_count != 0 && group_rows == 0)) {
    capture.native_read_failed = true;
  }
  if (!capture.native_read_failed && !capture.overflow) {
    std::array<std::uint32_t, kActivityGuestRuleMaxIdsV1> grouped_ids{};
    std::array<std::uint32_t, 64> begins{};
    std::array<std::uint32_t, 64> lengths{};
    std::uint32_t used = 0;
    for (std::int32_t i = 0; i < group_count; ++i) {
      const auto row = group_rows + static_cast<std::size_t>(i) * 0x18;
      std::uintptr_t ids = 0;
      std::int32_t length = -1;
      if (!Read(env, row, 0, ids) || !Read(env, row, 0xC, length) ||
          length < 0 ||
          static_cast<std::size_t>(length) > kActivityGuestRuleMaxIdsV1 - used ||
          (length != 0 && ids == 0) ||
          (length != 0 &&
           !ReadBytes(env, ids, 0, grouped_ids.data() + used,
                      static_cast<std::size_t>(length) * sizeof(std::uint32_t)))) {
        capture.native_read_failed = true;
        break;
      }
      begins[i] = used;
      lengths[i] = static_cast<std::uint32_t>(length);
      std::sort(grouped_ids.begin() + used,
                grouped_ids.begin() + used + length);
      used += static_cast<std::uint32_t>(length);
    }
    if (!capture.native_read_failed) {
      for (std::uint32_t i = 0; i < capture.rule_count; ++i) {
        auto &rule = capture.rules[i];
        if (rule.priority < 0 || rule.priority >= group_count) {
          capture.native_read_failed = true;
          break;
        }
        rule.filtered_begin = capture.filtered_id_count;
        const auto group_begin = begins[rule.priority];
        const auto group_end = group_begin + lengths[rule.priority];
        for (std::uint32_t j = 0; j < rule.raw_count; ++j) {
          const auto id = capture.raw_ids[rule.raw_begin + j];
          if (!std::binary_search(grouped_ids.begin() + group_begin,
                                  grouped_ids.begin() + group_end, id))
            continue;
          if (capture.filtered_id_count == kActivityGuestRuleMaxIdsV1) {
            capture.overflow = true;
            break;
          }
          capture.filtered_ids[capture.filtered_id_count++] = id;
          ++rule.filtered_count;
        }
        if (capture.overflow) break;
      }
    }
  }
  if (!capture.native_read_failed &&
      !GroupFingerprint(env, capture.filtered_groups,
                        capture.group_fingerprint))
    capture.native_read_failed = true;
  if (!capture.native_read_failed &&
      !ActiveRuleFingerprint(env, capture.active_rules,
                             capture.active_rule_fingerprint))
    capture.native_read_failed = true;
  {
    std::lock_guard lock(observer.capture_mutex);
    capture.sequence = observer.latest.sequence + 1;
    observer.latest = capture;
  }
}

ActivityGuestRuleProvenanceResultV1 ReadActivityGuestRuleProvenanceV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    const ActivityCostSlot12FrameV1 &expected, std::uintptr_t planner,
    std::uint32_t native_key_hash,
    std::uint32_t candidate_character_id) noexcept {
  ActivityGuestRuleProvenanceResultV1 result{};
  const auto &env = observer.environment;
  if (!env.enabled ||
      env.executable_sha256 != kActivityGuestRuleProvenanceExeSha256V1)
    return result;
  ActivityGuestRuleProvenanceCaptureV1 capture{};
  {
    std::lock_guard lock(observer.capture_mutex);
    capture = observer.latest;
  }
  if (capture.sequence == 0) {
    result.status = ActivityGuestRuleProvenanceStatusV1::no_normal_refresh;
    return result;
  }
  if (capture.frame.date_raw != expected.date_raw ||
      capture.frame.actor_character_id != expected.actor_character_id ||
      capture.frame.thread_id != expected.thread_id ||
      !capture.frame.paused || !expected.paused) {
    result.status = ActivityGuestRuleProvenanceStatusV1::frame_changed;
    return result;
  }
  if (capture.planner != planner || capture.planning_stage != 5 ||
      capture.filtered_groups != planner + 0x1590 ||
      capture.active_rules != planner + 0x1A18) {
    result.status = ActivityGuestRuleProvenanceStatusV1::planner_unavailable;
    return result;
  }
  if (capture.native_read_failed) {
    result.status = ActivityGuestRuleProvenanceStatusV1::native_read_failed;
    return result;
  }
  if (capture.overflow) {
    result.status = ActivityGuestRuleProvenanceStatusV1::capture_overflow;
    return result;
  }
  std::uint64_t current_fingerprint = 0;
  std::uint64_t current_rules = 0;
  ActivityCostSlot12FrameV1 after{};
  if (!GroupFingerprint(env, capture.filtered_groups,
                        current_fingerprint) ||
      current_fingerprint != capture.group_fingerprint ||
      !ActiveRuleFingerprint(env, capture.active_rules, current_rules) ||
      current_rules != capture.active_rule_fingerprint ||
      env.read_frame == nullptr ||
      !env.read_frame(env.context, after) ||
      after.date_raw != expected.date_raw ||
      after.actor_character_id != expected.actor_character_id ||
      after.thread_id != expected.thread_id || !after.paused) {
    result.status = ActivityGuestRuleProvenanceStatusV1::frame_changed;
    return result;
  }
  const ActivityGuestRuleProvenanceRuleV1 *match = nullptr;
  for (std::uint32_t i = 0; i < capture.rule_count; ++i) {
    const auto &rule = capture.rules[i];
    if (rule.native_key_hash != native_key_hash) continue;
    if (match != nullptr) {
      result.status = ActivityGuestRuleProvenanceStatusV1::ambiguous_rule;
      return result;
    }
    match = &rule;
  }
  if (match == nullptr) {
    result.status = ActivityGuestRuleProvenanceStatusV1::rule_unavailable;
    return result;
  }
  result.status = ActivityGuestRuleProvenanceStatusV1::observed;
  result.normal_refresh_sequence = capture.sequence;
  result.native_key_hash = match->native_key_hash;
  result.raw_rule_character_count = match->raw_count;
  result.filtered_rule_character_count = match->filtered_count;
  std::copy_n(capture.filtered_ids.begin() + match->filtered_begin,
              match->filtered_count, result.filtered_ids.begin());
  result.candidate_membership = std::find(
      result.filtered_ids.begin(),
      result.filtered_ids.begin() + match->filtered_count,
      candidate_character_id) !=
      result.filtered_ids.begin() + match->filtered_count;
  return result;
}

bool VerifyActivityGuestRuleProvenanceExactAbiV1(
    const ActivityCostSlot12EnvironmentV1 &env) noexcept {
  if (!env.enabled || !env.primary_thread_suspended ||
      env.executable_sha256 != kActivityGuestRuleProvenanceExeSha256V1 ||
      env.module_base == 0 || env.read_memory == nullptr ||
      env.read_frame == nullptr)
    return false;
  std::array<std::uint8_t, kActivityGuestRuleRefreshPatchBytesV1>
      refresh{};
  std::array<std::uint8_t, kActivityGuestRuleEffectPatchBytesV1>
      effect{};
  std::array<std::uint8_t, 5> refresh_call{}, effect_call{};
  return ReadBytes(env, env.module_base, kActivityGuestRuleRefreshRvaV1,
                   refresh.data(), refresh.size()) &&
         refresh == kRefreshPrologue &&
         ReadBytes(env, env.module_base, kActivityGuestRuleEffectRvaV1,
                   effect.data(), effect.size()) &&
         effect == kEffectPrologue &&
         ReadBytes(env, env.module_base,
                   kActivityGuestRuleRefreshReturnRvaV1 - 5,
                   refresh_call.data(), refresh_call.size()) &&
         refresh_call == kRefreshCall &&
         ReadBytes(env, env.module_base,
                   kActivityGuestRuleEffectReturnRvaV1 - 5,
                   effect_call.data(), effect_call.size()) &&
         effect_call == kEffectCall;
}

bool InstallActivityGuestRuleProvenanceV1(
    ActivityGuestRuleProvenanceObserverV1 &observer,
    const ActivityCostSlot12EnvironmentV1 &env) noexcept {
  if (observer.installed || !VerifyActivityGuestRuleProvenanceExactAbiV1(env))
    return false;
  auto *refresh = reinterpret_cast<std::uint8_t *>(
      env.module_base + kActivityGuestRuleRefreshRvaV1);
  auto *effect = reinterpret_cast<std::uint8_t *>(
      env.module_base + kActivityGuestRuleEffectRvaV1);
  std::memcpy(observer.refresh_original.data(), refresh,
              observer.refresh_original.size());
  std::memcpy(observer.effect_original.data(), effect,
              observer.effect_original.size());
  observer.environment = env;
  ActivityGuestRuleProvenanceObserverV1 *expected = nullptr;
  if (!g_observer.compare_exchange_strong(expected, &observer)) return false;
  if (!Patch(effect, reinterpret_cast<const void *>(&EffectHook),
             observer.effect_original.data(),
             observer.effect_original.size(), observer.effect_trampoline)) {
    g_observer.store(nullptr);
    return false;
  }
  if (!Patch(refresh, reinterpret_cast<const void *>(&RefreshHook),
             observer.refresh_original.data(),
             observer.refresh_original.size(),
             observer.refresh_trampoline)) {
    const bool rolled_back =
        Restore(effect, observer.effect_original.data(),
                observer.effect_original.size());
    if (rolled_back) {
      g_observer.store(nullptr);
      VirtualFree(observer.effect_trampoline, 0, MEM_RELEASE);
      observer.effect_trampoline = nullptr;
    }
    return false;
  }
  observer.installed = true;
  return true;
}

std::string_view ActivityGuestRuleProvenanceStatusKeyV1(
    ActivityGuestRuleProvenanceStatusV1 status) noexcept {
  switch (status) {
  case ActivityGuestRuleProvenanceStatusV1::observed: return "observed";
  case ActivityGuestRuleProvenanceStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityGuestRuleProvenanceStatusV1::no_normal_refresh:
    return "no_normal_refresh";
  case ActivityGuestRuleProvenanceStatusV1::frame_changed:
    return "frame_changed";
  case ActivityGuestRuleProvenanceStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityGuestRuleProvenanceStatusV1::rule_unavailable:
    return "rule_unavailable";
  case ActivityGuestRuleProvenanceStatusV1::ambiguous_rule:
    return "ambiguous_rule";
  case ActivityGuestRuleProvenanceStatusV1::capture_overflow:
    return "capture_overflow";
  case ActivityGuestRuleProvenanceStatusV1::native_read_failed:
    return "native_read_failed";
  }
  return "native_read_failed";
}

std::string DescribeActivityGuestRuleRefreshDiagnosticsV1(
    const ActivityGuestRuleProvenanceObserverV1 &observer) {
  constexpr std::array<std::string_view,
      static_cast<std::size_t>(ActivityGuestRuleRefreshDiagnosticV1::count)>
      labels{"hook", "nested", "invalid_group", "wrong_caller",
             "invalid_args", "frame_unavailable", "unpaused",
             "actor_thread", "planner", "feast_type", "stage_read",
             "stage_not_five", "accepted"};
  std::string result = "no_normal_refresh";
  for (std::size_t i = 0; i < labels.size(); ++i) {
    result += " ";
    result += labels[i];
    result += "=";
    result += std::to_string(observer.refresh_diagnostics[i].load(
        std::memory_order_relaxed));
  }
  result += " last_stage=";
  result += std::to_string(observer.last_seen_stage.load(
      std::memory_order_relaxed));
  return result;
}

} // namespace xar::bridge

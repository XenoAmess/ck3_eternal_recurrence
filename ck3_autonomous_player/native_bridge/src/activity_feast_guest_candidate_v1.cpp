#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"

#include "xar_bridge/ck3_12002_feast_guests_abi.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kPlayedIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorageRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackRva = 0x570C138;
constexpr std::uintptr_t kWorldRva = 0x570E068;
constexpr std::uintptr_t kProvinceFallbackRva = 0x57BFBA8;
constexpr std::size_t kMaxGroups = 64;
constexpr std::size_t kMaxCandidates = 4096;
constexpr std::size_t kMaxSelected = 128;
constexpr std::int64_t kDateEpochRaw = 0x29C55C0;

void Mix(std::uint64_t &fingerprint, const void *data,
         std::size_t size) noexcept {
  const auto *bytes = static_cast<const std::uint8_t *>(data);
  for (std::size_t i = 0; i < size; ++i) {
    fingerprint ^= bytes[i];
    fingerprint *= 1099511628211ULL;
  }
}

template <typename T>
bool Read(const ActivityPlannerDiagEnvironmentV1 &source,
          std::uintptr_t address, T &value) noexcept {
  return source.read_memory != nullptr && address != 0 &&
         source.read_memory(source.context, address, &value, sizeof(value));
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &source,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  if (base == source.module_base)
    offset = ActivityFeastGuestRvaV1(source.admitted_executable_sha256, offset);
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         Read(source, base + offset, value);
}

template <std::size_t N>
bool BytesAt(const ActivityPlannerDiagEnvironmentV1 &source,
             std::uintptr_t rva,
             const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return source.read_memory != nullptr &&
         source.read_memory(source.context, source.module_base + ActivityFeastGuestRvaV1(source.admitted_executable_sha256, rva),
                            actual.data(), actual.size()) && actual == expected;
}

bool VerifyAbi(const ActivityFeastGuestJoinEnvironmentV1 &env) noexcept {
  const auto &source = env.diagnostic;
  return env.enabled && env.passive_cost != nullptr && source.enabled &&
         source.module_base != 0 &&
         IsActivityPlannerSupportedBuildV1(source) &&
         env.passive_cost->environment.module_base == source.module_base &&
         env.passive_cost->environment.executable_sha256 ==
             source.admitted_executable_sha256 &&
         // 0x10B0780 maps active rules +0x1A18 into filtered groups +0x1590.
         BytesAt(source, 0x10B0796,
                 (IsActivityPlanner12002V1(source) ? std::array<std::uint8_t, 7>{0x4C, 0x8D, 0xB9, 0xC8, 0x15, 0, 0} : std::array<std::uint8_t, 7>{0x4C, 0x8D, 0xB9, 0x90, 0x15, 0, 0})) &&
         BytesAt(source, 0x10B07A3,
                 (IsActivityPlanner12002V1(source) ? std::array<std::uint8_t, 7>{0x48, 0x81, 0xC1, 0x50, 0x1A, 0, 0} : std::array<std::uint8_t, 7>{0x48, 0x81, 0xC1, 0x18, 0x1A, 0, 0})) &&
         // 0x28D06C0 removes IDs rejected by the native guest predicate.
         BytesAt(source, 0x28D07A1,
                 (IsActivityPlanner12002V1(source) ? std::array<std::uint8_t, 5>{0xE8, 0xDA, 0xE3, 0xFF, 0xFF} : std::array<std::uint8_t, 5>{0xE8, 0xBA, 0xE4, 0xFF, 0xFF})) &&
         // Stock guest-window list loads its planner at +0xD0 in 1.20,
         // then reads the planner's filtered groups at +0x15C8. The old
         // window used +0x100 and planner groups +0x1590.
         BytesAt(source, 0x151CD75,
                 (IsActivityPlanner12002V1(source)
                      ? std::array<std::uint8_t, 7>{0x48,0x8B,0x90,0xC8,0x15,0,0}
                      : std::array<std::uint8_t, 7>{0x48,0x8B,0x90,0x90,0x15,0,0}));
}

bool FeastType(const ActivityPlannerDiagEnvironmentV1 &source,
               std::uintptr_t type) noexcept {
  constexpr char key[] = "activity_feast";
  std::uintptr_t vtable = 0, data = type + 0x18;
  std::uint64_t size = 0, capacity = 0;
  if (!ReadAt(source, type, 0, vtable) ||
      vtable != source.module_base + ActivityFeastGuestRvaV1(source.admitted_executable_sha256, 0x440E308) ||
      !ReadAt(source, type, 0x28, size) ||
      !ReadAt(source, type, 0x30, capacity) ||
      size != sizeof(key) - 1 || size > capacity ||
      (capacity > 15 && !ReadAt(source, type, 0x18, data)))
    return false;
  std::array<char, sizeof(key) - 1> actual{};
  return source.read_memory(source.context, data, actual.data(),
                            actual.size()) &&
         std::memcmp(actual.data(), key, actual.size()) == 0;
}

bool ResolveCharacter(const ActivityPlannerDiagEnvironmentV1 &source,
                      std::int32_t id, std::uintptr_t &character) noexcept {
  std::uintptr_t storage = 0, fallback = 0, slots = 0;
  std::int32_t capacity = 0, found_id = -1;
  if (id <= 0 ||
      !ReadAt(source, source.module_base, kCharacterStorageRva, storage) ||
      storage == 0 ||
      !ReadAt(source, source.module_base, kCharacterFallbackRva, fallback) ||
      !ReadAt(source, storage, 0x20, slots) || slots == 0 ||
      !ReadAt(source, storage, 0x2C, capacity) ||
      capacity <= 0 || capacity > 0x01000000)
    return false;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFu;
  return index < static_cast<std::uint32_t>(capacity) &&
         ReadAt(source, slots, static_cast<std::size_t>(index) * 0x10 + 8,
                character) &&
         character != 0 && character != fallback &&
         ReadAt(source, character, 0x18, found_id) && found_id == id;
}

bool CaptureCurrent(const ActivityFeastGuestJoinEnvironmentV1 &env,
                    const ActivityPlannerDiagFrameV1 &expected,
                    ActivityCostSlot12CaptureV1 &capture) noexcept {
  if (expected.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      expected.date_raw > (std::numeric_limits<std::int32_t>::max)())
    return false;
  return ReadActivityCostSlot12PassiveV1(
             *env.passive_cost,
             {static_cast<std::int32_t>(expected.date_raw),
              expected.actor_character_id, GetCurrentThreadId(), true},
             capture) == ActivityCostSlot12ReadStatusV1::observed;
}

ActivityFeastGuestCandidateStatusV1 Arrival(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ActivityCostSlot12CaptureV1 &capture,
    const ActivityPlannerDiagFrameV1 &expected, std::int32_t id,
    std::uintptr_t character, std::int32_t &travel_days,
    std::int32_t &arrival_raw, std::int32_t &start_raw) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t world = 0, province_table = 0, provinces = 0;
  std::uintptr_t location_row = 0, destination = 0;
  std::int32_t today = 0, province_id = -1, province_count = 0;
  if (!ReadAt(source, source.module_base, kWorldRva, world) || world == 0 ||
      !ReadAt(source, world, 8, today) || today != expected.date_raw ||
      !ReadAt(source, world, 0xA0, province_table) || province_table == 0 ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1578), location_row) ||
      location_row == 0 || !ReadAt(source, location_row, 8, province_id) ||
      !ReadAt(source, province_table, 0x14C, province_count) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1550), start_raw))
    return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  if (province_id >= 1 && province_id < province_count &&
      ReadAt(source, province_table, 0x140, provinces) && provinces != 0 &&
      ReadAt(source, provinces, static_cast<std::size_t>(province_id) * 8,
             destination) && destination != 0) {
  } else if (!ReadAt(source, source.module_base, kProvinceFallbackRva,
                     destination) || destination == 0) {
    return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  }
  const auto activity_invoke = env.invoke_activity != nullptr
                                   ? env.invoke_activity
                                   : (IsActivityPlanner12002V1(source) ? &InvokeActivityFeastNativePlannerActivity12002V1 : &InvokeActivityFeastNativePlannerActivityV1);
  const auto activity = activity_invoke(env.arrival_context, source.module_base,
                                        capture.planner);
  std::uintptr_t activity_rows = 0;
  std::int32_t activity_count = -1;
  if (activity == 0 || !ReadAt(source, activity, 0x10, activity_rows) ||
      !ReadAt(source, activity, 0x1C, activity_count) ||
      activity_count < 0 || activity_count > 512 ||
      (activity_count != 0 && activity_rows == 0))
    return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  bool already_in_activity = false;
  for (std::int32_t index = 0; index < activity_count; ++index) {
    std::int32_t row_id = -1;
    if (!ReadAt(source, activity_rows, static_cast<std::size_t>(index) * 0x20,
                row_id))
      return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
    if (row_id == id) {
      already_in_activity = true;
      break;
    }
  }
  if (!already_in_activity) {
    const auto invoke = env.invoke_travel_days != nullptr
                            ? env.invoke_travel_days
                            : (IsActivityPlanner12002V1(source) ? &InvokeActivityFeastNativeTravelDays12002V1 : &InvokeActivityFeastNativeTravelDaysV1);
    if (!invoke(env.arrival_context, source.module_base, character,
                destination, travel_days))
      return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  } else {
    std::int32_t record_index = -1, record_count = 0, current_day = 0;
    std::uintptr_t records = 0;
    if (!ReadAt(source, activity, 0x83C, record_index) ||
        !ReadAt(source, activity, 0x36C, record_count) ||
        !ReadAt(source, activity, 0x360, records) ||
        !ReadAt(source, world, 0x9C, current_day) ||
        record_count < 0 || record_count > 512)
      return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
    travel_days = 0;
    if (record_index >= 0 && record_index < record_count) {
      std::int32_t recorded_raw = 0;
      if (records == 0 || !ReadAt(source, records, 0x38, recorded_raw))
        return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
      const auto days = (static_cast<std::int64_t>(recorded_raw) -
                         kDateEpochRaw) / 24 - current_day;
      if (days < (std::numeric_limits<std::int32_t>::min)() ||
          days > (std::numeric_limits<std::int32_t>::max)())
        return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
      travel_days = static_cast<std::int32_t>(days);
    }
  }
  if (travel_days == (std::numeric_limits<std::int32_t>::max)())
    return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  const auto predicted = static_cast<std::int64_t>(today) +
                         static_cast<std::int64_t>(travel_days) * 24;
  if (predicted < (std::numeric_limits<std::int32_t>::min)() ||
      predicted > (std::numeric_limits<std::int32_t>::max)())
    return ActivityFeastGuestCandidateStatusV1::arrival_unavailable;
  arrival_raw = static_cast<std::int32_t>(predicted);
  return ActivityFeastGuestCandidateStatusV1::observed;
}

ActivityFeastGuestCandidateStatusV1 ReadOne(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ActivityCostSlot12CaptureV1 &capture,
    const ActivityPlannerDiagFrameV1 &expected,
    ActivityFeastGuestCandidateResultV1 &result,
    std::int32_t target_character_id) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t groups = 0, selected = 0, rules = 0;
  std::uintptr_t current_planner = 0;
  std::int32_t group_count = -1, selected_count = -1;
  std::int32_t rule_count = -1, host_id = -1;
  std::uint32_t played_id = 0;
  if (!ReadAt(source, capture.owner, 0x3C0, current_planner) ||
      current_planner != capture.planner ||
      !ReadAt(source, source.module_base, kPlayedIdRva, played_id) ||
      played_id != static_cast<std::uint32_t>(expected.actor_character_id) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1538), host_id) ||
      host_id != expected.actor_character_id ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1590), groups) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x159C), group_count) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1A18), rules) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1A24), rule_count) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1678), selected) ||
      !ReadAt(source, capture.planner, ActivityFeastGuestPlannerOffsetV1(source.admitted_executable_sha256, 0x1684), selected_count) ||
      group_count < 0 || group_count > static_cast<std::int32_t>(kMaxGroups) ||
      rule_count < 0 || rule_count > static_cast<std::int32_t>(kMaxGroups) ||
      selected_count < 0 ||
      selected_count > static_cast<std::int32_t>(kMaxSelected) ||
      (group_count != 0 && groups == 0) ||
      (rule_count != 0 && rules == 0) ||
      (selected_count != 0 && selected == 0))
    return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
  std::uint64_t fingerprint = 14695981039346656037ULL;
  Mix(fingerprint, &groups, sizeof(groups));
  Mix(fingerprint, &group_count, sizeof(group_count));
  Mix(fingerprint, &rules, sizeof(rules));
  Mix(fingerprint, &rule_count, sizeof(rule_count));
  Mix(fingerprint, &selected_count, sizeof(selected_count));
  for (std::int32_t i = 0; i < rule_count; ++i) {
    std::array<std::uint8_t, 16> row{};
    if (!source.read_memory(source.context,
                            rules + static_cast<std::size_t>(i) * 16,
                            row.data(), row.size()))
      return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
    Mix(fingerprint, row.data(), row.size());
  }
  for (std::int32_t i = 0; i < selected_count; ++i) {
    std::array<std::uint8_t, 16> row{};
    if (!source.read_memory(source.context,
                            selected + static_cast<std::size_t>(i) * 16,
                            row.data(), row.size()))
      return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
    Mix(fingerprint, row.data(), row.size());
  }
  const auto invoke_join = env.invoke_join != nullptr
                               ? env.invoke_join
                               : (IsActivityPlanner12002V1(source) ? &InvokeActivityFeastNativePlannerGuestJoin12002V1 : &InvokeActivityFeastNativePlannerGuestJoinV1);
  std::array<std::int32_t, kMaxCandidates> candidates{};
  std::size_t examined = 0;
  for (std::int32_t group = 0; group < group_count; ++group) {
    std::uintptr_t ids = 0;
    std::int32_t count = -1;
    const auto row = groups + static_cast<std::size_t>(group) * 0x18;
    if (!ReadAt(source, row, 0, ids) || !ReadAt(source, row, 0x0C, count) ||
        count < 0 || (count != 0 && ids == 0) ||
        examined + static_cast<std::size_t>(count) > kMaxCandidates)
      return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
    Mix(fingerprint, &ids, sizeof(ids));
    Mix(fingerprint, &count, sizeof(count));
    for (std::int32_t i = 0; i < count; ++i) {
      std::int32_t id = -1;
      if (!ReadAt(source, ids, static_cast<std::size_t>(i) * 4, id))
        return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
      Mix(fingerprint, &id, sizeof(id));
      candidates[examined++] = id;
    }
  }
  result.source_fingerprint = fingerprint;
  result.active_rule_count = rule_count;
  result.filtered_group_count = group_count;
  result.selected_row_count = selected_count;
  for (std::size_t i = 0; i < examined; ++i) {
    const auto id = candidates[i];
    if (id <= 0)
      return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
    if (target_character_id != 0 && id != target_character_id) continue;
    if (id == host_id) continue;
    bool already_selected = false;
    for (std::int32_t j = 0; j < selected_count; ++j) {
      std::int32_t selected_id = -1;
      if (!ReadAt(source, selected,
                  static_cast<std::size_t>(j) * 0x10 + 8, selected_id))
        return ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable;
      if (selected_id == id) { already_selected = true; break; }
    }
    if (target_character_id == 0 && already_selected) continue;
    std::uintptr_t character = 0;
    std::int64_t join_raw = 0;
    if (!ResolveCharacter(source, id, character) ||
        !invoke_join(env.join_context, source.module_base, capture.planner,
                     character, join_raw))
      return ActivityFeastGuestCandidateStatusV1::native_evaluation_failed;
    if (target_character_id == 0 && join_raw <= 0) continue;
    std::int32_t travel_days = 0, arrival_raw = 0, start_raw = 0;
    const auto arrival = Arrival(env, capture, expected, id, character,
                                 travel_days, arrival_raw, start_raw);
    if (arrival != ActivityFeastGuestCandidateStatusV1::observed)
      return arrival;
    if (target_character_id == 0 && arrival_raw > start_raw) continue;
    result.character_id = id;
    result.planner_join_raw = join_raw;
    result.travel_days = travel_days;
    result.arrival_raw = arrival_raw;
    result.planned_start_raw = start_raw;
    result.native_filtered = true;
    result.selected_member = already_selected;
    return ActivityFeastGuestCandidateStatusV1::observed;
  }
  return target_character_id == 0
             ? ActivityFeastGuestCandidateStatusV1::no_qualified_candidate
             : ActivityFeastGuestCandidateStatusV1::target_not_filtered;
}

} // namespace

ActivityFeastGuestCandidateResultV1 ReadActivityFeastGuestCandidateV1(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected,
    std::int32_t target_character_id) noexcept {
  ActivityFeastGuestCandidateResultV1 result{};
  result.frame = expected;
  if (!VerifyAbi(env)) return result;
  if (!expected.application_main_thread || !expected.paused ||
      !expected.map_ready || !expected.actor_alive) {
    result.status = ActivityFeastGuestCandidateStatusV1::frame_changed;
    return result;
  }
  const auto before = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  if (before.status != ActivityPlannerDiagStatusV1::observed ||
      !before.value.planner_present || before.value.stage != 5 ||
      !before.value.widget_attached || !before.value.widget_visible ||
      (before.value.host_view_activity_key_known &&
       std::string_view(before.value.host_view_activity_key.data(),
                        before.value.host_view_activity_key_size) !=
           "activity_feast")) {
    result.status = ActivityFeastGuestCandidateStatusV1::planner_unavailable;
    return result;
  }
  ActivityCostSlot12CaptureV1 capture{};
  if (!CaptureCurrent(env, expected, capture)) {
    result.status = ActivityFeastGuestCandidateStatusV1::no_normal_refresh;
    return result;
  }
  if (capture.planning_stage != 5 ||
      capture.frame.actor_character_id != expected.actor_character_id ||
      capture.frame.date_raw != expected.date_raw ||
      !FeastType(env.diagnostic, capture.activity_type)) {
    result.status = ActivityFeastGuestCandidateStatusV1::configuration_changed;
    return result;
  }
  ActivityFeastGuestCandidateResultV1 first{}, second{};
  const auto first_status = ReadOne(env, capture, expected, first,
                                    target_character_id);
  const auto second_status = ReadOne(env, capture, expected, second,
                                     target_character_id);
  const auto after = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  ActivityCostSlot12CaptureV1 capture_after{};
  if (after.status != ActivityPlannerDiagStatusV1::observed ||
      after.value != before.value || !CaptureCurrent(env, expected,
                                                     capture_after) ||
      capture_after.sequence != capture.sequence ||
      capture_after.planner != capture.planner ||
      capture_after.configuration_fingerprint !=
          capture.configuration_fingerprint ||
      first_status != second_status || first != second) {
    result.status = ActivityFeastGuestCandidateStatusV1::configuration_changed;
    return result;
  }
  result.status = first_status;
  if (first_status == ActivityFeastGuestCandidateStatusV1::observed ||
      first_status == ActivityFeastGuestCandidateStatusV1::no_qualified_candidate ||
      (target_character_id != 0 &&
       first_status == ActivityFeastGuestCandidateStatusV1::target_not_filtered)) {
    result = first;
    result.frame = expected;
    result.status = first_status;
    result.normal_refresh_sequence = capture.sequence;
  }
  return result;
}

std::string_view ActivityFeastGuestCandidateStatusKeyV1(
    ActivityFeastGuestCandidateStatusV1 status) noexcept {
  switch (status) {
  case ActivityFeastGuestCandidateStatusV1::observed: return "observed";
  case ActivityFeastGuestCandidateStatusV1::no_qualified_candidate:
    return "no_qualified_candidate";
  case ActivityFeastGuestCandidateStatusV1::target_not_filtered:
    return "target_not_filtered";
  case ActivityFeastGuestCandidateStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityFeastGuestCandidateStatusV1::frame_changed:
    return "frame_changed";
  case ActivityFeastGuestCandidateStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityFeastGuestCandidateStatusV1::no_normal_refresh:
    return "no_normal_refresh";
  case ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable:
    return "candidate_source_unavailable";
  case ActivityFeastGuestCandidateStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityFeastGuestCandidateStatusV1::arrival_unavailable:
    return "arrival_unavailable";
  case ActivityFeastGuestCandidateStatusV1::configuration_changed:
    return "configuration_changed";
  }
  return "unknown";
}

} // namespace xar::bridge

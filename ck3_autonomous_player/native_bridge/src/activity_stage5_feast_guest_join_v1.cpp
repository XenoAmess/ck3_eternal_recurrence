#include "xar_bridge/activity_stage5_feast_guest_join_v1.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kPlayedCharacterIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorageRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackRva = 0x570C138;
constexpr std::uintptr_t kWorldRva = 0x570E068;
constexpr std::uintptr_t kProvinceFallbackRva = 0x57BFBA8;
constexpr std::int64_t kNativeDateEpochRaw = 0x29C55C0;
constexpr std::array<std::uint8_t, 7> kNormalGuestRowsRead{
    0x48, 0x8B, 0x83, 0x78, 0x16, 0x00, 0x00};
constexpr std::array<std::uint8_t, 5> kOriginalJoinCall{
    0xE8, 0xF5, 0x27, 0x00, 0x00};
constexpr std::array<std::uint8_t, 4> kPositiveJoinCacheWrite{
    0x88, 0x0C, 0x07, 0x48};
constexpr std::array<std::uint8_t, 5> kNativeTravelFallbackCall{
    0xE8, 0x54, 0xA9, 0xF5, 0x01};
constexpr std::array<std::uint8_t, 4> kNativeArrivalDateWrite{
    0x48, 0x89, 0x4B, 0x04};

template <typename T>
bool Read(const ActivityPlannerDiagEnvironmentV1 &env,
          std::uintptr_t address, T &output) noexcept {
  return env.read_memory != nullptr && address != 0 &&
         env.read_memory(env.context, address, &output, sizeof(output));
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, T &output) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         Read(env, base + offset, output);
}

bool VerifyAbi(const ActivityFeastGuestJoinEnvironmentV1 &env) noexcept {
  const auto &source = env.diagnostic;
  std::array<std::uint8_t, 7> rows_read{};
  std::array<std::uint8_t, 5> join_call{};
  std::array<std::uint8_t, 4> cache_write{};
  std::array<std::uint8_t, 5> travel_call{};
  std::array<std::uint8_t, 4> arrival_write{};
  return env.enabled && env.passive_cost != nullptr && source.enabled &&
         source.module_base != 0 &&
         source.admitted_executable_sha256 == kActivityPlannerDiagExeSha256V1 &&
         env.passive_cost->environment.module_base == source.module_base &&
         env.passive_cost->environment.executable_sha256 ==
             kActivityCostSlot12ExeSha256V1 &&
         ReadAt(source, source.module_base, 0x10AE220, rows_read) &&
         rows_read == kNormalGuestRowsRead &&
         ReadAt(source, source.module_base, 0x10AE286, join_call) &&
         join_call == kOriginalJoinCall &&
         ReadAt(source, source.module_base, 0x10AE298, cache_write) &&
         cache_write == kPositiveJoinCacheWrite &&
         ReadAt(source, source.module_base, 0x972827, travel_call) &&
         travel_call == kNativeTravelFallbackCall &&
         ReadAt(source, source.module_base, 0x9728CA, arrival_write) &&
         arrival_write == kNativeArrivalDateWrite;
}

bool ResolveCharacter(const ActivityPlannerDiagEnvironmentV1 &source,
                      std::int32_t character_id,
                      std::uintptr_t &character) noexcept {
  std::uintptr_t storage = 0, fallback = 0, slots = 0;
  std::int32_t capacity = 0, found_id = -1;
  if (character_id <= 0 ||
      !ReadAt(source, source.module_base, kCharacterStorageRva, storage) ||
      storage == 0 ||
      !ReadAt(source, source.module_base, kCharacterFallbackRva, fallback) ||
      !ReadAt(source, storage, 0x20, slots) || slots == 0 ||
      !ReadAt(source, storage, 0x2C, capacity) ||
      capacity <= 0 || capacity > 0x01000000)
    return false;
  const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFu;
  return index < static_cast<std::uint32_t>(capacity) &&
         ReadAt(source, slots, static_cast<std::size_t>(index) * 0x10 + 8,
                character) &&
         character != 0 && character != fallback &&
         ReadAt(source, character, 0x18, found_id) &&
         found_id == character_id;
}

struct ArrivalInputs {
  std::uintptr_t activity = 0;
  std::uintptr_t destination = 0;
  std::int32_t today_raw = 0;
  std::int32_t current_day = 0;
  std::int32_t planned_start_raw = 0;
};

bool ReadArrivalInputs(const ActivityFeastGuestJoinEnvironmentV1 &env,
                       const ActivityCostSlot12CaptureV1 &capture,
                       const ActivityPlannerDiagFrameV1 &expected,
                       ArrivalInputs &inputs) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t world = 0, location_row = 0, province_table = 0;
  std::uintptr_t provinces = 0;
  std::int32_t province_index = -1, province_capacity = 0;
  if (!ReadAt(source, source.module_base, kWorldRva, world) || world == 0 ||
      !ReadAt(source, world, 8, inputs.today_raw) ||
      inputs.today_raw != expected.date_raw ||
      !ReadAt(source, world, 0x9C, inputs.current_day) ||
      !ReadAt(source, world, 0xA0, province_table) ||
      province_table == 0 ||
      !ReadAt(source, capture.planner, 0x1578, location_row) ||
      location_row == 0 ||
      !ReadAt(source, location_row, 8, province_index) ||
      !ReadAt(source, province_table, 0x14C, province_capacity) ||
      !ReadAt(source, capture.planner, 0x1550,
              inputs.planned_start_raw))
    return false;
  if (province_index >= 1 && province_index < province_capacity &&
      ReadAt(source, province_table, 0x140, provinces) && provinces != 0 &&
      ReadAt(source, provinces,
             static_cast<std::size_t>(province_index) * 8,
             inputs.destination) && inputs.destination != 0) {
    // Original 0x151AF0A..0x151AF15 selected-province branch.
  } else if (!ReadAt(source, source.module_base,
                     kProvinceFallbackRva, inputs.destination) ||
             inputs.destination == 0) {
    return false;
  }
  const auto invoke = env.invoke_activity != nullptr
                          ? env.invoke_activity
                          : &InvokeActivityFeastNativePlannerActivityV1;
  inputs.activity = invoke(env.arrival_context, source.module_base,
                           capture.planner);
  return inputs.activity != 0;
}

ActivityFeastGuestJoinStatusV1 ReadOriginalArrival(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ArrivalInputs &inputs, std::int32_t character_id,
    std::uintptr_t character, std::int32_t &travel_days,
    std::int32_t &arrival_raw, bool &late) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t rows = 0;
  std::int32_t count = -1;
  if (!ReadAt(source, inputs.activity, 0x10, rows) ||
      !ReadAt(source, inputs.activity, 0x1C, count) || count < 0 ||
      count > 512 || (count != 0 && rows == 0))
    return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
  bool found = false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t row_id = -1;
    if (!ReadAt(source, rows, static_cast<std::size_t>(index) * 0x20,
                row_id))
      return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
    if (row_id == character_id) {
      found = true;
      break;
    }
  }
  if (!found) {
    const auto invoke = env.invoke_travel_days != nullptr
                            ? env.invoke_travel_days
                            : &InvokeActivityFeastNativeTravelDaysV1;
    if (!invoke(env.arrival_context, source.module_base, character,
                inputs.destination, travel_days))
      return ActivityFeastGuestJoinStatusV1::arrival_evaluation_failed;
  } else {
    std::int32_t record_index = -1, record_count = 0;
    std::uintptr_t records = 0;
    if (!ReadAt(source, inputs.activity, 0x83C, record_index) ||
        !ReadAt(source, inputs.activity, 0x36C, record_count) ||
        !ReadAt(source, inputs.activity, 0x360, records) ||
        record_count < 0 || record_count > 512)
      return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
    // 0x972818 uses zero when the selected record index is invalid.
    travel_days = 0;
    if (record_index >= 0 && record_index < record_count) {
      std::int32_t recorded_date_raw = 0;
      // The original code checks index*0x48 but finally reads the first
      // record's +0x38 date at 0x9727EC, not the indexed record.
      if (records == 0 ||
          !ReadAt(source, records, 0x38, recorded_date_raw))
        return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
      const auto days =
          (static_cast<std::int64_t>(recorded_date_raw) -
           kNativeDateEpochRaw) /
              24 -
          inputs.current_day;
      if (days < (std::numeric_limits<std::int32_t>::min)() ||
          days > (std::numeric_limits<std::int32_t>::max)())
        return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
      travel_days = static_cast<std::int32_t>(days);
    }
  }
  if (travel_days == (std::numeric_limits<std::int32_t>::max)())
    return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
  const auto predicted = static_cast<std::int64_t>(inputs.today_raw) +
                         static_cast<std::int64_t>(travel_days) * 24;
  if (predicted < (std::numeric_limits<std::int32_t>::min)() ||
      predicted > (std::numeric_limits<std::int32_t>::max)())
    return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
  arrival_raw = static_cast<std::int32_t>(predicted);
  late = arrival_raw > inputs.planned_start_raw;
  return ActivityFeastGuestJoinStatusV1::observed;
}

ActivityFeastGuestJoinStatusV1 ReadOne(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ActivityCostSlot12CaptureV1 &capture,
    const ActivityPlannerDiagFrameV1 &expected,
    ActivityFeastGuestJoinResultV1 &result) noexcept {
  const auto &source = env.diagnostic;
  std::uintptr_t current_planner = 0, rows = 0, cache = 0;
  std::int32_t count = -1, host_id = -1;
  std::uint32_t played_id = 0;
  if (!ReadAt(source, capture.owner, 0x3C0, current_planner) ||
      current_planner != capture.planner ||
      !ReadAt(source, source.module_base, kPlayedCharacterIdRva, played_id) ||
      played_id != static_cast<std::uint32_t>(expected.actor_character_id) ||
      !ReadAt(source, capture.planner, 0x1538, host_id) ||
      host_id != expected.actor_character_id ||
      !ReadAt(source, capture.planner, 0x1678, rows) ||
      !ReadAt(source, capture.planner, 0x1684, count) ||
      !ReadAt(source, capture.planner, 0x1A30, cache) || count < 0 ||
      count > static_cast<std::int32_t>(kActivityFeastPlannerGuestLimitV1) ||
      (count != 0 && (rows == 0 || cache == 0)))
    return ActivityFeastGuestJoinStatusV1::guest_source_unavailable;
  ArrivalInputs arrival{};
  if (!ReadArrivalInputs(env, capture, expected, arrival))
    return ActivityFeastGuestJoinStatusV1::arrival_source_unavailable;
  const auto invoke = env.invoke_join != nullptr
                          ? env.invoke_join
                          : &InvokeActivityFeastNativePlannerGuestJoinV1;
  for (std::int32_t index = 0; index < count; ++index) {
    std::array<std::uint8_t, 16> row{};
    std::uint8_t cached = 0;
    if (!ReadAt(source, rows, static_cast<std::size_t>(index) * 16, row) ||
        !ReadAt(source, cache, static_cast<std::size_t>(index), cached))
      return ActivityFeastGuestJoinStatusV1::guest_source_unavailable;
    std::int32_t character_id = -1;
    std::memcpy(&character_id, row.data() + 8, sizeof(character_id));
    if (character_id == -1 || character_id == host_id) continue;
    std::uintptr_t character = 0;
    std::int64_t join_raw = 0;
    if (!ResolveCharacter(source, character_id, character) ||
        !invoke(env.join_context, source.module_base, capture.planner,
                character, join_raw))
      return ActivityFeastGuestJoinStatusV1::native_evaluation_failed;
    const bool positive = join_raw > 0;
    if ((cached != 0) != positive)
      return ActivityFeastGuestJoinStatusV1::cache_disagreed;
    std::int32_t travel_days = 0, predicted_arrival_raw = 0;
    bool late = false;
    const auto arrival_status = ReadOriginalArrival(
        env, arrival, character_id, character, travel_days,
        predicted_arrival_raw, late);
    if (arrival_status != ActivityFeastGuestJoinStatusV1::observed)
      return arrival_status;
    auto &output = result.rows[result.selected_nonhost_count++];
    output = {character_id, join_raw, positive, predicted_arrival_raw,
              travel_days, late};
    if (positive) ++result.positive_join_count;
    if (positive && !late) ++result.timely_positive_join_count;
  }
  result.arrival_time_observed = true;
  return ActivityFeastGuestJoinStatusV1::observed;
}

bool CaptureCurrent(const ActivityFeastGuestJoinEnvironmentV1 &env,
                    const ActivityPlannerDiagFrameV1 &expected,
                    ActivityCostSlot12CaptureV1 &capture) noexcept {
  if (expected.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      expected.date_raw > (std::numeric_limits<std::int32_t>::max)())
    return false;
  const ActivityCostSlot12FrameV1 cost_frame{
      static_cast<std::int32_t>(expected.date_raw),
      expected.actor_character_id, GetCurrentThreadId(), true};
  return ReadActivityCostSlot12PassiveV1(*env.passive_cost, cost_frame,
                                         capture) ==
         ActivityCostSlot12ReadStatusV1::observed;
}

} // namespace

bool InvokeActivityFeastNativePlannerGuestJoinV1(
    void *, std::uintptr_t module_base, std::uintptr_t planner,
    std::uintptr_t character, std::int64_t &join_raw) noexcept {
  if (module_base == 0 || planner == 0 || character == 0) return false;
  using Original = std::int64_t *(__fastcall *)(
      std::int64_t *, void *, void *);
  const auto evaluator = reinterpret_cast<Original>(
      module_base + kActivityFeastPlannerGuestJoinRvaV1);
  std::int64_t value = 0;
  if (evaluator(&value, reinterpret_cast<void *>(planner),
                reinterpret_cast<void *>(character)) != &value)
    return false;
  join_raw = value;
  return true;
}

std::uintptr_t InvokeActivityFeastNativePlannerActivityV1(
    void *, std::uintptr_t module_base,
    std::uintptr_t planner) noexcept {
  if (module_base == 0 || planner == 0) return 0;
  using Original = void *(__fastcall *)(void *);
  const auto get_activity = reinterpret_cast<Original>(
      module_base + 0x10CDA10);
  return reinterpret_cast<std::uintptr_t>(
      get_activity(reinterpret_cast<void *>(planner)));
}

bool InvokeActivityFeastNativeTravelDaysV1(
    void *, std::uintptr_t module_base, std::uintptr_t character,
    std::uintptr_t destination, std::int32_t &days) noexcept {
  if (module_base == 0 || character == 0 || destination == 0) return false;
  using Original = std::int32_t(__fastcall *)(void *, void *);
  const auto get_days = reinterpret_cast<Original>(
      module_base + 0x28CD180);
  days = get_days(reinterpret_cast<void *>(character),
                  reinterpret_cast<void *>(destination));
  return days != (std::numeric_limits<std::int32_t>::max)();
}

ActivityFeastGuestJoinResultV1 ReadActivityFeastGuestJoinV1(
    const ActivityFeastGuestJoinEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityFeastGuestJoinResultV1 result{};
  result.frame = expected;
  if (!VerifyAbi(env)) return result;
  if (!expected.application_main_thread || !expected.paused ||
      !expected.map_ready || !expected.actor_alive) {
    result.status = ActivityFeastGuestJoinStatusV1::frame_changed;
    return result;
  }
  const auto before = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  if (before.status != ActivityPlannerDiagStatusV1::observed ||
      !before.value.planner_present || before.value.stage != 5 ||
      !before.value.widget_attached || !before.value.widget_visible ||
      !before.value.host_view_activity_key_known ||
      std::string_view(before.value.host_view_activity_key.data(),
                       before.value.host_view_activity_key_size) !=
          "activity_feast") {
    result.status = ActivityFeastGuestJoinStatusV1::planner_unavailable;
    return result;
  }
  ActivityCostSlot12CaptureV1 capture{};
  if (!CaptureCurrent(env, expected, capture)) {
    result.status = ActivityFeastGuestJoinStatusV1::no_normal_refresh;
    return result;
  }
  if (capture.planning_stage != 5 || capture.frame.actor_character_id !=
                                         expected.actor_character_id ||
      capture.frame.date_raw != expected.date_raw) {
    result.status = ActivityFeastGuestJoinStatusV1::configuration_changed;
    return result;
  }
  ActivityFeastGuestJoinResultV1 first{};
  ActivityFeastGuestJoinResultV1 second{};
  const auto first_status = ReadOne(env, capture, expected, first);
  const auto second_status = ReadOne(env, capture, expected, second);
  const auto after = ReadActivityPlannerDiagV1(env.diagnostic, expected);
  ActivityCostSlot12CaptureV1 capture_after{};
  if (after.status != ActivityPlannerDiagStatusV1::observed ||
      after.value != before.value ||
      !CaptureCurrent(env, expected, capture_after) ||
      capture_after.sequence != capture.sequence ||
      capture_after.planner != capture.planner ||
      capture_after.configuration_fingerprint !=
          capture.configuration_fingerprint) {
    result.status = ActivityFeastGuestJoinStatusV1::configuration_changed;
    return result;
  }
  if (first_status != second_status ||
      first.selected_nonhost_count != second.selected_nonhost_count ||
      first.positive_join_count != second.positive_join_count ||
      first.timely_positive_join_count != second.timely_positive_join_count ||
      first.arrival_time_observed != second.arrival_time_observed ||
      first.rows != second.rows) {
    result.status = ActivityFeastGuestJoinStatusV1::configuration_changed;
    return result;
  }
  result.status = first_status;
  if (first_status == ActivityFeastGuestJoinStatusV1::observed) {
    result.normal_refresh_sequence = capture.sequence;
    result.selected_nonhost_count = first.selected_nonhost_count;
    result.positive_join_count = first.positive_join_count;
    result.timely_positive_join_count = first.timely_positive_join_count;
    result.arrival_time_observed = first.arrival_time_observed;
    result.rows = first.rows;
  }
  return result;
}

std::string_view ActivityFeastGuestJoinStatusKeyV1(
    ActivityFeastGuestJoinStatusV1 status) noexcept {
  switch (status) {
  case ActivityFeastGuestJoinStatusV1::observed: return "observed";
  case ActivityFeastGuestJoinStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityFeastGuestJoinStatusV1::frame_changed: return "frame_changed";
  case ActivityFeastGuestJoinStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityFeastGuestJoinStatusV1::no_normal_refresh:
    return "no_normal_refresh";
  case ActivityFeastGuestJoinStatusV1::configuration_changed:
    return "configuration_changed";
  case ActivityFeastGuestJoinStatusV1::guest_source_unavailable:
    return "guest_source_unavailable";
  case ActivityFeastGuestJoinStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityFeastGuestJoinStatusV1::cache_disagreed:
    return "cache_disagreed";
  case ActivityFeastGuestJoinStatusV1::arrival_source_unavailable:
    return "arrival_source_unavailable";
  case ActivityFeastGuestJoinStatusV1::arrival_evaluation_failed:
    return "arrival_evaluation_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

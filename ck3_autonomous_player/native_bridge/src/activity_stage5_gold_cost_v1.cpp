#include "xar_bridge/activity_stage5_gold_cost_v1.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kPlayedCharacterIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorageRva = 0x570C130;
constexpr std::uintptr_t kCharacterFallbackRva = 0x570C138;
constexpr std::uintptr_t kGoldGetterRva = 0xBDC460;
constexpr std::array<std::uint8_t, 13> kGetCostByNamePrologue{
    0x48, 0x89, 0x5C, 0x24, 0x18, 0x56, 0x57,
    0x41, 0x56, 0x48, 0x83, 0xEC, 0x30};
constexpr std::array<std::uint8_t, 4> kGetCostIndexedRead{
    0x49, 0x8B, 0x0C, 0xC6};
constexpr std::array<std::uint8_t, 7> kGoldGetterLeaf{
    0x48, 0x8B, 0x80, 0x00, 0x01, 0x00, 0x00};

struct NativeShortString {
  char inline_bytes[16]{};
  std::uint64_t length = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(NativeShortString) == 0x20);

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  output = base + offset;
  return true;
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  return environment.read_memory != nullptr && Add(base, offset, address) &&
         environment.read_memory(environment.context, address, &output,
                                 sizeof(output));
}

bool VerifyNamedCostAbi(
    const ActivityPlannerDiagEnvironmentV1 &environment) noexcept {
  std::array<std::uint8_t, kGetCostByNamePrologue.size()> prologue{};
  std::array<std::uint8_t, kGetCostIndexedRead.size()> indexed_read{};
  std::array<std::uint8_t, kGoldGetterLeaf.size()> gold_leaf{};
  return environment.enabled && environment.module_base != 0 &&
         environment.admitted_executable_sha256 ==
             kActivityPlannerDiagExeSha256V1 &&
         ReadAt(environment, environment.module_base,
                kActivityGetCostByNameRvaV1, prologue) &&
         prologue == kGetCostByNamePrologue &&
         ReadAt(environment, environment.module_base, 0x2CD9795,
                indexed_read) &&
         indexed_read == kGetCostIndexedRead &&
         ReadAt(environment, environment.module_base,
                kGoldGetterRva + 0x36, gold_leaf) &&
         gold_leaf == kGoldGetterLeaf;
}

bool ReadActorGold(const ActivityPlannerDiagEnvironmentV1 &environment,
                   std::int32_t expected_actor,
                   std::int64_t &gold_raw) noexcept {
  std::uint32_t played_id = 0, native_id = 0;
  std::uintptr_t storage = 0, fallback = 0, slots = 0, actor = 0,
                 extension = 0;
  std::int32_t capacity = 0;
  if (expected_actor <= 0 ||
      !ReadAt(environment, environment.module_base,
              kPlayedCharacterIdRva, played_id) ||
      played_id != static_cast<std::uint32_t>(expected_actor) ||
      !ReadAt(environment, environment.module_base,
              kCharacterStorageRva, storage) ||
      storage == 0 ||
      !ReadAt(environment, environment.module_base,
              kCharacterFallbackRva, fallback) ||
      !ReadAt(environment, storage, 0x20, slots) || slots == 0 ||
      !ReadAt(environment, storage, 0x2C, capacity) ||
      capacity <= 0 || capacity > 0x01000000)
    return false;
  const auto index = played_id & 0x00FFFFFFu;
  if (index >= static_cast<std::uint32_t>(capacity) ||
      !ReadAt(environment, slots,
              static_cast<std::size_t>(index) * 0x10 + 0x08, actor) ||
      actor == 0 || actor == fallback ||
      !ReadAt(environment, actor, 0x18, native_id) ||
      native_id != played_id ||
      !ReadAt(environment, actor, 0x1A8, extension))
    return false;
  // Original CCharacter.GetGold (0xBDC460) treats a null extension as zero.
  if (extension == 0) {
    gold_raw = 0;
    return true;
  }
  return ReadAt(environment, extension, 0x100, gold_raw);
}

bool IsCurrentPlanner(const ActivityPlannerDiagEnvironmentV1 &environment,
                      const ActivityCostSlot12CaptureV1 &capture) noexcept {
  std::uintptr_t current = 0;
  return ReadAt(environment, capture.owner, 0x3C0, current) &&
         current == capture.planner;
}

bool IsFeastStageFive(const ActivityPlannerDiagResultV1 &diagnostic) noexcept {
  if (diagnostic.status != ActivityPlannerDiagStatusV1::observed ||
      !diagnostic.value.planner_present ||
      !diagnostic.value.widget_attached ||
      !diagnostic.value.widget_visible || diagnostic.value.stage != 5)
    return false;
  if (!diagnostic.value.host_view_activity_key_known) return true;
  return std::string_view(diagnostic.value.host_view_activity_key.data(),
                          diagnostic.value.host_view_activity_key_size) ==
         "activity_feast";
}

} // namespace

bool InvokeActivityStage5NativeGoldCostV1(
    void *, std::uintptr_t module_base,
    std::uintptr_t cost_breakdown, std::int64_t &gold_raw) noexcept {
  if (module_base == 0 || cost_breakdown == 0) return false;
  NativeShortString key{};
  std::memcpy(key.inline_bytes, "gold", 5);
  key.length = 4;
  using GetCost = std::int64_t *(__fastcall *)(
      std::int64_t *, const void *, const NativeShortString *);
  const auto getter = reinterpret_cast<GetCost>(
      module_base + kActivityGetCostByNameRvaV1);
  std::int64_t result = 0;
  if (getter(&result, reinterpret_cast<const void *>(cost_breakdown),
             &key) != &result)
    return false;
  gold_raw = result;
  return true;
}

ActivityStage5GoldCostResultV1 ReadActivityStage5GoldCostV1(
    const ActivityStage5GoldCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage5GoldCostResultV1 result{};
  result.frame = expected;
  const auto &diagnostic = environment.diagnostic;
  auto *passive = environment.passive_cost;
  if (!environment.enabled || passive == nullptr ||
      !VerifyNamedCostAbi(diagnostic) ||
      !passive->environment.enabled ||
      passive->environment.module_base != diagnostic.module_base ||
      passive->environment.executable_sha256 !=
          kActivityCostSlot12ExeSha256V1)
    return result;
  if (!expected.application_main_thread || !expected.paused ||
      expected.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      expected.date_raw > (std::numeric_limits<std::int32_t>::max)()) {
    result.status = ActivityStage5GoldCostStatusV1::frame_changed;
    return result;
  }
  const auto first_diag = ReadActivityPlannerDiagV1(diagnostic, expected);
  if (first_diag.status == ActivityPlannerDiagStatusV1::frame_changed ||
      first_diag.status == ActivityPlannerDiagStatusV1::frame_unavailable) {
    result.status = ActivityStage5GoldCostStatusV1::frame_changed;
    return result;
  }
  if (first_diag.status != ActivityPlannerDiagStatusV1::observed) {
    result.status = ActivityStage5GoldCostStatusV1::planner_unavailable;
    return result;
  }
  if (!IsFeastStageFive(first_diag)) {
    result.status = ActivityStage5GoldCostStatusV1::not_feast_stage_five;
    return result;
  }

  const ActivityCostSlot12FrameV1 cost_frame{
      static_cast<std::int32_t>(expected.date_raw),
      expected.actor_character_id, GetCurrentThreadId(), true};
  ActivityCostSlot12CaptureV1 before{};
  const auto cost_status =
      ReadActivityCostSlot12PassiveV1(*passive, cost_frame, before);
  if (cost_status == ActivityCostSlot12ReadStatusV1::no_normal_refresh) {
    result.status = ActivityStage5GoldCostStatusV1::no_normal_refresh;
    return result;
  }
  if (cost_status == ActivityCostSlot12ReadStatusV1::frame_changed) {
    result.status = ActivityStage5GoldCostStatusV1::frame_changed;
    return result;
  }
  if (cost_status != ActivityCostSlot12ReadStatusV1::observed ||
      before.planning_stage != 5 || !IsCurrentPlanner(diagnostic, before)) {
    result.status = ActivityStage5GoldCostStatusV1::configuration_changed;
    return result;
  }
  result.normal_refresh_sequence = before.sequence;
  std::int64_t actor_gold_before = 0;
  if (!ReadActorGold(diagnostic, expected.actor_character_id,
                     actor_gold_before)) {
    result.status = ActivityStage5GoldCostStatusV1::actor_unavailable;
    return result;
  }

  std::uintptr_t breakdown = 0;
  if (!Add(before.planner, 0x1AD8, breakdown)) {
    result.status = ActivityStage5GoldCostStatusV1::configuration_changed;
    return result;
  }
  std::int64_t gold_cost_raw = 0;
  const auto invoke = environment.invoke_gold_cost != nullptr
                          ? environment.invoke_gold_cost
                          : &InvokeActivityStage5NativeGoldCostV1;
  if (!invoke(diagnostic.context, diagnostic.module_base,
              breakdown, gold_cost_raw)) {
    result.status = ActivityStage5GoldCostStatusV1::native_query_failed;
    return result;
  }

  const auto after_diag = ReadActivityPlannerDiagV1(diagnostic, expected);
  ActivityCostSlot12CaptureV1 after{};
  const auto after_status =
      ReadActivityCostSlot12PassiveV1(*passive, cost_frame, after);
  std::int64_t actor_gold_after = 0;
  if (after_diag.status != ActivityPlannerDiagStatusV1::observed ||
      !IsFeastStageFive(after_diag) ||
      after_status != ActivityCostSlot12ReadStatusV1::observed ||
      after.sequence != before.sequence ||
      after.planner != before.planner ||
      after.configuration_fingerprint != before.configuration_fingerprint ||
      !IsCurrentPlanner(diagnostic, after)) {
    result.status = ActivityStage5GoldCostStatusV1::configuration_changed;
    return result;
  }
  if (!ReadActorGold(diagnostic, expected.actor_character_id,
                     actor_gold_after) ||
      actor_gold_after != actor_gold_before) {
    result.status = ActivityStage5GoldCostStatusV1::actor_unavailable;
    return result;
  }
  result.gold_cost_raw = gold_cost_raw;
  result.actor_gold_raw = actor_gold_after;
  result.status = ActivityStage5GoldCostStatusV1::observed;
  return result;
}

std::string_view ActivityStage5GoldCostStatusKeyV1(
    ActivityStage5GoldCostStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage5GoldCostStatusV1::observed:
    return "observed";
  case ActivityStage5GoldCostStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage5GoldCostStatusV1::no_normal_refresh:
    return "no_normal_refresh";
  case ActivityStage5GoldCostStatusV1::frame_changed:
    return "frame_changed";
  case ActivityStage5GoldCostStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityStage5GoldCostStatusV1::not_feast_stage_five:
    return "not_feast_stage_five";
  case ActivityStage5GoldCostStatusV1::configuration_changed:
    return "configuration_changed";
  case ActivityStage5GoldCostStatusV1::actor_unavailable:
    return "actor_unavailable";
  case ActivityStage5GoldCostStatusV1::native_query_failed:
    return "native_query_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

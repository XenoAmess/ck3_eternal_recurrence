#include "xar_bridge/activity_planner_diag_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kGlobalInterfaceRoot = 0x570F7B8;
constexpr std::uintptr_t kPlayedCharacterId = 0x4FE7EE0;
constexpr std::uintptr_t kCharacterStorage = 0x570C130;
constexpr std::uintptr_t kCharacterFallback = 0x570C138;
constexpr std::uintptr_t kIdlerSourceType = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxType = 0x501EF50;
constexpr std::uintptr_t kIdlerGfxVtable = 0x40B1D30;
constexpr std::uintptr_t kHandlerVtable = 0x40AF630;
constexpr std::uintptr_t kPlannerPrimaryVtable = 0x41205F0;
constexpr std::uintptr_t kPlannerSecondaryVtable = 0x41206C8;
constexpr std::uintptr_t kHostPrimaryVtable = 0x4166528;
constexpr std::uintptr_t kHostSecondaryVtable = 0x4166620;
constexpr std::uintptr_t kActivityTypeVtable = 0x440E308;
constexpr std::uintptr_t kPlannerSlotZero = 0x10AC480;
constexpr std::uintptr_t kPlannerVisibilitySlotSeven = 0x1F30970;
constexpr std::uintptr_t kPlannerCostSlotEleven = 0xAA33F0;
constexpr std::uintptr_t kPlannerCostSlotTwelve = 0x10AE180;
constexpr std::uintptr_t kPlannerSecondarySlotZero = 0x10C8454;

constexpr std::array<std::uint8_t, 7> kPlannerOwnerWrite{
    0x49, 0x89, 0xB6, 0xD0, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 4> kWidgetRead{0x48, 0x8B, 0x59, 0x78};
constexpr std::array<std::uint8_t, 7> kStageRead{
    0x48, 0x63, 0x81, 0xB0, 0x1A, 0x00, 0x00};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &result) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  result = base + offset;
  return true;
}

bool Read(const ActivityPlannerDiagEnvironmentV1 &environment,
          std::uintptr_t address, void *value, std::size_t size) noexcept {
  return environment.read_memory != nullptr && address != 0 && value != nullptr &&
         size != 0 && environment.read_memory(environment.context, address,
                                              value, size);
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) &&
         Read(environment, address, &value, sizeof(value));
}

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &environment,
               std::uintptr_t rva,
               const std::array<std::uint8_t, N> &bytes) noexcept {
  std::array<std::uint8_t, N> observed{};
  return ReadAt(environment, environment.module_base, rva, observed) &&
         observed == bytes;
}

bool ReadStableKey(const ActivityPlannerDiagEnvironmentV1 &environment,
                   std::uintptr_t activity_type,
                   ActivityPlannerDiagValueV1 &value) noexcept {
  std::uintptr_t native_string = 0;
  if (!Add(activity_type, 0x18, native_string)) return false;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadAt(environment, native_string, 0x10, size) ||
      !ReadAt(environment, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size >= value.host_view_activity_key.size())
    return false;
  std::uintptr_t data = native_string;
  if (capacity > 15 && !ReadAt(environment, native_string, 0, data))
    return false;
  if (!Read(environment, data, value.host_view_activity_key.data(),
            static_cast<std::size_t>(size)))
    return false;
  if (!std::all_of(value.host_view_activity_key.begin(),
                   value.host_view_activity_key.begin() + size,
                   [](char ch) {
                     return (ch >= 'a' && ch <= 'z') ||
                            (ch >= '0' && ch <= '9') || ch == '_';
                   }))
    return false;
  value.host_view_activity_key_size = static_cast<std::uint16_t>(size);
  value.host_view_activity_key_known = true;
  return true;
}

bool FrameValid(const ActivityPlannerDiagFrameV1 &frame) noexcept {
  return frame.revision != 0 && frame.actor_character_id > 0 &&
         frame.application_main_thread && frame.paused && frame.map_ready &&
         frame.actor_alive;
}

bool VerifyAbi(const ActivityPlannerDiagEnvironmentV1 &environment) noexcept {
  if (!environment.enabled || environment.module_base == 0 ||
      !IsActivityPlannerSupportedBuildV1(environment) ||
      environment.read_memory == nullptr || environment.read_frame == nullptr ||
      environment.rtti_cast == nullptr ||
      environment.invoke_visibility == nullptr ||
      !(IsActivityPlanner12002V1(environment)
            ? (MatchCode(environment, 0x11B2885,
                   std::array<std::uint8_t, 8>{0x49, 0x89, 0xB4, 0x24, 0xA0, 0, 0, 0}) &&
               MatchCode(environment, 0x21603AA,
                   std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x60}) &&
               MatchCode(environment, 0x11B8693,
                   std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xE8, 0x1A, 0, 0}))
            : (MatchCode(environment, 0x10AC0F3, kPlannerOwnerWrite) &&
               MatchCode(environment, 0x1F3097A, kWidgetRead) &&
               MatchCode(environment, 0x10B0DC3, kStageRead))))
    return false;
  std::uintptr_t slot0 = 0;
  std::uintptr_t slot7 = 0;
  std::uintptr_t slot11 = 0;
  std::uintptr_t slot12 = 0;
  std::uintptr_t secondary_slot0 = 0;
  return ReadAt(environment, environment.module_base,
                ActivityPlannerRvaV1(environment, kPlannerPrimaryVtable), slot0) &&
         ReadAt(environment, environment.module_base,
                ActivityPlannerRvaV1(environment, kPlannerPrimaryVtable) + 7 * 8, slot7) &&
         ReadAt(environment, environment.module_base,
                ActivityPlannerRvaV1(environment, kPlannerPrimaryVtable) + 11 * 8, slot11) &&
         ReadAt(environment, environment.module_base,
                ActivityPlannerRvaV1(environment, kPlannerPrimaryVtable) + 12 * 8, slot12) &&
         ReadAt(environment, environment.module_base,
                ActivityPlannerRvaV1(environment, kPlannerSecondaryVtable), secondary_slot0) &&
         slot0 == environment.module_base + ActivityPlannerRvaV1(environment, kPlannerSlotZero) &&
         slot7 == environment.module_base + ActivityPlannerRvaV1(environment, kPlannerVisibilitySlotSeven) &&
         slot11 == environment.module_base + ActivityPlannerRvaV1(environment, kPlannerCostSlotEleven) &&
         slot12 == environment.module_base + ActivityPlannerRvaV1(environment, kPlannerCostSlotTwelve) &&
         secondary_slot0 ==
             environment.module_base + ActivityPlannerRvaV1(environment, kPlannerSecondarySlotZero);
}

ActivityPlannerDiagStatusV1 ReadOne(
    const ActivityPlannerDiagEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &frame,
    ActivityPlannerDiagValueV1 &value) noexcept {
  value = {};
  std::uintptr_t root = 0;
  std::uintptr_t idler = 0;
  if (!ReadAt(environment, environment.module_base, ActivityPlannerRvaV1(environment, kGlobalInterfaceRoot),
              root) || root == 0 || !ReadAt(environment, root, 0x10, idler) ||
      idler == 0)
    return ActivityPlannerDiagStatusV1::native_owner_unavailable;
  const auto gfx = environment.rtti_cast(
      environment.context, idler,
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerSourceType),
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerGfxType));
  std::uintptr_t gfx_vtable = 0;
  std::uintptr_t handler = 0;
  std::uintptr_t handler_vtable = 0;
  std::uint32_t played_id = 0;
  if (gfx == 0 || !ReadAt(environment, gfx, 0, gfx_vtable) ||
      !ReadAt(environment, gfx, 0x88, handler) || handler == 0 ||
      !ReadAt(environment, handler, 0, handler_vtable) ||
      !ReadAt(environment, environment.module_base, ActivityPlannerRvaV1(environment, kPlayedCharacterId),
              played_id))
    return ActivityPlannerDiagStatusV1::native_owner_unavailable;
  if (gfx_vtable != environment.module_base + ActivityPlannerRvaV1(environment, kIdlerGfxVtable) ||
      handler_vtable != environment.module_base + ActivityPlannerRvaV1(environment, kHandlerVtable) ||
      played_id != static_cast<std::uint32_t>(frame.actor_character_id))
    return ActivityPlannerDiagStatusV1::native_identity_mismatch;

  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  const auto index = played_id & 0x00FFFFFFu;
  if (!ReadAt(environment, environment.module_base, ActivityPlannerRvaV1(environment, kCharacterStorage),
              storage) || storage == 0 ||
      !ReadAt(environment, environment.module_base, ActivityPlannerRvaV1(environment, kCharacterFallback),
              fallback) || !ReadAt(environment, storage, 0x20, slots) ||
      !ReadAt(environment, storage, 0x2C, capacity) || slots == 0 ||
      capacity <= 0 || capacity > 0x01000000 ||
      index >= static_cast<std::uint32_t>(capacity))
    return ActivityPlannerDiagStatusV1::native_owner_unavailable;
  std::uintptr_t actor_slot = 0;
  std::uintptr_t actor = 0;
  std::uint32_t actor_id = 0;
  if (!Add(slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
           actor_slot) || !ReadAt(environment, actor_slot, 0, actor) ||
      actor == 0 || actor == fallback ||
      !ReadAt(environment, actor, 0x18, actor_id) || actor_id != played_id)
    return ActivityPlannerDiagStatusV1::native_identity_mismatch;

  std::uintptr_t planner = 0;
  if (!ReadAt(environment, handler, 0x3C0, planner))
    return ActivityPlannerDiagStatusV1::native_read_failed;
  if (planner == 0)
    return ActivityPlannerDiagStatusV1::planner_absent;
  value.planner_present = true;
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::uintptr_t owner = 0;
  std::uintptr_t widget = 0;
  std::int32_t stage = -1;
  if (!ReadAt(environment, planner, 0, primary) ||
      !ReadAt(environment, planner, 0x10, secondary) ||
      !ReadAt(environment, planner, ActivityPlannerObjectOffsetV1(environment, 0xD0), owner) ||
      !ReadAt(environment, planner, ActivityPlannerObjectOffsetV1(environment, 0x78), widget) ||
      !ReadAt(environment, planner, ActivityPlannerObjectOffsetV1(environment, 0x1AB0), stage))
    return ActivityPlannerDiagStatusV1::native_read_failed;
  if (primary != environment.module_base + ActivityPlannerRvaV1(environment, kPlannerPrimaryVtable) ||
      secondary != environment.module_base + ActivityPlannerRvaV1(environment, kPlannerSecondaryVtable) ||
      owner != handler || stage < 0 || stage > 5)
    return ActivityPlannerDiagStatusV1::native_identity_mismatch;
  value.stage = stage;
  value.widget_attached = widget != 0;
  bool visible = false;
  if (!environment.invoke_visibility(
          environment.context, planner,
          environment.module_base + ActivityPlannerRvaV1(environment, kPlannerVisibilitySlotSeven), visible) ||
      (!value.widget_attached && visible))
    return ActivityPlannerDiagStatusV1::native_read_failed;
  value.widget_visible = visible;

  std::uintptr_t host = 0;
  if (!ReadAt(environment, handler, 0x3D8, host))
    return ActivityPlannerDiagStatusV1::native_read_failed;
  if (host != 0) {
    std::uintptr_t host_primary = 0;
    std::uintptr_t host_secondary = 0;
    std::uintptr_t host_owner = 0;
    std::int32_t host_actor_id = 0;
    std::uintptr_t type = 0;
    if (!ReadAt(environment, host, 0, host_primary) ||
        !ReadAt(environment, host, 0x10, host_secondary) ||
        !ReadAt(environment, host, (IsActivityPlanner12002V1(environment) ? 0xA0 : 0xD0), host_owner) ||
        !ReadAt(environment, host, (IsActivityPlanner12002V1(environment) ? 0xD0 : 0x100), host_actor_id) ||
        !ReadAt(environment, host, (IsActivityPlanner12002V1(environment) ? 0x238 : 0x268), type))
      return ActivityPlannerDiagStatusV1::native_read_failed;
    if (host_primary != environment.module_base + ActivityPlannerRvaV1(environment, kHostPrimaryVtable) ||
        host_secondary != environment.module_base + ActivityPlannerRvaV1(environment, kHostSecondaryVtable) ||
        host_owner != handler)
      return ActivityPlannerDiagStatusV1::native_identity_mismatch;
    // The HostView may exist before any player activity is selected. Its
    // previous/empty owner must never be reported as the planner's type.
    if (host_actor_id != frame.actor_character_id)
      return ActivityPlannerDiagStatusV1::observed;
    if (type != 0) {
      std::uintptr_t type_vtable = 0;
      if (!ReadAt(environment, type, 0, type_vtable) ||
          type_vtable != environment.module_base + ActivityPlannerRvaV1(environment, kActivityTypeVtable) ||
          !ReadStableKey(environment, type, value))
        return ActivityPlannerDiagStatusV1::native_identity_mismatch;
    }
  }
  return ActivityPlannerDiagStatusV1::observed;
}

} // namespace

bool ResolveActivityPlannerIdentityV1(
    const ActivityPlannerDiagEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    ActivityPlannerIdentityV1 &output) noexcept {
  output = {};
  const auto diagnostic = ReadActivityPlannerDiagV1(environment, expected);
  if (diagnostic.status != ActivityPlannerDiagStatusV1::observed ||
      !diagnostic.value.planner_present)
    return false;
  ActivityPlannerIdentityV1 candidate{};
  std::uintptr_t root = 0, idler = 0, storage = 0, slots = 0;
  if (!ReadAt(environment, environment.module_base,
              ActivityPlannerRvaV1(environment, kGlobalInterfaceRoot), root) ||
      !ReadAt(environment, root, 0x10, idler))
    return false;
  const auto gfx = environment.rtti_cast(environment.context, idler,
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerSourceType),
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerGfxType));
  const std::size_t planner_offset = 0x3C0;
  if (gfx == 0 || !ReadAt(environment, gfx, 0x88, candidate.handler) ||
      !ReadAt(environment, candidate.handler, planner_offset, candidate.planner) ||
      candidate.planner == 0 ||
      !ReadAt(environment, candidate.planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1530),
              candidate.activity_type) ||
      !ReadAt(environment, candidate.planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1AB0), candidate.stage) ||
      !ReadAt(environment, environment.module_base,
              ActivityPlannerRvaV1(environment, kCharacterStorage), storage) ||
      !ReadAt(environment, storage, 0x20, slots) || slots == 0)
    return false;
  const auto index = static_cast<std::uint32_t>(expected.actor_character_id) &
      0x00FFFFFFu;
  std::uint32_t actor_id = 0;
  if (!ReadAt(environment, slots, static_cast<std::size_t>(index) * 0x10 + 8,
              candidate.actor) || candidate.actor == 0 ||
      !ReadAt(environment, candidate.actor, 0x18, actor_id) ||
      actor_id != static_cast<std::uint32_t>(expected.actor_character_id))
    return false;
  ActivityPlannerDiagFrameV1 frame{};
  if (!environment.read_frame(environment.context, frame) || frame != expected)
    return false;
  output = candidate;
  return true;
}

ActivityPlannerDiagResultV1 ReadActivityPlannerDiagV1(
    const ActivityPlannerDiagEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityPlannerDiagResultV1 result{};
  result.frame = expected;
  if (!FrameValid(expected)) {
    result.status = ActivityPlannerDiagStatusV1::frame_unavailable;
    return result;
  }
  if (!VerifyAbi(environment)) return result;
  ActivityPlannerDiagFrameV1 before{};
  ActivityPlannerDiagFrameV1 after{};
  if (!environment.read_frame(environment.context, before)) {
    result.status = ActivityPlannerDiagStatusV1::frame_unavailable;
    return result;
  }
  if (before != expected) {
    result.status = ActivityPlannerDiagStatusV1::frame_changed;
    return result;
  }
  ActivityPlannerDiagValueV1 first{};
  ActivityPlannerDiagValueV1 second{};
  const auto first_status = ReadOne(environment, expected, first);
  const auto second_status = ReadOne(environment, expected, second);
  if (!environment.read_frame(environment.context, after) || after != expected) {
    result.status = ActivityPlannerDiagStatusV1::frame_changed;
    return result;
  }
  if (first_status != second_status || first != second) {
    result.status = ActivityPlannerDiagStatusV1::native_sample_changed;
    return result;
  }
  result.status = first_status;
  if (first_status == ActivityPlannerDiagStatusV1::observed ||
      first_status == ActivityPlannerDiagStatusV1::planner_absent)
    result.value = first;
  return result;
}

std::string_view ActivityPlannerDiagStatusKeyV1(
    ActivityPlannerDiagStatusV1 status) noexcept {
  switch (status) {
  case ActivityPlannerDiagStatusV1::observed: return "observed";
  case ActivityPlannerDiagStatusV1::planner_absent: return "planner_absent";
  case ActivityPlannerDiagStatusV1::frame_unavailable: return "frame_unavailable";
  case ActivityPlannerDiagStatusV1::frame_changed: return "frame_changed";
  case ActivityPlannerDiagStatusV1::exact_build_rejected: return "exact_build_rejected";
  case ActivityPlannerDiagStatusV1::native_owner_unavailable:
    return "native_owner_unavailable";
  case ActivityPlannerDiagStatusV1::native_identity_mismatch:
    return "native_identity_mismatch";
  case ActivityPlannerDiagStatusV1::native_read_failed: return "native_read_failed";
  case ActivityPlannerDiagStatusV1::native_sample_changed:
    return "native_sample_changed";
  }
  return "unknown";
}

} // namespace xar::bridge

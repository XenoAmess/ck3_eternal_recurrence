#include "xar_bridge/activity_feast_planner_open_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kRoot = 0x570F7B8;
constexpr std::uintptr_t kIdlerSourceType = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxType = 0x501EF50;
constexpr std::uintptr_t kHandlerVtable = 0x40AF630;
constexpr std::uintptr_t kPlannerVtable = 0x41205F0;
constexpr std::uintptr_t kTypeManager = 0x570BE98;
constexpr std::uintptr_t kInitialTypePointer = 0x57BFF28;
constexpr std::uintptr_t kTypeVtable = 0x440E308;
constexpr std::size_t kSpecialOptionCategory = 0xA88;
constexpr std::uintptr_t kTypeDescriptor = 0x4FE3DB0;
constexpr std::uintptr_t kTypeDescriptorVtable = 0x40DB298;
constexpr std::uintptr_t kTypeCopy = 0x80DCB0;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &out) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  out = base + offset;
  return true;
}

template <typename T>
bool Read(const ActivityPlannerDiagEnvironmentV1 &env,
          std::uintptr_t base, std::size_t offset, T &out) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && env.read_memory != nullptr &&
         env.read_memory(env.context, address, &out, sizeof(out));
}

template <std::size_t N>
bool Match(const ActivityPlannerDiagEnvironmentV1 &env, std::uintptr_t rva,
           const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return Read(env, env.module_base, rva, actual) && actual == expected;
}

bool VerifyOpenAbi(const ActivityFeastPlannerOpenEnvironmentV1 &environment)
    noexcept {
  const auto &env = environment.diagnostic;
  if (env.module_base == 0 || env.read_memory == nullptr ||
      env.read_frame == nullptr || env.rtti_cast == nullptr ||
      environment.dispatch == nullptr ||
      !IsActivityPlannerSupportedBuildV1(env))
    return false;
  if (IsActivityPlanner12002V1(env)) {
    std::uintptr_t descriptor_vtable = 0, descriptor_copy = 0, descriptor_move = 0;
    const auto descriptor = ActivityPlannerRvaV1(env, kTypeDescriptor);
    const auto descriptor_table = ActivityPlannerRvaV1(env, kTypeDescriptorVtable);
    const auto pointer_copy = ActivityPlannerRvaV1(env, kTypeCopy);
    // Native HostView slot 26 packages CActivityType* and sends event 0x65.
    // The new handler additionally evaluates CanDeliverPayload before queuing.
    return Match(env, 0xAF39E0,
                 std::array<std::uint8_t, 8>{0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74}) &&
           Match(env, 0xAF39FD,
                 std::array<std::uint8_t, 13>{0xE8, 0x4E, 0xFF, 0xFF, 0xFF,
                   0x33, 0xF6, 0x81, 0xFF, 0xAC, 0x00, 0x00, 0x00}) &&
           Match(env, 0x1643A17,
                 std::array<std::uint8_t, 13>{0xBA, 0x65, 0x00, 0x00, 0x00,
                   0x48, 0x8B, 0xCD, 0xE8, 0xBC, 0xFF, 0x4A, 0xFF}) &&
           Match(env, 0x1642F05,
                 std::array<std::uint8_t, 13>{0xE8, 0xF6, 0x92, 0x2B, 0xFF,
                   0x48, 0x8B, 0x78, 0x50, 0x48, 0x63, 0x48, 0x5C}) &&
           Match(env, 0x23FC85A,
                 std::array<std::uint8_t, 7>{0x48, 0x8B, 0x05, 0xDF, 0x32, 0x92, 0x03}) &&
           Read(env, env.module_base, descriptor, descriptor_vtable) &&
           Read(env, env.module_base, descriptor_table + 0x58, descriptor_copy) &&
           Read(env, env.module_base, descriptor_table + 0x60, descriptor_move) &&
           descriptor_vtable == env.module_base + descriptor_table &&
           descriptor_copy == env.module_base + pointer_copy &&
           descriptor_move == env.module_base + pointer_copy;
  }
  constexpr std::array<std::uint8_t, 8> kQueueEntry{
      0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74};
  constexpr std::array<std::uint8_t, 8> kImmediateDelivery{
      0xE8, 0x74, 0xFF, 0xFF, 0xFF, 0x81, 0xFF, 0xA3};
  constexpr std::array<std::uint8_t, 9> kRegistryLoop{
      0xE8, 0x78, 0x9A, 0x38, 0xFF, 0x4C, 0x8B, 0x70, 0x68};
  constexpr std::array<std::uint8_t, 7> kInitialTypeRead{
      0x48, 0x8B, 0x05, 0x47, 0x57, 0x62, 0x03};
  std::uintptr_t descriptor_vtable = 0;
  std::uintptr_t descriptor_copy = 0;
  std::uintptr_t descriptor_move = 0;
  return Match(env, 0xA79700, kQueueEntry) &&
         Match(env, 0xA79717, kImmediateDelivery) &&
         Match(env, 0x15046C3, kRegistryLoop) &&
         Match(env, 0x219A7DA, kInitialTypeRead) &&
         Read(env, env.module_base, kTypeDescriptor, descriptor_vtable) &&
         Read(env, env.module_base, kTypeDescriptorVtable + 0x58,
              descriptor_copy) &&
         Read(env, env.module_base, kTypeDescriptorVtable + 0x60,
              descriptor_move) &&
         descriptor_vtable == env.module_base + kTypeDescriptorVtable &&
         descriptor_copy == env.module_base + kTypeCopy &&
         descriptor_move == env.module_base + kTypeCopy;
}

bool IsFeastKey(const ActivityPlannerDiagEnvironmentV1 &env,
                std::uintptr_t type) noexcept {
  constexpr char kFeast[] = "activity_feast";
  std::uintptr_t vtable = 0;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  std::uintptr_t key = 0;
  if (!Read(env, type, 0, vtable) ||
      vtable != env.module_base + ActivityPlannerRvaV1(env, kTypeVtable) || !Add(type, 0x18, key) ||
      !Read(env, key, 0x10, size) || !Read(env, key, 0x18, capacity) ||
      size != sizeof(kFeast) - 1 || size > capacity)
    return false;
  std::uintptr_t characters = key;
  if (capacity > 15 && !Read(env, key, 0, characters)) return false;
  std::array<char, sizeof(kFeast) - 1> copied{};
  return env.read_memory(env.context, characters, copied.data(), copied.size()) &&
         std::memcmp(copied.data(), kFeast, copied.size()) == 0;
}

bool ResolveOwner(const ActivityPlannerDiagEnvironmentV1 &env,
                  std::uintptr_t &handler,
                  std::uintptr_t &planner) noexcept {
  if (IsActivityPlanner12002V1(env)) {
    ActivityPlannerDiagFrameV1 frame{};
    ActivityPlannerIdentityV1 identity{};
    if (env.read_frame == nullptr || !env.read_frame(env.context, frame) ||
        !ResolveActivityPlannerIdentityV1(env, frame, identity)) return false;
    handler = identity.handler;
    planner = identity.planner;
    return true;
  }
  std::uintptr_t root = 0;
  std::uintptr_t idler = 0;
  std::uintptr_t gfx = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t planner_vtable = 0;
  std::uintptr_t owner = 0;
  if (!Read(env, env.module_base, kRoot, root) || root == 0 ||
      !Read(env, root, 0x10, idler) || idler == 0)
    return false;
  gfx = env.rtti_cast(env.context, idler,
                      env.module_base + kIdlerSourceType,
                      env.module_base + kIdlerGfxType);
  return gfx != 0 && Read(env, gfx, 0x88, handler) && handler != 0 &&
         Read(env, handler, 0, handler_vtable) &&
         handler_vtable == env.module_base + kHandlerVtable &&
         Read(env, handler, 0x3C0, planner) && planner != 0 &&
         Read(env, planner, 0, planner_vtable) &&
         planner_vtable == env.module_base + kPlannerVtable &&
         Read(env, planner, 0xD0, owner) && owner == handler;
}

enum class TypeLookup { found, missing, ambiguous, invalid };

TypeLookup ResolveFeastType(const ActivityPlannerDiagEnvironmentV1 &env,
                            std::uintptr_t &feast) noexcept {
  std::uintptr_t manager = 0;
  std::uintptr_t types = 0;
  std::int32_t count = 0;
  if (!Read(env, env.module_base, ActivityPlannerRvaV1(env, kTypeManager), manager) || manager == 0 ||
      !Read(env, manager, IsActivityPlanner12002V1(env) ? 0x50 : 0x68, types) || types == 0 ||
      !Read(env, manager, IsActivityPlanner12002V1(env) ? 0x5C : 0x74, count) || count < 0 || count > 1024)
    return TypeLookup::invalid;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t type = 0;
    if (!Read(env, types, static_cast<std::size_t>(index) * 8, type))
      return TypeLookup::invalid;
    if (type == 0) continue;
    std::uintptr_t vtable = 0;
    if (!Read(env, type, 0, vtable)) return TypeLookup::invalid;
    if (vtable != env.module_base + ActivityPlannerRvaV1(env, kTypeVtable)) continue;
    if (IsFeastKey(env, type)) {
      if (feast != 0) return TypeLookup::ambiguous;
      feast = type;
    }
  }
  return feast != 0 ? TypeLookup::found : TypeLookup::missing;
}

bool FrameMatches(const ActivityPlannerDiagEnvironmentV1 &env,
                  const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityPlannerDiagFrameV1 current{};
  return env.read_frame != nullptr &&
         env.read_frame(env.context, current) && current == expected;
}

bool NativeOpeningStage(std::int32_t stage,
                        bool has_special_option_category) noexcept {
  return stage == 2 || (stage == 1 && has_special_option_category);
}

} // namespace

ActivityFeastPlannerOpenResultV1 OpenActivityFeastPlannerV1(
    const ActivityFeastPlannerOpenEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityFeastPlannerOpenResultV1 result{};
  const auto &env = environment.diagnostic;
  if (!VerifyOpenAbi(environment)) return result;
  result.before = ReadActivityPlannerDiagV1(env, expected);
  if (result.before.status == ActivityPlannerDiagStatusV1::frame_unavailable) {
    result.status = ActivityFeastPlannerOpenStatusV1::frame_unavailable;
    return result;
  }
  if (result.before.status == ActivityPlannerDiagStatusV1::frame_changed) {
    result.status = ActivityFeastPlannerOpenStatusV1::frame_changed;
    return result;
  }
  if (result.before.status != ActivityPlannerDiagStatusV1::observed ||
      !result.before.value.planner_present ||
      !result.before.value.widget_attached) {
    result.status = ActivityFeastPlannerOpenStatusV1::native_precondition_failed;
    return result;
  }
  std::uintptr_t handler = 0;
  std::uintptr_t planner = 0;
  std::uintptr_t selected = 0;
  std::uintptr_t initial_type = 0;
  if (!ResolveOwner(env, handler, planner) ||
      !Read(env, planner, ActivityPlannerObjectOffsetV1(env, 0x1530), selected) ||
      !Read(env, env.module_base, ActivityPlannerRvaV1(env, kInitialTypePointer), initial_type) ||
      initial_type == 0) {
    result.status = ActivityFeastPlannerOpenStatusV1::native_precondition_failed;
    return result;
  }
  std::uintptr_t feast = 0;
  switch (ResolveFeastType(env, feast)) {
  case TypeLookup::missing:
  case TypeLookup::invalid:
    result.status = ActivityFeastPlannerOpenStatusV1::type_unavailable;
    return result;
  case TypeLookup::ambiguous:
    result.status = ActivityFeastPlannerOpenStatusV1::type_ambiguous;
    return result;
  case TypeLookup::found: break;
  }
  std::uintptr_t special_option_category = 0;
  if (!Read(env, feast, ActivityPlannerTypeOffsetV1(env, kSpecialOptionCategory), special_option_category)) {
    result.status = ActivityFeastPlannerOpenStatusV1::native_precondition_failed;
    return result;
  }
  const bool has_special_option_category = special_option_category != 0;
  if (result.before.value.widget_visible && selected == feast) {
    result.after = result.before;
    result.selected_feast_verified = true;
    result.status = NativeOpeningStage(result.before.value.stage,
                                       has_special_option_category)
                        ? ActivityFeastPlannerOpenStatusV1::already_open
                        : ActivityFeastPlannerOpenStatusV1::postcondition_failed;
    return result;
  }
  if (result.before.value.widget_visible ||
      result.before.value.stage != 2 || selected != initial_type) {
    result.status = ActivityFeastPlannerOpenStatusV1::native_precondition_failed;
    return result;
  }
  if (!FrameMatches(env, expected)) {
    result.status = ActivityFeastPlannerOpenStatusV1::frame_changed;
    return result;
  }
  result.native_dispatch_invoked = true;
  if (!environment.dispatch(env.context, handler, feast)) {
    result.status = ActivityFeastPlannerOpenStatusV1::native_call_failed;
    return result;
  }
  result.after = ReadActivityPlannerDiagV1(env, expected);
  std::uintptr_t after_planner = 0;
  std::uintptr_t after_selected = 0;
  const bool selected_read =
      Read(env, handler, 0x3C0, after_planner) && after_planner == planner &&
      Read(env, planner, ActivityPlannerObjectOffsetV1(env, 0x1530), after_selected);
  result.selected_feast_verified =
      selected_read && after_selected == feast &&
      result.after.status == ActivityPlannerDiagStatusV1::observed;
  if (!FrameMatches(env, expected)) {
    result.status = ActivityFeastPlannerOpenStatusV1::frame_changed;
  } else if (!result.selected_feast_verified ||
             !result.after.value.widget_attached ||
             !result.after.value.widget_visible ||
             !NativeOpeningStage(result.after.value.stage,
                                 has_special_option_category)) {
    result.status = ActivityFeastPlannerOpenStatusV1::postcondition_failed;
  } else {
    result.status = ActivityFeastPlannerOpenStatusV1::opened;
  }
  return result;
}

const char *ActivityFeastPlannerOpenStatusKeyV1(
    ActivityFeastPlannerOpenStatusV1 status) noexcept {
  switch (status) {
  case ActivityFeastPlannerOpenStatusV1::opened: return "opened";
  case ActivityFeastPlannerOpenStatusV1::already_open: return "already_open";
  case ActivityFeastPlannerOpenStatusV1::frame_unavailable: return "frame_unavailable";
  case ActivityFeastPlannerOpenStatusV1::frame_changed: return "frame_changed";
  case ActivityFeastPlannerOpenStatusV1::exact_build_rejected: return "exact_build_rejected";
  case ActivityFeastPlannerOpenStatusV1::native_precondition_failed: return "native_precondition_failed";
  case ActivityFeastPlannerOpenStatusV1::type_unavailable: return "type_unavailable";
  case ActivityFeastPlannerOpenStatusV1::type_ambiguous: return "type_ambiguous";
  case ActivityFeastPlannerOpenStatusV1::native_call_failed: return "native_call_failed";
  case ActivityFeastPlannerOpenStatusV1::postcondition_failed: return "postcondition_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

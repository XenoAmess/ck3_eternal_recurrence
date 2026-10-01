#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kRoot = 0x570F7B8;
constexpr std::uintptr_t kPlayedId = 0x4FE7EE0;
constexpr std::uintptr_t kIdlerSourceType = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxType = 0x501EF50;
constexpr std::uintptr_t kGfxVtable = 0x40B1D30;
constexpr std::uintptr_t kHandlerVtable = 0x40AF630;
constexpr std::uintptr_t kPlannerPrimaryVtable = 0x41205F0;
constexpr std::uintptr_t kPlannerSecondaryVtable = 0x41206C8;
constexpr std::uintptr_t kActivityTypeVtable = 0x440E308;
constexpr std::uintptr_t kEvaluator = 0x10B0DA0;
constexpr std::uintptr_t kStage5Branch = 0x10B1018;

struct NativeIdentity {
  std::uintptr_t handler = 0;
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;

  friend bool operator==(const NativeIdentity &,
                         const NativeIdentity &) = default;
};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  output = base + offset;
  return true;
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && environment.read_memory != nullptr &&
         environment.read_memory(environment.context, address, &output,
                                 sizeof(output));
}

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &environment,
               std::uintptr_t rva,
               const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return ReadAt(environment, environment.module_base, rva, actual) &&
         actual == expected;
}

bool VerifyAbi(const ActivityStage5CanStartEnvironmentV1 &environment) noexcept {
  const auto &d = environment.diagnostic;
  constexpr std::array<std::uint8_t, 7> kEvaluatorSignature{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89};
  constexpr std::array<std::uint8_t, 7> kStage5Signature{
      0x48, 0x8D, 0x91, 0x30, 0x15, 0x00, 0x00};
  if (IsActivityPlanner12002V1(d))
    return d.enabled && d.module_base != 0 &&
           d.read_memory != nullptr && d.read_frame != nullptr &&
           d.rtti_cast != nullptr && d.invoke_visibility != nullptr &&
           MatchCode(d, ck3_12002::kFeastFinalCanStartRva,
                     ck3_12002::kFeastFinalCanStartPrefix) &&
           MatchCode(d, ck3_12002::kFeastFinalStage5BranchRva,
                     ck3_12002::kFeastFinalStage5Prefix);
  return d.enabled && d.module_base != 0 &&
         d.admitted_executable_sha256 == kActivityPlannerDiagExeSha256V1 &&
         d.read_memory != nullptr && d.read_frame != nullptr &&
         d.rtti_cast != nullptr && d.invoke_visibility != nullptr &&
         MatchCode(d, kEvaluator, kEvaluatorSignature) &&
         MatchCode(d, kStage5Branch, kStage5Signature);
}

bool IsFeastType(const ActivityPlannerDiagEnvironmentV1 &environment,
                 std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  std::uintptr_t vtable = 0;
  std::uint64_t size = 0, capacity = 0;
  std::uintptr_t data = type + 0x18;
  if (!ReadAt(environment, type, 0, vtable) ||
      vtable != environment.module_base +
                    ActivityPlannerRvaV1(environment, kActivityTypeVtable) ||
      !ReadAt(environment, type, 0x28, size) ||
      !ReadAt(environment, type, 0x30, capacity) || size != key.size() ||
      size > capacity)
    return false;
  if (capacity > 15 && !ReadAt(environment, type, 0x18, data)) return false;
  std::array<char, 16> observed{};
  return environment.read_memory(environment.context, data, observed.data(),
                                 key.size()) &&
         std::memcmp(observed.data(), key.data(), key.size()) == 0;
}

bool ResolveNative(const ActivityPlannerDiagEnvironmentV1 &environment,
                   const ActivityPlannerDiagFrameV1 &frame,
                   NativeIdentity &identity,
                   bool &selected_feast) noexcept {
  if (IsActivityPlanner12002V1(environment)) {
    ActivityPlannerIdentityV1 current{};
    if (!ResolveActivityPlannerIdentityV1(environment, frame, current) ||
        current.stage != 5 || current.activity_type == 0)
      return false;
    identity.handler = current.handler;
    identity.planner = current.planner;
    identity.activity_type = current.activity_type;
    selected_feast = IsFeastType(environment, identity.activity_type);
    return true;
  }
  std::uintptr_t root = 0, idler = 0, gfx_vtable = 0;
  std::uintptr_t handler_vtable = 0, primary = 0, secondary = 0, owner = 0;
  std::int32_t stage = -1;
  std::uint32_t played_id = 0;
  if (!ReadAt(environment, environment.module_base, kRoot, root) || root == 0 ||
      !ReadAt(environment, root, 0x10, idler) || idler == 0)
    return false;
  const auto gfx = environment.rtti_cast(
      environment.context, idler,
      environment.module_base + kIdlerSourceType,
      environment.module_base + kIdlerGfxType);
  if (gfx == 0 || !ReadAt(environment, gfx, 0, gfx_vtable) ||
      gfx_vtable != environment.module_base + kGfxVtable ||
      !ReadAt(environment, gfx, 0x88, identity.handler) ||
      identity.handler == 0 ||
      !ReadAt(environment, identity.handler, 0, handler_vtable) ||
      handler_vtable != environment.module_base + kHandlerVtable ||
      !ReadAt(environment, environment.module_base, kPlayedId, played_id) ||
      played_id != static_cast<std::uint32_t>(frame.actor_character_id) ||
      !ReadAt(environment, identity.handler, 0x3C0, identity.planner) ||
      identity.planner == 0 ||
      !ReadAt(environment, identity.planner, 0, primary) ||
      !ReadAt(environment, identity.planner, 0x10, secondary) ||
      !ReadAt(environment, identity.planner, 0xD0, owner) ||
      !ReadAt(environment, identity.planner, 0x1AB0, stage) ||
      !ReadAt(environment, identity.planner, 0x1530, identity.activity_type) ||
      primary != environment.module_base + kPlannerPrimaryVtable ||
      secondary != environment.module_base + kPlannerSecondaryVtable ||
      owner != identity.handler || stage != 5 || identity.activity_type == 0)
    return false;
  selected_feast = IsFeastType(environment, identity.activity_type);
  return true;
}

} // namespace

ActivityStage5CanStartResultV1 ReadActivityStage5CanStartV1(
    const ActivityStage5CanStartEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage5CanStartResultV1 result{};
  result.frame = expected;
  if (!VerifyAbi(environment)) return result;
  if (environment.evaluate == nullptr) {
    result.status = ActivityStage5CanStartStatusV1::callback_missing;
    return result;
  }
  const auto &d = environment.diagnostic;
  const auto first_diag = ReadActivityPlannerDiagV1(d, expected);
  if (first_diag.status != ActivityPlannerDiagStatusV1::observed ||
      !first_diag.value.planner_present ||
      !first_diag.value.widget_attached || !first_diag.value.widget_visible) {
    result.status = ActivityStage5CanStartStatusV1::planner_unavailable;
    return result;
  }
  if (first_diag.value.stage != 5) {
    result.status = ActivityStage5CanStartStatusV1::not_stage5;
    return result;
  }
  NativeIdentity before{};
  bool before_feast = false;
  if (!ResolveNative(d, expected, before, before_feast)) {
    result.status = ActivityStage5CanStartStatusV1::native_identity_mismatch;
    return result;
  }
  if (!before_feast) {
    result.status = ActivityStage5CanStartStatusV1::selected_type_mismatch;
    return result;
  }
  bool final_can_start = false;
  if (!environment.evaluate(d.context, before.planner, final_can_start)) {
    result.status = ActivityStage5CanStartStatusV1::native_evaluation_failed;
    return result;
  }
  NativeIdentity after{};
  bool after_feast = false;
  const auto final_diag = ReadActivityPlannerDiagV1(d, expected);
  if (!ResolveNative(d, expected, after, after_feast) ||
      !after_feast || after != before ||
      final_diag.status != ActivityPlannerDiagStatusV1::observed ||
      final_diag.value != first_diag.value || final_diag.frame != expected) {
    result.status = ActivityStage5CanStartStatusV1::frame_changed;
    return result;
  }
  result.status = ActivityStage5CanStartStatusV1::observed;
  result.final_can_start = final_can_start;
  return result;
}

std::string_view ActivityStage5CanStartStatusKeyV1(
    ActivityStage5CanStartStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage5CanStartStatusV1::observed: return "observed";
  case ActivityStage5CanStartStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage5CanStartStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage5CanStartStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityStage5CanStartStatusV1::not_stage5: return "not_stage5";
  case ActivityStage5CanStartStatusV1::selected_type_mismatch:
    return "selected_type_mismatch";
  case ActivityStage5CanStartStatusV1::native_identity_mismatch:
    return "native_identity_mismatch";
  case ActivityStage5CanStartStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityStage5CanStartStatusV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

} // namespace xar::bridge

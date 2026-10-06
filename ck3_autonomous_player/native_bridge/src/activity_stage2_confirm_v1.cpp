#include "xar_bridge/activity_stage2_confirm_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_CONFIRM_PRIVATE_V1)
constexpr std::uintptr_t kRootRva = 0x570F7B8;
constexpr std::uintptr_t kPlayedIdRva = 0x4FE7EE0;
constexpr std::uintptr_t kIdlerSourceTypeRva = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxTypeRva = 0x501EF50;
constexpr std::uintptr_t kGfxVtableRva = 0x40B1D30;
constexpr std::uintptr_t kHandlerVtableRva = 0x40AF630;
constexpr std::uintptr_t kPlannerVtableRva = 0x41205F0;
constexpr std::uintptr_t kActivityTypeVtableRva = 0x440E308;
constexpr std::uintptr_t kOptionVtableRva = 0x440E1D0;
constexpr std::uintptr_t kCanProgressRva = 0x10B0DA0;
constexpr std::uintptr_t kStageTwoGateRva = 0x10B0E0F;
constexpr std::uintptr_t kStageTwoBranchRva = 0x10B13B3;
constexpr std::uintptr_t kSetStageRva = 0x10B1BD0;

struct NativeSelection {
  std::uintptr_t planner = 0;
  std::uintptr_t type = 0;
  std::uintptr_t option = 0;
  std::int32_t option_id = -1;
};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &address) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

template <typename T>
bool Read(const ActivityPlannerDiagEnvironmentV1 &d, std::uintptr_t base,
          std::size_t offset, T &out) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) && d.read_memory != nullptr &&
         d.read_memory(d.context, address, &out, sizeof(out));
}

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &d,
               std::uintptr_t rva,
               const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return Read(d, d.module_base,
              Activity12004RvaV1(d.admitted_executable_sha256, rva), actual) && actual == expected;
}

bool VerifyActionAbi(const ActivityPlannerDiagEnvironmentV1 &d) noexcept {
  constexpr std::array<std::uint8_t, 7> kCanProgress{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89};
  constexpr std::array<std::uint8_t, 7> kStageTwoGate{
      0x48, 0x8B, 0x89, 0x78, 0x15, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 5> kStageTwoBranch{
      0xBA, 0x05, 0x00, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 10> kSetter{
      0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x8B, 0x81, 0xB0, 0x1A};
  constexpr std::array<std::uint8_t, 7> kStageTwoGate12002{
      0x48, 0x8B, 0x89, 0xB0, 0x15, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 15> kSetter12002{
      0x40, 0x53, 0x48, 0x81, 0xEC, 0xA0, 0x00, 0x00, 0x00,
      0x8B, 0x81, 0xE8, 0x1A, 0x00, 0x00};
  const bool current = IsActivityPlannerCrozierBuildV1(d);
  std::uintptr_t stage_notification = 0;
  return d.enabled && d.module_base != 0 &&
         (d.admitted_executable_sha256 == kActivityPlannerDiagExeSha256V1 || current) &&
         MatchCode(d, current ? 0x11B8670 : kCanProgressRva, kCanProgress) &&
         MatchCode(d, current ? 0x11B86DF : kStageTwoGateRva,
                   current ? kStageTwoGate12002 : kStageTwoGate) &&
         MatchCode(d, current ? 0x11B8D53 : kStageTwoBranchRva, kStageTwoBranch) &&
         (current ? MatchCode(d, 0x11B95D0, kSetter12002)
                  : MatchCode(d, kSetStageRva, kSetter)) &&
         Read(d, d.module_base, ActivityPlannerRvaV1(d, kPlannerVtableRva) + 0xC8,
              stage_notification) &&
         stage_notification == d.module_base + ActivityPlannerRvaV1(d, 0x10AEC20);
}

bool IsFeastType(const ActivityPlannerDiagEnvironmentV1 &d,
                 std::uintptr_t type) noexcept {
  constexpr std::string_view key = "activity_feast";
  std::uintptr_t vtable = 0;
  std::uint64_t size = 0, capacity = 0;
  std::uintptr_t bytes = type + 0x18;
  if (!Read(d, type, 0, vtable) ||
      vtable != d.module_base + ActivityPlannerRvaV1(d, kActivityTypeVtableRva) ||
      !Read(d, type, 0x28, size) || !Read(d, type, 0x30, capacity) ||
      size != key.size() || size > capacity)
    return false;
  if (capacity > 15 && !Read(d, type, 0x18, bytes)) return false;
  std::array<char, 16> actual{};
  return d.read_memory(d.context, bytes, actual.data(), key.size()) &&
         std::memcmp(actual.data(), key.data(), key.size()) == 0;
}

bool ResolveSelection(const ActivityStage1OptionEnvironmentV1 &env,
                      const ActivityPlannerDiagFrameV1 &expected,
                      std::int32_t required_stage,
                      NativeSelection &out) noexcept {
  const auto &d = env.diagnostic;
  if (IsActivityPlannerCrozierBuildV1(d)) {
    ActivityPlannerIdentityV1 identity{};
    std::uintptr_t option_vtable = 0;
    if (!ResolveActivityPlannerIdentityV1(d, expected, identity) ||
        identity.stage != required_stage ||
        !IsFeastType(d, identity.activity_type) ||
        env.selected_option == nullptr ||
        !env.selected_option(d.context, identity.planner, out.option) ||
        out.option == 0 ||
        !Read(d, out.option, 0, option_vtable) ||
        option_vtable != d.module_base + ActivityPlannerRvaV1(d, kOptionVtableRva) ||
        !Read(d, out.option, 8, out.option_id) || out.option_id < 0)
      return false;
    out.planner = identity.planner;
    out.type = identity.activity_type;
    return true;
  }
  std::uintptr_t root = 0, idler = 0, gfx = 0, handler = 0;
  std::uintptr_t vtable = 0, owner = 0, category = 0, rows = 0;
  std::uintptr_t selected_row = 0, matching_row = 0;
  std::int32_t stage = -1, count = 0;
  std::uint32_t played_id = 0;
  if (!Read(d, d.module_base, ActivityPlannerRvaV1(d, kRootRva), root) || root == 0 ||
      !Read(d, root, 0x10, idler) || idler == 0)
    return false;
  gfx = d.rtti_cast(d.context, idler,
                    d.module_base + ActivityPlannerRvaV1(d, kIdlerSourceTypeRva),
                    d.module_base + ActivityPlannerRvaV1(d, kIdlerGfxTypeRva));
  if (gfx == 0 || !Read(d, gfx, 0, vtable) ||
      vtable != d.module_base + ActivityPlannerRvaV1(d, kGfxVtableRva) ||
      !Read(d, gfx, 0x88, handler) || handler == 0 ||
      !Read(d, handler, 0, vtable) ||
      vtable != d.module_base + ActivityPlannerRvaV1(d, kHandlerVtableRva) ||
      !Read(d, d.module_base, ActivityPlannerRvaV1(d, kPlayedIdRva), played_id) ||
      played_id != static_cast<std::uint32_t>(expected.actor_character_id) ||
      !Read(d, handler, 0x3C0, out.planner) || out.planner == 0 ||
      !Read(d, out.planner, 0, vtable) ||
      vtable != d.module_base + ActivityPlannerRvaV1(d, kPlannerVtableRva) ||
      !Read(d, out.planner, 0xD0, owner) || owner != handler ||
      !Read(d, out.planner, ActivityPlannerObjectOffsetV1(d, 0x1AB0), stage) || stage != required_stage ||
      !Read(d, out.planner, ActivityPlannerObjectOffsetV1(d, 0x1530), out.type) || out.type == 0 ||
      !IsFeastType(d, out.type) ||
      !Read(d, out.type, ActivityPlannerTypeOffsetV1(d, 0xA88), category) || category == 0 ||
      !Read(d, out.planner, ActivityPlannerObjectOffsetV1(d, 0x1560), rows) || rows == 0 ||
      !Read(d, out.planner, ActivityPlannerObjectOffsetV1(d, 0x156C), count) || count <= 0 || count > 128 ||
      !Read(d, out.planner, ActivityPlannerObjectOffsetV1(d, 0x1AC8), selected_row) || selected_row != 0)
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t row = 0, row_category = 0;
    if (!Add(rows, static_cast<std::size_t>(index) * 0x10, row) ||
        !Read(d, row, 0, row_category))
      return false;
    if (row_category == category) {
      if (matching_row != 0) return false;
      matching_row = row;
    }
  }
  if (matching_row == 0 ||
      !Read(d, matching_row, 0x08, out.option) || out.option == 0 ||
      !Read(d, out.option, 0, vtable) ||
      vtable != d.module_base + ActivityPlannerRvaV1(d, kOptionVtableRva) ||
      !Read(d, out.option, 0x08, out.option_id))
    return false;
  std::uintptr_t native_getter_option = 0;
  return env.selected_option(d.context, out.planner,
                             native_getter_option) &&
         native_getter_option == out.option;
}

bool SameSelection(const NativeSelection &a,
                   const NativeSelection &b) noexcept {
  return a.planner == b.planner && a.type == b.type &&
         a.option == b.option && a.option_id == b.option_id;
}

#endif
} // namespace

ActivityStage2ConfirmResultV1 ConfirmActivityStage2V1(
    const ActivityStage2ConfirmEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
#if !defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_CONFIRM_PRIVATE_V1)
  (void)environment;
  (void)expected;
  return {};
#else
  ActivityStage2ConfirmResultV1 result{};
  const ActivityPlannerDiagFrameV1 frozen_expected = expected;
  const auto &env = environment.option;
  const auto &d = env.diagnostic;
  result.precondition = ReadActivityStage2OptionV1(env, frozen_expected);
  if (result.precondition.status !=
          ActivityStage2OptionReadStatusV1::observed ||
      !result.precondition.generic_feast_selected ||
      env.can_progress == nullptr || env.selected_option == nullptr ||
      environment.set_stage_five == nullptr ||
      environment.read_gold_raw == nullptr || !VerifyActionAbi(d))
    return result;

  NativeSelection first{};
  std::uint8_t stage_auto = 1;
  std::int64_t gold_before = 0;
  if (!ResolveSelection(env, frozen_expected, 2, first) ||
      !Read(d, first.planner, ActivityPlannerObjectOffsetV1(d, 0x1AD0), stage_auto) || stage_auto != 0 ||
      !env.can_progress(d.context, first.planner,
                        result.can_progress_stage_two) ||
      !result.can_progress_stage_two ||
      !environment.read_gold_raw(d.context, gold_before))
    return result;

  NativeSelection immediate_selection{};
  ActivityPlannerDiagFrameV1 immediate_frame{};
  std::int64_t immediate_gold = 0;
  if (!ResolveSelection(env, frozen_expected, 2, immediate_selection) ||
      !SameSelection(first, immediate_selection) ||
      !d.read_frame(d.context, immediate_frame) ||
      immediate_frame != frozen_expected ||
      !environment.read_gold_raw(d.context, immediate_gold) ||
      immediate_gold != gold_before)
    return result;

  result.submitted = true;
  if (!environment.set_stage_five(d.context, first.planner)) {
    result.status = ActivityStage2ConfirmStatusV1::native_transition_failed;
    return result;
  }

  const auto post = ReadActivityPlannerDiagV1(d, frozen_expected);
  result.stage_five_visible =
      post.status == ActivityPlannerDiagStatusV1::observed &&
      post.value.widget_attached && post.value.widget_visible &&
      post.value.stage == 5;
  NativeSelection second{};
  result.selected_option_retained =
      result.stage_five_visible &&
      ResolveSelection(env, frozen_expected, 5, second) &&
      SameSelection(first, second);
  std::int64_t gold_after = 0;
  result.gold_unchanged =
      environment.read_gold_raw(d.context, gold_after) &&
      gold_after == gold_before;
  ActivityPlannerDiagFrameV1 final_frame{};
  result.frame_unchanged =
      d.read_frame(d.context, final_frame) &&
      final_frame == frozen_expected;
  result.status = result.selected_option_retained && result.gold_unchanged &&
                          result.frame_unchanged
                      ? ActivityStage2ConfirmStatusV1::stage_five_verified
                      : ActivityStage2ConfirmStatusV1::postcondition_failed;
  return result;
#endif
}

std::string_view ActivityStage2ConfirmStatusKeyV1(
    ActivityStage2ConfirmStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage2ConfirmStatusV1::stage_five_verified:
    return "stage_five_verified";
  case ActivityStage2ConfirmStatusV1::precondition_rejected:
    return "precondition_rejected";
  case ActivityStage2ConfirmStatusV1::native_transition_failed:
    return "native_transition_failed";
  case ActivityStage2ConfirmStatusV1::postcondition_failed:
    return "postcondition_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

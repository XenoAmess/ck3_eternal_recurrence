#include "xar_bridge/activity_stage2_destination_select_v1.hpp"

#include <limits>

namespace xar::bridge {
namespace {

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
constexpr std::uintptr_t kCanSelectRva = 0x10AF6A0;
constexpr std::uintptr_t kSelectRva = 0x10AF3D0;
constexpr std::uintptr_t kProvinceIdWriteRva = 0x10AF407;
constexpr std::uintptr_t kSingleLocationBranchRva = 0x10AF423;
constexpr std::uintptr_t kPreviousStageBranchRva = 0x10AF430;
constexpr std::uintptr_t kStageFiveBranchRva = 0x10AF4A1;
constexpr std::size_t kConfigurationRowStride = 0x38;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &address) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &diagnostic,
               std::uintptr_t rva,
               const std::array<std::uint8_t, N> &expected) noexcept {
  std::uintptr_t address = 0;
  std::array<std::uint8_t, N> actual{};
  return diagnostic.read_memory != nullptr &&
         Add(diagnostic.module_base, rva, address) &&
         diagnostic.read_memory(diagnostic.context, address, actual.data(),
                                actual.size()) &&
         actual == expected;
}

bool ExactActionAbi(const ActivityPlannerDiagEnvironmentV1 &diagnostic)
    noexcept {
  constexpr std::array<std::uint8_t, 8> kCanSelect{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x55, 0x56, 0x57};
  constexpr std::array<std::uint8_t, 9> kSelect{
      0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24};
  constexpr std::array<std::uint8_t, 6> kProvinceIdWrite{
      0x8B, 0x42, 0x10, 0x89, 0x41, 0x08};
  constexpr std::array<std::uint8_t, 7> kSingleLocationBranch{
      0x40, 0x38, 0xBD, 0x75, 0x3C, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 6> kPreviousStageBranch{
      0x8B, 0x8B, 0xB4, 0x1A, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 8> kStageFiveBranch{
      0xBA, 0x05, 0x00, 0x00, 0x00, 0x48, 0x8B, 0xCB};
  return diagnostic.enabled && diagnostic.module_base != 0 &&
         diagnostic.admitted_executable_sha256 ==
             kActivityPlannerDiagExeSha256V1 &&
         MatchCode(diagnostic, kCanSelectRva, kCanSelect) &&
         MatchCode(diagnostic, kSelectRva, kSelect) &&
         MatchCode(diagnostic, kProvinceIdWriteRva, kProvinceIdWrite) &&
         MatchCode(diagnostic, kSingleLocationBranchRva,
                   kSingleLocationBranch) &&
         MatchCode(diagnostic, kPreviousStageBranchRva,
                   kPreviousStageBranch) &&
         MatchCode(diagnostic, kStageFiveBranchRva, kStageFiveBranch);
}

bool ReadProvinceId(const ActivityPlannerDiagEnvironmentV1 &diagnostic,
                    std::uintptr_t province,
                    std::uint32_t &province_id) noexcept {
  std::uintptr_t address = 0;
  return diagnostic.read_memory != nullptr &&
         Add(province, 0x10, address) &&
         diagnostic.read_memory(diagnostic.context, address, &province_id,
                                sizeof(province_id));
}

bool SameFrame(const ActivityPlannerDiagFrameV1 &current,
               const ActivityPlannerDiagFrameV1 &expected) noexcept {
  return current == expected && expected.actor_character_id > 0 &&
         expected.application_main_thread && expected.paused &&
         expected.map_ready && expected.actor_alive;
}

bool ReadyState(const ActivityStage2DestinationStateV1 &state,
                const ActivityPlannerDiagFrameV1 &expected,
                std::size_t &active_index) noexcept {
  if (!SameFrame(state.frame, expected) || state.planner == 0 ||
      state.activity_type == 0 || state.selected_option == 0 ||
      state.selected_option_id < 0 || !state.activity_feast ||
      !state.generic_feast_option || state.activity_started ||
      state.stage != 2 || state.previous_stage != 1 ||
      state.single_location_flag != 1 || state.configuration_rows == 0 ||
      state.configuration_row_count != 2 || state.active_row == 0 ||
      state.province_ids[0] != 0 || state.province_ids[1] != 0)
    return false;
  for (std::size_t index = 0; index < state.province_ids.size(); ++index) {
    std::uintptr_t row = 0;
    if (Add(state.configuration_rows, index * kConfigurationRowStride, row) &&
        row == state.active_row) {
      active_index = index;
      return true;
    }
  }
  return false;
}

#endif
} // namespace

ActivityStage2DestinationResultV1 SelectActivityStage2DestinationV1(
    const ActivityStage2DestinationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::uint32_t province_id) noexcept {
  ActivityStage2DestinationResultV1 result{};
#if !defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
  (void)environment;
  (void)expected;
  (void)province_id;
  return result;
#else
  const auto &diagnostic = environment.diagnostic;
  const ActivityPlannerDiagFrameV1 frozen_expected = expected;
  if (!ExactActionAbi(diagnostic)) return result;
  if (environment.read_state == nullptr ||
      environment.resolve_province == nullptr ||
      environment.can_select == nullptr || environment.select_once == nullptr) {
    result.status = ActivityStage2DestinationStatusV1::callback_missing;
    return result;
  }
  result.status = ActivityStage2DestinationStatusV1::precondition_rejected;
  if (province_id == 0) return result;

  ActivityStage2DestinationStateV1 first{};
  std::size_t active_index = 0;
  if (!environment.read_state(diagnostic.context, first) ||
      !ReadyState(first, frozen_expected, active_index))
    return result;

  std::uintptr_t province = 0;
  std::uint32_t resolved_id = 0;
  bool native_eligible = false;
  if (!environment.resolve_province(diagnostic.context, province_id,
                                    province) ||
      province == 0 ||
      !ReadProvinceId(diagnostic, province, resolved_id) ||
      resolved_id != province_id ||
      !environment.can_select(diagnostic.context, first.planner, province,
                              native_eligible) ||
      !native_eligible)
    return result;

  // The native predicate and resolver may inspect changing UI state. Re-read
  // the entire state and pointer identity immediately before the sole call.
  ActivityStage2DestinationStateV1 immediate{};
  std::uintptr_t immediate_province = 0;
  std::uint32_t immediate_id = 0;
  if (!environment.read_state(diagnostic.context, immediate) ||
      immediate != first ||
      !environment.resolve_province(diagnostic.context, province_id,
                                    immediate_province) ||
      immediate_province != province ||
      !ReadProvinceId(diagnostic, immediate_province, immediate_id) ||
      immediate_id != province_id)
    return result;

  result.submitted = true;
  result.needs_recovery = true;
  if (!environment.select_once(diagnostic.context, first.planner, province)) {
    result.status = ActivityStage2DestinationStatusV1::native_call_failed;
    return result;
  }

  ActivityStage2DestinationStateV1 post{};
  if (!environment.read_state(diagnostic.context, post)) {
    result.status = ActivityStage2DestinationStatusV1::postcondition_failed;
    return result;
  }
  result.frame_unchanged = SameFrame(post.frame, frozen_expected);
  result.stage_five_visible = post.stage == 5 &&
                              post.planner == first.planner &&
                              post.activity_type == first.activity_type &&
                              post.activity_feast;
  result.rows_filled = post.configuration_row_count == 2 &&
                       post.configuration_rows != 0 &&
                       post.province_ids[0] != 0 &&
                       post.province_ids[1] != 0 &&
                       post.province_ids[active_index] == province_id;
  result.selected_option_retained =
      post.generic_feast_option &&
      post.selected_option == first.selected_option &&
      post.selected_option_id == first.selected_option_id;
  result.gold_unchanged = post.gold_raw == first.gold_raw;
  result.no_activity_started = !post.activity_started;
  if (result.frame_unchanged && result.stage_five_visible &&
      result.rows_filled && result.selected_option_retained &&
      result.gold_unchanged && result.no_activity_started) {
    result.status = ActivityStage2DestinationStatusV1::verified_stage_five;
    result.needs_recovery = false;
  } else {
    result.status = ActivityStage2DestinationStatusV1::postcondition_failed;
  }
  return result;
#endif
}

std::string_view ActivityStage2DestinationStatusKeyV1(
    ActivityStage2DestinationStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage2DestinationStatusV1::verified_stage_five:
    return "verified_stage_five";
  case ActivityStage2DestinationStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage2DestinationStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage2DestinationStatusV1::precondition_rejected:
    return "precondition_rejected";
  case ActivityStage2DestinationStatusV1::native_call_failed:
    return "native_call_failed";
  case ActivityStage2DestinationStatusV1::postcondition_failed:
    return "postcondition_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

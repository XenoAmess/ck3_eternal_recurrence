#include "xar_bridge/activity_pilgrimage_destination_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <limits>

namespace xar::bridge {
namespace {

template <std::size_t N>
bool MatchCode(const ActivityPlannerDiagEnvironmentV1 &env,
               std::uintptr_t old12002_rva,
               const std::array<std::uint8_t, N> &expected) noexcept {
  const auto rva = Activity12004RvaV1(env.admitted_executable_sha256, old12002_rva);
  std::array<std::uint8_t, N> actual{};
  return rva != 0 && env.module_base != 0 && env.read_memory != nullptr &&
         rva <= (std::numeric_limits<std::uintptr_t>::max)() - env.module_base &&
         env.read_memory(env.context, env.module_base + rva, actual.data(), N) &&
         actual == expected;
}

// Operands/signatures copied from current exact destination helper and finite
// .4 mapper. No new RVA or arbitrary callback target is admitted.
bool ExactAbi(const ActivityPlannerDiagEnvironmentV1 &env) noexcept {
  return env.enabled && IsActivity12004BuildV1(env.admitted_executable_sha256) &&
      MatchCode(env, 0x11B6F50, std::array<std::uint8_t, 8>{
          0x48, 0x89, 0x5C, 0x24, 0x10, 0x55, 0x56, 0x57}) &&
      MatchCode(env, 0x11B6C80, std::array<std::uint8_t, 9>{
          0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24}) &&
      MatchCode(env, 0x11B6CB7, std::array<std::uint8_t, 6>{
          0x8B, 0x42, 0x10, 0x89, 0x41, 0x08}) &&
      MatchCode(env, 0x11B6CD3, std::array<std::uint8_t, 7>{
          0x40, 0x38, 0xBD, 0xED, 0x3B, 0x00, 0x00}) &&
      MatchCode(env, 0x11B6CE0, std::array<std::uint8_t, 6>{
          0x8B, 0x8B, 0xEC, 0x1A, 0x00, 0x00}) &&
      MatchCode(env, 0x11B6D51, std::array<std::uint8_t, 8>{
          0xBA, 0x05, 0x00, 0x00, 0x00, 0x48, 0x8B, 0xCB});
}

bool SameFrame(const ActivityPlannerDiagFrameV1 &current,
               const ActivityPlannerDiagFrameV1 &expected) noexcept {
  return current == expected && expected.revision != 0 &&
      expected.actor_character_id > 0 && expected.application_main_thread &&
      expected.paused && expected.map_ready && expected.actor_alive;
}

bool Ready(const ActivityPilgrimageDestinationStateV1 &state,
           const ActivityPlannerDiagFrameV1 &expected) noexcept {
  return SameFrame(state.frame, expected) && state.stage == 2 &&
      state.previous_stage == 1 && state.single_location_flag == 1 &&
      state.configuration_rows != 0 &&
      state.configuration_row_count ==
          kOrdinaryPilgrimagePiousContractV1.predefined_phase_count &&
      state.active_row == state.configuration_rows && state.phase != 0 &&
      state.phase_auto_raw == 1 && state.province_id == 0 &&
      MatchesActivityTypedPlannerSelectionV1(
          state.selection, expected, state.planner, state.activity_type, 2,
          kOrdinaryPilgrimagePiousContractV1);
}

bool Resolve(const ActivityPilgrimageDestinationEnvironmentV1 &env,
             std::uint32_t id, std::uintptr_t &province) noexcept {
  std::uint32_t actual_id = 0;
  return id > 0 && id <= 0x7FFFFFFFU &&
      env.resolve_province(env.diagnostic.context, id, province) && province != 0 &&
      province <= (std::numeric_limits<std::uintptr_t>::max)() - 0x10 &&
      env.diagnostic.read_memory(env.diagnostic.context, province + 0x10,
                                 &actual_id, sizeof(actual_id)) && actual_id == id;
}

bool Prepare(const ActivityPilgrimageDestinationEnvironmentV1 &env,
             const ActivityPlannerDiagFrameV1 &expected, std::uint32_t id,
             ActivityPilgrimageDestinationResultV1 &result,
             std::uintptr_t &province) noexcept {
  if (!ExactAbi(env.diagnostic)) return false;
  if (env.read_state == nullptr || env.resolve_province == nullptr ||
      env.can_select == nullptr) {
    result.status = ActivityPilgrimageDestinationStatusV1::callback_missing;
    return false;
  }
  result.status = ActivityPilgrimageDestinationStatusV1::precondition_rejected;
  if (!env.read_state(env.diagnostic.context, result.before) ||
      !Ready(result.before, expected) || !Resolve(env, id, province) ||
      !env.can_select(env.diagnostic.context, result.before.planner, province,
                       result.can_select))
    return false;
  result.can_select_observed = true;
  ActivityPilgrimageDestinationStateV1 immediate{};
  std::uintptr_t next_province = 0;
  if (!env.read_state(env.diagnostic.context, immediate) ||
      immediate != result.before || !Resolve(env, id, next_province) ||
      next_province != province)
    return false;
  result.after = immediate;
  result.planning_stage_after = immediate.stage;
  return true;
}

} // namespace

ActivityPilgrimageDestinationResultV1 ReadActivityPilgrimageDestinationCanSelectV1(
    const ActivityPilgrimageDestinationEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected, std::uint32_t id) noexcept {
  ActivityPilgrimageDestinationResultV1 result{};
  const auto frozen_expected = expected;
  std::uintptr_t province = 0;
  if (Prepare(env, frozen_expected, id, result, province))
    result.status = ActivityPilgrimageDestinationStatusV1::can_select_observed;
  return result;
}

ActivityPilgrimageDestinationResultV1 SelectActivityPilgrimageDestinationV1(
    const ActivityPilgrimageDestinationEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected, std::uint32_t id) noexcept {
  ActivityPilgrimageDestinationResultV1 result{};
#if !defined(XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1)
  (void)env; (void)expected; (void)id;
  return result;
#else
  const auto frozen_expected = expected;
  std::uintptr_t province = 0;
  if (!Prepare(env, frozen_expected, id, result, province)) return result;
  if (!result.can_select) return result;
  if (env.select_once == nullptr) {
    result.status = ActivityPilgrimageDestinationStatusV1::callback_missing;
    return result;
  }
  result.submitted = true;
  result.needs_recovery = true;
  if (!env.select_once(env.diagnostic.context, result.before.planner, province)) {
    result.status = ActivityPilgrimageDestinationStatusV1::native_call_failed;
    return result;
  }
  if (!env.read_state(env.diagnostic.context, result.after)) {
    result.status = ActivityPilgrimageDestinationStatusV1::postcondition_failed;
    return result;
  }
  const auto &before = result.before;
  const auto &after = result.after;
  result.frame_unchanged = SameFrame(after.frame, frozen_expected);
  result.planning_stage_after = after.stage;
  result.row_filled = after.configuration_row_count == 1 &&
      after.configuration_rows == before.configuration_rows &&
      after.phase == before.phase && after.province_id == id &&
      after.single_location_flag == 1;
  result.selected_option_retained = after.planner == before.planner &&
      after.activity_type == before.activity_type && after.stage >= 2 && after.stage <= 5 &&
      MatchesActivityTypedPlannerSelectionV1(
          after.selection, frozen_expected, after.planner, after.activity_type, after.stage,
          kOrdinaryPilgrimagePiousContractV1) &&
      after.selection.native_selected_option == before.selection.native_selected_option &&
      after.selection.native_option_id == before.selection.native_option_id;
  result.gold_unchanged = after.gold_raw == before.gold_raw;
  if (result.frame_unchanged && result.row_filled &&
      result.selected_option_retained && result.gold_unchanged) {
    result.status = ActivityPilgrimageDestinationStatusV1::selection_verified;
    result.needs_recovery = false;
  } else {
    result.status = ActivityPilgrimageDestinationStatusV1::postcondition_failed;
  }
  return result;
#endif
}

} // namespace xar::bridge

#pragma once

#include "xar_bridge/activity_planning_snapshot_v1_private_observer.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityPlanningSourceAdapterPrivateKeyV1 =
    "activity_planning_snapshot_v1_source_adapter";
inline constexpr std::string_view
    kActivityPlanningSourceAdapterExecutableSha256V1 =
        kActivityPlanningSnapshotExecutableSha256V1;

inline constexpr std::uintptr_t kActivityPlanningHostViewPrimaryVtableRvaV1 =
    0x4166528;
inline constexpr std::uintptr_t kActivityPlanningHostViewCanPlanRvaV1 =
    0x15051F0;
inline constexpr std::size_t kActivityPlanningHostViewCanPlanVtableSlotV1 = 25;
inline constexpr std::size_t kActivityPlanningHostViewActivityTypeOffsetV1 =
    0x268;

enum class ActivityPlanningSourceAdapterFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  callbacks_missing,
  request_invalid,
  session_busy,
  frame_unavailable,
  frame_mismatch,
  host_view_unavailable,
  host_view_identity_mismatch,
  activity_type_unavailable,
  activity_key_unavailable,
  activity_key_mismatch,
  final_can_plan_failed,
  source_container_unavailable,
  source_container_invalid,
  source_container_drift,
  source_row_unavailable,
  source_text_unavailable,
  source_sample_drift,
  source_container_release_failed,
};

struct ActivityPlanningSourceStringRefV1 {
  std::uintptr_t data = 0;
  std::uint32_t size = 0;

  friend bool operator==(const ActivityPlanningSourceStringRefV1 &,
                         const ActivityPlanningSourceStringRefV1 &) = default;
};

struct ActivityPlanningSourceLocationRowV1 {
  std::int64_t location_id = 0;
  ActivityPlanningSourceStringRefV1 location_key{};
  std::int64_t native_weight_q100000 = 0;
  std::uint8_t selectable = 0;
};

struct ActivityPlanningSourceCostRowV1 {
  ActivityPlanningSourceStringRefV1 resource_key{};
  std::int64_t amount_q100000 = 0;
};

struct ActivityPlanningSourceOptionRowV1 {
  ActivityPlanningSourceStringRefV1 option_key{};
};

struct ActivityPlanningSourceContainerViewV1 {
  std::uintptr_t location_rows = 0;
  std::uint32_t location_count = 0;
  std::uintptr_t configured_cost_rows = 0;
  std::uint32_t configured_cost_count = 0;
  std::uintptr_t selected_option_rows = 0;
  std::uint32_t selected_option_count = 0;
  ActivityPlanningSourceStringRefV1 host_intent_key{};
  ActivityPlanningSourceStringRefV1 guest_intent_key{};
  ActivityPlanningSourceStringRefV1 invite_rule_key{};
  std::uint8_t shown = 0;
  std::uint8_t can_start = 0;
  std::uint8_t affordable = 0;
  std::uint8_t cooldown_active = 0;
  std::int64_t cooldown_days_remaining = 0;

  friend bool
  operator==(const ActivityPlanningSourceContainerViewV1 &,
             const ActivityPlanningSourceContainerViewV1 &) = default;
};

struct ActivityPlanningSourceCanPlanResultV1 {
  std::uint8_t value = 0;
  ActivityPlanningSourceStringRefV1 failure_display_key{};
  ActivityPlanningSourceStringRefV1 failure_display_text{};
};

using ActivityPlanningSourceMemoryReadV1 = bool (*)(void *context,
                                                    std::uintptr_t address,
                                                    void *output,
                                                    std::size_t size) noexcept;
using ActivityPlanningResolveHostViewV1 =
    bool (*)(void *context, std::int32_t owner_character_id,
             std::string_view activity_key, std::uintptr_t &host_view) noexcept;
using ActivityPlanningReadDefinitionKeyV1 =
    bool (*)(void *context, std::uintptr_t activity_type,
             ActivityPlanningSourceStringRefV1 &key) noexcept;
using ActivityPlanningInvokeFinalCanPlanV1 = bool (*)(
    void *context, std::uintptr_t exact_entry_point, std::uintptr_t host_view,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningSourceCanPlanResultV1 &output) noexcept;
using ActivityPlanningOpenSourceContainerV1 = bool (*)(
    void *context, std::uintptr_t host_view, std::uintptr_t activity_type,
    const ActivityPlanningSnapshotRequestV1 &request,
    std::uintptr_t &container_token) noexcept;
using ActivityPlanningReadSourceContainerV1 =
    bool (*)(void *context, std::uintptr_t container_token,
             ActivityPlanningSourceContainerViewV1 &output) noexcept;
using ActivityPlanningReleaseSourceContainerV1 =
    bool (*)(void *context, std::uintptr_t container_token) noexcept;

struct ActivityPlanningSourceAdapterEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityPlanningReadFrameV1 read_frame = nullptr;
  ActivityPlanningSourceMemoryReadV1 read_memory = nullptr;
  ActivityPlanningResolveHostViewV1 resolve_host_view = nullptr;
  ActivityPlanningReadDefinitionKeyV1 read_definition_key = nullptr;
  ActivityPlanningInvokeFinalCanPlanV1 invoke_final_can_plan = nullptr;
  ActivityPlanningOpenSourceContainerV1 open_source_container = nullptr;
  ActivityPlanningReadSourceContainerV1 read_source_container = nullptr;
  ActivityPlanningReleaseSourceContainerV1 release_source_container = nullptr;
};

struct ActivityPlanningSourceAdapterOwnedSampleV1 {
  ActivityPlanningStableKeyV1 activity_key{};
  ActivityPlanningTypedBoolV1 shown{};
  ActivityPlanningTypedBoolV1 can_plan_final{};
  ActivityPlanningTypedBoolV1 can_start{};
  ActivityPlanningTypedStableKeyV1 failure_display_key{};
  ActivityPlanningTypedDisplayTextV1 failure_display_text{};
  std::array<ActivityPlanningCandidateV1, kActivityPlanningMaximumCandidatesV1>
      candidates{};
  std::uint16_t candidate_count = 0;
  std::array<ActivityPlanningStableKeyV1,
             kActivityPlanningMaximumSelectedOptionsV1>
      selected_options{};
  std::uint16_t selected_option_count = 0;
  ActivityPlanningStableKeyV1 host_intent_key{};
  ActivityPlanningStableKeyV1 guest_intent_key{};
  ActivityPlanningStableKeyV1 invite_rule_key{};
  std::array<ActivityPlanningConfiguredCostV1,
             kActivityPlanningMaximumConfiguredCostsV1>
      configured_costs{};
  std::uint16_t configured_cost_count = 0;
  ActivityPlanningTypedBoolV1 affordable{};
  ActivityPlanningTypedBoolV1 cooldown_active{};
  ActivityPlanningTypedIntegerV1 cooldown_days_remaining{};
};

struct ActivityPlanningSourceAdapterStateV1 {
  ActivityPlanningSourceAdapterEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(ActivityPlanningSourceAdapterFailureV1::none)};
  std::atomic<bool> session_active{false};
  ActivityPlanningSnapshotRequestV1 request{};
  ActivityPlanningSourceAdapterOwnedSampleV1 captured{};
  std::array<ActivityPlanningNativeCandidateV1,
             kActivityPlanningMaximumCandidatesV1>
      projected_candidates{};
  std::array<std::string_view, kActivityPlanningMaximumSelectedOptionsV1>
      projected_options{};
  std::array<ActivityPlanningNativeConfiguredCostV1,
             kActivityPlanningMaximumConfiguredCostsV1>
      projected_costs{};
};

bool ConfigureActivityPlanningSourceAdapterV1(
    ActivityPlanningSourceAdapterStateV1 &state,
    const ActivityPlanningSourceAdapterEnvironmentV1 &source_environment,
    ActivityPlanningSnapshotPrivateEnvironmentV1
        &observer_environment) noexcept;

ActivityPlanningSourceAdapterFailureV1
ReadActivityPlanningSourceAdapterFailureV1(
    const ActivityPlanningSourceAdapterStateV1 &state) noexcept;

std::string_view ActivityPlanningSourceAdapterFailureKeyV1(
    ActivityPlanningSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::bridge

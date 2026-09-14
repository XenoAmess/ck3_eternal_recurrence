#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActivityPlanningSnapshotPrivateObserverKeyV1 =
        "g2_activity_planning_snapshot_v1_private_observer";
inline constexpr std::string_view
    kActivityPlanningSnapshotPrivateSchemaV1 =
        "xar.ck3.private.activity_planning_snapshot/v1";
inline constexpr std::string_view
    kActivityPlanningSnapshotGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kActivityPlanningSnapshotExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kActivityPlanningSnapshotP0ActivityKeyV1 =
    "activity_feast";

inline constexpr std::size_t kActivityPlanningStableKeyCapacityV1 = 96;
inline constexpr std::size_t kActivityPlanningDisplayTextCapacityV1 = 512;
inline constexpr std::size_t kActivityPlanningMaximumCandidatesV1 = 32;
inline constexpr std::size_t kActivityPlanningMaximumConfiguredCostsV1 = 8;
inline constexpr std::size_t kActivityPlanningMaximumSelectedOptionsV1 = 16;

enum class ActivityPlanningSnapshotStatusV1 : std::uint8_t {
  unavailable = 0,
  available = 1,
};

enum class ActivityPlanningSnapshotFailureV1 : std::uint8_t {
  none = 0,
  observer_disabled,
  unsupported_build,
  callbacks_missing,
  request_invalid,
  frame_unavailable,
  requires_application_main,
  requires_paused,
  owner_unavailable,
  frame_changed,
  provider_failed,
  invalid_native_capture,
};

enum class ActivityPlanningFieldStateV1 : std::uint8_t {
  unknown = 0,
  known = 1,
};

enum class ActivityPlanningUnknownReasonV1 : std::uint8_t {
  none = 0,
  not_observed,
  not_applicable,
  native_final_evaluator_unresolved,
  native_stable_key_unresolved,
  native_candidate_collection_unresolved,
  native_configured_cost_unresolved,
  native_configuration_unresolved,
  provider_unavailable,
};

enum class ActivityPlanningCanPlanSourceV1 : std::uint8_t {
  unknown = 0,
  host_view_final_can_plan,
};

enum class ActivityPlanningCandidateSourceV1 : std::uint8_t {
  unknown = 0,
  native_legal_location_collection,
};

enum class ActivityPlanningConfiguredCostSourceV1 : std::uint8_t {
  unknown = 0,
  native_authoritative_configured_cost,
  ui_predicted_cost,
};

enum class ActivityPlanningConfigurationSourceV1 : std::uint8_t {
  unknown = 0,
  native_selected_configuration,
};

template <std::size_t Capacity> struct ActivityPlanningFixedTextV1 {
  std::array<char, Capacity> bytes{};
  std::uint16_t size = 0;
};

using ActivityPlanningStableKeyV1 =
    ActivityPlanningFixedTextV1<kActivityPlanningStableKeyCapacityV1>;
using ActivityPlanningDisplayTextV1 =
    ActivityPlanningFixedTextV1<kActivityPlanningDisplayTextCapacityV1>;

struct ActivityPlanningNativeTypedBoolV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  bool value = false;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningNativeTypedIntegerV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  std::int64_t value = 0;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningNativeTypedTextV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  std::string_view value{};
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningTypedBoolV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  bool value = false;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningTypedIntegerV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  std::int64_t value = 0;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

template <std::size_t Capacity> struct ActivityPlanningTypedTextV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningFixedTextV1<Capacity> value{};
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

using ActivityPlanningTypedStableKeyV1 =
    ActivityPlanningTypedTextV1<kActivityPlanningStableKeyCapacityV1>;
using ActivityPlanningTypedDisplayTextV1 =
    ActivityPlanningTypedTextV1<kActivityPlanningDisplayTextCapacityV1>;

struct ActivityPlanningFrameIdentityV1 {
  std::uint64_t snapshot_revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t owner_character_id = 0;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  bool owner_alive = false;

  friend bool operator==(const ActivityPlanningFrameIdentityV1 &,
                         const ActivityPlanningFrameIdentityV1 &) = default;
};

struct ActivityPlanningSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int64_t expected_date_raw = 0;
  std::int32_t expected_owner_character_id = 0;
  std::string_view activity_key{};
};

struct ActivityPlanningNativeCandidateV1 {
  std::int64_t location_id = 0;
  std::string_view location_key{};
  std::int64_t native_weight_q100000 = 0;
  ActivityPlanningNativeTypedBoolV1 selectable{};
};

struct ActivityPlanningNativeConfiguredCostV1 {
  std::string_view resource_key{};
  std::int64_t amount_q100000 = 0;
};

struct ActivityPlanningNativeCandidateCollectionV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningCandidateSourceV1 source =
      ActivityPlanningCandidateSourceV1::unknown;
  const ActivityPlanningNativeCandidateV1 *rows = nullptr;
  std::size_t count = 0;
  bool complete = false;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningNativeConfiguredCostCollectionV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningConfiguredCostSourceV1 source =
      ActivityPlanningConfiguredCostSourceV1::unknown;
  const ActivityPlanningNativeConfiguredCostV1 *rows = nullptr;
  std::size_t count = 0;
  bool complete = false;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningNativeSelectedOptionsV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningConfigurationSourceV1 source =
      ActivityPlanningConfigurationSourceV1::unknown;
  const std::string_view *keys = nullptr;
  std::size_t count = 0;
  bool complete = false;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningNativeCaptureV1 {
  std::int32_t owner_character_id = 0;
  std::string_view activity_key{};
  ActivityPlanningCanPlanSourceV1 can_plan_source =
      ActivityPlanningCanPlanSourceV1::unknown;
  ActivityPlanningNativeTypedBoolV1 shown{};
  ActivityPlanningNativeTypedBoolV1 can_plan_final{};
  ActivityPlanningNativeTypedBoolV1 can_start{};
  ActivityPlanningNativeTypedTextV1 failure_display_key{};
  ActivityPlanningNativeTypedTextV1 failure_display_text{};
  ActivityPlanningNativeCandidateCollectionV1 candidates{};
  ActivityPlanningNativeSelectedOptionsV1 selected_options{};
  ActivityPlanningNativeTypedTextV1 host_intent_key{};
  ActivityPlanningNativeTypedTextV1 guest_intent_key{};
  ActivityPlanningNativeTypedTextV1 invite_rule_key{};
  ActivityPlanningNativeConfiguredCostCollectionV1 configured_cost{};
  ActivityPlanningNativeTypedBoolV1 affordable{};
  ActivityPlanningNativeTypedBoolV1 cooldown_active{};
  ActivityPlanningNativeTypedIntegerV1 cooldown_days_remaining{};
};

struct ActivityPlanningCandidateV1 {
  std::int64_t location_id = 0;
  ActivityPlanningStableKeyV1 location_key{};
  std::int64_t native_weight_q100000 = 0;
  ActivityPlanningTypedBoolV1 selectable{};
};

struct ActivityPlanningConfiguredCostV1 {
  ActivityPlanningStableKeyV1 resource_key{};
  std::int64_t amount_q100000 = 0;
};

struct ActivityPlanningCandidateCollectionV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningCandidateSourceV1 source =
      ActivityPlanningCandidateSourceV1::unknown;
  std::array<ActivityPlanningCandidateV1,
             kActivityPlanningMaximumCandidatesV1>
      rows{};
  std::uint16_t count = 0;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningConfiguredCostCollectionV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningConfiguredCostSourceV1 source =
      ActivityPlanningConfiguredCostSourceV1::unknown;
  std::array<ActivityPlanningConfiguredCostV1,
             kActivityPlanningMaximumConfiguredCostsV1>
      rows{};
  std::uint16_t count = 0;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningSelectedOptionsV1 {
  ActivityPlanningFieldStateV1 state = ActivityPlanningFieldStateV1::unknown;
  ActivityPlanningConfigurationSourceV1 source =
      ActivityPlanningConfigurationSourceV1::unknown;
  std::array<ActivityPlanningStableKeyV1,
             kActivityPlanningMaximumSelectedOptionsV1>
      keys{};
  std::uint16_t count = 0;
  ActivityPlanningUnknownReasonV1 unknown_reason =
      ActivityPlanningUnknownReasonV1::not_observed;
};

struct ActivityPlanningSnapshotReadinessV1 {
  bool same_frame_ready = false;
  bool final_can_plan_ready = false;
  bool candidate_inputs_ready = false;
  bool configured_cost_ready = false;
  bool configuration_keys_ready = false;
  bool action_inputs_ready = false;
  bool raw_pointer_fields_persisted = false;
};

struct ActivityPlanningSnapshotPrivateV1 {
  ActivityPlanningSnapshotStatusV1 status =
      ActivityPlanningSnapshotStatusV1::unavailable;
  ActivityPlanningSnapshotFailureV1 unavailable_reason =
      ActivityPlanningSnapshotFailureV1::observer_disabled;
  std::uint64_t snapshot_revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t owner_character_id = 0;
  ActivityPlanningStableKeyV1 activity_key{};
  ActivityPlanningCanPlanSourceV1 can_plan_source =
      ActivityPlanningCanPlanSourceV1::unknown;
  ActivityPlanningTypedBoolV1 shown{};
  ActivityPlanningTypedBoolV1 can_plan_final{};
  ActivityPlanningTypedBoolV1 can_start{};
  ActivityPlanningTypedStableKeyV1 failure_display_key{};
  ActivityPlanningTypedDisplayTextV1 failure_display_text{};
  ActivityPlanningCandidateCollectionV1 candidates{};
  ActivityPlanningSelectedOptionsV1 selected_options{};
  ActivityPlanningTypedStableKeyV1 host_intent_key{};
  ActivityPlanningTypedStableKeyV1 guest_intent_key{};
  ActivityPlanningTypedStableKeyV1 invite_rule_key{};
  ActivityPlanningConfiguredCostCollectionV1 configured_cost{};
  ActivityPlanningTypedBoolV1 affordable{};
  ActivityPlanningTypedBoolV1 cooldown_active{};
  ActivityPlanningTypedIntegerV1 cooldown_days_remaining{};
  ActivityPlanningSnapshotReadinessV1 readiness{};
};

using ActivityPlanningReadFrameV1 = bool (*)(
    void *context, ActivityPlanningFrameIdentityV1 &output) noexcept;
using ActivityPlanningBeginCaptureV1 = bool (*)(
    void *context, const ActivityPlanningSnapshotRequestV1 &request,
    void *&session) noexcept;
using ActivityPlanningReadCaptureV1 = bool (*)(
    void *context, void *session,
    ActivityPlanningNativeCaptureV1 &output) noexcept;
using ActivityPlanningEndCaptureV1 = bool (*)(void *context,
                                              void *session) noexcept;

struct ActivityPlanningSnapshotPrivateEnvironmentV1 {
  bool observer_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  void *context = nullptr;
  ActivityPlanningReadFrameV1 read_frame = nullptr;
  ActivityPlanningBeginCaptureV1 begin_capture = nullptr;
  ActivityPlanningReadCaptureV1 read_capture = nullptr;
  ActivityPlanningEndCaptureV1 end_capture = nullptr;
};

bool ReadActivityPlanningSnapshotPrivateObserverV1(
    const ActivityPlanningSnapshotPrivateEnvironmentV1 &environment,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningSnapshotPrivateV1 &output) noexcept;

std::string SerializeActivityPlanningSnapshotPrivateObserverV1(
    const ActivityPlanningSnapshotPrivateV1 &snapshot);

std::string_view ActivityPlanningSnapshotFailureKeyV1(
    ActivityPlanningSnapshotFailureV1 value) noexcept;
std::string_view ActivityPlanningUnknownReasonKeyV1(
    ActivityPlanningUnknownReasonV1 value) noexcept;

template <std::size_t Capacity>
std::string_view ActivityPlanningFixedTextViewV1(
    const ActivityPlanningFixedTextV1<Capacity> &value) noexcept {
  return {value.bytes.data(), value.size};
}

} // namespace xar::bridge

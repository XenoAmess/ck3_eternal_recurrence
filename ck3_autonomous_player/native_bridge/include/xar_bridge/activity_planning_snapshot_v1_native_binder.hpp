#pragma once

#include "xar_bridge/activity_planning_snapshot_v1_source_adapter.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityPlanningNativeBinderPrivateKeyV1 =
    "activity_planning_snapshot_v1_native_binder";

inline constexpr std::uintptr_t kActivityPlanningRttiDynamicCastRvaV1 =
    0x3E631F4;
inline constexpr std::uintptr_t kActivityPlanningIdlerTypeDescriptorRvaV1 =
    0x501EF28;
inline constexpr std::uintptr_t kActivityPlanningIdlerGfxTypeDescriptorRvaV1 =
    0x501EF50;
inline constexpr std::uintptr_t kActivityPlanningGlobalRootPointerRvaV1 =
    0x570F7B8;
inline constexpr std::uintptr_t kActivityPlanningPlayedCharacterIdRvaV1 =
    0x4FE7EE0;
inline constexpr std::uintptr_t kActivityPlanningCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t kActivityPlanningCharacterFallbackSlotRvaV1 =
    0x570C138;

inline constexpr std::size_t kActivityPlanningRootIdlerOffsetV1 = 0x10;
inline constexpr std::size_t kActivityPlanningIdlerHandlerOffsetV1 = 0x88;
inline constexpr std::size_t kActivityPlanningHandlerActivityHostOffsetV1 =
    0x3D8;
inline constexpr std::size_t kActivityPlanningHostSecondaryVtableOffsetV1 =
    0x10;
inline constexpr std::size_t kActivityPlanningHostOwnerRoundTripOffsetV1 = 0xD0;
inline constexpr std::size_t kActivityPlanningHostOwnerIdOffsetV1 = 0x100;
inline constexpr std::size_t kActivityPlanningActivityTypeStableKeyOffsetV1 =
    0x18;
inline constexpr std::size_t kActivityPlanningCharacterStorageSlotsOffsetV1 =
    0x20;
inline constexpr std::size_t kActivityPlanningCharacterStorageCapacityOffsetV1 =
    0x2C;
inline constexpr std::size_t kActivityPlanningCharacterStorageSlotStrideV1 =
    0x10;
inline constexpr std::size_t kActivityPlanningCharacterStorageObjectOffsetV1 =
    0x08;
inline constexpr std::size_t kActivityPlanningCharacterIdentityOffsetV1 = 0x18;

inline constexpr std::uintptr_t kActivityPlanningIdlerGfxVtableRvaV1 =
    0x40B1D30;
inline constexpr std::uintptr_t kActivityPlanningHandlerVtableRvaV1 = 0x40AF630;
inline constexpr std::uintptr_t kActivityPlanningHostSecondaryVtableRvaV1 =
    0x4166620;
inline constexpr std::uintptr_t kActivityPlanningActivityTypeVtableRvaV1 =
    0x440E308;

inline constexpr std::uintptr_t kActivityPlanningIdlerGfxSlotZeroTargetRvaV1 =
    0xAA4070;
inline constexpr std::uintptr_t kActivityPlanningIdlerGfxSlotOneTargetRvaV1 =
    0xAA4350;
inline constexpr std::uintptr_t kActivityPlanningHandlerSlotZeroTargetRvaV1 =
    0xA72A80;
inline constexpr std::uintptr_t kActivityPlanningHostSlotZeroTargetRvaV1 =
    0xA972B0;
inline constexpr std::uintptr_t
    kActivityPlanningHostSecondarySlotZeroTargetRvaV1 = 0x1514400;
inline constexpr std::uintptr_t
    kActivityPlanningActivityTypeSlotZeroTargetRvaV1 = 0x7E9220;

inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningHandlerInstallSignatureV1{
        0x48, 0x8D, 0x05, 0xEB, 0xD7, 0x63, 0x03, 0x49,
        0x89, 0x06, 0x48, 0x8D, 0x05, 0x59, 0xD8, 0x63};
inline constexpr std::uintptr_t kActivityPlanningHandlerInstallSignatureRvaV1 =
    0xA71E3E;
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningIdlerOwnerSignatureV1{0x48, 0x89, 0x5C, 0x24, 0x10, 0x57,
                                           0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B,
                                           0xD9, 0xB9, 0xE8, 0x6C};
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningHostConstructorSignatureV1{
        0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x6C,
        0x24, 0x18, 0x48, 0x89, 0x74, 0x24, 0x20, 0x57};
inline constexpr std::uintptr_t kActivityPlanningHostConstructorSignatureRvaV1 =
    0xA90740;
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningTypeSetterSignatureV1{0x40, 0x53, 0x48, 0x83, 0xEC, 0x20,
                                           0x48, 0x8B, 0xD9, 0x48, 0x8B, 0xCA,
                                           0xE8, 0x7F, 0x1D, 0x00};
inline constexpr std::uintptr_t kActivityPlanningTypeSetterSignatureRvaV1 =
    0x15050E0;
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningOwnerSetterSignatureV1{0x89, 0x54, 0x24, 0x10, 0x53, 0x48,
                                            0x81, 0xEC, 0x90, 0x01, 0x00, 0x00,
                                            0x48, 0x8B, 0xD9, 0x48};
inline constexpr std::uintptr_t kActivityPlanningOwnerSetterSignatureRvaV1 =
    0x1505140;
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningCanPlanSignatureV1{0x48, 0x83, 0xEC, 0x38, 0x48, 0x8B,
                                        0x81, 0x68, 0x02, 0x00, 0x00, 0x80,
                                        0xB8, 0xC3, 0x3F, 0x00};
inline constexpr std::array<std::uint8_t, 16>
    kActivityPlanningRttiCastSignatureV1{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48,
                                         0x89, 0x74, 0x24, 0x18, 0x57, 0x41,
                                         0x54, 0x41, 0x55, 0x41};

enum class ActivityPlanningNativeBinderFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  callbacks_missing,
  image_signature_mismatch,
  vtable_slot_mismatch,
  request_invalid,
  frame_unavailable,
  frame_mismatch,
  owner_path_unavailable,
  owner_identity_mismatch,
  host_view_identity_mismatch,
  activity_type_identity_mismatch,
  activity_key_unavailable,
  activity_key_mismatch,
  final_can_plan_failed,
  semantic_read_failed,
  semantic_sample_invalid,
  semantic_sample_drift,
  container_busy,
  container_token_invalid,
};

struct ActivityPlanningNativeSemanticLocationV1 {
  std::int64_t location_id = 0;
  ActivityPlanningStableKeyV1 location_key{};
  std::int64_t native_weight_q100000 = 0;
  std::uint8_t selectable = 0;
};

struct ActivityPlanningNativeSemanticCostV1 {
  ActivityPlanningStableKeyV1 resource_key{};
  std::int64_t amount_q100000 = 0;
};

struct ActivityPlanningNativeSemanticSampleV1 {
  ActivityPlanningFrameIdentityV1 frame{};
  std::int32_t owner_character_id = 0;
  ActivityPlanningStableKeyV1 activity_key{};
  bool complete = false;
  ActivityPlanningCandidateSourceV1 candidate_source =
      ActivityPlanningCandidateSourceV1::unknown;
  ActivityPlanningConfiguredCostSourceV1 configured_cost_source =
      ActivityPlanningConfiguredCostSourceV1::unknown;
  ActivityPlanningConfigurationSourceV1 configuration_source =
      ActivityPlanningConfigurationSourceV1::unknown;
  std::array<ActivityPlanningNativeSemanticLocationV1,
             kActivityPlanningMaximumCandidatesV1>
      locations{};
  std::uint16_t location_count = 0;
  std::array<ActivityPlanningNativeSemanticCostV1,
             kActivityPlanningMaximumConfiguredCostsV1>
      configured_costs{};
  std::uint16_t configured_cost_count = 0;
  std::array<ActivityPlanningStableKeyV1,
             kActivityPlanningMaximumSelectedOptionsV1>
      selected_options{};
  std::uint16_t selected_option_count = 0;
  ActivityPlanningStableKeyV1 host_intent_key{};
  ActivityPlanningStableKeyV1 guest_intent_key{};
  ActivityPlanningStableKeyV1 invite_rule_key{};
  std::uint8_t shown = 0;
  std::uint8_t can_start = 0;
  std::uint8_t affordable = 0;
  std::uint8_t cooldown_active = 0;
  std::int64_t cooldown_days_remaining = 0;
};

struct ActivityPlanningNativeCanPlanResultV1 {
  bool complete = false;
  bool used_host_view_final_can_plan = false;
  std::uint8_t value = 0;
  ActivityPlanningStableKeyV1 failure_display_key{};
  ActivityPlanningDisplayTextV1 failure_display_text{};
};

using ActivityPlanningNativeRttiDynamicCastV1 =
    void *(*)(void *source, std::int32_t vf_delta, void *source_type,
              void *target_type, std::int32_t is_reference);
using ActivityPlanningNativeInvokeCanPlanV1 = bool (*)(
    void *context, std::uintptr_t module_base, std::uintptr_t exact_entry_point,
    std::uintptr_t host_view, std::uintptr_t activity_type,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningNativeCanPlanResultV1 &output) noexcept;
using ActivityPlanningNativeReadSemanticsV1 =
    bool (*)(void *context, std::uintptr_t module_base,
             std::uintptr_t host_view, std::uintptr_t activity_type,
             const ActivityPlanningSnapshotRequestV1 &request,
             ActivityPlanningNativeSemanticSampleV1 &output) noexcept;

struct ActivityPlanningNativeBinderEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  void *context = nullptr;
  ActivityPlanningReadFrameV1 read_frame = nullptr;
  ActivityPlanningSourceMemoryReadV1 read_memory = nullptr;
  ActivityPlanningNativeRttiDynamicCastV1 rtti_dynamic_cast = nullptr;
  ActivityPlanningNativeInvokeCanPlanV1 invoke_final_can_plan = nullptr;
  ActivityPlanningNativeReadSemanticsV1 read_semantics = nullptr;
};

struct ActivityPlanningNativeBinderStateV1 {
  ActivityPlanningNativeBinderEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{
      static_cast<std::uint32_t>(ActivityPlanningNativeBinderFailureV1::none)};
  std::atomic<bool> container_active{false};
  std::atomic<std::uint64_t> next_token{0};
  std::uintptr_t active_token = 0;
  ActivityPlanningSnapshotRequestV1 active_request{};
  ActivityPlanningNativeSemanticSampleV1 active_sample{};
  ActivityPlanningStableKeyV1 definition_key_scratch{};
  ActivityPlanningNativeCanPlanResultV1 can_plan_scratch{};
  std::array<ActivityPlanningSourceLocationRowV1,
             kActivityPlanningMaximumCandidatesV1>
      projected_locations{};
  std::array<ActivityPlanningSourceCostRowV1,
             kActivityPlanningMaximumConfiguredCostsV1>
      projected_costs{};
  std::array<ActivityPlanningSourceOptionRowV1,
             kActivityPlanningMaximumSelectedOptionsV1>
      projected_options{};
};

ActivityPlanningNativeBinderEnvironmentV1
BindActivityPlanningNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool ConfigureActivityPlanningNativeBinderV1(
    ActivityPlanningNativeBinderStateV1 &state,
    const ActivityPlanningNativeBinderEnvironmentV1 &environment,
    ActivityPlanningSourceAdapterEnvironmentV1 &source_environment) noexcept;

ActivityPlanningNativeBinderFailureV1 ReadActivityPlanningNativeBinderFailureV1(
    const ActivityPlanningNativeBinderStateV1 &state) noexcept;

std::string_view ActivityPlanningNativeBinderFailureKeyV1(
    ActivityPlanningNativeBinderFailureV1 failure) noexcept;

} // namespace xar::bridge

#include "xar_bridge/activity_planning_snapshot_v1_native_binder.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <type_traits>

#if defined(_MSC_VER)
#if !defined(NOMINMAX)
#define NOMINMAX
#endif
#include <Windows.h>
#endif

namespace xar::bridge {
namespace {

constexpr std::int32_t kMaximumCharacterStorageSlots = 0x01000000;

struct NativeIdentityV1 {
  std::uintptr_t handler = 0;
  std::uintptr_t host_view = 0;
  std::uintptr_t activity_type = 0;
  ActivityPlanningStableKeyV1 activity_key{};
};

static_assert(sizeof(void *) == 8,
              "activity planning native binder is x64-only");
static_assert(
    std::is_trivially_copyable_v<ActivityPlanningNativeSemanticSampleV1>);

void SetFailure(ActivityPlanningNativeBinderStateV1 &state,
                ActivityPlanningNativeBinderFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool CheckedAdd(std::uintptr_t base, std::size_t offset,
                std::uintptr_t &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

bool DirectMemoryRead(void *, std::uintptr_t address, void *output,
                      std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0)
    return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
#endif
}

bool ReadMemory(const ActivityPlanningNativeBinderEnvironmentV1 &environment,
                std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return environment.read_memory != nullptr && address != 0 &&
         output != nullptr && size != 0 &&
         environment.read_memory(environment.context, address, output, size);
}

template <typename Value>
bool ReadAt(const ActivityPlanningNativeBinderEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, Value &output) noexcept {
  std::uintptr_t address = 0;
  return CheckedAdd(base, offset, address) &&
         ReadMemory(environment, address, &output, sizeof(output));
}

bool ReadPointer(const ActivityPlanningNativeBinderEnvironmentV1 &environment,
                 std::uintptr_t address, std::uintptr_t &output) noexcept {
  output = 0;
  return ReadMemory(environment, address, &output, sizeof(output));
}

template <std::size_t Capacity>
bool ValidText(const ActivityPlanningFixedTextV1<Capacity> &value) noexcept {
  if (value.size == 0 || value.size >= Capacity)
    return false;
  return std::none_of(value.bytes.begin(), value.bytes.begin() + value.size,
                      [](char ch) { return ch == '\0'; });
}

template <std::size_t Capacity>
bool TextEquals(const ActivityPlanningFixedTextV1<Capacity> &value,
                std::string_view expected) noexcept {
  return ActivityPlanningFixedTextViewV1(value) == expected;
}

template <std::size_t Capacity>
ActivityPlanningSourceStringRefV1
TextRef(const ActivityPlanningFixedTextV1<Capacity> &value) noexcept {
  return {reinterpret_cast<std::uintptr_t>(value.bytes.data()), value.size};
}

bool ReadStableKey(const ActivityPlanningNativeBinderEnvironmentV1 &environment,
                   std::uintptr_t object, std::size_t key_offset,
                   ActivityPlanningStableKeyV1 &output) noexcept {
  output = {};
  std::uintptr_t native_string = 0;
  if (!CheckedAdd(object, key_offset, native_string))
    return false;
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!ReadAt(environment, native_string, 0x10, size) ||
      !ReadAt(environment, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size >= output.bytes.size()) {
    return false;
  }
  std::uintptr_t bytes = native_string;
  if (capacity > 15 &&
      (!ReadPointer(environment, native_string, bytes) || bytes == 0)) {
    return false;
  }
  if (!ReadMemory(environment, bytes, output.bytes.data(),
                  static_cast<std::size_t>(size))) {
    output = {};
    return false;
  }
  output.size = static_cast<std::uint16_t>(size);
  return ValidText(output);
}

bool FrameMatchesRequest(const ActivityPlanningFrameIdentityV1 &frame,
                         const ActivityPlanningSnapshotRequestV1 &request) {
  return frame.snapshot_revision == request.expected_snapshot_revision &&
         frame.date_raw == request.expected_date_raw &&
         frame.owner_character_id == request.expected_owner_character_id &&
         frame.application_main_thread && frame.paused && frame.map_ready &&
         frame.owner_alive;
}

bool ReadStableFrame(ActivityPlanningNativeBinderStateV1 &state,
                     const ActivityPlanningSnapshotRequestV1 &request,
                     ActivityPlanningFrameIdentityV1 &output) noexcept {
  output = {};
  if (state.environment.read_frame == nullptr ||
      !state.environment.read_frame(state.environment.context, output)) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::frame_unavailable);
    return false;
  }
  if (!FrameMatchesRequest(output, request)) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::frame_mismatch);
    return false;
  }
  return true;
}

bool ResolveCharacterRoundTrip(
    const ActivityPlanningNativeBinderEnvironmentV1 &environment,
    std::uint32_t full_id) noexcept {
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  if (!ReadPointer(environment,
                   environment.module_base +
                       kActivityPlanningCharacterStorageSlotRvaV1,
                   storage) ||
      !ReadPointer(environment,
                   environment.module_base +
                       kActivityPlanningCharacterFallbackSlotRvaV1,
                   fallback) ||
      storage == 0) {
    return false;
  }
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadAt(environment, storage,
              kActivityPlanningCharacterStorageSlotsOffsetV1, slots) ||
      !ReadAt(environment, storage,
              kActivityPlanningCharacterStorageCapacityOffsetV1, capacity) ||
      slots == 0 || capacity <= 0 || capacity > kMaximumCharacterStorageSlots) {
    return false;
  }
  const auto index = full_id & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity))
    return false;
  std::uintptr_t object_slot = 0;
  if (!CheckedAdd(slots,
                  static_cast<std::size_t>(index) *
                          kActivityPlanningCharacterStorageSlotStrideV1 +
                      kActivityPlanningCharacterStorageObjectOffsetV1,
                  object_slot)) {
    return false;
  }
  std::uintptr_t character = 0;
  std::uint32_t observed_id = 0xFFFFFFFFU;
  return ReadPointer(environment, object_slot, character) && character != 0 &&
         character != fallback &&
         ReadAt(environment, character,
                kActivityPlanningCharacterIdentityOffsetV1, observed_id) &&
         observed_id == full_id;
}

bool InvokeRttiCast(
    const ActivityPlanningNativeBinderEnvironmentV1 &environment,
    std::uintptr_t source, std::uintptr_t &output) noexcept {
  output = 0;
  if (environment.rtti_dynamic_cast == nullptr || source == 0)
    return false;
  void *result = nullptr;
#if defined(_MSC_VER)
  __try {
    result = environment.rtti_dynamic_cast(
        reinterpret_cast<void *>(source), 0,
        reinterpret_cast<void *>(environment.module_base +
                                 kActivityPlanningIdlerTypeDescriptorRvaV1),
        reinterpret_cast<void *>(environment.module_base +
                                 kActivityPlanningIdlerGfxTypeDescriptorRvaV1),
        0);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    result = nullptr;
  }
#else
  result = environment.rtti_dynamic_cast(
      reinterpret_cast<void *>(source), 0,
      reinterpret_cast<void *>(environment.module_base +
                               kActivityPlanningIdlerTypeDescriptorRvaV1),
      reinterpret_cast<void *>(environment.module_base +
                               kActivityPlanningIdlerGfxTypeDescriptorRvaV1),
      0);
#endif
  output = reinterpret_cast<std::uintptr_t>(result);
  return output != 0;
}

bool ResolveIdentity(ActivityPlanningNativeBinderStateV1 &state,
                     const ActivityPlanningSnapshotRequestV1 &request,
                     NativeIdentityV1 &output) noexcept {
  output = {};
  auto &environment = state.environment;
  std::uintptr_t root = 0;
  std::uintptr_t idler_base = 0;
  std::uintptr_t idler_gfx = 0;
  if (!ReadPointer(environment,
                   environment.module_base +
                       kActivityPlanningGlobalRootPointerRvaV1,
                   root) ||
      root == 0 ||
      !ReadAt(environment, root, kActivityPlanningRootIdlerOffsetV1,
              idler_base) ||
      idler_base == 0 || !InvokeRttiCast(environment, idler_base, idler_gfx)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::owner_path_unavailable);
    return false;
  }
  std::uintptr_t idler_vtable = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t host_primary_vtable = 0;
  std::uintptr_t host_secondary_vtable = 0;
  std::uintptr_t host_owner = 0;
  std::int32_t host_owner_id = 0;
  std::uint32_t current_owner_id = 0xFFFFFFFFU;
  if (!ReadAt(environment, idler_gfx, 0, idler_vtable) ||
      !ReadAt(environment, idler_gfx, kActivityPlanningIdlerHandlerOffsetV1,
              output.handler) ||
      output.handler == 0 ||
      !ReadAt(environment, output.handler, 0, handler_vtable) ||
      !ReadAt(environment, output.handler,
              kActivityPlanningHandlerActivityHostOffsetV1, output.host_view) ||
      output.host_view == 0 ||
      !ReadAt(environment, output.host_view, 0, host_primary_vtable) ||
      !ReadAt(environment, output.host_view,
              kActivityPlanningHostSecondaryVtableOffsetV1,
              host_secondary_vtable) ||
      !ReadAt(environment, output.host_view,
              kActivityPlanningHostOwnerRoundTripOffsetV1, host_owner) ||
      !ReadAt(environment, output.host_view,
              kActivityPlanningHostOwnerIdOffsetV1, host_owner_id) ||
      !ReadAt(environment, output.host_view,
              kActivityPlanningHostViewActivityTypeOffsetV1,
              output.activity_type) ||
      output.activity_type == 0 ||
      !ReadMemory(environment,
                  environment.module_base +
                      kActivityPlanningPlayedCharacterIdRvaV1,
                  &current_owner_id, sizeof(current_owner_id))) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::owner_path_unavailable);
    return false;
  }
  if (idler_vtable !=
          environment.module_base + kActivityPlanningIdlerGfxVtableRvaV1 ||
      handler_vtable !=
          environment.module_base + kActivityPlanningHandlerVtableRvaV1 ||
      host_primary_vtable != environment.module_base +
                                 kActivityPlanningHostViewPrimaryVtableRvaV1 ||
      host_secondary_vtable !=
          environment.module_base + kActivityPlanningHostSecondaryVtableRvaV1 ||
      host_owner != output.handler) {
    SetFailure(
        state,
        ActivityPlanningNativeBinderFailureV1::host_view_identity_mismatch);
    return false;
  }
  if (host_owner_id != request.expected_owner_character_id ||
      current_owner_id !=
          static_cast<std::uint32_t>(request.expected_owner_character_id) ||
      !ResolveCharacterRoundTrip(
          environment,
          static_cast<std::uint32_t>(request.expected_owner_character_id))) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::owner_identity_mismatch);
    return false;
  }
  std::uintptr_t type_vtable = 0;
  if (!ReadAt(environment, output.activity_type, 0, type_vtable) ||
      type_vtable !=
          environment.module_base + kActivityPlanningActivityTypeVtableRvaV1) {
    SetFailure(
        state,
        ActivityPlanningNativeBinderFailureV1::activity_type_identity_mismatch);
    return false;
  }
  if (!ReadStableKey(environment, output.activity_type,
                     kActivityPlanningActivityTypeStableKeyOffsetV1,
                     output.activity_key)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::activity_key_unavailable);
    return false;
  }
  if (!TextEquals(output.activity_key, request.activity_key)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::activity_key_mismatch);
    return false;
  }
  return true;
}

template <std::size_t Capacity>
void ClearTail(ActivityPlanningFixedTextV1<Capacity> &value) noexcept {
  if (value.size < Capacity) {
    std::fill(value.bytes.begin() + value.size, value.bytes.end(), '\0');
  }
}

void Normalize(ActivityPlanningNativeSemanticSampleV1 &sample) noexcept {
  ClearTail(sample.activity_key);
  ClearTail(sample.host_intent_key);
  ClearTail(sample.guest_intent_key);
  ClearTail(sample.invite_rule_key);
  for (std::size_t index = 0; index < sample.location_count; ++index)
    ClearTail(sample.locations[index].location_key);
  for (std::size_t index = sample.location_count;
       index < sample.locations.size(); ++index)
    sample.locations[index] = {};
  for (std::size_t index = 0; index < sample.configured_cost_count; ++index)
    ClearTail(sample.configured_costs[index].resource_key);
  for (std::size_t index = sample.configured_cost_count;
       index < sample.configured_costs.size(); ++index)
    sample.configured_costs[index] = {};
  for (std::size_t index = 0; index < sample.selected_option_count; ++index)
    ClearTail(sample.selected_options[index]);
  for (std::size_t index = sample.selected_option_count;
       index < sample.selected_options.size(); ++index)
    sample.selected_options[index] = {};
}

bool ValidSemanticSample(
    const ActivityPlanningNativeSemanticSampleV1 &sample,
    const ActivityPlanningSnapshotRequestV1 &request) noexcept {
  if (!sample.complete || !FrameMatchesRequest(sample.frame, request) ||
      sample.owner_character_id != request.expected_owner_character_id ||
      !ValidText(sample.activity_key) ||
      !TextEquals(sample.activity_key, request.activity_key) ||
      sample.candidate_source !=
          ActivityPlanningCandidateSourceV1::native_legal_location_collection ||
      sample.configured_cost_source !=
          ActivityPlanningConfiguredCostSourceV1::
              native_authoritative_configured_cost ||
      sample.configuration_source != ActivityPlanningConfigurationSourceV1::
                                         native_selected_configuration ||
      sample.location_count > sample.locations.size() ||
      sample.configured_cost_count > sample.configured_costs.size() ||
      sample.selected_option_count > sample.selected_options.size() ||
      !ValidText(sample.host_intent_key) ||
      !ValidText(sample.guest_intent_key) ||
      !ValidText(sample.invite_rule_key) || sample.shown > 1 ||
      sample.can_start > 1 || sample.affordable > 1 ||
      sample.cooldown_active > 1 || sample.cooldown_days_remaining < 0) {
    return false;
  }
  for (std::uint16_t index = 0; index < sample.location_count; ++index) {
    const auto &row = sample.locations[index];
    if (row.location_id == 0 || row.selectable > 1 ||
        !ValidText(row.location_key))
      return false;
    for (std::uint16_t previous = 0; previous < index; ++previous) {
      if (row.location_id == sample.locations[previous].location_id ||
          ActivityPlanningFixedTextViewV1(row.location_key) ==
              ActivityPlanningFixedTextViewV1(
                  sample.locations[previous].location_key))
        return false;
    }
  }
  for (std::uint16_t index = 0; index < sample.configured_cost_count; ++index) {
    const auto &row = sample.configured_costs[index];
    if (row.amount_q100000 < 0 || !ValidText(row.resource_key))
      return false;
    for (std::uint16_t previous = 0; previous < index; ++previous) {
      if (ActivityPlanningFixedTextViewV1(row.resource_key) ==
          ActivityPlanningFixedTextViewV1(
              sample.configured_costs[previous].resource_key))
        return false;
    }
  }
  for (std::uint16_t index = 0; index < sample.selected_option_count; ++index) {
    if (!ValidText(sample.selected_options[index]))
      return false;
    for (std::uint16_t previous = 0; previous < index; ++previous) {
      if (ActivityPlanningFixedTextViewV1(sample.selected_options[index]) ==
          ActivityPlanningFixedTextViewV1(sample.selected_options[previous]))
        return false;
    }
  }
  return true;
}

bool SemanticSamplesEqual(
    const ActivityPlanningNativeSemanticSampleV1 &left,
    const ActivityPlanningNativeSemanticSampleV1 &right) noexcept {
  if (left.frame != right.frame ||
      left.owner_character_id != right.owner_character_id ||
      ActivityPlanningFixedTextViewV1(left.activity_key) !=
          ActivityPlanningFixedTextViewV1(right.activity_key) ||
      left.complete != right.complete ||
      left.candidate_source != right.candidate_source ||
      left.configured_cost_source != right.configured_cost_source ||
      left.configuration_source != right.configuration_source ||
      left.location_count != right.location_count ||
      left.configured_cost_count != right.configured_cost_count ||
      left.selected_option_count != right.selected_option_count ||
      ActivityPlanningFixedTextViewV1(left.host_intent_key) !=
          ActivityPlanningFixedTextViewV1(right.host_intent_key) ||
      ActivityPlanningFixedTextViewV1(left.guest_intent_key) !=
          ActivityPlanningFixedTextViewV1(right.guest_intent_key) ||
      ActivityPlanningFixedTextViewV1(left.invite_rule_key) !=
          ActivityPlanningFixedTextViewV1(right.invite_rule_key) ||
      left.shown != right.shown || left.can_start != right.can_start ||
      left.affordable != right.affordable ||
      left.cooldown_active != right.cooldown_active ||
      left.cooldown_days_remaining != right.cooldown_days_remaining) {
    return false;
  }
  for (std::uint16_t index = 0; index < left.location_count; ++index) {
    const auto &a = left.locations[index];
    const auto &b = right.locations[index];
    if (a.location_id != b.location_id ||
        ActivityPlanningFixedTextViewV1(a.location_key) !=
            ActivityPlanningFixedTextViewV1(b.location_key) ||
        a.native_weight_q100000 != b.native_weight_q100000 ||
        a.selectable != b.selectable)
      return false;
  }
  for (std::uint16_t index = 0; index < left.configured_cost_count; ++index) {
    const auto &a = left.configured_costs[index];
    const auto &b = right.configured_costs[index];
    if (ActivityPlanningFixedTextViewV1(a.resource_key) !=
            ActivityPlanningFixedTextViewV1(b.resource_key) ||
        a.amount_q100000 != b.amount_q100000)
      return false;
  }
  for (std::uint16_t index = 0; index < left.selected_option_count; ++index) {
    if (ActivityPlanningFixedTextViewV1(left.selected_options[index]) !=
        ActivityPlanningFixedTextViewV1(right.selected_options[index]))
      return false;
  }
  return true;
}

bool ReadSemanticSample(
    ActivityPlanningNativeBinderStateV1 &state,
    const ActivityPlanningSnapshotRequestV1 &request,
    std::uintptr_t expected_host, std::uintptr_t expected_type,
    ActivityPlanningNativeSemanticSampleV1 &output) noexcept {
  ActivityPlanningFrameIdentityV1 before{};
  if (!ReadStableFrame(state, request, before))
    return false;
  NativeIdentityV1 identity{};
  if (!ResolveIdentity(state, request, identity))
    return false;
  if ((expected_host != 0 && identity.host_view != expected_host) ||
      (expected_type != 0 && identity.activity_type != expected_type)) {
    SetFailure(
        state,
        ActivityPlanningNativeBinderFailureV1::host_view_identity_mismatch);
    return false;
  }
  output = {};
  if (!state.environment.read_semantics(
          state.environment.context, state.environment.module_base,
          identity.host_view, identity.activity_type, request, output)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::semantic_read_failed);
    return false;
  }
  Normalize(output);
  if (!ValidSemanticSample(output, request)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::semantic_sample_invalid);
    return false;
  }
  ActivityPlanningFrameIdentityV1 after{};
  if (!ReadStableFrame(state, request, after))
    return false;
  if (after != before || output.frame != before) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::frame_mismatch);
    return false;
  }
  return true;
}

template <std::size_t Size>
bool MatchSignature(
    const ActivityPlanningNativeBinderEnvironmentV1 &environment,
    std::uintptr_t rva,
    const std::array<std::uint8_t, Size> &expected) noexcept {
  std::array<std::uint8_t, Size> actual{};
  return ReadMemory(environment, environment.module_base + rva, actual.data(),
                    actual.size()) &&
         actual == expected;
}

bool MatchSlot(const ActivityPlanningNativeBinderEnvironmentV1 &environment,
               std::uintptr_t vtable_rva, std::size_t slot,
               std::uintptr_t target_rva) noexcept {
  std::uintptr_t actual = 0;
  return ReadPointer(environment,
                     environment.module_base + vtable_rva +
                         slot * sizeof(std::uintptr_t),
                     actual) &&
         actual == environment.module_base + target_rva;
}

ActivityPlanningNativeBinderFailureV1 ValidateEnvironment(
    const ActivityPlanningNativeBinderEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kActivityPlanningSourceAdapterExecutableSha256V1) {
    return ActivityPlanningNativeBinderFailureV1::exact_build_not_admitted;
  }
  if (environment.read_frame == nullptr || environment.read_memory == nullptr ||
      environment.rtti_dynamic_cast == nullptr ||
      environment.invoke_final_can_plan == nullptr ||
      environment.read_semantics == nullptr) {
    return ActivityPlanningNativeBinderFailureV1::callbacks_missing;
  }
  if (!environment.offline_fixture &&
      reinterpret_cast<std::uintptr_t>(environment.rtti_dynamic_cast) !=
          environment.module_base + kActivityPlanningRttiDynamicCastRvaV1) {
    return ActivityPlanningNativeBinderFailureV1::callbacks_missing;
  }
  if (!MatchSignature(environment,
                      kActivityPlanningHandlerInstallSignatureRvaV1,
                      kActivityPlanningHandlerInstallSignatureV1) ||
      !MatchSignature(environment, kActivityPlanningIdlerGfxSlotOneTargetRvaV1,
                      kActivityPlanningIdlerOwnerSignatureV1) ||
      !MatchSignature(environment,
                      kActivityPlanningHostConstructorSignatureRvaV1,
                      kActivityPlanningHostConstructorSignatureV1) ||
      !MatchSignature(environment, kActivityPlanningTypeSetterSignatureRvaV1,
                      kActivityPlanningTypeSetterSignatureV1) ||
      !MatchSignature(environment, kActivityPlanningOwnerSetterSignatureRvaV1,
                      kActivityPlanningOwnerSetterSignatureV1) ||
      !MatchSignature(environment, kActivityPlanningHostViewCanPlanRvaV1,
                      kActivityPlanningCanPlanSignatureV1) ||
      !MatchSignature(environment, kActivityPlanningRttiDynamicCastRvaV1,
                      kActivityPlanningRttiCastSignatureV1)) {
    return ActivityPlanningNativeBinderFailureV1::image_signature_mismatch;
  }
  if (!MatchSlot(environment, kActivityPlanningIdlerGfxVtableRvaV1, 0,
                 kActivityPlanningIdlerGfxSlotZeroTargetRvaV1) ||
      !MatchSlot(environment, kActivityPlanningIdlerGfxVtableRvaV1, 1,
                 kActivityPlanningIdlerGfxSlotOneTargetRvaV1) ||
      !MatchSlot(environment, kActivityPlanningHandlerVtableRvaV1, 0,
                 kActivityPlanningHandlerSlotZeroTargetRvaV1) ||
      !MatchSlot(environment, kActivityPlanningHostViewPrimaryVtableRvaV1, 0,
                 kActivityPlanningHostSlotZeroTargetRvaV1) ||
      !MatchSlot(environment, kActivityPlanningHostViewPrimaryVtableRvaV1,
                 kActivityPlanningHostViewCanPlanVtableSlotV1,
                 kActivityPlanningHostViewCanPlanRvaV1) ||
      !MatchSlot(environment, kActivityPlanningHostSecondaryVtableRvaV1, 0,
                 kActivityPlanningHostSecondarySlotZeroTargetRvaV1) ||
      !MatchSlot(environment, kActivityPlanningActivityTypeVtableRvaV1, 0,
                 kActivityPlanningActivityTypeSlotZeroTargetRvaV1)) {
    return ActivityPlanningNativeBinderFailureV1::vtable_slot_mismatch;
  }
  return ActivityPlanningNativeBinderFailureV1::none;
}

bool BinderReadFrame(void *context,
                     ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  return state.environment.read_frame != nullptr &&
         state.environment.read_frame(state.environment.context, output);
}

bool BinderReadMemory(void *context, std::uintptr_t address, void *output,
                      std::size_t size) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  return ReadMemory(state.environment, address, output, size);
}

bool BinderResolveHostView(void *context, std::int32_t owner_character_id,
                           std::string_view activity_key,
                           std::uintptr_t &host_view) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  host_view = 0;
  if (owner_character_id <= 0 ||
      activity_key != kActivityPlanningSnapshotP0ActivityKeyV1) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::request_invalid);
    return false;
  }
  ActivityPlanningSnapshotRequestV1 request{};
  request.expected_owner_character_id = owner_character_id;
  request.activity_key = activity_key;
  ActivityPlanningFrameIdentityV1 frame{};
  if (state.environment.read_frame == nullptr ||
      !state.environment.read_frame(state.environment.context, frame)) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::frame_unavailable);
    return false;
  }
  request.expected_snapshot_revision = frame.snapshot_revision;
  request.expected_date_raw = frame.date_raw;
  if (!FrameMatchesRequest(frame, request)) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::frame_mismatch);
    return false;
  }
  NativeIdentityV1 identity{};
  if (!ResolveIdentity(state, request, identity))
    return false;
  host_view = identity.host_view;
  SetFailure(state, ActivityPlanningNativeBinderFailureV1::none);
  return true;
}

bool BinderReadDefinitionKey(void *context, std::uintptr_t activity_type,
                             ActivityPlanningSourceStringRefV1 &key) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  key = {};
  std::uintptr_t vtable = 0;
  if (activity_type == 0 ||
      !ReadAt(state.environment, activity_type, 0, vtable) ||
      vtable != state.environment.module_base +
                    kActivityPlanningActivityTypeVtableRvaV1) {
    SetFailure(
        state,
        ActivityPlanningNativeBinderFailureV1::activity_type_identity_mismatch);
    return false;
  }
  if (!ReadStableKey(state.environment, activity_type,
                     kActivityPlanningActivityTypeStableKeyOffsetV1,
                     state.definition_key_scratch)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::activity_key_unavailable);
    return false;
  }
  key = TextRef(state.definition_key_scratch);
  return true;
}

bool BinderInvokeCanPlan(
    void *context, std::uintptr_t exact_entry_point, std::uintptr_t host_view,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningSourceCanPlanResultV1 &output) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  output = {};
  if (exact_entry_point !=
      state.environment.module_base + kActivityPlanningHostViewCanPlanRvaV1) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::vtable_slot_mismatch);
    return false;
  }
  NativeIdentityV1 identity{};
  if (!ResolveIdentity(state, request, identity))
    return false;
  if (identity.host_view != host_view) {
    SetFailure(
        state,
        ActivityPlanningNativeBinderFailureV1::host_view_identity_mismatch);
    return false;
  }
  state.can_plan_scratch = {};
  if (!state.environment.invoke_final_can_plan(
          state.environment.context, state.environment.module_base,
          exact_entry_point, identity.host_view, identity.activity_type,
          request, state.can_plan_scratch)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::final_can_plan_failed);
    return false;
  }
  auto &result = state.can_plan_scratch;
  ClearTail(result.failure_display_key);
  ClearTail(result.failure_display_text);
  if (!result.complete || !result.used_host_view_final_can_plan ||
      result.value > 1 ||
      (result.value != 0 && (result.failure_display_key.size != 0 ||
                             result.failure_display_text.size != 0)) ||
      (result.value == 0 && (!ValidText(result.failure_display_key) ||
                             !ValidText(result.failure_display_text)))) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::final_can_plan_failed);
    return false;
  }
  output.value = result.value;
  if (result.value == 0) {
    output.failure_display_key = TextRef(result.failure_display_key);
    output.failure_display_text = TextRef(result.failure_display_text);
  }
  SetFailure(state, ActivityPlanningNativeBinderFailureV1::none);
  return true;
}

bool BinderOpenSourceContainer(void *context, std::uintptr_t host_view,
                               std::uintptr_t activity_type,
                               const ActivityPlanningSnapshotRequestV1 &request,
                               std::uintptr_t &container_token) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  container_token = 0;
  bool expected = false;
  if (!state.container_active.compare_exchange_strong(
          expected, true, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    SetFailure(state, ActivityPlanningNativeBinderFailureV1::container_busy);
    return false;
  }
  ActivityPlanningNativeSemanticSampleV1 sample{};
  if (!ReadSemanticSample(state, request, host_view, activity_type, sample)) {
    state.container_active.store(false, std::memory_order_release);
    return false;
  }
  auto current = state.next_token.load(std::memory_order_acquire);
  for (;;) {
    if (current == (std::numeric_limits<std::uint64_t>::max)()) {
      SetFailure(state, ActivityPlanningNativeBinderFailureV1::container_busy);
      state.container_active.store(false, std::memory_order_release);
      return false;
    }
    if (state.next_token.compare_exchange_weak(current, current + 1,
                                               std::memory_order_acq_rel,
                                               std::memory_order_acquire))
      break;
  }
  state.active_sample = sample;
  state.active_request = request;
  state.active_request.activity_key =
      ActivityPlanningFixedTextViewV1(state.active_sample.activity_key);
  state.active_token = static_cast<std::uintptr_t>(current + 1);
  container_token = state.active_token;
  SetFailure(state, ActivityPlanningNativeBinderFailureV1::none);
  return true;
}

void ProjectSample(ActivityPlanningNativeBinderStateV1 &state,
                   ActivityPlanningSourceContainerViewV1 &output) noexcept {
  state.projected_locations = {};
  state.projected_costs = {};
  state.projected_options = {};
  const auto &sample = state.active_sample;
  for (std::uint16_t index = 0; index < sample.location_count; ++index) {
    const auto &row = sample.locations[index];
    state.projected_locations[index] = {
        row.location_id, TextRef(row.location_key), row.native_weight_q100000,
        row.selectable};
  }
  for (std::uint16_t index = 0; index < sample.configured_cost_count; ++index) {
    const auto &row = sample.configured_costs[index];
    state.projected_costs[index] = {TextRef(row.resource_key),
                                    row.amount_q100000};
  }
  for (std::uint16_t index = 0; index < sample.selected_option_count; ++index) {
    state.projected_options[index] = {TextRef(sample.selected_options[index])};
  }
  output.location_rows =
      reinterpret_cast<std::uintptr_t>(state.projected_locations.data());
  output.location_count = sample.location_count;
  output.configured_cost_rows =
      reinterpret_cast<std::uintptr_t>(state.projected_costs.data());
  output.configured_cost_count = sample.configured_cost_count;
  output.selected_option_rows =
      reinterpret_cast<std::uintptr_t>(state.projected_options.data());
  output.selected_option_count = sample.selected_option_count;
  output.host_intent_key = TextRef(sample.host_intent_key);
  output.guest_intent_key = TextRef(sample.guest_intent_key);
  output.invite_rule_key = TextRef(sample.invite_rule_key);
  output.shown = sample.shown;
  output.can_start = sample.can_start;
  output.affordable = sample.affordable;
  output.cooldown_active = sample.cooldown_active;
  output.cooldown_days_remaining = sample.cooldown_days_remaining;
}

bool BinderReadSourceContainer(
    void *context, std::uintptr_t container_token,
    ActivityPlanningSourceContainerViewV1 &output) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  output = {};
  if (!state.container_active.load(std::memory_order_acquire) ||
      container_token == 0 || container_token != state.active_token) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::container_token_invalid);
    return false;
  }
  ActivityPlanningNativeSemanticSampleV1 current{};
  if (!ReadSemanticSample(state, state.active_request, 0, 0, current))
    return false;
  if (!SemanticSamplesEqual(current, state.active_sample)) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::semantic_sample_drift);
    return false;
  }
  ProjectSample(state, output);
  SetFailure(state, ActivityPlanningNativeBinderFailureV1::none);
  return true;
}

bool BinderReleaseSourceContainer(void *context,
                                  std::uintptr_t container_token) noexcept {
  auto &state = *static_cast<ActivityPlanningNativeBinderStateV1 *>(context);
  if (!state.container_active.load(std::memory_order_acquire) ||
      container_token == 0 || container_token != state.active_token) {
    SetFailure(state,
               ActivityPlanningNativeBinderFailureV1::container_token_invalid);
    return false;
  }
  state.active_token = 0;
  state.active_request = {};
  state.active_sample = {};
  state.definition_key_scratch = {};
  state.can_plan_scratch = {};
  state.projected_locations = {};
  state.projected_costs = {};
  state.projected_options = {};
  state.container_active.store(false, std::memory_order_release);
  return true;
}

} // namespace

ActivityPlanningNativeBinderEnvironmentV1
BindActivityPlanningNativeBinderEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  ActivityPlanningNativeBinderEnvironmentV1 output{};
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  output.module_base = module_base;
  output.read_memory = &DirectMemoryRead;
  if (module_base != 0) {
    output.rtti_dynamic_cast =
        reinterpret_cast<ActivityPlanningNativeRttiDynamicCastV1>(
            module_base + kActivityPlanningRttiDynamicCastRvaV1);
  }
  return output;
}

bool ConfigureActivityPlanningNativeBinderV1(
    ActivityPlanningNativeBinderStateV1 &state,
    const ActivityPlanningNativeBinderEnvironmentV1 &environment,
    ActivityPlanningSourceAdapterEnvironmentV1 &source_environment) noexcept {
  if (state.container_active.load(std::memory_order_acquire))
    return false;
  const auto failure = ValidateEnvironment(environment);
  state.environment = environment;
  state.active_token = 0;
  state.active_request = {};
  state.active_sample = {};
  state.definition_key_scratch = {};
  state.can_plan_scratch = {};
  state.projected_locations = {};
  state.projected_costs = {};
  state.projected_options = {};
  SetFailure(state, failure);
  source_environment = {};
  if (failure != ActivityPlanningNativeBinderFailureV1::none)
    return false;
  source_environment.exact_build_admitted = environment.exact_build_admitted;
  source_environment.admitted_executable_sha256 =
      environment.admitted_executable_sha256;
  source_environment.module_base = environment.module_base;
  source_environment.context = &state;
  source_environment.read_frame = &BinderReadFrame;
  source_environment.read_memory = &BinderReadMemory;
  source_environment.resolve_host_view = &BinderResolveHostView;
  source_environment.read_definition_key = &BinderReadDefinitionKey;
  source_environment.invoke_final_can_plan = &BinderInvokeCanPlan;
  source_environment.open_source_container = &BinderOpenSourceContainer;
  source_environment.read_source_container = &BinderReadSourceContainer;
  source_environment.release_source_container = &BinderReleaseSourceContainer;
  return true;
}

ActivityPlanningNativeBinderFailureV1 ReadActivityPlanningNativeBinderFailureV1(
    const ActivityPlanningNativeBinderStateV1 &state) noexcept {
  return static_cast<ActivityPlanningNativeBinderFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

std::string_view ActivityPlanningNativeBinderFailureKeyV1(
    ActivityPlanningNativeBinderFailureV1 failure) noexcept {
  switch (failure) {
  case ActivityPlanningNativeBinderFailureV1::none:
    return "none";
  case ActivityPlanningNativeBinderFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case ActivityPlanningNativeBinderFailureV1::callbacks_missing:
    return "callbacks_missing";
  case ActivityPlanningNativeBinderFailureV1::image_signature_mismatch:
    return "image_signature_mismatch";
  case ActivityPlanningNativeBinderFailureV1::vtable_slot_mismatch:
    return "vtable_slot_mismatch";
  case ActivityPlanningNativeBinderFailureV1::request_invalid:
    return "request_invalid";
  case ActivityPlanningNativeBinderFailureV1::frame_unavailable:
    return "frame_unavailable";
  case ActivityPlanningNativeBinderFailureV1::frame_mismatch:
    return "frame_mismatch";
  case ActivityPlanningNativeBinderFailureV1::owner_path_unavailable:
    return "owner_path_unavailable";
  case ActivityPlanningNativeBinderFailureV1::owner_identity_mismatch:
    return "owner_identity_mismatch";
  case ActivityPlanningNativeBinderFailureV1::host_view_identity_mismatch:
    return "host_view_identity_mismatch";
  case ActivityPlanningNativeBinderFailureV1::activity_type_identity_mismatch:
    return "activity_type_identity_mismatch";
  case ActivityPlanningNativeBinderFailureV1::activity_key_unavailable:
    return "activity_key_unavailable";
  case ActivityPlanningNativeBinderFailureV1::activity_key_mismatch:
    return "activity_key_mismatch";
  case ActivityPlanningNativeBinderFailureV1::final_can_plan_failed:
    return "final_can_plan_failed";
  case ActivityPlanningNativeBinderFailureV1::semantic_read_failed:
    return "semantic_read_failed";
  case ActivityPlanningNativeBinderFailureV1::semantic_sample_invalid:
    return "semantic_sample_invalid";
  case ActivityPlanningNativeBinderFailureV1::semantic_sample_drift:
    return "semantic_sample_drift";
  case ActivityPlanningNativeBinderFailureV1::container_busy:
    return "container_busy";
  case ActivityPlanningNativeBinderFailureV1::container_token_invalid:
    return "container_token_invalid";
  }
  return "unknown";
}

} // namespace xar::bridge

#include "xar_bridge/activity_planning_snapshot_v1_source_adapter.hpp"

#include <cstring>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "activity planning source adapter is x64-only");

template <typename Value>
bool AddRva(std::uintptr_t base, std::uintptr_t rva, Value &output) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = {};
    return false;
  }
  output = static_cast<Value>(base + rva);
  return true;
}

void SetFailure(ActivityPlanningSourceAdapterStateV1 &state,
                ActivityPlanningSourceAdapterFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const ActivityPlanningSourceAdapterEnvironmentV1 &environment,
                std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return environment.read_memory != nullptr && address != 0 &&
         output != nullptr && size != 0 &&
         environment.read_memory(environment.context, address, output, size);
}

template <typename Value>
bool ReadAt(const ActivityPlanningSourceAdapterEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, Value &output) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    return false;
  }
  return ReadMemory(environment, base + offset, &output, sizeof(output));
}

template <std::size_t Capacity>
bool ReadText(const ActivityPlanningSourceAdapterEnvironmentV1 &environment,
              ActivityPlanningSourceStringRefV1 source,
              ActivityPlanningFixedTextV1<Capacity> &output) noexcept {
  output = {};
  if (source.data == 0 || source.size == 0 || source.size >= Capacity ||
      !ReadMemory(environment, source.data, output.bytes.data(), source.size)) {
    return false;
  }
  for (std::uint32_t index = 0; index < source.size; ++index) {
    if (output.bytes[index] == '\0') {
      output = {};
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(source.size);
  return true;
}

template <std::size_t Capacity>
bool TextEquals(const ActivityPlanningFixedTextV1<Capacity> &left,
                const ActivityPlanningFixedTextV1<Capacity> &right) noexcept {
  return left.size == right.size &&
         std::memcmp(left.bytes.data(), right.bytes.data(), left.size) == 0;
}

template <std::size_t Capacity>
bool TextEquals(const ActivityPlanningFixedTextV1<Capacity> &left,
                std::string_view right) noexcept {
  return left.size == right.size() &&
         std::memcmp(left.bytes.data(), right.data(), left.size) == 0;
}

bool TypedBoolEquals(const ActivityPlanningTypedBoolV1 &left,
                     const ActivityPlanningTypedBoolV1 &right) noexcept {
  return left.state == right.state && left.value == right.value &&
         left.unknown_reason == right.unknown_reason;
}

bool TypedIntegerEquals(const ActivityPlanningTypedIntegerV1 &left,
                        const ActivityPlanningTypedIntegerV1 &right) noexcept {
  return left.state == right.state && left.value == right.value &&
         left.unknown_reason == right.unknown_reason;
}

template <std::size_t Capacity>
bool TypedTextEquals(
    const ActivityPlanningTypedTextV1<Capacity> &left,
    const ActivityPlanningTypedTextV1<Capacity> &right) noexcept {
  return left.state == right.state &&
         left.unknown_reason == right.unknown_reason &&
         TextEquals(left.value, right.value);
}

ActivityPlanningTypedBoolV1 KnownBool(bool value) noexcept {
  return {ActivityPlanningFieldStateV1::known, value,
          ActivityPlanningUnknownReasonV1::none};
}

ActivityPlanningTypedIntegerV1 KnownInteger(std::int64_t value) noexcept {
  return {ActivityPlanningFieldStateV1::known, value,
          ActivityPlanningUnknownReasonV1::none};
}

template <std::size_t Capacity>
void SetNotApplicable(ActivityPlanningTypedTextV1<Capacity> &output) noexcept {
  output = {};
  output.state = ActivityPlanningFieldStateV1::unknown;
  output.unknown_reason = ActivityPlanningUnknownReasonV1::not_applicable;
}

bool FrameMatchesRequest(
    const ActivityPlanningFrameIdentityV1 &frame,
    const ActivityPlanningSnapshotRequestV1 &request) noexcept {
  return frame.snapshot_revision == request.expected_snapshot_revision &&
         frame.date_raw == request.expected_date_raw &&
         frame.owner_character_id == request.expected_owner_character_id &&
         frame.application_main_thread && frame.paused && frame.map_ready &&
         frame.owner_alive;
}

ActivityPlanningSourceAdapterFailureV1 ValidateEnvironment(
    const ActivityPlanningSourceAdapterEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kActivityPlanningSourceAdapterExecutableSha256V1) {
    return ActivityPlanningSourceAdapterFailureV1::exact_build_not_admitted;
  }
  if (environment.read_frame == nullptr || environment.read_memory == nullptr ||
      environment.resolve_host_view == nullptr ||
      environment.read_definition_key == nullptr ||
      environment.invoke_final_can_plan == nullptr ||
      environment.open_source_container == nullptr ||
      environment.read_source_container == nullptr ||
      environment.release_source_container == nullptr) {
    return ActivityPlanningSourceAdapterFailureV1::callbacks_missing;
  }
  return ActivityPlanningSourceAdapterFailureV1::none;
}

class ContainerLeaseV1 {
public:
  ContainerLeaseV1(ActivityPlanningSourceAdapterStateV1 &state,
                   std::uintptr_t token) noexcept
      : state_(state), token_(token) {}
  ~ContainerLeaseV1() {
    if (token_ != 0 && !state_.environment.release_source_container(
                           state_.environment.context, token_)) {
      release_failed_ = true;
    }
  }
  ContainerLeaseV1(const ContainerLeaseV1 &) = delete;
  ContainerLeaseV1 &operator=(const ContainerLeaseV1 &) = delete;

  bool Release() noexcept {
    if (token_ == 0)
      return !release_failed_;
    const bool ok = state_.environment.release_source_container(
        state_.environment.context, token_);
    token_ = 0;
    release_failed_ = !ok;
    return ok;
  }

private:
  ActivityPlanningSourceAdapterStateV1 &state_;
  std::uintptr_t token_ = 0;
  bool release_failed_ = false;
};

bool ValidView(const ActivityPlanningSourceContainerViewV1 &view) noexcept {
  return view.location_count <= kActivityPlanningMaximumCandidatesV1 &&
         view.configured_cost_count <=
             kActivityPlanningMaximumConfiguredCostsV1 &&
         view.selected_option_count <=
             kActivityPlanningMaximumSelectedOptionsV1 &&
         (view.location_count == 0 || view.location_rows != 0) &&
         (view.configured_cost_count == 0 || view.configured_cost_rows != 0) &&
         (view.selected_option_count == 0 || view.selected_option_rows != 0) &&
         view.host_intent_key.data != 0 && view.host_intent_key.size != 0 &&
         view.guest_intent_key.data != 0 && view.guest_intent_key.size != 0 &&
         view.invite_rule_key.data != 0 && view.invite_rule_key.size != 0 &&
         view.shown <= 1 && view.can_start <= 1 && view.affordable <= 1 &&
         view.cooldown_active <= 1 && view.cooldown_days_remaining >= 0;
}

template <typename Row>
bool ReadRow(const ActivityPlanningSourceAdapterEnvironmentV1 &environment,
             std::uintptr_t rows, std::uint32_t index, Row &output) noexcept {
  if (index >
      ((std::numeric_limits<std::uintptr_t>::max)() - rows) / sizeof(Row)) {
    return false;
  }
  return ReadMemory(environment, rows + index * sizeof(Row), &output,
                    sizeof(output));
}

ActivityPlanningSourceAdapterFailureV1
ReadRows(const ActivityPlanningSourceAdapterEnvironmentV1 &environment,
         const ActivityPlanningSourceContainerViewV1 &view,
         ActivityPlanningSourceAdapterOwnedSampleV1 &output) noexcept {
  output.candidate_count = static_cast<std::uint16_t>(view.location_count);
  for (std::uint32_t index = 0; index < view.location_count; ++index) {
    ActivityPlanningSourceLocationRowV1 source{};
    if (!ReadRow(environment, view.location_rows, index, source) ||
        source.location_id == 0 || source.selectable > 1) {
      return ActivityPlanningSourceAdapterFailureV1::source_row_unavailable;
    }
    auto &target = output.candidates[index];
    target.location_id = source.location_id;
    target.native_weight_q100000 = source.native_weight_q100000;
    target.selectable = KnownBool(source.selectable != 0);
    if (!ReadText(environment, source.location_key, target.location_key)) {
      return ActivityPlanningSourceAdapterFailureV1::source_text_unavailable;
    }
  }

  output.configured_cost_count =
      static_cast<std::uint16_t>(view.configured_cost_count);
  for (std::uint32_t index = 0; index < view.configured_cost_count; ++index) {
    ActivityPlanningSourceCostRowV1 source{};
    if (!ReadRow(environment, view.configured_cost_rows, index, source) ||
        source.amount_q100000 < 0) {
      return ActivityPlanningSourceAdapterFailureV1::source_row_unavailable;
    }
    auto &target = output.configured_costs[index];
    target.amount_q100000 = source.amount_q100000;
    if (!ReadText(environment, source.resource_key, target.resource_key)) {
      return ActivityPlanningSourceAdapterFailureV1::source_text_unavailable;
    }
  }

  output.selected_option_count =
      static_cast<std::uint16_t>(view.selected_option_count);
  for (std::uint32_t index = 0; index < view.selected_option_count; ++index) {
    ActivityPlanningSourceOptionRowV1 source{};
    if (!ReadRow(environment, view.selected_option_rows, index, source) ||
        !ReadText(environment, source.option_key,
                  output.selected_options[index])) {
      return ActivityPlanningSourceAdapterFailureV1::source_row_unavailable;
    }
  }
  return ActivityPlanningSourceAdapterFailureV1::none;
}

ActivityPlanningSourceAdapterFailureV1
ReadOneSample(ActivityPlanningSourceAdapterStateV1 &state,
              ActivityPlanningSourceAdapterOwnedSampleV1 &output) noexcept {
  output = {};
  auto &environment = state.environment;
  ActivityPlanningFrameIdentityV1 frame_before{};
  if (!environment.read_frame(environment.context, frame_before)) {
    return ActivityPlanningSourceAdapterFailureV1::frame_unavailable;
  }
  if (!FrameMatchesRequest(frame_before, state.request)) {
    return ActivityPlanningSourceAdapterFailureV1::frame_mismatch;
  }

  std::uintptr_t host_view = 0;
  if (!environment.resolve_host_view(environment.context,
                                     state.request.expected_owner_character_id,
                                     state.request.activity_key, host_view) ||
      host_view == 0) {
    return ActivityPlanningSourceAdapterFailureV1::host_view_unavailable;
  }

  std::uintptr_t expected_vtable = 0;
  std::uintptr_t expected_can_plan = 0;
  std::uintptr_t actual_vtable = 0;
  std::uintptr_t actual_can_plan = 0;
  if (!AddRva(environment.module_base,
              kActivityPlanningHostViewPrimaryVtableRvaV1, expected_vtable) ||
      !AddRva(environment.module_base, kActivityPlanningHostViewCanPlanRvaV1,
              expected_can_plan) ||
      !ReadAt(environment, host_view, 0, actual_vtable) ||
      actual_vtable != expected_vtable ||
      !ReadAt(environment, actual_vtable,
              kActivityPlanningHostViewCanPlanVtableSlotV1 *
                  sizeof(std::uintptr_t),
              actual_can_plan) ||
      actual_can_plan != expected_can_plan) {
    return ActivityPlanningSourceAdapterFailureV1::host_view_identity_mismatch;
  }

  std::uintptr_t activity_type = 0;
  if (!ReadAt(environment, host_view,
              kActivityPlanningHostViewActivityTypeOffsetV1, activity_type) ||
      activity_type == 0) {
    return ActivityPlanningSourceAdapterFailureV1::activity_type_unavailable;
  }
  ActivityPlanningSourceStringRefV1 definition_key{};
  if (!environment.read_definition_key(environment.context, activity_type,
                                       definition_key) ||
      !ReadText(environment, definition_key, output.activity_key)) {
    return ActivityPlanningSourceAdapterFailureV1::activity_key_unavailable;
  }
  if (!TextEquals(output.activity_key, state.request.activity_key)) {
    return ActivityPlanningSourceAdapterFailureV1::activity_key_mismatch;
  }

  ActivityPlanningSourceCanPlanResultV1 can_plan{};
  if (!environment.invoke_final_can_plan(environment.context, expected_can_plan,
                                         host_view, state.request, can_plan) ||
      can_plan.value > 1) {
    return ActivityPlanningSourceAdapterFailureV1::final_can_plan_failed;
  }
  output.can_plan_final = KnownBool(can_plan.value != 0);
  if (can_plan.value != 0) {
    SetNotApplicable(output.failure_display_key);
    SetNotApplicable(output.failure_display_text);
  } else {
    output.failure_display_key.state = ActivityPlanningFieldStateV1::known;
    output.failure_display_key.unknown_reason =
        ActivityPlanningUnknownReasonV1::none;
    output.failure_display_text.state = ActivityPlanningFieldStateV1::known;
    output.failure_display_text.unknown_reason =
        ActivityPlanningUnknownReasonV1::none;
    if (!ReadText(environment, can_plan.failure_display_key,
                  output.failure_display_key.value) ||
        !ReadText(environment, can_plan.failure_display_text,
                  output.failure_display_text.value)) {
      return ActivityPlanningSourceAdapterFailureV1::source_text_unavailable;
    }
  }

  std::uintptr_t container_token = 0;
  if (!environment.open_source_container(environment.context, host_view,
                                         activity_type, state.request,
                                         container_token) ||
      container_token == 0) {
    return ActivityPlanningSourceAdapterFailureV1::source_container_unavailable;
  }
  ContainerLeaseV1 lease(state, container_token);
  const auto capture_failure = [&]() noexcept {
    ActivityPlanningSourceContainerViewV1 view_before{};
    if (!environment.read_source_container(environment.context, container_token,
                                           view_before) ||
        !ValidView(view_before)) {
      return ActivityPlanningSourceAdapterFailureV1::source_container_invalid;
    }
    const auto row_failure = ReadRows(environment, view_before, output);
    if (row_failure != ActivityPlanningSourceAdapterFailureV1::none) {
      return row_failure;
    }
    if (!ReadText(environment, view_before.host_intent_key,
                  output.host_intent_key) ||
        !ReadText(environment, view_before.guest_intent_key,
                  output.guest_intent_key) ||
        !ReadText(environment, view_before.invite_rule_key,
                  output.invite_rule_key)) {
      return ActivityPlanningSourceAdapterFailureV1::source_text_unavailable;
    }
    output.shown = KnownBool(view_before.shown != 0);
    output.can_start = KnownBool(view_before.can_start != 0);
    output.affordable = KnownBool(view_before.affordable != 0);
    output.cooldown_active = KnownBool(view_before.cooldown_active != 0);
    output.cooldown_days_remaining =
        KnownInteger(view_before.cooldown_days_remaining);

    ActivityPlanningSourceContainerViewV1 view_after{};
    if (!environment.read_source_container(environment.context, container_token,
                                           view_after) ||
        view_after != view_before) {
      return ActivityPlanningSourceAdapterFailureV1::source_container_drift;
    }
    return ActivityPlanningSourceAdapterFailureV1::none;
  }();
  if (!lease.Release()) {
    return ActivityPlanningSourceAdapterFailureV1::
        source_container_release_failed;
  }
  if (capture_failure != ActivityPlanningSourceAdapterFailureV1::none) {
    return capture_failure;
  }

  ActivityPlanningFrameIdentityV1 frame_after{};
  if (!environment.read_frame(environment.context, frame_after)) {
    return ActivityPlanningSourceAdapterFailureV1::frame_unavailable;
  }
  if (frame_after != frame_before) {
    return ActivityPlanningSourceAdapterFailureV1::frame_mismatch;
  }
  return ActivityPlanningSourceAdapterFailureV1::none;
}

bool SamplesEqual(
    const ActivityPlanningSourceAdapterOwnedSampleV1 &left,
    const ActivityPlanningSourceAdapterOwnedSampleV1 &right) noexcept {
  if (!TextEquals(left.activity_key, right.activity_key) ||
      !TypedBoolEquals(left.shown, right.shown) ||
      !TypedBoolEquals(left.can_plan_final, right.can_plan_final) ||
      !TypedBoolEquals(left.can_start, right.can_start) ||
      !TypedTextEquals(left.failure_display_key, right.failure_display_key) ||
      !TypedTextEquals(left.failure_display_text, right.failure_display_text) ||
      left.candidate_count != right.candidate_count ||
      left.selected_option_count != right.selected_option_count ||
      left.configured_cost_count != right.configured_cost_count ||
      !TextEquals(left.host_intent_key, right.host_intent_key) ||
      !TextEquals(left.guest_intent_key, right.guest_intent_key) ||
      !TextEquals(left.invite_rule_key, right.invite_rule_key) ||
      !TypedBoolEquals(left.affordable, right.affordable) ||
      !TypedBoolEquals(left.cooldown_active, right.cooldown_active) ||
      !TypedIntegerEquals(left.cooldown_days_remaining,
                          right.cooldown_days_remaining)) {
    return false;
  }
  for (std::uint16_t index = 0; index < left.candidate_count; ++index) {
    const auto &a = left.candidates[index];
    const auto &b = right.candidates[index];
    if (a.location_id != b.location_id ||
        !TextEquals(a.location_key, b.location_key) ||
        a.native_weight_q100000 != b.native_weight_q100000 ||
        !TypedBoolEquals(a.selectable, b.selectable)) {
      return false;
    }
  }
  for (std::uint16_t index = 0; index < left.selected_option_count; ++index) {
    if (!TextEquals(left.selected_options[index],
                    right.selected_options[index])) {
      return false;
    }
  }
  for (std::uint16_t index = 0; index < left.configured_cost_count; ++index) {
    const auto &a = left.configured_costs[index];
    const auto &b = right.configured_costs[index];
    if (a.amount_q100000 != b.amount_q100000 ||
        !TextEquals(a.resource_key, b.resource_key)) {
      return false;
    }
  }
  return true;
}

bool AdapterReadFrame(void *context,
                      ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto &state = *static_cast<ActivityPlanningSourceAdapterStateV1 *>(context);
  return state.environment.read_frame != nullptr &&
         state.environment.read_frame(state.environment.context, output);
}

bool AdapterBegin(void *context,
                  const ActivityPlanningSnapshotRequestV1 &request,
                  void *&session) noexcept {
  auto &state = *static_cast<ActivityPlanningSourceAdapterStateV1 *>(context);
  session = nullptr;
  const auto validation = ValidateEnvironment(state.environment);
  if (validation != ActivityPlanningSourceAdapterFailureV1::none) {
    SetFailure(state, validation);
    return false;
  }
  if (request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1 ||
      request.expected_owner_character_id <= 0) {
    SetFailure(state, ActivityPlanningSourceAdapterFailureV1::request_invalid);
    return false;
  }
  bool expected = false;
  if (!state.session_active.compare_exchange_strong(
          expected, true, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    SetFailure(state, ActivityPlanningSourceAdapterFailureV1::session_busy);
    return false;
  }
  state.request = request;
  state.captured = {};
  session = &state;
  SetFailure(state, ActivityPlanningSourceAdapterFailureV1::none);
  return true;
}

bool AdapterRead(void *context, void *session,
                 ActivityPlanningNativeCaptureV1 &output) noexcept {
  auto &state = *static_cast<ActivityPlanningSourceAdapterStateV1 *>(context);
  output = {};
  if (session != &state ||
      !state.session_active.load(std::memory_order_acquire)) {
    SetFailure(state, ActivityPlanningSourceAdapterFailureV1::session_busy);
    return false;
  }
  ActivityPlanningSourceAdapterOwnedSampleV1 first{};
  ActivityPlanningSourceAdapterOwnedSampleV1 second{};
  auto failure = ReadOneSample(state, first);
  if (failure == ActivityPlanningSourceAdapterFailureV1::none) {
    failure = ReadOneSample(state, second);
  }
  if (failure == ActivityPlanningSourceAdapterFailureV1::none &&
      !SamplesEqual(first, second)) {
    failure = ActivityPlanningSourceAdapterFailureV1::source_sample_drift;
  }
  if (failure != ActivityPlanningSourceAdapterFailureV1::none) {
    SetFailure(state, failure);
    return false;
  }
  state.captured = second;
  auto &captured = state.captured;
  output.owner_character_id = state.request.expected_owner_character_id;
  output.activity_key = ActivityPlanningFixedTextViewV1(captured.activity_key);
  output.can_plan_source =
      ActivityPlanningCanPlanSourceV1::host_view_final_can_plan;
  output.shown = {captured.shown.state, captured.shown.value,
                  captured.shown.unknown_reason};
  output.can_plan_final = {captured.can_plan_final.state,
                           captured.can_plan_final.value,
                           captured.can_plan_final.unknown_reason};
  output.can_start = {captured.can_start.state, captured.can_start.value,
                      captured.can_start.unknown_reason};
  output.failure_display_key = {
      captured.failure_display_key.state,
      ActivityPlanningFixedTextViewV1(captured.failure_display_key.value),
      captured.failure_display_key.unknown_reason};
  output.failure_display_text = {
      captured.failure_display_text.state,
      ActivityPlanningFixedTextViewV1(captured.failure_display_text.value),
      captured.failure_display_text.unknown_reason};
  state.projected_candidates = {};
  for (std::uint16_t index = 0; index < captured.candidate_count; ++index) {
    const auto &source = captured.candidates[index];
    state.projected_candidates[index] = {
        source.location_id,
        ActivityPlanningFixedTextViewV1(source.location_key),
        source.native_weight_q100000,
        {source.selectable.state, source.selectable.value,
         source.selectable.unknown_reason}};
  }
  output.candidates = {
      ActivityPlanningFieldStateV1::known,
      ActivityPlanningCandidateSourceV1::native_legal_location_collection,
      state.projected_candidates.data(),
      captured.candidate_count,
      true,
      ActivityPlanningUnknownReasonV1::none};
  output.selected_options = {
      ActivityPlanningFieldStateV1::known,
      ActivityPlanningConfigurationSourceV1::native_selected_configuration,
      nullptr,
      captured.selected_option_count,
      true,
      ActivityPlanningUnknownReasonV1::none};
  static_assert(std::is_trivially_copyable_v<ActivityPlanningStableKeyV1>);
  // These transient views point only into adapter-owned fixed arrays.
  // EndCapture clears them after the observer has deep-copied the capture.
  state.projected_options = {};
  for (std::uint16_t index = 0; index < captured.selected_option_count;
       ++index) {
    state.projected_options[index] =
        ActivityPlanningFixedTextViewV1(captured.selected_options[index]);
  }
  output.selected_options.keys = state.projected_options.data();
  output.host_intent_key = {
      ActivityPlanningFieldStateV1::known,
      ActivityPlanningFixedTextViewV1(captured.host_intent_key),
      ActivityPlanningUnknownReasonV1::none};
  output.guest_intent_key = {
      ActivityPlanningFieldStateV1::known,
      ActivityPlanningFixedTextViewV1(captured.guest_intent_key),
      ActivityPlanningUnknownReasonV1::none};
  output.invite_rule_key = {
      ActivityPlanningFieldStateV1::known,
      ActivityPlanningFixedTextViewV1(captured.invite_rule_key),
      ActivityPlanningUnknownReasonV1::none};
  state.projected_costs = {};
  for (std::uint16_t index = 0; index < captured.configured_cost_count;
       ++index) {
    state.projected_costs[index] = {
        ActivityPlanningFixedTextViewV1(
            captured.configured_costs[index].resource_key),
        captured.configured_costs[index].amount_q100000};
  }
  output.configured_cost = {ActivityPlanningFieldStateV1::known,
                            ActivityPlanningConfiguredCostSourceV1::
                                native_authoritative_configured_cost,
                            state.projected_costs.data(),
                            captured.configured_cost_count,
                            true,
                            ActivityPlanningUnknownReasonV1::none};
  output.affordable = {captured.affordable.state, captured.affordable.value,
                       captured.affordable.unknown_reason};
  output.cooldown_active = {captured.cooldown_active.state,
                            captured.cooldown_active.value,
                            captured.cooldown_active.unknown_reason};
  output.cooldown_days_remaining = {
      captured.cooldown_days_remaining.state,
      captured.cooldown_days_remaining.value,
      captured.cooldown_days_remaining.unknown_reason};
  SetFailure(state, ActivityPlanningSourceAdapterFailureV1::none);
  return true;
}

bool AdapterEnd(void *context, void *session) noexcept {
  auto &state = *static_cast<ActivityPlanningSourceAdapterStateV1 *>(context);
  if (session != &state ||
      !state.session_active.exchange(false, std::memory_order_acq_rel)) {
    SetFailure(state, ActivityPlanningSourceAdapterFailureV1::session_busy);
    return false;
  }
  state.request = {};
  state.captured = {};
  state.projected_candidates = {};
  state.projected_options = {};
  state.projected_costs = {};
  return true;
}

} // namespace

bool ConfigureActivityPlanningSourceAdapterV1(
    ActivityPlanningSourceAdapterStateV1 &state,
    const ActivityPlanningSourceAdapterEnvironmentV1 &source_environment,
    ActivityPlanningSnapshotPrivateEnvironmentV1
        &observer_environment) noexcept {
  if (state.session_active.load(std::memory_order_acquire))
    return false;
  state.environment = source_environment;
  state.request = {};
  state.captured = {};
  state.projected_candidates = {};
  state.projected_options = {};
  state.projected_costs = {};
  SetFailure(state, ActivityPlanningSourceAdapterFailureV1::none);
  observer_environment = {};
  observer_environment.observer_enabled = true;
  observer_environment.exact_build_admitted =
      source_environment.exact_build_admitted;
  observer_environment.admitted_executable_sha256 =
      source_environment.admitted_executable_sha256;
  observer_environment.context = &state;
  observer_environment.read_frame = &AdapterReadFrame;
  observer_environment.begin_capture = &AdapterBegin;
  observer_environment.read_capture = &AdapterRead;
  observer_environment.end_capture = &AdapterEnd;
  return true;
}

ActivityPlanningSourceAdapterFailureV1
ReadActivityPlanningSourceAdapterFailureV1(
    const ActivityPlanningSourceAdapterStateV1 &state) noexcept {
  return static_cast<ActivityPlanningSourceAdapterFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

std::string_view ActivityPlanningSourceAdapterFailureKeyV1(
    ActivityPlanningSourceAdapterFailureV1 failure) noexcept {
  switch (failure) {
  case ActivityPlanningSourceAdapterFailureV1::none:
    return "none";
  case ActivityPlanningSourceAdapterFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case ActivityPlanningSourceAdapterFailureV1::callbacks_missing:
    return "callbacks_missing";
  case ActivityPlanningSourceAdapterFailureV1::request_invalid:
    return "request_invalid";
  case ActivityPlanningSourceAdapterFailureV1::session_busy:
    return "session_busy";
  case ActivityPlanningSourceAdapterFailureV1::frame_unavailable:
    return "frame_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::frame_mismatch:
    return "frame_mismatch";
  case ActivityPlanningSourceAdapterFailureV1::host_view_unavailable:
    return "host_view_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::host_view_identity_mismatch:
    return "host_view_identity_mismatch";
  case ActivityPlanningSourceAdapterFailureV1::activity_type_unavailable:
    return "activity_type_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::activity_key_unavailable:
    return "activity_key_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::activity_key_mismatch:
    return "activity_key_mismatch";
  case ActivityPlanningSourceAdapterFailureV1::final_can_plan_failed:
    return "final_can_plan_failed";
  case ActivityPlanningSourceAdapterFailureV1::source_container_unavailable:
    return "source_container_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::source_container_invalid:
    return "source_container_invalid";
  case ActivityPlanningSourceAdapterFailureV1::source_container_drift:
    return "source_container_drift";
  case ActivityPlanningSourceAdapterFailureV1::source_row_unavailable:
    return "source_row_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::source_text_unavailable:
    return "source_text_unavailable";
  case ActivityPlanningSourceAdapterFailureV1::source_sample_drift:
    return "source_sample_drift";
  case ActivityPlanningSourceAdapterFailureV1::source_container_release_failed:
    return "source_container_release_failed";
  }
  return "unknown";
}

} // namespace xar::bridge

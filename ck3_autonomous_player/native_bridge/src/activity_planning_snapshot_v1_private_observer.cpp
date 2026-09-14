#include "xar_bridge/activity_planning_snapshot_v1_private_observer.hpp"

#include <algorithm>
#include <type_traits>

namespace xar::bridge {
namespace {

template <std::size_t Capacity>
bool CopyText(std::string_view source,
              ActivityPlanningFixedTextV1<Capacity> &output) noexcept {
  output = {};
  if (source.empty() || source.size() >= Capacity ||
      source.find('\0') != std::string_view::npos) {
    return false;
  }
  std::copy(source.begin(), source.end(), output.bytes.begin());
  output.size = static_cast<std::uint16_t>(source.size());
  return true;
}

bool TypedUnknownValid(ActivityPlanningFieldStateV1 state,
                       ActivityPlanningUnknownReasonV1 reason) noexcept {
  return state == ActivityPlanningFieldStateV1::known
             ? reason == ActivityPlanningUnknownReasonV1::none
             : reason != ActivityPlanningUnknownReasonV1::none;
}

bool CopyTypedBool(const ActivityPlanningNativeTypedBoolV1 &source,
                   ActivityPlanningTypedBoolV1 &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  output.state = source.state;
  output.unknown_reason = source.unknown_reason;
  if (source.state == ActivityPlanningFieldStateV1::known) {
    output.value = source.value;
  }
  return true;
}

bool CopyTypedInteger(const ActivityPlanningNativeTypedIntegerV1 &source,
                      ActivityPlanningTypedIntegerV1 &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  output.state = source.state;
  output.unknown_reason = source.unknown_reason;
  if (source.state == ActivityPlanningFieldStateV1::known) {
    output.value = source.value;
  }
  return true;
}

template <std::size_t Capacity>
bool CopyTypedText(const ActivityPlanningNativeTypedTextV1 &source,
                   ActivityPlanningTypedTextV1<Capacity> &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  output.state = source.state;
  output.unknown_reason = source.unknown_reason;
  if (source.state == ActivityPlanningFieldStateV1::known) {
    return CopyText(source.value, output.value);
  }
  return source.value.empty();
}

bool SameKey(const ActivityPlanningStableKeyV1 &left,
             const ActivityPlanningStableKeyV1 &right) noexcept {
  return ActivityPlanningFixedTextViewV1(left) ==
         ActivityPlanningFixedTextViewV1(right);
}

bool CopyCandidates(const ActivityPlanningNativeCandidateCollectionV1 &source,
                    ActivityPlanningCandidateCollectionV1 &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  if (source.state == ActivityPlanningFieldStateV1::unknown) {
    if (source.source != ActivityPlanningCandidateSourceV1::unknown ||
        source.rows != nullptr || source.count != 0 || source.complete) {
      return false;
    }
    output.unknown_reason = source.unknown_reason;
    return true;
  }
  if (source.source !=
          ActivityPlanningCandidateSourceV1::native_legal_location_collection ||
      !source.complete || source.count > kActivityPlanningMaximumCandidatesV1 ||
      (source.count != 0 && source.rows == nullptr)) {
    return false;
  }
  output.state = ActivityPlanningFieldStateV1::known;
  output.source = source.source;
  output.unknown_reason = ActivityPlanningUnknownReasonV1::none;
  output.count = static_cast<std::uint16_t>(source.count);
  for (std::size_t index = 0; index < source.count; ++index) {
    const auto &native = source.rows[index];
    auto &copied = output.rows[index];
    if (native.location_id <= 0 ||
        !CopyText(native.location_key, copied.location_key) ||
        !CopyTypedBool(native.selectable, copied.selectable)) {
      return false;
    }
    copied.location_id = native.location_id;
    copied.native_weight_q100000 = native.native_weight_q100000;
    for (std::size_t previous = 0; previous < index; ++previous) {
      if (output.rows[previous].location_id == copied.location_id ||
          SameKey(output.rows[previous].location_key, copied.location_key)) {
        return false;
      }
    }
  }
  return true;
}

bool CopyConfiguredCosts(
    const ActivityPlanningNativeConfiguredCostCollectionV1 &source,
    ActivityPlanningConfiguredCostCollectionV1 &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  if (source.state == ActivityPlanningFieldStateV1::unknown) {
    if (source.source != ActivityPlanningConfiguredCostSourceV1::unknown ||
        source.rows != nullptr || source.count != 0 || source.complete) {
      return false;
    }
    output.unknown_reason = source.unknown_reason;
    return true;
  }
  if (source.source != ActivityPlanningConfiguredCostSourceV1::
                           native_authoritative_configured_cost ||
      !source.complete ||
      source.count > kActivityPlanningMaximumConfiguredCostsV1 ||
      (source.count != 0 && source.rows == nullptr)) {
    return false;
  }
  output.state = ActivityPlanningFieldStateV1::known;
  output.source = source.source;
  output.unknown_reason = ActivityPlanningUnknownReasonV1::none;
  output.count = static_cast<std::uint16_t>(source.count);
  for (std::size_t index = 0; index < source.count; ++index) {
    const auto &native = source.rows[index];
    auto &copied = output.rows[index];
    if (native.amount_q100000 < 0 ||
        !CopyText(native.resource_key, copied.resource_key)) {
      return false;
    }
    copied.amount_q100000 = native.amount_q100000;
    for (std::size_t previous = 0; previous < index; ++previous) {
      if (SameKey(output.rows[previous].resource_key, copied.resource_key)) {
        return false;
      }
    }
  }
  return true;
}

bool CopySelectedOptions(const ActivityPlanningNativeSelectedOptionsV1 &source,
                         ActivityPlanningSelectedOptionsV1 &output) noexcept {
  output = {};
  if (!TypedUnknownValid(source.state, source.unknown_reason)) return false;
  if (source.state == ActivityPlanningFieldStateV1::unknown) {
    if (source.source != ActivityPlanningConfigurationSourceV1::unknown ||
        source.keys != nullptr || source.count != 0 || source.complete) {
      return false;
    }
    output.unknown_reason = source.unknown_reason;
    return true;
  }
  if (source.source !=
          ActivityPlanningConfigurationSourceV1::native_selected_configuration ||
      !source.complete ||
      source.count > kActivityPlanningMaximumSelectedOptionsV1 ||
      (source.count != 0 && source.keys == nullptr)) {
    return false;
  }
  output.state = ActivityPlanningFieldStateV1::known;
  output.source = source.source;
  output.unknown_reason = ActivityPlanningUnknownReasonV1::none;
  output.count = static_cast<std::uint16_t>(source.count);
  for (std::size_t index = 0; index < source.count; ++index) {
    if (!CopyText(source.keys[index], output.keys[index])) return false;
    for (std::size_t previous = 0; previous < index; ++previous) {
      if (SameKey(output.keys[previous], output.keys[index])) return false;
    }
  }
  return true;
}

bool FrameMatchesRequest(const ActivityPlanningFrameIdentityV1 &frame,
                         const ActivityPlanningSnapshotRequestV1 &request) {
  return frame.snapshot_revision == request.expected_snapshot_revision &&
         frame.date_raw == request.expected_date_raw &&
         frame.owner_character_id == request.expected_owner_character_id;
}

void SetUnavailable(ActivityPlanningSnapshotPrivateV1 &output,
                    ActivityPlanningSnapshotFailureV1 reason) noexcept {
  output = {};
  output.status = ActivityPlanningSnapshotStatusV1::unavailable;
  output.unavailable_reason = reason;
}

bool CopyNativeCapture(const ActivityPlanningNativeCaptureV1 &source,
                       const ActivityPlanningSnapshotRequestV1 &request,
                       ActivityPlanningSnapshotPrivateV1 &output) noexcept {
  if (source.owner_character_id != request.expected_owner_character_id ||
      source.activity_key != request.activity_key ||
      !CopyText(source.activity_key, output.activity_key) ||
      !CopyTypedBool(source.shown, output.shown) ||
      !CopyTypedBool(source.can_plan_final, output.can_plan_final) ||
      !CopyTypedBool(source.can_start, output.can_start) ||
      !CopyTypedText(source.failure_display_key, output.failure_display_key) ||
      !CopyTypedText(source.failure_display_text, output.failure_display_text) ||
      !CopyCandidates(source.candidates, output.candidates) ||
      !CopySelectedOptions(source.selected_options, output.selected_options) ||
      !CopyTypedText(source.host_intent_key, output.host_intent_key) ||
      !CopyTypedText(source.guest_intent_key, output.guest_intent_key) ||
      !CopyTypedText(source.invite_rule_key, output.invite_rule_key) ||
      !CopyConfiguredCosts(source.configured_cost, output.configured_cost) ||
      !CopyTypedBool(source.affordable, output.affordable) ||
      !CopyTypedBool(source.cooldown_active, output.cooldown_active) ||
      !CopyTypedInteger(source.cooldown_days_remaining,
                        output.cooldown_days_remaining)) {
    return false;
  }
  if (source.can_plan_final.state == ActivityPlanningFieldStateV1::known &&
      source.can_plan_source !=
          ActivityPlanningCanPlanSourceV1::host_view_final_can_plan) {
    return false;
  }
  if (source.can_plan_final.state == ActivityPlanningFieldStateV1::unknown &&
      source.can_plan_source != ActivityPlanningCanPlanSourceV1::unknown) {
    return false;
  }
  output.can_plan_source = source.can_plan_source;
  return true;
}

bool TypedKnown(const ActivityPlanningTypedBoolV1 &value) noexcept {
  return value.state == ActivityPlanningFieldStateV1::known;
}

bool TypedKnown(const ActivityPlanningTypedIntegerV1 &value) noexcept {
  return value.state == ActivityPlanningFieldStateV1::known;
}

template <std::size_t Capacity>
bool TypedKnown(const ActivityPlanningTypedTextV1<Capacity> &value) noexcept {
  return value.state == ActivityPlanningFieldStateV1::known;
}

void ComputeReadiness(ActivityPlanningSnapshotPrivateV1 &output) noexcept {
  auto &ready = output.readiness;
  ready.same_frame_ready = true;
  ready.final_can_plan_ready =
      TypedKnown(output.can_plan_final) &&
      output.can_plan_source ==
          ActivityPlanningCanPlanSourceV1::host_view_final_can_plan;
  ready.candidate_inputs_ready =
      output.candidates.state == ActivityPlanningFieldStateV1::known &&
      output.candidates.source == ActivityPlanningCandidateSourceV1::
                                      native_legal_location_collection;
  ready.configured_cost_ready =
      output.configured_cost.state == ActivityPlanningFieldStateV1::known &&
      output.configured_cost.source == ActivityPlanningConfiguredCostSourceV1::
                                           native_authoritative_configured_cost &&
      TypedKnown(output.affordable);
  ready.configuration_keys_ready =
      output.selected_options.state == ActivityPlanningFieldStateV1::known &&
      TypedKnown(output.host_intent_key) && TypedKnown(output.guest_intent_key) &&
      TypedKnown(output.invite_rule_key);
  ready.action_inputs_ready =
      ready.final_can_plan_ready && output.can_plan_final.value &&
      TypedKnown(output.shown) && output.shown.value &&
      TypedKnown(output.can_start) && output.can_start.value &&
      ready.candidate_inputs_ready && ready.configured_cost_ready &&
      ready.configuration_keys_ready && TypedKnown(output.cooldown_active) &&
      TypedKnown(output.cooldown_days_remaining);
  ready.raw_pointer_fields_persisted = false;
}

void AppendEscaped(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char ch : value) {
    switch (ch) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (ch >= 0x20) output.push_back(static_cast<char>(ch));
      break;
    }
  }
  output.push_back('"');
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendTypedBool(std::string &output,
                     const ActivityPlanningTypedBoolV1 &value) {
  output += "{\"state\":\"";
  output += value.state == ActivityPlanningFieldStateV1::known ? "known" :
                                                                  "unknown";
  output += '"';
  if (value.state == ActivityPlanningFieldStateV1::known) {
    output += ",\"value\":";
    AppendBool(output, value.value);
  } else {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(value.unknown_reason);
    output += '"';
  }
  output += '}';
}

void AppendTypedInteger(std::string &output,
                        const ActivityPlanningTypedIntegerV1 &value) {
  output += "{\"state\":\"";
  output += value.state == ActivityPlanningFieldStateV1::known ? "known" :
                                                                  "unknown";
  output += '"';
  if (value.state == ActivityPlanningFieldStateV1::known) {
    output += ",\"value\":" + std::to_string(value.value);
  } else {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(value.unknown_reason);
    output += '"';
  }
  output += '}';
}

template <std::size_t Capacity>
void AppendTypedText(std::string &output,
                     const ActivityPlanningTypedTextV1<Capacity> &value) {
  output += "{\"state\":\"";
  output += value.state == ActivityPlanningFieldStateV1::known ? "known" :
                                                                  "unknown";
  output += '"';
  if (value.state == ActivityPlanningFieldStateV1::known) {
    output += ",\"value\":";
    AppendEscaped(output, ActivityPlanningFixedTextViewV1(value.value));
  } else {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(value.unknown_reason);
    output += '"';
  }
  output += '}';
}

std::string_view CandidateSourceKey(ActivityPlanningCandidateSourceV1 value) {
  switch (value) {
  case ActivityPlanningCandidateSourceV1::unknown: return "unknown";
  case ActivityPlanningCandidateSourceV1::native_legal_location_collection:
    return "native_legal_location_collection";
  }
  return "unknown";
}

std::string_view CanPlanSourceKey(ActivityPlanningCanPlanSourceV1 value) {
  switch (value) {
  case ActivityPlanningCanPlanSourceV1::unknown: return "unknown";
  case ActivityPlanningCanPlanSourceV1::host_view_final_can_plan:
    return "host_view_final_can_plan";
  }
  return "unknown";
}

std::string_view ConfigurationSourceKey(
    ActivityPlanningConfigurationSourceV1 value) {
  switch (value) {
  case ActivityPlanningConfigurationSourceV1::unknown: return "unknown";
  case ActivityPlanningConfigurationSourceV1::native_selected_configuration:
    return "native_selected_configuration";
  }
  return "unknown";
}

std::string_view ConfiguredCostSourceKey(
    ActivityPlanningConfiguredCostSourceV1 value) {
  switch (value) {
  case ActivityPlanningConfiguredCostSourceV1::unknown: return "unknown";
  case ActivityPlanningConfiguredCostSourceV1::
      native_authoritative_configured_cost:
    return "native_authoritative_configured_cost";
  case ActivityPlanningConfiguredCostSourceV1::ui_predicted_cost:
    return "ui_predicted_cost";
  }
  return "unknown";
}

} // namespace

static_assert(
    std::is_trivially_copyable_v<ActivityPlanningSnapshotPrivateV1>,
    "the private activity snapshot must own copied values only");

std::string_view ActivityPlanningSnapshotFailureKeyV1(
    ActivityPlanningSnapshotFailureV1 value) noexcept {
  switch (value) {
  case ActivityPlanningSnapshotFailureV1::none: return "none";
  case ActivityPlanningSnapshotFailureV1::observer_disabled:
    return "observer_disabled";
  case ActivityPlanningSnapshotFailureV1::unsupported_build:
    return "unsupported_build";
  case ActivityPlanningSnapshotFailureV1::callbacks_missing:
    return "callbacks_missing";
  case ActivityPlanningSnapshotFailureV1::request_invalid:
    return "request_invalid";
  case ActivityPlanningSnapshotFailureV1::frame_unavailable:
    return "frame_unavailable";
  case ActivityPlanningSnapshotFailureV1::requires_application_main:
    return "requires_application_main";
  case ActivityPlanningSnapshotFailureV1::requires_paused:
    return "requires_paused";
  case ActivityPlanningSnapshotFailureV1::owner_unavailable:
    return "owner_unavailable";
  case ActivityPlanningSnapshotFailureV1::frame_changed:
    return "frame_changed";
  case ActivityPlanningSnapshotFailureV1::provider_failed:
    return "provider_failed";
  case ActivityPlanningSnapshotFailureV1::invalid_native_capture:
    return "invalid_native_capture";
  }
  return "invalid_native_capture";
}

std::string_view ActivityPlanningUnknownReasonKeyV1(
    ActivityPlanningUnknownReasonV1 value) noexcept {
  switch (value) {
  case ActivityPlanningUnknownReasonV1::none: return "none";
  case ActivityPlanningUnknownReasonV1::not_observed: return "not_observed";
  case ActivityPlanningUnknownReasonV1::not_applicable: return "not_applicable";
  case ActivityPlanningUnknownReasonV1::native_final_evaluator_unresolved:
    return "native_final_evaluator_unresolved";
  case ActivityPlanningUnknownReasonV1::native_stable_key_unresolved:
    return "native_stable_key_unresolved";
  case ActivityPlanningUnknownReasonV1::native_candidate_collection_unresolved:
    return "native_candidate_collection_unresolved";
  case ActivityPlanningUnknownReasonV1::native_configured_cost_unresolved:
    return "native_configured_cost_unresolved";
  case ActivityPlanningUnknownReasonV1::native_configuration_unresolved:
    return "native_configuration_unresolved";
  case ActivityPlanningUnknownReasonV1::provider_unavailable:
    return "provider_unavailable";
  }
  return "provider_unavailable";
}

bool ReadActivityPlanningSnapshotPrivateObserverV1(
    const ActivityPlanningSnapshotPrivateEnvironmentV1 &environment,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningSnapshotPrivateV1 &output) noexcept {
  SetUnavailable(output, ActivityPlanningSnapshotFailureV1::observer_disabled);
  if (!environment.observer_enabled) return false;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kActivityPlanningSnapshotExecutableSha256V1) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::unsupported_build);
    return false;
  }
  if (environment.context == nullptr || environment.read_frame == nullptr ||
      environment.begin_capture == nullptr ||
      environment.read_capture == nullptr || environment.end_capture == nullptr) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::callbacks_missing);
    return false;
  }
  if (request.expected_snapshot_revision == 0 ||
      request.expected_owner_character_id <= 0 ||
      request.activity_key != kActivityPlanningSnapshotP0ActivityKeyV1) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::request_invalid);
    return false;
  }

  ActivityPlanningFrameIdentityV1 before{};
  if (!environment.read_frame(environment.context, before)) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::frame_unavailable);
    return false;
  }
  if (!before.application_main_thread) {
    SetUnavailable(output,
                   ActivityPlanningSnapshotFailureV1::requires_application_main);
    return false;
  }
  if (!before.paused) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::requires_paused);
    return false;
  }
  if (!before.map_ready || !before.owner_alive ||
      before.owner_character_id <= 0) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::owner_unavailable);
    return false;
  }
  if (!FrameMatchesRequest(before, request)) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::frame_changed);
    return false;
  }

  void *session = nullptr;
  if (!environment.begin_capture(environment.context, request, session) ||
      session == nullptr) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::provider_failed);
    return false;
  }
  ActivityPlanningNativeCaptureV1 native{};
  const bool captured =
      environment.read_capture(environment.context, session, native);
  ActivityPlanningSnapshotPrivateV1 candidate{};
  const bool copied = captured && CopyNativeCapture(native, request, candidate);
  const bool ended = environment.end_capture(environment.context, session);

  ActivityPlanningFrameIdentityV1 after{};
  if (!ended || !environment.read_frame(environment.context, after)) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::provider_failed);
    return false;
  }
  if (after != before || !FrameMatchesRequest(after, request)) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::frame_changed);
    return false;
  }
  if (!captured) {
    SetUnavailable(output, ActivityPlanningSnapshotFailureV1::provider_failed);
    return false;
  }
  if (!copied) {
    SetUnavailable(output,
                   ActivityPlanningSnapshotFailureV1::invalid_native_capture);
    return false;
  }

  candidate.status = ActivityPlanningSnapshotStatusV1::available;
  candidate.unavailable_reason = ActivityPlanningSnapshotFailureV1::none;
  candidate.snapshot_revision = before.snapshot_revision;
  candidate.date_raw = before.date_raw;
  candidate.owner_character_id = before.owner_character_id;
  ComputeReadiness(candidate);
  output = candidate;
  return true;
}

std::string SerializeActivityPlanningSnapshotPrivateObserverV1(
    const ActivityPlanningSnapshotPrivateV1 &snapshot) {
  std::string output;
  output.reserve(4096);
  output += "{\"private_build\":true,\"read_only\":true,";
  output += "\"advertised\":false,\"schema\":\"";
  output += kActivityPlanningSnapshotPrivateSchemaV1;
  output += "\",\"schema_version\":1,\"status\":\"";
  output += snapshot.status == ActivityPlanningSnapshotStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"unavailable_reason\":\"";
  output += ActivityPlanningSnapshotFailureKeyV1(snapshot.unavailable_reason);
  output += "\",\"exact_build\":{\"game_version\":\"";
  output += kActivityPlanningSnapshotGameVersionV1;
  output += "\",\"executable_sha256\":\"";
  output += kActivityPlanningSnapshotExecutableSha256V1;
  output += "\"},\"snapshot_revision\":" +
            std::to_string(snapshot.snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(snapshot.date_raw);
  output += ",\"owner_character_id\":" +
            std::to_string(snapshot.owner_character_id);
  output += ",\"activity_key\":";
  AppendEscaped(output, ActivityPlanningFixedTextViewV1(snapshot.activity_key));
  output += ",\"can_plan_source\":\"";
  output += CanPlanSourceKey(snapshot.can_plan_source);
  output += '"';
  output += ",\"shown\":";
  AppendTypedBool(output, snapshot.shown);
  output += ",\"can_plan_final\":";
  AppendTypedBool(output, snapshot.can_plan_final);
  output += ",\"can_start\":";
  AppendTypedBool(output, snapshot.can_start);
  output += ",\"failure_display_key\":";
  AppendTypedText(output, snapshot.failure_display_key);
  output += ",\"failure_display_text\":";
  AppendTypedText(output, snapshot.failure_display_text);

  output += ",\"candidates\":{\"state\":\"";
  output += snapshot.candidates.state == ActivityPlanningFieldStateV1::known
                ? "known"
                : "unknown";
  output += "\",\"source\":\"";
  output += CandidateSourceKey(snapshot.candidates.source);
  output += '"';
  if (snapshot.candidates.state == ActivityPlanningFieldStateV1::unknown) {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(
        snapshot.candidates.unknown_reason);
    output += '"';
  }
  output += ",\"rows\":[";
  for (std::uint16_t index = 0; index < snapshot.candidates.count; ++index) {
    if (index != 0) output += ',';
    const auto &row = snapshot.candidates.rows[index];
    output += "{\"location_id\":" + std::to_string(row.location_id);
    output += ",\"location_key\":";
    AppendEscaped(output, ActivityPlanningFixedTextViewV1(row.location_key));
    output += ",\"native_weight_q100000\":" +
              std::to_string(row.native_weight_q100000);
    output += ",\"selectable\":";
    AppendTypedBool(output, row.selectable);
    output += '}';
  }
  output += "]}";

  output += ",\"selected_options\":{\"state\":\"";
  output += snapshot.selected_options.state == ActivityPlanningFieldStateV1::known
                ? "known"
                : "unknown";
  output += "\",\"source\":\"";
  output += ConfigurationSourceKey(snapshot.selected_options.source);
  output += "\",\"keys\":[";
  for (std::uint16_t index = 0; index < snapshot.selected_options.count;
       ++index) {
    if (index != 0) output += ',';
    AppendEscaped(output,
                  ActivityPlanningFixedTextViewV1(
                      snapshot.selected_options.keys[index]));
  }
  output += ']';
  if (snapshot.selected_options.state == ActivityPlanningFieldStateV1::unknown) {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(
        snapshot.selected_options.unknown_reason);
    output += '"';
  }
  output += '}';
  output += ",\"host_intent_key\":";
  AppendTypedText(output, snapshot.host_intent_key);
  output += ",\"guest_intent_key\":";
  AppendTypedText(output, snapshot.guest_intent_key);
  output += ",\"invite_rule_key\":";
  AppendTypedText(output, snapshot.invite_rule_key);

  output += ",\"configured_cost\":{\"state\":\"";
  output += snapshot.configured_cost.state == ActivityPlanningFieldStateV1::known
                ? "known"
                : "unknown";
  output += "\",\"source\":\"";
  output += ConfiguredCostSourceKey(snapshot.configured_cost.source);
  output += '"';
  if (snapshot.configured_cost.state == ActivityPlanningFieldStateV1::unknown) {
    output += ",\"unavailable_reason\":\"";
    output += ActivityPlanningUnknownReasonKeyV1(
        snapshot.configured_cost.unknown_reason);
    output += '"';
  }
  output += ",\"rows\":[";
  for (std::uint16_t index = 0; index < snapshot.configured_cost.count;
       ++index) {
    if (index != 0) output += ',';
    const auto &row = snapshot.configured_cost.rows[index];
    output += "{\"resource_key\":";
    AppendEscaped(output, ActivityPlanningFixedTextViewV1(row.resource_key));
    output += ",\"amount_q100000\":" +
              std::to_string(row.amount_q100000) + '}';
  }
  output += "]}";
  output += ",\"affordable\":";
  AppendTypedBool(output, snapshot.affordable);
  output += ",\"cooldown_active\":";
  AppendTypedBool(output, snapshot.cooldown_active);
  output += ",\"cooldown_days_remaining\":";
  AppendTypedInteger(output, snapshot.cooldown_days_remaining);
  output += ",\"readiness\":{\"same_frame_ready\":";
  AppendBool(output, snapshot.readiness.same_frame_ready);
  output += ",\"final_can_plan_ready\":";
  AppendBool(output, snapshot.readiness.final_can_plan_ready);
  output += ",\"candidate_inputs_ready\":";
  AppendBool(output, snapshot.readiness.candidate_inputs_ready);
  output += ",\"configured_cost_ready\":";
  AppendBool(output, snapshot.readiness.configured_cost_ready);
  output += ",\"configuration_keys_ready\":";
  AppendBool(output, snapshot.readiness.configuration_keys_ready);
  output += ",\"action_inputs_ready\":";
  AppendBool(output, snapshot.readiness.action_inputs_ready);
  output += ",\"raw_pointer_fields_persisted\":";
  AppendBool(output, snapshot.readiness.raw_pointer_fields_persisted);
  output += "}}";
  return output;
}

} // namespace xar::bridge

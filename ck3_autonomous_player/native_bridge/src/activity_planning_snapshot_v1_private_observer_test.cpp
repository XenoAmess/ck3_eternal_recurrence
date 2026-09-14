#include "xar_bridge/activity_planning_snapshot_v1_private_observer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace {

using namespace xar::bridge;

ActivityPlanningNativeTypedBoolV1 Known(bool value) {
  return {ActivityPlanningFieldStateV1::known, value,
          ActivityPlanningUnknownReasonV1::none};
}

ActivityPlanningNativeTypedBoolV1 UnknownBool(
    ActivityPlanningUnknownReasonV1 reason) {
  return {ActivityPlanningFieldStateV1::unknown, false, reason};
}

ActivityPlanningNativeTypedIntegerV1 KnownInteger(std::int64_t value) {
  return {ActivityPlanningFieldStateV1::known, value,
          ActivityPlanningUnknownReasonV1::none};
}

ActivityPlanningNativeTypedIntegerV1 UnknownInteger(
    ActivityPlanningUnknownReasonV1 reason) {
  return {ActivityPlanningFieldStateV1::unknown, 0, reason};
}

ActivityPlanningNativeTypedTextV1 KnownText(std::string_view value) {
  return {ActivityPlanningFieldStateV1::known, value,
          ActivityPlanningUnknownReasonV1::none};
}

ActivityPlanningNativeTypedTextV1 UnknownText(
    ActivityPlanningUnknownReasonV1 reason) {
  return {ActivityPlanningFieldStateV1::unknown, {}, reason};
}

struct Fixture {
  ActivityPlanningFrameIdentityV1 frame{
      42, 777, 12345, true, true, true, true};
  std::string activity_key{"activity_feast"};
  std::string failure_key{"activity_feast_can_plan_failure"};
  std::string failure_text{"A feast is unavailable."};
  std::array<std::string, 2> location_keys{"province_101", "province_202"};
  std::array<std::string, 2> option_keys{"activity_option_food_normal",
                                         "activity_option_drink_normal"};
  std::string host_intent{"reduce_stress_intent"};
  std::string guest_intent{"reduce_stress_intent"};
  std::string invite_rule{"activity_invite_rule_default"};
  std::array<std::string, 2> resource_keys{"gold", "piety"};
  std::array<ActivityPlanningNativeCandidateV1, 2> candidates{};
  std::array<std::string_view, 2> selected_options{};
  std::array<ActivityPlanningNativeConfiguredCostV1, 2> costs{};
  ActivityPlanningNativeCaptureV1 capture{};
  std::uint32_t begin_count = 0;
  std::uint32_t read_count = 0;
  std::uint32_t end_count = 0;
  bool fail_begin = false;
  bool fail_read = false;
  bool fail_end = false;
  bool drift_after_read = false;
  bool mutate_transient_storage_on_end = true;

  Fixture() { SetAvailable(); }

  void SetAvailable() {
    candidates = {
        ActivityPlanningNativeCandidateV1{101, location_keys[0], 150000,
                                          Known(true)},
        ActivityPlanningNativeCandidateV1{202, location_keys[1], 50000,
                                          Known(false)},
    };
    selected_options = {option_keys[0], option_keys[1]};
    costs = {
        ActivityPlanningNativeConfiguredCostV1{resource_keys[0], 12500000},
        ActivityPlanningNativeConfiguredCostV1{resource_keys[1], 250000},
    };
    capture = {};
    capture.owner_character_id = frame.owner_character_id;
    capture.activity_key = activity_key;
    capture.can_plan_source =
        ActivityPlanningCanPlanSourceV1::host_view_final_can_plan;
    capture.shown = Known(true);
    capture.can_plan_final = Known(true);
    capture.can_start = Known(true);
    capture.failure_display_key =
        UnknownText(ActivityPlanningUnknownReasonV1::not_applicable);
    capture.failure_display_text =
        UnknownText(ActivityPlanningUnknownReasonV1::not_applicable);
    capture.candidates = {
        ActivityPlanningFieldStateV1::known,
        ActivityPlanningCandidateSourceV1::native_legal_location_collection,
        candidates.data(), candidates.size(), true,
        ActivityPlanningUnknownReasonV1::none};
    capture.selected_options = {
        ActivityPlanningFieldStateV1::known,
        ActivityPlanningConfigurationSourceV1::native_selected_configuration,
        selected_options.data(), selected_options.size(), true,
        ActivityPlanningUnknownReasonV1::none};
    capture.host_intent_key = KnownText(host_intent);
    capture.guest_intent_key = KnownText(guest_intent);
    capture.invite_rule_key = KnownText(invite_rule);
    capture.configured_cost = {
        ActivityPlanningFieldStateV1::known,
        ActivityPlanningConfiguredCostSourceV1::
            native_authoritative_configured_cost,
        costs.data(), costs.size(), true,
        ActivityPlanningUnknownReasonV1::none};
    capture.affordable = Known(true);
    capture.cooldown_active = Known(false);
    capture.cooldown_days_remaining = KnownInteger(0);
  }

  void SetKnownBlocked() {
    capture.can_plan_source =
        ActivityPlanningCanPlanSourceV1::host_view_final_can_plan;
    capture.shown = Known(true);
    capture.can_plan_final = Known(false);
    capture.can_start = Known(false);
    capture.failure_display_key = KnownText(failure_key);
    capture.failure_display_text = KnownText(failure_text);
    capture.candidates = {
        ActivityPlanningFieldStateV1::unknown,
        ActivityPlanningCandidateSourceV1::unknown, nullptr, 0, false,
        ActivityPlanningUnknownReasonV1::
            native_candidate_collection_unresolved};
    capture.selected_options = {
        ActivityPlanningFieldStateV1::unknown,
        ActivityPlanningConfigurationSourceV1::unknown, nullptr, 0, false,
        ActivityPlanningUnknownReasonV1::native_configuration_unresolved};
    capture.host_intent_key = UnknownText(
        ActivityPlanningUnknownReasonV1::native_configuration_unresolved);
    capture.guest_intent_key = UnknownText(
        ActivityPlanningUnknownReasonV1::native_configuration_unresolved);
    capture.invite_rule_key = UnknownText(
        ActivityPlanningUnknownReasonV1::native_configuration_unresolved);
    capture.configured_cost = {
        ActivityPlanningFieldStateV1::unknown,
        ActivityPlanningConfiguredCostSourceV1::unknown, nullptr, 0, false,
        ActivityPlanningUnknownReasonV1::native_configured_cost_unresolved};
    capture.affordable = UnknownBool(
        ActivityPlanningUnknownReasonV1::native_configured_cost_unresolved);
    capture.cooldown_active = Known(true);
    capture.cooldown_days_remaining = KnownInteger(365);
  }

  void SetUnresolvedEvaluator() {
    SetKnownBlocked();
    capture.can_plan_source = ActivityPlanningCanPlanSourceV1::unknown;
    capture.can_plan_final = UnknownBool(
        ActivityPlanningUnknownReasonV1::native_final_evaluator_unresolved);
    capture.failure_display_key = UnknownText(
        ActivityPlanningUnknownReasonV1::native_final_evaluator_unresolved);
    capture.failure_display_text = UnknownText(
        ActivityPlanningUnknownReasonV1::native_final_evaluator_unresolved);
    capture.cooldown_active = UnknownBool(
        ActivityPlanningUnknownReasonV1::native_stable_key_unresolved);
    capture.cooldown_days_remaining = UnknownInteger(
        ActivityPlanningUnknownReasonV1::native_stable_key_unresolved);
  }
};

bool ReadFrame(void *context,
               ActivityPlanningFrameIdentityV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool BeginCapture(void *context,
                  const ActivityPlanningSnapshotRequestV1 &request,
                  void *&session) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.begin_count;
  if (fixture.fail_begin ||
      request.expected_owner_character_id != fixture.frame.owner_character_id) {
    session = nullptr;
    return false;
  }
  session = &fixture;
  return true;
}

bool ReadCapture(void *context, void *session,
                 ActivityPlanningNativeCaptureV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.read_count;
  if (fixture.fail_read || session != &fixture) return false;
  output = fixture.capture;
  return true;
}

bool EndCapture(void *context, void *session) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.end_count;
  if (session != &fixture || fixture.fail_end) return false;
  if (fixture.mutate_transient_storage_on_end) {
    fixture.location_keys[0] = "corrupted_location";
    fixture.option_keys[0] = "corrupted_option";
    fixture.resource_keys[0] = "corrupted_resource";
    fixture.host_intent = "corrupted_intent";
  }
  if (fixture.drift_after_read) ++fixture.frame.snapshot_revision;
  return true;
}

ActivityPlanningSnapshotPrivateEnvironmentV1 Environment(Fixture &fixture) {
  ActivityPlanningSnapshotPrivateEnvironmentV1 environment{};
  environment.observer_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      kActivityPlanningSnapshotExecutableSha256V1;
  environment.context = &fixture;
  environment.read_frame = &ReadFrame;
  environment.begin_capture = &BeginCapture;
  environment.read_capture = &ReadCapture;
  environment.end_capture = &EndCapture;
  return environment;
}

ActivityPlanningSnapshotRequestV1 Request(const Fixture &fixture) {
  return {fixture.frame.snapshot_revision, fixture.frame.date_raw,
          fixture.frame.owner_character_id,
          kActivityPlanningSnapshotP0ActivityKeyV1};
}

void TestDefaultOffAndExactBuildAdmission() {
  Fixture fixture{};
  auto environment = Environment(fixture);
  ActivityPlanningSnapshotPrivateV1 output{};
  environment.observer_enabled = false;
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      environment, Request(fixture), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::observer_disabled);
  assert(fixture.begin_count == 0);

  environment.observer_enabled = true;
  environment.admitted_executable_sha256 =
      "0000000000000000000000000000000000000000000000000000000000000000";
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      environment, Request(fixture), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::unsupported_build);

  environment = Environment(fixture);
  environment.read_capture = nullptr;
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      environment, Request(fixture), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::callbacks_missing);
}

void TestClosedFeastInputsAreDeepCopiedAndPointerFree() {
  static_assert(
      std::is_trivially_copyable_v<ActivityPlanningSnapshotPrivateV1>);
  Fixture fixture{};
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(fixture), Request(fixture), output));
  assert(fixture.begin_count == 1 && fixture.read_count == 1 &&
         fixture.end_count == 1);
  assert(output.status == ActivityPlanningSnapshotStatusV1::available);
  assert(output.unavailable_reason == ActivityPlanningSnapshotFailureV1::none);
  assert(output.owner_character_id == 12345);
  assert(ActivityPlanningFixedTextViewV1(output.activity_key) ==
         "activity_feast");
  assert(output.can_plan_source ==
         ActivityPlanningCanPlanSourceV1::host_view_final_can_plan);
  assert(output.can_plan_final.state == ActivityPlanningFieldStateV1::known &&
         output.can_plan_final.value);
  assert(output.candidates.count == 2);
  assert(output.candidates.rows[0].location_id == 101);
  assert(ActivityPlanningFixedTextViewV1(
             output.candidates.rows[0].location_key) == "province_101");
  assert(output.candidates.rows[0].native_weight_q100000 == 150000);
  assert(output.selected_options.count == 2);
  assert(ActivityPlanningFixedTextViewV1(output.selected_options.keys[0]) ==
         "activity_option_food_normal");
  assert(ActivityPlanningFixedTextViewV1(output.host_intent_key.value) ==
         "reduce_stress_intent");
  assert(output.configured_cost.count == 2);
  assert(ActivityPlanningFixedTextViewV1(
             output.configured_cost.rows[0].resource_key) == "gold");
  assert(output.configured_cost.rows[0].amount_q100000 == 12500000);
  assert(output.readiness.same_frame_ready);
  assert(output.readiness.final_can_plan_ready);
  assert(output.readiness.candidate_inputs_ready);
  assert(output.readiness.configured_cost_ready);
  assert(output.readiness.configuration_keys_ready);
  assert(output.readiness.action_inputs_ready);
  assert(!output.readiness.raw_pointer_fields_persisted);

  const std::string json =
      SerializeActivityPlanningSnapshotPrivateObserverV1(output);
  assert(json.find("\"private_build\":true") != std::string::npos);
  assert(json.find("\"read_only\":true") != std::string::npos);
  assert(json.find("\"advertised\":false") != std::string::npos);
  assert(json.find("\"can_plan_final\":{\"state\":\"known\",\"value\":true}") !=
         std::string::npos);
  assert(json.find("native_authoritative_configured_cost") !=
         std::string::npos);
  assert(json.find("province_101") != std::string::npos);
  assert(json.find("corrupted_location") == std::string::npos);
  assert(json.find("corrupted_resource") == std::string::npos);
  assert(json.find("ui_predicted_cost") == std::string::npos);
  assert(json.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
}

void TestKnownFalseAndTypedUnknownInputsRemainDistinct() {
  Fixture fixture{};
  fixture.SetKnownBlocked();
  fixture.mutate_transient_storage_on_end = false;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(fixture), Request(fixture), output));
  assert(output.readiness.final_can_plan_ready);
  assert(!output.can_plan_final.value);
  assert(!output.readiness.candidate_inputs_ready);
  assert(!output.readiness.configured_cost_ready);
  assert(!output.readiness.action_inputs_ready);
  assert(output.candidates.state == ActivityPlanningFieldStateV1::unknown);
  assert(output.candidates.unknown_reason ==
         ActivityPlanningUnknownReasonV1::
             native_candidate_collection_unresolved);
  assert(output.configured_cost.unknown_reason ==
         ActivityPlanningUnknownReasonV1::native_configured_cost_unresolved);
  assert(ActivityPlanningFixedTextViewV1(output.failure_display_key.value) ==
         "activity_feast_can_plan_failure");

  const std::string json =
      SerializeActivityPlanningSnapshotPrivateObserverV1(output);
  assert(json.find("native_candidate_collection_unresolved") !=
         std::string::npos);
  assert(json.find("native_configured_cost_unresolved") !=
         std::string::npos);
  assert(json.find("\"value\":null") == std::string::npos);
}

void TestUnresolvedFinalEvaluatorIsTypedUnknown() {
  Fixture fixture{};
  fixture.SetUnresolvedEvaluator();
  fixture.mutate_transient_storage_on_end = false;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(fixture), Request(fixture), output));
  assert(output.status == ActivityPlanningSnapshotStatusV1::available);
  assert(!output.readiness.final_can_plan_ready);
  assert(output.can_plan_final.state == ActivityPlanningFieldStateV1::unknown);
  assert(output.can_plan_final.unknown_reason ==
         ActivityPlanningUnknownReasonV1::
             native_final_evaluator_unresolved);
  const std::string json =
      SerializeActivityPlanningSnapshotPrivateObserverV1(output);
  assert(json.find(
             "\"can_plan_final\":{\"state\":\"unknown\",\"unavailable_reason\":\"native_final_evaluator_unresolved\"}") !=
         std::string::npos);
}

void TestFrameDriftRejectsOtherwiseValidCapture() {
  Fixture fixture{};
  fixture.drift_after_read = true;
  fixture.mutate_transient_storage_on_end = false;
  const auto request = Request(fixture);
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(fixture), request, output));
  assert(output.status == ActivityPlanningSnapshotStatusV1::unavailable);
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::frame_changed);
  assert(fixture.end_count == 1);
  assert(!output.readiness.same_frame_ready);
}

void TestFinalSourceAndAuthoritativeCostCannotBeSubstituted() {
  Fixture missing_final{};
  missing_final.capture.can_plan_source =
      ActivityPlanningCanPlanSourceV1::unknown;
  missing_final.mutate_transient_storage_on_end = false;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(missing_final), Request(missing_final), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::invalid_native_capture);

  Fixture predicted_cost{};
  predicted_cost.capture.configured_cost.source =
      ActivityPlanningConfiguredCostSourceV1::ui_predicted_cost;
  predicted_cost.mutate_transient_storage_on_end = false;
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(predicted_cost), Request(predicted_cost), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::invalid_native_capture);

  Fixture incomplete_candidates{};
  incomplete_candidates.capture.candidates.complete = false;
  incomplete_candidates.mutate_transient_storage_on_end = false;
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(incomplete_candidates), Request(incomplete_candidates),
      output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::invalid_native_capture);
}

void TestProviderFailureStillReleasesSession() {
  Fixture fixture{};
  fixture.fail_read = true;
  fixture.mutate_transient_storage_on_end = false;
  ActivityPlanningSnapshotPrivateV1 output{};
  assert(!ReadActivityPlanningSnapshotPrivateObserverV1(
      Environment(fixture), Request(fixture), output));
  assert(output.unavailable_reason ==
         ActivityPlanningSnapshotFailureV1::provider_failed);
  assert(fixture.begin_count == 1 && fixture.read_count == 1 &&
         fixture.end_count == 1);
}

} // namespace

int main() {
  TestDefaultOffAndExactBuildAdmission();
  TestClosedFeastInputsAreDeepCopiedAndPointerFree();
  TestKnownFalseAndTypedUnknownInputsRemainDistinct();
  TestUnresolvedFinalEvaluatorIsTypedUnknown();
  TestFrameDriftRejectsOtherwiseValidCapture();
  TestFinalSourceAndAuthoritativeCostCannotBeSubstituted();
  TestProviderFailureStillReleasesSession();
  return 0;
}

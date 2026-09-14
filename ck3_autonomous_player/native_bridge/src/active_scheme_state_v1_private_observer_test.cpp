#include "xar_bridge/active_scheme_state_v1_private_observer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <cassert>
#include <string_view>

namespace {

using Capture = xar::bridge::ActiveSchemeStateV1PrivateCapture;
using Failure = xar::bridge::ActiveSchemeStateV1PrivateFailure;
using Observation = xar::bridge::ActiveSchemeStateV1PrivateObservation;
using Row = xar::bridge::ActiveSchemeStateV1PrivateCapturedRow;
using TargetKind = xar::bridge::ActiveSchemeStateV1PrivateTargetKind;
using ValueStatus = xar::bridge::ActiveSchemeStateV1PrivateValueStatus;

template <std::size_t Size>
void SetKey(std::array<char, Size> &output, std::string_view key) {
  assert(key.size() + 1 <= output.size());
  output.fill('\0');
  std::copy(key.begin(), key.end(), output.begin());
}

template <typename T>
void SetAvailable(xar::bridge::ActiveSchemeStateV1PrivateValue<T> &output,
                  T value) {
  output.status = ValueStatus::available;
  output.value = value;
}

Row ComplexMurder() {
  Row row{};
  row.scheme_identity_round_trip = true;
  row.scheme_instance_id = 456;
  row.scheme_instance_generation = 7;
  row.owner_character_id = 123;
  SetKey(row.scheme_type_key, "murder");
  SetKey(row.category_key, "hostile");
  row.target_identity_round_trip = true;
  row.target_kind = TargetKind::character;
  row.target_id = 789;
  row.definition_flags_verified = true;
  row.is_secret = true;
  SetAvailable(row.progress, 6);
  SetAvailable(row.progress_goal, 10);
  SetAvailable(row.success_chance, 63);
  SetAvailable(row.maximum_success_chance, 95);
  SetAvailable(row.secrecy, 72);
  SetAvailable(row.opportunity_charges, 2);
  SetAvailable(row.breaches, 1);
  SetAvailable(row.maximum_breaches, 5);
  SetAvailable(row.phases_remaining_until_opportunity, 1);
  return row;
}

Row BasicSway() {
  Row row{};
  row.scheme_identity_round_trip = true;
  row.scheme_instance_id = 457;
  row.scheme_instance_generation = 2;
  row.owner_character_id = 123;
  SetKey(row.scheme_type_key, "sway");
  SetKey(row.category_key, "personal");
  row.target_identity_round_trip = true;
  row.target_kind = TargetKind::character;
  row.target_id = 790;
  row.definition_flags_verified = true;
  row.is_basic = true;
  SetAvailable(row.progress, 3);
  SetAvailable(row.progress_goal, 10);
  return row;
}

Capture StableCapture() {
  Capture capture{};
  capture.exact_build_admitted = true;
  capture.admitted_executable_sha256 = xar::bridge::
      kActiveSchemeStateV1PrivateObserverExecutableSha256;
  capture.source_adapter_bound = true;
  capture.application_main_thread = true;
  capture.paused = true;
  capture.capture_epoch_before = 44;
  capture.capture_epoch_after = 44;
  capture.date_raw_before = 53183856;
  capture.date_raw_after = 53183856;
  capture.played_character_id_before = 123;
  capture.played_character_id_after = 123;
  capture.container_identity_round_trip = true;
  capture.container_identity_before = 9001;
  capture.container_identity_after = 9001;
  capture.container_generation_before = 11;
  capture.container_generation_after = 11;
  capture.row_count_before = 2;
  capture.row_count_after = 2;
  capture.enumeration_complete = true;
  capture.rows[0] = ComplexMurder();
  capture.rows[1] = BasicSway();
  return capture;
}

void ExpectFailure(const Capture &capture, Failure reason) {
  Observation observation{};
  observation.status =
      xar::bridge::ActiveSchemeStateV1PrivateStatus::available;
  observation.row_count = 1;
  observation.rows[0].scheme_instance_id = 999;
  assert(!xar::bridge::ObserveActiveSchemeStateV1Private(capture,
                                                         observation));
  assert(observation.status ==
         xar::bridge::ActiveSchemeStateV1PrivateStatus::unavailable);
  assert(observation.unavailable_reason == reason);
  assert(observation.row_count == 0);
  assert(observation.rows[0].scheme_instance_id == 0);
  assert(!xar::bridge::ActiveSchemeStateV1PrivateFailureName(reason).empty());
}

void TestComplexAndBasicObservation() {
  const auto capture = StableCapture();
  Observation observation{};
  assert(xar::bridge::ObserveActiveSchemeStateV1Private(capture,
                                                        observation));
  assert(observation.status ==
         xar::bridge::ActiveSchemeStateV1PrivateStatus::available);
  assert(observation.unavailable_reason == Failure::none);
  assert(observation.capture_epoch == 44);
  assert(observation.date_raw == 53183856);
  assert(observation.played_character_id == 123);
  assert(observation.row_count == 2);

  const auto &murder = observation.rows[0];
  assert(murder.scheme_instance_id == 456);
  assert(murder.scheme_instance_generation == 7);
  assert(std::string_view(murder.scheme_type_key.data()) == "murder");
  assert(murder.target_kind == TargetKind::character);
  assert(murder.target_id == 789);
  assert(murder.progress.status == ValueStatus::available);
  assert(murder.progress.value == 6);
  assert(murder.progress_goal.value == 10);
  assert(murder.success_chance.value == 63);
  assert(murder.maximum_success_chance.value == 95);
  assert(murder.secrecy.value == 72);
  assert(murder.opportunity_charges.value == 2);
  assert(murder.breaches.value == 1);
  assert(murder.maximum_breaches.value == 5);
  assert(murder.phases_remaining_until_opportunity.value == 1);

  const auto &sway = observation.rows[1];
  assert(sway.is_basic);
  assert(sway.progress.status == ValueStatus::available);
  assert(sway.success_chance.status == ValueStatus::not_applicable);
  assert(sway.maximum_success_chance.status ==
         ValueStatus::not_applicable);
  assert(sway.secrecy.status == ValueStatus::not_applicable);
  assert(sway.opportunity_charges.status == ValueStatus::not_applicable);
  assert(sway.breaches.status == ValueStatus::not_applicable);
  assert(sway.maximum_breaches.status == ValueStatus::not_applicable);
  assert(sway.phases_remaining_until_opportunity.status ==
         ValueStatus::not_applicable);
}

void TestUnknownSourceAndWrongBuildFailClosed() {
  auto capture = StableCapture();
  capture.source_adapter_bound = false;
  ExpectFailure(capture, Failure::source_adapter_unavailable);
  capture.source_adapter_bound = true;
  capture.admitted_executable_sha256 = "wrong";
  ExpectFailure(capture, Failure::exact_build_mismatch);
}

void TestSameFrameAndEnumerationGates() {
  auto capture = StableCapture();
  capture.capture_epoch_after++;
  ExpectFailure(capture, Failure::frame_drift);

  capture = StableCapture();
  capture.container_generation_after++;
  ExpectFailure(capture, Failure::container_drift);

  capture = StableCapture();
  capture.enumeration_complete = false;
  ExpectFailure(capture, Failure::enumeration_incomplete);
}

void TestIdentityAndOwnershipGates() {
  auto capture = StableCapture();
  capture.rows[0].target_identity_round_trip = false;
  ExpectFailure(capture, Failure::target_unavailable);

  capture = StableCapture();
  capture.rows[1].scheme_instance_id = capture.rows[0].scheme_instance_id;
  capture.rows[1].scheme_instance_generation =
      capture.rows[0].scheme_instance_generation;
  ExpectFailure(capture, Failure::duplicate_scheme_identity);

  capture = StableCapture();
  capture.rows[1].owner_character_id = 999;
  ExpectFailure(capture, Failure::owner_mismatch);

  capture = StableCapture();
  capture.rows[0].scheme_identity_round_trip = false;
  ExpectFailure(capture, Failure::scheme_identity_unavailable);

  capture = StableCapture();
  SetKey(capture.rows[0].scheme_type_key, "Murder");
  ExpectFailure(capture, Failure::scheme_type_unavailable);

  capture = StableCapture();
  SetKey(capture.rows[0].category_key, "future_category");
  ExpectFailure(capture, Failure::scheme_category_unavailable);

  capture = StableCapture();
  capture.rows[0].target_kind = static_cast<TargetKind>(255);
  ExpectFailure(capture, Failure::target_unavailable);

  capture = StableCapture();
  capture.rows[0].target_kind = TargetKind::title;
  capture.rows[0].target_id = 42;
  Observation observation{};
  assert(xar::bridge::ObserveActiveSchemeStateV1Private(capture,
                                                        observation));
  assert(observation.rows[0].target_kind == TargetKind::title);
  assert(observation.rows[0].target_id == 42);
}

void TestMetricsFailClosed() {
  auto capture = StableCapture();
  capture.rows[0].secrecy.status = ValueStatus::unavailable;
  ExpectFailure(capture, Failure::metric_unavailable);

  capture = StableCapture();
  capture.rows[0].success_chance.value = 101;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].maximum_success_chance.value = 62;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].progress.value = -1;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].progress_goal.value = 0;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].secrecy.value = -1;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].opportunity_charges.value = -1;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].breaches.value = 6;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  capture.rows[0].phases_remaining_until_opportunity.value = -1;
  ExpectFailure(capture, Failure::metric_invalid);

  capture = StableCapture();
  SetAvailable(capture.rows[1].secrecy, 0);
  ExpectFailure(capture, Failure::basic_metric_claimed_available);

  capture = StableCapture();
  capture.rows[1].secrecy.status = static_cast<ValueStatus>(255);
  ExpectFailure(capture, Failure::basic_metric_claimed_available);

  capture = StableCapture();
  capture.rows[1].secrecy.status = ValueStatus::not_applicable;
  Observation observation{};
  assert(xar::bridge::ObserveActiveSchemeStateV1Private(capture,
                                                        observation));
  assert(observation.rows[1].secrecy.status ==
         ValueStatus::not_applicable);
}

void TestCompleteEmptyContainerIsAvailable() {
  auto capture = StableCapture();
  capture.row_count_before = 0;
  capture.row_count_after = 0;
  Observation observation{};
  assert(xar::bridge::ObserveActiveSchemeStateV1Private(capture,
                                                        observation));
  assert(observation.row_count == 0);
  assert(observation.status ==
         xar::bridge::ActiveSchemeStateV1PrivateStatus::available);
}

} // namespace

int main() {
  TestComplexAndBasicObservation();
  TestUnknownSourceAndWrongBuildFailClosed();
  TestSameFrameAndEnumerationGates();
  TestIdentityAndOwnershipGates();
  TestMetricsFailClosed();
  TestCompleteEmptyContainerIsAvailable();
  return 0;
}

#include "xar_bridge/active_scheme_state_v1_private_observer.hpp"

#include <algorithm>

namespace xar::bridge {
namespace {

using Failure = ActiveSchemeStateV1PrivateFailure;
using Observation = ActiveSchemeStateV1PrivateObservation;
using ValueStatus = ActiveSchemeStateV1PrivateValueStatus;

void SetUnavailable(Observation &output, Failure reason) noexcept {
  output = {};
  output.status = ActiveSchemeStateV1PrivateStatus::unavailable;
  output.unavailable_reason = reason;
}

template <std::size_t Size>
bool ValidKey(const std::array<char, Size> &key) noexcept {
  const auto end = std::find(key.begin(), key.end(), '\0');
  if (end == key.begin() || end == key.end()) return false;
  for (auto current = key.begin(); current != end; ++current) {
    const auto byte = static_cast<unsigned char>(*current);
    const bool lowercase = byte >= static_cast<unsigned char>('a') &&
                           byte <= static_cast<unsigned char>('z');
    const bool digit = byte >= static_cast<unsigned char>('0') &&
                       byte <= static_cast<unsigned char>('9');
    if (!lowercase && !digit && byte != static_cast<unsigned char>('_')) {
      return false;
    }
  }
  return true;
}

template <std::size_t Size>
bool KeyEquals(const std::array<char, Size> &key,
               std::string_view expected) noexcept {
  if (expected.size() >= key.size()) return false;
  return std::equal(expected.begin(), expected.end(), key.begin()) &&
         key[expected.size()] == '\0';
}

bool KnownCategory(
    const std::array<char, kActiveSchemeStateV1PrivateCategoryKeyCapacity>
        &category) noexcept {
  return KeyEquals(category, "personal") || KeyEquals(category, "contract") ||
         KeyEquals(category, "hostile");
}

bool AvailableInRange(const ActiveSchemeStateV1PrivateValue<std::int32_t> &v,
                      std::int32_t minimum,
                      std::int32_t maximum) noexcept {
  return v.status == ValueStatus::available && v.value >= minimum &&
         v.value <= maximum;
}

bool AvailableNonnegative(
    const ActiveSchemeStateV1PrivateValue<std::int32_t> &v) noexcept {
  return v.status == ValueStatus::available && v.value >= 0;
}

bool BasicOnlyMetricsUnavailable(
    const ActiveSchemeStateV1PrivateCapturedRow &row) noexcept {
  const auto known_absent = [](const auto &value) noexcept {
    return value.status == ValueStatus::unavailable ||
           value.status == ValueStatus::not_applicable;
  };
  return known_absent(row.success_chance) &&
         known_absent(row.maximum_success_chance) &&
         known_absent(row.secrecy) && known_absent(row.opportunity_charges) &&
         known_absent(row.breaches) && known_absent(row.maximum_breaches) &&
         known_absent(row.phases_remaining_until_opportunity);
}

template <typename T>
void SetNotApplicable(ActiveSchemeStateV1PrivateValue<T> &value) noexcept {
  value = {};
  value.status = ValueStatus::not_applicable;
}

bool SameIdentity(const ActiveSchemeStateV1PrivateCapturedRow &left,
                  const ActiveSchemeStateV1PrivateCapturedRow &right) noexcept {
  return left.scheme_instance_id == right.scheme_instance_id &&
         left.scheme_instance_generation == right.scheme_instance_generation;
}

} // namespace

bool ObserveActiveSchemeStateV1Private(
    const ActiveSchemeStateV1PrivateCapture &capture,
    ActiveSchemeStateV1PrivateObservation &output) noexcept {
  SetUnavailable(output, Failure::source_adapter_unavailable);
  if (!capture.exact_build_admitted ||
      capture.admitted_executable_sha256 !=
          kActiveSchemeStateV1PrivateObserverExecutableSha256) {
    SetUnavailable(output, Failure::exact_build_mismatch);
    return false;
  }
  if (!capture.source_adapter_bound) return false;
  if (!capture.application_main_thread) {
    SetUnavailable(output, Failure::not_application_main_thread);
    return false;
  }
  if (!capture.paused) {
    SetUnavailable(output, Failure::not_paused);
    return false;
  }
  if (capture.capture_epoch_before == 0 ||
      capture.capture_epoch_before != capture.capture_epoch_after ||
      capture.date_raw_before != capture.date_raw_after) {
    SetUnavailable(output, Failure::frame_drift);
    return false;
  }
  if (capture.played_character_id_before <= 0 ||
      capture.played_character_id_before !=
          capture.played_character_id_after) {
    SetUnavailable(output, Failure::played_character_unavailable);
    return false;
  }
  if (!capture.container_identity_round_trip ||
      capture.container_identity_before == 0 ||
      capture.container_generation_before == 0) {
    SetUnavailable(output, Failure::container_identity_unavailable);
    return false;
  }
  if (capture.container_identity_before != capture.container_identity_after ||
      capture.container_generation_before !=
          capture.container_generation_after ||
      capture.row_count_before != capture.row_count_after) {
    SetUnavailable(output, Failure::container_drift);
    return false;
  }
  if (!capture.enumeration_complete) {
    SetUnavailable(output, Failure::enumeration_incomplete);
    return false;
  }
  if (capture.row_count_after > capture.rows.size()) {
    SetUnavailable(output, Failure::row_count_invalid);
    return false;
  }

  Observation candidate{};
  candidate.status = ActiveSchemeStateV1PrivateStatus::available;
  candidate.unavailable_reason = Failure::none;
  candidate.capture_epoch = capture.capture_epoch_after;
  candidate.date_raw = capture.date_raw_after;
  candidate.played_character_id = capture.played_character_id_after;
  candidate.container_generation = capture.container_generation_after;
  candidate.row_count = capture.row_count_after;

  for (std::size_t index = 0; index < candidate.row_count; ++index) {
    const auto &source = capture.rows[index];
    if (!source.scheme_identity_round_trip ||
        source.scheme_instance_id == 0 ||
        source.scheme_instance_generation == 0) {
      SetUnavailable(output, Failure::scheme_identity_unavailable);
      return false;
    }
    for (std::size_t prior = 0; prior < index; ++prior) {
      if (SameIdentity(source, capture.rows[prior])) {
        SetUnavailable(output, Failure::duplicate_scheme_identity);
        return false;
      }
    }
    if (source.owner_character_id != candidate.played_character_id) {
      SetUnavailable(output, Failure::owner_mismatch);
      return false;
    }
    if (!ValidKey(source.scheme_type_key)) {
      SetUnavailable(output, Failure::scheme_type_unavailable);
      return false;
    }
    if (!ValidKey(source.category_key) ||
        !KnownCategory(source.category_key)) {
      SetUnavailable(output, Failure::scheme_category_unavailable);
      return false;
    }
    if (!source.target_identity_round_trip || source.target_id <= 0 ||
        (source.target_kind !=
             ActiveSchemeStateV1PrivateTargetKind::character &&
         source.target_kind != ActiveSchemeStateV1PrivateTargetKind::title)) {
      SetUnavailable(output, Failure::target_unavailable);
      return false;
    }
    if (!source.definition_flags_verified) {
      SetUnavailable(output, Failure::definition_flags_unavailable);
      return false;
    }
    if (source.progress.status != ValueStatus::available ||
        source.progress_goal.status != ValueStatus::available) {
      SetUnavailable(output, Failure::metric_unavailable);
      return false;
    }
    if (!AvailableInRange(source.progress, 0, 10) ||
        !AvailableInRange(source.progress_goal, 1, 10) ||
        source.progress.value > source.progress_goal.value) {
      SetUnavailable(output, Failure::metric_invalid);
      return false;
    }

    auto &target = candidate.rows[index];
    target.scheme_instance_id = source.scheme_instance_id;
    target.scheme_instance_generation = source.scheme_instance_generation;
    target.owner_character_id = source.owner_character_id;
    target.scheme_type_key = source.scheme_type_key;
    target.category_key = source.category_key;
    target.target_kind = source.target_kind;
    target.target_id = source.target_id;
    target.is_basic = source.is_basic;
    target.is_secret = source.is_secret;
    target.is_exposed = source.is_exposed;
    target.is_frozen = source.is_frozen;
    target.progress = source.progress;
    target.progress_goal = source.progress_goal;

    if (source.is_basic) {
      if (!BasicOnlyMetricsUnavailable(source)) {
        SetUnavailable(output, Failure::basic_metric_claimed_available);
        return false;
      }
      SetNotApplicable(target.success_chance);
      SetNotApplicable(target.maximum_success_chance);
      SetNotApplicable(target.secrecy);
      SetNotApplicable(target.opportunity_charges);
      SetNotApplicable(target.breaches);
      SetNotApplicable(target.maximum_breaches);
      SetNotApplicable(target.phases_remaining_until_opportunity);
      continue;
    }

    const bool metrics_available =
        source.success_chance.status == ValueStatus::available &&
        source.maximum_success_chance.status == ValueStatus::available &&
        source.secrecy.status == ValueStatus::available &&
        source.opportunity_charges.status == ValueStatus::available &&
        source.breaches.status == ValueStatus::available &&
        source.maximum_breaches.status == ValueStatus::available &&
        source.phases_remaining_until_opportunity.status ==
            ValueStatus::available;
    if (!metrics_available) {
      SetUnavailable(output, Failure::metric_unavailable);
      return false;
    }
    const bool metrics_valid =
        AvailableInRange(source.success_chance, 0, 100) &&
        AvailableInRange(source.maximum_success_chance, 0, 100) &&
        source.success_chance.value <=
            source.maximum_success_chance.value &&
        AvailableInRange(source.secrecy, 0, 100) &&
        AvailableNonnegative(source.opportunity_charges) &&
        AvailableNonnegative(source.breaches) &&
        AvailableNonnegative(source.maximum_breaches) &&
        source.breaches.value <= source.maximum_breaches.value &&
        AvailableNonnegative(source.phases_remaining_until_opportunity);
    if (!metrics_valid) {
      SetUnavailable(output, Failure::metric_invalid);
      return false;
    }
    target.success_chance = source.success_chance;
    target.maximum_success_chance = source.maximum_success_chance;
    target.secrecy = source.secrecy;
    target.opportunity_charges = source.opportunity_charges;
    target.breaches = source.breaches;
    target.maximum_breaches = source.maximum_breaches;
    target.phases_remaining_until_opportunity =
        source.phases_remaining_until_opportunity;
  }

  output = candidate;
  return true;
}

std::string_view ActiveSchemeStateV1PrivateFailureName(
    ActiveSchemeStateV1PrivateFailure failure) noexcept {
  switch (failure) {
  case Failure::none:
    return "none";
  case Failure::exact_build_mismatch:
    return "exact_build_mismatch";
  case Failure::source_adapter_unavailable:
    return "source_adapter_unavailable";
  case Failure::not_application_main_thread:
    return "not_application_main_thread";
  case Failure::not_paused:
    return "not_paused";
  case Failure::frame_drift:
    return "frame_drift";
  case Failure::played_character_unavailable:
    return "played_character_unavailable";
  case Failure::container_identity_unavailable:
    return "container_identity_unavailable";
  case Failure::container_drift:
    return "container_drift";
  case Failure::enumeration_incomplete:
    return "enumeration_incomplete";
  case Failure::row_count_invalid:
    return "row_count_invalid";
  case Failure::scheme_identity_unavailable:
    return "scheme_identity_unavailable";
  case Failure::duplicate_scheme_identity:
    return "duplicate_scheme_identity";
  case Failure::owner_mismatch:
    return "owner_mismatch";
  case Failure::scheme_type_unavailable:
    return "scheme_type_unavailable";
  case Failure::scheme_category_unavailable:
    return "scheme_category_unavailable";
  case Failure::target_unavailable:
    return "target_unavailable";
  case Failure::definition_flags_unavailable:
    return "definition_flags_unavailable";
  case Failure::metric_unavailable:
    return "metric_unavailable";
  case Failure::metric_invalid:
    return "metric_invalid";
  case Failure::basic_metric_claimed_available:
    return "basic_metric_claimed_available";
  }
  return "unknown";
}

} // namespace xar::bridge

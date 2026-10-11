#pragma once
#include "xar_bridge/first_heir_during_read_diagnostic_v1.hpp"

namespace xar::bridge_detail {
// The original result-admission conjunction, with its first failing predicate
// named. Route is evaluated only after the same ordered common predicates.
// Callbacks retain the production JSON/native operations and their order.
template<class Read, class Route>
inline std::string ObservedHeirMarriageAdmissionErrorV1(
    bool revision_parsed, std::uint64_t expected_revision,
    std::uint64_t native_revision,
    const std::optional<game::Snapshot> &previous, game::Snapshot &before,
    Read &&read, Route &&route) {
  bool read_completed = false;
  std::uint64_t read_sequence = 0;
  std::string_view guard;
  if (!revision_parsed) guard = "revision_parse_failed";
  else if (expected_revision != native_revision) guard = "revision_mismatch";
  else if (!previous.has_value()) guard = "previous_snapshot_missing";
  else {
    read_sequence = bridge::ck3_12004::CaptureSnapshotReadSequence12004();
    read_completed = read(before);
    if (!read_completed) guard = "snapshot_read_failed";
    else if (before != *previous) guard = "full_snapshot_changed";
    else if (!before.paused) guard = "not_paused";
    else if (!before.map_ready) guard = "map_not_ready";
    else guard = route();
  }
  if (guard.empty()) return {};

  std::string error = "observed-heir marriage result needs a later paused frame";
  error += "; admission_guard=";
  error += guard;
  error += "; expected_revision=";
  error += revision_parsed ? std::to_string(expected_revision) : "unknown";
  error += "; native_revision=" + std::to_string(native_revision);
  error += "; snapshot_read_completed=";
  error += read_completed ? "true" : "false";
  if (guard == "snapshot_read_failed") {
    if (const auto receipt =
        bridge::ck3_12004::FreshSnapshotReadFailure12004(read_sequence))
      error += bridge::ck3_12004::FormatSnapshotReadFailure12004(*receipt);
  } else if (guard == "full_snapshot_changed") {
    error += "; differing_fields=";
    error += FirstHeirSnapshotDifferenceNamesV1(*previous, before);
  }
  error += "; cached=";
  error += previous.has_value() ? FirstHeirSnapshotDiagnosticScalarsV1(*previous) : "unknown";
  error += "; observed=";
  error += read_completed ? FirstHeirSnapshotDiagnosticScalarsV1(before) : "unknown";
  error += "; complex_field_values=presence_or_count_only";
  return error;
}
} // namespace xar::bridge_detail

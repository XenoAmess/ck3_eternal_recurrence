#pragma once
#include "xar_bridge/first_heir_pre_read_diagnostic_v1.hpp"
#include "xar_bridge/snapshot_read_failure_diagnostics_12004.hpp"
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge_detail {
// The production during-read guard, in its original short-circuit order.
// Read runs once; diagnostics use only the already owned before/after DTOs.
// An empty error admits exactly the former success branch.
template<class Read, class Failure>
inline std::string FirstHeirDuringReadErrorV1(
    const game::Snapshot &before, game::Snapshot &after, Read &&read,
    Failure read_failure, Failure frame_changed,
    std::uint64_t expected_revision, std::uint64_t native_revision,
    std::int32_t heir_character_id) {
  const auto read_sequence = bridge::ck3_12004::CaptureSnapshotReadSequence12004();
  const bool read_completed = read(after);
  std::string_view guard;
  if (!read_completed) guard = "snapshot_read_failed";
  else if (after != before) guard = "full_snapshot_changed";
  else if (read_failure == frame_changed) guard = "relationship_frame_changed";
  else return {};

  std::string error = "current first-heir relationship frame changed during read";
  error += "; during_read_guard=";
  error += guard;
  error += "; snapshot_read_completed=";
  error += read_completed ? "true" : "false";
  error += "; expected_revision=" + std::to_string(expected_revision);
  error += "; native_revision=" + std::to_string(native_revision);
  error += "; heir_character_id=" + std::to_string(heir_character_id);
  error += "; relationship_failure_raw=" +
      std::to_string(static_cast<std::uint64_t>(read_failure));
  if (!read_completed) {
    if (const auto receipt =
        bridge::ck3_12004::FreshSnapshotReadFailure12004(read_sequence))
      error += bridge::ck3_12004::FormatSnapshotReadFailure12004(*receipt);
  } else if (after != before) {
    error += "; differing_fields=";
    error += FirstHeirSnapshotDifferenceNamesV1(before, after);
  }
  error += "; before=" + FirstHeirSnapshotDiagnosticScalarsV1(before);
  error += "; after=";
  error += read_completed ? FirstHeirSnapshotDiagnosticScalarsV1(after) : "unknown";
  error += "; complex_field_values=presence_or_count_only";
  return error;
}
} // namespace xar::bridge_detail

#pragma once
#include "xar_bridge/snapshot_read_failure_diagnostics_12004.hpp"

namespace xar::bridge::ck3_12004 {
// Called only after the existing war-admission ReadSnapshot returned false.
// Descriptor matching uses caller-owned metadata; this does not read the game.
inline std::string FormatWarAdmissionSnapshotFailureChannelV1(
    bool actual4_descriptor, std::uint64_t before_sequence) {
  const auto after_sequence = CaptureSnapshotReadSequence12004();
  const auto receipt = FreshSnapshotReadFailure12004(before_sequence);
  auto text = std::string(" actual4_descriptor=") +
      (actual4_descriptor ? "true" : "false") +
      " read_sequence_before=" + std::to_string(before_sequence) +
      " read_sequence_after=" + std::to_string(after_sequence) +
      " fresh_read_failure=" + (receipt ? "true" : "false");
  if (receipt) {
    text += FormatSnapshotReadFailure12004(*receipt);
  } else {
    text += " read_stage=unknown diagnostic_receipt=";
    if (after_sequence == before_sequence)
      text += "sequence_unchanged";
    else if (after_sequence != before_sequence + std::uint64_t{1})
      text += "sequence_not_single_attempt";
    else
      text += "single_attempt_without_failure_stage";
  }
  return text;
}
// The same owned diagnostic channel is also used by the Nonwar caller.
// This alias performs no additional read and preserves exact Fresh semantics.
inline std::string FormatSnapshotReadFailureChannel12004(
    bool actual4_descriptor, std::uint64_t before_sequence) {
  return FormatWarAdmissionSnapshotFailureChannelV1(
      actual4_descriptor, before_sequence);
}
} // namespace xar::bridge::ck3_12004

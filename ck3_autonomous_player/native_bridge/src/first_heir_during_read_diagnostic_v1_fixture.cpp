#include "xar_bridge/first_heir_during_read_diagnostic_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include <iostream>
#include <string_view>

namespace {
using Failure = xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1;
using xar::bridge_detail::FirstHeirDuringReadErrorV1;
namespace diagnostic = xar::bridge::ck3_12004;
bool Contains(const std::string &text, std::string_view value) {
  return text.find(value) != std::string::npos;
}
}

int main() {
  xar::game::Snapshot before{};
  before.date_raw = 53290176;
  before.paused = before.map_ready = before.has_played_character =
      before.played_character_alive = true;
  before.played_character_id = 29829;
  xar::game::Snapshot after{};
  int calls = 0;
  const auto same_read = [&](xar::game::Snapshot &out) {
    ++calls; out = before; return true;
  };
  auto error = FirstHeirDuringReadErrorV1(before, after, same_read,
      Failure::none, Failure::frame_changed, 2, 2, 38822);
  if (!error.empty() || calls != 1) return 1;

  calls = 0;
  error = FirstHeirDuringReadErrorV1(before, after,
      [&](xar::game::Snapshot &out) {
        ++calls; out = {}; diagnostic::BeginSnapshotReadAttempt12004();
        diagnostic::CopySnapshotReadPrefix12004(53290176, 5, 0, true, true,
            true, 29829, true);
        diagnostic::RecordSnapshotReadFailure12004(
            diagnostic::SnapshotReadFailureStage12004::world, std::uint32_t{2});
        return false;
      }, Failure::frame_changed, Failure::frame_changed, 2, 2, 38822);
  if (calls != 1 || !Contains(error, "during_read_guard=snapshot_read_failed") ||
      !Contains(error, "read_stage=world") || !Contains(error, "after=unknown") ||
      !Contains(error, "expected_revision=2; native_revision=2") ||
      !Contains(error, "relationship_failure_raw=1") ||
      Contains(error, "differing_fields=")) return 2;

  calls = 0;
  error = FirstHeirDuringReadErrorV1(before, after,
      [&](xar::game::Snapshot &out) {
        ++calls; out = before; out.date_raw += 24;
        out.played_character_id = 29830; return true;
      }, Failure::frame_changed, Failure::frame_changed, 2, 2, 38822);
  if (calls != 1 || !Contains(error, "during_read_guard=full_snapshot_changed") ||
      !Contains(error, "differing_fields=date_raw,played_character_id") ||
      !Contains(error, "before=date_raw:53290176") ||
      !Contains(error, "after=date_raw:53290200") ||
      Contains(error, "read_stage=")) return 3;

  calls = 0;
  error = FirstHeirDuringReadErrorV1(before, after,
      [&](xar::game::Snapshot &out) {
        ++calls; out = before; ++out.played_character_gold.raw; return true;
      }, Failure::none, Failure::frame_changed, 2, 2, 38822);
  if (calls != 1 || !Contains(error, "during_read_guard=full_snapshot_changed") ||
      !Contains(error, "differing_fields=played_character_gold")) return 4;

  calls = 0;
  error = FirstHeirDuringReadErrorV1(before, after, same_read,
      Failure::frame_changed, Failure::frame_changed, 2, 2, 38822);
  if (calls != 1 || !Contains(error, "during_read_guard=relationship_frame_changed") ||
      !Contains(error, "relationship_failure_raw=1") ||
      Contains(error, "differing_fields=")) return 5;

  diagnostic::BeginSnapshotReadAttempt12004();
  diagnostic::RecordSnapshotReadFailure12004(
      diagnostic::SnapshotReadFailureStage12004::events);
  calls = 0;
  error = FirstHeirDuringReadErrorV1(before, after,
      [&](xar::game::Snapshot &) { ++calls; return false; },
      Failure::none, Failure::frame_changed, 2, 2, 38822);
  if (calls != 1 || !Contains(error, "during_read_guard=snapshot_read_failed") ||
      !Contains(error, "after=unknown") || Contains(error, "read_stage=")) return 6;
  std::cout << "PASS 6 new first-heir during-read diagnostic cases\n";
  return 0;
}

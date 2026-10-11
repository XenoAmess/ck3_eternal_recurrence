#include "xar_bridge/observed_heir_marriage_admission_diagnostic_v1.hpp"
#include <iostream>

namespace diagnostic = xar::bridge::ck3_12004;
using xar::bridge_detail::ObservedHeirMarriageAdmissionErrorV1;
bool Contains(const std::string &text, std::string_view value) {
  return text.find(value) != std::string::npos;
}
int main() {
  xar::game::Snapshot frame{};
  frame.date_raw = 53290176;
  frame.paused = frame.map_ready = frame.has_played_character =
      frame.played_character_alive = true;
  frame.played_character_id = 29829;
  std::optional<xar::game::Snapshot> previous = frame;
  xar::game::Snapshot before{};
  int reads = 0, routes = 0;
  const auto same_read = [&](xar::game::Snapshot &out) {
    ++reads; out = frame; return true;
  };
  const auto accepted_route = [&]() -> std::string_view {
    ++routes; return {};
  };
  auto error = ObservedHeirMarriageAdmissionErrorV1(
      true, 2, 2, previous, before, same_read, accepted_route);
  if (!error.empty() || reads != 1 || routes != 1) return 1;

  reads = routes = 0;
  error = ObservedHeirMarriageAdmissionErrorV1(
      true, 147, 2, previous, before, same_read, accepted_route);
  if (reads != 0 || routes != 0 || !Contains(error, "admission_guard=revision_mismatch") ||
      !Contains(error, "expected_revision=147; native_revision=2") ||
      !Contains(error, "observed=unknown")) return 2;

  reads = routes = 0;
  error = ObservedHeirMarriageAdmissionErrorV1(
      true, 2, 2, previous, before, [&](xar::game::Snapshot &) {
        ++reads; diagnostic::BeginSnapshotReadAttempt12004();
        diagnostic::RecordSnapshotReadFailure12004(
            diagnostic::SnapshotReadFailureStage12004::actor_resources);
        return false;
      }, accepted_route);
  if (reads != 1 || routes != 0 || !Contains(error, "admission_guard=snapshot_read_failed") ||
      !Contains(error, "read_stage=actor_resources") ||
      !Contains(error, "observed=unknown")) return 3;

  reads = routes = 0;
  error = ObservedHeirMarriageAdmissionErrorV1(
      true, 2, 2, previous, before, [&](xar::game::Snapshot &out) {
        ++reads; out = frame; ++out.played_character_piety.raw; return true;
      }, accepted_route);
  if (reads != 1 || routes != 0 || !Contains(error, "admission_guard=full_snapshot_changed") ||
      !Contains(error, "differing_fields=played_character_piety")) return 4;

  reads = routes = 0;
  error = ObservedHeirMarriageAdmissionErrorV1(
      true, 2, 2, previous, before, same_read, [&]() -> std::string_view {
        ++routes; return "cold_observed_heir_revision_mismatch";
      });
  if (reads != 1 || routes != 1 ||
      !Contains(error, "admission_guard=cold_observed_heir_revision_mismatch") ||
      !Contains(error, "expected_revision=2; native_revision=2") ||
      !Contains(error, "observed=date_raw:53290176")) return 5;
  std::cout << "PASS 5 new observed-heir admission diagnostic cases\n";
  return 0;
}

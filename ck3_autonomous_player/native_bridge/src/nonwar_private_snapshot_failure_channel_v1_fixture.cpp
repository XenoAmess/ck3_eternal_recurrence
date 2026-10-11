#include "xar_bridge/nonwar_private_snapshot_guard_diagnostics_v1.hpp"
#include <iostream>
#include <string_view>

namespace {
bool Has(const std::string &text, std::string_view part) {
  return text.find(part) != std::string::npos;
}
}

int main() {
  using namespace xar::bridge;
  const std::optional<xar::game::Snapshot> previous{xar::game::Snapshot{}};
  xar::game::Snapshot current{};

  // 1. The real Nonwar guard's single failed callback now exposes an absent
  // receipt and the caller's actual descriptor fact; it invents no child stage.
  unsigned no_receipt_reads = 0;
  const auto no_receipt = NonwarPrivateSnapshotGuardFailureV1(
      false, true, 3, 3, previous, current,
      [&](xar::game::Snapshot &) { ++no_receipt_reads; return false; }, false);
  if (no_receipt_reads != 1 ||
      !Has(no_receipt, "cause=current_snapshot_read_failed expected_revision=3 native_revision=3") ||
      !Has(no_receipt, " actual4_descriptor=false") ||
      !Has(no_receipt, " fresh_read_failure=false read_stage=unknown diagnostic_receipt=sequence_unchanged")) return 11;

  // 2. Through this guard, one stamped producer failure is forwarded exactly
  // once by the same channel implementation already used by the war caller.
  unsigned fresh_reads = 0;
  const auto fresh = NonwarPrivateSnapshotGuardFailureV1(
      false, true, 3, 3, previous, current,
      [&](xar::game::Snapshot &) {
        ++fresh_reads;
        ck3_12004::BeginSnapshotReadAttempt12004();
        ck3_12004::RecordSnapshotReadFailure12004(
            ck3_12004::SnapshotReadFailureStage12004::events);
        return false;
      }, true);
  if (fresh_reads != 1 ||
      !Has(fresh, " actual4_descriptor=true") ||
      !Has(fresh, " fresh_read_failure=true read_stage=events prefix_ready=false") ||
      Has(fresh, " read_stage=unknown") ||
      fresh.find(" read_stage=events") != fresh.rfind(" read_stage=events")) return 21;

  // 3. Legacy callers without descriptor metadata keep their exact old error.
  // Unknown metadata does not become an observed false descriptor value.
  unsigned legacy_reads = 0;
  const auto legacy = NonwarPrivateSnapshotGuardFailureV1(
      false, true, 3, 3, previous, current,
      [&](xar::game::Snapshot &) { ++legacy_reads; return false; });
  if (legacy_reads != 1 || legacy !=
      "nonwar private snapshot revision is stale or malformed: cause=current_snapshot_read_failed expected_revision=3 native_revision=3") return 31;

  std::cout << "PASS 3 new cases: real Nonwar guard failure channel; adapter/Game not executed\n";
  return 0;
}

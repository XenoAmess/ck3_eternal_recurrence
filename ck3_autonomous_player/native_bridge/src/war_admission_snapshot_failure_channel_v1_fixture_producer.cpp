#include "xar_bridge/snapshot_read_failure_diagnostics_12004.hpp"

// A separate translation unit uses the exact production producer functions.
// This fixture does not instantiate an adapter or read game memory.
bool RecordWarAdmissionFailureFromProducerTranslationUnitV1() noexcept {
  using namespace xar::bridge::ck3_12004;
  BeginSnapshotReadAttempt12004();
  RecordSnapshotReadFailure12004(SnapshotReadFailureStage12004::core_prefix);
  return false;
}

void BeginWarAdmissionAttemptFromProducerTranslationUnitV1() noexcept {
  xar::bridge::ck3_12004::BeginSnapshotReadAttempt12004();
}

const void *WarAdmissionReceiptAddressFromProducerTranslationUnitV1() noexcept {
  return &xar::bridge::ck3_12004::detail::snapshot_read_attempt12004;
}

#include "xar_bridge/war_admission_snapshot_failure_channel_v1.hpp"
#include <iostream>
#include <string_view>

bool RecordWarAdmissionFailureFromProducerTranslationUnitV1() noexcept;
void BeginWarAdmissionAttemptFromProducerTranslationUnitV1() noexcept;
const void *WarAdmissionReceiptAddressFromProducerTranslationUnitV1() noexcept;

namespace {
bool Has(const std::string &text, std::string_view part) {
  return text.find(part) != std::string::npos;
}
}

int main() {
  using namespace xar::bridge::ck3_12004;
  // 1. Producer and consumer TUs refer to one actual inline TLS object. A
  // producer's single failed attempt is visible through the exact Fresh API.
  const auto first_before = CaptureSnapshotReadSequence12004();
  if (RecordWarAdmissionFailureFromProducerTranslationUnitV1()) return 11;
  const auto first = FormatWarAdmissionSnapshotFailureChannelV1(true, first_before);
  if (WarAdmissionReceiptAddressFromProducerTranslationUnitV1() !=
          &detail::snapshot_read_attempt12004 ||
      CaptureSnapshotReadSequence12004() != first_before + std::uint64_t{1} ||
      !Has(first, " actual4_descriptor=true") ||
      !Has(first, " fresh_read_failure=true read_stage=core_prefix prefix_ready=false") ||
      Has(first, "diagnostic_receipt=")) return 12;

  // 2. A failed call with no new producer attempt cannot reuse an old stage.
  const auto unchanged_before = CaptureSnapshotReadSequence12004();
  const auto unchanged = FormatWarAdmissionSnapshotFailureChannelV1(false, unchanged_before);
  if (!Has(unchanged, " actual4_descriptor=false") ||
      !Has(unchanged, " fresh_read_failure=false read_stage=unknown diagnostic_receipt=sequence_unchanged") ||
      Has(unchanged, "read_stage=core_prefix")) return 22;

  // 3. Two attempts remain unqualified by the existing exact +1 Fresh rule.
  const auto multiple_before = CaptureSnapshotReadSequence12004();
  BeginWarAdmissionAttemptFromProducerTranslationUnitV1();
  if (RecordWarAdmissionFailureFromProducerTranslationUnitV1()) return 31;
  const auto multiple = FormatWarAdmissionSnapshotFailureChannelV1(true, multiple_before);
  if (CaptureSnapshotReadSequence12004() != multiple_before + std::uint64_t{2} ||
      !Has(multiple, " fresh_read_failure=false read_stage=unknown diagnostic_receipt=sequence_not_single_attempt") ||
      Has(multiple, "read_stage=core_prefix")) return 32;

  // 4. A single Begin with no failure stamp has no qualified child stage.
  const auto unstamped_before = CaptureSnapshotReadSequence12004();
  BeginWarAdmissionAttemptFromProducerTranslationUnitV1();
  const auto unstamped = FormatWarAdmissionSnapshotFailureChannelV1(true, unstamped_before);
  if (!Has(unstamped, " fresh_read_failure=false read_stage=unknown diagnostic_receipt=single_attempt_without_failure_stage") ||
      Has(unstamped, "read_stage=core_prefix")) return 42;

  std::cout << "PASS 4 new cases: cross-TU inline TLS and war failure channel; adapter/Game not executed\n";
  return 0;
}

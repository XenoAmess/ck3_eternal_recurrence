#pragma once

#include "xar_bridge/person_transfer_blocke0_12004.hpp"
#include "xar_bridge/person_transfer_snapshot_scope_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

struct PersonTransferValuesSnapshot12004 {
  PersonTransferSnapshotScope12004 scope;
  // Original qualified copy DTO: independent descriptor fields, optional
  // ordered signed Q64 interpretation and the precise source-copy reason.
  PersonTransferBlockE0Copy12004 raw;
  std::optional<std::vector<std::uint64_t>> values_q64_raw_bits;
  bool descriptor_copy_complete = false;
  bool payload_copy_complete = false;
  bool declared_operand_copy_complete = false;
  std::size_t maximum_payload_bytes = 0;
  std::string reason;
};

// The caller supplies the same original wrapper occurrence/current event and
// its existing guarded reader. This adapter issues no clock, getter or native
// call and copies the legacy value operand once. The observer budget is not a
// native count/capacity rule: excess retains the actual count, with no payload.
// Values use their own count. Key/value pairing and event attribution belong
// to the aggregate collector, not these three copied-field completeness flags.
PersonTransferValuesSnapshot12004 CapturePersonTransferValuesSnapshot12004(
    const PersonTransferSnapshotScope12004 &scope, void *read_context,
    PersonInstalledTransferRead12004 read,
    std::size_t maximum_payload_bytes);

} // namespace xar::ck3_12004

#pragma once

#include "xar_bridge/person_transfer_block78_12004.hpp"
#include "xar_bridge/person_transfer_snapshot_scope_12004.hpp"

#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPersonTransferKeysSnapshotSchema12004 =
    "xar.ck3.person-transfer-keys-snapshot-12004-v1";

struct PersonTransferKeysSnapshot12004 {
  PersonTransferSnapshotScope12004 scope;
  PersonTransferKeyCopy12004 raw;
  std::size_t maximum_payload_bytes = 0;
  bool payload_budget_exceeded = false;
  bool descriptor_copy_complete = false;
  bool payload_copy_complete = false;
  bool declared_operand_copy_complete = false;
};

// The collector supplies the actual storage operand and original-call scope.
// This adapter samples no clock, performs no Model/PC arithmetic and uses only
// its supplied guarded reader. The budget bounds copied bytes, not native count.
PersonTransferKeysSnapshot12004 CapturePersonTransferKeysSnapshot12004(
    std::uintptr_t actual_storage,
    const PersonTransferSnapshotScope12004 &scope,
    void *read_context, PersonTransferSnapshotRead12004 read_memory,
    std::size_t maximum_payload_bytes);

} // namespace xar::ck3_12004

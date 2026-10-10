#pragma once

#include "xar_bridge/person_transfer_block248_12004.hpp"
#include "xar_bridge/person_transfer_snapshot_scope_12004.hpp"

#include <cstddef>

namespace xar::ck3_12004 {

struct PersonTransferBlock248SnapshotCapture12004 {
  PersonTransferSnapshotScope12004 scope;
  PersonTransferBlock248Snapshot12004 raw;
  // All five declared header fields were copied: pointer, signed capacity,
  // signed count, allocator identity, and allocator dispatch-vtable identity.
  bool descriptor_copy_complete = false;
  // Independent of descriptor completeness; a copied zero count is a known
  // empty payload even when another header field could not be copied.
  bool payload_copy_complete = false;
  // Covers this declared copied operand only, not native allocator internals
  // or a complete Person, Entry, or arbitrary container postimage.
  bool declared_operand_copy_complete = false;
};

// Reuses the qualified guarded reader for this one supplied phase/side/model.
// maximum_payload_bytes is an observer copy budget, not native capacity. A
// rejected payload preserves its actual copied count and all header fields.
// Scope is copied verbatim; this adapter creates no event, clock, or counter
// and invokes neither a native getter nor a native allocator.
PersonTransferBlock248SnapshotCapture12004
CapturePersonTransferBlock248Snapshot12004(
    const PersonTransferSnapshotScope12004 &scope, void *read_context,
    PersonInstalledTransferRead12004 read,
    std::size_t maximum_payload_bytes);

} // namespace xar::ck3_12004

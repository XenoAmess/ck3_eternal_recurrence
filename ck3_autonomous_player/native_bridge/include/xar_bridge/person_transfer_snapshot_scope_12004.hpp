#pragma once

#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {

enum class PersonTransferSnapshotPhase12004 : std::uint8_t {
  before_original,
  after_original,
};

enum class PersonTransferSnapshotSide12004 : std::uint8_t { a, b };

using PersonTransferSnapshotRead12004 = PersonInstalledTransferRead12004;

// Supplied by the one existing original wrapper. occurrence is its before
// event, event is the current boundary event. Adapters own neither clock nor
// occurrence counter and never infer these fields from a retention ordinal.
struct PersonTransferSnapshotScope12004 {
  PersonInstalledTransferEvent12004 occurrence;
  PersonInstalledTransferEvent12004 event;
  PersonTransferSnapshotPhase12004 phase =
      PersonTransferSnapshotPhase12004::before_original;
  PersonTransferSnapshotSide12004 side = PersonTransferSnapshotSide12004::a;
  std::uintptr_t model_identity = 0;
  std::uintptr_t original_return_rva = 0;
};

// Observer budgets for each independently copied operand, not native capacity
// rules. Each phase contains two receivers, each with four bounded operands.
struct PersonTransferSnapshotLimits12004 {
  std::size_t row_payload_bytes = 64 * 1024;
  std::size_t key_payload_bytes = 64 * 1024;
  std::size_t value_payload_bytes = 64 * 1024;
  std::size_t block248_payload_bytes = 64 * 1024;
};

} // namespace xar::ck3_12004

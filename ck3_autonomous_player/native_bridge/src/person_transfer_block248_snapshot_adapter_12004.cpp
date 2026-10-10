#include "xar_bridge/person_transfer_block248_snapshot_adapter_12004.hpp"

#include <cstring>
#include <limits>
#include <optional>

namespace xar::ck3_12004 {
namespace {

struct BoundedRead12004 {
  void *read_context = nullptr;
  PersonInstalledTransferRead12004 read = nullptr;
  std::size_t maximum_payload_bytes = 0;
  std::optional<std::uintptr_t> count_address;
  std::optional<std::int32_t> actual_count;
  bool payload_budget_exceeded = false;
};

bool CopyWithPayloadBudget12004(void *context, std::uintptr_t address,
                               void *destination,
                               std::size_t bytes) noexcept {
  auto &bounded = *static_cast<BoundedRead12004 *>(context);
  if (!bounded.read || !bounded.read(bounded.read_context, address,
                                     destination, bytes))
    return false;
  if (bounded.count_address && address == *bounded.count_address &&
      bytes == sizeof(std::int32_t)) {
    std::int32_t count = 0;
    std::memcpy(&count, destination, sizeof(count));
    bounded.actual_count = count;
    if (count > 0 && static_cast<std::size_t>(count) >
                         bounded.maximum_payload_bytes / sizeof(std::uint64_t)) {
      bounded.payload_budget_exceeded = true;
      // The qualified reader will still copy its remaining descriptor fields,
      // then stop at its count-unread branch before allocating a payload.
      return false;
    }
  }
  return true;
}

} // namespace

PersonTransferBlock248SnapshotCapture12004
CapturePersonTransferBlock248Snapshot12004(
    const PersonTransferSnapshotScope12004 &scope, void *read_context,
    PersonInstalledTransferRead12004 read,
    std::size_t maximum_payload_bytes) {
  PersonTransferBlock248SnapshotCapture12004 result;
  result.scope = scope;
  BoundedRead12004 bounded;
  bounded.read_context = read_context;
  bounded.read = read;
  bounded.maximum_payload_bytes = maximum_payload_bytes;
  constexpr auto count_offset = kPersonTransferBlock248Offset12004 + 0xC;
  if (scope.model_identity <=
      std::numeric_limits<std::uintptr_t>::max() - count_offset)
    bounded.count_address = scope.model_identity + count_offset;
  const PersonTransferBlock248Bindings12004 bindings{
      &bounded, &CopyWithPayloadBudget12004};
  result.raw = ReadPersonTransferBlock24812004(bindings, scope.model_identity);
  if (bounded.payload_budget_exceeded) {
    result.raw.count_i32 = bounded.actual_count;
    result.raw.reason = "block248_payload_budget_exceeded";
  }
  result.descriptor_copy_complete =
      result.raw.data_identity.has_value() &&
      result.raw.capacity_i32.has_value() && result.raw.count_i32.has_value() &&
      result.raw.allocator_identity.has_value() &&
      result.raw.allocator_dispatch_vtable_identity.has_value();
  result.payload_copy_complete = result.raw.payload_ready &&
                                result.raw.ordered_payload_raw64.has_value();
  result.declared_operand_copy_complete =
      result.descriptor_copy_complete && result.payload_copy_complete;
  return result;
}

} // namespace xar::ck3_12004

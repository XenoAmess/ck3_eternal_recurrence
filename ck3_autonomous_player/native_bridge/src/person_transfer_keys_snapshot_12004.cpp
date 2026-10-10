#include "xar_bridge/person_transfer_keys_snapshot_12004.hpp"

#include <cstring>

namespace xar::ck3_12004 {
namespace {
struct KeysReadBridge12004 {
  std::uintptr_t actual_storage = 0;
  void *read_context = nullptr;
  PersonTransferSnapshotRead12004 read_memory = nullptr;
  std::size_t maximum_payload_bytes = 0;
  std::optional<std::int32_t> actual_count;
  bool payload_budget_exceeded = false;
};

bool ReadKeys12004(void *opaque, const void *source, void *destination,
                   std::size_t bytes) noexcept {
  auto &bridge = *static_cast<KeysReadBridge12004 *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (bridge.read_memory == nullptr ||
      !bridge.read_memory(bridge.read_context, address, destination, bytes)) {
    return false;
  }
  if (address == bridge.actual_storage + 0xC &&
      bytes == sizeof(std::int32_t)) {
    std::int32_t count = 0;
    std::memcpy(&count, destination, sizeof(count));
    bridge.actual_count = count;
    if (count > 0 && static_cast<std::size_t>(count) >
                         bridge.maximum_payload_bytes / sizeof(std::uint16_t)) {
      bridge.payload_budget_exceeded = true;
      // The qualified copier stops before allocating its key vector when its
      // count read is denied. Retain this one successful actual read below;
      // never reread, truncate the operand, or substitute an empty sequence.
      return false;
    }
  }
  return true;
}
} // namespace

PersonTransferKeysSnapshot12004 CapturePersonTransferKeysSnapshot12004(
    std::uintptr_t actual_storage,
    const PersonTransferSnapshotScope12004 &scope,
    void *read_context, PersonTransferSnapshotRead12004 read_memory,
    std::size_t maximum_payload_bytes) {
  PersonTransferKeysSnapshot12004 out;
  out.scope = scope;
  out.maximum_payload_bytes = maximum_payload_bytes;
  KeysReadBridge12004 bridge;
  bridge.actual_storage = actual_storage;
  bridge.read_context = read_context;
  bridge.read_memory = read_memory;
  bridge.maximum_payload_bytes = maximum_payload_bytes;
  out.raw = CopyPersonTransferBlock78Keys12004(
      actual_storage, &bridge, read_memory != nullptr ? ReadKeys12004 : nullptr);
  if (bridge.payload_budget_exceeded) {
    out.raw.count_i32 = bridge.actual_count;
    out.raw.header_ready = out.raw.data_identity.has_value() &&
                           out.raw.capacity_i32.has_value() &&
                           out.raw.count_i32.has_value();
    out.raw.keys_u16.reset();
    out.raw.key_elements_ready = false;
    out.raw.reason = "key_payload_budget_exceeded";
    out.payload_budget_exceeded = true;
  }
  out.descriptor_copy_complete = out.raw.header_ready;
  out.payload_copy_complete = out.raw.key_elements_ready;
  out.declared_operand_copy_complete =
      out.descriptor_copy_complete && out.payload_copy_complete;
  return out;
}

} // namespace xar::ck3_12004

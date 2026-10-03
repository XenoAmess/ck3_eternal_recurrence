#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace xar::ck3_12002 {
template <typename Value>
inline Value ReadEventFactionScopeValue12003(const void *base, std::size_t offset) {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof value);
  return value;
}
// The native type-25 producer saves a full FactionID in the +8 scalar payload.
// Reuse the production faction store's generation and object identity layout.
inline bool ResolveEventFactionScopeIdentity12003(
    std::uint64_t payload, void **storage_slot, void **fallback_slot,
    std::uintptr_t expected_vtable, std::int32_t &faction_id) {
  faction_id = -1;
  const auto full_id = static_cast<std::uint32_t>(payload);
  if (payload != static_cast<std::uint64_t>(full_id) ||
      full_id == 0 || full_id > 0x7FFFFFFFU || storage_slot == nullptr ||
      *storage_slot == nullptr) return false;
  void *const storage = *storage_slot;
  void *const slots = ReadEventFactionScopeValue12003<void *>(storage, 0x20);
  const auto capacity = ReadEventFactionScopeValue12003<std::int32_t>(storage, 0x2C);
  const auto index = full_id & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > 0x01000000 ||
      index >= static_cast<std::uint32_t>(capacity)) return false;
  void *const faction = ReadEventFactionScopeValue12003<void *>(slots,
      static_cast<std::size_t>(index) * 0x10 + 8);
  if (faction == nullptr ||
      (fallback_slot != nullptr && faction == *fallback_slot) ||
      ReadEventFactionScopeValue12003<std::int32_t>(faction, 0x10) !=
          static_cast<std::int32_t>(full_id) ||
      ReadEventFactionScopeValue12003<std::uintptr_t>(faction, 0) != expected_vtable)
    return false;
  faction_id = static_cast<std::int32_t>(full_id);
  return true;
}
} // namespace xar::ck3_12002

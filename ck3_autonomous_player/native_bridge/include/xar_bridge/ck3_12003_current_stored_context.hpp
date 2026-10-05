#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <utility>

namespace xar::ck3_12002::current_stored_context_12003 {

// Read current owning-thread memory only. No reset, cleanup, initialization,
// modifier preparation or native getter is invoked by this reader.
inline bool CopyBytes(void *destination, const void *source,
                      std::size_t length) noexcept {
  if (length == 0) return true;
  if (!source) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(destination, source, length);
    return true;
  } __except (1) {
    return false;
  }
#else
  std::memcpy(destination, source, length);
  return true;
#endif
}

template <typename T>
inline std::optional<T> Read(const void *base, std::size_t offset) noexcept {
  if (!base) return std::nullopt;
  T value{};
  if (!CopyBytes(&value, static_cast<const std::byte *>(base) + offset,
                 sizeof(value))) return std::nullopt;
  return value;
}

inline std::uint64_t Address(const void *pointer) noexcept {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(pointer));
}

template <typename T>
inline void ReadDescriptor(const void *header,
                          game::BattleCurrentStoredArraySnapshotV1<T> &out) {
  if (const auto data = Read<const void *>(header, 0))
    out.data_address = Address(*data);
  out.capacity_raw = Read<std::uint32_t>(header, 8);
  out.count = Read<std::int32_t>(header, 0xC);
}

template <typename T>
inline game::BattleCurrentStoredArraySnapshotV1<T> ReadScalarArray(
    const void *header) {
  game::BattleCurrentStoredArraySnapshotV1<T> out{};
  ReadDescriptor(header, out);
  if (!out.count || *out.count < 0) return out;
  if (*out.count == 0) {
    // Empty active extent does not require an unused data pointer.
    out.items.emplace();
    return out;
  }
  if (!out.data_address || *out.data_address == 0) return out;
  std::vector<T> copied(static_cast<std::size_t>(*out.count));
  if (CopyBytes(copied.data(), reinterpret_cast<const void *>(
                    static_cast<std::uintptr_t>(*out.data_address)),
                copied.size() * sizeof(T))) out.items = std::move(copied);
  return out;
}

inline game::BattleCurrentStoredPropertyBlockSnapshotV1 ReadPropertyBlock(
    const void *block) {
  game::BattleCurrentStoredPropertyBlockSnapshotV1 out{};
  out.key_array = ReadScalarArray<std::uint16_t>(block);
  out.value_array = ReadScalarArray<std::int64_t>(
      static_cast<const std::byte *>(block) + 0x68);
  return out;
}

template <typename T>
inline bool ActiveArrayAvailable(
    const game::BattleCurrentStoredArraySnapshotV1<T> &array) noexcept {
  // Capacities and storage addresses are diagnostics, not numerical gates.
  return array.count.has_value() && array.items.has_value();
}

inline bool PropertyBlockAvailable(
    const game::BattleCurrentStoredPropertyBlockSnapshotV1 &block) noexcept {
  // Unequal independent counts remain meaningful observed values.
  return ActiveArrayAvailable(block.key_array) &&
         ActiveArrayAvailable(block.value_array);
}

inline game::BattleCurrentStoredArraySnapshotV1<
    game::BattleCurrentStoredWeightedRowSnapshotV1> ReadWeightedArray(
        const void *header) {
  game::BattleCurrentStoredArraySnapshotV1<
      game::BattleCurrentStoredWeightedRowSnapshotV1> out{};
  ReadDescriptor(header, out);
  if (!out.count || *out.count < 0) return out;
  if (*out.count == 0) {
    out.items.emplace();
    return out;
  }
  if (!out.data_address || *out.data_address == 0) return out;
  const auto *data = reinterpret_cast<const std::byte *>(
      static_cast<std::uintptr_t>(*out.data_address));
  out.items.emplace();
  out.items->reserve(static_cast<std::size_t>(*out.count));
  for (std::int32_t i = 0; i < *out.count; ++i) {
    const auto *native_row = data + static_cast<std::size_t>(i) * 16;
    game::BattleCurrentStoredWeightedRowSnapshotV1 row{};
    row.native_index = i;
    row.weight_raw = Read<std::int64_t>(native_row, 8);
    if (const auto block = Read<const void *>(native_row, 0); block && *block)
      row.property_block = ReadPropertyBlock(*block);
    out.items->push_back(std::move(row));
  }
  return out;
}

inline game::BattleCurrentStoredContextStateSnapshotV1 ReadCurrentStoredState(
    void *character, std::int32_t character_full_id) {
  game::BattleCurrentStoredContextStateSnapshotV1 out{};
  out.character_full_id = character_full_id;
  if (!character) {
    out.reason = "character_unresolved";
    return out;
  }
  const auto scratch = Read<const void *>(character, 0x1B0);
  if (!scratch) {
    out.reason = "stored_context_scratch_pointer_read_failed";
    return out;
  }
  out.scratch_address = Address(*scratch);
  out.scratch_present = *scratch != nullptr;
  if (!*scratch) {
    out.model_present = false;
    out.available = true;
    return out;
  }
  const auto model = Read<const void *>(*scratch, 0x258);
  if (!model) {
    out.reason = "stored_context_model_pointer_read_failed";
    return out;
  }
  out.model_address = Address(*model);
  out.model_present = *model != nullptr;
  if (!*model) {
    out.available = true;
    return out;
  }
  const auto *stored = static_cast<const std::byte *>(*model);
  out.context_address = Address(stored + 0x10);
  if (const auto owner = Read<const void *>(stored, 8)) {
    out.owner_address = Address(*owner);
    out.bound_to_requested_character = *owner == character;
    if (*owner) out.owner_character_full_id = Read<std::int32_t>(*owner, 0x18);
  }
  out.pending_raw = Read<std::uint8_t>(stored, 0x2F4);
  out.owned_count_raw = Read<std::int32_t>(stored, 0x254);
  out.weighted = ReadWeightedArray(stored + 0x10);
  out.key_array = ReadScalarArray<std::uint16_t>(stored + 0x78);
  out.value_array = ReadScalarArray<std::int64_t>(stored + 0xE0);
  if (out.weighted->count)
    out.weighted_count_nonzero = *out.weighted->count != 0;
  bool complete = ActiveArrayAvailable(*out.weighted) &&
      ActiveArrayAvailable(*out.key_array) && ActiveArrayAvailable(*out.value_array);
  if (out.weighted->items) {
    for (const auto &row : *out.weighted->items)
      if (!row.weight_raw || !row.property_block ||
          !PropertyBlockAvailable(*row.property_block)) complete = false;
  }
  out.available = complete;
  if (!complete) {
    const bool negative = (out.weighted->count && *out.weighted->count < 0) ||
        (out.key_array->count && *out.key_array->count < 0) ||
        (out.value_array->count && *out.value_array->count < 0);
    out.reason = negative ? "stored_context_negative_active_extent"
                          : "stored_context_active_array_read_unavailable";
  }
  return out;
}

} // namespace xar::ck3_12002::current_stored_context_12003

#include "xar_bridge/owned_regiments.hpp"

#include <cstddef>
#include <cstring>
#include <utility>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}

// Reuse the existing army reader's database/vector bounds and memory idiom.
constexpr std::int32_t kMaximumDatabaseCapacity = 1'000'000;
constexpr std::int32_t kMaximumRegiments = 65'536;
constexpr std::int32_t kChunkCount = 7;
constexpr std::size_t kChunkStride = 0x24;

bool ReadStorage(void **slot, void *&entries,
                 std::int32_t &capacity) noexcept {
  entries = nullptr;
  capacity = 0;
  if (slot == nullptr || *slot == nullptr) return false;
  entries = Load<void *>(*slot, 0x20);
  capacity = Load<std::int32_t>(*slot, 0x2C);
  return capacity >= 0 && capacity <= kMaximumDatabaseCapacity &&
         (capacity == 0 || entries != nullptr);
}

void FailRow(OwnedRegimentSnapshotV1 &row, const char *reason) noexcept {
  row.unavailable_reason = reason;
  row.type.unavailable_reason = reason;
}

void ReadType(const OwnedRegimentsBindingsV1 &bindings, void *regiment,
              OwnedRegimentTypeSnapshotV1 &output) noexcept {
  void *const maa_type = Load<void *>(regiment, 0x118);
  if (maa_type == nullptr ||
      Load<std::uint32_t>(maa_type, 0x38) != 0x4744624FU) {
    output.status = OwnedRegimentTypeStatusV1::absent;
    return;
  }
  if (bindings.read_type == nullptr) {
    output.unavailable_reason = "owned_regiment_type_reader_unavailable";
    return;
  }
  // No local MSVC string parser: the mounted existing GDbo reader owns it.
  bindings.read_type(bindings.type_context, maa_type, output);
  if (output.status == OwnedRegimentTypeStatusV1::unavailable &&
      output.unavailable_reason.empty()) {
    output.unavailable_reason = "owned_regiment_type_unavailable";
  }
}

void ReadChunks(void *regiment,
                std::vector<OwnedRegimentChunkSnapshotV1> &output) noexcept {
  output.reserve(static_cast<std::size_t>(kChunkCount));
  for (std::int32_t index = 0; index < kChunkCount; ++index) {
    const auto offset = 0x18 + static_cast<std::size_t>(index) * kChunkStride;
    const void *const chunk = static_cast<const std::byte *>(regiment) + offset;
    OwnedRegimentChunkSnapshotV1 row{};
    row.chunk_index = index;
    row.maximum_soldiers = Load<std::int32_t>(chunk, 0x00);
    row.current_soldiers = Load<std::int32_t>(chunk, 0x04);
    row.persistent_regiment_id = Load<std::int32_t>(chunk, 0x08);
    row.native_chunk_index = Load<std::int32_t>(chunk, 0x0C);
    row.army_regiment_id = Load<std::int32_t>(chunk, 0x10);
    row.pending_raw = Load<std::uint8_t>(chunk, 0x14);
    row.state_raw = Load<std::int32_t>(chunk, 0x18);
    output.push_back(row);
  }
}

} // namespace

OwnedRegimentsReadResultV1 ReadPlayerOwnedRegimentsV1(
    const OwnedRegimentsBindingsV1 &bindings, void *current_player_character,
    std::int32_t actor_character_id, OwnedRegimentsSnapshotV1 &output) noexcept {
  output = {};
  output.actor_character_id = actor_character_id;
  if (current_player_character == nullptr || actor_character_id == -1 ||
      Load<std::int32_t>(current_player_character, 0x18) != actor_character_id ||
      Load<std::uint32_t>(current_player_character, 0x1C) != 0x43686172U) {
    output.unavailable_reason = "owned_regiments_player_character_unavailable";
    return output.status;
  }
  void *const military = Load<void *>(current_player_character, 0x1C0);
  if (military == nullptr) {
    output.unavailable_reason = "owned_regiments_military_unavailable";
    return output.status;
  }
  const void *const header = static_cast<const std::byte *>(military) + 0x108;
  void *const ids = Load<void *>(header, 0x00);
  const auto count = Load<std::int32_t>(header, 0x0C);
  output.source_count = count;
  if (count < 0 || count > kMaximumRegiments ||
      (count != 0 && ids == nullptr)) {
    output.unavailable_reason = "owned_regiments_collection_unavailable";
    return output.status;
  }
  output.regiments.reserve(static_cast<std::size_t>(count));
  output.collection_complete = true;
  output.status = OwnedRegimentsReadResultV1::available;
  if (count == 0) return output.status;

  void *entries = nullptr;
  std::int32_t capacity = 0;
  const bool storage_available =
      ReadStorage(bindings.persistent_regiment_storage_slot, entries, capacity);
  for (std::int32_t index = 0; index < count; ++index) {
    OwnedRegimentSnapshotV1 row{};
    row.persistent_regiment_id =
        Load<std::int32_t>(ids, static_cast<std::size_t>(index) * 4);
    void *regiment = nullptr;
    if (!storage_available) {
      FailRow(row, "owned_regiment_storage_unavailable");
    } else if (row.persistent_regiment_id == -1) {
      FailRow(row, "owned_regiment_reference_absent");
    } else {
      const auto reference_index =
          static_cast<std::uint32_t>(row.persistent_regiment_id) & 0xFFFFFFU;
      if (reference_index >= static_cast<std::uint32_t>(capacity)) {
        FailRow(row, "owned_regiment_reference_out_of_range");
      } else {
        regiment = Load<void *>(entries,
                                static_cast<std::size_t>(reference_index) * 0x10 + 8);
        if (regiment == nullptr) {
          FailRow(row, "owned_regiment_not_found");
        } else if (Load<std::int32_t>(regiment, 0x10) !=
                   row.persistent_regiment_id) {
          FailRow(row, "owned_regiment_generation_mismatch");
          regiment = nullptr;
        } else if (Load<std::uint32_t>(regiment, 0x14) != 0x52656769U) {
          FailRow(row, "owned_regiment_identity_invalid");
          regiment = nullptr;
        }
      }
    }
    if (regiment != nullptr) {
      const auto owner = Load<std::int32_t>(regiment, 0x12C);
      if (owner != -1) row.owner_character_id = owner;
      row.native_capacity_raw = Load<std::int32_t>(regiment, 0x128);
      ReadChunks(regiment, row.chunks);
      ReadType(bindings, regiment, row.type);
      row.available = true;
    }
    if (!row.available ||
        row.type.status == OwnedRegimentTypeStatusV1::unavailable) {
      output.status = OwnedRegimentsReadResultV1::partial;
    }
    output.regiments.push_back(std::move(row));
  }
  if (output.status == OwnedRegimentsReadResultV1::partial) {
    output.unavailable_reason = "owned_regiments_partial";
  }
  return output.status;
}

} // namespace xar::ck3_12003

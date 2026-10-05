#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12003 {

// Independent DTOs: game_contract.hpp may include this header.
enum class OwnedRegimentsReadResultV1 { available, partial, unavailable };
enum class OwnedRegimentTypeStatusV1 { available, absent, unavailable };

struct OwnedRegimentTypeSnapshotV1 {
  OwnedRegimentTypeStatusV1 status = OwnedRegimentTypeStatusV1::unavailable;
  std::string maa_type_key;
  std::optional<std::int32_t> siege_tier;
  std::string unavailable_reason;
  bool operator==(const OwnedRegimentTypeSnapshotV1 &) const = default;
};

struct OwnedRegimentChunkSnapshotV1 {
  std::int32_t chunk_index = -1;
  std::int32_t maximum_soldiers = 0;
  std::int32_t current_soldiers = 0;
  std::int32_t persistent_regiment_id = -1;
  std::int32_t native_chunk_index = -1;
  // This backlink identifies ArRg, never CArmy or a public CUnit.
  std::int32_t army_regiment_id = -1;
  std::uint8_t pending_raw = 0;
  std::int32_t state_raw = 0;
  bool operator==(const OwnedRegimentChunkSnapshotV1 &) const = default;
};

struct OwnedRegimentSnapshotV1 {
  std::int32_t persistent_regiment_id = -1;
  bool available = false;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> native_capacity_raw;
  OwnedRegimentTypeSnapshotV1 type;
  // Exactly seven entries for a resolved Regi; empty for an unresolved row.
  std::vector<OwnedRegimentChunkSnapshotV1> chunks;
  std::string unavailable_reason;
  bool operator==(const OwnedRegimentSnapshotV1 &) const = default;
};

struct OwnedRegimentsSnapshotV1 {
  OwnedRegimentsReadResultV1 status = OwnedRegimentsReadResultV1::unavailable;
  std::int32_t actor_character_id = -1;
  std::optional<std::int32_t> source_count;
  // Completeness of direct A+108 ID enumeration, independent of row failures.
  bool collection_complete = false;
  std::vector<OwnedRegimentSnapshotV1> regiments;
  std::string unavailable_reason;
  bool operator==(const OwnedRegimentsSnapshotV1 &) const = default;
};

struct OwnedRegimentsBindingsV1 {
  void **persistent_regiment_storage_slot = nullptr;
  void *type_context = nullptr;
  // Reuse the mounted exact-build type/string reader. The receiver is GDbo*,
  // not ArRg*: its key uses stringbase+0x18 and the existing size_t reader.
  void (*read_type)(void *context, void *maa_type,
                    OwnedRegimentTypeSnapshotV1 &output) noexcept = nullptr;
};

// Called once on the paused owning game thread with the already resolved
// CURRENT PLAYER Character, then mounted on one authoritative player army row.
// No constructor, raising predicate or native mutator is invoked. All A+108
// IDs are retained, including failed full-generation resolution rows.
OwnedRegimentsReadResultV1 ReadPlayerOwnedRegimentsV1(
    const OwnedRegimentsBindingsV1 &bindings, void *current_player_character,
    std::int32_t actor_character_id, OwnedRegimentsSnapshotV1 &output) noexcept;

} // namespace xar::ck3_12003

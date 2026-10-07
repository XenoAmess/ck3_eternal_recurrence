#pragma once

#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12004_family_relationships.hpp"
#include "xar_bridge/current_first_heir_descendants_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <bit>
#include <cstring>
#include <utility>

namespace xar::ck3_12004 {
namespace first_heir_descendants_detail {

template <typename T>
inline T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

inline bool SameFrame(const CoreSnapshotPrefix &first,
                      const CoreSnapshotPrefix &second) noexcept {
  return first.clock.date_raw == second.clock.date_raw &&
      first.clock.paused == second.clock.paused &&
      first.clock.speed == second.clock.speed &&
      first.local_player_id == second.local_player_id &&
      first.map_ready == second.map_ready &&
      first.has_played_character == second.has_played_character &&
      first.played_character_id == second.played_character_id &&
      first.played_character_alive == second.played_character_alive;
}

inline bool Frame(const ck3_12002::FamilyBindings &bindings,
                  CoreSnapshotPrefix &output) noexcept {
  return bindings.enabled &&
      xar::ck3_12004::ReadCoreSnapshot(bindings.context.core, output) &&
      output.clock.paused && output.map_ready && output.has_played_character &&
      output.played_character_alive;
}

inline ck3_11906::CurrentFirstHeirDescendantLineageV1 ReadLineage(
    const ck3_12002::FamilyBindings &bindings, const void *character) noexcept {
  ck3_11906::CurrentFirstHeirDescendantLineageV1 result{};
  ck3_12002::family_value::Lineage lineage{};
  result.available = ck3_12002::family_value::ReadCharacterLineage(
      bindings.values, character, lineage, &result.unavailable_reason);
  if (result.available) {
    result.house_id_raw = lineage.house_id;
    result.dynasty_id_raw = lineage.dynasty_id;
  }
  return result;
}

} // namespace first_heir_descendants_detail

// Application-thread observation for the public primary-first-heir ID supplied
// by the owning callback. Root's before/after full snapshot binds that identity.
// Held actual4 collector operands: 1C11B94 Family1A8, 1C11BA0 children38,
// 1C11BAD data0, 1C11BB0 signed countC. No capacity operand is consumed.
inline ck3_11906::CurrentFirstHeirDescendantsReadV1
ReadCurrentFirstHeirDescendantsV1(
    const ck3_12002::FamilyBindings &bindings,
    std::int32_t heir_character_id) noexcept {
  using Status = ck3_11906::CurrentFirstHeirDescendantsStatusV1;
  using namespace first_heir_descendants_detail;
  ck3_11906::CurrentFirstHeirDescendantsReadV1 result{};
  result.heir_character_id = heir_character_id;
  if (!bindings.enabled) return result;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(bindings, before)) {
    result.unavailable_reason = "current_heir_descendant_frame_changed";
    return result;
  }
  result.played_character_id = before.played_character_id;
  result.date_raw = before.clock.date_raw;
  void *heir = xar::ck3_12004::ResolveCoreCharacter(
      bindings.context.core, heir_character_id);
  void *played = xar::ck3_12004::ResolveCoreCharacter(
      bindings.context.core, before.played_character_id);
  if (heir_character_id <= 0 || heir == nullptr || played == nullptr ||
      Load<void *>(heir, kCharacterDeathDataOffset) != nullptr) {
    result.unavailable_reason = "current_heir_descendant_identity_unavailable";
    return result;
  }
  result.played_lineage = ReadLineage(bindings, played);
  result.heir_lineage = ReadLineage(bindings, heir);
  const void *family = Load<const void *>(
      heir, family_relationships_abi::kCharacterFamilyOffset);
  result.family_present = family != nullptr;
  const std::uint32_t *data = nullptr;
  std::int32_t count = 0;
  if (family == nullptr) {
    result.status = Status::partial;
    result.unavailable_reason = "current_heir_family_absent";
  } else {
    data = Load<const std::uint32_t *>(family, 0x38);
    count = Load<std::int32_t>(family, 0x44);
    result.native_child_count_raw = count;
    result.data_pointer_present = data != nullptr;
    if (count < 0) {
      result.status = Status::partial;
      result.unavailable_reason = "native_child_count_negative";
    } else if (count > 0 && data == nullptr) {
      result.status = Status::partial;
      result.unavailable_reason = "native_child_data_unavailable";
    } else {
      result.status = Status::available;
      result.unavailable_reason = {};
      result.roster_complete = true;
      result.rows.reserve(static_cast<std::size_t>(count));
      for (std::int32_t index = 0; index < count; ++index) {
        ck3_11906::CurrentFirstHeirDescendantRowV1 row{};
        row.occurrence_index = static_cast<std::uint32_t>(index);
        row.raw_character_id = data[index];
        void *child = xar::ck3_12004::ResolveCoreCharacter(
            bindings.context.core,
            std::bit_cast<std::int32_t>(row.raw_character_id));
        row.generation_valid = child != nullptr;
        if (child != nullptr) {
          row.alive = Load<void *>(child, kCharacterDeathDataOffset) == nullptr;
          const void *child_family = Load<const void *>(
              child, family_relationships_abi::kCharacterFamilyOffset);
          row.parent_family_present = child_family != nullptr;
          if (child_family != nullptr) {
            // Actual inline is_child_of compares parent slots0/4 with full ID18.
            const auto parent_0 = Load<std::uint32_t>(child_family, 0x0);
            const auto parent_4 = Load<std::uint32_t>(child_family, 0x4);
            const auto heir_raw = Load<std::uint32_t>(heir, kCharacterFullIdOffset);
            row.parent_0_character_id_raw = parent_0;
            row.parent_4_character_id_raw = parent_4;
            row.child_of_heir = parent_0 == heir_raw || parent_4 == heir_raw;
          } else {
            row.child_of_heir = false;
          }
          // Dead Character rows remain observable; ReadCharacterValue would
          // impose liveness, so use the existing lineage-only reader directly.
          row.lineage = ReadLineage(bindings, child);
        } else {
          row.lineage.unavailable_reason = "descendant_full_id_unavailable";
        }
        result.rows.push_back(std::move(row));
      }
    }
  }
  const bool header_same = family == nullptr ||
      (Load<const std::uint32_t *>(family, 0x38) == data &&
       Load<std::int32_t>(family, 0x44) == count);
  if (!Frame(bindings, after) || !SameFrame(before, after) ||
      xar::ck3_12004::ResolveCoreCharacter(bindings.context.core,
                                         heir_character_id) != heir ||
      xar::ck3_12004::ResolveCoreCharacter(bindings.context.core,
                                         before.played_character_id) != played ||
      Load<const void *>(heir, family_relationships_abi::kCharacterFamilyOffset) !=
          family || !header_same) {
    ck3_11906::CurrentFirstHeirDescendantsReadV1 changed{};
    changed.heir_character_id = heir_character_id;
    changed.played_character_id = before.played_character_id;
    changed.date_raw = before.clock.date_raw;
    changed.unavailable_reason = "current_heir_descendant_frame_changed";
    return changed;
  }
  return result;
}

} // namespace xar::ck3_12004
#endif

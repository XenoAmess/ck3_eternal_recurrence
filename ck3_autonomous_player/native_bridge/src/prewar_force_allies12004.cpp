#include "xar_bridge/prewar_force_allies12004.hpp"

#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
namespace alliance = ck3_12002::family_obligations_alliance;

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}

void SetReason(PrewarOwnerAllies12004 &output, std::string_view value,
               std::string_view *reason) noexcept {
  output.reason = value;
  if (reason != nullptr) *reason = value;
}

bool SourceIds(const void *container, std::size_t stride, bool has_capacity,
               std::int32_t &source_count, std::int32_t &visited_count,
               std::vector<std::int32_t> &ids) {
  const auto data = Load<const std::byte *>(container, 0);
  source_count = Load<std::int32_t>(container, 0xC);
  if (source_count < 0 || source_count > 65'536 ||
      (source_count != 0 && data == nullptr)) return false;
  // Actual4's typed spouse receiver closes capacity+8. The relation lookup
  // closes data/count/stride only; do not infer a relation-capacity operand.
  if (has_capacity) {
    const auto capacity = Load<std::int32_t>(container, 8);
    if (capacity < source_count || capacity > 65'536) return false;
  }
  for (std::int32_t index = 0; index < source_count; ++index) {
    const auto id = Load<std::int32_t>(
        data, static_cast<std::size_t>(index) * stride);
    if (id != -1) ids.push_back(id);
    ++visited_count;
  }
  return true;
}
} // namespace

bool ReadPrewarOwnerAllies12004(
    const alliance::Bindings &bindings,
    const ck3_12002::CoreSnapshotPrefix &frame,
    std::int32_t owner_character_id, PrewarOwnerAllies12004 &output,
    std::string_view *reason) noexcept {
  output = {};
  output.owner_character_id = owner_character_id;
  if (reason != nullptr) *reason = {};
  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.core.character_storage_slot == nullptr ||
      bindings.is_allied == nullptr) {
    SetReason(output, "prewar_owner_allies_binding_unavailable", reason);
    return false;
  }
  if (!frame.clock.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive) {
    SetReason(output, "prewar_owner_allies_paused_played_frame_required", reason);
    return false;
  }
  try {
    // Keep the real player as the mailbox/frame identity. Never substitute the
    // foreign owner into frame.played_character_id to reach the old reader.
    const void *const player = ck3_12004::ResolveCoreCharacter(
        bindings.core, frame.played_character_id);
    if (player == nullptr ||
        Load<const void *>(player, kCharacterDeathDataOffset) != nullptr) {
      SetReason(output, "prewar_owner_allies_played_full_id_unavailable", reason);
      return false;
    }
    const void *const owner = ck3_12004::ResolveCoreCharacter(
        bindings.core, owner_character_id);
    if (owner == nullptr) {
      SetReason(output, "prewar_owner_allies_owner_full_id_unavailable", reason);
      return false;
    }
    output.owner_verified = true;
    output.owner_alive =
        Load<const void *>(owner, kCharacterDeathDataOffset) == nullptr;
    if (!output.owner_alive) {
      SetReason(output, "prewar_owner_allies_owner_not_alive", reason);
      return false;
    }

    const auto *family = Load<const std::byte *>(
        owner, alliance::kCharacterFamilyOffset);
    output.family_component_present = family != nullptr;
    if (family == nullptr) {
      // The native null-component branch selects an empty fallback source.
      output.family_source_count = 0;
      output.family_source_complete = true;
      output.family_betrothed_observed = true;
    } else {
      output.family_source_complete = SourceIds(
          family + alliance::kFamilySpousesOffset, 4, true,
          output.family_source_count, output.family_source_visited_count,
          output.source_character_ids);
      output.family_betrothed_character_id = Load<std::int32_t>(
          family, alliance::kFamilyBetrothedOffset);
      output.family_betrothed_observed = true;
      if (output.family_betrothed_character_id != -1)
        output.source_character_ids.push_back(output.family_betrothed_character_id);
    }

    const auto *relations = Load<const std::byte *>(
        owner, alliance::kCharacterRelationsOffset);
    output.relations_component_present = relations != nullptr;
    if (relations == nullptr) {
      output.relations_source_count = 0;
      output.relations_source_complete = true;
    } else {
      output.relations_source_complete = SourceIds(
          relations + alliance::kRelationsRowsOffset, 16, false,
          output.relations_source_count, output.relations_source_visited_count,
          output.source_character_ids);
    }

    auto &ids = output.source_character_ids;
    std::sort(ids.begin(), ids.end());
    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
    for (const auto id : ids) {
      if (id == owner_character_id) continue;
      const void *const candidate = ck3_12004::ResolveCoreCharacter(
          bindings.core, id);
      if (candidate == nullptr) {
        output.unresolved_source_character_ids.push_back(id);
        continue;
      }
      if (Load<const void *>(candidate, kCharacterDeathDataOffset) != nullptr) {
        output.dead_source_character_ids.push_back(id);
        continue;
      }
      const PrewarOwnerAlly12004 sampled{
          id, bindings.is_allied(owner, candidate),
          bindings.is_allied(candidate, owner),
          Load<const void *>(candidate, alliance::kCharacterRealmOffset) != nullptr};
      output.native_membership_samples.push_back(sampled);
      ++output.native_pair_predicate_sampled_count;
      if (sampled.forward_is_allied && sampled.reverse_is_allied)
        output.allies.push_back(sampled);
    }
    output.collection_complete = output.family_source_complete &&
        output.family_betrothed_observed && output.relations_source_complete &&
        output.unresolved_source_character_ids.empty();
    if (!output.family_source_complete)
      SetReason(output, "prewar_owner_allies_family_source_partial", reason);
    else if (!output.relations_source_complete)
      SetReason(output, "prewar_owner_allies_relations_source_partial", reason);
    else if (!output.unresolved_source_character_ids.empty())
      SetReason(output, "prewar_owner_allies_unresolved_source_partial", reason);
    return true;
  } catch (...) {
    output.collection_complete = false;
    SetReason(output, "prewar_owner_allies_native_capture_exception", reason);
    return false;
  }
}

} // namespace xar::ck3_12004

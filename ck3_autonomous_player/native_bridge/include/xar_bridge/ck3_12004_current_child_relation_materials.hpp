#pragma once

#include "xar_bridge/ck3_12004_child_guardian_presence.hpp"
#include <utility>

namespace xar::ck3_12004 {

struct CurrentChildRelationMaterialRow12004V1 {
  CurrentChildRelationPeerIdentities12004V1 peers;
  ChildGuardianMaterialPresence12004V1 named_guardian_material;
};

// The caller binds these IDs to the current query's selected actual living
// child rows. Roster-bound identifies this source join; it does not assert
// complete classification of every raw descendant occurrence.
// This is a generic peer/material observation, with named descriptor matching;
// it is not a Character.HasGuardian or education-guardian collection result.
struct CurrentChildrenRelationMaterials12004V1 {
  bool roster_bound{};
  bool collection_available{};
  std::string_view unavailable_reason{"current_child_roster_not_observed"};
  std::vector<std::uint32_t> child_character_ids;
  std::vector<CurrentChildRelationMaterialRow12004V1> rows;
};

inline CurrentChildrenRelationMaterials12004V1
ReadCurrentChildrenRelationMaterials12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    const GuardianFactoryDiscoveryMetadata12004V1 &metadata,
    bool roster_bound,
    const std::vector<std::uint32_t> &child_character_ids) noexcept {
  CurrentChildrenRelationMaterials12004V1 output{};
  output.roster_bound = roster_bound;
  if (!roster_bound) return output;
  try {
    output.child_character_ids = child_character_ids;
    for (const auto id : child_character_ids) {
      CurrentChildRelationMaterialRow12004V1 row{};
      row.peers = ReadCurrentChildRelationPeerIdentities12004V1(
          environment, metadata, id);
      row.named_guardian_material = ReadCurrentChildGuardianMaterialPresence12004V1(
          environment, metadata, row.peers);
      output.rows.push_back(std::move(row));
    }
    // Each child retains its own true/false/unavailable observation. A finished
    // collection never makes unavailable peer input into a false relation.
    output.collection_available = true;
    output.unavailable_reason = {};
  } catch (...) {
    output.collection_available = false;
    output.unavailable_reason = "child_relation_material_collection_exception";
    output.rows.clear();
  }
  return output;
}

} // namespace xar::ck3_12004

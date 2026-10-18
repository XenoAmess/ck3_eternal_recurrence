#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct ArmyOriginAdjacencyRowV1 {
  std::uint32_t occurrence_index = 0;
  std::int32_t target_province_id = -1;
  friend bool operator==(const ArmyOriginAdjacencyRowV1 &,
                         const ArmyOriginAdjacencyRowV1 &) = default;
};
struct ArmyOriginAdjacencyV1 {
  // Reader samples are not published until the owning preview's A/B join.
  bool available = false;
  std::string unavailable_reason = "origin_adjacency_not_sampled";
  std::int32_t source_province_id = -1;
  std::optional<std::uint64_t> source_province_identity, source_map_node_identity;
  std::optional<std::uint64_t> adjacency_data_identity;
  std::optional<std::int32_t> native_count;
  std::optional<std::vector<ArmyOriginAdjacencyRowV1>> rows;
  bool collection_complete = false;
  bool truncated = false;
  bool identity_before_after_match = false;
  friend bool operator==(const ArmyOriginAdjacencyV1 &,
                         const ArmyOriginAdjacencyV1 &) = default;
};
} // namespace xar::game

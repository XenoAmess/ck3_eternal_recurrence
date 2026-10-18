#pragma once
#include "xar_bridge/army_origin_adjacency_v1.hpp"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {
inline constexpr std::int32_t kOriginAdjacencyPublishedMaximum12004 = 64;

// Reuses the actual4 route/CampaignRoot map-node row layout. This reads the
// origin graph rows only, without invoking a provider, pathfinder or predicate.
// See episode04-origin-adjacency-publisher-12004.md for exact source pins.
template<class ReadAt>
game::ArmyOriginAdjacencyV1 ReadOriginAdjacency12004(
    const void *source, std::int32_t source_id, ReadAt read_at) {
  game::ArmyOriginAdjacencyV1 out{};
  out.source_province_id = source_id;
  const auto read = [&]<class T>(const void *base, std::size_t offset) -> std::optional<T> {
    T value{};
    if (!base || !read_at(base, offset, &value, sizeof(value))) return std::nullopt;
    return value;
  };
  const auto fail = [&](const char *reason) {
    out.available = false;
    out.unavailable_reason = reason;
    out.collection_complete = false;
    out.truncated = false;
    out.rows.reset();
    return out;
  };
  if (source_id <= 0 || !source) return fail("origin_province_unresolved");
  out.source_province_identity = static_cast<std::uint64_t>(
      reinterpret_cast<std::uintptr_t>(source));
  if (read.template operator()<std::int32_t>(source, 0x10) != source_id ||
      read.template operator()<std::uint32_t>(source, 0x85C) != 0x50726F76U)
    return fail("origin_province_identity_unavailable");
  const auto node = read.template operator()<const void *>(source, 0x08);
  if (!node) return fail("origin_map_node_read_failed");
  if (!*node) return fail("origin_map_node_null");
  out.source_map_node_identity = static_cast<std::uint64_t>(
      reinterpret_cast<std::uintptr_t>(*node));
  out.native_count = read.template operator()<std::int32_t>(*node, 0x5C);
  if (!out.native_count) return fail("origin_adjacency_count_read_failed");
  if (*out.native_count < 0)
    return fail("origin_adjacency_count_out_of_bounds");
  out.rows.emplace();
  if (*out.native_count != 0) {
    const auto data = read.template operator()<const void *>(*node, 0x50);
    if (!data) return fail("origin_adjacency_data_read_failed");
    if (!*data) return fail("origin_adjacency_data_null");
    out.adjacency_data_identity = static_cast<std::uint64_t>(
        reinterpret_cast<std::uintptr_t>(*data));
    const auto count = std::min(*out.native_count, kOriginAdjacencyPublishedMaximum12004);
    out.rows->reserve(static_cast<std::size_t>(count));
    for (std::int32_t index = 0; index < count; ++index) {
      const auto province_id = read.template operator()<std::int32_t>(
          *data, static_cast<std::size_t>(index) * 0x30 + 0x04);
      if (!province_id) return fail("origin_adjacency_row_read_failed");
      // The source body proves target ID, but does not read the row's kind.
      if (*province_id <= 0)
        return fail("origin_adjacency_row_out_of_bounds");
      out.rows->push_back({static_cast<std::uint32_t>(index), *province_id});
    }
  }
  out.truncated = *out.native_count > kOriginAdjacencyPublishedMaximum12004;
  out.collection_complete = !out.truncated;
  out.available = true;
  out.unavailable_reason.clear();
  return out;
}

inline game::ArmyOriginAdjacencyV1 FinishOriginAdjacency12004(
    const game::ArmyOriginAdjacencyV1 &before,
    const game::ArmyOriginAdjacencyV1 &after, bool owning_sample_stable) {
  auto out = before;
  const auto fail = [&](const char *reason) {
    out.available = false;
    out.unavailable_reason = reason;
    out.collection_complete = false;
    out.truncated = false;
    out.identity_before_after_match = false;
    out.rows.reset();
    return out;
  };
  if (!owning_sample_stable) return fail("origin_adjacency_owning_identity_changed");
  if (!before.available) return out;
  if (!after.available) return fail("origin_adjacency_after_read_failed");
  if (before != after) return fail("origin_adjacency_changed_during_preview");
  out.identity_before_after_match = true;
  return out;
}
} // namespace xar::ck3_12004

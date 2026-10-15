#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <span>
namespace xar::presentation {
using Bounds = std::array<std::int32_t, 4>;
inline bool ValidBounds(const Bounds &b) noexcept {
  return b[0] <= b[2] && b[1] <= b[3];
}
inline bool UnionBounds(Bounds &aggregate, const Bounds &next,
                        bool &initialized) noexcept {
  if (!ValidBounds(next)) return false;
  if (!initialized) { aggregate = next; initialized = true; return true; }
  aggregate = {std::min(aggregate[0], next[0]), std::min(aggregate[1], next[1]),
               std::max(aggregate[2], next[2]), std::max(aggregate[3], next[3])};
  return true;
}
// Native title zoom buckets use a square extent. Padding reserves HUD and
// overlay margins. This model selects a bucket; it is not a projection proof.
inline bool ViewportExtent(const Bounds &b, std::uint32_t width,
                           std::uint32_t height, float padding,
                           std::int32_t &extent) noexcept {
  if (!ValidBounds(b) || width < 320 || height < 240 ||
      !std::isfinite(padding) || padding < 0 || padding >= .45F) return false;
  const auto x = static_cast<double>(b[2]) - b[0];
  const auto z = static_cast<double>(b[3]) - b[1];
  const auto aspect = static_cast<double>(width) / height;
  const auto demand = std::ceil(std::max(x / std::min(1.0, aspect), z) /
                               (1.0 - 2.0 * padding));
  if (demand < 0 || demand > std::numeric_limits<std::int32_t>::max()) return false;
  extent = static_cast<std::int32_t>(demand);
  return true;
}
inline bool NativeBucket(std::int32_t extent,
                         std::span<const std::int32_t> thresholds,
                         std::size_t &bucket) noexcept {
  if (extent < 0 || thresholds.empty() || thresholds.size() > 4096) return false;
  bucket = 0;
  for (std::size_t i = 0; i < thresholds.size(); ++i)
    if (thresholds[i] < 0 || (i && thresholds[i] > thresholds[i - 1])) return false;
  for (std::size_t i = 0; i < thresholds.size(); ++i)
    if (extent > thresholds[i]) { bucket = i; break; }
  return true;
}
} // namespace xar::presentation

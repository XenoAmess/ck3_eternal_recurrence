#include "xar_bridge/realm_camera_geometry_v1.hpp"
#include "xar_bridge/camera_presentation_v1.hpp"
#include <iostream>

// Exact authored 1.20.0.4 title thresholds and independently reviewed buckets.
static int TestVanillaTerminalSentinel() {
  using namespace xar::presentation;
  const std::array<std::int32_t, 8> vanilla{1000, 800, 600, 400, 300, 200, 100, -1};
  const std::array<std::array<std::int32_t, 2>, 18> expected{{
      {0, 7}, {1, 7}, {50, 7}, {100, 7}, {101, 6}, {200, 6},
      {201, 5}, {300, 5}, {301, 4}, {400, 4}, {401, 3}, {600, 3},
      {601, 2}, {800, 2}, {801, 1}, {1000, 1}, {1001, 0}, {100000, 0}}};
  std::size_t bucket = 0;
  int checks = 0;
  for (const auto &row : expected) {
    if (!NativeBucket(row[0], vanilla, bucket) ||
        bucket != static_cast<std::size_t>(row[1])) return -1;
    ++checks;
  }
  if (NativeBucket(-1, vanilla, bucket)) return -1;
  ++checks;
  if (NativeBucket(0, std::array<std::int32_t, 3>{100, 200, -1}, bucket)) return -1;
  ++checks;
  if (NativeBucket(0, std::array<std::int32_t, 2>{100, -2}, bucket)) return -1;
  ++checks;
  if (NativeBucket(0, {}, bucket)) return -1;
  ++checks;
  if (!NativeBucket(0, std::array<std::int32_t, 1>{-1}, bucket) || bucket != 0) return -1;
  ++checks;
  std::int32_t extent = -1;
  if (!ViewportExtent({1898, 2444, 1898, 2444}, 2560, 1440, .15F, extent) || extent != 0) return -1;
  return checks + 1;
}

int main() {
  if (TestVanillaTerminalSentinel() != 24) return 8;
  using namespace xar::presentation;
  Bounds aggregate{}; bool initialized = false;
  if (!UnionBounds(aggregate, {10, 20, 100, 200}, initialized) ||
      !UnionBounds(aggregate, {10000, -200, 11000, 10}, initialized) ||
      aggregate != Bounds{10, -200, 11000, 200}) return 1;
  if (UnionBounds(aggregate, {3, 4, 2, 5}, initialized)) return 2;
  std::int32_t wide = 0, narrow = 0, padded = 0;
  if (!ViewportExtent({0, 0, 1000, 500}, 1920, 1080, 0, wide) || wide != 1000 ||
      !ViewportExtent({0, 0, 1000, 500}, 600, 1200, 0, narrow) || narrow != 2000 ||
      !ViewportExtent({0, 0, 1000, 500}, 1920, 1080, .15F, padded) || padded <= wide)
    return 3;
  if (ViewportExtent({INT_MIN, 0, INT_MAX, 10}, 1920, 1080, .15F, padded) ||
      ViewportExtent({0, 0, 1, 1}, 10, 10, .15F, padded)) return 4;
  const std::array<std::int32_t, 4> thresholds{4000, 2000, 1000, 0};
  std::size_t bucket = 0;
  if (!NativeBucket(1500, thresholds, bucket) || bucket != 2 ||
      !NativeBucket(11000, thresholds, bucket) || bucket != 0) return 5;
  if (NativeBucket(1500, std::array<std::int32_t, 2>{1, 2}, bucket)) return 6;
  if (sizeof(Request) != 168 || offsetof(Shared, request) != 24 ||
      offsetof(Shared, result) != 192 || offsetof(Result, county_ids) != 104) return 7;
  std::cout << "realm union, enclaves, viewport padding, native buckets and wire layout passed\n";
  return 0;
}

#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace xar::ck3_12004 {
using DeclarationCandidateMemoryReader12004 = bool (*)(
    const void *, void *, std::size_t) noexcept;

// Current31EFBC0 modes1..4 ->31EF2F0 searches defender pointer in the
// actor+1C8 cache: replacement+8E0 if count+8EC !=0, otherwise+688; then+7B0.
// Missing/malformed storage is unavailable, never a certified empty set.
// This copies the same pointer union, including duplicates/nulls/stale values;
// membership is later tested against current valid character-slot pointers.
inline bool ReadDeclarationRealmCandidates12004(
    void *actor, DeclarationCandidateMemoryReader12004 read,
    std::vector<void *> &out) noexcept {
  out.clear();
  void *cache = nullptr;
  if (!actor || !read || !read(static_cast<std::byte *>(actor) + 0x1C8,
                              &cache, sizeof(cache)) || !cache) return false;
  struct PointerVector { void **data; std::int32_t capacity, count; } first{}, second{};
  static_assert(sizeof(PointerVector) == 16);
  const auto *bytes = static_cast<const std::byte *>(cache);
  std::int32_t replacement_count = 0;
  if (!read(bytes + 0x8EC, &replacement_count, sizeof(replacement_count)) ||
      !read(bytes + (replacement_count != 0 ? 0x8E0 : 0x688), &first, sizeof(first)) ||
      !read(bytes + 0x7B0, &second, sizeof(second))) return false;
  const auto valid = [](const PointerVector &v) {
    return v.capacity >= 0 && v.count >= 0 && v.count <= v.capacity &&
           v.count <= 1'000'000 && (!v.count || v.data);
  };
  if (!valid(first) || !valid(second) ||
      static_cast<std::uint64_t>(first.count) + second.count > 1'000'000) return false;
  out.resize(static_cast<std::size_t>(first.count) + second.count);
  if ((first.count && !read(first.data, out.data(), static_cast<std::size_t>(first.count) * sizeof(void *))) ||
      (second.count && !read(second.data, out.data() + first.count,
                             static_cast<std::size_t>(second.count) * sizeof(void *)))) {
    out.clear(); return false;
  }
  return true;
}
} // namespace xar::ck3_12004

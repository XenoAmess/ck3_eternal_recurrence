#include "ghw_object_links_12004.hpp"
#include <array>
#include <limits>

namespace xar::ck3_12004::religion::ghw_links_candidate {
namespace {
// The engine masks a 24-bit component index. The largest count below permits
// every representable non-null index; it is a structural bound, not a scan.
constexpr std::uint32_t kMaximumReferenceCount = 0x1000000u;
constexpr std::uint32_t kIndexMask = 0x00ffffffu;
struct Pass {
  Observation value;
  // Resolution pointer/metadata fingerprints are private and never serialized.
  // Fields are explicit; there is no padding-dependent memcmp.
  std::array<std::uintptr_t, 6> pointers{};
  std::array<std::uint32_t, 6> words{};
};
bool Add(std::uintptr_t a, std::uintptr_t b, std::uintptr_t &out) noexcept {
  if (b > std::numeric_limits<std::uintptr_t>::max() - a) return false;
  out = a + b;
  return true;
}
template <class T> bool Load(const Access &a, std::uintptr_t base,
    std::uintptr_t offset, T &out, Failure &failure) noexcept {
  std::uintptr_t address = 0;
  if (!Add(base, offset, address) ||
      sizeof(T) - 1 > std::numeric_limits<std::uintptr_t>::max() - address) {
    failure = Failure::arithmetic_overflow;
    return false;
  }
  if (!a.read_memory(a.context, address, &out, sizeof(T))) {
    failure = Failure::memory_unreadable;
    return false;
  }
  return true;
}
bool Resolve(const Access &a, std::uintptr_t slot,
    std::uint32_t full_reference, std::uintptr_t identity_offset,
    std::uintptr_t magic_offset, std::uint32_t expected_magic,
    Pass &pass, std::size_t which, std::uintptr_t &object) noexcept {
  auto &failure = pass.value.failure;
  auto &database = pass.pointers[which * 3];
  auto &table = pass.pointers[which * 3 + 1];
  auto &identity = pass.words[which * 3 + 1];
  auto &magic = pass.words[which * 3 + 2];
  auto &count = pass.words[which * 3];
  if (!Load(a, a.image_base, slot, database, failure)) return false;
  if (!database) { failure = Failure::database_unavailable; return false; }
  if (!Load(a, database, 0x2c, count, failure)) return false;
  if (count > kMaximumReferenceCount) {
    failure = Failure::database_count_invalid;
    return false;
  }
  const auto index = full_reference & kIndexMask;
  if (index >= count) {
    failure = Failure::reference_index_out_of_range;
    return false;
  }
  if (!Load(a, database, 0x20, table, failure)) return false;
  if (!table) { failure = Failure::table_unavailable; return false; }
  // index <= 0xffffff, hence 16*index+8 fits even a 32-bit uintptr_t.
  const auto entry_offset = static_cast<std::uintptr_t>(index) * 16u + 8u;
  if (!Load(a, table, entry_offset, object, failure)) return false;
  pass.pointers[which * 3 + 2] = object;
  if (!object) { failure = Failure::object_unavailable; return false; }
  if (!Load(a, object, identity_offset, identity, failure)) return false;
  if (identity != full_reference) {
    failure = Failure::generation_mismatch;
    return false;
  }
  if (!Load(a, object, magic_offset, magic, failure)) return false;
  if (magic != expected_magic) {
    failure = Failure::magic_mismatch;
    return false;
  }
  return true;
}
Pass Capture(const Access &a) noexcept {
  Pass p{};
  auto &v = p.value;
  std::uint32_t ghw_ref = 0;
  if (!Load(a, a.bound_faith, kFaithGhwReferenceOffset, ghw_ref, v.failure))
    return p;
  v.ghw_reference_full_id = ghw_ref;
  v.faith_has_offensive_ghw = ghw_ref != kNullReference;
  if (ghw_ref == kNullReference) {
    v.ghw = State::absent;
    v.war = State::absent; // No war reachable through this Faith's GHW link.
    v.available = true;
    return p;
  }
  std::uintptr_t ghw = 0;
  if (!Resolve(a, kGhwDatabaseSlotRva, ghw_ref, kGhwIdentityOffset,
      kGhwMagicOffset, kGhwMagic, p, 0, ghw)) return p;
  v.ghw = State::present;
  std::uint32_t war_ref = 0;
  if (!Load(a, ghw, kGhwWarReferenceOffset, war_ref, v.failure)) return p;
  v.war_reference_full_id = war_ref;
  v.has_war_started = war_ref != kNullReference;
  if (war_ref == kNullReference) {
    v.war = State::absent;
    v.available = true;
    return p;
  }
  std::uintptr_t war = 0;
  if (!Resolve(a, kWarDatabaseSlotRva, war_ref, kWarIdentityOffset,
      kWarMagicOffset, kWarMagic, p, 1, war)) return p;
  v.war = State::present;
  v.available = true;
  return p;
}
bool Equal(const Pass &a, const Pass &b) noexcept {
  const auto &x = a.value;
  const auto &y = b.value;
  return a.pointers == b.pointers && a.words == b.words &&
      x.available == y.available && x.ghw == y.ghw && x.war == y.war &&
      x.failure == y.failure &&
      x.ghw_reference_full_id == y.ghw_reference_full_id &&
      x.war_reference_full_id == y.war_reference_full_id &&
      x.faith_has_offensive_ghw == y.faith_has_offensive_ghw &&
      x.has_war_started == y.has_war_started;
}
} // namespace
bool ReadGhwObjectLinks12004(const Access &a, Observation &out) noexcept {
  out = {};
  if (!a.read_memory || !a.image_base || !a.bound_faith ||
      a.executable_sha256 != kExactSha) {
    out.failure = Failure::input_not_admitted;
    return false;
  }
  const auto first = Capture(a);
  const auto second = Capture(a);
  if (!Equal(first, second)) {
    out.failure = Failure::observations_changed;
    return false;
  }
  out = second.value;
  out.stable_two_pass = true;
  return out.available;
}
const char *FailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::input_not_admitted: return "input_not_admitted";
  case Failure::memory_unreadable: return "memory_unreadable";
  case Failure::arithmetic_overflow: return "arithmetic_overflow";
  case Failure::database_unavailable: return "database_unavailable";
  case Failure::database_count_invalid: return "database_count_invalid";
  case Failure::reference_index_out_of_range: return "reference_index_out_of_range";
  case Failure::table_unavailable: return "table_unavailable";
  case Failure::object_unavailable: return "object_unavailable";
  case Failure::generation_mismatch: return "generation_mismatch";
  case Failure::magic_mismatch: return "magic_mismatch";
  case Failure::observations_changed: return "observations_changed";
  }
  return "unknown";
}
} // namespace xar::ck3_12004::religion::ghw_links_candidate

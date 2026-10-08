#include "xar_bridge/actor_cached_succession12004_v1.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>

// Pure fixture-owned memory and full-ID resolution. The production reader and
// serializer compile unchanged; no native classifier, process, or CK3 runs.
namespace {
namespace cache = xar::ck3_12004::actor_cached_succession;
constexpr std::uint32_t kActorId = 0x01000001U;
constexpr std::uint32_t kDate = 53220000U;
constexpr std::uint64_t kEpoch = 287;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

template <typename T>
void Put(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

template <typename T>
std::uintptr_t Address(T &object) noexcept {
  return reinterpret_cast<std::uintptr_t>(object.data());
}

enum class Mutation {
  none, reorder, data_pointer, count, owner_pointer, owner_full_id,
  land_state, candidate_full_id, unresolved_owner, unresolved_candidate,
  sentinel_fallback
};

struct Fixture {
  std::array<std::byte, 0x1C8> actor{}, alternate_actor{};
  std::array<std::byte, 0x3B0> land{}, alternate_land{};
  std::array<std::byte, 0x20> sentinel_fallback{};
  std::array<std::array<std::byte, 0x20>, 45> candidates{};
  std::array<std::uint32_t, 45> ids{}, alternate_ids{};
  Mutation mutation = Mutation::none;
  std::size_t list_reads = 0;
  std::size_t owner_land_reads = 0;
  std::size_t memory_reads = 0;
  std::size_t resolutions = 0;
  std::size_t sentinel_resolutions = 0;
  bool capacity_touched = false;
  bool mutated = false;

  explicit Fixture(Mutation mode = Mutation::none) : mutation(mode) {
    Put(actor.data(), xar::ck3_12004::kCharacterFullIdOffset, kActorId);
    Put(alternate_actor.data(), xar::ck3_12004::kCharacterFullIdOffset, kActorId);
    Put(actor.data(), cache::kActorLandStateOffset, Address(land));
    Put(alternate_actor.data(), cache::kActorLandStateOffset, Address(land));
    for (std::size_t index = 0; index < ids.size(); ++index) {
      // Preserve the high generation byte as uint32, including signed IDs.
      ids[index] = 0x81000010U + static_cast<std::uint32_t>(index);
      Put(candidates[index].data(), xar::ck3_12004::kCharacterFullIdOffset,
          ids[index]);
    }
    ids[41] = ids[0];
    ids[42] = kActorId;
    if (mutation == Mutation::sentinel_fallback) {
      ids[44] = 0xFFFFFFFFU;
      Put(sentinel_fallback.data(), xar::ck3_12004::kCharacterFullIdOffset,
          std::uint32_t{0xFFFFFFFFU});
    }
    alternate_ids = ids;
    SetHeader(land, Address(ids), 45);
    SetHeader(alternate_land, Address(ids), 45);
  }

  static void SetHeader(std::array<std::byte, 0x3B0> &object,
                        std::uintptr_t data, std::int32_t count) noexcept {
    Put(object.data(), cache::kLandStateCachedSuccessorsOffset, data);
    Put(object.data(), cache::kLandStateCachedSuccessorsOffset +
        cache::kCachedSuccessorsCountOffset, count);
  }

  cache::Bindings Bind() noexcept {
    return cache::BindImage(0x140000000ULL, xar::ck3_12004::kExecutableSha256,
                            &ReadMemory, &Resolve, this);
  }

  void MutateHeaderOrRows() noexcept {
    if (mutated) return;
    switch (mutation) {
    case Mutation::reorder: std::swap(ids[0], ids[44]); break;
    case Mutation::data_pointer: SetHeader(land, Address(alternate_ids), 45); break;
    case Mutation::count: SetHeader(land, Address(ids), 40); break;
    case Mutation::land_state:
      Put(actor.data(), cache::kActorLandStateOffset, Address(alternate_land));
      break;
    case Mutation::owner_full_id:
      Put(actor.data(), xar::ck3_12004::kCharacterFullIdOffset, kActorId + 0x01000000U);
      break;
    default: return;
    }
    mutated = true;
  }

  template <typename T>
  static bool CopyRange(T &object, std::uintptr_t source, void *output,
                        std::size_t size) noexcept {
    const auto begin = Address(object);
    const auto bytes = sizeof(object);
    if (source < begin || source - begin > bytes ||
        size > bytes - static_cast<std::size_t>(source - begin)) return false;
    std::memcpy(output, reinterpret_cast<const void *>(source), size);
    return true;
  }

  static bool ReadMemory(void *context, std::uintptr_t source,
                         void *output, std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.memory_reads;
    for (auto *object : {&self.land, &self.alternate_land}) {
      const auto capacity = Address(*object) +
          cache::kLandStateCachedSuccessorsOffset + 8;
      if (source <= capacity + 3 && capacity >= source &&
          size > capacity - source) self.capacity_touched = true;
      if (source > capacity && source <= capacity + 3 && size != 0)
        self.capacity_touched = true;
    }
    if (source == Address(self.actor) + cache::kActorLandStateOffset &&
        ++self.owner_land_reads == 2) self.MutateHeaderOrRows();
    if (source == Address(self.ids) || source == Address(self.alternate_ids))
      ++self.list_reads;
    return CopyRange(self.actor, source, output, size) ||
        CopyRange(self.alternate_actor, source, output, size) ||
        CopyRange(self.land, source, output, size) ||
        CopyRange(self.alternate_land, source, output, size) ||
        CopyRange(self.sentinel_fallback, source, output, size) ||
        CopyRange(self.candidates, source, output, size) ||
        CopyRange(self.ids, source, output, size) ||
        CopyRange(self.alternate_ids, source, output, size);
  }

  static std::uintptr_t Resolve(void *context, std::uint32_t id) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.resolutions;
    if (id == 0xFFFFFFFFU) {
      ++self.sentinel_resolutions;
      return Address(self.sentinel_fallback);
    }
    if (id == kActorId) {
      if (self.mutation == Mutation::unresolved_owner) return 0;
      if (self.mutation == Mutation::owner_pointer && self.list_reads != 0)
        return Address(self.alternate_actor);
      return Address(self.actor);
    }
    if (id < 0x81000010U || id >= 0x81000010U + self.candidates.size()) return 0;
    const auto index = static_cast<std::size_t>(id - 0x81000010U);
    if (self.mutation == Mutation::unresolved_candidate && index == 44) return 0;
    if (self.mutation == Mutation::candidate_full_id && self.list_reads >= 2 &&
        index == 44 && !self.mutated) {
      Put(self.candidates[index].data(), xar::ck3_12004::kCharacterFullIdOffset,
          id + 0x01000000U);
      self.mutated = true;
    }
    return Address(self.candidates[index]);
  }
};

void Rejected(Mutation mutation, const char *message) {
  Fixture fixture(mutation);
  cache::Snapshot result{};
  Check(!cache::Read(fixture.Bind(), kEpoch, kActorId, kDate, result), message);
  Check(!result.available && !result.roster_complete &&
        result.ordered_candidate_character_ids_raw.empty(),
        "failed observation must not expose a partial roster");
  Check(result.capture_epoch == kEpoch && result.date_raw ==
        static_cast<std::int32_t>(kDate) && result.actor_character_id_raw == kActorId,
        "failed observation retains requested identity and frame");
  const auto wire = cache::Serialize(result);
  Check(wire.find("\"native_count\":null") != std::string::npos &&
        wire.find("\"complete_cached_successor_ids\":null") != std::string::npos &&
        wire.find("\"native_data_pointer\":null") != std::string::npos &&
        wire.find("\"land_state_pointer\":null") != std::string::npos,
        "unavailable wire must not masquerade as an empty cache");
  Check(!fixture.capacity_touched, "unproven collection capacity must never be read");
}
} // namespace

int main() {
  try {
    Fixture fixture;
    cache::Snapshot result{};
    Check(cache::Read(fixture.Bind(), kEpoch, kActorId, kDate, result),
          "stable complete native cache must be readable");
    Check(result.available && result.roster_complete && result.native_count_raw == 45 &&
          result.ordered_candidate_character_ids_raw ==
              std::vector<std::uint32_t>(fixture.ids.begin(), fixture.ids.end()) &&
          result.original_data_pointer == Address(fixture.ids) &&
          result.land_state_pointer == Address(fixture.land) &&
          result.actor_pointer == Address(fixture.actor),
          "all 45 original occurrences and original owner/header are preserved");
    Check(result.ordered_candidate_character_ids_raw[41] == fixture.ids[0] &&
          result.ordered_candidate_character_ids_raw[42] == kActorId &&
          result.ordered_candidate_character_ids_raw[44] == 0x8100003CU,
          "duplicate, self and entries beyond a 40-row scorer remain unchanged");
    const auto wire = cache::Serialize(result);
    Check(wire.find("\"schema\":\"ck3-1.20.0.4-actor-cached-succession-v1\"") !=
          std::string::npos && wire.find("\"native_count\":45") != std::string::npos &&
          wire.find(std::to_string(fixture.ids[44])) != std::string::npos &&
          wire.find("\"unavailable_reason\":null") != std::string::npos,
          "wire carries the full uint32 cache and stable successful observation");
    Check(!fixture.capacity_touched, "capacity+8 is outside admitted field reads");

    std::swap(fixture.ids[0], fixture.ids[44]);
    Check(cache::Read(fixture.Bind(), kEpoch, kActorId, kDate, result) &&
          result.capture_epoch == kEpoch &&
          result.ordered_candidate_character_ids_raw.front() == fixture.ids[0],
          "same epoch reads current ordered memory rather than memoizing an old roster");
    Fixture::SetHeader(fixture.land, Address(fixture.ids), 40);
    Check(cache::Read(fixture.Bind(), kEpoch, kActorId, kDate, result) &&
          result.native_count_raw == 40 &&
          result.ordered_candidate_character_ids_raw == std::vector<std::uint32_t>(
              fixture.ids.begin(), fixture.ids.begin() + 40),
          "a native 40-entry cache stays exactly 40, independently of earlier 45 entries");

    Fixture empty;
    Fixture::SetHeader(empty.land, 0, 0);
    Check(cache::Read(empty.Bind(), kEpoch, kActorId, kDate, result) &&
          result.available && result.roster_complete && result.native_count_raw == 0 &&
          result.ordered_candidate_character_ids_raw.empty() &&
          result.original_data_pointer == 0 && empty.list_reads == 0 &&
          cache::Serialize(result).find("\"complete_cached_successor_ids\":[]") !=
              std::string::npos,
          "resolved owner and land state with count zero and null data is legal empty");

    Rejected(Mutation::reorder, "between-pass order changes must be rejected");
    Rejected(Mutation::data_pointer, "same IDs at a changed data pointer must be rejected");
    Rejected(Mutation::count, "45 to 40 count drift must be rejected");
    Rejected(Mutation::owner_pointer, "changed resolved owner identity must be rejected");
    Rejected(Mutation::owner_full_id, "changed owner generation must be rejected");
    Rejected(Mutation::land_state, "changed land state identity must be rejected");
    Rejected(Mutation::candidate_full_id, "changed candidate generation must be rejected");
    Rejected(Mutation::unresolved_owner, "unresolved owner cannot produce legal empty");
    Rejected(Mutation::unresolved_candidate, "unresolved tail candidate cannot be silently omitted");

    Fixture sentinel(Mutation::sentinel_fallback);
    Check(!cache::Read(sentinel.Bind(), kEpoch, kActorId, kDate, result) &&
          !result.available && !result.roster_complete &&
          result.ordered_candidate_character_ids_raw.empty() &&
          sentinel.sentinel_resolutions == 0,
          "invalid candidate sentinel is rejected before a matching fallback can resolve it");

    Fixture negative;
    Fixture::SetHeader(negative.land, Address(negative.ids), -1);
    Check(!cache::Read(negative.Bind(), kEpoch, kActorId, kDate, result),
          "negative signed native count is unavailable");
    Fixture no_land;
    Put(no_land.actor.data(), cache::kActorLandStateOffset, std::uintptr_t{0});
    Check(!cache::Read(no_land.Bind(), kEpoch, kActorId, kDate, result),
          "missing land state is unavailable rather than empty");
    const auto wrong_image = cache::BindImage(0x140000000ULL, "wrong-image",
        &Fixture::ReadMemory, &Fixture::Resolve, &fixture);
    const auto reads = fixture.memory_reads;
    Check(!cache::Read(wrong_image, kEpoch, kActorId, kDate, result) &&
          fixture.memory_reads == reads,
          "wrong-image admission performs no memory read");

    std::cout << "PASS actual4 readonly actor cache: ordered 45/40, duplicate/self/high-generation IDs, "
                 "same epoch, legal empty, pointer/count/order/generation drift and unresolved IDs\n";
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

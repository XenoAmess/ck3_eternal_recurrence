#include "xar_bridge/ck3_12002_realm_law_active_collection.hpp"
#include "xar_bridge/ck3_12002_realm_law_candidate_collection.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

namespace {

using namespace xar::ck3_12002::private_law;

constexpr std::uintptr_t kBase = 0x10000000;

struct Fixture {
  std::array<std::byte, 0x8000> memory{};
  std::uintptr_t database_singleton = 0;

  template <typename T> void Store(std::uintptr_t address, const T &value) {
    assert(address >= kBase && address + sizeof(value) <= kBase + memory.size());
    std::memcpy(memory.data() + (address - kBase), &value, sizeof(value));
  }

  void Key(std::uintptr_t law, std::string_view key,
           std::uintptr_t heap_address = 0) {
    assert(key.size() < kRealmLawActiveCollectionKeyCapacity);
    if (heap_address == 0) {
      assert(key.size() <= 15);
      std::memcpy(memory.data() + (law + 0x18 - kBase), key.data(), key.size());
      Store(law + 0x18 + 0x10, static_cast<std::uint64_t>(key.size()));
      Store(law + 0x18 + 0x18, std::uint64_t{15});
    } else {
      Store(law + 0x18, heap_address);
      Store(law + 0x18 + 0x10, static_cast<std::uint64_t>(key.size()));
      Store(law + 0x18 + 0x18, std::uint64_t{63});
      std::memcpy(memory.data() + (heap_address - kBase), key.data(),
                  key.size());
    }
  }

  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto *self = static_cast<Fixture *>(context);
    if (address == 0x140000000 + 0x5D202F0 &&
        size == sizeof(self->database_singleton)) {
      std::memcpy(output, &self->database_singleton, size);
      return true;
    }
    if (address < kBase || size > self->memory.size() ||
        address - kBase > self->memory.size() - size) {
      return false;
    }
    std::memcpy(output, self->memory.data() + (address - kBase), size);
    return true;
  }
};

std::string_view KeyText(const RealmLawActiveKey &key) {
  return {key.bytes.data(), key.size};
}

struct SeenCandidates {
  std::array<std::uintptr_t, 4> addresses{};
  std::size_t count = 0;
  bool reject = false;
};

bool ObserveCandidate(void *context, std::size_t group,
                      std::size_t index, std::uintptr_t law,
                      const RealmLawCandidateCollectionRow11906 &row) noexcept {
  auto &seen = *static_cast<SeenCandidates *>(context);
  assert(group < 2 && index < 2 && seen.count < seen.addresses.size());
  assert(row.key.size != 0);
  seen.addresses[seen.count++] = law;
  return !seen.reject;
}

} // namespace

int main() {
  Fixture fixture{};
  constexpr std::uintptr_t actor = kBase + 0x100;
  constexpr std::uintptr_t context = kBase + 0x400;
  constexpr std::uintptr_t slots = kBase + 0x800;
  constexpr std::uintptr_t law1 = kBase + 0xA00;
  constexpr std::uintptr_t law2 = kBase + 0xC00;
  constexpr std::uintptr_t heap = kBase + 0xE00;
  fixture.Store(actor + 0x1B8, std::uintptr_t{kBase + 0x700});
  fixture.Store(actor + 0x1C0, context);
  fixture.Store(context + 0x200, slots);
  fixture.Store(context + 0x20C, std::int32_t{2});
  fixture.Store(slots, law1);
  fixture.Store(slots + 8, law2);
  fixture.Key(law1, "short_law");
  fixture.Key(law2, "confederate_partition_succession_law", heap);
  RealmLawActiveCollectionAccess access{
      kRealmLawActiveCollectionExeSha25612002, actor, &fixture, &Fixture::Read};
  RealmLawActiveCollection result{};
  assert(ReadRealmLawActiveCollection12002(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::none);
  assert(result.count == 2);
  assert(KeyText(result.keys[0]) == "short_law");
  assert(KeyText(result.keys[1]) ==
         "confederate_partition_succession_law");

  access.admitted_executable_sha256 = "wrong-build";
  assert(!ReadRealmLawActiveCollection12002(access, result));
  assert(result.failure ==
         RealmLawActiveCollectionFailure::exact_build_mismatch);
  RealmLawCandidateCollection11906 diagnostic{};
  assert(!ReadRealmLawCandidateCollection12002(
      access, 0x140000000, diagnostic));
  assert(diagnostic.failure ==
         RealmLawCandidateCollectionFailure::active_collection_unavailable);
  assert(diagnostic.active_failure ==
         RealmLawActiveCollectionFailure::exact_build_mismatch);
  access.admitted_executable_sha256 = kRealmLawActiveCollectionExeSha25612002;

  fixture.Store(context + 0x20C, std::int32_t{65});
  assert(!ReadRealmLawActiveCollection12002(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::count_invalid);
  fixture.Store(context + 0x20C, std::int32_t{2});

  fixture.Key(law2, "short_law");
  assert(!ReadRealmLawActiveCollection12002(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::duplicate_key);

  fixture.Key(law2, "confederate_partition_succession_law", heap);
  constexpr std::uintptr_t database = kBase + 0x1000;
  constexpr std::uintptr_t authority_group = kBase + 0x1400;
  constexpr std::uintptr_t succession_group = kBase + 0x1800;
  constexpr std::uintptr_t group_slots = kBase + 0x1C00;
  constexpr std::uintptr_t authority_slots = kBase + 0x2000;
  constexpr std::uintptr_t succession_slots = kBase + 0x2100;
  constexpr std::uintptr_t law3 = kBase + 0x2500;
  constexpr std::uintptr_t law4 = kBase + 0x2700;
  fixture.database_singleton = database;
  fixture.Store(database + 0x50, group_slots);
  fixture.Store(database + 0x5C, std::int32_t{2});
  fixture.Store(group_slots, authority_group);
  fixture.Store(group_slots + 8, succession_group);
  fixture.Key(authority_group, "crown_authority");
  fixture.Key(succession_group, "succession_order_laws", kBase + 0x3000);
  fixture.Store(authority_group + 0x58, authority_slots);
  fixture.Store(authority_group + 0x64, std::int32_t{2});
  fixture.Store(succession_group + 0x58, succession_slots);
  fixture.Store(succession_group + 0x64, std::int32_t{2});
  fixture.Store(authority_slots, law1);
  fixture.Store(authority_slots + 8, law3);
  fixture.Store(succession_slots, law2);
  fixture.Store(succession_slots + 8, law4);
  fixture.Store(law1 + 0x38, std::uint32_t{0x4744624F});
  fixture.Store(law2 + 0x38, std::uint32_t{0x4744624F});
  fixture.Store(law3 + 0x38, std::uint32_t{0x4744624F});
  fixture.Store(law4 + 0x38, std::uint32_t{0x4744624F});
  fixture.Store(law1 + 0x40, authority_group);
  fixture.Store(law2 + 0x40, succession_group);
  fixture.Store(law3 + 0x40, authority_group);
  fixture.Store(law4 + 0x40, succession_group);
  fixture.Key(law3, "crown_authority_3", kBase + 0x3100);
  fixture.Key(law4, "high_partition_succession_law", kBase + 0x3200);
  RealmLawCandidateCollection11906 candidates{};
  assert(ReadRealmLawCandidateCollection12002(access, 0x140000000,
                                             candidates));
  assert(candidates.failure == RealmLawCandidateCollectionFailure::none);
  assert(candidates.groups[0].active_found);
  assert(candidates.groups[0].candidate_count == 2);
  assert(KeyText(candidates.groups[0].active_law_key) == "short_law");
  assert(KeyText(candidates.groups[0].candidates[1].key) ==
         "crown_authority_3");
  assert(candidates.groups[1].active_found);
  assert(KeyText(candidates.groups[1].active_law_key) ==
         "confederate_partition_succession_law");
  assert(!candidates.groups[1].candidates[1].active);

  SeenCandidates seen{};
  assert(ReadRealmLawCandidateCollectionWithObserver12002(
      access, 0x140000000, &seen, &ObserveCandidate, candidates));
  assert(seen.count == 4);
  assert(seen.addresses ==
         (std::array<std::uintptr_t, 4>{law1, law3, law2, law4}));
  seen = {};
  seen.reject = true;
  assert(!ReadRealmLawCandidateCollectionWithObserver12002(
      access, 0x140000000, &seen, &ObserveCandidate, candidates));
  assert(candidates.failure ==
         RealmLawCandidateCollectionFailure::candidate_observer_failed);

  // The stock succession_order_laws group contains more than 24 definitions.
  // Visit its full native collection but only emit the feudal decisions plus
  // any current active law. Unrelated definition final terms are not queried.
  constexpr std::uintptr_t filler_base = kBase + 0x4000;
  for (std::uintptr_t i = 0; i < 27; ++i) {
    const auto law = filler_base + i * 0x100;
    fixture.Store(succession_slots + (i + 1) * 8, law);
    fixture.Store(law + 0x40, succession_group);
    if (i == 0) {
      fixture.Key(law, "opaque_unrelated_succession_law", kBase + 0x7000);
    } else {
      const std::string key = "other_" + std::to_string(i);
      fixture.Key(law, key);
    }
  }
  fixture.Store(succession_slots + 28 * 8, law4);
  fixture.Store(succession_group + 0x64, std::int32_t{29});
  seen = {};
  assert(ReadRealmLawCandidateCollectionWithObserver12002(
      access, 0x140000000, &seen, &ObserveCandidate, candidates));
  assert(candidates.groups[1].candidate_count == 2);
  assert(seen.count == 4);
  assert(seen.addresses ==
         (std::array<std::uintptr_t, 4>{law1, law3, law2, law4}));

  fixture.Store(context + 0x20C, std::int32_t{0});
  assert(ReadRealmLawActiveCollection12002(access, result));
  assert(result.count == 0);
  assert(ReadRealmLawCandidateCollection12002(access, 0x140000000, candidates));
  assert(!candidates.groups[0].active_found);
  assert(!candidates.groups[1].active_found);
  fixture.Store(context + 0x20C, std::int32_t{2});

  fixture.Store(law3 + 0x40, succession_group);
  assert(!ReadRealmLawCandidateCollection12002(access, 0x140000000, candidates));
  assert(candidates.failure ==
         RealmLawCandidateCollectionFailure::candidate_group_mismatch);
  fixture.Store(law3 + 0x40, authority_group);

  assert(!ReadRealmLawCandidateCollection12002(access, 0, candidates));
  assert(candidates.failure ==
         RealmLawCandidateCollectionFailure::module_base_unavailable);

  fixture.Key(succession_group, "other_group");
  assert(!ReadRealmLawCandidateCollection12002(access, 0x140000000,
                                              candidates));
  assert(candidates.failure ==
         RealmLawCandidateCollectionFailure::relevant_group_missing);

  std::cout << "ck3_12002_realm_law_collections_test: 12/12 GREEN\n";
}

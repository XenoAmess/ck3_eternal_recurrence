#include "xar_bridge/realm_law_active_collection_11906.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

using namespace xar::ck3_11906::private_law;

constexpr std::uintptr_t kBase = 0x10000000;

struct Fixture {
  std::array<std::byte, 0x2000> memory{};

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

} // namespace

int main() {
  Fixture fixture{};
  constexpr std::uintptr_t actor = kBase + 0x100;
  constexpr std::uintptr_t context = kBase + 0x400;
  constexpr std::uintptr_t slots = kBase + 0x800;
  constexpr std::uintptr_t law1 = kBase + 0xA00;
  constexpr std::uintptr_t law2 = kBase + 0xC00;
  constexpr std::uintptr_t heap = kBase + 0xE00;
  fixture.Store(actor + 0x1B8, context);
  fixture.Store(context + 0x200, slots);
  fixture.Store(context + 0x20C, std::int32_t{2});
  fixture.Store(slots, law1);
  fixture.Store(slots + 8, law2);
  fixture.Key(law1, "short_law");
  fixture.Key(law2, "confederate_partition_succession_law", heap);
  RealmLawActiveCollectionAccess access{
      kRealmLawActiveCollectionExeSha256, actor, &fixture, &Fixture::Read};
  RealmLawActiveCollection result{};
  assert(ReadRealmLawActiveCollection11906(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::none);
  assert(result.count == 2);
  assert(KeyText(result.keys[0]) == "short_law");
  assert(KeyText(result.keys[1]) ==
         "confederate_partition_succession_law");

  access.admitted_executable_sha256 = "wrong-build";
  assert(!ReadRealmLawActiveCollection11906(access, result));
  assert(result.failure ==
         RealmLawActiveCollectionFailure::exact_build_mismatch);
  access.admitted_executable_sha256 = kRealmLawActiveCollectionExeSha256;

  fixture.Store(context + 0x20C, std::int32_t{65});
  assert(!ReadRealmLawActiveCollection11906(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::count_invalid);
  fixture.Store(context + 0x20C, std::int32_t{2});

  fixture.Key(law2, "short_law");
  assert(!ReadRealmLawActiveCollection11906(access, result));
  assert(result.failure == RealmLawActiveCollectionFailure::duplicate_key);

  std::cout << "realm_law_active_collection_11906_test: 4/4 GREEN\n";
}

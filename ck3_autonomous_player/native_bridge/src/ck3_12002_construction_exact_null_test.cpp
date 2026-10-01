#include "ck3_12002_construction.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <unordered_map>
#include <vector>

// Offline synthetic-memory regression. Calls the production 1.20.0.2 reader;
// does not open CK3, bind native calls, or use a mailbox. Fixture IDs are local
// constants, not assertions about the current live player's identity.
namespace {

constexpr std::uintptr_t kModule = 0x100000000ULL;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kBarony = 2143;
constexpr std::int32_t kProvince = 2619;
constexpr std::uintptr_t kDefinition = 0xB10000;
constexpr std::uintptr_t kExactNull = 0xB20000;
constexpr std::uintptr_t kUnmapped = 0xA20000;
constexpr std::uintptr_t kSlots = 0x730000;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes;
  xar::game::CampaignRootFrameV1 frame{
      3, 53178312, true, true, true, true, kActor};

  template <typename T>
  void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(T); ++index) {
      bytes[address + index] = raw[index];
    }
  }

  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    const auto base = reinterpret_cast<std::uintptr_t>(address);
    auto *raw = static_cast<std::uint8_t *>(output);
    for (std::size_t index = 0; index < size; ++index) {
      const auto found = self.bytes.find(base + index);
      if (found == self.bytes.end()) return false;
      raw[index] = found->second;
    }
    return true;
  }

  static bool Capture(void *context,
                      xar::game::CampaignRootFrameV1 &output) noexcept {
    output = static_cast<Fixture *>(context)->frame;
    return true;
  }

  static bool IsMain(void *) noexcept { return true; }

  xar::ck3_12002::PlayerWorldBuildingSourceAccessV1 Access() {
    xar::ck3_12002::PlayerWorldBuildingSourceAccessV1 access{};
    access.campaign = {this, Capture, IsMain, Read, nullptr};
    return access;
  }
};

Fixture Scene() {
  Fixture f;
  f.Put(kModule + 0x5C68C50, std::uintptr_t{0x100000});
  f.Put(kModule + 0x5C6A520, std::uintptr_t{0x110000});
  f.Put(kModule + 0x5C67568, std::uintptr_t{0x400000});
  f.Put(kModule + 0x5C67570, std::uintptr_t{0x410000});
  f.Put(kModule + 0x5D1DAF8, std::uintptr_t{0x500000});
  f.Put(kModule + 0x5D1DAE0, std::uintptr_t{0x510000});
  f.Put(kModule + 0x5C67540, std::uintptr_t{0xD00000});
  f.Put(kModule + 0x5D1E320, kExactNull);

  f.Put(0x100000 + 0xA0, std::uintptr_t{0x200000});
  f.Put(0x110000 + 0x18, std::uintptr_t{0x120000});
  f.Put(0x120000 + 0x1F0, std::int32_t{7});
  f.Put(0x200000 + 0x222E8 + 0x58, std::uintptr_t{0x300000});
  f.Put(0x200000 + 0x222E8 + 0x64, std::int32_t{1});
  f.Put(0x300000, std::uintptr_t{0x310000});
  f.Put(0x310000 + 0xD8, std::int32_t{7});
  f.Put(0x310000 + 0xB0, kActor);
  f.Put(0x400000 + 0x20, std::uintptr_t{0x400020});
  f.Put(0x400000 + 0x2C, std::int32_t{30000});
  f.Put(0x400020 + static_cast<std::uintptr_t>(kActor) * 0x10 + 8,
        std::uintptr_t{0x420000});
  f.Put(0x420000 + 0x18, kActor);
  f.Put(0x420000 + 0x1D0, std::uintptr_t{0});
  f.Put(0x420000 + 0x1C0, std::uintptr_t{0x430000});
  f.Put(0x430000 + 0x1E0, std::uintptr_t{0x440000});
  f.Put(0x430000 + 0x1E8, std::int32_t{1});
  f.Put(0x430000 + 0x1EC, std::int32_t{1});
  f.Put(0x440000, kBarony);

  f.Put(0x500000 + 0x20, std::uintptr_t{0x500020});
  f.Put(0x500000 + 0x2C, std::int32_t{4000});
  f.Put(0x500020 + static_cast<std::uintptr_t>(kBarony) * 0x10 + 8,
        std::uintptr_t{0x620000});
  f.Put(0x620000 + 0x10, kBarony);
  f.Put(0x620000 + 0x48, std::uintptr_t{0x630000});
  f.Put(0x630000 + 0x64, std::int32_t{1});
  f.Put(0x620000 + 0x128, kActor);
  f.Put(0x620000 + 0x338, std::uintptr_t{0x700000});
  f.Put(0x200000 + 0x140, std::uintptr_t{0x720000});
  f.Put(0x200000 + 0x14C, std::int32_t{4000});
  f.Put(0x720000 + static_cast<std::uintptr_t>(kProvince) * 8,
        std::uintptr_t{0x700000});
  f.Put(0x700000 + 0x10, kProvince);
  f.Put(0x700000 + 0x718, std::int64_t{2468000});
  f.Put(0x700000 + 0x620 + 0x10, kSlots);
  f.Put(0x700000 + 0x620 + 0x1C, std::int32_t{3});
  f.Put(0x700000 + 0x620 + 0x68, std::uintptr_t{0});

  // The singleton is outside the registry. No singleton object fields are
  // provided: the exact pointer identifies emptiness without dereferencing it.
  f.Put(kSlots, std::uintptr_t{0});
  f.Put(kSlots + 0x10, kExactNull);
  f.Put(kSlots + 0x20, kDefinition);
  f.Put(0xD00000 + 0x50, std::uintptr_t{0xD10000});
  f.Put(0xD00000 + 0x58, std::int32_t{1});
  f.Put(0xD00000 + 0x5C, std::int32_t{1});
  f.Put(0xD10000, kDefinition);
  f.Put(kDefinition, kModule + 0x48B6CC8);
  f.Put(kDefinition + 0x10, std::int32_t{22});
  return f;
}

void Require(bool condition, const char *name) {
  if (!condition) {
    std::cerr << "RED " << name << '\n';
    std::abort();
  }
}

} // namespace

int main() {
  using namespace xar::ck3_12002;
  auto f = Scene();
  const auto observed = xar::ck3_12002::ReadPlayerWorldBuildingDefinitionSourcesV1(
      kModule, true, f.Access(), {3, kProvince, 0, 0});
  Require(observed.source_available &&
              observed.failure == PlayerWorldBuildingFailureV1::none &&
              observed.completed_buildings_observed &&
              observed.completed_buildings ==
                  std::vector<PlayerWorldCompletedBuildingV1>{
                      {kBarony, kProvince, 22, 2}} &&
              observed.active_constructions.size() == 1 &&
              !observed.active_constructions[0].active,
          "zero_and_exact_null_are_empty_registry_occupant_is_observed");

  // Append an arbitrary non-registry pointer after the valid occupant. The
  // reader must clear partial results and keep this component unavailable.
  f.Put(0x700000 + 0x620 + 0x1C, std::int32_t{4});
  f.Put(kSlots + 0x30, kUnmapped);
  const auto unknown = xar::ck3_12002::ReadPlayerWorldBuildingDefinitionSourcesV1(
      kModule, true, f.Access(), {3, kProvince, 0, 0});
  Require(unknown.source_available &&
              unknown.failure == PlayerWorldBuildingFailureV1::none &&
              !unknown.completed_buildings_observed &&
              unknown.completed_buildings.empty(),
          "unmapped_pointer_remains_unobserved_and_clears_partial_results");
  std::cout << "GREEN exact-null completed-reader focused fixture\n";
}

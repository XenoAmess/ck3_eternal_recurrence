#include "player_held_construction_model_enumerator_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>

namespace {

constexpr std::uintptr_t kModule = 0x100000000ULL;
constexpr std::int32_t kPlayerId = 29829;
constexpr std::int32_t kBarony1 = 1001;
constexpr std::int32_t kBarony2 = 1002;
constexpr std::int32_t kCounty = 1003;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes;
  xar::game::CampaignRootFrameV1 frame{
      3, 53178312, true, true, true, true, kPlayerId};
  bool main_thread = true;
  bool change_second_frame = false;
  int capture_count = 0;

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
      if (found == self.bytes.end()) {
        return false;
      }
      raw[index] = found->second;
    }
    return true;
  }

  static bool Capture(void *context,
                      xar::game::CampaignRootFrameV1 &output) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    ++self.capture_count;
    output = self.frame;
    if (self.change_second_frame && self.capture_count == 2) {
      ++output.snapshot_revision;
    }
    return true;
  }

  static bool IsMain(void *context) noexcept {
    return static_cast<Fixture *>(context)->main_thread;
  }

  xar::ck3_11906::CampaignRootAccessV1 Access() {
    return {this, Capture, IsMain, Read, nullptr};
  }
};

void Require(bool condition, const char *name) {
  if (!condition) {
    std::cerr << "RED " << name << '\n';
    std::abort();
  }
}

void WriteTitle(Fixture &fixture, std::int32_t id,
                std::uintptr_t title, std::uintptr_t title_template,
                std::int32_t tier, std::uintptr_t province) {
  fixture.Put(0x500020 + static_cast<std::uintptr_t>(id) * 0x10 + 8,
              title);
  fixture.Put(title + 0x10, id);
  fixture.Put(title + 0x160, title_template);
  fixture.Put(title_template + 0x5C, tier);
  fixture.Put(title + 0x258, kPlayerId);
  if (tier == 1) {
    fixture.Put(title + 0x460, province);
  }
}

Fixture Scene() {
  Fixture fixture;
  fixture.Put(kModule + 0x570E068, std::uintptr_t{0x100000});
  fixture.Put(kModule + 0x570F7B8, std::uintptr_t{0x110000});
  fixture.Put(kModule + 0x570C130, std::uintptr_t{0x400000});
  fixture.Put(kModule + 0x570C138, std::uintptr_t{0x410000});
  fixture.Put(kModule + 0x570C410, std::uintptr_t{0x500000});
  fixture.Put(kModule + 0x570C3F8, std::uintptr_t{0x510000});
  fixture.Put(kModule + 0x57BFBA8, std::uintptr_t{0x900000});
  fixture.Put(0x100000 + 0xA0, std::uintptr_t{0x200000});
  fixture.Put(0x110000 + 0x18, std::uintptr_t{0x120000});
  fixture.Put(0x120000 + 0x1F0, std::int32_t{7});
  fixture.Put(0x200000 + 0x1D4F0 + 0x58,
              std::uintptr_t{0x300000});
  fixture.Put(0x200000 + 0x1D4F0 + 0x64, std::int32_t{1});
  fixture.Put(0x300000, std::uintptr_t{0x310000});
  fixture.Put(0x310000 + 0xD8, std::int32_t{7});
  fixture.Put(0x310000 + 0xB0, kPlayerId);
  fixture.Put(0x400000 + 0x20, std::uintptr_t{0x400020});
  fixture.Put(0x400000 + 0x2C, std::int32_t{30000});
  fixture.Put(0x400020 + static_cast<std::uintptr_t>(kPlayerId) * 0x10 + 8,
              std::uintptr_t{0x420000});
  fixture.Put(0x420000 + 0x18, kPlayerId);
  fixture.Put(0x420000 + 0x1C8, std::uintptr_t{0});
  fixture.Put(0x420000 + 0x1B8, std::uintptr_t{0x430000});
  fixture.Put(0x430000 + 0x1E0, std::uintptr_t{0x440000});
  fixture.Put(0x430000 + 0x1E8, std::int32_t{3});
  fixture.Put(0x430000 + 0x1EC, std::int32_t{3});
  fixture.Put(0x440000, kCounty);
  fixture.Put(0x440004, kBarony2);
  fixture.Put(0x440008, kBarony1);
  fixture.Put(0x500000 + 0x20, std::uintptr_t{0x500020});
  fixture.Put(0x500000 + 0x2C, std::int32_t{2000});
  WriteTitle(fixture, kCounty, 0x600000, 0x610000, 2, 0);
  WriteTitle(fixture, kBarony1, 0x620000, 0x630000, 1, 0x700000);
  WriteTitle(fixture, kBarony2, 0x640000, 0x650000, 1, 0x710000);
  // An unrelated loaded barony does not enter the personally held source.
  fixture.Put(0x200000 + 0x140, std::uintptr_t{0x720000});
  fixture.Put(0x200000 + 0x14C, std::int32_t{4000});
  fixture.Put(0x700000 + 0x10, std::int32_t{2619});
  fixture.Put(0x710000 + 0x10, std::int32_t{2620});
  fixture.Put(0x720000 + 2619 * 8, std::uintptr_t{0x700000});
  fixture.Put(0x720000 + 2620 * 8, std::uintptr_t{0x710000});
  fixture.Put(0x900000 + 0x628, std::uintptr_t{0x910000});
  fixture.Put(0x910000 + 0x60, std::uintptr_t{0x920000});
  fixture.Put(0x910000 + 0x6C, std::int32_t{2});
  fixture.Put(0x920000, std::uintptr_t{0xA00000});
  fixture.Put(0x920008, std::uintptr_t{0xB00000});
  // No CHoldingView instance or +0x118 GUI cache exists in this fixture.
  return fixture;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  {
    auto fixture = Scene();
    const auto result = ReadPlayerHeldConstructionModelSourcesV1(
        kModule, true, fixture.Access(), {3});
    Require(result.status ==
                PlayerHeldConstructionModelStatusV1::sources_available,
            "independent_model_sources");
    Require(result.failure == PlayerHeldConstructionModelFailureV1::none,
            "available_has_no_failure");
    Require(result.player_character_id == kPlayerId &&
                result.snapshot_revision == 3 &&
                result.date_raw == 53178312,
            "frame_binding");
    Require(result.directly_held_barony_provinces ==
                std::vector<PlayerHeldHoldingSourceV1>{{kBarony1, 2619},
                                                       {kBarony2, 2620}},
            "held_barony_identity_and_order");
    Require(result.borrowed_definition_addresses ==
                std::vector<std::uintptr_t>{0xA00000, 0xB00000} &&
                !result.legal_construction_evaluated,
            "definitions_are_sources_not_legality");
  }
  {
    auto fixture = Scene();
    fixture.Put(0x640000 + 0x258, std::int32_t{99});
    const auto result = ReadPlayerHeldConstructionModelSourcesV1(
        kModule, true, fixture.Access(), {3});
    Require(result.status == PlayerHeldConstructionModelStatusV1::unavailable &&
                result.failure ==
                    PlayerHeldConstructionModelFailureV1::held_title_source,
            "foreign_holder_does_not_become_player_source");
  }
  {
    auto fixture = Scene();
    fixture.Put(0x720000 + 2620 * 8, std::uintptr_t{0xDEAD00});
    const auto result = ReadPlayerHeldConstructionModelSourcesV1(
        kModule, true, fixture.Access(), {3});
    Require(result.status == PlayerHeldConstructionModelStatusV1::unavailable &&
                result.failure == PlayerHeldConstructionModelFailureV1::
                                      holding_province_identity,
            "province_identity_roundtrip");
  }
  {
    auto fixture = Scene();
    fixture.change_second_frame = true;
    const auto result = ReadPlayerHeldConstructionModelSourcesV1(
        kModule, true, fixture.Access(), {3});
    Require(result.failure ==
                PlayerHeldConstructionModelFailureV1::frame_changed,
            "same_paused_frame");
  }
  {
    auto fixture = Scene();
    fixture.Put(0x910000 + 0x6C, std::int32_t{0});
    const auto result = ReadPlayerHeldConstructionModelSourcesV1(
        kModule, true, fixture.Access(), {3});
    Require(result.status ==
                PlayerHeldConstructionModelStatusV1::sources_available &&
                result.borrowed_definition_addresses.empty() &&
                !result.legal_construction_evaluated,
            "empty_definition_source_is_not_no_legal_construction");
  }
  std::cout << "GREEN player-held construction model source enumeration\n";
  return 0;
}

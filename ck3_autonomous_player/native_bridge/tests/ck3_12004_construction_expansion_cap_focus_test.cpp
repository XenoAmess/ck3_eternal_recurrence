#include "xar_bridge/ck3_12004_construction.hpp"
#include "player_world_building_authored_income_v1.hpp"
#include "player_world_building_action_candidate_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>
#include <vector>

// One expansion scene using the retained coverage fixture memory shape.
// All 152 production economic keys and forty slots are synthetic.
// The old nineteen-target coverage matrix is not executed.
namespace {
constexpr std::uintptr_t kModule = 0x100000000ULL;
constexpr std::int32_t kActor = 29829;
constexpr std::uintptr_t kNull = 0xF90000;
constexpr std::size_t kPositiveCount = 19;
constexpr std::size_t kHoldingCount = 8;
constexpr std::int32_t kSlotsPerHolding = 5;
constexpr std::int32_t kOccupantsPerHolding = 2;
const std::vector<const char *> kKeys = [] {
  std::vector<const char *> keys;
  for (const auto &[key, income] : xar::ck3_11906::kAuthoredBuildingIncomeHundredthsV1) {
    (void)income;
    keys.push_back(key.data());
  }
  for (const auto &[key, income] : xar::ck3_11906::kAuthoredEconomicBuildingIncomeHundredths12004) {
    (void)income;
    keys.push_back(key.data());
  }
  return keys;
}();
constexpr std::size_t kFarmEstates03 = 20;

std::uintptr_t Definition(std::size_t index) { return 0xB00000 + index * 0x1000; }
std::int32_t Type(std::size_t index) { return 100 + static_cast<std::int32_t>(index); }
std::int32_t Barony(std::size_t index) { return 2100 + static_cast<std::int32_t>(index); }
std::int32_t Province(std::size_t index) { return 2600 + static_cast<std::int32_t>(index); }
std::uintptr_t ProvincePointer(std::size_t index) { return 0x700000 + index * 0x1000; }

struct Tuple {
  std::size_t definition;
  std::size_t holding;
  std::int32_t slot;
  friend bool operator==(const Tuple &, const Tuple &) = default;
};

std::array<std::int64_t, 10> Cost(const Tuple &tuple) {
  std::array<std::int64_t, 10> result{};
  result[0] = 10000000 + static_cast<std::int64_t>(tuple.definition) * 10000 +
              static_cast<std::int64_t>(tuple.holding) * 100 + tuple.slot;
  return result;
}

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes;
  std::vector<Tuple> legal_calls;
  std::vector<Tuple> cost_calls;
  xar::game::CampaignRootFrameV1 frame{
      3, 53178312, true, true, true, true, kActor};

  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *raw = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(T); ++index) bytes[address + index] = raw[index];
  }

  void PutKey(std::size_t index) {
    const auto native = Definition(index) + 0x18;
    const auto size = std::strlen(kKeys[index]);
    const auto chars = size > 15 ? 0xE00000 + index * 0x100 : native;
    Put(native + 0x10, size);
    Put(native + 0x18, size > 15 ? size : std::size_t{15});
    if (size > 15) Put(native, chars);
    for (std::size_t byte = 0; byte < size; ++byte) Put(chars + byte, kKeys[index][byte]);
  }

  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
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
  static bool Capture(void *context, xar::game::CampaignRootFrameV1 &output) noexcept {
    output = static_cast<Fixture *>(context)->frame;
    return true;
  }
  static bool IsMain(void *) noexcept { return true; }

  static bool ResolveTuple(std::int32_t actor, std::int32_t province,
                           std::uintptr_t definition, std::int32_t slot, Tuple &tuple) noexcept {
    if (actor != kActor) return false;
    for (std::size_t d = 0; d < kKeys.size(); ++d) {
      if (definition != Definition(d)) continue;
      for (std::size_t h = 0; h < kHoldingCount; ++h) {
        if (province == Province(h) && slot >= 0 && slot < kSlotsPerHolding) {
          tuple = {d, h, slot};
          return true;
        }
      }
    }
    return false;
  }

  static bool Legal(void *context, std::int32_t actor, std::int32_t province,
                    std::uintptr_t definition, std::int32_t slot, bool &allowed) noexcept {
    Tuple tuple{};
    if (!ResolveTuple(actor, province, definition, slot, tuple)) return false;
    auto &self = *static_cast<Fixture *>(context);
    self.legal_calls.push_back(tuple);
    allowed = (tuple.definition < kPositiveCount && slot >= kOccupantsPerHolding) ||
              (tuple.definition == kFarmEstates03 && tuple.holding == 0 && slot == 0);
    return true;
  }

  static bool Quote(void *context, std::int32_t actor, std::int32_t province_id,
                    std::uintptr_t province, std::int32_t type,
                    std::uintptr_t definition, std::int32_t slot,
                    std::array<std::int64_t, 10> &raw) noexcept {
    Tuple tuple{};
    if (!ResolveTuple(actor, province_id, definition, slot, tuple) ||
        !((tuple.definition < kPositiveCount && slot >= kOccupantsPerHolding) ||
          (tuple.definition == kFarmEstates03 && tuple.holding == 0 && slot == 0)) ||
        province != ProvincePointer(tuple.holding) || type != Type(tuple.definition)) return false;
    auto &self = *static_cast<Fixture *>(context);
    self.cost_calls.push_back(tuple);
    raw = Cost(tuple);
    return true;
  }

  xar::ck3_12004::PlayerWorldBuildingSourceAccessV1 Access() {
    xar::ck3_12004::PlayerWorldBuildingSourceAccessV1 access{};
    access.campaign = {this, Capture, IsMain, Read, nullptr};
    access.final_legality = Legal;
    access.final_legality_context = this;
    access.native_cost = Quote;
    access.native_cost_context = this;
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
  f.Put(kModule + 0x5D1E320, kNull);
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
  f.Put(0x400020 + static_cast<std::uintptr_t>(kActor) * 0x10 + 8, std::uintptr_t{0x420000});
  f.Put(0x420000 + 0x18, kActor);
  f.Put(0x420000 + 0x1D0, std::uintptr_t{0});
  f.Put(0x420000 + 0x1B0, std::uintptr_t{0x450000});
  f.Put(0x450000 + 0x100, std::int64_t{2000000000});
  f.Put(0x420000 + 0x1C0, std::uintptr_t{0x430000});
  f.Put(0x430000 + 0x1E0, std::uintptr_t{0x440000});
  f.Put(0x430000 + 0x1E8, static_cast<std::int32_t>(kHoldingCount));
  f.Put(0x430000 + 0x1EC, static_cast<std::int32_t>(kHoldingCount));
  f.Put(0x500000 + 0x20, std::uintptr_t{0x500020});
  f.Put(0x500000 + 0x2C, std::int32_t{4000});
  f.Put(0x200000 + 0x140, std::uintptr_t{0x720000});
  f.Put(0x200000 + 0x14C, std::int32_t{4000});
  for (std::size_t h = 0; h < kHoldingCount; ++h) {
    const auto title = 0x600000 + h * 0x1000;
    const auto title_template = 0x680000 + h * 0x1000;
    const auto slots = 0x730000 + h * 0x1000;
    const auto province = ProvincePointer(h);
    f.Put(0x440000 + h * 4, Barony(h));
    f.Put(0x500020 + static_cast<std::uintptr_t>(Barony(h)) * 0x10 + 8, title);
    f.Put(title + 0x10, Barony(h));
    f.Put(title + 0x48, title_template);
    f.Put(title_template + 0x64, std::int32_t{1});
    f.Put(title + 0x128, kActor);
    f.Put(title + 0x338, province);
    f.Put(0x720000 + static_cast<std::uintptr_t>(Province(h)) * 8, province);
    f.Put(province + 0x10, Province(h));
    f.Put(province + 0x718, std::int64_t{2468000});
    f.Put(province + 0x620 + 0x10, slots);
    f.Put(province + 0x620 + 0x1C, kSlotsPerHolding);
    f.Put(province + 0x620 + 0x68, std::uintptr_t{0});
    for (std::int32_t slot = 0; slot < kSlotsPerHolding; ++slot)
      f.Put(slots + static_cast<std::uintptr_t>(slot) * 0x10,
            slot < kOccupantsPerHolding ? Definition(kPositiveCount) : kNull);
  }
  f.Put(0xD00000 + 0x50, std::uintptr_t{0xD10000});
  f.Put(0xD00000 + 0x58, static_cast<std::int32_t>(kKeys.size()));
  f.Put(0xD00000 + 0x5C, static_cast<std::int32_t>(kKeys.size()));
  for (std::size_t d = 0; d < kKeys.size(); ++d) {
    f.Put(0xD10000 + d * 8, Definition(d));
    f.Put(Definition(d), kModule + 0x48B6CD8);
    f.Put(Definition(d) + 0x10, Type(d));
    f.PutKey(d);
  }
  return f;
}

} // namespace

int main() {
  if (kKeys.size() != 152 || std::string_view{kKeys[kPositiveCount]} != "farm_estates_02" ||
      std::string_view{kKeys[kFarmEstates03]} != "farm_estates_03") {
    std::cerr << "RED fixture must contain 152 economic keys and adjacent farm upgrade\n";
    return 1;
  }
  auto fixture = Scene();
  const auto result = xar::ck3_12004::ReadPlayerWorldBuildingDefinitionSourcesV1(
      kModule, true, fixture.Access(), {3, -1, 4096, 512});
  const auto tier_one_calls = static_cast<std::size_t>(std::count_if(
      fixture.legal_calls.begin(), fixture.legal_calls.end(),
      [](const Tuple &tuple) { return tuple.definition < kPositiveCount; }));
  const auto selected = xar::ck3_11906::SelectPlayerWorldBuildingActionCandidate12004(
      result, 7, 20000000);
  std::cout << "definitions=" << result.definition_source_count <<
               " slots=40 checks=" << result.final_legality_checks <<
               " tier_one_checks=" << tier_one_calls <<
               " quotes=" << result.native_cost_checks <<
               " coverage=" << result.positive_income_coverage_complete <<
               " truncated=" << result.checks_truncated <<
               " selected_type=" << selected.building_type_id << "\n";
  if (!result.source_available ||
      result.failure != xar::ck3_12004::PlayerWorldBuildingFailureV1::none ||
      result.definition_source_count != 152 || result.directly_held_barony_provinces.size() != 8 ||
      result.final_legality_checks != 4096 || fixture.legal_calls.size() != 4096 ||
      result.positive_income_coverage_complete || !result.checks_truncated) {
    std::cerr << "RED expanded scan must retain exact check cap and incomplete coverage\n";
    return 1;
  }
  if (tier_one_calls != 760) {
    std::cerr << "RED high-tier expansion exhausted cap before 19 tier-one targets\n";
    return 1;
  }
  if (result.native_cost_checks != 457 || result.legal_samples.size() != 457 ||
      fixture.cost_calls.size() != 457) {
    std::cerr << "RED legal tier-one empty tuples and adjacent upgrade must quote once\n";
    return 1;
  }
  for (std::size_t d = 0; d < kPositiveCount; ++d) {
    for (std::size_t h = 0; h < kHoldingCount; ++h) {
      for (std::int32_t slot = 0; slot < kSlotsPerHolding; ++slot) {
        const Tuple tuple{d, h, slot};
        if (std::count(fixture.legal_calls.begin(), fixture.legal_calls.end(), tuple) != 1 ||
            std::count(fixture.cost_calls.begin(), fixture.cost_calls.end(), tuple) !=
                (slot >= kOccupantsPerHolding ? 1 : 0)) {
          std::cerr << "RED tier-one tuple omitted or native quote altered\n";
          return 1;
        }
      }
    }
  }
  // Adjacent farm upgrade: gross160 - observed old115 = delta45.
  // Empty tier-one delta70 must win through the unchanged final selector.
  const Tuple expected{0, 0, 2};
  if (!selected.ready || selected.building_type_id != Type(0) ||
      selected.barony_title_id != Barony(0) || selected.province_id != Province(0) ||
      selected.slot_index != 2 || selected.stock_cost_raw_native != Cost(expected) ||
      selected.stock_gold_cost_raw != Cost(expected)[0] ||
      selected.gold_reserve_after_raw != result.player_gold_raw - Cost(expected)[0]) {
    std::cerr << "RED final selector must retain authored delta and native cost\n";
    return 1;
  }
  std::cout << "GREEN expanded-cap observation and unchanged net-delta selection\n";
  return 0;
}

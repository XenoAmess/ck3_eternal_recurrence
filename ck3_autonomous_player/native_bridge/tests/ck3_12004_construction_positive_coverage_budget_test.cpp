#include "xar_bridge/ck3_12004_construction.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>
#include <vector>

// Real actual4 production reader and held-source path, with synthetic memory
// and native callbacks. Eight holdings, five slots and two occupants per holding
// exercise the finite positive-definition budget; these are not actual R85 slots.
namespace {
constexpr std::uintptr_t kModule = 0x100000000ULL;
constexpr std::int32_t kActor = 29829;
constexpr std::uintptr_t kNull = 0xB90000;
constexpr std::size_t kPositiveCount = 19;
constexpr std::size_t kHoldingCount = 8;
constexpr std::int32_t kSlotsPerHolding = 5;
constexpr std::int32_t kOccupantsPerHolding = 2;
constexpr std::array<const char *, 23> kKeys{
    "caravanserai_01", "watermills_01", "windmills_01", "farm_estates_01",
    "paddy_fields_01", "cereal_fields_01", "murex_farm_01", "spice_plantation_01",
    "common_tradeport_01", "pastures_01", "orchards_01", "logging_camps_01",
    "peat_quarries_01", "hill_farms_01", "elephant_pens_01", "qanats_01",
    "hunting_grounds_01", "plantations_01", "quarries_01",
    "hospices_01", "barracks_01", "military_camps_01", "stables_01"};

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
    allowed = tuple.definition < kPositiveCount && slot >= kOccupantsPerHolding;
    return true;
  }

  static bool Quote(void *context, std::int32_t actor, std::int32_t province_id,
                    std::uintptr_t province, std::int32_t type,
                    std::uintptr_t definition, std::int32_t slot,
                    std::array<std::int64_t, 10> &raw) noexcept {
    Tuple tuple{};
    if (!ResolveTuple(actor, province_id, definition, slot, tuple) ||
        tuple.definition >= kPositiveCount || slot < kOccupantsPerHolding ||
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

void Require(bool condition, const char *name) {
  if (!condition) { std::cerr << "RED " << name << '\n'; std::abort(); }
}
bool Contains(const std::vector<Tuple> &rows, const Tuple &tuple) {
  return std::find(rows.begin(), rows.end(), tuple) != rows.end();
}
std::size_t TailCalls(const std::vector<Tuple> &rows) {
  return static_cast<std::size_t>(std::count_if(
      rows.begin(), rows.end(), [](const Tuple &tuple) {
        return tuple.definition >= kPositiveCount;
      }));
}
} // namespace

int main() {
  const Tuple last{18, 7, 4};
  auto limited_fixture = Scene();
  const auto limited = xar::ck3_12004::ReadPlayerWorldBuildingDefinitionSourcesV1(
      kModule, true, limited_fixture.Access(), {3, -1, 512, 512});
  Require(limited.source_available &&
              limited.failure == xar::ck3_12004::PlayerWorldBuildingFailureV1::none &&
              limited.completed_buildings_observed && limited.completed_buildings.size() == 16 &&
              limited.directly_held_barony_provinces.size() == kHoldingCount &&
              limited.final_legality_checks == 512 && limited_fixture.legal_calls.size() == 512 &&
              limited.legal_samples.size() == 306 && limited.native_cost_checks == 306 &&
              limited_fixture.cost_calls.size() == 306 &&
              limited.checks_truncated && !limited.positive_income_coverage_complete &&
              !Contains(limited_fixture.legal_calls, last) && !Contains(limited_fixture.cost_calls, last) &&
              TailCalls(limited_fixture.legal_calls) == 0,
          "legacy_512_check_request_stops_before_the_finite_positive_set_is_covered");

  auto full_fixture = Scene();
  const auto full = xar::ck3_12004::ReadPlayerWorldBuildingDefinitionSourcesV1(
      kModule, true, full_fixture.Access(), {3, -1, 4096, 512});
  Require(full.source_available &&
              full.failure == xar::ck3_12004::PlayerWorldBuildingFailureV1::none &&
              full.directly_held_barony_provinces.size() == kHoldingCount &&
              full.completed_buildings_observed && full.completed_buildings.size() == 16 &&
              full.definition_source_count == 23 && full.legal_samples.size() == 456 &&
              full.native_cost_checks == 456 && full_fixture.cost_calls.size() == 456 &&
              full.final_legality_checks == 760 && full_fixture.legal_calls.size() == 760 &&
              full.checks_truncated && full.positive_income_coverage_complete &&
              full.player_gold_observed && Contains(full_fixture.legal_calls, last) &&
              Contains(full_fixture.cost_calls, last) && TailCalls(full_fixture.legal_calls) == 0,
          "full_positive_budget_covers_760_checks_and_456_quotes_without_expanding_the_tail");
  Require(std::equal(limited.legal_samples.begin(), limited.legal_samples.end(),
                     full.legal_samples.begin()),
          "previously_visible_quotes_and_native_cost_arrays_remain_unchanged");

  for (std::size_t d = 0; d < kPositiveCount; ++d) {
    std::size_t quotes = 0;
    for (std::size_t h = 0; h < kHoldingCount; ++h) {
      for (std::int32_t slot = 0; slot < kSlotsPerHolding; ++slot) {
        const Tuple tuple{d, h, slot};
        Require(std::count(full_fixture.legal_calls.begin(), full_fixture.legal_calls.end(), tuple) == 1,
                "each_positive_definition_checks_each_of_40_slots_once");
        const auto quote_count = std::count(
            full_fixture.cost_calls.begin(), full_fixture.cost_calls.end(), tuple);
        Require(quote_count == (slot >= kOccupantsPerHolding ? 1 : 0),
                "each_legal_empty_tuple_quotes_once_and_occupied_slots_never_quote");
        if (slot >= kOccupantsPerHolding) ++quotes;
      }
    }
    Require(quotes == 24, "24_empty_cost_quotes_per_positive_definition");
  }
  for (const auto &sample : full.legal_samples) {
    const auto d = static_cast<std::size_t>(sample.building_type_id - 100);
    const auto h = static_cast<std::size_t>(sample.province_id - 2600);
    Require(d < kPositiveCount && h < kHoldingCount && sample.barony_title_id == Barony(h) &&
                sample.slot_index >= kOccupantsPerHolding && sample.slot_index < kSlotsPerHolding &&
                sample.building_key == kKeys[d] && sample.native_cost_observed,
            "every_published_quote_has_the_expected_legal_empty_tuple");
    const auto raw = Cost({d, h, sample.slot_index});
    const std::array<std::int64_t, 8> projected{
        raw[0], raw[1], raw[2], raw[4], raw[5], raw[6], raw[8], raw[9]};
    Require(sample.cost_raw_native == raw && sample.cost_raw_slots == projected,
            "every_published_quote_preserves_native_10_and_projected_8_cost_slots");
  }
  const auto &late = full.legal_samples.back();
  Require(late.building_key == "quarries_01" && late.building_type_id == Type(18) &&
              late.barony_title_id == Barony(7) && late.province_id == Province(7) &&
              late.slot_index == 4 && late.cost_raw_native == Cost(last),
          "last_positive_definition_last_holding_last_slot_is_checked_and_quoted");
  std::cout << "{\"scene_count\":2,\"production_reader\":true,"
               "\"old_positive_coverage\":false,\"new_positive_coverage\":true,"
               "\"positive_legality_checks\":760,\"positive_quotes\":456,"
               "\"tail_legality_checks\":0}\n";
}

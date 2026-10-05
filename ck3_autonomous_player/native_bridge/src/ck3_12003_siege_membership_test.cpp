#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/war_occupation_targets_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

namespace {
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  if (offset + sizeof(T) > N) throw std::runtime_error("fixture buffer too small");
  std::memcpy(object.data() + offset, &value, sizeof(T));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
  return value;
}
int checks = 0;
void Require(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
struct Storage {
  std::array<std::byte, 0x40> object{};
  std::array<std::byte, 0x80> slots{};
  void *slot = object.data();
  Storage() {
    Put(object, 0x20, static_cast<void *>(slots.data()));
    Put(object, 0x2C, std::int32_t{8});
  }
  void Set(std::size_t index, void *value) { Put(slots, index * 0x10 + 8, value); }
};
constexpr std::int32_t kEngineUnit = 0x01000001;
constexpr std::int32_t kEngineArmy = 0x02000001;
constexpr std::int32_t kEngineRegiment = 0x03000001;
std::int32_t exclusion_calls = 0, qualification_calls = 0;
std::uint8_t Excluded(void *) { ++exclusion_calls; return 0; }
std::uint8_t Eligible(void *army, void *province) {
  ++qualification_calls;
  Require(Get<std::int32_t>(province, 0x10) == 1, "predicate receives the actual Province");
  return static_cast<std::uint8_t>(
      Get<std::int32_t>(army, 0x10) == 0x02000002 ? 0 : 0x80);
}
std::int64_t *Progress(void *, std::int64_t *out) { *out = 25000; return out; }
std::int64_t *Total(void *, std::int64_t *out) { *out = 400000; return out; }
std::int32_t Days(void *) { return 3; }
struct Fixture {
  std::array<std::byte, 0xB0> gs{};
  std::array<std::byte, 0x180> gd{};
  std::array<std::byte, 0x880> province{};
  std::array<std::byte, 0x460> siege{};
  std::array<std::array<std::byte, 0x190>, 4> units{};
  std::array<std::array<std::byte, 0x200>, 4> armies{};
  std::array<std::array<std::byte, 0x80>, 2> regiments{};
  std::array<void *, 3> provinces{nullptr, province.data(), nullptr};
  std::array<std::int32_t, 5> residents{0, kEngineUnit, 0x01000002, 0x01000003, kEngineUnit};
  std::array<std::int32_t, 3> engine_regiments{kEngineRegiment, 0x03000002, kEngineRegiment};
  Storage units_store, armies_store, regiments_store, sieges_store;
  void *game_state = gs.data();
  xar::ck3_12002::ProvinceBindings bindings{};
  Fixture() {
    Put(gs, 0xA0, static_cast<void *>(gd.data()));
    Put(gd, 0x140, static_cast<void *>(provinces.data()));
    Put(gd, 0x14C, std::int32_t{3});
    Put(province, 0x10, std::int32_t{1});
    Put(province, 0x85C, std::uint32_t{0x50726F76});
    Put(province, 0x788, std::int32_t{0x04000001});
    Put(province, 0x740, static_cast<void *>(residents.data()));
    Put(province, 0x748, std::int32_t{5});
    Put(province, 0x74C, std::int32_t{5});
    Put(siege, 8, std::int32_t{0x04000001});
    Put(siege, 0xC, std::uint32_t{0x53696765});
    Put(siege, 0x200, static_cast<void *>(province.data()));
    Put(siege, 0x208, std::int32_t{0}); // Engine Army is independent of this lead.
    Put(siege, 0x3D0, std::int64_t{100000});
    sieges_store.Set(1, siege.data());
    for (std::size_t index = 0; index < units.size(); ++index) {
      const auto unit_id = index == 0 ? 0 : 0x01000000 + static_cast<std::int32_t>(index);
      const auto army_id = index == 0 ? 0 : 0x02000000 + static_cast<std::int32_t>(index);
      Put(units[index], 0x10, unit_id);
      Put(units[index], 0x20, std::int32_t{1});
      Put(units[index], 0x178, army_id);
      Put(armies[index], 0x10, army_id);
      Put(armies[index], 0x120, std::int32_t{-1});
      units_store.Set(index, units[index].data());
      armies_store.Set(index, armies[index].data());
    }
    Put(units[3], 0x170, std::int32_t{1});
    Put(armies[1], 0x38, static_cast<void *>(engine_regiments.data()));
    Put(armies[1], 0x40, std::int32_t{3});
    Put(armies[1], 0x44, std::int32_t{3});
    for (std::size_t index = 0; index < regiments.size(); ++index) {
      Put(regiments[index], 0x10, 0x03000001 + static_cast<std::int32_t>(index));
      Put(regiments[index], 0x14, std::uint32_t{0x41725267});
      Put(regiments[index], 0x38, std::int32_t{0}); // K has no positive-current-count test.
      regiments_store.Set(index + 1, regiments[index].data());
    }
    bindings.enabled = true;
    bindings.game_state_slot = &game_state;
    bindings.unit_storage_slot = &units_store.slot;
    bindings.siege_storage_slot = &sieges_store.slot;
    bindings.siege_progress = Progress;
    bindings.siege_total_work = Total;
    bindings.siege_days_left = Days;
    bindings.siege_armies.enabled = true;
    bindings.siege_armies.internal_army_storage_slot = &armies_store.slot;
    bindings.siege_armies.regiment_storage_slot = &regiments_store.slot;
    bindings.siege_army_excluded = Excluded;
    bindings.siege_army_province_eligible = Eligible;
  }
  xar::game::WarObjectiveProvinceState Read() {
    return xar::ck3_12002::ReadObjectiveProvince(bindings, 1, {}, -1, true);
  }
};
} // namespace

// Only native identity storage and AL predicates are fixture dependencies;
// ReadObjectiveProvince and the wire serializer are the production sources.
namespace xar::ck3_12002 {
ArmyBindings BindArmyImage(std::uintptr_t, std::string_view) noexcept { return {}; }
void *ResolveInternalArmy(const ArmyBindings &b, std::int32_t id) noexcept {
  if (!b.enabled || id == -1 || b.internal_army_storage_slot == nullptr ||
      *b.internal_army_storage_slot == nullptr) return nullptr;
  const auto store = *b.internal_army_storage_slot;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(Get<std::int32_t>(store, 0x2C))) return nullptr;
  const auto slots = Get<void *>(store, 0x20);
  const auto object = Get<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object != nullptr && Get<std::int32_t>(object, 0x10) == id ? object : nullptr;
}
} // namespace xar::ck3_12002

int main() {
  try {
    constexpr std::uintptr_t image = 0x140000000;
    const auto bound = xar::ck3_12002::BindProvinceImage(image, xar::ck3_12002::kExecutableSha256);
    Require(reinterpret_cast<std::uintptr_t>(bound.siege_army_excluded) == image + 0x24E8360 &&
            reinterpret_cast<std::uintptr_t>(bound.siege_army_province_eligible) == image + 0x2C16690,
            "exact .3 AL predicates bind to the closed source RVAs");
    Require(!xar::ck3_12002::BindProvinceImage(image, "other").enabled,
            "unsupported build does not bind the observer");
    Fixture fixture;
    const auto state = fixture.Read();
    const auto &rows = state.siege_province_unit_occurrences;
    Require(state.has_active_siege && state.siege_province_unit_occurrences_observable && rows.size() == 5,
            "actual Province occurrence list is observed separately from lead identity");
    Require(rows[0].public_unit_id == 0 && rows[0].native_carmy_id == 0 && rows[0].eligible &&
            rows[0].qualified_regiment_ids_observable && rows[0].qualified_regiment_ids.empty(),
            "slot zero and eligible empty regiment list are real native values");
    Require(rows[1].public_unit_id == kEngineUnit && rows[1].native_carmy_id == kEngineArmy &&
            rows[1].eligible && rows[1].qualified_regiment_ids ==
                std::vector<std::int32_t>{kEngineRegiment, 0x03000002, kEngineRegiment},
            "independent eligible Army retains the exact ArRg occurrence order");
    Require(rows[4].occurrence_index == 4 && rows[4].public_unit_id == kEngineUnit &&
            rows[4].qualified_regiment_ids == rows[1].qualified_regiment_ids,
            "repeat Province residents are not collapsed into a set");
    Require(rows[2].eligible_observable && !rows[2].eligible &&
            rows[2].qualified_regiment_ids_observable && rows[2].qualified_regiment_ids.empty() &&
            rows[3].eligible_observable && !rows[3].eligible,
            "same Province is insufficient; native and raw prerequisite exclusions are false");
    Require(exclusion_calls == 4 && qualification_calls == 4,
            "raw prerequisite rejection does not enter the native predicates");
    const std::string expected =
        "[{\"occurrence_index\":0,\"public_unit_id\":0,\"native_carmy_id\":0,\"eligible\":true,\"qualified_regiment_ids\":[]},"
        "{\"occurrence_index\":1,\"public_unit_id\":16777217,\"native_carmy_id\":33554433,\"eligible\":true,\"qualified_regiment_ids\":[50331649,50331650,50331649]},"
        "{\"occurrence_index\":2,\"public_unit_id\":16777218,\"native_carmy_id\":33554434,\"eligible\":false,\"qualified_regiment_ids\":[]},"
        "{\"occurrence_index\":3,\"public_unit_id\":16777219,\"native_carmy_id\":33554435,\"eligible\":false,\"qualified_regiment_ids\":[]},"
        "{\"occurrence_index\":4,\"public_unit_id\":16777217,\"native_carmy_id\":33554433,\"eligible\":true,\"qualified_regiment_ids\":[50331649,50331650,50331649]}]";
    Require(xar::game::SerializeSiegeProvinceUnitOccurrencesV1(true, rows) == expected,
            "shared objective wire serializer preserves actual identities and false/empty");
    xar::game::WarOccupationTargetsV1 observation{};
    xar::game::WarOccupationTargetRowV1 row{};
    row.siege_observable = row.has_active_siege = true;
    row.active_siege.province_unit_occurrences_observable = true;
    row.active_siege.province_unit_occurrences = rows;
    observation.rows.push_back(row);
    const auto wire = xar::game::SerializeWarOccupationTargetsV1(observation,
        xar::game::ReadWarOccupationTargetsV1Result::unavailable, 1, 1, "fixture");
    Require(wire.find("\"province_unit_occurrences\":" + expected) != std::string::npos,
            "rich occupation serializer uses the same member contract");
    fixture.bindings.siege_army_province_eligible = nullptr;
    auto partial = fixture.Read().siege_province_unit_occurrences;
    Require(!partial[1].eligible_observable && !partial[1].qualified_regiment_ids_observable &&
            partial[3].eligible_observable && !partial[3].eligible,
            "missing predicate remains unknown without erasing known raw exclusion");
    fixture.bindings.siege_army_province_eligible = Eligible;
    Put(fixture.regiments[0], 0x10, std::int32_t{0x05000001});
    partial = fixture.Read().siege_province_unit_occurrences;
    Require(partial[1].eligible && !partial[1].qualified_regiment_ids_observable &&
            partial[1].qualified_regiment_ids.empty(),
            "eligible Army with unreadable ArRg identity cannot invent consumed IDs");
    Put(fixture.province, 0x74C, std::int32_t{0});
    Require(fixture.Read().siege_province_unit_occurrences_observable &&
            fixture.Read().siege_province_unit_occurrences.empty(),
            "native empty Province list stays an observed empty array");
    Put(fixture.province, 0x74C, std::int32_t{-1});
    Require(!fixture.Read().siege_province_unit_occurrences_observable,
            "failed Province list read differs from an observed empty list");
    std::cout << "PASS checks=" << checks << " cases=5; owned fixtures, no game access\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}

#include "xar_bridge/ck3_12002_province.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
using namespace xar::ck3_12002;
template <class T, std::size_t N> void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Require(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << '\n'; std::exit(1); }
}
bool Occupied(void *p) { return Get<std::int32_t>(p, 0x73C) != -1; }
std::int32_t Fort(void *p) { return Get<std::int32_t>(p, 0x850); }
std::int32_t Garrison(void *) { return 120; }
std::int32_t Besiegers(void *) { return 500; }
std::int64_t g_progress = 25000;
std::int64_t *Progress(void *, std::int64_t *out) { *out = g_progress; return out; }
std::int64_t *Total(void *, std::int64_t *out) { *out = 400'000; return out; }
std::int32_t g_days = 3;
std::int32_t Days(void *) { return g_days; }
std::int32_t g_assault_calls = 0;
std::int64_t *Daily(void *, std::int64_t *out, std::int32_t strength) {
  ++g_assault_calls;
  Require(strength == 500, "native eligible besieger strength");
  *out = 3000;
  return out;
}
std::int32_t Casualties(void *) { ++g_assault_calls; return 10; }
bool CanStart(std::int32_t kind, std::int32_t actor, std::int32_t siege, void *error) {
  Require(kind == 1 && actor == 0x01000001 && siege == 0x02000001 && error == nullptr, "complete validator arguments");
  return true;
}
bool CanStop(std::int32_t, std::int32_t, std::int32_t, void *) { return false; }
void *TitleProvince(void *title) { return Get<void *>(title, 0x338); }
struct Storage {
  std::array<std::byte, 0x40> object{};
  std::array<std::byte, 0x80> slots{};
  Storage() {
    Put(object, 0x20, static_cast<void *>(slots.data()));
    Put(object, 0x2C, std::int32_t{8});
  }
  void Set(std::size_t index, void *value) { Put(slots, index * 0x10 + 8, value); }
};
} // namespace

int main() {
  using namespace xar::ck3_12002;
  constexpr std::uintptr_t image = 0x140000000;
  const auto native = BindProvinceImage(image, kExecutableSha256);
  Require(native.enabled && reinterpret_cast<std::uintptr_t>(native.siege_storage_slot) == image + 0x5D1EC88, "exact-build siege binding");
  Require(reinterpret_cast<std::uintptr_t>(native.title_province) == image + 0x230F900, "title province getter migration");
  Require(!BindProvinceImage(image, "old-build").enabled, "unknown-build disabled");

  std::array<std::byte, 0xB0> gs{};
  std::array<std::byte, 0x180> gd{};
  std::array<std::byte, 0x880> province{};
  std::array<std::byte, 0x460> siege{};
  std::array<std::byte, 0x1E0> character{};
  std::array<std::byte, 0x190> unit{};
  std::array<void *, 3> provinces{nullptr, province.data(), nullptr};
  Put(gs, 0xA0, static_cast<void *>(gd.data()));
  Put(gd, 0x140, static_cast<void *>(provinces.data()));
  Put(gd, 0x14C, std::int32_t{3});
  Put(province, 0x10, std::int32_t{1});
  Put(province, 0x85C, std::uint32_t{0x50726F76});
  Put(province, 0x73C, std::int32_t{0x01000001});
  Put(province, 0x744, std::int32_t{0x01000007}); // obsolete occupation decoy
  Put(province, 0x850, std::int32_t{9});
  Put(province, 0x858, std::int32_t{99}); // obsolete fort decoy
  Put(province, 0x788, std::int32_t{0x02000001});
  Put(province, 0x790, std::int32_t{-1}); // obsolete siege decoy
  Put(siege, 8, std::int32_t{0x02000001});
  Put(siege, 0xC, std::uint32_t{0x53696765});
  Put(siege, 0x200, static_cast<void *>(province.data()));
  Put(siege, 0x208, std::int32_t{0x03000002});
  Put(siege, 0x3D0, std::int64_t{100'000});
  Put(siege, 0x3D8, std::int32_t{1});
  Put(siege, 0x44C, std::uint8_t{0});
  Put(character, 0x18, std::int32_t{0x01000001});
  Put(unit, 0x10, std::int32_t{0x04000001});
  Put(unit, 0x178, std::int32_t{0x03000002});
  Storage siege_storage, character_storage, unit_storage;
  siege_storage.Set(1, siege.data());
  character_storage.Set(1, character.data());
  unit_storage.Set(1, unit.data());
  void *gs_ptr = gs.data(), *ss_ptr = siege_storage.object.data(),
       *cs_ptr = character_storage.object.data(), *us_ptr = unit_storage.object.data();
  ProvinceBindings fixture{};
  fixture.enabled = true;
  fixture.game_state_slot = &gs_ptr;
  fixture.siege_storage_slot = &ss_ptr;
  fixture.character_storage_slot = &cs_ptr;
  fixture.unit_storage_slot = &us_ptr;
  fixture.is_occupied = &Occupied;
  fixture.fort_level = &Fort;
  fixture.garrison_size = &Garrison;
  fixture.besieging_strength = &Besiegers;
  fixture.siege_progress = &Progress;
  fixture.siege_total_work = &Total;
  fixture.siege_days_left = &Days;
  fixture.assault_daily_progress = &Daily;
  fixture.assault_daily_casualties = &Casualties;
  fixture.validate_start_assault = &CanStart;
  fixture.validate_stop_assault = &CanStop;
  std::vector<xar::game::ArmySnapshot> armies(1);
  armies[0].army_id = 0x04000001;
  armies[0].controllable = true;
  auto row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001, true);
  Require(row.occupation_observable && row.is_occupied && row.occupying_character_id == 0x01000001, "new occupation layout");
  Require(row.fort_level_observable && row.fort_level == 9, "new fort layout");
  Require(row.siege_observable && row.has_active_siege && row.siege_id == 0x02000001, "new active siege offset");
  Require(row.besieging_army_id == 0x04000001 && row.player_army_besieging, "public/internal army identity");
  Require(row.siege_progress_fraction.raw == 25000 && row.siege_total_work.raw == 400000 && row.siege_current_work.raw == 100000, "fixed-point siege metrics");
  Require(row.assault_observable && row.can_start_assault && !row.can_stop_assault && row.assault_daily_casualties == 10, "complete assault read");
  row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001, false);
  Require(row.fort_level_observable && !row.garrison_size_observable && !row.siege_observable, "running scalar-only projection");
  Put(siege, 0x3D8, std::int32_t{0});
  g_assault_calls = 0;
  row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001);
  Require(row.assault_observable && row.assault_daily_progress.raw == 0 && g_assault_calls == 0, "intact wall does not evaluate breach-indexed getter");
  g_days = std::numeric_limits<std::int32_t>::max();
  row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001);
  Require(!row.siege_days_left_observable, "stalled siege sentinel unavailable");
  Put(siege, 8, std::int32_t{0x05000001});
  row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001);
  Require(!row.siege_observable && row.garrison_size_observable, "stale generation does not masquerade as absent siege");
  Put(siege, 8, std::int32_t{0x02000001});
  g_progress = 100001;
  Require(!ReadObjectiveProvince(fixture, 1, armies, 0x01000001).siege_observable, "invalid native fraction rejected");
  g_progress = 25000;
  Put(province, 0x788, std::int32_t{-1});
  row = ReadObjectiveProvince(fixture, 1, armies, 0x01000001);
  Require(row.siege_observable && !row.has_active_siege, "valid no-siege state");

  Storage title_storage;
  std::array<std::byte, 0x350> duchy{}, county{};
  std::array<std::byte, 0x80> duchy_template{}, county_template{};
  std::array<std::int32_t, 1> children{0x06000002};
  Put(duchy, 0x10, std::int32_t{0x06000001});
  Put(duchy, 0x48, static_cast<void *>(duchy_template.data()));
  Put(duchy_template, 0x64, std::int32_t{3});
  Put(duchy, 0x110, static_cast<void *>(children.data()));
  Put(duchy, 0x118, std::int32_t{1});
  Put(duchy, 0x11C, std::int32_t{1});
  Put(county, 0x10, std::int32_t{0x06000002});
  Put(county, 0x48, static_cast<void *>(county_template.data()));
  Put(county_template, 0x64, std::int32_t{2});
  Put(county, 0x338, static_cast<void *>(province.data()));
  title_storage.Set(1, duchy.data());
  title_storage.Set(2, county.data());
  void *ts_ptr = title_storage.object.data();
  fixture.landed_title_storage_slot = &ts_ptr;
  fixture.title_province = &TitleProvince;
  const std::array<std::int32_t, 1> targets{0x06000001};
  std::vector<std::int32_t> objective;
  Require(CollectObjectiveProvinceIds(fixture, targets, objective) && objective == std::vector<std::int32_t>{1}, "new title hierarchy and county capital projection");
  const std::array<std::int32_t, 2> duplicate_targets{0x06000002, 0x06000002};
  Require(CollectObjectiveProvinceIds(fixture, duplicate_targets, objective) && objective == std::vector<std::int32_t>{1}, "independent duplicate county targets share one province");
  const std::array<std::int32_t, 2> overlapping_targets{0x06000001, 0x06000002};
  Require(CollectObjectiveProvinceIds(fixture, overlapping_targets, objective) && objective == std::vector<std::int32_t>{1}, "independent parent and child target overlap is valid");
  children[0] = 0x07000002;
  Require(!CollectObjectiveProvinceIds(fixture, targets, objective) && objective.empty(), "atomic hierarchy failure on stale child generation");
  std::cout << "PASS ck3_12002_province synthetic fixtures; no game process accessed\n";
}

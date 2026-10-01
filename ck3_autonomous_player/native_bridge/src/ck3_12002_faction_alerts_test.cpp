#include "xar_bridge/ck3_12002_faction_alerts.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <string_view>
#include <vector>

namespace {
template <std::size_t N> using Blob = std::array<std::byte, N>;
template <std::size_t N, typename T>
void Put(Blob<N> &blob, std::size_t offset, T value) {
  if (offset + sizeof value > N) std::abort();
  std::memcpy(blob.data() + offset, &value, sizeof value);
}
struct Fixture;
Fixture *current = nullptr;
struct Fixture {
  static constexpr std::int32_t actor = 0x01000001;
  static constexpr std::int32_t leader = 0x01000002;
  static constexpr std::int32_t member = 0x01000003;
  static constexpr std::int32_t vassal = 0x01000004;
  static constexpr std::int32_t other_target = 0x01000005;
  static constexpr std::int32_t liberty = 0x02000001;
  static constexpr std::int32_t populist = 0x02000002;
  static constexpr std::int32_t peasant = 0x02000003;
  static constexpr std::int32_t foreign_populist = 0x02000004;
  static constexpr std::int32_t county_id = 0x03000001;
  static constexpr std::int32_t war_id = 0x04000001;
  static constexpr std::uintptr_t faction_vtable = 0x144743520;
  Blob<0x30> characters{}, factions{}, titles{}, wars{}, contracts{};
  Blob<0x60> character_slots{};
  Blob<0x50> faction_slots{};
  Blob<0x20> title_slots{}, war_slots{}, contract_slots{};
  Blob<0x30> contract{};
  std::array<Blob<0x1D8>, 6> character_objects{};
  std::array<Blob<0x98>, 5> faction_objects{};
  std::array<Blob<0x40>, 4> definitions{};
  Blob<0x240> land{};
  Blob<0x240> vassal_land{};
  Blob<0x1A0> title{};
  Blob<0x68> title_definition{};
  Blob<0x860> province{};
  Blob<0x3C0> county{};
  Blob<0x30> char_fallback{}, faction_fallback{}, title_fallback{}, war_fallback{};
  Blob<0x10> war{};
  std::array<Blob<0x20>, 2> character_members{};
  std::array<Blob<0x18>, 3> county_members{};
  std::array<std::int32_t, 3> targeting_ids{liberty, populist, peasant};
  std::array<std::int32_t, 1> joined_ids{foreign_populist};
  std::array<std::int32_t, 1> held_counties{county_id};
  std::array<std::int32_t, 1> contract_ids{0x05000001};
  void *character_store = characters.data();
  void *faction_store = factions.data();
  void *title_store = titles.data();
  void *war_store = wars.data();
  void *contract_store = contracts.data();
  void *character_null = char_fallback.data();
  void *faction_null = faction_fallback.data();
  void *title_null = title_fallback.data();
  void *war_null = war_fallback.data();
  void *contract_null = nullptr;
  std::vector<std::pair<const void *, std::size_t>> ranges;
  std::map<const void *, std::string> strings;
  std::array<std::int64_t, 5> powers{0, 11000000, 9000000, 2000000, 12000000};
  std::array<std::int64_t, 5> thresholds{0, 8000000, 8000000, 8000000, 8000000};
  std::array<std::int64_t, 5> growth{0, 200000, 500000, 0, 300000};
  std::array<std::int32_t, 5> months{0, 8, 10, 0, 4};
  bool human = false;
  bool at_war = false;
  bool metrics_drift = false;
  bool frame_drift = false;
  std::uint32_t power_calls = 0;
  std::uint32_t frame_calls = 0;
  xar::game::PlayerFactionAlertsFrameV1 frame{41, 53169072, true, true, true, true, actor};

  template <typename T> void Register(T &object) {
    ranges.emplace_back(&object, sizeof object);
  }
  Fixture() {
    current = this;
    Put(characters, 0x20, character_slots.data());
    Put(characters, 0x2C, std::int32_t{6});
    Put(factions, 0x20, faction_slots.data());
    Put(factions, 0x2C, std::int32_t{5});
    Put(titles, 0x20, title_slots.data());
    Put(titles, 0x2C, std::int32_t{2});
    Put(wars, 0x20, war_slots.data());
    Put(wars, 0x2C, std::int32_t{2});
    Put(contracts, 0x20, contract_slots.data());
    Put(contracts, 0x2C, std::int32_t{2});
    Put(contract_slots, 0x18, contract.data());
    Put(contract, 8, contract_ids[0]);
    Put(contract, 0x20, character_objects[4].data());
    for (std::int32_t i = 1; i < 6; ++i) {
      Put(character_slots, static_cast<std::size_t>(i) * 0x10 + 8,
          character_objects[static_cast<std::size_t>(i)].data());
      Put(character_objects[static_cast<std::size_t>(i)], 0x18, actor + i - 1);
    }
    Put(character_objects[1], 0x1C0, land.data());
    Put(character_objects[4], 0x1C0, vassal_land.data());
    Put(land, 0x218, contract_ids.data());
    Put(land, 0x224, std::int32_t{1});
    Put(vassal_land, 0x1E0, held_counties.data());
    Put(vassal_land, 0x1EC, std::int32_t{1});
    Put(char_fallback, 0x18, std::int32_t{-1});
    Put(land, 0x120, targeting_ids.data());
    Put(land, 0x12C, std::int32_t{3});
    const std::array<std::string_view, 4> keys{
      "liberty_faction", "populist_faction", "peasant_faction", "populist_faction"};
    for (std::int32_t i = 1; i < 5; ++i) {
      auto &object = faction_objects[static_cast<std::size_t>(i)];
      Put(faction_slots, static_cast<std::size_t>(i) * 0x10 + 8, object.data());
      Put(object, 0, faction_vtable);
      Put(object, 0x10, liberty + i - 1);
      Put(object, 0x20, definitions[static_cast<std::size_t>(i - 1)].data());
      Put(object, 0x28, std::int64_t{2500000});
      Put(object, 0x40, i == 4 ? other_target : actor);
      Put(object, 0x44, i == 1 ? leader : -1);
      Put(object, 0x8C, std::int32_t{-1});
      strings.emplace(definitions[static_cast<std::size_t>(i - 1)].data() + 0x18,
                      keys[static_cast<std::size_t>(i - 1)]);
    }
    Put(faction_objects[1], 0x48, character_members.data());
    Put(faction_objects[1], 0x54, std::int32_t{2});
    for (std::size_t i = 0; i < 2; ++i) {
      Put(character_members[i], 8, leader + static_cast<std::int32_t>(i));
      Put(character_members[i], 0x0C, liberty);
    }
    for (std::size_t i = 0; i < 3; ++i) {
      const auto faction_index = i + 2;
      Put(faction_objects[faction_index], 0x60, county_members[i].data());
      Put(faction_objects[faction_index], 0x6C, std::int32_t{1});
      Put(county_members[i], 8, county_id);
      Put(county_members[i], 0x0C, std::uint8_t{1});
      Put(county_members[i], 0x10, faction_objects[faction_index].data());
    }
    Put(title_slots, 0x18, title.data());
    Put(title, 0x10, county_id);
    Put(title, 0x48, title_definition.data());
    Put(title, 0x128, vassal);
    Put(title, 0x11C, std::int32_t{1});
    Put(title_definition, 0x64, std::int32_t{2});
    Put(province, 0x85C, std::uint32_t{0x50726F76});
    Put(province, 0x848, county.data());
    Put(county, 0x3B0, joined_ids.data());
    Put(county, 0x3BC, std::int32_t{1});
    Put(war_slots, 0x18, war.data());
    Put(war, 8, war_id);
    Put(war, 0x0C, std::uint32_t{0x5761725F});
    Register(characters); Register(factions); Register(titles); Register(wars);
    Register(character_slots); Register(faction_slots); Register(title_slots); Register(war_slots);
    Register(character_objects); Register(faction_objects); Register(definitions);
    Register(land); Register(title); Register(title_definition); Register(province); Register(county);
    Register(char_fallback); Register(faction_fallback); Register(title_fallback); Register(war_fallback);
    Register(war); Register(character_members); Register(county_members);
    Register(targeting_ids); Register(joined_ids);
    Register(character_store); Register(faction_store); Register(title_store); Register(war_store);
    Register(character_null); Register(faction_null); Register(title_null); Register(war_null);
    Register(contracts); Register(contract_slots); Register(contract); Register(vassal_land);
    Register(held_counties); Register(contract_ids); Register(contract_store); Register(contract_null);
  }
};

bool Memory(void *opaque, const void *address, void *output, std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto at = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &[base, length] : fixture.ranges) {
    const auto begin = reinterpret_cast<std::uintptr_t>(base);
    if (at >= begin && at - begin <= length && size <= length - (at - begin)) {
      std::memcpy(output, address, size);
      return true;
    }
  }
  return false;
}
bool String(void *opaque, const void *address, std::string &output) noexcept {
  const auto &values = static_cast<Fixture *>(opaque)->strings;
  const auto found = values.find(address);
  if (found == values.end()) return false;
  output = found->second;
  return true;
}
bool Main(void *) noexcept { return true; }
bool Frame(void *opaque, xar::game::PlayerFactionAlertsFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  if (fixture.frame_drift && ++fixture.frame_calls == 2) ++output.snapshot_revision;
  return true;
}
std::size_t Index(void *faction) {
  std::int32_t id = -1;
  std::memcpy(&id, static_cast<std::byte *>(faction) + 0x10, sizeof id);
  return static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
}
std::int64_t *Power(void *faction, std::int64_t *out) {
  *out = current->powers.at(Index(faction));
  if (current->metrics_drift && ++current->power_calls > 4) ++*out;
  return out;
}
std::int64_t *Threshold(void *faction, std::int64_t *out) {
  *out = current->thresholds.at(Index(faction)); return out;
}
std::int64_t *Growth(void *faction, std::int64_t *out) {
  *out = current->growth.at(Index(faction)); return out;
}
std::int32_t Months(void *faction) { return current->months.at(Index(faction)); }
bool AtWar(void *faction) { return current->at_war && Index(faction) == 1; }
bool Human(std::uint32_t id) {
  return current->human && id == static_cast<std::uint32_t>(Fixture::leader);
}
bool Danger(void *, void *faction) {
  const auto index = Index(faction);
  if (index == 1 && current->human) return true;
  return index == 3 ? current->months[index] <= 12 : current->growth[index] > 0;
}
void *Liege(void *character) {
  if (character == current->character_objects[4].data())
    return current->character_objects[1].data();
  return current->char_fallback.data();
}
void *Province(void *title) {
  return title == current->title.data() ? current->province.data() : nullptr;
}
xar::ck3_12002::PlayerFactionAlertsNativeEnvironmentV1 Environment(Fixture &f) {
  xar::ck3_12002::PlayerFactionAlertsNativeEnvironmentV1 e{};
  e.exact_build_admitted = true; e.offline_fixture_function_overrides = true;
  e.character_storage_slot = &f.character_store; e.character_fallback_slot = &f.character_null;
  e.faction_storage_slot = &f.faction_store; e.faction_fallback_slot = &f.faction_null;
  e.landed_title_storage_slot = &f.title_store; e.landed_title_fallback_slot = &f.title_null;
  e.war_storage_slot = &f.war_store; e.war_fallback_slot = &f.war_null;
  e.vassal_contract_storage_slot = &f.contract_store;
  e.vassal_contract_fallback_slot = &f.contract_null;
  e.expected_faction_vtable = Fixture::faction_vtable;
  e.immediate_liege = &Liege; e.title_province = &Province; e.character_is_human = &Human;
  e.power = &Power; e.power_threshold = &Threshold; e.discontent_per_month = &Growth;
  e.months_until_max_discontent = &Months; e.at_war = &AtWar; e.dangerous = &Danger;
  return e;
}
xar::ck3_12002::PlayerFactionAlertsAccessV1 Access(Fixture &f) {
  return {&f, &Frame, &Main, &Memory, &String};
}
bool Read(Fixture &f, xar::game::PlayerFactionAlertsV1 &out) {
  return xar::ck3_12002::ReadPlayerFactionAlertsV1(Environment(f), Access(f), {41}, out) ==
         xar::game::ReadPlayerFactionAlertsResultV1::available;
}
bool FullAndWire() {
  Fixture f;
  xar::game::PlayerFactionAlertsV1 out;
  if (!Read(f, out) || !out.readiness.alert_ready ||
      out.targeting_factions.size() != 3 || out.county_exposures.size() != 1 ||
      !out.planner_projection.dangerous.value_or(false)) return false;
  const auto &county_only = out.targeting_factions[1];
  if (county_only.leader_character_id || !county_only.character_member_ids.empty() ||
      county_only.county_member_title_ids != std::vector<std::int32_t>{Fixture::county_id} ||
      county_only.power.raw != 9000000 || !county_only.dangerous_by_stock_rule ||
      out.targeting_factions[0].power_threshold.raw != 8000000 ||
      out.targeting_factions[0].discontent.raw != 2500000 ||
      out.targeting_factions[0].discontent_per_month.raw != 200000 ||
      out.county_exposures[0].target_character_id != Fixture::other_target ||
      out.readiness.exact_ultimatum_timing_ready) return false;
  const auto json = xar::ck3_12002::SerializePlayerFactionAlertsV1(out);
  return json.find("1.20.0.2") != std::string::npos &&
         json.find("ck3-1.20.0.2-native-player-faction-alerts-v1") != std::string::npos &&
         json.find("1.19.0.6") == std::string::npos &&
         json.find("\"leader_character_id\":null") != std::string::npos;
}
bool KnownEmpty() {
  Fixture f;
  Put(f.land, 0x12C, std::int32_t{0}); Put(f.county, 0x3BC, std::int32_t{0});
  xar::game::PlayerFactionAlertsV1 out;
  return Read(f, out) && out.readiness.alert_ready && out.targeting_factions.empty() &&
         !out.planner_projection.present.value_or(true) &&
         !out.planner_projection.dangerous.value_or(true) &&
         !xar::ck3_12002::SerializePlayerFactionAlertsV1(out).empty();
}
bool IndependentEntity() {
  Fixture f;
  Put(f.land, 0x12C, std::int32_t{0});
  xar::game::PlayerTargetingFactionV1 row;
  const auto result = xar::ck3_12002::ReadFactionEntityV1(
      Environment(f), Access(f), Fixture::liberty, row);
  if (result != xar::ck3_12002::ReadFactionEntityResult12002::available ||
      row.character_member_ids.size() != 2) return false;
  Put(f.faction_objects[1], 0x10, Fixture::liberty + 0x01000000);
  return xar::ck3_12002::ReadFactionEntityV1(Environment(f), Access(f), Fixture::liberty, row) ==
         xar::ck3_12002::ReadFactionEntityResult12002::known_absent;
}
bool StrictExposureThresholdAndWatch() {
  Fixture f;
  f.powers[4] = f.thresholds[4]; f.growth[1] = -200000;
  xar::game::PlayerFactionAlertsV1 out;
  return Read(f, out) && out.county_exposures.empty() &&
         out.targeting_factions[0].danger_reason == "non_peasant_discontent_not_increasing" &&
         !out.targeting_factions[0].dangerous_by_stock_rule;
}
bool WarHandoffAndHuman() {
  Fixture f;
  f.human = true; f.at_war = true; f.growth[1] = 0;
  Put(f.faction_objects[1], 0x8C, Fixture::war_id);
  xar::game::PlayerFactionAlertsV1 out;
  return Read(f, out) && out.targeting_factions[0].leader_is_human &&
         out.targeting_factions[0].faction_war_id == Fixture::war_id &&
         out.planner_projection.war_handoff_faction_ids ==
             std::vector<std::int32_t>{Fixture::liberty};
}
bool DriftAndMigratedCountyOwner() {
  for (int variant = 0; variant < 3; ++variant) {
    Fixture f;
    if (variant == 0) f.metrics_drift = true;
    if (variant == 1) f.frame_drift = true;
    if (variant == 2) Put(f.county_members[0], 0x10, f.faction_objects[3].data());
    xar::game::PlayerFactionAlertsV1 out;
    if (Read(f, out) || !out.targeting_factions.empty() || out.readiness.alert_ready ||
        xar::ck3_12002::SerializePlayerFactionAlertsV1(out).empty()) return false;
  }
  return true;
}
bool ProductionBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto e = xar::ck3_12002::BindPlayerFactionAlertsNativeEnvironmentV1(base, true);
  return e.exact_build_admitted && !e.offline_fixture_function_overrides &&
         reinterpret_cast<std::uintptr_t>(e.faction_storage_slot) == base + 0x5D1DE90 &&
         reinterpret_cast<std::uintptr_t>(e.power) == base + 0x2601EF0 &&
         reinterpret_cast<std::uintptr_t>(e.power_threshold) == base + 0x26021A0 &&
         reinterpret_cast<std::uintptr_t>(e.at_war) == base + 0x2603AB0 &&
         !xar::ck3_12002::BindPlayerFactionAlertsNativeEnvironmentV1(base, false).exact_build_admitted;
}
} // namespace

int main(int argc, char **argv) {
  const std::array cases{
      std::pair{"full row, metrics, county exposure and wire", &FullAndWire},
      std::pair{"known empty", &KnownEmpty},
      std::pair{"independent entity receipt source", &IndependentEntity},
      std::pair{"strict exposure threshold and negative growth", &StrictExposureThresholdAndWatch},
      std::pair{"war handoff and native human identity", &WarHandoffAndHuman},
      std::pair{"actual source drift and new county owner layout", &DriftAndMigratedCountyOwner},
      std::pair{"production exact-build binding", &ProductionBindings}};
  for (const auto &[name, test] : cases) {
    if (!test()) { std::cerr << name << " failed\n"; return 1; }
  }
  if (argc == 3 && std::string_view(argv[1]) == "--emit-fixture") {
    Fixture f;
    xar::game::PlayerFactionAlertsV1 out;
    if (!Read(f, out)) return 1;
    std::ofstream target(argv[2], std::ios::binary);
    target << xar::ck3_12002::SerializePlayerFactionAlertsV1(out) << '\n';
    if (!target.good()) return 1;
  }
  std::cout << "1.20.0.2 faction alerts production-source fixtures passed (7 cases)\n";
  return 0;
}

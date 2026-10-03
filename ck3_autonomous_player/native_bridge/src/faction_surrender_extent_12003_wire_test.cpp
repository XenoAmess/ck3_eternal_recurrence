// One production reader -> serializer fixture. Its IDs are synthetic.
#define main legacy_faction_fixture_entry
#include "ck3_12002_faction_alerts_test.cpp"
#undef main

namespace {
constexpr auto county2_id = Fixture::county_id + 1;
constexpr auto duchy_id = Fixture::county_id + 2;
constexpr auto kingdom_id = Fixture::county_id + 3;
constexpr auto county3_id = Fixture::county_id + 4;
constexpr auto county4_id = Fixture::county_id + 5;
struct ImpactFixture {
  Fixture f;
  Blob<0x70> slots{};
  std::array<Blob<0x1A0>, 5> extra_titles{};
  std::array<Blob<0x68>, 5> extra_definitions{};
  Blob<0x50> government{};
  Blob<0x28> relation{};
  Blob<0x360> active_war{};
  std::int32_t state_faith_id = 17;
  std::array<std::int32_t, 4> duchy_counties{Fixture::county_id, county2_id, county3_id, county4_id};
  std::array<std::int32_t, 1> kingdom_duchies{duchy_id};
  std::array<std::int32_t, 3> actor_titles{county2_id, duchy_id, kingdom_id};
  ImpactFixture() {
    f.Register(slots); f.Register(extra_titles); f.Register(extra_definitions);
    f.Register(government); f.Register(relation); f.Register(active_war);
    f.Register(state_faith_id); f.Register(duchy_counties); f.Register(kingdom_duchies);
    f.Register(actor_titles);
    Put(f.titles, 0x20, slots.data()); Put(f.titles, 0x2C, std::int32_t{7});
    Put(slots, 0x18, f.title.data());
    Put(f.title, 0x108, duchy_id);
    for (std::size_t index = 0; index < extra_titles.size(); ++index) {
      auto &title = extra_titles[index];
      const auto id = county2_id + static_cast<std::int32_t>(index);
      Put(slots, (index + 2) * 0x10 + 8, title.data());
      Put(title, 0x10, id); Put(title, 0x48, extra_definitions[index].data());
      Put(title, 0x128, index >= 3 ? Fixture::other_target : Fixture::actor);
      Put(extra_definitions[index], 0x64, index == 1 ? 3 : index == 2 ? 4 : 2);
      Put(title, 0x108, index == 1 ? kingdom_id : index == 2 ? -1 : duchy_id);
      Put(title, 0x11C, std::int32_t{1});
    }
    Put(extra_titles[1], 0x110, duchy_counties.data());
    Put(extra_titles[1], 0x11C, std::int32_t{3});
    Put(extra_titles[2], 0x110, kingdom_duchies.data());
    Put(extra_titles[2], 0x11C, std::int32_t{1});
    Put(f.land, 0x1E0, actor_titles.data()); Put(f.land, 0x1EC, std::int32_t{3});
    f.targeting_ids[0] = Fixture::populist; Put(f.land, 0x12C, std::int32_t{1});
    Put(f.faction_objects[2], 0x44, Fixture::leader);
    Put(f.county, 0x3BC, std::int32_t{0});
    Put(relation, 0x20, std::int32_t{-1});
    Put(active_war, 8, Fixture::war_id);
  }
};
ImpactFixture *impact_fixture = nullptr;
void *ImpactGovernment(void *) { return impact_fixture->government.data(); }
void *ImpactRelation(void *, void *) { return impact_fixture->relation.data(); }
std::uint64_t ImpactMask(const std::int32_t *id) {
  return *id == 17 ? std::uint64_t{1} << 42 : 0;
}
void *ImpactProvince(void *) { return impact_fixture->f.province.data(); }

bool Emit(ImpactFixture &fixture) {
  impact_fixture = &fixture;
  auto environment = Environment(fixture.f);
  environment.surrender_observations_12003 = true;
  environment.government = &ImpactGovernment;
  environment.government_allows_mask = &ImpactMask;
  environment.pair_relation = &ImpactRelation;
  environment.state_faith_identifier = &fixture.state_faith_id;
  environment.title_province = &ImpactProvince;
  xar::game::PlayerFactionAlertsV1 output;
  if (xar::ck3_12002::ReadPlayerFactionAlertsV1(environment, Access(fixture.f), {41}, output) !=
      xar::game::ReadPlayerFactionAlertsResultV1::available) return false;
  const auto wire = xar::ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      output, "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
      "ck3-1.20.0.3-native-player-faction-alerts-v1");
  if (wire.empty()) return false;
  std::cout << wire << '\n';
  return true;
}
} // namespace

int main() {
  ImpactFixture fixture;
  // Two ROOT realm counties in the same duchy; only one is a faction member.
  if (!Emit(fixture)) return 1;
  // Strict >50%, so two seized out of four is not a majority.
  Put(fixture.extra_titles[1], 0x11C, std::int32_t{4});
  if (!Emit(fixture)) return 2;
  // State-faith and active leader-target war must disable complete ordinary losses.
  Put(fixture.government, 0x40, std::uint64_t{1} << 42);
  if (!Emit(fixture)) return 3;
  Put(fixture.government, 0x40, std::uint64_t{0});
  Put(fixture.relation, 0x20, Fixture::war_id);
  Put(fixture.f.war_slots, 0x18, fixture.active_war.data());
  if (!Emit(fixture)) return 4;
  Put(fixture.active_war, 0x358, std::uint8_t{1});
  if (!Emit(fixture)) return 5;
  // A failed title read is a typed unavailable component, with no loss guessed.
  Put(fixture.extra_titles[1], 0x108, kingdom_id + 0x01000000);
  if (!Emit(fixture)) return 6;
  return 0;
}

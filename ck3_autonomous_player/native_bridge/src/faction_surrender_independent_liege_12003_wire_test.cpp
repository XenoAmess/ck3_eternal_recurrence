// Focused regression for the exact native immediate-liege self return.
#define XAR_SURRENDER_EXTENT_FIXTURE_NO_MAIN
#include "faction_surrender_extent_12003_wire_test.cpp"
#undef XAR_SURRENDER_EXTENT_FIXTURE_NO_MAIN

namespace {
void *IndependentLiegeSelf(void *character) {
  auto *liege = Liege(character);
  return liege == current->char_fallback.data() ? character : liege;
}

bool EmitIndependentLiege(ImpactFixture &fixture, bool returns_self) {
  impact_fixture = &fixture;
  auto environment = Environment(fixture.f);
  environment.surrender_observations_12003 = true;
  environment.government = &ImpactGovernment;
  environment.government_allows_mask = &ImpactMask;
  environment.pair_relation = &ImpactRelation;
  environment.state_faith_identifier = &fixture.state_faith_id;
  environment.title_province = &ImpactProvince;
  if (returns_self) environment.immediate_liege = &IndependentLiegeSelf;
  xar::game::PlayerFactionAlertsV1 output;
  if (xar::ck3_12002::ReadPlayerFactionAlertsV1(
          environment, Access(fixture.f), {41}, output) !=
      xar::game::ReadPlayerFactionAlertsResultV1::available) return false;
  const auto wire = xar::ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      output, "1.20.0.3",
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
      "ck3-1.20.0.3-native-player-faction-alerts-v1");
  if (wire.empty()) return false;
  std::cout << wire << '\n';
  return true;
}
} // namespace

int main() {
  ImpactFixture fixture;
  // Vassal -> independent actor -> itself, matching RVA 0x28BFC70.
  if (!EmitIndependentLiege(fixture, true)) return 1;
  // Keep the previously supported fallback representation.
  if (!EmitIndependentLiege(fixture, false)) return 2;
  // A subsequent title failure must retain successfully read branch predicates.
  Put(fixture.extra_titles[1], 0x108, kingdom_id + 0x01000000);
  if (!EmitIndependentLiege(fixture, true)) return 3;
  return 0;
}

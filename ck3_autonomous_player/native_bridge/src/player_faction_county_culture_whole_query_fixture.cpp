// Focused new fixture. First compile/run belongs to Root's joint batch.
// This imports the existing memory layout scaffold, without running its main.
#define main ExistingFactionAlertFixtureMainNotRun
#include "ck3_12002_faction_alerts_test.cpp"
#undef main

namespace {
std::int32_t CultureOpinion(void *) { return -22; }
std::int64_t *CultureJoinScore(void *, std::int64_t *out, void *) {
  *out = 3'100'000;
  return out;
}
bool CultureCanAdd(void *, void *) { return true; }

struct CultureWholeQueryFixture {
  Fixture base;
  Blob<0x30> cultures{};
  Blob<0x30> culture_slots{};
  std::array<Blob<0x30>, 3> culture_objects{};
  Blob<0x30> culture_fallback{};
  void *culture_store = cultures.data();
  void *culture_null = culture_fallback.data();
  std::int32_t leave_threshold = 5;
  static constexpr std::int32_t county_culture = 0x01000001;
  static constexpr std::int32_t holder_culture = 0x01000002;

  CultureWholeQueryFixture() {
    Put(cultures, 0x20, culture_slots.data());
    Put(cultures, 0x2C, std::int32_t{3});
    const std::array<std::int32_t, 3> ids{0, county_culture, holder_culture};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(culture_objects[index], 0x10, ids[index]);
      Put(culture_slots, index * 0x10 + 8, culture_objects[index].data());
    }
    Put(culture_fallback, 0x10, std::int32_t{-1});
    Put(base.character_objects[1], 0xB0, std::int32_t{0});
    Put(base.character_objects[4], 0xB0, holder_culture);
    Put(base.county, 0x18, Fixture::county_id);
    Put(base.county, 0x388, county_culture);
    Put(base.province, 0x10, std::int32_t{2638});
    for (auto &member : base.county_members)
      Put(member, 0x0C, std::uint8_t{0});
    base.Register(cultures);
    base.Register(culture_slots);
    base.Register(culture_objects);
    base.Register(culture_fallback);
    base.Register(culture_store);
    base.Register(culture_null);
    base.Register(leave_threshold);
  }

  xar::ck3_12002::PlayerFactionAlertsNativeEnvironmentV1 EnvironmentWithCulture() {
    auto environment = Environment(base);
    environment.county_observations_12003 = true;
    environment.culture_storage_slot = &culture_store;
    environment.culture_fallback_slot = &culture_null;
    environment.county_opinion = &CultureOpinion;
    environment.county_faction_finals.join_score = &CultureJoinScore;
    environment.county_faction_finals.can_add = &CultureCanAdd;
    environment.county_faction_finals.leave_score_threshold = &leave_threshold;
    return environment;
  }

  bool ReadWhole(xar::game::PlayerFactionAlertsV1 &output) {
    return xar::ck3_12002::ReadPlayerFactionAlertsV1(
        EnvironmentWithCulture(), Access(base), {41}, output) ==
        xar::game::ReadPlayerFactionAlertsResultV1::available;
  }
};

const xar::game::PlayerFactionCountyMemberObservationV1 *CountyRow(
    const xar::game::PlayerFactionAlertsV1 &output) {
  for (const auto &faction : output.targeting_factions) {
    if (faction.faction_id != Fixture::populist ||
        faction.target_character_id != Fixture::actor ||
        faction.county_member_observations.size() != 1)
      continue;
    return &faction.county_member_observations.front();
  }
  return nullptr;
}

bool ExistingMaterialAvailable(const xar::game::PlayerFactionCountyMemberObservationV1 &row) {
  return row.county_opinion == -22 && row.opinion_status == "available" &&
         row.native_county_join_score_raw == 3'100'000 &&
         row.can_add_county == true && row.removal_queued == false &&
         row.native_leave_score_threshold == 5 &&
         row.native_final_status == "available";
}

void Emit(const xar::game::PlayerFactionAlertsV1 &output) {
  std::cout << xar::ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      output, "1.20.0.3",
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
      "ck3-1.20.0.3-native-player-faction-alerts-v1") << '\n';
}

bool DifferentUsesTargetAndKeepsExistingMaterial() {
  CultureWholeQueryFixture fixture;
  xar::game::PlayerFactionAlertsV1 output;
  if (!fixture.ReadWhole(output) || !output.readiness.alert_ready) return false;
  const auto *row = CountyRow(output);
  if (!row || !ExistingMaterialAvailable(*row) ||
      row->holder_character_id != Fixture::vassal ||
      row->county_culture_id != CultureWholeQueryFixture::county_culture ||
      row->target_culture_id != 0 || row->same_culture_as_target != false ||
      row->culture_relation_status != "available") return false;
  Emit(output);
  return true;
}

bool CultureZeroCanBeSame() {
  CultureWholeQueryFixture fixture;
  Put(fixture.base.county, 0x388, std::int32_t{0});
  xar::game::PlayerFactionAlertsV1 output;
  if (!fixture.ReadWhole(output)) return false;
  const auto *row = CountyRow(output);
  if (!row || row->county_culture_id != 0 || row->target_culture_id != 0 ||
      row->same_culture_as_target != true ||
      row->culture_relation_status != "available") return false;
  Emit(output);
  return true;
}

bool MissingTargetDoesNotInvalidateAlertOrExistingMaterial() {
  CultureWholeQueryFixture fixture;
  Put(fixture.base.character_objects[1], 0xB0, std::int32_t{-1});
  xar::game::PlayerFactionAlertsV1 output;
  if (!fixture.ReadWhole(output) || !output.readiness.alert_ready) return false;
  const auto *row = CountyRow(output);
  if (!row || !ExistingMaterialAvailable(*row) ||
      row->county_culture_id != CultureWholeQueryFixture::county_culture ||
      row->target_culture_id || row->same_culture_as_target ||
      row->culture_relation_status != "unavailable") return false;
  Emit(output);
  return true;
}

bool GenerationMismatchIsMissingNotFalse() {
  CultureWholeQueryFixture fixture;
  Put(fixture.base.county, 0x388, std::int32_t{0x02000001});
  xar::game::PlayerFactionAlertsV1 output;
  if (!fixture.ReadWhole(output) || !output.readiness.alert_ready) return false;
  const auto *row = CountyRow(output);
  if (!row || !ExistingMaterialAvailable(*row) || row->county_culture_id ||
      row->target_culture_id != 0 || row->same_culture_as_target ||
      row->culture_relation_status != "unavailable") return false;
  Emit(output);
  return true;
}
} // namespace

int main() {
  const std::array cases{
      std::pair{"different culture uses target, keeps native final materials", &DifferentUsesTargetAndKeepsExistingMaterial},
      std::pair{"actual zero culture can be same", &CultureZeroCanBeSame},
      std::pair{"missing culture is independent of alert/material readiness", &MissingTargetDoesNotInvalidateAlertOrExistingMaterial},
      std::pair{"full generation mismatch is missing input", &GenerationMismatchIsMissingNotFalse},
  };
  for (const auto &[name, test] : cases) {
    if (!test()) {
      std::cerr << "RED: " << name << '\n';
      return 1;
    }
  }
  std::cerr << "GREEN: county culture whole-query fixtures\n";
  return 0;
}

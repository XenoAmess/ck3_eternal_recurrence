// Reuse only the existing fixture construction and callback seams. Its original
// seven-case main is compiled but never run by this focused extension test.
#define main county_component_previous_main
#include "ck3_12003_county_conversion_test.cpp"
#undef main

namespace {
struct ValueFixture : Fixture {
  std::array<Bytes<0x4C0>, 5> value_rites{};
  std::array<Bytes<0x10>, 5> faiths{};
  std::array<std::uint32_t, 5> value_rite_ids{152, 154, 153, 0, 0x83000003};
  std::array<std::uint32_t, 5> faith_ids{23, 77, 55, 23, 66};
  std::array<std::int32_t, 3> opinions{-42, 0, 17};
  Bytes<0x68> government{};
  std::array<std::int32_t, 2> flags{1, 2};
  Bytes<0x130> china{};
  static constexpr std::int32_t china_id = 0x02000008;
  std::int32_t failed_faith = -1;
  int opinion_calls = 0, title_lookup_calls = 0;

  ValueFixture() {
    Put(incumbent, r::kCharacterRiteOffset, std::uint32_t{154});
    for (std::size_t i = 0; i < value_rites.size(); ++i) {
      Put(value_rites[i], 8, value_rite_ids[i]);
      Put(value_rites[i], 0x4B8, faith_ids[i]);
      Put(faiths[i], 8, faith_ids[i]);
    }
    Put(government, 0x50, flags.data());
    Put(government, 0x5C, std::int32_t{0});
    Put(china, 0x10, china_id); Put(china, 0x128, owner_id);
    Put(title_slots, 8 * 0x10 + 8, china.data());
  }
};
ValueFixture *vf = nullptr;
const void *ValueCountyRite(const void *county) {
  for (std::size_t i = 0; i < 3; ++i)
    if (county == vf->counties[i].data()) return vf->value_rites[i + 2].data();
  vf->bad_arguments = true; return nullptr;
}
const void *ValueCharacterRite(const void *character) {
  if (character == vf->owner.data()) return vf->value_rites[0].data();
  if (character == vf->incumbent.data()) return vf->value_rites[1].data();
  vf->bad_arguments = true; return nullptr;
}
const void *ValueRiteFaith(const void *rite) {
  for (std::size_t i = 0; i < 5; ++i)
    if (rite == vf->value_rites[i].data())
      return static_cast<int>(i) == vf->failed_faith ? nullptr : vf->faiths[i].data();
  vf->bad_arguments = true; return nullptr;
}
const void *ValueGovernment(const void *owner) {
  if (owner != vf->owner.data()) vf->bad_arguments = true;
  return vf->government.data();
}
const std::string *ValueIdentifierName(std::int32_t id) {
  static const std::string celestial = "government_is_celestial";
  static const std::string budget = "government_uses_ministry_budget";
  if (id == 1) return &celestial;
  if (id == 2) return &budget;
  vf->bad_arguments = true; return nullptr;
}
const void *ValueTitleByKey(const void *key) {
  ++vf->title_lookup_calls;
  if (std::string_view(static_cast<const char *>(key), 7) != "h_china" ||
      Load<std::uint64_t>(key, 0x10) != 7 || Load<std::uint64_t>(key, 0x18) != 15)
    vf->bad_arguments = true;
  return vf->china.data();
}
std::int32_t ValueCountyOpinion(const void *county) {
  ++vf->opinion_calls;
  for (std::size_t i = 0; i < 3; ++i)
    if (county == vf->counties[i].data()) return vf->opinions[i];
  vf->bad_arguments = true; return 999;
}
q::Environment BindValues(ValueFixture &fixture) {
  vf = &fixture;
  auto e = Bind(fixture);
  e.value_inputs_enabled = true;
  e.county_rite = &ValueCountyRite;
  e.character_rite = &ValueCharacterRite;
  e.rite_faith = &ValueRiteFaith;
  e.government = &ValueGovernment;
  e.title_by_key = &ValueTitleByKey;
  e.identifier_name = &ValueIdentifierName;
  e.county_opinion = &ValueCountyOpinion;
  e.government_fallback_slot = &fixture.fallback_ptr;
  return e;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 100;
  const std::filesystem::path dir{argv[1]};
  ValueFixture fixture; auto environment = BindValues(fixture); q::Observation out{};
  if (!Check(q::ReadCountyConversion12003(environment, 201, out) && out.value_inputs &&
      out.value_inputs->available, "value inputs from production reader") ||
      !Check(out.value_inputs->owner_faith_id == 23U && out.value_inputs->incumbent_faith_id == 77U &&
      out.value_inputs->owner_has_access_to_ministry == false, "actual distinct owner/chaplain faith and ministry") ||
      !Check(out.value_inputs->candidates[0].destination_rite_id == 154 &&
      out.value_inputs->candidates[1].destination_rite_id == 152 &&
      out.value_inputs->candidates[2].destination_rite_id == 154,
      "off-Faith matrix uses owner only for owner-Faith county") ||
      !Check(out.value_inputs->candidates[0].current_popular_opinion == 17 &&
      out.value_inputs->candidates[1].current_popular_opinion == 0 &&
      out.value_inputs->candidates[2].current_popular_opinion == -42,
      "actual current-holder county opinion int32 includes negative and legal zero") ||
      !Check(fixture.title_lookup_calls == 0 && fixture.opinion_calls == 3 && !fixture.bad_arguments,
      "non-ministry skips title lookup and opinion uses county receiver")) return 1;
  Wire(dir, "off-faith-candidate-values.json", out);

  Put(fixture.value_rites[1], 0x4B8, std::uint32_t{23}); Put(fixture.faiths[1], 8, std::uint32_t{23});
  Put(fixture.task, 0x18, fixture.conversion_type.data());
  Put(fixture.task, 0x48, std::uint32_t{8}); Put(fixture.task, 0x50, Fixture::province_ids[1]);
  fixture.task[0x39] = std::byte{1};
  if (!Check(q::ReadCountyConversion12003(environment, 202, out) && out.value_inputs->available,
      "current conversion and aligned chaplain values") ||
      !Check(out.value_inputs->current_target && out.value_inputs->current_target->county_faith_id == 23 &&
      out.value_inputs->current_target->destination_rite_id == 152 &&
      out.value_inputs->current_target->current_popular_opinion == 0 &&
      !out.value_inputs->current_target->faith_changes && out.value_inputs->current_target->rite_changes,
      "current real target has Rite-only destination and zero opinion") ||
      !Check(std::all_of(out.value_inputs->candidates.begin(), out.value_inputs->candidates.end(),
      [](const auto &row) { return row.destination_rite_id == 152 && row.destination_faith_id == 23; }),
      "aligned chaplain propagates owner Rite for every county") ||
      !Check(out.current_conversion_monthly_rate_raw == 777000 && out.current_task_frozen == true,
      "new value inputs preserve independent actual rate and frozen state")) return 2;
  Wire(dir, "aligned-current-target-values.json", out);

  Put(fixture.value_rites[1], 0x4B8, std::uint32_t{77}); Put(fixture.faiths[1], 8, std::uint32_t{77});
  Put(fixture.government, 0x5C, std::int32_t{2});
  if (!Check(q::ReadCountyConversion12003(environment, 203, out) && out.value_inputs->available &&
      out.value_inputs->owner_has_access_to_ministry == true, "exact three-part ministry access") ||
      !Check(std::all_of(out.value_inputs->candidates.begin(), out.value_inputs->candidates.end(),
      [](const auto &row) { return row.destination_rite_id == 152; }),
      "ministry overrides off-Faith county matrix") ||
      !Check(fixture.title_lookup_calls == 1 && !fixture.bad_arguments,
      "fixed h_china native string resolver and full TitleID roundtrip")) return 3;
  Wire(dir, "ministry-destination-values.json", out);

  Put(fixture.china, 0x128, Fixture::other_holder_id);
  if (!Check(q::ReadCountyConversion12003(environment, 204, out) && out.value_inputs->available &&
      out.value_inputs->owner_has_access_to_ministry == false &&
      out.value_inputs->candidates[0].destination_rite_id == 154,
      "ministry flags alone do not imply h_china ownership")) return 4;
  Wire(dir, "ministry-title-not-held.json", out);

  fixture.failed_faith = 2;
  if (!Check(q::ReadCountyConversion12003(environment, 205, out) && out.available && out.value_inputs &&
      !out.value_inputs->available && out.value_inputs->failure == "candidate_values_unavailable" &&
      out.value_inputs->candidates.empty() && out.candidates.size() == 3,
      "value getter failure is separate from proven base county query") ||
      !Check(fixture.allocations == fixture.releases && !fixture.bad_arguments,
      "new readonly getter path keeps target allocation balanced")) return 5;
  Wire(dir, "value-getter-unavailable.json", out);
  std::cout << "PASS checks=" << checks << " cases=5 actual_reader=true actual_serializer=true live=false\n";
  return 0;
}

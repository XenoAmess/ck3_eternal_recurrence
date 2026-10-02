#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/ck3_12003_steward_develop_county.hpp"

#include <array>
#include <cstring>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

using Failure = xar::game::StewardDevelopCountyFailureReasonV1;
using Result = xar::game::ReadStewardDevelopCountyCandidatesResultV1;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "steward develop county core fixture failed at line " +
        std::to_string(location.line()));
  }
}

struct Fixture {
  xar::game::StewardDevelopCountyCandidatesFrameV1 frame{
      77, 53'175'816, true, true, true, true, 0x0100002A};
  xar::ck3_11906::StewardDevelopCountyCandidatesSourceSampleV1 sample;
  int source_reads = 0;
  bool drift_identity = false;
  bool drift_value = false;
  bool drift_frame = false;

  Fixture() {
    sample.player_character_id = frame.played_character_id;
    sample.steward_character_id = 0x02000011;
    sample.player_identity_round_trip = true;
    sample.steward_identity_round_trip = true;
    sample.shown = true;
    sample.valid = true;
    sample.steward_increase_development_value_raw = 9'000'000;
    sample.current_gold_raw = 15'000'000;
    sample.has_active_improve_development_directive = true;
    xar::ck3_11906::StewardDevelopCountyCandidateSourceRowV1 row;
    row.candidate.county_title_id = 0x0300000A;
    row.candidate.capital_province_id = 921;
    row.candidate.holder_character_id = frame.played_character_id;
    row.candidate.is_player_capital = true;
    row.candidate.directly_held_by_player = true;
    row.candidate.native_legal = true;
    row.candidate.development_level_raw = 12'000'000;
    row.candidate.development_progress_raw = 35'000;
    row.candidate.monthly_development_rate_raw = 8'250;
    row.candidate.max_development_level_raw = 100'000'000;
    row.candidate.terrain_key = "plains";
    row.candidate.same_culture_as_player = true;
    row.candidate.cultural_acceptance_threshold_passed = true;
    row.county_title_identity_round_trip = true;
    row.capital_province_identity_round_trip = true;
    row.holder_character_identity_round_trip = true;
    sample.candidates.push_back(row);
  }
};

bool MainThread(void *) noexcept { return true; }

bool CaptureFrame(
    void *context,
    xar::game::StewardDevelopCountyCandidatesFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame;
  if (fixture.drift_frame && fixture.source_reads >= 2) {
    ++output.snapshot_revision;
  }
  return true;
}

bool ReadSource(
    void *context,
    xar::ck3_11906::StewardDevelopCountyCandidatesSourceSampleV1
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.sample;
  ++fixture.source_reads;
  if (fixture.source_reads == 2 && fixture.drift_identity) {
    ++output.candidates.front().candidate.county_title_id;
  }
  if (fixture.source_reads == 2 && fixture.drift_value) {
    ++output.candidates.front().candidate.monthly_development_rate_raw;
  }
  return true;
}

xar::ck3_11906::StewardDevelopCountyCandidatesAccessV1 Access(Fixture &f) {
  return {&f, CaptureFrame, MainThread, ReadSource};
}

xar::ck3_11906::StewardDevelopCountyCandidatesNativeEnvironmentV1
FixtureEnvironment() {
  return {0, true, true};
}

void TestProductionStrictUnavailable() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  auto environment =
      BindStewardDevelopCountyCandidatesNativeEnvironmentV1(0x140000000, true);
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             environment, Access(fixture), {fixture.frame.snapshot_revision},
             output) == Result::unavailable);
  Require(output.unavailable_reason == Failure::native_reader_not_frozen);
  Require(fixture.source_reads == 0);

  environment.offline_fixture_source = true;
  Require(ReadStewardDevelopCountyCandidatesV1(
             environment, Access(fixture), {fixture.frame.snapshot_revision},
             output) == Result::unavailable);
  Require(output.unavailable_reason ==
         Failure::offline_fixture_source_not_authorized);
  Require(fixture.source_reads == 0);
}

void TestOfflineFixtureHappyPath() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(fixture),
             {fixture.frame.snapshot_revision}, output) == Result::available);
  Require(fixture.source_reads == 2);
  Require(output.status ==
         xar::game::StewardDevelopCountyCandidatesStatusV1::available);
  Require(output.readiness.ready && output.same_frame_stable);
  Require(output.player_character_id == fixture.frame.played_character_id);
  Require(output.steward_character_id == fixture.sample.steward_character_id);
  Require(output.task_key == "task_develop_county");
  Require(output.target_selection_mode == "engine_random_unscored");
  Require(output.candidates.size() == 1);
  Require(output.candidates.front().capital_province_id == 921);
  Require(output.candidates.front().monthly_development_rate_raw == 8'250);
}

void TestDriftRejection() {
  using namespace xar::ck3_11906;
  for (int mode = 0; mode != 3; ++mode) {
    Fixture fixture;
    fixture.drift_identity = mode == 0;
    fixture.drift_value = mode == 1;
    fixture.drift_frame = mode == 2;
    xar::game::StewardDevelopCountyCandidatesV1 output;
    Require(ReadStewardDevelopCountyCandidatesV1(
               FixtureEnvironment(), Access(fixture),
               {fixture.frame.snapshot_revision}, output) ==
           Result::unavailable);
    const auto expected =
        mode == 0 ? Failure::identity_drift
                  : mode == 1 ? Failure::native_sample_drift
                              : Failure::same_frame_drift;
    Require(output.unavailable_reason == expected);
    Require(output.candidates.empty() && !output.readiness.ready);
  }
}

void TestIdentityAndSchemaRejection() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  fixture.sample.candidates.front().holder_character_identity_round_trip =
      false;
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(fixture),
             {fixture.frame.snapshot_revision}, output) ==
         Result::unavailable);
  Require(output.unavailable_reason == Failure::identity_round_trip_failed);

  Fixture signed_rates;
  signed_rates.sample.candidates.front().candidate.development_progress_raw =
      -1;
  signed_rates.sample.candidates.front().candidate.monthly_development_rate_raw =
      -500;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(signed_rates),
             {signed_rates.frame.snapshot_revision}, output) ==
          Result::available);

  Fixture invalid_key;
  invalid_key.sample.candidates.front().candidate.terrain_key = "Bad-Key";
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(invalid_key),
             {invalid_key.frame.snapshot_revision}, output) ==
          Result::unavailable);
  Require(output.unavailable_reason == Failure::schema_invariant_failed);

  Fixture invalid;
  invalid.sample.valid = false;
  invalid.sample.task_failure_reason = "native_fixture_invalid";
  // Invalid tasks do not publish a candidate domain.
  invalid.sample.candidates.clear();
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(invalid),
             {invalid.frame.snapshot_revision}, output) == Result::available);
  Require(output.valid == false && output.candidates.empty());
}

template <std::size_t Size, typename T>
void Put(std::array<std::byte, Size> &object, std::size_t offset, const T &value) {
  Require(offset + sizeof(T) <= object.size());
  std::memcpy(object.data() + offset, &value, sizeof(T));
}

template <std::size_t Size>
void PutKey(std::array<std::byte, Size> &object, const char *key) {
  const auto length = std::strlen(key);
  Require(length > 15);
  Put(object, 0x18, key);
  Put(object, 0x28, length);
  Put(object, 0x30, length);
}

struct MaterialFixture {
  static constexpr std::int32_t owner_id = 0x0100002A;
  static constexpr std::int32_t steward_id = 0x02000011;
  static constexpr std::int32_t vassal_id = 0x03000037;
  static constexpr std::int32_t active_id = 0x05000004;
  std::array<std::byte, 0x200> owner{}, steward{}, vassal{};
  std::array<std::byte, 0x260> extension{};
  std::array<std::byte, 0x80> active{}, active_type{}, develop_type{};
  std::array<std::byte, 0x40> position{}, character_database{}, task_database{}, title_database{};
  std::array<std::byte, 64 * 0x10> character_slots{}, title_slots{};
  std::array<std::byte, 8 * 0x10> task_slots{};
  std::array<std::array<std::byte, 0x138>, 3> titles{};
  std::array<std::array<std::byte, 0x40>, 3> counties{};
  std::array<std::array<std::byte, 0x870>, 3> provinces{};
  std::array<const void *, 4> province_slots{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x150> game_data{};
  void *character_storage = character_database.data();
  void *task_storage = task_database.data();
  void *title_storage = title_database.data();
  void *state_slot = game_state.data();
  void *type_database = develop_type.data();
  void *fallback = nullptr;
  std::array<std::int32_t, 1> task_ids{active_id};
  bool shown = true, valid = true;
  bool drift_frame = false, drift_growth = false;
  int captures = 0, productions = 0, releases = 0, growth_reads = 0;

  MaterialFixture() {
    Put(owner, 0x18, owner_id);
    Put(steward, 0x18, steward_id);
    Put(vassal, 0x18, vassal_id);
    Put(owner, 0x1C0, extension.data());
    Put(extension, 0x230, task_ids.data());
    Put(extension, 0x23C, std::int32_t{1});
    Put(character_database, 0x20, character_slots.data());
    Put(character_database, 0x2C, std::int32_t{64});
    Put(character_slots, 42 * 0x10 + 8, owner.data());
    Put(character_slots, 17 * 0x10 + 8, steward.data());
    Put(character_slots, 55 * 0x10 + 8, vassal.data());
    Put(task_database, 0x20, task_slots.data());
    Put(task_database, 0x2C, std::int32_t{8});
    Put(task_slots, 4 * 0x10 + 8, active.data());
    Put(active, 0x10, active_id);
    Put(active, 0x18, active_type.data());
    Put(active, 0x40, steward_id);
    Put(active, 0x44, owner_id);
    PutKey(active_type, "task_collect_taxes");
    PutKey(develop_type, "task_develop_county");
    PutKey(position, "councillor_steward");
    Put(active_type, 0x40, position.data());
    Put(develop_type, 0x40, position.data());
    Put(develop_type, 0x48, std::int32_t{1});
    Put(develop_type, 0x4C, std::int32_t{2});
    Put(develop_type, 0x50, std::int32_t{3});
    Put(develop_type, 0x54, std::int32_t{2});
    Put(title_database, 0x20, title_slots.data());
    Put(title_database, 0x2C, std::int32_t{64});
    for (std::size_t index = 0; index < provinces.size(); ++index) {
      const auto title_id = std::int32_t{0x0400000A} + static_cast<std::int32_t>(index);
      Put(titles[index], 0x10, title_id);
      Put(titles[index], 0x128, index == 0 ? owner_id : vassal_id);
      Put(title_slots, (10 + index) * 0x10 + 8, titles[index].data());
      Put(counties[index], 0x18, title_id);
      Put(provinces[index], 0x10, static_cast<std::int32_t>(index + 1));
      Put(provinces[index], 0x848, counties[index].data());
      Put(provinces[index], 0x85C, std::uint32_t{0x50726F76});
      province_slots[index + 1] = provinces[index].data();
      Put(counties[index], 0x20, std::int64_t{index == 0 ? 10'000 : index == 1 ? 250 : 0});
      Put(counties[index], 0x28, std::int64_t{index == 0 ? -1'750 : index == 1 ? -1'000 : 0});
      Put(counties[index], 0x30, std::int64_t{2'600'000 + static_cast<std::int64_t>(index) * 100'000});
    }
    Put(game_state, 0xA0, game_data.data());
    Put(game_data, 0x140, province_slots.data());
    Put(game_data, 0x14C, std::int32_t{4});
  }
};

MaterialFixture *g_material = nullptr;

bool MaterialCapture(void *opaque, xar::game::StewardDevelopCountyCandidatesFrameV1 &out) noexcept {
  auto &fixture = *static_cast<MaterialFixture *>(opaque);
  ++fixture.captures;
  out = {77, 53'328'600, true, true, true, true, MaterialFixture::owner_id};
  if (fixture.drift_frame && fixture.captures == 2) ++out.date_raw;
  return true;
}

void MaterialInitialize(void *allocator, std::uintptr_t *data, std::int32_t *capacity) {
  *data = reinterpret_cast<std::uintptr_t>(allocator) + 8;
  *capacity = 64;
}

void UnusedCouncilProducer(const void *, const void *, bool,
                          xar::ck3_12003::DevelopVector *) {}

void MaterialRelease(void *allocator, void *data, std::size_t element_size) {
  Require(element_size == 8);
  Require(data == static_cast<std::byte *>(allocator) + 8);
  ++g_material->releases;
}

std::int32_t MaterialHash(void *unused, const char *key, std::uint32_t size) {
  Require(unused == nullptr && size == 19 && std::string_view(key, size) == "task_develop_county");
  return 0x123456;
}

const void *MaterialLookup(const void *database, std::int32_t hash) {
  Require(database == g_material->type_database && hash == 0x123456);
  return g_material->develop_type.data();
}

const void *MaterialLiege(const void *character) {
  Require(character == g_material->steward.data());
  return g_material->owner.data();
}

const void *MaterialCapital(const void *character) {
  Require(character == g_material->owner.data());
  return g_material->provinces[0].data();
}

bool MaterialHuman(std::int32_t id) { return id == MaterialFixture::owner_id; }

void CheckMaterialScopes(const void *type, const void *scopes) {
  Require(type == g_material->develop_type.data());
  std::array<std::int32_t, 2> ids{};
  std::memcpy(ids.data(), scopes, sizeof(ids));
  Require(ids[0] == MaterialFixture::steward_id && ids[1] == MaterialFixture::owner_id);
}

bool MaterialShown(const void *type, const void *scopes) {
  CheckMaterialScopes(type, scopes);
  return g_material->shown;
}

bool MaterialValid(const void *type, const void *scopes, void *tooltip) {
  CheckMaterialScopes(type, scopes);
  Require(tooltip == nullptr);
  return g_material->valid;
}

bool MaterialTarget(const void *type, const void *steward, const void *province, void *tooltip) {
  Require(type == g_material->develop_type.data() && steward == g_material->steward.data() && tooltip == nullptr);
  // Independent final predicate results are observations, including false.
  return province != g_material->provinces[2].data();
}

std::int64_t *MaterialGrowth(std::int64_t *out, const void *county, void *tooltip) {
  Require(tooltip == nullptr);
  std::memcpy(out, static_cast<const std::byte *>(county) + 0x20, sizeof(*out));
  ++g_material->growth_reads;
  if (g_material->drift_growth && g_material->growth_reads > 3) ++*out;
  return out;
}

std::int64_t *MaterialDecay(std::int64_t *out, const void *county, void *tooltip) {
  Require(tooltip == nullptr);
  std::memcpy(out, static_cast<const std::byte *>(county) + 0x28, sizeof(*out));
  return out;
}

std::int64_t *MaterialCurrent(const void *type, std::int64_t *out, const void *scopes) {
  CheckMaterialScopes(type, scopes);
  std::int32_t province_id = 0;
  std::uint16_t tag = 0;
  std::memcpy(&tag, static_cast<const std::byte *>(scopes) + 8, sizeof(tag));
  std::memcpy(&province_id, static_cast<const std::byte *>(scopes) + 0x10, sizeof(province_id));
  Require(tag == 8 && province_id >= 1 && province_id <= 3);
  std::memcpy(out, g_material->counties[static_cast<std::size_t>(province_id - 1)].data() + 0x30, sizeof(*out));
  return out;
}

std::int64_t *MaterialMaximum(const void *type, std::int64_t *out, const void *scopes) {
  CheckMaterialScopes(type, scopes);
  *out = 10'000'000;
  return out;
}

void MaterialProduce(const void *steward, const void *type, bool first_only,
                     xar::ck3_12003::DevelopVector *vector, bool expand) {
  Require(steward == g_material->steward.data() && type == g_material->develop_type.data());
  Require(!first_only && expand && vector->capacity == 64);
  std::int32_t player_scope = 0;
  std::memcpy(&player_scope, static_cast<const std::byte *>(type) + 0x4C, sizeof(player_scope));
  Require(player_scope == 2); // Full realm, including the vassal-held county.
  std::array<const void *, 3> rows{g_material->provinces[2].data(),
      g_material->provinces[0].data(), g_material->provinces[1].data()};
  std::memcpy(reinterpret_cast<void *>(vector->data_address), rows.data(), sizeof(rows));
  vector->count = 3;
  ++g_material->productions;
}

xar::ck3_12003::StewardDevelopCountyEnvironment12003 MaterialEnvironment(MaterialFixture &fixture) {
  using namespace xar::ck3_12003;
  g_material = &fixture;
  auto environment = BindStewardDevelopCounty12003(0x140000000, kExecutableSha256);
  environment.offline_fixture_function_overrides = true;
  environment.council.offline_fixture_function_overrides = true;
  environment.council.character_storage_slot = &fixture.character_storage;
  environment.council.character_fallback_slot = &fixture.fallback;
  environment.council.active_task_storage_slot = &fixture.task_storage;
  environment.council.active_task_fallback_slot = &fixture.fallback;
  environment.council.allocator_vtable = 1;
  environment.council.fallback_allocator = 2;
  environment.council.initialize_vector = &MaterialInitialize;
  environment.council.produce_candidates = &UnusedCouncilProducer;
  environment.council.release_allocation = &MaterialRelease;
  environment.game_state_slot = &fixture.state_slot;
  environment.title_storage_slot = &fixture.title_storage;
  environment.title_fallback_slot = &fixture.fallback;
  environment.task_type_database_slot = &fixture.type_database;
  environment.task_type_fallback_slot = &fixture.fallback;
  environment.hash_key = &MaterialHash;
  environment.lookup_type = &MaterialLookup;
  environment.immediate_liege = &MaterialLiege;
  environment.capital_province = &MaterialCapital;
  environment.is_human = &MaterialHuman;
  environment.shown = &MaterialShown;
  environment.valid = &MaterialValid;
  environment.target_valid = &MaterialTarget;
  environment.growth = &MaterialGrowth;
  environment.decay = &MaterialDecay;
  environment.current_progress = &MaterialCurrent;
  environment.maximum_progress = &MaterialMaximum;
  environment.produce_targets = &MaterialProduce;
  return environment;
}

xar::game::StewardDevelopCountyCandidatesV1 ReadMaterial(MaterialFixture &fixture) {
  const auto environment = MaterialEnvironment(fixture);
  const xar::ck3_12003::StewardDevelopCountyAccess12003 access{&fixture, &MaterialCapture, &MainThread, nullptr};
  xar::game::StewardDevelopCountyCandidatesV1 output;
  xar::ck3_12003::ReadStewardDevelopCounty12003(environment, access, {77}, output);
  return output;
}

void TestMaterialProduction(const std::filesystem::path &output_directory) {
  MaterialFixture available;
  const auto output = ReadMaterial(available);
  Require(output.status == xar::game::StewardDevelopCountyCandidatesStatusV1::available);
  Require(output.material && output.material->candidate_collection_complete);
  Require(output.readiness.ready && output.same_frame_stable);
  Require(available.productions == 2 && available.releases == 2);
  Require(output.material->candidates.size() == 3);
  const auto &rows = output.material->candidates;
  Require(rows[0].county_title_id == 0x0400000A && rows[0].native_collection_ordinal == 1);
  Require(rows[0].is_player_capital && rows[0].directly_held_by_player && rows[0].native_target_valid);
  Require(rows[1].holder_character_id == MaterialFixture::vassal_id && !rows[1].directly_held_by_player);
  Require(rows[0].monthly_development_rate.raw == 8'250 && rows[1].monthly_development_rate.raw == -750);
  Require(rows[2].monthly_development_rate.raw == 0 && !rows[2].native_target_valid);
  Require(rows[0].development_progress_current.raw == 2'600'000 && rows[0].development_progress_maximum.raw == 10'000'000);
  const auto &binding = output.material->current_active_task_binding.value();
  Require(binding.task_key == "task_collect_taxes" && binding.task_type == xar::game::CampaignRootCouncilTaskTypeV1::general);
  Require(!binding.target && binding.progress && !binding.progress->current && !binding.progress->maximum);
  const auto available_json = xar::ck3_11906::SerializeStewardDevelopCountyQueryResultV1(
      "develop-material-available", 1, output);
  Require(!available_json.empty() && available_json.find(xar::ck3_12003::kExecutableSha256) != std::string::npos);

  MaterialFixture blocked;
  blocked.valid = false;
  const auto blocked_output = ReadMaterial(blocked);
  Require(blocked_output.status == xar::game::StewardDevelopCountyCandidatesStatusV1::available);
  Require(blocked_output.valid == false && blocked_output.shown == true);
  Require(blocked_output.task_failure_reason == "task_invalid" && blocked_output.readiness.ready);
  Require(blocked_output.material->candidate_collection_complete && blocked_output.material->candidates.empty());
  Require(blocked.productions == 0 && blocked.releases == 0);
  const auto blocked_json = xar::ck3_11906::SerializeStewardDevelopCountyQueryResultV1(
      "develop-material-blocked", 2, blocked_output);
  Require(!blocked_json.empty());
  if (!output_directory.empty()) {
    std::filesystem::create_directories(output_directory);
    std::ofstream available_file(output_directory / "develop_material_available.json", std::ios::binary);
    available_file << available_json;
    Require(available_file.good());
    std::ofstream blocked_file(output_directory / "develop_material_blocked.json", std::ios::binary);
    blocked_file << blocked_json;
    Require(blocked_file.good());
  }
}

void TestMaterialFailures() {
  MaterialFixture frame_drift;
  frame_drift.drift_frame = true;
  const auto drift = ReadMaterial(frame_drift);
  Require(drift.unavailable_reason == Failure::same_frame_drift && drift.material->candidates.empty());
  MaterialFixture numeric_drift;
  numeric_drift.drift_growth = true;
  const auto numeric = ReadMaterial(numeric_drift);
  Require(numeric.unavailable_reason == Failure::native_sample_drift && numeric_drift.releases == 2);
  MaterialFixture stale_title;
  Put(stale_title.titles[0], 0x10, std::int32_t{0x0600000A});
  const auto stale = ReadMaterial(stale_title);
  Require(stale.unavailable_reason == Failure::identity_round_trip_failed && stale_title.releases == 1);
  MaterialFixture not_shown;
  not_shown.shown = false;
  const auto hidden = ReadMaterial(not_shown);
  Require(hidden.shown == false && hidden.task_failure_reason == "task_not_shown" && hidden.readiness.ready);
  Require(hidden.material->candidate_collection_complete && hidden.material->candidates.empty());
  MaterialFixture scope;
  Put(scope.develop_type, 0x4C, std::int32_t{3});
  const auto wrong_scope = ReadMaterial(scope);
  Require(wrong_scope.unavailable_reason == Failure::native_reader_not_frozen && scope.productions == 0);
}

} // namespace

int main(int argc, char **argv) {
  try {
    using namespace xar::ck3_11906;
    static_assert(kStewardDevelopCountyCandidatesV1ExecutableSha256.size() ==
                  64);
    Require(StewardDevelopCountyFailureReasonKeyV1(
               Failure::native_reader_not_frozen) ==
           "native_reader_not_frozen");
    TestProductionStrictUnavailable();
    TestOfflineFixtureHappyPath();
    TestDriftRejection();
    TestIdentityAndSchemaRejection();
    std::filesystem::path output_directory;
    if (argc == 3 && std::string_view(argv[1]) == "--material-json-dir") output_directory = argv[2];
    TestMaterialProduction(output_directory);
    TestMaterialFailures();
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

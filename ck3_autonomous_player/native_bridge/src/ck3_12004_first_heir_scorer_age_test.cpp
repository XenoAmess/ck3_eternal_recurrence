#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12002_family_fertility_floor.hpp"
#include "xar_bridge/ck3_12002_family_scorer_age.hpp"
#include "xar_bridge/ck3_12002_family_wire.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t kActor = 0x03000001;
constexpr std::int32_t kHeir = 0x03000002;
constexpr std::int32_t kRecipient = 0x03000004;
constexpr std::int64_t kAcceptance = 1'600'000;
constexpr std::int64_t kHeirFertility = 30'000;
constexpr std::array<std::int32_t, 5> kCandidateIds{
    0x03000003, 0x03000005, 0x03000006, 0x03000007, 0x03000008};
constexpr std::array<std::size_t, 5> kCandidateSlots{2, 4, 5, 6, 7};
constexpr std::array<std::int32_t, 8> kCharacterHouses{
    100, 100, 300, -1, 301, 302, 303, 304};
constexpr std::array<std::int32_t, 6> kHouseIds{100, 300, 301, 302, 303, 304};
constexpr std::array<std::int32_t, 6> kDynastyIds{200, 400, 401, 402, 403, 404};

struct Scene {
  std::string_view name;
  std::int16_t heir_override = 16;
  std::array<std::int16_t, 5> candidate_overrides{16, 16, 16, 16, 16};
  std::int16_t measure = 16;
  std::int32_t upper = 45;
  std::uint8_t heir_selector = 0;
  std::uint8_t candidate_selector = 1;
  std::int32_t threshold_zero = 16;
  std::int32_t threshold_one = 16;
  bool bind_upper = true;
  bool deny_upper = false;
  bool deny_heir_override = false;
  bool deny_candidate_override = false;
  bool request_matrilineal = false;
};

template <typename T>
void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
template <typename T>
T Load(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(T));
  return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

// Only memory/context scaffolding is reused from ck3_12002_family_test.cpp.
// No old main, candidate enumerator, native producer scorer or action is run.
void *local_player = nullptr;
void *definition = nullptr;
std::array<void *, 8> projection_characters{};
std::size_t contexts = 0;
std::size_t destroys = 0;

void *LocalPlayer(void *) { return local_player; }
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient,
              std::int32_t *subject, std::int32_t *candidate,
              std::int32_t *intermediary, std::int32_t *sixth_role) {
  Check(def == definition && *actor == kActor && *subject == kHeir &&
            *recipient == *candidate && *intermediary == -1 &&
            *sixth_role == -1,
        "fixture redirect preserves actor and couple roles");
  bool known_candidate = false;
  for (const auto id : kCandidateIds) {
    known_candidate = known_candidate || *candidate == id;
  }
  Check(known_candidate, "fixture redirect has one of the five full IDs");
  *recipient = kRecipient;
}
void *Construct(void *context, void *def, std::int32_t actor,
                std::int32_t recipient, std::int32_t subject,
                std::int32_t candidate, std::int32_t intermediary, void *extra) {
  Check(extra == nullptr, "ordinary disposable context has no extra role");
  ++contexts;
  Put(context, 0, def);
  Put(context, 0x2D8, actor);
  Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, subject);
  Put(context, 0x2E4, candidate);
  Put(context, 0x2E8, intermediary);
  Put(context, 0x300, std::uint8_t{0});
  Put(context, 0x301, std::uint8_t{0});
  return context;
}
void Refresh(void *, bool full) {
  Check(full, "actual reader requests full fixture context refresh");
}
void Finalize(void *) {}
bool Validate(void *context, void *error) {
  Check(error == nullptr && Load<std::int32_t>(context, 0x2E0) == kHeir,
        "actual reader validates heir fixture context");
  return true;
}
// This is the fixture recipient-acceptance callback, not a candidate score.
std::int64_t *Acceptance(void *, std::int64_t *out) {
  *out = kAcceptance;
  return out;
}
std::uint8_t Answer(void *, std::uint8_t mode, std::uint8_t flag,
                    void *first, void *second) {
  Check(mode == 1 && flag == 1 && first == nullptr && second == nullptr,
        "actual reader uses recipient final-answer ABI");
  return 0;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  Check(block == static_cast<std::byte *>(definition) + 0x40 &&
            Load<void *>(static_cast<const std::byte *>(scope) - 8, 0) ==
                definition,
        "actual reader retains ten-resource fixture context");
  for (std::size_t index = 0; index < 10; ++index) {
    out[index] = index == 0 ? -20'000
                           : static_cast<std::int64_t>(index) * 10'000;
  }
}
bool Option(const void *context, std::uint32_t id) {
  Check(id == 1 || id == 2, "fixture option identity");
  return Load<std::uint8_t>(context, 0x300 + id - 1) != 0;
}
void SetOption(void *context, std::uint32_t id, bool selected) {
  Check(id == 2, "fixture matrilineal option identity");
  Put(context, 0x301, static_cast<std::uint8_t>(selected));
}
bool Allied(const void *, const void *) { return false; }
bool FertilityGate(void *) { return true; }
void Destroy(void *context) {
  ++destroys;
  Put(context, 0, static_cast<void *>(nullptr));
}
void Project(const void *context, void *output) {
  struct Header {
    void *data;
    std::int32_t capacity;
    std::int32_t count;
    void *owner;
  };
  struct Row {
    const void *first;
    const void *second;
    const void *subject;
    const void *candidate;
  };
  auto &header = *static_cast<Header *>(output);
  const void *candidate = nullptr;
  for (const auto *character : projection_characters) {
    if (Load<std::int32_t>(character, 0x18) ==
        Load<std::int32_t>(context, 0x2E4)) {
      candidate = character;
      break;
    }
  }
  Check(candidate != nullptr, "projection retains actual context candidate");
  const std::array<Row, 3> rows{{
      {projection_characters[0], projection_characters[3],
       projection_characters[1], candidate},
      {projection_characters[0], candidate, projection_characters[1], candidate},
      {projection_characters[1], projection_characters[3],
       projection_characters[1], candidate}}};
  std::memcpy(header.data, rows.data(), sizeof(rows));
  header.count = 3;
}

struct Fixture;
bool Memory(void *context, std::uintptr_t address, void *out,
            std::size_t size) noexcept;

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 16 * 0x10> slots{};
  std::array<std::byte, 0x30> house_store{};
  std::array<std::byte, 0x30> dynasty_store{};
  std::array<std::byte, 512 * 0x10> house_slots{};
  std::array<std::byte, 512 * 0x10> dynasty_slots{};
  std::array<std::array<std::byte, 0x30>, 6> houses{};
  std::array<std::array<std::byte, 0x18>, 6> dynasties{};
  std::array<std::array<std::byte, 0x1D8>, 8> characters{};
  std::array<std::array<std::byte, 0x30>, 8> families{};
  std::array<std::array<std::byte, 0x2E8>, 8> living{};
  std::array<std::byte, 0x1000> database{};
  std::array<std::byte, 0x2720> def{};
  void *state_ptr = state.data();
  void *jomini_ptr = jomini.data();
  void *store_ptr = store.data();
  void *house_store_ptr = house_store.data();
  void *dynasty_store_ptr = dynasty_store.data();
  void *house_fallback_ptr = nullptr;
  void *dynasty_fallback_ptr = nullptr;
  void *database_ptr = database.data();
  std::int32_t threshold_zero = 16;
  std::int32_t threshold_one = 16;
  std::uint32_t grand_id = 1;
  std::uint32_t matri_id = 2;
  std::int64_t floor_raw = 0;
  std::int32_t upper_raw = 45;
  bool deny_upper_read = false;
  bool deny_heir_override = false;
  bool deny_candidate_override = false;
  std::size_t floor_read_calls = 0;
  std::size_t upper_read_calls = 0;
  std::size_t heir_override_read_calls = 0;
  std::size_t candidate_override_read_calls = 0;
  FamilyBindings bindings{};

  explicit Fixture(const Scene &scene)
      : threshold_zero(scene.threshold_zero), threshold_one(scene.threshold_one),
        floor_raw(10'000), upper_raw(scene.upper),
        deny_upper_read(scene.deny_upper),
        deny_heir_override(scene.deny_heir_override),
        deny_candidate_override(scene.deny_candidate_override) {
    contexts = destroys = 0;
    Put(state.data(), 8, std::int32_t{53220000});
    Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data());
    jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local.data(), 0x70, std::int32_t{7});
    Put(game.data(), 0x222E8 + 0x58, entries.data());
    Put(game.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7});
    Put(entry.data(), 0xB0, kActor);
    Put(store.data(), 0x20, slots.data());
    Put(store.data(), 0x2C, std::int32_t{16});
    Put(house_store.data(), 0x20, house_slots.data());
    Put(house_store.data(), 0x2C, std::int32_t{512});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data());
    Put(dynasty_store.data(), 0x2C, std::int32_t{512});
    for (std::size_t index = 0; index < kHouseIds.size(); ++index) {
      Put(houses[index].data(), 0x10, kHouseIds[index]);
      Put(houses[index].data(), 0x2C, kDynastyIds[index]);
      Put(dynasties[index].data(), 0x10, kDynastyIds[index]);
      Put(house_slots.data(),
          static_cast<std::size_t>(kHouseIds[index]) * 0x10 + 8,
          houses[index].data());
      Put(dynasty_slots.data(),
          static_cast<std::size_t>(kDynastyIds[index]) * 0x10 + 8,
          dynasties[index].data());
    }
    const std::array<std::int32_t, 8> ids{
        kActor, kHeir, kCandidateIds[0], kRecipient, kCandidateIds[1],
        kCandidateIds[2], kCandidateIds[3], kCandidateIds[4]};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      auto *character = characters[index].data();
      Put(character, 0x18, ids[index]);
      Put(slots.data(),
          static_cast<std::size_t>(ids[index] & 0xFFFFFF) * 0x10 + 8,
          character);
      Put(character, 0x1A8, families[index].data());
      Put(character, 0x1A0, std::uint64_t{0});
      Put(families[index].data(), 0x10, std::int32_t{-1});
      Put(families[index].data(), 0x14, std::int32_t{-1});
      Put(character, 0x68, scene.measure);
      Put(character, 0x6C, scene.heir_override);
      Put(character, 0x158, kCharacterHouses[index]);
      Put(character, 0x1C0, std::uintptr_t{1});
      Put(character, 0x1D0, static_cast<void *>(nullptr));
      Put(character, 0x1B0, living[index].data());
      Put(living[index].data(), 0x2E0, kHeirFertility);
      projection_characters[index] = character;
    }
    Put(characters[1].data(), 0x1A1, scene.heir_selector);
    for (std::size_t index = 0; index < kCandidateSlots.size(); ++index) {
      const auto slot = kCandidateSlots[index];
      Put(characters[slot].data(), 0x1A1, scene.candidate_selector);
      Put(characters[slot].data(), 0x6C, scene.candidate_overrides[index]);
      Put(living[slot].data(), 0x2E0, std::int64_t{20'000});
    }
    Put(database.data(), 0xF30, def.data());
    definition = def.data();
    local_player = local.data();
    auto &context = bindings.context;
    bindings.enabled = context.enabled = true;
    context.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer};
    bindings.values.enabled = true;
    bindings.values.core = context.core;
    bindings.values.house_store = &house_store_ptr;
    bindings.values.house_fallback = &house_fallback_ptr;
    bindings.values.dynasty_store = &dynasty_store_ptr;
    bindings.values.dynasty_fallback = &dynasty_fallback_ptr;
    bindings.values.fertility_gate = &FertilityGate;
    bindings.values.candidate_fertility_floor = &floor_raw;
    bindings.values.candidate_scorer_age_upper =
        scene.bind_upper ? &upper_raw : nullptr;
    context.interaction_database_slot = &database_ptr;
    context.redirect_roles = &Redirect;
    context.construct_all_roles = &Construct;
    context.refresh = &Refresh;
    context.finalize = &Finalize;
    context.validate = &Validate;
    context.destroy = &Destroy;
    context.recipient_answer_score = &Acceptance;
    context.evaluate_cost = &Cost;
    // Command bindings and send callbacks deliberately remain unset.
    bindings.evaluate_answer = &Answer;
    bindings.read_boolean_option = &Option;
    bindings.set_boolean_option = &SetOption;
    bindings.adult_threshold_zero = &threshold_zero;
    bindings.adult_threshold_one = &threshold_one;
    bindings.grand_wedding_option = &grand_id;
    bindings.matrilineal_option = &matri_id;
  }

  FamilyProjectionBindings Projection() {
    FamilyProjectionBindings projection{};
    projection.exact_build_admitted = true;
    projection.admitted_executable_sha256 = xar::ck3_12004::kExecutableSha256;
    projection.offline_fixture = true;
    projection.memory_context = this;
    projection.read_memory = &Memory;
    projection.project_pairs = &Project;
    projection.read_boolean_option = &Option;
    projection.set_boolean_option = &SetOption;
    projection.is_allied = &Allied;
    projection.matrilineal_option_id_slot =
        reinterpret_cast<std::uintptr_t>(&matri_id);
    projection.native_owner_vtable = 1;
    return projection;
  }
};

bool Memory(void *context, std::uintptr_t address, void *out,
            std::size_t size) noexcept {
  if (context == nullptr || address == 0 || out == nullptr) return false;
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == reinterpret_cast<std::uintptr_t>(&fixture.floor_raw)) {
    ++fixture.floor_read_calls;
    if (size != sizeof(fixture.floor_raw)) return false;
  }
  if (address == reinterpret_cast<std::uintptr_t>(&fixture.upper_raw)) {
    ++fixture.upper_read_calls;
    if (fixture.deny_upper_read || size != sizeof(fixture.upper_raw)) return false;
  }
  if (address == reinterpret_cast<std::uintptr_t>(fixture.characters[1].data()) +
                     family_value::kCharacterScorerAgeOverrideOffset) {
    ++fixture.heir_override_read_calls;
    if (fixture.deny_heir_override || size != sizeof(std::int16_t)) return false;
  }
  for (const auto slot : kCandidateSlots) {
    if (address == reinterpret_cast<std::uintptr_t>(fixture.characters[slot].data()) +
                       family_value::kCharacterScorerAgeOverrideOffset) {
      ++fixture.candidate_override_read_calls;
      if (fixture.deny_candidate_override || size != sizeof(std::int16_t))
        return false;
      break;
    }
  }
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}

void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  Check(output.is_open(), "fixture output file opened");
  output << text << '\n';
  Check(output.good(), "fixture output file written");
}

void EmitCase(const std::filesystem::path &directory, const Scene &scene) {
  Fixture fixture(scene);
  const auto projection = fixture.Projection();
  Check(projection.admitted_executable_sha256 ==
            xar::ck3_12004::kExecutableSha256,
        "fixture projection retains actual4 SHA");
  const auto captured_floor = family_value::ReadCandidateFertilityFloorRawV1(
      fixture.bindings.values, projection);
  const auto captured_upper = family_value::ReadCandidateScorerAgeUpperRawV1(
      fixture.bindings.values, projection);
  const std::optional<std::int32_t> expected_upper =
      scene.bind_upper && !scene.deny_upper
          ? std::optional<std::int32_t>{scene.upper} : std::nullopt;
  const std::optional<std::int16_t> expected_heir_override =
      scene.deny_heir_override
          ? std::nullopt : std::optional<std::int16_t>{scene.heir_override};
  Check(captured_floor == 10'000 && captured_upper == expected_upper,
        "one floor and one optional signed loaded upper sample per frame");
  std::array<FamilyAllianceWireRowV1, 5> rows{};
  for (std::size_t index = 0; index < rows.size(); ++index) {
    auto &observed = rows[index].observed;
    observed.played_character_id = kActor;
    observed.subject_character_id = kHeir;
    observed.candidate_character_id = kCandidateIds[index];
    observed.recipient_matchmaker_character_id = kRecipient;
    observed.intermediary_character_id = -1;
    observed.recipient_ai_accept_raw = kAcceptance;
    observed.recipient_answer_status_raw = 0;
    observed.complete_can_send = true;
    observed.recipient_answer_allows_send = true;
    observed.heir_adult_measure_raw = scene.measure;
    observed.candidate_adult_measure_raw = scene.measure;
    observed.played_dynasty_id = 200;
    observed.heir_dynasty_id = 200;
    observed.candidate_dynasty_id = 400 + static_cast<std::int32_t>(index);
    observed.realm_backed_actor_recipient = true;
    // Real shared reader retains its historical DTO/layout namespace.
    rows[index].read = ReadMarriageCandidateAlliancePrivateV1(
        fixture.bindings, observed, projection, scene.request_matrilineal, true);
    auto &read = rows[index].read;
    read.native_candidate_fertility_floor_raw = captured_floor;
    read.native_candidate_scorer_age_upper_raw = captured_upper;
    const auto heir_threshold =
        scene.heir_selector == 0 ? scene.threshold_zero : scene.threshold_one;
    const auto candidate_threshold =
        scene.candidate_selector == 0 ? scene.threshold_zero : scene.threshold_one;
    Check(read.failure ==
              xar::ck3_11906::MarriageCandidateAlliancePrivateFailureV1::none &&
              read.projection_failure ==
                  xar::bridge::MarriageCandidateAllianceProjectionFailureV1::none &&
              read.final_legality_sampled && read.complete_can_send &&
              read.recipient_ai_accept_raw == observed.recipient_ai_accept_raw &&
              read.projection.pair_count == 3 &&
              read.heir_is_adult == (scene.measure >= heir_threshold) &&
              read.candidate_is_adult == (scene.measure >= candidate_threshold) &&
              read.heir_adult_measure_raw == scene.measure &&
              read.candidate_adult_measure_raw == scene.measure &&
              read.heir_adult_threshold_raw == heir_threshold &&
              read.candidate_adult_threshold_raw == candidate_threshold &&
              read.effective_matrilineal_if_accepted == scene.request_matrilineal &&
              read.requested_matrilineal_option == scene.request_matrilineal &&
              read.selected_option_readback == scene.request_matrilineal,
          "new optional reads preserve truthful full legacy rich row");
    Check(read.heir_fertility.available &&
              read.heir_fertility.native_gate_allows &&
              read.heir_fertility.effective_raw == kHeirFertility &&
              read.candidate_fertility.available &&
              read.candidate_fertility.native_gate_allows &&
              read.candidate_fertility.effective_raw == 20'000 &&
              read.native_candidate_fertility_floor_raw == 10'000,
          "actual fertility reader and copied floor remain available");
    const std::optional<std::int16_t> expected_candidate_override =
        scene.deny_candidate_override
            ? std::nullopt
            : std::optional<std::int16_t>{scene.candidate_overrides[index]};
    Check(read.heir_native_scorer_age_override_raw == expected_heir_override &&
              read.candidate_native_scorer_age_override_raw ==
                  expected_candidate_override &&
              read.native_candidate_scorer_age_upper_raw == expected_upper,
          "actual rich reader and wire retain signed overrides or independent null");
    Check(read.played_lineage.house_id == 100 &&
              read.played_lineage.dynasty_id == 200 &&
              read.heir_lineage.house_id == 100 &&
              read.heir_lineage.dynasty_id == 200 &&
              read.candidate_lineage.house_id ==
                  300 + static_cast<std::int32_t>(index) &&
              read.candidate_lineage.dynasty_id ==
                  400 + static_cast<std::int32_t>(index) &&
              read.heir_sex_selector_raw == scene.heir_selector &&
              read.candidate_sex_selector_raw == scene.candidate_selector,
          "actual reader resolves positive full-ID lineage and opposite selectors");
    Check(read.heir_relationship.betrothed_character_id == -1 &&
              read.heir_relationship.primary_spouse_character_id == -1 &&
              read.heir_relationship.spouse_character_ids.empty() &&
              read.candidate_relationship.betrothed_character_id == -1 &&
              read.candidate_relationship.primary_spouse_character_id == -1 &&
              read.candidate_relationship.spouse_character_ids.empty(),
          "all fixture relationships remain empty");
  }
  Check(fixture.floor_read_calls == 1 &&
            fixture.upper_read_calls == (scene.bind_upper ? 1U : 0U) &&
            fixture.heir_override_read_calls == 10 &&
            fixture.candidate_override_read_calls == 10 &&
            contexts == rows.size() && destroys == rows.size(),
        "one loaded upper capture and two real override reads per rich row");
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  Check(descriptor.game_version == "1.20.0.4" &&
            descriptor.executable_sha256 == xar::ck3_12004::kExecutableSha256,
        "actual4 envelope descriptor is independent of retained reader layout");
  auto frame = SerializeFamilyAllianceFrameV1(
      scene.name, 11, 7, rows, kFamilyAllianceProjectionWireStepV1);
  frame = xar::game::Render12004BuildIdentity(std::move(frame), descriptor);
  Write(directory / (std::string(scene.name) + ".json"), frame);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "supply exactly one output directory");
    constexpr std::uintptr_t image_base = 0x140000000;
    const auto actual = xar::ck3_12004::BindFamilyValuesImage(
        image_base, xar::ck3_12004::kExecutableSha256);
    Check(actual.enabled &&
              reinterpret_cast<std::uintptr_t>(actual.candidate_fertility_floor) ==
                  image_base + xar::ck3_12004::kFamilyCandidateFertilityFloorRva &&
              reinterpret_cast<std::uintptr_t>(actual.candidate_scorer_age_upper) ==
                  image_base + xar::ck3_12004::kFamilyCandidateScorerAgeUpperRva,
          "actual4 binder calculates loaded floor and signed upper addresses only");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    std::array<Scene, 10> scenes{{
        {"override"}, {"fallback"}, {"selector0"}, {"firstfail"},
        {"subjectadjust"}, {"uppermissing"}, {"upperreadfailure"},
        {"heirunread"}, {"candidateunread"}, {"subjectwrap"}}};
    scenes[0].candidate_overrides = {40, 45, 46, 0, 32767};
    scenes[1].heir_override = -1;
    scenes[1].candidate_overrides = {-1, -2, -32768, -1, -1};
    scenes[1].upper = 16;
    scenes[2].heir_selector = 1;
    scenes[2].candidate_selector = 0;
    scenes[2].deny_heir_override = true;
    scenes[2].deny_candidate_override = true;
    scenes[2].deny_upper = true;
    scenes[2].request_matrilineal = true;
    scenes[3].candidate_overrides = {46, 47, 48, 49, 50};
    scenes[3].deny_heir_override = true;
    scenes[4].heir_override = 10;
    scenes[4].candidate_overrides = {45, 44, 40, 16, 0};
    scenes[5].bind_upper = false;
    scenes[6].deny_upper = true;
    scenes[7].deny_heir_override = true;
    scenes[8].deny_candidate_override = true;
    scenes[9].heir_override = -1;
    scenes[9].measure = std::numeric_limits<std::int16_t>::min();
    scenes[9].threshold_zero = std::numeric_limits<std::int32_t>::max();
    for (const auto &scene : scenes) EmitCase(directory, scene);
    Write(directory / "metadata.json",
          "{\"schema\":\"ck3.first-heir-scorer-age.fixture.v1\","
          "\"cases\":10,\"actual_reader_calls\":50,"
          "\"rows_per_case\":5,\"upper_read_calls\":[1,1,1,1,1,0,1,1,1,1],"
          "\"native_candidate_score_calls\":0,\"action_calls\":0,"
          "\"live\":false}");
    std::cout << "PASS actual4 first-heir scorer age: ten five-row envelopes\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/ck3_12004_first_heir_reproductive_inputs.hpp"
#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t kActor = 0x03000001;
constexpr std::int32_t kHeir = 0x03000002;
constexpr std::int32_t kPartner = 0x03000003;
constexpr std::int32_t kRecipient = 0x03000004;
struct Scene {
  std::string_view name;
  std::int32_t count = 18;
  bool data_present = true;
  bool family_present = true;
  bool lineage_present = true;
  bool betrothed = true;
};
template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
template <typename T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(T));
  return value;
}
void Check(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
void *local_player = nullptr;
void *definition = nullptr;
void *active_context = nullptr;
std::size_t constructs = 0;
std::size_t destroys = 0;
void *LocalPlayer(void *) { return local_player; }
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient,
              std::int32_t *subject, std::int32_t *candidate,
              std::int32_t *intermediary, std::int32_t *sixth) {
  Check(def == definition && *actor == kActor && *subject == kHeir &&
            *candidate == kPartner && *recipient == kPartner &&
            *intermediary == -1 && *sixth == -1,
        "current pair keeps actual six-role context");
  *recipient = kRecipient;
}
void *Construct(void *context, void *def, std::int32_t actor,
                std::int32_t recipient, std::int32_t subject,
                std::int32_t candidate, std::int32_t intermediary,
                void *extra) {
  Check(extra == nullptr, "current context has no extra role");
  ++constructs;
  active_context = context;
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
void Refresh(void *context, bool full) {
  Check(context == active_context && full, "refresh owning context");
}
void Finalize(void *context) {
  Check(context == active_context, "finalize owning context");
  Put(context, 0x301, std::uint8_t{0});
}
bool Validate(void *context, void *error) {
  Check(context == active_context && error == nullptr,
        "sample final native current-pair legality");
  return true;
}
std::int64_t *Acceptance(void *context, std::int64_t *out) {
  Check(context == active_context, "answer uses same finalized context");
  *out = 1'600'000;
  return out;
}
std::uint8_t Answer(void *context, std::uint8_t mode, std::uint8_t flag,
                    void *first, void *second) {
  Check(context == active_context && mode == 1 && flag == 1 &&
            first == nullptr && second == nullptr,
        "final answer ABI unchanged");
  return 0;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  Check(block == static_cast<std::byte *>(definition) + 0x40 &&
            static_cast<const std::byte *>(scope) - 8 == active_context,
        "current ten-resource cost uses finalized context");
  for (std::size_t i = 0; i < 10; ++i) out[i] = 0;
}
bool Option(const void *context, std::uint32_t id) {
  Check(context == active_context && (id == 1 || id == 2),
        "option is sampled from owning current-pair context");
  return Load<std::uint8_t>(context, 0x300 + id - 1) != 0;
}
void Destroy(void *context) {
  Check(context == active_context, "destroy only owning current context");
  ++destroys;
  active_context = nullptr;
  Put(context, 0, static_cast<void *>(nullptr));
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> character_store{};
  std::array<std::byte, 16 * 0x10> character_slots{};
  std::array<std::array<std::byte, 0x1D8>, 8> characters{};
  std::array<std::array<std::byte, 0x50>, 8> families{};
  std::array<std::array<std::byte, 0x10>, 3> pregnancy_records{};
  std::array<void *, 2> first_pregnancy_records{};
  std::array<void *, 2> second_pregnancy_records{};
  std::array<std::uint32_t, 18> children{};
  std::array<std::byte, 0x1000> database{};
  std::array<std::byte, 0x2720> def{};
  std::array<std::byte, 0x30> house_store{}, dynasty_store{};
  std::array<std::byte, 512 * 0x10> house_slots{}, dynasty_slots{};
  std::array<std::array<std::byte, 0x30>, 2> houses{};
  std::array<std::array<std::byte, 0x18>, 2> dynasties{};
  void *state_ptr = state.data();
  void *jomini_ptr = jomini.data();
  void *character_store_ptr = character_store.data();
  void *database_ptr = database.data();
  void *house_store_ptr = house_store.data();
  void *dynasty_store_ptr = dynasty_store.data();
  void *house_fallback = nullptr;
  void *dynasty_fallback = nullptr;
  std::int32_t threshold_zero = 16, threshold_one = 16;
  std::uint32_t grand_id = 1, matri_id = 2;
  FamilyBindings family{};

  explicit Fixture(const Scene &scene) {
    constructs = destroys = 0;
    active_context = nullptr;
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
    Put(character_store.data(), 0x20, character_slots.data());
    Put(character_store.data(), 0x2C, std::int32_t{16});
    const std::array<std::int32_t, 8> ids{kActor, kHeir, kPartner, kRecipient,
        0x03000005, 0x03000006, 0x03000007, 0x03000008};
    for (std::size_t i = 0; i < ids.size(); ++i) {
      Put(characters[i].data(), 0x18, ids[i]);
      Put(characters[i].data(), 0x1C, std::uint32_t{0x43686172});
      Put(character_slots.data(), static_cast<std::size_t>(ids[i] & 0xFFFFFF) * 0x10 + 8,
          characters[i].data());
      Put(characters[i].data(), 0x1A8, families[i].data());
      Put(characters[i].data(), 0x1C0, std::uintptr_t{1});
      Put(characters[i].data(), 0x68, std::int16_t{20});
      Put(characters[i].data(), 0x158, std::int32_t{-1});
      Put(families[i].data(), 0x10, std::int32_t{-1});
      Put(families[i].data(), 0x14, std::int32_t{-1});
    }
    if (scene.betrothed) {
      Put(families[1].data(), 0x10, kPartner);
      Put(families[2].data(), 0x10, kHeir);
    }
    Put(characters[2].data(), 0x1A1, std::uint8_t{1});
    Put(characters[0].data(), 0x158, std::int32_t{300});
    Put(characters[1].data(), 0x158, std::int32_t{100});
    Put(characters[2].data(), 0x158, std::int32_t{300});
    for (std::size_t i = 4; i < characters.size(); ++i) {
      Put(families[i].data(), 0, static_cast<std::uint32_t>(kHeir));
      Put(families[i].data(), 4, static_cast<std::uint32_t>(kPartner));
      Put(characters[i].data(), 0x158, static_cast<std::int32_t>(i == 4 ? 100 : 300));
    }
    Put(characters[5].data(), 0x1D0, std::uintptr_t{1});
    Put(families[6].data(), 0, static_cast<std::uint32_t>(kActor));
    Put(families[6].data(), 4, static_cast<std::uint32_t>(kPartner));
    children.fill(0x03000005U);
    children[1] = 0x03000006U;
    children[2] = 0xFFFFFFFFU;
    children[3] = 0x07000005U;
    children[4] = 0x03000007U;
    children[17] = 0x03000008U;
    Put(families[1].data(), 0x38,
        scene.data_present ? children.data() : static_cast<std::uint32_t *>(nullptr));
    Put(families[1].data(), 0x44, scene.count);
    if (!scene.family_present)
      Put(characters[1].data(), 0x1A8, static_cast<void *>(nullptr));
    Put(house_store.data(), 0x20, house_slots.data());
    Put(house_store.data(), 0x2C, std::int32_t{512});
    Put(dynasty_store.data(), 0x20, dynasty_slots.data());
    Put(dynasty_store.data(), 0x2C, std::int32_t{512});
    const std::array<std::int32_t, 2> house_ids{100, 300};
    const std::array<std::int32_t, 2> dynasty_ids{200, 400};
    for (std::size_t i = 0; i < house_ids.size(); ++i) {
      Put(houses[i].data(), 0x10, house_ids[i]);
      Put(houses[i].data(), 0x2C, dynasty_ids[i]);
      Put(dynasties[i].data(), 0x10, dynasty_ids[i]);
      Put(house_slots.data(), static_cast<std::size_t>(house_ids[i]) * 0x10 + 8,
          houses[i].data());
      Put(dynasty_slots.data(), static_cast<std::size_t>(dynasty_ids[i]) * 0x10 + 8,
          dynasties[i].data());
    }
    if (!scene.lineage_present)
      Put(houses[0].data(), 0x10, std::int32_t{0x06000064});
    Put(database.data(), 0xF30, def.data());
    definition = def.data();
    local_player = local.data();
    auto &context = family.context;
    family.enabled = context.enabled = true;
    context.core = {true, &state_ptr, &jomini_ptr, &character_store_ptr, &LocalPlayer};
    family.values.enabled = true;
    family.values.core = context.core;
    family.values.house_store = &house_store_ptr;
    family.values.house_fallback = &house_fallback;
    family.values.dynasty_store = &dynasty_store_ptr;
    family.values.dynasty_fallback = &dynasty_fallback;
    context.interaction_database_slot = &database_ptr;
    context.redirect_roles = &Redirect;
    context.construct_all_roles = &Construct;
    context.refresh = &Refresh;
    context.finalize = &Finalize;
    context.validate = &Validate;
    context.destroy = &Destroy;
    context.recipient_answer_score = &Acceptance;
    context.evaluate_cost = &Cost;
    family.evaluate_answer = &Answer;
    family.read_boolean_option = &Option;
    family.adult_threshold_zero = &threshold_zero;
    family.adult_threshold_one = &threshold_one;
    family.grand_wedding_option = &grand_id;
    family.matrilineal_option = &matri_id;
    // No command constructor, owning queue or gameplay sender is installed.
  }
};
void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream stream(path, std::ios::binary | std::ios::trunc);
  Check(stream.is_open(), "new whole-wire output opened");
  stream << text << '\n';
  Check(stream.good(), "new whole-wire output written");
}
void Emit(const std::filesystem::path &directory, const Scene &scene) {
  Fixture fixture(scene);
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "production current relationship reader preserves bilateral whole pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  const auto &read = relation.betrothal_actionability;
  if (scene.betrothed && scene.family_present) {
    Check(read.unavailable_reason.empty() && read.complete_can_send &&
              read.outcome_available && read.lineality_available &&
              read.adult.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::marriage &&
              read.effective_matrilineal_if_accepted == false &&
              read.matrilineal_option_selected == false,
          "new observation retains legacy final actionability and actual option");
    Check(constructs == 1 && destroys == 1,
          "one finalized context is released once");
  } else {
    Check(read.unavailable_reason == "current_heir_has_no_betrothal" &&
              !read.matrilineal_option_selected.has_value() &&
              constructs == 0 && destroys == 0,
          "no current betrothal skips unused context and preview");
  }
  using Status = xar::ck3_11906::CurrentFirstHeirDescendantsStatusV1;
  const auto &desc = *relation.descendants;
  Check(desc.played_character_id == kActor && desc.heir_character_id == kHeir &&
            desc.date_raw == 53220000 && desc.played_lineage.available &&
            desc.played_lineage.dynasty_id_raw == 400,
        "descendants use the current actor/heir and separate played Dynasty");
  if (!scene.family_present) {
    Check(desc.status == Status::partial && desc.family_present == false &&
              !desc.native_child_count_raw.has_value() && !desc.roster_complete &&
              desc.rows.empty() && desc.unavailable_reason == "current_heir_family_absent",
          "absent Family is independent partial, not an observed empty roster");
  } else if (!scene.data_present && scene.count > 0) {
    Check(desc.status == Status::partial && desc.native_child_count_raw == 18 &&
              desc.data_pointer_present == false && !desc.roster_complete &&
              desc.rows.empty() && desc.unavailable_reason == "native_child_data_unavailable",
          "nonempty missing data remains partial without dropping occurrences");
  } else {
    Check(desc.status == Status::available && desc.roster_complete &&
              desc.native_child_count_raw == scene.count &&
              desc.rows.size() == static_cast<std::size_t>(scene.count),
          "whole production reader retains the signed count and complete occurrences");
    if (scene.count > 0) {
      for (std::size_t index = 0; index < fixture.children.size(); ++index) {
        Check(desc.rows[index].occurrence_index == index &&
                  desc.rows[index].raw_character_id == fixture.children[index],
              "raw occurrence order and duplicates survive beyond diagnostic16");
      }
      Check(desc.rows[0].generation_valid && desc.rows[0].alive == true &&
                desc.rows[0].child_of_heir == true &&
                desc.rows[1].generation_valid && desc.rows[1].alive == false &&
                desc.rows[1].child_of_heir == true &&
                desc.rows[1].lineage.available &&
                desc.rows[1].lineage.dynasty_id_raw == 400,
            "actual dead child keeps its independently observed lineage");
      Check(!desc.rows[2].generation_valid && !desc.rows[2].alive.has_value() &&
                !desc.rows[3].generation_valid && !desc.rows[3].child_of_heir.has_value() &&
                desc.rows[4].generation_valid && desc.rows[4].child_of_heir == false,
            "invalid and stale full IDs differ from a resolved foreign parent");
      Check(desc.rows[17].raw_character_id == 0x03000008U &&
                desc.rows[17].alive == true && desc.rows[17].child_of_heir == true &&
                desc.rows[17].lineage.available &&
                desc.rows[17].lineage.dynasty_id_raw == 400,
            "last actual child beyond16 establishes played-Dynasty evidence");
      Check(desc.heir_lineage.available == scene.lineage_present &&
                desc.rows[0].lineage.available == scene.lineage_present,
            "missing lineage does not alter raw-roster completeness");
      if (scene.lineage_present) {
        Check(desc.heir_lineage.dynasty_id_raw == 200 &&
                  desc.rows[0].lineage.dynasty_id_raw == 200,
              "heir Dynasty differs from played Dynasty without inference");
      }
    }
  }
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      scene.name, 7, kHeir, relation);
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), xar::game::Ck3_12004AdapterDescriptor());
  Write(directory / (std::string(scene.name) + ".json"), wire);
}

bool household_gate_allows = true;
bool HouseholdFertilityGate(void *) { return household_gate_allows; }

void EmitHousehold(const std::filesystem::path &directory,
                   std::string_view name) {
  Fixture fixture({"current-household", 0, true, true, true, false});
  std::array<std::byte, 0x2E8> heir_extension{}, partner_extension{};
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  const bool partnered = name != "unpartnered";
  if (partnered) {
    Put(fixture.families[1].data(), 0x14, kPartner);
    Put(fixture.families[2].data(), 0x14, kHeir);
    Put(fixture.families[1].data(), 0x20, heir_spouses.data());
    Put(fixture.families[2].data(), 0x20, partner_spouses.data());
    for (const auto index : {1U, 2U}) {
      Put(fixture.families[index].data(), 0x28, std::int32_t{1});
      Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
    }
  }
  Put(fixture.characters[1].data(), 0x68, std::int16_t{32});
  Put(fixture.characters[2].data(), 0x68, std::int16_t{29});
  Put(fixture.characters[1].data(), 0x1B0, heir_extension.data());
  Put(fixture.characters[2].data(), 0x1B0, partner_extension.data());
  Put(heir_extension.data(), 0x2E0, std::int64_t{80'000});
  const auto partner_raw = name == "signed-negative" ? std::int64_t{-2'500}
                                                     : std::int64_t{60'000};
  Put(partner_extension.data(), 0x2E0, partner_raw);
  household_gate_allows = name != "gate-zero";
  fixture.family.values.fertility_gate = name == "missing-gate"
      ? nullptr : &HouseholdFertilityGate;
  if (name == "extension-zero")
    Put(fixture.characters[2].data(), 0x1B0, static_cast<void *>(nullptr));
  if (name == "partner-value-unavailable")
    Put(fixture.characters[2].data(), 0x1A1, std::uint8_t{2});
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "new household keeps the actual reciprocal current relation");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  relation.reproductive_inputs = xar::ck3_12004::ReadCurrentFirstHeirReproductiveInputsV1(
      fixture.family, relation);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation);
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), xar::game::Ck3_12004AdapterDescriptor());
  // Preserve the first emitted production envelope before scene assertions.
  Write(directory / (std::string(name) + ".json"), wire);
  const auto &household = *relation.reproductive_inputs;
  Check(household.played_character_id == kActor && household.heir_character_id == kHeir &&
            household.date_raw == 53220000 && household.rows.size() == (partnered ? 2U : 1U),
        "only the current heir and distinct observed partner are captured");
  Check(household.rows[0].character_id == kHeir &&
            household.rows[0].roles == std::vector<std::string_view>{"heir"},
        "current household starts with the current heir");
  if (partnered)
    Check(household.rows[1].character_id == kPartner &&
              household.rows[1].roles == std::vector<std::string_view>{"primary_spouse", "spouse"},
          "primary and spouse-array membership are one observed receiver");
  if (name == "missing-gate") {
    Check(household.status == "partial" && !household.rows[0].available &&
              !household.rows[1].available && !household.rows[0].age_measure_raw.has_value(),
          "missing native gate remains unavailable rather than effective zero");
  } else {
    Check(household.rows[0].available && household.rows[0].age_measure_raw == 32 &&
              household.rows[0].sex_selector_raw == 0 &&
              household.rows[0].fertility.effective_raw == (household_gate_allows ? 80'000 : 0),
          "current heir preserves raw age and qualified effective input");
    if (name == "partner-value-unavailable") {
      Check(household.status == "partial" && !household.rows[1].available &&
                !household.rows[1].age_measure_raw.has_value(),
            "one unavailable partner does not erase the known heir input");
    } else {
      Check(household.status == "available", "all demanded current values are observed");
      if (partnered) {
        const auto &partner = household.rows[1];
        const bool extension_present = name != "extension-zero";
        Check(partner.available && partner.age_measure_raw == 29 && partner.sex_selector_raw == 1 &&
                  partner.fertility.extension_present == extension_present &&
                  partner.fertility.native_gate_evaluated == extension_present &&
                  partner.fertility.effective_raw ==
                      (extension_present && household_gate_allows ? partner_raw : 0),
              "known native zero and negative signed inputs remain distinct");
      }
    }
  }
  Check(relation.descendants->roster_complete && relation.descendants->native_child_count_raw == 0 &&
            relation.betrothal_actionability.unavailable_reason == "current_heir_has_no_betrothal" &&
            constructs == 0 && destroys == 0,
        "current child baseline and unused betrothal context are unchanged");
}

void EmitPregnancyHousehold(const std::filesystem::path &directory,
                           std::string_view name) {
  Fixture fixture({"current-pregnancy-household", 0, true, true, true, false});
  std::array<std::byte, 0x2E8> heir_extension{}, partner_extension{};
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  Put(fixture.characters[1].data(), 0x68, std::int16_t{32});
  Put(fixture.characters[2].data(), 0x68, std::int16_t{29});
  Put(fixture.characters[1].data(), 0x1B0, heir_extension.data());
  Put(fixture.characters[2].data(), 0x1B0, partner_extension.data());
  Put(heir_extension.data(), 0x2E0, std::int64_t{80'000});
  Put(partner_extension.data(), 0x2E0, std::int64_t{60'000});
  household_gate_allows = true;
  const bool fertility_missing = name == "fertility-unavailable-pregnant";
  fixture.family.values.fertility_gate = fertility_missing
      ? nullptr : &HouseholdFertilityGate;

  // Actual full mother IDs in real pointer arrays; the first decoy has the
  // partner's index but a different generation and must not match either row.
  Put(fixture.pregnancy_records[0].data(), 8, std::int32_t{0x07000003});
  Put(fixture.pregnancy_records[1].data(), 8, kPartner);
  Put(fixture.pregnancy_records[2].data(), 8, kRecipient);
  fixture.first_pregnancy_records = {
      fixture.pregnancy_records[0].data(), fixture.pregnancy_records[2].data()};
  fixture.second_pregnancy_records = {
      fixture.pregnancy_records[0].data(), fixture.pregnancy_records[2].data()};
  if (name == "pregnant-first-array" || fertility_missing)
    fixture.first_pregnancy_records[1] = fixture.pregnancy_records[1].data();
  if (name == "pregnant-second-array")
    fixture.second_pregnancy_records[1] = fixture.pregnancy_records[1].data();
  auto *manager = fixture.game.data() + 0x2EE40;
  const bool pregnancy_missing = name == "pregnancy-unavailable";
  Put(manager, 0x4EA0, pregnancy_missing
      ? static_cast<void **>(nullptr) : fixture.first_pregnancy_records.data());
  Put(manager, 0x4EAC, std::int32_t{pregnancy_missing ? 1 : 2});
  Put(manager, 0x4E88, fixture.second_pregnancy_records.data());
  Put(manager, 0x4E94, std::int32_t{2});

  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "pregnancy scene keeps the same reciprocal current married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  relation.reproductive_inputs = xar::ck3_12004::ReadCurrentFirstHeirReproductiveInputsV1(
      fixture.family, relation);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation);
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), descriptor);
  Write(directory / (std::string(name) + ".json"), wire);
  Check(xar::game::IsCk3_12004Descriptor(descriptor) &&
            wire.find("\"native_pregnancy\":{\"source\":\"native_is_pregnant\"") != std::string::npos,
        "whole wire uses canonical actual4 descriptor and native pregnancy source");
  const auto &household = *relation.reproductive_inputs;
  Check(household.played_character_id == kActor && household.heir_character_id == kHeir &&
            household.date_raw == 53220000 && household.rows.size() == 2 &&
            household.rows[0].character_id == kHeir &&
            household.rows[1].character_id == kPartner &&
            household.rows[0].roles == std::vector<std::string_view>{"heir"} &&
            household.rows[1].roles == std::vector<std::string_view>{"primary_spouse", "spouse"},
        "pregnancy observations retain actual deduplicated household receivers");
  for (const auto &row : household.rows) {
    if (pregnancy_missing) {
      Check(row.native_pregnancy.status == "unavailable" &&
                !row.native_pregnancy.unavailable_reason.empty() &&
                !row.native_pregnancy.is_pregnant.has_value(),
            "nonempty pregnancy array without data is unavailable, not false");
    } else {
      const bool expected = row.character_id == kPartner && name != "not-pregnant";
      Check(row.native_pregnancy.status == "available" &&
                row.native_pregnancy.unavailable_reason.empty() &&
                row.native_pregnancy.is_pregnant == expected,
            "both native arrays compare exact full mother IDs independently of fertility");
    }
    if (fertility_missing) {
      Check(!row.available && !row.fertility.available &&
                !row.age_measure_raw.has_value() && !row.unavailable_reason.empty(),
            "missing fertility gate retains pregnancy but not guessed fertility values");
    } else {
      const bool heir_row = row.character_id == kHeir;
      Check(row.available && row.fertility.available &&
                row.age_measure_raw == (heir_row ? 32 : 29) &&
                row.sex_selector_raw == (heir_row ? 0 : 1) &&
                row.fertility.effective_raw == (heir_row ? 80'000 : 60'000),
            "unavailable pregnancy does not erase qualified age or fertility inputs");
    }
  }
  Check(household.status == (fertility_missing ? "partial" : "available") &&
            relation.descendants->roster_complete && relation.descendants->native_child_count_raw == 0 &&
            relation.betrothal_actionability.unavailable_reason == "current_heir_has_no_betrothal" &&
            constructs == 0 && destroys == 0,
        "pregnancy adds independent evidence without changing fertility status or sending actions");
}
} // namespace
int main(int argc, char **argv) {
  try {
    if (argc == 3 && std::string_view(argv[1]) == "--pregnancy-observer-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"pregnant-first-array", "pregnant-second-array",
               "not-pregnant", "pregnancy-unavailable", "fertility-unavailable-pregnant"})
        EmitPregnancyHousehold(directory, name);
      std::cout << "PASS actual4 current household pregnancy: five new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--reproductive-inputs-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"married-pair", "gate-zero", "extension-zero",
               "signed-negative", "missing-gate", "partner-value-unavailable", "unpartnered"})
        EmitHousehold(directory, name);
      std::cout << "PASS actual4 current household: seven new whole wires\n";
      return 0;
    }
    Check(argc == 2, "supply exactly one new whole-wire directory");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    const std::array<Scene, 6> scenes{{
        {"complete-roster"},
        {"known-empty", 0},
        {"data-missing", 18, false},
        {"family-missing", 18, true, false},
        {"lineage-missing", 18, true, true, false},
        {"no-betrothal", 18, true, true, true, false}}};
    for (const auto &scene : scenes) Emit(directory, scene);
    std::cout << "PASS actual4 current first-heir descendants: six new whole wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

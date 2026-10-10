#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/ck3_12004_first_heir_conception_trait_inputs.hpp"
#include "xar_bridge/ck3_12004_first_heir_child_inputs.hpp"
#include "xar_bridge/ck3_12004_event_window_context.hpp"
#include "xar_bridge/current_first_heir_child_inputs_json_v1.hpp"
#include "xar_bridge/ck3_12004_first_heir_reproductive_inputs.hpp"
#include "xar_bridge/current_first_heir_relationship_v1.hpp"
#include "xar_bridge/current_first_heir_character_window_identity_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>

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
void *fixture_interaction_definition = nullptr;
void *active_context = nullptr;
std::size_t constructs = 0;
std::size_t destroys = 0;
void *LocalPlayer(void *) { return local_player; }
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient,
              std::int32_t *subject, std::int32_t *candidate,
              std::int32_t *intermediary, std::int32_t *sixth) {
  Check(def == fixture_interaction_definition && *actor == kActor && *subject == kHeir &&
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
  Check(block == static_cast<std::byte *>(fixture_interaction_definition) + 0x40 &&
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
    fixture_interaction_definition = def.data();
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

struct ConceptionTraitFixture70 {
  std::array<std::byte, 0x60> database{};
  std::array<std::array<std::byte, 0x4A8>, 2> definitions{};
  std::array<std::byte, 0x4A8> invalid_definition{};
  std::array<const void *, 2> ordered_definitions{
      definitions[0].data(), definitions[1].data()};
  const void *database_ptr{database.data()};
  const void *invalid_definition_ptr{invalid_definition.data()};
  std::array<std::int32_t, 3> heir_trait_ids{0, 1, -1};
  std::array<std::int32_t, 1> partner_trait_ids{1};
  std::array<std::byte, 0x2E8> heir_extension{}, partner_extension{};
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};

  ConceptionTraitFixture70(Fixture &fixture, std::string_view name) {
    Put(database.data(), 0x50, ordered_definitions.data());
    Put(database.data(), 0x5C, std::int32_t{2});
    Put(definitions[0].data(), 0x4A4, std::uint32_t{0x1});
    Put(definitions[1].data(), 0x4A4, std::uint32_t{0x10});
    Put(invalid_definition.data(), 0x4A4, std::uint32_t{0x8});
    if (name == "heir-blocked" || name == "fertility-unavailable-trait-blocked")
      Put(definitions[0].data(), 0x4A4, std::uint32_t{0x8});
    if (name == "spouse-blocked")
      Put(definitions[1].data(), 0x4A4, std::uint32_t{0x8});
    const bool empty = name == "no-traits";
    const bool multiple = name == "multiple-traits-fallback-blocked";
    const bool database_missing = name == "trait-db-unavailable";
    if (database_missing) database_ptr = nullptr;
    if (multiple) partner_trait_ids[0] = 0;
    Put(fixture.characters[1].data(), 0xF8,
        empty ? static_cast<std::int32_t *>(nullptr) : heir_trait_ids.data());
    Put(fixture.characters[1].data(), 0x104, std::int32_t{empty ? 0 : multiple ? 3 : 1});
    Put(fixture.characters[2].data(), 0xF8,
        empty || database_missing
            ? static_cast<std::int32_t *>(nullptr) : partner_trait_ids.data());
    Put(fixture.characters[2].data(), 0x104,
        std::int32_t{empty || database_missing ? 0 : 1});

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
    fixture.family.values.fertility_gate = name == "fertility-unavailable-trait-blocked"
        ? nullptr : &HouseholdFertilityGate;
    auto *manager = fixture.game.data() + 0x2EE40;
    Put(manager, 0x4EA0, static_cast<void **>(nullptr));
    Put(manager, 0x4EAC, std::int32_t{0});
    Put(manager, 0x4E88, static_cast<void **>(nullptr));
    Put(manager, 0x4E94, std::int32_t{0});
  }
};

void EmitConceptionTraitExclusion70(const std::filesystem::path &directory,
                                   std::string_view name) {
  Fixture fixture({"current-conception-trait-household", 0, true, true, true, false});
  ConceptionTraitFixture70 traits(fixture, name);
  xar::ck3_12004::NativeConceptionTraitBindingsV1 trait_bindings{
      true, &traits.database_ptr, &traits.invalid_definition_ptr};
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "conception trait scene retains the same reciprocal current married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  relation.reproductive_inputs = xar::ck3_12004::ReadCurrentFirstHeirReproductiveInputsV1(
      fixture.family, relation);
  const auto sidecar = xar::ck3_12004::ReadCurrentFirstHeirConceptionTraitInputsV1(
      fixture.family, trait_bindings, relation);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, nullptr, &sidecar);
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  wire = xar::game::Render12004BuildIdentity(std::move(wire), descriptor);
  Write(directory / (std::string(name) + ".json"), wire);

  constexpr std::string_view leaf_source =
      "\"native_conception_trait_exclusion\":{\"source\":\"native_conception_trait_exclusion\"";
  const auto first_leaf = wire.find(leaf_source);
  Check(xar::game::IsCk3_12004Descriptor(descriptor) &&
            first_leaf != std::string::npos &&
            wire.find(leaf_source, first_leaf + leaf_source.size()) != std::string::npos,
        "whole canonical actual4 wire serializes the real conception trait sidecar for both rows");
  const auto &household = *relation.reproductive_inputs;
  const bool fertility_missing = name == "fertility-unavailable-trait-blocked";
  const bool database_missing = name == "trait-db-unavailable";
  Check(household.played_character_id == kActor && household.heir_character_id == kHeir &&
            household.date_raw == 53220000 && household.rows.size() == 2 &&
            household.rows[0].character_id == kHeir &&
            household.rows[1].character_id == kPartner &&
            household.rows[0].roles == std::vector<std::string_view>{"heir"} &&
            household.rows[1].roles == std::vector<std::string_view>{"primary_spouse", "spouse"} &&
            sidecar.rows.size() == 2 && sidecar.rows[0].character_id == kHeir &&
            sidecar.rows[1].character_id == kPartner,
        "query-local sidecar follows the actual deduplicated married household receivers");
  for (std::size_t index = 0; index < household.rows.size(); ++index) {
    const auto &row = household.rows[index];
    const auto &trait_read = sidecar.rows[index].read;
    const bool heir_row = index == 0;
    if (database_missing && heir_row) {
      Check(trait_read.status == "unavailable" &&
                trait_read.unavailable_reason == "native_conception_trait_database_unavailable" &&
                !trait_read.blocks_pair_conception.has_value(),
            "a nonempty trait list with an unavailable database is unknown rather than false");
    } else {
      const bool expected = heir_row
          ? name == "heir-blocked" || name == "multiple-traits-fallback-blocked" ||
                fertility_missing
          : name == "spouse-blocked";
      Check(trait_read.status == "available" && trait_read.unavailable_reason.empty() &&
                trait_read.blocks_pair_conception == expected,
            "actual definition bit3 and signed empty-list semantics produce the expected independent bool");
    }
    Check(row.native_pregnancy.status == "available" &&
              row.native_pregnancy.unavailable_reason.empty() &&
              row.native_pregnancy.is_pregnant == false,
          "legal empty active-pregnancy arrays remain independently known false");
    if (fertility_missing) {
      Check(!row.available && !row.fertility.available &&
                !row.age_measure_raw.has_value() && !row.unavailable_reason.empty(),
            "unavailable fertility leaves the conception trait result independently available");
    } else {
      Check(row.available && row.fertility.available &&
                row.age_measure_raw == (heir_row ? 32 : 29) &&
                row.sex_selector_raw == (heir_row ? 0 : 1) &&
                row.fertility.effective_raw == (heir_row ? 80'000 : 60'000),
            "conception trait failures do not erase qualified age or fertility inputs");
    }
  }
  if (name == "multiple-traits-fallback-blocked") {
    Check(Load<std::int32_t>(fixture.characters[1].data(), 0x104) == 3 &&
              traits.heir_trait_ids == std::array<std::int32_t, 3>{0, 1, -1} &&
              Load<std::uint32_t>(traits.definitions[0].data(), 0x4A4) == 0x1U &&
              Load<std::uint32_t>(traits.definitions[1].data(), 0x4A4) == 0x10U &&
              Load<std::uint32_t>(traits.invalid_definition.data(), 0x4A4) == 0x8U &&
              sidecar.rows[0].read.blocks_pair_conception == true &&
              sidecar.rows[1].read.blocks_pair_conception == false,
          "the third invalid trait ID reaches its owned nonnull fallback after two nonblocking definitions");
  }
  if (name == "no-traits" || database_missing) {
    Check(Load<std::int32_t>(fixture.characters[2].data(), 0x104) == 0 &&
              Load<const std::int32_t *>(fixture.characters[2].data(), 0xF8) == nullptr &&
              sidecar.rows[1].read.blocks_pair_conception == false,
          "a legal zero trait count returns a known false without requiring the trait database");
  }
  Check(household.status == (fertility_missing ? "partial" : "available") &&
            relation.descendants->roster_complete && relation.descendants->native_child_count_raw == 0 &&
            relation.betrothal_actionability.unavailable_reason == "current_heir_has_no_betrothal" &&
            constructs == 0 && destroys == 0,
        "six conception trait scenes add only read-only observations to the existing childless pair");
}

struct ChildTraitFixture35 {
  std::array<std::byte, 0x60> database{};
  std::array<std::array<std::byte, 0x38>, 5> definitions{};
  std::array<const void *, 5> ordered_definitions{};
  std::array<void *, 2> child_characters{};
  std::array<std::array<bool, 5>, 2> present{};
  std::size_t has_trait_calls = 0;

  void SetKey(std::size_t index, std::string_view key) {
    Check(index < definitions.size() && !key.empty() && key.size() < 16,
          "fixture owns a valid native SSO Trait key");
    auto &definition_bytes = definitions[index];
    definition_bytes.fill(std::byte{});
    std::memcpy(definition_bytes.data() + 0x18, key.data(), key.size());
    Put(definition_bytes.data(), 0x28, static_cast<std::uint64_t>(key.size()));
    Put(definition_bytes.data(), 0x30, std::uint64_t{15});
  }

  explicit ChildTraitFixture35(Fixture &fixture) {
    child_characters = {fixture.characters[4].data(), fixture.characters[7].data()};
    const std::array<std::size_t, 5> order{3, 0, 4, 2, 1};
    for (std::size_t index = 0; index < definitions.size(); ++index) {
      SetKey(index, xar::ck3_11906::kChildhoodTraitKeysV1[index]);
      ordered_definitions[index] = definitions[order[index]].data();
    }
    Put(database.data(), 0x50, ordered_definitions.data());
    Put(database.data(), 0x5C, std::int32_t{5});
  }
};

ChildTraitFixture35 *active_child_traits35 = nullptr;
void *ChildTraitDatabase35() {
  return active_child_traits35 == nullptr ? nullptr : active_child_traits35->database.data();
}
bool ChildHasTrait35(void *character, const void *trait) {
  Check(active_child_traits35 != nullptr, "child Trait callbacks have an owning fixture");
  auto &source = *active_child_traits35;
  std::size_t child_index = source.child_characters.size();
  std::size_t trait_index = source.definitions.size();
  for (std::size_t index = 0; index < source.child_characters.size(); ++index)
    if (character == source.child_characters[index]) child_index = index;
  for (std::size_t index = 0; index < source.definitions.size(); ++index)
    if (trait == source.definitions[index].data()) trait_index = index;
  Check(child_index < source.child_characters.size() &&
            trait_index < source.definitions.size(),
        "generic HasTrait receives the exact child and decoded native definition");
  ++source.has_trait_calls;
  return source.present[child_index][trait_index];
}

void EmitChildObservers35(const std::filesystem::path &directory,
                          std::string_view name) {
  const bool empty = name == "empty-children";
  const bool affinity = name == "childhood-affinity";
  const bool values_missing = name == "child-values-unavailable";
  const bool traits_missing = name == "child-traits-unavailable";
  Fixture fixture({"current-child-inputs", empty ? 0 : affinity ? 18 : 1,
                   true, true, true, false});
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  Put(fixture.characters[4].data(), 0x68, static_cast<std::int16_t>(affinity ? 7 : 0));
  Put(fixture.characters[4].data(), 0x1A1, static_cast<std::uint8_t>(values_missing ? 2 : 0));
  Put(fixture.characters[7].data(), 0x68, std::int16_t{9});
  Put(fixture.characters[7].data(), 0x1A1, std::uint8_t{1});

  ChildTraitFixture35 traits(fixture);
  if (affinity) {
    traits.present[0] = {true, false, false, true, false};
    traits.present[1] = {false, true, true, false, true};
  } else if (values_missing) {
    traits.present[0][0] = true;
  }
  if (traits_missing) traits.SetKey(4, "other");
  active_child_traits35 = &traits;
  xar::ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 trait_environment{};
  trait_environment.trait_database = &ChildTraitDatabase35;
  trait_environment.character_has_trait = &ChildHasTrait35;

  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "child inputs keep the same reciprocal current married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  auto &desc = *relation.descendants;
  const auto child_inputs = xar::ck3_12004::ReadCurrentFirstHeirChildInputsV1(
      fixture.family, trait_environment, desc);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, &child_inputs);
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  wire = xar::game::Render12004BuildIdentity(std::move(wire), descriptor);
  Write(directory / (std::string(name) + ".json"), wire);
  Check(xar::game::IsCk3_12004Descriptor(descriptor) &&
            wire.find("\"child_inputs\":{") != std::string::npos,
        "genuine whole relationship wire uses canonical actual4 descriptor and child leaf");

  const auto &inputs = child_inputs;
  Check(desc.roster_complete && desc.native_child_count_raw == (empty ? 0 : affinity ? 18 : 1) &&
            inputs.played_character_id == kActor && inputs.heir_character_id == kHeir &&
            inputs.date_raw == 53220000 &&
            inputs.rows.size() == (empty ? 0U : affinity ? 2U : 1U),
        "child inputs retain owner metadata and distinct actual living children");
  Check(inputs.status == (values_missing || traits_missing ? "partial" : "available") &&
            (inputs.unavailable_reason.empty() == !(values_missing || traits_missing)),
        "independent missing child values or traits retain partial observation");
  if (empty) {
    Check(inputs.rows.empty() && traits.has_trait_calls == 0,
          "known zero children is a complete empty input without trait receivers");
  } else {
    const auto &first = inputs.rows[0];
    const std::vector<std::uint32_t> first_indices = affinity
        ? std::vector<std::uint32_t>{0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
        : std::vector<std::uint32_t>{0};
    Check(first.character_id == 0x03000005 && first.occurrence_indices == first_indices,
          "first child groups only its eligible original occurrences");
    if (values_missing) {
      Check(!first.values.available && !first.values.age_measure_raw.has_value() &&
                !first.values.sex_selector_raw.has_value() &&
                first.values.unavailable_reason == "character_sex_selector_unavailable",
            "invalid selector leaves both child values unavailable rather than default zero");
    } else {
      Check(first.values.available && first.values.unavailable_reason.empty() &&
                first.values.age_measure_raw == (affinity ? 7 : 0) &&
                first.values.sex_selector_raw == 0,
            "live child generic values preserve zero age without a fertility callback");
    }
    if (traits_missing) {
      Check(!first.childhood_traits.available &&
                !first.childhood_traits.unavailable_reason.empty() &&
                !first.childhood_traits.present_trait_keys.has_value(),
            "genuine missing required Trait definition is unavailable rather than an empty subset");
    } else {
      const auto expected = affinity ? std::vector<std::string_view>{"curious", "pensive"}
          : values_missing ? std::vector<std::string_view>{"curious"}
                           : std::vector<std::string_view>{};
      Check(first.childhood_traits.available && first.childhood_traits.unavailable_reason.empty() &&
                first.childhood_traits.present_trait_keys.has_value() &&
                *first.childhood_traits.present_trait_keys == expected,
            "native definition scan and exact child HasTrait preserve the observed ordered subset");
    }
    if (affinity) {
      const auto &second = inputs.rows[1];
      Check(second.character_id == 0x03000008 &&
                second.occurrence_indices == std::vector<std::uint32_t>{17} &&
                second.values.available && second.values.age_measure_raw == 9 &&
                second.values.sex_selector_raw == 1 && second.childhood_traits.available &&
                second.childhood_traits.present_trait_keys.has_value() &&
                *second.childhood_traits.present_trait_keys ==
                    std::vector<std::string_view>{"rowdy", "bossy", "charming"},
            "last living actual child survives duplicate dead stale and nonchild roster entries");
      Check(desc.rows.size() == 18 && desc.rows[1].alive == false &&
                !desc.rows[2].generation_valid && !desc.rows[3].generation_valid &&
                desc.rows[4].child_of_heir == false,
            "raw descendant evidence remains complete independently of eligible child inputs");
    }
  }
  Check(relation.relationship.betrothed_character_id == -1 &&
            relation.relationship.primary_spouse_character_id == kPartner &&
            relation.relationship.spouse_character_ids == std::vector<std::int32_t>{kPartner} &&
            relation.betrothal_actionability.unavailable_reason == "current_heir_has_no_betrothal" &&
            constructs == 0 && destroys == 0,
        "five child scenes keep identical current marriage and send no action");
  active_child_traits35 = nullptr;
}

struct ChildFocusFixture39 {
  std::array<std::array<std::byte, 0x288>, 2> extensions{};
  std::array<std::array<std::byte, 0x10>, 2> holders{};
  std::array<std::array<std::byte, 0x38>, 2> definitions{};
  std::array<std::array<char, 32>, 2> key_storage{};
  std::array<void *, 2> child_characters{};
  std::array<std::byte, 8> absent_object{};
  void *fallback = absent_object.data();
  std::size_t getter_calls = 0;

  explicit ChildFocusFixture39(Fixture &fixture) {
    child_characters = {fixture.characters[4].data(), fixture.characters[7].data()};
    const std::array<std::string_view, 2> keys{
        "education_diplomacy", "education_learning"};
    for (std::size_t index = 0; index < keys.size(); ++index) {
      std::memcpy(key_storage[index].data(), keys[index].data(), keys[index].size());
      Put(definitions[index].data(), 0x18, key_storage[index].data());
      Put(definitions[index].data(), 0x28, static_cast<std::uint64_t>(keys[index].size()));
      Put(definitions[index].data(), 0x30, std::uint64_t{31});
      Put(child_characters[index], 0x1B0, extensions[index].data());
      Put(extensions[index].data(), 0x280, holders[index].data());
      Put(holders[index].data(), 0x8, definitions[index].data());
    }
  }
};

ChildFocusFixture39 *active_child_focus39 = nullptr;
void *ChildCurrentFocus39(void *character) {
  Check(active_child_focus39 != nullptr, "focus getter has an owning native fixture");
  auto &source = *active_child_focus39;
  Check(std::find(source.child_characters.begin(), source.child_characters.end(), character)
            != source.child_characters.end(),
        "focus getter receives the actual descendant child, never the played actor");
  ++source.getter_calls;
  const auto extension = Load<void *>(character, 0x1B0);
  if (extension == nullptr) return source.fallback;
  const auto holder = Load<void *>(extension, 0x280);
  if (holder == nullptr) return source.fallback;
  return Load<void *>(holder, 0x8);
}

void EmitChildFocusObservers39(const std::filesystem::path &directory,
                               std::string_view name) {
  const bool empty = name == "empty-children-focus";
  const bool distinct = name == "distinct-child-focus-keys";
  const bool absent = name == "child-focus-sentinel-absent";
  const bool null_focus = name == "child-focus-null-unavailable";
  const bool bad_key = name == "child-focus-key-unavailable";
  const bool bad_values = name == "child-focus-independent-of-values";
  Fixture fixture({"current-child-focus", empty ? 0 : distinct ? 18 : 1,
                   true, true, true, false});
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  Put(fixture.characters[4].data(), 0x68, std::int16_t{7});
  Put(fixture.characters[4].data(), 0x1A1, static_cast<std::uint8_t>(bad_values ? 2 : 0));
  Put(fixture.characters[7].data(), 0x68, std::int16_t{9});
  Put(fixture.characters[7].data(), 0x1A1, std::uint8_t{1});
  ChildTraitFixture35 traits(fixture);
  ChildFocusFixture39 focus(fixture);
  if (absent) Put(fixture.characters[4].data(), 0x1B0, static_cast<void *>(nullptr));
  if (null_focus) Put(focus.holders[0].data(), 0x8, static_cast<void *>(nullptr));
  if (bad_key) Put(focus.definitions[0].data(), 0x28, std::uint64_t{128});
  active_child_traits35 = &traits;
  active_child_focus39 = &focus;
  xar::ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 environment{};
  environment.trait_database = &ChildTraitDatabase35;
  environment.character_has_trait = &ChildHasTrait35;
  environment.current_focus = &ChildCurrentFocus39;
  environment.focus_fallback_slot_address = reinterpret_cast<std::uintptr_t>(&focus.fallback);
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "focus observers retain the same reciprocal current married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  const auto inputs = xar::ck3_12004::ReadCurrentFirstHeirChildInputsV1(
      fixture.family, environment, *relation.descendants);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, &inputs);
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  wire = xar::game::Render12004BuildIdentity(std::move(wire), descriptor);
  Write(directory / (std::string(name) + ".json"), wire);
  Check(xar::game::IsCk3_12004Descriptor(descriptor) &&
            inputs.rows.size() == (empty ? 0U : distinct ? 2U : 1U) &&
            inputs.status == (bad_values ? "partial" : "available") &&
            relation.descendants->native_child_count_raw == (empty ? 0 : distinct ? 18 : 1),
        "canonical whole child focus wire retains independent original aggregation and raw roster");
  if (empty) {
    Check(focus.getter_calls == 0 && traits.has_trait_calls == 0,
          "empty current-child roster invokes no focus or trait callback");
  } else {
    const auto &row = inputs.rows[0];
    Check(row.character_id == 0x03000005 && row.native_focus.has_value(),
          "native focus belongs to the exact resolved actual child row");
    const auto &observed = *row.native_focus;
    if (null_focus || bad_key) {
      Check(!observed.available && observed.presence.empty() && !observed.key &&
                observed.unavailable_reason == (null_focus
                    ? "child_current_focus_getter_failed" : "child_current_focus_key_read_failed") &&
                row.values.available && row.childhood_traits.available,
            "null native return and real key read failure preserve usable age and traits");
    } else {
      Check(observed.available && observed.unavailable_reason.empty() &&
                observed.presence == (absent ? "absent" : "present") &&
                (absent ? !observed.key : observed.key == "education_diplomacy"),
            "native focus sentinel absence is distinct from a readable exact education key");
    }
    if (bad_values) Check(!row.values.available && observed.available &&
                            row.childhood_traits.available,
                        "focus stays readable when the existing sex selector fails");
    if (distinct) {
      const auto &other = inputs.rows[1];
      Check(other.character_id == 0x03000008 && other.native_focus &&
                other.native_focus->available && other.native_focus->key == "education_learning" &&
                other.occurrence_indices == std::vector<std::uint32_t>{17} &&
                row.occurrence_indices.size() == 13 && relation.descendants->rows.size() == 18,
            "distinct child focus keys retain duplicate grouping and all raw roster evidence");
    }
    Check(wire.find("\"source\":\"native_character_current_focus\"") != std::string::npos,
          "new child focus came through the complete production serializer");
  }
  Check(relation.relationship.primary_spouse_character_id == kPartner &&
            relation.relationship.spouse_character_ids == std::vector<std::int32_t>{kPartner} &&
            constructs == 0 && destroys == 0,
        "read-only focus qualification dispatches no game action");
  active_child_focus39 = nullptr;
  active_child_traits35 = nullptr;
}

struct ChildEducationPointTraitFixture40 {
  static constexpr std::size_t kChildhoodCount =
      xar::ck3_11906::kChildhoodTraitKeysV1.size();
  static constexpr std::size_t kEducationCount =
      xar::ck3_11906::kChildEducationPointTraitKeysV1.size();
  static constexpr std::size_t kTraitCount = kChildhoodCount + kEducationCount;
  std::array<std::byte, 0x60> database{};
  std::array<std::array<std::byte, 0x38>, kTraitCount> definitions{};
  std::array<std::array<char, 32>, kTraitCount> key_storage{};
  std::array<const void *, kTraitCount> ordered_definitions{};
  std::array<void *, 2> child_characters{};
  std::array<std::array<bool, kTraitCount>, 2> present{};
  std::array<std::size_t, 2> education_sample_calls{};
  bool change_second_sample = false;

  void SetKey(std::size_t index, std::string_view key) {
    Check(index < definitions.size() && !key.empty() &&
              key.size() < key_storage[index].size(),
          "education fixture owns a valid complete native Trait key");
    auto &bytes = definitions[index];
    bytes.fill(std::byte{});
    if (key.size() < 16) {
      std::memcpy(bytes.data() + 0x18, key.data(), key.size());
      Put(bytes.data(), 0x30, std::uint64_t{15});
    } else {
      auto &storage = key_storage[index];
      storage.fill('\0');
      std::memcpy(storage.data(), key.data(), key.size());
      Put(bytes.data(), 0x18, storage.data());
      Put(bytes.data(), 0x30, static_cast<std::uint64_t>(storage.size() - 1));
    }
    Put(bytes.data(), 0x28, static_cast<std::uint64_t>(key.size()));
  }

  explicit ChildEducationPointTraitFixture40(Fixture &fixture) {
    child_characters = {fixture.characters[4].data(), fixture.characters[7].data()};
    for (std::size_t index = 0; index < definitions.size(); ++index) {
      SetKey(index, index < kChildhoodCount
          ? xar::ck3_11906::kChildhoodTraitKeysV1[index]
          : xar::ck3_11906::kChildEducationPointTraitKeysV1[index - kChildhoodCount]);
      ordered_definitions[index] = definitions[kTraitCount - 1 - index].data();
    }
    Put(database.data(), 0x50, ordered_definitions.data());
    Put(database.data(), 0x5C, static_cast<std::int32_t>(kTraitCount));
  }
};

ChildEducationPointTraitFixture40 *active_child_education_traits40 = nullptr;
void *ChildEducationPointTraitDatabase40() {
  return active_child_education_traits40 == nullptr ? nullptr
      : active_child_education_traits40->database.data();
}
bool ChildHasEducationPointTrait40(void *character, const void *trait) {
  Check(active_child_education_traits40 != nullptr,
        "education trait callbacks have an owning native dictionary fixture");
  auto &source = *active_child_education_traits40;
  std::size_t child_index = source.child_characters.size();
  std::size_t trait_index = source.definitions.size();
  for (std::size_t index = 0; index < source.child_characters.size(); ++index)
    if (character == source.child_characters[index]) child_index = index;
  for (std::size_t index = 0; index < source.definitions.size(); ++index)
    if (trait == source.definitions[index].data()) trait_index = index;
  Check(child_index < source.child_characters.size() &&
            trait_index < source.definitions.size(),
        "HasTrait receives the exact descendant child and resolved education definition");
  if (trait_index >= source.kChildhoodCount) {
    ++source.education_sample_calls[child_index];
    if (source.change_second_sample && child_index == 0 &&
        source.education_sample_calls[child_index] > source.kEducationCount &&
        trait_index == source.kChildhoodCount + 2)
      return !source.present[child_index][trait_index];
  }
  return source.present[child_index][trait_index];
}

void EmitChildEducationPointTraits40(const std::filesystem::path &directory,
                                    std::string_view name) {
  const bool subsets = name == "education-point-trait-subsets";
  const bool known_empty = name == "education-point-known-empty";
  const bool traits_missing = name == "education-point-traits-unavailable";
  const bool values_missing = name == "education-point-values-unavailable";
  const bool traits_changed = name == "education-point-traits-changed";
  Fixture fixture({"current-child-education-traits", subsets ? 18 : 1,
                   true, true, true, false});
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  Put(fixture.characters[4].data(), 0x68,
      static_cast<std::int16_t>(known_empty ? 0 : 7));
  Put(fixture.characters[4].data(), 0x1A1,
      static_cast<std::uint8_t>(values_missing ? 2 : 0));
  Put(fixture.characters[7].data(), 0x68, std::int16_t{9});
  Put(fixture.characters[7].data(), 0x1A1, std::uint8_t{1});
  ChildEducationPointTraitFixture40 traits(fixture);
  ChildFocusFixture39 focus(fixture);
  if (!known_empty) {
    traits.present[0][traits.kChildhoodCount + 2] = true; // intellect_good_3
    traits.present[0][traits.kChildhoodCount + 6] = true; // shrewd
  }
  if (subsets) {
    traits.present[1][traits.kChildhoodCount + 4] = true; // intellect_bad_2
    traits.present[1][traits.kChildhoodCount + 7] = true; // dull
    traits.present[1][traits.kChildhoodCount + 8] = true; // inbred
  }
  if (known_empty)
    Put(fixture.characters[4].data(), 0x1B0, static_cast<void *>(nullptr));
  if (traits_missing) traits.SetKey(traits.kTraitCount - 1, "other");
  traits.change_second_sample = traits_changed;
  active_child_education_traits40 = &traits;
  active_child_focus39 = &focus;
  xar::ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 environment{};
  environment.trait_database = &ChildEducationPointTraitDatabase40;
  environment.character_has_trait = &ChildHasEducationPointTrait40;
  environment.current_focus = &ChildCurrentFocus39;
  environment.focus_fallback_slot_address = reinterpret_cast<std::uintptr_t>(&focus.fallback);
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "education trait observers retain the current reciprocal married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  const auto inputs = xar::ck3_12004::ReadCurrentFirstHeirChildInputsV1(
      fixture.family, environment, *relation.descendants);
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, &inputs);
  const auto &descriptor = xar::game::Ck3_12004AdapterDescriptor();
  wire = xar::game::Render12004BuildIdentity(std::move(wire), descriptor);
  Write(directory / (std::string(name) + ".json"), wire);
  Check(xar::game::IsCk3_12004Descriptor(descriptor) &&
            inputs.rows.size() == (subsets ? 2U : 1U) &&
            inputs.status == (values_missing ? "partial" : "available") &&
            relation.descendants->roster_complete &&
            relation.descendants->native_child_count_raw == (subsets ? 18 : 1) &&
            wire.find("\"education_point_traits\":{\"source\":\"native_character_has_trait\"")
                != std::string::npos,
        "whole education trait wire uses the canonical descriptor and independent child aggregate");
  const auto &row = inputs.rows[0];
  Check(row.character_id == 0x03000005 && row.education_point_traits &&
            row.childhood_traits.available && row.childhood_traits.present_trait_keys &&
            row.childhood_traits.present_trait_keys->empty() && row.native_focus &&
            row.native_focus->available && row.values.available == !values_missing,
        "education predicates use the actual child and preserve old affinity focus and values");
  const auto &observed = *row.education_point_traits;
  if (traits_missing || traits_changed) {
    Check(!observed.available && !observed.present_trait_keys &&
              observed.unavailable_reason == (traits_missing
                  ? "child_trait_definitions_unavailable" : "child_trait_values_changed"),
          "missing education-only definition and changed real sample remain explicit failures");
  } else {
    const auto expected = known_empty ? std::vector<std::string_view>{}
        : std::vector<std::string_view>{"intellect_good_3", "shrewd"};
    Check(observed.available && observed.unavailable_reason.empty() &&
              observed.present_trait_keys && *observed.present_trait_keys == expected,
          "multiple true child traits and lawful all-false subset survive production collection");
  }
  if (known_empty)
    Check(row.values.age_measure_raw == 0 && row.native_focus->presence == "absent" &&
              !row.native_focus->key,
          "newborn zero age and no education trait are values rather than read failures");
  else if (!values_missing)
    Check(row.values.age_measure_raw == 7 && row.native_focus->key == "education_diplomacy",
          "school-age child preserves its independent readable current focus");
  if (subsets) {
    const auto &other = inputs.rows[1];
    Check(row.occurrence_indices == std::vector<std::uint32_t>{
                  0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16} &&
              other.character_id == 0x03000008 &&
              other.occurrence_indices == std::vector<std::uint32_t>{17} &&
              other.values.age_measure_raw == 9 && other.values.sex_selector_raw == 1 &&
              other.education_point_traits && other.education_point_traits->available &&
              other.education_point_traits->present_trait_keys ==
                  std::vector<std::string_view>{"intellect_bad_2", "dull", "inbred"} &&
              other.native_focus && other.native_focus->key == "education_learning" &&
              relation.descendants->rows.size() == 18,
          "distinct true trait subsets retain full-ID role age duplicate grouping and raw evidence");
  }
  Check(relation.relationship.primary_spouse_character_id == kPartner &&
            relation.relationship.spouse_character_ids == std::vector<std::int32_t>{kPartner} &&
            constructs == 0 && destroys == 0,
        "education trait observation dispatches no game or guardian action");
  active_child_focus39 = nullptr;
  active_child_education_traits40 = nullptr;
}
struct TypedWindowFixture51 {
  std::array<std::string, 7> names{};
  std::string fallback = "fixture_type_name_fallback";
  std::array<std::byte, 0x800> image{};
  std::array<std::byte, 0xD0> handler{};
  std::array<std::array<std::byte, sizeof(void *)>, 2> objects{};
  std::vector<std::int32_t> name_calls{};
  bool independent_unavailable = false;

  TypedWindowFixture51() {
    for (std::size_t index = 0; index < names.size(); ++index)
      names[index] = index == 6 ? "FixtureArmyWindowType6"
                               : "FixtureWindowType" + std::to_string(index);
    constexpr std::array<std::size_t, 2> vtables{0x108, 0x408};
    constexpr std::array<std::uint32_t, 2> locators{0x200, 0x500};
    constexpr std::array<std::uint32_t, 2> descriptors{0x300, 0x600};
    constexpr std::array<std::string_view, 2> type_names{
        ".?AVFixtureWindow0@@", ".?AVFixtureArmyWindow@@"};
    for (std::size_t index = 0; index < objects.size(); ++index) {
      Put(objects[index].data(), 0, image.data() + vtables[index]);
      Put(image.data(), vtables[index] - sizeof(void *),
          image.data() + locators[index]);
      Put(image.data(), locators[index], std::uint32_t{1});
      Put(image.data(), locators[index] + 0xC, descriptors[index]);
      Put(image.data(), locators[index] + 0x14, locators[index]);
      std::memcpy(image.data() + descriptors[index] + 0x10,
                  type_names[index].data(), type_names[index].size());
    }
    Put(handler.data(), 0x98, objects[0].data());
    Put(handler.data(), 0xC8, objects[1].data());
  }
};

TypedWindowFixture51 *active_typed_windows51 = nullptr;

const std::string *FixtureWindowTypeName51(std::int32_t identifier) {
  Check(active_typed_windows51 != nullptr,
        "fixed registered-name callback has an owning fixture");
  auto &window_source = *active_typed_windows51;
  window_source.name_calls.push_back(identifier);
  const auto &specs = xar::ck3_11906::kCurrentFirstHeirTypedWindowSpecsV1;
  for (std::size_t index = 0; index < specs.size(); ++index) {
    if (identifier != specs[index].type_identifier) continue;
    if (window_source.independent_unavailable && index == 1)
      return &window_source.fallback;
    if (window_source.independent_unavailable && index == 2) return nullptr;
    return &window_source.names[index];
  }
  throw std::runtime_error("observer resolved an ID outside the fixed seven");
}

void EmitChildTypedWindows51(const std::filesystem::path &directory,
                            std::string_view name) {
  const bool independent_unavailable = name == "typed-window-independent-unavailable";
  const bool handler_unavailable = name == "typed-window-handler-unavailable";
  Fixture fixture({"current-child-typed-windows", handler_unavailable ? 1 : 0,
                   !handler_unavailable, true, true, false});
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "window diagnostic retains the existing reciprocal married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  auto inputs = xar::ck3_12004::ReadCurrentFirstHeirChildInputsV1(
      fixture.family, {}, *relation.descendants);
  TypedWindowFixture51 windows{};
  windows.independent_unavailable = independent_unavailable;
  if (independent_unavailable)
    Put(windows.image.data(), 0x500, std::uint32_t{0});
  active_typed_windows51 = &windows;
  xar::ck3_12002::EventWindowBindings name_bindings{};
  name_bindings.resolve_generic_value_type_name = &FixtureWindowTypeName51;
  name_bindings.generic_value_type_name_fallback = &windows.fallback;
  inputs.typed_windows = xar::ck3_11906::ReadCurrentFirstHeirTypedWindowRows12004V1(
      reinterpret_cast<std::uintptr_t>(windows.image.data()), windows.image.size(),
      name_bindings, handler_unavailable ? nullptr : windows.handler.data());
  const auto &observed = *inputs.typed_windows;
  const auto &specs = xar::ck3_11906::kCurrentFirstHeirTypedWindowSpecsV1;
  Check(observed.rows.size() == specs.size() && windows.name_calls.size() == specs.size() &&
            observed.window_handler_available == !handler_unavailable &&
            inputs.rows.empty() &&
            inputs.status == (handler_unavailable ? "unavailable" : "available"),
        "seven typed inputs remain independent of empty or unavailable child roster");
  for (std::size_t index = 0; index < specs.size(); ++index) {
    const auto &row = observed.rows[index];
    Check(row.slot_index == specs[index].slot_index &&
              row.handler_member_offset == specs[index].handler_member_offset &&
              row.type_identifier == specs[index].type_identifier &&
              windows.name_calls[index] == specs[index].type_identifier,
          "each native name lookup and handler offset uses its exact fixed ID");
    const bool name_missing = independent_unavailable && (index == 1 || index == 2);
    Check(row.registered_name_available == !name_missing &&
              (name_missing ? !row.registered_name
                            : row.registered_name == windows.names[index]),
          "null and fallback names never become plausible registered type names");
    if (handler_unavailable) {
      Check(row.window_presence == "unavailable" &&
                row.object_type_status == "unavailable" && row.registered_name_available,
            "unavailable handler preserves all seven independent registered names");
    } else if (index != 0 && index != 6) {
      Check(row.window_presence == "absent" &&
                row.object_type_status == "not_applicable" &&
                !row.object_type_descriptor_rva && !row.object_type_decorated_name,
            "null slot is lawful absent rather than failed object typing");
    } else if (independent_unavailable && index == 6) {
      Check(row.window_presence == "present" && row.object_type_status == "unavailable" &&
                !row.object_type_unavailable_reason.empty() && row.registered_name_available,
            "invalid object RTTI preserves the independently observed type-table name");
    } else {
      Check(row.window_presence == "present" && row.object_type_status == "available" &&
                row.object_vtable_rva == (index == 0 ? 0x108U : 0x408U) &&
                row.object_col_rva == (index == 0 ? 0x200U : 0x500U) &&
                row.object_type_descriptor_rva == (index == 0 ? 0x300U : 0x600U) &&
                row.object_type_decorated_name ==
                    (index == 0 ? ".?AVFixtureWindow0@@" : ".?AVFixtureArmyWindow@@"),
            "present windows retain their exact native COL/TD and decorated type");
    }
  }
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, &inputs);
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), xar::game::Ck3_12004AdapterDescriptor());
  Write(directory / (std::string(name) + ".json"), wire);
  Check(wire.find("\"typed_windows\":{\"source\":\"native_fixed_window_type_diagnostic\"")
                != std::string::npos &&
            relation.relationship.primary_spouse_character_id == kPartner &&
            constructs == 0 && destroys == 0,
        "typed-window evidence uses the production whole serializer without dispatch");
  active_typed_windows51 = nullptr;
}
struct CharacterWindowIdentityFixture {
  static constexpr std::uintptr_t kVtable = 0x451BA18;
  static constexpr std::uintptr_t kCol = 0x4AEF4B8;
  static constexpr std::uintptr_t kTypeDescriptor = 0x5723010;
  static constexpr std::uintptr_t kImageSize = 0x5724000;
  static constexpr std::uintptr_t kPageSize = 0x1000;
  std::byte *image = nullptr;
  std::array<std::byte, 0xD0> window{};
  std::array<std::byte, 0xE0> handler{};

  CharacterWindowIdentityFixture(bool wrong_type, std::int32_t requested_id) {
    image = static_cast<std::byte *>(VirtualAlloc(
        nullptr, kImageSize, MEM_RESERVE, PAGE_NOACCESS));
    Check(image != nullptr, "reserve the exact named CharacterWindow fixture image");
    for (const auto rva : {kVtable, kCol, kTypeDescriptor}) CommitPage(rva);
    if (wrong_type) CommitPage(0);
    const auto vtable = wrong_type ? std::uintptr_t{0x108} : kVtable;
    const auto col = wrong_type ? std::uintptr_t{0x200} : kCol;
    const auto descriptor = wrong_type ? std::uintptr_t{0x300} : kTypeDescriptor;
    const std::string_view decorated = wrong_type ? ".?AVCArmyWindow@@"
                                                  : ".?AVCCharacterWindow@@";
    Put(window.data(), 0, image + vtable);
    Put(window.data(), 0xC8, requested_id);
    Put(handler.data(), 0xD8, window.data());
    Put(image, vtable - sizeof(void *), image + col);
    Put(image, col, std::uint32_t{1});
    Put(image, col + 4, std::uint32_t{0});
    Put(image, col + 0xC, static_cast<std::uint32_t>(descriptor));
    Put(image, col + 0x14, static_cast<std::uint32_t>(col));
    std::memcpy(image + descriptor + 0x10, decorated.data(), decorated.size());
  }

  ~CharacterWindowIdentityFixture() {
    if (image != nullptr) VirtualFree(image, 0, MEM_RELEASE);
  }
  CharacterWindowIdentityFixture(const CharacterWindowIdentityFixture &) = delete;
  CharacterWindowIdentityFixture &operator=(const CharacterWindowIdentityFixture &) = delete;

  void CommitPage(std::uintptr_t rva) {
    const auto page = rva & ~(kPageSize - 1);
    if (VirtualAlloc(image + page, kPageSize, MEM_COMMIT, PAGE_READWRITE) == nullptr) {
      VirtualFree(image, 0, MEM_RELEASE);
      image = nullptr;
      throw std::runtime_error("commit the named RTTI fixture page");
    }
  }
};

void EmitChildCharacterWindowIdentity(const std::filesystem::path &directory,
                                     std::string_view name) {
  const bool receiver_missing = name == "character-window-receiver-unavailable";
  const bool wrong_type = name == "character-window-type-mismatch";
  const bool invalid_id = name == "character-window-id-invalid";
  const bool generation_mismatch = name == "character-window-generation-mismatch";
  const bool resolved = name == "character-window-id-resolved";
  Fixture fixture({"current-child-character-window-identity", 0, true, true, true, false});
  std::array<std::int32_t, 1> heir_spouses{kPartner}, partner_spouses{kHeir};
  Put(fixture.families[1].data(), 0x14, kPartner);
  Put(fixture.families[2].data(), 0x14, kHeir);
  Put(fixture.families[1].data(), 0x20, heir_spouses.data());
  Put(fixture.families[2].data(), 0x20, partner_spouses.data());
  for (const auto index : {1U, 2U}) {
    Put(fixture.families[index].data(), 0x28, std::int32_t{1});
    Put(fixture.families[index].data(), 0x2C, std::int32_t{1});
  }
  auto relation = ReadCurrentFirstHeirRelationshipV1(fixture.family, kHeir);
  Check(relation.failure == xar::ck3_11906::CurrentFirstHeirRelationshipFailureV1::none,
        "CharacterWindow evidence retains the actual reciprocal married pair");
  relation.betrothal_actionability = ReadCurrentFirstHeirBetrothalActionabilityV1(
      fixture.family, relation);
  relation.descendants = xar::ck3_12004::ReadCurrentFirstHeirDescendantsV1(
      fixture.family, kHeir);
  auto inputs = xar::ck3_12004::ReadCurrentFirstHeirChildInputsV1(
      fixture.family, {}, *relation.descendants);
  const auto requested_id = invalid_id ? std::int32_t{-1}
      : generation_mismatch ? std::int32_t{0x07000004} : kRecipient;
  CharacterWindowIdentityFixture window(wrong_type, requested_id);
  if (receiver_missing) Put(window.handler.data(), 0xD8, static_cast<void *>(nullptr));
  inputs.character_window_identity =
      xar::bridge::ReadCurrentFirstHeirCharacterWindowCandidate12004V1(
          reinterpret_cast<std::uintptr_t>(window.image), window.kImageSize,
          fixture.family.context.core, window.handler.data());
  const auto &identity = *inputs.character_window_identity;
  const bool receiver_available = !receiver_missing && !wrong_type;
  const char *receiver_reason = receiver_missing ? "character_window_receiver_absent"
      : wrong_type ? "character_window_vtable_mismatch" : "";
  const char *character_reason = !receiver_available ? "character_window_receiver_unavailable"
      : invalid_id ? "character_window_character_id_invalid"
      : generation_mismatch ? "character_window_character_unresolved" : "";
  Check(identity.receiver_available == receiver_available &&
            identity.character_available == resolved &&
            identity.receiver_unavailable_reason == receiver_reason &&
            identity.character_unavailable_reason == character_reason,
        "receiver admission and generation-valid identity remain distinct native results");
  Check((receiver_available ? identity.raw_character_id == requested_id
                            : !identity.raw_character_id) &&
            (resolved ? identity.character_id == kRecipient : !identity.character_id),
        "the raw C8 full ID retains sentinel and generation while only a resolved ID is published");
  Check(inputs.status == "available" && inputs.rows.empty() &&
            relation.descendants->rows.empty() &&
            kRecipient != kActor && kRecipient != kHeir &&
            relation.relationship.primary_spouse_character_id == kPartner &&
            relation.relationship.spouse_character_ids == std::vector<std::int32_t>{kPartner},
        "the fixture window subject never replaces the real empty child roster or actor/heir");
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, kHeir, relation, {}, &inputs);
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), xar::game::Ck3_12004AdapterDescriptor());
  Write(directory / (std::string(name) + ".json"), wire);
  Check(wire.find("\"character_window_identity\":{") != std::string::npos &&
            constructs == 0 && destroys == 0,
        "CharacterWindow identity uses the production complete packet serializer without actions");
}
} // namespace
int main(int argc, char **argv) {
  try {
    if (argc == 3 && std::string_view(argv[1]) == "--conception-trait-exclusion-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"heir-blocked", "spouse-blocked", "no-traits",
               "multiple-traits-fallback-blocked", "trait-db-unavailable",
               "fertility-unavailable-trait-blocked"})
        EmitConceptionTraitExclusion70(directory, name);
      std::cout << "PASS actual4 current household conception trait exclusion: six new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--child-character-window-identity-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"character-window-receiver-unavailable",
               "character-window-type-mismatch", "character-window-id-invalid",
               "character-window-generation-mismatch", "character-window-id-resolved"})
        EmitChildCharacterWindowIdentity(directory, name);
      std::cout << "PASS actual4 current-child CharacterWindow identity: five new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--child-typed-window-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"typed-window-seven-mixed",
               "typed-window-independent-unavailable", "typed-window-handler-unavailable"})
        EmitChildTypedWindows51(directory, name);
      std::cout << "PASS actual4 current-child typed windows: three new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--child-education-point-trait-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"education-point-trait-subsets",
               "education-point-known-empty", "education-point-traits-unavailable",
               "education-point-values-unavailable", "education-point-traits-changed"})
        EmitChildEducationPointTraits40(directory, name);
      std::cout << "PASS actual4 current-child education point traits: five new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--child-focus-observer-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"empty-children-focus", "distinct-child-focus-keys",
               "child-focus-sentinel-absent", "child-focus-null-unavailable",
               "child-focus-key-unavailable", "child-focus-independent-of-values"})
        EmitChildFocusObservers39(directory, name);
      std::cout << "PASS actual4 current-child focus: six new whole wires\n";
      return 0;
    }
    if (argc == 3 && std::string_view(argv[1]) == "--child-observer-wire-dir") {
      const std::filesystem::path directory(argv[2]);
      std::filesystem::create_directories(directory);
      for (const std::string_view name : {"empty-children", "living-child-no-traits",
               "childhood-affinity", "child-values-unavailable", "child-traits-unavailable"})
        EmitChildObservers35(directory, name);
      std::cout << "PASS actual4 current first-heir child inputs: five new whole wires\n";
      return 0;
    }
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

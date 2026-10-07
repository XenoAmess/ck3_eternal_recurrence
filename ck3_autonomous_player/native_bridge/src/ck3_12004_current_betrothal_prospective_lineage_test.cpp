#include "xar_bridge/ck3_12002_family.hpp"
#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_family.hpp"
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
constexpr std::uintptr_t kOfferVtable = 0x12004;
struct Scene {
  std::string_view name;
  bool selected = false;
  std::uint8_t subject_selector = 0;
  std::uint8_t partner_selector = 1;
  bool bind_preview = true;
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
void *subject_object = nullptr;
void *partner_object = nullptr;
void *active_context = nullptr;
bool final_selected = false;
std::size_t constructs = 0;
std::size_t destroys = 0;
std::size_t parent_reads = 0;
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
  Put(context, 0x301, static_cast<std::uint8_t>(final_selected));
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
void *Parent(const void *offer) {
  ++parent_reads;
  Check(constructs == 1 && destroys == 0 && active_context != nullptr,
        "preview reuses current finalized context without a second context");
  Check(Load<std::uintptr_t>(offer, 0) == kOfferVtable &&
            Load<void *>(offer, 8) == nullptr &&
            Load<std::int32_t>(offer, 0x28) == kHeir &&
            Load<std::int32_t>(offer, 0x2C) == kPartner &&
            Load<bool>(offer, 0x80) == final_selected,
        "detached offer preserves actual selected bool and fixed full IDs");
  const bool subject_selector = Load<std::uint8_t>(subject_object, 0x1A1) != 0;
  return final_selected == subject_selector ? subject_object : partner_object;
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
  std::array<std::array<std::byte, 0x1D8>, 4> characters{};
  std::array<std::array<std::byte, 0x30>, 4> families{};
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
  family_obligations_lineage::Bindings lineage{};

  explicit Fixture(const Scene &scene) {
    constructs = destroys = parent_reads = 0;
    active_context = nullptr;
    final_selected = scene.selected;
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
    const std::array<std::int32_t, 4> ids{kActor, kHeir, kPartner, kRecipient};
    for (std::size_t i = 0; i < ids.size(); ++i) {
      Put(characters[i].data(), 0x18, ids[i]);
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
    Put(characters[1].data(), 0x1A1, scene.subject_selector);
    Put(characters[2].data(), 0x1A1, scene.partner_selector);
    Put(characters[1].data(), 0x158, std::int32_t{100});
    Put(characters[2].data(), 0x158, std::int32_t{300});
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
    Put(database.data(), 0xF30, def.data());
    definition = def.data();
    local_player = local.data();
    subject_object = characters[1].data();
    partner_object = characters[2].data();
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
    lineage.enabled = true;
    lineage.family = family;
    lineage.native_offer_vtable = kOfferVtable;
    lineage.native_preview_parent = scene.bind_preview ? &Parent : nullptr;
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
      fixture.family, relation, &fixture.lineage);
  const auto &read = relation.betrothal_actionability;
  if (scene.betrothed) {
    const bool effective = scene.subject_selector == scene.partner_selector
        ? scene.subject_selector != 0 : scene.selected;
    Check(read.unavailable_reason.empty() && read.complete_can_send &&
              read.outcome_available && read.lineality_available &&
              read.adult.predicted_outcome == xar::bridge::MarriagePredictedOutcomeV1::marriage &&
              read.effective_matrilineal_if_accepted == effective &&
              read.matrilineal_option_selected == scene.selected,
          "new observation retains legacy final actionability and actual option");
    Check(constructs == 1 && destroys == 1,
          "one finalized context is released once");
    if (scene.bind_preview) {
      const bool subject_parent = scene.selected == (scene.subject_selector != 0);
      Check(read.native_child_house_preview_available && parent_reads == 1 &&
                read.native_selected_parent_character_id == (subject_parent ? kHeir : kPartner) &&
                read.native_preview_lineage.house_id == (subject_parent ? 100 : 300) &&
                read.native_preview_lineage.dynasty_id == (subject_parent ? 200 : 400),
            "actual parent getter and full House/Dynasty reader reach current preview");
    } else {
      Check(!read.native_child_house_preview_available && parent_reads == 0,
            "missing optional preview leaves current legacy action usable");
    }
  } else {
    Check(read.unavailable_reason == "current_heir_has_no_betrothal" &&
              !read.matrilineal_option_selected.has_value() &&
              !read.native_child_house_preview_available &&
              constructs == 0 && destroys == 0 && parent_reads == 0,
          "no current betrothal skips unused context and preview");
  }
  auto wire = xar::ck3_11906::CurrentFirstHeirRelationshipResultJsonV1(
      scene.name, 7, kHeir, relation);
  wire = xar::game::Render12004BuildIdentity(
      std::move(wire), xar::game::Ck3_12004AdapterDescriptor());
  Write(directory / (std::string(scene.name) + ".json"), wire);
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "supply exactly one new whole-wire directory");
    constexpr std::uintptr_t image_base = 0x140000000;
    const auto actual = xar::ck3_12004::BindFamilyLineageImage(
        image_base, xar::ck3_12004::kExecutableSha256);
    Check(actual.enabled &&
              reinterpret_cast<std::uintptr_t>(actual.native_preview_parent) == image_base + 0x1375380 &&
              actual.native_offer_vtable == image_base + 0x454E470,
          "actual4 binder uses source-closed preview entrance and offer vtable");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    const std::array<Scene, 5> scenes{{
        {"selected-false"},
        {"selected-true", true},
        {"same-selector", true, 0, 0},
        {"preview-binding-missing", false, 0, 1, false},
        {"no-betrothal", false, 0, 1, true, false}}};
    for (const auto &scene : scenes) Emit(directory, scene);
    std::cout << "PASS actual4 current-betrothal prospective lineage: five new whole wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}

#include "xar_bridge/ck3_12002_family_obligations_break.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t actor_id = 0x03000001, subject_id = 0x03000002, partner_id = 0x03000003;
constexpr std::uint32_t stable_hash = 0xB3401202;
template <typename T> void Put(void *p, std::size_t n, T v) {
  std::memcpy(static_cast<std::byte *>(p) + n, &v, sizeof(T));
}
template <typename T> T Load(const void *p, std::size_t n) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + n, sizeof(T)); return value;
}
void Check(bool ok, const char *text) { if (!ok) throw std::runtime_error(text); }
void *local_player = nullptr, *database = nullptr, *definition = nullptr;
void *clock_state = nullptr;
void *trait_database = nullptr, *promised_context = nullptr, *empty_context = nullptr;
const std::string promise_key = "promised_grand_wedding_by", flag_key = "can_not_marry";
bool legal = true, drift = false, wrong_subject = false, missing = false;
int contexts = 0, destroys = 0, validates = 0, costs = 0;
void *LocalPlayer(void *) { return local_player; }
void *Database() { return database; }
std::int32_t Hash(void *db, const char *key, std::uint32_t length) {
  Check(db == database && std::string_view(key, length) == kFamilyBreakDefinitionKeyV1, "canonical definition hash");
  return static_cast<std::int32_t>(stable_hash);
}
void *Lookup(void *db, std::int32_t hash) {
  Check(db == database && static_cast<std::uint32_t>(hash) == stable_hash, "full signed native hash");
  return missing ? nullptr : definition;
}
void Redirect(void *def, std::int32_t *actor, std::int32_t *recipient, std::int32_t *subject,
    std::int32_t *partner, std::int32_t *intermediary, std::int32_t *sixth) {
  Check(def == definition && *actor == actor_id && *recipient == partner_id && *subject == subject_id &&
      *partner == partner_id && *intermediary == -1 && *sixth == -1, "exact requested pair and six-role redirect");
  if (wrong_subject) *subject = actor_id;
}
void *Construct(void *context, void *def, std::int32_t actor, std::int32_t recipient,
    std::int32_t subject, std::int32_t partner, std::int32_t intermediary, void *extra) {
  Check(extra == nullptr, "all-role final context argument");
  ++contexts; Put(context, 0, def); Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  Put(context, 0x2E0, subject); Put(context, 0x2E4, partner); Put(context, 0x2E8, intermediary);
  return context;
}
void Refresh(void *, bool full) { Check(full, "complete native refresh"); }
void Finalize(void *) {}
bool Validate(void *context, void *error) {
  ++validates;
  Check(error == nullptr && Load<std::int32_t>(context, 0x2E0) == subject_id, "native final legality subject");
  return legal;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  ++costs;
  Check(block == static_cast<std::byte *>(definition) + 0x40 &&
      Load<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition, "real native cost block/scope");
  for (int i = 0; i < 10; ++i) out[i] = i == 1 ? -1'000'000 : i * 100'000;
  if (drift) Put(clock_state, 8, std::int32_t{53220001});
}
void Destroy(void *context) { ++destroys; Put(context, 0, static_cast<void *>(nullptr)); }
void *TraitDatabase() { return trait_database; }
bool HasTrait(void *, const void *) { return false; }
bool HasFlag(void *, const std::int32_t *id) { Check(*id == 55, "native cannot-marry flag ID"); return false; }
void *VariableTable() { return trait_database; }
std::int32_t *VariableId(void *, std::int32_t *id, const PhaseStringView32 *view) {
  Check(std::string_view(view->data, view->size) == promise_key, "actual grand promise variable key");
  *id = 56; return id;
}
const std::string *VariableName(void *, std::int32_t id) { Check(id == 56, "variable round trip"); return &promise_key; }
std::int32_t ScriptId(const PhaseStringView64 *view) {
  Check(std::string_view(view->data, static_cast<std::size_t>(view->size)) == flag_key, "script flag key");
  return 55;
}
const std::string *ScriptName(std::int32_t id) { Check(id == 55, "script identifier round trip"); return &flag_key; }
void *Variables(const PhaseVariableTarget *target) {
  Check(target->kind == 4, "native variable target kind is Character");
  return target->payload == subject_id ? promised_context : empty_context;
}
void *Matchmaker(void *character) { return character; }
bool Family(void *, void *) { return false; }
std::int32_t HighestTier(void *) { return 4; }
bool Yields(void *, void *, void *, void *) { return false; }
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 3> characters{};
  std::array<std::array<std::byte, 0x30>, 3> families{};
  std::array<std::byte, 0x80> def{};
  std::array<std::byte, 0x60> trait_db{};
  std::array<std::array<std::byte, 0x40>, 2> trait_defs{};
  std::array<void *, 2> trait_entries{trait_defs[0].data(), trait_defs[1].data()};
  std::array<std::byte, 0x20> variable_record{}, promised_variables{}, no_variables{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *store_ptr = store.data(), *missing_ptr = nullptr;
  FamilyObligationsBreakBindingsV1 b{};
  Fixture() {
    legal = true; drift = wrong_subject = missing = false;
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game.data()); Put(jomini.data(), 0x18, players.data());
    jomini[0x20] = std::byte{1}; Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local.data(), 0x70, std::int32_t{7});
    Put(game.data(), 0x222E8 + 0x58, entries.data()); Put(game.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{7}); Put(entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{8});
    for (std::size_t i = 0; i < characters.size(); ++i) {
      const auto id = actor_id + static_cast<std::int32_t>(i);
      Put(characters[i].data(), 0x18, id); Put(slots.data(), (id & 0xFFFFFF) * 0x10 + 8, characters[i].data());
      Put(characters[i].data(), 0x1C, std::uint32_t{0x43686172});
      Put(characters[i].data(), kMarriageCharacterFamilyDataOffset, families[i].data());
      Put(families[i].data(), 0x10, std::int32_t{-1});
    }
    Put(families[1].data(), 0x10, partner_id); Put(families[2].data(), 0x10, subject_id);
    Put(def.data(), kFamilyBreakDefinitionOrdinalOffsetV1, std::int32_t{12});
    Put(def.data(), kFamilyBreakDefinitionHashOffsetV1, stable_hash);
    Put(def.data(), kFamilyBreakDefinitionKeyOffsetV1, kFamilyBreakDefinitionKeyV1.data());
    Put(def.data(), kFamilyBreakDefinitionKeyOffsetV1 + 0x10, kFamilyBreakDefinitionKeyV1.size());
    Put(def.data(), kFamilyBreakDefinitionKeyOffsetV1 + 0x18, std::size_t{31});
    Put(def.data(), kFamilyBreakDefinitionKindOffsetV1, kFamilyBreakDefinitionKindV1);
    local_player = local.data(); database = &b; definition = def.data(); clock_state = state.data();
    b.enabled = b.interaction.enabled = true;
    b.interaction.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer};
    b.get_database = &Database; b.stable_hash = &Hash; b.lookup_definition = &Lookup;
    b.missing_definition_slot = &missing_ptr;
    b.interaction.redirect_roles = &Redirect; b.interaction.construct_all_roles = &Construct;
    b.interaction.refresh = &Refresh; b.interaction.finalize = &Finalize; b.interaction.validate = &Validate;
    b.interaction.destroy = &Destroy; b.interaction.evaluate_cost = &Cost;
  }
  void EnableGrandPenalty() {
    const std::array<std::string_view, 2> keys{"eunuch_1", "beardless_eunuch"};
    for (std::size_t i = 0; i < keys.size(); ++i) {
      if (keys[i].size() <= 15)
        std::memcpy(trait_defs[i].data() + 0x18, keys[i].data(), keys[i].size());
      else Put(trait_defs[i].data(), 0x18, keys[i].data());
      Put(trait_defs[i].data(), 0x28, keys[i].size());
      Put(trait_defs[i].data(), 0x30, keys[i].size() <= 15 ? std::size_t{15} : std::size_t{31});
    }
    Put(trait_db.data(), 0x50, trait_entries.data()); Put(trait_db.data(), 0x5C, std::int32_t{2});
    Put(variable_record.data(), 8, std::int32_t{56});
    Put(promised_variables.data(), 0x10, variable_record.data()); Put(promised_variables.data(), 0x1C, std::int32_t{1});
    Put(characters[2].data(), family_value::kCharacterSexSelectorOffset, std::uint8_t{1});
    trait_database = trait_db.data(); promised_context = promised_variables.data(); empty_context = no_variables.data();
    auto &p = b.penalty;
    p.enabled = true; p.traits.get_trait_database = &TraitDatabase; p.traits.character_has_trait = &HasTrait;
    p.has_trait_flag = &HasFlag; p.matchmaker = &Matchmaker; p.close_family = p.close_or_extended_family = &Family;
    p.highest_tier = &HighestTier; p.yields_alliance = &Yields;
    auto &d = p.identifiers;
    d.enabled = true; d.variable_table = &VariableTable; d.lookup_variable_identifier = &VariableId;
    d.variable_identifier_name = &VariableName; d.lookup_script_identifier = &ScriptId;
    d.script_identifier_name = &ScriptName; d.variable_context = &Variables;
  }
  auto Read() { return ReadFamilyObligationsBreakTermsV1(b, subject_id, partner_id); }
};
} // namespace

int main() {
  try {
    using Status = FamilyObligationsBreakStatusV1;
    const auto exact = BindFamilyObligationsBreakImageV1(0x140000000, kExecutableSha256);
    Check(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.lookup_definition) ==
        0x140000000 + kFamilyBreakLookupDefinitionRvaV1, "exact new native source binding");
    Check(!BindFamilyObligationsBreakImageV1(0x140000000, "1.19.0.6").enabled, "old image not bound");
    Fixture f;
    auto read = f.Read();
    Check(read.status == Status::available && read.complete_can_send && read.final_legality_sampled &&
        read.native_send_costs_available && read.native_send_costs_raw[1] == -1'000'000 &&
        read.native_send_costs_raw[9] == 900'000 && read.secondary_actor_character_id == subject_id &&
        read.betrothed_character_id == partner_id && read.definition_ordinal == 12 &&
        read.definition_stable_hash == stable_hash && !read.outcome_resource_penalty.resource_penalty_available,
        "actual provider reads final CanSend and signed costs without claiming total on_accept penalty");
    legal = false; read = f.Read();
    Check(read.status == Status::available && !read.complete_can_send && read.final_legality_sampled &&
        read.native_send_costs_available, "negative CanSend remains complete observation");
    f.EnableGrandPenalty(); read = f.Read();
    Check(read.status == Status::available && read.outcome_resource_penalty.resource_penalty_available &&
        read.outcome_resource_penalty.grand_wedding_promised && !read.outcome_resource_penalty.proper_reason &&
        read.outcome_resource_penalty.stock_prestige_effect_raw == -75'000'000 &&
        read.outcome_resource_penalty.stock_prestige_level_effect == -1 &&
        !read.outcome_resource_penalty.effects_complete && read.native_send_costs_raw[1] == -1'000'000,
        "same actual provider composes native penalty inputs and exact stock resources separately from send costs");
    const auto before = contexts;
    wrong_subject = true;
    Check(f.Read().status == Status::unavailable && contexts == before, "redirected different subject not sampled");
    wrong_subject = false; missing = true;
    Check(f.Read().unavailable_reason == "break_betrothal_definition_unavailable", "lookup missing definition observable");
    missing = false;
    Put(f.families[2].data(), 0x10, std::int32_t{-1});
    Check(f.Read().unavailable_reason == "break_betrothal_bilateral_pair_unavailable", "one-sided relationship not accepted");
    Put(f.families[2].data(), 0x10, subject_id);
    Put(f.families[1].data(), 0x10, std::int32_t{-1});
    read = f.Read();
    Check(read.status == Status::no_betrothal && !read.final_legality_sampled, "known no-betrothal observation");
    Put(f.families[1].data(), 0x10, partner_id); drift = true;
    read = f.Read();
    Check(read.status == Status::unavailable && !read.native_send_costs_available &&
        read.native_send_costs_raw == std::array<std::int64_t, 10>{} &&
        read.unavailable_reason == "break_betrothal_frame_changed", "changed frame discards evaluated terms");
    Check(contexts == destroys && validates == costs, "owned context destructor after actual evaluations");
    std::cout << "PASS break-betrothal provider: canonical definition, bilateral pair, native roles/CanSend/10 costs, stock-resource/native-input composition, no pair, negative, lifetime\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}

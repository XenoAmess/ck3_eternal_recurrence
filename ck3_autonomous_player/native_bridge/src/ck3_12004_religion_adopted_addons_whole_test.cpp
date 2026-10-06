// AUTHORED_NOTRUN. Ten fresh whole command_result packets from production
// owner mailboxes, actual .4 reader wrappers and owned synthetic callbacks.
// No EXE branches, game process, archived packet or old fixture main is used.
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12004_religion_context_addons.hpp"
#include "xar_bridge/ck3_12004_religion_parameter_bindings.hpp"
#include "xar_bridge/ck3_12004_doctrine_catalogue_bindings.hpp"
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_hostility_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_catalogue_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_numeric_mailbox.hpp"
#include "xar_bridge/religion_doctrine12002_personal_parameters_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_choices_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_reasons_mailbox.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_inputs_mailbox.hpp"
#include "xar_bridge/conversion_outcome12002_mailbox.hpp"

#include <windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

namespace {
namespace old = xar::ck3_12002;
namespace actual = xar::ck3_12004;
namespace religion = old::religion;
namespace fourth = actual::religion;
namespace third = xar::ck3_12003::religion;
namespace doctrine = religion::doctrine12002;
namespace factory = third::pilgrimage_candidate_factory;
namespace api = xar::ck3_11906;
namespace game = xar::game;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <class T> T Load(const void *object, std::size_t offset = 0) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
template <class T> void Store(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class Buffer, class T> void Put(Buffer &buffer, std::size_t offset, T value) {
  Store(buffer.data(), offset, value);
}
void NativeString(void *object, std::size_t offset, const char *literal) {
  auto *key = static_cast<std::byte *>(object) + offset;
  const auto size = std::strlen(literal);
  std::memset(key, 0, 0x20);
  if (size < 16) std::memcpy(key, literal, size);
  else Store(key, 0, literal); // World-owned literal; no native heap ownership.
  Store(key, 0x10, static_cast<std::uint64_t>(size));
  Store(key, 0x18, static_cast<std::uint64_t>(size < 16 ? 15 : size));
}
template <class Buffer, class T, std::size_t N>
void Collection(Buffer &buffer, std::size_t offset, std::array<T, N> &items) {
  Put(buffer, offset, items.data());
  Put(buffer, offset + 8, static_cast<std::int32_t>(N));
  Put(buffer, offset + 0xC, static_cast<std::int32_t>(N));
}

struct World {
  static constexpr std::uintptr_t image_base = 0x140000000;
  static constexpr std::int32_t actor_id = 29829;
  static constexpr std::int32_t date = 53286648;
  static constexpr std::uint64_t revision = 171, epoch = 12004;
  static constexpr std::uint32_t rite_id = 0x82000002, main_id = 0x83000004;
  static constexpr std::uint32_t target_id = 0x86000003;
  static constexpr std::uint32_t faith_id = 0x84000001, religion_id = 0x85000001;
  static constexpr std::uint32_t title_id = 0x81000001, holy_id = 0x87000001;
  static constexpr std::int32_t province_id = 72;
  const DWORD owner = GetCurrentThreadId();
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, rite_storage{}, faith_storage{}, title_storage{}, holy_storage{};
  std::vector<std::byte> character_slots = std::vector<std::byte>((actor_id + 1U) * 0x10);
  Bytes<0x80> rite_slots{};
  Bytes<0x30> faith_slots{}, title_slots{}, holy_slots{};
  Bytes<0x200> character{};
  Bytes<0x350> resources{};
  Bytes<0x100> extension{};
  Bytes<0x220> land{};
  Bytes<0x1000> rite{}, main_rite{}, target_rite{};
  Bytes<0x900> faith{};
  Bytes<0x28> native_religion{};
  Bytes<0x40> religion_definition{};
  Bytes<0x400> title{};
  Bytes<0xC0> holy_site{};
  Bytes<0xB20> doctrine_a{}, doctrine_b{};
  Bytes<0x40> group_a{}, group_b{};
  Bytes<0x70> doctrine_database{};
  std::array<const void *, 3> doctrine_rows{doctrine_b.data(), doctrine_a.data(), doctrine_b.data()};
  Bytes<0x780> tenet{};
  Bytes<0xF40> tenet_database{};
  std::array<const void *, 1> tenets{tenet.data()};
  std::array<std::int32_t, 1> owned_tokens{700};
  std::array<std::int32_t, 2> supported_tokens{700, 701};
  Bytes<0x20> token_true{}, token_false{};
  Bytes<0x30> faith_rites{};
  std::array<std::uint32_t, 3> rite_ids{rite_id, target_id, main_id};
  std::array<void *, 1> world_faiths{faith.data()};
  std::array<std::uint32_t, 1> titles{title_id}, holy_ids{holy_id};
  Bytes<0x70> fulfillment_type{};
  Bytes<0x430> fulfillment_levels{};
  Bytes<0x30> fulfillment_database{};
  std::int64_t minimum = 0, maximum = 1'000'000, native_define = 6'500'000;
  std::array<std::int64_t, 2> thresholds{500'000, 1'500'000};
  Bytes<0x10> threshold_vector{};
  Bytes<0x40> decision_database{};
  Bytes<0x40> communion{}, confession{}, vow{}, decision_fallback{}, cost{};
  Bytes<0x70> activity_database{};
  Bytes<0x3C00> activity_type{};
  Bytes<0x1180> phase_definition{};
  std::array<const void *, 1> activity_types{activity_type.data()};
  Bytes<0x880> province{}, start_province{};
  std::array<void *, 74> provinces{};
  std::array<const void *, 1> filtered_provinces{province.data()};
  Bytes<0x48> route_row{};
  std::uint64_t default_date = 0xFFFFFFFFU;
  std::array<std::uintptr_t, 3> allocator_vtable{};
  const void *allocator_vtable_pointer = allocator_vtable.data();
  Bytes<0x40> contract{}; // Expanded rule storage lives separately below.
  Bytes<0x380> lease_contract{};
  Bytes<0x40> trait_database{}, trait_a{}, trait_b{}, trait_c{};
  Bytes<0x30> virtue_record{}, sin_record{};
  std::array<std::int32_t, 3> traits{10, 11, 12};
  Bytes<0x30> atom_pool{}, flags{};
  Bytes<0x40> flag_rows{};
  std::int32_t host_token = 1, special_token = 2, location_token = 3;
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *rite_storage_ptr = rite_storage.data();
  void *faith_storage_ptr = faith_storage.data(), *title_storage_ptr = title_storage.data();
  void *holy_storage_ptr = holy_storage.data(), *doctrine_database_ptr = doctrine_database.data();
  void *tenet_database_ptr = tenet_database.data(), *fulfillment_database_ptr = fulfillment_database.data();
  void *decision_database_ptr = decision_database.data(), *activity_database_ptr = activity_database.data();
  const void *decision_fallback_ptr = decision_fallback.data();
  unsigned callbacks = 0;
  bool callback_scope_valid = true;
  bool callback_failure_reported = false;
  const char *callback_scene = "pre-query-core";

  World() {
    Put(state, actual::kGameStateDateOffset, date);
    Put(state, actual::kGameStateSpeedOffset, std::int32_t{2});
    Put(state, actual::kGameStateDataOffset, data.data());
    Put(jomini, actual::kJominiPlayersOffset, players.data());
    jomini[actual::kJominiPausedOffset] = std::byte{1};
    Put(players, actual::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(player, actual::kPlayerIdOffset, std::int32_t{7});
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerEntriesOffset, entries.data());
    Put(data, actual::kPlayerCharacterManagerOffset + actual::kPlayerManagerCountOffset, std::int32_t{1});
    Put(entry, actual::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry, actual::kPlayerEntryCharacterIdOffset, actor_id);
    Put(character_storage, 0x20, character_slots.data());
    Put(character_storage, 0x2C, actor_id + 1);
    Put(character_slots, static_cast<std::size_t>(actor_id) * 0x10 + 8, character.data());
    Put(character, actual::kCharacterFullIdOffset, actor_id);
    Put(character, 0x1C, std::uint32_t{0x43686172});
    Put(character, 0xB4, rite_id);
    Put(character, 0x1B0, resources.data());
    Put(character, 0x1C0, land.data());
    Put(character, 0x1C8, extension.data());
    Put(resources, 0x100, std::int64_t{-200'000});
    Put(resources, 0x110, std::int64_t{1'250'000});
    Put(resources, 0x118, std::int64_t{0});
    Put(resources, 0x130, std::int64_t{0});
    Put(resources, 0x300, std::int64_t{-50'000});
    Collection(land, 0x1E0, titles);
    Put(land, 0x1B8, actor_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{8});
    Put(rite_slots, 2 * 0x10 + 8, rite.data());
    Put(rite_slots, 3 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 4 * 0x10 + 8, main_rite.data());
    for (const auto pair : {std::pair{rite.data(), rite_id}, std::pair{main_rite.data(), main_id}, std::pair{target_rite.data(), target_id}}) {
      Store(pair.first, 8, pair.second);
      Store(pair.first, 0xC, std::uint32_t{0x52697465});
      Store(pair.first, 0x4B8, faith_id);
      Store(pair.first, 0x4BC, std::uint32_t{0xFFFFFFFF});
      Store(pair.first, 0x4C0, std::uint32_t{0xFFFFFFFF});
    }
    Put(faith, 8, faith_id); Put(faith, 0x8C, religion_id); Put(faith, 0x98, main_id);
    NativeString(faith.data(), 0xE0, "fixture_faith");
    Collection(faith, 0x890, holy_ids); Collection(faith_rites, 0, rite_ids);
    Put(faith_storage, 0x20, faith_slots.data()); Put(faith_storage, 0x2C, std::int32_t{3});
    Put(faith_slots, 0x10 + 8, faith.data());
    Collection(data, 0xD598, world_faiths);
    Put(native_religion, 8, religion_id); Put(native_religion, 0x20, religion_definition.data());
    NativeString(religion_definition.data(), 0x18, "fixture_religion");
    Put(title, 0x10, title_id); Put(title, 0x308, target_id);
    Put(title_storage, 0x20, title_slots.data()); Put(title_storage, 0x2C, std::int32_t{3});
    Put(title_slots, 0x10 + 8, title.data());
    Put(holy_site, 0x10, holy_id); Put(holy_site, 0xB0, title_id);
    Put(holy_storage, 0x20, holy_slots.data()); Put(holy_storage, 0x2C, std::int32_t{3});
    Put(holy_slots, 0x10 + 8, holy_site.data());
    NativeString(group_a.data(), 0x18, "group_a"); NativeString(group_b.data(), 0x18, "group_b");
    NativeString(doctrine_a.data(), 0x18, "custom_a"); NativeString(doctrine_b.data(), 0x18, "custom_b");
    Put(doctrine_a, 0xB08, group_a.data()); Put(doctrine_b, 0xB08, group_b.data());
    Collection(doctrine_database, 0x50, doctrine_rows);
    NativeString(tenet.data(), 0x18, "tenet_confession");
    Put(tenet, 0x38, std::uint32_t{0x4744624F});
    Collection(extension, 0x88, tenets); Collection(tenet_database, 0xEF0, tenets);
    Collection(tenet, 0x740, owned_tokens); Collection(tenet_database, 0xF20, supported_tokens);
    NativeString(token_true.data(), 0, "flag_true"); NativeString(token_false.data(), 0, "flag_false");
    Put(rite, 0x7DC, std::int32_t{-1}); Put(rite, 0x7E0, std::int64_t{5'000});
    Put(rite, 0x7E8, std::int64_t{0}); Put(rite, 0x7F0, std::int32_t{0});
    Put(rite, 0x7F8, std::int64_t{-500'000});
    Put(main_rite, 0x7DC, std::int32_t{45}); Put(main_rite, 0x7E0, std::int64_t{10'000});
    Put(main_rite, 0x7E8, std::int64_t{50'000}); Put(main_rite, 0x7F0, std::int32_t{1});
    Put(main_rite, 0x7F8, std::int64_t{500'000});
    NativeString(fulfillment_type.data(), 0x18, "fulfillment_a");
    Put(fulfillment_type, 0x58, fulfillment_levels.data());
    Put(fulfillment_type, 0x64, std::int32_t{2});
    for (std::int32_t index = 0; index < 2; ++index) {
      const auto offset = static_cast<std::size_t>(index) * 0x218;
      Put(fulfillment_levels, offset + 0x1E0, static_cast<std::int64_t>(index) * 500'000);
      Put(fulfillment_levels, offset + 0x1E8, static_cast<std::int64_t>(index + 1) * 500'000);
      Put(fulfillment_levels, offset + 0x210, index);
    }
    Collection(threshold_vector, 0, thresholds);
    NativeString(communion.data(), 0x18, "hold_mystical_communion_decision");
    NativeString(confession.data(), 0x18, "pam_decision_confession");
    NativeString(vow.data(), 0x18, "take_vow_of_poverty_decision");
    Put(activity_type, 0, std::uintptr_t{image_base + 0x1000});
    NativeString(activity_type.data(), 0x18, "activity_pilgrimage");
    Put(activity_type, 0x3BC0, std::int32_t{5});
    activity_type[0x3BED] = std::byte{1};
    Put(phase_definition, 8, std::int32_t{17});
    Put(phase_definition, 0x698, std::int32_t{1});
    phase_definition[0x69C] = std::byte{1};
    Collection(activity_database, 0x50, activity_types);
    Put(province, 0x10, province_id); Put(province, 0x85C, std::uint32_t{0x50726F76});
    Put(start_province, 0x10, std::int32_t{71}); Put(start_province, 0x85C, std::uint32_t{0x50726F76});
    provinces[71] = start_province.data(); provinces[province_id] = province.data();
    Collection(data, 0x140, provinces);
    Put(lease_contract, 0x68 + 0x2F8, std::int64_t{75'000});
    Collection(character, 0xF8, traits);
    Put(virtue_record, 0x18, std::int64_t{20'000}); Put(virtue_record, 0x20, std::int64_t{100'000});
    Put(sin_record, 0x18, std::int64_t{-25'000}); Put(sin_record, 0x20, std::int64_t{150'000});
    Put(atom_pool, 0x10, flag_rows.data()); Put(atom_pool, 0x1C, std::int32_t{3});
    Put(flags, 0x10, flag_rows.data()); Put(flags, 0x1C, std::int32_t{2});
    Put(flags, 0x28, std::int32_t{100});
    Put(flag_rows, 8, std::uint32_t{2}); Put(flag_rows, 0xC, std::int32_t{-1});
    Put(flag_rows, 0x20 + 8, std::uint32_t{3}); Put(flag_rows, 0x20 + 0xC, std::int32_t{115});
  }
};
World *world = nullptr;
void RecordCallback(const char *name, int line, const char *predicate,
    std::initializer_list<bool> receiver_arguments) {
  const bool receiver_ok = receiver_arguments.size() == 0 || *receiver_arguments.begin();
  const auto actual_thread = GetCurrentThreadId();
  const bool owner_thread_matches = actual_thread == world->owner;
  ++world->callbacks;
  world->callback_scope_valid &= owner_thread_matches && receiver_ok;
  if ((!owner_thread_matches || !receiver_ok) && !world->callback_failure_reported) {
    world->callback_failure_reported = true;
    std::cerr << "synthetic_callback_scope_failure scene=" << world->callback_scene
        << " callback=" << name << " source_line=" << line
        << " receiver_predicate=" << predicate << " receiver_ok=" << receiver_ok
        << " owner_thread_matches=" << owner_thread_matches
        << " actual_thread=" << actual_thread << " owner_thread=" << world->owner << '\n';
  }
}
#define Callback(...) RecordCallback(__func__, __LINE__, #__VA_ARGS__, {__VA_ARGS__})
void *Player(void *owner) { Callback(owner == world->jomini.data()); return world->player.data(); }
void *CharacterRite(void *actor) { Callback(actor == world->character.data()); return world->rite.data(); }
void *CharacterFaith(void *actor) { Callback(actor == world->character.data()); return world->faith.data(); }
void *RiteFaith(void *rite) {
  Callback(rite == world->rite.data() || rite == world->main_rite.data() || rite == world->target_rite.data());
  return world->faith.data();
}
void *FaithReligion(void *faith) { Callback(faith == world->faith.data()); return world->native_religion.data(); }
void *FaithMainRite(void *faith) { Callback(faith == world->faith.data()); return world->main_rite.data(); }
const void *FaithKey(void *faith) { Callback(faith == world->faith.data()); return world->faith.data() + 0xE0; }
std::int64_t *Fervor(void *faith, std::int64_t *out) { Callback(faith == world->faith.data()); *out = 6'250'000; return out; }
std::int64_t *Fulfillment(void *actor, std::int64_t *out) { Callback(actor == world->character.data()); *out = 125'000; return out; }
actual::CoreBindings Core(World &w) { return {true, &w.state_ptr, &w.jomini_ptr, &w.character_storage_ptr, &Player}; }
fourth::ContextBindings Context(World &w) {
  auto b = fourth::BindReligionContextImage12004(World::image_base, actual::kExecutableSha256);
  b.core = Core(w); b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion; b.faith_main_rite = &FaithMainRite;
  b.faith_fervor = &Fervor; b.character_spiritual_fulfillment = &Fulfillment; b.faith_tag = &FaithKey;
  return b;
}
std::uint8_t RiteHostility(void *component, void *source, void *target) {
  Callback(component == static_cast<std::byte *>(source) + 0x750 &&
      ((source == world->rite.data() && target == world->target_rite.data()) ||
       (source == world->target_rite.data() && target == world->rite.data())));
  return source == world->rite.data() ? 0 : 2;
}
std::uint8_t FaithHostility(void *source, void *target, bool offset) {
  Callback(source == world->faith.data() && target == world->faith.data() && !offset); return 0;
}
std::int64_t *FinalThreshold(const void *faith, std::int64_t *out) {
  Callback(faith == world->faith.data()); *out = 7'000'000; return out;
}
const void *OwnedTenets(const void *actor) { Callback(actor == world->character.data()); return world->extension.data() + 0x88; }
bool ParameterMember(const void *set, const std::int32_t *token) {
  Callback((set == world->tenet_database.data() + 0xF20 ||
      set == world->tenet.data() + 0x740) && token != nullptr);
  const auto *items = Load<const std::int32_t *>(set);
  const auto count = Load<std::int32_t>(set, 0xC);
  return std::find(items, items + count, *token) != items + count;
}
const void *TokenKey(std::int32_t token) {
  Callback(token == 700 || token == 701); return token == 700 ? world->token_true.data() : world->token_false.data();
}
void *FulfillmentType(void *database, void *actor) {
  Callback(database == world->fulfillment_database.data() && actor == world->character.data()); return world->fulfillment_type.data();
}
void *FulfillmentLevel(void *type, std::int64_t raw) {
  Callback(type == world->fulfillment_type.data() && raw == 125'000); return world->fulfillment_levels.data();
}
std::int64_t *FulfillmentProgress(std::int64_t *out, std::int64_t raw, std::int64_t lower, std::int64_t upper) {
  Callback(raw == 125'000 && lower == 0 && upper == 500'000); *out = 2'500'000; return out;
}
void *RootConstruct(void *root) { Callback(); return root; }
void Destroy(void *) { Callback(); }
std::uint32_t DecisionHash(void *database, const char *text, std::uint32_t length) {
  Callback(database == world->decision_database.data());
  const std::string_view key{text, length};
  return key == third::mystical_communion::kDecisionId ? 1 : key == third::confession::kDecisionId ? 2 : 3;
}
const void *DecisionLookup(void *database, std::uint32_t hash) {
  Callback(database == world->decision_database.data() && hash >= 1 && hash <= 3);
  return hash == 1 ? world->communion.data() : hash == 2 ? world->confession.data() : world->vow.data();
}
bool DecisionShown(const void *definition, void *actor) { Callback(actor == world->character.data() && definition != nullptr); return true; }
bool DecisionCanTake(const void *definition, void *actor, void *root, const void *unused, void *reason) {
  Callback(actor == world->character.data() && Load<std::int64_t>(root, 8) == World::actor_id && unused == nullptr);
  const bool allowed = definition != world->confession.data();
  NativeString(reason, 0, allowed ? "" : "not_ready"); return allowed;
}
const void *DecisionCost(const void *definition) { Callback(definition != nullptr); return world->cost.data(); }
void DecisionCostEvaluate(const void *cost, void *root, std::int64_t *out) {
  Callback(cost == world->cost.data() && Load<std::int64_t>(root, 8) == World::actor_id);
  std::fill_n(out, 10, std::int64_t{0}); out[2] = 100'000; out[6] = 50'000;
}
bool DecisionAffordable(const void *cost, void *root, void *actor, void *unused) {
  Callback(cost == world->cost.data() && Load<std::int64_t>(root, 8) == World::actor_id && actor == world->character.data() && unused == nullptr); return true;
}
std::uint8_t ConfessionState(void *rite, const void *definition) {
  Callback(rite == world->rite.data() && definition == world->tenet.data()); return 2;
}
std::int64_t *ChurchIncome(std::int64_t *out, void *actor, bool first, bool second, void *tooltip) {
  Callback(actor == world->character.data() && !first && tooltip == nullptr); *out = second ? 250'000 : 0; return out;
}
void *IncomeContext(void *actor) { Callback(actor == world->character.data()); return actor; }
void *FaithLease(void *faith) { Callback(faith == world->faith.data()); return world->lease_contract.data(); }
std::int32_t *LeaseLiege(void *manager, std::int32_t *out, std::int32_t lessee) {
  Callback(manager == world->data.data() + 0x1F1E0 && lessee == World::actor_id); *out = -1; return out;
}
std::int32_t *TopLease(std::int32_t *out, std::int32_t lessee) { Callback(lessee == World::actor_id); *out = lessee; return out; }
std::int64_t *PriorShare(void *rule, std::int64_t *out, void *scope, std::int64_t, std::int64_t,
    std::int32_t lessee, std::int32_t, std::int64_t, const void *, void *tooltip) {
  Callback(rule == world->lease_contract.data() + 0x68 && lessee == World::actor_id && tooltip == nullptr);
  *out = scope == static_cast<std::byte *>(rule) + 0x108 ? 0 : 20'000; return out;
}
std::int64_t *RulerShare(void *rule, std::int64_t *out, void *ruler, std::int32_t lessee, bool detail, std::int64_t remaining, void *tooltip) {
  Callback(rule == world->lease_contract.data() + 0x68 && ruler == world->character.data() && lessee == World::actor_id && !detail && remaining == 80'000 && tooltip == nullptr);
  *out = 30'000; return out;
}
third::church_tax_inputs::NativeString32 *IncomeRules(void *rule, third::church_tax_inputs::NativeString32 *out, void *ruler, void *lessee) {
  Callback(rule == world->lease_contract.data() + 0x68 && ruler == world->character.data() && lessee == ruler);
  NativeString(out, 0, "tax_rules"); return out;
}
void TaxStringDestroy(third::church_tax_inputs::NativeString32 *) { Callback(); }
std::int32_t DevotionLevel(void *actor) { Callback(actor == world->character.data()); return 0; }
std::int64_t *DevotionPercent(std::int64_t *out, void *actor) { Callback(actor == world->character.data()); *out = 0; return out; }
std::int32_t DevotionCap(religion::devotion_profile12003::PlayerValueItemScope *) { Callback(); return 2; }
void DevotionThreshold(religion::devotion_profile12003::PlayerValueItemScope *, std::int64_t *numerator, std::int64_t *denominator) {
  Callback(); *numerator = 0; *denominator = 500'000;
}
const void *DevotionVector(religion::devotion_profile12003::PlayerValueItemScope *) { Callback(); return world->threshold_vector.data(); }
void *TraitDatabase() { Callback(); return world->trait_database.data(); }
void *TraitLookup(void *database, std::int32_t id) {
  Callback(database == world->trait_database.data() && id >= 10 && id <= 12);
  return id == 10 ? world->trait_a.data() : id == 11 ? world->trait_b.data() : world->trait_c.data();
}
std::int32_t TraitClassification(void *trait, void *map, void **record) {
  Callback(map == world->rite.data() + 0x950);
  *record = trait == world->trait_a.data() ? world->virtue_record.data() : trait == world->trait_b.data() ? world->sin_record.data() : nullptr;
  return trait == world->trait_a.data() ? 1 : trait == world->trait_b.data() ? 2 : 0;
}

bool CanPlan(const void *type, void *actor) {
  Callback(type == world->activity_type.data() && actor == world->character.data()); return true;
}
void *CanPlanTooltip(void *out, const void *type, void *actor) {
  Callback(type == world->activity_type.data() && actor == world->character.data()); NativeString(out, 0, "can_plan"); return out;
}
void ReleaseArray(const void *, void *data, std::size_t alignment) {
  Callback(alignment == 8); delete[] static_cast<const void **>(data);
}
void FilterProvinces(const void *filter, void *actor, factory::NativeArray *out) {
  Callback(filter == world->activity_type.data() + 0x3BC0 && actor == world->character.data());
  out->data = new const void *[1]{world->province.data()}; out->capacity = out->count = 1;
}
void *ActorRootConstruct(void *root, const std::int32_t *id) {
  Callback(*id == World::actor_id); Store(root, 0, std::int32_t{4}); Store(root, 8, static_cast<std::uint64_t>(*id)); return root;
}
void NamedScope(void *, std::int32_t token, const factory::ScopeToken *value) {
  Callback(token >= 1 && token <= 3 && value != nullptr);
}
bool Predicate(const void *definition, void *) { Callback(definition != nullptr); return true; }
bool PredicateWithEvaluator(const void *definition, void *, void *evaluator) {
  Callback(definition != nullptr && evaluator != nullptr); return true;
}
void *Allocate(std::size_t bytes) { Callback(bytes == 0xD8); return new std::byte[bytes]{}; }
void Deallocate(void *data, std::size_t bytes) { Callback(bytes == 0xD8); delete[] static_cast<std::byte *>(data); }
void *EvaluatorConstruct(void *storage) { Callback(storage != nullptr); return storage; }
void EvaluatorFormat(void **evaluator, const void *, void *reason) {
  Callback(*evaluator != nullptr); NativeString(reason, 0, "route_ready");
}
std::int32_t PhaseCap(const void *type, void *) { Callback(type == world->activity_type.data()); return 2; }
void PhaseOffers(const factory::PhaseContext *context, std::int32_t filter, const void *province, factory::NativeArray *out) {
  Callback(context->activity_type == world->activity_type.data() && context->actual_actor == world->character.data() && filter == 1 && province == world->province.data());
  out->data = nullptr; out->capacity = out->count = 0; // Native fixed default-only branch.
}
void *ConfigInitialize(void *config, const void *type, std::int32_t actor) {
  Callback(type == world->activity_type.data() && actor == World::actor_id);
  auto *row = new std::byte[factory::PhaseRowView::stride]{};
  Store(row, 0, world->phase_definition.data()); Store(row, 8, std::int32_t{-1});
  Store(config, 0x20, World::date); Store(config, 0xB0, row);
  Store(config, 0xB8, std::int32_t{1}); Store(config, 0xBC, std::int32_t{1}); return config;
}
const void *SelectedSpecial(const void *) { Callback(); return nullptr; }
void *PhaseInsert(void *array, std::int32_t index, const void *type) {
  Callback(index == 0 && type == world->activity_type.data()); return Load<void *>(array);
}
void ConfigNormalize(void *) { Callback(); }
void ConfigDestroy(void *config) { Callback(); delete[] Load<std::byte *>(config, 0xB0); }
void ActivityCost(const void *, std::int64_t *out) {
  Callback(); std::fill_n(out, 10, std::int64_t{0}); out[0] = 100'000; out[6] = 50'000;
}
bool ActivityAffordable(const std::int64_t *cost, void *actor, void *reason) {
  Callback(cost[0] == 100'000 && actor == world->character.data()); NativeString(reason, 0, ""); return true;
}
void *ArrayInitialize(void *array) {
  Callback(); Store(array, 0, static_cast<void *>(nullptr)); Store(array, 8, std::int32_t{0}); Store(array, 0xC, std::int32_t{0}); return array;
}
void ProvinceAppend(void *array, std::int32_t index, const std::int32_t *begin, const std::int32_t *end) {
  Callback(index == 0 && end == begin + 1 && *begin == World::province_id);
  Store(array, 0, new std::int32_t{*begin}); Store(array, 8, std::int32_t{1}); Store(array, 0xC, std::int32_t{1});
}
void CreationInputDestroy(void *input) { Callback(); delete Load<std::int32_t *>(input, 0x20); }
void *TravelConstruct(void *out, const void *input) {
  Callback(Load<std::int32_t>(input) == World::actor_id && Load<std::int32_t>(input, 0x2C) == 1 &&
      *Load<const std::int32_t *>(input, 0x20) == World::province_id);
  Store(world->route_row.data(), 8, world->province.data());
  Store(out, 8, World::actor_id); Store(out, 0x360, world->route_row.data());
  Store(out, 0x36C, std::int32_t{1}); Store(out, 0x83C, std::int32_t{0}); return out;
}
const void *TravelStart(const void *) { Callback(); return world->start_province.data(); }
bool EvaluateRoute(void *) { Callback(); return true; }
void EvaluateArrival(void *data) {
  Callback(Load<const void *>(data, 0x360) == world->route_row.data());
  Put(world->route_row, 0x38, World::date + 12);
}

template <class DecisionBindings> void DecisionCallbacks(DecisionBindings &b, World &w) {
  b.decision_database = &w.decision_database_ptr; b.decision_fallback = &w.decision_fallback_ptr;
  b.decision_hash = &DecisionHash; b.decision_lookup = &DecisionLookup;
  b.root_construct = &RootConstruct; b.root_destroy = &Destroy;
  b.decision_shown = &DecisionShown; b.decision_can_take = &DecisionCanTake;
  b.decision_cost = &DecisionCost; b.cost_evaluate = &DecisionCostEvaluate;
  b.cost_affordable = &DecisionAffordable; b.reason_destroy = &Destroy;
}
old::ProvinceBindings Provinces(World &w) {
  old::ProvinceBindings b{}; b.enabled = true; b.game_state_slot = &w.state_ptr; return b;
}
fourth::ContextAddonBindings Addons(World &w) {
  auto b = fourth::BindReligionContextAddonsImage12004(World::image_base, actual::kExecutableSha256);
  auto &progress = b.progress_bindings;
  progress.database_slot = &w.fulfillment_database_ptr;
  progress.type_for_character = &FulfillmentType; progress.level_for_value = &FulfillmentLevel;
  progress.progress_within_level = &FulfillmentProgress; progress.minimum = &w.minimum; progress.maximum = &w.maximum;
  DecisionCallbacks(b.mystical_communion_bindings, w); DecisionCallbacks(b.confession_bindings, w);
  DecisionCallbacks(b.vow_of_poverty_bindings, w);
  auto &type = b.pilgrimage_bindings;
  type.activity_type_database = &w.activity_database_ptr;
  type.activity_type_vtable = Load<std::uintptr_t>(w.activity_type.data());
  type.can_plan = &CanPlan; type.can_plan_tooltip = &CanPlanTooltip; type.reason_destroy = &Destroy;
  auto &activity = b.pilgrimage_activity_bindings;
  activity.activity_type = type; activity.config_initialize = &ConfigInitialize;
  activity.selected_special = &SelectedSpecial; activity.phase_insert = &PhaseInsert;
  activity.config_normalize = &ConfigNormalize; activity.activity_cost = &ActivityCost;
  activity.activity_affordable = &ActivityAffordable; activity.config_destroy = &ConfigDestroy; activity.reason_destroy = &Destroy;
  auto &c = activity.candidates;
  c.provinces = Provinces(w); c.character_rite = &CharacterRite; c.rite_faith = &RiteFaith;
  c.holy_site_storage = &w.holy_storage_ptr; c.title_storage = &w.title_storage_ptr;
  w.allocator_vtable[2] = reinterpret_cast<std::uintptr_t>(&ReleaseArray);
  c.province_array_allocator = c.phase_choice_allocator = &w.allocator_vtable_pointer;
  c.filter_provinces = &FilterProvinces; c.root_construct = &RootConstruct;
  c.actor_root_construct = &ActorRootConstruct; c.root_destroy = &Destroy; c.named_scope_save = &NamedScope;
  c.host_token = &w.host_token; c.special_token = &w.special_token; c.location_token = &w.location_token;
  c.predicate = &Predicate; c.predicate_with_evaluator = &PredicateWithEvaluator;
  c.allocate = &Allocate; c.deallocate = &Deallocate; c.evaluator_construct = &EvaluatorConstruct;
  c.evaluator_prepare_first = c.evaluator_prepare_second = c.evaluator_destroy = c.reason_destroy = &Destroy;
  c.evaluator_format = &EvaluatorFormat; c.total_phase_cap = c.same_province_phase_cap = &PhaseCap;
  c.phase_offers = &PhaseOffers;
  auto &route = b.pilgrimage_route_bindings;
  route.provinces = Provinces(w);
  route.participant_allocator = route.travel_option_allocator = route.descriptor_allocator = &w.allocator_vtable_pointer;
  route.native_default_date = &w.default_date; route.province_ids_initialize = route.waypoints_initialize = &ArrayInitialize;
  route.province_ids_append = &ProvinceAppend; route.root_construct = &RootConstruct;
  route.creation_input_destroy = &CreationInputDestroy; route.data_destroy = &Destroy; route.data_construct = &TravelConstruct;
  route.start_province = &TravelStart; route.evaluate_route = &EvaluateRoute; route.evaluate_arrival = &EvaluateArrival;
  b.confession_permission_bindings.tenet_database_global = &w.tenet_database_ptr;
  b.confession_permission_bindings.source_main_rite_status = &ConfessionState;
  b.church_income_bindings.monthly_income = &ChurchIncome;
  auto &tax = b.church_tax_bindings;
  tax.core = Core(w); tax.game_state_slot = &w.state_ptr;
  tax.income_context = &IncomeContext; tax.character_faith = &CharacterFaith; tax.faith_lease_contract = &FaithLease;
  tax.lease_liege = &LeaseLiege; tax.top_lease_liege_direct = &TopLease;
  tax.prior_share = &PriorShare; tax.ruler_share = &RulerShare;
  tax.income_rules = &IncomeRules; tax.string_destroy = &TaxStringDestroy;
  tax.lease_liege_label = "lease"; tax.top_lease_liege_direct_label = "top_lease";
  auto &devotion = b.devotion_bindings;
  devotion.effective_level = &DevotionLevel; devotion.progress_percent = &DevotionPercent;
  devotion.effective_cap = &DevotionCap; devotion.threshold_progress = &DevotionThreshold; devotion.threshold_vector = &DevotionVector;
  auto &virtue = b.rite_virtue_sin_bindings;
  virtue.trait_database = &TraitDatabase; virtue.trait_lookup = &TraitLookup;
  virtue.character_rite = &CharacterRite; virtue.trait_classification = &TraitClassification;
  return b;
}

const void *FaithRites(void *faith) { Callback(faith == world->faith.data()); return world->faith_rites.data(); }
bool FaithRule(void *actor, std::uint32_t faith, void *tooltip) {
  Callback(actor == world->character.data() && faith == World::faith_id && tooltip == nullptr); return false;
}
bool ValidateConversion(const old::religion_conversion_rite::FaithAndRiteConversionCommand *command, void *reason) {
  const auto actual_value = fourth::MakeReadOnlyConvertRiteValue12004(
      World::image_base, World::actor_id, World::target_id, command->pay_piety != 0);
  Callback(command->actor_id == World::actor_id && command->target_rite_id == World::target_id &&
      command->primary_vtable == actual_value.primary_vtable && command->secondary_vtable == actual_value.secondary_vtable &&
      command->pay_piety <= 1);
  if (reason) NativeString(reason, 0, command->pay_piety ? "" : "pay_piety");
  return command->pay_piety != 0;
}
std::int32_t FinalPietyCost(const religion::conversion_cost::NativeCostCommand *command, void *tooltip) {
  Callback(command->actor_id == World::actor_id && command->target_rite_id == World::target_id && tooltip == nullptr);
  return 0;
}
void ReasonStringDestroy(old::religion_conversion::reasons::NativeReasonString *) { Callback(); }
void *TopLiege(void *actor) { Callback(actor == world->character.data()); return actor; }
void *PrimaryTitle(void *actor) { Callback(actor == world->character.data()); return world->title.data(); }
void *TitleStateRite(void *title) { Callback(title == world->title.data()); return world->target_rite.data(); }
std::int64_t *Knowledge(std::int64_t *out, void *actor, void *rite) {
  Callback(actor == world->character.data() && rite == world->target_rite.data()); *out = 0; return out;
}
std::uint32_t *ExistingAtom(void *pool, std::uint32_t *out, const religion::conversion_gates::NativeStringView *view) {
  Callback(pool == world->atom_pool.data() && view != nullptr);
  const std::string_view key{Load<const char *>(view)};
  *out = key == "faith_conversion_recently_converted" ? 1U : key == "conversion_memory_recently_created" ? 2U : 3U;
  return out;
}
void *FlagCollection(void *resources) { Callback(resources == world->resources.data()); return world->flags.data(); }
std::int64_t *BaseFulfillment(std::int64_t *out, void *actor, void *rite) {
  Callback(actor == world->character.data() && rite == world->target_rite.data()); *out = -50'000; return out;
}
bool ReadMemory(void *context, std::uintptr_t address, void *out, std::size_t bytes) noexcept {
  auto &w = *static_cast<World *>(context);
  const auto in = [&](const auto &buffer) {
    const auto base = reinterpret_cast<std::uintptr_t>(buffer.data());
    return address >= base && address - base <= buffer.size() && bytes <= buffer.size() - (address - base);
  };
  const bool valid = in(w.character) || in(w.resources);
  Callback(valid); if (!valid) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), bytes); return true;
}
fourth::ConversionBindings Conversion(World &w) {
  auto b = fourth::BindReligionConversionImage12004(World::image_base, actual::kExecutableSha256);
  b.rite.core = Core(w); b.rite.rite_storage_slot = &w.rite_storage_ptr;
  b.rite.validate = &ValidateConversion; b.rite.character_faith = &CharacterFaith; b.rite.faith_rites = &FaithRites;
  b.rite.read_only_value_factory = &fourth::MakeReadOnlyConvertRiteValue12004;
  b.faith.core = Core(w); b.faith.faith_storage_slot = &w.faith_storage_ptr;
  b.faith.character_faith = &CharacterFaith; b.faith.faith_main_rite = &FaithMainRite;
  b.faith.rite_faith = &RiteFaith; b.faith.faith_tag = &FaithKey; b.faith.conversion_rule = &FaithRule;
  b.cost.core = Core(w); b.cost.rite_database = &w.rite_storage_ptr;
  b.cost.character_rite = &CharacterRite; b.cost.character_faith = &CharacterFaith;
  b.cost.rite_faith = &RiteFaith; b.cost.final_piety_cost = &FinalPietyCost;
  b.terms.rite = b.rite; b.terms.cost = b.cost;
  b.reasons.rite = b.rite; b.reasons.destroy_string = &ReasonStringDestroy;
  auto &g = b.gates;
  g.state.context = Context(w); g.state.character_top_liege = &TopLiege;
  g.state.character_primary_title = &PrimaryTitle; g.state.title_state_rite = &TitleStateRite;
  g.rite_storage_slot = &w.rite_storage_ptr; g.rite_knowledge = &Knowledge;
  g.existing_atom = &ExistingAtom; g.atom_pool = w.atom_pool.data(); g.character_flag_collection = &FlagCollection;
  b.prediction.core = Core(w); b.prediction.rite_storage_slot = &w.rite_storage_ptr; b.prediction.base_fulfillment = &BaseFulfillment;
  b.outcome.actor.current_religion = Context(w); b.outcome.actor.read_memory = &ReadMemory; b.outcome.actor.memory_context = &w;
  auto &s = b.outcome.state;
  s.core = Core(w); s.rite_storage_slot = &w.rite_storage_ptr; s.rite_knowledge = &Knowledge;
  s.existing_atom = &ExistingAtom; s.atom_pool = w.atom_pool.data(); s.character_flag_collection = &FlagCollection;
  s.character_spiritual_fulfillment = &Fulfillment;
  return b;
}

// Exercise production Enter/FinishQueryMailbox with an admitted executing slot
// and owned current-thread stamp. This fixture does not claim SDL/game pumping.
template <class Query, class Serialize>
std::string Whole(World &w, const game::GameAdapter &adapter, const game::Snapshot &snapshot,
    Query &query, api::MainThreadQueryExecutorV1 execute, Serialize serialize, const char *request_id) {
  api::MainThreadQueryMailboxV1 mailbox{};
  auto &envelope = query.envelope;
  envelope.game = &adapter; envelope.mailbox = &mailbox;
  envelope.expected_snapshot = snapshot; envelope.expected_snapshot_revision = World::revision;
  envelope.snapshot_comparison = old::QuerySnapshotComparison12002::core_frame;
  envelope.typed_context = &query; envelope.ticket.sequence = 1;
  mailbox.state.store(api::MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(1); mailbox.owner_thread_id.store(w.owner);
  mailbox.executor = execute; mailbox.executor_context = &envelope;
  Bytes<0x28> tls{}; tls[0x20] = std::byte{1};
  api::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = World::epoch; stamp.thread_id = w.owner;
  stamp.tls_initialized = stamp.tls_main_thread_marker = 1;
  stamp.tls_context = reinterpret_cast<std::uintptr_t>(tls.data());
  stamp.jomini_state = reinterpret_cast<std::uintptr_t>(w.jomini.data());
  stamp.game_state = reinterpret_cast<std::uintptr_t>(w.state.data());
  stamp.date_raw = World::date; stamp.paused = true;
  const auto before = w.callbacks;
  w.callback_scene = request_id;
  Require(execute(&envelope, stamp) && query.completed && envelope.frame_stable && query.failure.empty(),
      "production whole owner mailbox completes on the actual4 current frame");
  Require(w.callback_scope_valid && w.callbacks > before,
      "typed synthetic native callbacks consumed current owner-scoped pointers");
  auto result = game::Render12004BuildIdentity(serialize(query, request_id), adapter.descriptor());
  Require(!result.empty() && result.find("\"type\":\"command_result\"") != std::string::npos &&
      result.find("\"status\":\"observed\"") != std::string::npos &&
      result.find("\"snapshot_revision\":171") != std::string::npos &&
      result.find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
      result.find(actual::kExecutableSha256) != std::string::npos,
      "fresh whole production serialization has current actual4 build identity");
  return result;
}

void InstallAddons(old::PlayerReligionMailboxContext12002 &q, const fourth::ContextAddonBindings &b) {
  q.progress_bindings = b.progress_bindings;
  q.mystical_communion_bindings = b.mystical_communion_bindings;
  q.pilgrimage_bindings = b.pilgrimage_bindings;
  q.pilgrimage_activity_bindings = b.pilgrimage_activity_bindings;
  q.pilgrimage_route_bindings = b.pilgrimage_route_bindings;
  q.confession_bindings = b.confession_bindings;
  q.confession_permission_bindings = b.confession_permission_bindings;
  q.church_income_bindings = b.church_income_bindings;
  q.church_tax_bindings = b.church_tax_bindings;
  q.devotion_bindings = b.devotion_bindings;
  q.rite_virtue_sin_bindings = b.rite_virtue_sin_bindings;
  q.vow_of_poverty_bindings = b.vow_of_poverty_bindings;
}

std::vector<std::string> Produce(World &w, const game::GameAdapter &adapter, const game::Snapshot &snapshot) {
  std::vector<std::string> samples;
  auto context = Context(w);
  auto addons = Addons(w);
  auto conversion = Conversion(w);
  old::PlayerReligionMailboxContext12002 q_context{};
  q_context.bindings = context; InstallAddons(q_context, addons);
  samples.push_back(Whole(w, adapter, snapshot, q_context, &old::ExecutePlayerReligionMailbox12002,
      &old::SerializePlayerReligionResult12002, "g2-read-religion-context-12004"));
  Require(q_context.observation.available && q_context.progress.available &&
      q_context.spiritual_fulfillment_type.available && q_context.mystical_communion_terms.available &&
      q_context.pilgrimage_terms.available && q_context.pilgrimage_activity_terms.available &&
      q_context.pilgrimage_candidate_routes.size() == 1 && q_context.pilgrimage_candidate_routes[0].available &&
      q_context.confession_terms.available && q_context.confession_rite_permission.available &&
      q_context.church_income_terms.available && q_context.church_tax_inputs.available &&
      q_context.devotion_profile.available && q_context.rite_virtue_sin_profile.available && q_context.vow_of_poverty_terms.available,
      "all thirteen adopted context sibling domains are genuinely observed");
  old::PlayerReligionHostilityMailboxContext12002 q_hostility{};
  q_hostility.bindings = fourth::BindHostilityImage12004(World::image_base, actual::kExecutableSha256);
  q_hostility.bindings.context = context; q_hostility.bindings.rite_storage_slot = &w.rite_storage_ptr;
  q_hostility.bindings.rite_hostility = &RiteHostility; q_hostility.bindings.faith_hostility = &FaithHostility;
  q_hostility.target_rite_id = World::target_id;
  samples.push_back(Whole(w, adapter, snapshot, q_hostility, &old::ExecutePlayerReligionHostilityMailbox12002,
      &old::SerializePlayerReligionHostilityResult12002, "g2-read-religion-hostility-12004"));
  old::PlayerReligionDoctrineCatalogueMailboxContext12002 q_catalogue{};
  q_catalogue.bindings = fourth::doctrine_catalogue::BindDoctrineCatalogueImage12004(World::image_base, actual::kExecutableSha256);
  q_catalogue.bindings.core = Core(w); q_catalogue.bindings.database_slot = &w.doctrine_database_ptr;
  samples.push_back(Whole(w, adapter, snapshot, q_catalogue, &old::ExecutePlayerReligionDoctrineCatalogueMailbox12002,
      &old::SerializePlayerReligionDoctrineCatalogueResult12002, "g2-read-religion-doctrine-catalogue-12004"));
  Require(q_catalogue.observation.catalogue_complete && q_catalogue.observation.rows.size() == 3 &&
      q_catalogue.observation.rows[0].doctrine_key == "custom_b" &&
      q_catalogue.observation.rows[1].doctrine_key == "custom_a" &&
      q_catalogue.observation.rows[2].doctrine_key == "custom_b",
      "current loaded mod catalogue retains original order and duplicate occurrences");
  old::PlayerReligionNumericSpecialParametersMailboxContext12002 q_numeric{};
  q_numeric.bindings = context;
  q_numeric.numeric_bindings = fourth::BindNumericSpecialParametersImage12004(World::image_base, actual::kExecutableSha256);
  q_numeric.final_bindings = fourth::BindFaithNumericFinalImage12004(World::image_base, actual::kExecutableSha256);
  q_numeric.final_bindings.faith_heresy_threshold = &FinalThreshold;
  q_numeric.final_bindings.heresy_threshold_define = &w.native_define;
  samples.push_back(Whole(w, adapter, snapshot, q_numeric, &old::ExecutePlayerReligionNumericSpecialParametersMailbox12002,
      &old::SerializePlayerReligionNumericSpecialParametersResult12002, "g2-read-religion-numeric-special-parameters-12004"));
  Require(q_numeric.final_observation.available && q_numeric.final_observation.final_heresy_threshold_raw == 7'000'000,
      "same-packet faith numeric final uses its independent native callback");
  old::PlayerReligionPersonalParametersMailboxContext12002 q_personal{};
  q_personal.bindings = context;
  q_personal.parameter_bindings = fourth::BindPersonalParametersImage12004(World::image_base, actual::kExecutableSha256);
  q_personal.parameter_bindings.database_slot = &w.tenet_database_ptr;
  q_personal.parameter_bindings.owned_tenets = &OwnedTenets;
  q_personal.parameter_bindings.contains_parameter = &ParameterMember; q_personal.parameter_bindings.parameter_key = &TokenKey;
  samples.push_back(Whole(w, adapter, snapshot, q_personal, &old::ExecutePlayerReligionPersonalParametersMailbox12002,
      &old::SerializePlayerReligionPersonalParametersResult12002, "g2-read-religion-personal-parameters-12004"));
  Require(q_personal.observation.parameters.size() == 2 && q_personal.observation.parameters[0].value &&
      !q_personal.observation.parameters[1].value, "native personal token membership preserves observed true and false");
  old::PlayerReligionConversionTermsMailboxContext12002 q_terms{};
  q_terms.bindings = conversion.terms; q_terms.target_rite_id = World::target_id;
  samples.push_back(Whole(w, adapter, snapshot, q_terms, &old::ExecutePlayerReligionConversionTermsMailbox12002,
      &old::SerializePlayerReligionConversionTermsResult12002, "g2-read-religion-conversion-terms-12004"));
  old::PlayerReligionConversionChoicesMailboxContext12002 q_choices{};
  q_choices.faith_bindings = conversion.faith; q_choices.rite_bindings = conversion.rite;
  samples.push_back(Whole(w, adapter, snapshot, q_choices, &old::ExecutePlayerReligionConversionChoicesMailbox12002,
      &old::SerializePlayerReligionConversionChoicesResult12002, "g2-read-religion-conversion-choices-12004"));
  Require(q_choices.observation.current_faith_rites.rite_ids == std::vector<std::uint32_t>(w.rite_ids.begin(), w.rite_ids.end()),
      "native full generation-bearing rite association order survives conversion choices");
  old::PlayerReligionConversionReasonsMailboxContext12002 q_reasons{};
  q_reasons.bindings = conversion.reasons; q_reasons.target_rite_id = World::target_id;
  samples.push_back(Whole(w, adapter, snapshot, q_reasons, &old::ExecutePlayerReligionConversionReasonsMailbox12002,
      &old::SerializePlayerReligionConversionReasonsResult12002, "g2-read-religion-conversion-reasons-12004"));
  old::PlayerReligionConversionInputsMailboxContext12002 q_inputs{};
  q_inputs.gates_bindings = conversion.gates; q_inputs.prediction_bindings = conversion.prediction; q_inputs.target_rite_id = World::target_id;
  samples.push_back(Whole(w, adapter, snapshot, q_inputs, &old::ExecutePlayerReligionConversionInputsMailbox12002,
      &old::SerializePlayerReligionConversionInputsResult12002, "g2-read-religion-conversion-inputs-12004"));
  old::PlayerReligionConversionOutcomeMailboxContext12002 q_outcome{};
  q_outcome.bindings = conversion.outcome; q_outcome.target_rite_id = World::target_id;
  samples.push_back(Whole(w, adapter, snapshot, q_outcome, &old::ExecutePlayerReligionConversionOutcomeMailbox12002,
      &old::SerializePlayerReligionConversionOutcomeResult12002, "g2-read-religion-conversion-outcome-12004"));
  Require(q_outcome.observation.actor.available && q_outcome.observation.state.available &&
      q_outcome.observation.actor.gold_raw == -200'000 && q_outcome.observation.actor.prestige_raw == 0 &&
      q_outcome.observation.state.target_rite_id == World::target_id,
      "independent conversion current state preserves signed resources, zero and full target ID");
  return samples;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: EXE ABSOLUTE_NEW_DIR/ck3_12004_religion_adopted_addons_native.json");
    const std::filesystem::path output_path{argv[1]};
    Require(output_path.is_absolute(), "native fixture output is an explicit absolute new artifact path");
    World memory{}; world = &memory;
    auto adapter_bindings = game::BindCk3_12004AdapterImage(World::image_base, actual::kExecutableSha256);
    adapter_bindings.core = Core(memory);
    auto adapter = game::CreateCk3_12004AdapterFromBindings(std::move(adapter_bindings));
    Require(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
        "production actual4 adapter identifies the current synthetic world");
    game::Snapshot snapshot{};
    Require(game::ReadCk3_12002TimelineCoreSnapshot(*adapter, snapshot) && snapshot.paused &&
        snapshot.map_ready && snapshot.played_character_alive && snapshot.played_character_id == World::actor_id &&
        snapshot.date_raw == World::date, "actual4 Core produces the common current paused player frame");
    const auto samples = Produce(memory, *adapter, snapshot);
    Require(samples.size() == 10, "ten original complete command_result packets are produced");
    std::filesystem::create_directories(output_path.parent_path());
    std::ofstream output(output_path, std::ios::binary);
    output << "{\"fixture_provenance\":{\"kind\":\"synthetic_native_world_and_callbacks\","
        "\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"" << actual::kExecutableSha256 << "\","
        "\"actor_id\":29829,\"date_raw\":53286648,\"native_revision\":171,\"capture_epoch\":12004,"
        "\"target_rite_full_dword\":2248146947,\"producer\":\"production_owner_execute_and_whole_serializer\","
        "\"new_executable_bytes\":0,\"exe_branches_executed\":0,\"game_process_used\":false},\"samples\":[";
    for (std::size_t index = 0; index < samples.size(); ++index) {
      if (index) output << ',';
      output << samples[index]; // Original complete producer packet, unchanged.
    }
    output << "]}\n";
    Require(static_cast<bool>(output), "new native document writes all ten original whole packets");
    std::cout << "ten fresh actual4 whole religion addon packets written\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}

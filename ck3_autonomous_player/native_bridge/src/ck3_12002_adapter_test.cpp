#include "xar_bridge/ck3_12002_adapter.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
template <class T, class Buffer>
void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void *local_player = nullptr, *active_event = nullptr, *globals = nullptr;
void *province_pointer = nullptr;
void *GetPlayer(void *) { return local_player; }
void *GetEvent(void *) { return active_event; }
void *GetGlobals() { return globals; }
void *GetIdentifiers() { return globals; }
constexpr auto names = std::to_array<std::string_view>({
    "xa_settlement_ready", "xa_settlement_commit_serial",
    "xa_settlement_source_character", "xa_settlement_final_score",
    "xa_settlement_score_before_reject", "xa_settlement_record_candidate",
    "xa_settlement_old_record", "xa_settlement_record_delta",
    "xa_settlement_blessing_count", "xa_settlement_refusal_count",
    "xa_settlement_contract_progress", "xa_settlement_record_written"});
std::int32_t *Lookup(void *, std::int32_t *out, const void *view) {
  const auto text = Load<const char *>(view, 0);
  const auto size = Load<std::int32_t>(view, 8);
  *out = -1;
  for (std::size_t i = 0; i < names.size(); ++i)
    if (names[i] == std::string_view(text, static_cast<std::size_t>(size)))
      *out = static_cast<std::int32_t>(i);
  return out;
}
bool PendingFor(void *, void *) { return true; }
bool ValidateReply(void *) { return true; }
bool Contains(const void *side, std::int32_t id) {
  std::vector<std::int32_t> ids;
  assert(ck3_12002::ReadWarParticipantIds(side, ids));
  for (const auto item : ids) if (item == id) return true;
  return false;
}
std::int32_t WarScore(const void *, void *) { return 43; }
std::int32_t UnitState(void *) { return 7; }
void *TitleProvince(void *) { return province_pointer; }
bool Occupied(void *) { return false; }
std::int32_t Fort(void *) { return 6; }
std::int32_t Garrison(void *) { return 1234; }
std::int32_t Besiegers(void *) { return 0; }
std::int64_t *Fixed(void *, std::int64_t *out) { *out = 0; return out; }
std::int32_t Days(void *) { return 0; }

struct FixtureTable { std::array<std::uintptr_t, 9> slots{}; };
std::size_t queue_calls = 0, clone_calls = 0, delete_calls = 0;
std::int32_t last_instance = -1, last_choice = -1;
void *Delete(void *command, std::uint32_t flags) {
  assert(flags == 1);
  ++delete_calls;
  delete[] static_cast<std::byte *>(command);
  return nullptr;
}
void **Clone(const void *command, void **out) {
  ++clone_calls;
  auto *copy = new std::byte[0x28];
  std::memcpy(copy, command, 0x28);
  *out = copy;
  return out;
}
bool Queue(void *context, void **owned, std::uint32_t flags) {
  assert(context == &queue_calls && flags == 7);
  ++queue_calls;
  last_instance = Load<std::int32_t>(*owned, 0x20);
  last_choice = Load<std::int32_t>(*owned, 0x24);
  assert(ck3_12002::DestroyOwnedCommand(*owned));
  return true;
}

struct Scene {
  static constexpr std::int32_t player_id = 0x01000001;
  static constexpr std::int32_t spouse_id = 0x02000002;
  static constexpr std::int32_t enemy_id = 0x03000003;
  static constexpr std::int32_t unit_id = 0x04000000;
  static constexpr std::int32_t war_id = 0x05000000;
  static constexpr std::int32_t title_id = 0x06000000;
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> played_record{};
  std::array<void *, 1> played_records{played_record.data()};
  std::array<std::byte, 0x30> characters{}, pending_storage{}, units{}, wars{}, titles{}, sieges{};
  std::array<std::byte, 0x40> character_slots{};
  std::array<std::byte, 0x10> pending_slots{}, unit_slots{}, war_slots{}, title_slots{};
  std::array<std::byte, 0x1D8> played{}, spouse{}, enemy{};
  std::array<std::byte, 0x30> family{};
  std::array<std::byte, 0x300> living_extension{};
  std::array<std::int32_t, 1> spouse_ids{spouse_id};
  std::array<std::byte, 0x5C8> pending{};
  std::array<std::byte, 0x1C0> event{};
  std::array<std::byte, 0x1B0> event_definition{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x10> attacker{}, defender{};
  std::array<void *, 1> attackers{attacker.data()}, defenders{defender.data()};
  std::array<std::int32_t, 1> targeted_titles{title_id};
  std::array<std::byte, 0x120> title{};
  std::array<std::byte, 0x70> title_definition{};
  std::array<std::byte, 0x860> province{};
  std::array<void *, 4> provinces{nullptr, nullptr, nullptr, province.data()};
  std::array<std::byte, 0x20> global_container{};
  std::array<std::byte, 12 * 0x20> global_entries{};
  ck3_12002::SettlementGlobalAccessor accessor = GetGlobals;
  FixtureTable table{};
  void *state_slot = state.data(), *jomini_slot = jomini.data();
  void *character_slot = characters.data(), *pending_slot = pending_storage.data();
  void *unit_slot = units.data(), *siege_slot = sieges.data(), *title_slot = titles.data();

  Scene() {
    Put(state, 8, std::int32_t{53175816});
    Put(state, 0x70, std::int32_t{3});
    Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data());
    jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7});
    Put(player, 0x70, std::int32_t{7});
    Put(data, ck3_12002::kPlayerCharacterManagerOffset + 0x58, played_records.data());
    Put(data, ck3_12002::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(played_record, 0xB0, player_id);
    Put(played_record, 0xD8, std::int32_t{7});
    Storage(characters, character_slots, 4);
    Put(character_slots, 0x18, played.data());
    Put(character_slots, 0x28, spouse.data());
    Put(character_slots, 0x38, enemy.data());
    Put(played, 0x18, player_id); Put(spouse, 0x18, spouse_id); Put(enemy, 0x18, enemy_id);
    Put(played, 0x1A8, family.data());
    Put(played, 0x1B0, living_extension.data());
    Put(living_extension, 0x100, std::int64_t{12345000});
    Put(living_extension, 0x130, std::int64_t{54321000});
    Put(living_extension, 0x110, std::int64_t{-375000});
    Put(living_extension, 0x2F8, std::int32_t{65});
    Put(played, 0x1C8, played_record.data()); // Old death-layout decoy.
    Put(family, 0x10, std::int32_t{-1}); Put(family, 0x14, spouse_id);
    Put(family, 0x20, spouse_ids.data());
    Put(family, 0x28, std::int32_t{1}); Put(family, 0x2C, std::int32_t{1});
    Storage(pending_storage, pending_slots, 1); Put(pending_slots, 8, pending.data());
    Put(pending, 0x10, std::int32_t{0x07000000});
    Put(pending, 0x2F0, enemy_id); Put(pending, 0x300, player_id);
    Put(pending, 0x5C0, std::int32_t{1}); pending[0x5C6] = std::byte{1};
    Put(event, 0x1B0, event_definition.data()); Put(event, 0x1BC, std::int32_t{99});
    Put(event_definition, 0x1AC, std::int32_t{3});
    Storage(units, unit_slots, 1); Put(unit_slots, 8, unit.data());
    Put(unit, 0x10, unit_id); Put(unit, 0x20, province.data()); Put(unit, 0x174, player_id);
    Storage(wars, war_slots, 1); Put(war_slots, 8, war.data()); Put(war, 8, war_id);
    Put(data, ck3_12002::kWorldWarManagerOffset + 0x20, wars.data());
    Put(attacker, 8, player_id); Put(defender, 8, enemy_id);
    Put(war, 0x28, attackers.data()); Put(war, 0x30, std::int32_t{1}); Put(war, 0x34, std::int32_t{1});
    Put(war, 0x88, defenders.data()); Put(war, 0x90, std::int32_t{1}); Put(war, 0x94, std::int32_t{1});
    Put(war, 0x288, player_id); Put(war, 0x28C, enemy_id);
    Put(war, 0x270, targeted_titles.data()); Put(war, 0x278, std::int32_t{1}); Put(war, 0x27C, std::int32_t{1});
    Storage(titles, title_slots, 1); Put(title_slots, 8, title.data()); Put(title, 0x10, title_id);
    Put(title, 0x48, title_definition.data()); Put(title_definition, 0x64, std::int32_t{2});
    Put(data, 0x140, provinces.data()); Put(data, 0x14C, std::int32_t{4});
    Put(province, 0x10, std::int32_t{3}); Put(province, 0x85C, std::uint32_t{0x50726F76});
    Put(province, 0x788, std::int32_t{-1});
    Put(global_container, 0x10, global_entries.data()); Put(global_container, 0x1C, std::int32_t{12});
    const std::array<std::int64_t, 12> values{1, 17, 0, 7654321, 8765432, 76, 60, 16, 4, 2, 9, 1};
    for (std::size_t i = 0; i < names.size(); ++i) {
      const auto offset = i * 0x20;
      Put(global_entries, offset + 8, static_cast<std::int32_t>(i));
      Put(global_entries, offset + 0x10, std::uint16_t{1});
      Put(global_entries, offset + 0x18, values[i] * 100'000);
    }
    Put(global_entries, 2 * 0x20 + 0x10, std::uint16_t{4});
    Put(global_entries, 2 * 0x20 + 0x18, player_id);
    table.slots[0] = reinterpret_cast<std::uintptr_t>(&Delete);
    table.slots[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    local_player = player.data(); active_event = event.data(); globals = global_container.data();
    province_pointer = province.data();
  }
  template <class Buffer>
  static void Storage(std::array<std::byte, 0x30> &storage, Buffer &slots, std::int32_t count) {
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, count);
  }
  game::Ck3_12002AdapterBindings Bindings() {
    game::Ck3_12002AdapterBindings b{};
    b.core = {true, &state_slot, &jomini_slot, &character_slot, GetPlayer};
    b.events.core = b.core;
    b.events.image_base = reinterpret_cast<std::uintptr_t>(&table) - ck3_12002::kSelectEventOptionPrimaryVtableRva;
    b.events.get_current_event = GetEvent;
    b.events.pending_interaction_storage_slot = &pending_slot;
    b.events.is_pending_for_character = PendingFor;
    b.events.validate_reply = ValidateReply;
    b.commands.enabled = true;
    b.commands.command_manager = &queue_calls;
    b.commands.queue_owned_command = Queue;
    b.commands.pause_primary_vtable = reinterpret_cast<std::uintptr_t>(&table);
    b.commands.pause_secondary_vtable = 1;
    b.commands.set_speed_primary_vtable = reinterpret_cast<std::uintptr_t>(&table);
    b.commands.set_speed_secondary_vtable = 1;
    b.armies.enabled = true;
    b.armies.game_state_slot = &state_slot; b.armies.unit_storage_slot = &unit_slot;
    b.armies.get_unit_state = UnitState;
    b.world = {true, &state_slot, Contains, WarScore, &character_slot};
    b.provinces.enabled = true;
    b.provinces.game_state_slot = &state_slot; b.provinces.character_storage_slot = &character_slot;
    b.provinces.unit_storage_slot = &unit_slot; b.provinces.siege_storage_slot = &siege_slot;
    b.provinces.landed_title_storage_slot = &title_slot; b.provinces.title_province = TitleProvince;
    b.provinces.is_occupied = Occupied; b.provinces.fort_level = Fort;
    b.provinces.garrison_size = Garrison; b.provinces.besieging_strength = Besiegers;
    b.provinces.siege_progress = Fixed; b.provinces.siege_total_work = Fixed; b.provinces.siege_days_left = Days;
    b.settlement = {true, &accessor, GetIdentifiers, Lookup};
    return b;
  }
};
} // namespace

int main() {
  Scene scene;
  auto dependencies = scene.Bindings();
  auto adapter = game::CreateCk3_12002AdapterFromBindings(dependencies);
  dependencies.commands = {}; // The adapter owns its callback context.
  game::Snapshot snapshot;
  assert(adapter->enabled() && adapter->read_snapshot(snapshot));
  assert(snapshot.map_ready && snapshot.paused && snapshot.date_raw == 53175816 && snapshot.speed == 4);
  assert(snapshot.played_character_id == Scene::player_id && snapshot.played_character_alive);
  assert(snapshot.played_character_gold.raw == 12345000);
  assert(snapshot.played_character_prestige.raw == 54321000);
  assert(snapshot.played_character_piety.raw == -375000);
  assert(snapshot.played_character_stress_points == 65);
  assert(snapshot.played_character_primary_spouse_id == Scene::spouse_id);
  assert(snapshot.played_character_spouse_ids == std::vector<std::int32_t>{Scene::spouse_id});
  assert(snapshot.has_active_event && snapshot.active_event_instance_id == 99 && snapshot.active_event_option_count == 3);
  assert(snapshot.has_pending_character_interaction && snapshot.pending_auto_accept_notification);
  assert(snapshot.pending_sender_character_id == Scene::enemy_id);
  assert(snapshot.player_armies.size() == 1 && snapshot.player_armies[0].army_id == Scene::unit_id);
  assert(snapshot.player_armies[0].current_province_id == 3 && snapshot.player_armies[0].controllable);
  assert(snapshot.active_wars.size() == 1 && snapshot.active_wars[0].war_id == Scene::war_id);
  assert(snapshot.active_wars[0].player_relative_war_score == 43);
  assert(snapshot.active_wars[0].war_objective_province_ids == std::vector<std::int32_t>{3});
  assert(snapshot.active_wars[0].objective_province_states[0].garrison_size == 1234);
  assert(snapshot.has_one_life_settlement && snapshot.one_life_settlement.commit_serial == 17);
  assert(snapshot.one_life_settlement.source_character_id == Scene::player_id);
  assert(snapshot.one_life_settlement.final_score.raw == 765432100000LL);
  assert(adapter->submit_select_event_option(2) == game::SelectEventOptionResult::submitted);
  assert(queue_calls == 1 && clone_calls == 1 && delete_calls == 1 && last_instance == 99 && last_choice == 2);
  assert(adapter->submit_set_speed(2));
  assert(queue_calls == 2 && clone_calls == 2 && delete_calls == 2);

  // The observed-pointer API returns the complete frame used for the
  // idempotent result or command, without reading again after queueing it.
  game::Snapshot timeline{};
  if (adapter->submit_pause_map(&timeline) != game::PauseSubmitResult::already_paused ||
      timeline != snapshot || queue_calls != 2) return 1;
  if (adapter->submit_resume_map(&timeline) != game::ResumeSubmitResult::submitted ||
      timeline != snapshot || queue_calls != 3 || last_instance != 7 || last_choice != 0)
    return 1;

  // The worker's version-private path validates one native core prefix
  // against its published full frame. A changed date or pause state does
  // not queue a command or claim the stale frame is an observation.
  auto stale_timeline = snapshot;
  ++stale_timeline.date_raw;
  if (game::SubmitCk3_12002PauseMapObserved(*adapter, stale_timeline) !=
          game::PauseSubmitResult::unavailable || queue_calls != 3) return 1;
  if (game::SubmitCk3_12002PauseMapObserved(*adapter, snapshot) !=
          game::PauseSubmitResult::already_paused || queue_calls != 3) return 1;
  scene.jomini[0x20] = std::byte{0};
  if (game::SubmitCk3_12002ResumeMapObserved(*adapter, snapshot) !=
          game::ResumeSubmitResult::unavailable || queue_calls != 3) return 1;
  if (!adapter->read_snapshot(timeline) || timeline.paused) return 1;
  const auto running_timeline = timeline;
  if (game::SubmitCk3_12002ResumeMapObserved(*adapter, running_timeline) !=
          game::ResumeSubmitResult::already_running || queue_calls != 3) return 1;
  if (game::SubmitCk3_12002PauseMapObserved(*adapter, running_timeline) !=
          game::PauseSubmitResult::submitted || queue_calls != 4 ||
      last_instance != 7 || last_choice != 1) return 1;
  if (adapter->submit_pause_map(&timeline) != game::PauseSubmitResult::submitted ||
      timeline != running_timeline || queue_calls != 5) return 1;
  if (adapter->submit_resume_map(&timeline) != game::ResumeSubmitResult::already_running ||
      timeline != running_timeline || queue_calls != 5) return 1;
  scene.jomini[0x20] = std::byte{1};

  std::vector<game::DeclarableWarSnapshot> targeted{{Scene::enemy_id}};
  if (adapter->read_declarable_wars_for_target(Scene::enemy_id, targeted) !=
          game::ReadDeclarableWarsResult::unavailable || !targeted.empty()) return 1;
  std::vector<game::ArrangeMarriageFamilyCandidateV1> family_candidates(1);
  game::ArrangeMarriageQueryDiagnostics family_diagnostics{};
  family_diagnostics.storage_capacity = 99;
  if (adapter->read_arrange_marriage_family_candidates_v1(
          Scene::spouse_id, family_candidates, family_diagnostics) !=
          game::ReadArrangeMarriageFamilyCandidatesResultV1::unavailable ||
      !family_candidates.empty() || family_diagnostics.storage_capacity != 0) return 1;
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  // Binding is pure address construction for this exact image; it neither
  // discovers nor reads a game process. The concrete adapter owns this new
  // provider bundle instead of falling back to a legacy native binder.
  const auto image_bindings = game::BindCk3_12002AdapterImage(
      0x140000000ULL, ck3_12002::kExecutableSha256);
  if (!image_bindings.family.enabled || !image_bindings.family.context.enabled ||
      image_bindings.family.context.core.character_storage_slot !=
          image_bindings.core.character_storage_slot) return 1;
  const auto wrong_image = game::BindCk3_12002AdapterImage(0x140000000ULL, "wrong");
  if (wrong_image.family.enabled) return 1;
#endif

  bool has_prisoner_release_query = false;
  for (const auto capability : adapter->descriptor().capabilities)
    if (capability == "game.command.query-war-prisoner-release-pairs-v1-N")
      has_prisoner_release_query = true;
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  if (!has_prisoner_release_query) return 1;
#else
  if (has_prisoner_release_query) return 1;
#endif

  // Domain failure invalidates the entire read, never a convincing empty war.
  Put(scene.living_extension, 0x100, std::int64_t{-750000});
  assert(adapter->read_snapshot(snapshot) && snapshot.played_character_gold.raw == -750000);
  Put(scene.living_extension, 0x100, std::int64_t{12345000});
  Put(scene.war, 0x27C, std::int32_t{2});
  assert(!adapter->read_snapshot(snapshot) && snapshot.active_wars.empty() && !snapshot.map_ready);
  timeline.date_raw = 99;
  if (adapter->submit_pause_map(&timeline) != game::PauseSubmitResult::unavailable ||
      timeline != game::Snapshot{} || queue_calls != 5) return 1;
  Put(scene.war, 0x27C, std::int32_t{1});
  Put(scene.global_entries, 0x10, std::uint16_t{8});
  assert(!adapter->read_snapshot(snapshot) && !snapshot.has_one_life_settlement);
  Put(scene.global_entries, 0x10, std::uint16_t{1});
  Put(scene.global_entries, 0x18, std::int64_t{0});
  assert(adapter->read_snapshot(snapshot) && !snapshot.has_one_life_settlement);
  scene.pending_slot = nullptr;
  assert(!adapter->read_snapshot(snapshot) && !snapshot.has_pending_character_interaction);
  local_player = nullptr;
  assert(adapter->read_snapshot(snapshot) && !snapshot.map_ready && snapshot.speed == 4);
  assert(!snapshot.has_played_character && !snapshot.has_active_event && snapshot.active_wars.empty());
  std::cout << "PASS: full_snapshot_domains=1 transactional_failure=1 startup_prefix=1 stable_command_context=1 observed_timeline_snapshot=1 stale_worker_prefix=1 typed_target_unavailable=1\n";
}

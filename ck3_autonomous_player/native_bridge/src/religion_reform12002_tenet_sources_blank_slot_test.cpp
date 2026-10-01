#include "xar_bridge/religion_reform12002_tenet_sources.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion_reform;
namespace c = xar::ck3_12002;
namespace {
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class B, class T> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
template<class T> T Load(const void *p, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{};
  Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}; Bytes<0x80> character_entries{}; Bytes<0x1D8> character{};
  Bytes<0x90> idler{}; Bytes<0x280> handler{}; Bytes<0xA00> window{};
  Bytes<0x30> rite_storage{}, faith_storage{}; Bytes<0x80> rite_entries{}, faith_entries{};
  Bytes<0x500> source_rite{}, actor_rite{}, main_rite{};
  Bytes<0xA0> source_faith{}, actor_faith{};
  Bytes<0xF08> tenet_database{}, perk_database{};
  std::array<Bytes<0x700>, 8> definitions{};
  std::array<void *, 8> source_pointers{};
  Bytes<0xE0> actual_tenet_slots{};
  Bytes<0x10> extra_collection{}, perks_collection{};
  std::array<void *, 1> extra_entries{}, perks_entries{};
  Bytes<0x40> prophet{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *character_storage_ptr = character_storage.data();
  void *rite_storage_ptr = rite_storage.data(), *faith_storage_ptr = faith_storage.data();
  void *tenet_database_ptr = tenet_database.data(), *perk_database_ptr = perk_database.data();
  static constexpr std::uint32_t actor_id = 0x03000004U, source_rite_id = 0x83000003U;
  static constexpr std::uint32_t actor_rite_id = 0x82000001U, main_id = 0x86000002U;
  static constexpr std::uint32_t source_faith_id = 0x85000006U, actor_faith_id = 0x87000005U;
  std::array<std::uint8_t, 8> statuses{4, 3, 1, 0, 0, 0, 3, 4};
  std::array<std::uint8_t, 8> actor_statuses{4, 3, 1, 0, 2, 0, 3, 4};
  std::array<bool, 8> shown{true, true, true, true, true, true, false, true};
  std::array<bool, 8> selectable{true, true, false, true, true, true, true, true};
  bool native_collection_failure{}, correct_native_inputs = true;
  int filter_calls{};
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_storage, 0x20, character_entries.data()); Put(character_storage, 0x2C, std::uint32_t{8});
    Put(character_entries, 4 * 16 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, actor_rite_id);
    Put(jomini, 0x10, idler.data()); Put(idler, 0, std::uintptr_t{11}); Put(idler, 0x88, handler.data());
    Put(handler, 0, std::uintptr_t{22}); Put(handler, 0x278, window.data());
    Put(window, 0, std::uintptr_t{33}); Put(window, 0x10, std::uintptr_t{44});
    Put(window, 0xA0, handler.data()); Put(window, 0xC8, source_rite_id); Put(window, 0xCC, actor_id);
    Put(window, 0x888, window.data());
    Put(rite_storage, 0x20, rite_entries.data()); Put(rite_storage, 0x2C, std::uint32_t{8});
    Put(faith_storage, 0x20, faith_entries.data()); Put(faith_storage, 0x2C, std::uint32_t{8});
    Put(rite_entries, 3 * 16 + 8, source_rite.data()); Put(source_rite, 8, source_rite_id); Put(source_rite, 0x4B8, source_faith_id);
    Put(rite_entries, 2 * 16 + 8, main_rite.data()); Put(main_rite, 8, main_id); Put(main_rite, 0x4B8, source_faith_id);
    Put(rite_entries, 1 * 16 + 8, actor_rite.data()); Put(actor_rite, 8, actor_rite_id); Put(actor_rite, 0x4B8, actor_faith_id);
    Put(faith_entries, 6 * 16 + 8, source_faith.data()); Put(source_faith, 8, source_faith_id); Put(source_faith, 0x98, main_id);
    Put(faith_entries, 5 * 16 + 8, actor_faith.data()); Put(actor_faith, 8, actor_faith_id); Put(actor_faith, 0x98, actor_rite_id);
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      const auto key = "tenet_" + std::to_string(i);
      std::memcpy(definitions[i].data() + 0x18, key.data(), key.size());
      Put(definitions[i], 0x28, static_cast<std::uint64_t>(key.size()));
      Put(definitions[i], 0x30, std::uint64_t{15}); Put(definitions[i], 0x38, std::uint32_t{0x4744624F});
      source_pointers[i] = definitions[i].data();
    }
    Put(tenet_database, 0xEF0, source_pointers.data()); Put(tenet_database, 0xEF8, std::int32_t{8}); Put(tenet_database, 0xEFC, std::int32_t{8});
    Put(perk_database, 0xEF0, prophet.data());
    Put(window, 0x778, actual_tenet_slots.data()); Put(window, 0x780, std::int32_t{2}); Put(window, 0x784, std::int32_t{2});
    Put(actual_tenet_slots, 0x20, std::uint32_t{7}); Put(actual_tenet_slots, 0x28, definitions[0].data());
    Put(actual_tenet_slots, 0x90, std::uint32_t{11}); Put(actual_tenet_slots, 0x98, definitions[1].data());
    extra_entries[0] = definitions[3].data(); perks_entries[0] = prophet.data();
    Put(extra_collection, 0, extra_entries.data()); Put(extra_collection, 8, std::int32_t{1}); Put(extra_collection, 0xC, std::int32_t{1});
    Put(perks_collection, 0, perks_entries.data()); Put(perks_collection, 8, std::int32_t{1});
  }
};
Fixture *f{};
void *Player(void *) { return f->player.data(); }
bool Visible(const void *) { return true; }
std::size_t Index(const void *definition) {
  for (std::size_t i = 0; i < f->definitions.size(); ++i)
    if (f->definitions[i].data() == definition) return i;
  f->correct_native_inputs = false; return 0;
}
const void *Extra(void *actor) {
  f->correct_native_inputs &= actor == f->character.data();
  return f->native_collection_failure ? nullptr : f->extra_collection.data();
}
const void *Perks(void *actor) {
  f->correct_native_inputs &= actor == f->character.data(); return f->perks_collection.data();
}
bool Contains(const void *collection, const void *address) {
  const auto *definition = Load<const void *>(address, 0);
  const auto *entries = Load<const void *>(collection, 0);
  const auto count = Load<std::int32_t>(collection, 0xC);
  for (std::int32_t i = 0; i < count; ++i)
    if (Load<const void *>(entries, static_cast<std::size_t>(i) * 8) == definition) return true;
  return false;
}
std::uint8_t Status(void *rite, const void *definition) {
  f->correct_native_inputs &= rite == f->main_rite.data(); return f->statuses[Index(definition)];
}
std::uint8_t ActorStatus(void *faith, const void *definition) {
  f->correct_native_inputs &= faith == f->actor_faith.data(); return f->actor_statuses[Index(definition)];
}
bool Trigger(const void *trigger, const void *scope) {
  f->correct_native_inputs &= scope == f->window.data() + 0xD0;
  for (std::size_t i = 0; i < f->definitions.size(); ++i) {
    if (trigger == f->definitions[i].data() + 0x658) return f->shown[i];
    if (trigger == f->definitions[i].data() + 0x4B8) return f->selectable[i];
  }
  f->correct_native_inputs = false; return false;
}
bool Filter(const void *category, const void *definition) {
  ++f->filter_calls;
  f->correct_native_inputs &= category == f->window.data() + 0x888 &&
    Load<const void *>(category, 0) == f->window.data();
  const auto i = Index(definition);
  if (definition != Load<const void *>(category, 0x18))
    for (int j = 0; j < 2; ++j)
      if (definition == Load<const void *>(f->actual_tenet_slots.data(), static_cast<std::size_t>(j) * 0x70 + 0x28)) return false;
  const auto *prophet = f->prophet.data();
  return (Contains(f->extra_collection.data(), &definition) || Contains(f->perks_collection.data(), &prophet) ||
    f->actor_statuses[i] != 0) && f->shown[i];
}
r::TenetSourcesBindings Bind(Fixture &q) {
  f = &q; r::TenetSourcesBindings b{}; b.enabled = true; b.window.enabled = true;
  b.window.core = {true, &q.state_ptr, &q.jomini_ptr, &q.character_storage_ptr, &Player};
  b.window.idler_vtable = 11; b.window.handler_vtable = 22;
  b.window.window_vtable = 33; b.window.window_secondary_vtable = 44; b.window.is_visible = &Visible;
  b.tenet_database_global = &q.tenet_database_ptr; b.perk_database_global = &q.perk_database_ptr;
  b.rite_storage_global = &q.rite_storage_ptr; b.faith_storage_global = &q.faith_storage_ptr;
  b.source_filter = &Filter; b.source_main_rite_status = &Status; b.actor_faith_status = &ActorStatus;
  b.actor_extra_collection = &Extra; b.actor_perks_collection = &Perks;
  b.contains = &Contains; b.evaluate_trigger = &Trigger; return b;
}
int cases{};
bool Check(bool ok, const char *label) {
  ++cases; if (!ok) std::cerr << "FAIL " << label << '\n'; return ok;
}
void Wire(const std::filesystem::path &dir, const char *name, const r::DraftTenetSources &v) {
  std::ofstream(dir / name) << r::SerializeCurrentDraftTenetSources12002(v) << '\n';
}
} // namespace

int main(int argc,char **argv) {
  const auto dir=argc>1?std::filesystem::path(argv[1]):std::filesystem::current_path();
  Fixture q;auto b=Bind(q);r::DraftTenetSources out{};
  Bytes<0x150> rows{};std::memcpy(rows.data(),q.actual_tenet_slots.data(),q.actual_tenet_slots.size());
  Bytes<0x40> native_default{};Put(native_default,0x38,std::uint32_t{0x4E756C6C});
  void *native_default_ptr=native_default.data();b.default_tenet_definition_global=&native_default_ptr;
  Put(rows,0x20,std::uint32_t{0});Put(rows,0x90,std::uint32_t{1});
  Put(rows,0x100,std::uint32_t{2});Put(rows,0x108,native_default.data());
  Put(q.window,0x778,rows.data());Put(q.window,0x780,std::int32_t{3});Put(q.window,0x784,std::int32_t{3});
  if(!Check(r::ReadCurrentDraftTenetSources12002(b,26988,out)&&out.available&&out.draft_observed&&
      out.tenet_gates_complete&&out.slots.size()==3&&out.slots[0].selected_tenet_key=="tenet_0"&&
      out.slots[1].selected_tenet_key=="tenet_1"&&out.slots[2].slot_index==2&&out.slots[2].selected_tenet_key.empty()&&
      out.sources.size()==8&&out.sources[3].final_selectable&&q.correct_native_inputs,
      "actual native-default third slot is observed and preserves all sources"))return 1;
  Wire(dir,"native-default-third-slot.json",out);
  std::cout<<"GREEN cases=1 new actual native-default blank-slot production reader/serializer path; old main not run; no CK3\n";
  return 0;
}

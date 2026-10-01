#include "xar_bridge/religion_reform12002_choices.hpp"
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
template<class B, class T> void Put(B &b, std::size_t at, T value) { std::memcpy(b.data() + at, &value, sizeof(value)); }
template<class B> void Key(B &b, const char *key) {
  const auto n = std::strlen(key); std::memcpy(b.data() + 0x18, key, n);
  Put(b, 0x28, static_cast<std::uint64_t>(n)); Put(b, 0x30, std::uint64_t{15});
}
template<class B, class T> void Array(B &b, std::size_t at, T data, std::int32_t count) {
  Put(b, at, data); Put(b, at + 8, count + 2); Put(b, at + 0xC, count);
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}; Bytes<0x80> slots{}; Bytes<0x1D8> character{};
  Bytes<0x90> idler{}; Bytes<0x280> handler{}; Bytes<0xC00> window{};
  Bytes<0xB20> doctrine{}; Bytes<0x40> doctrine_group{}; Bytes<0x50> doctrine_item{};
  Bytes<0x40> tenet{}; Bytes<0x70> tenet_item{}; Bytes<0x20> tenet_group{}; Bytes<0xF00> perk_database{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data(), *perk_ptr = perk_database.data();
  static constexpr std::int32_t actor = 0x03000004;
  bool visible = true, native_doctrine = true, known = true, prophet = false, native_tenet = true, drift = false;
  int trigger_calls = 0, knows_calls = 0, perk_calls = 0, tenet_calls = 0; bool arguments_correct = true;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data()); Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor);
    Put(jomini, 0x10, idler.data()); Put(idler, 0, std::uintptr_t{11}); Put(idler, 0x88, handler.data());
    Put(handler, 0, std::uintptr_t{22}); Put(handler, 0x278, window.data());
    Put(window, 0, std::uintptr_t{33}); Put(window, 0x10, std::uintptr_t{44}); Put(window, 0xA0, handler.data());
    Put(window, 0xC8, std::uint32_t{0x83000003}); Put(window, 0xCC, static_cast<std::uint32_t>(actor));
    Key(doctrine, "doctrine_a"); Key(doctrine_group, "group_a"); Put(doctrine, 0xB08, doctrine_group.data());
    Put(doctrine_item, 0x28, doctrine.data()); Array(window, 0x8A8, doctrine_item.data(), 1);
    Key(tenet, "tenet_a"); Put(tenet, 0x38, std::uint32_t{0x4744624F});
    Put(tenet_item, 0x28, tenet.data()); tenet_item[0x24] = std::byte{1};
    Array(tenet_group, 8, tenet_item.data(), 1); Array(window, 0x7A8, tenet_group.data(), 1);
    Put(perk_database, 0xEF0, player.data());
  }
};
Fixture *f{};
void *Player(void *) { return f->player.data(); }
bool Visible(const void *) { return f->visible; }
bool Trigger(const void *trigger, const void *scope) {
  ++f->trigger_calls; f->arguments_correct &= scope == f->window.data() + 0xD0 &&
    (trigger == f->doctrine.data() + 0x1B8 || trigger == f->doctrine.data() + 0xE8);
  return f->native_doctrine;
}
bool Knows(void *actor, const void *definition) {
  ++f->knows_calls; f->arguments_correct &= actor == f->character.data() && definition == f->doctrine.data(); return f->known;
}
bool HasPerk(void *actor, const void *perk) {
  ++f->perk_calls; f->arguments_correct &= actor == f->character.data() && perk == f->player.data(); return f->prophet;
}
bool Tenet(const void *item, void *actor, const void *scope) {
  ++f->tenet_calls; f->arguments_correct &= item == f->tenet_item.data() && actor == f->character.data() && scope == f->window.data() + 0xD0;
  if (f->drift) Put(f->state, 8, std::int32_t{53175817}); return f->native_tenet;
}
r::DraftChoiceBindings Bind(Fixture &q) {
  f = &q; r::DraftChoiceBindings b{}; b.window.enabled = true;
  b.window.core = {true, &q.state_ptr, &q.jomini_ptr, &q.storage_ptr, &Player};
  b.window.idler_vtable = 11; b.window.handler_vtable = 22; b.window.window_vtable = 33;
  b.window.window_secondary_vtable = 44; b.window.is_visible = &Visible;
  b.evaluate_trigger = &Trigger; b.knows_doctrine = &Knows; b.has_perk = &HasPerk;
  b.tenet_can_pick = &Tenet; b.perk_database_global = &q.perk_ptr; return b;
}
int cases{};
bool Check(bool ok, const char *name) { ++cases; if (!ok) std::cerr << "FAIL " << name << '\n'; return ok; }
void Wire(const std::filesystem::path &p, const char *name, const r::DraftChoices &v) {
  std::ofstream(p / name) << r::SerializeCurrentDraftChoices12002(v) << '\n';
}
} // namespace

#include "xar_bridge/religion_doctrine12002_selection.hpp"
Bytes<0xB20> def_b{},def_c{},def_d{};
bool MultiTrigger(const void *trigger,const void *scope) {
  f->arguments_correct &= scope==f->window.data()+0xD0;
  return trigger != def_b.data()+0xE8 && trigger != def_c.data()+0x1B8;
}
bool MultiKnows(void *actor,const void *definition) {
  f->arguments_correct &= actor==f->character.data();
  return definition==f->doctrine.data();
}
int main(int argc,char **argv) {
  const auto p=argc>1?std::filesystem::path(argv[1]):std::filesystem::current_path();
  const bool baseline=argc>2;
  Fixture q;auto b=Bind(q);b.evaluate_trigger=&MultiTrigger;b.knows_doctrine=&MultiKnows;
  Key(def_b,"doctrine_b");Key(def_c,"doctrine_c");Key(def_d,"doctrine_d");
  Put(def_b,0xB08,q.doctrine_group.data());Put(def_c,0xB08,q.doctrine_group.data());Put(def_d,0xB08,q.doctrine_group.data());
  Bytes<0x48*4> items{};
  Put(items,0x28,q.doctrine.data());Put(items,0x48+0x28,def_b.data());
  Put(items,0x90+0x28,def_c.data());Put(items,0xD8+0x28,def_d.data());
  Array(q.window,0x8A8,items.data(),4);
  r::DraftChoices popup{};
  if (baseline) {
    const bool ok=r::ReadCurrentDraftChoices12002(b,70,popup);
    if(ok||popup.failure!="doctrine_definition_unavailable"||!popup.doctrines.empty())return 90;
    Wire(p,"baseline-multirow-red.json",popup);
    std::cout<<"GREEN reproduced baseline stride50 failure on actual four-row popup\n";return 0;
  }
  if(!Check(r::ReadCurrentDraftChoices12002(b,70,popup)&&popup.doctrines.size()==4&&
       popup.doctrines[3].doctrine_key=="doctrine_d"&&q.arguments_correct,"actual four rows at48"))return 1;
  Wire(p,"patched-multirow-popup.json",popup);
  c::religion::doctrine12002::CurrentDoctrineSelection selection{};
  if(!Check(c::religion::doctrine12002::ObserveCurrentDraftDoctrineSelection12002(b,popup,70,selection)&&
       selection.rows.size()==4&&selection.selectable_doctrine_keys==std::vector<std::string>{"doctrine_a"}&&
       selection.rows[1].selection_blocker=="blocked_by_native_can_pick"&&
       selection.rows[2].selection_blocker=="hidden_by_native_should_display"&&
       selection.rows[3].selection_blocker=="doctrine_not_known_and_no_prophet","actual selection observer positive blocked hidden knowledge"))return 2;
  std::ofstream(p/"patched-multirow-selection.json")<<c::religion::doctrine12002::SerializeCurrentDraftDoctrineSelection12002(selection);
  if(!Check(c::religion::doctrine12002::ReadCurrentDraftDoctrineSelection12002(b,71,selection)&&
       selection.rows.size()==4,"actual convenience reader uses same single header leaf"))return 3;
  std::cout<<"GREEN checks="<<cases<<" actual four-row popup+selection; no CK3\n";return 0;
}

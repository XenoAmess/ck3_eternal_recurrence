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
int main(int argc, char **argv) {
  const auto p = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::current_path();
  Fixture q; auto b = Bind(q); r::DraftChoices v{};
  if (!Check(r::ReadCurrentDraftChoices12002(b, 1, v) && v.draft_observed && v.doctrines.size() == 1 &&
      v.tenets.size() == 1 && v.doctrines[0].button_enabled && v.doctrines[0].native_knows_doctrine == true &&
      !v.doctrines[0].native_has_prophet && v.tenets[0].native_can_pick && q.arguments_correct &&
      q.trigger_calls == 2 && q.perk_calls == 0, "current popup actor/scope/definition and short-circuit")) return 1;
  Wire(p, "known-doctrine.json", v);
  q.known = false; q.prophet = true;
  if (!Check(r::ReadCurrentDraftChoices12002(b, 2, v) && v.doctrines[0].button_enabled &&
      v.doctrines[0].native_knows_doctrine == false && v.doctrines[0].native_has_prophet == true && q.arguments_correct,
      "scripted GUI prophet alternative")) return 2;
  Wire(p, "prophet-doctrine.json", v);
  q.prophet = false; q.native_tenet = false;
  if (!Check(r::ReadCurrentDraftChoices12002(b, 3, v) && !v.doctrines[0].button_enabled && !v.tenets[0].native_can_pick,
      "native false remains observed false")) return 3;
  Wire(p, "blocked-popup.json", v);
  q.native_doctrine = false; const auto calls = q.knows_calls;
  if (!Check(r::ReadCurrentDraftChoices12002(b, 4, v) && !v.doctrines[0].native_can_pick &&
      !v.doctrines[0].native_knows_doctrine && q.knows_calls == calls, "base trigger blocks before knowledge")) return 4;
  q.visible = false; const auto tenet_calls = q.tenet_calls;
  if (!Check(r::ReadCurrentDraftChoices12002(b, 5, v) && !v.draft_observed && v.doctrines.empty() &&
      v.tenets.empty() && q.tenet_calls == tenet_calls, "hidden window known no current popup")) return 5;
  Wire(p, "hidden-window.json", v);
  q.visible = true; Array(q.window, 0x8A8, q.doctrine_item.data(), 0); Array(q.window, 0x7A8, q.tenet_group.data(), 0);
  if (!Check(r::ReadCurrentDraftChoices12002(b, 6, v) && v.draft_observed && v.doctrines.empty() && v.tenets.empty(),
      "materialized zero rows are observed empty")) return 6;
  Wire(p, "empty-popup.json", v);
  Array(q.window, 0x8A8, q.doctrine_item.data(), 1); Array(q.window, 0x7A8, q.tenet_group.data(), 1);
  q.native_doctrine = true; q.known = true; q.drift = true;
  if (!Check(!r::ReadCurrentDraftChoices12002(b, 7, v) && v.failure == "state_changed" && v.doctrines.empty() &&
      v.tenets.empty(), "changed frame never publishes partial rows")) return 7;
  Wire(p, "state-changed.json", v);
  q.drift = false; Put(q.state, 8, std::int32_t{53175816}); q.tenet_item[0x24] = std::byte{0}; q.perk_ptr = nullptr;
  if (!Check(!r::ReadCurrentDraftChoices12002(b, 8, v) && v.failure == "prophet_definition_unavailable" &&
      q.tenet_calls == tenet_calls + 1, "no lazy native database initialization")) return 8;
  q.perk_ptr = q.perk_database.data(); Put(q.window, 0xCC, std::uint32_t{0x04000004});
  if (!Check(!r::ReadCurrentDraftChoices12002(b, 9, v) && v.failure == "draft_subject_unavailable",
      "actual window must belong to complete current actor ID")) return 9;
  const auto exact = r::BindCurrentDraftChoices12002(0x140000000, c::kExecutableSha256);
  if (!Check(exact.window.enabled && reinterpret_cast<std::uintptr_t>(exact.tenet_can_pick) == 0x140EE0AD0ULL &&
      !r::BindCurrentDraftChoices12002(0x140000000, "old-build").window.enabled,
      "actual exact image binding")) return 10;
  std::cout << "GREEN cases=" << cases << " actual popup choice reader/serializer; no CK3\n"; return 0;
}

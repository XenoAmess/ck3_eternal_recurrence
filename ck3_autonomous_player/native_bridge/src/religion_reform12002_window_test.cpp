#include "xar_bridge/religion_reform12002_window.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion_reform;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &b, std::size_t at, T v) {
  std::memcpy(b.data() + at, &v, sizeof(v));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{};
  Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}; Bytes<0x80> slots{}; Bytes<0x1D8> character{};
  Bytes<0x90> idler{}; Bytes<0x280> handler{}; Bytes<0xD0> window{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t actor = 0x03000004;
  bool visible = true, drift = false; int visible_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor);
    Put(jomini, 0x10, idler.data()); Put(idler, 0, std::uintptr_t{11});
    Put(idler, r::kDraftHandlerFromIdlerOffset, handler.data());
    Put(handler, 0, std::uintptr_t{22}); Put(handler, r::kDraftWindowFromHandlerOffset, window.data());
    Put(window, 0, std::uintptr_t{33}); Put(window, 0x10, std::uintptr_t{44});
    Put(window, r::kDraftWindowOwnerOffset, handler.data());
    Put(window, r::kDraftWindowRiteIdOffset, std::uint32_t{0x83000003});
    Put(window, r::kDraftWindowActorIdOffset, static_cast<std::uint32_t>(actor));
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
bool Visible(const void *) {
  ++f->visible_calls;
  if (f->drift) Put(f->entry, 0xB0, std::int32_t{0x04000004});
  return f->visible;
}
r::DraftWindowBindings Bind(Fixture &q) {
  f = &q; r::DraftWindowBindings b{}; b.enabled = true;
  b.core = {true, &q.state_ptr, &q.jomini_ptr, &q.storage_ptr, &Player};
  b.idler_vtable = 11; b.handler_vtable = 22; b.window_vtable = 33;
  b.window_secondary_vtable = 44; b.is_visible = &Visible; return b;
}
int cases = 0;
bool Check(bool ok, const char *name) {
  ++cases; if (!ok) std::cerr << "FAIL " << name << '\n'; return ok;
}
void Wire(const std::filesystem::path &p, const char *name, const r::DraftWindowView &v) {
  std::ofstream(p / name) << r::SerializeCurrentRiteCreationWindow12002(v) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::current_path();
  Fixture q; auto b = Bind(q); r::DraftWindowView v{};
  if (!Check(r::ReadCurrentRiteCreationWindow12002(b, 88, v) && v.available && v.present &&
      v.visible && v.window == q.window.data() && v.source_rite_id == 0x83000003U &&
      v.played_character_id == static_cast<std::uint32_t>(Fixture::actor) &&
      v.date_raw == 53175816 && v.capture_epoch == 88, "actual visible current player draft")) return 1;
  Wire(directory, "visible-current-draft.json", v);
  q.visible = false;
  if (!Check(r::ReadCurrentRiteCreationWindow12002(b, 89, v) && v.present && !v.visible &&
      !v.window && !v.source_rite_id, "hidden cached draft is not current draft")) return 2;
  Wire(directory, "hidden-window.json", v);
  Put(q.handler, r::kDraftWindowFromHandlerOffset, static_cast<void *>(nullptr));
  if (!Check(r::ReadCurrentRiteCreationWindow12002(b, 90, v) && !v.present && !v.visible &&
      !v.window, "known absent materialized window")) return 3;
  Wire(directory, "absent-window.json", v);
  Put(q.handler, r::kDraftWindowFromHandlerOffset, q.window.data()); q.visible = true;
  Put(q.window, r::kDraftWindowActorIdOffset, std::uint32_t{0x04000004});
  if (!Check(!r::ReadCurrentRiteCreationWindow12002(b, 91, v) &&
      v.failure == r::DraftWindowFailure::draft_subject_unavailable, "full actor generation matters")) return 4;
  Wire(directory, "different-actor-draft.json", v);
  Put(q.window, r::kDraftWindowActorIdOffset, static_cast<std::uint32_t>(Fixture::actor));
  q.drift = true;
  if (!Check(!r::ReadCurrentRiteCreationWindow12002(b, 92, v) &&
      v.failure == r::DraftWindowFailure::state_changed && !v.window, "actual subject changed while observing")) return 5;
  q.drift = false; Put(q.entry, 0xB0, Fixture::actor); q.jomini[0x20] = std::byte{0};
  if (!Check(!r::ReadCurrentRiteCreationWindow12002(b, 93, v) &&
      v.failure == r::DraftWindowFailure::frame_not_paused, "paused query owner contract")) return 6;
  q.jomini[0x20] = std::byte{1}; Put(q.window, r::kDraftWindowOwnerOffset, static_cast<void *>(nullptr));
  if (!Check(!r::ReadCurrentRiteCreationWindow12002(b, 94, v) &&
      v.failure == r::DraftWindowFailure::window_layout_unavailable, "fresh published window belongs to handler")) return 7;
  const auto exact = r::BindCurrentRiteCreationWindow12002(0x140000000, c::kExecutableSha256);
  if (!Check(exact.enabled && exact.window_vtable == 0x144565C30ULL &&
      !r::BindCurrentRiteCreationWindow12002(0x140000000, "old-build").enabled,
      "actual production bindings exact build")) return 8;
  std::cout << "GREEN cases=" << cases << " current visible draft/root reader; no CK3\n";
  return 0;
}

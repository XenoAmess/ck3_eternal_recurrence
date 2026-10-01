#include "xar_bridge/religion_rite_governance12002_head.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace h = xar::ck3_12002::religion::head;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x100> slots{};
  Bytes<0x1D8> actor{}, actor_head{}, main_head{}, faith_holder{}, another_generation{};
  Bytes<0x500> rite{}, main_rite{}, another_rite{};
  Bytes<0x320> faith{};
  Bytes<0x140> title{}, another_title{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::uint32_t actor_id = 0x83000004, actor_head_id = 0x84000005;
  static constexpr std::uint32_t main_head_id = 0x02000006, faith_holder_id = 0x85000007;
  static constexpr std::uint32_t rite_id = 0, main_rite_id = 0x82000002;
  static constexpr std::uint32_t faith_id = 0x87000003, title_id = 0x88000000;
  bool missing_rite = false, wrong_title = false, wrong_head = false, bad_head_return = false;
  bool drift = false;
  int head_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{16});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(slots, 5 * 0x10 + 8, actor_head.data()); Put(actor_head, 0x18, actor_head_id);
    Put(slots, 6 * 0x10 + 8, main_head.data()); Put(main_head, 0x18, main_head_id);
    Put(slots, 7 * 0x10 + 8, faith_holder.data()); Put(faith_holder, 0x18, faith_holder_id);
    Put(another_generation, 0x18, std::uint32_t{0x01000005});
    Put(actor, r::kCharacterRiteIdOffset, rite_id);
    Put(rite, 8, rite_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(rite, h::kRiteHeadCharacterIdOffset, actor_head_id);
    Put(main_rite, 8, main_rite_id); Put(main_rite, h::kRiteHeadCharacterIdOffset, main_head_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_rite_id);
    Put(faith, h::kFaithReligiousHeadTitleIdOffset, title_id);
    Put(title, h::kTitleReferenceIdOffset, title_id);
    Put(title, h::kTitleHolderCharacterIdOffset, faith_holder_id);
    Put(another_title, h::kTitleReferenceIdOffset, std::uint32_t{0x01000000});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->missing_rite ? nullptr : f->rite.data(); }
void *CharacterFaith(void *) { return f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *MainRite(void *) { return f->main_rite.data(); }
std::uint32_t *HeadId(void *rite, std::uint32_t *out) {
  *out = Get<std::uint32_t>(rite, h::kRiteHeadCharacterIdOffset);
  return f->bad_head_return ? nullptr : out;
}
void *Head(void *rite) {
  if (f->wrong_head) return f->another_generation.data();
  const auto id = Get<std::uint32_t>(rite, h::kRiteHeadCharacterIdOffset);
  auto *value = c::ResolveCoreCharacter({true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player},
                                       std::bit_cast<std::int32_t>(id));
  if (f->drift && ++f->head_calls == 2)
    Put(f->rite, h::kRiteHeadCharacterIdOffset, Fixture::actor_id);
  return value;
}
void *Title(void *) { return f->wrong_title ? f->another_title.data() : f->title.data(); }
void *FaithHead(void *) {
  const auto id = Get<std::uint32_t>(f->title.data(), h::kTitleHolderCharacterIdOffset);
  return c::ResolveCoreCharacter({true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player},
                                std::bit_cast<std::int32_t>(id));
}
h::Bindings Bind(Fixture &q) {
  f = &q;
  h::Bindings b{}; b.enabled = true; b.context.enabled = true;
  b.context.core = {true, &q.state_ptr, &q.jomini_ptr, &q.storage_ptr, &Player};
  b.context.character_rite = &CharacterRite; b.context.character_faith = &CharacterFaith;
  b.context.rite_faith = &RiteFaith; b.context.faith_main_rite = &MainRite;
  b.rite_head_id = &HeadId; b.rite_head = &Head;
  b.faith_religious_head_title = &Title; b.faith_religious_head = &FaithHead;
  return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const h::Context &out) {
  if (!directory.empty()) std::ofstream(directory / name) << h::SerializePlayedRiteHeads12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); h::Context out{};
  if (!Check(h::ReadPlayedRiteHeads12002(b, 101, out), "production reader current heads") ||
      !Check(out.available && out.capture_epoch == 101, "available epoch") ||
      !Check(out.actor_rite_id == std::uint32_t{0} && out.faith_main_rite_id == Fixture::main_rite_id,
             "zero rite identity and separate main rite") ||
      !Check(out.actor_rite_head_character_id == Fixture::actor_head_id &&
             out.faith_main_rite_head_character_id == Fixture::main_head_id &&
             out.faith_religious_head_holder_character_id == Fixture::faith_holder_id,
             "three native head sources remain distinct") ||
      !Check(out.faith_religious_head_title_id == Fixture::title_id,
             "title ID is not holder CharacterID") ||
      !Check(out.played_character_id == std::bit_cast<std::int32_t>(Fixture::actor_id),
             "played character preserves high generation")) return 1;
  Wire(directory, "distinct-heads.json", out);
  Put(q.title, h::kTitleHolderCharacterIdOffset, r::kAbsentReference);
  if (!Check(h::ReadPlayedRiteHeads12002(b, 102, out) && out.faith_religious_head_title_id &&
             !out.faith_religious_head_holder_character_id, "vacant religious title remains present")) return 2;
  Wire(directory, "vacant-title.json", out);
  Put(q.rite, h::kRiteHeadCharacterIdOffset, r::kAbsentReference);
  Put(q.main_rite, h::kRiteHeadCharacterIdOffset, r::kAbsentReference);
  Put(q.faith, h::kFaithReligiousHeadTitleIdOffset, r::kAbsentReference);
  if (!Check(h::ReadPlayedRiteHeads12002(b, 103, out) && out.actor_rite_id && out.faith_id &&
             !out.actor_rite_head_character_id && !out.faith_main_rite_head_character_id &&
             !out.faith_religious_head_title_id, "legitimate absence retains rite and faith")) return 3;
  Wire(directory, "legal-head-absence.json", out);
  Put(q.actor, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(h::ReadPlayedRiteHeads12002(b, 104, out) && !out.actor_rite_id && !out.faith_id,
             "legal missing rite has no invented authority")) return 4;
  Wire(directory, "legal-rite-absence.json", out);
  Put(q.actor, r::kCharacterRiteIdOffset, Fixture::rite_id);
  Put(q.rite, h::kRiteHeadCharacterIdOffset, Fixture::actor_id);
  if (!Check(h::ReadPlayedRiteHeads12002(b, 105, out) &&
             out.actor_rite_head_character_id == Fixture::actor_id,
             "player can be head without changing faith-title source")) return 5;
  Wire(directory, "actor-is-rite-head.json", out);
  Put(q.faith, h::kFaithReligiousHeadTitleIdOffset, Fixture::title_id); q.wrong_title = true;
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 106, out) &&
             out.failure == h::Failure::faith_head_title_unavailable && !out.available &&
             !out.faith_religious_head_title_id, "actual title lookup wrong generation is unavailable")) return 6;
  Wire(directory, "title-unavailable.json", out); q.wrong_title = false;
  Put(q.title, h::kTitleHolderCharacterIdOffset, std::uint32_t{0x01000007});
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 107, out) &&
             out.failure == h::Failure::faith_head_holder_unavailable,
             "holder storage wrong generation is not absence")) return 7;
  Put(q.title, h::kTitleHolderCharacterIdOffset, Fixture::faith_holder_id);
  q.wrong_head = true;
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 108, out) &&
             out.failure == h::Failure::rite_head_unavailable, "native head lookup disagreement")) return 8;
  q.wrong_head = false; q.bad_head_return = true;
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 109, out) &&
             out.failure == h::Failure::rite_head_unavailable, "typed head out getter missing return")) return 9;
  q.bad_head_return = false;
  Put(q.rite, h::kRiteHeadCharacterIdOffset, Fixture::actor_head_id);
  Put(q.main_rite, h::kRiteHeadCharacterIdOffset, Fixture::main_head_id);
  q.drift = true; q.head_calls = 0;
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 110, out) && out.failure == h::Failure::state_changed,
             "changed observed identities do not form one paused snapshot")) return 10;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!h::ReadPlayedRiteHeads12002(b, 111, out) && out.failure == h::Failure::frame_not_paused,
             "owning paused context required")) return 11;
  const auto image = h::BindRiteHeadsImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(image.enabled && image.context.enabled &&
             reinterpret_cast<std::uintptr_t>(image.rite_head_id) == 0x140D55CF0 &&
             reinterpret_cast<std::uintptr_t>(image.rite_head) == 0x1424FC610 &&
             reinterpret_cast<std::uintptr_t>(image.faith_religious_head) == 0x142439E10 &&
             reinterpret_cast<std::uintptr_t>(image.faith_religious_head_title) == 0x142443FA0,
             "actual exact binder callbacks") ||
      !Check(!h::BindRiteHeadsImage12002(0, c::kExecutableSha256).enabled &&
             !h::BindRiteHeadsImage12002(0x140000000, "old").enabled,
             "exact image version binding")) return 12;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

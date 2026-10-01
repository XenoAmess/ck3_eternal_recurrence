#include "xar_bridge/religion_rite_governance12002_state_rite.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace s = r::state_rite;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
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
  Bytes<0x80> slots{};
  Bytes<0x1D8> actor{}, top_liege{};
  Bytes<0x200> actor_landed{}, top_landed{};
  Bytes<0x310> own_title{}, realm_title{};
  Bytes<0x500> actor_rite{}, actor_main_rite{}, own_rite{}, realm_rite{};
  Bytes<0xA0> actor_faith{}, own_faith{}, realm_faith{};
  Bytes<0x10> wrong_object{};
  std::array<std::uint32_t, 1> actor_titles{0x82000001U};
  std::array<std::uint32_t, 1> top_titles{0x83000002U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t top_id = 0x84000006U;
  static constexpr std::uint32_t own_rite_id = 0x85000007U;
  static constexpr std::uint32_t realm_rite_id = 0x86000008U;
  static constexpr std::uint32_t actor_faith_id = 0x87000009U;
  static constexpr std::uint32_t own_faith_id = 0x8800000AU;
  static constexpr std::uint32_t realm_faith_id = 0x8900000BU;
  bool independent = false, missing_state_faith = false, missing_top = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(slots, 6 * 0x10 + 8, top_liege.data());
    Put(actor, s::kCharacterIdentityOffset, actor_id); Put(top_liege, s::kCharacterIdentityOffset, top_id);
    Put(actor, s::kCharacterLandedDataOffset, actor_landed.data());
    Put(top_liege, s::kCharacterLandedDataOffset, top_landed.data());
    Put(actor_landed, s::kLandedTitlesOffset, actor_titles.data());
    Put(top_landed, s::kLandedTitlesOffset, top_titles.data());
    Put(actor_landed, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(top_landed, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(own_title, s::kTitleIdentityOffset, actor_titles[0]); Put(realm_title, s::kTitleIdentityOffset, top_titles[0]);
    Put(own_title, s::kTitleStateRiteIdOffset, own_rite_id);
    Put(realm_title, s::kTitleStateRiteIdOffset, realm_rite_id);
    Put(actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(actor_rite, 8, std::uint32_t{0}); Put(actor_rite, r::kRiteFaithIdOffset, actor_faith_id);
    Put(actor_main_rite, 8, std::uint32_t{0x8A00000C});
    Put(own_rite, 8, own_rite_id); Put(own_rite, r::kRiteFaithIdOffset, own_faith_id);
    Put(realm_rite, 8, realm_rite_id); Put(realm_rite, r::kRiteFaithIdOffset, realm_faith_id);
    Put(actor_faith, 8, actor_faith_id); Put(actor_faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x8A00000C});
    Put(own_faith, 8, own_faith_id); Put(realm_faith, 8, realm_faith_id);
  }
};
Fixture *q = nullptr;
void *Player(void *) { return q->player.data(); }
void *CharacterRite(void *) { return q->actor_rite.data(); }
void *CharacterFaith(void *) { return q->actor_faith.data(); }
void *FaithMainRite(void *) { return q->actor_main_rite.data(); }
void *RiteFaith(void *rite) {
  if (rite == q->actor_rite.data()) return q->actor_faith.data();
  if (rite == q->own_rite.data()) return q->own_faith.data();
  return q->missing_state_faith ? q->wrong_object.data() : q->realm_faith.data();
}
void *TopLiege(void *) { return q->missing_top ? nullptr : (q->independent ? q->actor.data() : q->top_liege.data()); }
void *PrimaryTitle(void *character) { return character == q->actor.data() ? q->own_title.data() : q->realm_title.data(); }
void *TitleStateRite(void *title) { return title == q->own_title.data() ? q->own_rite.data() : q->realm_rite.data(); }
s::Bindings Bind(Fixture &fixture) {
  q = &fixture;
  s::Bindings b{}; b.enabled = true; b.context.enabled = true;
  b.context.core = {true, &q->state_ptr, &q->jomini_ptr, &q->storage_ptr, &Player};
  b.context.character_rite = &CharacterRite; b.context.character_faith = &CharacterFaith;
  b.context.rite_faith = &RiteFaith; b.context.faith_main_rite = &FaithMainRite;
  b.character_top_liege = &TopLiege; b.character_primary_title = &PrimaryTitle;
  b.title_state_rite = &TitleStateRite; return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &directory, const char *name, const s::Context &out) {
  if (!directory.empty()) std::ofstream(directory / name) << s::SerializePlayedStateRite12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture f; const auto b = Bind(f); s::Context out{};
  if (!Check(s::ReadPlayedStateRite12002(b, 501, out), "actual paused vassal context") ||
      !Check(out.available && out.capture_epoch == 501 && out.date_raw == 53175816, "actual owner frame") ||
      !Check(out.top_liege_character_id == Fixture::top_id, "top-liege full high-bit generation") ||
      !Check(out.actor_rite_id == 0U && out.actor_faith_id == Fixture::actor_faith_id,
             "actor zero rite and actual faith") ||
      !Check(out.actor_faith_main_rite_id == 0x8A00000CU && out.actor_faith_main_rite_id != out.actor_rite_id,
             "main rite differs from actor rite") ||
      !Check(out.player_primary_title.title_id == f.actor_titles[0] &&
             out.realm_primary_title.title_id == f.top_titles[0], "own and realm titles differ") ||
      !Check(out.player_primary_title.state_rite_id == Fixture::own_rite_id &&
             out.realm_primary_title.state_rite_id == Fixture::realm_rite_id,
             "own and realm state rites differ") ||
      !Check(out.realm_primary_title.state_faith_id == Fixture::realm_faith_id,
             "realm state faith observed independently")) return 1;
  Wire(dir, "vassal.json", out);
  f.independent = true;
  if (!Check(s::ReadPlayedStateRite12002(b, 502, out) &&
             out.top_liege_character_id == static_cast<std::uint32_t>(Fixture::actor_id) &&
             out.realm_primary_title == out.player_primary_title, "independent realm uses own title")) return 2;
  Wire(dir, "independent.json", out); f.independent = false;
  Put(f.realm_title, s::kTitleStateRiteIdOffset, std::uint32_t{0});
  Put(f.realm_rite, 8, std::uint32_t{0});
  if (!Check(s::ReadPlayedStateRite12002(b, 503, out) && out.realm_primary_title.state_rite_id == 0U,
             "realm state rite zero is observed reference")) return 3;
  Wire(dir, "state-rite-zero.json", out);
  Put(f.realm_title, s::kTitleStateRiteIdOffset, r::kAbsentReference);
  if (!Check(s::ReadPlayedStateRite12002(b, 504, out) && out.realm_primary_title.title_id &&
             !out.realm_primary_title.state_rite_id && !out.realm_primary_title.state_faith_id,
             "observed title has legal unset state rite")) return 4;
  Wire(dir, "state-rite-unset.json", out);
  Put(f.top_landed, s::kLandedTitlesCountOffset, std::int32_t{0});
  if (!Check(s::ReadPlayedStateRite12002(b, 505, out) && !out.realm_primary_title.title_id &&
             out.player_primary_title.title_id, "realm has no primary title")) return 5;
  Wire(dir, "realm-no-title.json", out);
  Put(f.actor, s::kCharacterLandedDataOffset, static_cast<void *>(nullptr));
  Put(f.top_landed, s::kLandedTitlesCountOffset, std::int32_t{1});
  Put(f.realm_title, s::kTitleStateRiteIdOffset, Fixture::realm_rite_id);
  Put(f.realm_rite, 8, Fixture::realm_rite_id);
  if (!Check(s::ReadPlayedStateRite12002(b, 506, out) && !out.player_primary_title.title_id &&
             out.realm_primary_title.state_rite_id == Fixture::realm_rite_id,
             "landless player retains realm observation")) return 6;
  Wire(dir, "landless-player.json", out);
  Put(f.actor, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(s::ReadPlayedStateRite12002(b, 507, out) && !out.actor_rite_id &&
             !out.actor_faith_id && out.realm_primary_title.state_faith_id == Fixture::realm_faith_id,
             "actor legal rite absence does not hide realm")) return 7;
  Wire(dir, "actor-rite-unset.json", out); Put(f.actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
  f.missing_state_faith = true;
  if (!Check(!s::ReadPlayedStateRite12002(b, 508, out) && !out.available &&
             out.failure == s::Failure::title_state_faith_unavailable && !out.realm_primary_title.title_id,
             "failed state faith read is unavailable, not legal absence")) return 8;
  Wire(dir, "state-faith-unavailable.json", out); f.missing_state_faith = false;
  Put(f.realm_title, s::kTitleIdentityOffset, std::uint32_t{0x03000002});
  if (!Check(!s::ReadPlayedStateRite12002(b, 509, out) &&
             out.failure == s::Failure::primary_title_unavailable, "same title index wrong generation")) return 9;
  Put(f.realm_title, s::kTitleIdentityOffset, f.top_titles[0]);
  Put(f.realm_rite, 8, std::uint32_t{0x06000008});
  if (!Check(!s::ReadPlayedStateRite12002(b, 510, out) &&
             out.failure == s::Failure::title_state_rite_unavailable, "same rite index wrong generation")) return 10;
  Put(f.realm_rite, 8, Fixture::realm_rite_id);
  Put(f.top_liege, s::kCharacterIdentityOffset, std::uint32_t{0x04000006});
  // Simulate a native top-liege callback returning a stale object, while the
  // full-generation reference stored by core still points at a newer object.
  Bytes<0x1D8> newer{}; Put(newer, s::kCharacterIdentityOffset, Fixture::top_id);
  Put(f.slots, 6 * 0x10 + 8, newer.data());
  if (!Check(!s::ReadPlayedStateRite12002(b, 511, out) &&
             out.failure == s::Failure::top_liege_unavailable, "native top-liege object must resolve through current core")) return 11;
  Put(f.slots, 6 * 0x10 + 8, f.top_liege.data()); Put(f.top_liege, s::kCharacterIdentityOffset, Fixture::top_id);
  f.jomini[0x20] = std::byte{0};
  if (!Check(!s::ReadPlayedStateRite12002(b, 512, out) &&
             out.failure == s::Failure::frame_not_paused, "paused owner only")) return 12;
  f.jomini[0x20] = std::byte{1}; f.missing_top = true;
  if (!Check(!s::ReadPlayedStateRite12002(b, 513, out) &&
             out.failure == s::Failure::top_liege_unavailable, "actual missing top-liege return")) return 13;
  const auto image = s::BindStateRiteImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(image.enabled && image.context.core.enabled &&
             reinterpret_cast<std::uintptr_t>(image.character_top_liege) == 0x1428BFDA0 &&
             reinterpret_cast<std::uintptr_t>(image.character_primary_title) == 0x14289DA30 &&
             reinterpret_cast<std::uintptr_t>(image.title_state_rite) == 0x142315030,
             "exact-build typed binder") ||
      !Check(!s::BindStateRiteImage12002(0, c::kExecutableSha256).enabled &&
             !s::BindStateRiteImage12002(0x140000000, "old-build").enabled,
             "only frozen version binds")) return 14;
  std::cout << "PASS checks=" << checks << " cases=14 actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

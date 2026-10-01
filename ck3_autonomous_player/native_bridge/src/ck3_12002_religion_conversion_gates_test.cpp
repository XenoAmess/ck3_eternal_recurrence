#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace s = r::state_rite;
namespace g = r::conversion_gates;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}, rite_storage{}; Bytes<0x100> slots{}, rite_slots{};
  Bytes<0x1D8> actor{}, liege{}; Bytes<0x200> own_land{}, realm_land{};
  Bytes<0x310> own_title{}, realm_title{};
  Bytes<0x500> actor_rite{}, target_rite{}, main_rite{}, state_rite{};
  Bytes<0xB0> actor_faith{}, target_faith{}; Bytes<0x10> actor_religion{}, target_religion{};
  Bytes<0x4> script{}; Bytes<0x30> flags{}, flag_rows{}, atom_pool{};
  std::array<std::uint32_t, 1> own_titles{0x82000001U}, realm_titles{0x83000002U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *rite_storage_ptr = rite_storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t liege_id = 0x84000006U, target_id = 0x85000007U;
  static constexpr std::uint32_t actor_faith_id = 0x86000009U, target_faith_id = 0x8700000AU;
  static constexpr std::uint32_t religion_id = 0x8800000BU, state_rite_id = 0x8900000CU;
  static constexpr std::uint32_t recent_atom = 0x07000123U;
  std::int64_t knowledge = 40'000;
  bool key_registered = true, lookup_fails = false, collection_missing = false, knowledge_fails = false;
  bool knowledge_changes = false, same_faith = false, same_religion = true;
  int knowledge_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(slots, 6 * 0x10 + 8, liege.data());
    Put(actor, s::kCharacterIdentityOffset, actor_id); Put(liege, s::kCharacterIdentityOffset, liege_id);
    Put(actor, s::kCharacterLandedDataOffset, own_land.data()); Put(liege, s::kCharacterLandedDataOffset, realm_land.data());
    Put(own_land, s::kLandedTitlesOffset, own_titles.data()); Put(realm_land, s::kLandedTitlesOffset, realm_titles.data());
    Put(own_land, s::kLandedTitlesCountOffset, std::int32_t{1}); Put(realm_land, s::kLandedTitlesCountOffset, std::int32_t{1});
    Put(own_title, s::kTitleIdentityOffset, own_titles[0]); Put(realm_title, s::kTitleIdentityOffset, realm_titles[0]);
    Put(own_title, s::kTitleStateRiteIdOffset, target_id); Put(realm_title, s::kTitleStateRiteIdOffset, state_rite_id);
    Put(actor, r::kCharacterRiteIdOffset, std::uint32_t{0}); Put(actor_rite, 8, std::uint32_t{0});
    Put(actor_rite, r::kRiteFaithIdOffset, actor_faith_id);
    Put(main_rite, 8, std::uint32_t{0x8A00000D});
    Put(target_rite, 8, target_id); Put(target_rite, r::kRiteFaithIdOffset, target_faith_id);
    Put(state_rite, 8, state_rite_id); Put(state_rite, r::kRiteFaithIdOffset, target_faith_id);
    Put(actor_faith, 8, actor_faith_id); Put(target_faith, 8, target_faith_id);
    Put(actor_faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x8A00000D});
    Put(actor_faith, r::kFaithReligionIdOffset, religion_id); Put(target_faith, r::kFaithReligionIdOffset, religion_id);
    Put(actor_religion, 8, religion_id); Put(target_religion, 8, religion_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{16});
    Put(rite_slots, 7 * 0x10 + 8, target_rite.data());
    Put(actor, g::kCharacterScriptDataOffset, script.data()); Put(script, 0, std::int32_t{4});
    Put(flags, g::kFlagRowsOffset, flag_rows.data()); Put(flags, g::kFlagCountOffset, std::int32_t{1});
    Put(flag_rows, g::kFlagKeyOffset, recent_atom);
    Put(atom_pool, 0x10, flag_rows.data()); Put(atom_pool, 0x1C, std::int32_t{15});
  }
};
Fixture *q = nullptr;
void *Player(void *) { return q->player.data(); }
void *CharacterRite(void *) { return q->actor_rite.data(); }
void *CharacterFaith(void *) { return q->actor_faith.data(); }
void *FaithMainRite(void *) { return q->main_rite.data(); }
void *RiteFaith(void *rite) { return rite == q->actor_rite.data() ? q->actor_faith.data() : q->target_faith.data(); }
void *FaithReligion(void *faith) { return faith == q->actor_faith.data() ? q->actor_religion.data() : q->target_religion.data(); }
void *TopLiege(void *) { return q->liege.data(); }
void *PrimaryTitle(void *actor) { return actor == q->actor.data() ? q->own_title.data() : q->realm_title.data(); }
void *TitleStateRite(void *title) { return title == q->own_title.data() ? q->target_rite.data() : q->state_rite.data(); }
void *FlagCollection(void *script) {
  if (script != q->script.data()) return nullptr;
  return q->collection_missing ? nullptr : q->flags.data();
}
std::uint32_t *Lookup(void *pool, std::uint32_t *out, const g::NativeStringView *key) {
  if (pool != q->atom_pool.data() || std::string_view(key->data, key->length) != g::kRecentConversionFlag ||
      key->range_comparison != 1 || q->lookup_fails) return nullptr;
  *out = q->key_registered ? Fixture::recent_atom : r::kAbsentReference;
  return out;
}
std::int64_t *Knowledge(std::int64_t *out, void *actor, void *rite) {
  if (actor != q->actor.data() || rite != q->target_rite.data() || q->knowledge_fails) return nullptr;
  *out = q->knowledge + (q->knowledge_changes ? q->knowledge_calls++ : 0);
  return out;
}
g::Bindings Bind(Fixture &fixture) {
  q = &fixture; g::Bindings b{}; b.enabled = true; b.state.enabled = true; b.state.context.enabled = true;
  b.state.context.core = {true, &q->state_ptr, &q->jomini_ptr, &q->storage_ptr, &Player};
  b.state.context.character_rite = &CharacterRite; b.state.context.character_faith = &CharacterFaith;
  b.state.context.rite_faith = &RiteFaith; b.state.context.faith_main_rite = &FaithMainRite;
  b.state.context.faith_religion = &FaithReligion;
  b.state.character_top_liege = &TopLiege; b.state.character_primary_title = &PrimaryTitle;
  b.state.title_state_rite = &TitleStateRite; b.rite_storage_slot = &q->rite_storage_ptr;
  b.rite_knowledge = &Knowledge; b.existing_atom = &Lookup; b.atom_pool = q->atom_pool.data();
  b.character_flag_collection = &FlagCollection; return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &dir, const char *name, const g::Context &out) {
  if (!dir.empty()) std::ofstream(dir/name) << g::SerializePlayedReligionConversionGates12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture f; const auto b = Bind(f); g::Context out{};
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 701, out), "actual provider read") ||
      !Check(out.knowledge_level_raw == 40'000 && out.recently_converted == true, "raw threshold and flag presence") ||
      !Check(out.target_rite_id == Fixture::target_id && out.played_character_id == Fixture::actor_id, "full target and played actor") ||
      !Check(out.same_faith == false && out.same_religion == true, "independent faith/religion identities") ||
      !Check(out.state_rite_target_match == false && out.state_faith_target_match == true, "own title cannot replace realm state rite") ||
      !Check(out.capture_epoch == 701 && out.date_raw == 53175816, "actual paused frame")) return 1;
  Wire(dir, "threshold-recent-state-faith.json", out);
  f.knowledge = 0; Put(f.flags, g::kFlagCountOffset, std::int32_t{0});
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 702, out) &&
             out.knowledge_level_raw == 0 && out.recently_converted == false && out.recent_flag_key_registered == true,
             "actual zero and known empty flags")) return 2;
  Wire(dir, "known-zero-empty-flags.json", out);
  f.knowledge = 60'001; f.key_registered = false;
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 703, out) &&
             out.knowledge_level_raw == 60'001 && out.recently_converted == false && out.recent_flag_key_registered == false,
             "native key absent is observed absence")) return 3;
  Wire(dir, "unregistered-flag-key.json", out); f.key_registered = true;
  Put(f.realm_title, s::kTitleStateRiteIdOffset, r::kAbsentReference);
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 704, out) &&
             !out.realm_state_rite_id && out.state_rite_target_match == false && out.state_faith_target_match == false,
             "legal state rite absence")) return 4;
  Wire(dir, "realm-state-unset.json", out);
  Put(f.realm_title, s::kTitleStateRiteIdOffset, Fixture::state_rite_id);
  f.collection_missing = true;
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 705, out) &&
             out.failure == g::Failure::flag_collection_unavailable && !out.recently_converted && !out.knowledge_level_raw,
             "failed flag read does not become false")) return 5;
  Wire(dir, "flag-collection-unavailable.json", out); f.collection_missing = false;
  f.knowledge_fails = true;
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 706, out) &&
             out.failure == g::Failure::knowledge_unavailable && !out.knowledge_level_raw, "knowledge failure is unknown")) return 6;
  Wire(dir, "knowledge-unavailable.json", out); f.knowledge_fails = false;
  f.knowledge_changes = true;
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 707, out) &&
             out.failure == g::Failure::state_changed, "two actual getter samples changed")) return 7;
  f.knowledge_changes = false;
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, 0x05000007, 708, out) &&
             out.failure == g::Failure::target_rite_unavailable, "same index wrong Rite generation")) return 8;
  Put(f.actor, g::kCharacterScriptDataOffset, static_cast<void *>(nullptr));
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 709, out) &&
             out.recently_converted == false, "legal no character flag data")) return 9;
  Put(f.actor, g::kCharacterScriptDataOffset, f.script.data());
  Put(f.script, 0, std::int32_t{-1});
  if (!Check(g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 710, out) &&
             out.recently_converted == false, "native empty default flag set not lazy initialized")) return 10;
  Put(f.script, 0, std::int32_t{4}); f.lookup_fails = true;
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 711, out) &&
             out.failure == g::Failure::flag_pool_unavailable, "actual atom lookup return checked")) return 11;
  f.lookup_fails = false; f.jomini[0x20] = std::byte{0};
  if (!Check(!g::ReadPlayedReligionConversionGates12002(b, Fixture::target_id, 712, out) &&
             out.failure == g::Failure::state_rite_unavailable, "existing state owner enforces pause")) return 12;
  const auto bound = g::BindReligionConversionGatesImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.rite_knowledge) == 0x142BDBDE0 &&
             reinterpret_cast<std::uintptr_t>(bound.existing_atom) == 0x143F8A3A0 &&
             reinterpret_cast<std::uintptr_t>(bound.atom_pool) == 0x145DC1390, "exact ABI source binder") ||
      !Check(!g::BindReligionConversionGatesImage12002(0, c::kExecutableSha256).enabled &&
             !g::BindReligionConversionGatesImage12002(0x140000000, "old-build").enabled, "frozen build binding")) return 13;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

#include "xar_bridge/ck3_12003_confucian_assembly_predicates.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "../tests/ck3_12003_readonly_revision_cases.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace n = xar::ck3_12003::confucian_assembly;
namespace c = xar::ck3_12002;
namespace r = xar::ck3_12002::religion;
namespace m = r::organization::members;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}, alternate_state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x2EE70);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}, title_storage{}, rite_storage{};
  Bytes<0xA0> slots{};
  Bytes<0x40> title_slots{};
  Bytes<0x60> rite_slots{};
  std::array<Bytes<0x1D8>, 4> characters{};
  std::array<Bytes<0x290>, 4> extensions{};
  Bytes<0x500> rite{}, sibling_rite{}, empty_rite{};
  Bytes<0x320> faith{}, religion{};
  std::array<Bytes<0x400>, 2> counties{};
  std::array<Bytes<0x130>, 2> titles{};
  std::array<Bytes<0x70>, 2> definitions{};
  std::array<void *, 4> alive{};
  std::array<void *, 2> county_pool{counties[0].data(), counties[1].data()};
  Bytes<0x70> trait_database{};
  Bytes<0x50> incapable_definition{};
  std::array<void *, 1> trait_rows{incapable_definition.data()};
  std::array<std::uint32_t, 3> faith_rite_ids{0x85000003U, 0x86000004U, 0x87000005U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *title_storage_ptr = title_storage.data(), *rite_storage_ptr = rite_storage.data();
  std::int32_t adult_zero = 18, adult_one = 14;
  static constexpr std::array<std::uint32_t, 4> character_ids{
      0x03000004U, 0x87000005U, 0x88000006U, 0x89000007U};
  static constexpr std::uint32_t faith_id = 0x83000002U, religion_id = 0x84000005U;
  static constexpr std::array<std::uint32_t, 2> title_ids{0x89000002U, 0x8A000003U};
  bool drift = false, duplicate = false, overflow = false, stale_member = false;
  bool empty_roster = false, omit_actor = false;
  bool late_title_kind = false, late_title_rank = false;
  int late_graph_change = 0;
  int faith_calls = 0, county_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_ids[0]);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{10});
    for (std::size_t i = 0; i < characters.size(); ++i) {
      Put(slots, (i + 4) * 16 + 8, characters[i].data());
      Put(characters[i], 0x18, character_ids[i]); Put(characters[i], 0x1C, std::uint32_t{0x43686172U});
      Put(characters[i], r::kCharacterRiteIdOffset, faith_rite_ids[0]);
      Put(characters[i], 0x68, std::int16_t{16}); Put(characters[i], 0x1A1, std::uint8_t{0});
      Put(characters[i], 0xE8, std::int32_t{12 + static_cast<std::int32_t>(i)});
      alive[i] = characters[i].data();
    }
    Put(characters[0], 0x68, std::int16_t{25});
    Put(characters[1], r::kCharacterRiteIdOffset, faith_rite_ids[1]);
    Put(characters[1], 0x1A1, std::uint8_t{1});
    Put(characters[1], 0x1B0, extensions[1].data());
    // Custody pointer deliberately exists while its jailer ID is absent. The
    // proven script trigger reports imprisoned=true without resolving jailer.
    Put(extensions[1], 0x288, reinterpret_cast<void *>(1));
    Put(characters[3], c::kCharacterDeathDataOffset, reinterpret_cast<void *>(1));
    Put(data, m::kAlivePoolOffset, alive.data()); Put(data, m::kAlivePoolSizeOffset, std::int32_t{4});
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::int32_t{6});
    const std::array<void *, 3> rites{rite.data(), sibling_rite.data(), empty_rite.data()};
    for (std::size_t i = 0; i < rites.size(); ++i) {
      std::memcpy(static_cast<std::byte *>(rites[i]) + 8, &faith_rite_ids[i], 4);
      std::memcpy(static_cast<std::byte *>(rites[i]) + r::kRiteFaithIdOffset, &faith_id, 4);
      Put(rite_slots, (i + 3) * 16 + 8, rites[i]);
    }
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id); Put(religion, 8, religion_id);
    Put(faith, 0x20, faith_rite_ids.data()); Put(faith, 0x28, std::int32_t{3}); Put(faith, 0x2C, std::int32_t{3});
    Put(religion, m::kReligionCountyPoolOffset, county_pool.data()); Put(religion, m::kReligionCountyPoolSizeOffset, std::int32_t{2});
    Put(title_storage, 0x20, title_slots.data()); Put(title_storage, 0x2C, std::int32_t{4});
    for (std::size_t i = 0; i < counties.size(); ++i) {
      Put(counties[i], 0x18, title_ids[i]); Put(counties[i], 0x384, faith_rite_ids[i]);
      Put(titles[i], m::kTitleIdentityOffset, title_ids[i]); Put(titles[i], 0x14, std::uint32_t{0x4C616E64U});
      Put(titles[i], m::kTitleTemplateOffset, definitions[i].data()); Put(definitions[i], m::kTitleTemplateRankOffset, std::int32_t{2});
      Put(title_slots, (i + 2) * 16 + 8, titles[i].data());
    }
    constexpr char key[] = "incapable";
    std::memcpy(incapable_definition.data() + 0x18, key, sizeof(key));
    Put(incapable_definition, 0x28, std::uint64_t{9}); Put(incapable_definition, 0x30, std::uint64_t{15});
    Put(trait_database, 0x50, trait_rows.data()); Put(trait_database, 0x5C, std::int32_t{1});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *character) {
  const auto id = Get<std::uint32_t>(character, r::kCharacterRiteIdOffset);
  if (id == f->faith_rite_ids[0]) return f->rite.data();
  if (id == f->faith_rite_ids[1]) return f->sibling_rite.data();
  if (id == f->faith_rite_ids[2]) return f->empty_rite.data();
  return nullptr;
}
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithReligion(void *) { return f->religion.data(); }
const void *FaithRites(void *faith) { return static_cast<std::byte *>(faith) + 0x20; }
void *TraitDatabase() { return f->trait_database.data(); }
bool HasTrait(void *character, const void *definition) {
  return definition == f->incapable_definition.data() && Get<std::uint32_t>(character, 0x18) == Fixture::character_ids[2];
}
bool Human(std::int32_t id) { return static_cast<std::uint32_t>(id) == Get<std::uint32_t>(f->entry.data(), 0xB0); }
std::int32_t Skill(void *character, std::int32_t skill) {
  return skill == 4 ? Get<std::int32_t>(character, 0xE8) : -999;
}
bool Imprisoned(void *character) {
  const auto *extension = Get<void *>(character, 0x1B0);
  return extension != nullptr && Get<void *>(extension, 0x288) != nullptr;
}
void Push(m::ScopeArray *out, std::uint16_t scope, std::uint32_t id) {
  if (out->size < out->capacity) out->data[out->size++] = {scope, 0, 0xDEADBEEFU, id};
}
void FaithCollector(void *, m::ScopeArray *out, const m::ScopeRoot *root) {
  ++f->faith_calls;
  if (root->root->kind != m::kFaithScope || f->empty_roster) return;
  for (const auto *character : f->alive) {
    if (Get<void *>(character, c::kCharacterDeathDataOffset) == nullptr &&
       !(f->omit_actor && Get<std::uint32_t>(character, 0x18) == Get<std::uint32_t>(f->entry.data(), 0xB0)))
      Push(out, m::kCharacterScope, Get<std::uint32_t>(character, 0x18));
  }
  if (f->duplicate) Push(out, m::kCharacterScope, Fixture::character_ids[0]);
  if (f->overflow) out->size = out->capacity;
  if (f->stale_member) Put(f->characters[1], 0x18, std::uint32_t{0x8B000005U});
}
void CountyCollector(void *, m::ScopeArray *out, const m::ScopeRoot *root) {
  ++f->county_calls;
  for (const auto *county : f->county_pool)
    if (Get<std::uint32_t>(county, 0x384) == root->root->identity)
      Push(out, m::kTitleScope, Get<std::uint32_t>(county, 0x18));
  if (f->drift) Put(f->state, 8, std::int32_t{53175817});
  if (f->county_calls == 4 && f->late_title_kind) Put(f->titles[0], 0x14, std::uint32_t{0});
  if (f->county_calls == 4 && f->late_title_rank) Put(f->definitions[0], m::kTitleTemplateRankOffset, std::int32_t{3});
  if (f->county_calls == 6) {
    if (f->late_graph_change == 1) Put(f->rite, r::kRiteFaithIdOffset, Fixture::faith_id + 1);
    if (f->late_graph_change == 2) Put(f->faith, r::kFaithReligionIdOffset, Fixture::religion_id + 1);
    if (f->late_graph_change == 3) Put(f->religion, 8, Fixture::religion_id + 1);
    if (f->late_graph_change == 4) Put(f->state, 0xA0, static_cast<void *>(nullptr));
    if (f->late_graph_change == 5) { f->alternate_state = f->state; f->state_ptr = f->alternate_state.data(); }
  }
}
n::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  n::Bindings b;
  b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.traits.enabled = true; b.traits.get_trait_database = &TraitDatabase;
  b.traits.character_has_trait = &HasTrait; b.traits.is_human_player_character = &Human;
  b.rite_storage_slot = &f->rite_storage_ptr; b.title_storage_slot = &f->title_storage_ptr;
  b.character_rite = &CharacterRite; b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion;
  b.faith_rites = &FaithRites; b.faith_characters = &FaithCollector; b.rite_counties = &CountyCollector;
  b.effective_skill = &Skill; b.adult_threshold_zero = &f->adult_zero; b.adult_threshold_one = &f->adult_one;
  b.is_imprisoned = &Imprisoned;
  return b;
}
int checks = 0;
bool Check(bool condition, const char *message) { ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition; }
void Wire(const std::filesystem::path &directory, const char *name, const n::Snapshot &snapshot) {
  if (!directory.empty()) std::ofstream(directory / name) << n::Serialize(snapshot) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  if (!xar::ck3_12003::readonly_query::source_tests::VerifyRevisionParsing(&Check)) return 14;
  Fixture fixture;
  auto b = Bind(fixture);
  n::Snapshot out;
  if (!Check(n::ReadCurrentFaithPredicates(b, 501, out) && out.available && out.predicates_complete, "complete native collection and predicates") ||
      !Check(out.complete_native_faith_member_ids == std::vector<std::uint32_t>{Fixture::character_ids[0], Fixture::character_ids[1], Fixture::character_ids[2]}, "full generation Faith roster including high-bit identities") ||
      !Check(out.complete_native_faith_rite_ids.size() == 3 && out.rites.size() == 3 && out.rites[2].complete && out.rites[2].county_title_ids.empty(), "every Faith Rite and native known empty county count") ||
      !Check(out.members[0].adult == true && out.members[1].adult == true && out.members[2].adult == false, "selected runtime thresholds rather than hardcoded age16") ||
      !Check(out.members[0].is_ai == false && out.members[1].is_ai == true && out.members[2].is_ai == true, "actual complete human/NPC predicates") ||
      !Check(out.members[1].imprisoned == true && out.members[0].imprisoned == false, "exact imprisoned predicate ignores jailer validity") ||
      !Check(out.members[2].incapable == true && out.members[0].incapable == false && out.members[1].effective_learning == 13, "concrete trait lookup and effective learning") ||
      !Check(fixture.faith_calls == 2 && fixture.county_calls == 6, "second full collection closes same-frame graph")) return 1;
  Wire(directory, "complete.json", out);
  b.is_imprisoned = nullptr;
  if (!Check(n::ReadCurrentFaithPredicates(b, 502, out) && out.available && !out.predicates_complete && !out.members[0].imprisoned &&
      n::Serialize(out).find("\"imprisoned\":null") != std::string::npos, "unavailable imprisoned stays UNKNOWN")) return 2;
  Wire(directory, "imprisoned-unknown.json", out);
  b.is_imprisoned = &Imprisoned;
  fixture.duplicate = true;
  if (!Check(!n::ReadCurrentFaithPredicates(b, 503, out) && !out.available && n::Serialize(out).find("\"members\":null") != std::string::npos, "duplicate enumeration rejected without empty-success substitute")) return 3;
  fixture.duplicate = false;
  fixture.overflow = true;
  if (!Check(!n::ReadCurrentFaithPredicates(b, 504, out) && !out.available, "collector exhaustion stays unavailable")) return 4;
  fixture.overflow = false;
  fixture.drift = true;
  if (!Check(!n::ReadCurrentFaithPredicates(b, 505, out) && !out.available, "frame drift discards apparently valid roster")) return 5;
  fixture.drift = false; Put(fixture.state, 8, std::int32_t{53175816});
  Put(fixture.characters[1], 0x1A1, std::uint8_t{2});
  if (!Check(n::ReadCurrentFaithPredicates(b, 506, out) && out.available && !out.predicates_complete && !out.members[1].adult, "unknown threshold selector remains UNKNOWN")) return 6;
  Put(fixture.characters[1], 0x1A1, std::uint8_t{1});
  fixture.stale_member = true;
  if (!Check(!n::ReadCurrentFaithPredicates(b, 507, out) && !out.available, "generation changed during collector cannot receive valid predicate credit")) return 7;
  fixture.stale_member = false; Put(fixture.characters[1], 0x18, Fixture::character_ids[1]);
  {
    Fixture high_actor; auto high_bindings = Bind(high_actor);
    constexpr std::uint32_t high_id = 0x83000004U;
    Put(high_actor.entry, 0xB0, high_id); Put(high_actor.characters[0], 0x18, high_id);
    if (!Check(n::ReadCurrentFaithPredicates(high_bindings, 510, out) && out.available && out.predicates_complete &&
       static_cast<std::uint32_t>(out.played_character_id) == high_id && out.members[0].is_ai == false, "high-bit played actor preserved")) return 10;
  }
  for (int mode = 0; mode < 2; ++mode) {
    Fixture incomplete; incomplete.empty_roster = mode == 0; incomplete.omit_actor = mode == 1;
    if (!Check(!n::ReadCurrentFaithPredicates(Bind(incomplete), 511, out) && !out.available &&
       n::Serialize(out).find("\"members\":null") != std::string::npos, "empty or actor-omitting native roster cannot be complete")) return 11;
  }
  for (int mode = 0; mode < 2; ++mode) {
    Fixture changed; changed.late_title_kind = mode == 0; changed.late_title_rank = mode == 1;
    if (!Check(!n::ReadCurrentFaithPredicates(Bind(changed), 512, out) && !out.available, "county kind or exact rank changed in closure")) return 12;
  }
  for (int mode = 1; mode <= 5; ++mode) {
    Fixture changed; changed.late_graph_change = mode;
    if (!Check(!n::ReadCurrentFaithPredicates(Bind(changed), 513, out) && !out.available, "late Faith relation or state/data-pointer change rejected")) return 13;
  }
  (void)Bind(fixture);
  fixture.jomini[0x20] = std::byte{0};
  if (!Check(!n::ReadCurrentFaithPredicates(b, 508, out), "unpaused observation unavailable")) return 8;
  const auto exact = n::BindImage(0x140000000ULL, xar::ck3_12003::kExecutableSha256);
  if (!Check(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.faith_characters) == 0x141C610E0ULL &&
      reinterpret_cast<std::uintptr_t>(exact.effective_skill) == 0x1428B16B0ULL, "exactcurrent binder addresses") ||
      !Check(!n::BindImage(0x140000000ULL, c::kExecutableSha256).enabled && !n::BindImage(0, xar::ck3_12003::kExecutableSha256).enabled, "old build and zero image rejected")) return 9;
  std::cout << "PASS checks=" << checks << " actual_reader=true actual_serializer=true live=false\n";
  return 0;
}

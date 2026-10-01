#include "xar_bridge/religion_rite_governance12002_organization_members.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace m = xar::ck3_12002::religion::organization::members;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &bytes, std::size_t at, T value) {
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
  std::vector<std::byte> data = std::vector<std::byte>(0x2EE70);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{}, title_storage{};
  Bytes<0xA0> slots{};
  Bytes<0x40> title_slots{};
  std::array<Bytes<0x1D8>, 5> characters{};
  Bytes<0x500> rite{}, sibling_rite{}, other_rite{};
  Bytes<0x320> faith{}, other_faith{}, religion{};
  std::array<Bytes<0x400>, 2> counties{};
  std::array<Bytes<0x120>, 2> titles{};
  std::array<Bytes<0x70>, 2> definitions{};
  std::array<void *, 5> alive{};
  std::array<void *, 2> county_pool{counties[0].data(), counties[1].data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *title_storage_ptr = title_storage.data();
  static constexpr std::array<std::uint32_t, 5> character_ids{
      0x03000004, 0x87000005, 0x88000006, 0x89000007, 0x8A000008};
  static constexpr std::uint32_t rite_id = 0x85000003, sibling_rite_id = 0x86000004,
      other_rite_id = 0x87000005, faith_id = 0x83000002, other_faith_id = 0x84000003,
      religion_id = 0x84000005;
  static constexpr std::array<std::uint32_t, 2> title_ids{0x89000002, 0x8A000003};
  bool invalid_output = false, drift = false;
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
      Put(characters[i], 0x18, character_ids[i]);
      Put(characters[i], r::kCharacterRiteIdOffset, rite_id); alive[i] = characters[i].data();
    }
    Put(characters[1], r::kCharacterRiteIdOffset, sibling_rite_id);
    Put(characters[3], c::kCharacterDeathDataOffset, reinterpret_cast<void *>(1));
    Put(characters[4], r::kCharacterRiteIdOffset, other_rite_id);
    Put(data, m::kAlivePoolOffset, alive.data()); Put(data, m::kAlivePoolSizeOffset, std::int32_t{5});
    Put(rite, 8, rite_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(sibling_rite, 8, sibling_rite_id); Put(sibling_rite, r::kRiteFaithIdOffset, faith_id);
    Put(other_rite, 8, other_rite_id); Put(other_rite, r::kRiteFaithIdOffset, other_faith_id);
    Put(faith, 8, faith_id); Put(other_faith, 8, other_faith_id);
    Put(faith, r::kFaithReligionIdOffset, religion_id); Put(religion, 8, religion_id);
    Put(religion, m::kReligionCountyPoolOffset, county_pool.data());
    Put(religion, m::kReligionCountyPoolSizeOffset, std::int32_t{2});
    Put(title_storage, 0x20, title_slots.data()); Put(title_storage, 0x2C, std::int32_t{4});
    for (std::size_t i = 0; i < counties.size(); ++i) {
      Put(counties[i], 0x18, title_ids[i]); Put(counties[i], 0x384, rite_id);
      Put(titles[i], m::kTitleIdentityOffset, title_ids[i]);
      Put(titles[i], m::kTitleTemplateOffset, definitions[i].data());
      Put(definitions[i], m::kTitleTemplateRankOffset, std::int32_t{2});
      Put(title_slots, (i + 2) * 16 + 8, titles[i].data());
    }
    Put(counties[1], 0x384, sibling_rite_id);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *character) {
  const auto id = Get<std::uint32_t>(character, r::kCharacterRiteIdOffset);
  if (id == Fixture::rite_id) return f->rite.data();
  if (id == Fixture::sibling_rite_id) return f->sibling_rite.data();
  if (id == Fixture::other_rite_id) return f->other_rite.data();
  return nullptr;
}
void *RiteFaith(void *rite) {
  return Get<std::uint32_t>(rite, r::kRiteFaithIdOffset) == Fixture::faith_id ? f->faith.data() : f->other_faith.data();
}
void *FaithReligion(void *) { return f->religion.data(); }
bool Push(m::ScopeArray *out, std::uint16_t scope, std::uint32_t id) {
  if (out->size == out->capacity) return false;
  out->data[out->size++] = {scope, 0, 0, id}; return true;
}
void FaithCollector(void *, m::ScopeArray *out, const m::ScopeRoot *root) {
  ++f->faith_calls;
  if (root->root->kind != m::kFaithScope) return;
  const auto count = Get<std::int32_t>(f->data.data(), m::kAlivePoolSizeOffset);
  for (int i = 0; i < count; ++i) {
    auto *character = f->alive[static_cast<std::size_t>(i)];
    auto *rite = CharacterRite(character);
    if (rite && Get<std::uint32_t>(rite, r::kRiteFaithIdOffset) == root->root->identity &&
        !Get<void *>(character, c::kCharacterDeathDataOffset))
      (void)Push(out, f->invalid_output ? m::kTitleScope : m::kCharacterScope,
                 Get<std::uint32_t>(character, 0x18));
  }
}
void CountyCollector(void *, m::ScopeArray *out, const m::ScopeRoot *root) {
  ++f->county_calls;
  if (root->root->kind != m::kRiteScope) return;
  const auto count = Get<std::int32_t>(f->religion.data(), m::kReligionCountyPoolSizeOffset);
  for (int i = 0; i < count; ++i) {
    const auto *county = f->county_pool[static_cast<std::size_t>(i)];
    if (Get<std::uint32_t>(county, 0x384) == root->root->identity)
      (void)Push(out, m::kTitleScope, Get<std::uint32_t>(county, 0x18));
  }
  if (f->drift) Put(f->state, 8, std::int32_t{53175817});
}
m::Bindings Bind(Fixture &q) {
  f = &q; m::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion;
  b.title_storage_slot = &f->title_storage_ptr;
  b.faith_characters = &FaithCollector; b.rite_counties = &CountyCollector; return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &dir, const char *name, const m::Snapshot &out) {
  if (!dir.empty()) std::ofstream(dir / name) << m::SerializePlayedOrganizationMembers12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); m::Snapshot out{};
  if (!Check(m::ReadPlayedOrganizationMembers12002(b, 101, out), "production collector reader") ||
      !Check(out.rite_id == Fixture::rite_id && out.faith_id == Fixture::faith_id &&
             out.religion_id == Fixture::religion_id, "full religion identities") ||
      !Check(out.faith_character_ids == std::vector<std::uint32_t>{Fixture::character_ids[0],
                 Fixture::character_ids[1], Fixture::character_ids[2]}, "Faith includes sibling Rite, excludes dead and other Faith") ||
      !Check(out.rite_character_ids == std::vector<std::uint32_t>{Fixture::character_ids[0], Fixture::character_ids[2]},
             "exact Rite membership projection") ||
      !Check(out.county_title_ids == std::vector<std::uint32_t>{Fixture::title_ids[0]},
             "full county title ID and exact Rite filter") ||
      !Check(q.faith_calls == 1 && q.county_calls == 1, "actual native collector callbacks")) return 1;
  Wire(directory, "current-members.json", out);
  Put(q.data, m::kAlivePoolSizeOffset, std::int32_t{0});
  Put(q.religion, m::kReligionCountyPoolSizeOffset, std::int32_t{0});
  if (!Check(m::ReadPlayedOrganizationMembers12002(b, 102, out) && out.faith_character_ids.empty() &&
             out.rite_character_ids.empty() && out.county_title_ids.empty(), "known empty pools")) return 2;
  Wire(directory, "known-empty.json", out);
  Put(q.data, m::kAlivePoolSizeOffset, std::int32_t{5});
  Put(q.religion, m::kReligionCountyPoolSizeOffset, std::int32_t{2});
  Put(q.titles[0], m::kTitleIdentityOffset, std::uint32_t{0x8B000002});
  if (!Check(!m::ReadPlayedOrganizationMembers12002(b, 103, out) && out.county_title_ids.empty() &&
             out.failure == m::Failure::county_title_unavailable, "title generation mismatch is unavailable")) return 3;
  Wire(directory, "title-unavailable.json", out); Put(q.titles[0], m::kTitleIdentityOffset, Fixture::title_ids[0]);
  q.invalid_output = true;
  if (!Check(!m::ReadPlayedOrganizationMembers12002(b, 104, out) &&
             out.failure == m::Failure::native_output_unavailable, "actual wrong-kind native row")) return 4;
  q.invalid_output = false;
  Put(q.definitions[0], m::kTitleTemplateRankOffset, std::int32_t{3});
  if (!Check(!m::ReadPlayedOrganizationMembers12002(b, 105, out) &&
             out.failure == m::Failure::county_title_unavailable, "duchy is not county")) return 5;
  Put(q.definitions[0], m::kTitleTemplateRankOffset, std::int32_t{2}); q.drift = true;
  if (!Check(!m::ReadPlayedOrganizationMembers12002(b, 106, out) &&
             out.failure == m::Failure::state_changed, "actual frame changed")) return 6;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!m::ReadPlayedOrganizationMembers12002(b, 107, out) &&
             out.failure == m::Failure::frame_not_paused, "paused owner frame only")) return 7;
  q.jomini[0x20] = std::byte{1}; Put(q.characters[0], r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(m::ReadPlayedOrganizationMembers12002(b, 108, out) && !out.rite_id &&
             out.county_title_ids.empty(), "legal no Rite")) return 8;
  Wire(directory, "legal-no-rite.json", out);
  const auto actual = m::BindOrganizationMembersImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
             reinterpret_cast<std::uintptr_t>(actual.faith_characters) == 0x141C610E0 &&
             reinterpret_cast<std::uintptr_t>(actual.rite_counties) == 0x141D2B6F0 &&
             reinterpret_cast<std::uintptr_t>(actual.title_storage_slot) == 0x145D1DAF8,
             "actual exact binder") ||
      !Check(!m::BindOrganizationMembersImage12002(0x140000000, "old").enabled, "version-bound binder")) return 9;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

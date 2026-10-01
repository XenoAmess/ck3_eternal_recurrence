#include "xar_bridge/religion_rite_governance12002_organization.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion;
namespace o = r::organization;
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
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> rite{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t rite_id = 0x85000003;
  bool missing_rite = false, drift = false;
  int follower_reads = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, rite_id);
    Put(rite, 8, rite_id); Put(rite, o::kCountyCountOffset, std::int32_t{17});
    Put(rite, o::kCharacterFollowerCountOffset, std::int32_t{353});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->missing_rite ? nullptr : f->rite.data(); }
std::int32_t Counties(void *rite) { return Get<std::int32_t>(rite, o::kCountyCountOffset); }
std::int32_t Followers(void *rite) {
  auto value = Get<std::int32_t>(rite, o::kCharacterFollowerCountOffset);
  if (f->drift && (++f->follower_reads % 2 == 0)) ++value;
  return value;
}
o::Bindings Bind(Fixture &q) {
  f = &q; o::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.county_count = &Counties; b.character_follower_count = &Followers;
  return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const o::Counts &out) {
  if (!directory.empty()) std::ofstream(directory / name) << o::SerializePlayedOrganizationCounts12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); o::Counts out{};
  if (!Check(o::ReadPlayedOrganizationCounts12002(b, 88, out) && out.available, "production reader") ||
      !Check(out.rite_id == Fixture::rite_id, "full high-bit generation") ||
      !Check(out.county_count == 17 && out.character_follower_count == 353, "native count callbacks") ||
      !Check(out.capture_epoch == 88 && out.date_raw == 53175816 &&
             out.played_character_id == Fixture::character_id, "actual frame")) return 1;
  Wire(directory, "current-counts.json", out);
  Put(q.rite, o::kCountyCountOffset, std::int32_t{0});
  Put(q.rite, o::kCharacterFollowerCountOffset, std::int32_t{0});
  if (!Check(o::ReadPlayedOrganizationCounts12002(b, 89, out) && out.county_count == 0 &&
             out.character_follower_count == 0, "observed zeros remain zero")) return 2;
  Wire(directory, "current-zero.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(o::ReadPlayedOrganizationCounts12002(b, 90, out) && !out.rite_id && !out.county_count &&
             !out.character_follower_count, "legal no rite is distinct from zero")) return 3;
  Wire(directory, "legal-absent.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::rite_id); q.missing_rite = true;
  if (!Check(!o::ReadPlayedOrganizationCounts12002(b, 91, out) && !out.available &&
             out.failure == o::Failure::rite_unavailable && !out.county_count,
             "present reference has missing object")) return 4;
  Wire(directory, "rite-unavailable.json", out); q.missing_rite = false;
  Put(q.rite, 8, std::uint32_t{0x86000003});
  if (!Check(!o::ReadPlayedOrganizationCounts12002(b, 92, out) &&
             out.failure == o::Failure::rite_unavailable, "generation mismatch")) return 5;
  Put(q.rite, 8, Fixture::rite_id); q.drift = true;
  if (!Check(!o::ReadPlayedOrganizationCounts12002(b, 93, out) &&
             out.failure == o::Failure::state_changed, "actual count changed during two reads")) return 6;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!o::ReadPlayedOrganizationCounts12002(b, 94, out) &&
             out.failure == o::Failure::frame_not_paused, "only current paused actor")) return 7;
  q.jomini[0x20] = std::byte{1}; b.county_count = nullptr;
  if (!Check(!o::ReadPlayedOrganizationCounts12002(b, 95, out) &&
             out.failure == o::Failure::bindings_unavailable, "missing getter unavailable")) return 8;
  const auto actual = o::BindOrganizationImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
             reinterpret_cast<std::uintptr_t>(actual.county_count) == 0x140B80410 &&
             reinterpret_cast<std::uintptr_t>(actual.character_follower_count) == 0x140EDDB90 &&
             reinterpret_cast<std::uintptr_t>(actual.character_rite) == 0x1428D2F90,
             "actual exact image binder") ||
      !Check(!o::BindOrganizationImage12002(0x140000000, "old").enabled &&
             !o::BindOrganizationImage12002(0, c::kExecutableSha256).enabled,
             "version-bound binder")) return 9;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

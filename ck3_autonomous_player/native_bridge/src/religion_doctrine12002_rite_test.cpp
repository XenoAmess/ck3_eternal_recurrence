#include "xar_bridge/religion_doctrine12002_rite.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace d = xar::ck3_12002::religion::doctrine12002;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t at, T value) {
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
  Bytes<0x1D8> character{};
  Bytes<0x7C0> rite{}, main_rite{};
  Bytes<0x320> faith{};
  Bytes<0xB10> rite_definition{}, inherited_definition{}, mainline_definition{};
  Bytes<0x40> head_group{}, clergy_group{};
  std::string long_doctrine = "doctrine_head_of_faith_spiritual";
  std::string long_mainline = "doctrine_head_of_faith_temporal";
  std::string long_group = "doctrine_group_head_of_faith";
  std::string escaped_doctrine = "教义\"\n";
  std::array<const void *, 2> definitions{rite_definition.data(), inherited_definition.data()};
  std::array<const void *, 1> main_definitions{mainline_definition.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t rite_id = 0x85000006, faith_id = 0x83000003;
  bool missing_rite = false, missing_faith = false, drift = false;
  int rite_calls = 0;
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
    Put(rite, 8, rite_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x86000007});
    Put(main_rite, 8, std::uint32_t{0x86000007});
    Collection(2); Put(main_rite, d::kRiteEffectiveDoctrineDataOffset, main_definitions.data());
    Put(main_rite, d::kRiteEffectiveDoctrineCapacityOffset, std::int32_t{1});
    Put(main_rite, d::kRiteEffectiveDoctrineCountOffset, std::int32_t{1});
    Tag(rite_definition, 0x18, long_doctrine); Tag(mainline_definition, 0x18, long_mainline);
    Tag(inherited_definition, 0x18, escaped_doctrine); Tag(head_group, 0x18, long_group);
    Tag(clergy_group, 0x18, std::string_view("clergy_gender"));
    Put(rite_definition, 0xB08, head_group.data()); Put(mainline_definition, 0xB08, head_group.data());
    Put(inherited_definition, 0xB08, clergy_group.data());
  }
  void Collection(std::int32_t count) {
    Put(rite, d::kRiteEffectiveDoctrineDataOffset, definitions.data());
    Put(rite, d::kRiteEffectiveDoctrineCapacityOffset, std::int32_t{2});
    Put(rite, d::kRiteEffectiveDoctrineCountOffset, count);
  }
  template <typename Buffer> static void Tag(Buffer &object, std::size_t at, std::string_view value) {
    if (value.size() < 16) std::memcpy(object.data() + at, value.data(), value.size());
    else Put(object, at, value.data());
    Put(object, at + 0x10, static_cast<std::uint64_t>(value.size()));
    Put(object, at + 0x18, static_cast<std::uint64_t>(value.size() < 16 ? 15 : value.size()));
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) {
  if (f->drift && ++f->rite_calls == 2) f->definitions[0] = f->mainline_definition.data();
  return f->missing_rite ? nullptr : f->rite.data();
}
void *Faith(void *) { return f->missing_faith ? nullptr : f->faith.data(); }
r::Bindings Bind(Fixture &fixture) {
  f = &fixture; r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &Faith; b.rite_faith = &Faith;
  return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const d::RiteDoctrineSnapshot &out) {
  std::ofstream(directory / name) << d::SerializeRiteDoctrines12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 90;
  const std::filesystem::path directory(argv[1]);
  Fixture q; auto b = Bind(q); d::RiteDoctrineSnapshot out{};
  if (!Check(d::ReadPlayedRiteDoctrines12002(b, 301, out), "actual current Rite reader") ||
      !Check(out.available && out.capture_epoch == 301 && out.date_raw == 53175816, "observed frame") ||
      !Check(out.played_character_id == Fixture::character_id && out.rite_id == Fixture::rite_id &&
             out.faith_id == Fixture::faith_id, "full-generation actor/Rite/Faith refs") ||
      !Check(out.rows.size() == 2, "actual count, not capacity or Tenet list") ||
      !Check(out.rows[0].doctrine_key == q.long_doctrine && out.rows[0].group_key == q.long_group,
             "heap native definition/group CString copied") ||
      !Check(out.rows[1].doctrine_key == q.escaped_doctrine && out.rows[1].group_key == "clergy_gender",
             "SSO UTF-8 quote and newline copied") ||
      !Check(out.rows[0].source == "rite_effective", "honest effective scope provenance") ||
      !Check(d::HasRiteDoctrineByStableKey12002(out, q.long_doctrine), "current effective membership") ||
      !Check(!d::HasRiteDoctrineByStableKey12002(out, q.long_mainline), "same-group main Rite is not substituted") ||
      !Check(!d::HasRiteDoctrineByStableKey12002(out, "tenet_test"), "strict Doctrine is not compatibility Tenet query")) return 1;
  Wire(directory, "rite-effective.json", out);
  q.Collection(0);
  if (!Check(d::ReadPlayedRiteDoctrines12002(b, 302, out) && out.available && out.rows.empty(),
             "known empty native array")) return 2;
  Wire(directory, "known-empty.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedRiteDoctrines12002(b, 303, out) && out.available && !out.rite_id &&
             !out.faith_id && out.rows.empty(), "legal Rite absence distinct from unavailable")) return 3;
  Wire(directory, "legal-absent.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::rite_id); q.Collection(2);
  Put(q.rite, r::kRiteFaithIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedRiteDoctrines12002(b, 304, out) && out.rows.size() == 2 && !out.faith_id,
             "Rite rows remain independent from absent parent Faith")) return 4;
  Put(q.rite, r::kRiteFaithIdOffset, Fixture::faith_id); q.missing_rite = true;
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 305, out) && out.unavailable_reason == "rite_unavailable",
             "failed current Rite getter")) return 5;
  Wire(directory, "rite-unavailable.json", out); q.missing_rite = false;
  q.missing_faith = true;
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 306, out) && out.unavailable_reason == "faith_unavailable",
             "actual parent Faith failure")) return 6;
  q.missing_faith = false;
  Put(q.rite, 8, std::uint32_t{0x86000006});
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 307, out) && out.unavailable_reason == "rite_unavailable",
             "same index different generation rejected")) return 7;
  Put(q.rite, 8, Fixture::rite_id); q.Collection(-1);
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 308, out) && out.unavailable_reason == "doctrine_collection_unavailable",
             "malformed signed collection count")) return 8;
  q.Collection(3);
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 309, out) && out.unavailable_reason == "doctrine_collection_unavailable",
             "actual count exceeds actual capacity")) return 9;
  q.Collection(2); q.definitions[1] = nullptr;
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 310, out) && out.unavailable_reason == "doctrine_definition_unavailable" &&
             out.rows.empty(), "native definition read failure is not partial successful state") ||
      !Check(!d::HasRiteDoctrineByStableKey12002(out, q.long_doctrine), "unavailable does not provide known membership")) return 10;
  q.definitions[1] = q.inherited_definition.data(); q.drift = true; q.rite_calls = 0;
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 311, out) && out.unavailable_reason == "state_changed",
             "actual two reads disagree")) return 11;
  q.drift = false; q.definitions[0] = q.rite_definition.data(); q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 312, out) && out.unavailable_reason == "frame_not_paused",
             "actual owner frame must be paused")) return 12;
  q.jomini[0x20] = std::byte{1}; b.character_rite = nullptr;
  if (!Check(!d::ReadPlayedRiteDoctrines12002(b, 313, out) && out.unavailable_reason == "bindings_unavailable",
             "required native getter unavailable")) return 13;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

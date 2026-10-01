#include "xar_bridge/conversion_outcome12002_actor.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace a = xar::ck3_12002::religion_conversion::outcome::actor;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{};
  Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_db{}; Bytes<0x80> character_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> rite{}, main_rite{};
  Bytes<0x320> faith{}, resources{};
  Bytes<0x40> religion{}; Bytes<0x50> religion_definition{};
  Bytes<0xB0> spiritual_extension{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *character_db_ptr = character_db.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  bool fail_resources = false, fail_faith = false, frame_drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_db, 0x20, character_slots.data()); Put(character_db, 0x2C, std::uint32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0}); Put(character, 0x1B0, resources.data());
    Put(character, 0x1C8, spiritual_extension.data());
    Put(rite, 8, std::uint32_t{0}); Put(rite, 0x4B8, std::uint32_t{0x83000003});
    Put(faith, 8, std::uint32_t{0x83000003}); Put(faith, 0x8C, std::uint32_t{0x84000005});
    Put(faith, 0x98, std::uint32_t{0x02000002}); Put(main_rite, 8, std::uint32_t{0x02000002});
    Put(faith, 0x2F8, std::int64_t{12345}); Tag(faith, 0xE0, "old_faith");
    Put(religion, 8, std::uint32_t{0x84000005}); Put(religion, 0x20, religion_definition.data());
    Tag(religion_definition, 0x28, "old_religion");
    Put(spiritual_extension, 0xA0, std::int64_t{1110000});
    Put(resources, 0x100, std::int64_t{-123456});
    Put(resources, 0x130, std::int64_t{-7654321}); Put(resources, 0x110, std::int64_t{0});
  }
  template <typename B> static void Tag(B &b, std::size_t at, std::string_view value) {
    std::memcpy(b.data() + at, value.data(), value.size());
    Put(b, at + 0x10, static_cast<std::uint64_t>(value.size())); Put(b, at + 0x18, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->rite.data(); }
void *CharacterFaith(void *) { return f->fail_faith ? nullptr : f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithReligion(void *) { return f->religion.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
std::int64_t *Fervor(void *object, std::int64_t *out) { *out = Get<std::int64_t>(object, 0x2F8); return out; }
std::int64_t *Fulfillment(void *, std::int64_t *out) {
  *out = Get<std::int64_t>(f->spiritual_extension.data(), 0xA0); return out;
}
const void *FaithTag(void *object) { return static_cast<const std::byte *>(object) + 0xE0; }
const void *ReligionTag(void *) { return f->religion_definition.data() + 0x28; }
bool ResourceRead(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  if (f->fail_resources) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  if (f->frame_drift && address == reinterpret_cast<std::uintptr_t>(f->resources.data()) + 0x110)
    Put(f->state, 8, std::int32_t{53175817});
  return true;
}
a::Bindings Bind(Fixture &fixture) {
  f = &fixture; a::Bindings b{}; auto &q = b.current_religion; q.enabled = true;
  q.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_db_ptr, &Player};
  q.character_rite = &CharacterRite; q.character_faith = &CharacterFaith; q.rite_faith = &RiteFaith;
  q.faith_religion = &FaithReligion; q.faith_main_rite = &FaithMainRite;
  q.faith_fervor = &Fervor; q.character_spiritual_fulfillment = &Fulfillment;
  q.faith_tag = &FaithTag; q.religion_tag = &ReligionTag;
  b.read_memory = &ResourceRead; return b;
}
int checks = 0;
bool Check(bool ok, const char *message) {
  ++checks; if (!ok) std::cerr << "FAIL " << message << '\n'; return ok;
}
void Wire(const std::filesystem::path &dir, const char *name, const a::Context &context) {
  if (!dir.empty()) std::ofstream(dir / name) << a::SerializeConversionOutcomeActor12002(context) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); a::Context before{}, after{};
  if (!Check(a::ReadPlayedConversionOutcomeActor12002(b, 11, before), "before independent current sample") ||
      !Check(before.current_religion.available && before.current_religion.rite_id == 0u &&
      before.current_religion.faith_id == 0x83000003 && before.current_religion.religion_id == 0x84000005,
      "full current identities including legitimate Rite zero") ||
      !Check(before.piety_raw == 0 && before.gold_raw == -123456 && before.prestige_raw == -7654321,
      "signed current piety gold prestige values") ||
      !Check(before.current_religion.spiritual_fulfillment_raw == 1110000,
      "independent fulfillment separate from wallet")) return 1;
  Wire(dir, "before.json", before);
  Put(q.character, 0xB4, std::uint32_t{0x87000002}); Put(q.rite, 8, std::uint32_t{0x87000002});
  Put(q.rite, 0x4B8, std::uint32_t{0x85000003}); Put(q.faith, 8, std::uint32_t{0x85000003});
  Put(q.faith, 0x8C, std::uint32_t{0x88000005}); Put(q.religion, 8, std::uint32_t{0x88000005});
  Fixture::Tag(q.faith, 0xE0, "new_faith"); Fixture::Tag(q.religion_definition, 0x28, "new_religion");
  Put(q.resources, 0x100, std::int64_t{9876543}); Put(q.resources, 0x130, std::int64_t{3456789});
  Put(q.resources, 0x110, std::int64_t{-17012345}); Put(q.spiritual_extension, 0xA0, std::int64_t{-223456});
  if (!Check(a::ReadPlayedConversionOutcomeActor12002(b, 12, after), "after independent current sample") ||
      !Check(after.current_religion.rite_id == 0x87000002 && after.current_religion.faith_id == 0x85000003 &&
      after.current_religion.religion_id == 0x88000005 && after.current_religion.faith_key == "new_faith",
      "read changed current identities, not a copied target or ACK") ||
      !Check(after.piety_raw == -17012345 && after.gold_raw == 9876543 && after.prestige_raw == 3456789 &&
      after.current_religion.spiritual_fulfillment_raw == -223456,
      "read actual changed counters without quoted fee or fixed gain") ||
      !Check(before.current_religion.rite_id == 0u && before.gold_raw == -123456,
      "previous sample owns values")) return 2;
  Wire(dir, "after.json", after);
  Put(q.character, 0x1B0, static_cast<void *>(nullptr));
  if (!Check(a::ReadPlayedConversionOutcomeActor12002(b, 13, after) && after.piety_raw == 0 &&
      after.gold_raw == 0 && after.prestige_raw == 0, "native legal absent-resource zero")) return 3;
  Wire(dir, "legal-zero-wallet.json", after);
  q.fail_resources = true;
  if (!Check(!a::ReadPlayedConversionOutcomeActor12002(b, 14, after) &&
      after.failure == a::Failure::resources_unavailable && !after.piety_raw && !after.gold_raw &&
      after.current_religion.available, "failed resource read is null, preserved observed context")) return 4;
  Wire(dir, "resources-unavailable.json", after);
  q.fail_resources = false; q.fail_faith = true;
  if (!Check(!a::ReadPlayedConversionOutcomeActor12002(b, 15, after) &&
      after.failure == a::Failure::current_religion_unavailable && !after.piety_raw &&
      after.current_religion.failure == r::Failure::faith_unavailable,
      "actual nested religion failure remains visible")) return 5;
  q.fail_faith = false; Put(q.character, 0x1B0, q.resources.data()); q.frame_drift = true;
  if (!Check(!a::ReadPlayedConversionOutcomeActor12002(b, 16, after) &&
      after.failure == a::Failure::state_changed && !after.piety_raw,
      "resource and religion sample bind to one paused player date")) return 6;
  q.frame_drift = false; q.jomini[0x20] = std::byte{};
  if (!Check(!a::ReadPlayedConversionOutcomeActor12002(b, 17, after) &&
      after.failure == a::Failure::frame_not_paused, "paused owner sampling")) return 7;
  const auto native = a::BindConversionOutcomeActorImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(native.current_religion.enabled && native.current_religion.core.enabled && native.read_memory &&
      reinterpret_cast<std::uintptr_t>(native.current_religion.character_rite) == 0x1428D2F90,
      "reuse exact native religion binder") ||
      !Check(!a::BindConversionOutcomeActorImage12002(0x140000000, "old").read_memory,
      "admitted build only")) return 8;
  std::cout << "PASS checks=" << checks << " cases=8 actual_actor_provider=true actual_reused_resources=true actual_serializer=true live=false\n";
  return 0;
}

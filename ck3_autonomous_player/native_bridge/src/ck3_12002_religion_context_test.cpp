#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

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
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> rite{}, main_rite{}, wrong_faith{};
  Bytes<0x320> faith{};
  Bytes<0x40> religion{};
  Bytes<0x50> religion_definition{};
  Bytes<0xB0> extension{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t faith_id = 0x83000003, religion_id = 0x84000005;
  std::int64_t fallback_value = 7654321;
  int fallback_calls = 0, fervor_calls = 0;
  bool bad_faith = false, missing_rite = false, bad_fervor = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(character, 0x1C8, extension.data());
    Put(rite, 8, std::uint32_t{0}); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, std::uint32_t{0x02000002});
    Put(faith, 8, faith_id); Put(faith, r::kFaithReligionIdOffset, religion_id);
    Put(faith, r::kFaithMainRiteIdOffset, std::uint32_t{0x02000002});
    Put(faith, 0x2F8, std::int64_t{0}); Put(extension, 0xA0, std::int64_t{0});
    Put(religion, 8, religion_id); Put(religion, 0x10, std::int32_t{7});
    Put(religion, 0x20, religion_definition.data());
    Tag(faith, 0xE0, "faith\"key"); Tag(religion_definition, 0x28, "christianity");
  }
  template <typename Buffer> static void Tag(Buffer &object, std::size_t at, std::string_view value) {
    std::memcpy(object.data() + at, value.data(), value.size());
    Put(object, at + 0x10, static_cast<std::uint64_t>(value.size()));
    Put(object, at + 0x18, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->missing_rite ? nullptr : f->rite.data(); }
void *CharacterFaith(void *) { return f->bad_faith ? f->wrong_faith.data() : f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithReligion(void *) { return f->religion.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
std::int64_t *Fervor(void *faith, std::int64_t *out) {
  if (f->bad_fervor) return nullptr;
  *out = Get<std::int64_t>(faith, 0x2F8);
  if (f->drift && (++f->fervor_calls % 2 == 0)) ++*out;
  return out;
}
std::int64_t *Fulfillment(void *character, std::int64_t *out) {
  const auto *extension = Get<const void *>(character, 0x1C8);
  if (extension) *out = Get<std::int64_t>(extension, 0xA0);
  else { ++f->fallback_calls; *out = f->fallback_value; }
  return out;
}
const void *FaithTag(void *faith) { return static_cast<const std::byte *>(faith) + 0xE0; }
const void *ReligionTag(void *religion) {
  return static_cast<const std::byte *>(Get<const void *>(religion, 0x20)) + 0x28;
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_religion = &FaithReligion; b.faith_main_rite = &FaithMainRite;
  b.faith_fervor = &Fervor; b.character_spiritual_fulfillment = &Fulfillment;
  b.faith_tag = &FaithTag; b.religion_tag = &ReligionTag; return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const r::Context &out) {
  if (!directory.empty()) std::ofstream(directory / name) << r::SerializePlayedReligionContext12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); r::Context out{};
  if (!Check(r::ReadPlayedReligionContext12002(b, 88, out), "current context") ||
      !Check(out.available && out.capture_epoch == 88, "available epoch") ||
      !Check(out.rite_id && *out.rite_id == 0, "zero is a legitimate full reference") ||
      !Check(out.faith_id == Fixture::faith_id && out.religion_id == Fixture::religion_id, "preserve high-bit generations") ||
      !Check(out.religion_id != Get<std::uint32_t>(q.religion.data(), 0x10), "reflection integer is not full ref") ||
      !Check(out.faith_main_rite_id != out.rite_id, "main rite and character rite differ") ||
      !Check(out.faith_fervor_raw && *out.faith_fervor_raw == 0, "observed fervor zero") ||
      !Check(out.spiritual_fulfillment_raw && *out.spiritual_fulfillment_raw == 0, "observed fulfillment zero") ||
      !Check(out.faith_key == "faith\"key" && out.religion_key == "christianity", "native tags copied")) return 1;
  Wire(directory, "current-zero.json", out);
  Put(q.faith, 0x2F8, std::int64_t{-123456}); Put(q.extension, 0xA0, std::int64_t{345678});
  if (!Check(r::ReadPlayedReligionContext12002(b, 89, out) && out.faith_fervor_raw == -123456 &&
             out.spiritual_fulfillment_raw == 345678, "signed fixed point preserved")) return 2;
  Wire(directory, "signed-values.json", out);
  Put(q.character, 0x1C8, static_cast<void *>(nullptr));
  if (!Check(r::ReadPlayedReligionContext12002(b, 90, out) && out.spiritual_fulfillment_raw == q.fallback_value &&
             q.fallback_calls == 2, "canonical getter evaluates extension-absent default")) return 3;
  Wire(directory, "native-default.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(r::ReadPlayedReligionContext12002(b, 91, out) && !out.rite_id && !out.faith_id &&
             !out.faith_fervor_raw && out.spiritual_fulfillment_raw == q.fallback_value,
             "legal absence does not invent identities or fervor zero")) return 4;
  Wire(directory, "legal-absent.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, std::uint32_t{0}); q.bad_faith = true;
  if (!Check(!r::ReadPlayedReligionContext12002(b, 92, out) && out.failure == r::Failure::faith_unavailable &&
             !out.available && !out.faith_fervor_raw, "failed native read is distinct from legal absence")) return 5;
  Wire(directory, "faith-unavailable.json", out); q.bad_faith = false; q.missing_rite = true;
  if (!Check(!r::ReadPlayedReligionContext12002(b, 93, out) && out.failure == r::Failure::rite_unavailable,
             "present rite has no native object")) return 6;
  q.missing_rite = false; q.bad_fervor = true;
  if (!Check(!r::ReadPlayedReligionContext12002(b, 94, out) && out.failure == r::Failure::fervor_unavailable &&
             !out.faith_fervor_raw, "missing native fixed-point return is not zero")) return 7;
  q.bad_fervor = false; q.drift = true;
  if (!Check(!r::ReadPlayedReligionContext12002(b, 95, out) && out.failure == r::Failure::state_changed,
             "two actual reads disagree")) return 8;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!r::ReadPlayedReligionContext12002(b, 96, out) && out.failure == r::Failure::frame_not_paused,
             "only paused owner frame")) return 9;
  q.jomini[0x20] = std::byte{1};
  Put(q.rite, 8, std::uint32_t{0x01000000});
  if (!Check(!r::ReadPlayedReligionContext12002(b, 97, out) && out.failure == r::Failure::rite_unavailable,
             "same index with another generation")) return 10;
  const auto actual = r::BindReligionContextImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
             reinterpret_cast<std::uintptr_t>(actual.character_rite) == 0x1428D2F90 &&
             reinterpret_cast<std::uintptr_t>(actual.character_faith) == 0x14289E750 &&
             reinterpret_cast<std::uintptr_t>(actual.character_spiritual_fulfillment) == 0x1428BCE40,
             "actual exact-image binder addresses") ||
      !Check(!r::BindReligionContextImage12002(0x140000000, "old").enabled &&
             !r::BindReligionContextImage12002(0, c::kExecutableSha256).enabled,
             "version-bound binder")) return 11;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

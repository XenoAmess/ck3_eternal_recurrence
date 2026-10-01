#include "xar_bridge/religion_doctrine12002_tenet.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion;
namespace d = r::doctrine12002;
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
  Bytes<0x800> rite{}, main_rite{}, wrong_faith{};
  Bytes<0x320> faith{};
  std::array<Bytes<32>, 5> strings{};
  std::array<std::int32_t, 2> current_tokens{1, 3};
  std::array<std::int32_t, 2> main_tokens{2, 4};
  std::string long_key = "effective_parameter_with_a_long_key";
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t current_id = 0, main_id = 0x82000002, faith_id = 0x83000003;
  bool key_missing = false, membership_missing = false, bad_faith = false, drift = false;
  int key_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, current_id);
    Put(rite, 8, current_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, main_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Set(rite, current_tokens.data(), 2); Set(main_rite, main_tokens.data(), 2);
    Tag(strings[1], "ritual\"key"); Tag(strings[2], "main_key"); Tag(strings[3], "参数");
    Put(strings[4], 0, long_key.data()); Put(strings[4], 0x10, static_cast<std::uint64_t>(long_key.size()));
    Put(strings[4], 0x18, static_cast<std::uint64_t>(long_key.size()));
  }
  static void Set(Bytes<0x800> &object, const std::int32_t *tokens, std::int32_t count) {
    Put(object, d::kRiteBooleanParameterOffset, tokens);
    Put(object, d::kRiteBooleanParameterOffset + d::kArrayCountOffset, count);
  }
  static void Tag(Bytes<32> &object, std::string_view value) {
    std::memcpy(object.data(), value.data(), value.size());
    Put(object, 0x10, static_cast<std::uint64_t>(value.size())); Put(object, 0x18, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->rite.data(); }
void *CharacterFaith(void *) { return f->bad_faith ? f->wrong_faith.data() : f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
bool Member(const void *array, const std::int32_t *token) {
  if (f->membership_missing) return false;
  const auto *data = Get<const std::int32_t *>(array, 0);
  const auto count = Get<std::int32_t>(array, 0xC);
  return std::binary_search(data, data + count, *token);
}
const void *Key(std::int32_t token) {
  ++f->key_calls;
  if (f->key_missing) return nullptr;
  if (f->drift && f->key_calls == 5) f->current_tokens[1] = 2;
  return f->strings[static_cast<std::size_t>(token)].data();
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_main_rite = &FaithMainRite; return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const d::TenetParameterContext &out) {
  if (!directory.empty()) std::ofstream(directory / name) << d::SerializeTenetParameters12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto rbind = Bind(q); d::TenetParameterBindings b{true, &Member, &Key}; d::TenetParameterContext out{};
  if (!Check(d::ReadPlayedTenetParameters12002(rbind, b, 81, out), "actual played provider") ||
      !Check(out.available && out.capture_epoch == 81 && out.date_raw == 53175816, "frame and epoch") ||
      !Check(out.played_character_id == Fixture::character_id && out.faith_id == Fixture::faith_id, "full refs") ||
      !Check(out.current_rite && out.current_rite->rite_id == 0, "zero Rite is present") ||
      !Check(out.faith_main_rite && out.faith_main_rite->rite_id == Fixture::main_id, "main Rite high generation") ||
      !Check(out.current_rite->parameters.size() == 2 && out.current_rite->parameters[0].key == "ritual\"key" &&
             out.current_rite->parameters[1].key == "参数", "native inline keys") ||
      !Check(out.faith_main_rite->parameters[1].key == q.long_key, "native heap key") ||
      !Check(out.current_rite->parameters != out.faith_main_rite->parameters, "distinct current and main sources") ||
      !Check(q.key_calls == 8, "real two-sample read")) return 1;
  Wire(directory, "current-versus-main.json", out);
  Fixture::Set(q.rite, nullptr, 0);
  if (!Check(d::ReadPlayedTenetParameters12002(rbind, b, 82, out) && out.current_rite &&
             out.current_rite->parameters.empty() && out.faith_main_rite->parameters.size() == 2,
             "known empty current collection")) return 2;
  Wire(directory, "known-empty-current.json", out);
  Fixture::Set(q.rite, q.current_tokens.data(), 2); q.key_missing = true;
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 83, out) && !out.available &&
             out.failure == "parameter_key_unavailable", "missing key is unavailable")) return 3;
  Wire(directory, "key-unavailable.json", out); q.key_missing = false;
  q.membership_missing = true;
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 84, out) &&
             out.failure == "parameter_membership_unavailable", "actual membership used")) return 4;
  q.membership_missing = false; q.bad_faith = true;
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 85, out) &&
             out.failure == "faith_unavailable", "two native Faith getters agree")) return 5;
  q.bad_faith = false;
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedTenetParameters12002(rbind, b, 86, out) && !out.current_rite &&
             !out.faith_id && !out.faith_main_rite, "legal absent Rite")) return 6;
  Wire(directory, "legal-absent.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::current_id);
  Put(q.main_rite, 8, std::uint32_t{0x81000002});
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 87, out) &&
             out.failure == "main_rite_unavailable", "main Rite generation differs")) return 7;
  Put(q.main_rite, 8, Fixture::main_id); q.drift = true; q.key_calls = 0;
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 88, out) &&
             out.failure == "state_changed", "actual samples differ")) return 8;
  Wire(directory, "state-changed.json", out); q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedTenetParameters12002(rbind, b, 89, out) &&
             out.failure == "frame_not_paused", "paused frame required")) return 9;
  auto exact = d::BindTenetParameters12002(0x140000000, c::kExecutableSha256);
  if (!Check(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.parameter_key) == 0x143F4F900 &&
             reinterpret_cast<std::uintptr_t>(exact.contains_boolean_parameter) == 0x140B9DE80,
             "exact-image binding") ||
      !Check(!d::BindTenetParameters12002(0x140000000, "old").enabled &&
             !d::BindTenetParameters12002(0, c::kExecutableSha256).enabled, "version binding")) return 10;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

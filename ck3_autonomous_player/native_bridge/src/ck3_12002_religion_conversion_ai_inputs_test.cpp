#include "xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace a = xar::ck3_12002::religion_conversion_ai_inputs;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t at, T v) {
  std::memcpy(b.data() + at, &v, sizeof(v));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> characters{}, rites{}; Bytes<0x80> character_slots{};
  Bytes<0x20> rite_slots{}; Bytes<0x1D8> character{}; Bytes<0x10> current{}, target{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_ptr = characters.data(), *rite_ptr = rites.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_id = 0x83000001;
  std::int64_t current_base = -1250000, target_base = 3350000;
  int calls = 0; bool fail = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(characters, 0x20, character_slots.data()); Put(characters, 0x2C, std::uint32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, a::kCharacterRiteOffset, std::uint32_t{0});
    Put(rites, 0x20, rite_slots.data()); Put(rites, 0x2C, std::uint32_t{2});
    Put(rite_slots, 8, current.data()); Put(rite_slots, 0x18, target.data());
    Put(current, 8, std::uint32_t{0}); Put(target, 8, target_id);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
std::int64_t *Base(std::int64_t *out, void *actor, void *rite) {
  if (f->fail || actor != f->character.data()) return nullptr;
  ++f->calls;
  *out = rite == f->target.data() ? f->target_base : f->current_base;
  if (f->drift && f->calls % 2 == 1) Put(f->character, a::kCharacterRiteOffset, Fixture::target_id);
  return out;
}
a::Bindings Bind(Fixture &q) {
  f = &q; a::Bindings b{}; b.enabled = true;
  b.core = {true, &q.state_ptr, &q.jomini_ptr, &q.character_ptr, &Player};
  b.rite_storage_slot = &q.rite_ptr; b.base_fulfillment = &Base; return b;
}
int checks = 0;
bool Check(bool ok, const char *label) {
  ++checks; if (!ok) std::cerr << "FAIL " << label << '\n'; return ok;
}
void Wire(const std::filesystem::path &dir, const char *name, const a::FulfillmentInput &v) {
  if (!dir.empty()) std::ofstream(dir / name) << a::SerializeExpectedRiteFulfillment12002(v) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); a::FulfillmentInput v{};
  if (!Check(a::ReadExpectedRiteFulfillment12002(b, 77, Fixture::target_id, v), "actual played provider") ||
      !Check(v.available && v.capture_epoch == 77 && v.played_character_id == Fixture::actor_id,
             "actual frame and epoch") ||
      !Check(v.current_rite_id == 0U && v.target_rite_id == Fixture::target_id, "full generation and valid zero") ||
      !Check(v.current_rite_base_raw == -1250000 && v.target_rite_base_raw == 3350000 &&
             v.expected_base_change_raw == 4600000 && q.calls == 2, "native target minus current base")) return 1;
  Wire(dir, "positive.json", v);
  q.current_base = 1250000; q.target_base = -3350000;
  if (!Check(a::ReadExpectedRiteFulfillment12002(b, 78, Fixture::target_id, v) &&
      v.expected_base_change_raw == -4600000, "negative prediction")) return 2;
  Wire(dir, "negative.json", v);
  q.current_base = 0; q.target_base = 0;
  if (!Check(a::ReadExpectedRiteFulfillment12002(b, 79, Fixture::target_id, v) &&
      v.current_rite_base_raw == 0 && v.target_rite_base_raw == 0 &&
      v.expected_base_change_raw == 0, "zero is observed")) return 3;
  Wire(dir, "zero.json", v);
  if (!Check(a::ReadExpectedRiteFulfillment12002(b, 80, 0, v) &&
      v.expected_base_change_raw == 0, "same rite is a valid zero preview, not conversion legality")) return 4;
  const auto previous_calls = q.calls;
  if (!Check(!a::ReadExpectedRiteFulfillment12002(b, 81, 0x82000001, v) &&
      v.failure == a::Failure::target_rite_unavailable && q.calls == previous_calls,
      "same slot different generation")) return 5;
  Wire(dir, "unavailable.json", v);
  q.fail = true;
  if (!Check(!a::ReadExpectedRiteFulfillment12002(b, 82, Fixture::target_id, v) &&
      v.failure == a::Failure::base_fulfillment_unavailable && !v.expected_base_change_raw,
      "actual callback failure is not zero")) return 6;
  q.fail = false; q.drift = true; q.calls = 0;
  if (!Check(!a::ReadExpectedRiteFulfillment12002(b, 83, Fixture::target_id, v) &&
      v.failure == a::Failure::state_changed && !v.current_rite_base_raw, "current rite changed during query")) return 7;
  Wire(dir, "frame-changed.json", v);
  q.drift = false; Put(q.character, a::kCharacterRiteOffset, std::uint32_t{0});
  q.jomini[0x20] = std::byte{0};
  if (!Check(!a::ReadExpectedRiteFulfillment12002(b, 84, Fixture::target_id, v) &&
      v.failure == a::Failure::frame_not_paused, "paused only")) return 8;
  q.jomini[0x20] = std::byte{1}; Put(q.character, a::kCharacterRiteOffset, std::uint32_t{0xFFFFFFFFU});
  if (!Check(!a::ReadExpectedRiteFulfillment12002(b, 85, Fixture::target_id, v) &&
      v.failure == a::Failure::current_rite_unavailable, "absent current rite is not a default base")) return 9;
  const auto actual = a::BindConversionAIInputsImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
      reinterpret_cast<std::uintptr_t>(actual.rite_storage_slot) == 0x145D1E2F8 &&
      reinterpret_cast<std::uintptr_t>(actual.base_fulfillment) == 0x142BFC270,
      "exact production binder") ||
      !Check(!a::BindConversionAIInputsImage12002(0, c::kExecutableSha256).enabled &&
      !a::BindConversionAIInputsImage12002(0x140000000, "old").enabled, "version-bound binder")) return 10;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
}

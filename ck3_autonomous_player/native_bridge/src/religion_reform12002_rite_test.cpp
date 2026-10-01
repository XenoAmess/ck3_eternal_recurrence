#include "xar_bridge/religion_reform12002_rite.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = c::religion;
namespace m = c::religion_reform::rite;
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
  Bytes<0x820> current{}, main{};
  Bytes<0x320> faith{}, wrong_faith{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t rite_id = 0x80000000U, main_id = 0x81000002U, faith_id = 0x82000003U;
  static constexpr std::uint32_t founder_id = 0xF3000007U, head_id = 0xE2000006U;
  std::int64_t divergence = 7'500'000, threshold = 8'000'000;
  bool bad_faith = false, bad_main = false, bad_divergence = false, bad_threshold = false, drift = false;
  int divergence_calls = 0;
  bool abi_arguments_correct = true;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, r::kCharacterRiteIdOffset, rite_id);
    Put(current, 8, rite_id); Put(current, r::kRiteFaithIdOffset, faith_id);
    Put(current, m::kRiteFounderCharacterIdOffset, founder_id);
    Put(current, m::kRiteHeadCharacterIdOffset, head_id);
    Put(main, 8, main_id); Put(main, r::kRiteFaithIdOffset, faith_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Put(wrong_faith, 8, std::uint32_t{0x83000003U});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->current.data(); }
void *RiteFaith(void *) { return f->bad_faith ? f->wrong_faith.data() : f->faith.data(); }
void *FaithMainRite(void *) {
  if (f->bad_main) return nullptr;
  return Get<std::uint32_t>(f->faith.data(), r::kFaithMainRiteIdOffset) ==
      Get<std::uint32_t>(f->current.data(), 8) ? f->current.data() : f->main.data();
}
bool IsMain(void *current) {
  return Get<std::uint32_t>(current, 8) == Get<std::uint32_t>(f->faith.data(), r::kFaithMainRiteIdOffset);
}
std::int64_t *Divergence(std::int64_t *out, void *current, void *tooltip) {
  f->abi_arguments_correct &= current == f->current.data() && tooltip == nullptr;
  if (f->bad_divergence) return nullptr;
  *out = f->divergence;
  if (f->drift && ++f->divergence_calls % 2 == 0) ++*out;
  return out;
}
std::int64_t *Threshold(void *faith, std::int64_t *out) {
  f->abi_arguments_correct &= faith == f->faith.data();
  if (f->bad_threshold) return nullptr;
  *out = f->threshold;
  return out;
}
m::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  m::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.rite_faith = &RiteFaith; b.faith_main_rite = &FaithMainRite;
  b.rite_is_main = &IsMain; b.divergence_to_main = &Divergence; b.faith_heresy_threshold = &Threshold;
  return b;
}
int checks = 0;
bool Check(bool value, const char *description) {
  ++checks; if (!value) std::cerr << "FAIL " << description << '\n'; return value;
}
void Wire(const std::filesystem::path &directory, const char *name, const m::Model &out) {
  if (!directory.empty()) std::ofstream(directory / name) << m::SerializePlayedRiteModel12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture fixture; auto b = Bind(fixture); m::Model out{};
  if (!Check(m::ReadPlayedRiteModel12002(b, 81, out), "current actual model") ||
      !Check(out.available && out.capture_epoch == 81 && out.played_character_id == Fixture::actor_id, "actual frame identity") ||
      !Check(out.rite_id == Fixture::rite_id && out.faith_id == Fixture::faith_id && out.faith_main_rite_id == Fixture::main_id, "full independent Rite/Faith/main refs") ||
      !Check(out.founder_character_id == Fixture::founder_id && out.head_character_id == Fixture::head_id, "opaque Character refs preserve high generation") ||
      !Check(out.current_is_main && !*out.current_is_main, "native non-main status") ||
      !Check(out.divergence_to_main_raw == 7'500'000 && out.faith_heresy_threshold_raw == 8'000'000, "native current values; threshold is not hardcoded 65") ||
      !Check(fixture.abi_arguments_correct, "output-first divergence/null tooltip and faith-first threshold ABI")) return 1;
  Wire(directory, "non-main-current.json", out);
  Put(fixture.faith, r::kFaithMainRiteIdOffset, Fixture::rite_id);
  Put(fixture.current, m::kRiteFounderCharacterIdOffset, r::kAbsentReference);
  Put(fixture.current, m::kRiteHeadCharacterIdOffset, std::uint32_t{0});
  fixture.divergence = 0; fixture.threshold = 0;
  if (!Check(m::ReadPlayedRiteModel12002(b, 82, out) && out.current_is_main == true, "native current main Rite") ||
      !Check(!out.founder_character_id && out.head_character_id == 0U, "absent founder and valid zero head differ") ||
      !Check(out.divergence_to_main_raw == 0 && out.faith_heresy_threshold_raw == 0, "observed zero values stay zero")) return 2;
  Wire(directory, "main-zero.json", out);
  Put(fixture.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(m::ReadPlayedRiteModel12002(b, 83, out) && out.available &&
      !out.rite_id && !out.current_is_main && !out.divergence_to_main_raw && !out.faith_heresy_threshold_raw,
      "legitimate no Rite is observed empty without invented resources")) return 3;
  Wire(directory, "legal-absent.json", out);
  Put(fixture.character, r::kCharacterRiteIdOffset, Fixture::rite_id);
  fixture.bad_faith = true;
  if (!Check(!m::ReadPlayedRiteModel12002(b, 84, out) && out.failure == m::Failure::faith_unavailable &&
      !out.available && !out.divergence_to_main_raw, "native same-index different Faith generation is unavailable")) return 4;
  Wire(directory, "faith-unavailable.json", out);
  fixture.bad_faith = false; fixture.bad_main = true;
  if (!Check(!m::ReadPlayedRiteModel12002(b, 85, out) && out.failure == m::Failure::main_rite_unavailable,
      "present Faith main reference needs an actual native object")) return 5;
  fixture.bad_main = false; fixture.bad_divergence = true;
  if (!Check(!m::ReadPlayedRiteModel12002(b, 86, out) && out.failure == m::Failure::divergence_unavailable,
      "failed fixed-point getter is not a zero divergence")) return 6;
  Wire(directory, "divergence-unavailable.json", out);
  fixture.bad_divergence = false; fixture.bad_threshold = true;
  if (!Check(!m::ReadPlayedRiteModel12002(b, 87, out) && out.failure == m::Failure::threshold_unavailable,
      "failed threshold getter is not a default literal")) return 7;
  fixture.bad_threshold = false; fixture.drift = true;
  if (!Check(!m::ReadPlayedRiteModel12002(b, 88, out) && out.failure == m::Failure::state_changed,
      "two current samples differ")) return 8;
  fixture.drift = false; fixture.jomini[0x20] = std::byte{0};
  if (!Check(!m::ReadPlayedRiteModel12002(b, 89, out) && out.failure == m::Failure::frame_not_paused,
      "reuse paused core contract")) return 9;
  fixture.jomini[0x20] = std::byte{1};
  Put(fixture.current, 8, std::uint32_t{0x81000000U});
  if (!Check(!m::ReadPlayedRiteModel12002(b, 90, out) && out.failure == m::Failure::rite_unavailable,
      "same Rite index with another generation is not current Rite")) return 10;
  const auto image = m::BindRiteModelImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(image.enabled && image.core.enabled &&
      reinterpret_cast<std::uintptr_t>(image.rite_is_main) == 0x1424F7E40 &&
      reinterpret_cast<std::uintptr_t>(image.divergence_to_main) == 0x142BDFBA0 &&
      reinterpret_cast<std::uintptr_t>(image.faith_heresy_threshold) == 0x142440920,
      "actual frozen-image binder") ||
      !Check(!m::BindRiteModelImage12002(0x140000000, "old").enabled &&
      !m::BindRiteModelImage12002(0, c::kExecutableSha256).enabled, "exact build binding")) return 11;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

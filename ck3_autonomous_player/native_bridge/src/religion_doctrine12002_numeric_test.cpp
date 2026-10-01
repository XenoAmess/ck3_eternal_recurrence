#include "xar_bridge/religion_doctrine12002_numeric.hpp"

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
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t current_id = 0, main_id = 0x82000002, faith_id = 0x83000003;
  bool bad_faith = false, drift = false;
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
    Put(character, r::kCharacterRiteIdOffset, current_id);
    Put(rite, 8, current_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, main_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Set(rite, 0, 5000, 50000, 1, -500000);
    Set(main_rite, 45, 0, 75000, 2, 500000);
  }
  static void Set(Bytes<0x800> &object, std::int32_t minimum, std::int64_t holy_site,
                  std::int64_t gain, std::int32_t protection, std::int64_t threshold) {
    Put(object, d::kRiteNumericSpecialOffset + d::kNumericMinimumFervorOffset, minimum);
    Put(object, d::kRiteNumericSpecialOffset + d::kNumericHolySiteGainOffset, holy_site);
    Put(object, d::kRiteNumericSpecialOffset + d::kNumericFervorGainOffset, gain);
    Put(object, d::kRiteNumericSpecialOffset + d::kNumericHeresyProtectionOffset, protection);
    Put(object, d::kRiteNumericSpecialOffset + d::kNumericHeresyThresholdOffset, threshold);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) {
  ++f->rite_calls;
  if (f->drift && f->rite_calls == 2)
    Put(f->rite, d::kRiteNumericSpecialOffset + d::kNumericHeresyThresholdOffset, std::int64_t{700000});
  return f->rite.data();
}
void *CharacterFaith(void *) { return f->bad_faith ? f->wrong_faith.data() : f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
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
void Wire(const std::filesystem::path &directory, const char *name, const d::NumericSpecialContext &out) {
  if (!directory.empty()) std::ofstream(directory / name) << d::SerializeNumericSpecialParameters12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; const auto rbind = Bind(q);
  const auto b = d::BindNumericSpecialParameters12002(0x140000000, c::kExecutableSha256);
  d::NumericSpecialContext out{};
  if (!Check(d::ReadPlayedNumericSpecialParameters12002(rbind, b, 91, out), "actual played numeric provider") ||
      !Check(out.available && out.capture_epoch == 91 && out.date_raw == 53175816 &&
             out.played_character_id == Fixture::character_id, "actual frame full character epoch") ||
      !Check(out.current_rite && out.current_rite->rite_id == 0U && out.faith_main_rite &&
             out.faith_main_rite->rite_id == Fixture::main_id && out.faith_id == Fixture::faith_id,
             "separate full refs and legal zero Rite") ||
      !Check(out.current_rite->parameters.size() == 5 && out.faith_main_rite->parameters.size() == 5,
             "all five native cache cells") ||
      !Check(out.current_rite->parameters[0].raw == 0 && !out.current_rite->parameters[0].unset &&
             out.faith_main_rite->parameters[0].raw == 45, "minimum valid zero distinct from main45") ||
      !Check(out.current_rite->parameters[1].raw == 5000 && out.current_rite->parameters[1].scale == 100000 &&
             out.current_rite->parameters[2].raw == 50000 && out.current_rite->parameters[3].raw == 1 &&
             out.current_rite->parameters[3].scale == 1 && out.current_rite->parameters[4].raw == -500000,
             "raw fixedpoint versus signed integer payloads") ||
      !Check(d::LookupNumericSpecialParameter12002(out, false, "heresy_threshold").parameter->raw == -500000 &&
             d::LookupNumericSpecialParameter12002(out, true, "heresy_threshold").parameter->raw == 500000,
             "typed lookup retains signed additive and source") ||
      !Check(d::LookupNumericSpecialParameter12002(out, false, "unimplemented_key").state ==
             d::NumericParameterLookupState::UnsupportedKey, "unknown supported key absent not zero")) return 1;
  Wire(directory, "current-versus-main.json", out);
  Fixture::Set(q.rite, 0, 0, 0, 0, 0);
  if (!Check(d::ReadPlayedNumericSpecialParameters12002(rbind, b, 92, out) &&
             d::LookupNumericSpecialParameter12002(out, false, "bonus_fervor_gain").state ==
             d::NumericParameterLookupState::Value && out.current_rite->parameters[2].raw == 0,
             "observed effective zero is a value")) return 2;
  Wire(directory, "known-zero-current.json", out);
  Fixture::Set(q.rite, -1, 0, 0, 0, 0);
  if (!Check(d::ReadPlayedNumericSpecialParameters12002(rbind, b, 93, out) &&
             d::LookupNumericSpecialParameter12002(out, false, "minimum_fervor").state ==
             d::NumericParameterLookupState::Unset && out.current_rite->parameters[0].raw == -1,
             "native minus-one minimum unset")) return 3;
  Wire(directory, "minimum-unset.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedNumericSpecialParameters12002(rbind, b, 94, out) && !out.current_rite &&
             !out.faith_main_rite && !out.faith_id &&
             d::LookupNumericSpecialParameter12002(out, false, "minimum_fervor").state ==
             d::NumericParameterLookupState::UnavailableSource, "legal absent source distinct from zero")) return 4;
  Wire(directory, "legal-absent.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::current_id); q.bad_faith = true;
  if (!Check(!d::ReadPlayedNumericSpecialParameters12002(rbind, b, 95, out) && !out.available &&
             out.failure == "faith_unavailable" && !out.current_rite, "failed source not known-zero cache")) return 5;
  Wire(directory, "faith-unavailable.json", out); q.bad_faith = false;
  q.drift = true; q.rite_calls = 0;
  if (!Check(!d::ReadPlayedNumericSpecialParameters12002(rbind, b, 96, out) &&
             out.failure == "state_changed", "actual cache samples differ")) return 6;
  Wire(directory, "state-changed.json", out); q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedNumericSpecialParameters12002(rbind, b, 97, out) &&
             out.failure == "frame_not_paused", "paused owner prerequisite")) return 7;
  if (!Check(!d::BindNumericSpecialParameters12002(0x140000000, "old").enabled &&
             !d::BindNumericSpecialParameters12002(0, c::kExecutableSha256).enabled,
             "exact build binding")) return 8;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

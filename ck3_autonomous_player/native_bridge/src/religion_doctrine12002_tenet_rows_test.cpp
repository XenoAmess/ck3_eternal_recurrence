#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"

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
  Bytes<0x800> rite{}, main_rite{};
  Bytes<0x320> faith{};
  Bytes<0xA0> extension{};
  std::array<Bytes<64>, 5> definitions{};
  std::array<const void *, 1> core{definitions[4].data()}, main_core{definitions[3].data()};
  std::array<const void *, 2> personal{definitions[0].data(), definitions[4].data()};
  std::array<Bytes<16>, 3> states{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t current_id = 0, main_id = 0x82000002, faith_id = 0x83000003;
  bool invalid_state = false, drift = false;
  int calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, current_id); Put(character, d::kCharacterExtensionOffset, extension.data());
    Put(rite, 8, current_id); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(main_rite, 8, main_id); Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Set(rite, d::kRiteCoreTenetsOffset, core.data(), 1);
    Set(main_rite, d::kRiteCoreTenetsOffset, main_core.data(), 1);
    Set(extension, d::kPersonalTenetsOffset, personal.data(), 2);
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      const auto key = "tenet_" + std::to_string(i);
      std::memcpy(definitions[i].data() + 0x18, key.data(), key.size());
      Put(definitions[i], 0x28, static_cast<std::uint64_t>(key.size()));
      Put(definitions[i], 0x30, std::uint64_t{15}); Put(definitions[i], 0x38, std::uint32_t{0x4744624F});
    }
    for (std::size_t i = 0; i < states.size(); ++i) {
      Put(states[i], 0, definitions[i].data()); Put(states[i], 8, static_cast<std::uint8_t>(i));
    }
    Set(main_rite, d::kRiteTenetStatesOffset, states.data(), 3);
  }
  template <typename Buffer, typename P> static void Set(Buffer &buffer, std::size_t at, P data_ptr, std::int32_t count) {
    Put(buffer, at, data_ptr); Put(buffer, at + 0xC, count);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->rite.data(); }
void *CharacterFaith(void *) { return f->faith.data(); }
void *RiteFaith(void *) { return f->faith.data(); }
void *FaithMainRite(void *) { return f->main_rite.data(); }
std::uint8_t State(void *, const void *definition) {
  ++f->calls;
  if (f->invalid_state) return 9;
  for (std::size_t i = 0; i < f->definitions.size(); ++i) {
    if (definition == f->definitions[i].data()) {
      if (f->drift && f->calls >= 10) return static_cast<std::uint8_t>((i + 1) % 5);
      return static_cast<std::uint8_t>(i);
    }
  }
  return 0;
}
r::Bindings Bind(Fixture &q) {
  f = &q; r::Bindings b{}; b.enabled = true;
  b.core = {true, &q.state_ptr, &q.jomini_ptr, &q.storage_ptr, &Player};
  b.character_rite = &CharacterRite; b.character_faith = &CharacterFaith;
  b.rite_faith = &RiteFaith; b.faith_main_rite = &FaithMainRite; return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const d::TenetRowsContext &out) {
  if (!directory.empty()) std::ofstream(directory / name) << d::SerializeTenetRows12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto rbind = Bind(q); d::TenetRowsBindings b{true, &State}; d::TenetRowsContext out{};
  if (!Check(d::ReadPlayedTenetRows12002(rbind, b, 81, out), "actual played reader") ||
      !Check(out.available && out.capture_epoch == 81 && out.date_raw == 53175816, "frame epoch") ||
      !Check(out.current_rite->rite_id == 0 && out.faith_main_rite->rite_id == Fixture::main_id &&
             out.faith_id == Fixture::faith_id && out.played_character_id == Fixture::character_id, "full refs") ||
      !Check(out.current_rite->core_tenets[0].key == "tenet_4" &&
             out.faith_main_rite->core_tenets[0].key == "tenet_3", "distinct real Core collections") ||
      !Check(out.personal_tenets.size() == 2 && out.personal_tenets[0].key == "tenet_0" &&
             out.personal_tenets[0].current_rite_status == 0, "personal Unknown is known native zero") ||
      !Check(out.effective_tenet_states.size() == 5, "definition union deduplicated") ||
      !Check(out.effective_tenet_states[0].current_rite_status == 4 &&
             out.effective_tenet_states[1].current_rite_status == 3 &&
             out.effective_tenet_states[2].current_rite_status == 0 &&
             out.effective_tenet_states[3].current_rite_status == 1 &&
             out.effective_tenet_states[4].current_rite_status == 2, "actual getter states all five") ||
      !Check(q.calls == 18, "actual getter called in two samples")) return 1;
  Wire(directory, "current-main-personal.json", out);
  Put(q.character, d::kCharacterExtensionOffset, static_cast<void *>(nullptr));
  if (!Check(d::ReadPlayedTenetRows12002(rbind, b, 82, out) && out.personal_tenets.empty(),
             "extension absent is legal empty personal collection")) return 2;
  Wire(directory, "no-extension.json", out);
  Put(q.character, d::kCharacterExtensionOffset, q.extension.data());
  Put(q.character, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedTenetRows12002(rbind, b, 83, out) && !out.current_rite && !out.faith_main_rite &&
             out.personal_tenets.size() == 2 && !out.personal_tenets[0].current_rite_status,
             "legal absent Rite keeps personal keys without inventing status")) return 3;
  Wire(directory, "personal-without-rite.json", out);
  Put(q.character, r::kCharacterRiteIdOffset, Fixture::current_id); q.invalid_state = true;
  if (!Check(!d::ReadPlayedTenetRows12002(rbind, b, 84, out) && out.failure == "tenet_state_unavailable",
             "native invalid state is a failed read")) return 4;
  Wire(directory, "state-unavailable.json", out); q.invalid_state = false;
  Put(q.definitions[4], 0x38, std::uint32_t{0});
  if (!Check(!d::ReadPlayedTenetRows12002(rbind, b, 85, out) && out.failure == "tenet_definition_unavailable",
             "native definition identity")) return 5;
  Put(q.definitions[4], 0x38, std::uint32_t{0x4744624F}); q.calls = 0; q.drift = true;
  if (!Check(!d::ReadPlayedTenetRows12002(rbind, b, 86, out) && out.failure == "state_changed",
             "actual samples differ")) return 6;
  Wire(directory, "state-changed.json", out); q.drift = false;
  auto exact = d::BindTenetRows12002(0x140000000, c::kExecutableSha256);
  if (!Check(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.tenet_state) == 0x1424F88A0,
             "actual image state binder") ||
      !Check(!d::BindTenetRows12002(0x140000000, "old").enabled &&
             !d::BindTenetRows12002(0, c::kExecutableSha256).enabled, "exact version binder")) return 7;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

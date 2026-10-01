#include "xar_bridge/ck3_12002_epidemic_treatment_presence.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace c = xar::ck3_12002;
namespace old = xar::ck3_11906;
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
  Bytes<0x200> extension{};
  Bytes<0x90> rows{};
  Bytes<0x60> wanted{}, fallback{}, other{};
  std::string wanted_name = std::string(old::kPlayerEpidemicTreatmentModifierKeyV1);
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *fallback_ptr = fallback.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::int32_t date = 53350560;
  static constexpr std::uint64_t revision = 123;
  static constexpr std::uint32_t hash = 0xE0000042;
  bool no_database = false, fallback_lookup = false, null_lookup = false;
  bool hash_input_correct = false, lookup_input_correct = false, drift_date = false;
  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, c::kTreatmentCharacterExtensionOffset12002, extension.data());
    Put(extension, c::kTreatmentModifierRowsOffset12002, rows.data());
    Put(extension, c::kTreatmentModifierCountOffset12002, std::int32_t{2});
    Put(rows, 0, other.data()); Put(rows, c::kTreatmentModifierRowStride12002, wanted.data());
    SetName(wanted_name);
  }
  void SetName(std::string value) {
    wanted_name = std::move(value);
    if (wanted_name.size() < 16) {
      std::memset(wanted.data() + c::kTreatmentModifierDefinitionKeyOffset12002, 0, 16);
      std::memcpy(wanted.data() + c::kTreatmentModifierDefinitionKeyOffset12002,
                  wanted_name.data(), wanted_name.size());
      Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002 + 0x18, std::size_t{15});
    } else {
      Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002, wanted_name.data());
      Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002 + 0x18, wanted_name.size());
    }
    Put(wanted, c::kTreatmentModifierDefinitionKeyOffset12002 + 0x10, wanted_name.size());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *Database() {
  if (f->drift_date) Put(f->state, 8, Fixture::date + 1);
  return f->no_database ? nullptr : f;
}
std::uint32_t Hash(void *database, const char *key, std::uint32_t size) {
  f->hash_input_correct = database == f &&
      std::string_view(key, size) == old::kPlayerEpidemicTreatmentModifierKeyV1;
  return Fixture::hash;
}
void *Lookup(void *database, std::int32_t hash) {
  f->lookup_input_correct = database == f && std::bit_cast<std::uint32_t>(hash) == Fixture::hash;
  return f->null_lookup ? nullptr : (f->fallback_lookup ? f->fallback.data() : f->wanted.data());
}
c::TreatmentPresenceBindings12002 Bind(Fixture &fixture) {
  f = &fixture;
  c::TreatmentPresenceBindings12002 result{}; result.enabled = true;
  result.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  result.get_modifier_database = &Database; result.hash_stable_key = &Hash;
  result.lookup_modifier = &Lookup; result.fallback_definition_slot = &f->fallback_ptr;
  return result;
}
int checks = 0;
bool Check(bool condition, const char *name) {
  ++checks;
  if (!condition) std::cerr << "FAIL " << name << '\n';
  return condition;
}
bool Wire(const std::filesystem::path &directory, const char *name,
          const old::PlayerEpidemicTreatmentPresenceV1 &value) {
  const auto json = old::SerializePlayerEpidemicTreatmentPresenceV1(value);
  if (json.empty()) return false;
  std::ofstream output(directory / name); output << json << '\n';
  return output.good();
}
old::PlayerEpidemicTreatmentPresenceV1 Read(const c::TreatmentPresenceBindings12002 &b) {
  return c::ReadPlayerEpidemicTreatmentPresence12002(b, Fixture::revision, Fixture::date, Fixture::actor_id);
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const auto directory = std::filesystem::path(argv[1]);
  std::filesystem::create_directories(directory);
  Fixture q; auto b = Bind(q); auto value = Read(b);
  if (!Check(value.available && value.present && value.unavailable_reason.empty(), "actual core to wanted presence") ||
      !Check(q.hash_input_correct && q.lookup_input_correct, "fixed key and all hash bits passed") ||
      !Check(value.snapshot_revision == Fixture::revision && value.date_raw == Fixture::date &&
             value.played_character_id == Fixture::actor_id, "exact frame/full actor DTO") ||
      !Check(Wire(directory, "present.json", value), "actual present serializer")) return 3;
  Put(q.rows, c::kTreatmentModifierRowStride12002, q.other.data()); value = Read(b);
  if (!Check(value.available && !value.present, "known rows exclude wanted definition") ||
      !Check(Wire(directory, "absent.json", value), "actual absent serializer")) return 4;
  Put(q.character, c::kTreatmentCharacterExtensionOffset12002, static_cast<void *>(nullptr)); value = Read(b);
  if (!Check(value.available && !value.present, "null extension is known empty") ||
      !Check(Wire(directory, "empty-extension.json", value), "empty extension wire")) return 5;
  Put(q.character, c::kTreatmentCharacterExtensionOffset12002, q.extension.data());
  Put(q.extension, c::kTreatmentModifierRowsOffset12002, static_cast<void *>(nullptr));
  Put(q.extension, c::kTreatmentModifierCountOffset12002, std::int32_t{0}); value = Read(b);
  if (!Check(value.available && !value.present, "zero count and null data are known empty") ||
      !Check(Wire(directory, "empty-rows.json", value), "empty rows wire")) return 6;
  Put(q.extension, c::kTreatmentModifierCountOffset12002, std::int32_t{1}); value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_rows_unavailable", "positive count null rows unavailable") ||
      !Check(Wire(directory, "rows-unavailable.json", value), "unavailable wire uses null")) return 7;
  Put(q.extension, c::kTreatmentModifierCountOffset12002, std::int32_t{-1}); value = Read(b);
  if (!Check(!value.available && !value.present, "negative count not false absence")) return 8;
  Put(q.extension, c::kTreatmentModifierRowsOffset12002, reinterpret_cast<void *>(1));
  Put(q.extension, c::kTreatmentModifierCountOffset12002, std::int32_t{1}); value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_rows_unavailable", "actual failed row read not false absence")) return 9;
  Put(q.extension, c::kTreatmentModifierRowsOffset12002, q.rows.data());
  q.fallback_lookup = true; value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_definition_unavailable", "fallback is not definition") ||
      !Check(Wire(directory, "definition-unavailable.json", value), "definition unavailable wire")) return 10;
  q.fallback_lookup = false; q.null_lookup = true; value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_definition_unavailable", "null lookup is unavailable")) return 11;
  q.null_lookup = false; q.SetName("other"); value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_definition_unavailable", "SSO wrong key rejected")) return 12;
  q.SetName(std::string(old::kPlayerEpidemicTreatmentModifierKeyV1)); q.no_database = true; value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "modifier_database_unavailable", "missing database is unavailable")) return 13;
  q.no_database = false; q.jomini[0x20] = std::byte{0}; value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "frame_not_paused", "requires actual paused core")) return 14;
  q.jomini[0x20] = std::byte{1};
  value = c::ReadPlayerEpidemicTreatmentPresence12002(b, Fixture::revision, Fixture::date, Fixture::actor_id + 0x01000000);
  if (!Check(!value.available && value.unavailable_reason == "frame_binding_unavailable", "same index different generation not current actor")) return 15;
  Put(q.character, 0x18, Fixture::actor_id + 0x01000000); value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "played_character_unavailable", "core full ID roundtrip")) return 16;
  Put(q.character, 0x18, Fixture::actor_id); q.drift_date = true; value = Read(b);
  if (!Check(!value.available && value.unavailable_reason == "frame_changed", "actual core date changes during lookup")) return 17;
  q.drift_date = false; Put(q.state, 8, Fixture::date);
  const auto actual = c::BindTreatmentPresenceImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
             reinterpret_cast<std::uintptr_t>(actual.get_modifier_database) == 0x1408FD4E0 &&
             reinterpret_cast<std::uintptr_t>(actual.hash_stable_key) == 0x143F7E240 &&
             reinterpret_cast<std::uintptr_t>(actual.lookup_modifier) == 0x140AB8D20 &&
             reinterpret_cast<std::uintptr_t>(actual.fallback_definition_slot) == 0x145D1E0B0,
             "real exact image binder addresses") ||
      !Check(!c::BindTreatmentPresenceImage12002(0x140000000, "old").enabled &&
             !c::BindTreatmentPresenceImage12002(0, c::kExecutableSha256).enabled,
             "same exact binary bound") ||
      !Check(!Read(c::TreatmentPresenceBindings12002{}).available, "disabled binding unavailable")) return 18;
  std::cout << "PASS checks=" << checks << " actual_core=true actual_reader=true actual_serializer=true live=false\n";
  return 0;
}

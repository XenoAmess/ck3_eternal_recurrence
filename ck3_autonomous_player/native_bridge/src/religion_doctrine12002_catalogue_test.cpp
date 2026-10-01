#include "xar_bridge/religion_doctrine12002_catalogue.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace c = xar::ck3_12002;
namespace d = c::religion::doctrine12002;
namespace {
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class B, class T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template<class B> void Key(B &b, std::string_view key) {
  const auto at = d::kDoctrineStableKeyOffset;
  if (key.size() < 16) std::memcpy(b.data() + at, key.data(), key.size());
  else Put(b, at, key.data());
  Put(b, at + 0x10, static_cast<std::uint64_t>(key.size()));
  Put(b, at + 0x18, key.size() < 16 ? std::uint64_t{15} : static_cast<std::uint64_t>(key.size()));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; Bytes<0x22350> data{}; Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()}; Bytes<0x30> storage{};
  Bytes<0x80> slots{}; Bytes<0x1D8> actor{}; Bytes<0x80> database{};
  Bytes<0xB10> one{}, two{}, three{}; Bytes<0x150> group{};
  std::array<const void *, 3> rows{one.data(), two.data(), three.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  void *database_ptr = database.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::string_view mod_key = "mod_custom_doctrine\"信";
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(database, d::kDoctrineDatabaseArrayOffset, rows.data());
    Put(database, 0x58, std::int32_t{3}); Put(database, d::kDoctrineDatabaseCountOffset, std::int32_t{3});
    Key(one, "doctrine_a"); Key(two, "doctrine_b"); Key(three, mod_key); Key(group, "group_a");
    Put(one, d::kDoctrineGroupPointerOffset, group.data());
    Put(two, d::kDoctrineGroupPointerOffset, group.data());
    Put(three, d::kDoctrineGroupPointerOffset, group.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
d::CatalogueBindings Bind(Fixture &q) {
  f = &q; d::CatalogueBindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.database_slot = &f->database_ptr; return b;
}
int checks = 0;
bool Check(bool value, const char *label) {
  ++checks; if (!value) std::cerr << "FAIL " << label << '\n'; return value;
}
void Wire(const std::filesystem::path &p, const char *name, const d::DoctrineCatalogue &v) {
  if (!p.empty()) std::ofstream(p / name) << d::SerializeDoctrineCatalogue12002(v) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto output = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; const auto b = Bind(q); d::DoctrineCatalogue out{};
  if (!Check(d::ReadPlayedDoctrineCatalogue12002(b, 101, out), "actual loaded native DB provider") ||
      !Check(out.available && out.catalogue_complete && out.rows.size() == 3, "full list including non-stock definition") ||
      !Check(out.capture_epoch == 101 && out.date_raw == 53175816 && out.played_character_id == Fixture::actor_id,
             "actual current player frame") ||
      !Check(out.rows[2].doctrine_key == Fixture::mod_key && out.rows[2].group_key == "group_a" &&
             out.rows[2].source == "loaded_doctrine_registry", "raw definition key and explicit registry source")) return 1;
  Wire(output, "loaded-catalogue.json", out);
  const void *definition = nullptr; std::string failure;
  if (!Check(d::ResolveDoctrineDefinitionByStableKey12002(b, Fixture::mod_key, definition, failure) &&
             definition == q.three.data() && failure.empty(), "stable key resolves actual loaded native pointer")) return 2;
  if (!Check(d::ResolveDoctrineDefinitionByStableKey12002(b, "unknown_key", definition, failure) &&
             !definition && failure.empty(), "complete missing-key lookup")) return 3;
  Put(q.database, d::kDoctrineDatabaseCountOffset, std::int32_t{0});
  if (!Check(d::ReadPlayedDoctrineCatalogue12002(b, 102, out) && out.catalogue_complete && out.rows.empty(),
             "known empty is complete")) return 4;
  Wire(output, "known-empty.json", out); q.database_ptr = nullptr;
  if (!Check(!d::ReadPlayedDoctrineCatalogue12002(b, 103, out) && !out.available && !out.catalogue_complete &&
             out.unavailable_reason == "doctrine_database_unavailable", "missing DB never calls lazy getter")) return 5;
  Wire(output, "database-unavailable.json", out);
  if (!Check(!d::ResolveDoctrineDefinitionByStableKey12002(b, "doctrine_a", definition, failure) &&
             !definition && failure == "doctrine_database_unavailable", "failed DB lookup distinct from absent key")) return 6;
  q.database_ptr = q.database.data(); q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedDoctrineCatalogue12002(b, 104, out) && out.unavailable_reason == "frame_not_paused",
             "current paused owner frame only")) return 7;
  const auto native = d::BindDoctrineCatalogueImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(native.enabled && native.core.enabled &&
             reinterpret_cast<std::uintptr_t>(native.database_slot) == 0x145C67198,
             "actual exact-image global-slot binder")) return 8;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_key_resolver=true actual_serializer=true live=false\n";
  return 0;
}

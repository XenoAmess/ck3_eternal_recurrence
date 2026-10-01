#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace d = r::doctrine12002;
namespace {
template<std::size_t N> using Bytes = std::array<std::byte, N>;
template<class B, class T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template<class B> void Key(B &b, std::string_view key) {
  constexpr auto offset = d::kDoctrineStableKeyOffset;
  if (key.size() < 16) std::memcpy(b.data() + offset, key.data(), key.size());
  else Put(b, offset, key.data());
  Put(b, offset + 0x10, static_cast<std::uint64_t>(key.size()));
  Put(b, offset + 0x18, key.size() < 16 ? std::uint64_t{15} : static_cast<std::uint64_t>(key.size()));
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{};
  Bytes<0x78> player{}; Bytes<0x22350> data{}; Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()}; Bytes<0x30> storage{};
  Bytes<0x80> slots{}; Bytes<0x1D8> actor{}; Bytes<0x800> rite{}, main_rite{};
  Bytes<0x320> faith{}; Bytes<0xB10> one{}, two{}, actor_only{};
  Bytes<0x150> group_one{}, group_two{};
  std::array<const void *, 2> rows{one.data(), two.data()};
  const void *actor_row = actor_only.data();
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  bool missing_main = false, drift = false; int main_reads = 0;
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t faith_id = 0x83000003, main_id = 0x85000002;
  static constexpr std::string_view long_key = "doctrine_quoted\"信";
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(actor, r::kCharacterRiteIdOffset, std::uint32_t{0});
    Put(rite, 8, std::uint32_t{0}); Put(rite, r::kRiteFaithIdOffset, faith_id);
    Put(faith, 8, faith_id); Put(faith, r::kFaithMainRiteIdOffset, main_id);
    Put(main_rite, 8, main_id);
    Put(main_rite, d::kMainRiteDoctrineArrayOffset, rows.data());
    Put(main_rite, d::kMainRiteDoctrineArrayOffset + 8, std::int32_t{2});
    Put(main_rite, d::kMainRiteDoctrineCountOffset, std::int32_t{2});
    Put(rite, d::kMainRiteDoctrineArrayOffset, &actor_row);
    Put(rite, d::kMainRiteDoctrineArrayOffset + 8, std::int32_t{1});
    Put(rite, d::kMainRiteDoctrineCountOffset, std::int32_t{1});
    Key(one, "doctrine_a"); Key(two, long_key); Key(actor_only, "actor_only");
    Key(group_one, "group_a"); Key(group_two, "group_b");
    Put(one, d::kDoctrineGroupPointerOffset, group_one.data());
    Put(two, d::kDoctrineGroupPointerOffset, group_two.data());
    Put(actor_only, d::kDoctrineGroupPointerOffset, group_one.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *Rite(void *) { return f->rite.data(); }
void *Faith(void *) { return f->faith.data(); }
void *Main(void *) {
  if (f->drift && ++f->main_reads == 2)
    Put(f->main_rite, d::kMainRiteDoctrineCountOffset, std::int32_t{1});
  return f->missing_main ? nullptr : f->main_rite.data();
}
r::Bindings Bind(Fixture &q) {
  f = &q; r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player};
  b.character_rite = &Rite; b.character_faith = &Faith;
  b.rite_faith = &Faith; b.faith_main_rite = &Main; return b;
}
int checks = 0;
bool Check(bool value, const char *label) {
  ++checks; if (!value) std::cerr << "FAIL " << label << '\n'; return value;
}
void Wire(const std::filesystem::path &p, const char *name, const d::FaithMainRiteDoctrines &v) {
  if (!p.empty()) std::ofstream(p / name) << d::SerializeFaithMainRiteDoctrines12002(v) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto output = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); d::FaithMainRiteDoctrines value{};
  if (!Check(d::ReadPlayedFaithMainRiteDoctrines12002(b, 101, value), "actual current provider") ||
      !Check(value.available && value.capture_epoch == 101 && value.date_raw == 53175816,
             "current frame provenance") ||
      !Check(value.rite_id == 0U && value.main_rite_id == Fixture::main_id &&
             value.faith_id == Fixture::faith_id, "zero actor rite and full generation main/faith") ||
      !Check(value.rows.size() == 2 && value.rows[0].doctrine_key == "doctrine_a" &&
             value.rows[1].doctrine_key == Fixture::long_key, "SSO and heap stable native definition keys") ||
      !Check(value.rows[1].group_key == "group_b" && value.rows[1].source == "faith_main_rite",
             "actual group and explicit source") ||
      !Check(value.rows[0].doctrine_key != "actor_only", "actor rite never substituted for faith main rite")) return 1;
  Wire(output, "current-main-rite.json", value);
  Put(q.main_rite, d::kMainRiteDoctrineCountOffset, std::int32_t{0});
  if (!Check(d::ReadPlayedFaithMainRiteDoctrines12002(b, 102, value) && value.rows.empty(),
             "observed empty main rite collection")) return 2;
  Wire(output, "known-empty.json", value);
  Put(q.actor, r::kCharacterRiteIdOffset, r::kAbsentReference);
  if (!Check(d::ReadPlayedFaithMainRiteDoctrines12002(b, 103, value) && !value.rite_id &&
             !value.faith_id && !value.main_rite_id && value.rows.empty(), "legal absence")) return 3;
  Wire(output, "legal-absent.json", value);
  Put(q.actor, r::kCharacterRiteIdOffset, std::uint32_t{0}); q.missing_main = true;
  if (!Check(!d::ReadPlayedFaithMainRiteDoctrines12002(b, 104, value) && !value.available &&
             value.unavailable_reason == "main_rite_unavailable", "unavailable is not observed empty")) return 4;
  Wire(output, "main-rite-unavailable.json", value); q.missing_main = false;
  Put(q.main_rite, 8, std::uint32_t{0x84000002});
  if (!Check(!d::ReadPlayedFaithMainRiteDoctrines12002(b, 105, value) &&
             value.unavailable_reason == "main_rite_unavailable", "full main rite generation preserved")) return 5;
  Put(q.main_rite, 8, Fixture::main_id);
  Put(q.main_rite, d::kMainRiteDoctrineCountOffset, std::int32_t{2}); q.drift = true;
  if (!Check(!d::ReadPlayedFaithMainRiteDoctrines12002(b, 106, value) &&
             value.unavailable_reason == "state_changed", "independent native reads changed")) return 6;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedFaithMainRiteDoctrines12002(b, 107, value) &&
             value.unavailable_reason == "frame_not_paused", "paused production entry")) return 7;
  d::DoctrineRow row{};
  if (!Check(d::CopyDoctrineDefinition12002(q.two.data(), row) && row.doctrine_key == Fixture::long_key &&
             row.group_key == "group_b", "shared definition copier")) return 8;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

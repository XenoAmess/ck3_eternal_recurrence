#include "xar_bridge/religion_doctrine12002_hostility.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace d = xar::ck3_12002::religion::doctrine12002;
namespace r = xar::ck3_12002::religion;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t at, T value) {
  std::memcpy(buffer.data() + at, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}; Bytes<0x28> jomini{}; Bytes<0x1F8> players{}; Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{}; std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, rite_storage{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x900> actor_rite{}, target_rite{}, actor_main{}, target_main{};
  Bytes<0x320> actor_faith{}, target_faith{};
  Bytes<0x40> actor_religion{}, target_religion{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *rite_storage_ptr = rite_storage.data();
  static constexpr std::int32_t character_id = 0x03000004;
  static constexpr std::uint32_t actor_rite_id = 0x02000001, target_rite_id = 0x83000002;
  static constexpr std::uint32_t actor_faith_id = 0x82000003, target_faith_id = 0x83000004;
  static constexpr std::uint32_t actor_main_id = 0x04000005, target_main_id = 0x06000006;
  static constexpr std::uint32_t actor_religion_id = 0x87000001, target_religion_id = 0x88000002;
  std::uint8_t forward_rite = 2, reverse_rite = 0, forward_faith = 3, reverse_faith = 1;
  int rite_calls = 0, faith_calls = 0;
  bool bad_call = false, drift = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(character_storage, 0x20, character_slots.data()); Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, actor_rite_id);
    Put(rite_storage, 0x20, rite_slots.data()); Put(rite_storage, 0x2C, std::uint32_t{8});
    Put(rite_slots, 1 * 0x10 + 8, actor_rite.data()); Put(rite_slots, 2 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 5 * 0x10 + 8, actor_main.data()); Put(rite_slots, 6 * 0x10 + 8, target_main.data());
    Rite(actor_rite, actor_rite_id, actor_faith_id); Rite(target_rite, target_rite_id, target_faith_id);
    Rite(actor_main, actor_main_id, actor_faith_id); Rite(target_main, target_main_id, target_faith_id);
    Faith(actor_faith, actor_faith_id, actor_religion_id, actor_main_id);
    Faith(target_faith, target_faith_id, target_religion_id, target_main_id);
    Put(actor_religion, 8, actor_religion_id); Put(target_religion, 8, target_religion_id);
  }
  static void Rite(Bytes<0x900> &rite, std::uint32_t id, std::uint32_t faith) {
    Put(rite, 8, id); Put(rite, 0x0C, d::kHostilityRiteTypeTag); Put(rite, r::kRiteFaithIdOffset, faith);
  }
  static void Faith(Bytes<0x320> &faith, std::uint32_t id, std::uint32_t religion, std::uint32_t main) {
    Put(faith, 8, id); Put(faith, r::kFaithReligionIdOffset, religion); Put(faith, r::kFaithMainRiteIdOffset, main);
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CharacterRite(void *) { return f->actor_rite.data(); }
void *CharacterFaith(void *) { return f->actor_faith.data(); }
void *RiteFaith(void *rite) {
  return Get<std::uint32_t>(rite, r::kRiteFaithIdOffset) == Fixture::actor_faith_id ?
      f->actor_faith.data() : f->target_faith.data();
}
void *FaithReligion(void *faith) {
  return Get<std::uint32_t>(faith, r::kFaithReligionIdOffset) == Fixture::actor_religion_id ?
      f->actor_religion.data() : f->target_religion.data();
}
void *FaithMain(void *faith) { return faith == f->actor_faith.data() ? f->actor_main.data() : f->target_main.data(); }
std::uint8_t RiteLevel(void *component, void *source, void *target) {
  ++f->rite_calls;
  if (component != static_cast<std::byte *>(source) + d::kHostilityRiteComponentOffset ||
      (source != f->actor_rite.data() && source != f->target_rite.data()) ||
      (target != f->actor_rite.data() && target != f->target_rite.data())) f->bad_call = true;
  if (Get<std::uint32_t>(source, r::kRiteFaithIdOffset) == Get<std::uint32_t>(target, r::kRiteFaithIdOffset)) return 0;
  if (f->drift && f->rite_calls == 3) return 1;
  return source == f->actor_rite.data() ? f->forward_rite : f->reverse_rite;
}
std::uint8_t FaithLevel(void *source, void *target, bool offset) {
  ++f->faith_calls;
  if (offset || (source != f->actor_faith.data() && source != f->target_faith.data()) ||
      (target != f->actor_faith.data() && target != f->target_faith.data())) f->bad_call = true;
  if (source == target) return 0;
  return source == f->actor_faith.data() ? f->forward_faith : f->reverse_faith;
}
d::HostilityBindings Bind(Fixture &fixture) {
  f = &fixture;
  d::HostilityBindings b{}; b.enabled = true; b.context.enabled = true;
  b.context.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_storage_ptr, &Player};
  b.context.character_rite = &CharacterRite; b.context.character_faith = &CharacterFaith;
  b.context.rite_faith = &RiteFaith; b.context.faith_religion = &FaithReligion; b.context.faith_main_rite = &FaithMain;
  b.rite_storage_slot = &f->rite_storage_ptr; b.rite_hostility = &RiteLevel; b.faith_hostility = &FaithLevel;
  return b;
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &dir, const char *name, const d::HostilityObservation &out) {
  if (!dir.empty()) std::ofstream(dir / name) << d::SerializeHostilityObservation12002(out) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); d::HostilityObservation out{};
  if (!Check(d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 88, out), "actual provider path") ||
      !Check(out.available && out.capture_epoch == 88 && out.played_character_id == Fixture::character_id, "paused player root") ||
      !Check(out.target_rite_id == Fixture::target_rite_id && out.target_faith_id == Fixture::target_faith_id, "full generations retained") ||
      !Check(out.actor_rite_id != out.actor_main_rite_id && out.target_rite_id != out.target_main_rite_id, "personal and main rite distinct") ||
      !Check(out.actor_rite_towards_target == d::HostilityLevel::hostile && out.target_rite_towards_actor == d::HostilityLevel::righteous, "asymmetric Rite native results") ||
      !Check(out.actor_faith_towards_target == d::HostilityLevel::evil && out.target_faith_towards_actor == d::HostilityLevel::astray, "Faith results remain independent from Rite") ||
      !Check(out.same_faith == false && out.same_religion == false, "identity classification") ||
      !Check(!q.bad_call && q.rite_calls == 4 && q.faith_calls == 4, "two actual frames; owning component and offset false") ||
      !Check(std::string(d::HostilityLevelKey(d::HostilityLevel::righteous)) == "righteous" &&
             std::string(d::HostilityLevelKey(d::HostilityLevel::astray)) == "astray" &&
             std::string(d::HostilityLevelKey(d::HostilityLevel::hostile)) == "hostile" &&
             std::string(d::HostilityLevelKey(d::HostilityLevel::evil)) == "evil", "stock enum labels")) return 1;
  Wire(directory, "asymmetric.json", out);
  q.forward_rite = 0; q.forward_faith = 0;
  if (!Check(d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 89, out) &&
             out.actor_rite_towards_target == d::HostilityLevel::righteous && out.same_religion == false,
             "native override preserved; different Religion does not imply evil")) return 2;
  Wire(directory, "different-religion-righteous.json", out);
  Put(q.target_faith, r::kFaithReligionIdOffset, Fixture::actor_religion_id);
  if (!Check(d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 90, out) && out.same_religion == true &&
             out.same_faith == false && out.target_faith_towards_actor == d::HostilityLevel::astray, "same Religion retains final native result")) return 3;
  Wire(directory, "same-religion.json", out);
  Put(q.target_rite, r::kRiteFaithIdOffset, Fixture::actor_faith_id);
  if (!Check(d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 91, out) && out.same_faith == true &&
             out.actor_rite_towards_target == d::HostilityLevel::righteous &&
             out.target_faith_towards_actor == d::HostilityLevel::righteous && out.actor_rite_id != out.target_rite_id,
             "different Rites of same Faith")) return 4;
  Wire(directory, "same-faith.json", out);
  Put(q.target_rite, r::kRiteFaithIdOffset, Fixture::target_faith_id);
  Put(q.target_rite, 8, std::uint32_t{0}); Put(q.rite_slots, 8, q.target_rite.data());
  if (!Check(d::ReadPlayedHostilityTowardsRite12002(b, 0, 92, out) && out.target_rite_id == 0U,
             "zero full reference is legal")) return 5;
  Wire(directory, "zero-target-id.json", out);
  Put(q.target_rite, 8, Fixture::target_rite_id);
  if (!Check(!d::ReadPlayedHostilityTowardsRite12002(b, 0x82000002, 93, out) &&
             out.failure == d::HostilityFailure::target_rite_unavailable && !out.actor_rite_towards_target,
             "actual storage full-generation match")) return 6;
  Wire(directory, "target-unavailable.json", out);
  q.forward_rite = 4;
  if (!Check(!d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 94, out) &&
             out.failure == d::HostilityFailure::native_level_unavailable && !out.actor_rite_towards_target,
             "native invalid sentinel remains unavailable")) return 7;
  Wire(directory, "native-sentinel.json", out);
  q.forward_rite = 2; q.rite_calls = 0; q.drift = true;
  if (!Check(!d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 95, out) &&
             out.failure == d::HostilityFailure::state_changed, "actual second native read differs")) return 8;
  q.drift = false; q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 96, out) &&
             out.failure == d::HostilityFailure::frame_not_paused, "paused owner requirement")) return 9;
  q.jomini[0x20] = std::byte{1}; Put(q.actor_main, 8, std::uint32_t{0x03000005});
  if (!Check(!d::ReadPlayedHostilityTowardsRite12002(b, Fixture::target_rite_id, 97, out) &&
             out.failure == d::HostilityFailure::main_rite_unavailable, "Faith path does not invent a main Rite")) return 10;
  const auto real = d::BindHostilityImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(real.enabled && real.context.core.enabled &&
             reinterpret_cast<std::uintptr_t>(real.rite_storage_slot) == 0x145D1E2F8 &&
             reinterpret_cast<std::uintptr_t>(real.rite_hostility) == 0x142591CE0 &&
             reinterpret_cast<std::uintptr_t>(real.faith_hostility) == 0x14243E950, "exact image binding") ||
      !Check(!d::BindHostilityImage12002(0x140000000, "old").enabled, "exact build binding")) return 11;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

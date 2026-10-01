#include "xar_bridge/ck3_12002_religion_conversion_faith.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace n = xar::ck3_12002;
namespace q = xar::ck3_12002::religion_conversion::faith;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T> void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> world = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_storage{}, faith_storage{};
  Bytes<0x80> character_slots{}, faith_slots{};
  Bytes<0x1D8> actor{};
  Bytes<0x120> current{}, target{};
  Bytes<0x4C0> current_main{}, target_main{};
  std::array<void *, 2> faiths{current.data(), target.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_storage_ptr = character_storage.data(), *faith_storage_ptr = faith_storage.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t current_id = 0x81000002u, target_id = 0x83000003u;
  static constexpr std::uint32_t current_main_id = 0x82000001u, target_main_id = 0x84000001u;
  bool target_passes = true, wrong_rite = false, drift = false, invocation_ok = true;
  int calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, world.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(world, n::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(world, n::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_storage, 0x20, character_slots.data()); Put(character_storage, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 16 + 8, actor.data()); Put(actor, 0x18, actor_id);
    Put(faith_storage, 0x20, faith_slots.data()); Put(faith_storage, 0x2C, std::int32_t{8});
    Put(faith_slots, 2 * 16 + 8, current.data()); Put(faith_slots, 3 * 16 + 8, target.data());
    Put(current, 8, current_id); Put(target, 8, target_id);
    Put(current, q::kFaithMainRiteIdOffset, current_main_id); Put(target, q::kFaithMainRiteIdOffset, target_main_id);
    Put(current_main, 8, current_main_id); Put(target_main, 8, target_main_id);
    Put(world, q::kWorldFaithsOffset, faiths.data()); Put(world, q::kWorldFaithCountOffset, std::int32_t{2});
    NativeTag(current, "current"); NativeTag(target, "target\"faith");
  }
  static void NativeTag(Bytes<0x120> &faith, std::string_view text) {
    std::memcpy(faith.data() + 0xE0, text.data(), text.size());
    Put(faith, 0xF0, static_cast<std::uint64_t>(text.size())); Put(faith, 0xF8, std::uint64_t{15});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CurrentFaith(void *) { return f->current.data(); }
void *MainRite(void *faith) { return faith == f->current.data() ? f->current_main.data() : f->target_main.data(); }
void *RiteFaith(void *rite) {
  if (f->wrong_rite && rite == f->target_main.data()) return f->current.data();
  return rite == f->current_main.data() ? f->current.data() : f->target.data();
}
const void *Tag(void *faith) { return static_cast<std::byte *>(faith) + 0xE0; }
bool Rule(void *actor, std::uint32_t target, void *reasons) {
  ++f->calls;
  f->invocation_ok = f->invocation_ok && actor == f->actor.data() && !reasons &&
      (target == Fixture::current_id || target == Fixture::target_id);
  if (f->drift) Put(f->state, 8, std::int32_t{53175817});
  return target == Fixture::target_id && f->target_passes;
}
q::Bindings Bind(Fixture &fixture) {
  f = &fixture; q::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_storage_ptr, &Player};
  b.faith_storage_slot = &f->faith_storage_ptr; b.character_faith = &CurrentFaith;
  b.faith_main_rite = &MainRite; b.rite_faith = &RiteFaith;
  b.faith_tag = &Tag; b.conversion_rule = &Rule; return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &out, const char *name, const q::Choices &choices) {
  if (!out.empty()) std::ofstream(out / name) << q::SerializePlayedFaithConversionChoices12002(choices) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture fixture; auto b = Bind(fixture); q::Choices out;
  if (!Check(q::ReadPlayedFaithConversionChoices12002(b, 17, out), "actual registry provider") ||
      !Check(out.available && out.choices.size() == 2 && out.capture_epoch == 17, "two actual rows") ||
      !Check(out.current_faith_id == Fixture::current_id, "current full generation") ||
      !Check(out.choices[1].faith_id == Fixture::target_id && out.choices[1].main_rite_id == Fixture::target_main_id,
             "candidate full Faith and Rite generations") ||
      !Check(!out.choices[0].native_faith_rule_passes && out.choices[1].native_faith_rule_passes,
             "consume native final faith predicate, not identity approximation") ||
      !Check(fixture.calls == 2 && fixture.invocation_ok, "actual actor, full IDs, null reasons ABI") ||
      !Check(out.choices[1].faith_key == "target\"faith", "native tags copy")) return 1;
  Wire(directory, "choices.json", out);
  fixture.target_passes = false;
  if (!Check(q::ReadPlayedFaithConversionChoices12002(b, 18, out) && !out.choices[1].native_faith_rule_passes,
             "scripted gate changes with same identity")) return 2;
  Wire(directory, "rule-blocked.json", out);
  fixture.target_passes = true;
  Put(fixture.target, q::kFaithMainRiteIdOffset, q::kAbsentId);
  if (!Check(q::ReadPlayedFaithConversionChoices12002(b, 19, out) && !out.choices[1].main_rite_id,
             "legitimate missing main rite preserves null")) return 3;
  Wire(directory, "no-main-rite.json", out);
  Put(fixture.target, q::kFaithMainRiteIdOffset, Fixture::target_main_id);
  fixture.wrong_rite = true;
  if (!Check(!q::ReadPlayedFaithConversionChoices12002(b, 20, out) && out.choices.empty() &&
             out.unavailable_reason == "faith_main_rite_unavailable", "main Rite belongs to another Faith")) return 4;
  fixture.wrong_rite = false;
  Put(fixture.target, 8, std::uint32_t{0x85000003u});
  if (!Check(q::ReadPlayedFaithConversionChoices12002(b, 21, out) && out.choices[1].faith_id == 0x85000003u &&
             !out.choices[1].native_faith_rule_passes, "registry uses current full object generation")) return 5;
  Put(fixture.target, 8, Fixture::target_id); fixture.invocation_ok = true;
  Put(fixture.faith_slots, 3 * 16 + 8, fixture.current.data());
  if (!Check(!q::ReadPlayedFaithConversionChoices12002(b, 22, out) && out.choices.empty() &&
             out.unavailable_reason == "faith_candidate_unavailable", "registry and actual storage disagree")) return 6;
  Wire(directory, "candidate-unavailable.json", out);
  Put(fixture.faith_slots, 3 * 16 + 8, fixture.target.data()); fixture.drift = true;
  if (!Check(!q::ReadPlayedFaithConversionChoices12002(b, 23, out) && out.choices.empty() &&
             out.unavailable_reason == "state_changed", "actual final sample changed")) return 7;
  Wire(directory, "state-changed.json", out);
  fixture.drift = false; fixture.jomini[0x20] = std::byte{0};
  if (!Check(!q::ReadPlayedFaithConversionChoices12002(b, 24, out) &&
             out.unavailable_reason == "frame_not_paused", "paused owner precondition")) return 8;
  fixture.jomini[0x20] = std::byte{1}; Put(fixture.world, q::kWorldFaithCountOffset, std::int32_t{0});
  if (!Check(q::ReadPlayedFaithConversionChoices12002(b, 25, out) && out.choices.empty(), "known empty registry")) return 9;
  Wire(directory, "empty.json", out);
  const auto actual = q::BindFaithConversionImage12002(0x140000000, n::kExecutableSha256);
  if (!Check(actual.enabled && reinterpret_cast<std::uintptr_t>(actual.conversion_rule) == 0x141D635E0 &&
             reinterpret_cast<std::uintptr_t>(actual.faith_storage_slot) == 0x145D1E300,
             "actual exact image binder") ||
      !Check(!q::BindFaithConversionImage12002(0x140000000, "old").enabled &&
             !q::BindFaithConversionImage12002(0, n::kExecutableSha256).enabled, "exact SHA binding")) return 10;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

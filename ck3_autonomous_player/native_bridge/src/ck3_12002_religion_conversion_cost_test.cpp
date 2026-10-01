#include "xar_bridge/ck3_12002_religion_conversion_cost.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion::conversion_cost;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &b, std::size_t offset, T value) {
  std::memcpy(b.data() + offset, &value, sizeof(value));
}
struct Fixture {
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> character_db{}, rite_db{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x120> resources{};
  Bytes<0x4C0> current_rite{}, target_rite{}, same_faith_rite{};
  Bytes<0x10> current_faith{}, target_faith{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_db_ptr = character_db.data(), *rite_db_ptr = rite_db.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_rite_id = 0xA0000002;
  static constexpr std::uint32_t same_faith_rite_id = 0xB0000003;
  static constexpr std::uint32_t current_faith_id = 0x81000001, target_faith_id = 0x82000002;
  bool command_valid = true;
  bool target_faith_missing = false;
  bool drift = false;
  int calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(character_db, 0x20, character_slots.data()); Put(character_db, 0x2C, std::uint32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0}); Put(character, 0x1B0, resources.data());
    Put(resources, 0x110, std::int64_t{40'000'000});
    Put(current_rite, 8, std::uint32_t{0}); Put(current_rite, 0x4B8, current_faith_id);
    Put(target_rite, 8, target_rite_id); Put(target_rite, 0x4B8, target_faith_id);
    Put(same_faith_rite, 8, same_faith_rite_id); Put(same_faith_rite, 0x4B8, current_faith_id);
    Put(current_faith, 8, current_faith_id); Put(target_faith, 8, target_faith_id);
    Put(rite_db, 0x20, rite_slots.data()); Put(rite_db, 0x2C, std::uint32_t{8});
    Put(rite_slots, 8, current_rite.data()); Put(rite_slots, 2 * 0x10 + 8, target_rite.data());
    Put(rite_slots, 3 * 0x10 + 8, same_faith_rite.data());
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *CurrentRite(void *) { return f->current_rite.data(); }
void *CurrentFaith(void *) { return f->current_faith.data(); }
void *RiteFaith(void *rite) {
  return rite == f->target_rite.data() ?
      (f->target_faith_missing ? nullptr : f->target_faith.data()) : f->current_faith.data();
}
std::int32_t NativeCost(const r::NativeCostCommand *cmd, void *tooltip) {
  ++f->calls;
  bool base_zero = cmd->flags == 0;
  for (const auto b : cmd->reserved) base_zero &= b == std::byte{};
  f->command_valid &= cmd->actor_id == Fixture::actor_id &&
      cmd->pay_piety == 1 && !tooltip && base_zero &&
      cmd->primary_vtable == 0x144770340 && cmd->secondary_vtable == 0x1447703D8;
  const auto points = cmd->target_rite_id == Fixture::same_faith_rite_id ? 251 : 377;
  return points + (f->drift && f->calls % 2 == 0 ? 1 : 0);
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture; r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_db_ptr, &Player};
  b.rite_database = &f->rite_db_ptr;
  b.character_rite = &CurrentRite; b.character_faith = &CurrentFaith; b.rite_faith = &RiteFaith;
  b.final_piety_cost = &NativeCost;
  b.command_vtable = 0x144770340; b.command_secondary_vtable = 0x1447703D8;
  return b;
}
int checks = 0;
bool Check(bool ok, const char *message) {
  ++checks; if (!ok) std::cerr << "FAIL " << message << '\n'; return ok;
}
void Wire(const std::filesystem::path &dir, const char *name, const r::Cost &cost) {
  if (!dir.empty()) std::ofstream(dir / name) << r::SerializeReligionConversionCost12002(cost) << '\n';
}
} // namespace

int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; auto b = Bind(q); r::Cost out{};
  if (!Check(r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 88, out), "faith conversion cost") ||
      !Check(q.command_valid && q.calls == 2, "actual local command layout with paid flag and null tooltip") ||
      !Check(out.piety_points == 377 && out.piety_cost_raw == 37'700'000, "whole native point return converted to transport raw") ||
      !Check(out.actor_piety_raw == 40'000'000 && out.can_afford_piety == true, "real balance affordability") ||
      !Check(out.target_faith_id == Fixture::target_faith_id && out.same_faith == false, "full target identity and faith distinction")) return 1;
  Wire(dir, "faith-cost.json", out);
  Put(q.resources, 0x110, std::int64_t{25'099'999});
  if (!Check(r::ReadPlayedReligionConversionCost12002(b, Fixture::same_faith_rite_id, 89, out) &&
      out.same_faith == true && out.piety_points == 251 && out.can_afford_piety == false,
      "same faith Rite uses cost getter, fractional balance remains short")) return 2;
  Wire(dir, "rite-short.json", out);
  Put(q.resources, 0x110, std::int64_t{-100'001});
  if (!Check(r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 90, out) &&
      out.actor_piety_raw == -100'001 && out.can_afford_piety == false,
      "signed debt preserved without inventing free conversion")) return 3;
  Wire(dir, "piety-debt.json", out);
  Put(q.character, 0x1B0, static_cast<void *>(nullptr));
  if (!Check(r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 91, out) &&
      out.actor_piety_raw == 0 && out.piety_points == 377 && out.can_afford_piety == false,
      "native absent-resource balance is legal zero, cost still evaluated")) return 4;
  Wire(dir, "zero-wallet.json", out);
  const auto before = q.calls;
  if (!Check(!r::ReadPlayedReligionConversionCost12002(b, 0xA1000002, 92, out) &&
      out.failure == r::Failure::target_rite_unavailable && !out.piety_points && q.calls == before,
      "full target Rite identity resolves current database object")) return 5;
  Wire(dir, "target-unavailable.json", out);
  q.target_faith_missing = true;
  if (!Check(!r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 93, out) &&
      out.failure == r::Failure::target_faith_unavailable && !out.actor_piety_raw,
      "target faith read failure does not produce zero fee")) return 6;
  q.target_faith_missing = false; q.drift = true; q.calls = 0;
  if (!Check(!r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 94, out) &&
      out.failure == r::Failure::state_changed, "two paused dynamic cost reads agree")) return 7;
  q.drift = false; q.jomini[0x20] = std::byte{};
  if (!Check(!r::ReadPlayedReligionConversionCost12002(b, Fixture::target_rite_id, 95, out) &&
      out.failure == r::Failure::frame_not_paused, "only paused owner")) return 8;
  const auto actual = r::BindReligionConversionCostImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(actual.enabled && actual.core.enabled &&
      reinterpret_cast<std::uintptr_t>(actual.final_piety_cost) == 0x1429A3DE0 &&
      reinterpret_cast<std::uintptr_t>(actual.rite_database) == 0x145D1E2F8 &&
      actual.command_vtable == 0x144770340 && actual.command_secondary_vtable == 0x1447703D8,
      "exact final cost binder") ||
      !Check(!r::BindReligionConversionCostImage12002(0x140000000, "old").enabled,
      "exact build binding")) return 9;
  std::cout << "PASS checks=" << checks << " cases=9 actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

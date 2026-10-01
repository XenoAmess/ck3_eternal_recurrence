#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace r = xar::ck3_12002::religion_conversion_rite;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &bytes, std::size_t at, T value) {
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
  Bytes<0x30> characters{}, rites{};
  Bytes<0x80> character_slots{}, rite_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x500> current{}, target{};
  Bytes<0x60> faith{};
  std::array<std::uint32_t, 2> rite_ids{0, 0x82000002U};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = characters.data(), *rites_ptr = rites.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t faith_id = 0x83000003U;
  bool rule_gate = true, can_pay = true, command_shape = true, null_reasons = true;
  int without_payment_calls = 0, with_payment_calls = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2});
    Put(state, 0xA0, data.data()); Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(characters, 0x20, character_slots.data()); Put(characters, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0});
    Put(rites, 0x20, rite_slots.data()); Put(rites, 0x2C, std::int32_t{8});
    Put(rite_slots, 8, current.data()); Put(rite_slots, 2 * 0x10 + 8, target.data());
    Put(current, 8, std::uint32_t{0}); Put(target, 8, rite_ids[1]);
    Put(current, 0x4B8, faith_id); Put(target, 0x4B8, faith_id); Put(faith, 8, faith_id);
    Put(faith, 0x20, rite_ids.data()); Put(faith, 0x28, std::int32_t{2});
    Put(faith, 0x2C, std::int32_t{2});
  }
};
Fixture *fixture = nullptr;
void *LocalPlayer(void *) { return fixture->player.data(); }
void *CharacterFaith(void *) { return fixture->faith.data(); }
const void *FaithRites(void *faith) { return static_cast<std::byte *>(faith) + 0x20; }
bool NativeValidate(const r::FaithAndRiteConversionCommand *command, void *reasons) {
  fixture->null_reasons = fixture->null_reasons && reasons == nullptr;
  fixture->command_shape = fixture->command_shape && command->actor_id == Fixture::actor_id &&
      command->primary_vtable == 0x144770340 && command->secondary_vtable == 0x1447703D8 &&
      command->flags == 0 && command->reserved == std::array<std::byte, 15>{} &&
      command->tail == std::array<std::byte, 7>{};
  if (command->pay_piety) ++fixture->with_payment_calls;
  else ++fixture->without_payment_calls;
  return fixture->rule_gate && (!command->pay_piety || fixture->can_pay);
}
r::Bindings Bind(Fixture &f) {
  fixture = &f; r::Bindings b{}; b.enabled = true; b.module_base = 0x140000000;
  b.core = {true, &f.state_ptr, &f.jomini_ptr, &f.characters_ptr, &LocalPlayer};
  b.rite_storage_slot = &f.rites_ptr; b.validate = &NativeValidate;
  b.character_faith = &CharacterFaith; b.faith_rites = &FaithRites; return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &dir, const char *name, const r::Preview &p) {
  if (!dir.empty()) std::ofstream(dir / name) << r::SerializeRitePreview12002(p) << '\n';
}
void Wire(const std::filesystem::path &dir, const char *name, const r::FaithRites &p) {
  if (!dir.empty()) std::ofstream(dir / name) << r::SerializeCurrentFaithRites12002(p) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture f; auto b = Bind(f); r::Preview p{}; r::FaithRites ids{};
  if (!Check(r::ReadRitePreview12002(b, 501, f.rite_ids[1], p), "actual source query") ||
      !Check(p.available && p.validator_with_payment && p.validator_without_payment &&
             p.same_faith && p.different_from_current_rite, "paid same faith verdict") ||
      !Check(p.current_rite_id == 0 && p.target_rite_id == 0x82000002U &&
             p.current_faith_id == Fixture::faith_id && p.target_faith_id == Fixture::faith_id,
             "full generation references including zero") ||
      !Check(f.command_shape && f.null_reasons && f.with_payment_calls == 1 &&
             f.without_payment_calls == 1, "real command layout and two distinct diagnostics")) return 1;
  Wire(dir, "same-faith-paid.json", p);
  f.can_pay = false;
  if (!Check(r::ReadRitePreview12002(b, 502, f.rite_ids[1], p) &&
             p.validator_without_payment && !p.validator_with_payment,
             "rule allowed payment refused is an available native negative")) return 2;
  Wire(dir, "insufficient-piety.json", p); f.rule_gate = false;
  if (!Check(r::ReadRitePreview12002(b, 503, f.rite_ids[1], p) &&
             !p.validator_without_payment && !p.validator_with_payment,
             "rule refused is separate from read failure")) return 3;
  Wire(dir, "rule-refused.json", p); f.rule_gate = true; f.can_pay = true;
  Put(f.target, 0x4B8, std::uint32_t{0x84000006});
  if (!Check(r::ReadRitePreview12002(b, 504, f.rite_ids[1], p) && !p.same_faith &&
             p.target_faith_id == 0x84000006U && p.validator_with_payment,
             "different faith uses the same native final validator")) return 4;
  Wire(dir, "different-faith-paid.json", p); Put(f.target, 0x4B8, Fixture::faith_id);
  if (!Check(r::ReadRitePreview12002(b, 505, 0, p) && !p.different_from_current_rite,
             "same target exposes native entry difference separately")) return 5;
  Wire(dir, "already-current.json", p);
  if (!Check(r::ReadCurrentFaithRites12002(b, 506, ids) &&
             ids.rite_ids == std::vector<std::uint32_t>{0, 0x82000002U} &&
             ids.faith_id == Fixture::faith_id, "actual association order and stride4")) return 6;
  Wire(dir, "faith-rites.json", ids);
  Put(f.faith, 0x2C, std::int32_t{0});
  if (!Check(r::ReadCurrentFaithRites12002(b, 507, ids) && ids.rite_ids.empty(),
             "native known empty list is available")) return 7;
  Wire(dir, "faith-rites-empty.json", ids); Put(f.faith, 0x2C, std::int32_t{2});
  Put(f.target, 8, std::uint32_t{0x81000002});
  const int calls = f.with_payment_calls;
  if (!Check(!r::ReadRitePreview12002(b, 508, f.rite_ids[1], p) &&
             p.failure == r::Failure::target_rite_unavailable && f.with_payment_calls == calls,
             "stale generation is unavailable before native validator")) return 8;
  Wire(dir, "target-unavailable.json", p); Put(f.target, 8, f.rite_ids[1]);
  f.jomini[0x20] = std::byte{0};
  if (!Check(!r::ReadRitePreview12002(b, 509, f.rite_ids[1], p) &&
             p.failure == r::Failure::frame_not_paused && f.with_payment_calls == calls,
             "paused owner requirement")) return 9;
  Wire(dir, "frame-not-paused.json", p);
  const auto native = r::BindRiteConversionImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(native.enabled && reinterpret_cast<std::uintptr_t>(native.validate) == 0x1429A34C0 &&
             reinterpret_cast<std::uintptr_t>(native.rite_storage_slot) == 0x145D1E2F8 &&
             reinterpret_cast<std::uintptr_t>(native.faith_rites) == 0x140B801B0,
             "exact executable binder") ||
      !Check(!r::BindRiteConversionImage12002(0x140000000, "old").enabled,
             "old executable has no native binding")) return 10;
  std::cout << "PASS " << checks << " checks; target preview and native association fixture\n";
  return 0;
}

#include "xar_bridge/ck3_12002_religion_conversion_reasons.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace q = xar::ck3_12002::religion_conversion::reasons;
namespace r = xar::ck3_12002::religion_conversion_rite;
namespace c = xar::ck3_12002;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename B, typename T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data()+at, &value, sizeof(value));
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
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *characters_ptr = characters.data(), *rites_ptr = rites.data();
  static constexpr std::int32_t actor_id = 0x03000004;
  static constexpr std::uint32_t target_id = 0x82000002U;
  std::string text = "Not adult.";
  bool native_accepted = false, initialized_string = true, command_shape = true;
  int calls = 0, destroys = 0, allocations = 0, heap_destroys = 0;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2});
    Put(state, 0xA0, data.data()); Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset+0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset+0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, actor_id);
    Put(characters, 0x20, character_slots.data()); Put(characters, 0x2C, std::int32_t{8});
    Put(character_slots, 4*0x10+8, character.data()); Put(character, 0x18, actor_id);
    Put(character, 0xB4, std::uint32_t{0});
    Put(rites, 0x20, rite_slots.data()); Put(rites, 0x2C, std::int32_t{8});
    Put(rite_slots, 8, current.data()); Put(rite_slots, 2*0x10+8, target.data());
    Put(current, 8, std::uint32_t{0}); Put(target, 8, target_id);
  }
};
Fixture *f = nullptr;
void *LocalPlayer(void *) { return f->player.data(); }
bool NativeValidate(const r::FaithAndRiteConversionCommand *command, void *raw) {
  ++f->calls;
  auto &reason = *static_cast<q::NativeReasonString *>(raw);
  f->initialized_string = f->initialized_string && reason.size == 0 && reason.capacity == 15 &&
      reason.storage[0] == std::byte{0};
  f->command_shape = f->command_shape && command->primary_vtable == 0x144770340 &&
      command->secondary_vtable == 0x1447703D8 && command->actor_id == Fixture::actor_id &&
      command->target_rite_id == Fixture::target_id && command->pay_piety == 1;
  reason.size = static_cast<std::uint64_t>(f->text.size());
  if (f->text.size() < 16) {
    std::memcpy(reason.storage.data(), f->text.c_str(), f->text.size()+1);
  } else {
    auto *heap = new char[f->text.size()+1]; ++f->allocations;
    std::memcpy(heap, f->text.c_str(), f->text.size()+1);
    std::memcpy(reason.storage.data(), &heap, sizeof(heap));
    reason.capacity = static_cast<std::uint64_t>(f->text.size());
  }
  return f->native_accepted;
}
void NativeDestroy(q::NativeReasonString *string) {
  ++f->destroys;
  if (string->capacity >= 16) {
    char *data = nullptr; std::memcpy(&data, string->storage.data(), sizeof(data));
    delete[] data; ++f->heap_destroys;
  }
  string->size = 0; string->capacity = 15; string->storage[0] = std::byte{0};
}
q::Bindings Bind(Fixture &fixture) {
  f = &fixture; q::Bindings b{};
  b.rite.enabled = true; b.rite.module_base = 0x140000000;
  b.rite.core = {true, &f->state_ptr, &f->jomini_ptr, &f->characters_ptr, &LocalPlayer};
  b.rite.rite_storage_slot = &f->rites_ptr; b.rite.validate = &NativeValidate;
  b.destroy_string = &NativeDestroy; return b;
}
int checks = 0;
bool Check(bool value, const char *name) {
  ++checks; if (!value) std::cerr << "FAIL " << name << '\n'; return value;
}
void Wire(const std::filesystem::path &dir, const char *name, const q::Reasons &out) {
  if (!dir.empty()) std::ofstream(dir/name) << q::SerializeReligionConversionReasons12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto dir = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture fixture; auto b = Bind(fixture); q::Reasons out{};
  if (!Check(q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 901, out),
             "owned native SSO source") ||
      !Check(out.available && out.native_paid_validator_passes == false &&
             out.raw_native_text == "Not adult." && out.ui_blocker_text == "Not adult.\n",
             "native rejection with raw text and actual UI newline normalization") ||
      !Check(fixture.initialized_string && fixture.command_shape &&
             fixture.calls == 1 && fixture.destroys == 1 && fixture.heap_destroys == 0,
             "native ctor ABI, paid command and one owning destructor")) return 1;
  Wire(dir, "native-refusal-sso.json", out);
  fixture.text = "#N Cannot adopt \"target Rite\".#!\n知晓程度不足。\n";
  if (!Check(q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 902, out) &&
             out.raw_native_text == fixture.text && out.ui_blocker_text == fixture.text,
             "heap-backed UTF8, markup and multiline native text preserved") ||
      !Check(fixture.allocations == 1 && fixture.heap_destroys == 1 && fixture.destroys == 2,
             "game-owned heap buffer destroyed after copy") ||
      !Check(q::SerializeReligionConversionReasons12002(out).find("\\\"target Rite\\\"") != std::string::npos,
             "actual serializer escapes native quotes")) return 2;
  Wire(dir, "native-refusal-heap.json", out);
  fixture.native_accepted = true; fixture.text.clear();
  if (!Check(q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 903, out) &&
             out.native_paid_validator_passes == true && out.raw_native_text == "" &&
             out.ui_blocker_text == "", "available allowed result has known empty text")) return 3;
  Wire(dir, "native-allowed-empty.json", out);
  fixture.text = "A native formatted explanation.";
  if (!Check(q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 904, out) &&
             out.native_paid_validator_passes == true && out.raw_native_text == fixture.text,
             "text presence is never a substitute for native verdict")) return 4;
  Wire(dir, "native-allowed-with-text.json", out);
  fixture.native_accepted = false; fixture.text.clear();
  if (!Check(q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 905, out) &&
             out.native_paid_validator_passes == false && out.ui_blocker_text == "",
             "available native rejection can have known empty formatter text")) return 5;
  Wire(dir, "native-refusal-empty.json", out);
  const int calls = fixture.calls, destroys = fixture.destroys;
  Put(fixture.target, 8, std::uint32_t{0x81000002});
  if (!Check(!q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 906, out) &&
             out.failure == q::Failure::target_rite_unavailable && !out.ui_blocker_text &&
             fixture.calls == calls && fixture.destroys == destroys,
             "unavailable target never enters native formatter")) return 6;
  Wire(dir, "target-unavailable.json", out); Put(fixture.target, 8, Fixture::target_id);
  fixture.jomini[0x20] = std::byte{0};
  if (!Check(!q::ReadPlayedReligionConversionReasons12002(b, Fixture::target_id, 907, out) &&
             out.failure == q::Failure::frame_not_paused && fixture.calls == calls &&
             fixture.destroys == destroys, "new source uses existing paused owner convention")) return 7;
  Wire(dir, "frame-not-paused.json", out);
  const auto native = q::BindReligionConversionReasonsImage12002(0x140000000, c::kExecutableSha256);
  if (!Check(native.rite.enabled && reinterpret_cast<std::uintptr_t>(native.destroy_string) == 0x140856050 &&
             reinterpret_cast<std::uintptr_t>(native.rite.validate) == 0x1429A34C0,
             "exact image reason formatter/destructor binding") ||
      !Check(!q::BindReligionConversionReasonsImage12002(0x140000000, "old").destroy_string,
             "older image has no reason ABI binding")) return 8;
  std::cout << "PASS " << checks << " checks; native reason string lifetime and serializer\n";
  return 0;
}

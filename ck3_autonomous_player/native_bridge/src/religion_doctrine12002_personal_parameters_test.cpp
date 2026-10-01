#include "xar_bridge/religion_doctrine12002_personal_parameters.hpp"

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
template <typename T> T Get(const void *object, std::size_t at) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value)); return value;
}
struct Fixture {
  Bytes<0xA8> state{}, extension{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x22350);
  Bytes<0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  Bytes<0x30> storage{};
  Bytes<0x80> slots{};
  Bytes<0x1D8> character{};
  Bytes<0xF38> database{};
  Bytes<0x758> guest{}, adaptive{}, unowned{};
  std::array<const void *, 2> owned{guest.data(), adaptive.data()};
  std::array<std::int32_t, 4> supported{1, 2, 3, 4};
  std::array<std::int32_t, 1> guest_tokens{2}, adaptive_tokens{3}, unowned_tokens{4};
  std::array<std::string, 4> names{"meditation_mechanics_active",
      "tenet_ritual_hospitality_free_guest_recruitment", "tenet_adaptive_study_rite_bonus",
      "tenet_adoptionism_adoption_personal_active"};
  std::array<Bytes<0x20>, 4> native_names{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  const void *database_ptr = database.data();
  static constexpr std::int32_t character_id = 0x03000004;
  int getter_calls = 0, membership_calls = 0;
  bool drift = false, bad_key = false;
  Fixture() {
    Put(state, 8, std::int32_t{53175816}); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(data, c::kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry, 0xD8, std::int32_t{7}); Put(entry, 0xB0, character_id);
    Put(storage, 0x20, slots.data()); Put(storage, 0x2C, std::int32_t{8});
    Put(slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, character_id);
    Put(character, r::kCharacterRiteIdOffset, r::kAbsentReference);
    Put(character, d::kPersonalParameterCharacterExtensionOffset, extension.data());
    Put(extension, d::kPersonalParameterOwnedTenetsOffset, owned.data());
    Put(extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{2});
    Put(database, d::kPersonalParameterSupportedSetOffset, supported.data());
    Put(database, d::kPersonalParameterSupportedSetOffset + 0xC, std::int32_t{4});
    Definition(guest, "tenet_guest", guest_tokens.data());
    Definition(adaptive, "tenet_adaptive", adaptive_tokens.data());
    Definition(unowned, "tenet_unowned", unowned_tokens.data());
    for (std::size_t n = 0; n < names.size(); ++n) {
      Put(native_names[n], 0, names[n].data());
      Put(native_names[n], 0x10, static_cast<std::uint64_t>(names[n].size()));
      Put(native_names[n], 0x18, static_cast<std::uint64_t>(names[n].size()));
    }
  }
  static void Definition(Bytes<0x758> &definition, const char *key, const std::int32_t *tokens) {
    const auto size = std::strlen(key);
    std::memcpy(definition.data() + 0x18, key, size);
    Put(definition, 0x28, static_cast<std::uint64_t>(size));
    Put(definition, 0x30, std::uint64_t{15}); Put(definition, 0x38, std::uint32_t{0x4744624F});
    Put(definition, d::kPersonalParameterDefinitionSetOffset, tokens);
    Put(definition, d::kPersonalParameterDefinitionSetOffset + 0xC, std::int32_t{1});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
const void *Owned(const void *character) {
  ++f->getter_calls;
  if (f->drift && f->getter_calls == 2) f->adaptive_tokens[0] = 4;
  const auto *extension = Get<const std::byte *>(character, d::kPersonalParameterCharacterExtensionOffset);
  return extension ? extension + d::kPersonalParameterOwnedTenetsOffset : nullptr;
}
bool Contains(const void *collection, const std::int32_t *token) {
  ++f->membership_calls;
  const auto *data = Get<const std::int32_t *>(collection, 0);
  const auto count = Get<std::int32_t>(collection, 0xC);
  for (std::int32_t n = 0; n < count; ++n) if (data[n] == *token) return true;
  return false;
}
const void *Key(std::int32_t token) {
  if (f->bad_key || token < 1 || token > 4) return nullptr;
  return f->native_names[static_cast<std::size_t>(token - 1)].data();
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture; r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->storage_ptr, &Player}; return b;
}
d::PersonalParameterBindings BindParameters(Fixture &fixture) {
  return {true, &fixture.database_ptr, &Owned, &Contains, &Key};
}
int checks = 0;
bool Check(bool condition, const char *message) {
  ++checks; if (!condition) std::cerr << "FAIL " << message << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name, const d::PersonalParameterContext &out) {
  if (!directory.empty()) std::ofstream(directory / name) << d::SerializePersonalParameters12002(out) << '\n';
}
} // namespace
int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  Fixture q; const auto rbind = Bind(q); const auto b = BindParameters(q);
  d::PersonalParameterContext out{};
  if (!Check(d::ReadPlayedPersonalParameters12002(rbind, b, 101, out), "actual played provider without Rite/Faith") ||
      !Check(out.available && out.capture_epoch == 101 && out.date_raw == 53175816 &&
             out.played_character_id == Fixture::character_id, "real paused frame epoch full character") ||
      !Check(out.has_character_extension && out.personal_tenet_keys == std::vector<std::string>{"tenet_guest", "tenet_adaptive"},
             "actual owned stable Tenet keys only") ||
      !Check(out.parameters.size() == 4 && q.getter_calls == 2 && q.membership_calls > 8,
             "every actual supported key calls native membership") ||
      !Check(d::LookupPersonalParameter12002(out, q.names[1]).value == true &&
             d::LookupPersonalParameter12002(out, q.names[2]).value == true,
             "native any owned definition true flags") ||
      !Check(d::LookupPersonalParameter12002(out, q.names[0]).state == d::PersonalParameterLookupState::Value &&
             d::LookupPersonalParameter12002(out, q.names[0]).value == false,
             "supported known missing is Boolean false") ||
      !Check(d::LookupPersonalParameter12002(out, q.names[3]).value == false,
             "unowned authored definition does not contribute") ||
      !Check(d::LookupPersonalParameter12002(out, "undefined_flag").state == d::PersonalParameterLookupState::UnsupportedKey &&
             !d::LookupPersonalParameter12002(out, "undefined_flag").value,
             "undefined is unsupported distinct from known false")) return 1;
  Wire(directory, "current-personal-flags.json", out);
  Put(q.character, d::kPersonalParameterCharacterExtensionOffset, static_cast<void *>(nullptr));
  const auto before = q.getter_calls;
  if (!Check(d::ReadPlayedPersonalParameters12002(rbind, b, 102, out) && !out.has_character_extension &&
             out.personal_tenet_keys.empty() && q.getter_calls == before,
             "legal absent extension matches native early false without lazy getter") ||
      !Check(out.parameters.size() == 4 && d::LookupPersonalParameter12002(out, q.names[1]).value == false,
             "absent extension still complete supported false registry")) return 2;
  Wire(directory, "extension-absent.json", out);
  Put(q.character, d::kPersonalParameterCharacterExtensionOffset, q.extension.data());
  Put(q.extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{0});
  if (!Check(d::ReadPlayedPersonalParameters12002(rbind, b, 103, out) && out.has_character_extension &&
             out.personal_tenet_keys.empty() && d::LookupPersonalParameter12002(out, q.names[2]).value == false,
             "actual known empty collection supported false")) return 3;
  Wire(directory, "known-empty-personal.json", out);
  q.database_ptr = nullptr;
  if (!Check(!d::ReadPlayedPersonalParameters12002(rbind, b, 104, out) && !out.available &&
             out.failure == "parameter_registry_unavailable" &&
             d::LookupPersonalParameter12002(out, q.names[1]).state == d::PersonalParameterLookupState::UnavailableSource,
             "database read failure is unavailable not known false")) return 4;
  Wire(directory, "registry-unavailable.json", out); q.database_ptr = q.database.data();
  Put(q.extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{2}); q.bad_key = true;
  if (!Check(!d::ReadPlayedPersonalParameters12002(rbind, b, 105, out) && out.failure == "parameter_key_unavailable",
             "native key read failure typed")) return 5;
  Wire(directory, "key-unavailable.json", out); q.bad_key = false;
  q.drift = true; q.getter_calls = 0;
  if (!Check(!d::ReadPlayedPersonalParameters12002(rbind, b, 106, out) && out.failure == "state_changed",
             "actual sampled personal values changed")) return 6;
  Wire(directory, "state-changed.json", out); q.drift = false;
  Put(q.extension, d::kPersonalParameterOwnedTenetsOffset + 0xC, std::int32_t{-1});
  if (!Check(!d::ReadPlayedPersonalParameters12002(rbind, b, 107, out) &&
             out.failure == "personal_tenet_collection_unavailable", "bad actual collection is read failure")) return 7;
  q.jomini[0x20] = std::byte{0};
  if (!Check(!d::ReadPlayedPersonalParameters12002(rbind, b, 108, out) && out.failure == "frame_not_paused",
             "owner paused requirement")) return 8;
  const auto native = d::BindPersonalParameters12002(0x140000000, c::kExecutableSha256);
  if (!Check(native.enabled && reinterpret_cast<std::uintptr_t>(native.database_slot) ==
             0x140000000 + d::kPersonalParameterDatabaseSlotRva &&
             reinterpret_cast<std::uintptr_t>(native.owned_tenets) ==
             0x140000000 + d::kPersonalParameterCollectionGetterRva &&
             !d::BindPersonalParameters12002(0, c::kExecutableSha256).enabled &&
             !d::BindPersonalParameters12002(0x140000000, "old").enabled, "exact build initialized slot and native getter")) return 9;
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

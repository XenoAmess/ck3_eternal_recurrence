#include "xar_bridge/ck3_12002_epidemic_recovery.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace c = xar::ck3_12002;
namespace r = xar::ck3_12002::epidemic_recovery;
namespace old = xar::ck3_11906;
namespace {
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename Buffer, typename T>
void Put(Buffer &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
struct Target {
  std::uint16_t kind = 5, subtype = 0;
  std::uint32_t padding = 0;
  std::int64_t payload = 0;
};
static_assert(sizeof(Target) == 0x10);
struct Fixture {
  static constexpr std::int32_t actor = 0x03000004;
  static constexpr std::int32_t county_a = 0x04000002, county_b = 0x05000003;
  static constexpr std::int32_t date = 53175816;
  Bytes<0xA8> state{};
  Bytes<0x28> jomini{};
  Bytes<0x1F8> players{};
  Bytes<0x78> player{};
  std::vector<std::byte> game_data = std::vector<std::byte>(0x22360);
  Bytes<0xE0> player_entry{};
  std::array<void *, 1> player_entries{player_entry.data()};
  Bytes<0x30> character_store{}, title_store{};
  Bytes<0x80> character_slots{}, title_slots{};
  Bytes<0x1D8> character{};
  Bytes<0x90> title_a{}, title_b{}, template_a{}, template_b{};
  Bytes<0x50> context{}, row{};
  std::array<Target, 2> targets{{{5, 0, 0, county_a}, {5, 0, 0, county_b}}};
  Bytes<0x50> minor_definition{}, tiny_definition{}, fallback_definition{};
  std::string list_name = old::kPlayerEpidemicRecoveryListKeyV1;
  std::string minor_name = old::kPlayerEpidemicRecoveryMinorKeyV1;
  std::string tiny_name = old::kPlayerEpidemicRecoveryTinyKeyV1;
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *character_store_ptr = character_store.data(), *title_store_ptr = title_store.data();
  void *fallback_ptr = fallback_definition.data();
  std::array<bool, 2> minor{false, true}, tiny{true, false};
  bool context_fails = false, database_fails = false, lookup_fails = false;
  bool getter_fails = false, getter_bad_byte = false, frame_changes = false;
  int getter_calls = 0;
  Fixture() {
    Put(state, 8, date); Put(state, 0x70, std::int32_t{2}); Put(state, 0xA0, game_data.data());
    Put(jomini, 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players, 0x1F0, std::int32_t{7}); Put(player, 0x70, std::int32_t{7});
    Put(game_data, c::kPlayerCharacterManagerOffset + 0x58, player_entries.data());
    Put(game_data, c::kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(player_entry, 0xD8, std::int32_t{7}); Put(player_entry, 0xB0, actor);
    Put(character_store, 0x20, character_slots.data()); Put(character_store, 0x2C, std::int32_t{8});
    Put(character_slots, 4 * 0x10 + 8, character.data()); Put(character, 0x18, actor);
    Put(title_store, 0x20, title_slots.data()); Put(title_store, 0x2C, std::int32_t{8});
    Put(title_slots, 2 * 0x10 + 8, title_a.data()); Put(title_slots, 3 * 0x10 + 8, title_b.data());
    Put(title_a, 0x10, county_a); Put(title_b, 0x10, county_b);
    Put(title_a, 0x14, std::uint32_t{0x4C616E64}); Put(title_b, 0x14, std::uint32_t{0x4C616E64});
    Put(title_a, 0x48, template_a.data()); Put(title_b, 0x48, template_b.data());
    Put(template_a, 0x64, std::int32_t{2}); Put(template_b, 0x64, std::int32_t{2});
    Put(context, 0x30, row.data()); Put(context, 0x3C, std::int32_t{1});
    Put(row, 8, std::int32_t{0}); Put(row, 0x10, targets.data()); Put(row, 0x1C, std::int32_t{2});
    Name(minor_definition, minor_name); Name(tiny_definition, tiny_name);
  }
  static void Name(Bytes<0x50> &object, const std::string &value) {
    Put(object, 0x18, value.data()); Put(object, 0x28, value.size());
    Put(object, 0x30, std::size_t{64}); Put(object, 0x38, std::uint32_t{0x4744624F});
  }
};
Fixture *f = nullptr;
void *Player(void *) { return f->player.data(); }
void *IdentifierTable() { return f; }
std::int32_t *LookupIdentifier(void *, std::int32_t *out, const c::PhaseStringView32 *key) {
  if (std::string_view(key->data, static_cast<std::size_t>(key->size)) != f->list_name) return nullptr;
  *out = 0; return out;
}
const std::string *IdentifierName(void *, std::int32_t id) { return id == 0 ? &f->list_name : nullptr; }
void *Context(const c::PhaseVariableTarget *scope) {
  return !f->context_fails && scope->kind == 4 && scope->payload == Fixture::actor
             ? f->context.data() : nullptr;
}
void *Database() { return f->database_fails ? nullptr : f; }
std::uint32_t Hash(void *database, const char *key, std::uint32_t size) {
  if (database != f) return 0;
  const std::string_view value(key, size);
  return value == f->minor_name ? 1U : value == f->tiny_name ? 2U : 0U;
}
void *Lookup(void *, std::int32_t hash) {
  if (f->lookup_fails) return f->fallback_ptr;
  return hash == 1 ? f->minor_definition.data() : hash == 2 ? f->tiny_definition.data() : nullptr;
}
r::CountyModifierResult *Getter(r::CountyModifierResult *out, void *title, void *definition) {
  ++f->getter_calls;
  if (f->getter_fails) return nullptr;
  const auto index = title == f->title_a.data() ? 0U : 1U;
  out->native_time = 0;
  out->present = static_cast<std::uint8_t>(definition == f->minor_definition.data()
                                             ? f->minor[index] : f->tiny[index]);
  if (f->getter_bad_byte) out->present = 2;
  if (f->frame_changes) Put(f->state, 8, Fixture::date + 24);
  return out;
}
r::Bindings Bind(Fixture &fixture) {
  f = &fixture;
  r::Bindings b{}; b.enabled = true;
  b.core = {true, &f->state_ptr, &f->jomini_ptr, &f->character_store_ptr, &Player};
  b.identifiers.enabled = true; b.identifiers.variable_table = &IdentifierTable;
  b.identifiers.lookup_variable_identifier = &LookupIdentifier;
  b.identifiers.variable_identifier_name = &IdentifierName; b.identifiers.variable_context = &Context;
  b.landed_title_store_slot = &f->title_store_ptr; b.modifier_fallback_slot = &f->fallback_ptr;
  b.modifier_database = &Database; b.stable_key_hash = &Hash;
  b.modifier_lookup = &Lookup; b.county_modifier_getter = &Getter; return b;
}
int checks = 0;
bool Check(bool condition, const char *label) {
  ++checks; if (!condition) std::cerr << "FAIL " << label << '\n'; return condition;
}
void Wire(const std::filesystem::path &directory, const char *name,
          const old::PlayerEpidemicRecoveryV1 &value) {
  if (directory.empty()) return;
  const auto serialized = old::SerializePlayerEpidemicRecoveryV1(value);
  if (serialized.empty()) throw std::runtime_error("production serializer rejected fixture output");
  std::ofstream(directory / name) << serialized << '\n';
}
old::PlayerEpidemicRecoveryV1 Read(const r::Bindings &b, std::int32_t title = 0,
                                 std::uint64_t revision = 88) {
  return r::ReadEpidemicRecovery12002(b, revision, Fixture::date, Fixture::actor, title);
}
} // namespace

int main(int argc, char **argv) {
  const auto directory = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path{};
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Fixture q; auto b = Bind(q); auto out = Read(b);
  if (!Check(out.available && out.counties.size() == 2, "actual full recovery list") ||
      !Check(out.played_character_id == Fixture::actor && out.snapshot_revision == 88 && out.date_raw == Fixture::date,
             "preserve actual same-frame envelope") ||
      !Check(out.counties[0].landed_title_id == Fixture::county_a &&
             out.counties[1].landed_title_id == Fixture::county_b, "preserve full title generations") ||
      !Check(!out.counties[0].minor_present && out.counties[0].tiny_present &&
             out.counties[1].minor_present && !out.counties[1].tiny_present, "native false is known absence") ||
      !Check(q.getter_calls == 4, "actual two definitions queried per county")) return 1;
  Wire(directory, "two-counties.json", out);
  Put(q.context, 0x3C, std::int32_t{0}); q.minor[0] = true; q.tiny[0] = false;
  out = Read(b, Fixture::county_a, 89);
  if (!Check(out.available && out.requested_title_id == Fixture::county_a && out.counties.size() == 1 &&
             out.snapshot_revision == 89 && out.counties[0].minor_present && !out.counties[0].tiny_present,
             "explicit frozen county works after native list clearing")) return 2;
  Wire(directory, "explicit-title-after.json", out);
  q.tiny[1] = true; out = Read(b, Fixture::county_b, 89);
  if (!Check(out.available && out.requested_title_id == Fixture::county_b && out.counties.size() == 1 &&
             out.snapshot_revision == 89 && out.counties[0].minor_present && out.counties[0].tiny_present,
             "second frozen county has independent same-day later-revision wire")) return 17;
  Wire(directory, "explicit-title-b-after.json", out);
  q.minor[0] = false; out = Read(b, Fixture::county_a);
  if (!Check(out.available && !out.counties[0].minor_present && !out.counties[0].tiny_present,
             "both modifier values can legitimately be false")) return 3;
  Wire(directory, "both-absent.json", out);
  const auto calls_before_empty = q.getter_calls; q.database_fails = true; out = Read(b);
  if (!Check(out.available && out.counties.empty() && out.unavailable_reason.empty() &&
             q.getter_calls == calls_before_empty, "known empty list requires no modifier read")) return 4;
  Wire(directory, "empty-list.json", out); q.database_fails = false;
  Put(q.context, 0x3C, std::int32_t{1}); Put(q.row, 8, std::int32_t{7}); out = Read(b);
  if (!Check(out.available && out.counties.empty(), "absent list key is known empty")) return 5;
  Put(q.row, 8, std::int32_t{0}); q.context_fails = true; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "variable_list_unavailable", "native list read failure is not empty")) return 6;
  Wire(directory, "list-unavailable.json", out); q.context_fails = false;
  q.lookup_fails = true; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "modifier_definition_unavailable", "fallback definition is unavailable")) return 7;
  Wire(directory, "definition-unavailable.json", out); q.lookup_fails = false;
  q.getter_fails = true; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "county_modifier_unavailable" && out.counties.empty(),
             "getter return failure is not false presence")) return 8;
  Wire(directory, "presence-unavailable.json", out); q.getter_fails = false;
  q.getter_bad_byte = true; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "county_modifier_unavailable", "invalid returned presence is unavailable")) return 9;
  q.getter_bad_byte = false;
  Put(q.title_a, 0x10, std::int32_t{0x06000002}); out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "landed_title_unavailable", "same index is not same full title")) return 10;
  Put(q.title_a, 0x10, Fixture::county_a); Put(q.template_a, 0x64, std::int32_t{3}); out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "landed_title_unavailable", "only actual county tier accepted")) return 11;
  Put(q.template_a, 0x64, std::int32_t{2}); q.targets[0].kind = 4; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "variable_list_unavailable", "native title target kind required")) return 12;
  q.targets[0].kind = 5; q.frame_changes = true; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "state_changed", "material read binds one paused date")) return 13;
  q.frame_changes = false; Put(q.state, 8, Fixture::date); q.jomini[0x20] = std::byte{0}; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "played_character_or_paused_frame_unavailable",
             "owner query requires actual paused frame")) return 14;
  q.jomini[0x20] = std::byte{1};
  const auto native = r::BindImage(0x140000000, c::kExecutableSha256);
  if (!Check(native.enabled && native.core.enabled && native.identifiers.enabled &&
             reinterpret_cast<std::uintptr_t>(native.landed_title_store_slot) == 0x145D1DAF8 &&
             reinterpret_cast<std::uintptr_t>(native.county_modifier_getter) == 0x141AF5D40 &&
             reinterpret_cast<std::uintptr_t>(native.modifier_database) == 0x1408FD4E0 &&
             reinterpret_cast<std::uintptr_t>(native.modifier_lookup) == 0x140AB8D20,
             "actual exact-image source binding") ||
      !Check(!r::BindImage(0x140000000, "old").enabled &&
             !r::BindImage(0, c::kExecutableSha256).enabled, "version-bound source")) return 15;
  b.enabled = false; out = Read(b);
  if (!Check(!out.available && out.unavailable_reason == "exact_build_or_frame_unavailable", "disabled version is unavailable")) return 16;
  Wire(directory, "version-unavailable.json", out);
  std::cout << "PASS checks=" << checks << " actual_provider=true actual_serializer=true live=false\n";
  return 0;
}

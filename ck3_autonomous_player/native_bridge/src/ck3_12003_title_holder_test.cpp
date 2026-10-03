#include "xar_bridge/ck3_12003_title_holder.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/title_holder_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace {
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof value);
}

// These are synthetic component objects. Requested IDs 2128/2115 deliberately
// match the query use case; none of the holders below are live CK3 evidence.
struct Fixture {
  static constexpr std::int32_t actor_id = 29829;
  std::array<std::byte, 0x30> titles_storage{}, characters_storage{};
  std::vector<std::byte> titles_slots = std::vector<std::byte>(2400 * 0x10);
  std::vector<std::byte> characters_slots = std::vector<std::byte>(60000 * 0x10);
  std::map<std::int32_t, std::array<std::byte, 0x140>> titles;
  std::map<std::int32_t, std::array<std::byte, 0x70>> definitions;
  std::map<std::int32_t, std::array<std::byte, 0x30>> characters;
  std::map<void *, void *> lieges;
  std::map<void *, void *> tops;
  void *titles_pointer = titles_storage.data();
  void *characters_pointer = characters_storage.data();
  void *fallback = nullptr;
  xar::ck3_12003::TitleHolderBindingsV1 bindings{};
  xar::game::Snapshot snapshot{};
  static Fixture *active;

  static void *Immediate(void *character) {
    const auto found = active->lieges.find(character);
    return found != active->lieges.end() ? found->second : nullptr;
  }
  static void *Top(void *character) {
    const auto found = active->tops.find(character);
    return found != active->tops.end() ? found->second : nullptr;
  }
  void *Character(std::int32_t id) {
    auto &bytes = characters[id];
    Put(bytes.data(), 0x18, id);
    Put(bytes.data(), 0x1C, std::uint32_t{0x43686172});
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    Put(characters_slots.data(), static_cast<std::size_t>(index) * 0x10 + 8,
        static_cast<void *>(bytes.data()));
    return bytes.data();
  }
  void Title(std::int32_t id, std::int32_t holder) {
    auto &bytes = titles[id];
    auto &definition = definitions[id];
    Put(bytes.data(), 0x10, id);
    Put(bytes.data(), 0x48, static_cast<void *>(definition.data()));
    Put(bytes.data(), 0x128, holder);
    Put(definition.data(), 0x64, std::int32_t{2});
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    Put(titles_slots.data(), static_cast<std::size_t>(index) * 0x10 + 8,
        static_cast<void *>(bytes.data()));
  }
  Fixture() {
    active = this;
    Put(titles_storage.data(), 0x20, static_cast<void *>(titles_slots.data()));
    Put(titles_storage.data(), 0x2C, std::int32_t{2400});
    Put(characters_storage.data(), 0x20, static_cast<void *>(characters_slots.data()));
    Put(characters_storage.data(), 0x2C, std::int32_t{60000});
    void *actor = Character(actor_id);
    void *king = Character(29097);
    void *vassal = Character(34333);
    void *middle = Character(34334);
    void *sibling = Character(56513);
    void *foreign = Character(32750);
    lieges = {{actor, king}, {king, nullptr}, {vassal, middle},
              {middle, actor}, {sibling, king}, {foreign, foreign}};
    tops = {{actor, king}, {king, king}, {vassal, king},
            {middle, king}, {sibling, king}, {foreign, foreign}};
    Title(2128, 34333);
    Title(2115, actor_id);
    Title(2200, -1);
    Title(2250, 56513);
    Title(2260, 32750);
    bindings.enabled = true;
    bindings.provinces.enabled = true;
    bindings.provinces.landed_title_storage_slot = &titles_pointer;
    bindings.character_storage_slot = &characters_pointer;
    bindings.character_fallback_slot = &fallback;
    bindings.immediate_liege = &Immediate;
    bindings.top_liege = &Top;
    snapshot.paused = true;
    snapshot.map_ready = true;
    snapshot.has_played_character = true;
    snapshot.played_character_alive = true;
    snapshot.played_character_id = actor_id;
    snapshot.date_raw = 53236632;
  }
};
Fixture *Fixture::active = nullptr;

int checks = 0;
int cases = 0;
std::uint64_t sequence = 0;
bool Require(bool condition, const char *message) {
  ++checks;
  if (!condition) std::cerr << "FAIL: " << message << '\n';
  return condition;
}

bool Case(Fixture &fixture, const std::filesystem::path &wire_directory,
          const char *name, std::int32_t title_id, bool available,
          std::initializer_list<std::string_view> expected) {
  xar::game::TitleHolderV1 observation{};
  const auto result = xar::ck3_12003::ReadTitleHolderV1(
      fixture.bindings, fixture.snapshot, title_id, observation);
  if (!Require(result == (available ? xar::game::ReadTitleHolderV1Result::available
                                   : xar::game::ReadTitleHolderV1Result::unavailable),
               "production reader availability") ||
      !Require(observation.title_id == title_id &&
                   observation.actor_character_id == Fixture::actor_id &&
                   observation.date_raw == fixture.snapshot.date_raw,
               "production request and paused frame identity")) return false;
  const auto step = "query-title-holder-v1-" + std::to_string(title_id);
  const auto native_result = xar::game::SerializeTitleHolderV1(
      observation, result, ++sequence, 40, step);
  if (!Require(!native_result.empty(), "production serializer completed"))
    return false;
  for (const auto text : expected) {
    if (!Require(native_result.find(text) != std::string::npos,
                 "production serializer expected field")) return false;
  }
  const auto wire = "{\"type\":\"command_result\",\"protocol_version\":1,"
                    "\"request_id\":\"synthetic-title-holder-" +
                    std::to_string(sequence) + "\",\"ok\":true,\"result\":" +
                    native_result + '}';
  std::ofstream output(wire_directory / (std::string(name) + ".json"),
                       std::ios::binary);
  output << wire << '\n';
  if (!Require(static_cast<bool>(output), "actual production wire file"))
    return false;
  ++cases;
  return true;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) { std::cerr << "Expected output wire directory\n"; return 2; }
  const std::filesystem::path wire(argv[1]);
  std::filesystem::create_directories(wire);
  Fixture fixture;
  if (!Case(fixture, wire, "county-vassal-2128", 2128, true,
            {"\"holder_character_id\":34333", "\"holder_is_player\":false",
             "\"holder_in_player_realm\":true",
             "\"holder_immediate_liege_character_id\":34334",
             "\"holder_top_liege_character_id\":29097"}) ||
      !Case(fixture, wire, "county-player-2115", 2115, true,
            {"\"holder_character_id\":29829", "\"holder_is_player\":true",
             "\"holder_in_player_realm\":true"}) ||
      !Case(fixture, wire, "unheld", 2200, true,
            {"\"holder_character_id\":null", "\"holder_is_player\":false",
             "\"holder_in_player_realm\":false",
             "\"holder_immediate_liege_character_id\":null",
             "\"holder_top_liege_character_id\":null"}) ||
      !Case(fixture, wire, "sibling-same-top-outside", 2250, true,
            {"\"holder_character_id\":56513", "\"holder_is_player\":false",
             "\"holder_in_player_realm\":false",
             "\"holder_top_liege_character_id\":29097"}) ||
      !Case(fixture, wire, "foreign-realm", 2260, true,
            {"\"holder_character_id\":32750", "\"holder_in_player_realm\":false",
             "\"holder_immediate_liege_character_id\":null",
             "\"holder_top_liege_character_id\":32750"}) ||
      !Case(fixture, wire, "missing-title", 2300, false,
            {"\"unavailable_reason\":\"title_generation_unavailable\"",
             "\"holder_character_id\":null", "\"holder_in_player_realm\":null"}) ||
      !Case(fixture, wire, "title-generation-mismatch", 0x01000850, false,
            {"\"unavailable_reason\":\"title_generation_unavailable\""})) return 1;
  // Same slot, wrong generation in the actual object resolves unavailable.
  Put(fixture.characters[34333].data(), 0x18, std::int32_t{0x0100861D});
  if (!Case(fixture, wire, "holder-generation-mismatch", 2128, false,
            {"\"unavailable_reason\":\"holder_generation_unavailable\"",
             "\"title_tier_raw\":null", "\"holder_character_id\":null"})) return 1;
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto binding = xar::ck3_12003::BindTitleHolderImageV1(
      base, xar::ck3_12003::kExecutableSha256);
  if (!Require(binding.enabled && binding.provinces.enabled &&
                   reinterpret_cast<std::uintptr_t>(binding.immediate_liege) ==
                       base + 0x28BFC70 &&
                   reinterpret_cast<std::uintptr_t>(binding.top_liege) ==
                       base + 0x28BFDA0,
               "exact .3 native liege bindings") ||
      !Require(!xar::ck3_12003::BindTitleHolderImageV1(base, "old-build").enabled,
               "exact .3 binding identity")) return 1;
  std::cout << "PASS checks=" << checks << " cases=" << cases
            << " synthetic native memory; production reader and serializer; no CK3 access\n";
  return 0;
}

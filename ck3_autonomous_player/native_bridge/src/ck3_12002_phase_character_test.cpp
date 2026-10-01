#include "xar_bridge/ck3_12002_phase_character.hpp"

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/combat_v3.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>

namespace {
using namespace xar::ck3_12002::phase_character;

template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

std::int32_t human_calls = 0;
bool IsHuman(std::int32_t id) {
  ++human_calls;
  return id == 0x0100002A;
}
void *present_trait = nullptr;
std::vector<void *> present_traits;
bool HasTrait(void *, const void *trait) {
  return trait == present_trait ||
         std::find(present_traits.begin(), present_traits.end(), trait) !=
             present_traits.end();
}
void *trait_database = nullptr;
void *GetDatabase() { return trait_database; }
std::array<std::int64_t, 3> xp{1234567, 0, 987654321};
std::int32_t xp_count = 3;
bool return_wrong_span = false;
bool return_null_data = false;
void *ReadTracks(void *, void *output, const void *) {
  auto &span = *static_cast<NativeTraitXpSpan *>(output);
  span.data = return_null_data ? nullptr : xp.data();
  span.count = xp_count;
  span.reserved = -123456789;  // The native ABI does not store count here.
  return return_wrong_span ? nullptr : output;
}
std::int32_t TrackIndex(const void *, const std::string *key) {
  if (*key == "bow" || *key == "fragile_bones") return 0;
  if (*key == "foot") return 1;
  if (*key == "horse") return 2;
  if (*key == "out_of_range") return 3;
  return -1;
}

bool Check(bool condition, const char *label) {
  if (!condition) std::cerr << label << '\n';
  return condition;
}

bool TestIdentityAndKnightLink() {
  Bindings bindings;
  bindings.enabled = true;
  bindings.is_human_player_character = &IsHuman;
  std::array<std::byte, 0x210> character{};
  const auto id = 0x0100002A;
  Put(character, 0x18, id);
  Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(character, 0xD8, std::int32_t{99});  // New diplomacy, old martial.
  Put(character, 0xDC, std::int32_t{17});
  Put(character, 0xE8, std::int32_t{23});  // New learning, old prowess.
  Put(character, 0xEC, std::int32_t{41});
  Put(character, 0xF0, std::int32_t{-777}); // Incorrect blanket +8 migration.
  Put(character, 0x1C8, static_cast<const void *>(&bindings)); // Old death.
  Identity output;
  if (!Check(ReadIdentity(bindings, character.data(), id, output) &&
                 output.alive && !output.is_ai && output.martial == 17 &&
                 output.learning == 23 && output.prowess == 41 &&
                 human_calls == 1,
             "effective skills and death layout")) return false;
  Put(character, 0x1D0, static_cast<const void *>(&bindings));
  if (!Check(ReadIdentity(bindings, character.data(), id, output) &&
                 !output.alive && output.is_ai && human_calls == 1,
             "dead character is not an active human")) return false;
  if (!Check(!ReadIdentity(bindings, character.data(), id + 0x01000000, output),
             "full generation must match")) return false;
  Put(character, 0x1C, std::uint32_t{0});
  if (!Check(!ReadIdentity(bindings, character.data(), id, output),
             "native Character kind must match")) return false;
  Put(character, 0x1C, std::uint32_t{0x43686172});
  std::int32_t regiment_id = 0;
  std::array<std::byte, 0x100> link{};
  Put(link, 0xF8, std::int32_t{0x02000012});
  Put(character, 0x1B0, static_cast<const void *>(link.data()));
  if (!Check(ReadKnightRegimentId(character.data(), id, regiment_id) &&
                 regiment_id == -1, "old knight link offset is ignored"))
    return false;
  Put(character, 0x1B8, static_cast<const void *>(link.data()));
  if (!Check(ReadKnightRegimentId(character.data(), id, regiment_id) &&
                 regiment_id == 0x02000012, "native knight regiment link"))
    return false;
  Put(link, 0xF8, std::int32_t{-2});
  return Check(!ReadKnightRegimentId(character.data(), id, regiment_id),
               "invalid negative RegimentID is unavailable");
}

template <std::size_t N>
void SetKey(std::array<std::byte, N> &definition, std::string_view key) {
  if (key.size() < 0x10) {
    std::memcpy(definition.data() + 0x18, key.data(), key.size());
    Put(definition, 0x30, std::uint64_t{15});
  } else {
    Put(definition, 0x18, key.data());
    Put(definition, 0x30, std::uint64_t{key.size()});
  }
  Put(definition, 0x28, std::uint64_t{key.size()});
}

bool TestDefinitionsAndPresence() {
  std::array<std::byte, 0x2A0> short_trait{}, long_trait{}, duplicate{};
  SetKey(short_trait, "wounded_1");
  SetKey(long_trait, "lifestyle_blademaster");
  SetKey(duplicate, "wounded_1");
  std::array<void *, 3> rows{short_trait.data(), long_trait.data(),
                            duplicate.data()};
  std::array<std::byte, 0x80> database{};
  Put(database, 0x50, rows.data());
  Put(database, 0x5C, std::int32_t{2});
  Put(database, 0x68, static_cast<void **>(nullptr));
  Put(database, 0x74, std::int32_t{-99});
  if (!Check(FindUniqueTraitDefinition(database.data(), "wounded_1") ==
                 short_trait.data() &&
                 FindUniqueTraitDefinition(database.data(),
                                           "lifestyle_blademaster") ==
                     long_trait.data() &&
                 FindUniqueTraitDefinition(database.data(), "missing") == nullptr,
             "new database definition array and both native string forms"))
    return false;
  Put(database, 0x5C, std::int32_t{3});
  if (!Check(FindUniqueTraitDefinition(database.data(), "wounded_1") == nullptr,
             "duplicate definition key is unavailable")) return false;
  Bindings bindings;
  bindings.enabled = true;
  bindings.character_has_trait = &HasTrait;
  present_trait = long_trait.data();
  bool present = false;
  std::array<void *, 2> group{short_trait.data(), long_trait.data()};
  if (!Check(ReadTraitPresence(bindings, &database, group, present) && present,
             "group is the union of concrete trait predicates")) return false;
  present_trait = nullptr;
  if (!Check(ReadTraitPresence(bindings, &database, group, present) && !present,
             "valid absent trait group")) return false;
  group[1] = nullptr;
  return Check(!ReadTraitPresence(bindings, &database, group, present),
               "unresolved trait definition is not absence");
}

bool TestTraitXp() {
  Bindings bindings;
  bindings.enabled = true;
  bindings.character_trait_tracks = &ReadTracks;
  bindings.trait_track_index = &TrackIndex;
  std::array<std::byte, 0x2A0> definition{};
  Put(definition, 0x294, std::int32_t{-777});
  Put(definition, 0x29C, std::int32_t{3});
  std::int64_t output = 0;
  if (!Check(ReadTraitTrackXp(bindings, &bindings, definition.data(), "horse",
                              output) && output == xp[2],
             "XP count is +8 even when +C is poisoned")) return false;
  if (!Check(ReadTraitTrackXp(bindings, &bindings, definition.data(), "foot",
                              output) && output == 0,
             "zero XP is a valid fixed-point value")) return false;
  if (!Check(!ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output) &&
                 !ReadTraitTrackXp(bindings, &bindings, definition.data(),
                                   "missing", output) &&
                 !ReadTraitTrackXp(bindings, &bindings, definition.data(),
                                   "out_of_range", output),
             "track identity and range checks")) return false;
  Put(definition, 0x29C, std::int32_t{1});
  if (!Check(ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output) &&
                 output == xp[0], "single implicit track definition +29C"))
    return false;
  xp_count = 0;
  return_null_data = true;
  if (!Check(ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output) &&
                 output == 0, "native empty XP span")) return false;
  xp_count = 3;
  if (!Check(!ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output),
             "nonempty XP span requires data")) return false;
  return_null_data = false;
  return_wrong_span = true;
  if (!Check(!ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output),
             "native return must identify caller-owned span")) return false;
  return_wrong_span = false;
  xp_count = -1;
  return Check(!ReadTraitTrackXp(bindings, &bindings, definition.data(), "", output),
               "negative XP span is unavailable");
}

bool TestFullIdentityTraits() {
  Bindings bindings;
  bindings.enabled = true;
  bindings.is_human_player_character = &IsHuman;
  bindings.get_trait_database = &GetDatabase;
  bindings.character_has_trait = &HasTrait;
  bindings.character_trait_tracks = &ReadTracks;
  bindings.trait_track_index = &TrackIndex;
  std::array<std::byte, 0x210> character{};
  Put(character, 0x18, std::int32_t{0x0100002A});
  Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(character, 0xDC, std::int32_t{31});
  Put(character, 0xE8, std::int32_t{22});
  Put(character, 0xEC, std::int32_t{54});
  std::vector<std::string_view> keys;
  for (const auto key : TraitOrGroupKeys()) {
    if (key == "physique_good") {
      keys.insert(keys.end(), {"physique_good_1", "physique_good_2",
                               "physique_good_3"});
    } else keys.push_back(key == "scholar" ? "erudite" : key);
  }
  std::array<std::array<std::byte, 0x2A0>, 58> definitions{};
  std::array<void *, 58> rows{};
  if (!Check(keys.size() == definitions.size(), "56 groups have 58 definitions"))
    return false;
  present_traits.clear();
  void *second_wound = nullptr;
  for (std::size_t index = 0; index < keys.size(); ++index) {
    SetKey(definitions[index], keys[index]);
    Put(definitions[index], 0x29C,
         std::int32_t{keys[index] == "tourney_participant" ? 3 : 1});
    rows[index] = definitions[index].data();
    if (keys[index] == "wounded_2" || keys[index] == "fragile_bones" ||
        keys[index] == "physique_good_3" || keys[index] == "erudite")
      present_traits.push_back(rows[index]);
    if (keys[index] == "wounded_1") second_wound = rows[index];
  }
  std::array<std::byte, 0x80> database{};
  Put(database, 0x50, rows.data());
  Put(database, 0x5C, std::int32_t{58});
  trait_database = database.data();
  present_trait = nullptr;
  xp_count = 3;
  return_null_data = false;
  return_wrong_span = false;
  xar::game::CombatPhaseCharacterV3 output;
  output.character_id = 0x0100002A;
  output.source_army_id = 456;
  if (!Check(ReadPhaseCharacterIdentityTraits(bindings, character.data(), output) &&
                 output.source_army_id == 456 && output.martial == 31 &&
                 output.learning == 22 && output.prowess == 54 &&
                 output.traits_or_groups.size() == 56 &&
                 output.wounded_rank_raw == 200000 &&
                 output.fragile_bones_rank_raw == 100000 &&
                 output.fragile_bones_xp_raw == xp[0] &&
                 output.lifestyle_blademaster_xp_raw == xp[0] &&
                 output.tourney_bow_xp_raw == xp[0] &&
                 output.tourney_foot_xp_raw == 0 &&
                 output.tourney_horse_xp_raw == xp[2],
             "complete 56-key identity/traits/rank/five-XP DTO leaf")) return false;
  const auto physique = std::find_if(output.traits_or_groups.begin(),
                                    output.traits_or_groups.end(),
                                    [](const auto &row) {
                                      return row.key == "physique_good";
                                    });
  if (!Check(physique != output.traits_or_groups.end() && physique->value,
             "physique child resolves to group membership")) return false;
  const auto scholar = std::find_if(output.traits_or_groups.begin(),
                                   output.traits_or_groups.end(),
                                   [](const auto &row) {
                                     return row.key == "scholar";
                                   });
  if (!Check(scholar != output.traits_or_groups.end() && scholar->value,
             "new erudite definition supplies stable scholar operand"))
    return false;
  present_traits.push_back(second_wound);
  if (!Check(!ReadPhaseCharacterIdentityTraits(bindings, character.data(), output),
             "contradictory wounded ranks reject full leaf")) return false;
  present_traits.pop_back();
  Put(database, 0x5C, std::int32_t{57});
  if (!Check(!ReadPhaseCharacterIdentityTraits(bindings, character.data(), output),
             "missing stable trait definition rejects full leaf")) return false;
  Put(database, 0x5C, std::int32_t{58});
  xp_count = 0;
  return_null_data = true;
  return Check(ReadPhaseCharacterIdentityTraits(bindings, character.data(), output) &&
                   output.fragile_bones_xp_raw == 0 &&
                   output.lifestyle_blademaster_xp_raw == 0 &&
                   output.tourney_horse_xp_raw == 0,
               "five native empty XP spans remain valid zero values");
}
}  // namespace

int main() {
  const auto bound = BindImage(0x140000000,
                               xar::ck3_12002::kExecutableSha256);
  if (!Check(bound.enabled &&
                 reinterpret_cast<std::uintptr_t>(bound.character_has_trait) ==
                     0x1428BB1F0 &&
                 !BindImage(0x140000000, "wrong-build").enabled &&
                 !BindImage(0, xar::ck3_12002::kExecutableSha256).enabled,
             "exact-build function binding") ||
      !TestIdentityAndKnightLink() || !TestDefinitionsAndPresence() ||
      !TestTraitXp() || !TestFullIdentityTraits()) return 1;
  std::cout << "CK3 1.20.0.2 phase character offline fixtures passed\n";
  return 0;
}

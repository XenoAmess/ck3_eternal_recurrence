#include "xar_bridge/ck3_12002_phase_character.hpp"

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/combat_v3.hpp"

#include <algorithm>
#include <array>
#include <cstring>

namespace xar::ck3_12002::phase_character {
namespace {

constexpr std::array<std::string_view, 56> kTraitOrGroupKeys{
    "ambitious", "athletic", "berserker", "brave", "calm",
    "cautious_leader", "compassionate", "content", "craven",
    "desert_warrior", "disfigured", "education_martial_1",
    "education_martial_2", "education_martial_3", "education_martial_4",
    "education_martial_5", "education_martial_prowess_1",
    "education_martial_prowess_2", "education_martial_prowess_3",
    "education_martial_prowess_4", "flexible_leader", "forest_fighter",
    "giant", "holy_warrior", "impatient", "incapable", "intellect_good_1",
    "intellect_good_2", "intellect_good_3", "jungle_stalker", "lazy",
    "lifestyle_blademaster", "maimed", "nomadic_philosophy", "one_eyed",
    "one_legged", "open_terrain_expert", "patient", "physique_good",
    "reckless", "rough_terrain_expert", "sadistic", "scholar",
    "shieldmaiden", "shrewd", "strong", "temperate", "winter_soldier",
    "wrathful", "zealous", "aggressive_attacker", "wounded_1", "wounded_2",
    "wounded_3", "fragile_bones", "tourney_participant"};
constexpr std::array<std::string_view, 3> kPhysiqueGoodKeys{
    "physique_good_1", "physique_good_2", "physique_good_3"};

template <typename T>
T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

bool CharacterMatches(const void *character, std::int32_t expected_id) noexcept {
  return character != nullptr && expected_id >= 0 &&
         LoadAt<std::int32_t>(character, kCharacterIdentityOffset) ==
             expected_id &&
         LoadAt<std::uint32_t>(character, kCharacterKindOffset) == 0x43686172;
}

bool TraitKeyEquals(const void *definition, std::string_view key) noexcept {
  if (definition == nullptr || key.empty() || key.size() > 1024) {
    return false;
  }
  const auto *native_string = static_cast<const std::byte *>(definition) + 0x18;
  const auto size = LoadAt<std::uint64_t>(native_string, 0x10);
  const auto capacity = LoadAt<std::uint64_t>(native_string, 0x18);
  if (size != key.size() || size > capacity) {
    return false;
  }
  const auto *data = capacity < 0x10
                         ? reinterpret_cast<const char *>(native_string)
                         : LoadAt<const char *>(native_string, 0);
  return data != nullptr && std::memcmp(data, key.data(), key.size()) == 0;
}

}  // namespace

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept {
  Bindings output;
  if (image_base == 0 || executable_sha256 != ck3_12002::kExecutableSha256) {
    return output;
  }
  output.enabled = true;
  output.get_trait_database =
      reinterpret_cast<GetTraitDatabase>(image_base + kTraitDatabaseRva);
  output.character_has_trait =
      reinterpret_cast<CharacterHasTrait>(image_base + kCharacterHasTraitRva);
  output.character_trait_tracks = reinterpret_cast<CharacterTraitTracks>(
      image_base + kCharacterTraitTracksRva);
  output.trait_track_index =
      reinterpret_cast<TraitTrackIndex>(image_base + kTraitTrackIndexRva);
  output.is_human_player_character = reinterpret_cast<IsHumanPlayerCharacter>(
      image_base + kIsHumanPlayerCharacterRva);
  output.knight_context =
      reinterpret_cast<KnightContext>(image_base + kKnightContextRva);
  return output;
}

bool ReadIdentity(const Bindings &bindings, const void *character,
                  std::int32_t expected_character_id,
                  Identity &output) noexcept {
  output = {};
  if (!bindings.enabled || bindings.is_human_player_character == nullptr ||
      !CharacterMatches(character, expected_character_id)) {
    return false;
  }
  output.character_id = expected_character_id;
  output.alive = LoadAt<const void *>(character, kCharacterDeathDataOffset) ==
                 nullptr;
  output.is_ai = !output.alive ||
                 !bindings.is_human_player_character(expected_character_id);
  output.martial = LoadAt<std::int32_t>(character, kCharacterMartialOffset);
  output.learning = LoadAt<std::int32_t>(character, kCharacterLearningOffset);
  output.prowess = LoadAt<std::int32_t>(character, kCharacterProwessOffset);
  return true;
}

bool ReadKnightRegimentId(const void *character,
                         std::int32_t expected_character_id,
                         std::int32_t &output) noexcept {
  output = -1;
  if (!CharacterMatches(character, expected_character_id)) {
    return false;
  }
  const auto *link =
      LoadAt<const void *>(character, kCharacterKnightLinkOffset);
  if (link == nullptr) {
    return true;
  }
  output = LoadAt<std::int32_t>(link, kKnightLinkRegimentIdOffset);
  return output >= -1;
}

void *FindUniqueTraitDefinition(const void *database,
                                std::string_view key) noexcept {
  if (database == nullptr || key.empty()) {
    return nullptr;
  }
  auto *const data =
      LoadAt<void *const *>(database, kTraitDatabaseObjectsOffset);
  const auto count =
      LoadAt<std::int32_t>(database, kTraitDatabaseCountOffset);
  if (count < 0 || count > 1000000 || (count > 0 && data == nullptr)) {
    return nullptr;
  }
  void *match = nullptr;
  for (std::int32_t index = 0; index < count; ++index) {
    void *const object = data[index];
    if (TraitKeyEquals(object, key)) {
      if (match != nullptr) {
        return nullptr;
      }
      match = object;
    }
  }
  return match;
}

bool ReadTraitPresence(const Bindings &bindings, void *character,
                       std::span<void *const> concrete_traits,
                       bool &output) noexcept {
  output = false;
  if (!bindings.enabled || bindings.character_has_trait == nullptr ||
      character == nullptr || concrete_traits.empty() ||
      std::any_of(concrete_traits.begin(), concrete_traits.end(),
                  [](const auto *trait) { return trait == nullptr; })) {
    return false;
  }
  output = std::any_of(concrete_traits.begin(), concrete_traits.end(),
                       [&](const auto *trait) {
                         return bindings.character_has_trait(character, trait);
                       });
  return true;
}

bool ReadTraitTrackXp(const Bindings &bindings, void *character,
                      const void *trait_definition, std::string_view track_key,
                      std::int64_t &output) noexcept {
  output = 0;
  if (!bindings.enabled || bindings.character_trait_tracks == nullptr ||
      bindings.trait_track_index == nullptr || character == nullptr ||
      trait_definition == nullptr) {
    return false;
  }
  NativeTraitXpSpan span;
  if (bindings.character_trait_tracks(character, &span, trait_definition) !=
          &span ||
      span.count < 0 || span.count > 1024 ||
      (span.count > 0 && span.data == nullptr)) {
    return false;
  }
  if (span.count == 0) {
    return true;
  }
  std::int32_t index = 0;
  if (track_key.empty()) {
    if (LoadAt<std::int32_t>(trait_definition,
                             kTraitTrackDefinitionCountOffset) != 1) {
      return false;
    }
  } else {
    const std::string native_key(track_key);
    index = bindings.trait_track_index(trait_definition, &native_key);
  }
  if (index < 0 || index >= span.count) {
    return false;
  }
  output = span.data[index];
  return true;
}

std::span<const std::string_view> TraitOrGroupKeys() noexcept {
  return kTraitOrGroupKeys;
}

bool ReadPhaseCharacterIdentityTraits(
    const Bindings &bindings, void *character,
    game::CombatPhaseCharacterV3 &output) noexcept {
  Identity identity;
  if (!ReadIdentity(bindings, character, output.character_id, identity) ||
      bindings.get_trait_database == nullptr) {
    return false;
  }
  const auto *database = bindings.get_trait_database();
  if (database == nullptr) return false;
  std::vector<game::NamedBoolV3> presence;
  presence.reserve(kTraitOrGroupKeys.size());
  const void *fragile = nullptr;
  const void *blademaster = nullptr;
  const void *tourney = nullptr;
  std::int32_t wounded_rank = 0;
  bool fragile_present = false;
  for (const auto key : kTraitOrGroupKeys) {
    std::array<void *, 3> concrete{};
    std::size_t count = 1;
    if (key == "physique_good") {
      count = kPhysiqueGoodKeys.size();
      for (std::size_t index = 0; index < count; ++index)
        concrete[index] = FindUniqueTraitDefinition(database,
                                                    kPhysiqueGoodKeys[index]);
    } else {
      // 1.20 trait_conversion.lookup explicitly renames scholar to erudite.
      // Keep the established wire operand key while reading the new definition.
      concrete[0] = FindUniqueTraitDefinition(database,
                                              key == "scholar" ? "erudite" : key);
    }
    bool present = false;
    if (!ReadTraitPresence(bindings, character,
                            std::span<void *const>(concrete.data(), count),
                            present)) return false;
    presence.push_back({std::string(key), present});
    if (key == "wounded_1" || key == "wounded_2" || key == "wounded_3") {
      if (present) {
        if (wounded_rank != 0) return false;
        wounded_rank = key.back() - '0';
      }
    } else if (key == "fragile_bones") {
      fragile = concrete[0];
      fragile_present = present;
    } else if (key == "lifestyle_blademaster") {
      blademaster = concrete[0];
    } else if (key == "tourney_participant") {
      tourney = concrete[0];
    }
  }
  std::int64_t fragile_xp = 0, blademaster_xp = 0;
  std::int64_t bow_xp = 0, foot_xp = 0, horse_xp = 0;
  if (!ReadTraitTrackXp(bindings, character, fragile, "fragile_bones", fragile_xp) ||
      !ReadTraitTrackXp(bindings, character, blademaster, "", blademaster_xp) ||
      !ReadTraitTrackXp(bindings, character, tourney, "bow", bow_xp) ||
      !ReadTraitTrackXp(bindings, character, tourney, "foot", foot_xp) ||
      !ReadTraitTrackXp(bindings, character, tourney, "horse", horse_xp))
    return false;
  output.alive = identity.alive;
  output.is_ai = identity.is_ai;
  output.martial = identity.martial;
  output.learning = identity.learning;
  output.prowess = identity.prowess;
  output.traits_or_groups = std::move(presence);
  output.wounded_rank_raw = static_cast<std::int64_t>(wounded_rank) * 100000;
  output.fragile_bones_rank_raw = fragile_present ? 100000 : 0;
  output.fragile_bones_xp_raw = fragile_xp;
  output.lifestyle_blademaster_xp_raw = blademaster_xp;
  output.tourney_bow_xp_raw = bow_xp;
  output.tourney_foot_xp_raw = foot_xp;
  output.tourney_horse_xp_raw = horse_xp;
  return true;
}

}  // namespace xar::ck3_12002::phase_character

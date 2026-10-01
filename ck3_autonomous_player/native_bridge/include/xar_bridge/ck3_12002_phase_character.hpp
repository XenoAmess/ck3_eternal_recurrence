#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>

namespace xar::game {
struct CombatPhaseCharacterV3;
}

namespace xar::ck3_12002::phase_character {

inline constexpr std::uintptr_t kTraitDatabaseRva = 0x89E5B0;
inline constexpr std::uintptr_t kTraitDatabaseSlotRva = 0x5C67528;
inline constexpr std::uintptr_t kCharacterHasTraitRva = 0x28BB1F0;
inline constexpr std::uintptr_t kCharacterTraitTracksRva = 0x28BB0F0;
inline constexpr std::uintptr_t kTraitTrackIndexRva = 0x30E5710;
inline constexpr std::uintptr_t kIsHumanPlayerCharacterRva = 0x2BAA710;
inline constexpr std::uintptr_t kKnightContextRva = 0x28BFC70;

inline constexpr std::size_t kTraitDatabaseObjectsOffset = 0x50;
inline constexpr std::size_t kTraitDatabaseCountOffset = 0x5C;
inline constexpr std::size_t kTraitTrackDefinitionCountOffset = 0x29C;
inline constexpr std::size_t kCharacterIdentityOffset = 0x18;
inline constexpr std::size_t kCharacterKindOffset = 0x1C;
inline constexpr std::size_t kCharacterDeathDataOffset = 0x1D0;
inline constexpr std::size_t kCharacterMartialOffset = 0xDC;
inline constexpr std::size_t kCharacterLearningOffset = 0xE8;
inline constexpr std::size_t kCharacterProwessOffset = 0xEC;
inline constexpr std::size_t kCharacterKnightLinkOffset = 0x1B8;
inline constexpr std::size_t kKnightLinkRegimentIdOffset = 0xF8;

struct NativeTraitXpSpan {
  const std::int64_t *data = nullptr;
  std::int32_t count = 0;
  std::int32_t reserved = 0;
};
static_assert(sizeof(NativeTraitXpSpan) == 0x10);
static_assert(offsetof(NativeTraitXpSpan, count) == 0x08);

using GetTraitDatabase = void *(*)();
using CharacterHasTrait = bool (*)(void *, const void *);
using CharacterTraitTracks = void *(*)(void *, void *, const void *);
using TraitTrackIndex = std::int32_t (*)(const void *, const std::string *);
using IsHumanPlayerCharacter = bool (*)(std::int32_t);
using KnightContext = void *(*)(void *);

struct Bindings {
  bool enabled = false;
  GetTraitDatabase get_trait_database = nullptr;
  CharacterHasTrait character_has_trait = nullptr;
  CharacterTraitTracks character_trait_tracks = nullptr;
  TraitTrackIndex trait_track_index = nullptr;
  IsHumanPlayerCharacter is_human_player_character = nullptr;
  KnightContext knight_context = nullptr;
};

struct Identity {
  std::int32_t character_id = -1;
  bool alive = false;
  bool is_ai = true;
  std::int32_t martial = 0;
  std::int32_t learning = 0;
  std::int32_t prowess = 0;
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

// All native calls belong on the game owning thread. The caller resolves and
// revalidates the full generation CharacterID before and after this leaf read.
bool ReadIdentity(const Bindings &bindings, const void *character,
                  std::int32_t expected_character_id, Identity &output) noexcept;
bool ReadKnightRegimentId(const void *character,
                         std::int32_t expected_character_id,
                         std::int32_t &output) noexcept;
void *FindUniqueTraitDefinition(const void *database,
                                std::string_view key) noexcept;
bool ReadTraitPresence(const Bindings &bindings, void *character,
                       std::span<void *const> concrete_traits,
                       bool &output) noexcept;
bool ReadTraitTrackXp(const Bindings &bindings, void *character,
                      const void *trait_definition, std::string_view track_key,
                      std::int64_t &output) noexcept;
std::span<const std::string_view> TraitOrGroupKeys() noexcept;
bool ReadPhaseCharacterIdentityTraits(
    const Bindings &bindings, void *character,
    game::CombatPhaseCharacterV3 &output) noexcept;

}  // namespace xar::ck3_12002::phase_character

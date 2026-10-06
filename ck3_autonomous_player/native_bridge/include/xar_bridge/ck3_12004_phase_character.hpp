#pragma once

#include "xar_bridge/ck3_12002_phase_character.hpp"

namespace xar::ck3_12004::phase_character {

// Actual .4 entries: activity/phase-character-native retained entry proof and
// complete track surface. These are not admission of the old image RVAs.
inline constexpr std::uintptr_t kTraitDatabaseRva = 0x89E5B0;
inline constexpr std::uintptr_t kTraitDatabaseSlotRva = 0x5C67528;
inline constexpr std::uintptr_t kCharacterHasTraitRva = 0x28BB1D0;
inline constexpr std::uintptr_t kCharacterTraitTracksRva = 0x28BB0D0;
inline constexpr std::uintptr_t kTraitTrackIndexRva = 0x30E56F0;
inline constexpr std::uintptr_t kIsHumanPlayerCharacterRva = 0x2BAA6F0;
inline constexpr std::uintptr_t kKnightContextRva = 0x28BFC50;

// Reuse the adopted caller-owned function table and trait/name/presence/XP
// reading policy. Actual image identity and entry selection belong here.
using Bindings = ck3_12002::phase_character::Bindings;

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

}  // namespace xar::ck3_12004::phase_character

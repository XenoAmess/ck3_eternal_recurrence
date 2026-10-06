#include "xar_bridge/ck3_12004_phase_character.hpp"

#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004::phase_character {

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept {
  Bindings output;
  if (image_base == 0 || executable_sha256 != ck3_12004::kExecutableSha256) {
    return output;
  }
  output.get_trait_database = reinterpret_cast<decltype(output.get_trait_database)>(
      image_base + kTraitDatabaseRva);
  output.character_has_trait = reinterpret_cast<decltype(output.character_has_trait)>(
      image_base + kCharacterHasTraitRva);
  output.character_trait_tracks =
      reinterpret_cast<decltype(output.character_trait_tracks)>(
          image_base + kCharacterTraitTracksRva);
  output.trait_track_index = reinterpret_cast<decltype(output.trait_track_index)>(
      image_base + kTraitTrackIndexRva);
  output.is_human_player_character =
      reinterpret_cast<decltype(output.is_human_player_character)>(
          image_base + kIsHumanPlayerCharacterRva);
  output.knight_context = reinterpret_cast<decltype(output.knight_context)>(
      image_base + kKnightContextRva);
  output.enabled = true;
  return output;
}

}  // namespace xar::ck3_12004::phase_character

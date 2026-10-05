#pragma once

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kOrdinaryInteractionQueryV1Step =
    "query-character-interaction-ordinary-v1";
inline constexpr std::string_view kOrdinaryInteractionQueryV1Capability =
    "game.query.character-interaction-ordinary.v1";
inline constexpr std::string_view kOrdinaryInteractionInitiateV1Step =
    "initiate-character-interaction-ordinary-v1";
inline constexpr std::string_view kOrdinaryInteractionInitiateV1Capability =
    "game.command.initiate-character-interaction-ordinary-v1";

struct OrdinaryInteractionRequestV1 {
  std::string interaction_key;
  // Preserve the generation-bearing unsigned Character ID. The native leaf
  // may bit-cast this ID to int32; it must never mask off its generation.
  std::uint32_t recipient_id = 0;
  std::uint64_t expected_revision = 0;
  std::int32_t expected_player_character_id = 0;
  std::uint32_t expected_game_pid = 0;
  std::uint64_t expected_connection_generation = 0;
};

bool OrdinaryInteractionRequestValidV1(
    const OrdinaryInteractionRequestV1 &request) noexcept;

// Accept only the closed ten-field execute_step wire object for the chosen
// step. Standard JSON whitespace is allowed; strings are unescaped ASCII.
// Every field is required, duplicate/extra fields and integer coercions are
// rejected, and output remains unchanged on failure.
bool ParseOrdinaryInteractionRequestV1(
    std::string_view json, bool initiate,
    OrdinaryInteractionRequestV1 &output) noexcept;

}  // namespace xar::ck3_12003

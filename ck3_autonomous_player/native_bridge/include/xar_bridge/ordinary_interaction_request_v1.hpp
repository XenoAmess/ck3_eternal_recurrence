#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

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
  // Education-only optional intent. Character IDs retain all generation bits.
  // The child/guardian pair is supplied together; the option list is independent.
  std::optional<std::uint32_t> child_full_id{};
  std::optional<std::uint32_t> guardian_full_id{};
  // Absent means unsupplied; an explicit empty list means all options off.
  // Repeated keys retain their caller order for the later native consumer.
  std::optional<std::vector<std::string>> requested_option_keys{};
};

bool OrdinaryInteractionRequestValidV1(
    const OrdinaryInteractionRequestV1 &request) noexcept;

// The existing ten execute_step fields remain required. Only the exact
// educate_child_interaction key accepts the optional child_full_id/guardian_full_id
// pair and the independently optional requested_option_keys array.
// Standard JSON whitespace and the existing unescaped ASCII key subset apply.
// Duplicate/unknown fields and integer coercions are rejected; duplicate option
// keys are retained, and output remains unchanged on failure.
bool ParseOrdinaryInteractionRequestV1(
    std::string_view json, bool initiate,
    OrdinaryInteractionRequestV1 &output) noexcept;

}  // namespace xar::ck3_12003

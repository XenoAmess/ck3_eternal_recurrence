#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

inline constexpr std::string_view kTitleHolderV1Capability =
    "game.command.query-title-holder-v1-N";

struct TitleHolderV1 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t title_id = -1;
  std::int32_t title_tier_raw = 0;
  std::string_view title_tier_key;
  // A missing holder is legal only when available=true and native holder=-1.
  // ID 0 remains a real full-generation component ID.
  std::optional<std::int32_t> holder_character_id;
  bool holder_is_player = false;
  bool holder_in_player_realm = false;
  std::optional<std::int32_t> holder_immediate_liege_character_id;
  std::optional<std::int32_t> holder_top_liege_character_id;
  // Additive key observation; key failure preserves base holder availability.
  std::string title_key;
  bool title_key_available = false;
  std::string_view title_key_unavailable_reason = "not_read";
};

enum class ReadTitleHolderV1Result { unavailable, available };

} // namespace xar::game

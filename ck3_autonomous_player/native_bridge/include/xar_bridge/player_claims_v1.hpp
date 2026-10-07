#pragma once

#include "xar_bridge/game_contract.hpp"
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace xar::game {
inline constexpr std::string_view kPlayerClaimsV1Capability =
    "game.command.query-player-claims-v1-IDS";
// Same finite ceiling as ReadWarTargetTitleIds; this is a request bound.
inline constexpr std::size_t kPlayerClaimsV1MaximumTitles = 4096;
struct PlayerClaimsV1 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::vector<std::int32_t> title_ids;
  std::vector<WarClaimSnapshot> claims;
};
enum class ReadPlayerClaimsV1Result { unavailable, available };
inline bool ValidPlayerClaimsTitleIdsV1(std::span<const std::int32_t> ids) noexcept {
  if (ids.empty() || ids.size() > kPlayerClaimsV1MaximumTitles) return false;
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (ids[i] < 0) return false;
    for (std::size_t prior = 0; prior < i; ++prior)
      if (ids[i] == ids[prior]) return false;
  }
  return true;
}
} // namespace xar::game

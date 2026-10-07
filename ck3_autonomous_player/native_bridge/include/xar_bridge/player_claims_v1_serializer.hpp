#pragma once
#include "xar_bridge/player_claims_v1.hpp"
#include <string>
#include <charconv>
#include <system_error>
#include <utility>

namespace xar::game {
inline constexpr std::string_view kPlayerClaimsV1StepPrefix = "query-player-claims-v1-";
inline bool ParsePlayerClaimsStepV1(std::string_view step,
                            std::vector<std::int32_t> &ids) noexcept {
  ids.clear();
  if (!step.starts_with(kPlayerClaimsV1StepPrefix)) return false;
  auto text = step.substr(kPlayerClaimsV1StepPrefix.size());
  try {
    std::vector<std::int32_t> parsed;
    while (!text.empty()) {
      const auto comma = text.find(',');
      const auto token = text.substr(0, comma);
      if (token.empty() || (token.size() > 1 && token.front() == '0')) return false;
      for (const char byte : token) if (byte < '0' || byte > '9') return false;
      std::int32_t id = -1;
      const auto result = std::from_chars(token.data(), token.data() + token.size(), id);
      if (result.ec != std::errc{} || result.ptr != token.data() + token.size() || id < 0)
        return false;
      parsed.push_back(id);
      if (parsed.size() > kPlayerClaimsV1MaximumTitles) return false;
      if (comma == std::string_view::npos) break;
      text.remove_prefix(comma + 1);
      if (text.empty()) return false;
    }
    if (!ValidPlayerClaimsTitleIdsV1(parsed)) return false;
    ids = std::move(parsed);
    return true;
  } catch (...) { return false; }
}

std::string SerializePlayerClaimsV1(const PlayerClaimsV1 &observation,
    ReadPlayerClaimsV1Result read_result, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision, std::string_view step);
} // namespace xar::game

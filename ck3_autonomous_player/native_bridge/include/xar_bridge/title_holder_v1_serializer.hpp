#pragma once

#include "xar_bridge/title_holder_v1.hpp"

#include <charconv>
#include <string>
#include <system_error>

namespace xar::game {

inline constexpr std::string_view kTitleHolderV1StepPrefix =
    "query-title-holder-v1-";

inline bool ParseTitleHolderStepV1(
    std::string_view step, std::int32_t &title_id) noexcept {
  title_id = -1;
  if (!step.starts_with(kTitleHolderV1StepPrefix)) return false;
  const auto literal = step.substr(kTitleHolderV1StepPrefix.size());
  if (literal.empty() || (literal.size() > 1 && literal.front() == '0'))
    return false;
  for (const char byte : literal) {
    if (byte < '0' || byte > '9') return false;
  }
  std::int32_t parsed = -1;
  const auto result = std::from_chars(
      literal.data(), literal.data() + literal.size(), parsed);
  if (result.ec != std::errc{} ||
      result.ptr != literal.data() + literal.size() || parsed < 0) return false;
  title_id = parsed;
  return true;
}

// snapshot_revision is the bridge's native admission revision, never a public
// MCP revision. The existing command-result wrapper supplies request_id.
std::string SerializeTitleHolderV1(
    const TitleHolderV1 &observation, ReadTitleHolderV1Result read_result,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::string_view step);

} // namespace xar::game

#pragma once

#include "xar_bridge/war_occupation_targets_v1.hpp"

#include <charconv>
#include <string>
#include <system_error>

namespace xar::game {

inline constexpr std::string_view kWarOccupationTargetsV1StepPrefix =
    "query-war-occupation-targets-v1-";

inline bool ParseWarOccupationTargetsStepV1(
    std::string_view step, std::int32_t &war_id) noexcept {
  war_id = -1;
  if (!step.starts_with(kWarOccupationTargetsV1StepPrefix)) return false;
  const auto literal = step.substr(kWarOccupationTargetsV1StepPrefix.size());
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
  war_id = parsed;
  return true;
}

// snapshot_revision is the bridge's native admission revision. Public MCP
// revisions are translated by the driver and are never written into this DTO.
std::string SerializeWarOccupationTargetsV1(
    const WarOccupationTargetsV1 &observation,
    ReadWarOccupationTargetsV1Result read_result, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision, std::string_view step);

} // namespace xar::game

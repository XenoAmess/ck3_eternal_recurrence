#pragma once

#include "xar_bridge/title_own_laws_v1.hpp"
#include <charconv>
#include <system_error>

namespace xar::game {
inline constexpr std::string_view kTitleOwnLawsV1StepPrefix =
    "query-title-own-laws-v1-";

inline bool ParseTitleOwnLawsStepV1(std::string_view step,
                                  std::uint32_t &title_id) noexcept {
  title_id = UINT32_MAX;
  if (!step.starts_with(kTitleOwnLawsV1StepPrefix)) return false;
  const auto digits = step.substr(kTitleOwnLawsV1StepPrefix.size());
  if (digits.empty() || (digits.size() > 1 && digits.front() == '0')) return false;
  for (const char digit : digits) if (digit < '0' || digit > '9') return false;
  std::uint32_t value = UINT32_MAX;
  const auto result = std::from_chars(digits.data(), digits.data() + digits.size(), value);
  if (result.ec != std::errc{} || result.ptr != digits.data() + digits.size() ||
      value == UINT32_MAX) return false;
  title_id = value;
  return true;
}

std::string SerializeTitleOwnLawsV1(const TitleOwnLawsV1 &observation,
    ReadTitleOwnLawsV1Result read_result, std::uint64_t sequence,
    std::uint64_t revision, std::string_view step);
} // namespace xar::game

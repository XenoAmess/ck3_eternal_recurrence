#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::game {

enum class CouncilCurrentTaskDomainTaxFailureV1 : std::uint8_t {
  none = 0,
  context_unavailable,
  native_bindings_unavailable,
  keyword_unavailable,
  keyword_mismatch,
  builder_unavailable,
  cleanup_unavailable,
  numeric_unavailable,
};

inline std::string_view CouncilCurrentTaskDomainTaxFailureKeyV1(
    CouncilCurrentTaskDomainTaxFailureV1 reason) noexcept {
  switch (reason) {
  case CouncilCurrentTaskDomainTaxFailureV1::none: return {};
  case CouncilCurrentTaskDomainTaxFailureV1::context_unavailable:
    return "current_task_owner_tax_context_unavailable";
  case CouncilCurrentTaskDomainTaxFailureV1::native_bindings_unavailable:
    return "current_task_owner_tax_native_bindings_unavailable";
  case CouncilCurrentTaskDomainTaxFailureV1::keyword_unavailable:
    return "current_task_owner_tax_keyword_unavailable";
  case CouncilCurrentTaskDomainTaxFailureV1::keyword_mismatch:
    return "current_task_owner_tax_keyword_mismatch";
  case CouncilCurrentTaskDomainTaxFailureV1::builder_unavailable:
    return "current_task_owner_tax_builder_unavailable";
  case CouncilCurrentTaskDomainTaxFailureV1::cleanup_unavailable:
    return "current_task_owner_tax_cleanup_unavailable";
  case CouncilCurrentTaskDomainTaxFailureV1::numeric_unavailable:
    return "current_task_owner_tax_numeric_unavailable";
  }
  return "current_task_owner_tax_unavailable";
}

// Evaluated current owner component, not applied income or a replacement quote.
struct CouncilCurrentTaskDomainTaxV1 {
  std::int32_t active_task_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t incumbent_character_id = -1;
  std::array<char, 128> task_key{};
  std::optional<bool> frozen;
  std::uint16_t modifier_id = 0xFFFF;
  std::uint32_t keyword_id = 0;
  std::array<char, 64> observed_keyword_key{};
  std::optional<std::int64_t> raw;
  CouncilCurrentTaskDomainTaxFailureV1 unavailable_reason =
      CouncilCurrentTaskDomainTaxFailureV1::none;
};

} // namespace xar::game

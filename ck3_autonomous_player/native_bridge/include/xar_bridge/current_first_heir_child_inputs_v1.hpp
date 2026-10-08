#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::array<std::string_view, 5> kChildhoodTraitKeysV1{
    "curious", "rowdy", "bossy", "pensive", "charming"};

struct CurrentFirstHeirChildValuesV1 {
  bool available = false;
  std::string_view unavailable_reason = "child_character_values_unavailable";
  std::optional<std::int16_t> age_measure_raw{};
  std::optional<std::uint8_t> sex_selector_raw{};
};

struct CurrentFirstHeirChildTraitsV1 {
  bool available = false;
  std::string_view unavailable_reason = "child_trait_definitions_unavailable";
  std::optional<std::vector<std::string_view>> present_trait_keys{};
};

struct CurrentFirstHeirChildFocusV1 {
  bool available = false;
  std::string_view unavailable_reason = "child_current_focus_bindings_unavailable";
  std::string_view presence{};
  std::optional<std::string> key{};
};

struct CurrentFirstHeirChildInputRowV1 {
  std::int32_t character_id = -1;
  std::vector<std::uint32_t> occurrence_indices{};
  CurrentFirstHeirChildValuesV1 values{};
  CurrentFirstHeirChildTraitsV1 childhood_traits{};
  std::optional<CurrentFirstHeirChildFocusV1> native_focus{};
};

// This leaf describes distinct living actual children, while the owning
// descendants leaf retains every original raw occurrence, including failures.
struct CurrentFirstHeirChildInputsReadV1 {
  std::string_view status = "unavailable";
  std::string_view unavailable_reason = "current_heir_child_roster_unavailable";
  std::int32_t played_character_id = -1;
  std::int32_t heir_character_id = -1;
  std::optional<std::int64_t> date_raw{};
  std::vector<CurrentFirstHeirChildInputRowV1> rows{};
};

} // namespace xar::ck3_11906

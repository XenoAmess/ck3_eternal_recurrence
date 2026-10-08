#pragma once

#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

enum class CurrentFirstHeirDescendantsStatusV1 : std::uint8_t {
  unavailable = 0,
  partial,
  available,
};

struct CurrentFirstHeirDescendantLineageV1 {
  bool available = false;
  std::string_view unavailable_reason = "descendant_lineage_unavailable";
  std::int32_t house_id_raw = -1;
  std::int32_t dynasty_id_raw = -1;
};

struct CurrentFirstHeirDescendantRowV1 {
  std::uint32_t occurrence_index = 0;
  std::uint32_t raw_character_id = 0;
  bool generation_valid = false;
  std::optional<bool> alive{};
  std::optional<bool> parent_family_present{};
  std::optional<std::uint32_t> parent_0_character_id_raw{};
  std::optional<std::uint32_t> parent_4_character_id_raw{};
  std::optional<bool> child_of_heir{};
  CurrentFirstHeirDescendantLineageV1 lineage{};
};

// Complete describes the stored raw roster, including unresolved, duplicate,
// dead and non-child occurrences. It is independent of per-row lineage reads.
struct CurrentFirstHeirDescendantsReadV1 {
  CurrentFirstHeirDescendantsStatusV1 status =
      CurrentFirstHeirDescendantsStatusV1::unavailable;
  std::string_view unavailable_reason =
      "current_heir_descendant_binding_unavailable";
  std::int32_t played_character_id = -1;
  std::int32_t heir_character_id = -1;
  std::optional<std::int64_t> date_raw{};
  std::optional<bool> family_present{};
  std::optional<std::int32_t> native_child_count_raw{};
  std::optional<bool> data_pointer_present{};
  bool roster_complete = false;
  CurrentFirstHeirDescendantLineageV1 played_lineage{};
  CurrentFirstHeirDescendantLineageV1 heir_lineage{};
  std::vector<CurrentFirstHeirDescendantRowV1> rows{};
  std::optional<CurrentFirstHeirChildInputsReadV1> child_inputs{};
};

} // namespace xar::ck3_11906

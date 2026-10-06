#pragma once
#include "xar_bridge/diac_literal_numeric_inputs_12003.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
// Snapshot-local identities and demanded raw operands, never callable pointers.
struct Rule43NodeV1 {
  std::string path;
  std::optional<std::string> identity;
  std::optional<std::uint64_t> slot58_rva, slot60_rva, slotc8_rva;
  std::optional<std::int32_t> children_count_raw, reference_arguments_count_raw;
  std::optional<bool> children_array_present, nested_present;
  std::optional<std::uint8_t> reference_compare_raw;
  std::vector<Rule43NodeV1> children;
  std::optional<bool> result;
  std::string reason;
  friend bool operator==(const Rule43NodeV1 &, const Rule43NodeV1 &) = default;
};
struct Rule43AdmissionV1 {
  std::int32_t input_character_full_id = 0;
  std::uint16_t source_constructed_root_kind = 4;
  std::uint64_t expected_validator_rva = 0x22565B0;
  std::optional<std::uint8_t> mode_raw;
  std::optional<std::string> provider_identity, rule_identity;
  std::optional<std::int32_t> registry_count_raw;
  std::optional<std::string> descriptor_selection;
  std::optional<std::uint64_t> loaded_validator_rva;
  std::optional<std::string> root_lookup_selection, root_object_identity;
  std::optional<std::uint32_t> root_tag_raw;
  std::optional<std::int32_t> root_full_id_raw;
  std::optional<bool> root_valid;
  std::vector<Rule43NodeV1> nodes;
  std::optional<bool> result;
  std::string reason;
  friend bool operator==(const Rule43AdmissionV1 &, const Rule43AdmissionV1 &) = default;
};
struct DiacSelectionV1 {
  std::optional<std::string> source_character_identity;
  std::optional<std::int32_t> requested_diac_id_raw;
  std::optional<std::string> lookup_selection, diac_identity;
  std::optional<std::uint32_t> diac_tag_raw;
  std::optional<std::int32_t> diac_full_id_raw, diac_owner_full_id_raw;
  std::optional<std::string> early_character_lookup_selection;
  std::optional<std::int32_t> rule_character_full_id_raw;
  std::optional<bool> diac_valid, owner_matches;
  std::optional<Rule43AdmissionV1> rule;
  std::string reason;
  friend bool operator==(const DiacSelectionV1 &, const DiacSelectionV1 &) = default;
};
struct FollowingDiac2920d60V1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = 0;
  std::optional<std::int32_t> current_character_full_id_raw;
  DiacSelectionV1 primary;
  std::optional<DiacSelectionV1> secondary;
  std::optional<std::string> selected_family;
  std::optional<ck3_12003::DiacLiteralNumericSnapshot12003> numeric_inputs;
  std::string reason;
  friend bool operator==(const FollowingDiac2920d60V1 &, const FollowingDiac2920d60V1 &) = default;
};
} // namespace xar::game

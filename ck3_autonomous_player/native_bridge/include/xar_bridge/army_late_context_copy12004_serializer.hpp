#pragma once
#include "xar_bridge/army_late_context_copy12004.hpp"
#include <sstream>
#include <string>

namespace xar::ck3_12004 {
inline std::string SerializeActualArmyLateContextCopy12004(const ArmyLateContextCopy12004 &copy,
    const ArmyLateContextSourceRoles12004 &roles) {
  std::ostringstream out;
  const auto optional = [&](const auto &value) {
    if (value) out << *value;
    else out << "null";
  };
  out << std::boolalpha << "{\"root_copy_ready\":" << copy.root_copy_ready << ",\"root_kind_raw_u16\":";
  optional(copy.root_kind_raw_u16);
  out << ",\"root_subtype_raw_u16\":"; optional(copy.root_subtype_raw_u16);
  out << ",\"root_payload_raw_u64\":"; optional(copy.root_payload_raw_u64);
  out << ",\"context_seed_10_raw_u32\":"; optional(copy.context_seed_10_raw_u32);
  out << ",\"named_capacity_raw_i32\":"; optional(copy.named_capacity_raw_i32);
  out << ",\"named_count_raw_i32\":"; optional(copy.named_count_raw_i32);
  out << ",\"named_header_copy_ready\":" << copy.named_header_copy_ready
      << ",\"named_header_unchanged\":" << copy.named_header_unchanged
      << ",\"named_rows_copy_ready\":" << copy.named_rows_copy_ready
      << ",\"named_rows_truncated\":" << copy.named_rows_truncated
      << ",\"copied_row_count\":" << copy.copied_row_count
      << ",\"unavailable_reason\":\"" << copy.unavailable_reason << "\",\"rows\":[";
  for (std::size_t i = 0; i < copy.copied_row_count; ++i) {
    const auto &row = copy.rows[i];
    if (i) out << ',';
    out << "{\"key_raw_u32\":" << row.key_raw_u32 << ",\"kind_raw_u16\":" << row.kind_raw_u16
        << ",\"subtype_raw_u16\":" << row.subtype_raw_u16 << ",\"payload_raw_u64\":" << row.payload_raw_u64 << '}';
  }
  out << "],\"root_kind27_subtype0_matches\":"; optional(roles.root_kind27_subtype0_matches);
  out << ",\"named_keys_loaded\":" << roles.named_keys_loaded
      << ",\"complete_named_input_shape_matches\":" << roles.complete_named_input_shape_matches << ",\"source_roles\":[";
  for (std::size_t i = 0; i < roles.roles.size(); ++i) {
    const auto &role = roles.roles[i];
    if (i) out << ',';
    out << "{\"expected_kind_raw_u16\":" << role.expected_kind_raw_u16
        << ",\"loaded_key_raw_u32\":" << role.loaded_key_raw_u32
        << ",\"matching_key_count\":" << role.matching_key_count << ",\"token_kind_and_subtype_match\":";
    optional(role.token_kind_and_subtype_match);
    out << ",\"payload_raw_u64\":"; optional(role.payload_raw_u64); out << '}';
  }
  out << "],\"builder_called\":"; optional(copy.builder_called);
  out << ",\"builder_callsite_rva\":"; optional(copy.builder_callsite_rva);
  out << ",\"parent_pc_rva\":"; optional(copy.parent_pc_rva); out << '}';
  return out.str();
}
} // namespace xar::ck3_12004

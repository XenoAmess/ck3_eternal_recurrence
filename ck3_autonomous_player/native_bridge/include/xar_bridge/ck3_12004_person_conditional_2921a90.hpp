#pragma once

#include "xar_bridge/ck3_12004_person_following_2921a90.hpp"

namespace xar::ck3_12004 {
inline constexpr char kPersonConditional2921a90Schema[] =
    "xar.ck3.person-following-2921a90-conditional-12004-v1";

struct PersonConditional2921a90Vote {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::string resolution_selection = "unavailable";
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<std::uintptr_t> registry_identity;
  std::optional<std::uint32_t> registry_count_u32;
  std::optional<std::uintptr_t> registry_slots_identity;
  std::optional<std::uintptr_t> candidate_character_identity;
  std::optional<std::uint32_t> candidate_full_id_u32;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uintptr_t> selected_scratch_identity;
  std::optional<std::int32_t> base_opinion_i32;
  std::optional<std::int32_t> additional_opinion_i32;
  std::optional<std::int32_t> minimum_i32;
  std::optional<std::int32_t> maximum_i32;
  std::optional<std::int32_t> clamped_i32;
  std::optional<std::uint32_t> high_threshold_bits_u32;
  std::optional<std::uint32_t> low_threshold_bits_u32;
  std::string vote;
  friend bool operator==(const PersonConditional2921a90Vote &,
                         const PersonConditional2921a90Vote &) = default;
};
struct PersonConditional2921a90Metadata {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uint16_t> key_u16;
  std::optional<std::uintptr_t> definition_identity;
  std::optional<std::uint8_t> flag_ba_u8;
  std::optional<std::uint8_t> flag_b8_u8;
  friend bool operator==(const PersonConditional2921a90Metadata &,
                         const PersonConditional2921a90Metadata &) = default;
};
struct PersonConditional2921a90Row {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> object_identity;
  std::optional<std::int32_t> expression_flag_280_i32;
  std::optional<std::uintptr_t> expression_tree_278_identity;
  std::optional<std::uintptr_t> expression_scoped_268_identity;
  std::optional<std::int32_t> expression_count_1d4_i32;
  std::optional<std::int64_t> raw_value_258_q64;
  std::optional<std::int64_t> weight_q64;
  std::optional<std::int32_t> keys_count_i32;
  std::optional<std::int32_t> values_count_i32;
  std::optional<PersonCarrierDirect12004Properties> properties;
  std::optional<std::uintptr_t> metadata_registry_identity;
  std::optional<std::uintptr_t> metadata_table_identity;
  std::vector<PersonConditional2921a90Metadata> metadata;
  friend bool operator==(const PersonConditional2921a90Row &,
                         const PersonConditional2921a90Row &) = default;
};
struct PersonConditional2921a90DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<std::uintptr_t> selected_object_identity;
  std::optional<std::uintptr_t> conditional_definition_identity;
  std::optional<bool> admitted;
  std::optional<std::int32_t> gate_b8c_count_i32;
  std::optional<std::int32_t> gate_bbc_count_i32;
  bool classifier_ready = false;
  std::string classifier_reason;
  std::optional<std::uint32_t> classifier_magic_u32;
  std::optional<std::uint32_t> classifier_full_id_u32;
  std::optional<std::uintptr_t> classifier_land_identity;
  std::string classifier_header_selection = "unavailable";
  std::optional<std::uintptr_t> classifier_header_identity;
  std::optional<std::int32_t> classifier_default_guard_i32;
  std::optional<std::uintptr_t> classifier_array_identity;
  std::optional<std::int32_t> classifier_count_i32;
  std::vector<PersonConditional2921a90Vote> classifier_rows;
  std::optional<std::int32_t> classifier_result_i32;
  std::string selected_family = "unavailable";
  std::optional<std::uintptr_t> selected_array_identity;
  std::optional<std::int32_t> selected_count_i32;
  std::vector<PersonConditional2921a90Row> rows;
  std::optional<std::uint32_t> occurrence_count;
  friend bool operator==(const PersonConditional2921a90DTO &,
                         const PersonConditional2921a90DTO &) = default;
};

// Existing exact4 guarded-copy binding and already observed linked receiver.
// No opinion, expression, initialization, container or Model callback runs.
PersonConditional2921a90DTO ReadPersonConditional2921a90Inputs12004(
    const PersonCarrierDirect12004Bindings &,
    const PersonFollowing2921a90DTO &same_query_source);
std::string SerializePersonConditional2921a90(
    const PersonConditional2921a90DTO &);
} // namespace xar::ck3_12004

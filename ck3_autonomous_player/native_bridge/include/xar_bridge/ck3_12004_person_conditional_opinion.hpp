#pragma once

#include "xar_bridge/ck3_12004_person_conditional_2921a90.hpp"
#include "xar_bridge/ck3_12004_gift_opinion.hpp"

namespace xar::ck3_12004 {
inline constexpr char kPersonConditionalOpinion12004Schema[] =
    "xar.ck3.person-following-2921a90-opinion-12004-v1";

struct PersonConditionalOpinion12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  // Legacy-named storage type, bound exclusively by the actual4 factory.
  ck3_12002::GiftOpinionBindings12002 opinion;
};
struct PersonConditionalOpinion12004Row {
  std::uint32_t source_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> selected_full_character_id;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> toward_full_character_id;
  std::optional<std::uintptr_t> toward_character_identity;
  std::string source_selection = "unavailable";
  std::optional<std::int32_t> base_value;
  std::optional<std::int32_t> additional_value;
  // Actual 28BC470 already clamped this signed integer. Never clamp again.
  std::optional<std::int32_t> total_opinion_i32;
  std::optional<std::uint32_t> high_threshold_bits_u32;
  std::optional<std::uint32_t> low_threshold_bits_u32;
  std::string vote;
  friend bool operator==(const PersonConditionalOpinion12004Row &,
                         const PersonConditionalOpinion12004Row &) = default;
};
struct PersonConditionalOpinion12004DTO {
  std::string build_version;
  std::string executable_sha256;
  std::optional<std::uint32_t> character_id;
  bool ready = false;
  std::string reason;
  PersonConditional2921a90DTO source_inputs;
  std::vector<PersonConditionalOpinion12004Row> opinion_rows;
  bool classifier_ready = false;
  std::string classifier_reason;
  std::optional<std::int32_t> classifier_result_i32;
  std::string selected_family = "unavailable";
  std::optional<std::uintptr_t> selected_array_identity;
  std::optional<std::int32_t> selected_count_i32;
  std::vector<PersonConditional2921a90Row> rows;
  std::optional<std::uint32_t> occurrence_count;
  friend bool operator==(const PersonConditionalOpinion12004DTO &,
                         const PersonConditionalOpinion12004DTO &) = default;
};

PersonConditionalOpinion12004Bindings BindPersonConditionalOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
PersonConditionalOpinion12004DTO ReadPersonConditionalOpinionInputs12004(
    const PersonConditionalOpinion12004Bindings &,
    const PersonCarrierDirect12004Bindings &guarded_source_binding,
    const PersonFollowing2921a90DTO &same_query_direct,
    const PersonConditional2921a90DTO &unchanged_same_query_source_inputs);
std::string SerializePersonConditionalOpinion12004(
    const PersonConditionalOpinion12004DTO &);

// Internal reusable seams implemented beside the original reader. They reuse
// its proven row logic without changing its reader or original formatter.
PersonConditional2921a90Row ReadPersonConditional2921a90RowInputs12004(
    const PersonCarrierDirect12004Bindings &, std::uintptr_t physical_array,
    std::uint32_t native_index);
std::string SerializePersonConditional2921a90RowInputs12004(
    const PersonConditional2921a90Row &);
} // namespace xar::ck3_12004

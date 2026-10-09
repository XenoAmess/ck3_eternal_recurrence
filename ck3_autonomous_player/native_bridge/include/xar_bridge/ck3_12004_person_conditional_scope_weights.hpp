#pragma once

#include "xar_bridge/ck3_12004_person_conditional_opinion.hpp"

namespace xar::ck3_12004 {
inline constexpr char kPersonConditionalScopeWeights12004Schema[] =
    "xar.ck3.person-following-2921a90-scope-weights-12004-v1";
inline constexpr std::uintptr_t kPersonConditionalScopeConstructorRva12004 = 0x8895D0;
inline constexpr std::uintptr_t kPersonConditionalScopeRowWeightRva12004 = 0x2872300;
inline constexpr std::size_t kPersonConditionalScopeStorageBytes12004 = 0x170;

using PersonConditionalScopeConstructVector12004 = void *(*)(void *);
using PersonConditionalScopeReadWeight12004 =
    std::int64_t *(*)(const void *, std::int64_t *, const void *);
struct PersonConditionalScopeWeights12004Bindings {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  PersonConditionalScopeConstructVector12004 construct_vector = nullptr;
  PersonConditionalScopeReadWeight12004 read_weight = nullptr;
};
struct PersonConditionalScopeWeightRow12004 {
  std::uint32_t native_index = 0;
  std::string evaluation_selection = "unavailable";
  std::optional<std::uint32_t> weight_call_ordinal;
  bool scope_prefix_ready = false;
  PersonConditional2921a90Row source_inputs;
  std::optional<PersonConditional2921a90Row> evaluated_inputs;
  friend bool operator==(const PersonConditionalScopeWeightRow12004 &,
                         const PersonConditionalScopeWeightRow12004 &) = default;
};
struct PersonConditionalScopeWeights12004DTO {
  std::string build_version;
  std::string executable_sha256;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> selected_object_identity;
  bool classifier_ready = false;
  std::optional<std::int32_t> classifier_result_i32;
  std::string selected_family = "unavailable";
  std::optional<std::uintptr_t> selected_array_identity;
  std::optional<std::int32_t> selected_count_i32;
  bool scope_initialized = false;
  std::optional<std::uint16_t> scope_kind_u16;
  std::optional<std::uint32_t> scope_payload_u32;
  bool ready = false;
  std::string reason;
  std::vector<PersonConditionalScopeWeightRow12004> rows;
  std::optional<std::uint32_t> occurrence_count;
  friend bool operator==(const PersonConditionalScopeWeights12004DTO &,
                         const PersonConditionalScopeWeights12004DTO &) = default;
};

PersonConditionalScopeWeights12004Bindings BindPersonConditionalScopeWeightsImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
PersonConditionalScopeWeights12004DTO ReadPersonConditionalScopeWeights12004(
    const PersonConditionalScopeWeights12004Bindings &,
    const PersonCarrierDirect12004Bindings &guarded_source_binding,
    const PersonFollowing2921a90DTO &same_query_following_direct,
    const PersonConditionalOpinion12004DTO &same_query_opinion);
std::string SerializePersonConditionalScopeWeights12004(
    const PersonConditionalScopeWeights12004DTO &);

// New observed-weight seam only; old literal readers/formatters stay unchanged.
PersonConditional2921a90Row ReadPersonConditional2921a90RowWithWeightInputs12004(
    const PersonCarrierDirect12004Bindings &, std::uintptr_t physical_array,
    std::uint32_t native_index, std::int64_t observed_weight);
} // namespace xar::ck3_12004

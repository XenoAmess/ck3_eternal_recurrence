#pragma once

#include "xar_bridge/battle_context_locale_inputs_v1.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// Current, same-frame source operands only. Opaque identities compare native
// pointers within this snapshot; they are not persistent definition keys.
struct ContextSourcePropertiesV1 {
  std::optional<std::int32_t> keys_count;
  std::optional<std::int32_t> values_count;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  std::optional<std::vector<std::int64_t>> values_q64;
  std::string reason;
  friend bool operator==(const ContextSourcePropertiesV1 &,
                         const ContextSourcePropertiesV1 &) = default;
};
struct ContextSourceResolutionV1 {
  std::string status = "unavailable";
  std::optional<std::uint32_t> requested_full_id;
  std::optional<std::uint32_t> selected_full_id;
  std::string reason;
  friend bool operator==(const ContextSourceResolutionV1 &,
                         const ContextSourceResolutionV1 &) = default;
};
struct ContextSourceWeightedRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> definition_identity;
  std::optional<std::int64_t> weight_q64;
  friend bool operator==(const ContextSourceWeightedRowV1 &,
                         const ContextSourceWeightedRowV1 &) = default;
};
struct ContextSourceWeightedSpanV1 {
  std::string selected_source;
  std::optional<std::int32_t> count;
  std::optional<std::vector<ContextSourceWeightedRowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceWeightedSpanV1 &,
                         const ContextSourceWeightedSpanV1 &) = default;
};
struct ContextSourceDefinitionBlockV1 {
  std::string definition_identity;
  std::optional<ContextSourcePropertiesV1> properties;
  friend bool operator==(const ContextSourceDefinitionBlockV1 &,
                         const ContextSourceDefinitionBlockV1 &) = default;
};
struct ContextSource291e210V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> component_present;
  ContextSourceResolutionV1 first_relation_resolution;
  ContextSourceResolutionV1 second_relation_resolution;
  ContextSourceResolutionV1 house_resolution;
  std::optional<bool> house_extra_enabled;
  std::optional<ContextSourceWeightedSpanV1> selected_lifestyle_span;
  std::optional<ContextSourceWeightedSpanV1> selected_dynasty_span;
  std::optional<ContextSourceWeightedSpanV1> selected_house_span;
  std::optional<ContextSourceWeightedSpanV1> selected_house_extra_span;
  std::vector<ContextSourceDefinitionBlockV1> definition_blocks;
  std::string reason;
  friend bool operator==(const ContextSource291e210V1 &,
                         const ContextSource291e210V1 &) = default;
};
struct ContextSourceSignedKeySetV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> count;
  std::optional<std::vector<std::int32_t>> keys_i32;
  std::string reason;
  friend bool operator==(const ContextSourceSignedKeySetV1 &,
                         const ContextSourceSignedKeySetV1 &) = default;
};
struct ContextSourceConditionalAV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> key_identity;
  std::optional<std::uint32_t> key_object_id;
  std::optional<std::uint32_t> key_object_magic;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::optional<bool> admitted;
  std::string reason;
  std::string property_source;
  std::optional<std::int32_t> property_source_native_index;
  friend bool operator==(const ContextSourceConditionalAV1 &,
                         const ContextSourceConditionalAV1 &) = default;
};
struct ContextSourceConditionalBV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> key_i32;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::optional<bool> admitted;
  std::string reason;
  std::string admission_source;
  std::optional<std::int32_t> admission_nested_native_index;
  friend bool operator==(const ContextSourceConditionalBV1 &,
                         const ContextSourceConditionalBV1 &) = default;
};
struct ContextSourceConditionalCV1 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> source_key_u32;
  std::optional<std::uint32_t> masked_index_u32;
  std::optional<std::int32_t> resolver_count_i32;
  std::optional<bool> selected_native_fallback;
  std::optional<std::uint8_t> invert_u8;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::optional<std::string> resolved_condition_identity;
  std::string condition_source;
  std::optional<std::int32_t> condition_length;
  std::optional<std::uint64_t> condition_capacity;
  std::optional<std::vector<std::uint8_t>> condition_bytes;
  std::optional<std::int32_t> first_signed_byte;
  std::optional<std::int32_t> classifier_mode_i32;
  std::optional<std::int32_t> classifier_result_i32;
  std::optional<ContextSourceLocaleClassificationV1> locale_classification;
  std::string lookup_status;
  std::optional<std::int32_t> condition_token_id;
  std::optional<bool> admitted;
  std::string token_origin;
  std::string reason;
  friend bool operator==(const ContextSourceConditionalCV1 &,
                         const ContextSourceConditionalCV1 &) = default;
};
struct ContextSourceSourceRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> source_identity;
  std::optional<ContextSourcePropertiesV1> base_properties;
  std::string auxiliary_410_provenance = "unobserved_shape_source+410";
  std::optional<std::string> auxiliary_retained_identity;
  std::optional<bool> auxiliary_retained_present;
  std::optional<std::uint32_t> auxiliary_tag_u32;
  std::optional<std::int32_t> conditional_a_count;
  std::optional<std::int32_t> conditional_b_count;
  std::optional<std::int32_t> conditional_c_count;
  std::optional<std::vector<ContextSourceConditionalAV1>> conditional_a_rows;
  std::optional<std::vector<ContextSourceConditionalBV1>> conditional_b_rows;
  std::optional<std::vector<ContextSourceConditionalCV1>> conditional_c_rows;
  std::string reason;
  friend bool operator==(const ContextSourceSourceRowV1 &,
                         const ContextSourceSourceRowV1 &) = default;
};
struct ContextSource291d7e0V1 {
  std::string status = "unavailable";
  bool ready = false;
  bool base_inputs_ready = false;
  std::optional<bool> component_present;
  std::string selected_source;
  std::optional<std::int32_t> source_count;
  std::optional<std::vector<ContextSourceSourceRowV1>> source_rows;
  std::optional<ContextSourcePropertiesV1> conditional_a_fallback_properties;
  std::optional<ContextSourceResolutionV1> selector_a_stage1;
  std::optional<ContextSourceResolutionV1> selector_a_stage2;
  std::optional<ContextSourceResolutionV1> selector_a_stage3;
  std::string selector_a_selected_source;
  std::optional<std::int32_t> selector_a_key_count;
  std::optional<std::vector<std::string>> selector_a_key_identities;
  std::optional<ContextSourceResolutionV1> selector_b_resolution;
  std::optional<ContextSourceSignedKeySetV1> selector_b_primary_keys;
  std::optional<std::int32_t> selector_b_nested_count;
  std::optional<std::vector<ContextSourceSignedKeySetV1>> selector_b_nested_keys;
  std::optional<std::int32_t> government_token_count;
  std::optional<std::vector<std::int32_t>> government_token_ids_i32;
  std::optional<std::int32_t> condition_registry_guard;
  std::optional<std::int32_t> condition_fallback_guard;
  std::optional<bool> token_manager_present;
  std::string government_source;
  std::string reason;
  friend bool operator==(const ContextSource291d7e0V1 &,
                         const ContextSource291d7e0V1 &) = default;
};
struct BattleCurrentPersonContextSourceInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<ContextSource291e210V1> branch_291e210;
  std::optional<ContextSource291d7e0V1> branch_291d7e0;
  std::string reason;
  friend bool operator==(const BattleCurrentPersonContextSourceInputsSnapshotV1 &,
                         const BattleCurrentPersonContextSourceInputsSnapshotV1 &) = default;
};

} // namespace xar::game

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
// 291C255 predicate and 291C277 unit contribution. These are current operands,
// after 291D1D0 and before A/B, never a before-stage context postimage.
struct ContextSourcePre291e2101640V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::string> army_selection;
  std::optional<std::int32_t> army_key_f4_raw;
  std::optional<std::int32_t> army_field_120_raw;
  std::optional<std::int32_t> army_field_124_raw;
  std::optional<std::string> second_selection;
  std::optional<std::int32_t> second_field_174_raw;
  std::optional<bool> admitted;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePre291e2101640V1 &,
                         const ContextSourcePre291e2101640V1 &) = default;
};
struct ContextSourcePostGuarded630V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> carrier_1b0_present;
  std::optional<bool> carrier280_present;
  std::optional<std::string> selection;
  std::optional<std::int32_t> selected_field38_raw;
  std::optional<std::int16_t> character68_signed;
  std::optional<std::int32_t> threshold_signed;
  std::optional<bool> admitted;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePostGuarded630V1 &,
                         const ContextSourcePostGuarded630V1 &) = default;
};
struct ContextSourcePostCarrier40V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> carrier_1b0_present;
  std::optional<bool> carrier288_present;
  std::optional<bool> admitted;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePostCarrier40V1 &,
                         const ContextSourcePostCarrier40V1 &) = default;
};
struct ContextSourcePostD8OccurrenceV1 {
  std::int32_t source_index = 0;
  std::optional<std::string> source_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePostD8OccurrenceV1 &,
                         const ContextSourcePostD8OccurrenceV1 &) = default;
};
struct ContextSourcePostOrderedD8V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> carrier_1c0_present;
  std::optional<std::string> header_selection;
  std::optional<bool> source_array_present;
  std::optional<std::int32_t> source_count_raw;
  std::optional<std::vector<ContextSourcePostD8OccurrenceV1>> occurrences;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePostOrderedD8V1 &,
                         const ContextSourcePostOrderedD8V1 &) = default;
};
struct ContextSourcePost291d7e0V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourcePostGuarded630V1 guarded630;
  ContextSourcePostCarrier40V1 carrier40;
  ContextSourcePostOrderedD8V1 ordered_d8;
  std::string unavailable_reason;
  friend bool operator==(const ContextSourcePost291d7e0V1 &,
                         const ContextSourcePost291d7e0V1 &) = default;
};
// The caller-direct leaves after helper291F0A0. Independent readiness does not
// close that preceding helper or a contiguous complete-person source chain.
struct ContextSourceLaterOrderedRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::string> selection;
  std::optional<std::string> selected_identity;
  std::optional<std::int32_t> selected_field_24c_raw;
  std::optional<bool> admitted;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceLaterOrderedRowV1 &,
                         const ContextSourceLaterOrderedRowV1 &) = default;
};
struct ContextSourceLaterDirectV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::string> ordered_header_selection;
  std::optional<std::int32_t> ordered_count;
  std::optional<bool> ordered_array_present;
  std::optional<std::vector<ContextSourceLaterOrderedRowV1>> ordered_rows;
  std::optional<std::string> guarded_selection;
  std::optional<std::uint32_t> guarded_magic_raw;
  std::optional<bool> guarded_admitted;
  std::optional<ContextSourcePropertiesV1> guarded_property_block;
  std::string reason;
  friend bool operator==(const ContextSourceLaterDirectV1 &,
                         const ContextSourceLaterDirectV1 &) = default;
};
struct ContextSourceHelperRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> source_identity;
  std::optional<std::int32_t> gate_raw;
  std::optional<bool> admitted;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceHelperRowV1 &,
                         const ContextSourceHelperRowV1 &) = default;
};
struct ContextSourceHelperFamilyV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string selected_source;
  std::optional<bool> admitted;
  std::optional<std::int32_t> count;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceHelperRowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceHelperFamilyV1 &,
                         const ContextSourceHelperFamilyV1 &) = default;
};
struct ContextSourceHelper291f0a0V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::string> first_selection;
  std::optional<std::int32_t> first_key_b4_raw;
  std::optional<bool> manager_present;
  std::optional<std::string> manager_definition_selection;
  std::optional<std::string> manager_definition_identity;
  std::optional<std::string> recipient_source;
  std::optional<std::int64_t> recipient_q64;
  std::optional<std::int32_t> range_count_raw;
  std::optional<std::string> range_selection;
  std::optional<std::int32_t> range_native_index;
  std::optional<std::int64_t> range_lower_q64;
  std::optional<std::int64_t> range_upper_q64;
  std::optional<std::int32_t> default_pc_guard_raw;
  std::optional<std::int32_t> pointer_list_guard_raw;
  std::optional<std::int32_t> predicate_character_15c_raw;
  std::optional<std::int32_t> predicate_first_key_b4_raw;
  std::optional<std::int32_t> predicate_second_key_4b8_raw;
  std::optional<std::int32_t> predicate_second_a0_raw;
  std::optional<bool> predicate_admitted;
  ContextSourceHelperFamilyV1 primary_direct;
  ContextSourceHelperFamilyV1 manager_range;
  ContextSourceHelperFamilyV1 source_a18;
  ContextSourceHelperFamilyV1 conditional_direct;
  std::string reason;
  friend bool operator==(const ContextSourceHelper291f0a0V1 &,
                         const ContextSourceHelper291f0a0V1 &) = default;
};
struct BattleCurrentPersonContextSourceInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<ContextSourcePre291e2101640V1> pre_291e210_1640;
  std::optional<ContextSourceLaterDirectV1> later_direct_291c3fb_44c;
  std::optional<ContextSourceHelper291f0a0V1> helper_291f0a0;
  std::optional<ContextSource291e210V1> branch_291e210;
  std::optional<ContextSource291d7e0V1> branch_291d7e0;
  std::optional<ContextSourcePost291d7e0V1> post_291d7e0_sources;
  std::string reason;
  friend bool operator==(const BattleCurrentPersonContextSourceInputsSnapshotV1 &,
                         const BattleCurrentPersonContextSourceInputsSnapshotV1 &) = default;
};

} // namespace xar::game

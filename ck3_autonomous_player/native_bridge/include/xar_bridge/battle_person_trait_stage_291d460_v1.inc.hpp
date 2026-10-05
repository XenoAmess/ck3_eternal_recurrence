// Included after ContextSourcePropertiesV1, inside namespace xar::game.
struct ContextSourceTraitCondition291d460V1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> key_i32;
  std::optional<bool> admitted;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceTraitCondition291d460V1 &,
                         const ContextSourceTraitCondition291d460V1 &) = default;
};
struct ContextSourceTraitGroup291d460V1 {
  std::string role;
  std::optional<std::int32_t> track_index;
  std::optional<std::int32_t> level_index;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> base_property_block;
  std::optional<std::int32_t> conditional_b_count;
  std::optional<std::vector<ContextSourceTraitCondition291d460V1>> conditional_b_rows;
  std::optional<std::int32_t> conditional_a_count;
  std::optional<std::vector<ContextSourceTraitCondition291d460V1>> conditional_a_rows;
  bool ready = false;
  std::string reason;
  friend bool operator==(const ContextSourceTraitGroup291d460V1 &,
                         const ContextSourceTraitGroup291d460V1 &) = default;
};
struct ContextSourceTraitTrack291d460V1 {
  std::int32_t native_index = 0;
  std::optional<std::int64_t> current_value_raw;
  std::optional<std::int32_t> level_count;
  std::optional<std::vector<std::int64_t>> thresholds_read;
  std::optional<std::int32_t> admitted_prefix_count;
  std::string reason;
  friend bool operator==(const ContextSourceTraitTrack291d460V1 &,
                         const ContextSourceTraitTrack291d460V1 &) = default;
};
struct ContextSourceTraitProbe291d460V1 {
  std::int64_t row_index = 0;
  std::uint8_t distance_u8 = 1;
  std::optional<std::uint8_t> control_u8;
  std::optional<std::uint64_t> key_pointer_raw;
  std::optional<bool> admitted;
  std::string reason;
  friend bool operator==(const ContextSourceTraitProbe291d460V1 &,
                         const ContextSourceTraitProbe291d460V1 &) = default;
};
struct ContextSourceTraitSide291d460V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> map_mask_raw;
  std::optional<std::uint8_t> map_overflow_raw;
  std::optional<std::uint32_t> hash_u32;
  std::optional<std::int64_t> first_row_index;
  std::vector<ContextSourceTraitProbe291d460V1> probes;
  std::optional<std::int32_t> kind_raw;
  std::optional<std::string> owner_selection;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceTraitSide291d460V1 &,
                         const ContextSourceTraitSide291d460V1 &) = default;
};
struct ContextSourceTraitRow291d460V1 {
  std::int32_t native_index = 0;
  std::int32_t trait_id_raw = 0;
  std::optional<std::string> definition_selection;
  std::optional<std::string> definition_identity;
  std::optional<std::uint64_t> definition_pointer_raw;
  std::optional<std::int32_t> definition_id_raw;
  bool composite_ready = false;
  std::vector<ContextSourceTraitGroup291d460V1> composite_groups;
  std::optional<std::uint8_t> growth_flag_raw;
  std::optional<std::int32_t> track_count_raw;
  std::optional<std::int32_t> growth_trait_match_index;
  std::optional<std::vector<std::int32_t>> growth_prefix_track_counts;
  std::optional<std::int32_t> growth_prefix_offset_raw;
  std::optional<std::int32_t> growth_aux_count_raw;
  std::optional<std::int32_t> growth_output_count_raw;
  std::vector<ContextSourceTraitTrack291d460V1> growth_tracks;
  std::string growth_selection;
  std::string composite_reason;
  ContextSourceTraitSide291d460V1 side;
  std::string reason;
  friend bool operator==(const ContextSourceTraitRow291d460V1 &,
                         const ContextSourceTraitRow291d460V1 &) = default;
};
struct ContextSourceTraitStage291d460V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::int32_t> trait_count;
  std::optional<bool> trait_array_present;
  std::optional<std::vector<ContextSourceTraitRow291d460V1>> rows;
  std::optional<std::int32_t> selector_a_key_raw;
  std::optional<std::string> selector_a_selection;
  std::optional<std::string> selector_a_identity;
  std::optional<std::int32_t> selector_b_key_raw;
  std::optional<std::string> selector_b_selection;
  std::optional<std::string> selector_b_identity;
  std::optional<std::int32_t> selector_a_membership_count;
  std::optional<std::vector<std::int32_t>> selector_a_keys_i32;
  std::optional<std::int32_t> selector_b_primary_count;
  std::optional<std::vector<std::int32_t>> selector_b_primary_keys_i32;
  std::optional<std::int32_t> selector_b_nested_count;
  std::optional<std::vector<ContextSourceSignedKeySetV1>> selector_b_nested_keys;
  std::string reason;
  friend bool operator==(const ContextSourceTraitStage291d460V1 &,
                         const ContextSourceTraitStage291d460V1 &) = default;
};

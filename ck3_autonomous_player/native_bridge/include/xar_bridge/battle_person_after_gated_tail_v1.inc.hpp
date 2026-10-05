// Included inside xar::game; FINAL-RAW-SCHEMA.json precedes implementation.
struct ContextSourceAfterPcV1 {
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceAfterPcV1 &, const ContextSourceAfterPcV1 &) = default;
};
struct ContextSourceAfterDateV1 {
  std::optional<std::int32_t> raw_i32;
  std::optional<std::int8_t> day_cache_i8;
  std::optional<std::int8_t> month_cache_i8;
  std::optional<std::int16_t> year_cache_i16;
  friend bool operator==(const ContextSourceAfterDateV1 &, const ContextSourceAfterDateV1 &) = default;
};
struct ContextSourceAfterThresholdRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> threshold_raw;
  std::optional<bool> admitted;
  ContextSourceAfterPcV1 pc{};
  std::string reason;
  friend bool operator==(const ContextSourceAfterThresholdRowV1 &, const ContextSourceAfterThresholdRowV1 &) = default;
};
struct ContextSourceAfterRowsetV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::int32_t> count_raw;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceAfterThresholdRowV1>> rows;
  std::string reason = "after_rowset_unobserved";
  friend bool operator==(const ContextSourceAfterRowsetV1 &, const ContextSourceAfterRowsetV1 &) = default;
};
struct ContextSourceAfterRelatedSelectionV1 {
  std::optional<bool> carrier_present;
  std::vector<ContextSourceGatedResolutionV1> attempts;
  std::optional<std::int32_t> self_full_id_raw;
  std::optional<std::int32_t> helper_return_full_id_raw;
  std::optional<std::string> caller_selection;
  std::optional<std::string> caller_identity;
  std::optional<std::int32_t> caller_requested_full_id_raw;
  std::optional<std::int32_t> caller_full_id_raw;
  std::optional<std::uint32_t> caller_magic_raw;
  std::optional<bool> caller_admitted;
  std::optional<bool> land_present;
  std::optional<bool> selected_present;
  std::string reason;
  friend bool operator==(const ContextSourceAfterRelatedSelectionV1 &, const ContextSourceAfterRelatedSelectionV1 &) = default;
};
struct ContextSourceAfterCompositionV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::uint8_t> global_flag_u8;
  std::optional<bool> global_bit20;
  std::optional<bool> current_land_present;
  std::optional<bool> current_selected_present;
  std::optional<std::string> receiver_selection;
  std::optional<bool> admitted;
  ContextSourceAfterRelatedSelectionV1 related{};
  std::optional<bool> owner_mode;
  std::optional<std::string> definition_identity;
  std::optional<std::int32_t> level_raw;
  ContextSourceAfterDateV1 handle_date{};
  ContextSourceAfterDateV1 fifth_date{};
  ContextSourceAfterDateV1 current_date{};
  std::optional<std::string> chosen_date_selection;
  std::optional<std::int32_t> completed_months_raw;
  ContextSourceAfterRowsetV1 level_rows{};
  ContextSourceAfterRowsetV1 month_rows{};
  std::string reason = "after_composition_unobserved";
  friend bool operator==(const ContextSourceAfterCompositionV1 &, const ContextSourceAfterCompositionV1 &) = default;
};
struct ContextSourceAfterRuleV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> mode_raw;
  std::optional<bool> tree_present;
  std::optional<std::string> tree_identity;
  std::optional<bool> named_present;
  ContextSourceGatedNamedLiteralV1 named{0};
  std::optional<std::int32_t> target_count_raw;
  std::optional<std::int64_t> raw_98_q64;
  std::optional<std::int64_t> value_q64;
  std::optional<std::string> selection;
  std::string reason = "after_definition_600_rule_unconsumed";
  friend bool operator==(const ContextSourceAfterRuleV1 &, const ContextSourceAfterRuleV1 &) = default;
};
struct ContextSourceAfterKindV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> position_120_raw;
  std::optional<std::int32_t> position_124_raw;
  std::optional<std::string> owner_selection;
  std::optional<std::string> owner_identity;
  std::optional<std::int32_t> owner_full_id_raw;
  std::optional<std::int32_t> played_count_raw;
  std::optional<std::vector<std::int32_t>> played_full_ids;
  std::optional<bool> owner_played;
  std::optional<std::uint8_t> raw_a0_u8;
  std::optional<std::int32_t> threshold_count_raw;
  std::optional<std::vector<std::int32_t>> thresholds_i32;
  ContextSourceAfterRuleV1 rule{};
  std::optional<std::int32_t> kind_raw;
  std::string reason = "after_position_kind_unconsumed";
  friend bool operator==(const ContextSourceAfterKindV1 &, const ContextSourceAfterKindV1 &) = default;
};
struct ContextSourceAfterPairProbeV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> count_raw;
  friend bool operator==(const ContextSourceAfterPairProbeV1 &, const ContextSourceAfterPairProbeV1 &) = default;
};
struct ContextSourceAfterPositionV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::string> position_selection;
  std::optional<std::string> position_identity;
  std::optional<std::int32_t> position_full_id_raw;
  std::optional<std::string> definition_identity;
  std::optional<std::string> other_definition_identity;
  std::optional<std::uint32_t> other_magic_raw;
  std::optional<bool> other_admitted;
  ContextSourceAfterPcV1 base_pc{};
  ContextSourceAfterPcV1 tier_pc{};
  std::optional<ContextSourceTraitGroup291d460V1> composite_group;
  ContextSourceAfterKindV1 kind{};
  ContextSourceAfterPcV1 other_base_pc{};
  ContextSourceAfterPcV1 other_tier_pc{};
  ContextSourceAfterKindV1 other_kind{};
  std::vector<ContextSourceAfterPairProbeV1> definition_pair_probes;
  std::optional<bool> definition_pair_admitted;
  std::vector<ContextSourceAfterPairProbeV1> other_pair_probes;
  std::optional<bool> other_pair_admitted;
  bool ready = false;
  std::string reason;
  friend bool operator==(const ContextSourceAfterPositionV1 &, const ContextSourceAfterPositionV1 &) = default;
};
struct ContextSourceAfterCourtListV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> owner_present;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> count_raw;
  std::optional<std::int32_t> numeric_count;
  std::optional<bool> array_present;
  std::optional<std::int32_t> default_init_guard_raw;
  ContextSourceAfterRelatedSelectionV1 related{};
  std::optional<std::vector<ContextSourceAfterPositionV1>> rows;
  std::string reason = "after_court_list_unobserved";
  friend bool operator==(const ContextSourceAfterCourtListV1 &, const ContextSourceAfterCourtListV1 &) = default;
};
struct ContextSourceAfterGatedTail326a8e0And2920310V1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> current_land_present;
  // Only the sealed selector-ledger fields are serialized from this reused
  // read-state DTO. No trait, side, growth or trait emitter is invoked.
  ContextSourceTraitStage291d460V1 selector_inputs{};
  ContextSourceAfterCompositionV1 composition_326a8e0{};
  ContextSourceAfterCourtListV1 current_1b8_court_positions{};
  ContextSourceAfterCourtListV1 current_1c0_court_positions{};
  ContextSourceAfterCourtListV1 related_court_positions{};
  std::string reason = "after_gated_tail_unobserved";
  friend bool operator==(const ContextSourceAfterGatedTail326a8e0And2920310V1 &,
                         const ContextSourceAfterGatedTail326a8e0And2920310V1 &) = default;
};

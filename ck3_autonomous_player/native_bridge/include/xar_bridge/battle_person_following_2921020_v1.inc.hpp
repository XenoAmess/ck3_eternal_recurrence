// Included inside xar::game. Source and FINAL-RAW-SCHEMA precede code.
struct ContextSourceFollowing2921020InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> component_present;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::string> resolution_selection;
  std::optional<std::int32_t> selected_full_id_raw;
  std::optional<std::string> object_identity;
  std::optional<std::uint32_t> magic_u32;
  std::optional<std::int32_t> full_id_raw;
  std::optional<bool> admitted;
  std::optional<std::int32_t> character_full_id_raw;
  std::optional<std::int32_t> owner_full_id_raw;
  std::optional<bool> owner_matches;
  std::optional<std::string> table_identity;
  std::optional<std::string> definition_identity;
  std::optional<std::int8_t> rank_raw_i8;
  std::optional<std::string> tier_selection;
  std::optional<std::string> selected_row_identity;
  std::optional<ContextSourceWeightedSpanV1> owner_weighted_header;
  std::vector<ContextSourceDefinitionBlockV1> owner_definition_blocks;
  std::optional<bool> owner_header_ready;
  ContextSourceAfterPcV1 base_pc{};
  ContextSourceAfterPcV1 tier_pc{};
  bool composite_ready = false;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921020InputsV1 &,
                         const ContextSourceFollowing2921020InputsV1 &) = default;
};

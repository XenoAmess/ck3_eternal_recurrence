// Included inside xar::game; source and FINAL-RAW-SCHEMA precede code.
struct ContextSourceFollowing2920b50AttributeV1 {
  std::int32_t native_index = 0;
  std::optional<bool> definition_present;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> definition_magic_u32;
  std::optional<bool> preflight_valid;
  std::optional<std::int32_t> rank_raw_i32;
  std::optional<std::int32_t> index_raw_i32;
  std::optional<std::string> ranked_header_identity;
  std::optional<std::int32_t> ranked_count_raw;
  std::optional<bool> ranked_array_present;
  std::optional<std::string> selection;
  std::optional<std::string> selected_row_identity;
  std::optional<std::int32_t> ranked_default_init_guard_raw;
  ContextSourceAfterPcV1 pc{};
  bool ready = false;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2920b50AttributeV1 &, const ContextSourceFollowing2920b50AttributeV1 &) = default;
};
struct ContextSourceFollowing2920b50OccurrenceV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::string> resolution_selection;
  std::optional<std::int32_t> selected_full_id_raw;
  std::optional<std::string> object_identity;
  std::optional<std::uint32_t> accolade_magic_u32;
  std::optional<std::int32_t> accolade_full_id_raw;
  std::optional<bool> admitted;
  std::optional<std::int32_t> attribute_count_raw;
  std::optional<bool> attribute_array_present;
  bool preflight_ready = false;
  std::optional<bool> preflight_all_valid;
  std::optional<std::vector<ContextSourceFollowing2920b50AttributeV1>> attributes;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2920b50OccurrenceV1 &, const ContextSourceFollowing2920b50OccurrenceV1 &) = default;
};
struct ContextSourceFollowing2920b50ListV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> component_present;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> default_init_guard_raw;
  std::optional<std::int32_t> count_raw;
  std::optional<std::int32_t> numeric_count;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceFollowing2920b50OccurrenceV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2920b50ListV1 &, const ContextSourceFollowing2920b50ListV1 &) = default;
};
struct ContextSourceFollowing2920b50OwnV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> component_present;
  ContextSourceFollowing2920b50OccurrenceV1 occurrence{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2920b50OwnV1 &, const ContextSourceFollowing2920b50OwnV1 &) = default;
};
struct ContextSourceFollowing2920b50InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceFollowing2920b50ListV1 list_1c8_50{};
  ContextSourceFollowing2920b50OwnV1 own_1b0_570{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2920b50InputsV1 &, const ContextSourceFollowing2920b50InputsV1 &) = default;
};

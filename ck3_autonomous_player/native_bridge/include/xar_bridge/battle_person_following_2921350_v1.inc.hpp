// Included inside xar::game; source and raw schema precede this collector DTO.
struct ContextSourceFollowing2921350TitleSourceV1 {
  std::string status = "partial"; bool ready = false;
  std::optional<bool> carrier_present;
  std::optional<std::string> selection, header_identity;
  std::optional<std::int32_t> count_raw;
  std::optional<bool> array_present;
  std::optional<std::vector<std::uint32_t>> full_ids_u32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350TitleSourceV1 &, const ContextSourceFollowing2921350TitleSourceV1 &) = default;
};
struct ContextSourceFollowing2921350TitleWalkV1 {
  std::int32_t native_index = 0, root_index = 0;
  std::optional<std::int32_t> parent_index;
  std::optional<std::uint32_t> requested_full_id_u32, selected_full_id_u32;
  std::optional<std::string> selection, title_identity, definition_identity;
  std::optional<std::int32_t> tier_raw_i32, children_count_raw;
  std::optional<bool> children_array_present;
  std::optional<std::vector<std::uint32_t>> child_ids_u32;
  std::optional<bool> collected;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350TitleWalkV1 &, const ContextSourceFollowing2921350TitleWalkV1 &) = default;
};
struct ContextSourceFollowing2921350MapProbeV1 {
  std::int32_t native_index = 0;
  std::optional<std::int64_t> bucket_index_i64;
  std::optional<std::uint8_t> distance_raw_u8;
  std::optional<std::uint32_t> key_raw_u32;
  std::optional<std::int64_t> operand_q64;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350MapProbeV1 &, const ContextSourceFollowing2921350MapProbeV1 &) = default;
};
struct ContextSourceFollowing2921350MapV1 {
  std::string status = "partial"; bool ready = false;
  std::optional<std::string> data_identity;
  std::optional<std::int32_t> mask_raw_i32;
  std::optional<std::uint8_t> overflow_raw_u8;
  std::vector<ContextSourceFollowing2921350MapProbeV1> probes;
  std::optional<bool> found;
  std::optional<std::int64_t> operand_q64;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350MapV1 &, const ContextSourceFollowing2921350MapV1 &) = default;
};
struct ContextSourceFollowing2921350TierV1 {
  std::string status = "partial"; bool ready = false;
  std::optional<std::int32_t> count_raw_i32;
  std::optional<std::string> data_identity;
  std::optional<std::vector<std::int64_t>> thresholds_q64;
  std::optional<std::int32_t> selected_index_raw_i32;
  std::optional<std::string> selection;
  std::optional<std::int32_t> default_guard_raw_i32;
  ContextSourceAfterPcV1 pc{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350TierV1 &, const ContextSourceFollowing2921350TierV1 &) = default;
};
struct ContextSourceFollowing2921350SourceV1 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> requested_full_id_u32, selected_full_id_u32;
  std::optional<std::string> selection, object_identity, definition_identity;
  std::optional<std::int32_t> group_index_raw_i32;
  ContextSourceFollowing2921350MapV1 map{};
  ContextSourceFollowing2921350TierV1 tiers{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350SourceV1 &, const ContextSourceFollowing2921350SourceV1 &) = default;
};
struct ContextSourceFollowing2921350ProvinceStepV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> title_identity, definition_identity, selection;
  std::optional<std::int32_t> tier_raw_i32;
  std::optional<std::uint32_t> requested_full_id_u32, selected_full_id_u32;
  std::optional<std::int32_t> first_child_count_raw;
  std::optional<bool> first_child_array_present;
  std::optional<std::uint32_t> first_child_full_id_u32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350ProvinceStepV1 &, const ContextSourceFollowing2921350ProvinceStepV1 &) = default;
};
struct ContextSourceFollowing2921350ProvinceV1 {
  std::int32_t native_index = 0, title_walk_index = 0;
  std::vector<ContextSourceFollowing2921350ProvinceStepV1> steps;
  std::optional<std::string> province_identity;
  std::optional<std::uint32_t> magic_u32;
  std::optional<bool> admitted;
  std::optional<std::uint32_t> full_id_u32;
  std::optional<std::int32_t> source_count_raw;
  std::optional<bool> source_array_present;
  std::optional<std::vector<std::uint32_t>> source_ids_u32;
  std::vector<ContextSourceFollowing2921350SourceV1> sources;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350ProvinceV1 &, const ContextSourceFollowing2921350ProvinceV1 &) = default;
};
struct ContextSourceFollowing2921350ManagerV1 {
  std::string status = "partial"; bool ready = false;
  std::optional<bool> loaded;
  std::optional<std::string> identity;
  std::optional<std::int32_t> group_count_raw_i32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350ManagerV1 &, const ContextSourceFollowing2921350ManagerV1 &) = default;
};
struct ContextSourceFollowing2921350InputsV1 {
  std::string status = "partial"; bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::string> character_identity;
  std::string source_scope = "held_current_native_inputs";
  ContextSourceFollowing2921350TitleSourceV1 title_source{};
  std::vector<ContextSourceFollowing2921350TitleWalkV1> title_walk;
  std::vector<ContextSourceFollowing2921350ProvinceV1> provinces;
  ContextSourceFollowing2921350ManagerV1 manager{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2921350InputsV1 &, const ContextSourceFollowing2921350InputsV1 &) = default;
};

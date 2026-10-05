// Included after ContextSourcePropertiesV1 inside namespace xar::game.
struct ContextSource2922070EdgeV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_id_raw;
  std::optional<std::string> selection;
  std::optional<std::string> object_identity;
  std::optional<std::string> holder_identity;
  std::optional<std::int32_t> holder_id_18_raw;
  std::string reason;
  friend bool operator==(const ContextSource2922070EdgeV1 &,
                         const ContextSource2922070EdgeV1 &) = default;
};
struct ContextSource2922070WalkV1 {
  std::int32_t native_index = 0;
  std::string character_identity;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> count_c_raw;
  std::optional<bool> array_present;
  std::vector<ContextSource2922070EdgeV1> edges;
  std::string reason;
  friend bool operator==(const ContextSource2922070WalkV1 &,
                         const ContextSource2922070WalkV1 &) = default;
};
struct ContextSource2922070CharacterV1 {
  std::int32_t native_index = 0;
  bool include_self = false;
  std::optional<std::int32_t> input_id_raw;
  std::optional<std::string> selection;
  std::optional<std::string> character_identity;
  std::optional<std::int32_t> character_id_18_raw;
  std::optional<std::int32_t> first_key_158_raw;
  std::optional<std::string> first_selection;
  std::optional<std::string> first_identity;
  std::optional<std::int32_t> owner_id_160_raw;
  std::optional<std::string> owner_selection;
  std::optional<std::string> owner_identity;
  std::optional<std::string> government_selection;
  std::optional<std::string> government_identity;
  std::optional<std::uint64_t> government_mask_40_raw;
  std::optional<std::string> top_character_identity;
  std::optional<std::string> top_government_selection;
  std::optional<std::string> top_government_identity;
  std::optional<std::uint64_t> top_government_mask_40_raw;
  std::optional<bool> admitted;
  std::string reason;
  friend bool operator==(const ContextSource2922070CharacterV1 &,
                         const ContextSource2922070CharacterV1 &) = default;
};
struct ContextSource2922070KeyV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_id_raw;
  std::optional<std::string> selection;
  std::optional<std::string> object_identity;
  std::optional<std::uint8_t> gate_32_raw;
  std::string reason;
  friend bool operator==(const ContextSource2922070KeyV1 &,
                         const ContextSource2922070KeyV1 &) = default;
};
struct ContextSource2922070MembershipV1 {
  std::int32_t native_index = 0;
  std::int32_t character_index = 0;
  std::optional<std::int32_t> first_key_158_raw;
  std::optional<std::string> first_selection;
  std::optional<std::string> first_identity;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> count_c_raw;
  std::optional<bool> array_present;
  std::vector<ContextSource2922070KeyV1> scans;
  std::optional<bool> admitted;
  std::optional<std::int32_t> first_id_10_raw;
  std::optional<bool> appended;
  std::string reason;
  friend bool operator==(const ContextSource2922070MembershipV1 &,
                         const ContextSource2922070MembershipV1 &) = default;
};
struct ContextSource2922070RowV1 {
  std::int32_t native_index = 0;
  std::int32_t input_index = 0;
  std::int32_t requested_id_raw = -1;
  std::optional<std::string> selection;
  std::optional<std::string> source_identity;
  std::optional<std::int32_t> selected_id_10_raw;
  std::optional<std::uint8_t> type_280_raw;
  std::optional<bool> admitted;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> definition_magic_38_raw;
  std::optional<std::int32_t> count_214_raw;
  std::optional<std::int32_t> requested_index_228_raw;
  std::optional<std::int32_t> selected_index_raw;
  std::optional<std::string> table_identity;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSource2922070RowV1 &,
                         const ContextSource2922070RowV1 &) = default;
};
struct ContextSourceHelper2922070V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  bool gate_ready = false;
  bool collection_ready = false;
  bool rows_ready = false;
  std::optional<std::string> government_selection;
  std::optional<std::string> government_identity;
  std::optional<std::uint8_t> government_mode_4d6_raw;
  std::optional<bool> character_land_present;
  std::optional<std::string> subject_identity;
  std::optional<std::uint32_t> subject_magic_c_raw;
  std::optional<std::int32_t> subject_id_8_raw;
  std::optional<bool> admitted;
  std::optional<std::vector<ContextSource2922070WalkV1>> walk_nodes;
  std::optional<std::vector<ContextSource2922070CharacterV1>> characters;
  std::optional<std::vector<std::int32_t>> character_order;
  std::optional<std::vector<ContextSource2922070MembershipV1>> membership_rows;
  std::optional<std::vector<std::int32_t>> output_ids;
  std::optional<std::vector<ContextSource2922070RowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceHelper2922070V1 &,
                         const ContextSourceHelper2922070V1 &) = default;
};

// Included after ContextSourcePropertiesV1 inside namespace xar::game.
struct ContextSourceTailPrefixRelationV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> character_identity;
  std::optional<std::uint32_t> magic_1c_raw;
  std::optional<std::int32_t> character_id_18_raw;
  std::optional<bool> accepted;
  std::optional<std::string> next_selection;
  std::optional<std::int32_t> next_key_c8_raw;
  std::optional<std::string> next_identity;
  std::string reason;
  friend bool operator==(const ContextSourceTailPrefixRelationV1 &,
                         const ContextSourceTailPrefixRelationV1 &) = default;
};
struct ContextSourceTailPrefix275V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> first_key_158_raw;
  std::optional<std::string> first_selection;
  std::optional<std::string> first_identity;
  std::optional<std::uint8_t> caller_gate_218_raw;
  std::optional<std::uint8_t> caller_gate_218_recheck_raw;
  std::optional<bool> caller_admitted;
  std::optional<std::string> definition_identity;
  std::optional<std::string> definition_pointer_260_identity;
  std::optional<bool> character_land_present;
  std::optional<std::int32_t> land_field_1f8_raw;
  std::optional<std::string> government_selection;
  std::optional<std::string> government_identity;
  std::optional<std::uint8_t> government_mode_80c_raw;
  std::optional<std::string> predicate_pointer_selection;
  std::optional<std::string> predicate_pointer_identity;
  std::optional<bool> predicate_admitted;
  std::optional<std::int32_t> owner_key_1e0_raw;
  std::optional<std::string> owner_selection;
  std::optional<std::string> owner_identity;
  std::optional<std::int32_t> owner_id_160_raw;
  std::optional<std::int32_t> character_id_18_raw;
  std::optional<std::string> initial_relation_selection;
  std::optional<std::int32_t> initial_relation_key_c8_raw;
  std::optional<std::string> initial_relation_identity;
  std::optional<std::vector<ContextSourceTailPrefixRelationV1>> relation_rows;
  std::optional<std::int32_t> last_character_id_18_raw;
  std::optional<bool> owner_admitted;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceTailPrefix275V1 &,
                         const ContextSourceTailPrefix275V1 &) = default;
};
struct ContextSourceTailPrefix2530RowV1 {
  std::int32_t native_index = 0;
  std::optional<bool> admitted;
  std::optional<std::string> definition_identity;
  std::optional<std::int32_t> count_214_raw;
  std::optional<std::int32_t> requested_index_228_raw;
  std::optional<std::int32_t> selected_index_raw;
  std::optional<std::string> table_identity;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceTailPrefix2530RowV1 &,
                         const ContextSourceTailPrefix2530RowV1 &) = default;
};
struct ContextSourceTailPrefix2530V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> first_key_158_raw;
  std::optional<std::string> first_selection;
  std::optional<std::string> first_identity;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> definition_magic_38_raw;
  std::optional<bool> admitted;
  std::optional<std::uint8_t> type_280_raw;
  std::optional<std::int32_t> owner_id_160_raw;
  std::optional<std::int32_t> character_id_18_raw;
  std::optional<std::vector<ContextSourceTailPrefix2530RowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceTailPrefix2530V1 &,
                         const ContextSourceTailPrefix2530V1 &) = default;
};
struct ContextSourceTailPrefixV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceTailPrefix275V1 helper_2753860;
  ContextSourceTailPrefix2530V1 helper_2922530;
  std::string reason;
  friend bool operator==(const ContextSourceTailPrefixV1 &,
                         const ContextSourceTailPrefixV1 &) = default;
};

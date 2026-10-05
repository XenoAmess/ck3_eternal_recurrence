// Included after ContextSourcePropertiesV1, inside namespace xar::game.
struct ContextSourceRemainingRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> source_identity;
  std::optional<std::string> key_identity;
  std::optional<std::uint32_t> key_magic_raw;
  std::optional<std::int32_t> key_full_id_raw;
  std::optional<bool> admitted;
  std::optional<std::string> property_selection;
  std::optional<std::int32_t> mapping_native_index;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceRemainingRowV1 &,
                         const ContextSourceRemainingRowV1 &) = default;
};
struct ContextSourceRemainingFamilyV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> admitted;
  std::optional<std::int32_t> count;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceRemainingRowV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceRemainingFamilyV1 &,
                         const ContextSourceRemainingFamilyV1 &) = default;
};
struct ContextSourceRemainingRiteV1 {
  std::optional<std::int32_t> first_key_b4_raw;
  std::optional<std::string> first_selection;
  std::optional<std::int32_t> second_key_4b8_raw;
  std::optional<std::string> second_selection;
  std::optional<std::int32_t> third_key_98_raw;
  std::optional<std::string> third_selection;
  std::optional<std::string> selected_identity;
  std::optional<std::int32_t> membership_count;
  std::optional<bool> membership_array_present;
  std::optional<std::vector<std::string>> membership_identities;
  std::string reason;
  friend bool operator==(const ContextSourceRemainingRiteV1 &,
                         const ContextSourceRemainingRiteV1 &) = default;
};
struct ContextSourceRemaining550V1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int32_t> culture_key_b0_raw;
  std::optional<std::string> culture_selection;
  std::optional<std::string> culture_identity;
  std::optional<std::uint32_t> culture_magic_raw;
  std::optional<std::int32_t> culture_full_id_raw;
  std::optional<bool> admitted;
  std::optional<std::string> government_selection;
  std::optional<std::string> government_identity;
  std::optional<std::uint32_t> government_magic_raw;
  std::optional<std::int32_t> government_full_id_raw;
  std::optional<std::int32_t> government_default_guard_raw;
  std::optional<std::int32_t> mapped_default_guard_raw;
  ContextSourceRemainingRiteV1 rite;
  ContextSourceRemainingFamilyV1 government_indexed;
  ContextSourceRemainingFamilyV1 culture_direct;
  ContextSourceRemainingFamilyV1 culture_mapped;
  std::string reason;
  friend bool operator==(const ContextSourceRemaining550V1 &,
                         const ContextSourceRemaining550V1 &) = default;
};
struct ContextSourceRemainingOuterV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> source_identity;
  std::optional<std::int32_t> direct_gate_raw;
  std::optional<bool> direct_admitted;
  std::optional<std::string> direct_property_identity;
  std::optional<ContextSourcePropertiesV1> direct_property_block;
  std::string direct_reason;
  ContextSourceRemainingFamilyV1 inner_mapped;
  friend bool operator==(const ContextSourceRemainingOuterV1 &,
                         const ContextSourceRemainingOuterV1 &) = default;
};
struct ContextSourceRemaining940V1 {
  std::string status = "unavailable";
  bool ready = false;
  bool direct_ready = false;
  bool mapped_ready = false;
  std::optional<std::int32_t> first_key_158_raw;
  std::optional<std::string> first_selection;
  std::optional<std::int32_t> second_key_2c_raw;
  std::optional<std::string> second_selection;
  std::optional<std::string> selected_identity;
  std::optional<std::int32_t> outer_count;
  std::optional<bool> outer_array_present;
  std::optional<std::vector<ContextSourceRemainingOuterV1>> outer_rows;
  std::optional<std::int32_t> mapped_default_guard_raw;
  ContextSourceRemainingRiteV1 rite;
  std::string reason;
  friend bool operator==(const ContextSourceRemaining940V1 &,
                         const ContextSourceRemaining940V1 &) = default;
};
struct ContextSourceRemainingHelpersV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceRemaining550V1 helper_291f550;
  ContextSourceRemaining940V1 helper_291f940;
  std::string reason;
  friend bool operator==(const ContextSourceRemainingHelpersV1 &,
                         const ContextSourceRemainingHelpersV1 &) = default;
};


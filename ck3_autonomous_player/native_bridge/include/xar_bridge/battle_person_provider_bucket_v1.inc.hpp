// Included inside xar::game after the existing paired PropertyContainer DTO.
// key_2f8_raw is a held current Character component, not a future refreshed input.
struct ContextSourceProviderBucket291c5b2V1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> provider_present;
  std::optional<std::string> provider_identity;
  std::optional<bool> carrier_present;
  std::optional<std::int32_t> key_2f8_raw;
  std::optional<std::int32_t> denominator_5c68ce8_raw;
  std::optional<std::int32_t> bucket_index_raw;
  std::optional<std::int32_t> provider_count_1204_raw;
  std::optional<bool> provider_array_present;
  std::optional<std::string> selection;
  std::optional<std::string> selected_definition_identity;
  std::optional<std::uint32_t> selected_magic_raw;
  std::optional<bool> admitted;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceProviderBucket291c5b2V1 &,
                         const ContextSourceProviderBucket291c5b2V1 &) = default;
};

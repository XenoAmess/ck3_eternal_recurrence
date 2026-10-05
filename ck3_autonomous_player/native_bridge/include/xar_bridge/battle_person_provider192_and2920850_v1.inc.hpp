// Included inside xar::game; the provider192/2920850 source schema precedes code.
struct ContextSourceProvider192V1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> provider_loaded;
  std::optional<std::string> provider_identity;
  std::optional<std::int16_t> character_192_i16;
  std::optional<std::int32_t> upper_i32;
  std::optional<std::int32_t> lower_i32;
  std::optional<std::string> selection;
  std::optional<std::string> selected_identity;
  std::optional<std::uint32_t> magic_u32;
  std::optional<bool> admitted;
  ContextSourceAfterPcV1 pc{};
  std::string reason;
  friend bool operator==(const ContextSourceProvider192V1 &, const ContextSourceProvider192V1 &) = default;
};
struct ContextSourceProvider2920850DirectV1 {
  std::int32_t native_index = 0;
  ContextSourceAfterPcV1 pc{};
  friend bool operator==(const ContextSourceProvider2920850DirectV1 &, const ContextSourceProvider2920850DirectV1 &) = default;
};
struct ContextSourceProvider2920850NestedV1 {
  std::int32_t native_index = 0;
  ContextSourceRemainingFamilyV1 mapped_family{};
  friend bool operator==(const ContextSourceProvider2920850NestedV1 &, const ContextSourceProvider2920850NestedV1 &) = default;
};
struct ContextSourceProvider2920850OccurrenceV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<std::string> resolution_selection;
  std::optional<std::int32_t> selected_full_id_raw;
  std::optional<std::string> object_identity;
  std::optional<std::string> table_identity;
  std::optional<std::vector<ContextSourceProvider2920850DirectV1>> direct_rows;
  std::optional<std::vector<ContextSourceProvider2920850NestedV1>> nested_rows;
  bool direct_ready = false;
  bool mapped_ready = false;
  bool ready = false;
  std::string reason;
  friend bool operator==(const ContextSourceProvider2920850OccurrenceV1 &, const ContextSourceProvider2920850OccurrenceV1 &) = default;
};
struct ContextSourceProvider2920850ListV1 {
  std::string status = "partial";
  bool ready = false;
  bool direct_ready = false;
  bool mapped_ready = false;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> default_init_guard_raw;
  std::optional<std::int32_t> count_raw;
  std::optional<std::int32_t> numeric_count;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceProvider2920850OccurrenceV1>> rows;
  std::string reason;
  friend bool operator==(const ContextSourceProvider2920850ListV1 &, const ContextSourceProvider2920850ListV1 &) = default;
};
struct ContextSourceProvider192And2920850InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> current_land_present;
  std::optional<bool> current_death_present;
  ContextSourceRemainingRiteV1 rite{};
  std::optional<std::int32_t> mapped_default_guard_raw;
  ContextSourceProvider192V1 provider_192{};
  ContextSourceProvider2920850ListV1 list_168{};
  ContextSourceProvider2920850ListV1 list_180{};
  std::string reason;
  friend bool operator==(const ContextSourceProvider192And2920850InputsV1 &, const ContextSourceProvider192And2920850InputsV1 &) = default;
};
